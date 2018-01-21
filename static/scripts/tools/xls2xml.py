# -*- coding: utf-8 -*-
#
# Debug/Helper script for XLS stylesheet development
#
# >>> python xls2xml <XLS File>
#       ... converts the XLS file into XML
#
# >>> python xls2xml <XLS File> <XSLT Stylesheet>
#       ... converts the XLS file into XML and transforms it using the stylesheet
#
import datetime
import sys

from lxml import etree
from xml.sax.saxutils import escape, unescape

TABLE = "table"
ROW = "row"
COL = "col"
FIELD = "field"
TAG = "tag"
HASHTAG = "hashtag"

# -----------------------------------------------------------------------------
def xml_encode(s):

    if s:
        s = escape(s, {"'": "&apos;", '"': "&quot;"})
    return s

# -----------------------------------------------------------------------------
def xml_decode(s):

    if s:
        s = unescape(s, {"&apos;": "'", "&quot;": '"'})
    return s

# -----------------------------------------------------------------------------
def parse(source):

    parser = etree.XMLParser(no_network=False)
    result = etree.parse(source, parser)
    return result

# -----------------------------------------------------------------------------
def s3_unicode(s, encoding="utf-8"):

    if type(s) is unicode:
        return s
    try:
        if not isinstance(s, basestring):
            if hasattr(s, "__unicode__"):
                s = unicode(s)
            else:
                try:
                    s = unicode(str(s), encoding, "strict")
                except UnicodeEncodeError:
                    if not isinstance(s, Exception):
                        raise
                    s = " ".join([s3_unicode(arg, encoding) for arg in s])
        else:
            s = s.decode(encoding)
    except UnicodeDecodeError:
        if not isinstance(s, Exception):
            raise
        else:
            s = " ".join([s3_unicode(arg, encoding) for arg in s])
    return s

# -------------------------------------------------------------------------
def encode_iso_datetime(dt):

    dx = dt - datetime.timedelta(microseconds=dt.microsecond)
    return dx.isoformat()

# -------------------------------------------------------------------------
def xls2tree(source,
             resourcename=None,
             extra_data=None,
             hashtags=None,
             sheet=None,
             rows=None,
             cols=None,
             fields=None,
             header_row=True):

    import xlrd

    # Shortcuts
    SubElement = etree.SubElement

    DEFAULT_SHEET_NAME = "SahanaData"

    # Root element
    root = etree.Element(TABLE)
    if resourcename is not None:
        root.set("name", resourcename)

    if isinstance(sheet, xlrd.sheet.Sheet):
        # Open work sheet passed as argument => use this
        s = sheet
    else:
        if hasattr(source, "read"):
            # Source is a stream
            if hasattr(source, "seek"):
                source.seek(0)
            wb = xlrd.open_workbook(file_contents=source.read(),
                                    # requires xlrd 0.7.x or higher
                                    on_demand=True)
        elif isinstance(source, xlrd.book.Book):
            # Source is an open work book
            wb = source
        else:
            # Unsupported source type
            raise RuntimeError("xls2tree: invalid source %s" % type(source))

        # Find the sheet
        try:
            if isinstance(sheet, (int, long)):
                s = wb.sheet_by_index(sheet)
            elif isinstance(sheet, basestring):
                s = wb.sheet_by_name(sheet)
            elif sheet is None:
                if DEFAULT_SHEET_NAME in wb.sheet_names():
                    s = wb.sheet_by_name(DEFAULT_SHEET_NAME)
                else:
                    s = wb.sheet_by_index(0)
            else:
                raise SyntaxError("xls2tree: invalid sheet %s" % sheet)
        except IndexError, xlrd.XLRDError:
            s = None

    def cell_range(cells, max_cells):
        """
            Helper method to calculate a cell range

            @param cells: the specified range
            @param max_cells: maximum number of cells
        """
        if not cells:
            cells = (0, max_cells)
        elif not isinstance(cells, (tuple, list)):
            cells = (0, cells)
        elif len(cells) == 1:
            cells = (cells[0], max_cells)
        else:
            cells = (cells[0], cells[0] + cells[1])
        return cells

    if s:
        # Calculate cell range
        rows = cell_range(rows, s.nrows)
        cols = cell_range(cols, s.ncols)

        # Column headers
        if fields:
            headers = fields
        elif not header_row:
            headers = dict((i, "%s" % i) for i in range(cols[1]- cols[0]))
        else:
            # Use header row in the work sheet
            headers = {}

        # Lambda to decode XLS dates into an ISO datetime-string
        decode_date = lambda v: datetime.datetime(*xlrd.xldate_as_tuple(v, wb.datemode))

        def decode(t, v):
            """
                Helper method to decode the cell value by type

                @param t: the cell type
                @param v: the cell value
                @return: text representation of the cell value
            """
            text = ""
            if v:
                if t is None:
                    text = s3_unicode(v).strip()
                elif t == xlrd.XL_CELL_TEXT:
                    text = v.strip()
                elif t == xlrd.XL_CELL_NUMBER:
                    text = str(long(v)) if long(v) == v else str(v)
                elif t == xlrd.XL_CELL_DATE:
                    text = encode_iso_datetime(decode_date(v))
                elif t == xlrd.XL_CELL_BOOLEAN:
                    text = str(value).lower()
            return text

        def add_col(row, name, t, v, hashtags=None):
            """
                Helper method to add a column to an output row

                @param row: the output row (etree.Element)
                @param name: the column name
                @param t: the cell type
                @param v: the cell value
            """
            col = SubElement(row, COL)
            col.set(FIELD, name)
            if hashtags:
                hashtag = hashtags.get(name)
                if hashtag and hashtag[1:]:
                    col.set(HASHTAG, hashtag)
            col.text = decode(t, v)

        hashtags = dict(hashtags) if hashtags else {}

        # Process the rows
        record_idx = 0
        extra_fields = set(extra_data) if extra_data else None
        check_headers = extra_fields is not None
        for ridx in range(*rows):
            # Read types and values
            types = s.row_types(ridx, *cols)
            values = s.row_values(ridx, *cols)

            # Skip empty rows
            if not any(v != "" for v in values):
                continue

            if header_row and record_idx == 0:
                # Read column headers
                if not fields:
                    for cidx, value in enumerate(values):
                        header = decode(types[cidx], value)
                        headers[cidx] = header
                        if check_headers:
                            extra_fields.discard(header)
                    check_headers = False
            else:
                if not fields and \
                   (header_row and record_idx == 1 or record_idx == 0):
                    # Autodetect hashtags
                    items = {}
                    for cidx, name in headers.items():
                        try:
                            t = types[cidx]
                            v = values[cidx]
                        except IndexError:
                            continue
                        if t not in (xlrd.XL_CELL_TEXT, xlrd.XL_CELL_EMPTY):
                            items = None
                            break
                        elif v:
                            items[name] = v
                    if items and all(v[0] == '#' for v in items.values()):
                        hashtags.update(items)
                        continue
                # Add output row
                orow = SubElement(root, ROW)
                for cidx, name in headers.items():
                    if check_headers:
                        extra_fields.discard(name)
                    try:
                        t = types[cidx]
                        v = values[cidx]
                    except IndexError:
                        pass
                    else:
                        add_col(orow, name, t, v, hashtags=hashtags)
                check_headers = False

                # Add extra data
                if extra_fields:
                    for key in extra_fields:
                        add_col(orow, key, None, extra_data[key], hashtags=hashtags)
            record_idx += 1

    return  etree.ElementTree(root)

# -----------------------------------------------------------------------------
def transform(tree, stylesheet_path, **args):

    if args:
        _args = [(k, "'%s'" % args[k]) for k in args]
        _args = dict(_args)
    else:
        _args = None
    stylesheet = etree.parse(stylesheet_path)

    ac = etree.XSLTAccessControl(read_file=True, read_network=True)
    transformer = etree.XSLT(stylesheet, access_control=ac)
    if _args:
        result = transformer(tree, **_args)
    else:
        result = transformer(tree)
    return result

# -----------------------------------------------------------------------------
def main(argv):

    try:
        xlspath = argv[0]
    except:
        sys.stderr.write("Usage: python xls2xml.py <XLS File> [<XSLT Stylesheet>]\n")
        return
    try:
        xslpath = argv[1]
    except:
        xslpath = None

    xlsfile = open(xlspath)
    tree = xls2tree(xlsfile)

    if xslpath is not None:
        tree = transform(tree, xslpath)

    sys.stdout.write(etree.tostring(tree, pretty_print=True))

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

# END =========================================================================
