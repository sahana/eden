# -*- coding: utf-8 -*-

"""
    S3 Microsoft Excel codec

    @copyright: 2011-2016 (c) Sahana Software Foundation
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

__all__ = ("S3XLS",
           )

try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO

from gluon import *
from gluon.contenttype import contenttype
from gluon.storage import Storage

from ..s3codec import S3Codec
from ..s3utils import s3_str, s3_strip_markup, s3_unicode

# =============================================================================
class S3XLS(S3Codec):
    """
        Simple Microsoft Excel format codec
    """

    # The xlwt library supports a maximum of 182 characters in a single cell
    MAX_CELL_SIZE = 182

    # Customizable styles
    COL_WIDTH_MULTIPLIER = 310
    # Python xlwt Colours
    # https://docs.google.com/spreadsheets/d/1ihNaZcUh7961yU7db1-Db0lbws4NT24B7koY8v8GHNQ/pubhtml?gid=1072579560&single=true
    LARGE_HEADER_COLOUR = 0x2C # pale_blue
    HEADER_COLOUR = 0x2C # pale_blue
    SUB_HEADER_COLOUR = 0x18 # periwinkle
    SUB_TOTALS_COLOUR = 0x96
    TOTALS_COLOUR = 0x00
    ROW_ALTERNATING_COLOURS = [0x2A, # light_green
                               0x2B, # light_yellow
                               ]

    ERROR = Storage(
        XLRD_ERROR = "XLS export requires python-xlrd module to be installed on server",
        XLWT_ERROR = "XLS export requires python-xlwt module to be installed on server",
    )

    # -------------------------------------------------------------------------
    def extract(self, resource, list_fields):
        """
            Extract the rows from the resource

            @param resource: the resource
            @param list_fields: fields to include in list views
        """

        title = self.crud_string(resource.tablename, "title_list")

        get_vars = dict(current.request.vars)
        get_vars["iColumns"] = len(list_fields)
        query, orderby, left = resource.datatable_filter(list_fields,
                                                         get_vars,
                                                         )
        resource.add_filter(query)

        if orderby is None:
            orderby = resource.get_config("orderby")

        data = resource.select(list_fields,
                               left = left,
                               limit = None,
                               count = True,
                               getids = True,
                               orderby = orderby,
                               represent = True,
                               show_links = False,
                               )

        rfields = data.rfields
        rows = data.rows

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
    def encode(self, data_source, title=None, as_stream=False, **attr):
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
            @param title: the title for the output document
            @param as_stream: return the buffer (StringIO) rather than
                              its contents (str), useful when the output
                              is supposed to be stored locally
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

        MAX_CELL_SIZE = self.MAX_CELL_SIZE
        COL_WIDTH_MULTIPLIER = self.COL_WIDTH_MULTIPLIER

        # Get the attributes
        title = attr.get("title")
        if title is None:
            title = current.T("Report")
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
            (title, types, lfields, headers, rows) = self.extract(data_source,
                                                                  list_fields,
                                                                  )

        # Verify columns in items
        request = current.request
        if len(rows) > 0 and len(lfields) > len(rows[0]):
            msg = """modules/s3/codecs/xls: There is an error in the list items, a field doesn't exist
requesting url %s
Headers = %d, Data Items = %d
Headers     %s
List Fields %s""" % (request.url, len(lfields), len(rows[0]), headers, lfields)
            current.log.error(msg)

        # Grouping
        report_groupby = lfields[group] if group else None
        groupby_label = headers[report_groupby] if report_groupby else None

        # Date/Time formats from L10N deployment settings
        settings = current.deployment_settings
        date_format = settings.get_L10n_date_format()
        date_format_str = str(date_format)

        dt_format_translate = self.dt_format_translate
        date_format = dt_format_translate(date_format)
        time_format = dt_format_translate(settings.get_L10n_time_format())
        datetime_format = dt_format_translate(settings.get_L10n_datetime_format())

        title_row = settings.get_xls_title_row()

        # Get styles
        styles = self._styles(use_colour = use_colour,
                              evenodd = evenodd,
                              datetime_format = datetime_format,
                              )

        # Create the workbook
        book = xlwt.Workbook(encoding="utf-8")

        # Add sheets
        sheets = []
        # XLS exports are limited to 65536 rows per sheet, we bypass
        # this by creating multiple sheets
        row_limit = 65536
        sheetnum = len(rows) / row_limit
        # Can't have a / in the sheet_name, so replace any with a space
        sheet_name = str(title.replace("/", " "))
        if len(sheet_name) > 31:
            # Sheet name cannot be over 31 chars
            # (take sheet number suffix into account)
            sheet_name = sheet_name[:31] if sheetnum == 1 else sheet_name[:28]
        count = 1
        while len(sheets) <= sheetnum:
            sheets.append(book.add_sheet("%s-%s" % (sheet_name, count)))
            count += 1

        if callable(title_row):
            # Calling with sheet None to get the number of title rows
            title_row_length = title_row(None)
        else:
            title_row_length = 2

        # Add header row to all sheets, determine columns widths
        header_style = styles["header"]
        for sheet in sheets:
            # Move this down if a title row will be added
            if title_row:
                header_row = sheet.row(title_row_length)
            else:
                header_row = sheet.row(0)
            column_widths = []
            has_id = False
            col_index = 0
            for selector in lfields:
                if selector == report_groupby:
                    continue
                label = headers[selector]
                if label == "Id":
                    # Indicate to adjust col_index when writing out
                    has_id = True
                    column_widths.append(0)
                    col_index += 1
                    continue
                if label == "Sort":
                    continue
                if has_id:
                    # Adjust for the skipped column
                    write_col_index = col_index - 1
                else:
                    write_col_index = col_index
                header_row.write(write_col_index, str(label), header_style)
                width = max(len(label) * COL_WIDTH_MULTIPLIER, 2000)
                width = min(width, 65535) # USHRT_MAX
                column_widths.append(width)
                sheet.col(write_col_index).width = width
                col_index += 1

        title = s3_str(title)

        # Title row (optional, deployment setting)
        if title_row:
            T = current.T
            large_header_style = styles["large_header"]
            notes_style = styles["notes"]
            for sheet in sheets:
                if callable(title_row):
                    # Custom title rows
                    title_row(sheet)
                else:
                    # First row => Title (standard = "title_list" CRUD string)
                    current_row = sheet.row(0)
                    if col_index > 0:
                        sheet.write_merge(0, 0, 0, col_index,
                                          title,
                                          large_header_style,
                                          )
                    current_row.height = 500
                    # Second row => Export date/time
                    current_row = sheet.row(1)
                    current_row.write(0, "%s:" % T("Date Exported"), notes_style)
                    current_row.write(1, request.now, notes_style)
                    # Fix the size of the last column to display the date
                    if 16 * COL_WIDTH_MULTIPLIER > width:
                        sheet.col(col_index).width = 16 * COL_WIDTH_MULTIPLIER

        # Initialize counters
        totalCols = col_index
        # Move the rows down if a title row is included
        if title_row:
            row_index = title_row_length
        else:
            row_index = 0

        # Helper function to get the current row
        def get_current_row(row_count, row_limit):

            sheet_count = int(row_count / row_limit)
            row_number = row_count - (sheet_count * row_limit)
            if sheet_count > 0:
                row_number += 1
            return sheets[sheet_count], sheets[sheet_count].row(row_number)

        # Write the table contents
        subheading = None
        odd_style = styles["odd"]
        even_style = styles["even"]
        subheader_style = styles["subheader"]
        for row in rows:
            # Current row
            row_index += 1
            current_sheet, current_row = get_current_row(row_index, row_limit)
            style = even_style if row_index % 2 == 0 else odd_style

            # Group headers
            if report_groupby:
                represent = s3_strip_markup(s3_unicode(row[report_groupby]))
                if subheading != represent:
                    # Start of new group - write group header
                    subheading = represent
                    current_sheet.write_merge(row_index, row_index, 0, totalCols,
                                             subheading,
                                             subheader_style,
                                             )
                    # Move on to next row
                    row_index += 1
                    current_sheet, current_row = get_current_row(row_index, row_limit)
                    style = even_style if row_index % 2 == 0 else odd_style

            col_index = 0
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
                        current_sheet.write_merge(row_index,
                                                  row_index,
                                                  0,
                                                  totalCols - 1,
                                                  label,
                                                  style,
                                                  )
                        if totals:
                            # Write totals into the next row
                            row_index += 1
                            current_sheet, current_row = \
                                get_current_row(row_index, row_limit)
                    else:
                        current_sheet.write_merge(row_index,
                                                  row_index,
                                                  0,
                                                  span - 1,
                                                  label,
                                                  style,
                                                  )
                        col_index = span
                        remaining_fields = lfields[span:]
                if not totals:
                    continue

            for field in remaining_fields:
                label = headers[field]
                if label == groupby_label:
                    continue
                if label == "Id":
                    # Skip the ID column from XLS exports
                    col_index += 1
                    continue

                if field not in row:
                    represent = ""
                else:
                    represent = s3_strip_markup(s3_unicode(row[field]))

                coltype = types[col_index]
                if coltype == "sort":
                    continue
                if len(represent) > MAX_CELL_SIZE:
                    represent = represent[:MAX_CELL_SIZE]
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
                if has_id:
                    # Adjust for the skipped column
                    write_col_index = col_index - 1
                else:
                    write_col_index = col_index

                current_row.write(write_col_index, value, style)
                width = len(represent) * COL_WIDTH_MULTIPLIER
                if width > column_widths[col_index]:
                    column_widths[col_index] = width
                    current_sheet.col(write_col_index).width = width
                col_index += 1

        # Additional sheet settings
        for sheet in sheets:
            sheet.panes_frozen = True
            sheet.horz_split_pos = 1

        # Write output
        output = StringIO()
        book.save(output)
        output.seek(0)

        if as_stream:
            return output

        # Response headers
        filename = "%s_%s.xls" % (request.env.server_name, title)
        disposition = "attachment; filename=\"%s\"" % filename
        response = current.response
        response.headers["Content-Type"] = contenttype(".xls")
        response.headers["Content-disposition"] = disposition

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

        if datetime_format is None:
            # Support easier usage from external functions
            datetime_format = cls.dt_format_translate(current.deployment_settings.get_L10n_datetime_format())


        # Styles
        large_header = xlwt.XFStyle()
        large_header.font.bold = True
        large_header.font.height = 400
        if use_colour:
            SOLID_PATTERN = large_header.pattern.SOLID_PATTERN
            large_header.alignment.horz = large_header.alignment.HORZ_CENTER
            large_header.pattern.pattern = SOLID_PATTERN
            large_header.pattern.pattern_fore_colour = cls.LARGE_HEADER_COLOUR

        notes = xlwt.XFStyle()
        notes.font.italic = True
        notes.font.height = 160 # 160 Twips = 8 point
        notes.num_format_str = datetime_format

        header = xlwt.XFStyle()
        header.font.bold = True
        header.num_format_str = datetime_format
        if use_colour:
            header.pattern.pattern = SOLID_PATTERN
            header.pattern.pattern_fore_colour = cls.HEADER_COLOUR

        subheader = xlwt.XFStyle()
        subheader.font.bold = True
        if use_colour:
            subheader.pattern.pattern = SOLID_PATTERN
            subheader.pattern.pattern_fore_colour = cls.SUB_HEADER_COLOUR

        subtotals = xlwt.XFStyle()
        subtotals.font.bold = True
        if use_colour:
            subtotals.pattern.pattern = SOLID_PATTERN
            subtotals.pattern.pattern_fore_colour = cls.SUB_TOTALS_COLOUR

        totals = xlwt.XFStyle()
        totals.font.bold = True
        if use_colour:
            totals.pattern.pattern = SOLID_PATTERN
            totals.pattern.pattern_fore_colour = cls.TOTALS_COLOUR

        odd = xlwt.XFStyle()
        if use_colour and evenodd:
            odd.pattern.pattern = SOLID_PATTERN
            odd.pattern.pattern_fore_colour = cls.ROW_ALTERNATING_COLOURS[0]

        even = xlwt.XFStyle()
        if use_colour and evenodd:
            even.pattern.pattern = SOLID_PATTERN
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
#class S3HTML2XLS():
#    """
#        Class that takes HTML in the form of web2py helper objects
#        and converts it to XLS
#
#        @ToDo: Complete this (e.g. start with a copy of S3html2pdf)
#        See https://gist.github.com/JustOnce/2be3e4d951a66c22c5e0
#        & http://pydoc.net/Python/Kiowa/0.2w.rc9/kiowa.utils.xls.html2xls/
#
#        Places  to use this:
#            org_CapacityReport()
#    """
#
#    def __init__(self):
#
#        pass
#
#    # -------------------------------------------------------------------------
#    def parse(self, html):
#        """
#            Entry point for class
#        """
#
#        return None
#
# END =========================================================================
