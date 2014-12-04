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
            homepage("event", f="incident_report"),
            homepage("org"),
            homepage("hrm"),
            homepage("inv"),
            homepage("cr"),
            homepage("req"),
            homepage("vol"),
            homepage("project"),
        ]
    # -------------------------------------------------------------------------
    @classmethod
    def menu_help(cls, **attr):
        """ Help Menu """

        menu_help = MM("Help", c="default", f="help", **attr)(
            MM("Contact us", f="contact"),
            MM("About Us", f="about"),
            MM("User Guide", f="index/userguide"),
        )
        return menu_help
# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """ Custom Application Side Menu """

    # -------------------------------------------------------------------------
    @staticmethod
    def event():
        """ EVENT / Event Module """

        return M()(
                    M("Incident Reports", c="event", f="incident_report")(
                        M("Create", m="create"),
                    ),
                )
        
# END =========================================================================
