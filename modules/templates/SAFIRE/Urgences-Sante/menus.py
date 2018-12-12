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

        menu= [MM("Call Logs", c="event", f="incident_report"),
               MM("Incidents", c="event", f="incident", m="summary"),
               MM("Scenarios", c="event", f="scenario"),
               MM("more", link=False)(
                MM("Documents", c="doc", f="document"),
                MM("Events", c="event", f="event"),
                MM("Staff", c="hrm", f="staff"),
                MM("Volunteers", c="vol", f="volunteer"),
                MM("Assets", c="asset", f="asset"),
                MM("Organizations", c="org", f="organisation"),
                MM("Facilities", c="org", f="facility"),
                #MM("Hospitals", c="hms", f="hospital", m="summary"),
                MM("Shelters", c="cr", f="shelter"),
                MM("Warehouses", c="inv", f="warehouse"),
                MM("Item Catalog", c="supply", f="catalog_item"),
                ),
               ]

        return menu

# END =========================================================================
