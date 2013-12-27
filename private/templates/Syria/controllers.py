# -*- coding: utf-8 -*-

from gluon import current
from gluon.html import URL
from gluon.http import redirect

from s3.s3utils import S3CustomController

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        gtable = current.s3db.gis_location
        syria = current.db(gtable.name == "Syrian Arab Republic").select(gtable.id,
                                                                         limitby=(0, 1)
                                                                         ).first()

        redirect(URL(c="gis", f="location", args=[syria.id, "profile"]))

# END =========================================================================
