# -*- coding: utf-8 -*-

from gluon import current
from s3 import *
from eden.layouts import *
try:
    from .layouts import *
except ImportError:
    pass
import eden.menus as default

# =============================================================================
class S3MainMenu(default.S3MainMenu):
    """ Custom Application Main Menu """

    # -------------------------------------------------------------------------
    @classmethod
    def menu(cls):
        """ Compose Menu """

        # Modules menus
        main_menu = MM()(
            cls.menu_modules(),
        )

        # Additional menus
        current.menu.top = cls.menu_top()

        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        return [
            MM("Home", c="default", f="index"),
            MM("Project List", c="project", f="project", m="search"),
            MM("Project Analysis", c="default", f="index", args="analysis"),
            MM("Regional Organizations", c="default", f="index", args="organisations"),
            MM("DRR Frameworks", c="project", f="framework"),
            MM("My Page", c="default", f="index", args="mypage"),
        ]

    # -------------------------------------------------------------------------
    @classmethod
    def menu_top(cls, **attr):
        """ Custom Top Menu """

        auth = current.auth

        if not auth.is_logged_in():
            self_registration = current.deployment_settings.get_security_self_registration()
            request = current.request
            login_next = URL(args=request.args, vars=request.vars)
            if request.controller == "default" and \
               request.function == "user" and \
               "_next" in request.get_vars:
                login_next = request.get_vars["_next"]

            menu_top = MT()(
                    MT("Login", c="default", f="user", m="login",
                       _id="auth_menu_login",
                       vars=dict(_next=login_next), **attr),
                    MT("Register", c="default", f="index", args="register"),
                    MT("About", c="default", f="index", args="about"),
                    MT("User Manual", c="static", f="DRR_Portal_User_Manual.pdf"),
                    MT("Contact", c="default", f="index", args="contact"),
                )
        else:
            # Logged-in
            user = auth.user
            welcome = "Welcome %s %s" % (user.first_name, user.last_name)

            menu_top = MT()(
                    MT(welcome, c="default", f="user",
                       translate=False, link=False, _id="auth_menu_email",
                       **attr),
                    MT("Logout", c="default", f="user", args="logout", _id="auth_menu_logout"),
                    MT("About", c="default", f="index", args="about"),
                    MT("User Manual", c="static", f="DRR_Portal_User_Manual.pdf"),
                    MT("Contact", c="default", f="index", args="contact"),
                )

        return menu_top

# END =========================================================================
