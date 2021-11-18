# -*- coding: utf-8 -*-

"""
    S3 Adobe PDF codec

    @copyright: 2011-2021 (c) Sahana Software Foundation
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

import os
import unicodedata

from copy import deepcopy
from io import BytesIO
from urllib.parse import unquote

from gluon import current, redirect, URL, \
                  A, B, DIV, H1, H2, H3, H4, H5, H6, I, IMG, P, \
                  TABLE, TBODY, TD, TFOOT, TH, THEAD, TR
from gluon.storage import Storage
from gluon.contenttype import contenttype
from gluon.languages import lazyT

from ..s3codec import S3Codec
from ..s3utils import s3_strip_markup, s3_str

try:
    from reportlab.graphics.shapes import Drawing, Line
    from reportlab.lib import colors
    from reportlab.lib.colors import Color, HexColor
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT#, TA_JUSTIFY
    from reportlab.lib.pagesizes import A4, LETTER, landscape, portrait
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas
    from reportlab.platypus import BaseDocTemplate, \
                                   KeepTogether, \
                                   PageBreak, \
                                   PageTemplate, \
                                   Paragraph, \
                                   Spacer, \
                                   Table
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
    biDiImported = True
except ImportError:
    biDiImported = False
    current.log.warning("PDF Codec", "BiDirectional Support not available: Install python-bidi")

try:
    import arabic_reshaper
    reshaperImported = True
except ImportError:
    reshaperImported = False
    current.log.warning("PDF Codec", "Arabic Reshaper not available: Install arabic_reshaper")

PDF_WIDTH = 0
PDF_HEIGHT = 1

# -----------------------------------------------------------------------------
def set_fonts(instance):
    """
        DRY Helper function for all classes which use PDF to set the appropriate Fonts
    """

    font_set = current.deployment_settings.get_pdf_export_font()
    if font_set:
        if isinstance(font_set, tuple):
            font_name = font_set[0]
            font_name_bold = font_set[1]
            #font_name_italic = font_set[2]
            try:
                folder = current.request.folder
                os_path_join = os.path.join
                registerFont = pdfmetrics.registerFont
                # Requires the font-files at /static/fonts/<font_name>.ttf
                registerFont(TTFont(font_name, os_path_join(folder,
                                                            "static",
                                                            "fonts",
                                                            "%s.ttf" % font_name,
                                                            )))
                registerFont(TTFont(font_name_bold, os_path_join(folder,
                                                                 "static",
                                                                 "fonts",
                                                                 "%s.ttf" % font_name_bold,
                                                                 )))
                #registerFont(TTFont(font_name_italic, os_path_join(folder,
                #                                                   "static",
                #                                                   "fonts",
                #                                                   "%s.ttf" % font_name_italic,
                #                                                   )))
            except:
                current.log.error("%s Font not found: Please install it to see the correct fonts in PDF exports" % font_name)
            else:
                instance.font_name = font_name
                instance.font_name_bold = font_name_bold
                #instance.font_name_italic = font_name_italic
                #instance.font_name_bold_italic = font_name_bold_italic
                # @ToDo: To have B & I tags work with non-built-in fonts, need to form a family:
                #from reportlab.lib.fonts import addMapping
                #addMapping(font_name, 0, 0, font_name)
                #addMapping(font_name, 0, 1, font_name_italic)
                #addMapping(font_name, 1, 0, font_name_bold)
                #addMapping(font_name, 1, 1, font_name_bold_italic)
                return
        else:
            # e.g. Unifont
            try:
                # Requires the font-file at /static/fonts/<font_name>.ttf
                pdfmetrics.registerFont(TTFont(font_name, os.path.join(current.request.folder,
                                                                       "static",
                                                                       "fonts",
                                                                       "%s.ttf" % font_set,
                                                                       )))
            except:
                current.log.error("%s Font not found: Please install it to see the correct fonts in PDF exports" % font_set)
            else:
                instance.font_name = font_set
                instance.font_name_bold = font_set
                #instance.font_name_italic = font_set
                #instance.font_name_bold_italic = font_set
                return

    # Use the default "Helvetica"
    instance.font_name = "Helvetica"
    instance.font_name_bold = "Helvetica-Bold"
    #instance.font_name_italic = "Helvetica-Oblique"
    #instance.font_name_bold_italic = "Helvetica-BoldOblique"

# -----------------------------------------------------------------------------
def biDiText(text):
    """
        Ensure that RTL text is rendered RTL & also that Arabic text is
        rewritten to use the joined format.
    """

    text = s3_str(text)

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

        if isArabic and reshaperImported:
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

        # Set Fonts
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
        """

        if not reportLabImported:
            current.session.error = self.ERROR.RL_ERROR
            redirect(URL(extension=""))

        # Settings
        attr_get = attr.get
        r = self.r = attr_get("request", None)

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
                title = title.decode("utf-8")
            filename = "%s_%s.pdf" % (title, now)
        elif len(filename) < 5 or filename[-4:] != ".pdf":
            # Add extension
            filename = "%s.pdf" % filename
        #self.filename = filename

        # Get the Doc Template
        size = attr_get("pdf_size")
        orientation = attr_get("pdf_orientation")
        if not orientation:
            orientation = current.deployment_settings.get_pdf_orientation()
        doc = EdenDocTemplate(title = docTitle,
                              size = size,
                              orientation = orientation,
                              )
        printable_width = doc.printable_width

        # HTML styles
        pdf_html_styles = attr_get("pdf_html_styles")

        # Get the header
        header = attr_get("pdf_header")
        if not header:
            header = attr_get("rheader")
        if header:
            header_flowable = self.get_html_flowable(header,
                                                     printable_width,
                                                     styles = pdf_html_styles,
                                                     )
            if header_flowable:
                pdf_header_padding = attr_get("pdf_header_padding", 6)
                if pdf_header_padding:
                    header_flowable.append(Spacer(1, pdf_header_padding))
        else:
            header_flowable = None

        # Get the footer
        footer = attr_get("pdf_footer")
        if not footer:
            footer = attr_get("rfooter")
        if footer:
            footer_flowable = self.get_html_flowable(footer,
                                                     printable_width,
                                                     styles = pdf_html_styles,
                                                     )
            if footer_flowable:
                pdf_footer_padding = attr_get("pdf_footer_padding", 3)
                if pdf_footer_padding:
                    footer_flowable.append(Spacer(1, pdf_footer_padding))
        else:
            footer_flowable = None

        # Build report template

        # Get data for the body of the text
        body_flowable = None

        callback = attr_get("pdf_callback")
        if callback:
            # Get the document body from the callback
            body_flowable = self.get_html_flowable(callback(r),
                                                   printable_width,
                                                   styles = pdf_html_styles,
                                                   )

        else:
            self.list_fields = attr_get("list_fields")
            self.pdf_groupby = attr_get("pdf_groupby")
            # Not actioned currently:
            #self.pdf_orderby = attr_get("pdf_orderby")
            self.pdf_hide_comments = attr_get("pdf_hide_comments")
            self.table_autogrow = attr_get("pdf_table_autogrow")
            pdf_componentname = attr_get("pdf_componentname", None)
            if pdf_componentname: # and resource.parent is None:
                # Enforce a particular component
                resource = current.s3db.resource(r.tablename,
                                                 components = [pdf_componentname],
                                                 id = r.id,
                                                 )
                component = resource.components.get(pdf_componentname)
                if component:
                    # Calculate the body_height
                    doc.calc_body_size(header_flowable, footer_flowable)
                    body_flowable = self.get_resource_flowable(component, doc)

            elif r.component or attr_get("method", "list") != "read":
                # Use the requested resource
                # Calculate the body_height
                doc.calc_body_size(header_flowable, footer_flowable)
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
                  canvasmaker = S3NumberedCanvas,
                  )

        # Return the generated PDF
        response = current.response
        if response:
            if "uwsgi_scheme" in current.request.env:
                # Running uwsgi then we can't have unicode filenames
                #if isinstance(filename, str):
                #    filename = filename.encode("utf-8")
                # Accent Folding
                def string_escape(s):
                    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("utf-8")
                filename = string_escape(filename)
            disposition = 'attachment; filename="%s"' % filename
            response.headers["Content-Type"] = contenttype(".pdf")
            response.headers["Content-disposition"] = disposition

        return doc.output.getvalue()

    # -------------------------------------------------------------------------
    def get_html_flowable(self,
                          rules,
                          printable_width,
                          styles = None,
                          ):
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

        parser = S3html2pdf(page_width = printable_width,
                            exclude_class_list = ["tabs"], # rheader
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
            list_fields = resource.list_fields("pdf_fields", id_column=False)
            if self.pdf_hide_comments:
                list_fields = [f for f in list_fields if f != "comments"]

        get_vars = Storage(current.request.get_vars)
        get_vars["iColumns"] = len(list_fields)
        dtfilter, orderby, left = resource.datatable_filter(list_fields, get_vars)
        resource.add_filter(dtfilter)

        # Should we limit the number of rows in the export?
        max_rows = current.deployment_settings.get_pdf_max_rows()
        limit, count = (max_rows, True) if max_rows else (None, False)

        result = resource.select(list_fields,
                                 count = count,
                                 left = left,
                                 limit = limit,
                                 orderby = orderby,
                                 represent = True,
                                 show_links = False,
                                 )
        totalrows = result.numrows if count else None

        if resource.get_config("pdf_format") == "list":
            # Export as data list
            output = S3PDFList(doc,
                               result.rfields,
                               result.rows,
                               totalrows = totalrows,
                               ).build()
        else:
            # Export as data table
            output = S3PDFTable(doc,
                                result.rfields,
                                result.rows,
                                groupby = self.pdf_groupby,
                                autogrow = self.table_autogrow,
                                totalrows = totalrows,
                                ).build()
        return output

# =============================================================================
class EdenDocTemplate(BaseDocTemplate):
    """
        The standard document template for eden reports
        It allows for the following page templates:
        1) First Page
        2) Even Page (tbc)
        3) Odd Page (tbc)
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

        self.output = BytesIO()

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

        # BaseDocTemplate.__init__ calls our custom _calc()
        self.insideMargin = margin_inside

        BaseDocTemplate.__init__(self,
                                 self.output,
                                 title = s3_str(title),
                                 leftMargin = margin[1],
                                 rightMargin = margin[3],
                                 topMargin = margin[0],
                                 bottomMargin = margin[2],
                                 )

        self.MINIMUM_MARGIN_SIZE = 0.2 * inch
        self.body_flowable = None

        # Called by BaseDocTemplate.__init__
        #self._calc()

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
        printable_width = self.printable_width
        printable_height = self.printable_height
        for f in flowable:
            if f:
                size = f.wrap(printable_width,
                              printable_height)
                if size[PDF_WIDTH] > w:
                    w = size[PDF_WIDTH]
                h += size[PDF_HEIGHT]
        return (w, h)

    # -------------------------------------------------------------------------
    def _calc(self):

        if self.page_orientation == "Landscape":
            self.pagesize = pagesize = landscape(self.paper_size)
        else:
            self.pagesize = pagesize = portrait(self.paper_size)

        BaseDocTemplate._calc(self)

        self.height = height = pagesize[PDF_HEIGHT]
        self.width = width = pagesize[PDF_WIDTH]
        self.printable_width = width - \
                               self.leftMargin - \
                               self.rightMargin - \
                               self.insideMargin
        self.printable_height = height - \
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
        get_flowable_size = self.get_flowable_size
        header_size = get_flowable_size(header_flowable)
        footer_size = get_flowable_size(footer_flowable)
        self.header_height = header_height = header_size[PDF_HEIGHT]
        self.footer_height = footer_height = footer_size[PDF_HEIGHT]
        self.body_height = self.printable_height - \
                           header_height - \
                           footer_height

    # -------------------------------------------------------------------------
    def build(self,
              header_flowable,
              body_flowable,
              footer_flowable,
              canvasmaker = canvas.Canvas,
              ):
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

        #self.body_frame = body_frame
        if self.page_orientation == "Landscape":
            landscapePage = PageTemplate(id = "Landscape",
                                         frames = [body_frame,],
                                         onPage = self.add_page_decorators,
                                         pagesize = landscape(self.pagesize)
                                         )
            self.addPageTemplates(landscapePage)
        else:
            normalPage = PageTemplate(id = "Normal",
                                      frames = [body_frame,],
                                      onPage = self.add_page_decorators,
                                      pagesize = self.pagesize
                                      )
            self.addPageTemplates(normalPage)
            # @todo set these page templates up
            #evenPage = PageTemplate(id = "even",
            #                        frames = frame_list,
            #                        onPage = self.onEvenPage,
            #                        pagesize = self.pagesize
            #                        )
            #oddPage = PageTemplate(id = "odd",
            #                       frames = frame_list,
            #                       onPage = self.onOddPage,
            #                       pagesize = self.pagesize
            #                       )

        BaseDocTemplate.build(self,
                              body_flowable,
                              canvasmaker = canvasmaker,
                              )

    # -------------------------------------------------------------------------
    def add_page_decorators(self, canvas, doc):
        """
        """

        get_flowable_size = self.get_flowable_size
        leftMargin = self.leftMargin

        header_flowable = self.header_flowable
        if header_flowable:
            top = self.bottomMargin + self.printable_height
            for flow in header_flowable:
                height = get_flowable_size(flow)[PDF_HEIGHT]
                bottom = top - height
                flow.drawOn(canvas,
                            leftMargin,
                            bottom
                           )
                top = bottom

        footer_flowable = self.footer_flowable
        if footer_flowable:
            top = self.bottomMargin + self.footer_height
            for flow in footer_flowable:
                height = get_flowable_size(flow)[PDF_HEIGHT]
                bottom = top - height
                flow.drawOn(canvas,
                            leftMargin,
                            bottom
                           )
                top = bottom

    # -------------------------------------------------------------------------
    def addParagraph(self,
                     text,
                     style = None,
                     append = True,
                     ):
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
class S3PDFList:
    """ Export resource data as list-style report """

    def __init__(self,
                 document,
                 rfields,
                 rows,
                 totalrows = None,
                 ):
        """
            Constructor

            @param document: the DocTemplate
            @param rfields: the S3ResourceFields (for labels and order)
            @param rows: the data (S3ResourceData.rows)
            @param totalrows: total number of rows matching the filter
        """

        self.document = document

        self.rfields = rfields
        self.rows = rows

        self.numrows = len(rows)
        self.totalrows = totalrows

        # Set fonts
        set_fonts(self)

        self.styles = self.get_styles()

    # -------------------------------------------------------------------------
    def build(self):
        """
            Build the list

            @returns: list of Flowables
        """

        flowables = []

        document = self.document
        try:
            printable_width = document.printable_width
        except AttributeError:
            printable_width = document.width

        rfields = self.rfields
        formatted = self.formatted
        for index, row in enumerate(self.rows):

            # Insert a horizontal line between records
            ruler = Drawing(printable_width, 6)
            ruler.add(Line(0, 6, printable_width, 6,
                           strokeColor = colors.grey,
                           strokeWidth = 0.5,
                           ))

            item = [ruler]
            for rfield in rfields:
                item.extend(formatted(rfield, row[rfield.colname]))
            if index == 0:
                flowables.extend(item)
            else:
                flowables.append(KeepTogether(item))

        # Hint for too many records
        totalrows = self.totalrows
        numrows = self.numrows
        if totalrows and totalrows > numrows:
            hint = current.T("Too many records - %(number)s more records not included") % \
                                {"number": totalrows - numrows}
            flowables.append(PageBreak())
            flowables.append(Paragraph(s3_str(hint), self.styles["warning"]))

        return flowables

    # -------------------------------------------------------------------------
    def formatted(self, rfield, value):
        """
            Format a field value with label

            @returns: a list of Flowables
        """

        label = biDiText(rfield.label)

        inline = self.styles["inline"]
        indented = self.styles["indented"]

        if isinstance(value, (str, lazyT)):
            v = biDiText(value)
            if "\n" in v:
                flowables = [Paragraph("<b>%s:</b>" % label, inline),
                             Paragraph(v.replace("\n", "<br/>"), indented),
                             ]
            else:
                # Convert to paragraph with inline label
                flowables = [Paragraph("<b>%s:</b> %s" % (label, biDiText(value)), inline),
                             ]
        else:
            flowables = self.format_value(rfield, value)
            label_paragraph = Paragraph("<b>%s:</b>" % label, inline)
            if isinstance(flowables, list):
                flowables.insert(0, label_paragraph)
                flowables.append(Spacer(1, 6))
            else:
                flowables = [label_paragraph,
                             Paragraph(s3_str(flowables).replace("\n", "<br/>"), indented),
                             ]

        # Return list of flowables
        return flowables

    # -------------------------------------------------------------------------
    def format_value(self, rfield, value):
        """
            Convert represented field value into suitable ReportLab elements

            @param rfield: the S3ResourceField
            @param value: the field value

            @returns: a BiDi-converted unicode string, or a list of Flowables
        """

        if isinstance(value, (str, lazyT)):
            formatted = biDiText(value)

        elif isinstance(value, IMG):
            field = rfield.field
            if field:
                formatted = S3html2pdf.parse_img(value, field.uploadfolder)
                if formatted:
                    formatted = formatted[:1]
            else:
                formatted = []

        elif isinstance(value, DIV):
            is_header = isinstance(value, (H1, H2, H3, H4, H5, H6))
            is_block = is_header or isinstance(value, (P, DIV))

            # Paragraph Style
            style = self.styles["indented_bold"] \
                    if is_header else self.styles["indented"]

            num_components = len(value.components)

            if num_components == 1:
                # Simple tag => convert to string
                formatted = self.format_value(rfield, value.components[0])

                # Wrap in paragraph if string contains newlines or component is
                # a block-element, preserving newlines and setting font weight
                if isinstance(formatted, str) and (is_block or "\n" in formatted):
                    formatted = [Paragraph(formatted.replace("\n", "<br/>"), style)]
                elif not isinstance(formatted, list):
                    formatted = [formatted]

            elif num_components > 0:
                # Complex tag => convert to list of paragraphs
                # @todo: support bulleted lists and tables in represents
                formatted = []

                def add_paragraph(text):
                    # Wrap text in Paragraph to preserve newlines and set font weight
                    para = Paragraph(biDiText(text).replace("\n", "<br/>"), style)
                    formatted.append(para)

                text = ""
                for component in value.components:
                    if isinstance(component, str):
                        # Concatenate consecutive strings
                        text = "".join((text, component))
                    else:
                        # Convert component
                        sub = self.format_value(rfield, component)
                        if isinstance(sub, str):
                            text = "".join((text, sub))
                            continue
                        elif text:
                            add_paragraph(text)
                            text = ""
                        if isinstance(sub, list):
                            formatted.extend(sub)
                        else:
                            formatted.append(sub)
                if text:
                    add_paragraph(text)
            else:
                # Empty tag => empty string
                formatted = ""
        else:
            formatted = biDiText(value)

        return formatted

    # -------------------------------------------------------------------------
    def get_styles(self):
        """
            Get the paragraph styles used in this layout

            @returns: dict of paragraph styles
        """

        styles = {}

        styles["inline"] = style_inline = getSampleStyleSheet()["Normal"]
        style_inline.spaceAfter = 6
        style_inline.fontName = self.font_name

        styles["indented"] = style_indented = getSampleStyleSheet()["Normal"]
        style_indented.leftIndent = style_indented.rightIndent = 12
        style_indented.spaceAfter = 6
        style_indented.fontName = self.font_name

        styles["indented_bold"] = style_indented_bold = getSampleStyleSheet()["Normal"]
        style_indented_bold.leftIndent = style_indented_bold.rightIndent = 12
        style_indented_bold.spaceAfter = 6
        style_indented_bold.fontName = self.font_name_bold

        styles["warning"] = style_warning = getSampleStyleSheet()["Normal"]
        style_warning.textColor = colors.red
        style_warning.fontSize = 12

        return styles

# =============================================================================
class S3PDFTable:
    """
        Class to build a table that can then be placed in a pdf document
        The table will be formatted so that it fits on the page.

        Called by get_resource_flowable()
    """

    MIN_COL_WIDTH = 200
    MIN_ROW_HEIGHT = 20

    def __init__(self,
                 document,
                 rfields,
                 rows,
                 groupby = None,
                 autogrow = False,
                 totalrows = None,
                 ):
        """
            Constructor

            @param document: the EdenDocTemplate instance in which the table
                             shall be rendered
            @param rfields: list of resolved field selectors for
                            the columns (S3ResourceData.rfields)
            @param rows: the represented rows (S3ResourceData.rows)
            @param groupby: a field name that is to be used as a sub-group
                            - all records with the same value in that the
                              groupby column will be clustered together
            @param autogrow: what to do about empty space on the page:
                             "H" - make columns wider to fill horizontally
                             "V" - add extra (empty) rows to fill vertically
                             "B" - do both
                             False - do nothing
            @param totalrows: total number of rows matching the filter
        """

        rtl = current.response.s3.rtl

        # The main document
        self.doc = document

        # Parameters for rendering
        self.body_height = document.body_height
        self.autogrow = autogrow

        # Set fonts
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

        self.totalrows = totalrows
        self.numrows = len(rows)

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
    def convert(self, rfield, value):
        """
            Convert represented field value into a suitable
            ReportLab element

            @param rfield: the S3ResourceField
            @param value: the field value
        """

        if isinstance(value, (str, lazyT)):

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

            num_components = len(value.components)

            # Paragraph style
            if isinstance(value, (H1, H2, H3, H4, H5, H6)):
                font = self.font_name_bold
            else:
                font = self.font_name
            stylesheet = getSampleStyleSheet()
            para_style = stylesheet["Normal"]
            para_style.fontName = font

            if num_components == 1:
                # Simple tag => convert to string
                pdf_value = self.convert(rfield, value.components[0])

                # Wrap in paragraph if string contains newlines or component is
                # a block-element, preserving newlines and setting font weight
                is_block = lambda e: isinstance(e, DIV) and \
                                     e.tag in ("h6", "h5", "h4", "h3", "h2", "h1", "p", "div")
                if isinstance(pdf_value, str) and \
                   (is_block(value) or "\n" in pdf_value):
                    pdf_value = Paragraph(pdf_value.replace("\n", "<br/>"), para_style)

            elif num_components > 0:
                # Complex tag => convert to list of paragraphs
                # @todo: support bulleted lists and tables in represents
                pdf_value = []

                def add_paragraph(text):
                    # Wrap text in Paragraph to preserve newlines and set font weight
                    para = Paragraph(biDiText(text).replace("\n", "<br/>"), para_style)
                    pdf_value.append(para)

                text = ""
                for component in value.components:
                    if isinstance(component, str):
                        # Concatenate consecutive strings
                        text = "".join((text, component))
                    else:
                        # Convert component
                        sub = self.convert(rfield, component)
                        if isinstance(sub, str):
                            text = "".join((text, sub))
                            continue
                        elif text:
                            add_paragraph(text)
                            text = ""
                        if isinstance(sub, list):
                            pdf_value.extend(sub)
                        else:
                            pdf_value.append(sub)
                if text:
                    add_paragraph(text)
            else:
                # Empty tag => empty string
                pdf_value = ""
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

        table_style = self.table_style(0, len(data), len(self.labels) - 1)

        self.parts = self.calc(data, table_style)

        return self.presentation()

    # -------------------------------------------------------------------------
    def group_data(self):
        """
            Group the rows

            @returns: the PDF-formatted data with grouping headers

            FIXME: will not work with RTL-biDiText or any non-text
                   representation, rewrite to use raw resource data
        """

        groups = self.groupby.split(",")
        new_data = []
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
            current_group = None
            r = 0
            for row in data:
                if r + 1 in self.subheading_rows:
                    new_data.append(row)
                    r += 1
                else:
                    try:
                        group = row[i]
                        if group != current_group:
                            line = [group]
                            new_data.append(line)
                            r += 1
                            current_group = group
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
                        new_data.append(line)
                        r += 1
                    except:
                        new_data.append(row)
                        r += 1
            data = new_data
            new_data = []

        self.list_fields = list_fields
        return data

    # -------------------------------------------------------------------------
    def calc(self, data, table_style):
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
        table_style = table_style[:]

        # Build the table to determine row heights and column widths
        table = Table(data,
                      repeatRows = 1,
                      style = table_style,
                      hAlign = "LEFT",
                      )
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

        stylesheet = getSampleStyleSheet()
        para_style = stylesheet["Normal"]
        para_style.fontName = self.font_name

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
                        if col_index in para_cols and isinstance(item, str):
                            col_widths[col_index] = min_width
                            para = main_doc.addParagraph(item,
                                                         style = para_style,
                                                         append = False,
                                                         )
                            temp_row.append(para)
                        else:
                            temp_row.append(item)
                    adj_data.append(temp_row)

            # Rebuild temp_doc to re-calculate col widths and row heights
            table_style[1] = ("FONTSIZE", (0, 0), (-1, -1), fontsize)
            table = Table(adj_data,
                          repeatRows = 1,
                          style = table_style,
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

                        # Re-calculate page size and margins
                        temp_doc._calc()
                        main_doc._calc()
                        self.body_height = main_doc.printable_height - \
                                           main_doc.header_height - \
                                           main_doc.footer_height

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
        """

        # Build the tables
        tables = []
        tappend = tables.append

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
        start_row = 0
        for current_part, part in enumerate(self.parts):

            if part == []:
                continue
            num_rows = len(part)

            col_widths = self.col_widths[current_part % num_horz_parts]
            row_heights = self.row_heights[int(current_part / num_horz_parts)]

            # Auto-grow vertically (=add empty extra rows)
            if autogrow == "V" or autogrow == "B":

                total_height = sum(row_heights)
                available_height = body_height - total_height

                if available_height > default_row_height:
                    num_extra_rows = int(available_height / default_row_height)
                    if num_extra_rows:
                        part += [[""] * len(col_widths)] * num_extra_rows
                        row_heights = list(row_heights) + \
                                      [default_row_height] * num_extra_rows

            table_style = self.table_style(start_row, num_rows, len(col_widths) - 1)
            (part, table_style) = main_doc.addCellStyling(part, table_style)

            p = Table(part,
                      repeatRows = 1,
                      style = table_style,
                      hAlign = "LEFT",
                      colWidths = col_widths,
                      rowHeights = row_heights,
                      emptyTableAction = "indicate",
                      )
            tappend(p)

            # Add a page break, except for the last part
            next_part = current_part + 1
            if next_part < num_parts:
                tappend(PageBreak())
            if next_part % num_horz_parts == 0:
                start_row += num_rows - 1 # Don't include the heading

        # Hint for too many records
        totalrows = self.totalrows
        numrows = self.numrows
        if totalrows and totalrows > numrows:
            hint = current.T("Too many records - %(number)s more records not included") % \
                                {"number": totalrows - numrows}
            stylesheet = getSampleStyleSheet()
            style = stylesheet["Normal"]
            style.textColor = colors.red
            style.fontSize = 12
            tappend(PageBreak())
            tappend(Paragraph(s3_str(hint), style))

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
    def table_style(self,
                    start_row,
                    row_cnt,
                    end_col,
                    colour_required = False,
                    ):
        """
            Internally used method to assign a style to the table

            @param start_row: The row from the data that the first data row in
            the table refers to. When a table is split the first row in the
            table (ignoring the label header row) will not always be the first row
            in the data. This is needed to align the two. Currently this parameter
            is used to identify sub headings and give them an emphasised styling
            @param row_cnt: The number of rows in the table
            @param end_col: The last column in the table

            FIXME: replace end_col with -1
                   (should work but need to test with a split table)
        """

        font_name_bold = self.font_name_bold

        style = [("FONTNAME", (0, 0), (-1, -1), self.font_name),
                 ("FONTSIZE", (0, 0), (-1, -1), self.fontsize),
                 ("VALIGN", (0, 0), (-1, -1), "TOP"),
                 ("LINEBELOW", (0, 0), (end_col, 0), 1, Color(0, 0, 0)),
                 ("FONTNAME", (0, 0), (end_col, 0), font_name_bold),
                 ]
        sappend = style.append
        if colour_required:
            sappend(("BACKGROUND", (0, 0), (end_col, 0), self.header_color))
        else:
            sappend(("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey))
            sappend(("INNERGRID", (0, 0), (-1, -1), 0.2, colors.lightgrey))
        if self.groupby != None:
            sappend(("LEFTPADDING", (0, 0), (-1, -1), 20))

        row_color_cnt = 0 # used to alternate the colours correctly when we have subheadings
        for i in range(row_cnt):
            # If subheading
            if start_row + i in self.subheading_rows:
                level = self.subheading_level[start_row + i]
                if colour_required:
                    sappend(("BACKGROUND", (0, i), (end_col, i),
                             self.header_color))
                sappend(("FONTNAME", (0, i), (end_col, i), font_name_bold))
                sappend(("SPAN", (0, i), (end_col, i)))
                sappend(("LEFTPADDING", (0, i), (end_col, i), 6 * level))
            elif i > 0:
                if colour_required:
                    if row_color_cnt % 2 == 0:
                        sappend(("BACKGROUND", (0, i), (end_col, i),
                                 self.even_color))
                        row_color_cnt += 1
                    else:
                        sappend(("BACKGROUND", (0, i), (end_col, i),
                                 self.odd_color))
                        row_color_cnt += 1
        sappend(("BOX", (0, 0), (-1, -1), 1, Color(0, 0, 0)))
        return style

# =============================================================================
class S3html2pdf():
    """
        Class that takes HTML in the form of web2py helper objects
        and converts it to PDF
    """

    def __init__(self,
                 page_width,
                 exclude_class_list = None,
                 styles = None,
                 ):
        """
            Constructor

            @param page_width: the printable width
            @param exclude_class_list: list of classes for elements to skip
            @param styles: the styles dict from the caller (e.g. pdf_html_styles)
        """

        # Set Fonts
        set_fonts(self)

        self.exclude_class_list = exclude_class_list or []

        self.page_width = page_width
        #self.fontsize = 10

        # Standard styles
        styleSheet = getSampleStyleSheet()

        plainstyle = styleSheet["Normal"]
        plainstyle.fontName = self.font_name
        plainstyle.fontSize = 9
        self.plainstyle = plainstyle

        plainstyle_para = deepcopy(plainstyle)
        plainstyle_para.spaceAfter = 8
        self.plainstyle_para = plainstyle_para

        plainstyle_center = deepcopy(plainstyle)
        plainstyle_center.alignment = TA_CENTER
        self.plainstyle_center = plainstyle_center

        plainstyle_right = deepcopy(plainstyle)
        plainstyle_right.alignment = TA_RIGHT
        self.plainstyle_right = plainstyle_right

        boldstyle = deepcopy(plainstyle)
        boldstyle.fontName = self.font_name_bold
        boldstyle.fontSize = 10
        self.boldstyle = boldstyle

        boldstyle_center = deepcopy(boldstyle)
        boldstyle_center.alignment = TA_CENTER
        self.boldstyle_center = boldstyle_center

        boldstyle_right = deepcopy(boldstyle)
        boldstyle_right.alignment = TA_RIGHT
        self.boldstyle_right = boldstyle_right

        titlestyle = deepcopy(boldstyle)
        titlestyle.fontSize = 16
        titlestyle.spaceAfter = 8
        self.titlestyle = titlestyle

        # To add more PDF styles define the style above (just like the titlestyle)
        # Then add the style and the name to the lookup dict below
        #- only applied currently to P/H tags
        # These can then be added to the html in the code as follows:
        # TD("Waybill", _class="pdf_title")
        self.style_lookup = {"pdf_title": titlestyle,
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
    def select_tag(self,
                   html,
                   strip_markup = True,
                   style = None,
                   ):
        """
            Parses the element and converts it into a format for ReportLab

            @param html: the element to convert
            @param strip_markup: whether to strip markup
            @param style: the style to use

            @return: a list containing text that ReportLab can use
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
        elif isinstance(html, (str, lazyT)):
            html = s3_str(html)
            if strip_markup and "<" in html:
                html = s3_strip_markup(html)
            text = biDiText(html)
            text = text.replace("\n", "<br/>")
            if not style:
                style = self.plainstyle
            para = [Paragraph(text, style)]
            return para
        return None

    # -------------------------------------------------------------------------
    def exclude_tag(self, html):
        """
            Work out whether to exclude a Tag based on it's class
        """

        try:
            _class = html.attributes["_class"]
        except (AttributeError, KeyError):
            return False

        if _class in self.exclude_class_list:
            return True

        return False

    # -------------------------------------------------------------------------
    def parse_div(self, html):
        """
            Parses a DIV element and converts it into a format for ReportLab

            @ToDo: Add support for B & I

            @param html: the DIV element to convert
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

            @param html: the A element to convert
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

            @param html: the IMG element to convert
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
                                       "uploads",
                                       src[1],
                                       )
            src = unquote(src)
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
            Parses a P or H element and converts it into a format for ReportLab

            @param html: the P element to convert
            @return: a list containing text that ReportLab can use
        """

        style = None

        try:
            _class = html.attributes["_class"]
        except KeyError:
            pass
        else:
            if _class in self.style_lookup:
                style = self.style_lookup[_class]

        if not style:
            tag = html.tag
            title = tag != "p"
            if title:
                if tag == "h2":
                    style = self.titlestyle
                else:    
                    # Need to create a custom style
                    style = deepcopy(self.boldstyle)
                    font_sizes = {#"p": 9, # self.plainstyle default
                                  "h1": 18,
                                  #"h2": 16, # self.titlestyle default
                                  "h3": 14,
                                  "h4": 12,
                                  "h5": 10,
                                  "h6": 9,
                                  }
                    style.fontSize = font_sizes.get(tag)
                    style.spaceAfter = 8
            else:
                style = self.plainstyle_para

        content = []
        select_tag = self.select_tag
        for component in html.components:
            result = select_tag(component,
                                style = style,
                                )
            if result != None:
                content += result

        if content == []:
            return None

        return content

    # -------------------------------------------------------------------------
    def parse_table(self, html):
        """
            Parses a TABLE element and converts it into a format for ReportLab

            @param html: the TABLE element to convert
            @return: a list containing text that ReportLab can use
        """

        _class = html["_class"]
        if _class:
            table_classes = _class.split()
        else:
            table_classes = []

        table_style = [#("FONTNAME", (0, 0), (-1, -1), self.font_name),   # Done in Paragraph
                       #("FONTSIZE", (0, 0), (-1, -1), self.fontsize),    # Done in Paragraph
                       ("VALIGN", (0, 0), (-1, -1), "TOP"),
                       ]
        if "no-grid" not in table_classes:
            table_style.append(("GRID", (0, 0), (-1, -1), 0.5, colors.grey))

        content = self.parse_table_components(html,
                                              table_style = table_style,
                                              )[0]

        if content == []:
            return None

        table = Table(content,
                      style = table_style,
                      hAlign = "LEFT",  # defaults to "CENTER"
                      vAlign = "TOP",   # defaults to "MIDDLE", but we control via the table_style instead...this seems to do nothing
                      repeatRows = 1 if "repeat-header" in table_classes else 0,
                      )

        if "shrink-to-fit" in table_classes:
            # Calculate column widths
            pw = self.page_width
            table.wrap(pw, 0)

            cw = table._colWidths
            tw = sum(cw)

            if tw and tw > pw:
                # Table overflows => adjust column widths proportionally
                factor = pw / tw
                cw = [w * factor for w in cw]

                # Re-instantiate with colWidths
                table = Table(content,
                              colWidths = cw,
                              style = table_style,
                              hAlign = "LEFT",
                              vAlign = "TOP",
                              repeatRows = 1 if "repeat-header" in table_classes else 0,
                              )

        return [table]

    # -------------------------------------------------------------------------
    def parse_table_components(self,
                               table,
                               content = None,
                               row_count = 0,
                               table_style = None,
                               ):
        """
            Parses TABLE components

            @param table: the TABLE instance or a subcomponent of it
            @param content: the current content array
            @param row_count: the current number of rows in the content array
            @param table_style: the table_style list
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
                                           table_style = table_style,
                                           )

            elif isinstance(component, TR):
                result = parse_tr(component, table_style, row_count, rowspans)
                row_count += 1

            if result != None:
                cappend(result)

        return content, row_count

    # -------------------------------------------------------------------------
    def parse_tr(self, html, table_style, rowCnt, rowspans):
        """
            Parses a TR element and converts it into a format for ReportLab

            @param html: the TR element to convert
            @param table_style: the table_style list
            @param rowCnt: the row counter
            @param rowspans: the remaining rowspans (if any)

            @return: a list containing text that ReportLab can use
        """

        # Identify custom styles
        row_styles = self._styles(html)
        row_styles_get = row_styles.get

        _color = self._color
        row_background = _color(row_styles_get("background-color"))
        row_color = _color(row_styles_get("color"))

        row = []
        rappend = row.append
        sappend = table_style.append

        exclude_tag = self.exclude_tag
        select_tag = self.select_tag

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

            if isinstance(component, TH):
                title = True
            else:
                title = False

            attr_get = component.attributes.get
            rowspan = attr_get("_rowspan")
            if rowspan:
                # @ToDo: Centre the text across the rows
                rowspans[rspan_index] = rowspan - 1

            cell_valign = attr_get("_valign")
            if cell_valign:
                cell_valign = cell_valign.upper()

            cell_align = attr_get("_align", "LEFT")
            if cell_align == "LEFT":
                text_align = TA_LEFT
            else:
                cell_align = cell_align.upper()
                if cell_align == "CENTER":
                    text_align = TA_CENTER
                elif cell_align == "RIGHT":
                    text_align = TA_RIGHT
                else:
                    text_align = TA_LEFT

            cell_style = None
            try:
                _class = component.attributes["_class"]
            except KeyError:
                pass
            else:
                if _class in self.style_lookup:
                    cell_style = self.style_lookup[_class]

            if not cell_style:
                if title:
                    if text_align == TA_LEFT:
                        cell_style = self.boldstyle
                    elif text_align == TA_CENTER:
                        cell_style = self.boldstyle_center
                    elif text_align == TA_RIGHT:
                        cell_style = self.boldstyle_right
                    #elif text_align == TA_JUSTIFY:
                    #    cell_style = self.boldstyle_justify
                else:
                    if text_align == TA_LEFT:
                        cell_style = self.plainstyle
                    elif text_align == TA_CENTER:
                        cell_style = self.plainstyle_center
                    elif text_align == TA_RIGHT:
                        cell_style = self.plainstyle_right
                    #elif text_align == TA_JUSTIFY:
                    #    cell_style = self.plainstyle_justify

                if row_color and \
                   row_color != colors.black:
                    # Need to create a custom style
                    cell_style = deepcopy(cell_style)
                    cell_style.textColor = row_color

            colspan = attr_get("_colspan", 1)
            parse = False
            for detail in component.components:
                if isinstance(detail, DIV):
                    if isinstance(detail, (B, I)):
                        continue
                    parse = True
                    break

            if parse:
                # Components present which need full parsing
                # - each element will be in a separate Paragraph
                cell = []
                for detail in component.components:
                    # Render cell content
                    result = select_tag(detail,
                                        #strip_markup = True,
                                        style = cell_style,
                                        )
                    if result is None:
                        continue
                    cell.append(result)

                len_cell = len(cell)
                if len_cell == 1:
                    rappend(cell[0])
                elif len_cell > 1:
                    rappend(cell)

            else:
                # Components don't need full parsing
                # - keep B, I elements within a single Paragraph
                text = ""
                strip_markup = True
                for detail in component.components:
                    if isinstance(detail, (B, I)):
                        strip_markup = False

                    text = "%s%s" % (text, detail)

                # Render cell content
                result = select_tag(text,
                                    strip_markup = strip_markup,
                                    style = cell_style,
                                    )
                if result is None:
                    continue
                rappend(result)

            # Add cell styles
            cell = (colCnt, rowCnt)
            # Always done in the Paragraph
            #if row_color:
            #    sappend(("TEXTCOLOR", cell, cell, row_color))
            if row_background:
                sappend(("BACKGROUND", cell, cell, row_background))
            elif title:
                sappend(("BACKGROUND", cell, cell, colors.lightgrey))
                # Always done in the Paragraph
                #sappend(("FONTNAME", cell, cell, self.font_name_bold))
            # Doesn't work for cells which contain a Paragraph as the alignment needs setting there
            # - if we need to align Images then uncomment this
            #if cell_align != "LEFT":
            #    sappend(("ALIGN", cell, cell, cell_align))
            if cell_valign:
                sappend(("VALIGN", cell, cell, cell_valign))

            # Column span
            if colspan > 1:
                for i in range(1, colspan):
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
            Get the custom styles for the given element (match by tag and classes)

            @param element: the HTML element (web2py helper)
        """

        element_styles = {}

        styles = self.styles # pdf_html_styles dict
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
            return None

        if val[:1] == "#":
            color = HexColor(val)
        else:
            try:
                color = object.__getattribute__(colors, val)
            except AttributeError:
                color = None
        return color

# =============================================================================
class S3NumberedCanvas(canvas.Canvas):
    """
        Canvas type with page numbers
        - based on http://code.activestate.com/recipes/576832
    """
    def __init__(self, *args, **kwargs):

        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):

        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):

        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):

        self.setFont("Helvetica", 7)
        pagesize = self._pagesize
        self.drawRightString(pagesize[0] - 12,
                             pagesize[1] - 12,
                             "%d / %d" % (self._pageNumber, page_count),
                             )

# END =========================================================================
