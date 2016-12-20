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
    """
        Custom Main Menu
    """

    # -------------------------------------------------------------------------
    @classmethod
    def menu(cls):

        main_menu = MM()(

            # Modules-menu, align-left
            cls.menu_modules(),

            # Service menus, align-right
            # Note: always define right-hand items in reverse order!
            cls.menu_lang(right=True),
            #cls.menu_gis(right=True),
            cls.menu_auth(right=True),
            cls.menu_admin(right=True),
            cls.menu_help(right=True),
        )

        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        person_id = current.auth.s3_logged_in_person()
        if person_id:
            dashboard = MM("Dashboard", c="pr", f="person",
                           args=[person_id, "dashboard"])
        else:
            dashboard = None

        return [#homepage(),
                #MM("Feed", c="cms", f="newsfeed", m="datalist",
                #   icon = "news",
                #   ),
                dashboard,
                MM("Map", c="gis", f="index"),
                #MM("Dashboard", c="event", f="event", m="summary"),
                MM("Incidents", c="event", f="incident", m="summary"),
                #MM("Alerts", c="event", f="alert", m="summary"),
                MM("Events", c="event", f="event", m="summary"),
                #MM("Tasks", c="project", f="task", m="summary"),
                MM("Resources", c="pr", f="group", m="summary"),
                #MM("Contacts", c="hrm", f="staff", m="summary"),
                MM("More", link=False)(
                   MM("Fire Stations", c="fire", f="station"),
                   MM("Police Stations", c="police", f="station"),
                   ),
                ]

    # -------------------------------------------------------------------------
    @classmethod
    def menu_help(cls, **attr):
        """ Custom Help Menu """

        menu_help = MM("About", f="about", **attr)

        return menu_help

    # -------------------------------------------------------------------------
    @classmethod
    def menu_auth(cls, **attr):
        """ Auth Menu """

        auth = current.auth
        logged_in = auth.is_logged_in()

        if not logged_in:
            request = current.request
            login_next = URL(args=request.args, vars=request.vars)
            if request.controller == "default" and \
               request.function == "user" and \
               "_next" in request.get_vars:
                login_next = request.get_vars["_next"]

            self_registration = current.deployment_settings.get_security_registration_visible()
            if self_registration == "index":
                register = MM("Register", c="default", f="index", m="register",
                               vars=dict(_next=login_next),
                               check=self_registration)
            else:
                register = MM("Register", m="register",
                               vars=dict(_next=login_next),
                               check=self_registration)

            menu_auth = MM("Login", c="default", f="user", m="login",
                           _id="auth_menu_login",
                           vars=dict(_next=login_next), **attr)(
                            MM("Login", m="login",
                               vars=dict(_next=login_next)),
                            register,
                            MM("Lost Password", m="retrieve_password")
                        )
        else:
            # Logged-in
            menu_auth = MM(auth.user.email, c="default", f="user",
                           translate=False, link=False, _id="auth_menu_email",
                           **attr)(
                            MM("User Profile", m="profile"),
                            #MM("Personal Data", c="default", f="person", m="update"),
                            #MM("Contact Details", c="pr", f="person",
                            #    args="contact",
                            #    vars={"person.pe_id" : auth.user.pe_id}),
                            #MM("Subscriptions", c="pr", f="person",
                            #    args="pe_subscription",
                            #    vars={"person.pe_id" : auth.user.pe_id}),
                            MM("Change Password", m="change_password"),
                            MM("Logout", m="logout", _id="auth_menu_logout"),
                            #SEP(),
                            #MM({"name": current.T("Rapid Data Entry"),
                            #   "id": "rapid_toggle",
                            #   "value": current.session.s3.rapid_data_entry is True},
                            #   f="rapid"),
                        )

        return menu_auth

    # -------------------------------------------------------------------------
    @classmethod
    def menu_lang(cls, **attr):
        """ Language Selector """

        s3 = current.response.s3

        menu_lang = ML("Language", **attr)
        for language in s3.l10n_languages.items():
            code, name = language
            menu_lang(
                ML(name, translate=False, lang_code=code, lang_name=name)
            )
        return menu_lang

# END =========================================================================
