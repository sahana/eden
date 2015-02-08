from base import BaseGraph, UnifiedGraph
from canvas import ScatterCanvas, DoubleScatterCanvas, BarCanvas, HorizontalBarCanvas, PieCanvas, LineCanvas
from axes import YAxis

from ..utils.struct import Vector as V

from ..graphics.utils import ViewBox, Translate, Rotate, addAttr, blank, boolean
from ..graphics.color import hex_to_color, Color 
from ..graphics.shapes import Line, Rectangle, Text
from ..graphics.group import Group


class Graph (BaseGraph):
    def __init__ (self, **attr):
       BaseGraph.__init__ (self, None, **attr) 


class ScatterPlot (UnifiedGraph):
    def __init__ (self, regLine = True, settings = None):
        UnifiedGraph.__init__ (self, 
                               ScatterCanvas, 
                               regLine = regLine, 
                               settings = settings)
        #self.addScript (self.jsLocator ())

    def jsLocator (self):
        return """
  function Locator (root) {
    var canvasRoot = root;
  }

  registerEvent (window, 'load', function () {
                                   var root = document.getElementById ('canvas-root');
                                   var l = new Locator (root);
                                 }
"""

    def jsPosition (self):
        return """

function showPosition (element) {
  
}          

"""

    def formatSettings (self, settings):
        UnifiedGraph.formatSettings (self, settings)
        
        addAttr (settings, 'markerSize', float, 2.0)
        addAttr (settings, 'markerType', str, 'circle')

        addAttr (settings, 'colorScheme', str, 'tripleAxis')
        addAttr (settings, 'color1', hex_to_color, hex_to_color ('ff0000'))
        addAttr (settings, 'color2', hex_to_color, hex_to_color ('00ff00'))
        addAttr (settings, 'color3', hex_to_color, hex_to_color ('0000ff'))
        
        addAttr (settings, 'regLineColor', hex_to_color, hex_to_color('000000'))
        addAttr (settings, 'regLineWidth', float, 1.0)

    def setColors (self, color1= None, color2 = None, color3 = None):
        self.settings.color1 = color1
        self.settings.color2 = color2
        self.settings.color3 = color3

    def setProperties (self):
        self.xaxis = True
        self.yaxis = True
        self.y2axis = False

    def addPoint (self, x, y, name = None):
        self.canvas.drawPoint (name, x, y)


class DoubleScatterPlot (ScatterPlot):
    def __init__ (self, **attr):
        UnifiedGraph.__init__ (self, DoubleScatterCanvas, **attr)

    def jsPosition (self):
        return """
function showPosition (element) {
  
}          
    """

    def formatSettings (self, settings):
        UnifiedGraph.formatSettings (self, settings)
        
        addAttr (settings, 'g1MarkerType', str, 'circle')
        addAttr (settings, 'g1MarkerSize', float, '2.0')
        addAttr (settings, 'g1ColorScheme', str, 'solid')
        addAttr (settings, 'g1Color1', hex_to_color, Color (255, 0, 0))
        addAttr (settings, 'g1Color2', hex_to_color, Color (0, 255, 0))
        addAttr (settings, 'g1Color3', hex_to_color, Color (0, 0, 255))
        addAttr (settings, 'g1RegLine', boolean, False)
        addAttr (settings, 'g1RegLineColor', hex_to_color, Color (0, 0, 0))
        addAttr (settings, 'g1RegLineWidth', float, 1.0)

        addAttr (settings, 'g2MarkerType', str, 'square')
        addAttr (settings, 'g2MarkerSize', float, '4.0')
        addAttr (settings, 'g2ColorScheme', str, 'solid')
        addAttr (settings, 'g2Color1', hex_to_color, Color (0, 0, 255))
        addAttr (settings, 'g2Color2', hex_to_color, Color (0, 255, 0))
        addAttr (settings, 'g2Color3', hex_to_color, Color (255, 0, 0))
        addAttr (settings, 'g2RegLine', boolean, False)
        addAttr (settings, 'g2RegLineColor', hex_to_color, Color (0, 0, 0))
        addAttr (settings, 'g2RegLineWidth', float, 1.0)

    def setColors (self, color1, color2):
        raise NotImplementedError ()

    def setProperties (self):
        self.xaxis = True
        self.yaxis = True
        self.y2axis = True

    """def setY2Bounds (self):
        return (self.canvas.minY2, self.canvas.maxY2)"""

    def addPoint1 (self, x, y, name = None):
        self.canvas.drawPoint (name, x, y)        

    def addPoint2 (self, x, y, name = None):
        self.canvas.drawPoint2 (name, x, y)


class BarGraph (UnifiedGraph):
    def __init__ (self, **attr):
        """if attr.has_key ('horizontal') and attr['horizontal']:
            self.horizontal = True
            UnifiedGraph.__init__ (self, HorizontalBarCanvas, **attr)
        else:
            self.horizontal = False
            UnifiedGraph.__init__ (self, BarCanvas, **attr)"""
        UnifiedGraph.__init__ (self, None, **attr)
        if self.settings.horizontal == True:
            self.attachCanvas (HorizontalBarCanvas)
        else:
            self.attachCanvas (BarCanvas)
        #self.addScript ('hs/static/highlight.js')

    def formatSettings (self, settings):
        UnifiedGraph.formatSettings (self, settings)
        
        addAttr (settings, 'barColor', hex_to_color, Color (210, 10, 10))    
        addAttr (settings, 'barWidth', float, 1.0)    
        addAttr (settings, 'barSpacing', float, .1)    
        addAttr (settings, 'blankSpace', float, .5)

        addAttr (settings, 'horizontal', boolean, False)

    def jsChangeTooltipPos (self):
        if not self.settings.horizontal:
            return UnifiedGraph.jsChangeTooltipPos (self)
        else:
            return """
      if (target.getAttribute ('width'))
        targetWidth = parseFloat (target.getAttribute ('width'));
      else
        targetWidth = 0;
      v.x += targetWidth"""

    def setProperties (self):
        if self.settings.horizontal:
            self.xaxis = True
            self.yaxis = True
            self.y2axis = False
        else:
            self.xaxis = True
            self.yaxis = True
            self.y2axis = False

    def setColors (self, colors):
        self.canvas.colors = colors

    def addSpace (self):
        self.canvas.addSpace ()

    def addBar (self, name, data):
        self.canvas.addBar (None, name, data)
        #if self.horizontal:
        #    self.ylabels.append (name)

    def addGroup (self, name, data):
        for key, value in data:
            self.canvas.addBar (name, key, value)
        self.canvas.addSpace ()

    def createXAxisSpace (self):
        if self.settings.horizontal:
            UnifiedGraph.createXAxisSpace (self)
        else:
            h = self.settings.xAxisTextHeight
            width = []
            for child in self.canvas.data:
                if child.xml.has_key ('data') and not child.xml['data'] is None :
                    w = Text.textWidth (child.xml['data'], h)
                    width.append (w)
            if len (width) > 0:
                maxWidth = max (width)
            else:
                maxWidth = 0
            delta = self.settings.xAxisSpace + maxWidth
            self.canvas.move (0, delta)
            self.canvas.changeSize (0, -delta)

    def createYAxis (self):
        if not self.settings.horizontal:
            UnifiedGraph.createYAxis (self)
        else:
            for child in self.canvas.data:
                self.ypositions.append (child.y + (child.height / 2.0))
                self.ylabels.append (child.xml['data'])
            UnifiedGraph.createYAxis (self)

    def createXAxis (self):
        ax = Group ()
        x = self.canvas.x - self.canvas.height
        y = self.canvas.y + self.canvas.height
        ax.appendTransform (Rotate (-90, self.canvas.x, y))
        if self.settings.horizontal:
            UnifiedGraph.createXAxis (self)
        else:
            textProperties = {'textHeight': self.settings.xAxisTextHeight,
                              'verticalAnchor': 'middle',
                              'horizontalAnchor': 'right',
                              }
            xaxis = YAxis (id = 'x-axis',
                           inf = self.canvas.y + self.canvas.height,
                           sup = self.canvas.y + self.canvas.height - self.canvas.width,
                           x = self.canvas.x - self.canvas.height - self.settings.xAxisSpace,
                           lower = self.xbounds[0],
                           upper = self.xbounds[1],
                           textProperties = textProperties)
            ticks = []
            labels = []
            for child in self.canvas.data:
                if child.xml.has_key ('name'):
                    ticks.append (child.x + child.width / 2.0)
                    labels.append (child.xml['data'])
            xaxis.createTicks (ticks)
            xaxis.setText (map (str, labels))
            xaxis.drawTicks ()
            ax.draw (xaxis)
            self.dataGroup.drawAt (ax, 0)
        

    def setSVG (self):
        attr = UnifiedGraph.setSVG (self)
        return attr


class LineChart (UnifiedGraph):
    def __init__ (self, **attr):
        UnifiedGraph.__init__ (self, LineCanvas, **attr)

    def setProperties (self):
        self.xaxis = True
        self.yaxis = True
        self.y2axis = False

    def setColors (self, colorDict):
        self.canvas.colors.update (colorDict)

    def addSeries (self, name, series):
        self.canvas.addData (name, *series)
    
    def setSeriesNames (self, seriesNames):
        self.xlabels = seriesNames


class PieChart (BaseGraph):
    def __init__ (self, **attr):
        BaseGraph.__init__ (self, PieCanvas)
        self.addScript ('hs/static/pie.js')

    def addWedge (self, name, value):
        self.canvas.addData (name, float (value))

    def finalize (self):
        BaseGraph.finalize (self) 
        self.canvas.finalize ()
