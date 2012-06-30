# -*- coding: utf-8 -*-

"""
    This file is unused
    - current tests are in modules/tests
"""

__all__ = ["WSGI_Test"]

import wsgi_intercept.webtest_intercept

class WSGI_Test(wsgi_intercept.webtest_intercept.WebCase):
    """
    Class to use for Testing Sahana
    - DocTests can call this direct
    - UnitTests can extend this
    """
    HTTP_CONN = wsgi_intercept.WSGI_HTTPConnection
    HOST = "localhost"
    PORT = 8000

    def __init__(self, db):
        "Copy Intialise"
        wsgi_intercept.webtest_intercept.WebCase.__init__(self)
        #current.db=db
        return

    def setUp(self):
        "Hook into the WSGI process"
        wsgi_intercept.add_wsgi_intercept(self.HOST, self.PORT, create_fn)
        return

    def runTest(self):
        "Mandatory method for all TestCase instances"
        return

