# -*- coding: utf-8 -*-

from gluon import *
from s3 import *
from s3layouts import *
try:
    from .layouts import *
except ImportError:
    pass
import s3menus as default

class S3MainMenu(default.S3MainMenu):
    """
        Custom Application Main Menu:

        The main menu consists of several sub-menus, each of which can
        be customised separately as a method of this class. The overall
        composition of the menu is defined in the menu() method, which can
        be customised as well:

        Function        Sub-Menu                Access to (standard)

        menu_modules()  the modules menu        the Eden modules
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

        AUTHENTICATED = current.session.s3.system_roles.AUTHENTICATED

        return [
            MM("Contacts", c="org", f="index")(
            ),                
            MM("Facilities", c="org", f="facility", m="summary",
               restrict=[AUTHENTICATED])(
            ),
            MM("News", c="cms", f="newsfeed", args="datalist",
               icon="icon-news"),
            MM("Map", c="gis", f="index",
               icon="icon-map"),
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
    def hrm():
        """ HRM / Human Resources Management """

        s3 = current.session.s3
        ADMIN = s3.system_roles.ADMIN
        AUTHENTICATED = s3.system_roles.AUTHENTICATED

        return M()(
                    M("Contacts", c="hrm", f="staff",
                      check=manager_mode)(
                        M("Create", m="create"),
                        M("View"),
                        M("Import", f="person", m="import",
                          vars={"group":"staff"}, p="create"),
                    ),
                    M("Organizations", c="org", f="organisation")(
                        M("Create", m="create",
                          restrict=[AUTHENTICATED]),
                        M("View"),
                        M("Import", m="import",
                          restrict=[SUPER])
                    ),
                    M("Groups", c="hrm", f="group")(
                        M("Create", m="create"),
                        M("View"),
                    ),
                    M("Networks", c="org", f="group")(
                        M("Create", m="create"),
                        M("View"),
                    ),
                    M("Your Personal Profile", c="default", f="person",
                      m="update",
                      ),
                    M("Organization Types", c="org", f="organisation_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                        M("View"),
                    ),
                    M("Job Title Catalog", c="hrm", f="job_title",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                        M("View"),
                    ),
                    M("Skills Catalog", c="hrm", f="skill",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                        M("View"),
                        #M("Skill Provisions", f="skill_provision"),
                    ),
                    M("Organization Approval", c="org", f="organisation",
                      m="review",
                      restrict=[ADMIN])(
                        M("Review/Approve New", m="review"),
                    ),
                )

    # -------------------------------------------------------------------------
    def org(self):
        """ ORG / Organization Registry """

        if current.request.function in ("facility", "facility_type"):
            ADMIN = current.session.s3.system_roles.ADMIN
            return M()(
                   M("Facilities", c="org", f="facility", m="summary")(
                        M("Create", m="create"),
                        M("View"),
                    ),
                    M("Import Facilities", c="org", f="facility", m="import",
                      restrict=[ADMIN])(
                        M("Import", m="import"),
                    ),
                    M("Facility Types", c="org", f="facility_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                        M("View"),
                    ),
                )
        else:
            # organisation, organisation_type or hrm
            return self.hrm()

    # -------------------------------------------------------------------------
    def pr(self):
        """ Person Registry """

        return self.hrm()

# END =========================================================================
