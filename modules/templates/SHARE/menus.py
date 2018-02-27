# -*- coding: utf-8 -*-

from gluon import current
from s3 import *
from s3layouts import *
try:
    from .layouts import *
except ImportError:
    pass
import s3menus as default

# =============================================================================
class S3MainMenu(default.S3MainMenu):
    """ Custom Application Main Menu """

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        menu= [MM("Requests", c="req", f="req")(
                MM("Approve", c="req", f="req"),
                MM("Commitments", c="req", f="commit"),
                ),
               MM("Supplies", c="req", f="commit")(
                MM("Items", c="supply", f="item", m="summary"),
                MM("Facilities", c="org", f="facility"),
                MM("Assets", c="asset", f="asset"),
                ),
               MM("Sitreps", c="cms", f="blog", m="1"),
               MM("Organization", c="org", f="organisation"),
               MM("more", link=False)(
                MM("Documents", c="doc", f="document"),
                MM("Events", c="event", f="event"),
                ),
               ]

        return menu

# END =========================================================================
