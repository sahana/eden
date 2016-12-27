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
    """
        Convert an object into an unicode instance, to be used instead of
        unicode(s) (Note: user data should never be converted into str).

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
        else:
            s = " ".join([s3_unicode(arg, encoding) for arg in s])
    return s

# -------------------------------------------------------------------------
def csv2tree(source,
             delimiter=",",
             quotechar='"'):

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

        encodings = ["utf-8-sig", "iso-8859-1"]
        e = encodings[0]
        for line in source:
            if e:
                try:
                    yield unicode(line, e, "strict").encode("utf-8")
                except:
                    pass
                else:
                    continue
            for encoding in encodings:
                try:
                    yield unicode(line, encoding, "strict").encode("utf-8")
                except:
                    continue
                else:
                    e = encoding
                    break

    hashtags = {}

    import StringIO
    if not isinstance(source, StringIO.StringIO):
        source = utf_8_encode(source)
    reader = csv.DictReader(source,
                            delimiter=delimiter,
                            quotechar=quotechar)

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
        print "Usage: python csv2xml <CSV File> [<XSLT Stylesheet>]"
        return
    try:
        xslpath = argv[1]
    except:
        xslpath = None

    csvfile = open(csvpath)
    tree = csv2tree(csvfile)

    if xslpath is not None:
        tree = transform(tree, xslpath)

    print etree.tostring(tree, pretty_print=True)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

# END =========================================================================
