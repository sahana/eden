"""
    Custom Menus for DIRECT

    License: MIT
"""

from gluon import current, URL, TAG, SPAN
from core import IS_ISO639_2_LANGUAGE_CODE
from core.ui.layouts import MM, M, ML, MP, MA

try:
    from .layouts import OM
except ImportError:
    pass
import core.ui.menus as default

# =============================================================================
class MainMenu(default.MainMenu):
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
        current.menu.personal = cls.menu_personal()
        current.menu.lang = cls.menu_lang()
        current.menu.about = cls.menu_about()
        current.menu.org = cls.menu_org()

        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Modules Menu """

        # ORG menu to match CMS for newsletter functions only
        request = current.request
        is_newsletter = request.controller == "cms" and \
                        request.function in ("newsletter", "read_newsletter")
        org_c = ("org", "hrm", "act", "cms") if is_newsletter else ("org", "hrm", "act")

        menu = [MM("Needs", c="req", f="need"),
                MM("Assets", c="asset", f="asset"),
                MM("Inventory", c="inv", f="warehouse"),
                MM("Shelters", c="cr", f="shelter"),
                MM("Water Sources", c="water", f="index"),
                MM("Beneficiaries", c="dvr", f="person"),
                MM("Organizations", c=org_c, f=("organisation", "*")),
                ]

        return menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_org(cls):
        """ Organisation Logo and Name """

        #OM = OrgMenuLayout
        return OM()

    # -------------------------------------------------------------------------
    @classmethod
    def menu_lang(cls, **attr):
        """ Language Selector """

        languages = current.deployment_settings.get_L10n_languages()
        represent_local = IS_ISO639_2_LANGUAGE_CODE.represent_local

        menu_lang = ML("Language", right=True)

        for code in languages:
            # Show each language name in its own language
            lang_name = represent_local(code)
            menu_lang(
                ML(lang_name,
                   translate = False,
                   lang_code = code,
                   lang_name = lang_name,
                   )
            )

        return menu_lang

    # -------------------------------------------------------------------------
    @classmethod
    def menu_personal(cls):
        """ Personal Menu """

        auth = current.auth
        #s3 = current.response.s3
        settings = current.deployment_settings

        sr = current.auth.get_system_roles()
        ADMIN = sr.ADMIN

        if not auth.is_logged_in():
            request = current.request
            login_next = URL(args=request.args, vars=request.get_vars)
            if request.controller == "default" and \
               request.function == "user" and \
               "_next" in request.get_vars:
                login_next = request.get_vars["_next"]

            self_registration = settings.get_security_self_registration()
            menu_personal = MP()(
                        MP("Register", c="default", f="user",
                           m = "register",
                           check = self_registration,
                           ),
                        MP("Login", c="default", f="user",
                           m = "login",
                           vars = {"_next": login_next},
                           ),
                        )
            if settings.get_auth_password_retrieval():
                menu_personal(MP("Lost Password", c="default", f="user",
                                 m = "retrieve_password",
                                 ),
                              )
        else:
            has_role = auth.s3_has_role
            is_user_admin = lambda i: not has_role(ADMIN) and (
                                        has_role(sr.ORG_ADMIN, include_admin=False) or \
                                        has_role(sr.ORG_GROUP_ADMIN, include_admin=False)
                                        )
            menu_personal = MP()(
                        MP("Administration", c="admin", f="index",
                           restrict = ADMIN,
                           ),
                        MP("Administration", c="admin", f="user",
                           check = is_user_admin,
                           ),
                        MP("Profile", c="default", f="person"),
                        MP("Change Password", c="default", f="user",
                           m = "change_password",
                           ),
                        MP("Logout", c="default", f="user",
                           m = "logout",
                           ),
            )
        return menu_personal

    # -------------------------------------------------------------------------
    @classmethod
    def menu_about(cls):

        menu_about = MA(c="default")(
            MA("Help", f="help"),
            MA("Contact", f="contact"),
            MA("Privacy", f="index", args=["privacy"]),
            MA("Legal Notice", f="index", args=["legal"]),
            MA("Version", f="about", restrict = ("ORG_GROUP_ADMIN")),
        )
        return menu_about

# =============================================================================
class OptionsMenu(default.OptionsMenu):
    """ Custom Controller Menus """

    # -------------------------------------------------------------------------
    @staticmethod
    def admin():
        """ ADMIN menu """

        if not current.auth.s3_has_role("ADMIN"):
            # OrgAdmin: No Side-menu
            return None

        has_cms = lambda i: current.deployment_settings.has_module("cms")

        # NB: Do not specify a controller for the main menu to allow
        #     re-use of this menu by other controllers
        return M()(
                    M("Users and Roles", c="admin", link=False)(
                        M("Manage Users", f="user"),
                        M("Manage Roles", f="role"),
                    ),
                    M("Announcements", c="admin", f="announcement", check=has_cms),
                    M("Content Management", c="cms", f="post", check=has_cms),
                    M("Database", c="appadmin", f="index")(
                        M("Raw Database access", c="appadmin", f="index")
                    ),
                    M("Event Log", c="admin", f="event"),
                    M("Error Tickets", c="admin", f="errors"),
                    M("Scheduler", c="admin", f="task"),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def asset():
        """ ASSET Controller """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="asset")(
                    M("Equipment", f="asset")(
                        M("Create", m="create"),
                    ),
                    M("Administration", link=False, restrict=[ADMIN])(
                        M("Items", f="item"),
                        ),
                )

    # -------------------------------------------------------------------------
    @classmethod
    def cms(cls):

        if current.request.function in ("newsletter", "read_newsletter"):
            return cls.org()

        return M(c="cms")(
                    M("Series", f="series")(
                        M("Create", m="create"),
                        M("View as Pages", f="blog"),
                        ),
                    M("Posts", f="post")(
                        M("Create", m="create"),
                        M("View as Pages", f="page"),
                        ),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def cr():
        """ CR / Shelter Registry """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="cr")(
                    M("Shelter", f="shelter")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        # M("Report", m="report"),
                    ),
                    M("Shelter Settings", restrict=[ADMIN])(
                        M("Types", f="shelter_type"),
                        M("Services", f="shelter_service"),
                    )
                )

    # -------------------------------------------------------------------------
    @classmethod
    def hrm(cls):
        """ HRM / Human Resources Management """

        return cls.org()

    # -------------------------------------------------------------------------
    @staticmethod
    def inv():
        """ INV / Inventory """

        current.s3db.inv_recv_crud_strings()
        inv_recv_list = current.response.s3.crud_strings.inv_recv.title_list

        settings = current.deployment_settings
        use_adjust = lambda i: not settings.get_inv_direct_stock_edits()
        # use_commit = lambda i: settings.get_req_use_commit()

        return M()(
                    M("Warehouses", c="inv", f="warehouse")(
                        M("Create", m="create", restrict=["ADMIN", "ORG_ADMIN", "SUPPLY_COORDINATOR"]),
                        # M("Import", m="import", p="create", restrict=["ADMIN", "ORG_ADMIN", "SUPPLY_COORDINATOR"]),
                    ),
                    M("Warehouse Stock", c="inv", f="inv_item")(
                        M("Adjust Stock Levels", f="adj", check=use_adjust, restrict=["ADMIN", "ORG_ADMIN", "SUPPLY_COORDINATOR"]),
                        # M("Kitting", f="kitting"),
                        # M("Import", f="inv_item", m="import", p="create", restrict=["ADMIN", "ORG_ADMIN", "SUPPLY_COORDINATOR"]),
                    ),
                    # M("Reports", c="inv", f="inv_item")(
                    #     M("Warehouse Stock", f="inv_item", m="report"),
                    #     M("Expiration Report", c="inv", f="track_item",
                    #       vars={"report": "exp"}),
                    #     M("Monetization Report", c="inv", f="inv_item",
                    #       vars={"report": "mon"}),
                    #     M("Utilization Report", c="inv", f="track_item",
                    #       vars={"report": "util"}),
                    #     M("Summary of Incoming Supplies", c="inv", f="track_item",
                    #       vars={"report": "inc"}),
                    #     M("Summary of Releases", c="inv", f="track_item",
                    #       vars={"report": "rel"}),
                    # ),
                    M(inv_recv_list, c="inv", f="recv", translate=False)( # Already T()
                        M("Create", m="create", restrict=["ADMIN", "ORG_ADMIN", "SUPPLY_COORDINATOR"]),
                    ),
                    M("Sent Shipments", c="inv", f="send")(
                        M("Create", m="create", restrict=["ADMIN", "ORG_ADMIN", "SUPPLY_COORDINATOR"]),
                        M("Search Shipped Items", f="track_item"),
                    ),
                    M("Distributions", c="supply", f="distribution")(
                        M("Create", m="create", restrict=["ADMIN", "ORG_ADMIN", "SUPPLY_COORDINATOR"]),
                    ),
                    M("Items", c="supply", f="item")(
                        M("Create", m="create", restrict=["ADMIN", "ORG_ADMIN", "SUPPLY_COORDINATOR"]),
                        # M("Import", f="catalog_item", m="import", p="create", restrict=["ADMIN", "ORG_ADMIN", "SUPPLY_COORDINATOR"]),
                    ),
                    # Catalog Items moved to be next to the Item Categories
                    #M("Catalog Items", c="supply", f="catalog_item")(
                       #M("Create", m="create"),
                    #),
                    #M("Brands", c="supply", f="brand",
                    #  restrict=[ADMIN])(
                    #    M("Create", m="create"),
                    #),

                    M("Administration", c=("supply", "inv"), restrict=["ADMIN", "ORG_ADMIN", "SUPPLY_COORDINATOR"], link=False)(
                        M("Catalogs", f="catalog"),
                        M("Item Categories", f="item_category"),
                        M("Warehouse Types", c="inv", f="warehouse_type"),
                        ),

                    # M("Catalogs", c="supply", f="catalog")(
                    #     M("Create", m="create"),
                    # ),
                    # M("Item Categories", c="supply", f="item_category",
                    #   restrict=[ADMIN])(
                    #     M("Create", m="create"),
                    # ),
                    # M("Suppliers", c="inv", f="supplier")(
                    #     M("Create", m="create"),
                    #     M("Import", m="import", p="create"),
                    # ),
                    # M("Facilities", c="inv", f="facility")(
                    #     M("Create", m="create", t="org_facility"),
                    # ),
                    # M("Facility Types", c="inv", f="facility_type",
                    #   restrict=[ADMIN])(
                    #     M("Create", m="create"),
                    # ),
                    #M("Warehouse Types", c="inv", f="warehouse_type",
                    #  restrict=[ADMIN])(
                    #    M("Create", m="create"),
                    #),
                    # M("Requests", c="req", f="req")(
                    #     M("Create", m="create"),
                    #     M("Requested Items", f="req_item"),
                    # ),
                    # M("Commitments", c="req", f="commit", check=use_commit)(
                    # ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def org():
        """ ORG / Organization Registry """

        T = current.T
        auth = current.auth

        ADMIN = current.session.s3.system_roles.ADMIN

        # Newsletter menu
        author = auth.s3_has_permission("create", "cms_newsletter", c="cms", f="newsletter")
        inbox_label = T("Inbox") if author else T("Newsletters")
        unread = current.s3db.cms_unread_newsletters()
        if unread:
            inbox_label = TAG[""](inbox_label, SPAN(unread, _class="num-pending"))
        if author:
            cms_menu = M("Newsletters", c="cms", link=False)(
                            M(inbox_label, f="read_newsletter", translate=False),
                            M("Compose and Send", f="newsletter", p="create"),
                            )
        else:
            cms_menu = M(inbox_label, c="cms", f="read_newsletter", translate=False)

        return M(c=("org", "hrm", "act"))(
                    M("Organizations", c="org", f="organisation")(
                        M("Create", m="create"),
                        ),
                    M("Staff", c="hrm", f="staff"),
                    M("Teams", c="hrm", f="group"),
                    cms_menu,
                    M("Administration", link=False, restrict=[ADMIN])(
                        M("Organization Types", c="org", f="organisation_type"),
                        M("Organization Groups", f="group"),
                        M("Services", "org", f="service"),
                        # M("Activity Types", c="act", f="activity_type"),
                        # M("Job Titles", c="hrm", f="job_title"),
                        ),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def req():
        """ REQ / Needs Management """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="req")(
                    M("Needs Assessments", f="need")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        ),
                    M("Assistance", f="need_service")(
                        M("Manage"),
                        # M("Map", m="map"), # TODO needs location context
                        ),
                    M("Administration", link=False, restrict=[ADMIN])(
                        M("Site Types", f="need_site_type"),
                        ),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def water():
        """ Water: Wells, etc """

        return M(c="water")(
                    M("Wells", f="well")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        ),
                    )

# END =========================================================================
