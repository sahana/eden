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

        menu= [MM("Needs", c="req", f="need")(
                #MM("Approve", c="req", f="req"),
                #MM("Commitments", c="req", f="commit"),
                MM("Statistics", c="req", f="need", m="report"),
                ),
               #MM("Donors", c="req", f="commit")(
               # MM("Supply items", c="supply", f="item", m="summary"),
               # MM("Facilities", c="org", f="facility"),
               # MM("Assets", c="asset", f="asset"),
               # ),
               #MM("Sitreps", c="cms", f="blog", m="1"),
               #MM("Sitreps", c="cms", f="series", m="1/post"),
               MM("Sitreps", c="event", f="sitrep"),
               MM("Organizations", c="org", f="organisation"),
               MM("more", link=False)(
                MM("Documents", c="doc", f="document"),
                MM("Events", c="event", f="event"),
                MM("Sectors", c="org", f="sector"),
                ),
               ]

        return menu

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """ Custom Controller Menus """

    # -------------------------------------------------------------------------
    @staticmethod
    def event():
        """ EVENT / Event Module """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M()(
                    #M("Scenarios", c="event", f="scenario")(
                    #    M("Create", m="create"),
                    #    #M("Import", m="import", p="create"),
                    #),
                    M("Disasters", c="event", f="event")(
                        M("Create", m="create"),
                    ),
                    M("Disaster Types", c="event", f="event_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                        #M("Import", m="import", p="create"),
                    ),
                    #M("Incidents", c="event", f="incident")(
                    #    M("Create", m="create"),
                    #),
                    #M("Incident Reports", c="event", f="incident_report", m="summary")(
                    #    M("Create", m="create"),
                    #),
                    #M("Incident Types", c="event", f="incident_type")(
                    #    M("Create", m="create"),
                    #    #M("Import", m="import", p="create"),
                    #),
                    M("Situation Reports", c="event", f="sitrep")(
                        M("Create", m="create"),
                        #M("Import", m="import", p="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def org():
        """ ORG / Organization Registry """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="org")(
                    M("Organizations", f="organisation")(
                        M("Create", m="create"),
                        M("Import", m="import")
                    ),
                    M("Offices", f="office")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        M("Import", m="import")
                    ),
                    M("Facilities", f="facility")(
                        M("Create", m="create"),
                        M("Import", m="import"),
                    ),
                    M("Organization Types", f="organisation_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Office Types", f="office_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Facility Types", f="facility_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Sectors", f="sector", restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def req():
        """ REQ / Request Management """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="req")(
                    M("Needs", f="need")(
                        M("Create", m="create"),
                        M("Report", m="report"),
                        #M("Import", m="import", p="create"),
                    ),
                    M("Items", c="supply", f="item")(
                        M("Create", m="create"),
                        M("Report", m="report"),
                        M("Import", m="import", p="create"),
                    ),
                    # Catalog Items moved to be next to the Item Categories
                    #M("Catalog Items", c="supply", f="catalog_item")(
                       #M("Create", m="create"),
                    #),
                    M("Catalogs", c="supply", f="catalog")(
                        M("Create", m="create"),
                    ),
                    M("Item Categories", c="supply", f="item_category",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                )

# END =========================================================================
