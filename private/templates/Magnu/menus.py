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

        return [
            MM("Magnu"),
            MM("News", c="cms", f="newsfeed", args="datalist"),
            MM("Map", c="gis", f="index"),
            MM("Resources", link=False)(
                MM("Camps", c="cr", f="shelter", args="summary"),
                MM("Contacts", c="pr", f="person", args="summary"),
                MM("Demographics", c="stats", f="demographic_data", args="summary"),
                MM("Health", c="hms", f="hospital", args="summary"),
                MM("Incidents", c="event", f="ireport", args="summary"),
                MM("Offices", c="org", f="office", args="summary"),
                MM("Organisations", c="org", f="organisation", args="summary"),
                MM("Projects", c="project", f="project", args="summary"),
                MM("Security", c="security", f="level"),
                MM("Transport", c="transport", f="index"),
                MM("Water", c="water", f="index"),
            ),
        ]

# END =========================================================================
