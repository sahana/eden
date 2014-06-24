# -*- coding: utf-8 -*-

from gluon import *
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
    def menu(cls):
        """ Compose Menu """

        main_menu = MMO()(

            # Align left
            MM()(
                # Home link
                HM(),
                # Modules
                cls.menu_modules()
            ),

            # Service menus, align-right
            MM(right=True)(
                cls.menu_admin(),
                #cls.menu_gis()
                cls.menu_lang(),
                cls.menu_auth(),
                cls.menu_help(),
            ),
        )
        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        AUTHENTICATED = current.session.s3.system_roles.AUTHENTICATED

        return [
            MM("News", c="cms", f="newsfeed", args="datalist",
               icon="icon-news"),
            MM("Map", c="gis", f="index",
               icon="icon-map"),
            MM("Projects", c="project", f="project"),
            MM("Requests", c="req", f="req")(
                MM("Fulfill Requests", f="req"),
                MM("Request Supplies", f="req", m="create", vars={"type": 1}),
                MM("Request People", f="req", m="create", vars={"type": 3})
            ),
            MM("Locations", c="org", f="facility", m="summary",
               restrict=[AUTHENTICATED])(
                MM("Facilities", c="org", f="facility", m="summary"),
                MM("Create a Facility", c="org", f="facility", m="create")
            ),
            MM("Contacts", c="hrm", f="staff")(
                MM("People", c="hrm", f="staff"),
                MM("Groups", c="hrm", f="group"),
                MM("Organizations", c="org", f="organisation"),
                #MM("People Registry", c="pr", f="index")
            ),                
            MM("Networks", c="org", f="group")(
                #MM("Networks", c="org", f="group"),
                #MM("Organizations", c="org", f="organisation"),
            ),                
            MM("Resources", c="inv", f="index")(
                MM("Assets", c="asset", f="asset"),
                MM("Inventory", c="inv", f="inv_item"),
                MM("Stock Counts", c="inv", f="adj"),
                MM("Shipments", c="inv", f="send")
            ),
             MM("Cases", c="assess", f="building")(
                MM("Building Assessments", f="building"),
                MM("Canvass", f="canvass"), 
            ),  
            MM("Survey", c="survey")(
                MM("Templates", f="template"),
                MM("Assessments", f="series"),
                MM("Import Templates", f="question_list", m="import"),
            ),
        ]

    # -------------------------------------------------------------------------
    @classmethod
    def menu_help(cls, **attr):
        """ Help Menu """

        menu_help = MM("Help", c="default", f="help",
                       icon="icon-question-sign", **attr
                       )(
            MM("Contact us", f="contact"),
            MM("About", f="about")
        )

        # -------------------------------------------------------------------
        # Now add the available guided tours to the help menu

        # check that a guided_tour is enabled
        if current.deployment_settings.get_base_guided_tour():
            # load the guided tour configuration from the database
            table = current.s3db.tour_config
            logged_in = current.auth.is_logged_in()
            if logged_in:
                query = (table.deleted == False) &\
                        (table.role != "")
            else:
                query = (table.deleted == False) &\
                        (table.role == "")
            tours = current.db(query).select(table.id,
                                             table.name,
                                             table.controller,
                                             table.function,
                                             table.role,
                                             )
            if len(tours) > 0:
                menu_help.append(SEP())
            for row in tours:
                menu_help.append(MM(row.name,
                                    c=row.controller,
                                    f=row.function,
                                    vars={"tour":row.id},
                                    restrict=row.role
                                    )
                                 )

        return menu_help

    # -------------------------------------------------------------------------
    @classmethod
    def menu_auth(cls, **attr):
        """ Auth Menu """

        auth = current.auth
        logged_in = auth.is_logged_in()

        if not logged_in:
            self_registration = current.deployment_settings.get_security_self_registration()
            request = current.request
            login_next = URL(args=request.args, vars=request.vars)
            if request.controller == "default" and \
               request.function == "user" and \
               "_next" in request.get_vars:
                login_next = request.get_vars["_next"]

            menu_auth = MM("Login", c="default", f="user", m="login",
                           icon="icon-signin",
                           _id="auth_menu_login",
                           vars=dict(_next=login_next), **attr)(
                            MM("Login", m="login",
                               vars=dict(_next=login_next)),
                            MM("Register", f="index", m="register",
                               vars=dict(_next=login_next),
                               check=self_registration),
                            MM("Lost Password", m="retrieve_password")
                        )
        else:
            # Logged-in
            filter_manager = current.deployment_settings.get_search_filter_manager()
            user = auth.user
            menu_auth = MM(user.email, c="default", f="user",
                           translate=False, link=False, _id="auth_menu_email",
                           **attr)(
                            MM("Logout", m="logout", _id="auth_menu_logout",
                               icon="icon-off",
                               ),
                            MM("Profile", c="default", f="person", m="update",
                               icon="icon-user",
                               ),
                            MM("Saved Filters", c="pr", f="filter", m="datalist",
                               vars={"~.pe_id": user.pe_id},
                               icon="icon-filter",
                               ),
                            MM("Change Password", m="change_password",
                               icon="icon-lock",
                               ),
                            # @ToDo:
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
        """ Language Menu """

        settings = current.deployment_settings
        if not settings.get_L10n_display_toolbar():
            return None

        s3 = current.response.s3
        languages = s3.l10n_languages
        lang = s3.language
        request = current.request

        menu_lang = MM("Language", icon="icon-comment-alt", **attr)
        for language in languages:
            menu_lang.append(MM(languages[language], r=request,
                                translate=False,
                                vars={"_language": language},
                                ltr=True,
                                icon="icon-check" if language == lang else "icon-check-empty"
                                ))
        return menu_lang

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
        db = current.db
        SUPER = lambda i: \
            db(db.auth_group.uuid=="super").select(db.auth_group.id,
                                                   limitby=(0, 1),
                                                   cache=s3db.cache
                                                   ).first().id

        # Custom conditions for the check-hook, as lambdas in order
        # to have them checked only immediately before rendering:
        def hrm_vars():
            if not s3.hrm:
                if current.auth.is_logged_in():
                    current.s3db.hrm_vars()
                else:
                    s3.hrm = Storage(mode="personal")
            return True
        manager_mode = lambda i: hrm_vars() and s3.hrm.mode is None
        personal_mode = lambda i: hrm_vars() and s3.hrm.mode is not None
        is_org_admin = lambda i: hrm_vars() and s3.hrm.orgs or \
                                 ADMIN in s3.roles
        settings = current.deployment_settings
        teams = settings.get_hrm_teams()
        use_teams = lambda i: teams

        return M()(
                    M(settings.get_hrm_staff_label(), c="hrm", f="staff",
                      check=manager_mode)(
                        M("Create", m="create"),
                        M("Import", f="person", m="import",
                          vars={"group":"staff"}, p="create"),
                    ),
                    M(teams, c="hrm", f="group",
                      check=[use_teams])(
                        M("Create", m="create"),
                    ),
                    M("Organizations", c="org", f="organisation")(
                        M("Create", m="create",
                          restrict=[AUTHENTICATED]),
                        M("Review/Approve New", m="review"),
                        M("Import", m="import",
                          restrict=[SUPER])
                    ),
                    M("Organization Types", c="org", f="organisation_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    #M("Department Catalog", c="hrm", f="department",
                    #  check=manager_mode)(
                    #    M("Create", m="create"),
                    #),
                    M("Job Title Catalog", c="hrm", f="job_title",
                      check=manager_mode)(
                        M("Create", m="create"),
                    ),
                    M("Skill Catalog", c="hrm", f="skill",
                      check=manager_mode)(
                        M("Create", m="create"),
                        #M("Skill Provisions", f="skill_provision"),
                    ),
                    M("Personal Profile", c="hrm", f="person",
                      check=personal_mode, vars=dict(mode="personal")),
                    # This provides the link to switch to the manager mode:
                    M("Staff Management", c="hrm", f="index",
                      check=[personal_mode, is_org_admin]),
                    # This provides the link to switch to the personal mode:
                    M("Personal Profile", c="hrm", f="person",
                      check=manager_mode, vars=dict(mode="personal"))
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def inv():
        """ INV / Inventory """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M()(
                    M("Facilities", c="inv", f="facility", m="summary")(
                        M("Create", m="create"),
                        M("Import", m="import")
                    ),
                    M("Warehouse Stock", c="inv", f="inv_item")(
                        #M("Search Shipped Items", f="track_item"),
                        M("Stock Count", f="adj"),
                        #M("Kitting", f="kit"),
                        M("Import", f="inv_item", m="import", p="create"),
                    ),
                    M("Reports", c="inv", f="inv_item")(
                        M("Warehouse Stock", f="inv_item",m="report"),
                        M("Expiration Report", c="inv", f="track_item",
                          vars=dict(report="exp")),
                        #M("Monetization Report", c="inv", f="inv_item",
                        #  vars=dict(report="mon")),
                        #M("Utilization Report", c="inv", f="track_item",
                        #  vars=dict(report="util")),
                        #M("Summary of Incoming Supplies", c="inv", f="track_item",
                        #  vars=dict(report="inc")),
                        #M("Summary of Releases", c="inv", f="track_item",
                        #  vars=dict(report="rel")),
                    ),
                    #M(inv_recv_list, c="inv", f="recv")(
                    #    M("Create", m="create"),
                    #),
                    M("Sent Shipments", c="inv", f="send")(
                        M("Create", m="create"),
                        M("Search Shipped Items", f="track_item"),
                    ),
                    M("Items", c="supply", f="item")(
                        M("Create", m="create"),
                        M("Report", m="report"),
                        M("Import", f="catalog_item", m="import", p="create"),
                    ),
                    M("Item Categories", c="supply", f="item_category",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    def org(self):
        """ ORG / Organization Registry """

        fn = current.request.function
        if fn  == "group":
            return M()(
                    M("Networks", c="org", f="group")(
                        M("Create", m="create"),
                    ),
                )
        elif fn in ("facility", "facility_type"):
            ADMIN = current.session.s3.system_roles.ADMIN
            return M()(
                   M("Facilities", c="org", f="facility", m="summary")(
                        M("Create", m="create"),
                        #M("Review/Approve New", m="review"),
                        M("Import", m="import")
                    ),
                    M("Facility Types", c="org", f="facility_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                )
        else:
            # organisation, organisation_type or hrm
            return self.hrm()

    # -------------------------------------------------------------------------
    def pr(self):
        """ Person Registry """

        return self.hrm()

    # -------------------------------------------------------------------------
    @staticmethod
    def project():
        """ PROJECT / Project Tracking & Management """

        return M(c="project")(
                    M("Projects", f="project")(
                        M("Create", m="create"),
                        M("Import", m="import", p="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def req():
        """ REQ / Request Management """

        db = current.db
        SUPER = lambda i: \
            db(db.auth_group.uuid=="super").select(db.auth_group.id,
                                                   limitby=(0, 1),
                                                   cache=s3db.cache
                                                   ).first().id

        return M(c="req")(
                    M("Requests", f="req")(
                        M("Request Supplies", m="create", vars={"type": 1}),
                        M("Request People", m="create", vars={"type": 3}),
                        M("Fulfill Requests"),
                        M("List Recurring Requests", f="req_template"),
                        #M("Map", m="map"),
                        M("Report", m="report"),
                        M("FEMA Items Required", f="fema",
                          restrict=[SUPER]),
                        M("Search All Requested Items", f="req_item"),
                        M("Search All Requested Skills", f="req_skill"),
                    ),
                    #M("Priority Items", f="summary_option")(
                    #    M("Create", m="create"),
                    #),
                    M("Commitments", f="commit")(
                    ),
                    M("Sent Shipments", f="send")(
                        #M("Create", m="create"),
                        #M("Search Shipped Items", f="track_item"),
                    ),
                    M("Items", c="supply", f="item",
                      restrict=[SUPER])(
                        M("Create", m="create"),
                        M("Report", m="report"),
                        M("Import", f="catalog_item", m="import", p="create"),
                    ),
                    M("Item Categories", c="supply", f="item_category",
                      restrict=[SUPER])(
                        M("Create", m="create"),
                    ),
                )

# END =========================================================================
