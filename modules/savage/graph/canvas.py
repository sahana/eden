from base import BaseGraph
from reg import RegressionLine

from ..graphics import Canvas
from ..graphics.shapes import Circle, Line, Rectangle, Sector, Path, Square
from ..graphics.group import Group, Grouping
from ..graphics.utils import ViewBox
from ..graphics.color import white

from ..utils.struct import Vector as V, Matrix
#from ..utils.dictionary import DefaultDictionary

from re import match

from copy import deepcopy
from math import pi


class GraphCanvas (Canvas):
    def __init__ (self, **attr):
        Canvas.__init__ (self, **attr)
        if attr.has_key ('regLine'):
            self.regLine = attr['regLine']
        else:
            self.regLine = True

    def graph (self):
        parent = self
        while not isinstance (parent, BaseGraph):
            parent = parent.parent
        return parent

    def changeSize (self, dx, dy):
        self.width += dx
        self.height += dy

    def move (self, dx, dy):
        self.x += dx
        self.y += dy

    def makeTransform (self, minX, maxX, minY, maxY):
        matrix1 = Matrix (3, 3)
        matrix1.set (-minX, 0, 2)
        matrix1.set (-minY, 1, 2)

        currentRangeX = float (maxX - minX)
        currentRangeY = float (maxY - minY)

        matrix2 = Matrix (3, 3)
        matrix2.set (self.width / currentRangeX, 0, 0)
        matrix2.set (self.height / currentRangeY, 1, 1)
        
        matrix3 = Matrix (3, 3)
        matrix3.set (self.height, 1, 2)
        matrix3.set (-1.0, 1, 1)

        return (matrix3 * (matrix2 * matrix1))

    def setSVG (self):
        attr = Canvas.setSVG (self)
        attr['viewBox'] = ViewBox (0, 0, attr['width'], attr['height'])
        return attr


class ScatterCanvas (GraphCanvas):
    def __init__ (self, **attr):
        GraphCanvas.__init__ (self, **attr)
        self.data = Grouping ()
        self.dataPoints = Group (id = 'data')

    def drawPoint (self, name, x, y):
        settings = self.graph ().settings
        self.drawPointAux (self.dataPoints, name, x, y, settings.markerType, settings.markerSize)

    def drawPointAux (self, group, name, x, y, pointType, pointSize):
        if pointType == 'circle':
            m = Circle (radius = pointSize, x = x, y = y)
        elif pointType == 'square':
            half = pointSize / 2.0
            m = Square (pointSize, 
                        x = x, 
                        y = y,
                        worldDeltaX = -half,
                        worldDeltaY = -half,
                        absoluteSize = True)
        if name:
            m.xml['has-tooltip'] = True
            m.xml['tooltip-text'] = name
        m.xml['has-highlight'] = True
        m.xml['highlight-fill'] = 'red'
        group.draw (m)

    def addColor (self):
        settings = self.graph ().settings
        if settings.colorScheme == 'tripleAxis':
            self.setTripleColor (self.dataPoints, settings.color1, settings.color2, settings.color3)
        elif settings.colorScheme == 'solid':
            self.setSolidColor (self.dataPoints, settings.color1)

    def setSolidColor (self, group, color):
        for item in group:
            item.style.fill = color
            item.xml['highlight-fill'] = color.interpolate (white, .35)

    def setTripleColor (self, group, color1, color2, color3):
        for item in group:
            perX = (item.x - self.minX) / (self.maxX - self.minX)
            perY = (item.y - self.minY) / (self.maxY - self.minY)
            c1 = color2.interpolate (color3, perX)
            c2 = color2.interpolate (color1, perY)
            per = (perY + (1 - perX)) / 2.0
            c = c1.interpolate (c2, per)
            item.style.fill = c 
            item.xml['highlight-fill'] = c.interpolate (white, .35)

    def setBounds (self):
        self.xlist = []
        self.ylist = []
        for child in self.dataPoints:
            self.xlist.append (child.x)
            self.ylist.append (child.y)
        
        minX = min (self.xlist)
        maxX = max (self.xlist)
        minY = min (self.ylist)
        maxY = max (self.ylist)
        rangeX = maxX - minX
        rangeY = maxY - minY

        self.minX = minX - rangeX * .05
        self.maxX = maxX + rangeX * .05
        self.minY = minY - rangeY * .05
        self.maxY = maxY + rangeY * .05

        self.xml['minX'] = self.minX
        self.xml['maxX'] = self.maxX
        self.xml['minY'] = self.minY
        self.xml['maxY'] = self.maxY

    def setRegLine (self):
        settings = self.graph().settings
        if self.regLine:
            self.regLineAux (self.data, self.xlist, self.ylist,
                             (self.minX, self.maxX), (self.minY, self.maxY),
                             settings.regLineColor, settings.regLineWidth)

    def regLineAux (self, group, xlist, ylist, xbounds, ybounds, color, width):
        r = RegressionLine (xlist, ylist, xbounds, ybounds)
        r.style.strokeWidth = width
        r.style.strokeColor = color
        group.draw (r)

    def finalize (self):
        self.draw (self.data)
        if len (self.dataPoints) > 0:
            self.data.draw (self.dataPoints)

        self.setRegLine ()
        self.addColor ()

        self.data.transform = self.makeTransform (self.minX, self.maxX, self.minY, self.maxY)

class DoubleScatterCanvas (ScatterCanvas):
    def __init__ (self, **attr):
        ScatterCanvas.__init__ (self, **attr)
        self.data2 = Grouping ()
        self.dataPoints2 = Group (id = 'data2')

    def drawPoint (self, name, x, y):
        settings = self.graph ().settings
        self.drawPointAux (self.dataPoints, name, x, y, settings.g1MarkerType, settings.g1MarkerSize)

    def drawPoint2 (self, name, x, y):
        settings = self.graph ().settings
        self.drawPointAux (self.dataPoints2, name, x, y, settings.g2MarkerType, settings.g2MarkerSize)

    def addColor (self):
        settings = self.graph ().settings
        if settings.g1ColorScheme == 'tripleAxis':
            self.setTripleColor (self.dataPoints, settings.g1Color1, settings.g1Color2, settings.g1Color3)
        elif settings.g1ColorScheme == 'solid':
            self.setSolidColor (self.dataPoints, settings.g1Color1)

        if settings.g2ColorScheme == 'tripleAxis':
            self.setTripleColor (self.dataPoints2, settings.g2Color1, settings.g2Color2, settings.g2Color3)
        elif settings.g2ColorScheme == 'solid':
            self.setSolidColor (self.dataPoints2, settings.g2Color1)
        #for child in self.data:
        #    child.style.fill = self.color1
        #for child in self.data2:
        #    child.style.fill = self.color2

    def setBounds (self):
        self.xlist = []
        self.x2list = []
        self.ylist = []
        self.y2list = []
        for child in self.dataPoints:
            self.xlist.append (child.x)
            self.ylist.append (child.y)

        for child in self.dataPoints2:
            self.x2list.append (child.x)
            self.y2list.append (child.y)

        minX = min (self.xlist + self.x2list)
        maxX = max (self.xlist + self.x2list)
        minY = min (self.ylist)
        maxY = max (self.ylist)
        minY2 = min (self.y2list)
        maxY2 = max (self.y2list)
        rangeX = maxX - minX
        rangeY = maxY - minY
        rangeY2 = maxY2 - minY2

        self.minX = minX - rangeX * .05
        self.maxX = maxX + rangeX * .05
        self.minY= minY - rangeY * .05
        self.maxY = maxY + rangeY * .05
        self.minY2 = minY2 - rangeY2 * .05
        self.maxY2 = maxY2 + rangeY2 * .05

        self.xml['minX'] = self.minX
        self.xml['maxX'] = self.maxX
        self.xml['minY'] = self.minY
        self.xml['maxY'] = self.maxY
        self.xml['minY2'] = self.minY2
        self.xml['maxY2'] = self.maxY2

    def setRegLine (self):
        settings = self.graph ().settings
        if settings.g1RegLine:
            self.regLineAux (self.data, self.xlist, self.ylist,
                             (self.minX, self.maxX), (self.minY, self.maxY),
                             settings.g1RegLineColor, settings.g1RegLineWidth)

    def setRegLine2 (self):
        settings = self.graph ().settings
        if settings.g2RegLine:
            self.regLineAux (self.data2, self.x2list, self.y2list,
                             (self.minX, self.maxX), (self.minY2, self.maxY2),
                             settings.g2RegLineColor, settings.g2RegLineWidth)

    def finalize (self):
        ScatterCanvas.finalize (self)
        self.draw (self.data2)
        if len (self.dataPoints2) > 0:
            self.data2.draw(self.dataPoints2)
        self.setRegLine2 ()
        self.data2.transform = self.makeTransform (self.minX, self.maxX, self.minY2, self.maxY2)


class LineCanvas (GraphCanvas):
    def __init__ (self, **attr):
        GraphCanvas.__init__ (self, **attr)
        self.data = Grouping ()
        self.dataPoints =  Group (id = 'data')
        self.colors = {}
        self.seriesLength = 1

    def setBounds (self):
        ylist = []
        for group in self.data:
            points = group.getElementByClassName ('point-group')
            for child in points:
                ylist.append (child.y)
        self.minX = 0
        self.maxX = self.seriesLength - 1
        self.minY = min (ylist)
        self.maxY = max (ylist)

    def addColor (self):
        for group in self.data:
            try:
                color = self.colors[group.id]
            except KeyError:
                color = 'black'
            for child in group.getElementByClassName ('point-group'):
                child.style.fill = color
            group.getElementByName ('path').style.strokeColor = color

    def addData (self, name, *data):
        group = Group (id = name)
        pointGroup = Group (className = 'point-group')
        path = None
        if len (data) > self.seriesLength:
            self.seriesLength = len (data)
        for i, val in enumerate (data):
            if val is None: 
                continue
            if not path:
                path = Path ()
                path.move (i, val)
            else:
                path.line (i, val)
            c = Circle (radius = 2, x = i, y = val)
            pointGroup.draw (c)
        if path:
            path.style.fill = 'none'
            group.draw (path)
        if len (pointGroup) > 0:
            group.draw (pointGroup)
            self.data.draw (group)

    def finalize (self):
        self.draw (self.data)
        if len (self.dataPoints) > 0:
            self.draw (self.dataPoints)
        self.addColor ()
        self.data.transform = self.makeTransform (self.minX, self.maxX, self.minY, self.maxY)        


class BarCanvas (GraphCanvas):
    def __init__ (self, **attr):
        GraphCanvas.__init__ (self, **attr)
        self.data = Group (id = 'data')
        self.counter = 0.0
        self.lastBar = 0
        self.colors = {}

    def addBar (self, group, name, val):
        settings = self.graph ().settings
        rect = Rectangle (x = self.counter, y = 0, height = val, width = 1)
        self.data.draw (rect)
        rect.xml['has-tooltip'] = True
        rect.xml['name'] = name
        rect.xml['group'] = group
        if group and name:
            rect.xml['data'] = str(group) + ': ' + str(name)
        elif group:
            rect.xml['data'] = str(group)
        elif name:
            rect.xml['data'] = str(name)
        else:
            rect.xml['data'] = None
        rounded = match ('-?\d*(\.\d{2})?', str (val))
        strVal = rounded.group (0);
        rect.xml['tooltip-text'] = 'Value: ' + strVal
        self.lastBar = self.counter + settings.barWidth
        self.counter += (settings.barWidth + settings.barSpacing)
        
    def addSpace (self):
        self.counter += self.graph ().settings.blankSpace

    def setBounds (self):
        ylist = []
        for child in self.data:
            ylist.append (child.height)
        
        if len (ylist):
            minY = min (ylist)
            maxY = max (ylist)

            rangeY = maxY - minY
            
            if rangeY:
                self.minY = minY - rangeY * .05
                self.maxY = maxY + rangeY * .05
            else:
                self.minY = minY - 1.0
                self.maxY = maxY + 1.0

            if self.lastBar:
                self.minX = 0
                self.maxX = self.lastBar
            
            else:
                self.minX = 0
                self.maxX = 1

        else:

            self.minX = 0.0
            self.maxX = 1.0
            self.minY = 0.0
            self.maxY = 1.0


        self.xml['minX'] = self.minX
        self.xml['maxX'] = self.maxX
        self.xml['minY'] = self.minY
        self.xml['maxY'] = self.maxY

        self.barHeights ()


    def addColor (self):
        for child in self.data:
            try:
                key = child.xml['name']
                child.style.fill = self.colors[key]
            except KeyError:
                child.style.fill = self.graph ().settings.barColor
            if child.xml['has-tooltip']:
                child.xml['has-highlight'] = True
                child.xml['default-fill'] = child.style.fill
                child.xml['highlight-fill'] = child.style.fill.interpolate (white, .35)

    def barHeights (self):
        for child in self.data:
            child.y = self.minY
            child.height -= self.minY

    def finalize (self):
        self.addColor ()
        if len (self.data) > 0:
            self.draw (self.data)

        self.data.transform = self.makeTransform (self.minX, self.maxX, self.minY, self.maxY)

class HorizontalBarCanvas (BarCanvas):
    def addBar (self, group, name, val):
        settings = self.graph ().settings
        rect = Rectangle (y = self.counter, x = 0, height = 1, width = val)
        self.data.draw (rect)
        rect.xml['has-tooltip'] = True
        rect.xml['name'] = name
        rect.xml['group'] = group
        if group and name:
            rect.xml['data'] = str(group) + ': ' + str(name)
        elif group:
            rect.xml['data'] = str(group)
        elif name:
            rect.xml['data'] = str(name)
        else:
            rect.xml['data'] = None
        rect.xml['tooltip-text'] = 'Value: ' + str (val)
        self.lastBar = self.counter + settings.barWidth
        self.counter += (settings.barWidth + settings.barSpacing)

    def setBounds (self):
        xlist = []
        for child in self.data:
            xlist.append (child.width)
        
        minX = min (xlist)
        maxX = max (xlist)

        self.minX = 0
        self.maxX = maxX + maxX * .05
        #self.minY = minY - minY * .05
        self.minY = 0
        self.maxY = self.lastBar

        self.xml['minX'] = self.minX
        self.xml['maxX'] = self.maxX
        self.xml['minY'] = self.minY
        self.xml['maxY'] = self.maxY

        self.barHeights ()

    def barHeights (self):
        for child in self.data:
            child.x = self.minX
            child.width -= self.minX


class PieCanvas (GraphCanvas):
    def __init__ (self, **attr):
        GraphCanvas.__init__ (self, **attr)
        self.values = []
        self.names = []

    def addData (self, name, value):
        self.values.append (value)
        self.names.append (name)
        
    def finalize (self):
        radius = min (self.width, self.height) / 2.0 - 10.0
        x = self.x + self.width / 2.0
        y = self.y + self.height / 2.0
        total = sum (self.values)
        data = zip (self.values, self.names)
        data.sort ()
        current = pi / 2.0
        for value, name in data:
            rad = (value / total) * (2 * pi)
            s = Sector (radius, current, rad, x = x, y = y)
            s.xml ['name'] = name
            s.style.fill = 'red'
            s.style.strokeWidth = .5
            s.style.strokeColor = 'black'
            self.draw (s)
            current += rad
