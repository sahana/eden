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
    """
        Custom Application Main Menu:

        The main menu consists of several sub-menus, each of which can
        be customised separately as a method of this class. The overall
        composition of the menu is defined in the menu() method, which can
        be customised as well:

        Function        Sub-Menu                Access to (standard)

        menu_modules()  the modules menu        the Eden modules
        menu_gis()      the GIS menu            GIS configurations
        menu_admin()    the Admin menu          System/User Administration
        menu_lang()     the Language menu       Selection of the GUI locale
        menu_auth()     the User menu           Login, Logout, User Profile
        menu_help()     the Help menu           Contact page, About page

        The standard uses the MM layout class for main menu items - but you
        can of course use a custom layout class which you define in layouts.py.

        Additional sub-menus can simply be defined as additional functions in
        this class, and then be included in the menu() method.

        Each sub-menu function returns a list of menu items, only the menu()
        function must return a layout class instance.
    """

    # -------------------------------------------------------------------------
    @classmethod
    def menu(cls):
        """ Compose Menu """

        main_menu = MM()(

            # Modules-menu, align-left
            cls.menu_modules(),

            # Service menus, align-right
            # Note: always define right-hand items in reverse order!
            cls.menu_help(right=True),
            cls.menu_auth(right=True),
            #cls.menu_lang(right=True),
            cls.menu_admin(right=True),
            cls.menu_gis(right=True)
        )
        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        has_role = current.auth.s3_has_role

        if has_role("ADMIN"):
            return [
                homepage(),
                MM("Users", c="admin", f="user"),
                MM("Master Data", link=False)(
                    M("Locations", c="gis", f="location"),
                    M("Demographics", c="stats", f="demographic_data"),
                    M("Organizations", c="org", f="organisation"),
                    M("Disasters", c="event", f="event"),
                    M("Documents", c="doc", f="document"),
                    M("Photos", c="doc", f="image"),
                    M("Items", c="supply", f="distribution_item"),
                    M("Staff", c="hrm", f="human_resource"),
                    M("Beneficiaries", c="dvr", f="case"),
                ),
                MM("Assessments", c="dc", f="collection", m="summary")(
                    M("Table", m="list"),
                    M("Report", m="report"),
                    M("Map", m="map"),
                ),
                MM("Projects", c="project", f="project")(
                    M("Report", m="report"),
                    M("Map", m="map"),
                ),
                MM("Activities", c="project", f="activity")(
                    M("Report", m="report"),
                    M("Map", m="map"),
                ),
                MM("SitReps", c="doc", f="sitrep")(
                    M("Report", m="report"),
                    M("Map", m="map"),
                ),
                homepage("gis"),
            ]
        elif has_role("HUM_MANAGER"):
            # Manage Projects
            return [
                homepage(),
                MM("Calendar", c="project", f="activity", m="report"),
                MM("Assessments", c="dc", f="collection"),
                MM("Projects", c="project", f="project"),
                MM("4W", c="project", f="activity", m="summary"),
                MM("SitReps", c="doc", f="sitrep"),
                MM("Documents", c="doc", f="document"),
                homepage("gis"),
            ]
        elif has_role("LOGISTICS"):
            # Manage Distributions inc Beneficiary Registration
            return [
                homepage(),
                M("Distributions", c="project", f="distribution"),
                M("Beneficiaries", c="dvr", f="case"),
                homepage("gis"),
            ]
        elif has_role("ERT_LEADER"):
            # Field Operations
            return [
                homepage(),
                MM("Assessments", c="dc", f="collection"),
                MM("SitReps", c="doc", f="sitrep"),
                MM("Documents", c="doc", f="document"),
                MM("Activities", c="project", f="activity"),
                homepage("gis"),
            ]
        elif has_role("AUTHENTICATED"):
            # SC Staff inc Senior Managers
            return [
                homepage(),
                MM("Assessments", c="dc", f="collection", m="summary"),
                MM("SitReps", c="doc", f="sitrep"),
                MM("4W", c="project", f="activity", m="summary"),
                homepage("gis"),
            ]
        else:
            # Anonymous - can just see 4W (& external SitReps?)
            return [
                homepage(),
                homepage("gis"),
                M("4W", c="project", f="activity", m="summary"),
                MM("SitReps", c="doc", f="sitrep"),
            ]

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """
        Custom Controller Menus

        The options menu (left-hand options menu) is individual for each
        controller, so each controller has its own options menu function
        in this class.

        Each of these option menu functions can be customised separately,
        by simply overriding (re-defining) the default function. The
        options menu function must return an instance of the item layout.

        The standard menu uses the M item layout class, but you can of
        course also use any other layout class which you define in
        layouts.py (can also be mixed).

        Make sure additional helper functions in this class don't match
        any current or future controller prefix (e.g. by using an
        underscore prefix).
    """

    def dvr(self):
        """ Beneficiary Registration """

        return M(c="dvr")(
                    M("Beneficiaries", f="person")(
                        M("Create", m="create"),
                     ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def event():
        """ EVENT / Event Module """

        return M()(
                    M("Disasters", c="event", f="event")(
                        M("Create", m="create"),
                    ),
                    M("Disaster Types", c="event", f="event_type")(
                        M("Create", m="create"),
                        M("Import", m="import", p="create"),
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
                    M("Organization Types", f="organisation_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Sectors", f="sector", restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def project():
        """ PROJECT / Project Tracking & Management """

        has_role = current.auth.s3_has_role

        if has_role("ADMIN"):
            return M(c="project")(
                     M("Projects", f="project")(
                        M("Create", m="create"),
                     ),
                     M("Locations", f="location")(
                        # Better created from tab (otherwise Activity Type filter won't work)
                        #M("Create", m="create"),
                        M("Map", m="map"),
                     ),
                     M("Activities", f="activity")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                     ),
                     M("Reports", f="location", m="report")(
                        M("3W", f="location", m="report"),
                        M("Beneficiaries", f="beneficiary", m="report"),
                        M("Funding", f="organisation", m="report"),
                     ),
                     M("Import", f="project", m="import", p="create")(
                        M("Import Projects", m="import", p="create"),
                        M("Import Project Organizations", f="organisation",
                          m="import", p="create"),
                        M("Import Project Locations", f="location",
                          m="import", p="create"),
                     ),
                     M("Partner Organizations",  f="partners")(
                        M("Create", m="create"),
                        M("Import", m="import", p="create"),
                     ),
                     M("Beneficiary Types", f="beneficiary_type")(
                        M("Create", m="create"),
                     ),
                 )
        elif has_role("HUM_MANAGER"):
            # Manage Projects
            return M(c="project")(
                     M("Projects", f="project")(
                        M("Create", m="create"),
                     ),
                     M("Project Locations", f="location")(
                        # Better created from tab (otherwise Activity Type filter won't work)
                        #M("Create", m="create"),
                        M("Map", m="map"),
                     ),
                     M("Activities", f="activity")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                     ),
                     M("Reports", f="location", m="report")(
                        M("3W", f="location", m="report"),
                        M("Beneficiaries", f="beneficiary", m="report"),
                        M("Funding", f="organisation", m="report"),
                     ),
                 )
        elif has_role("LOGISTICS"):
            # Manage Distributions inc Beneficiary Registration
            return M(c="project")(
                     M("Distributions", f="distribution")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                     ),
                 )
        elif has_role("ERT_LEADER"):
            # Field Operations
            return M(c="project")(
                     M("Activities", f="activity")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                     ),
                     M("Reports", f="location", m="report")(
                        M("3W", f="location", m="report"),
                        M("Beneficiaries", f="beneficiary", m="report"),
                        M("Funding", f="organisation", m="report"),
                     ),
                 )
        elif has_role("AUTHENTICATED"):
            # SC Staff inc Senior Managers
            return M(c="project")(
                     M("Projects", f="project"),
                     M("Activities", f="activity")(
                        M("Map", m="map"),
                     ),
                     M("Reports", f="location", m="report")(
                        M("3W", f="location", m="report"),
                        M("Beneficiaries", f="beneficiary", m="report"),
                        M("Funding", f="organisation", m="report"),
                     ),
                 )
        else:
            # Anonymous - can just see 4W
            return M(c="project")(
                     M("Activities", f="activity")(
                        M("Map", m="map"),
                     ),
                     M("Reports", f="location", m="report")(
                        M("3W", f="location", m="report"),
                        M("Beneficiaries", f="beneficiary", m="report"),
                        M("Funding", f="organisation", m="report"),
                     ),
                 )

# END =========================================================================
