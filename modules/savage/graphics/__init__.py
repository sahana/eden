from base import BoxElement, Script
from group import Grouping, GroupableElement
from defs import Defs
from utils import ViewBox

class Canvas (BoxElement, GroupableElement):
    def __init__ (self, **attr):
        GroupableElement.__init__ (self, name = 'svg', **attr)
        BoxElement.__init__ (self, name = 'svg', **attr)
        if attr.has_key ('viewBox'):
            self.viewBox = attr['viewBox']
        else:
            self.viewBox = None

    def setSVG (self):
        attr = BoxElement.setSVG (self)
        attr.update (GroupableElement.setSVG (self))
        attr.update ([('viewBox', self.viewBox)])
        return attr

    def SVG (self, indent):
        return GroupableElement.SVG (self, indent)


class PrintableCanvas (Canvas):
    def __init__ (self, **attr):
        Canvas.__init__ (self, **attr)
        self.xmlns = 'http://www.w3.org/2000/svg'
        self.xlink = 'http://www.w3.org/1999/xlink'
        self.ev = 'http://www.w3.org/2001/xml-events'
        self.defs = Defs ()
        self.scripts = []

    def addScript (self, cdata):
        self.scripts.append (Script (cdata))

    def setSVG (self):
        self.addDefTags ()
        if len (self.defs) > 0:
            self.drawAt (self.defs, 0)
        attr = Canvas.setSVG (self)
        if self.parent is None:
            attr.update ([('xmlns', self.xmlns),
                          ('xmlns:xlink', self.xlink),
                          ('xmlns:ev', self.ev)])
        return attr

    def addDefTags (self):
        dlist = {}
        for child in self:
            self.addDefs (child, dlist)
        for key, value in dlist.iteritems ():
            self.defs.draw (value)
        

    def addDefs (self, node, dlist):
        if hasattr (node, '__iter__'):
            for child in node:
                self.addDefs (child, dlist)
        if hasattr (node, 'defs'):
            for d in node.defs:
                dlist.update ([(d.id, d)])

    def SVG (self, indent):
        if self.parent is None:
            prepend = '<?xml version="1.0" standalone="no"?>\n'
            prepend += '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" '
            prepend += '"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
            self.scripts.reverse ()
            for script in self.scripts:
                self.drawAt (script, 0)
            return prepend + GroupableElement.SVG (self, indent)
        else:
            return GroupableElement.SVG (self, indent)

    def save (self, fileOrString = None):
        if fileOrString is None:
            return self.SVG ('')
        needToClose = False
        if isinstance (fileOrString, str):
            needToClose = True
            fileOrString = open (fileOrString, 'w')
        fileOrString.write (self.SVG (''))
        if needToClose:
            fileOrString.close ()
