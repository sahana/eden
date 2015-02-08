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

from utils import R, Vector, BoundingBox
from ..utils.dictionary import Dictionary
from point import SpatialPointList, PointList, Point, QuadTree
from query import Query
from base import SpatialData
from instruction import Instruction

from math import sqrt, pow
from re import findall
from random import shuffle


class PolygonDictionary (Dictionary):
    def __init__ (self):
        Dictionary.__init__ (self)

    def push (self, points):
        shuffle (points)
        tree = QuadTree ()
        for p in points:
            tree.append (p)
        for pname, poly in self:
            poly.pushPoints (tree)

    def compute (self, instruction):
        try:
            for i in instruction:
                for pName, poly in self:
                    poly.compute (i)
        except TypeError:
            for pName, poly in self:
                poly.compute (instruction)

    def synchMap (self, polyMap):
        for pname, poly in self:
            poly.synchMap (polyMap)

    def union (self, *args):
        raise NotImplementedError ()


class GeneralizedPolygon:
    def __init__ (self, type, *args):
        self.type = type
        if type == enum.ABSTRACT:
            self._polygon = AbstractPolygon (*args)
        elif type == enum.SPATIAL:
            self._polygon = SpatialPolygon (*args)

    def __getattr__ (self, attr, *args):
        return self._polygon.__getattribute__ (attr, *args)

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
        p = self._polygon
        coords = self.coordinatesFromText (p.geometry ())
        poly = SpatialPolygon (coords, p, p.source, p.geometry ())
        self._polygon = poly

    @staticmethod
    def coordinatesFromText (text):
        stringPolys = findall ('\(([^\(\)]+)\)', text)
        polygonCoords = []
        for s in stringPolys:
            stringCoords = s.split (',')
            polygon = []
            for c in stringCoords:
                pair = c.split (' ')
                polygon.append (pair)
            polygonCoords.append (polygon)
        return polygonCoords


class Polygon (SpatialData):
    def __init__ (self, data, source):
        SpatialData.__init__ (self, source)
        self.points = PointList ()
        self.update (data)

    def pushPoints (self, pointList):
        raise NotImplementedError ()

    def compute (self, instruction):
        if instruction.mode is enum.EXTERN:
            value = self.points.compute (instruction)
            if value != None:
                self.update ([(instruction.dst, value)])
        else:
            try:
                SpatialData.compute (self, instruction)
            except:
                self.points.compute (instruction)

    """"def __getitem__ (self, key):
        if self.has_key (key):
            return SpatialData.__getitem__ (self, key)
        else:
            valueList = []
            for p in self.points:
                if p.has_key (key):
                    valueList.append (p[key])
            if len(valueList) == 0:
                raise KeyError ()
            else:
                return valueList"""


class SpatialPolygon (Polygon):
    pointInPolygon = False
    def __init__ (self, shp, data, source, geom=None):
        Polygon.__init__ (self, data, source)
        self.simplePolys = []
        self._geom = geom
        maxXList = []
        maxYList = []
        minXList = []
        minYList = []
        for s in shp:
            simple = SimpleSpatialPolygon (s)
            self.simplePolys.append (simple) 
            maxXList.append (simple.max[0])
            maxYList.append (simple.max[1])
            minXList.append (simple.min[0])
            minYList.append (simple.min[1])
        maxX = max (maxXList)
        maxY = max (maxYList)
        minX = min (minXList)
        minY = min (minYList)
        self.bounds = BoundingBox ((maxX, maxY), (minX, minY))
        if not SpatialPolygon.pointInPolygon:
            R.importLibrary ('sp')
            SpatialPolygon.pointInPolygon = True

    def pushPoints (self, pointTree):
        for s in self.simplePolys:
            pList = pointTree.search (s.bounds)
            v = pList.vector ()
            c = s.coordinates
            locations = R.function ('point.in.polygon', v.x, v.y, c.x, c.y)
            for i, val in enumerate(locations):
                if val != 0:
                    self.points.append (pList[i])

    def geometry (self):
        if self._geom:
            return self._geom
        else:
            raise NotImplementedError ()

    def synchMap (self, map):
        raise NotImplementedError ()


class SimpleSpatialPolygon:
    def __init__ (self, shp):
        xCoords = []
        yCoords = []
        for point in shp:
            xCoords.append (float(point[0]))
            yCoords.append (float(point[1]))
        self.coordinates = Vector (xCoords, yCoords)
        maxX = max (xCoords)
        minX = min (xCoords)
        maxY = max (yCoords)
        minY = min (yCoords)
        self.max = (maxX, maxY)
        self.min = (minX, minY)
        self.bounds = BoundingBox (self.max, self.min)


class AbstractPolygon (Polygon):
    def __init__ (self, id, geom, data, source):
        self._geom = geom
        self.id = id
        Polygon.__init__ (self, data, source)

    def pushPoints (self, abstractPoints):
        abstractPoints.set (self.source.name, self.id)
        for p in abstractPoints:
            self.points.append (p)
        #points = abstractPoints.pullFromDB (self.id, self.source.name)
        #for p in points:
        #    self.points.append (p)

    def synchMap (self, polygonMap):
        data = polygonMap.loadMatchingPolygonData (self.source.name, self.id)
        self.update (data)

    def geometry (self):
        return self._geom
