"""                                                                                                                            
    Healthscapes Literature Module                                                                                                   
                                                                                                                               
    @author: Colin Burreson <kasapo@gmail.com>                                                                         
    @author: Nico Preston <nicopresto@gmail.com>                                                                                 
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

######################################################
# Desc:
#       Queries Geoserver for layer ids matching 
#       given keyword
#
######################################################

import urllib as u
import libxml2 as l

def mapSearch(keyword=''):
   #file = open("/dmz/xkw.txt","w")
   #file.write("\nKeywordType: " + str(type(keyword)))
   #file.write("\nValue: " + str(keyword))
    f = u.urlopen("http://dev.healthscapes.org/geoserver/wms?request=GetCapabilities&version=1.1.0&namespace=hsd")
    d = l.parseDoc(f.read())
    ct = d.xpathNewContext()
   #file.write("\nXPath:  //Layer[KeywordList/Keyword='"+ str(keyword) +"']/Name/text()")
   #file.close()
    x = ct.xpathEval("//Layer[KeywordList/Keyword='"+ str(keyword) +"']/Name/text()")
    #x = ct.xpathEval("//Layer[KeywordList/Keyword='%s']/Name/text()") % ( str(keyword) )

    layer_list = []
    for node in x:
        layer_list.append(node.content)

   #if(len(layer_list) == 0):
   #    return "No Results for [" + keyword + "]"
   #else:
    return layer_list

def searchInfo(keyword):
    #import urllib2 as u
    #import libxml2 as l
    f = u.urlopen("http://dev.healthscapes.org/geoserver/wms?request=GetCapabilities&version=1.1.0&namespace=hsd")
    d = l.parseDoc(f.read())
    ct = d.xpathNewContext()
    nodes = ct.xpathEval("//Layer[KeywordList/Keyword='"+keyword+"']")

    title = []
    desc = []
    layer = []
    for node in nodes:
        lyr = l.parseDoc(node.serialize())
        title.append(lyr.xpathEval("/Layer/Title")[0].content)
        desc.append(lyr.xpathEval("/Layer/Abstract")[0].content)
        layer.append(lyr.xpathEval("/Layer/Name")[0].content)

# if len(title) == 0:
#     title = "'null'"
# 
# if len(desc) == 0:
#     desc = "'null'"
# 
# if len(layer) == 0:
#     layer = "'null'"
# 
    return {'layers': layer, 'desc': desc, 'name': title}
