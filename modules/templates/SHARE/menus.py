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
                MM("Commitments", c="req", f="commit"),
                ),
               MM("Aid & Supplies", c="supply", f="item/summary")(
                MM("Item Catalog", c="supply", f="catalog_item"),
                MM("Assets", c="asset", f="asset"),
                ),
               MM("Sitreps", c="cms", f="blog/1"),
               MM("more", link=False)(
                MM("Organizations", c="org", f="organisation"),
                MM("Facilities", c="org", f="facility"),
                MM("Documents", c="doc", f="document"),
                MM("Events", c="event", f="event"),
                ),
               ]

        return menu

# END =========================================================================
