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
    def project(self):
        """ PROJECT / Project Tracking & Management """

        menu = M(c="project")(
            M("Projects", f="project")(
                M("New", m="create"),
                M("List All"),
                M("Map", f="location", m="map"),
                M("Search", m="search"),
            ),
            M("Reports", f="location", m="report2")(
                M("3W", f="location", m="report2"),
                M("Beneficiaries", f="beneficiary", m="report2"),
                M("Funding", f="organisation", m="report2"),
            ),
            M("Import", f="project", m="import", p="create")(
                M("Import Projects", m="import", p="create"),
                M("Import Project Organizations", f="organisation",
                  m="import", p="create"),
                M("Import Project Locations", f="location",
                  m="import", p="create"),
            ),
            M("Partner Organizations",  f="partners")(
                M("New", m="create"),
                M("List All"),
                M("Search", m="search"),
                M("Import", m="import", p="create"),
            ),
            M("Themes", f="theme")(
                M("New", m="create"),
                M("List All"),
            ),
            M("Activity Types", f="activity_type")(
                M("New", m="create"),
                M("List All"),
                #M("Search", m="search")
            ),
            M("Beneficiary Types", f="beneficiary_type")(
                M("New", m="create"),
                M("List All"),
            ),
            M("Demographics", f="demographic")(
                M("New", m="create"),
                M("List All"),
            ),
        )

        return menu

# END =========================================================================
