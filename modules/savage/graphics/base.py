from utils import ViewBox, attributesToSVG
from ..utils.struct import Vector as V, identity
from ..utils.dictionary import Dictionary


class Element (object):
    def __init__ (self, **attr):
        if attr.has_key ('name'):
            self.name = attr['name']
        else:
            self.name = None
        if attr.has_key ('id'):
            self.id = attr['id']
        else:
            self.id = None
        if attr.has_key ('className'):
            self.className = attr['className']
        else:
            self.className = None
        self.parent = None
        self.style = Style ()
        self.xml = {}

    def root (self):
        parent = self
        while not parent.parent is None:
            parent = parent.parent
        return parent

    def createDef (self, element):
        if not hasattr (self, 'defs') :
            self.defs = Defs ()
        node = self.defs.getElementById (element.id)
        if node is None:
            self.defs.draw (element)
            return True
        else:
            return False

    def setSVG (self):
        attr = {'class': self.className,
                'id': self.id}
        attr.update (self.style.setSVG ())
        attr.update (self.xml)
        return attr

    def SVG (self, indent):
        attr = self.setSVG ()
        return indent + '<' + self.name + ' ' + attributesToSVG (attr) + ' />\n'


class Style:
    def setSVG (self):
        attr = {}
        elements = []
        for key, value in self.__dict__.iteritems ():
            try:
                elements.append ((StyleDict[key], value))
            except KeyError:
                print 'Warning: ' + str(key) + ' is not a known style attribute. Skipping.'
        attr.update (elements)
        return attr


StyleDict = {'strokeColor': 'stroke',
             'strokeWidth': 'stroke-width',
             'stokeWidth': 'stoke-width',
             'fill': 'fill',
             'opacity': 'opacity',
             'shapeRendering': 'shape-rendering',
}

class Script (Element):
    def __init__ (self, cdata, **attr):
        Element.__init__ (self, name = 'script', **attr)
        self.xml ['type'] = 'text/javascript'
        #file = open (filename)
        #self.text = file.read ()
        self.text = cdata

    def SVG (self, indent):
        tag = '<script type="text/javascript"><![CDATA[\n'
        tag += self.text + '\n'
        tag += ']]></script>\n'
        return tag

class PositionableElement (Element):
    def __init__ (self, **attr):
        Element.__init__ (self, **attr)
        if attr.has_key ('x'):
            self.x = float (attr['x'])
        else:
            self.x = 0.0
        if attr.has_key ('y'):
            self.y = float (attr['y'])
        else:
            self.y = 0.0

    def position (self, x = None, y = None):
        if (x is None) and (y is None):
            return (self.x, self.y)
        if not (x is None):
            self.x = float (x)
        if not (y is None):
            self.y = float (y)

    def applyTransform (self, *points):
        parent = self.parent
        matrix = identity (3)
        while not (parent is None):
            matrix = parent.transform * matrix
            if parent.name == 'svg':
                break
            parent = parent.parent
        for p in points:
            q = matrix * p.matrix ()
            p.x = q.get (0, 0)
            p.y = q.get (1, 0)

    def getWorldPoint (self, x, y):
        parent = self.parent
        matrix = identity (3)
        while not (parent is None):
            matrix = parent.transform * matrix
            parent = parent.parent
        point = V (x, y)
        return (matrix * point)


class BoxElement (PositionableElement):
    def __init__ (self, **attr):
        PositionableElement.__init__ (self, **attr)
        if attr.has_key ('width'):
            self.width = float (attr['width'])
        else:
            self.width = None
        if attr.has_key ('height'):
            self.height = float (attr['height'])
        else:
            self.height = None

    def calulateBox (self, x, y, width, height):
        try:
            minPoint = V (x, y)
            maxPoint = V (x + width, y + height)
            self.applyTransform (minPoint, maxPoint)
            self.reconfigurePoints (minPoint, maxPoint)
            x = minPoint.x
            y = minPoint.y
            return {'x': x,
                    'y': y,
                    'width': (maxPoint.x - minPoint.x),
                    'height': (maxPoint.y - minPoint.y)
                    }
        except TypeError:
            minPoint = V (x, y)
            x = minPoint.x
            y = minPoint.y
            self.applyTransform (minPoint)
            return {'x': x,
                    'y': y,
                    'width': None,
                    'height': None
                    }

    def reconfigurePoints (self, minPoint, maxPoint):
        if minPoint.x > maxPoint.x:
            tmp = minPoint.x
            minPoint.x = maxPoint.x
            maxPoint.x = tmp
        if minPoint.y > maxPoint.y:
            tmp = minPoint.y
            minPoint.y = maxPoint.y
            maxPoint.y = tmp

    def setSVG (self):
        attr = PositionableElement.setSVG (self)
        points = self.calulateBox (self.x, self.y, self.width, self.height)
        attr.update (points)
        return attr

from defs import Defs

### OLD CODE ###
        
"""
class Node:
    def __init__ (self, **attr):
        self.parent = None
        self.attributes = Dictionary ()
        if attr.has_key ('id'):
            self.id = attr['id']
        else:
            self.id = None
        if attr.has_key ('className'):
            self.className = attr['className']
        else:
            self.className = None

    def getAttribute (self, key):
        if self.attributes.has_key (key):
            return self.attributes[key]
        else:
            return None

    def setAttribute (self, key, value):
        self.attributes.update ([(key, value)])

    def SVG (self, indent=''):
        self.setSVG ()
        output = indent + '<' + self.name
        attr = attributesToSVG (self.attributes)
        if attr:
            output += ' ' + attr
        output += ' />\n'
        return output

    def setSVG (self):
        self.setAttribute ('id', self.id)
        self.setAttribute ('class', self.className)


class ScriptNode (Node):
    def __init__ (self, type, filename, **attr):
        Node.__init__ (self, **attr)
        self.name = 'script'
        self.type = type
        self.filename = filename

    def setSVG (self):
        self.setAttribute ('type', self.type)
        self.setAttribute ('xlink:href', self.filename)


class PositionableNode (Node):
    def __init__ (self, **attr):
        Node.__init__ (self, **attr)

    def setPosition (self):
        raise NotImplementedError ()

    def setSVG (self):
        Node.setSVG (self)
        matrix = identity (3)
        parent = self.parent
        while not parent is None:
            matrix = parent.transform * matrix
            parent = parent.parent
        points = []
        for p in self.points ():
            q = matrix * p
            points.append (q)
        self.returnPoints (points)
        self.setPosition ()

    def translate (self, vect):
        for p in self.points ():
            p += vect

    def points (self):
        raise NotImplementedError ()

    def returnPoints (self, points):
        raise NotImplementedError ()


class BoxNode (PositionableNode):
    def __init__ (self, **attr):
        PositionableNode.__init__ (self, **attr)

        if attr.has_key ('position'):
            minPoint = attr['position']
        else:
            minPoint = V (0, 0)
        if attr.has_key ('width'):
            width = attr['width']
        else:
            width = 0
        if attr.has_key ('height'):
            height = attr['height']
        else:
            height = 0
        self.minPoint = minPoint
        self.maxPoint = minPoint + V (width, height)
        self.minPoint.set (1, 2, 0)
        self.maxPoint.set (1, 2, 0)
        self.reconfigurePoints ()

    def reconfigurePoints (self):
        if self.minPoint.x > self.minPoint.x:
            tmp = self.minPoint.x
            self.minPoint.x = self.maxPoint.x
            self.maxPoint.x = tmp
        if self.minPoint.y > self.maxPoint.y:
            tmp = self.minPoint.y
            self.minPoint.y = self.maxPoint.y
            self.maxPoint.y = tmp

    def changePosition (self, dx, dy):
        d = V (dx, dy)
        self.minPoint += d
        self.maxPoint += d

    def changeSize (self, dx, dy):
        d = V (dx, dy)
        self.maxPoint += d
        self.reconfigurePoints ()

    def setPosition (self):
        if self.minPoint.x:
            self.setAttribute ('x', self.minPoint.x)
        if self.minPoint.y:
            self.setAttribute ('y', self.minPoint.y)

    def setSize (self):
        width = self.maxPoint.x - self.minPoint.x
        height = self.maxPoint.y - self.minPoint.y
        if width:
            self.setAttribute ('width', width)
        if height:
            self.setAttribute ('height', height)

    def width (self):
        return self.maxPoint.x - self.minPoint.x

    def height (self):
        return self.maxPoint.y - self.minPoint.y

    def points (self):
        return [self.minPoint, self.maxPoint]

    def returnPoints (self, points):
        self.minPoint = points[0]
        self.maxPoint = points[1]
        self.reconfigurePoints ()

    def setSVG (self):
        PositionableNode.setSVG (self)
        self.setSize ()
        

class GroupableNode (Node):
    def __init__ (self, **attr):
        Node.__init__ (self, **attr)
        self.children = []
        self.transform = identity (3)

    def clear (self):
        for child in self.children:
            child.parent = None
        self.children = []
    
    def draw (self, nodeToDraw):
        nodeToDraw.parent = self
        self.children.append (nodeToDraw)

    def drawBefore (self, nodeToDraw, existingNode):
        index = 0
        for node in self.children:
            if existingNode is node:
                nodeToDraw.parent = self
                break
        index += 1
        self.children.insert (index, nodeToDraw)

    def drawAt (self, nodeToDraw, index):
        nodeToDraw.parent = self
        self.children.insert (index, nodeToDraw)
        
    def getGroupById (self, id):
        for node in self.children:
            if node.id == id:
                return node
        return None

    def removeNodeById (self, id):
        index = 0
        for node in self.children:
           if node.id == id:
               self.children[index].parent = None
               del self.children[index]
               return
           else:
               index += 1

    #def transform (self, matrix):
    #    for child in self.children:
    #        child.transform (matrix)

    def __len__ (self):
        return len (self.children)

    def __iter__ (self):
        return iter (self.children)

    def SVG (self, indent=''):
        self.setSVG ()
        output = indent + '<' + self.name
        attr = attributesToSVG (self.attributes)
        if attr:
            output += ' ' + attr
        if len (self.children) > 0:
            output += '>\n'
            nextIndent = '    ' + indent
            for node in self.children:
                output += node.SVG (nextIndent)
            output += indent + '</' + self.name + '>\n'
        else:
            output += ' />\n'
        return output


class Group (GroupableNode):
    def __init__ (self, **attr):
        GroupableNode.__init__ (self, **attr)
        self.name = 'g'
        self.transforms = []

    def appendTransform (self, transform):
        self.transforms.append (transform)

    def setSVG (self):
        GroupableNode.setSVG (self)
        transforms = []
        for trans in self.transforms:
            transforms.append (str (trans))
        finalTransform = ' '.join (transforms)
        if finalTransform != '':
            self.setAttribute ('transform', finalTransform)


class Canvas (GroupableNode, BoxNode):
    def __init__ (self, **attr):
        GroupableNode.__init__ (self, **attr)
        BoxNode.__init__ (self, **attr)
        self.name = 'svg'
        if attr.has_key ('viewBox'):
            self.viewBox = attr['viewBox']
        else:
            self.viewBox = None

    #def transform (self, matrix):
    #    BoxNode.transform (self, matrix)
    #    GroupableNode.transform (self, matrix)

    def coordinateFrame (self, viewBox = ViewBox (), aspect = None):
        self.viewBox = viewBox
        if aspect is not None:
            self.setAttribute ('preserveAspectRatio', aspect)

    def setSVG (self):
        GroupableNode.setSVG (self)
        BoxNode.setSVG (self)
        self.setAttribute ('viewBox', self.viewBox)


class PrintableCanvas (Canvas):
    def __init__ (self):
        Canvas.__init__ (self)
        self.stylesheets = []
        self.scripts = []

    def addJS (self, filename):
        self.scripts.append (filename)

    def addCSS (self, filename):
        self.stylesheets.append (filename)

    def setSVG (self):
        Canvas.setSVG (self)
        self.setAttribute ('xmlns', 'http://www.w3.org/2000/svg')
        self.setAttribute ('xmlns:xlink', 'http://www.w3.org/1999/xlink')
        self.setAttribute ('xmlns:ev', 'http://www.w3.org/2001/xml-events')
 
    def SVG (self):
        self.scripts.reverse ()
        for script in self.scripts:
            s = ScriptNode ('text/javascript', script)
            self.drawAt (s, 0)
        output = Canvas.SVG (self)
        prepend = '<?xml version="1.0" standalone="no"?>\n'
        prepend += '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" '
        prepend += '"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
        for entry in self.stylesheets:
            prepend += '<?xml-stylesheet type="text/css" href="'
            prepend += entry  + '" ?>\n'
        return prepend + output
        
    def save (self, fileOrString):
        needToClose = False
        if isinstance (fileOrString, str):
            needToClose = True
            fileOrString = open (fileOrString, 'w')
        fileOrString.write (self.SVG ())
        if needToClose:
            fileOrString.close ()


class Shape (PositionableNode):
    def __init__ (self, **attr):
        PositionableNode.__init__ (self, **attr)

    def setSVG (self):
        PositionableNode.setSVG (self)
"""

