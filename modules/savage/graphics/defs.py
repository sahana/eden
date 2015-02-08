from base import BoxElement
from group import GroupableElement

class Defs (GroupableElement):
    def __init__ (self, **attr):
        GroupableElement.__init__ (self, name = 'defs', **attr)


class Symbol (GroupableElement):
    def __init__ (self, **attr):
        GroupableElement.__init__ (self, name= 'symbol', **attr)
        if attr.has_key ('viewBox'):
            self.viewBox = attr['viewBox']
        else:
            self.viewBox = None
            
    def setSVG (self):
        attr = GroupableElement.setSVG (self)
        attr.update ([('viewBox', self.viewBox)])
        return attr


class Use (BoxElement):
    def __init__ (self, **attr):
        BoxElement.__init__ (self, name = 'use', **attr)
        if attr.has_key ('href'):
            self.href = attr['href']
        else:
            self.href = None

    def setSVG (self):
        attr = BoxElement.setSVG (self)
        attr.update ([('xlink:href', self.href)])
        return attr
    
