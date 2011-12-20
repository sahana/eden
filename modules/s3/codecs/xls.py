# -*- coding: utf-8 -*-

"""
    S3 Microsoft Excel codec

    @author: Dominic König <dominic[at]aidiq.com>

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

__all__ = ["S3XLS"]

try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO

from gluon import *
from gluon import current
from gluon.storage import Storage
from gluon.contenttype import contenttype
try:
    from lxml import etree
except ImportError:
    import sys
    print >> sys.stderr, "ERROR: lxml module needed for XML handling"
    raise

from ..s3codec import S3Codec

# =============================================================================

class S3XLS(S3Codec):
    """
        Simple Microsoft Excel format codec
    """

    # Customizable styles
    COL_WIDTH_MULTIPLIER = 360
    LARGE_HEADER_COLOUR = 0x2C
    HEADER_COLOUR = 0x2C
    SUB_HEADER_COLOUR = 0x18
    ROW_ALTERNATING_COLOURS = [0x2A, 0x2B]

    # -------------------------------------------------------------------------
    def __init__(self):
        """
            Constructor
        """

        # Error codes
        T = current.T
        self.ERROR = Storage(
            XLWT_ERROR = T("ERROR: Running Python needs the xlwt module installed for XLS export")
        )


    # -------------------------------------------------------------------------
    def encode(self, resource, list_fields=None, report_groupby=None):
        """
            Export a resource as Microsoft Excel spreadsheet

            @param resource: the resource
            @param list_fields: fields to include in list views
            @param report_groupby: a Field object of the field to group the records by
        """

        manager = current.manager

        # Try import xlwt
        try:
            import xlwt
        except ImportError:
            manager.session.error = self.ERROR.XLWT_ERROR
            redirect(URL(extension=""))

        # Environment
        db = current.db
        session = current.session
        request = current.request
        response = current.response

        # Date/Time formats from L10N deployment settings
        settings = current.deployment_settings
        date_format = S3XLS.dt_format_translate(settings.get_L10n_date_format())
        time_format = S3XLS.dt_format_translate(settings.get_L10n_time_format())
        datetime_format = S3XLS.dt_format_translate(settings.get_L10n_datetime_format())

        # List fields
        if not list_fields:
            fields = resource.readable_fields()
            list_fields = [f.name for f in fields if f != "id"]
        indices = manager.model.indices
        list_fields = [f for f in list_fields if f not in indices]

        # Filter and orderby
        if response.s3.filter is not None:
            resource.add_filter(response.s3.filter)
        orderby = report_groupby

        # Retrieve the resource contents
        crud = resource.crud
        table = resource.table
        lfields, joins = crud.get_list_fields(table, list_fields)
        fields = [f for f in lfields if f.show]
        #headers = [f.label for f in lfields if f.show]
        items = crud.sqltable(fields=list_fields,
                              start=None,
                              limit=None,
                              orderby=orderby,
                              no_ids=True,
                              as_page=True)

        if items is None:
            items = []

        # Initialize output
        output = StringIO()

        # Create the workbook and a sheet in it
        book = xlwt.Workbook(encoding="utf-8")
        sheet1 = book.add_sheet(str(table))

        # Styles
        styleLargeHeader = xlwt.XFStyle()
        styleLargeHeader.font.bold = True
        styleLargeHeader.font.height = 400
        styleLargeHeader.alignment.horz = styleLargeHeader.alignment.HORZ_CENTER
        styleLargeHeader.pattern.pattern = styleLargeHeader.pattern.SOLID_PATTERN
        styleLargeHeader.pattern.pattern_fore_colour = S3XLS.LARGE_HEADER_COLOUR

        styleHeader = xlwt.XFStyle()
        styleHeader.font.bold = True
        styleHeader.num_format_str = datetime_format
        styleHeader.pattern.pattern = styleHeader.pattern.SOLID_PATTERN
        styleHeader.pattern.pattern_fore_colour = S3XLS.HEADER_COLOUR

        styleSubHeader = xlwt.XFStyle()
        styleSubHeader.font.bold = True
        styleSubHeader.pattern.pattern = styleHeader.pattern.SOLID_PATTERN
        styleSubHeader.pattern.pattern_fore_colour = S3XLS.SUB_HEADER_COLOUR

        styleOdd = xlwt.XFStyle()
        styleOdd.pattern.pattern = styleOdd.pattern.SOLID_PATTERN
        styleOdd.pattern.pattern_fore_colour = S3XLS.ROW_ALTERNATING_COLOURS[0]

        styleEven = xlwt.XFStyle()
        styleEven.pattern.pattern = styleEven.pattern.SOLID_PATTERN
        styleEven.pattern.pattern_fore_colour = S3XLS.ROW_ALTERNATING_COLOURS[1]

        # Initialize counters
        rowCnt = 0
        colCnt = 0

        # Title row
        currentRow = sheet1.row(rowCnt)
        totalRows = len(fields)-1
        if report_groupby != None:
            totalRows -= 1

        # Use the title_list CRUD string for the title
        name = "title_list"
        s3 = response.s3
        tablename = resource.tablename
        crud_strings = s3.crud_strings.get(tablename, s3.crud_strings)
        not_found = s3.crud_strings.get(name, request.function)
        title = str(crud_strings.get(name, not_found))

        sheet1.write_merge(rowCnt, rowCnt, 0, totalRows-1, title, styleLargeHeader)
        currentRow.write(totalRows, request.now, styleHeader)
        currentRow.height = 440
        rowCnt += 1
        currentRow = sheet1.row(rowCnt)

        # Header row
        fieldWidth=[]
        for field in fields:
            if report_groupby != None:
                if field.label == report_groupby.label:
                    continue
            currentRow.write(colCnt, str(field.label), styleHeader)
            width=len(field.label)*S3XLS.COL_WIDTH_MULTIPLIER
            fieldWidth.append(width)
            sheet1.col(colCnt).width = width
            colCnt += 1

        # fix the size of the last column to display the date
        if 16*S3XLS.COL_WIDTH_MULTIPLIER > width:
            sheet1.col(totalRows).width = 16*S3XLS.COL_WIDTH_MULTIPLIER

        subheading = None
        for item in items:
            # Item details
            rowCnt += 1
            currentRow = sheet1.row(rowCnt)
            colCnt = 0
            if rowCnt%2 == 0:
                style = styleEven
            else:
                style = styleOdd
            for field in fields:
                represent = item[colCnt]
                # Strip away markup from representation
                try:
                    markup = etree.XML(str(represent))
                    text = markup.xpath(".//text()")
                    if text:
                        text = " ".join(text)
                    else:
                        text = ""
                    represent = text
                except:
                    pass
                if report_groupby != None:
                    if field.label == report_groupby.label:
                        if subheading != represent:
                            subheading = represent
                            sheet1.write_merge(rowCnt, rowCnt, 0, totalRows,
                                               represent, styleSubHeader)
                            rowCnt += 1
                            currentRow = sheet1.row(rowCnt)
                            if rowCnt%2 == 0:
                                style = styleEven
                            else:
                                style = styleOdd
                        continue
                if field.colname:
                    tab, col = field.colname.split(".")
                try:
                    # Check for Date formats
                    coltype = db[tab][col].type
                    if coltype == "date":
                        style.num_format_str = date_format
                    elif coltype == "datetime":
                        style.num_format_str = datetime_format
                    elif coltype == "time":
                        style.num_format_str = time_format
                except:
                    pass
                currentRow.write(colCnt, unicode(represent), style)
                width = len(unicode(represent))*S3XLS.COL_WIDTH_MULTIPLIER
                if width > fieldWidth[colCnt]:
                    fieldWidth[colCnt] = width
                    sheet1.col(colCnt).width = width
                colCnt += 1
        sheet1.panes_frozen = True
        sheet1.horz_split_pos = 2
        book.save(output)

        # Response headers
        filename = "%s_%s.xls" % (request.env.server_name, str(table))
        disposition = "attachment; filename=\"%s\"" % filename
        response.headers["Content-Type"] = contenttype(".xls")
        response.headers["Content-disposition"] = disposition

        output.seek(0)
        return output.read()

    # -------------------------------------------------------------------------
    @staticmethod
    def dt_format_translate(pyfmt):
        """
            Translate a Python datetime format string into an
            Excel datetime format string

            @param pyfmt: the Python format string
        """

        translate = {"%a": "ddd",
                     "%A": "dddd",
                     "%b": "mmm",
                     "%B": "mmmm",
                     "%c": "",
                     "%d": "dd",
                     "%f": "",
                     "%H": "hh",
                     "%I": "hh",
                     "%j": "",
                     "%m": "mm",
                     "%M": "mm",
                     "%p": "AM/PM",
                     "%S": "ss",
                     "%U": "",
                     "%w": "",
                     "%W": "",
                     "%x": "",
                     "%X": "",
                     "%y": "yy",
                     "%Y": "yyyy",
                     "%z": "",
                     "%Z": "",
                     "%%": "%"}

        xlfmt = str(pyfmt)

        for item in translate:
            if item in xlfmt:
                xlfmt = xlfmt.replace(item, translate[item])
        return xlfmt

# End =========================================================================
