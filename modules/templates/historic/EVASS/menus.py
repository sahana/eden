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

        return [homepage(name="EVASS"),
                homepage("gis"),
                homepage("org"),
                homepage("msg"),
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
    def hrm(self):
        """ Staff """

        s3 = current.session.s3
        ADMIN = s3.system_roles.ADMIN

        # Custom conditions for the check-hook, as lambdas in order
        # to have them checked only immediately before rendering:
        is_org_admin = lambda i: s3.hrm.orgs and True or \
                                 ADMIN in s3.roles
        settings = current.deployment_settings
        teams = settings.get_hrm_teams()
        use_teams = lambda i: teams
        vol_enabled = lambda i: settings.has_module("vol")

        return M(c="hrm")(
                    M(settings.get_hrm_staff_label(), f="staff", m="summary")(
                        M("Create", m="create"),
                        M("Search by Skills", f="competency"),
                        M("Import", f="person", m="import",
                          vars={"group":"staff"}, p="create"),
                    ),
                    M("Staff & Volunteers (Combined)",
                      c="hrm", f="human_resource", m="summary", check=vol_enabled),
                    M(teams, f="group", check=use_teams)(
                        M("Create", m="create"),
                        M("Search Members", f="group_membership"),
                        M("Import", f="group_membership", m="import"),
                    ),
                    M("Department Catalog", f="department")(
                        M("Create", m="create"),
                    ),
                    M("Job Title Catalog", f="job_title")(
                        M("Create", m="create"),
                    ),
                    M("Skill Catalog", f="skill")(
                        M("Create", m="create"),
                        #M("Skill Provisions", f="skill_provision"),
                    ),
                    M("Reports", f="staff", m="report")(
                        M("Staff Report", m="report"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def vol():
        """ Volunteer Management """

        s3 = current.session.s3
        ADMIN = s3.system_roles.ADMIN

        # Custom conditions for the check-hook, as lambdas in order
        # to have them checked only immediately before rendering:
        is_org_admin = lambda i: s3.hrm.orgs and True or \
                                 ADMIN in s3.roles

        settings = current.deployment_settings
        show_programmes = lambda i: settings.get_hrm_vol_experience() == "programme"
        show_tasks = lambda i: settings.has_module("project") and \
                               settings.get_project_mode_task()
        teams = settings.get_hrm_teams()
        use_teams = lambda i: teams
        show_staff = lambda i: settings.get_hrm_show_staff()

        return M(c="vol")(
                    M("Volunteers", f="volunteer", m="summary")(
                        M("Create", m="create"),
                        M("Search by skills", f="competency"),
                        M("Import", f="person", m="import",
                          vars={"group":"volunteer"}, p="create"),
                    ),
                    M("Staff & Volunteers (Combined)",
                      c="vol", f="human_resource", m="summary", check=show_staff),
                    M(teams, f="group", check=use_teams)(
                        M("Create", m="create"),
                        M("Search Members", f="group_membership"),
                        M("Import", f="group_membership", m="import"),
                    ),
                    M("Department Catalog", f="department")(
                        M("Create", m="create"),
                    ),
                    M("Job Title Catalog", f="job_title")(
                        M("Create", m="create"),
                    ),
                    M("Volunteer Role Catalog", f="job_title")(
                        M("Create", m="create"),
                    ),
                    M("Skill Catalog", f="skill")(
                        M("Create", m="create"),
                        #M("Skill Provisions", f="skill_provision"),
                    ),
                    M("Programs", f="programme", check=show_programmes)(
                        M("Create", m="create"),
                        M("Import Hours", f="programme_hours", m="import"),
                    ),
                    M("Reports", f="volunteer", m="report")(
                        M("Volunteer Report", m="report"),
                        M("Hours by Role Report", f="programme_hours", m="report",
                          vars = {"rows": "job_title_id",
                                  "cols": "month",
                                  "fact": "sum(hours)",
                                  },
                          check = show_programmes,
                          ),
                        M("Hours by Program Report", f="programme_hours", m="report",
                          vars = {"rows": "programme_id",
                                  "cols": "month",
                                  "fact": "sum(hours)",
                                  },
                          check = show_programmes,
                          ),
                    ),
                )


#    -------------------------------------------------------------------------
    def evr(self):
        """ EVR / Evacuees Registry """

        return M(c="evr")(
                    M("Persons", f="person")(
                        M("New", m="create"),
                        M("Reports",m="report"),
                        M("Import", m="import")
                    ),
                    M("Groups", f="group")(
                        M("New", m="create"),
                    ),
                )

# END =========================================================================
