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



from uuid import uuid4

from query import SQLTable

from re import sub

def toMap (connection, polygons):
    name = '_map__' + str(uuid4 ().int)
    keys = set ([])
    types= {}
    for pname, poly in polygons:
        keys.update (poly.keys ())
    for key in keys:
        for pname, poly in polygons:
            try:
                t = type (poly[key])
                if types.has_key (key):
                    if types[key] != t :
                        raise RuntimeError ()
                else:
                    types[key] = t
            except KeyError:
                pass
    table = SQLTable (connection, name, 'gid')
    table.addGeometryColumn ('the_geom', '4326', 'MULTIPOLYGON', '2')
    table.addColumn ('Polygon', 'varchar')
    for key in keys:
        val = noSpace (str(key))
        if types[key] == type('str'):
            table.addColumn (val, 'varchar')
        else:
            table.addColumn (val, 'numeric')
    for pname, poly in polygons:
        insertMap = {}
        geom = "GeomFromText ('" + poly.geometry () + "', 4326)"
        pname = str(pname)
        insertMap.update ({'Polygon': pname})
        insertMap.update ({'the_geom': geom})
        for key, value in poly:
            insertMap.update ({noSpace(str(key)):value})
        table.insert (**insertMap)
    table.save ()

    #cursor = connection2.cursor ()
    #cursor.execute ('INSERT INTO usertables (name) VALUES (\'' + tableName + '\')')
    #cursor.execute ('COMMIT')

    return name

def noSpace (string):
    s = sub ('\s',r'_', string)
    return s

"""from query import Query
from point import SpatialPointList, AbstractPointList, SpatialPoint
from polygon import SpatialPolygon, AbstractPolygon
from utils import R

from re import findall, match

def spatialPointsFromDB (connection, pointTable,  datafields):
    R.importLibrary ('sp')
    query = Query (connection)
    query.SELECT ('the_geom', pointTable, 'AsEWKT')
    for data in datafields:
        query.SELECT (data, pointTable)
    pList = SpatialPointList ()
    for entry in query:
        data = {}
        pairs = []
        for field in datafields:
            pairs.append((field, entry[field]))
            data.update (pairs)
        m = match ('POINT\(([^ \)]+) ([^ \)]+)', entry['the_geom'])
        x = float(m.group(1))
        y = float(m.group(2))
        pList.append (SpatialPoint (x, y, data))
    return pList

def pointsFromDB (connection, geomTable, pointTable, datafields):
    query = Query (connection)
    query.SELECT ('gid', pointTable)
    query.FROM (geomTable)
    for d in datafields:
        query.SELECT (d, pointTable)
    query.where = geomTable + '.gid=%(id)s AND '
    query.where += 'ST_Contains(' + geomTable + '.the_geom, '
    query.where += pointTable + '.the_geom)'

    pointList = AbstractPointList (query)
    return pointList

def polysFromDB (connection, table, datafield, subset):
    query = Query (connection)
    query.SELECT ('gid', table)
    query.SELECT ('the_geom', table, 'AsEWKT')
    query.SELECT (datafield, table)
    whereList = []
    for entry in subset:
        item = table + '.' + datafield + '=\'' + entry + '\''
        whereList.append (item)
    if len (whereList) >= 1:
        query.where = ' OR '.join (whereList)
    polyList = []
    for entry in query:
        p = AbstractPolygon (entry['gid'], entry['the_geom'], entry[datafield])
        polyList.append (p)
    return polyList

def spatialPolysFromDB (connection, table, datafield, subset):
    query = Query (connection)
    query.SELECT ('gid', table)
    query.SELECT ('the_geom', table, 'AsEWKT')
    query.SELECT (datafield, table)
    whereList = []
    for entry in subset:
        item = table + '.' + datafield + '=\'' + entry + '\''
        whereList.append (item)
    if len (whereList) >= 1:
        query.where = ' OR '.join (whereList)
    polyList = []
    for entry in query:
        p = polyFromText (entry['gid'], entry['the_geom'], entry[datafield])
        polyList.append (p)
    return polyList

def polyFromText (id, text, data):
    stringPolys = findall ('\(([^\(\)]+)\)', text)
    polygonCoords = []
    for s in stringPolys:
        stringCoords = s.split (',')
        polygon = []
        for c in stringCoords:
            pair = c.split (' ')
            polygon.append (pair)
        polygonCoords.append (polygon)
    p = SpatialPolygon (id, polygonCoords, data)
    return p"""
