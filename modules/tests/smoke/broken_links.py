""" Sahana Eden Test Framework

    @copyright: 2011-2014 (c) Sahana Software Foundation
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

from time import time
from types import MethodType
try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO
import sys
import socket

from tests.web2unittest import Web2UnitTest
from gluon import current

class BrokenLinkTest(Web2UnitTest):
    """ Smoke Test, visit every link it can find and report on the outcome """
    def __init__(self):
        Web2UnitTest.__init__(self)
        self.clearRecord()
        # This string must exist in the URL for it to be followed
        # Useful to avoid going to linked sites
        self.homeURL = self.url
        # Link used to identify a URL to a ticket
        self.url_ticket = "/admin/default/ticket/"
        # Tuple of strings that if in the URL will be ignored
        # Useful to avoid dynamic URLs that trigger the same functionality
        self.include_ignore = ("_language=",
                               "logout",
                               "appadmin",
                               "admin",
                               "delete",
                              )
        # tuple of strings that should be removed from the URL before storing
        # Typically this will be some variables passed in via the URL
        self.strip_url = ("?_next=",
                          )
        self.reportOnly = False
        self.maxDepth = 16 # sanity check
        self.setThreshold(10)
        self.setUser("test@example.com/eden")
        self.total_visited = 0
        self.broken_links_count = 0

    def clearRecord(self):
        # the total url links visited
        self.totalLinks = 0
        # The number of unique urls found at depth i, where i is the index
        self.linkDepth = []
        # Dictionary of the parent for each URL
        self.urlParentList = {}
        # dictionary of ReportData objects indexed on the url
        self.results = {}

    def setAgent(self, agentAcronym):
       # Decide on the agent that will be used to power the smoke test
        if agentAcronym == "g":
            self.agent = "Ghost"
            try:
                from ghost import Ghost
                self.ghost = Ghost(wait_timeout = 360)
            except ImportError:
                raise NameError("Ghost not installed")

            from using_ghost import login, visit

        else:
            self.agent = "Twill"
            try:
                from twill import get_browser
                from twill import set_output
            except ImportError:
                raise NameError("Twill not installed")

            try:
                import mechanize
            except ImportError:
                raise NameError("Mechanize not installed")

            self.b = get_browser()
            self.b_data = StringIO()
            set_output(self.b_data)

            from using_twill import login, visit

        self.visit = MethodType(visit, self)
        self.login = MethodType(login, self)

    def setReportOnly(self, action):
        self.reportOnly = action

    def setDepth(self, depth):
        self.maxDepth = depth

    def setUser(self, user):
        self.credentials = user.split(",")

    def setThreshold(self, value):
        value = float(value)
        self.threshold = value
#        socket.setdefaulttimeout(value*2)

    def addResults2Current(self):
        '''
        Store the count links in gluon.current to be used by HTMLTestRunner for better reporting
        '''
        smoke_results = {}
        smoke_results['working_links'] = self.total_visited - self.broken_links_count
        smoke_results['broken_links_count'] = self.broken_links_count
        current.data['smoke_results'] = smoke_results

    def runTest(self):
        """
            Test to find all exposed links and check the http code returned.

            This test doesn't run any javascript so some false positives
            will be found.

            The test can also display an histogram depicting the number of
            links found at each depth.

            Failure or Success to be shown in the report is checked in addSuccess in TestResult
            class
        """
        self.reporter("Running the smoke tests using %s" % self.agent)

        for user in self.credentials:
            self.clearRecord()
            if self.login(user):
                self.reporter("Smoke Test for user %s" % self.user)
                self.visitLinks()
                self.report()
                self.addResults2Current()
            else:
                raise Exception("Login Failed")

    def visitLinks(self):
        url = self.homeURL + "/default/index"
        to_visit = [url]
        start = time()
        self.total_visited = 0
        if not self.reportOnly:
            for depth in range(self.maxDepth):
                if len(to_visit) == 0:
                    break
                self.linkDepth.append(len(to_visit))
                self.totalLinks += len(to_visit)
                visit_start = time()
                url_visited = "%d urls" % len(to_visit)
                self.total_visited += len(to_visit)
                to_visit = self.visit(to_visit, depth)
                msg = "%.2d Visited %s in %.3f seconds, %d more urls found" % (depth, url_visited, time()-visit_start, len(to_visit))
                self.reporter(msg)
                if self.config.verbose >= 2:
                    if self.config.verbose >= 3:
                        print >> self.stdout
                    if self.stdout.isatty(): # terminal should support colour
                        msg = "%.2d Visited \033[1;32m%s\033[0m in %.3f seconds, \033[1;31m%d\033[0m more urls found" % (depth, url_visited, time()-visit_start, len(to_visit))
                    print >> self.stdout, msg
            if len(to_visit) > 0:
                self.linkDepth.append(len(to_visit))
            finish = time()
            self.reporter("Finished took %.3f seconds" % (finish - start))

    def report(self):
        self.reporter("%d URLs visited" % self.totalLinks)
        self.brokenReport()
        self.timeReport()
        if self.config.record_timings:
            if not self.reportOnly:
                self.record_timings()
            self.scatterplot()
        self.depthReport()

    def record_timings(self):
        import_error = ""
        try:
            import xlrd
        except:
            import_error += "ERROR: the xlrd modules is needed to record timings\n"
        try:
            import xlwt
        except:
            import_error += "ERROR: the xlwt modules is needed to record timings\n"
        if import_error != "":
            print >> self.stderr, import_error
            return
        rec_time_filename = self.config.record_timings_filename
        try:
            workbook = xlrd.open_workbook(filename=rec_time_filename,
                                          formatting_info=True)
        except:
            workbook = None
            summary = {}
        if workbook:
            summary = self.read_timings_sheet(workbook)
            if len(summary["date"]) > 100:
                # Need to rotate the file
                # 1) make a summary and save this
                self.report_timings_summary(summary, rec_time_filename)
                # 2) archive the file
                from zipfile import ZipFile
                import os
                zip_filename = os.path.join(self.config.path, "rec_time.zip")
                archive = ZipFile(zip_filename, "a")
                arc_name = "%s-%s.xls" % (rec_time_filename[len(self.config.path):-4],
                                          current.request.now.date()
                                          )
                archive.write(rec_time_filename,arc_name)
                archive.close()
                # 3) clear the current file
                os.unlink(rec_time_filename)
                summary = {}
        if "date" not in summary:
            last_col = 0
            summary["date"] = [current.request.now.date()]
        else:
            last_col = len(summary["date"])
            summary["date"].append(current.request.now.date())
        for (url, rd_obj) in self.results.items():
            if url not in summary:
                summary[url] = []
            # ensure that the row is as long as the number of dates
            shortage = last_col - len(summary[url])
            if shortage > 0:
                summary[url] = summary[url] + ['']*shortage
            summary[url].append((rd_obj.get_duration(), rd_obj.is_broken()))
        self.write_timings_sheet(summary, rec_time_filename)

    def read_timings_sheet(self, workbook):
        """
            This will extract all the details from the xls sheet
        """
        sheet = workbook.sheet_by_name("Timings")
        summary = {}
        RED = 0x0A
        num_cells = sheet.ncols
        summary["date"] = []
        for col in range(1, num_cells):
            summary["date"].append(sheet.cell_value(0, col))
        for row in range(1,sheet.nrows):
            url = sheet.cell_value(row, 0)
            summary[url] = []
            for col in range(1, num_cells):
                duration = sheet.cell_value(row, col)
                xf = sheet.cell_xf_index(row, col)
                bg = workbook.xf_list[xf].background
                broken = (bg.pattern_colour_index == RED)
                summary[url].append((duration, broken))
        return summary

    def write_timings_sheet(self, summary, filename=None):
        import xlwt
        RED = 0x0A
        book = xlwt.Workbook(encoding="utf-8")
        sheet = book.add_sheet("Timings")
        stylebroken = xlwt.XFStyle()
        stylebroken.pattern.pattern = stylebroken.pattern.SOLID_PATTERN
        stylebroken.pattern.pattern_fore_colour = RED
        col = 1
        for date in summary["date"]:
            sheet.write(0,col,str(date))
            col += 1
        row = 1
        for (url, results) in summary.items():
            if url == "date":
                continue
            sheet.write(row,0,url)
            col = 1
            for data in results:
                if len(data) == 2 and data[1]:
                    sheet.write(row,col,data[0],stylebroken)
                elif len(data) > 0:
                    sheet.write(row,col,data[0])
                col += 1
            row += 1
        if filename:
            book.save(filename)
        return book

    def report_timings_summary(self,
                               summary,
                               summary_file_name = None,
                               mean_threshold = 1):
        """
            This will extract the details from the sheet and optionally save
            them to a summary file

            summary: the summary details returned from the spreadsheet (read_timings_sheet)
            summary_file_name: name of the file to record the summary details (if required)
            mean_threshold: The minimum number of values required to include
                            the mean in the regression calculations
        """
        import numpy
        import datetime
        good_values = []
        other_values = []
        total_values = []
        for date in summary["date"]:
             good_values.append([])
             other_values.append([])
             total_values.append([])
        for (url,results)  in summary.items():
            if url == "date":
                continue
            else:
                cnt = 0
            for (duration, broken) in results:
                if duration != "":
                    total_values[cnt].append(duration)
                    if broken:
                        other_values[cnt].append(duration)
                    else:
                        good_values[cnt].append(duration)
                cnt += 1
        # get the number of days each entry is after the first date
        # and calculate the average, if the average is NAN then ignore both
        date_summary = []
        gv_mean = []
        gv_std = []
        gv_date = []
        cnt = 0
        start = datetime.datetime.strptime(summary["date"][0],"%Y-%m-%d")
        for list in good_values:
            if len(list) > mean_threshold:
                mean = numpy.mean(list)
                std = numpy.std(list)
                if not numpy.isnan(mean):
                    this_date = datetime.datetime.strptime(summary["date"][cnt],"%Y-%m-%d")
                    date_summary.append((this_date - start).days)
                    gv_mean.append(mean)
                    gv_std.append(std)
                    gv_date.append(summary["date"][cnt])
            cnt += 1
        # calculate the regression line
        if len(gv_mean) > 2:
            (m,b) = numpy.polyfit(date_summary, gv_mean, 1)
        else:
            m = b = 0

        if summary_file_name != None:
            book = self.write_timings_sheet(summary)
            sheet = book.add_sheet("summary")
            row = 0
            for date in gv_date:
                sheet.write(row,0,str(date))
                sheet.write(row,1,gv_mean[row])
                row += 1
            sheet.write(row,0,"Trend")
            sheet.write(row,1,m)
            # Save the details to the summary file
            book.save(summary_file_name)
        return (date_summary, gv_mean, gv_std, m, b)

    def report_model_url(self):
        print "Report breakdown by module"
        for (model, value) in self.model_url.items():
            print model
            for ud in value:
                url = ud[0]
                depth = ud[1]
                parent = ud[2]
                tabs = "\t" * depth
                print "%s %s-%s (parent url - %s)" % (tabs, depth, url, parent)

    def brokenReport(self):
        self.reporter("Broken Links")
        as_html = current.test_config.html
        self.broken_links_count = 0
        for (url, rd_obj) in self.results.items():
            if as_html:
                print_url = "<a href=%s%s target=\"_blank\">%s</a>" % (self.homeURL, url, url)
            else:
                print_url = url
            if rd_obj.is_broken():
                if rd_obj.threw_exception():
                    msg = "(Exception) %s" % print_url
                else:
                    http_code = rd_obj.return_http_code()
                    ticket = rd_obj.the_ticket(as_html)
                    try:
                        parent = self.urlParentList[url]
                        if as_html:
                            parent = "<a href=%s%s target=\"_blank\">Parent</a>" % (self.homeURL, parent)
                    except:
                        parent = "unknown"
                    msg = "%3d. (%s - %s) %s called from %s" % (self.broken_links_count + 1,
                                                                http_code,
                                                                ticket,
                                                                print_url,
                                                                parent
                                                                )
                self.reporter(msg)
                self.broken_links_count += 1

    def timeReport(self):
        from operator import itemgetter
        import numpy
        thresholdLink = {}
        linktimes = []
        for (url, rd_obj) in self.results.items():
            duration = rd_obj.get_duration()
            linktimes.append(duration)
            if duration > self.threshold:
                thresholdLink[url] = duration
        self.reporter("Time Analysis - Links beyond threshold")
        for (visited_url, duration) in sorted(thresholdLink.iteritems(),
                                              key=itemgetter(1),
                                              reverse=True):
            self.reporter( "%s took %.3f seconds" % (visited_url, duration))

        self.reporter("Time Analysis - summary")
        total = len(linktimes)
        average = numpy.mean(linktimes)
        std = numpy.std(linktimes)
        msg = "%s links visited with an average time of %.3f and standard deviation of %.3f" % (total, average, std)
        self.reporter(msg)

    def scatterplot(self):
        """
            Method to draw a scatterplot of the average time to download links
            against time. Add a regression line to show the trend over time.
        """
        try:
            from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
            self.FigureCanvas = FigureCanvas
            from matplotlib.figure import Figure
            self.Figure = Figure
            import numpy
        except ImportError:
            return
        try:
            import xlrd
        except:
            import_error += "ERROR: the xlrd modules is needed to record timings\n"
        rec_time_filename = self.config.record_timings_filename
        try:
            workbook = xlrd.open_workbook(filename=rec_time_filename,
                                          formatting_info=True)
        except:
            return
        import numpy
        # Only include the mean in the regression values if there are at least 10 URL timings
        summary = self.read_timings_sheet(workbook)
        (date_summary, gv_mean, gv_std, m, b) = self.report_timings_summary(summary, mean_threshold=10)
        if len(gv_mean) <= 2:
            return
        fig = Figure(figsize=(5, 2.5))
        canvas = self.FigureCanvas(fig)
        ax = fig.add_subplot(111)
        linear = numpy.poly1d([m,b])
        denom = numpy.max(gv_std)/50
        size = gv_std/denom
        ax.scatter(date_summary, gv_mean, marker="d", s=size)
        ax.plot(date_summary, linear(date_summary), '--r')

        chart = StringIO()
        canvas.print_figure(chart)
        image = chart.getvalue()
        import base64
        base64Img = base64.b64encode(image)
        image = "<img src=\"data:image/png;base64,%s\">" % base64Img
        self.reporter("Scatterplot of average link times per successful run")
        self.reporter(image)
        self.reporter("The trend line has a current slope of %s" % m)
        self.reporter("The y-intercept is %s seconds" % b)

    def depthReport(self):
        """
            Method to draw a histogram of the number of new links
            discovered at each depth.
            (i.e. show how many links are required to reach a link)
        """
        try:
            from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
            self.FigureCanvas = FigureCanvas
            from matplotlib.figure import Figure
            self.Figure = Figure
            from numpy import arange
        except ImportError:
            return
        self.reporter("Analysis of link depth")
        fig = Figure(figsize=(4, 2.5))
        # Draw a histogram
        width = 0.9
        rect = [0.12, 0.08, 0.9, 0.85]
        ax = fig.add_axes(rect)
        left = arange(len(self.linkDepth))
        plot = ax.bar(left, self.linkDepth, width=width)
        # Add the x axis labels
        ax.set_xticks(left+(width*0.5))
        ax.set_xticklabels(left)

        chart = StringIO()
        canvas = self.FigureCanvas(fig)
        canvas.print_figure(chart)
        image = chart.getvalue()
        import base64
        base64Img = base64.b64encode(image)
        image = "<img src=\"data:image/png;base64,%s\">" % base64Img
        self.reporter(image)

