# -*- coding: utf-8 -*-

from gluon import current, URL
from s3 import IS_ISO639_2_LANGUAGE_CODE
from s3layouts import M, MM
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
    def menu(cls):
        """ Compose Menu """

        main_menu = MM()(

            # Modules-menu, align-left
            cls.menu_modules(),

            # Service menus, align-right
            # Note: always define right-hand items in reverse order!
            cls.menu_help(right = True),
            #cls.menu_lang(right = True),
            #cls.menu_gis(right = True),
            cls.menu_auth(right = True),
            cls.menu_admin(right = True),
        )

        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        if not current.auth.is_logged_in():
            menu = []
        else:
            menu = [MM("Requests", c="req", f="req", m="summary")(),
                    MM("Facilities", c="org", f="facility", m="summary")(
                       MM("Airports", c="transport", f="airport", m="summary"),
                       MM("Facilities", c="org", f="facility", m="summary"),
                       MM("Fire Stations", c="fire", f="station", m="summary"),
                       MM("Hospitals", c="hms", f="hospital", m="summary"),
                       MM("Offices", c="org", f="office", m="summary"),
                       MM("Warehouses", c="inv", f="warehouse", m="summary"),
                       ),
                    MM("Organisations", c="org", f="organisation", m="summary")(),
                    MM("Contacts", c="hrm", f="staff", m="summary")(),
                    MM("Map", c="gis", f="index")(),
                    ]

        return menu

# END =========================================================================
