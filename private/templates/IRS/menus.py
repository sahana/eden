# -*- coding: utf-8 -*-

from gluon import *
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

        logged_in = current.auth.is_logged_in()

        return [
            MM("Home", c="default", f="index"),
            MM("News", c="cms", f="newsfeed", args="datalist"),
            MM("Map", c="gis", f="index"),
            MM("Incidents", c="event", f="incident"),
            MM("Staff", c="hrm", f="staff", m="summary",
               check=logged_in),
            MM("Vehicles", c="vehicle", f="vehicle"),
            MM("more", link=False, check=logged_in)(
                MM("Person Registry", c="pr", f="person",),
                MM("Organizations", c="org", f="organisation", m="summary"),
                MM("Content Management", c="cms", f="index"),
                MM("Documents", c="doc", f="document"),
                MM("Disease", c="disease", f="index"),
                MM("Hospitals", c="hms", f="hospital"),
                MM("Logistics", c="inv", f="warehouse"),
                MM("Projects", c="project", f="project"),
                MM("Requests", c="req", f="req"),
                MM("Statistics", c="stats", f="demographic_data", m="summary"),
                MM("Transport", c="transport", f="index"),
            ),
        ]

# END =========================================================================
