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
    """ Selenium Unit Test """
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
        self.threshold = 10
        self.setUser("test@example.com/eden")
        self.linkDepth = []

    def clearRecord(self):
        # list of links that return a http_code other than 200
        # with the key being the URL and the value the http code
        self.brokenLinks = dict()
        # List of links visited (key) with the parent
        self.urlParentList = dict()
        # List of links visited (key) with the depth
        self.urlList = dict()
        # List of urls for each model
        self.model_url = dict()
        self.totalLinks = 0

    def setDepth(self, depth):
        self.maxDepth = depth

    def setUser(self, user):
        self.credentials = user.split(",")

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
        self.threasholdLink = []
        self.linktimes = []
        for user in self.credentials:
            self.clearRecord()
            if self.login(user):
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
        self.report()
        self.reporter("Finished took %.3f seconds" % (finish - start))
        self.report_link_depth()
#        self.report_model_url()
    


    def add_to_model(self, url, depth, parent):
        start = url.find(self.homeURL) + len(self.homeURL)
        end = url.find("/",start) 
        model = url[start:end]
        if model in self.model_url:
            self.model_url[model].append((url, depth, parent))
        else:
            self.model_url[model] = [(url, depth, parent)]
    
    def visit(self, url_list, depth):
        repr_list = [".pdf", ".xls", ".rss", ".kml"]
        to_visit = []
        for visited_url in url_list:
            index_url = visited_url[len(self.homeURL):]
            # Find out if the page can be visited
            open_novisit = False
            for repr in repr_list:
                if repr in index_url:
                    open_novisit = True
                    break
            try:
                if open_novisit:
                    visit_start = time()
                    self.b._journey("open_novisit", visited_url)
                    http_code = self.b.get_code()
                    if http_code != 200: # an error situation
                        self.b.go(visited_url)
                        http_code = self.b.get_code()
                    duration = time() - visit_start
                    self.linktimes.append(duration)
                    if duration > self.threshold:
                        self.threasholdLink.append((visited_url, duration))
                        if self.config.verbose >= 3:
                            print >> self.stdout, "%s took %.3f seconds" % (visited_url, duration)
                else:
                    visit_start = time()
                    self.b.go(visited_url)
                    http_code = self.b.get_code()
                    duration = time() - visit_start
                    self.linktimes.append(duration)
                    if duration > self.threshold:
                        self.threasholdLink.append((visited_url, duration))
                        if self.config.verbose >= 3:
                            print >> self.stdout, "%s took %.3f seconds" % (visited_url, duration)
            except Exception as e:
                import traceback
                print traceback.format_exc()
                self.brokenLinks[index_url] = ("-","Exception raised")
                continue
            http_code = self.b.get_code()
            if http_code != 200:
                url = "<a href=%s target=\"_blank\">URL</a>" % (visited_url)
                self.brokenLinks[index_url] = (http_code,url)
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
                self.brokenLinks[index_url] = ("-","Exception raised")
                continue
            for link in (links):
                url = link.absolute_url
                if url.find(self.url_ticket) != -1:
                    # A ticket was raised so...
                    # capture the details and add to brokenLinks
                    if current.test_config.html:
                        ticket = "<a href=%s target=\"_blank\">Ticket</a> at <a href=%s target=\"_blank\">URL</a>" % (url,visited_url)
                    else:
                        ticket = "Ticket: %s" % url
                    self.brokenLinks[index_url] = (http_code,ticket)
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
                if url not in self.urlList:
                    self.urlList[url] = depth
                    self.urlParentList[url[len(self.homeURL):]] = visited_url
                    self.add_to_model(url, depth, visited_url)
                    if url not in to_visit:
                        to_visit.append(url)
        return to_visit
    
    def report(self):
#        print "Visited pages"
#        n = 1
#        for (url, depth) in self.urlList.items():
#            print "%d. depth %d %s" % (n, depth, url,)
#            n += 1
        self.reporter("%d URLs visited" % self.totalLinks)
        self.reporter("Broken Links")
        n = 1
        for (url, result) in self.brokenLinks.items():
            http_code = result[0]
            try:
                parent = self.urlParentList[url]
                if current.test_config.html:
                    parent = "<a href=%s target=\"_blank\">Parent</a>" % (parent)
            except:
                parent = "unknown"
            if len(result) == 1:
                self.reporter("%3d. (%s) %s called from %s" % (n,
                                                http_code,
                                                url,
                                                parent
                                               )
                )
            else:
                self.reporter("%3d. (%s-%s) %s called from %s" % (n,
                                                   http_code,
                                                   result[1],
                                                   url,
                                                   parent
                                                  )
                )
            n += 1
        for (visited_url, duration) in self.threasholdLink:
            self.reporter( "%s took %.3f seconds" % (visited_url, duration))

        import numpy
        self.reporter("Time Analysis")
        total = len(self.linktimes)
        average = numpy.mean(self.linktimes)
        std = numpy.std(self.linktimes)
        msg = "%s links visited with an average time of %s and standard deviation of %s" % (total, average, std)
        self.reporter(msg)

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
