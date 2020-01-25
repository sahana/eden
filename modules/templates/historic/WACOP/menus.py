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

        return [dashboard,
                MM("Map", c="gis", f="index"),
                MM("Incidents", c="event", f="incident", m="browse"),
                MM("Events", c="event", f="event", m="browse"),
                MM("Resources", c="pr", f="group", m="browse"),
                MM("Groups", c="pr", f="forum", m="browse"),
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

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """ Custom Application Side Menu """

    # -------------------------------------------------------------------------
    def admin(self):
        """ ADMIN menu """

        ADMIN = current.session.s3.system_roles.ADMIN
        settings_messaging = self.settings_messaging()
        #translate = current.deployment_settings.has_module("translate")

        # NB: Do not specify a controller for the main menu to allow
        #     re-use of this menu by other controllers
        return M(restrict=[ADMIN])(
                    M("Settings", c="admin", f="setting")(
                        settings_messaging,
                    ),
                    M("User Management", c="admin", f="user")(
                        M("Create User", m="create"),
                        M("List All Users"),
                        M("Import Users", m="import"),
                        M("List All Roles", f="role"),
                        M("List All Organization Approvers & Whitelists", f="organisation"),
                        #M("Roles", f="group"),
                        #M("Membership", f="membership"),
                    ),
                    M("Database", c="appadmin", f="index")(
                        M("Raw Database access", c="appadmin", f="index"),
                    ),
                    M("Error Tickets", c="admin", f="errors"),
                    M("Synchronization", c="sync", f="index")(
                        M("Settings", f="config", args=[1], m="update"),
                        M("Repositories", f="repository"),
                        M("Log", f="log"),
                    ),
                    M("Taxonomies")(
                        #M("Event Types", c="event", f="event_type"),
                        M("Incident Types", c="event", f="incident_type"),
                        M("Organization Types", c="org", f="organisation_type"),
                        M("Update Statuses", c="cms", f="status"),
                    ),
                    #M("Edit Application", a="admin", c="default", f="design",
                      #args=[request.application]),
                    #M("Translation", c="admin", f="translate", check=translate)(
                    #   M("Select Modules for translation", c="admin", f="translate",
                    #     m="create", vars=dict(opt="1")),
                    #   M("Upload translated files", c="admin", f="translate",
                    #     m="create", vars=dict(opt="2")),
                    #   M("View Translation Percentage", c="admin", f="translate",
                    #     m="create", vars=dict(opt="3")),
                    #   M("Add strings manually", c="admin", f="translate",
                    #     m="create", vars=dict(opt="4"))
                    #),
                    #M("View Test Result Reports", c="admin", f="result"),
                    #M("Portable App", c="admin", f="portable")
                )

# END =========================================================================
