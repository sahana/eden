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


from ...utils.dictionary import DefaultDictionary

from savage.graph import ScatterPlot, DoubleScatterPlot, BarGraph, LineChart, PieChart

from rpy2 import rinterface as R
from rpy2.robjects import RFormula

from uuid import uuid4

from re import search

def usage (fname):
    R.initr ()
    fname = R.StrSexpVector ([fname])

    try:
        location = R.globalEnv.get ('help') (fname)[0]
    except IndexError:
        raise RuntimeError ('Function not found')

    file = open (location)
    m = search ('_\x08U_\x08s_\x08a_\x08g_\x08e:\n([^\x08]+)(?=_)', file.read ())
    
    if m is None:
        raise RuntimeError ('Usage not found')
    else:
        return m.group (1)

def cp (fileOrString, filename):
    needToClose = False
    if isinstance (fileOrString, str):
        needToClose = True
        fileOrString = open (fileOrString, 'w')
    readingFile = open (filename, 'r')
    fileOrString.write (readingFile.read ())
    if needToClose:
        fileOrString.close ()
    readingFile.close ()


def multiRScatter (response, data, groups, tmpdir = '.',  params = {}):
    R.initr ()
    svg = R.globalEnv.get ('svg')
    off = R.globalEnv.get ('graphics.off')
    pairs = R.globalEnv.get ('pairs')
    for g in groups:
        dataList = []
        for key, value in data:
            try:
                dataList.append (value[g])
            except KeyError:
                dataList.append (None)
        R.globalEnv[str(g)] = R.FloatSexpVector (dataList)
    f = '~' + '+'.join (map (str, groups))
    formula = RFormula (f)

    params = formatForR (params)

    filename = tmpdir + '/' + str(uuid4 ().int) + '.svg'
    svg (R.StrSexpVector([filename]), width=R.FloatSexpVector ([10.5]),
         height=R.FloatSexpVector ([7]))
    pairs (formula, **params)
    off ()
    cp (response, filename)


def boxPlotData (response, data, tmpdir = '.', params = {}):
    R.initr ()
    svg = R.globalEnv.get ('svg')
    off = R.globalEnv.get ('graphics.off')
    boxplot = R.globalEnv.get ('boxplot')
    vectors = []
    for dataList in data:
        vectors.append (R.FloatSexpVector (dataList))

    params = formatForR (params)

    filename = tmpdir + '/' + str(uuid4 ().int) + '.svg'
    svg (R.StrSexpVector([filename]), width=R.FloatSexpVector ([10.5]),
         height=R.FloatSexpVector ([7]))
    boxplot (*vectors, **params)
    off ()
    cp (response, filename)


def formatForR (params):
    kwargs = {}
    for key, value in params.iteritems ():
        if not isinstance (value, list):
            value = [value]

        t = commonType (value)

        if t == float:
            v = R.FloatSexpVector (value)
        elif t == int:
            v = R.IntSexpVector (value)
        elif t == bool:
            v = R.BoolSexpVector (value)
        elif t == str:
            v = R.StrSexpVector (value)
        else:
            v = None
        
        kwargs.update ([(key, v)])
    return kwargs


def commonType (elements):
    if len (elements) == 0:
        raise RuntimeError ('Empty List')
    t = type (elements[0])
    for item in elements:
        if t != type (item):
            return False
    return t


def barGraphData (responseBody, data, groups, title='Bar Graph', 
                  xBar='X Label', yBar='Y Label', 
                  colors=DefaultDictionary ('rgb(200,10,10)')):
    graph = BarGraph ()
    graph.setXLabel (xBar)
    graph.setYLabel (yBar)
    graph.setTitle (title)
    graph.setColors (colors)
    for rname, row in data:
        groupData = []
        for key in groups:
            try:
                value = row[key]
                groupData.append ((key, value))
            except KeyError:
                continue
        if len (groupData)> 0:
            graph.addGroup (rname, groupData)
    graph.finalize ()
    graph.save (responseBody)


def scatterPlotData (responseBody, data, pair, title= 'Title Text', 
                     xLabel = "X Label", yLabel = "Y Label",
                     colors=None):
    if len (pair) != 2:
        raise RuntimeError ('Two groups must be provided')
    plot = ScatterPlot ()
    #if colors:
    #    plot.setColors (colors[0], colors[1], colors[2])
    for key, value in data:
        
        try:
            name = key
            x = value[pair[0]]
            y = value[pair[1]]
            if x != None and y != None:
                plot.addPoint (name, x, y)
        except KeyError:
            continue
    plot.setTitle (title)
    plot.setXLabel (xLabel)
    plot.setYLabel (yLabel)
    plot.finalize ()
    plot.save (responseBody)


def doubleScatterPlotData (responseBody, data, pair, pair2, title= 'Title Text', 
                           xLabel = "X Label", yLabel = "Y Label", 
                           y2Label = "Y2 Label", 
                           colors=None):
    if len (pair) != 2 or len (pair2) != 2:
        raise RuntimeError ('Two groups must be provided')
    plot = DoubleScatterPlot ()
    if colors:
        plot.setColors (colors[0], colors[1])
    for key, value in data:
        try:
            x = value[pair[0]]
            y = value[pair[1]]
            if x != None and y != None:
                plot.addPoint1 (key, x, y)
        except KeyError:
            pass

        try:
            x = value[pair2[0]]
            y = value[pair2[1]]
            if x != None and y != None:
                plot.addPoint2 (key, x, y)
        except KeyError:
            pass

    plot.setTitle (title)
    plot.setXLabel (xLabel)
    plot.setYLabel (yLabel)
    plot.setY2Label (y2Label)
    plot.finalize ()
    plot.save (responseBody)



def lineChartData (responseBody, data, series, title= 'Title Text', 
                     xLabel = "X Label", yLabel = "Y Label", colors=[]):
    plot = LineChart ()
    for key, value in data:
        group = []
        for item in series:
            group.append (value[item])
        plot.addSeries (key, group)
    plot.addColors (colors)
    plot.setSeriesTitles (series)
    plot.setTitle (title)
    plot.setXLabel (xLabel)
    plot.setYLabel (yLabel)
    plot.save (responseBody)


def pieChartData (responseBody, data, group, title= 'Title Text'):
    rawValueList = []
    total = 0
    g = PieChart ()
    for key, value in data:
        try:
            v = value[group]
            if v is None:
                continue
            g.addWedge (key, v)
        except KeyError:
            continue
    #g.setTitle (title)
    g.save (responseBody)
