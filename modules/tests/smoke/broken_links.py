from time import time
from StringIO import StringIO

from tests.web2unittest import Web2UnitTest
from gluon import current
try:
    from twill import get_browser
    from twill import set_output
    from twill.browser import *
except ImportError:
    raise NameError("Twill not installed")
try:
    from mechanize import BrowserStateError
    from mechanize import ControlNotFoundError
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
                               "/admin/default/",
                              )
        # tuple of strings that should be removed from the URL before storing
        # Typically this will be some variables passed in via the URL 
        self.strip_url = ("?_next=",
                          )
        self.maxDepth = 2 # sanity check
        self.setUser("test@example.com/eden")

    def clearRecord(self):
        # list of links that return a http_code other than 200
        # with the key being the URL and the value the http code
        self.brokenLinks = dict()
        # List of links visited (key) with the depth
        self.urlList = dict()
        # List of urls for each model
        self.model_url = dict()

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
                    return True
            except:
                pass
        return False

    def runTest(self):
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
            visit_start = time()
            msg = "%d urls" % len(to_visit)
            to_visit = self.visit(to_visit, depth)
            msg = "Visited %s in %.3f seconds, %d more urls found" % (msg, time()-visit_start, len(to_visit))
            self.reporter(msg)
        finish = time()
        self.report()
#        self.report_model_url()
        self.reporter("Finished took %.3f seconds" % (finish - start))
    


    def add_to_model(self, url, depth, parent):
        start = url.find(self.homeURL) + len(self.homeURL)
        end = url.find("/",start) 
        model = url[start:end]
        if model in self.model_url:
            self.model_url[model].append((url, depth, parent))
        else:
            self.model_url[model] = [(url, depth, parent)]
    
    def visit(self, url_list, depth):
        to_visit = []
        for visited_url in url_list:
            index_url = visited_url[len(self.homeURL):]
            try:
                self.b.go(visited_url)
            except Exception as e:
                try:
                    # If the page is not an html then we shouldn't really visit it
                    # @todo put a check in earlier for the representation
                    self.b._journey("open_novisit", visited_url)
                    print "%s: %s" % (self.b.get_code(), visited_url)
                except Exception as e:
                    import traceback
                    print traceback.format_exc()
                    self.brokenLinks[index_url] = ("-","Exception raised")
                    continue
            http_code = self.b.get_code()
            if http_code != 200:
                url = "<a href=%s target=\"_blank\">URL</a>" % (visited_url)
                self.brokenLinks[index_url] = (http_code,url)
            try:
                links = self.b._browser.links()
            except BrowserStateError:
                continue # not html so unable to extract links
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
    
        self.reporter("Broken Links")
        n = 1
        for (url, result) in self.brokenLinks.items():
            http_code = result[0]
            if len(result) == 1:
                self.reporter("%3d. (%s) %s" % (n, http_code, url,))
            else:
                self.reporter("%3d. (%s-%s) %s" % (n, http_code, result[1], url))
            n += 1
    
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
