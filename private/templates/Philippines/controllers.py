# -*- coding: utf-8 -*-

from gluon import current
from gluon.html import *
from gluon.storage import Storage

from s3.s3utils import S3CustomController

THEME = "Philippines"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        response = current.response
        
        output = {}
        #output["title"] = response.title = current.deployment_settings.get_system_name()

        s3 = response.s3
        # Image Carousel
        s3.jquery_ready.append('''$('#myCarousel').carousel()''')

        # @ToDo: Latest 4 Requests

        self._view(THEME, "index.html")
        return output

# =============================================================================
class time(S3CustomController):
    """ Custom page to display opportunities to donate Time """

    # -------------------------------------------------------------------------
    def __call__(self):
        """ Main entry point, configuration """

        self._view(THEME, "time.html")
        return dict()

# END =========================================================================
