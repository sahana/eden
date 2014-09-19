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

        return [
            homepage(name="ATHEWAAS"),
            homepage("gis"),
            homepage("org"),
            homepage("req"),
            homepage("inv"),
            homepage("hrm"),
       ]

# END =========================================================================
