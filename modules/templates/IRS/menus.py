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
            MM("Disease Tracking", c="disease", f="index"),
            MM("Hospitals", c="hms", f="hospital"),
            MM("Statistics", c="stats", f="demographic_data", m="summary"),
            MM("more", link=False, check=logged_in)(
                MM("Person Registry", c="pr", f="person",),
                MM("Organizations", c="org", f="organisation", m="summary"),
                MM("Burials", c="dvi", f="body"),
                MM("Content Management", c="cms", f="index"),
                MM("Documents", c="doc", f="document"),
                MM("Incidents", c="event", f="incident"),
                MM("Logistics", c="inv", f="warehouse"),
                MM("Projects", c="project", f="project"),
                MM("Requests", c="req", f="req"),
                MM("Staff", c="hrm", f="staff", m="summary",
                   check=logged_in),
                MM("Transport", c="transport", f="index"),
                MM("Vehicles", c="vehicle", f="vehicle"),
            ),
        ]

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """ Custom Controller Menus """

    # -------------------------------------------------------------------------
    @staticmethod
    def dvi():
        """ DVI / Disaster Victim Identification """

        return M(c="dvi")(
                    #M("Home", f="index"),
                    M("Recovery Requests", f="recreq")(
                        M("New Request", m="create"),
                        M("List Current",
                          vars={"recreq.status":"1,2,3"}),
                    ),
                    M("Dead Bodies", f="body")(
                        M("Add", m="create"),
                        M("List unidentified",
                          vars={"identification.status": "None"}),
                        M("Report by Age/Gender", m="report",
                          vars=dict(rows="age_group",
                                    cols="gender",
                                    fact="count(pe_label)",
                                    ),
                          ),
                    ),
                    #M("Missing Persons", f="person")(
                    #    M("List all"),
                    #),
                    M("Morgues", f="morgue")(
                        M("Create", m="create"),
                    ),
                    M("Dashboard", f="index"),
                )

# END =========================================================================
