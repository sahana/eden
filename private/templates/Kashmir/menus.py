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
    """ Custom Application Main Menu """

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        sysname = current.deployment_settings.get_system_name_short()
        return [
            homepage(name=sysname),
            homepage("gis"),
            homepage("org"),
            homepage("hrm"),
            homepage("inv"),
            homepage("cr"),
            homepage("req"),
            homepage("vol"),
            homepage("project"),
       ]

# END =========================================================================
