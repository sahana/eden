# -*- coding: utf-8 -*-

from gluon import current
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
    def menu(cls):
        """ Compose Menu """

        if current.auth.s3_logged_in():
            main_menu = MM()(
                # Note: always define right-hand items in reverse order!
                cls.menu_auth(right = True),
                cls.menu_lang(right = True),
                cls.menu_modules(right = True),
                #cls.menu_admin(right = True),
                )
        else:
            main_menu = MM()(
                # Note: always define right-hand items in reverse order!
                cls.menu_auth(right = True),
                #cls.menu_lang(right = True),
                cls.menu_modules(right = True),
                #cls.menu_admin(right = True),
                )

        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls, **attr):
        """ Custom Modules Menu """

        menu= [MM("Evidence", c="cms", f="page", vars={"name": "Evidence"}, **attr)(
               ),
               ]

        return menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_auth(cls, **attr):
        """ Auth Menu """

        auth = current.auth
        logged_in = auth.is_logged_in()
        settings = current.deployment_settings

        if not logged_in:
            request = current.request
            login_next = URL(args=request.args, vars=request.vars)
            if request.controller == "default" and \
               request.function == "user" and \
               "_next" in request.get_vars:
                login_next = request.get_vars["_next"]

            #self_registration = settings.get_security_registration_visible()
            #if self_registration == "index":
            #    register = MM("Register", c="default", f="index", m="register",
            #                   vars={"_next": login_next}),
            #                   check=self_registration)
            #else:
            #    register = MM("Register", m="register",
            #                   vars={"_next": login_next},
            #                   check=self_registration)

            #if settings.get_auth_password_changes() and \
            #   settings.get_auth_password_retrieval():
            #    lost_pw = MM("Lost Password", m="retrieve_password")
            #else:
            #    lost_pw = None

            menu_auth = MM("My Account", c="default", f="user", m="login",
                           _id="auth_menu_login",
                           vars={"_next": login_next}, **attr)(
                                #MM("Login", m="login",
                                #   vars={"_next": login_next}),
                                #register,
                                #lost_pw,
                                )
        else:
            # Logged-in

            if settings.get_auth_password_changes():
                change_pw = MM("Change password", m="change_password")
            else:
                change_pw = None

            menu_auth = MM("My Account", c="default", f="user", link=False,
                           **attr)(
                            MM("Dashboard", c="project", f="project", m="datalist"),
                            MM("User profile", m="profile"),
                            change_pw,
                            MM("Log out", m="logout", _id="auth_menu_logout"),
                        )

        return menu_auth

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """ Custom Controller Menus """

    # -------------------------------------------------------------------------
    @staticmethod
    def ucce():
        """ UCCE Side Menu """

        return M()(M("Projects", c="project", f="project", m="datalist", icon="folder-alt")(
                     #M("Create", m="create"),
                       ),
                   M("Reports", c="dc", f="target", m="datalist", icon="reports")(
                     #restrict=[ADMIN])(
                     #M("Create", m="create"),
                     ),
                   M("Guides", c="doc", f="document", m="datalist", icon="file-text-alt")(
                     #restrict=[ADMIN])(
                     #M("Create", m="create"),
                     ),
                   )

    # -------------------------------------------------------------------------
    def default(self):
        """ Default Controller """

        request = current.request
        if request.function == "user" and \
           request.args(0) in ("change_password", "profile"):
            return self.ucce()
        else:
            return None

    # -------------------------------------------------------------------------
    def doc(self):
        """ Documents Module """

        return self.ucce()

    # -------------------------------------------------------------------------
    def dc(self):
        """ Data Collection Module """

        return self.ucce()

    # -------------------------------------------------------------------------
    def project(self):
        """ Projects Module """

        return self.ucce()

# END =========================================================================
