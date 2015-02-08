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
from map import DatabasePolygonMap, ShapePolygonMap
from map import DatabasePointMap, ShapePointMap
from utils import keygen

from math import sqrt


def Map (mapType, loadMethod, mapSource, connection=None, subset=None):
    if mapType == enum.POLYGON:
        return polygonMap (loadMethod, mapSource, connection, subset)
    elif mapType == enum.POINT:
        return pointMap (loadMethod, mapSource, connection)


def polygonMap (loadMethod, mapSource, connection=None, subset=None):
    if loadMethod == enum.DB:
        return DatabasePolygonMap (mapSource, connection, subset)
    elif loadMethod == enum.SHP:
        return ShapePolygonMap (mapSource, subset)


def pointMap (loadMethod, mapSource, connection=None):
    if loadMethod == enum.DB:
        return DatabasePointMap (mapSource, connection)
    elif loadMethod == enum.SHP:
        return ShapePointMap (mapSource)


def getFunction (enumeratedType, *args):
    if enumeratedType is enum.MEAN:
        return MEAN
    elif enumeratedType is enum.SUM:
        return SUM
    elif enumeratedType is enum.COUNT:
        return countFunction (args[0])
    elif enumeratedType is enum.NONZERO:
        return NONZERO
    elif enumeratedType is enum.MAX:
        return max
    elif enumeratedType is enum.MIN:
        return min
    elif enumeratedType is enum.SD:
        return SD


def MEAN (*args):
    if len (args) == 0:
        raise RuntimeError ("Need at least one element to calculate mean")
    value = 0
    for a in args:
        value += a
    value /= len (args)
    return value

def NONZERO (*args):
    if args[0] == 0:
        return None
    else:
        return args[0]

def SUM (*args):
    if len (args) == 0:
        raise RuntimeError ("Need at least one element to calculate sum")
    value = 0
    for a in args:
        value += a
    return value

def SD (*args):
    mean = MEAN (*args)
    sum = 0
    for s in args:
        val = s - mean
        val = val * val
        sum += val
    sum /= (len (args) - 1)
    return sqrt (sum)

def countFunction (map):
    def f (*args):
        count = 0
        for a in args:
            if a == map:
                count += 1
        return count
    return f        
