# -*- coding: utf-8 -*-

"""
    S3 Adobe PDF codec

    @copyright: 2011 (c) Sahana Software Foundation
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

__all__ = ["S3RL_PDF"]

# Import the necessary libraries
from gluon import *
from gluon import current
from gluon.storage import Storage
from gluon.contenttype import contenttype
from gluon.languages import lazyT

from ..s3codec import S3Codec

try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO

from copy import deepcopy

# Import the specialist libraries
try:
    from PIL import Image
    from PIL import ImageOps
    from PIL import ImageStat
    PILImported = True
except(ImportError):
    try:
        import Image
        import ImageOps
        import ImageStat
        PILImported = True
    except(ImportError):
        PILImported = False
try:
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.pdfbase import pdfmetrics

    from reportlab.pdfgen import canvas
    from reportlab.lib.fonts import tt2ps
    from reportlab.rl_config import canvas_basefontname as _baseFontName
    from reportlab.platypus import BaseDocTemplate, SimpleDocTemplate, PageTemplate
    from reportlab.platypus.frames import Frame
    from reportlab.platypus import Spacer, PageBreak, FrameBreak, Paragraph
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.colors import Color
    from reportlab.lib.pagesizes import A4, LETTER, landscape, portrait
    from reportlab.platypus.flowables import Flowable
    reportLabImported = True
except ImportError:
    reportLabImported = False
    BaseDocTemplate = object
    inch = 72.0
    canvas = Storage()
    canvas.Canvas = None

PDF_WIDTH = 0
PDF_HEIGHT = 1

# =============================================================================

class S3RL_PDF(S3Codec):
    """
        Simple Report Labs PDF format codec
    """
    # -------------------------------------------------------------------------
    def __init__(self):
        """
            Constructor
        """

        # Error codes
        T = current.T
        self.ERROR = Storage(
            PIL_ERROR = T("PIL (Python Image Library) not installed, images cannot be embedded in the PDF report"),
            RL_ERROR = T("Reportlab not installed")
        )

    # -------------------------------------------------------------------------
    def encode(self, r, **attr):
        """
            Export data as a PDF spreadsheet

            @param r: the S3Request object
            @param attr: dictionary of parameters:
                 * pdf_callback:    callback to be used rather than r
                 * list_fields:     Fields to include in list views
                 * pdf_componentname: The name of the component to use
                                         This should be a component of the resource
                 * pdf_title:    The title of the report
                 * pdf_filename: The filename of the report
                 * pdf_header:   The header (maybe a callback)
                 * rHeader:         used if pdf_header doesn't exist
                 * pdf_header_padding: add this amount of space between the header and the body
                 * pdf_footer:   The footer (maybe a callback)
                 * rFooter:         used if pdf_footer doesn't exist
                 * pdf_footer_padding: add this amount of space between the body and the footer
                 * use_colour:      True to add colour to the cells. default False
                 * pdf_groupby:  How to group the results
                 * pdf_orderby:  How to sort rows (within any level of grouping)
                 * pdf_hide_comments: don't show the comments in a table
                 * pdf_table_autogrow: Indicates that a table should grow to
                                          fill the available space. Valid values:
                                          H - Horizontal
                                          V - Vertical
                                          B - Both
                * pdf_paper_alignment: Portrait (default) or Landscape
        """
        if not PILImported:
            current.session.warning = self.ERROR.PIL_ERROR
        if not reportLabImported:
            current.session.error = self.ERROR.RL_ERROR
            redirect(URL(extension=""))

        # Environment
        request = current.request
        response = current.response
        self.r = r
        self.list_fields = attr.get("list_fields")
        self.pdf_groupby = attr.get("pdf_groupby")
        self.pdf_orderby = attr.get("pdf_orderby")
        self.pdf_hide_comments = attr.get("pdf_hide_comments")
        self.table_autogrow = attr.get("pdf_table_autogrow")
        self.pdf_header_padding = attr.get("pdf_header_padding",0)
        self.pdf_footer_padding = attr.get("pdf_footer_padding",0)
        # Get the title & filename
        now = request.now.isoformat()[:19].replace("T", " ")
        title = attr.get("pdf_title")
        if title == None:
            title = "Report"
        docTitle = "%s %s" % (title, now)
        self.filename = attr.get("pdf_filename")
        if self.filename == None:
            self.filename = "%s_%s.pdf" % (title, now)
        # get the pdf document template
        paper_size = attr.get("paper_size")
        pdf_paper_alignment = attr.get("pdf_paper_alignment","Portrait")
        doc = EdenDocTemplate(title=docTitle,
                              paper_size = paper_size,
                              paper_alignment = pdf_paper_alignment)
        # Get the header
        header_flowable = None
        header = attr.get("pdf_header")
        if not header:
            header = attr.get("rheader")
        if header:
            header_flowable = self.get_html_flowable(header,
                                                     doc.printable_width)
            if self.pdf_header_padding:
                header_flowable.append(Spacer(1,self.pdf_header_padding))
        # Get the footer
        footer_flowable = None
        footer = attr.get("pdf_footer")
        if not footer:
            footer = attr.get("rFooter")
        if footer:
            footer_flowable = self.get_html_flowable(footer,
                                                     doc.printable_width)
            if self.pdf_footer_padding:
                footer_flowable.append(Spacer(1, self.pdf_footer_padding))
        # Build report template

        # Get data for the body of the text
        data = None
        body_flowable = None

        doc.calc_body_size(header_flowable, footer_flowable)
        callback = attr.get("pdf_callback")
        if callback:
            body_flowable = self.get_html_flowable(callback(r),
                                                   doc.printable_width)
        elif attr.get("pdf_componentname"):
            componentname = attr.get("pdf_componentname")
            (prefix, component) = componentname.split("_", 1)
            resource = current.s3db.resource(r.tablename,
                                             components = [component],
                                             id = r.id)
            body_flowable = self.get_resource_flowable(resource.components[component],
                                                       doc)
        else:
            if r.component:
                resource = r.component
            else:
                resource = r.resource
            body_flowable = self.get_resource_flowable(resource,
                                                       doc)
        styleSheet = getSampleStyleSheet()
        self.normalstyle = styleSheet["Normal"]
        self.normalstyle.fontName = "Helvetica"
        self.normalstyle.fontSize = 9
        if not body_flowable:
            body_flowable = [Paragraph("",self.normalstyle)]
        # Build the pdf
        doc.build(header_flowable,
                  body_flowable,
                  footer_flowable,
                 )
        # return the generated pdf
        # Set content type and disposition headers
        if response:
            disposition = "attachment; filename=\"%s\"" % self.filename
            response.headers["Content-Type"] = contenttype(".pdf")
            response.headers["Content-disposition"] = disposition

        # Return the stream
        doc.output.seek(0)
        return doc.output.read()

    def get_html_flowable(self, rules, printable_width):
        """
            Function to convert the rules passed in to a flowable.

            the rules (for example) could be a rHeader callback
        """
        # let's assume that it's a callable
        try:
            # switch the representation to html so the callback doesn't barf
            repr = self.r.representation
            self.r.representation = "html"
            html = rules(self.r)
            self.r.representation = repr
        except:
            # okay so maybe it wasn't ... it could be an HTML object
            html = rules
        parser = S3html2pdf(pageWidth = printable_width,
                            exclude_class_list=["tabs"])
        result = parser.parse(html)
        return result

    def get_resource_flowable(self, resource, doc):
        # get a list of fields, if the list_fields attribute is provided
        # then use that to extract the fields that are required, otherwise
        # use the list of readable fields.
        from s3.s3utils import S3DataTable
        if not self.list_fields:
            self.list_fields = []
            fields = resource.readable_fields()
            for field in fields:
                if field.type == "id":
                    continue
                if self.pdf_hide_comments and field.name == "comments":
                    continue
                self.list_fields.append(field.name)
        rfields = resource.resolve_selectors(self.list_fields)[0]
        (orderby, filter) = S3DataTable.getControlData(rfields, current.request.vars)
        resource.add_filter(filter)
        current.manager.ROWSPERPAGE = None # needed to get all the data
        rows = resource.select(self.list_fields,
                               orderby=orderby,
                               )
        data = resource.extract(rows,
                                self.list_fields,
                                represent=True,
                                )
        # Now generate the PDF table
        pdf_table = S3PDFTable(doc,
                               rfields,
                               data,
                               groupby = self.pdf_groupby,
                               autogrow = self.table_autogrow,
                               body_height = doc.body_height,
                               ).build()
        return pdf_table

# -------------------------------------------------------------------------
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
                 margin = (0.5*inch,  # top
                           0.3*inch,  # left
                           0.5*inch,  # bottom
                           0.3*inch), # right
                 margin_inside = 0.0*inch, # used for odd even pages
                 paper_size = None,
                 paper_alignment = "Portrait"):
        """
            Set up the standard page templates
        """
        self.output = StringIO()
        self.defaultPage = paper_alignment
        if paper_size:
            self.paper_size = paper_size
        else:
            settings = current.deployment_settings
            if settings.get_paper_size() == "Letter":
                self.paper_size = LETTER
            else:
                self.paper_size = A4
        self.topMargin = margin[0]
        self.leftMargin = margin[1]
        self.bottomMargin = margin[2]
        self.rightMargin = margin[3]
        self.insideMargin = margin_inside

        BaseDocTemplate.__init__(self,
                                 self.output,
                                 title = title,
                                 leftMargin = self.leftMargin,
                                 rightMargin = self.rightMargin,
                                 topMargin = self.topMargin,
                                 bottomMargin = self.bottomMargin,
                                )

        self.MINIMUM_MARGIN_SIZE = 0.2 * inch
        self.body_flowable = None

        self._calc()

    def get_flowable_size(self, flowable):
        """
            Function to return the size a flowable will require
        """
        if not flowable:
            return (0,0)
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

    def _calc(self):
        if self.defaultPage == "Landscape":
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

    def calc_body_size(self,
                       header_flowable,
                       footer_flowable,
                      ):
        """
            Helper function to calculate the various sizes of the page
        """
        self._calc()    # in case we changed margins sizes etc
        self.height = self.pagesize[PDF_HEIGHT]
        self.width = self.pagesize[PDF_WIDTH]
        self.printable_width = self.width - \
                               self.leftMargin - \
                               self.rightMargin - \
                               self.insideMargin
        self.printable_height = self.height - \
                                self.topMargin - \
                                self.bottomMargin
        header_size = self.get_flowable_size(header_flowable)
        footer_size = self.get_flowable_size(footer_flowable)
        self.header_height = header_size[PDF_HEIGHT]
        self.footer_height = footer_size[PDF_HEIGHT]
        self.body_height = self.printable_height - \
                           self.header_height - \
                           self.footer_height

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
        self.normalPage = PageTemplate (id = 'Normal',
                                        frames = [body_frame,],
                                        onPage = self.add_page_decorators,
                                        pagesize = self.pagesize
                                       )
        # @todo set these page templates up
#        self.evenPage = PageTemplate (id='even',
#                                      frames=frame_list,
#                                      onPage=self.onEvenPage,
#                                      pagesize=self.pagesize
#                                     )
#        self.oddPage = PageTemplate (id='odd',
#                                     frames=frame_list,
#                                     onPage=self.onOddPage,
#                                     pagesize=self.pagesize
#                                    )
        self.landscapePage = PageTemplate (id='Landscape',
                                           frames = [body_frame,],
                                           onPage=self.add_page_decorators,
                                           pagesize=landscape(self.pagesize)
                                          )
        if self.defaultPage == "Landscape":
            self.addPageTemplates(self.landscapePage)
        else:
            self.addPageTemplates(self.normalPage)

        BaseDocTemplate.build(self, self.body_flowable, canvasmaker=canvasmaker)

    def add_page_decorators(self, canvas, doc):
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
            para = Paragraph(text, style)
            if append and self.body_flowable:
                self.body_flowable.append(para)
            return para
        return ""

    def cellStyle(self, style, cell):
        """
            Add special styles to the text in a cell
        """
        if style == "*GREY":
            return [("TEXTCOLOR",cell, cell, colors.lightgrey)]
        elif style == "*RED":
            return [("TEXTCOLOR",cell, cell, colors.red)]
        return []


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
                        (instruction,sep,text) = cell.partition(" ")
                        style += self.cellStyle(instruction, (col, row))
                        table[row][col] = text
                except:
                    pass
                col += 1
            row += 1
        return (table, style)
# end of class EdenDocTemplate


# -----------------------------------------------------------------------------
class S3PDFTable(object):
    """
        Class to build a table that can then be placed in a pdf document

        The table will be formatted so that is fits on the page. This class
        doesn't need to be called directly. Rather see S3PDF.addTable()
    """

    def __init__(self,
                 document,
                 rfields,
                 raw_data,
                 groupby = None,
                 hide_comments = False,
                 autogrow = False,
                 body_height = 0,
                ):
        """
            Method to create a table object

            @param document: A S3PDF object
            @param raw_data: A list of rows
            @param list_fields: A list of field names
            @param labels: a list of labels
            @param groupby: A field name that is to be used as a sub-group
                   All the records that share the same pdf_groupby value
                   will be clustered together
            @param hide_comments: Any comment field will be hidden
        """

        settings = current.deployment_settings
        if settings.get_paper_size() == "Letter":
            self.paper_size = LETTER
        else:
            self.paper_size = A4

        self.pdf = document
        # @todo: change the code to use raw_data directly rather than this
        #        conversion to an ordered list of values
        self.rfields = rfields
        self.raw_data = []
        for row in raw_data:
            data = []
            for value in rfields:
                text = row[value.colname]
                if isinstance(text, str):
                    data.append(text)
                else:
                    try:
                        # extract the text from the html tag
                        data.append(text.components[0])
                    except:
                        data.append(str(text))
            self.raw_data.append(data)
        self.labels = [field.label for field in self.rfields]
        self.list_fields = [field.fname for field in self.rfields]
        self.pdf_groupby = groupby
        self.hideComments = hide_comments
        self.autogrow = autogrow
        self.body_height = body_height
        self.data = []
        self.subheadingList = []
        self.subheadingLevel = {}
        self.pages = []
        self.colWidths = []
        self.newColWidth = [] # @todo: remove this (but see presentation)
        self.rowHeights = []
        self.style = None
        # temp document to test the table size, default to A4 portrait
        # @todo: use custom template
        # @todo: set pagesize for pdf component not whole document
        self.tempDoc = EdenDocTemplate()
#        self.tempDoc.setPageTemplates(self.pdf.pageHeader,
#                                      self.pdf.pageFooter)
#        self.tempDoc.pagesize = portrait(self.paper_size)
        # Set up style constants
        self.headerColour = Color(0.73, 0.76, 1)
        self.oddColour = Color(0.92, 0.92, 1)
        self.evenColour = Color(0.83, 0.84, 1)
        self.MIN_COMMENT_COL_WIDTH = 200
        self.fontsize = 12

    # -------------------------------------------------------------------------
    def build(self):
        """
            Method to build the table.

            @return: A list of Table objects. Normally this will be a list with
                     just one table object, but if the table needs to be split
                     across columns then one object per page will be created.
        """
        if self.pdf_groupby:
            data = self.group_data()
            self.data = [self.labels] + data
        elif self.raw_data != None:
            self.data = [self.labels] + self.raw_data
        # Only build the table if we have some data
        if not self.data or not (self.data[0]):
            return None
        endCol = len(self.labels) - 1
        rowCnt = len(self.data)

        self.style = self.tableStyle(0, rowCnt, endCol)
        tempTable = Table(self.data, repeatRows=1,
                          style=self.style, hAlign="LEFT"
                         )
        self.tempDoc.build(None, [tempTable], None)
        self.newColWidth = [tempTable._colWidths]
        self.rowHeights = [tempTable._rowHeights]
        self.pages.append(self.data)
        if not self.tweakDoc(tempTable):
            #print "Need to split the table"
            self.pages = self.splitTable(tempTable)
        return self.presentation()

    def group_data(self):
        groups = self.pdf_groupby.split(",")
        newData = []
        data = self.raw_data
        level = 0
        for field in groups:
            level += 1
            field = field.strip()
            # find the location of field in list_fields
            i = 0
            rowlength = len(self.list_fields)
            while i < rowlength:
                if self.list_fields[i] == field:
                    break
                i += 1
            list_fields = self.list_fields[0:i]+self.list_fields[i+1:]
            self.list_fields = list_fields
            labels = self.labels[0:i]+self.labels[i+1:]
            self.labels = labels
            currentGroup = None
            r = 0
            for row in data:
                if r+1 in self.subheadingList:
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
                            self.subheadingList.append(r)
                            self.subheadingLevel[r] = level
                            # all existing subheadings after this point need to
                            # be shuffled down one place.
                            for x in range (len(self.subheadingList)):
                                if self.subheadingList[x] > r:
                                    posn = self.subheadingList[x]
                                    self.subheadingList[x] = posn + 1
                                    oldlevel = self.subheadingLevel[posn]
                                    del self.subheadingLevel[posn]
                                    self.subheadingLevel[posn+1] = oldlevel
                        line = row[0:i]+row[i+1:]
                        newData.append(line)
                        r += 1
                    except:
                        newData.append(row)
                        r += 1
            data = newData
            newData = []
        return data

    # -------------------------------------------------------------------------
    def presentation(self):
        """
            This will convert the S3PDFTABLE object to a format that can be
            used to add to a S3PDF document object.

            This is only used internally but could be used to generate a copy
            of a previously generated table
        """
        # Build the tables
        content = []
        currentPage = 0
        totalPagesAcross = len(self.newColWidth)
        if self.autogrow == "H" or self.autogrow == "B":
            printable_width = self.pdf.printable_width
            # expand the columns to use all the available space
            newColWidth = []
            for cols in self.newColWidth:
                col_width = 0
                for col in cols:
                    col_width += col
                if col_width < printable_width:
                    surplus = printable_width - col_width
                    proportion = surplus / col_width
                    newcols = []
                    for col in cols:
                        newcols.append(col+col*proportion)
                    newColWidth.append(newcols)
            self.newColWidth = newColWidth
        startRow = 0
        for page in self.pages:
            if page == []:
                currentPage += 1
                continue
            colWidths = self.newColWidth[currentPage % totalPagesAcross]
            if self.autogrow == "V" or self.autogrow == "B":
                row_height = self.rowHeights[0][0]
                rows = len(page)
                if self.body_height > row_height * rows:
                    rowCnt = int(self.body_height/row_height)
                    extra_rows = rowCnt - rows
                    if extra_rows:
                        cells = len(colWidths)
                        row = [""] * cells
                        extra = [row] * extra_rows
                        page = page + extra
            endCol = len(colWidths) - 1
            rowCnt = len(page)
            self.style = self.tableStyle(startRow, rowCnt, endCol)
            (page,self.style) = self.pdf.addCellStyling(page, self.style)
            p = Table(page, repeatRows=1,
                      style=self.style,
                      hAlign="LEFT",
                      colWidths=colWidths
                     )
            content.append(p)
            # add a page break, except for the last page.
            if currentPage + 1 < len(self.pages):
                content.append(PageBreak())
            currentPage += 1
            if currentPage % totalPagesAcross == 0:
                startRow += rowCnt - 1 # Don't include the heading
        return content

    # -------------------------------------------------------------------------
    def getAvailableMarginSpace(self):
        """
            Internally used method to calculate the amount of space available
            on the width of a page.
        """
        currentLeftMargin = self.pdf.leftMargin
        currentRightMargin = self.pdf.rightMargin
        availableMarginSpace = currentLeftMargin \
                             + currentRightMargin \
                             - 2 * self.pdf.MINIMUM_MARGIN_SIZE
        return availableMarginSpace

    # -------------------------------------------------------------------------
    def tweakMargin(self, tableWidth):
        """
            Internally used method to adjust the document margins so that the
            table will fit into the available space
        """
        availableMarginSpace = self.getAvailableMarginSpace()
        currentOverlap = tableWidth - self.tempDoc.printable_width
        endCol = len(self.labels) - 1
        rowCnt = len(self.data)
        # Check margins
        if currentOverlap < availableMarginSpace:
            self.pdf.leftMargin -= currentOverlap / 2
            self.pdf.rightMargin -= currentOverlap / 2
            return True
        return False

    # -------------------------------------------------------------------------
    def tweakFont(self, tableWidth, newFontSize, colWidths):
        """
            Internally used method to adjust the font size used so that the
            table will fit into the available space on the page.
        """
        # Check font
        adjustedWidth = tableWidth * newFontSize / self.fontsize
        if (adjustedWidth - self.tempDoc.printable_width) < self.getAvailableMarginSpace():
            for i in range(len(colWidths)):
                colWidths[i] *= float(newFontSize) / float(self.fontsize)
            self.newColWidth = [colWidths]
            self.fontsize = newFontSize
            return self.tweakMargin(adjustedWidth)
        return False

    # -------------------------------------------------------------------------
    def minorTweaks(self, tableWidth, colWidths):
        """
            Internally used method to tweak the formatting so that the table
            will fit into the available space on the page.
        """
        if self.tweakMargin(tableWidth):
            return True
        originalFont = self.fontsize
        if self.tweakFont(tableWidth, originalFont -1, colWidths):
            return True
        if self.tweakFont(tableWidth, originalFont -2, colWidths):
            return True
        if self.tweakFont(tableWidth, originalFont -3, colWidths):
            return True
        return False
        # end of function minorTweaks

    # -------------------------------------------------------------------------
    def tweakDoc(self, table):
        """
            Internally used method to adjust the table so that it will fit
            into the available space on the page.

            @return: True if it is able to perform minor adjustments and have
            the table fit in the page. False means that the table will need to
            be split across the columns.
        """
        tableWidth = 0
        for colWidth in table._colWidths:
            tableWidth += colWidth
        colWidths = table._colWidths
        #print "Doc size %s x %s Table width %s" % (self.tempDoc.printable_width, self.tempDoc.height, total)
        if tableWidth > self.tempDoc.printable_width:
            # self.pdf.setMargins(0.5*inch, 0.5*inch)
            # First massage any comment column by putting it in a paragraph
            colNo = 0
            for label in self.labels:
                # Wrap comments in a paragraph
                if label.lower() == "comments":
                    currentWidth = table._colWidths[colNo]
                    # print "%s %s" % (colNo, currentWidth)
                    if currentWidth > self.MIN_COMMENT_COL_WIDTH:
                        for i in range(1, len(self.data)): # skip the heading
                            try:
                                comments = self.data[i][colNo]
                                if comments:
                                    comments = self.pdf.addParagraph(comments, append=False)
                                    self.data[i][colNo] = comments
                            except IndexError:
                                pass
                        colWidths[colNo] = self.MIN_COMMENT_COL_WIDTH
                        tableWidth += self.MIN_COMMENT_COL_WIDTH - currentWidth
                colNo += 1

            if not self.minorTweaks(tableWidth, colWidths):
                self.tempDoc.defaultPage = "Landscape"
                self.tempDoc._calc()
                self.pdf.defaultPage = "Landscape"
                self.pdf._calc()
                return self.minorTweaks(tableWidth, colWidths)
        return True

    # -------------------------------------------------------------------------
    def splitTable(self, tempTable):
        """
            Internally used method to split the table across columns so that it
            will fit into the available space on the page.
        """
        colWidths = tempTable._colWidths
        rowHeights = tempTable._rowHeights
        total = 0
        colNo = 0
        colSplit = []
        newColWidth = []
        pageColWidth = []
        for colW in colWidths:
            if total + colW > self.tempDoc.printable_width:
                colSplit.append(colNo)
                newColWidth.append(pageColWidth)
                pageColWidth = [colW]
                total = colW
            else:
                pageColWidth.append(colW)
                total += colW
            colNo += 1
        colSplit.append(len(colWidths))
        newColWidth.append(pageColWidth)
        self.newColWidth = newColWidth

        total = 0
        rowNo = 0
        lastKnownHeight = 20 # Not all row heights get calculated.
        rowSplit = []
        for rowH in rowHeights:
            if rowH == None:
                rowH = lastKnownHeight
            else:
                lastKnownHeight = rowH
            if total + rowH > self.body_height:
                rowSplit.append(rowNo)
                total = 2 * rowH # 2* is needed to take into account the repeated header row
            else:
                total += rowH
            rowNo += 1
        rowSplit.append(rowNo)

        # Build the pages of data
        pages = []

        startRow = 1 # Skip the first row (the heading) because we'll generate our own
        for endRow in rowSplit:
            startCol = 0
            for endCol in colSplit:
                page = []
                label = []
                for colIndex in range(startCol, endCol):
                    try:
                        label.append(self.labels[colIndex])
                    except IndexError:
                        label.append("")
                page.append(label)
                for rowIndex in range(startRow, endRow):
                    line = []
                    for colIndex in range(startCol, endCol):
                        try:
                            line.append(self.data[rowIndex][colIndex])
                        except IndexError: # No data to add.
                            # If this is the first column of a subheading row then repeat the subheading
                            if len(line) == 0 and rowIndex in self.subheadingList:
                                try:
                                    line.append(self.data[rowIndex][0])
                                except IndexError:
                                    line.append("")
                            else:
                                line.append("")
                    page.append(line)
                pages.append(page)
                startCol = endCol
            startRow = endRow
        return pages

    # -------------------------------------------------------------------------
    def tableStyle(self, startRow, rowCnt, endCol, colour_required = False):
        """
            Internally used method to assign a style to the table

            @param startRow: The row from the data that the first data row in
            the table refers to. When a table is split the first row in the
            table (ignoring the label header row) will not always be the first row
            in the data. This is needed to align the two. Currently this parameter
            is used to identify sub headings and give them an emphasised styling
            @param rowCnt: The number of rows in the table
            @param endCol: The last column in the table

            @todo: replace endCol with -1
                   (should work but need to test with a split table)
        """
        style = [("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                 ("FONTSIZE", (0, 0), (-1, -1), self.fontsize),
                 ("VALIGN", (0, 0), (-1, -1), "TOP"),
                 ("LINEBELOW", (0, 0), (endCol, 0), 1, Color(0, 0, 0)),
                 ("FONTNAME", (0, 0), (endCol, 0), "Helvetica-Bold"),
                ]
        if colour_required:
            style.append(("BACKGROUND", (0, 0), (endCol, 0), self.headerColour))
        else:
            style.append(("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey))
            style.append(("INNERGRID", (0, 0), (-1, -1), 0.2, colors.lightgrey))
        if self.pdf_groupby != None:
            style.append(("LEFTPADDING", (0, 0), (-1, -1), 20))
        rowColourCnt = 0 # used to alternate the colours correctly when we have subheadings
        for i in range(rowCnt):
            # If subheading
            if startRow + i in self.subheadingList:
                level = self.subheadingLevel[startRow + i]
                if colour_required:
                    style.append(("BACKGROUND", (0, i), (endCol, i),
                                  self.headerColour))
                style.append(("FONTNAME", (0, i), (endCol, i),
                              "Helvetica-Bold"))
                style.append(("SPAN", (0, i), (endCol, i)))
                style.append(("LEFTPADDING", (0, i), (endCol, i), 6 * level))
            elif i > 0:
                if colour_required:
                    if rowColourCnt % 2 == 0:
                        style.append(("BACKGROUND", (0, i), (endCol, i),
                                      self.evenColour))
                        rowColourCnt += 1
                    else:
                        style.append(("BACKGROUND", (0, i), (endCol, i),
                                      self.oddColour))
                        rowColourCnt += 1
        style.append(("BOX", (0, 0), (-1,-1), 1, Color(0, 0, 0)))
        return style

#end of class S3PDFTable
# -------------------------------------------------------------------------
class S3html2pdf():

    def __init__(self,
                 pageWidth,
                 exclude_class_list = []):
        """
            Method that takes html in the web2py helper objects
            and converts it to pdf
        """
        self.exclude_class_list = exclude_class_list
        self.pageWidth = pageWidth
        self.fontsize = 10
        styleSheet = getSampleStyleSheet()
        self.plainstyle = styleSheet["Normal"]
        self.plainstyle.fontName = "Helvetica"
        self.plainstyle.fontSize = 9
        self.boldstyle = deepcopy(styleSheet["Normal"])
        self.boldstyle.fontName = "Helvetica-Bold"
        self.boldstyle.fontSize = 10
        self.titlestyle = deepcopy(styleSheet["Normal"])
        self.titlestyle.fontName = "Helvetica-Bold"
        self.titlestyle.fontSize = 16
        self.normalstyle = self.plainstyle
        # To add more pdf styles define the style above (just like the titlestyle)
        # Then add the style and the name to the lookup dict below
        # These can then be added to the html in the code as follows:
        # TD("Waybill", _class="pdf_title")
        self.style_lookup = {"pdf_title": self.titlestyle
                            }

    def parse(self, html):
        result = self.select_tag(html)
        return result

    def select_tag(self, html, title=False):
        if self.exclude_tag(html):
            return None
        if isinstance(html, TABLE):
            return self.parse_table(html)
        elif isinstance(html, A):
            return self.parse_a(html)
        elif isinstance(html, P):
            return self.parse_p(html)
        elif isinstance(html, IMG):
            return self.parse_img(html)
        elif isinstance(html, DIV):
            return self.parse_div(html)
        elif (isinstance(html, str) or isinstance(html, lazyT)):
            if title:
                para = [Paragraph(html, self.boldstyle)]
            else:
                para = [Paragraph(html, self.normalstyle)]
            self.normalstyle = self.plainstyle
            return para
        return None

    def exclude_tag(self, html):
        try:
            if html.attributes["_class"] in self.exclude_class_list:
                return True
            if html.attributes["_class"] in self.style_lookup:
                self.normalstyle = self.style_lookup[html.attributes["_class"]]
        except:
            pass
        return False

    def parse_div (self,
                   html
                  ):
        content = []
        for component in html.components:
            result = self.select_tag(component)
            if result != None:
                content += result
        if content == []:
            return None
        return content

    def parse_a (self,
                 html
                ):
        content = []
        for component in html.components:
            result = self.select_tag(component)
            if result != None:
                content += result
        if content == []:
            return None
        return content

    def parse_img (self,
                   html
                  ):
        import os
        I = None
        from reportlab.platypus import Image
        if "_src" in html.attributes:
            src = html.attributes["_src"]
            if os.path.exists(src):
                I = Image(src)
            else:
                src = src.rsplit("/",1)
                src = os.path.join(current.request.folder,"uploads/", src[1])
                if os.path.exists(src):
                    I = Image(src)
        if not I:
            return None

        iwidth = I.drawWidth
        iheight = I.drawHeight
        # @todo: extract the number from a 60px value
#        if "_height" in html.attributes:
#            height = int(html.attributes["_height"]) * inch / 80.0
#            width = iwidth * (height/iheight)
#        elif "_width" in html.attributes:
#            width = int(html.attributes["_width"]) * inch / 80.0
#            height = iheight * (width/iwidth)
#        else:
#            height = 1.0 * inch
#            width = iwidth * (height/iheight)
        height = 1.0 * inch
        width = iwidth * (height/iheight)
        I.drawHeight = height
        I.drawWidth = width
        return [I]


    def parse_p (self, html):
        content = []
        for component in html.components:
            result = self.select_tag(component)
            if result != None:
                content += result
        if content == []:
            return None
        return content

    def parse_table (self, html):
        style = [("FONTSIZE", (0, 0), (-1, -1), self.fontsize),
                 ("VALIGN", (0, 0), (-1, -1), "TOP"),
                 ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                 ('GRID',(0,0),(-1,-1),0.5,colors.grey),
                ]
        content = []
        rowCnt = 0
        result = None
        for component in html.components:
            if self.exclude_tag(component):
                continue
            if isinstance(component,TR):
                result = self.parse_tr(component, style, rowCnt)
                rowCnt += 1
            if result != None:
                content.append(result)
        if content == []:
            return None
        table = Table(content,
                      style=style,
                      hAlign="LEFT",
                      vAlign="Top",
                     )
        cw = table._colWidths
        return [table]

    def parse_tr (self, html, style, rowCnt):
        row = []
        colCnt = 0
        for component in html.components:
            if isinstance(component,(TH,TD)):
                if self.exclude_tag(component):
                    continue
                colspan = 1
                if "_colspan" in component.attributes:
                    colspan = component.attributes["_colspan"]
                if component.components == []:
                    row.append("")
                else:
                    for detail in component.components:
                        result = self.select_tag(detail, title=isinstance(component,TH))
                        if result != None:
                            row.append(result)
                            if isinstance(component,TH):
                                style.append(("BACKGROUND", (colCnt, rowCnt), (colCnt, rowCnt), colors.lightgrey))
                                style.append(("FONTNAME", (colCnt, rowCnt), (colCnt, rowCnt), "Helvetica-Bold"))
                            if colspan > 1:
                                for i in xrange(1,colspan):
                                    row.append("")
                                style.append(("SPAN", (colCnt, rowCnt), (colCnt+colspan-1, rowCnt)))
                                colCnt += colspan
                            else:
                                colCnt += 1
        if row == []:
            return None
        return row

# end of class S3html2pdf
