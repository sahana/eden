from ..utils.struct import Vector as V
from ..graphics.group import Group
from ..graphics.shapes import Text

from copy import deepcopy

class Axis (Group):
    def __init__ (self, **attr):
        Group.__init__ (self, **attr)
        self.ticks = []
        self.labels = []
        self.incr = None
        if attr.has_key ('inf'):
            self.inf = attr['inf']
        else:
            self.inf = 0
        if attr.has_key ('sup'):
            self.sup = attr['sup']
        else:
            self.sup = 0
        if attr.has_key ('lower'):
            self.lower = attr['lower']
        else:
            self.lower = 0
        if attr.has_key ('upper'):
            self.upper = attr['upper']
        else:
            self.upper = 0
        if attr.has_key ('textProperties'):
            self.textProperties = attr['textProperties']
        else:
            self.textPrperties = {}

    def bounds (self, lower, upper):
        self.lower = lower
        self.upper = upper

    def increment (self, incr=None):
        self.incr = incr

    def findIncrement (self):
        numberRange = self.upper - self.lower
        if numberRange == 0:
            raise RuntimeError ('upper == lower')
        incr = 0
        div = 1.0
        if numberRange < 1:
            while numberRange / pow (10, incr) < 1:
                incr -= 1
            #incr += 1
        elif numberRange > 1:
            while numberRange / pow (10, incr) > 1:
                incr += 1
            incr -= 1
        ticks = self.tickPositions (pow (10, incr) / div)
        if len (ticks) < 2:
            incr -= 1
        elif len (ticks) < 5:
            div = 2
        return float (pow (10, incr)) / div

    def setText (self, text=None):
        if text:
            self.labels = text

    def tickPositions (self, incr):
        current = 0
        ticks = []
        while current > self.lower:
            current -= incr
        while current < self.lower:
            current += incr
        while current <= self.upper:
            ticks.append (current)
            current += incr
        return ticks

    def createTicks (self, tickPos = None):
        if not tickPos:
            if not self.incr:
                self.incr = self.findIncrement ()
            ticks = self.tickPositions (self.incr)
        else:
            ticks = tickPos
        for tick in ticks:
            per = ((tick - self.lower) / (self.upper - self.lower))
            val = ((1 - per) * self.inf) + (per * self.sup)
            self.ticks.append (val)
            self.labels.append (str (tick))
        return deepcopy (self.ticks)

    def drawTicks (self):
        raise RuntimeError ("Abstract base class does not have method")

    def move (self, dx, dy):
        for child in self:
            child.move (dx, dy)


class XAxis (Axis):
    def __init__ (self, **attr):
        Axis.__init__ (self, **attr)
        if attr.has_key ('y'):
            self.y = attr['y']
        else:
            self.y = 0

    def drawTicks (self):
        for pos, label in zip (self.ticks, self.labels):
            t = Text(text = str(label), x = pos, y = self.y, **self.textProperties)
            self.draw (t)

class YAxis (Axis):
    def __init__ (self, **attr):
        Axis.__init__ (self, **attr)
        if attr.has_key ('x'):
            self.x = attr['x']
        else:
            self.x = 0

    def drawTicks (self):
        width = []
        for pos, label in zip (self.ticks, self.labels):
            t = Text(text = str(label), y = pos, x = self.x, **self.textProperties)
            width.append (t.width)
            self.draw (t)
        self.width = max (width)

