# -*- coding: utf-8 -*-

from gluon import current
from s3 import *
from s3layouts import *
try:
    from .layouts import *
except ImportError:
    pass
import s3menus as default

class S3MainMenu(default.S3MainMenu):
    """
        Custom Application Main Menu:

        The main menu consists of several sub-menus, each of which can
        be customised separately as a method of this class. The overall
        composition of the menu is defined in the menu() method, which can
        be customised as well:

        Function        Sub-Menu                Access to (standard)

        menu_modules()  the modules menu        the Eden modules
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
    def menu_modules(cls):
        """ Custom Modules Menu """

        AUTHENTICATED = current.session.s3.system_roles.AUTHENTICATED

        INDIVIDUALS = current.deployment_settings.get_hrm_staff_label()

        return [
            MM("Dashboard", c="default", f="index",
               args=["dashboard"],
               restrict=[AUTHENTICATED],
               ),
            MM("Contacts", link=False, restrict=[AUTHENTICATED])(
                MM("Networks", c="org", f="group"),
                MM("Groups", c="hrm", f="group"),
                MM("Organizations", c="org", f="organisation"),
                MM(INDIVIDUALS, c="hrm", f="staff"),
            ),
            MM("Facilities", c="org", f="facility", m="summary",
               restrict=[AUTHENTICATED])(
            ),
            MM("Services", c="cms", f="page", vars={"name": "Services"}),
            MM("News", c="cms", f="newsfeed", m="datalist",
               #icon="icon-news",
               restrict=[AUTHENTICATED],
               ),
            MM("Map", c="gis", f="index",
               #icon="icon-map",
               restrict=[AUTHENTICATED],
               ),
            MM("Data", c="cms", f="page", vars={"name": "Data"}),
            MM("Get Involved", link=False)(
                MM("Events",
                   url="http://nycprepared.org/events",
                   _target="_blank",
                   ),
                MM("Learn more",
                   url="http://nycprepared.org",
                   _target="_blank",
                   ),
                MM("Donate",
                   url="https://sarapis.org/donate-to-nycprepared",
                   _target="_blank",
                   ),
            ),
        ]

    # -------------------------------------------------------------------------
    @classmethod
    def menu_help(cls, **attr):
        """ Help Menu """

        ADMIN = current.auth.get_system_roles().ADMIN

        menu_help = MM("Help", c="default", f="help", link=False, **attr)(
            MM("User Guide", f="help"),
            MM("Contact us", f="contact"),
            #MM("About", f="about", restrict=[ADMIN]),
        )

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
                           translate=False,
                           link=False,
                           _id="auth_menu_email",
                           **attr)(
                            MM("Logout", m="logout", _id="auth_menu_logout"),
                            #MM("User Profile", m="profile"),
                            MM("Personal Profile", c="default", f="person", m="update"),
                            #MM("Contact Details", c="pr", f="person",
                            #    args="contact",
                            #    vars={"person.pe_id" : auth.user.pe_id}),
                            #MM("Subscriptions", c="pr", f="person",
                            #    args="pe_subscription",
                            #    vars={"person.pe_id" : auth.user.pe_id}),
                            MM("Change Password", m="change_password"),
                            SEP(),
                            MM({"name": current.T("Rapid Data Entry"),
                                "id": "rapid_toggle",
                                "value": current.session.s3.rapid_data_entry is True,
                                },
                               f="rapid",
                               ),
                        )

        return menu_auth

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
    def hrm():
        """ HRM / Human Resources Management """

        s3 = current.session.s3
        ADMIN = s3.system_roles.ADMIN
        AUTHENTICATED = s3.system_roles.AUTHENTICATED

        INDIVIDUALS = current.deployment_settings.get_hrm_staff_label()

        return M()(
                    M("Networks", c="org", f="group")(
                        M("Search"),
                        M("Create", m="create"),
                    ),
                    M("Groups", c="hrm", f="group")(
                        M("Search"),
                        M("Create", m="create"),
                    ),
                    M("Organizations", c="org", f="organisation")(
                        M("Search"),
                        M("Create", m="create",
                          restrict=[AUTHENTICATED]),
                    ),
                    M(INDIVIDUALS, c="hrm", f="staff", t="hrm_human_resource")(
                        M("Search"),
                        M("Create", m="create"),
                    ),
                    M("Your Personal Profile", c="default", f="person",
                      m="update")(
                    ),
                    M("Import", link=False,
                      restrict=[ADMIN])(
                        M("Import Contacts", c="hrm", f="person", m="import",
                          vars={"group":"staff"}),
                        M("Import Organizations", c="org", f="organisation",
                          m="import"),
                        M("Import Groups", c="hrm", f="group", m="import"),
                    ),
                    M("Organization Types", c="org", f="organisation_type",
                      restrict=[ADMIN])(
                        M("View"),
                        M("Create", m="create"),
                    ),
                    M("Job Title Catalog", c="hrm", f="job_title",
                      restrict=[ADMIN])(
                        M("View"),
                        M("Create", m="create"),
                    ),
                    M("Skills Catalog", c="hrm", f="skill",
                      restrict=[ADMIN])(
                        M("View"),
                        M("Create", m="create"),
                    ),
                    M("Organization Approval", c="org", f="organisation",
                      m="review", restrict=[ADMIN])(
                    ),
                )

    # -------------------------------------------------------------------------
    def org(self):
        """ ORG / Organization Registry """

        if not current.auth.is_logged_in():
            # No Side Menu
            return None
        else:
            request = current.request
            function = request.function
            if function in ("facility", "facility_type"):
                ADMIN = current.session.s3.system_roles.ADMIN
                if function == "facility" and request.args(0) == "summary":
                    LIST = M("List", _onclick="$('#ui-id-1').click()")
                    MAP = M("Map", _onclick="$('#ui-id-3').click()")
                    REPORT = M("Report", _onclick="$('#ui-id-2').click()")
                else:
                    LIST = M("List", m="summary")
                    MAP = M("Map", m="summary", vars={"t":2})
                    REPORT = M("Report", m="summary", vars={"t":1})
                return M()(
                        M("Create a Facility", c="org", f="facility", m="create")(
                        ),
                        M("View Facilities", c="org", f="facility", m="summary")(
                            LIST,
                            MAP,
                            REPORT,
                        ),
                        M("Import Facilities", c="org", f="facility", m="import",
                          restrict=[ADMIN])(
                        ),
                        M("Facility Types", c="org", f="facility_type",
                          restrict=[ADMIN])(
                            M("View"),
                            M("Create", m="create"),
                        ),
                    )
            else:
                # organisation, organisation_type or hrm
                return self.hrm()

    # -------------------------------------------------------------------------
    def pr(self):
        """ Person Registry """

        if not current.auth.is_logged_in():
            # No Side Menu
            return None
        else:
            return self.hrm()

# END =========================================================================
