""" Sahana Eden Test Framework

    @copyright: 2011-2012 (c) Sahana Software Foundation
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
try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO
import sys
import socket

from tests.web2unittest import Web2UnitTest
from gluon import current
try:
    from twill import get_browser
    from twill import set_output
    from twill.browser import *
except ImportError:
    raise NameError("Twill not installed")
try:
    import mechanize
    #from mechanize import BrowserStateError
    #from mechanize import ControlNotFoundError
except ImportError:
    raise NameError("Mechanize not installed")

class BrokenLinkTest(Web2UnitTest):
    """ Smoke Test, visit every link it can find and report on the outcome """
    def __init__(self):
        Web2UnitTest.__init__(self)
        self.b = get_browser()
        self.b_data = StringIO()
        set_output(self.b_data)
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
        self.maxDepth = 16 # sanity check
        self.setThreshold(10)
        self.setUser("test@example.com/eden")

    def clearRecord(self):
        # the total url links visited
        self.totalLinks = 0
        # The number of unique urls found at depth i, where i is the index
        self.linkDepth = []
        # Dictionary of the parent for each URL
        self.urlParentList = {}
        # dictionary of ReportData objects indexed on the url
        self.results = {}

    def setDepth(self, depth):
        self.maxDepth = depth

    def setUser(self, user):
        self.credentials = user.split(",")

    def setThreshold(self, value):
        value = float(value)
        self.threshold = value
#        socket.setdefaulttimeout(value*2)

    def login(self, credentials):
        if credentials == "UNAUTHENTICATED":
            url = "%s/default/user/logout" % self.homeURL
            self.b.go(url)
            return True
        try:
            (self.user, self.password) = credentials.split("/",1)
        except:
            msg = "Unable to split %s into a user name and password" % user
            self.reporter(msg)
            return False
        url = "%s/default/user/login" % self.homeURL
        self.b.go(url)
        forms = self.b.get_all_forms()
        for form in forms:
            try:
                if form["_formname"] == "login":
                    self.b._browser.form = form
                    form["email"] = self.user
                    form["password"] = self.password
                    self.b.submit("Login")
                    # If login is successful then should be redirected to the homepage
                    return self.b.get_url()[len(self.homeURL):] == "/default/index"
            except:
                # This should be a mechanize.ControlNotFoundError, but
                # for some unknown reason that isn't caught on Windows or Mac
                pass
        return False

    def runTest(self):
        """
            Test to find all exposed links and check the http code returned.

            This test doesn't run any javascript so some false positives
            will be found.

            The test can also display an histogram depicting the number of
            links found at each depth.
        """
        for user in self.credentials:
            self.clearRecord()
            if self.login(user):
                self.reporter("Smoke Test for user %s" % self.user)
                self.visitLinks()

    def visitLinks(self):
        url = self.homeURL
        to_visit = [url]
        start = time()
        for depth in range(self.maxDepth):
            if len(to_visit) == 0:
                break
            self.linkDepth.append(len(to_visit))
            self.totalLinks += len(to_visit)
            visit_start = time()
            url_visited = "%d urls" % len(to_visit)
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
        self.report()

    def visit(self, url_list, depth):
        repr_list = [".pdf", ".xls", ".rss", ".kml"]
        to_visit = []
        record_data = self.config.verbose > 0
        for visited_url in url_list:
            index_url = visited_url[len(self.homeURL):]
            if record_data:
                if index_url in self.results.keys():
                    print >> self.stdout, "Warning duplicated url: %s" % index_url
                self.results[index_url] = ReportData()
                current_results = self.results[index_url]
                current_results.depth = depth
            # Find out if the page can be visited
            open_novisit = False
            for repr in repr_list:
                if repr in index_url:
                    open_novisit = True
                    break
            try:
                if open_novisit:
                    action = "open_novisit"
                else:
                    action = "open"
                visit_start = time()
                self.b._journey(action, visited_url)
                http_code = self.b.get_code()
                duration = time() - visit_start
                if record_data:
                    current_results.duration = duration
                if duration > self.threshold:
                    if self.config.verbose >= 3:
                        print >> self.stdout, "%s took %.3f seconds" % (visited_url, duration)
            except Exception as e:
                duration = time() - visit_start
                import traceback
                print traceback.format_exc()
                if record_data:
                    current_results.broken = True
                    current_results.exception = True
                    current_results.duration = duration
                continue
            http_code = self.b.get_code()
            if http_code != 200:
                if record_data:
                    current_results.broken = True
                    current_results.http_code = http_code
            elif open_novisit:
                continue
            links = []
            try:
                if self.b._browser.viewing_html():
                    links = self.b._browser.links()
                else:
                    continue
            except Exception as e:
                import traceback
                print traceback.format_exc()
                if record_data:
                    current_results.broken = True
                    current_results.exception = True
                continue
            for link in (links):
                url = link.absolute_url
                if url.find(self.url_ticket) != -1:
                    # A ticket was raised so...
                    # capture the details and add to brokenLinks
                    if record_data:
                        current_results.broken = True
                        current_results.ticket = url[len(self.homeURL):]
                    break # no need to check any other links on this page
                if url.find(self.homeURL) == -1:
                    continue
                ignore_link = False
                for ignore in self.include_ignore:
                    if url.find(ignore) != -1:
                        ignore_link = True
                        break
                if ignore_link:
                    continue
                for strip in self.strip_url:
                    location = url.find(strip)
                    if location != -1:
                        url = url[0:location]
                short_url = url[len(self.homeURL):]
                if url not in url_list and \
                   short_url not in self.results.keys() and \
                   url not in to_visit:
                    self.urlParentList[short_url] = index_url
                    to_visit.append(url)
        return to_visit
    
    def report(self):
        self.reporter("%d URLs visited" % self.totalLinks)
        self.brokenReport()
        self.timeReport()
        if self.config.record_timings:
            self.record_timings()
        self.report_link_depth()

    def report_link_depth(self):
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
            rec_time_filename = config.record_timings_filename
            try:
                workbook = xlrd.open_workbook(filename=rec_time_filename)
                try:
                    sheet = workbook.sheet_by_name("Timings")
                    summary = report_read_timings_file
                    if sheet.ncols > 200:
                        # Need to rotate the file
                        # 1) make a summary and save this
                        report_timings_summary(summary, config.record_summary_filename)
                        # 2) archive the file
                        from zipfile import ZipFile
                        archive = ZipFile("rec_time.zip", "a")
                        arc_name = "%s-%s.xls" % (rec_time_filename[:-4],
                                                  current.request.now.date()
                                                  )
                        archive.write(filename,arc_name)
                        # 3) clear the current file
                        import os
                        os.unlink(rec_time_filename)
                except:
                    pass
            except:
                pass

    def report_read_timings_file(self, sheet):
        """
            This will extract all the details from the sheet
        """
        summary = {}
        num_cells = worksheet.ncols
        for row in range(sheet.nrows):
            url = sheet.cell_value(row, 0)
            summary[url] = []
            for col in range(1, num_cells, 2):
                if sheet.cell_type(row, col) != 0: # not empty
                    date = sheet.cell_value(0, col)
                    time = sheet.cell_value(row, col)
                    code = sheet.cell_value(row, col+1)
                    summary[url].append((date, time, code))
        return summary

    def report_timings_summary(self, summary, summary_file_name = None):
        """
            This will extract the details from the sheet and optionally save
            them to a summary file
        """
        # @todo calculate the summary details
        good_values = []
        other_values = []
        total_values = []
        if summary_file_name != None:
            # Save the details to the summary file
            # @todo save the details to the file
            pass

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
        n = 1
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
                    msg = "%3d. (%s - %s) %s called from %s" % (n,
                                                                http_code,
                                                                ticket,
                                                                print_url,
                                                                parent
                                                                )
                self.reporter(msg)
                n += 1

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
        msg = "%s links visited with an average time of %s and standard deviation of %s" % (total, average, std)
        self.reporter(msg)

    def depthReport(self):
        pass

class ReportData():
    """
    Class to hold the data collected from the smoke test ready for reporting
    Instances of this class will be held in the dictionary results which will
    be keyed on the url. This way, in an attempt to minimise the memory used,
    the url doesn't need to be stored in this class.

    The class will have the following properties
    broken: boolean
    exception: boolean
    http_code: integer
    ticket: URL of any ticket linked with this url
    parent: the parent URL of this url
    depth: how deep is this url
    duration: how long did it take to get the url
    """
    def is_broken(self):
        if hasattr(self, "broken"):
            return self.broken
        return False

    def threw_exception(self):
        if hasattr(self, "exception"):
            return self.exception
        return False

    def return_http_code(self):
        if hasattr(self, "http_code"):
            return self.http_code
        return "-"

    def the_ticket(self, html):
        """
            Should only have a ticket if it is broken,
            but won't always have a ticket to display.
        """
        if hasattr(self, "ticket"):
            if html:
                return "<a href=%s target=\"_blank\">Ticket</a>" % (self.ticket)
            else:
                return "Ticket: %s" % (self.ticket)
        return "no ticket"

    def get_parent(self):
        if hasattr(self, "parent"):
            return self.parent
        return ""

    def get_depth(self):
        if hasattr(self, "depth"):
            return self.depth
        return 0

    def get_duration(self):
        if hasattr(self, "duration"):
            return self.duration
        return 0
