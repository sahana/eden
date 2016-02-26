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
    def menu_modules(cls):
        """ Custom Modules Menu """

        return [
            homepage(),
            homepage("gis"),
            M("Organizations", c="org", f="organisation", m="summary")(),
            M("Resources", c="org", f="resource", m="summary")(),
            M("Volunteers", c="vol", f="volunteer", m="summary")(),
            M("Needs", c="req", f="organisation_needs")(),
            M("Projects", c="project", f="project", m="summary")(),
            M("Incident Reports", c="event", f="incident_report")(),
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

    # -------------------------------------------------------------------------
    @staticmethod
    def org():
        """ ORG / Organization Registry """

        settings = current.deployment_settings
        ADMIN = current.session.s3.system_roles.ADMIN
        SECTORS = "Clusters" if settings.get_ui_label_cluster() \
                             else "Sectors"
        #stats = lambda i: settings.has_module("stats")

        return M(c="org")(
                    M("Organizations", f="organisation", m="summary")(
                        M("Create", m="create"),
                        M("Import", m="import")
                    ),
                    M("Offices", f="office")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        M("Import", m="import")
                    ),
                    M("Resources", f="resource", m="summary",
                      #check=stats
                      )(
                        M("Create", m="create"),
                        M("Import", m="import")
                    ),
                    M("Organization Needs", c="req", f="organisation_needs")(
                        M("Create", m="create"),
                        M("Import", m="import", restrict=[ADMIN]),
                    ),
                    M("Organization Types", f="organisation_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Facilities", f="facility", m="summary")(
                        M("Create", m="create"),
                        M("Import", m="import"),
                    ),
                    M("Facility Needs", c="req", f="site_needs")(
                        M("Create", m="create"),
                        M("Import", m="import", restrict=[ADMIN]),
                    ),
                    #M("Office Types", f="office_type",
                    #  restrict=[ADMIN])(
                    #    M("Create", m="create"),
                    #),
                    M("Facility Types", f="facility_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M(SECTORS, f="sector", restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    def req(self):
        """ REQ / Request Management """

        return self.org()

    # -------------------------------------------------------------------------
    @staticmethod
    def event():
        """ EVENT / Event Module """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M()(
                    M("Incident Reports", c="event", f="incident_report", m="summary")(
                        M("Create", m="create"),
                    ),
                    M("Incident Types", c="event", f="incident_type", restrict=[ADMIN])(
                        M("Create", m="create"),
                        M("Import", m="import", p="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def project():
        """ PROJECT / Project Tracking & Management """

        settings = current.deployment_settings
        #activities = lambda i: settings.get_project_activities()
        activity_types = lambda i: settings.get_project_activity_types()
        community = settings.get_project_community()
        if community:
            IMPORT = "Import Project Communities"
        else:
            IMPORT = "Import Project Locations"
        community_volunteers = lambda i: settings.get_project_community_volunteers()
        demographics = lambda i: settings.get_project_demographics()
        hazards = lambda i: settings.get_project_hazards()
        #indicators = lambda i: settings.get_project_indicators()
        programmes = lambda i: settings.get_project_programmes()
        sectors = lambda i: settings.get_project_sectors()
        stats = lambda i: settings.has_module("stats")
        themes = lambda i: settings.get_project_themes()

        menu = M(c="project")

        if settings.get_project_mode_3w():
            if community:
                menu(
                     M("Programs", f="programme",
                       check=programmes)(
                        M("Create", m="create"),
                     ),
                     M("Projects", f="project")(
                        M("Create", m="create"),
                     ),
                     M("Communities", f="location")(
                        # Better created from tab (otherwise Activity Type filter won't work)
                        #M("Create", m="create"),
                        M("Map", m="map"),
                        M("Community Contacts", f="location_contact"),
                        M("Community Volunteers", f="volunteer",
                          check=community_volunteers),
                     ),
                    )
            else:
                menu(
                     M("Programs", f="programme",
                       check=programmes)(
                        M("Create", m="create"),
                     ),
                     M("Projects", f="project")(
                        M("Create", m="create"),
                        M("Map", f="location", m="map"),
                     )
                    )
            menu(
                 M("Reports", f="location", m="report")(
                    M("3W", f="location", m="report"),
                    M("Beneficiaries", f="beneficiary", m="report",
                      check=stats,
                      ),
                    #M("Indicators", f="indicator", m="report",
                    #  check=indicators,
                    #  ),
                    #M("Indicators over Time", f="indicator", m="timeplot",
                    #  check=indicators,
                    #  ),
                    M("Funding", f="organisation", m="report"),
                 ),
                 M("Import", f="project", m="import", p="create")(
                    M("Import Projects", m="import", p="create"),
                    M("Import Project Organizations", f="organisation",
                      m="import", p="create"),
                    M(IMPORT, f="location",
                      m="import", p="create"),
                 ),
                 M("Partner Organizations",  f="partners")(
                    M("Create", m="create"),
                    M("Import", m="import", p="create"),
                 ),
                 M("Activity Types", f="activity_type",
                   check=activity_types)(
                    M("Create", m="create"),
                 ),
                 M("Beneficiary Types", f="beneficiary_type",
                   check=stats)(
                    M("Create", m="create"),
                 ),
                 M("Demographics", f="demographic",
                   check=demographics)(
                    M("Create", m="create"),
                 ),
                 M("Hazards", f="hazard",
                   check=hazards)(
                    M("Create", m="create"),
                 ),
                 #M("Indicators", f="indicator",
                 #  check=indicators)(
                 #   M("Create", m="create"),
                 #),
                 M("Sectors", f="sector",
                   check=sectors)(
                    M("Create", m="create"),
                 ),
                 M("Themes", f="theme",
                   check=themes)(
                    M("Create", m="create"),
                 ),
                )

        elif settings.get_project_mode_task():
            menu(
                 M("Projects", f="project")(
                    M("Create", m="create"),
                    M("Open Tasks for Project", vars={"tasks":1}),
                 ),
                 M("Tasks", f="task")(
                    M("Create", m="create"),
                 ),
                )
            if current.auth.s3_has_role("STAFF"):
                ADMIN = current.session.s3.system_roles.ADMIN
                menu(
                     M("Daily Work", f="time")(
                        M("My Logged Hours", vars={"mine":1}),
                        M("My Open Tasks", f="task", vars={"mine":1}),
                     ),
                     M("Admin", restrict=[ADMIN])(
                        M("Activity Types", f="activity_type"),
                        M("Import Tasks", f="task", m="import", p="create"),
                     ),
                     M("Reports", f="report")(
                        M("Activity Report", f="activity", m="report"),
                        M("Last Week's Work", f="time", m="report",
                          vars=Storage(rows="person_id",
                                       cols="day",
                                       fact="sum(hours)",
                                       week=1)),
                        M("Last Month's Work", f="time", m="report",
                          vars=Storage(rows="person_id",
                                       cols="week",
                                       fact="sum(hours)",
                                       month=1)),
                        M("Project Time Report", f="time", m="report"),
                     ),
                    )
        else:
            menu(
                 M("Projects", f="project")(
                    M("Create", m="create"),
                    M("Import", m="import", p="create"),
                 ),
                )

        return menu

# END =========================================================================
