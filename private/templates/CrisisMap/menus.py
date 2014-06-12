# -*- coding: utf-8 -*-

from gluon import *
from s3 import *
from s3layouts import *
try:
    from .layouts import *
except ImportError:
    pass
import s3menus as default

# Below is an example which you can base your own template's menus.py on
# - there are also other examples in the other templates folders

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
            homepage(name="Crisis Map"),
            homepage("gis", name = "Map"),
#           homepage("evr")(
#                 MM("Persons", f="person"),
#                 MM("Groups", f="group")
#              ),
#           homepage("cr"),
#           homepage("msg"),
#           homepage("msg"),
            homepage("project"),
            homepage("req"),
            homepage("event")(
                  MM("Incidents", c="event", f="incident"),
                  MM("Events", c="event", f="event")
            ),
            #Do not use irs, it will be depreceated soon   homepage("irs"),
            homepage("vol"),
            homepage("hrm")
            #MM("more", link=False)(
            #),
       ]

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    #"""
        #Custom Controller Menus

        #The options menu (left-hand options menu) is individual for each
        #controller, so each controller has its own options menu function
        #in this class.

        #Each of these option menu functions can be customised separately,
        #by simply overriding (re-defining) the default function. The
        #options menu function must return an instance of the item layout.

        #The standard menu uses the M item layout class, but you can of
        #course also use any other layout class which you define in
        #layouts.py (can also be mixed).

        #Make sure additional helper functions in this class don't match
        #any current or future controller prefix (e.g. by using an
        #underscore prefix).
    #"""

    # -------------------------------------------------------------------------
    def evr(self):
        """ EVR / Evacuees Registry """

        return M(c="evr")(
                    M("Persons", f="person")(
                        M("New", m="create"),
                        M("Import", m="import")
                    ),
                    M("Groups", f="group")(
                        M("New", m="create"),
                    ),
                )

# END =========================================================================
