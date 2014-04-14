# -*- coding: utf-8 -*-

""" Sahana Test Framework

    Used by broken_links to use Ghost.py to power the smoke tests
"""

from report_data import ReportData
from time import time

def login(self, credentials):
    if credentials == "UNAUTHENTICATED":
        url = "%s/default/user/logout" % self.homeURL
        self.ghost.open(url)
        return True

    try:
        _values = credentials.split("/",1)
    except:
        msg = "Unable to split %s into a user name and password" % user
        self.reporter(msg)
        return False

    values = {'email':_values[0], 'password':_values[1]}

    url = "%s/default/user/login" % self.homeURL

    self.ghost.open(url)
    self.ghost.fill("form", values)

    _formSubmit_js = 'document.getElementsByName("_formname")[0].form.submit()'
    page, resources = self.ghost.evaluate(_formSubmit_js,
        expect_loading = True)

    return page.url[len(self.homeURL):] == "/default/index"

def visit(self, url_list, depth):
    repr_list = [".pdf", ".xls", ".rss", ".kml"]
    record_data = self.config.verbose > 0
    to_visit = []

    for visited_url in url_list:
        index_url = visited_url[len(self.homeURL):]
        if record_data:
            if index_url in self.results.keys():
                print >> self.stdout, "Warning duplicated url: %s" % index_url
            self.results[index_url] = ReportData()
            current_results = self.results[index_url]
            current_results.depth = depth

        # try opening the page using ghost
        try:
            visit_start = time()
            page, resources = self.ghost.open(visited_url)
            if page is None and extra_resources is None:
                raise Exception("Ghost could not process the url %s" % visited_url)
        except Exception as e:
            duration = time() - visit_start
            import traceback
            print traceback.format_exc()
            if record_data:
                current_results.broken = True
                current_results.exception = True
                current_results.duration = duration
            continue

        open_novisit = False

        for repr in repr_list:
            if repr in index_url:
                open_novisit = True
                break

        # it is not a web page (.pdf etc), then the page will be None
        if page is None:
            resource = resources[0]
            http_code = resource.http_status
        # it is a html page
        else:
            http_code = page.http_status

        duration = time() - visit_start
        if record_data:
            current_results.duration = duration
        if duration > self.threshold:
            if self.config.verbose >= 3:
                print >> self.stdout, "%s took %.3f seconds" % (visited_url, duration)

        if http_code != 200:
            if record_data:
                current_results.broken = True
                current_results.http_code = http_code
        elif open_novisit:
            continue

        # get all the anchor tags present in the page
        try:
            links = []
            _get_links_js = """
                            var anchor_elems = document.getElementsByTagName('a');
                            var urls = [];
                            var url;
                            for (var i = 0; i< anchor_elems.length; i++)
                            {
                                url = anchor_elems[i].href;
                                urls.push(url);
                            }
                            urls;
                        """
            links, resources = self.ghost.evaluate(_get_links_js)
            if links is None:
                raise Exception("Javascript could not fetch the links in this page")

        except Exception as e:
            import traceback
            print traceback.format_exc()
            if record_data:
                current_results.broken = True
                current_results.exception = True
            continue

        for url in links:
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
        # TODO close the files opened by visited_url
    return to_visit
