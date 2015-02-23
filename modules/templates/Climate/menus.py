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

        menu_climate()  Custom Menu

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
            cls.menu_climate(),
        )
        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_climate(cls, **attr):
        """ Climate module menu """

        name_nice = current.deployment_settings.modules["climate"].name_nice
        ADMIN = current.session.s3.system_roles.ADMIN

        menu_climate = MM(name_nice, c="climate", **attr)(
                MM("Station Parameters", f="station_parameter"),
                #MM("Saved Queries", f="save_query"),
                MM("Purchase Data", f="purchase"),
                MM("DataSet Prices", f="prices", restrict=[ADMIN]),
            )
        return menu_climate

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
    def climate(self):
        """ CLIMATE Controller """

        return M(c="climate")(
                    M("Home", f="index"),
                    M("Station Parameters", f="station_parameter"),
                    M("Saved Queries", f="save_query"),
                    M("Purchase Data", f="purchase"),
                )

# END =========================================================================