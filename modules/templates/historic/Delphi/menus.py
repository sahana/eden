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

    # -------------------------------------------------------------------------
    @staticmethod
    def delphi():
        """ DELPHI / Delphi Decision Maker """

        #ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="delphi")(
                    M("Active Problems", f="problem")(
                        M("Create", m="create"),
                    ),
                    M("Groups", f="group")(
                        M("Create", m="create"),
                    ),
                    #M("Solutions", f="solution"),
                    #M("Administration", restrict=[ADMIN])(
                        #M("Groups", f="group"),
                        #M("Group Memberships", f="membership"),
                        #M("Problems", f="problem"),
                    #)
                )

# END =========================================================================
