# -*- coding: utf-8 -*-

from gluon import current
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
            MM("Contacts", c="hrm", f="staff")(
            ),                
            MM("Facilities", c="org", f="facility", m="summary",
               restrict=[AUTHENTICATED])(
            ),
            MM("News", c="cms", f="newsfeed", args="datalist",
               icon="icon-news",
               restrict=[AUTHENTICATED]),
            MM("Map", c="gis", f="index",
               icon="icon-map",
               restrict=[AUTHENTICATED]
               ),
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
                    M("Contacts", c="hrm", f="staff")(
                        M("View"),
                        M("Create", m="create"),
                    ),
                    M("Organizations", c="org", f="organisation")(
                        M("View"),
                        M("Create", m="create",
                          restrict=[AUTHENTICATED]),
                    ),
                    M("Groups", c="hrm", f="group")(
                        M("View"),
                        M("Create", m="create"),
                    ),
                    M("Networks", c="org", f="group")(
                        M("View"),
                        M("Create", m="create"),
                    ),
                    M("Your Personal Profile", c="default", f="person",
                      m="update")(
                    ),
                    M("Import", link=False,
                      restrict=[ADMIN])(
                        M("Import Contacts", c="hrm", f="person", m="import",
                          vars={"group":"staff"}),
                        M("Import Organizations", c="org", f="organisation",
                          m="import"),
                        M("Import Groups", c="hrm", f="group", m="import"),
                    ),
                    M("Organization Types", c="org", f="organisation_type",
                      restrict=[ADMIN])(
                        M("View"),
                        M("Create", m="create"),
                    ),
                    M("Job Title Catalog", c="hrm", f="job_title",
                      restrict=[ADMIN])(
                        M("View"),
                        M("Create", m="create"),
                    ),
                    M("Skills Catalog", c="hrm", f="skill",
                      restrict=[ADMIN])(
                        M("View"),
                        M("Create", m="create"),
                    ),
                    M("Organization Approval", c="org", f="organisation",
                      m="review", restrict=[ADMIN])(
                    ),
                )

    # -------------------------------------------------------------------------
    def org(self):
        """ ORG / Organization Registry """

        if not current.auth.is_logged_in():
            # No Side Menu
            return None
        else:
            request = current.request
            function = request.function
            if function in ("facility", "facility_type"):
                ADMIN = current.session.s3.system_roles.ADMIN
                if function == "facility" and request.args(0) == "summary":
                    LIST = M("List", _onclick="$('#ui-id-1').click()")
                    MAP = M("Map", _onclick="$('#ui-id-3').click()")
                    REPORT = M("Report", _onclick="$('#ui-id-2').click()")
                else:
                    LIST = M("List", m="summary")
                    MAP = M("Map", m="summary", vars={"t":2})
                    REPORT = M("Report", m="summary", vars={"t":1})
                return M()(
                        M("Create a Facility", c="org", f="facility", m="create")(
                        ),
                        M("View Facilities", c="org", f="facility", m="summary")(
                            LIST,
                            MAP,
                            REPORT,
                        ),
                        M("Import Facilities", c="org", f="facility", m="import",
                          restrict=[ADMIN])(
                        ),
                        M("Facility Types", c="org", f="facility_type",
                          restrict=[ADMIN])(
                            M("View"),
                            M("Create", m="create"),
                        ),
                    )
            else:
                # organisation, organisation_type or hrm
                return self.hrm()

    # -------------------------------------------------------------------------
    def pr(self):
        """ Person Registry """

        if not current.auth.is_logged_in():
            # No Side Menu
            return None
        else:
            return self.hrm()

# END =========================================================================
