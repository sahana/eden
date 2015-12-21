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
    def menu_help(cls, **attr):
        """ Help Menu """

        return MM("About", link=False, right=True)(
                    MM("About this Site", f="about", right=True),
                    MM("User Manual", c="default", f="index",
                        args=["docs"],
                        vars={"name": "UserManual"},
                        ),
                    MM("Contact us", f="contact", right=True),
                    )


    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        return [
            MM("News", c="cms", f="newsfeed", args="datalist",
               icon="icon-news",
               ),
            MM("Current Needs", c="req", f="organisation_needs"),
            MM("Organizations", c="org", f="organisation"),
            MM("Facilities", c="org", f="facility", m="summary"),
            homepage("gis"),
            MM("More", link=False)(
                MM("Requests", c="req", f="req", vars = {"type": "1"}),
                homepage("inv"),
                homepage("hrm"),
                homepage("vol"),
                homepage("project"),
                homepage("event"),
                #MM("Missing Persons", c="mpr", f="person"),
            ),
        ]

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """ Custom Application Side Menu """

    # -------------------------------------------------------------------------
    @staticmethod
    def org():
        """ ORG / Organization Registry """

        ADMIN = current.session.s3.system_roles.ADMIN
        SECTORS = "Clusters" if current.deployment_settings.get_ui_label_cluster() \
                             else "Sectors"

        return M(c="org")(
                    M("Organizations", f="organisation")(
                        M("Create", m="create"),
                        M("Import", m="import")
                    ),
                    M("Facilities", f="facility", m="summary")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        M("Import", m="import"),
                    ),
                    M("Offices", f="office")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        M("Import", m="import")
                    ),
                    M("Resources", f="resource", m="summary")(
                        M("Create", m="create"),
                        M("Import", m="import")
                    ),
                    M("Organization Types", f="organisation_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Service Types", f="service",
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
                    M(SECTORS, f="sector", restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def project():
        """ PROJECT / Project Tracking & Management """

        ADMIN = current.session.s3.system_roles.ADMIN

        menu = M(c="project")(
             M("Projects", f="project", m="summary")(
                M("Create", m="create"),
             ),
             M("Locations", f="location")(
                M("Map", m="map"),
                M("Contacts", f="location_contact"),
             ),
            M("Reports", f="location", m="report")(
                M("3W", f="location", m="report"),
                M("Beneficiaries", f="beneficiary", m="report"),
                #M("Indicators", f="indicator", m="report",
                #  check=indicators,
                #  ),
                #M("Indicators over Time", f="indicator", m="timeplot",
                #  check=indicators,
                #  ),
                M("Funding", f="organisation", m="report"),
             ),
             M("Import", f="project", m="import", p="create", restrict=[ADMIN])(
                M("Import Projects", m="import", p="create"),
                M("Import Project Organizations", f="organisation",
                  m="import", p="create"),
                M("Import Project Communities", f="location",
                  m="import", p="create"),
             ),
             M("Activity Types", f="activity_type", restrict=[ADMIN])(
                M("Create", m="create"),
             ),
             M("Beneficiary Types", f="beneficiary_type", restrict=[ADMIN])(
                M("Create", m="create"),
             ),
             M("Sectors", f="sector", restrict=[ADMIN])(
                M("Create", m="create"),
             ),
             M("Themes", f="theme", restrict=[ADMIN])(
                M("Create", m="create"),
             ),
            )

        return menu

    # -------------------------------------------------------------------------
    @staticmethod
    def req():
        """ REQ / Request Management """

        if not current.auth.s3_logged_in():
            return None

        ADMIN = current.session.s3.system_roles.ADMIN
        settings = current.deployment_settings
        types = settings.get_req_req_type()

        get_vars = {}
        if len(types) == 1:
            t = types[0]
            if t == "Stock":
                get_vars = {"type": "1"}
            elif t == "People":
                get_vars = {"type": "2"}
        create_menu = M("Create", m="create", vars=get_vars)

        recurring = lambda i: settings.get_req_recurring()
        use_commit = lambda i: settings.get_req_use_commit()
        req_items = lambda i: "Stock" in types
        req_skills = lambda i: "People" in types

        return M(c="req")(
                    M("Current Needs", f="organisation_needs")(
                        M("Create", m="create"),
                        M("Import", m="import", restrict=[ADMIN]),
                    ),
                    M("Needs at Facilities", f="site_needs", m="summary")(
                        M("Create", m="create"),
                    ),
                    M("Requests", f="req", vars=get_vars)(
                        create_menu,
                        M("List Recurring Requests", f="req_template", check=recurring),
                        M("Map", m="map"),
                        M("Report", m="report"),
                        M("Search All Requested Items", f="req_item",
                          check=req_items),
                        M("Search All Requested Skills", f="req_skill",
                          check=req_skills),
                    ),
                    M("Commitments", f="commit", check=use_commit)(
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
