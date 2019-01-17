# -*- coding: utf-8 -*-

"""
    S3 Adobe PDF codec

    @copyright: 2011-2018 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ("S3RL_PDF",)

try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO

from copy import deepcopy
import os

from gluon import current, redirect, URL, \
                  A, DIV, H1, H2, H3, H4, H5, H6, IMG, P, \
                  TABLE, TBODY, TD, TFOOT, TH, THEAD, TR
from gluon.storage import Storage
from gluon.contenttype import contenttype
from gluon.languages import lazyT

from ..s3codec import S3Codec
from ..s3utils import s3_strip_markup, s3_unicode, s3_str

try:
    from reportlab.lib import colors
    from reportlab.lib.colors import Color, HexColor
    from reportlab.lib.pagesizes import A4, LETTER, landscape, portrait
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas
    from reportlab.platypus import BaseDocTemplate, PageBreak, PageTemplate, \
                                   Paragraph, Spacer, Table
    from reportlab.platypus.frames import Frame
    reportLabImported = True
except ImportError:
    reportLabImported = False
    BaseDocTemplate = object
    inch = 72.0
    canvas = Storage()
    canvas.Canvas = None

try:
    from bidi.algorithm import get_display
    import arabic_reshaper
    import unicodedata
    biDiImported = True
except ImportError:
    biDiImported = False
    current.log.warning("PDF Codec", "BiDirectional Support not available: Install Python-BiDi")

PDF_WIDTH = 0
PDF_HEIGHT = 1

# -----------------------------------------------------------------------------
def set_fonts(instance):
    """
        DRY Helper function for all classes which use PDF to set the appropriate Fonts
    """

    font_set = current.deployment_settings.get_pdf_export_font()
    if font_set:
        try:
            font_name = font_set[0]
            font_name_bold = font_set[1]
            folder = current.request.folder
            # Requires the font-files at /static/fonts/<font_name>.ttf
            pdfmetrics.registerFont(TTFont(font_name, os.path.join(folder,
                                                                   "static",
                                                                   "fonts",
                                                                   "%s.ttf" % font_name)))
            pdfmetrics.registerFont(TTFont(font_name_bold, os.path.join(folder,
                                                                        "static",
                                                                        "fonts",
                                                                        "%s.ttf" % font_name_bold)))
        except:
            current.log.error("%s Font not found: Please install it to see the correct fonts in PDF exports" % font_set[0])
            # Use the default "Helvetica" and "Helvetica-Bold"
            instance.font_name = "Helvetica"
            instance.font_name_bold = "Helvetica-Bold"
        else:
            instance.font_name = font_name
            instance.font_name_bold = font_name_bold
    else:
        # Use the default "Helvetica" and "Helvetica-Bold"
        instance.font_name = "Helvetica"
        instance.font_name_bold = "Helvetica-Bold"

# -----------------------------------------------------------------------------
def biDiText(text):
    """
        Ensure that RTL text is rendered RTL & also that Arabic text is
        rewritten to use the joined format.
    """

    text = s3_unicode(text)

    if biDiImported and current.deployment_settings.get_pdf_bidi():

        isArabic = False
        isBidi = False

        for c in text:
            cat = unicodedata.bidirectional(c)

            if cat in ("AL", "AN"):
                isArabic = True
                isBidi = True
                break
            elif cat in ("R", "RLE", "RLO"):
                isBidi = True

        if isArabic:
            text = arabic_reshaper.reshape(text)

        if isBidi:
            text = get_display(text)

    return text

# =============================================================================
class S3RL_PDF(S3Codec):
    """
        Simple Report Labs PDF format codec
    """

    def __init__(self):
        """
            Constructor
        """

        # Error codes
        self.ERROR = Storage(
            RL_ERROR = "Python needs the ReportLab module installed for PDF export"
        )

        # Fonts
        self.font_name = None
        self.font_name_bold = None
        set_fonts(self)

    # -------------------------------------------------------------------------
    def encode(self, resource, **attr):
        """
            Export data as a PDF document

            @param resource: the resource
            @param attr: dictionary of keyword arguments, in s3_rest_controller
                         passed through from the calling controller

            @keyword request: the S3Request
            @keyword method: "read" to not include a list view when no
                             component is specified
            @keyword list_fields: fields to include in lists

            @keyword pdf_componentname: enforce this component

            @keyword pdf_groupby: how to group the results
            @keyword pdf_orderby: how to sort rows (within any level of grouping)

            @keyword pdf_callback: callback to be used rather than request

            @keyword pdf_title: the title of the report
            @keyword pdf_filename: the filename for the report

            @keyword rheader: HTML page header (override by pdf_header)
            @keyword rfooter: HTML page footer (override by pdf_footer)
            @keyword pdf_header: callback to generate the HTML header
                                 (overrides rheader)
            @keyword pdf_footer: callback to generate the HTML footer,
                                 or static HTML (overrides rfooter)

            @keyword pdf_header_padding: add this amount of space between
                                         the header and the body
            @keyword pdf_footer_padding: add this amount of space between
                                         the body and the footer

            @keyword pdf_hide_comments: don't show the comments in a table

            @keyword pdf_table_autogrow: Indicates that a table should grow to
                                          fill the available space. Valid values:
                                          H - Horizontal
                                          V - Vertical
                                          B - Both
            @keyword pdf_orientation: Portrait (default) or Landscape
            @keyword use_colour:      True to add colour to the cells. default False

            @keyword pdf_html_styles: styles for S3html2pdf (dict)

            @ToDo: Add Page Numbers in Footer:
                   http://www.blog.pythonlibrary.org/2013/08/12/reportlab-how-to-add-page-numbers/
        """

        if not reportLabImported:
            current.session.error = self.ERROR.RL_ERROR
            redirect(URL(extension=""))

        # Settings
        attr_get = attr.get
        r = self.r = attr_get("request", None)
        self.list_fields = attr_get("list_fields")
        self.pdf_groupby = attr_get("pdf_groupby")
        self.pdf_orderby = attr_get("pdf_orderby")
        self.pdf_hide_comments = attr_get("pdf_hide_comments")
        self.table_autogrow = attr_get("pdf_table_autogrow")
        self.pdf_header_padding = attr_get("pdf_header_padding", 0)
        self.pdf_footer_padding = attr_get("pdf_footer_padding", 0)

        # Get the title & filename
        now = current.request.now.isoformat()[:19].replace("T", " ")
        title = attr_get("pdf_title")
        if title is None:
            title = "Report"
        docTitle = "%s %s" % (title, now)
        filename = attr_get("pdf_filename")
        if filename is None:
            if not isinstance(title, str):
                # Must be str not unicode
                title = title.encode("utf-8")
            filename = "%s_%s.pdf" % (title, now)
        elif len(filename) < 5 or filename[-4:] != ".pdf":
            # Add extension
            filename = "%s.pdf" % filename
        self.filename = filename

        # Get the Doc Template
        size = attr_get("pdf_size")
        orientation = attr_get("pdf_orientation")
        if not orientation:
            orientation = current.deployment_settings.get_pdf_orientation()
        doc = EdenDocTemplate(title = docTitle,
                              size = size,
                              orientation = orientation,
                              )

        # HTML styles
        pdf_html_styles = attr_get("pdf_html_styles")

        # Get the header
        header_flowable = None
        header = attr_get("pdf_header")
        if not header:
            header = attr_get("rheader")
        if header:
            header_flowable = self.get_html_flowable(header,
                                                     doc.printable_width,
                                                     styles = pdf_html_styles,
                                                     )
            if self.pdf_header_padding:
                header_flowable.append(Spacer(1, self.pdf_header_padding))

        # Get the footer
        footer_flowable = None
        footer = attr_get("pdf_footer")
        if not footer:
            footer = attr_get("rfooter")
        if footer:
            footer_flowable = self.get_html_flowable(footer,
                                                     doc.printable_width,
                                                     styles = pdf_html_styles,
                                                     )
            if self.pdf_footer_padding:
                footer_flowable.append(Spacer(1, self.pdf_footer_padding))

        # Build report template

        # Get data for the body of the text
        body_flowable = None

        doc.calc_body_size(header_flowable, footer_flowable)

        callback = attr_get("pdf_callback")
        pdf_componentname = attr_get("pdf_componentname", None)
        if callback:
            # Get the document body from the callback
            body_flowable = self.get_html_flowable(callback(r),
                                                   doc.printable_width,
                                                   styles = pdf_html_styles,
                                                   )

        elif pdf_componentname: # and resource.parent is None:
            # Enforce a particular component
            resource = current.s3db.resource(r.tablename,
                                             components = [pdf_componentname],
                                             id = r.id,
                                             )
            component = resource.components.get(pdf_componentname)
            if component:
                body_flowable = self.get_resource_flowable(component, doc)

        elif r.component or attr_get("method", "list") != "read":
            # Use the requested resource
            body_flowable = self.get_resource_flowable(resource, doc)

        styleSheet = getSampleStyleSheet()
        style = styleSheet["Normal"]
        style.fontName = self.font_name
        style.fontSize = 9
        if not body_flowable:
            body_flowable = [Paragraph("", style)]
        self.normalstyle = style

        # Build the PDF
        doc.build(header_flowable,
                  body_flowable,
                  footer_flowable,
                  )

        # Return the generated PDF
        response = current.response
        if response:
            disposition = "attachment; filename=\"%s\"" % self.filename
            response.headers["Content-Type"] = contenttype(".pdf")
            response.headers["Content-disposition"] = disposition

        return doc.output.getvalue()

    # -------------------------------------------------------------------------
    def get_html_flowable(self, rules, printable_width, styles=None):
        """
            Function to convert the rules passed in to a flowable.
            The rules (for example) could be an rHeader callback

            @param rules: the HTML (web2py helper class) or a callback
                          to produce it. The callback receives the
                          S3Request as parameter.
            @param printable_width: the printable width
            @param styles: styles for HTML=>PDF conversion
        """

        if callable(rules):
            # Callback to produce the HTML (e.g. rheader)
            r = self.r
            # Switch to HTML representation
            if r is not None:
                representation = r.representation
                r.representation = "html"
            try:
                html = rules(r)
            except:
                # Unspecific except => must raise in debug mode
                if current.response.s3.debug:
                    raise
                else:
                    import sys
                    current.log.error(sys.exc_info()[1])
                    html = ""
            if r is not None:
                r.representation = representation
        else:
            # Static HTML
            html = rules

        parser = S3html2pdf(pageWidth=printable_width,
                            exclude_class_list=["tabs"],
                            styles = styles,
                            )
        result = parser.parse(html)
        return result

    # -------------------------------------------------------------------------
    def get_resource_flowable(self, resource, doc):
        """
            Get a list of fields, if the list_fields attribute is provided
            then use that to extract the fields that are required, otherwise
            use the list of readable fields.
        """

        fields = self.list_fields
        if fields:
            list_fields = [f for f in fields if f != "id"]
        else:
            list_fields = [f.name for f in resource.readable_fields()
                                  if f.type != "id" and
                                     f.name != "comments" or
                                     not self.pdf_hide_comments]

        get_vars = Storage(current.request.get_vars)
        get_vars["iColumns"] = len(list_fields)
        dtfilter, orderby, left = resource.datatable_filter(list_fields, get_vars)
        resource.add_filter(dtfilter)

        result = resource.select(list_fields,
                                 left=left,
                                 limit=None,
                                 count=True,
                                 getids=True,
                                 orderby=orderby,
                                 represent=True,
                                 show_links=False)

        # Now generate the PDF table
        pdf_table = S3PDFTable(doc,
                               result.rfields,
                               result.rows,
                               groupby = self.pdf_groupby,
                               autogrow = self.table_autogrow,
                               body_height = doc.body_height,
                               ).build()

        return pdf_table

# =============================================================================
class EdenDocTemplate(BaseDocTemplate):
    """
        The standard document template for eden reports
        It allows for the following page templates:
        1) First Page
        2) Even Page
        3) Odd Page
        4) Landscape Page
    """

    def __init__(self,
                 title = "Sahana Eden",
                 margin = (0.5 * inch,  # top
                           0.3 * inch,  # left
                           0.5 * inch,  # bottom
                           0.3 * inch), # right
                 margin_inside = 0.0 * inch, # used for odd even pages
                 size = None,
                 orientation = "Auto",
                 ):
        """
            Set up the standard page templates
        """

        self.output = StringIO()

        if orientation == "Auto":
            # Start with "Portrait", allow later adjustment
            self.page_orientation = "Portrait"
            self.auto_orientation = True
        else:
            # Fixed page orientation
            self.page_orientation = orientation
            self.auto_orientation = False

        if not size:
            size = current.deployment_settings.get_pdf_size()
        if size == "Letter":
            self.paper_size = LETTER
        elif size == "A4" or not isinstance(size, tuple):
            self.paper_size = A4
        else:
            self.paper_size = size

        self.topMargin = margin[0]
        self.leftMargin = margin[1]
        self.bottomMargin = margin[2]
        self.rightMargin = margin[3]
        self.insideMargin = margin_inside

        BaseDocTemplate.__init__(self,
                                 self.output,
                                 title = s3_str(title),
                                 leftMargin = self.leftMargin,
                                 rightMargin = self.rightMargin,
                                 topMargin = self.topMargin,
                                 bottomMargin = self.bottomMargin,
                                 )

        self.MINIMUM_MARGIN_SIZE = 0.2 * inch
        self.body_flowable = None

        self._calc()

    # -------------------------------------------------------------------------
    def get_flowable_size(self, flowable):
        """
            Function to return the size a flowable will require
        """

        if not flowable:
            return (0, 0)
        if not isinstance(flowable, list):
            flowable = [flowable]
        w = 0
        h = 0
        for f in flowable:
            if f:
                size = f.wrap(self.printable_width,
                              self.printable_height)
                if size[0] > w:
                    w = size[PDF_WIDTH]
                h += size[PDF_HEIGHT]
        return (w, h)

    # -------------------------------------------------------------------------
    def _calc(self):

        if self.page_orientation == "Landscape":
            self.pagesize = landscape(self.paper_size)
        else:
            self.pagesize = portrait(self.paper_size)

        BaseDocTemplate._calc(self)
        self.height = self.pagesize[PDF_HEIGHT]
        self.width = self.pagesize[PDF_WIDTH]
        self.printable_width = self.width - \
                               self.leftMargin - \
                               self.rightMargin - \
                               self.insideMargin
        self.printable_height = self.height - \
                                self.topMargin - \
                                self.bottomMargin

    # -------------------------------------------------------------------------
    def calc_body_size(self,
                       header_flowable,
                       footer_flowable,
                       ):
        """
            Helper function to calculate the various sizes of the page
        """

        self._calc()    # in case we changed margins sizes etc
        #self.height = self.pagesize[PDF_HEIGHT]
        #self.width = self.pagesize[PDF_WIDTH]
        #self.printable_width = self.width - \
        #                       self.leftMargin - \
        #                       self.rightMargin - \
        #                       self.insideMargin
        #self.printable_height = self.height - \
        #                        self.topMargin - \
        #                        self.bottomMargin
        header_size = self.get_flowable_size(header_flowable)
        footer_size = self.get_flowable_size(footer_flowable)
        self.header_height = header_size[PDF_HEIGHT]
        self.footer_height = footer_size[PDF_HEIGHT]
        self.body_height = self.printable_height - \
                           self.header_height - \
                           self.footer_height

    # -------------------------------------------------------------------------
    def build(self,
              header_flowable,
              body_flowable,
              footer_flowable,
              canvasmaker=canvas.Canvas):
        """
            Build the document using the flowables.

            Set up the page templates that the document can use
        """

        self.header_flowable = header_flowable
        self.body_flowable = body_flowable
        self.footer_flowable = footer_flowable
        self.calc_body_size(header_flowable,
                            footer_flowable,
                            )
        showBoundary = 0 # for debugging set to 1, otherwise 0

        body_frame = Frame(self.leftMargin,
                           self.bottomMargin + self.footer_height,
                           self.printable_width,
                           self.body_height,
                           leftPadding = 0,
                           bottomPadding = 0,
                           rightPadding = 0,
                           topPadding = 0,
                           id = "body",
                           showBoundary = showBoundary
                           )

        self.body_frame = body_frame
        self.normalPage = PageTemplate(id = "Normal",
                                       frames = [body_frame,],
                                       onPage = self.add_page_decorators,
                                       pagesize = self.pagesize
                                       )
        # @todo set these page templates up
        #self.evenPage = PageTemplate(id = "even",
        #                             frames = frame_list,
        #                             onPage = self.onEvenPage,
        #                             pagesize = self.pagesize
        #                             )
        #self.oddPage = PageTemplate(id = "odd",
        #                            frames = frame_list,
        #                            onPage = self.onOddPage,
        #                            pagesize = self.pagesize
        #                            )
        self.landscapePage = PageTemplate(id = "Landscape",
                                          frames = [body_frame,],
                                          onPage = self.add_page_decorators,
                                          pagesize = landscape(self.pagesize)
                                          )
        if self.page_orientation == "Landscape":
            self.addPageTemplates(self.landscapePage)
        else:
            self.addPageTemplates(self.normalPage)

        BaseDocTemplate.build(self, self.body_flowable, canvasmaker=canvasmaker)

    # -------------------------------------------------------------------------
    def add_page_decorators(self, canvas, doc):
        """
        """

        if self.header_flowable:
            top = self.bottomMargin + self.printable_height
            for flow in self.header_flowable:
                height = self.get_flowable_size(flow)[PDF_HEIGHT]
                bottom = top - height
                flow.drawOn(canvas,
                            self.leftMargin,
                            bottom
                           )
                top = bottom
        if self.footer_flowable:
            top = self.bottomMargin + self.footer_height
            for flow in self.footer_flowable:
                height = self.get_flowable_size(flow)[PDF_HEIGHT]
                bottom = top - height
                flow.drawOn(canvas,
                            self.leftMargin,
                            bottom
                           )
                top = bottom

    # -------------------------------------------------------------------------
    def addParagraph(self, text, style=None, append=True):
        """
            Method to create a paragraph that may be inserted into the document

            @param text: The text for the paragraph
            @param append: If True then the paragraph will be stored in the
            document flow ready for generating the pdf.

            @return The paragraph

            This method can return the paragraph rather than inserting into the
            document. This is useful if the paragraph needs to be first
            inserted in another flowable, before being added to the document.
            An example of when this is useful is when large amounts of text
            (such as a comment) are added to a cell of a table.
        """

        if text != "":
            if style == None:
                styleSheet = getSampleStyleSheet()
                style = styleSheet["Normal"]
            text = biDiText(text)
            para = Paragraph(text, style)
            if append and self.body_flowable:
                self.body_flowable.append(para)
            return para
        return ""

    # -------------------------------------------------------------------------
    def cellStyle(self, style, cell):
        """
            Add special styles to the text in a cell
        """

        if style == "*GREY":
            return [("TEXTCOLOR", cell, cell, colors.lightgrey)]
        elif style == "*RED":
            return [("TEXTCOLOR", cell, cell, colors.red)]
        return []

    # -------------------------------------------------------------------------
    def addCellStyling(self, table, style):
        """
            Add special styles to the text in a table
        """

        row = 0
        for line in table:
            col = 0
            for cell in line:
                try:
                    if cell.startswith("*"):
                        (instruction, sep, text) = cell.partition(" ")
                        style += self.cellStyle(instruction, (col, row))
                        table[row][col] = text
                except:
                    pass
                col += 1
            row += 1
        return (table, style)

# =============================================================================
class S3PDFTable(object):
    """
        Class to build a table that can then be placed in a pdf document

        The table will be formatted so that is fits on the page. This class
        doesn't need to be called directly. Rather see S3PDF.addTable()
    """

    MIN_COL_WIDTH = 200
    MIN_ROW_HEIGHT = 20

    def __init__(self,
                 document,
                 rfields,
                 rows,
                 groupby = None,
                 autogrow = False,
                 body_height = 0,
                 ):
        """
            Constructor

            @param document: the EdenDocTemplate instance in which the table
                             shall be rendered
            @param rows: the represented rows (S3ResourceData.rows)
            @param rfields: list of resolved field selectors for
                            the columns (S3ResourceData.rfields)
            @param groupby: a field name that is to be used as a sub-group
                            - all records with the same value in that the
                              groupby column will be clustered together
        """

        rtl = current.response.s3.rtl

        # The main document
        self.doc = document

        # Parameters for rendering
        self.body_height = body_height
        self.autogrow = autogrow

        # Set fonts
        self.font_name = None
        self.font_name_bold = None
        set_fonts(self)

        # Determine list fields and collect the labels
        list_fields = []
        labels = []
        for rfield in rfields:
            list_fields.append(rfield.fname)
            labels.append(biDiText(rfield.label))
        if rtl:
            list_fields.reverse()
            labels.reverse()
        self.list_fields = list_fields
        self.labels = labels

        # Convert the input data into suitable ReportLab elements
        convert = self.convert
        data = []
        append = data.append
        for row in rows:
            row_data = [convert(rfield, row[rfield.colname]) for rfield in rfields]
            if rtl:
                row_data.reverse()
            append(row_data)
        self.data = data

        # Initialize style parameters (can be changed by caller after init)
        self.header_color = Color(0.73, 0.76, 1)
        self.odd_color = Color(0.92, 0.92, 1)
        self.even_color = Color(0.83, 0.84, 1)
        self.fontsize = 12

        # Initialize groups
        self.groupby = groupby
        self.subheading_rows = []
        self.subheading_level = {}

        # Initialize output
        self.pdf_data = []
        self.parts = []
        self.col_widths = []
        self.row_heights = []

    # -------------------------------------------------------------------------
    @classmethod
    def convert(cls, rfield, value):
        """
            Convert represented field value into a suitable
            ReportLab element

            @param rfield: the S3ResourceField
            @param value: the field value
        """

        if isinstance(value, (basestring, lazyT)):

            pdf_value = biDiText(value)

        elif isinstance(value, IMG):

            field = rfield.field
            if field:
                pdf_value = S3html2pdf.parse_img(value, field.uploadfolder)
                if pdf_value:
                    pdf_value = pdf_value[0]
            else:
                pdf_value = ""

        elif isinstance(value, DIV):

            if len(value.components) > 0:
                pdf_value = cls.convert(rfield, value.components[0])
            else:
                pdf_value = biDiText(value)

        else:

            pdf_value = biDiText(value)

        return pdf_value

    # -------------------------------------------------------------------------
    def build(self):
        """
            Method to build the table.

            @returns: a list of ReportLab Table instances
                      - if the table fits into the page width, this list will
                        contain a single Table, otherwise it will contain the
                        parts of the split table in the order in which they
                        shall be inserted into the main document
        """

        if self.groupby:
            data = self.group_data()
            data = [self.labels] + data
        elif self.data != None:
            data = [self.labels] + self.data
        self.pdf_data = data

        # Only build the table if we have some data
        if not data or not (data[0]):
            return None

        style = self.table_style(0, len(data), len(self.labels) - 1)

        self.parts = self.calc(data, style)

        return self.presentation()

    # -------------------------------------------------------------------------
    def group_data(self):
        """
            Group the rows

            @returns: the PDF-formatted data with grouping headers

            FIXME: will not work with RTL-biDiText or any non-text
                   representation, rewrite to use raw resource data

            FIXME: naming conventions!
        """

        groups = self.groupby.split(",")
        newData = []
        data = self.data
        level = 0
        list_fields = self.list_fields
        for field in groups:
            level += 1
            field = field.strip()
            # Find the location of field in list_fields
            i = 0
            rowlength = len(list_fields)
            while i < rowlength:
                if list_fields[i] == field:
                    break
                i += 1
            list_fields = list_fields[0:i] + list_fields[i + 1:]
            labels = self.labels[0:i] + self.labels[i + 1:]
            self.labels = labels
            currentGroup = None
            r = 0
            for row in data:
                if r + 1 in self.subheading_rows:
                    newData.append(row)
                    r += 1
                else:
                    try:
                        group = row[i]
                        if group != currentGroup:
                            line = [group]
                            newData.append(line)
                            r += 1
                            currentGroup = group
                            self.subheading_rows.append(r)
                            self.subheading_level[r] = level
                            # All existing subheadings after this point need to
                            # be shuffled down one place.
                            for x in range (len(self.subheading_rows)):
                                if self.subheading_rows[x] > r:
                                    posn = self.subheading_rows[x]
                                    self.subheading_rows[x] = posn + 1
                                    oldlevel = self.subheading_level[posn]
                                    del self.subheading_level[posn]
                                    self.subheading_level[posn + 1] = oldlevel
                        line = row[0:i] + row[i + 1:]
                        newData.append(line)
                        r += 1
                    except:
                        newData.append(row)
                        r += 1
            data = newData
            newData = []

        self.list_fields = list_fields
        return data

    # -------------------------------------------------------------------------
    def calc(self, data, style):
        """
            Compute rendering parameters:
                 - formatted output data
                 - row heights and column widths
                 - font-size

            @returns: the table parts, a list of row data arrays:
                      [ [[value1, value2, value3, ...], ...], ...]
        """

        main_doc = self.doc

        # A temporary document to test and adjust rendering parameters
        if main_doc.auto_orientation:
            orientation = "Auto"
        else:
            orientation = main_doc.page_orientation
        temp_doc = EdenDocTemplate(orientation = orientation,
                                   size = main_doc.paper_size,
                                   )

        # Make a copy so it can be changed
        style = style[:]

        # Build the table to determine row heights and column widths
        table = Table(data, repeatRows=1, style=style, hAlign="LEFT")
        temp_doc.build(None, [table], None)
        col_widths = table._colWidths
        row_heights = table._rowHeights

        # Determine the overall table width and whether it fits into the page
        table_width = sum(col_widths)
        fit = table_width <= temp_doc.printable_width

        # Prepare possible adjustments
        min_width = self.MIN_COL_WIDTH
        if not fit:
            # Determine which columns should be wrapped in Paragraphs
            # for automatic line breaks (=primary means to reduce width)
            para_cols = set(i for i, _ in enumerate(self.labels)
                              if col_widths[i] > min_width)
        else:
            para_cols = ()

        fontsize = self.fontsize
        min_fontsize = fontsize - 3

        styleSheet = getSampleStyleSheet()
        para_style = styleSheet["Normal"]

        adj_data = data = self.pdf_data
        while not fit:

            # Adjust margins
            available_margin_space = main_doc.leftMargin + \
                                     main_doc.rightMargin - \
                                     2 * main_doc.MINIMUM_MARGIN_SIZE

            overlap = table_width - temp_doc.printable_width
            if overlap < available_margin_space:
                # This will work => exit with current adjustments
                fit = True
                main_doc.leftMargin -= overlap / 2
                main_doc.rightMargin -= overlap / 2
                break

            # Wrap wide columns in Paragraphs (for automatic line breaks)
            adj_data = []
            para_style.fontSize = fontsize

            for row_index, row in enumerate(data):
                if row_index == 0:
                    adj_data.append(row)
                else:
                    temp_row = []
                    for col_index, item in enumerate(row):
                        if col_index in para_cols:
                            col_widths[col_index] = min_width
                            para = main_doc.addParagraph(item,
                                                              style=para_style,
                                                              append=False,
                                                              )
                            temp_row.append(para)
                        else:
                            temp_row.append(item)
                    adj_data.append(temp_row)

            # Rebuild temp_doc to re-calculate col widths and row heights
            style[1] = ("FONTSIZE", (0, 0), (-1, -1), fontsize)
            table = Table(adj_data,
                          repeatRows = 1,
                          style = style,
                          colWidths = col_widths,
                          hAlign = "LEFT",
                          )
            temp_doc.build(None, [table], None)

            col_widths = table._colWidths
            row_heights = table._rowHeights

            # Check if table fits into page
            table_width = sum(col_widths)
            if table_width > temp_doc.printable_width:

                if fontsize <= min_fontsize:
                    # Last resort: try changing page orientation
                    if main_doc.page_orientation == "Portrait" and \
                       main_doc.auto_orientation:

                        # Switch to Landscape
                        temp_doc.page_orientation = \
                        main_doc.page_orientation = "Landscape"

                        # Width becomes height
                        self.body_height = temp_doc.printable_width

                        # Re-calculate page size and margins
                        temp_doc._calc()
                        main_doc._calc()

                        # Reset font-size
                        fontsize = self.fontsize
                    else:
                        break
                else:
                    # Reduce font-size
                    fontsize -= 1
            else:
                fit = True
                break

        # Store adjusted rendering parameters
        self.pdf_data = adj_data
        self.fontsize = fontsize
        self.col_widths = [col_widths]
        self.row_heights = [row_heights]

        return [adj_data] if fit else self.split(temp_doc)

    # -------------------------------------------------------------------------
    def presentation(self):
        """
            Render all data parts (self.parts) as a list of ReportLab Tables.

            @returns: a list of ReportLab Table instances

            FIXME: clean up, naming conventions!
        """

        # Build the tables
        tables = []

        main_doc = self.doc
        autogrow = self.autogrow
        body_height = self.body_height
        default_row_height = self.MIN_ROW_HEIGHT

        num_parts = len(self.parts)
        num_horz_parts = len(self.col_widths)

        # Auto-grow horizontally (=make columns wider to fill page width)
        if autogrow == "H" or autogrow == "B":

            printable_width = self.doc.printable_width
            new_col_widths = []

            for widths in self.col_widths:
                total_width = sum(widths)
                if total_width and total_width < printable_width:
                    factor = 1 + (printable_width - total_width) / total_width
                    new_col_widths.append([width * factor for width in widths])
                else:
                    new_col_widths.append(widths)

            self.col_widths = new_col_widths

        # Render each part
        startRow = 0
        for current_part, part in enumerate(self.parts):

            if part == []:
                continue
            num_rows = len(part)

            col_widths = self.col_widths[current_part % num_horz_parts]
            row_heights = self.row_heights[int(current_part / num_horz_parts)]

            # Auto-grow vertically (=add empty extra rows)
            if autogrow == "V" or autogrow == "B":

                total_height = sum(row_heights)
                available_height = total_height - body_height

                if available_height > default_row_height:
                    num_extra_rows = int(available_height / default_row_height)
                    if num_extra_rows:
                        row = [""] * len(col_widths)
                        part += [row] * num_extra_rows

            style = self.table_style(startRow, num_rows, len(col_widths) - 1)
            (part, style) = main_doc.addCellStyling(part, style)

            p = Table(part,
                      repeatRows = 1,
                      style = style,
                      hAlign = "LEFT",
                      colWidths = col_widths,
                      rowHeights = row_heights,
                      emptyTableAction = "indicate",
                      )
            tables.append(p)

            # Add a page break, except for the last part
            next_part = current_part + 1
            if next_part < num_parts:
                tables.append(PageBreak())
            if next_part % num_horz_parts == 0:
                startRow += num_rows - 1 # Don't include the heading

        # Return a list of table objects
        return tables

    # -------------------------------------------------------------------------
    def split(self, temp_doc):
        """
            Helper for calc(): split the table horizontally so that each
            part fits into the page width

            @param temp_doc: the temporary doc

            @returns: the data slices for each part
        """

        col_widths = self.col_widths[0]
        row_heights = self.row_heights[0]

        # Split columns
        total = 0
        split_cols = []
        new_col_widths = []
        part_col_widths = []

        for i, col_width in enumerate(col_widths):
            if i > 0 and total + col_width > temp_doc.printable_width:
                # Split before this column...
                split_cols.append(i)
                new_col_widths.append(part_col_widths)
                # ...and start a new part
                part_col_widths = [col_width]
                total = col_width
            else:
                # Append this column to the current part
                part_col_widths.append(col_width)
                total += col_width

        split_cols.append(len(col_widths))
        new_col_widths.append(part_col_widths)
        self.col_widths = new_col_widths

        # Split rows
        total = 0
        split_rows = []
        new_row_heights = []
        page_row_heights = []

        body_height = self.body_height
        header_height = 20 # default
        for i, row_height in enumerate(row_heights):

            # Remember the actual header height
            if i == 0:
                header_height = row_height

            if total + row_height > body_height:
                # Split before this row
                new_row_heights.append(page_row_heights)
                # ...and start a new page
                page_row_heights = [header_height, row_height] if i > 0 else [row_height]
                total = sum(page_row_heights)
                split_rows.append(i)
            else:
                page_row_heights.append(row_height)
                total += row_height

        split_rows.append(len(row_heights))
        new_row_heights.append(page_row_heights)
        self.row_heights = new_row_heights

        # Split the data into slices (parts)
        pdf_data = self.pdf_data
        all_labels = self.labels
        subheading_rows = self.subheading_rows
        parts = []

        start_row = 1 # skip labels => generating new partial label-rows
        for end_row in split_rows:

            start_col = 0

            for end_col in split_cols:

                part = []
                pappend = part.append

                # Add the labels-row to the part
                labels = []
                lappend = labels.append
                for col_index in range(start_col, end_col):
                    try:
                        lappend(all_labels[col_index])
                    except IndexError:
                        lappend("")
                pappend(labels)

                # Add all other rows
                for row_index in range(start_row, end_row):

                    row_data = pdf_data[row_index]

                    out_row = []
                    oappend = out_row.append

                    for col_index in range(start_col, end_col):
                        try:
                            oappend(row_data[col_index])
                        except IndexError:
                            # If this is the first column of a subheading row then
                            # repeat the subheading:
                            if len(out_row) == 0 and row_index in subheading_rows:
                                try:
                                    oappend(row_data[0])
                                except IndexError:
                                    oappend("")
                            else:
                                oappend("")

                    pappend(out_row)

                parts.append(part)
                start_col = end_col
            start_row = end_row

        return parts

    # -------------------------------------------------------------------------
    def table_style(self, startRow, rowCnt, endCol, colour_required=False):
        """
            Internally used method to assign a style to the table

            @param startRow: The row from the data that the first data row in
            the table refers to. When a table is split the first row in the
            table (ignoring the label header row) will not always be the first row
            in the data. This is needed to align the two. Currently this parameter
            is used to identify sub headings and give them an emphasised styling
            @param rowCnt: The number of rows in the table
            @param endCol: The last column in the table

            FIXME: replace endCol with -1
                   (should work but need to test with a split table)

            FIXME: naming conventions!
        """

        font_name_bold = self.font_name_bold

        style = [("FONTNAME", (0, 0), (-1, -1), self.font_name),
                 ("FONTSIZE", (0, 0), (-1, -1), self.fontsize),
                 ("VALIGN", (0, 0), (-1, -1), "TOP"),
                 ("LINEBELOW", (0, 0), (endCol, 0), 1, Color(0, 0, 0)),
                 ("FONTNAME", (0, 0), (endCol, 0), font_name_bold),
                 ]
        sappend = style.append
        if colour_required:
            sappend(("BACKGROUND", (0, 0), (endCol, 0), self.header_color))
        else:
            sappend(("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey))
            sappend(("INNERGRID", (0, 0), (-1, -1), 0.2, colors.lightgrey))
        if self.groupby != None:
            sappend(("LEFTPADDING", (0, 0), (-1, -1), 20))

        rowColourCnt = 0 # used to alternate the colours correctly when we have subheadings
        for i in range(rowCnt):
            # If subheading
            if startRow + i in self.subheading_rows:
                level = self.subheading_level[startRow + i]
                if colour_required:
                    sappend(("BACKGROUND", (0, i), (endCol, i),
                             self.header_color))
                sappend(("FONTNAME", (0, i), (endCol, i), font_name_bold))
                sappend(("SPAN", (0, i), (endCol, i)))
                sappend(("LEFTPADDING", (0, i), (endCol, i), 6 * level))
            elif i > 0:
                if colour_required:
                    if rowColourCnt % 2 == 0:
                        sappend(("BACKGROUND", (0, i), (endCol, i),
                                 self.even_color))
                        rowColourCnt += 1
                    else:
                        sappend(("BACKGROUND", (0, i), (endCol, i),
                                 self.odd_color))
                        rowColourCnt += 1
        sappend(("BOX", (0, 0), (-1, -1), 1, Color(0, 0, 0)))
        return style

# =============================================================================
class S3html2pdf():
    """
        Class that takes HTML in the form of web2py helper objects
        and converts it to PDF
    """

    def __init__(self,
                 pageWidth,
                 exclude_class_list=None,
                 styles=None):
        """
            Constructor

            @param pageWidth: the printable width
            @param exclude_class_list: list of classes for elements to skip
            @param styles: the styles dict from the caller
        """

        # Fonts
        self.font_name = None
        self.font_name_bold = None
        set_fonts(self)

        if exclude_class_list is None:
            self.exclude_class_list = []
        else:
            self.exclude_class_list = exclude_class_list

        self.pageWidth = pageWidth
        self.fontsize = 10

        # Standard styles
        styleSheet = getSampleStyleSheet()

        self.plainstyle = styleSheet["Normal"]
        self.plainstyle.fontName = self.font_name
        self.plainstyle.fontSize = 9

        self.boldstyle = deepcopy(styleSheet["Normal"])
        self.boldstyle.fontName = self.font_name_bold
        self.boldstyle.fontSize = 10

        self.titlestyle = deepcopy(styleSheet["Normal"])
        self.titlestyle.fontName = self.font_name_bold
        self.titlestyle.fontSize = 16

        self.normalstyle = self.plainstyle

        # To add more PDF styles define the style above (just like the titlestyle)
        # Then add the style and the name to the lookup dict below
        # These can then be added to the html in the code as follows:
        # TD("Waybill", _class="pdf_title")
        self.style_lookup = {"pdf_title": self.titlestyle,
                             }

        # Additional styles from the caller
        self.styles = styles

    # -------------------------------------------------------------------------
    def parse(self, html):
        """
            Entry point for class
        """

        result = self.select_tag(html)
        return result

    # -------------------------------------------------------------------------
    def select_tag(self, html, title=False):
        """
        """

        if self.exclude_tag(html):
            return None
        if isinstance(html, TABLE):
            return self.parse_table(html)
        elif isinstance(html, A):
            return self.parse_a(html)
        elif isinstance(html, (P, H1, H2, H3, H4, H5, H6)):
            return self.parse_p(html)
        elif isinstance(html, IMG):
            return S3html2pdf.parse_img(html)
        elif isinstance(html, DIV):
            return self.parse_div(html)
        elif (isinstance(html, basestring) or isinstance(html, lazyT)):
            html = s3_str(html)
            if "<" in html:
                html = s3_strip_markup(html)
            if title:
                para = [Paragraph(biDiText(html), self.boldstyle)]
            else:
                para = [Paragraph(biDiText(html), self.normalstyle)]
            self.normalstyle = self.plainstyle
            return para
        return None

    # -------------------------------------------------------------------------
    def exclude_tag(self, html):
        """
        """

        try:
            if html.attributes["_class"] in self.exclude_class_list:
                return True
            if html.attributes["_class"] in self.style_lookup:
                self.normalstyle = self.style_lookup[html.attributes["_class"]]
        except:
            pass
        return False

    # -------------------------------------------------------------------------
    def parse_div(self, html):
        """
            Parses a DIV element and converts it into a format for ReportLab

            @param html: the DIV element  to convert
            @return: a list containing text that ReportLab can use
        """

        content = []
        select_tag = self.select_tag
        for component in html.components:
            result = select_tag(component)
            if result != None:
                content += result
        if content == []:
            return None
        return content

    # -------------------------------------------------------------------------
    def parse_a(self, html):
        """
            Parses an A element and converts it into a format for ReportLab

            @param html: the A element  to convert
            @return: a list containing text that ReportLab can use
        """

        content = []
        select_tag = self.select_tag
        for component in html.components:
            result = select_tag(component)
            if result != None:
                content += result
        if content == []:
            return None
        return content

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_img(html, uploadfolder=None):
        """
            Parses an IMG element and converts it into an Image for ReportLab

            @param html: the IMG element  to convert
            @param uploadfolder: an optional uploadfolder in which to find the file
            @return: a list containing an Image that ReportLab can use


            @note: The `src` attribute of the image must either
            point to a static resource, directly to a file, or to an upload.
        """

        I = None
        src = html.attributes.get("_src")
        if src:
            if uploadfolder:
                # Assume that src is a filename directly off the uploadfolder
                src = src.rsplit("/", 1) # Don't use os.sep here
                src = os.path.join(uploadfolder, src[1])
            else:
                request = current.request
                base_url = "/%s/" % request.application
                STATIC = "%sstatic" % base_url
                if src.startswith(STATIC):
                    # Assume that filename is specified as a URL in static
                    src = src.split(base_url)[-1]
                    src = src.replace("/", os.sep)
                    src = os.path.join(request.folder, src)
                else:
                    # Assume that filename is in root of main uploads folder
                    # @ToDo: Allow use of subfolders!
                    src = src.rsplit("/", 1) # Don't use os.sep here
                    src = os.path.join(request.folder,
                                       "uploads", src[1])
            if os.path.exists(src):
                from reportlab.platypus import Image
                I = Image(src)

        if not I:
            return None

        iwidth = I.drawWidth
        iheight = I.drawHeight

        # Assuming 96dpi original resolution
        resolution = 96
        if "_height" in html.attributes:
            height = int(html.attributes["_height"]) * inch / resolution
            width = iwidth * (height / iheight)
        elif "_width" in html.attributes:
            width = int(html.attributes["_width"]) * inch / resolution
            height = iheight * (width / iwidth)
        else:
            height = 1.0 * inch
            width = iwidth * (height / iheight)

        I.drawHeight = height
        I.drawWidth = width
        return [I]

    # -------------------------------------------------------------------------
    def parse_p(self, html):
        """
            Parses a P element and converts it into a format for ReportLab

            @param html: the P element  to convert
            @return: a list containing text that ReportLab can use
        """

        font_sizes = {"p": 9,
                      "h1": 18,
                      "h2": 16,
                      "h3": 14,
                      "h4": 12,
                      "h5": 10,
                      "h6": 9,
                      }

        font_size = None
        title = False
        try:
            tag = html.tag
        except AttributeError:
            pass
        else:
            font_size = font_sizes.get(tag)
            title = tag != "p"
        style = self.boldstyle if title else self.normalstyle

        if font_size:
            default_font_size = style.fontSize
            style.fontSize = font_size
            style.spaceAfter = 8

        content = []
        select_tag = self.select_tag
        for component in html.components:
            result = select_tag(component, title=title)
            if result != None:
                content += result

        if font_size:
            style.fontSize = default_font_size

        if content == []:
            return None
        return content

    # -------------------------------------------------------------------------
    def parse_table(self, html):
        """
            Parses a TABLE element and converts it into a format for ReportLab

            @param html: the TABLE element  to convert
            @return: a list containing text that ReportLab can use
        """

        table_classes = (html["_class"] or "").split()

        style = [("FONTSIZE", (0, 0), (-1, -1), self.fontsize),
                 ("VALIGN", (0, 0), (-1, -1), "TOP"),
                 ("FONTNAME", (0, 0), (-1, -1), self.font_name),
                 ]
        if "no-grid" not in table_classes:
            style.append(("GRID", (0, 0), (-1, -1), 0.5, colors.grey))

        content = self.parse_table_components(html,
                                              style = style,
                                              )[0]

        if content == []:
            return None

        table = Table(content,
                      style = style,
                      hAlign = "LEFT",
                      vAlign = "Top",
                      repeatRows = 1 if "repeat-header" in table_classes else 0,
                      )

        if "shrink-to-fit" in table_classes:
            # Calculate column widths
            table.wrap(self.pageWidth, 0)

            cw = table._colWidths
            tw = sum(cw)
            pw = self.pageWidth

            if tw and tw > pw:
                # Table overflows => adjust column widths proportionally
                factor = pw / tw
                cw = [w * factor for w in cw]

                # Re-instantiate with colWidths
                table = Table(content,
                              style = style,
                              hAlign = "LEFT",
                              vAlign = "Top",
                              repeatRows = 1 if "repeat-header" in table_classes else 0,
                              colWidths = cw
                              )

        return [table]

    # -------------------------------------------------------------------------
    def parse_table_components(self,
                               table,
                               content=None,
                               row_count=0,
                               style=None):
        """
            Parses TABLE components

            @param table: the TABLE instance or a subcomponent of it
            @param content: the current content array
            @param row_count: the current number of rows in the content array
            @param style: the style list
        """

        if content is None:
            content = []
        cappend = content.append

        rowspans = []

        exclude_tag = self.exclude_tag
        parse_tr = self.parse_tr
        parse = self.parse_table_components

        for component in table.components:
            result = None

            if exclude_tag(component):
                continue

            if isinstance(component, (THEAD, TBODY, TFOOT)):
                content, row_count = parse(component,
                                           content = content,
                                           row_count = row_count,
                                           style = style,
                                           )

            elif isinstance(component, TR):
                result = parse_tr(component, style, row_count, rowspans)
                row_count += 1

            if result != None:
                cappend(result)

        return content, row_count

    # -------------------------------------------------------------------------
    def parse_tr(self, html, style, rowCnt, rowspans):
        """
            Parses a TR element and converts it into a format for ReportLab

            @param html: the TR element  to convert
            @param style: the default style
            @param rowCnt: the row counter
            @param rowspans: the remaining rowspans (if any)

            @return: a list containing text that ReportLab can use
        """

        # Identify custom styles
        row_styles = self._styles(html)

        background = self._color(row_styles.get("background-color"))
        color = self._color(row_styles.get("color"))

        row = []
        rappend = row.append
        sappend = style.append

        select_tag = self.select_tag
        font_name_bold = self.font_name_bold

        exclude_tag = self.exclude_tag

        colCnt = 0
        rspan_index = -1
        for component in html.components:

            if not isinstance(component, (TH, TD)) or \
               exclude_tag(component):
                continue

            rspan_index += 1

            if len(rowspans) < (rspan_index + 1):
                rowspans.append(0)

            if rowspans[rspan_index]:
                rappend("")
                rowspans[rspan_index] -= 1
                cell = (colCnt, rowCnt)
                sappend(("LINEABOVE", cell, cell, 0, colors.white))
                colCnt += 1

            if component.components == []:
                rappend("")
                continue

            rowspan = component.attributes.get("_rowspan")
            if rowspan:
                # @ToDo: Centre the text across the rows
                rowspans[rspan_index] = rowspan - 1

            colspan = component.attributes.get("_colspan", 1)
            for detail in component.components:
                if color:
                    self.normalstyle.textColor = color
                else:
                    # Reset to black
                    self.normalstyle.textColor = colors.black

                # Render cell content
                result = select_tag(detail, title=isinstance(component, TH))
                if result is None:
                    continue
                rappend(result)

                # Add cell styles
                cell = (colCnt, rowCnt)
                if color:
                    sappend(("TEXTCOLOR", cell, cell, color))
                if background:
                    sappend(("BACKGROUND", cell, cell, background))
                elif isinstance(component, TH):
                    sappend(("BACKGROUND", cell, cell, colors.lightgrey))
                    sappend(("FONTNAME", cell, cell, font_name_bold))

                # Column span
                if colspan > 1:
                    for i in xrange(1, colspan):
                        rappend("")
                    sappend(("SPAN", cell, (colCnt + colspan - 1, rowCnt)))
                    colCnt += colspan
                else:
                    colCnt += 1

        if row == []:
            return None
        else:
            return row

    # -------------------------------------------------------------------------
    def _styles(self, element):
        """
            Get the custom styles for the given element (match by tag and
            classes)

            @param element: the HTML element (web2py helper)
            @param styles: the pdf_html_styles dict
        """

        element_styles = {}

        styles = self.styles
        if styles:

            classes = element["_class"]
            if classes:
                tag = element.tag
                classes = set(classes.split(" "))
                for k, v in styles.items():
                    t, c = k.split(".", 1)
                    if t != tag:
                        continue
                    keys = set(c.split("."))
                    if keys <= classes:
                        element_styles.update(v)

        return element_styles

    # -------------------------------------------------------------------------
    @staticmethod
    def _color(val):
        """
            Get the Color instance from colors for:
              a given name (e.g. 'white')
                or
              Hex string (e.g. '#FFFFFF')

            @param val: the name or hex string
        """

        if not val:
            color = None
        else:
            if val[:1] == '#':
                color = HexColor(val)
            else:
                try:
                    color = object.__getattribute__(colors, val)
                except AttributeError:
                    color = None
        return color

# END =========================================================================
