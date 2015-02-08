
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

from point import SpatialPointList, SpatialPoint
from polygon import SpatialPolygon
from utils import R

def pointsFromSHP (pointsFilename, datafield=[]):
    shapes = shapelib.open(pointsFilename)
    if len(datafield) != 0:
        data = dbflib.open (pointsFilename)
    list = SpatialPointList ()
    for i in range (shapes.info ()[0]):
        records = {}
        pair = []
        for entry in datafield:
            pair.append ((entry, data.read_record (i)[entry]))
        records.update (pair)
        x = shapes.read_object (i).vertices ()[0][0]
        y = shapes.read_object (i).vertices ()[0][1]
        list.append (SpatialPoint (x, y, records))
    return list

def polysFromSHP (polysFilename, datafield, polySubset):
    R.importLibrary ('sp')
    shapes = shapelib.open(polysFilename)
    data = dbflib.open (polysFilename)
    polyList = []
    for i in range (shapes.info ()[0]):
        shp = shapes.read_object (i)
        d = data.read_record (i)[datafield]
        if len(polySubset) != 0:
            for item in polySubset:
                if item == d:
                    p = SpatialPolygon (i, shp.vertices (), d)
                    polyList.append(p)
        else:
            p = SpatialPolygon (i, shp.vertices (), d)
            polyList.append(p)
    return polyList
