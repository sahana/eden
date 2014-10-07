# -*- coding: utf-8 -*-

#from gluon import current, URL
#from gluon.html import *
#from gluon.storage import Storage

from s3 import S3CustomController

THEME = "CRMT2"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        output = {}

        self._view(THEME, "index.html")
        return output

# END =========================================================================
