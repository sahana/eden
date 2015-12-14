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

        #sysname = current.deployment_settings.get_system_name_short()
        return [
            homepage(),
            MM("Case Management", c=("dvr", "pr")),
            #homepage("gis"),
            homepage("org"),
            homepage("hrm"),
            #homepage("cr"),
        ]
    # -------------------------------------------------------------------------
    @classmethod
    def menu_help(cls, **attr):
        """ Help Menu """

        menu_help = MM("Help", c="default", f="help", **attr)(
            MM("Contact us", f="contact"),
            MM("About Us", f="about"),
        )
        return menu_help

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """ Custom Application Side Menu """

    # -------------------------------------------------------------------------
    @staticmethod
    def dvr():
        """ DVR / Disaster Victim Registry """

        return M(c="dvr")(
                    M("Cases", c=("dvr", "pr"), f="person")(
                        M("Create", m="create"),
                        M("Archived Cases", vars={"archived": "1"}),
                    ),
                    M("Case Types", f="case_type")(
                        M("Create", m="create"),
                    ),
                    M("Need Types", f="need")(
                       M("Create", m="create"),
                    ),
                    M("Housing Types", f="housing_type")(
                       M("Create", m="create"),
                    ),
                    M("Income Sources", f="income_source")(
                      M("Create", m="create"),
                    ),
                    M("Beneficiary Types", f="beneficiary_type")(
                       M("Create", m="create"),
                    ),
                )

# END =========================================================================
