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
class S3OptionsMenu(default.S3OptionsMenu):
    """
        Custom Controller Menus

        The options menu (left-hand options menu) is individual for each
        controller, so each controller has its own options menu function
        in this class.

        Each of these option menu functions can be customized separately,
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
    def org(self):
        """ ORG / Organization Registry """

        #ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="org")(
                    M("Facilities", f="facility")(
                        M("New", m="create"),
                        M("List All"),
                        M("Map", m="map"),
                        M("Search", m="search"),
                        M("Import", m="import")
                    ),
                    M("Organizations", f="organisation")(
                        M("Add Organization", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", m="import")
                    ),
                    M("Facility Types", f="facility_type",
                      #restrict=[ADMIN]
                      )(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Organization Types", f="organisation_type",
                      #restrict=[ADMIN]
                      )(
                        M("New", m="create"),
                        M("List All"),
                    ),
                )

# END =========================================================================
