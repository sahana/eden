from axes import XAxis, YAxis

from ..graphics import Canvas, PrintableCanvas
from ..graphics.group import Group, Grouping
from ..graphics.shapes import Line, Rectangle, Text
from ..graphics.utils import ViewBox, Translate, Rotate, addAttr, blank, boolean
from ..graphics.color import hex_to_color, Color

from ..utils.struct import Matrix
from ..utils.struct import Vector as V

from re import match


class BaseGraph (PrintableCanvas):
    def __init__ (self, canvasType, **attr):
        if attr.has_key ('settings') and attr['settings']:
            self.applySettings (attr['settings'])
        else:
            self.formatSettings (blank ())
        if attr.has_key ('width'):
            self.settings.width = attr['width']
        if attr.has_key ('height'):
            self.settings.height = attr['height']
        
        view = ViewBox (0, 0, self.settings.width, self.settings.height)
        PrintableCanvas.__init__ (self, viewBox = view, **attr)

        self.addScript (self.jsUtils ())
        self.addScript (self.jsHighlight ())

        self.dataGroup = Grouping ()
        if canvasType:
            self.attachCanvas (canvasType, **attr)
        else:
            self.canvas = None
        self.draw (self.dataGroup)
        self.initialFormatting ()

    def attachCanvas (self, canvasType, **attr):
        self.canvas = canvasType (width = self.settings.width - self.settings.leftMargin - self.settings.rightMargin, 
                                  height = self.settings.height - self.settings.topMargin - self.settings.bottomMargin, 
                                  x = self.settings.leftMargin,
                                  y = self.settings.topMargin,
                                  id='canvas-root',
                                  **attr)
        self.dataGroup.draw (self.canvas)

    def jsUtils (self):
        return """
  function registerEvent (object, event, method, scope, capture) {
    if (!scope)
      scope = window;
    if (!capture)
      capture = false;
    var func = function (event) {
      if (!event)
        event = window.event;
      return method.call (scope, event);
    }

    if (object.addEventListener)
      object.addEventListener (event, func, capture);
    else if (object.attachEvent)
      object.attachEvent (event, method, func, capture);
    else
      return false;
    return true;
  }

  function ViewBox (x, y, width, height) {
    this.x = parseFloat (x);
    this.y = parseFloat (y);
    this.width = parseFloat (width);
    this.height = parseFloat (height);

    this.quadrant = function (v) {
      var midX = this.x + (this.width / 2.0);
      var midY = this.y + (this.height / 2.0);

      if (v.y <= midY) {
	if (v.x >= midX)
	  return 1;
	else
	  return 2;
      }
      else {
	if (v.x <= midX)
	  return 3;
	else
	  return 4;
      }
    }
  }

  function getView (viewer) {
    var view = viewer.getAttribute ('viewBox');
    view = view.split (' ');
    return new ViewBox (view[0], view[1], view[2], view[3]);
  }

  function vect (x, y) {
    this.x = x;
    this.y = y;
  }

  function pos (node) {
    var x, y;
    if (node.getAttribute ('x')) {
      x = node.getAttribute ('x');
      y = node.getAttribute ('y');
    }
    else if (node.getAttribute ('cx')) {
      x = node.getAttribute ('cx');
      y = node.getAttribute ('cy');
    }
    x = parseFloat (x);
    y = parseFloat (y);
    return new vect (x, y);
  }
"""

    def jsHighlight (self):
        return """
  function highlight (event) {
    this.setAttribute ('fill', this.getAttribute ('highlight-fill'));
  }

  function unHighlight (event) {
    this.setAttribute ('fill', this.getAttribute ('default-fill'));
  }

  function addHighlights (node) {
    if (node.getAttribute) {
      if (node.getAttribute ('has-highlight')) {
        node.setAttribute ('default-fill', node.getAttribute ('fill'));
        registerEvent (node, 'mouseover', highlight, node);
        registerEvent (node, 'mouseout', unHighlight, node);
      }
      for (var i = 0; i < node.childNodes.length; i ++) {
        addHighlights (node.childNodes[i]);
      }
    }
  }

  registerEvent (window, 'load', function () {
                                   var root = document.getElementById ('canvas-root');
                                   addHighlights (root); 
                                 });
"""

    def applySettings (self, filenameOrDict):
        if type (filenameOrDict) == str:
            file = open (filenameOrDict)
            buffer = file.read ()
            setList = []
            for child in buffer.split ('\n'):
                if len (child) == 0:
                    continue
                if child.startswith ('#'):
                    continue
                pair = match ('^([^=]+)=(.*)$', child)
                if pair is None:
                    print 'Warning, Bad formatting in line: ' + child
                    continue
                key = pair.group (1)
                value = pair.group (2)
                setList.append ((key.strip (), value.strip ()))
            settings = blank ()
            for key, value in setList:
                setattr (settings, key, value)
        elif type (filenameOrDict) == dict:
            settings = blank ()
            for key, value in filenameOrDict.iteritems ():
                setattr (settings, key, str (value))
        else:
            raise RuntimeError ('Bad type for settings')
        self.formatSettings (settings)

    def formatSettings (self, settings):
        addAttr (settings, 'width', float, 300.0)
        addAttr (settings, 'height', float, 200.0)
        addAttr (settings, 'fixedWidth', float, None)

        addAttr (settings, 'titleSize', float, 10.0)
        addAttr (settings, 'xLabelSize', float, 8.0)
        addAttr (settings, 'yLabelSize', float, 8.0)
        addAttr (settings, 'y2LabelSize', float, 8.0)

        addAttr (settings, 'leftMargin', float, 10.0)
        addAttr (settings, 'rightMargin', float, 10.0)
        addAttr (settings, 'topMargin', float, 10.0)
        addAttr (settings, 'bottomMargin', float, 10.0)

        addAttr (settings, 'titleSpace', float, 10.0)
        addAttr (settings, 'xLabelSpace', float, 10.0)
        addAttr (settings, 'yLabelSpace', float, 10.0)
        addAttr (settings, 'y2LabelSpace', float, 10.0)

        addAttr (settings, 'tooltipSize', float, 7.0)
        
        self.settings = settings

    def initialFormatting  (self):
        # Format Label Group
        self.labels = Group (className = 'labels')

        # Format Title
        self.title = Text (text = '', 
                           id = 'title', 
                           textHeight= self.settings.titleSize, 
                           horizontalAnchor = 'center')

        # Format X Label
        self.xlabel = Text (text = '', 
                            id = 'xlabel', 
                            textHeight = self.settings.xLabelSize, 
                            verticalAnchor = 'bottom', 
                            horizontalAnchor = 'center')

        # Format Y Label
        self.ylabel = Group ()
        ylabelRotate = Rotate (-90)
        self.ylabel.appendTransform (ylabelRotate)
        self.ylabelText = Text (text = '',
                                id = 'ylabel', 
                                textHeight = self.settings.yLabelSize,  
                                horizontalAnchor = 'center')
        self.ylabel.draw (self.ylabelText)

        # Format Y2 Label
        self.y2label = Group ()
        y2labelRotate = Rotate (90, self.settings.width, 0)
        self.y2label.appendTransform (y2labelRotate)
        self.y2labelText = Text (text = '', 
                                 id = 'y2label', 
                                 textHeight = self.settings.y2LabelSize,  
                                 horizontalAnchor = 'center')
        self.y2label.draw (self.y2labelText)

    def positionLabels (self):
        if self.canvas:
            topY = self.settings.height - (self.canvas.height + self.canvas.y)
            midX = self.canvas.x + (self.canvas.width) / 2.0
            midY = topY + (self.canvas.height) / 2.0 
        else:
            midX = self.settings.width / 2.0
            midY = self.settings.height / 2.0

        # Title Position
        self.title.move (midX, self.settings.topMargin)

        # Y Label Position
        self.ylabelText.move (-midY, self.settings.leftMargin)
    
        # X Label Position
        self.xlabel.move (midX, self.settings.height - self.settings.bottomMargin) 

        # Y2 Label Position
        self.y2labelText.move (self.settings.width + midY, self.settings.rightMargin)

    def setTitle (self, title):
        self.title.setText (title)
        self.labels.draw (self.title)
        if self.canvas:
            deltaY = self.title.height + self.settings.titleSpace
            self.canvas.changeSize (0, -deltaY)

    def setXLabel (self, xlabel):
        self.xlabel.setText (xlabel)
        self.labels.draw (self.xlabel)
        if self.canvas:
            deltaY = self.xlabel.height + self.settings.xLabelSpace
            self.canvas.move (0, deltaY)
            self.canvas.changeSize (0, -deltaY) 

    def setYLabel (self, ylabel):
        self.ylabelText.setText (ylabel)
        self.labels.draw (self.ylabel)
        if self.canvas:
            deltaX = self.ylabelText.height + self.settings.yLabelSpace
            self.canvas.move (deltaX, 0)
            self.canvas.changeSize (-deltaX, 0)

    def setY2Label (self, ylabel):
        self.y2labelText.setText (ylabel)
        self.labels.draw (self.y2label)
        if self.canvas:
            deltaX = self.y2labelText.height + self.settings.y2LabelSpace
            self.canvas.changeSize (-deltaX, 0)

    def setSVG (self):
        self.finalize ()
        attr = PrintableCanvas.setSVG (self)
        if self.settings.fixedWidth:
            height = self.settings.fixedWidth * (self.settings.height / self.settings.width)
            attr.update ([('width', self.settings.fixedWidth),
                          ('height', height)]) 
        return attr

    def finalize (self):
        self.dataGroup.transform.set (-1, 1, 1)
        self.dataGroup.transform.set (self.viewBox.y + self.viewBox.height, 1, 2)
        self.positionLabels ()
        if len (self.labels) > 0:
            self.drawAt (self.labels, 1)


class UnifiedGraph (BaseGraph):
    def __init__ (self, canvas,  **attr):
        BaseGraph.__init__ (self, canvas, **attr)
        self.addScript (self.jsCanvasZone ())
        self.addScript (self.jsTooltip ())
        self.setProperties ()
        self.xlabels = []
        self.ylabels = []
        self.ypositions = []
        self.y2labels = []

    def formatSettings (self, settings):
        BaseGraph.formatSettings (self, settings)

        addAttr (settings, 'xAxisSpace', float, 2.0)
        addAttr (settings, 'yAxisSpace', float, 2.0)
        addAttr (settings, 'y2AxisSpace', float, 2.0)

        addAttr (settings, 'xAxisTextHeight', float, 6.0)
        addAttr (settings, 'yAxisTextHeight', float, 6.0)
        addAttr (settings, 'y2AxisTextHeight', float, 6.0) 

        addAttr (settings, 'bg', boolean, True)
        addAttr (settings, 'bgBarDir', str, 'horizontal')
        addAttr (settings, 'bgBars', int, 6)
        addAttr (settings, 'bgColor1', hex_to_color, hex_to_color ('efefef'))
        addAttr (settings, 'bgColor2', hex_to_color, hex_to_color ('c1c1c1'))

        addAttr (settings, 'canvasBorder', boolean, True)
        addAttr (settings, 'canvasBorderWidth', float, 1.0)
        addAttr (settings, 'canvasBorderColor', hex_to_color, Color (0, 0, 0))

        addAttr (settings, 'tooltipXOffset', float, 10.0)
        addAttr (settings, 'tooltipYOffset', float, 10.0)
        addAttr (settings, 'tooltipXPadding', float, 20.0)
        addAttr (settings, 'tooltipYPadding', float, 10.0)

    def jsCanvasZone (self):
        return """
  function addCanvasZone (event) {
    var canvasRoot = document.getElementById ('canvas-root');
    var canvasRect = document.createElementNS ('http://www.w3.org/2000/svg', 'rect');
    canvasRect.id = 'canvas-rect';
    var view = getView (canvasRoot);
    canvasRect.setAttribute ('x', view.x);
    canvasRect.setAttribute ('y', view.y);
    canvasRect.setAttribute ('width', view.width);
    canvasRect.setAttribute ('height', view.height);
    canvasRect.setAttribute ('opacity', 0);
    canvasRoot.insertBefore (canvasRect, canvasRoot.childNodes[0]);
  }

  registerEvent (window, 'load', addCanvasZone);
"""

    def jsTooltip (self):
        settings = self.root ().settings
        return """
  function Tooltip (root) {
    var canvasRoot = root;
    var tooltipGroup;
    var tooltipPath;
    var tooltipTextNode;
    var tooltipText;
    var xPadding = """ + str (settings.tooltipXPadding) + """;
    var yPadding = """ + str (settings.tooltipYPadding) + """; 
    var xOffset = """ + str (settings.tooltipXOffset) + """;
    var yOffset = """ + str (settings.tooltipYOffset) + """;

    this.setText = function (value) {
      tooltipText.nodeValue = value;
      setPath ();
      positionText ();
    }

    this.move = function (target) {
      var v = pos (target)
""" + self.jsChangeTooltipPos () + """   
      var o = getOffset (target);
      var transform = 'translate(' + (v.x + o.x) + ' ' + (v.y + o.y) + ')'
      tooltipGroup.setAttribute ('transform', transform);
    }

    this.show = function () {
      tooltipGroup.setAttribute ('visibility', 'visible');
    }

    this.hide = function (event) {
      tooltipGroup.setAttribute ('visibility', 'hidden');
    }

    var setPath = function () {
      var width = parseFloat (tooltipTextNode.getBBox().width) + xPadding;
      var height = parseFloat (tooltipTextNode.getBBox ().height) + yPadding;
      var data = 'M 0 0 ';
      data += 'L ' + width + ' 0 ';
      data += 'L ' + width + ' ' + height + ' ';
      data += 'L ' + 0 + ' ' + height + ' ';
      data += 'Z'
      tooltipPath.setAttribute ('d', data);
    }

    var positionText = function () {
        tooltipTextNode.setAttribute ('x', 0);
        tooltipTextNode.setAttribute ('y', 0);
        var box = tooltipTextNode.getBBox ();
        tooltipTextNode.setAttribute ('x', xPadding / 2.0);
        tooltipTextNode.setAttribute ('y', -box.y + (yPadding / 2.0));

    }

    var getOffset = function (target) {
      var v = pos (target);
      var x, y;
      targetWidth;
""" + self.jsChangeTooltipPos () + """   
      var width = parseFloat (tooltipTextNode.getBBox().width);
      var height = parseFloat (tooltipTextNode.getBBox ().height);
      quad = getView (canvasRoot).quadrant (v);
      switch (quad) {
      case 1:
        x = -(width + xPadding + xOffset);
        y = yOffset;
        break;
      case 2:
        x = xOffset;
        y = yOffset;
        break;
      case 3:
        x = xOffset;
        y = -(height + yPadding + yOffset);
        break;
      case 4:
        x = -(width + xPadding + xOffset);
        y = -(height + yPadding + yOffset);
      }
      return new vect (x, y);
    }

    var tooltipDOM = function () {
      tooltipGroup = document.createElementNS ('http://www.w3.org/2000/svg', 'g');
      tooltipPath = document.createElementNS ('http://www.w3.org/2000/svg', 'path');
      tooltipTextNode = document.createElementNS ('http://www.w3.org/2000/svg', 'text');
      tooltipText = document.createTextNode ('TestNode');

      tooltipPath.setAttribute ('fill', 'white');
      tooltipPath.setAttribute ('stroke', 'black');

      tooltipTextNode.setAttribute ('font-family', 'arial, sans-serif');
      tooltipTextNode.setAttribute ('font-size', """ + str (settings.tooltipSize) + """);
      tooltipTextNode.setAttribute ('text-anchor', 'start');

      canvasRoot.appendChild (tooltipGroup);
      tooltipGroup.appendChild (tooltipPath);
      tooltipGroup.appendChild (tooltipTextNode);
      tooltipTextNode.appendChild (tooltipText);

      this.hide ();

      setEvents.call (this, canvasRoot);
    }

    var onHover = function (event) {
      var target = event.target;
      p = pos (target);  
      this.setText (target.getAttribute ('tooltip-text'));
      this.move (target);
      this.show ();
    }

    var unHover = function (event) {
      this.hide ();
    }

    var setEvents = function (node) {
      if (node.getAttribute) {
        if (node.getAttribute ('has-tooltip') && node.getAttribute ('has-tooltip') != 'False') {
          registerEvent (node, 'mouseover', onHover, this);
          registerEvent (node, 'mouseout', unHover, this);
        }
        for (var i = 0; i < node.childNodes.length; i ++) {
          setEvents.call (this, node.childNodes[i]);
        }
      }
    }

    tooltipDOM.call (this);
  }

  registerEvent (window, 'load', function () {
                                   var root = document.getElementById ('canvas-root');
                                   var t = new Tooltip (root);
                                 });
"""

    def jsChangeTooltipPos (self):
        return """
      if (target.getAttribute ('width'))
        targetWidth = parseFloat (target.getAttribute ('width'));
      else
        targetWidth = 0;
      targetWidth /= 2.0;
      v.x += targetWidth """
    
    def setProperties (self):
        self.xaxis = False
        self.yaxis = False
        self.y2axis = False

    def boundingBox (self):
        if not self.settings.canvasBorder:
            return
        bbox = Rectangle (x =  self.canvas.x,
                          y = self.canvas.y,
                          width= self.canvas.width, 
                          height = self.canvas.height)
        bbox.style.strokeColor = self.settings.canvasBorderColor
        bbox.style.strokeWidth = self.settings.canvasBorderWidth
        bbox.style.fill = 'none'
        self.dataGroup.draw (bbox)

    def background (self):
        if not self.settings.bg:
            return
        numBars = self.settings.bgBars
        color1 = self.settings.bgColor1
        color2 = self.settings.bgColor2
        if self.settings.bgBarDir == 'vertical':
            barHeight =self.canvas.height
            barWidth = self.canvas.width / float (numBars)
            offsetW = 1.0
            offsetH = 0
        else:    
            barHeight = self.canvas.height / float (numBars)
            barWidth = self.canvas.width
            offsetW = 0
            offsetH = 1.0
        
            
        for i in range (numBars):
            rect = Rectangle (x = (self.canvas.x + barWidth * float(i) * offsetW),
                              y = (self.canvas.y + barHeight * float(i) * offsetH),
                              width = barWidth,
                              height = barHeight)
            if i % 2 == 0:
                fill = color1
            else:
                fill = color2
            rect.style.fill = fill
            rect.style.strokeWidth = 0
            rect.style.opacity = .35
            self.dataGroup.drawAt (rect, 0)

    def setXBounds (self):
        self.xbounds = (self.canvas.minX, self.canvas.maxX)

    def setYBounds (self):
        self.ybounds = (self.canvas.minY, self.canvas.maxY)

    def setY2Bounds (self):
        self.y2bounds = (self.canvas.minY2, self.canvas.maxY2)

    def createXAxisSpace (self):
        self.canvas.move (0, self.settings.xAxisTextHeight)
        self.canvas.changeSize (0, -self.settings.xAxisTextHeight)
        self.xAxisPos = self.canvas.y
        self.canvas.move (0, self.settings.xAxisSpace)
        self.canvas.changeSize (0, -self.settings.xAxisSpace)

    def createXAxis (self):
        textProperties = {'textHeight': self.settings.xAxisTextHeight,
                          'horizontalAnchor': 'center',
                          }
        xaxis = XAxis (id = 'x-axis',
                       inf = self.canvas.x,
                       sup = self.canvas.x + self.canvas.width,
                       y = self.xAxisPos,
                       lower = self.xbounds[0],
                       upper = self.xbounds[1],
                       textProperties = textProperties)
        xaxis.createTicks ()
        if self.xlabels:
            xaxis.setText (self.xlabels)
        xaxis.drawTicks ()
        self.dataGroup.drawAt (xaxis, 0)

    def createYAxis (self):
        textProperties = {'textHeight': self.settings.yAxisTextHeight,
                          'horizontalAnchor': 'right',
                          'verticalAnchor': 'middle',
                          }
        yaxis = YAxis (inf = self.canvas.y,
                       sup = self.canvas.y + self.canvas.height,
                       x = 0,
                       lower = self.ybounds[0],
                       upper = self.ybounds[1],
                       textProperties = textProperties)
        yaxis.createTicks (self.ypositions)
        yaxis.setText (self.ylabels)
        yaxis.drawTicks ()
        yaxis.move (self.canvas.x + yaxis.width, 0)
        self.canvas.changeSize (-yaxis.width - self.settings.yAxisSpace, 0)
        self.canvas.move (yaxis.width + self.settings.yAxisSpace, 0)
        self.dataGroup.drawAt (yaxis, 0)

    def createY2Axis (self):
        ybounds = self.y2bounds
        textProperties = {'textHeight': self.settings.y2AxisTextHeight,
                          'horizontalAnchor': 'left',
                          'verticalAnchor': 'middle',
                          }
        yaxis = YAxis (inf = self.canvas.y,
                       sup = self.canvas.y + self.canvas.height,
                       x = 0,
                       lower = self.y2bounds[0],
                       upper = self.y2bounds[1],
                       textProperties = textProperties)
        yaxis.createTicks ()
        if self.y2labels:
            yaxis.setText (self.y2labels)
        yaxis.drawTicks ()
        yaxis.move (self.canvas.x + self.canvas.width - yaxis.width, 0)
        self.canvas.changeSize (-yaxis.width - self.settings.y2AxisSpace, 0)
        self.dataGroup.drawAt (yaxis, 0)

    def finalize (self):
        self.canvas.setBounds ()
        if self.xaxis:
            self.setXBounds ()
            self.createXAxisSpace ()
        if self.yaxis:
            self.setYBounds ()
            self.createYAxis ()
        if self.y2axis:
            self.setY2Bounds ()
            self.createY2Axis ()
        if self.xaxis:
            self.createXAxis ()
        BaseGraph.finalize (self)
        self.background ()
        self.boundingBox ()
        self.canvas.finalize ()
