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
        Custom Application Main Menu:

        The main menu consists of several sub-menus, each of which can
        be customised separately as a method of this class. The overall
        composition of the menu is defined in the menu() method, which can
        be customised as well:

        Function        Sub-Menu                Access to (standard)

        menu_modules()  the modules menu        the Eden modules
        menu_gis()      the GIS menu            GIS configurations
        menu_admin()    the Admin menu          System/User Administration
        menu_lang()     the Language menu       Selection of the GUI locale
        menu_auth()     the User menu           Login, Logout, User Profile
        menu_help()     the Help menu           Contact page, About page

        The standard uses the MM layout class for main menu items - but you
        can of course use a custom layout class which you define in layouts.py.

        Additional sub-menus can simply be defined as additional functions in
        this class, and then be included in the menu() method.

        Each sub-menu function returns a list of menu items, only the menu()
        function must return a layout class instance.
    """

    # -------------------------------------------------------------------------
    @classmethod
    def menu(cls):
        """ Compose Menu """

        main_menu = MM()(

            cls.menu_modules(),
            cls.menu_lang(right=True),
            cls.menu_auth(),
            cls.menu_admin(),
        )

        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        auth = current.auth
        has_role = auth.s3_has_role
        alert_hub_menu = MM("Alert Hub", c="default", f="index",
                            args=["alert_hub_cop"])
        if auth.s3_logged_in():
            alerting_menu = MM("Alerts", c="cap", f="alert")
            mapping_menu = MM("Map", c="gis", f="index")
            recipient_menu = MM("Recipients", c="pr", f="subscription",
                                vars={"option": "manage_recipient"})

            if has_role("ADMIN"):
                # Full set
                # @ToDo: Add menu entries for "Create RSS Feed for CAP" & "Create RSS Feed for CMS"
                return [homepage(),
                        alerting_menu,
                        alert_hub_menu,
                        MM("Organizations", c="org", f="organisation"),
                        MM("Persons", c="pr", f="person"),
                        recipient_menu,
                        mapping_menu,                                                
                        ]
            else:
                # Publisher sees minimal options
                menus_ = [homepage(),
                          alerting_menu,
                          alert_hub_menu,
                          ]

                if has_role("MAP_ADMIN"):
                    menus_.append(mapping_menu)
                else:
                    return menus_

                return menus_

        # Public or CUG reader sees minimal options
        return [homepage(),
                alert_hub_menu,
                ]

    # -------------------------------------------------------------------------
    @classmethod
    def menu_auth(cls, **attr):
        """ Auth Menu """

        auth = current.auth

        if not auth.is_logged_in():
            menu_auth = MM("Login", link=False, right=True)(
                           MM("Login", c="default", f="user", m="login",
                              vars={"_next": URL(c="cap", f="alert")}),
                           MM("Lost Password", c="default", f="user",
                              m="retrieve_password"),
                           MM("Request for Account", c="default", f="user",
                              m="register"),
                        )
        else:
            # Logged-in
            user_id = auth.s3_logged_in_person()                
            menu_auth = MM(auth.user.email, link=False, right=True)(
                           MM("Subscription", c="pr", f="subscription"),
                           MM("Edit Profile", c="pr", f="person", args=[user_id]),
                           MM("Change Password", c="default", f="user",
                              m="change_password"),
                           MM("Logout", c="default", f="user", m="logout"),
                        )

        return menu_auth

    # -------------------------------------------------------------------------
    @classmethod
    def menu_admin(cls, **attr):
        """ Administrator Menu """

        if current.auth.s3_has_role("ADMIN"):
            name_nice = current.deployment_settings.modules["admin"].name_nice
            menu_admin = MM(name_nice, c="admin", right=True, **attr)(
                            MM("Settings", f="setting"),
                            MM("Manage Users", f="user"),
                            MM("Database", c="appadmin", f="index"),
                            MM("Error Tickets", f="errors"),
                            #MM("Synchronization", c="sync", f="index"),
                         )
        else:
            menu_admin = None

        return menu_admin

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
    def admin(self):
        """ ADMIN menu """

        ADMIN = current.session.s3.system_roles.ADMIN
        settings_messaging = self.settings_messaging()

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
                    ),
                    M("Database", c="appadmin", f="index")(
                        M("Raw Database access", c="appadmin", f="index")
                    ),
                    M("Error Tickets", c="admin", f="errors")
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def cap():
        """ CAP menu """

        if current.request.get_vars["~.external"] == "True":
            # Alert Hub
            return M(c="cap")(
                        M("Alert Hub", f="alert", vars={"~.external": True})(
                            M("Map View", c="default",
                              f="index", args=["alert_hub_cop"]),
                        ),
                    )
        else:
            s3_has_role = current.auth.s3_has_role
            cap_editors = lambda i: s3_has_role("ALERT_EDITOR") or \
                                    s3_has_role("ALERT_APPROVER")
            return M(c="cap", check=cap_editors)(
                        M("Alerts", f="alert")(
                            M("Create", m="create", check=cap_editors),
                            M("Import from Feed URL", m="import_feed", p="create",
                              check=cap_editors),
                            M("To Review", c="cap", f="alert", m="review",
                              check=s3_has_role("ALERT_APPROVER")),
                        ),
                        M("View", check=cap_editors)(
                            M("Approved Alerts", c="cap", f="alert",
                              vars={"~.approved_by__ne": None},
                              ),
                            M("Incomplete Alerts", c="cap", f="alert", m="review",
                              vars={"status": "incomplete"}
                              ),
                            M("Archived Alerts/ Alert History", c="cap",
                              f="alert_history", restrict=["ADMIN"]
                              ),
                        ),
                        M("Templates", f="template")(
                            M("Create", m="create",
                              restrict=["ADMIN"]),
                        ),
                        M("Warning Classifications", f="warning_priority",
                          restrict=["ADMIN"])(
                            M("Create", m="create"),
                            M("Import from CSV", m="import", p="create"),
                        ),
                        M("Predefined Alert Area", f="area", vars={"~.is_template": True},
                          restrict=["ADMIN"])(
                            M("Create", m="create"),
                            M("Import from CSV", m="import", p="create"),
                        ),
                        M("Event Types", c="event", f="event_type",
                          restrict=["ADMIN"])(
                            M("Create", m="create"),
                            M("Import from CSV", m="import", p="create"),
                        ),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def org():
        """ ORG / Organization Registry """

        return M(c="org")(
                    M("Organizations", f="organisation")(
                        M("Create", m="create"),
                        M("Import", m="import")
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def pr():
        """ PR / Person Registry """

        ADMIN = current.session.s3.system_roles.ADMIN

        if current.request.vars.option == "manage_recipient":
            return M(c="pr", restrict=ADMIN)(
                        M("Manage Recipients", f="subscription",
                              vars={"option": "manage_recipient"})(
                            M("Add Recipient to List", c="default", f="index",
                              m="subscriptions", vars={"option": "manage_recipient"})
                        )
                    )
        else:
            return M(c="pr", restrict=ADMIN)(
                        M("Persons", f="person")(
                            M("Create", m="create"),
                        ),
                        M("Groups", f="group")(
                            M("Create", m="create"),
                        ),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def event():
        """ Events """

        return M(c="event")(
                    M("Event Types", f="event_type")(
                        M("Create", m="create"),
                        M("Import", m="import")
                    ),
                )

    # -------------------------------------------------------------------------
    @classmethod
    def settings_messaging(cls):
        """ Messaging settings menu items:

            These items are used in multiple menus, but each item instance can
            always only belong to one parent, so we need to re-instantiate
            with the same parameters, and therefore this is defined as a
            function here.

            This separates the RSS containing CAP Feeds or CMS Feeds
        """

        return [
            M("Email Channels (Inbound)", c="msg", f="email_channel"),
            M("Facebook Channels", c="msg", f="facebook_channel"),
            M("RSS Channels", link=False)(
                M("Create RSS Feed for CAP", c="msg", f="rss_channel", vars={"type": "cap"}),
                M("Create RSS Feed for CMS", c="msg", f="rss_channel"),
            ),
            M("SMS Outbound Gateways", c="msg", f="sms_outbound_gateway")(
                M("SMS Modem Channels", c="msg", f="sms_modem_channel"),
                M("SMS SMTP Channels", c="msg", f="sms_smtp_channel"),
                M("SMS WebAPI Channels", c="msg", f="sms_webapi_channel"),
            ),
            #M("Mobile Commons Channels", c="msg", f="mcommons_channel"),
            #M("Twilio Channels", c="msg", f="twilio_channel"),
            M("Twitter Channels", c="msg", f="twitter_channel"),
            M("Parsers", c="msg", f="parser"),
        ]

# END =========================================================================
