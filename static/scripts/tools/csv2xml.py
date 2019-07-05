# -*- coding: utf-8 -*-
#
# Debug/Helper script for CSV stylesheet development
#
# >>> python csv2xml <CSV File>
#       ... converts the CSV file into XML
#
# >>> python csv2xml <CSV File> <XSLT Stylesheet>
#       ... converts the CSV file into XML and transforms it using the stylesheet
#

import csv
import sys

PY2 = sys.version_info[0] == 2

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
if PY2:
    def s3_unicode(s, encoding="utf-8"):
        """
            Convert an object into an unicode instance, to be used
            instead of unicode(s)

            @param s: the object
            @param encoding: the character encoding
        """

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
            s = " ".join([s3_unicode(arg, encoding) for arg in s])
        return s

else:

    def s3_unicode(s, encoding="utf-8"):
        """
            Convert an object into a str, for backwards-compatibility

            @param s: the object
            @param encoding: the character encoding
        """

        if type(s) is str:
            return s
        elif type(s) is bytes:
            return s.decode(encoding, "strict")
        else:
            return str(s)

# -------------------------------------------------------------------------
def csv2tree(source, delimiter=",", quotechar='"'):

    # Increase field size to be able to import WKTs
    csv.field_size_limit(2**20 * 100)  # 100 megs

    # Shortcuts
    SubElement = etree.SubElement

    root = etree.Element(TABLE)

    def add_col(row, key, value, hashtags=None):

        col = SubElement(row, COL)
        col.set(FIELD, s3_unicode(key))
        if hashtags:
            hashtag = hashtags.get(key)
            if hashtag and hashtag[1:]:
                col.set(HASHTAG, hashtag)
        if value:
            text = s3_unicode(value).strip()
            if text[:6].lower() not in ("null", "<null>"):
                col.text = text
        else:
            col.text = ""

    def utf_8_encode(source):

        encodings = ("utf-8-sig", "iso-8859-1")
        e = encodings[0]
        for line in source:
            if e:
                try:
                    s = s3_unicode(line, e)
                    yield s.encode("utf-8") if PY2 else s
                except:
                    pass
                else:
                    continue
            for encoding in encodings:
                try:
                    s = s3_unicode(line, encoding)
                    yield s.encode("utf-8") if PY2 else s
                except:
                    continue
                else:
                    e = encoding
                    break

    hashtags = {}

    def read_from_csv(source):

        source = utf_8_encode(source)
        reader = csv.DictReader(source, delimiter=delimiter, quotechar=quotechar)

        for i, r in enumerate(reader):
            # Skip empty rows
            if not any(r.values()):
                continue
            if i == 0:
                # Auto-detect hashtags
                items = {}
                for k, v in r.items():
                    if v:
                        try:
                            v = v.strip()
                        except AttributeError: # v is a List
                            v = s3_unicode(v)
                        items[k] = v
                if all(v[0] == '#' for v in items.values()):
                    hashtags.update(items)
                    continue
            row = SubElement(root, ROW)
            for k in r:
                add_col(row, k, r[k], hashtags=hashtags)

    if PY2:
        from StringIO import StringIO
    else:
        from io import StringIO
    if not isinstance(source, StringIO):
        try:
            read_from_csv(source)
        except UnicodeDecodeError as e:
            try:
                fname, fmode = source.name, source.mode
            except AttributeError:
                fname = fmode = None
            if not PY2 and fname and fmode and "b" not in fmode:
                # Perhaps a file opened in text mode with wrong encoding,
                # => try to reopen in binary mode
                with open(fname, "rb") as bsource:
                    read_from_csv(bsource)
            else:
                raise e

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
        csvpath = argv[0]
    except:
        sys.stderr.write("Usage: python csv2xml.py <CSV File> [<XSLT Stylesheet>]\n")
        return
    try:
        xslpath = argv[1]
    except:
        xslpath = None

    with open(csvpath, "r") as csvfile:
        tree = csv2tree(csvfile)

    if xslpath is not None:
        tree = transform(tree, xslpath)

    sys.stdout.write(etree.tostring(tree,
                                    encoding = "utf-8" if PY2 else "unicode",
                                    pretty_print = True,
                                    ))

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

# END =========================================================================
