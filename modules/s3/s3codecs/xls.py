# -*- coding: utf-8 -*-

"""
    S3 Microsoft Excel codec

    @copyright: 2011-15 (c) Sahana Software Foundation
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
    SUB_TOTALS_COLOUR = 0x96
    TOTALS_COLOUR = 0x00
    ROW_ALTERNATING_COLOURS = [0x2A, 0x2B]

    ERROR = Storage(
        XLRD_ERROR = "XLS export requires python-xlrd module to be installed on server",
        XLWT_ERROR = "XLS export requires python-xlwt module to be installed on server",
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
                                as a spreadsheet, can be either of:
                                1) an S3Resource
                                2) an array of value dicts (dict of
                                   column labels as first item, list of
                                   field types as second item)
                                3) a dict like:
                                   {columns: [key, ...],
                                    headers: {key: label},
                                    types: {key: type},
                                    rows: [{key:value}],
                                    }
            @param attr: keyword parameters

            @keyword title: the main title of the report
            @keyword list_fields: fields to include in list views
            @keyword report_groupby: used to create a grouping of the result:
                                     either a Field object of the resource
                                     or a string which matches a value in
                                     the heading
            @keyword use_colour: True to add colour to the cells, default False
            @keyword evenodd: render different background colours
                              for even/odd rows ("stripes")
        """

        # Do not redirect from here!
        # ...but raise proper status code, which can be caught by caller
        try:
            import xlwt
        except ImportError:
            error = self.ERROR.XLWT_ERROR
            current.log.error(error)
            raise HTTP(503, body=error)
        try:
            from xlrd.xldate import xldate_from_date_tuple, \
                                    xldate_from_time_tuple, \
                                    xldate_from_datetime_tuple
        except ImportError:
            error = self.ERROR.XLRD_ERROR
            current.log.error(error)
            raise HTTP(503, body=error)

        import datetime

        request = current.request

        # The xlwt library supports a maximum of 182 characters in a single cell
        max_cell_size = 182

        COL_WIDTH_MULTIPLIER = self.COL_WIDTH_MULTIPLIER

        # Get the attributes
        title = attr.get("title")
        list_fields = attr.get("list_fields")
        group = attr.get("dt_group")
        use_colour = attr.get("use_colour", False)
        evenodd = attr.get("evenodd", True)

        # Extract the data from the data_source
        if isinstance(data_source, dict):
            headers = data_source.get("headers", {})
            lfields = data_source.get("columns", list_fields)
            column_types = data_source.get("types")
            types = [column_types[col] for col in lfields]
            rows = data_source.get("rows")
        elif isinstance(data_source, (list, tuple)):
            headers = data_source[0]
            types = data_source[1]
            rows = data_source[2:]
            lfields = list_fields
        else:
            if not list_fields:
                list_fields = data_source.list_fields()
            (title, types, lfields, headers, rows) = self.extractResource(data_source,
                                                                          list_fields)
        report_groupby = lfields[group] if group else None
        if len(rows) > 0 and len(lfields) > len(rows[0]):
            msg = """modules/s3/codecs/xls: There is an error in the list items, a field doesn't exist
requesting url %s
Headers = %d, Data Items = %d
Headers     %s
List Fields %s""" % (request.url, len(lfields), len(rows[0]), headers, lfields)
            current.log.error(msg)

        groupby_label = headers[report_groupby] if report_groupby else None

        # Date/Time formats from L10N deployment settings
        settings = current.deployment_settings
        date_format = settings.get_L10n_date_format()
        date_format_str = str(date_format)

        dt_format_translate = self.dt_format_translate
        date_format = dt_format_translate(date_format)
        time_format = dt_format_translate(settings.get_L10n_time_format())
        datetime_format = dt_format_translate(settings.get_L10n_datetime_format())

        # Get styles
        styles = self._styles(use_colour = use_colour,
                              evenodd = evenodd,
                              datetime_format = datetime_format,
                              )

        # Create the workbook
        book = xlwt.Workbook(encoding="utf-8")

        # Add a sheet
        # Can't have a / in the sheet_name, so replace any with a space
        sheet_name = str(title.replace("/", " "))
        # sheet_name cannot be over 31 chars
        if len(sheet_name) > 31:
            sheet_name = sheet_name[:31]
        sheets = []
        rowLimit = 65536 #.xls exports are limited to 65536 rows per sheet, we bypass this by creating multiple sheets
        sheetnum = len(rows) / rowLimit
        count = 1
        while len(sheets) <= sheetnum:
            sheets.append(book.add_sheet('%s-%s' % (sheet_name, count)))
            count += 1

        header_style = styles["header"]
        for sheet in sheets:
            # Header row
            colCnt = 0
            # Move this down if a title row will be added
            if settings.get_xls_title_row():
                headerRow = sheet.row(2)
            else:
                headerRow = sheet.row(0)
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
                headerRow.write(writeCol, str(label), header_style)
                width = max(len(label) * COL_WIDTH_MULTIPLIER, 2000)
                width = min(width, 65535) # USHRT_MAX
                fieldWidths.append(width)
                sheet.col(writeCol).width = width
                colCnt += 1

        # Title row (optional, deployment setting)
        if settings.get_xls_title_row():
            large_header_style = styles["large_header"]
            notes_style = style["notes"]
            for sheet in sheets:
                # First row => Title (standard = "title_list" CRUD string)
                currentRow = sheet.row(0)
                if colCnt > 0:
                    sheet.write_merge(0, 0, 0, colCnt, str(title),
                                      large_header_style,
                                      )
                currentRow.height = 500
                # Second row => Export date/time
                currentRow = sheet.row(1)
                currentRow.write(0, str(current.T("Date Exported:")), notes_style)
                currentRow.write(1, request.now, notes_style)
                # Fix the size of the last column to display the date
                if 16 * COL_WIDTH_MULTIPLIER > width:
                    sheet.col(colCnt).width = 16 * COL_WIDTH_MULTIPLIER

        # Initialize counters
        totalCols = colCnt
        # Move the rows down if a title row is included
        if settings.get_xls_title_row():
            rowCnt = 2
        else:
            rowCnt = 0

        def get_current_row(row_count, row_limit):

            sheet_count = int(row_count / row_limit)
            row_number = row_count - (sheet_count * row_limit)
            if sheet_count > 0:
                row_number += 1
            return sheets[sheet_count], sheets[sheet_count].row(row_number)

        subheading = None
        odd_style = styles["odd"]
        even_style = styles["even"]
        subheader_style = styles["subheader"]
        for row in rows:

            # Row to write to
            rowCnt += 1
            currentSheet, currentRow = get_current_row(rowCnt, rowLimit)
            style = even_style if rowCnt % 2 == 0 else odd_style

            # Group headers
            if report_groupby:
                represent = s3_strip_markup(s3_unicode(row[report_groupby]))
                if subheading != represent:
                    # Start of new group - write group header
                    subheading = represent
                    currentSheet.write_merge(rowCnt, rowCnt, 0, totalCols,
                                             subheading,
                                             subheader_style,
                                             )
                    # Next row
                    rowCnt += 1
                    currentSheet, currentRow = get_current_row(rowCnt, rowLimit)
                    style = even_style if rowCnt % 2 == 0 else odd_style

            colCnt = 0
            remaining_fields = lfields

            # Custom row style?
            row_style = None
            if "_style" in row:
                stylename = row["_style"]
                if stylename in styles:
                    row_style = styles[stylename]

            # Group header/footer row?
            if "_group" in row:
                group_info = row["_group"]
                label = group_info.get("label")
                totals = group_info.get("totals")
                if label:
                    label = s3_strip_markup(s3_unicode(label))
                    style = row_style or subheader_style
                    span = group_info.get("span")
                    if span == 0:
                        currentSheet.write_merge(rowCnt, rowCnt, 0, totalCols - 1,
                                                 label,
                                                 style,
                                                 )
                        if totals:
                            # Write totals into the next row
                            rowCnt += 1
                            currentSheet, currentRow = get_current_row(rowCnt, rowLimit)
                    else:
                        currentSheet.write_merge(rowCnt, rowCnt, 0, span - 1,
                                                 label,
                                                 style,
                                                 )
                        colCnt = span
                        remaining_fields = lfields[span:]
                if not totals:
                    continue

            for field in remaining_fields:
                label = headers[field]
                if label == groupby_label:
                    continue
                if label == "Id":
                    # Skip the ID column from XLS exports
                    colCnt += 1
                    continue

                if field not in row:
                    represent = ""
                else:
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
                    currentSheet.col(writeCol).width = width
                colCnt += 1
        for sheet in sheets:
            sheet.panes_frozen = True
            sheet.horz_split_pos = 1

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
                     }

        PERCENT = "__percent__"
        xlfmt = str(pyfmt).replace("%%", PERCENT)

        for tag, translation in translate.items():
            xlfmt = xlfmt.replace(tag, translation)

        return xlfmt.replace(PERCENT, "%")

    # -------------------------------------------------------------------------
    @classmethod
    def _styles(cls,
                use_colour=False,
                evenodd=True,
                datetime_format=None,
                ):
        """
            XLS encoder standard cell styles

            @param use_colour: use background colour in cells
            @param evenodd: render different background colours
                            for even/odd rows ("stripes")
            @param datetime_format: the date/time format
        """

        import xlwt

        # Styles
        large_header = xlwt.XFStyle()
        large_header.font.bold = True
        large_header.font.height = 400
        if use_colour:
            large_header.alignment.horz = large_header.alignment.HORZ_CENTER
            large_header.pattern.pattern = large_header.pattern.SOLID_PATTERN
            large_header.pattern.pattern_fore_colour = cls.LARGE_HEADER_COLOUR

        notes = xlwt.XFStyle()
        notes.font.italic = True
        notes.font.height = 160 # 160 Twips = 8 point
        notes.num_format_str = datetime_format

        header = xlwt.XFStyle()
        header.font.bold = True
        header.num_format_str = datetime_format
        if use_colour:
            header.pattern.pattern = header.pattern.SOLID_PATTERN
            header.pattern.pattern_fore_colour = cls.HEADER_COLOUR

        subheader = xlwt.XFStyle()
        subheader.font.bold = True
        if use_colour:
            subheader.pattern.pattern = subheader.pattern.SOLID_PATTERN
            subheader.pattern.pattern_fore_colour = cls.SUB_HEADER_COLOUR

        subtotals = xlwt.XFStyle()
        subtotals.font.bold = True
        if use_colour:
            subtotals.pattern.pattern = subtotals.pattern.SOLID_PATTERN
            subtotals.pattern.pattern_fore_colour = cls.SUB_TOTALS_COLOUR

        totals = xlwt.XFStyle()
        totals.font.bold = True
        if use_colour:
            totals.pattern.pattern = totals.pattern.SOLID_PATTERN
            totals.pattern.pattern_fore_colour = cls.TOTALS_COLOUR

        odd = xlwt.XFStyle()
        if use_colour and evenodd:
            odd.pattern.pattern = odd.pattern.SOLID_PATTERN
            odd.pattern.pattern_fore_colour = cls.ROW_ALTERNATING_COLOURS[0]

        even = xlwt.XFStyle()
        if use_colour and evenodd:
            even.pattern.pattern = even.pattern.SOLID_PATTERN
            even.pattern.pattern_fore_colour = cls.ROW_ALTERNATING_COLOURS[1]

        return {"large_header": large_header,
                "notes": notes,
                "header": header,
                "subheader": subheader,
                "subtotals": subtotals,
                "totals": totals,
                "odd": odd,
                "even": even,
                }

# =============================================================================
class S3HTML2XLS():
    """
        Class that takes HTML in the form of web2py helper objects
        and converts it to XLS

        @ToDo: Complete this (e.g. start with a copy of S3html2pdf)
        See https://gist.github.com/JustOnce/2be3e4d951a66c22c5e0
        & http://pydoc.net/Python/Kiowa/0.2w.rc9/kiowa.utils.xls.html2xls/

        Places  to use this:
            org_CapacityReport()
    """

    def __init__(self):

        pass

    # -------------------------------------------------------------------------
    def parse(self, html):
        """
            Entry point for class
        """

        return None

# END =========================================================================
