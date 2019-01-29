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

        auth = current.auth

        if auth.s3_has_role("MANAGER"):
            return [MM("Organizations", c="org", f="organisation",
                       ),
                    MM("Contacts", c="hrm", f="staff",
                       ),
                    MM("Facilities", c="org", f="facility",
                       ),
                    MM("Map", c="gis", f="index",
                       #icon="icon-map",
                       ),
                    ]
        elif auth.s3_logged_in():
            return [MM("Dashboard", c="default", f="index",
                       args=["dashboard"],
                       ),
                    ]

    # -------------------------------------------------------------------------
    @classmethod
    def menu_help(cls, **attr):
        """ Help Menu """

        menu_help = [MM("Contact", f="contact", **attr),
                     MM("Help", c="default", f="help", **attr),
                     ]

        return menu_help

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

    @staticmethod
    def howcalm():
        """ Side menu for all of HowCalm """

        auth = current.auth

        if not auth.s3_logged_in():
            return None

        if auth.s3_has_role("MANAGER"):
            return M()(M("Manage", showlink=False)(
                        M("My Organizations", c="org", f="organisation", vars={"mine": 1}),
                        M("My Contacts", c="hrm", f="staff", vars={"mine": 1}),
                        M("My Facilities", c="org", f="facility", vars={"mine": 1}),
                        ),
                       M("Create", showlink=False)(
                         M("Organization", c="org", f="organisation", m="create"),
                         M("Contact", c="hrm", f="staff", m="create"),
                         M("Facility", c="org", f="facility", m="create"),
                         ),
                       )
        else:
            return M()(M("Manage", showlink=False)(
                        M("My Personal Profile", c="hrm", f="staff", vars={"mine": 1}),
                        M("My Organizations", c="org", f="organisation", vars={"mine": 1}),
                        M("My Facilities", c="org", f="facility", vars={"mine": 1}),
                        ),
                       )

    # -------------------------------------------------------------------------
    def default(self):
        """ Home page """

        return self.howcalm()

    # -------------------------------------------------------------------------
    def hrm(self):
        """ Organisation Registry """

        return self.howcalm()

    # -------------------------------------------------------------------------
    def org(self):
        """ Organisation Registry """

        return self.howcalm()

# END =========================================================================
