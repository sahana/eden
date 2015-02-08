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


from utils import keygen

R = keygen ('R')
DB = keygen ('DB')
SHP = keygen ('SHP')

PASS = keygen ('PASS')

MEAN = keygen ('MEAN')
SUM = keygen ('SUM')
COUNT = keygen ('COUNT')
MAX = keygen ('MAX')
MIN = keygen ('MIN')
SD = keygen ('SD')

BAR = keygen ('BAR')
BOX = keygen ('BOX')
SCATTER = keygen ('SCATTER')

EUCLIDEAN = keygen ('EUCLIDEAN')
TAXICAB = keygen ('TAXICAB')

DICT = keygen ('DICT')

SPATIAL = keygen ('SPATIAL')
ABSTRACT = keygen ('ABSTRACT')

POLYGON = keygen ('POLYGON')
POINT = keygen ('POINT')

SOURCE = keygen ('SOURCE')

EXTERN = keygen ('EXTERN')
INTERN = keygen ('INTERN')

NONZERO = keygen ('NONZERO')
