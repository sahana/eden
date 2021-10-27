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
    def menu_modules(cls):
        """ Custom Modules Menu """

        menu= [MM("Call Logs", c="event", f="incident_report"),
               MM("Incidents", c="event", f="incident", m="summary"),
               MM("Scenarios", c="event", f="scenario"),
               MM("more", link=False)(
                MM("Documents", c="doc", f="document"),
                MM("Events", c="event", f="event"),
                MM("Staff", c="hrm", f="staff"),
                MM("Volunteers", c="vol", f="volunteer"),
                MM("Assets", c="asset", f="asset"),
                MM("Organizations", c="org", f="organisation"),
                MM("Facilities", c="org", f="facility"),
                #MM("Hospitals", c="med", f="hospital", m="summary"),
                MM("Shelters", c="cr", f="shelter"),
                MM("Warehouses", c="inv", f="warehouse"),
                MM("Item Catalog", c="supply", f="catalog_item"),
                ),
               ]

        return menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_auth(cls, **attr):
        """
            Auth Menu
            - switch Login to use OpenID Connect
        """

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

            self_registration = settings.get_security_registration_visible()
            if self_registration == "index":
                register = MM("Register", c="default", f="index", m="register",
                               vars=dict(_next=login_next),
                               check=self_registration)
            else:
                register = MM("Register", m="register",
                               vars=dict(_next=login_next),
                               check=self_registration)

            if settings.get_auth_password_changes() and \
               settings.get_auth_password_retrieval():
                lost_pw = MM("Lost Password", m="retrieve_password")
            else:
                lost_pw = None

            menu_auth = MM("Login", c="default", f="openid_connect", m="login",
                           _id="auth_menu_login",
                           vars=dict(_next=login_next), **attr)(
                                MM("Login", m="login",
                                   vars=dict(_next=login_next)),
                                register,
                                lost_pw,
                                )
        else:
            # Logged-in

            if settings.get_auth_password_changes():
                change_pw = MM("Change Password", m="change_password")
            else:
                change_pw = None

            menu_auth = MM(auth.user.email, c="default", f="user",
                           translate=False, link=False, _id="auth_menu_email",
                           **attr)(
                            MM("Logout", m="logout", _id="auth_menu_logout"),
                            MM("User Profile", m="profile"),
                            MM("Personal Data", c="default", f="person", m="update"),
                            MM("Contact Details", c="pr", f="person",
                                args="contact",
                                vars={"person.pe_id" : auth.user.pe_id}),
                            #MM("Subscriptions", c="pr", f="person",
                            #    args="pe_subscription",
                            #    vars={"person.pe_id" : auth.user.pe_id}),
                            change_pw,
                            SEP(),
                            MM({"name": current.T("Rapid Data Entry"),
                               "id": "rapid_toggle",
                               "value": current.session.s3.rapid_data_entry is True},
                               f="rapid"),
                        )

        return menu_auth

# END =========================================================================
