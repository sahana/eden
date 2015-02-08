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




import shapelib
import dbflib

import enum
from query import Query
from utils import keygen
from ..utils.dictionary import Dictionary
from polygon import GeneralizedPolygon, SpatialPolygon, PolygonDictionary
from point import GeneralizedPointList, SpatialPointList, SpatialPoint


class BaseMap (object):
    def __init__ (self, mapSource):
        self._fields = Dictionary ()
        self.name = mapSource

    def load (outputMode):
        pass

    def addField (self, fieldName):
        key = keygen (fieldName)
        self._fields.update ({fieldName:key})
        return key

    def __getitem__ (self, item):
        try:
            return self._fields[item]
        except KeyError:
            return self.addField (item)


class PolygonMap (BaseMap):
    def __init__ (self, mapSource, subset):
        BaseMap.__init__ (self, mapSource)
        self._subset = subset

    def addSortField (self, fieldName):
        self._primary = fieldName

    #def __getitem__ (self, item):
    #    if not self._primaryKeys.has_key(item): 
    #        self._primaryKeys.update ([(item, keygen(item))])
    #    else:
    #        return self._primaryKeys[item]


class PointMap (BaseMap):
    def __init__ (self, mapSource):
        BaseMap.__init__ (self, mapSource) 


class DatabasePointMap (PointMap):
    def __init__ (self, mapSource, connection):
        PointMap.__init__ (self, mapSource)
        self._connection = connection

    def load (self):
        query = Query (self._connection)
        query.SELECT ('gid', self.name)
        for key, value in self._fields:
            query.SELECT (key, self.name)
        query.FROM ('%(geomSource)s')
        query.where = '%(geomSource)s.gid=%(id)s AND '
        query.where += 'ST_Contains(%(geomSource)s.the_geom, '
        query.where += self.name + '.the_geom)'

        spatialQuery = Query (self._connection)
        spatialQuery.SELECT ('the_geom', self.name, 'AsText')
        for key, value in self._fields:
            spatialQuery.SELECT (key, self.name)
        
        pointList = GeneralizedPointList (enum.ABSTRACT, query, spatialQuery, self._fields, self)
        return pointList
        

class DatabasePolygonMap (PolygonMap): 
    def __init__ (self, mapSource, connection, subset):
        PolygonMap.__init__ (self, mapSource, subset)
        self._connection = connection
        self._matchQuery = None

    def load (self):
        query = Query (self._connection)
        query.SELECT ('gid', self.name)
        query.SELECT ('the_geom', self.name, 'AsText')
        query.SELECT (self._primary, self.name)
        for key, gen in self._fields:
            query.SELECT (key, self.name)
        whereList = []
        try:
            for entry in self._subset:
                item = self.name + '.' + self._primary + '=\'' + entry + '\''
                whereList.append (item)
                query.where = ' OR '.join (whereList)
        except TypeError:
                pass
        polyDict = PolygonDictionary ()
        pairs = []
        for entry in query:
            d = []
            for key, gen in self._fields:
                d.append ((gen,entry[key]))
            data = Dictionary ()
            data.update (d)
            p = GeneralizedPolygon (enum.ABSTRACT, entry['gid'], 
                                    entry['the_geom'], data, self)
            polyKey = keygen (entry[self._primary])
            pairs.append ((polyKey, p))
        polyDict.update(pairs)
        return polyDict

    def loadMatchingPolygonData (self, mapName, fieldID):
        if not self._matchQuery:
            self._matchQuery = Query (self._connection)
            self._matchQuery.FROM ('%(mapName)s')
            for key, gen in self._fields:
                self._matchQuery.SELECT (key, self.name)
            self._matchQuery.where='%(mapName)s.gid=%(fieldID)s AND ST_Equals'
            self._matchQuery.where += '(%(mapName)s.the_geom,' + self.name
            self._matchQuery.where += '.the_geom);'
            self._matchQuery.SELECT 
        self._matchQuery.setVariable ('mapName', mapName)
        self._matchQuery.setVariable ('fieldID', fieldID)
        data = []
        for entry in self._matchQuery:
            for key, gen in self._fields:
                data.append ((gen,entry[key]))
        return data
        

class ShapePointMap (PointMap):
    def __init__ (self, mapSource):
        PointMap.__init__ (self, mapSource)

    def load (self):
        shapes = shapelib.open(self.name)
        if len(self._fields) != 0:
            data = dbflib.open (self.name)
        list = SpatialPointList ()
        for i in range (shapes.info ()[0]):
            records = Dictionary ()
            for key, gen in self._fields:
                records.update ([(gen,float(data.read_record (i)[key]))])
            x = float (shapes.read_object (i).vertices ()[0][0])
            y = float (shapes.read_object (i).vertices ()[0][1])
            list.append (SpatialPoint (x, y, records, self))
        return list


class ShapePolygonMap (PolygonMap):
    def __init__ (self, mapSource, subset):
        PolygonMap.__init__ (self, mapSource, subset)

    def load (self):
        shapes = shapelib.open (self.name)
        data = dbflib.open (self.name)
        polys = PolygonDictionary ()
        for i in range (shapes.info ()[0]):
            shp = shapes.read_object (i)
            d = data.read_record (i)[self._primary]
            if self._subset != None:
                for item in self._subset:
                    if item == d:
                        p = SpatialPolygon (shp.vertices (), [], self)
                        polys.update({d:p})
            else:
                p = SpatialPolygon (shp.vertices (), [], self)
                polys.update({d:p})
        return polys
