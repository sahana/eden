# -*- coding: utf-8 -*-

"""
    S3 Charting Toolkit

    @copyright: 2011-12 (c) Sahana Software Foundation
    @license: MIT

    @requires: U{B{I{NumPy}} <http://www.numpy.org>}
    @requires: U{B{I{MatPlotLib}} <http://matplotlib.sourceforge.net>}

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

__all__ = ["S3Chart"]

try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO

from gluon import current
from gluon.storage import Storage
from gluon.html import IMG

# =============================================================================
class S3Chart(object):
    """
        Module for graphing

        Currently a simple wrapper to matplotlib
    """

    # This folder needs to be writable by the web2py process
    CACHE_PATH = "/%s/static/cache/chart"  %  current.request.application

    # -------------------------------------------------------------------------
    def __init__(self, path, width=9, height=6):
        """
            Create the base Figure object
            
            @param: height x100px
            @param: width x100px
        """
        try:
            # Causes deadlocking issues
            # http://sjohannes.wordpress.com/2010/06/11/using-matplotlib-in-a-web-application/
            #import matplotlib
            #matplotlib.use("Agg")
            #import matplotlib.pyplot as plt
            #from pylab import savefig
            from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
            self.FigureCanvas = FigureCanvas
            from matplotlib.figure import Figure
            self.Figure = Figure
            MATPLOTLIB = True
        except ImportError:
            import sys
            print >> sys.stderr, "WARNING: S3Chart unresolved dependency: matplotlib required for charting"
            MATPLOTLIB = False

        self.filename = path
        self.width = width
        self.height = height
        self.asInt = False
        if MATPLOTLIB:
            self.fig = Figure(figsize=(width, height))
        else:
            self.fig = None

    # -------------------------------------------------------------------------
    @staticmethod
    def getCachedPath(filename):
        import os
        path = "applications"
        chartFile = "%s/%s.png" % (S3Chart.CACHE_PATH, filename)
        fullPath = "%s%s" % (path, chartFile)
        if os.path.exists(fullPath):
            return chartFile
        else:
            return None

    # -------------------------------------------------------------------------
    @staticmethod
    def getCachedFile(filename):
        """
            Return the opened cached file, if the file can't be found then
            return None
        """
        chartFile = S3Chart.getCachedPath(filename)
        if chartFile:
            try:
                f = open(chartFile)
                return f.read()
            except:
                # for some reason been unable to get the cached version
                pass
        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def storeCachedFile(filename, image):
        """
            Save the file in the cache area, and return the path to this file
        """

        path = "applications"
        chartFile = "%s/%s.png" % (S3Chart.CACHE_PATH, filename)
        fullPath = "%s%s" % (path, chartFile)
        try:
            f = open(fullPath, "w+")
            print >> f, image
        except:
            return None
        return chartFile

    # -------------------------------------------------------------------------
    @staticmethod
    def purgeCache(prefix=None):
        """
            Delete the files in the cache that match the file name prefix,
            if the prefix is None then all files will be deleted
        """

        import os
        folder = "applications%s/" % S3Chart.CACHE_PATH
        if os.path.exists(folder):
            filelist = os.listdir(folder)
            for file in filelist:
                if prefix == None or file.startswith(prefix):
                    os.remove("%s%s" % (folder, file))

    # -------------------------------------------------------------------------
    def draw(self, output="xml"):
        """
            Output the chart as a PNG embedded in an IMG tag
                - used by the Delphi module
        """

        fig = self.fig
        if not fig:
            return "Matplotlib not installed"

        # For interactive shell tests
        #plt.show()
        # For web response
        #savefig(response.body)
        chart = Storage()
        chart.body = StringIO()
        chart.headers = Storage()
        chart.headers["Content-Type"] = "image/png"

        canvas = self.FigureCanvas(fig)
        canvas.print_figure(chart.body)
        #return response.body.getvalue()
        image = chart.body.getvalue()
        # IE 8 and before has a 32K limit on URIs this can be quickly 
        # gobbled up if the image is too large. So the image will
        # stored on the server and a URI used in the src
        cachePath = self.storeCachedFile(self.filename, image)
        if output == "xml":
            if cachePath != None:
                image = IMG(_src = cachePath)
            else:
                import base64
                base64Img = base64.b64encode(image)
                image = IMG(_src="data:image/png;base64,%s" % base64Img)
        else:
            current.response.headers["Content-Type"] = "image/png"
        return image

    # -------------------------------------------------------------------------
    def survey_hist(self, title,
                    data, bins, min, max, xlabel=None, ylabel=None):
        """
            Draw a Histogram
                - used by the Survey module
        """

        fig = self.fig
        if not fig:
            return "Matplotlib not installed"

        from numpy import arange

        # Draw a histogram
        ax = fig.add_subplot(111)
        ax.hist(data, bins=bins, range=(min, max))
        left = arange(0, bins + 1)
        if self.asInt:
            label = left * int(max / bins)
        else:
            label = left * max / bins
        ax.set_xticks(label)
        ax.set_xticklabels(label, rotation=30)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

    # -------------------------------------------------------------------------
    def survey_pie(self, title, data, label):
        """
            Draw a Pie Chart
                - used by the Survey module
        """

        fig = self.fig
        if not fig:
            return "Matplotlib not installed"

        # Draw a pie chart
        ax = fig.add_subplot(111)
        ax.pie(data, labels=label)
        ax.legend()
        ax.set_title(title)

    # -------------------------------------------------------------------------
    def survey_bar(self, title, data, labels, legendLabels):
        """
            Draw a Bar Chart
                - used by the Survey module
        """

        barColourList = ["#F2D7A0", "#7B77A8", "#69889A", "#9D7B34"]
        barColourListExt = [(242, 215, 160),
                            (123, 118, 168),
                            (105, 136, 154),
                            (157, 123, 52)
                           ]
        fig = self.fig
        if not fig:
            return "Matplotlib not installed"

        from numpy import arange

        # Draw a bar chart
        if not isinstance(data[0],list):
            dataList = [data]
        else:
            dataList = data
        legendColCnt = 3
        cnt = len(labels)
        dcnt = len(dataList)
        lcnt = 0
        if legendLabels != None:
            lcnt = (len(legendLabels) + legendColCnt - 1) / legendColCnt
        width = 0.9 / dcnt
        offset = 0
        gap = 0.1 / dcnt
        bcnt = 0
        bars = []
        height = max(0.2, 0.85 - (0.04 * lcnt))
        rect = [0.08, 0.08, 0.9, height]
        ax = fig.add_axes(rect)
        for data in dataList:
            left = arange(offset, cnt + offset)    # the x locations for the bars
            if bcnt < 3:
                colour = barColourList[bcnt]
            else:
                colour = []
                colourpart = barColourListExt[bcnt%4]
                divisor = 256.0 - (32 * bcnt/4)
                if divisor < 0.0:
                    divisor = divisor * -1
                for part in colourpart:
                    calc = part/divisor
                    while calc > 1.0:
                        calc -= 1
                    colour.append(calc)
            plot = ax.bar(left, data, width=width, color=colour)
            bars.append(plot[0])
            bcnt += 1
            offset += width + gap
        left = arange(cnt)
        lblAdjust = (1.0 - gap) * 0.5
        if cnt <= 3:
            angle = 0
        elif cnt <= 10:
            angle = -10
        elif cnt <= 20:
            angle = -30
        else:
            angle = -45
        ax.set_xticks(left + lblAdjust)
        try: # This function is only available with version 1.1 of matplotlib
            ax.set_xticklabels(labels, rotation=angle)
            ax.tick_params(labelsize=self.width)
        except AttributeError:
            newlabels = []
            for label in labels:
                if len(label) > 12:
                    label = label[0:10] + "..."
                newlabels.append(label)
            ax.set_xticklabels(newlabels)
        ax.set_title(title)
        if legendLabels != None:
            fig.legend(bars,
                       legendLabels,
                       "upper left",
                       mode="expand",
                       ncol = legendColCnt,
                       prop={"size":10},
                      )

# END =========================================================================
