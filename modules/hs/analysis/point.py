"""                                                                                                                            
    Healthscapes Geolytics Module                                                                                                   
                                                                                                                                                                               
                                                                                                                               
    @author: Nico Preston <nicopresto@gmail.com>                                                                                 
    @author: Colin Burreson <kasapo@gmail.com>                                                                         
    @author: Zack Krejci <zack.krejci@gmail.com>                                                                             
    @copyright: (c) 2010 Healthscapes                                                                             
    @license: MIT                                                                                                              
                                                                                                                               
    Permission is hereby granted, free of charge, to any person                                                                
    obtaining a copy of this software and associated documentation                                                             
    files (the "Software"), to deal in the Software without                                                                    
    restriction, including without limitation the rights to use,                                                               
    copy, modify, merge, publish, distribute, sublicense, and/or sell                                                          
    copies of the Software, and to permit persons to whom the                                                                  
    Software is furnished to do so, subject to the following                                                                   
    conditions:                                                                                                                
          
    The above copyright notice and this permission notice shall be                                                             
    included in all copies or substantial portions of the Software.                                                            
                                                                                                                               
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,                                                            
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES                                                            
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND                                                                   
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT                                                                
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,                                                               
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING                                                               
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR                                                              
    OTHER DEALINGS IN THE SOFTWARE.                                                                                            
                                                                                                                               
"""



import enum

from query import Query
from utils import Vector, decode, BoundingBox
from ..utils.dictionary import Dictionary
from base import SpatialData, SpatialCollection

from math import pow, sqrt
from re import match


class QuadTree (object):
    def __init__ (self):
        self.root = None

    def append (self, point):
        if not self.root:
            self.root = Treenode (point)
        else:
            self.root.append (point)

    def search (self, box):
        pointList = SpatialPointList ()
        self.root.search (pointList, box)
        return pointList


class Treenode (object):
    def __init__ (self, point):
        self.x = point.x
        self.y = point.y
        self.data = point
        self.first = None
        self.second = None
        self.third = None
        self.fourth = None
        """self.children = []
        self.children.append(None)
        self.children.append(None)
        self.children.append(None)
        self.children.append(None)"""

    def quadrant (self, point):
        if self.y <= point.y:
            if self.x <= point.x:
                return 1
            else:
                return 2
        else:
            if self.x >= point.x:
                return 3
            else:
                return 4

    def getNext (self, int):
        if int == 1:
            return self.first
        elif int == 2:
            return self.second
        elif int == 3:
            return self.third
        elif int == 4:
            return self.fourth

    def setNext (self, int, point):
        if int == 1:
            self.first = Treenode (point)
        elif int == 2:
            self.second = Treenode (point)
        elif int == 3:
            self.third = Treenode (point)
        elif int == 4:
            self.fourth = Treenode (point)

    def append (self, point):
        quad = self.quadrant (point)
        node = self.getNext (quad)
        if not node:
            self.setNext (quad, point)
        else:
            node.append (point)

    def search (self, pointList, box):
        if box.contains (self.data):
            pointList.append (self.data)
            for i in xrange (1, 5):
                node = self.getNext (i)
                if node:
                    node.search (pointList, box)
        else:
            num = []
            for vertex in box:
                num.append (self.quadrant (vertex))
            indices = set (num)
            for i in indices:
                node = self.getNext (i)
                if node: 
                    node.search (pointList, box)
        

class Point (SpatialData):
    def __init__ (self, data, source):
        SpatialData.__init__ (self, source)
        self.update(data)


class SpatialPoint (Point):
    def __init__ (self, xCoord, yCoord, data, source):
        self.x = xCoord
        self.y = yCoord
        Point.__init__ (self, data, source)

    @staticmethod
    def compareX (point1, point2):
        if point1.x < point2.x:
            return -1
        elif point1.x > point2.x:
            return 1
        else:
            return 0

    @staticmethod
    def compareY (point1, point2):
        if point1.y < point2.y:
            return -1
        elif point1.y > point2.y:
            return 1
        else:
            return 0


class PointList (SpatialCollection):
    def __init__ (self):
        SpatialCollection.__init__ (self)

 
class SpatialPointList (PointList):
    def __init__ (self):
        PointList.__init__ (self)

    def vector (self):
        spatialListX = []
        spatialListY = []
        for p in self:
            spatialListX.append (p.x)
            spatialListY.append (p.y)
        v = Vector (spatialListX, spatialListY)
        return v

    def sortX (self):
        self.sort (SpatialPoint.compareX)

    def sortY (self):
        self.sort (SpatialPoint.compareY)

    def distances (self, pointList):
        dList = []
        for p1 in self:
            list = []
            for p2 in pointList:
                dist = self.d (p1, p2)
                list.append (dist)
            dList.append (list)
        return dList


    def distanceMode (self, mode):
        if mode == enum.EUCLIDEAN:
            self.d = SpatialPointList.euclidean
        elif mode == enum.TAXICAB:
            self.d = SpatialPointList.taxicab

    @staticmethod
    def euclidean (p1, p2):
        x = p1.x - p2.x
        x = pow (x, 2)
        y = p1.y - p2.y
        y = pow (y, 2)
        dist = sqrt (x + y)
        return dist

    @staticmethod
    def taxicab (p1, p2):
        x = abs (p1.x - p2.x)
        y = abs (p1.y - p2.y)
        return x + y


class GeneralizedPointList (object):
    def __init__ (self, type, *args):
        self.type = type
        if type == enum.ABSTRACT:
            self._points = AbstractPointList (*args)
        elif type == enum.SPATIAL:
            self._points = SpatialPointList (*args)

    def __getattr__ (self, attr, *args):
        return self._points.__getattribute__ (attr, *args)

    def transform (self, type):
        if self.type == enum.ABSTRACT:
            if type == enum.SPATIAL:
                self._abstractToSpatial ()
        elif self.type == enum.SPATIAL:
            if type == enum.ABSTRACT:
                self._spatialToAbstract ()
        self.type = type

    def _spatialToAbstract (self):
        raise NotImplementedError ()

    def _abstractToSpatial (self):
        sPointList = SpatialPointList ()
        for entry in self._points.spatialQuery:
            data = []
            for key, gen in self._points.keyList:
                data.append ((gen, float(entry[key])))
            m = match ('POINT\(([^ \)]+) ([^ \)]+)', entry['the_geom'])
            x = float(m.group(1))
            y = float(m.group(2))
            sPointList.append (SpatialPoint (x, y, data, self.source))
        self._points = sPointList

    def __getitem__ (self, key):
        return self._points[key]

    def __setitem__ (self, key, value):
        self._points[key] = value

    def __iter__ (self):
        return iter (self._points)

    def __len__ (self):
        return len (self._points)


class AbstractPointList (PointList):
    def __init__(self, abstractQuery, spatialQuery, keyList, source):
        self.abstractQuery = abstractQuery
        self.spatialQuery = spatialQuery
        self.keyList = keyList
        self.source = source

    def vector (self):
        raise NotImplementedError ()
        #self.convertToSpatialPoints ()
        #return self.vector ()

    #def _spatialVector (self):
    #    return SpatialPointList.vector (self)

    """def convertToSpatialPoints (self):
        SpatialPointList.__init__ (self)
        for entry in self.spatialQuery:
            data = {}
            for key, gen in self.keyList:
                data.update ({gen:float(entry[key])})
            m = match ('POINT\(([^ \)]+) ([^ \)]+)', entry['the_geom'])
            x = float(m.group(1))
            y = float(m.group(2))
            self.append (SpatialPoint (x, y, data, self.source))
        self.vector = self._spatialVector"""

    def set (self, source, id):
        self.abstractQuery.setVariable ('geomSource', source)
        self.abstractQuery.setVariable ('id', id)

    def __iter__ (self):
        return AbstractPointListIterator (self.abstractQuery, self.keyList)

    """def pullFromDB (self, id, source):
        self.abstractQuery.setVariable ('id', id)
        self.abstractQuery.setVariable ('geomSource', source)
        pointList = PointList ()
        for entry in self.abstractQuery:
            data = []
            for key, gen in self.keyList:
                data.append((gen,float(entry[key])))
            point = Point (data, self.source)
            pointList.append (point)
        return pointList"""


class AbstractPointListIterator:
    def __init__ (self, query, keys):
        self.it = iter (query)
        self.keys = keys

    def next (self):
        entry = self.it.next ()
        data = []
        for key, gen in self.keys:
            data.append((gen,float(entry[key])))
        point = Point (data, self.source)
        return point

    def __iter__ (self):
        return self

