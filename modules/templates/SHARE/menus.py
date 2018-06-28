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

        menu= [MM("Needs", link=False)(
                #MM("Statistics",  m="report"),
                #MM("Map", m="map"),
                MM("View", c="req", f="need", m="summary"),
                MM("Create", c="req", f="need", m="create"),
                ),
               MM("4W", link=False)(
                #MM("Statistics",  m="report"),
                #MM("Map", m="map"),
                MM("View", c="project", f="activity", m="summary"),
                MM("Create", c="project", f="activity", m="create"),
                ),
               MM("Situational Updates", c="event", f="sitrep"),
               MM("Organizations", c="org", f="organisation")(
                MM("Offices", c="org", f="office"),
                MM("Facilities", c="org", f="facility"),
               ),
               MM("more", link=False)(
                MM("Documents", c="doc", f="document"),
                MM("Disasters", c="event", f="event"),
                MM("Items", c="supply", f="item"),
                MM("Sectors", c="org", f="sector"),
                #MM("Services", c="org", f="service"),
                ),
               ]

        return menu

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """ Custom Controller Menus """

    # -------------------------------------------------------------------------
    @staticmethod
    def event():
        """ Events Module """

        if current.request.function == "sitrep":
            return M()(
                        M("Situational Updates", c="event", f="sitrep")(
                            M("Create", m="create"),
                        ),
                    )
        else:
            ADMIN = current.session.s3.system_roles.ADMIN
            return M()(
                        M("Disasters", c="event", f="event")(
                            M("Create", m="create"),
                        ),
                        M("Disaster Types", c="event", f="event_type",
                          restrict=[ADMIN])(
                            M("Create", m="create"),
                        ),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def org():
        """ Organisation Registry """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="org")(
                    M("Organizations", f="organisation")(
                        M("Create", m="create"),
                        #M("Import", m="import")
                    ),
                    M("Offices", f="office")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        #M("Import", m="import")
                    ),
                    M("Facilities", f="facility")(
                        M("Create", m="create"),
                        #M("Import", m="import"),
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
                    #M("Services", f="service", restrict=[ADMIN])(
                    #    M("Create", m="create"),
                    #),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def project():
        """ Project Module """

        #ADMIN = current.session.s3.system_roles.ADMIN

        #return M()(
        #            M("Activities", c="project", f="activity", m="summary")(
        #                M("Create", m="create"),
        #                #M("Statistics", m="report"),
        #                #M("Map", m="map"),
        #                #M("Import", m="import", p="create"),
        #            ),
        #        )

        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def req():
        """ Requests Management """

        #ADMIN = current.session.s3.system_roles.ADMIN

        #return M(c="req")(
        #            M("Needs", f="need", m="summary")(
        #                M("Create", m="create"),
        #                #M("Statistics", m="report"),
        #                #M("Map", m="map"),
        #                #M("Import", m="import", p="create"),
        #            ),
        #        )

        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def supply():
        """ Supply Management """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="supply")(
                    M("Items", c="supply", f="item")(
                        M("Create", m="create"),
                        M("Report", m="report"),
                        M("Import", m="import", p="create"),
                    ),
                    # Catalog Items moved to be next to the Item Categories
                    #M("Catalog Items", c="supply", f="catalog_item")(
                       #M("Create", m="create"),
                    #),
                    #M("Catalogs", c="supply", f="catalog")(
                    #    M("Create", m="create"),
                    #),
                    M("Item Categories", c="supply", f="item_category",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                )

# END =========================================================================
