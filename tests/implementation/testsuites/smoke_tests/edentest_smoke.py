# -*- coding: utf-8 -*-

class edentest_smoke(object):
    """ Smoke Test, visit every link it can find and report on the outcome """

    def __init__(self, base_url, do_not_follow, ext_links):
        self.base_url = base_url
        self.do_not_follow = do_not_follow
        self.follow_external_links = ext_links

    def check_if_url_should_be_skipped(self, url):

        if len(url) == 0:
            return 1

        if not self.follow_external_links and url.find(self.base_url) == -1:
            return 1

        for ignore in self.do_not_follow:
            if url.find(ignore) != -1:
                return 1

        return 0

    @staticmethod
    def strip_url_of_unwanted_parts(url):

        strip_url = ("?_next=",)

        for strip_part in strip_url:
            url = url.split(strip_part)[0]

        return url

    @staticmethod
    def increment_urls_failed(lf, status):

        if status != 0:
            lf = lf + 1

        return lf

    @staticmethod
    def check_if_not_already_added_or_visited(visited, to_visit, url_list, url):

        if url in visited or url in to_visit or url in url_list:
            return 1
        else:
            return 0

