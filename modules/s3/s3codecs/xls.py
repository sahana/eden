# -*- coding: utf-8 -*-

"""
    S3 Microsoft Excel codec

    @copyright: 2011-14 (c) Sahana Software Foundation
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

__all__ = ("S3XLS",)

try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO

from gluon import *
from gluon.contenttype import contenttype
from gluon.storage import Storage

from ..s3codec import S3Codec
from ..s3utils import s3_unicode, s3_strip_markup

# =============================================================================
class S3XLS(S3Codec):
    """
        Simple Microsoft Excel format codec
    """

    # Customizable styles
    COL_WIDTH_MULTIPLIER = 310
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
            XLRD_ERROR = "Python needs the xlrd module installed for XLS export",
            XLWT_ERROR = "Python needs the xlwt module installed for XLS export"
        )

    # -------------------------------------------------------------------------
    def extractResource(self, resource, list_fields):
        """
            Extract the rows from the resource

            @param resource: the resource
            @param list_fields: fields to include in list views
        """

        title = self.crud_string(resource.tablename, "title_list")

        vars = Storage(current.request.vars)
        vars["iColumns"] = len(list_fields)
        filter, orderby, left = resource.datatable_filter(list_fields, vars)
        resource.add_filter(filter)

        if orderby is None:
            orderby = resource.get_config("orderby", None)

        result = resource.select(list_fields,
                                 left=left,
                                 limit=None,
                                 count=True,
                                 getids=True,
                                 orderby=orderby,
                                 represent=True,
                                 show_links=False)

        rfields = result["rfields"]
        rows = result["rows"]

        types = []
        lfields = []
        heading = {}
        for rfield in rfields:
            if rfield.show:
                lfields.append(rfield.colname)
                heading[rfield.colname] = rfield.label
                if rfield.ftype == "virtual":
                    types.append("string")
                else:
                    types.append(rfield.ftype)

        return (title, types, lfields, heading, rows)

    # -------------------------------------------------------------------------
    def encode(self, data_source, **attr):
        """
            Export data as a Microsoft Excel spreadsheet

            @param data_source: the source of the data that is to be encoded
                                as a spreadsheet. This may be:
                                resource: the resource
                                item:     a list of pre-fetched values
                                          the headings are in the first row
                                          the data types are in the second row
            @param attr: dictionary of parameters:
                 * title:          The main title of the report
                 * list_fields:    Fields to include in list views
                 * report_groupby: Used to create a grouping of the result:
                                   either a Field object of the resource
                                   or a string which matches a value in the heading
                 * use_colour:     True to add colour to the cells. default False
        """

        request = current.request

        import datetime
        try:
            import xlwt
        except ImportError:
            from ..s3rest import S3Request
            if current.auth.permission.format in S3Request.INTERACTIVE_FORMATS:
                current.session.error = self.ERROR.XLWT_ERROR
                redirect(URL(extension=""))
            else:
                error = self.ERROR.XLWT_ERROR
                current.log.error(error)
                return error
        try:
            from xlrd.xldate import xldate_from_date_tuple, \
                                    xldate_from_time_tuple, \
                                    xldate_from_datetime_tuple
        except ImportError:
            from ..s3rest import S3Request
            if current.auth.permission.format in S3Request.INTERACTIVE_FORMATS:
                current.session.error = self.ERROR.XLRD_ERROR
                redirect(URL(extension=""))
            else:
                error = self.ERROR.XLRD_ERROR
                current.log.error(error)
                return error

        # The xlwt library supports a maximum of 182 characters in a single cell
        max_cell_size = 182

        COL_WIDTH_MULTIPLIER = S3XLS.COL_WIDTH_MULTIPLIER

        # Get the attributes
        title = attr.get("title")
        list_fields = attr.get("list_fields")
        if not list_fields:
            list_fields = data_source.list_fields()
        group = attr.get("dt_group")
        use_colour = attr.get("use_colour", False)

        # Extract the data from the data_source
        if isinstance(data_source, (list, tuple)):
            headers = data_source[0]
            types = data_source[1]
            rows = data_source[2:]
        else:
            (title, types, lfields, headers, rows) = self.extractResource(data_source,
                                                                          list_fields)
        report_groupby = lfields[group] if group else None
        if len(rows) > 0 and len(headers) != len(rows[0]):
            msg = """modules/s3/codecs/xls: There is an error in the list_items, a field doesn't exist"
requesting url %s
Headers = %d, Data Items = %d
Headers     %s
List Fields %s""" % (request.url, len(headers), len(items[0]), headers, list_fields)
            current.log.error(msg)
        groupby_label = headers[report_groupby] if report_groupby else None

        # Date/Time formats from L10N deployment settings
        settings = current.deployment_settings
        date_format = settings.get_L10n_date_format()
        date_format_str = str(date_format)
        date_format = S3XLS.dt_format_translate(date_format)
        time_format = S3XLS.dt_format_translate(settings.get_L10n_time_format())
        datetime_format = S3XLS.dt_format_translate(settings.get_L10n_datetime_format())

        # Create the workbook
        book = xlwt.Workbook(encoding="utf-8")

        # Add a sheet
        # Can't have a / in the sheet_name, so replace any with a space
        sheet_name = str(title.replace("/", " "))
        # sheet_name cannot be over 31 chars
        if len(sheet_name) > 31:
            sheet_name = sheet_name[:31]
        sheet1 = book.add_sheet(sheet_name)

        # Styles
        styleLargeHeader = xlwt.XFStyle()
        styleLargeHeader.font.bold = True
        styleLargeHeader.font.height = 400
        if use_colour:
            styleLargeHeader.alignment.horz = styleLargeHeader.alignment.HORZ_CENTER
            styleLargeHeader.pattern.pattern = styleLargeHeader.pattern.SOLID_PATTERN
            styleLargeHeader.pattern.pattern_fore_colour = S3XLS.LARGE_HEADER_COLOUR

        styleNotes = xlwt.XFStyle()
        styleNotes.font.italic = True
        styleNotes.font.height = 160 # 160 Twips = 8 point
        styleNotes.num_format_str = datetime_format

        styleHeader = xlwt.XFStyle()
        styleHeader.font.bold = True
        styleHeader.num_format_str = datetime_format
        if use_colour:
            styleHeader.pattern.pattern = styleHeader.pattern.SOLID_PATTERN
            styleHeader.pattern.pattern_fore_colour = S3XLS.HEADER_COLOUR

        styleSubHeader = xlwt.XFStyle()
        styleSubHeader.font.bold = True
        if use_colour:
            styleSubHeader.pattern.pattern = styleHeader.pattern.SOLID_PATTERN
            styleSubHeader.pattern.pattern_fore_colour = S3XLS.SUB_HEADER_COLOUR

        styleOdd = xlwt.XFStyle()
        if use_colour:
            styleOdd.pattern.pattern = styleOdd.pattern.SOLID_PATTERN
            styleOdd.pattern.pattern_fore_colour = S3XLS.ROW_ALTERNATING_COLOURS[0]

        styleEven = xlwt.XFStyle()
        if use_colour:
            styleEven.pattern.pattern = styleEven.pattern.SOLID_PATTERN
            styleEven.pattern.pattern_fore_colour = S3XLS.ROW_ALTERNATING_COLOURS[1]

        # Header row
        colCnt = 0
        #headerRow = sheet1.row(2)
        headerRow = sheet1.row(0)
        fieldWidths = []
        id = False
        for selector in lfields:
            if selector == report_groupby:
                continue
            label = headers[selector]
            if label == "Id":
                # Indicate to adjust colCnt when writing out
                id = True
                fieldWidths.append(0)
                colCnt += 1
                continue
            if label == "Sort":
                continue
            if id:
                # Adjust for the skipped column
                writeCol = colCnt - 1
            else:
                writeCol = colCnt
            headerRow.write(writeCol, str(label), styleHeader)
            width = max(len(label) * COL_WIDTH_MULTIPLIER, 2000)
            #width = len(label) * COL_WIDTH_MULTIPLIER
            fieldWidths.append(width)
            sheet1.col(writeCol).width = width
            colCnt += 1
        # Title row
        # - has been removed to allow columns to be easily sorted post-export.
        # - add deployment_setting if an Org wishes a Title Row
        # currentRow = sheet1.row(0)
        # if colCnt > 0:
            # sheet1.write_merge(0, 0, 0, colCnt, str(title),
                               # styleLargeHeader)
        # currentRow.height = 500
        # currentRow = sheet1.row(1)
        # currentRow.write(0, str(current.T("Date Exported:")), styleNotes)
        # currentRow.write(1, request.now, styleNotes)
        # Fix the size of the last column to display the date
        #if 16 * COL_WIDTH_MULTIPLIER > width:
        #    sheet1.col(colCnt).width = 16 * COL_WIDTH_MULTIPLIER

        # Initialize counters
        totalCols = colCnt
        #rowCnt = 2
        rowCnt = 0

        subheading = None
        for row in rows:
            # Item details
            rowCnt += 1
            currentRow = sheet1.row(rowCnt)
            colCnt = 0
            if rowCnt % 2 == 0:
                style = styleEven
            else:
                style = styleOdd
            if report_groupby:
                represent = s3_strip_markup(s3_unicode(row[report_groupby]))
                if subheading != represent:
                    subheading = represent
                    sheet1.write_merge(rowCnt, rowCnt, 0, totalCols,
                                       subheading, styleSubHeader)
                    rowCnt += 1
                    currentRow = sheet1.row(rowCnt)
                    if rowCnt % 2 == 0:
                        style = styleEven
                    else:
                        style = styleOdd

            for field in lfields:
                label = headers[field]
                if label == groupby_label:
                    continue
                if label == "Id":
                    # Skip the ID column from XLS exports
                    colCnt += 1
                    continue
                represent = s3_strip_markup(s3_unicode(row[field]))
                coltype = types[colCnt]
                if coltype == "sort":
                    continue
                if len(represent) > max_cell_size:
                    represent = represent[:max_cell_size]
                value = represent
                if coltype == "date":
                    try:
                        cell_datetime = datetime.datetime.strptime(value,
                                                                   date_format_str)
                        date_tuple = (cell_datetime.year,
                                      cell_datetime.month,
                                      cell_datetime.day)
                        value = xldate_from_date_tuple(date_tuple, 0)
                        style.num_format_str = date_format
                    except:
                        pass
                elif coltype == "datetime":
                    try:
                        cell_datetime = datetime.datetime.strptime(value,
                                                                   date_format_str)
                        date_tuple = (cell_datetime.year,
                                      cell_datetime.month,
                                      cell_datetime.day,
                                      cell_datetime.hour,
                                      cell_datetime.minute,
                                      cell_datetime.second)
                        value = xldate_from_datetime_tuple(date_tuple, 0)
                        style.num_format_str = datetime_format
                    except:
                        pass
                elif coltype == "time":
                    try:
                        cell_datetime = datetime.datetime.strptime(value,
                                                                   date_format_str)
                        date_tuple = (cell_datetime.hour,
                                      cell_datetime.minute,
                                      cell_datetime.second)
                        value = xldate_from_time_tuple(date_tuple)
                        style.num_format_str = time_format
                    except:
                        pass
                elif coltype == "integer":
                    try:
                        value = int(value)
                        style.num_format_str = "0"
                    except:
                        pass
                elif coltype == "double":
                    try:
                        value = float(value)
                        style.num_format_str = "0.00"
                    except:
                        pass
                if id:
                    # Adjust for the skipped column
                    writeCol = colCnt - 1
                else:
                    writeCol = colCnt
                currentRow.write(writeCol, value, style)
                width = len(represent) * COL_WIDTH_MULTIPLIER
                if width > fieldWidths[colCnt]:
                    fieldWidths[colCnt] = width
                    sheet1.col(writeCol).width = width
                colCnt += 1
        sheet1.panes_frozen = True
        #sheet1.horz_split_pos = 3
        sheet1.horz_split_pos = 1

        output = StringIO()
        book.save(output)

        # Response headers
        filename = "%s_%s.xls" % (request.env.server_name, str(title))
        disposition = "attachment; filename=\"%s\"" % filename
        response = current.response
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
                     "%%": "%",
                     }

        xlfmt = str(pyfmt)

        for item in translate:
            if item in xlfmt:
                xlfmt = xlfmt.replace(item, translate[item])
        return xlfmt

# End =========================================================================
