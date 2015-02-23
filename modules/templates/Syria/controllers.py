# -*- coding: utf-8 -*-

#from gluon import current
from gluon.html import URL
from gluon.http import redirect

from s3 import S3CustomController

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        redirect(URL(c="project", f="activity", args=["summary"]))

# END =========================================================================
