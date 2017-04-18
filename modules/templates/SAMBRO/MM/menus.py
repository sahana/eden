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

    @staticmethod
    def cap():
        """ CAP menu """

        s3_has_role = current.auth.s3_has_role
        cap_editors = lambda i: s3_has_role("ALERT_EDITOR") or \
                                s3_has_role("ALERT_APPROVER")

        return M(c="cap")(
                    M("Manage Recipients",
                      c="pr",
                      f="subscription",
                      vars={"option": "manage_recipient"},
                      check=cap_editors,
                      ),
                    M("Manage Recipient Groups",
                      c="pr",
                      f="group",
                      check=cap_editors,
                      ),
                    M("Alerts", f="alert",
                      check=cap_editors)(
                        M("Create", m="create"),
                        M("Import from Feed URL", m="import_feed", p="create",
                          check=cap_editors),
                    ),
                    M("Templates", f="template")(
                        M("Create", m="create",
                          check=cap_editors),
                    ),
                    M("Warning Priorities", f="warning_priority",
                      restrict=["ADMIN"])(
                        M("Create", m="create"),
                        M("Import from CSV", m="import", p="create"),
                    ),
                    M("Predefined Alert Area", f="area", vars={"~.is_template": True},
                      restrict=["ADMIN"])(
                        M("Create", m="create"),
                        M("Import from CSV", m="import", p="create"),
                    ),
                )

# END =========================================================================
