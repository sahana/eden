# -*- coding: utf-8 -*-

""" Sahana Test Framework

    Used by broken_links for reporting
"""

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
