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
        Custom Main Menu
    """

    # -------------------------------------------------------------------------
    @classmethod
    def menu(cls):

        main_menu = MM()(

            # Modules-menu, align-left
            cls.menu_modules(),

            # Service menus, align-right
            # Note: always define right-hand items in reverse order!
            cls.menu_help(right=True),
            #cls.menu_lang(right=True),
            cls.menu_gis(right=True),
            cls.menu_auth(right=True),
            cls.menu_admin(right=True),
        )

        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        return [#homepage(),
                MM("Feed", c="cms", f="newsfeed", m="datalist",
                   icon = "news",
                   ),
                MM("Map", c="gis", f="index"),
                MM("Dashboard", c="event", f="event", m="summary"),
                MM("Incidents", c="event", f="incident", m="summary"),
                MM("Resources", c="org", f="resource", m="summary"),
                MM("Events", c="event", f="event"),
                ]

# END =========================================================================
