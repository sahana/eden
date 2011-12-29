# -*- coding: utf-8 -*-

"""
    S3 Charting Toolkit

    @author: Fran Boon <fran[at]aidiq[dot]com>

    @copyright: 2011 (c) Sahana Software Foundation
    @license: MIT

    @status: work in progress

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

import sys
import base64

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

    # -------------------------------------------------------------------------
    def __init__(self, width=9, height=6):
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
            print >> sys.stderr, "WARNING: S3Chart unresolved dependency: matplotlib required for charting"
            MATPLOTLIB = False

        #from numpy import array

        self.width = width
        self.height = height
        if MATPLOTLIB:
            self.fig = Figure(figsize=(width, height))
        else:
            self.fig = None

    # -------------------------------------------------------------------------
    def displayAsIntegers(self):
        """
            Configure Charts to display Integers
                - used by the Survey module
                  @ToDo: Replace with simple attribute?
        """
        self.asInt = True

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
        if output == "xml":
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
        bcnt = 1
        bars = []
        height = max(0.2, 0.85 - (0.04 * lcnt))
        rect = [0.08, 0.08, 0.9, height]
        ax = fig.add_axes(rect)
        for data in dataList:
            left = arange(offset, cnt + offset)    # the x locations for the bars
            colour = (0.2/bcnt, 0.5/bcnt, 1.0/bcnt)
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

# =============================================================================
