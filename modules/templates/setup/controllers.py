# -*- coding: utf-8 -*-

from gluon import redirect, URL
from s3 import S3CustomController

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        redirect(URL(c="setup", f="index"))

# END =========================================================================
