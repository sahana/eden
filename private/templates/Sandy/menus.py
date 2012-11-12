# -*- coding: utf-8 -*-

from gluon import *
from s3 import *
from eden.layouts import *
try:
    from .layouts import *
except ImportError:
    pass
import eden.menus as default

# =============================================================================
class S3MainMenu(default.S3MainMenu):
    # -------------------------------------------------------------------------
    @classmethod
    def menu_help(cls, **attr):
        """ Help Menu """

        menu_help = MM("Help", c="default", f="help", **attr)(
            MM("Contact us", f="contact"),
            MM("Terms of Service", f="tos"),
            MM("About", f="about")
        )
        return menu_help

# END =========================================================================
