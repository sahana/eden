# -*- coding: utf-8 -*-
#
# Debug/Helper script for XSL stylesheet development
#
# >>> python xsltransform <XML File> <XSLT Stylesheet> [<name>]
#       ... transforms the XML file using the stylesheet
#
import sys
from lxml import etree

def parse(source):

    parser = etree.XMLParser(no_network=False)
    result = etree.parse(source, parser)
    return result

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
        xmlpath = argv[0]
    except:
        print "Usage: python xsltransform <XML File> [<XSLT Stylesheet>] [<name>]"
        return
    try:
        xslpath = argv[1]
    except:
        xslpath = None

    tree = parse(xmlpath)

    if xslpath is not None:
        try:
            name = argv[2]
            tree = transform(tree, xslpath, name=name)
        except:
            tree = transform(tree, xslpath)

    print etree.tostring(tree, pretty_print=True)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
