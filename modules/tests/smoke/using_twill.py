# -*- coding: utf-8 -*-

""" Sahana Test Framework

    Used by broken_links to use Twill to power the smoke tests
"""


from report_data import ReportData
from time import time

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
                    current_results.ticket = url
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
               short_url != "" and \
               short_url not in self.results.keys() and \
               url not in to_visit:
                self.urlParentList[short_url] = index_url
                to_visit.append(url)
    return to_visit

