# -*- coding: utf-8 -*-

from s3.s3utils import S3CustomController

THEME = "skeleton"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        self._view(THEME, "index.html")
        return dict()

# END =========================================================================
