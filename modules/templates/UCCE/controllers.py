# -*- coding: utf-8 -*-

#from gluon import *
from s3 import S3CustomController

THEME = "UCCE"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        self._view(THEME, "index.html")
        return {}

# END =========================================================================
