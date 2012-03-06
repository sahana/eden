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
import sys
import csv
from lxml import etree
from xml.sax.saxutils import escape, unescape

TABLE = "table"
ROW = "row"
COL = "col"
FIELD = "field"

def xml_encode(s):

    if s:
        s = escape(s, {"'": "&apos;", '"': "&quot;"})
    return s

def xml_decode(s):

    if s:
        s = unescape(s, {"&apos;": "'", "&quot;": '"'})
    return s

def parse(source):

    parser = etree.XMLParser(no_network=False)
    result = etree.parse(source, parser)
    return result

def csv2tree(source, delimiter=",", quotechar='"'):

    root = etree.Element(TABLE)

    def utf_8_encode(source):

        encodings = ["utf-8", "iso-8859-1"]
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

    reader = csv.DictReader(utf_8_encode(source),
                            delimiter=delimiter,
                            quotechar=quotechar)
    for r in reader:
        row = etree.SubElement(root, ROW)
        for k in r:
            col = etree.SubElement(row, COL)
            col.set(FIELD, str(k))
            value = r[k]
            if value:
                text = str(value)
                if text.lower() not in ("null", "<null>"):
                    text = xml_encode(unicode(text.decode("utf-8")))
                    col.text = text
            else:
                col.text = ""

    return  etree.ElementTree(root)

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
