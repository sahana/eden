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

        # Modules menus
        main_menu = MM()(
            cls.menu_modules(),
            cls.menu_personal(),
            cls.menu_lang(),
        )

        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        return [
            homepage(name = "&nbsp;",
                     left = True,
                     icon = "%s/static/themes/img/logo-small.png" % \
                            current.request.application,
                     ),
            # @todo:
            MM("Newsfeed", link=False),
            MM("Organizations", c="org", f="organisation"),
            MM("Projects", c="project", f="project"),
            # @todo:
            MM("Aid Requests", link=False),
            # @todo:
            #MM("Aid Deliveries", link=False),
            MM("Map", c="gis", f="index"),
        ]

    # -------------------------------------------------------------------------
    @classmethod
    def menu_personal(cls):
        """ Custom Personal Menu """

        auth = current.auth
        s3 = current.response.s3
        settings = current.deployment_settings

        if not auth.is_logged_in():

            request = current.request

            login_next = URL(args=request.args, vars=request.vars)
            if request.controller == "default" and \
               request.function == "user" and \
               "_next" in request.get_vars:
                login_next = request.get_vars["_next"]

            self_registration = settings.get_security_self_registration()
            menu_personal = MM(icon="icon-cog", link=False)(
                        MM("Register", c="default", f="user",
                           m="register",
                           check = self_registration,
                           ),
                        MM("Login", c="default", f="user",
                           m="login",
                           vars = {"_next": login_next},
                           ),
                        MM("Lost Password", c="default", f="user",
                           m="retrieve_password",
                           ),
                        )

        else:
            s3_has_role = auth.s3_has_role
            is_org_admin = lambda i: s3_has_role("ORG_ADMIN") and \
                                     not s3_has_role("ADMIN")

            menu_personal = MM(icon="user", link=False)(
                        MM("Administration", c="admin", f="index",
                           restrict = "ADMIN",
                           ),
                        MM("Administration", c="admin", f="user",
                           check = is_org_admin,
                           ),
                        MM("Change Password", c="default", f="user",
                           m = "change_password",
                           ),
                        MM("Logout", c="default", f="user",
                           m = "logout",
                           ),
                        )

        return menu_personal

    # -------------------------------------------------------------------------
    @classmethod
    def menu_lang(cls):
        """ Language Selector """

        s3 = current.response.s3

        menu_lang = ML("Language", right=True)
        for language in s3.l10n_languages.items():
            code, name = language
            menu_lang(
                ML(name, translate=False, lang_code=code, lang_name=name)
            )
        return menu_lang

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """ Custom Controller Menus """

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm():
        """ HRM / Human Resources Management """

        s3 = current.session.s3
        ADMIN = s3.system_roles.ADMIN
        AUTHENTICATED = s3.system_roles.AUTHENTICATED

        INDIVIDUALS = current.deployment_settings.get_hrm_staff_label()

        return M()(
                    #M("Networks", c="org", f="group")(
                    #    M("Search"),
                    #    M("Create", m="create"),
                    #),
                    #M("Groups", c="hrm", f="group")(
                    #    M("Search"),
                    #    M("Create", m="create"),
                    #),
                    M("Organizations", c="org", f="organisation")(
                        #M("Search", m="summary"),
                        M("Create", m="create",
                          restrict=[AUTHENTICATED]),
                    ),
                    M(INDIVIDUALS, c="hrm", f="staff", t="hrm_human_resource")(
                        #M("Search"),
                        M("Create", m="create"),
                    ),
                    M("Service Locations", c="org", f="service_location", m="summary")(
                        M("Search", m="summary"),
                    ),
                    #M("Your Personal Profile", c="default", f="person",
                    #  m="update")(
                    #),
                    #M("Import", link=False,
                    #  restrict=[ADMIN])(
                    #    M("Import Contacts", c="hrm", f="person", m="import",
                    #      vars={"group":"staff"}),
                    #   M("Import Organizations", c="org", f="organisation",
                    #      m="import"),
                    #    #M("Import Groups", c="hrm", f="group", m="import"),
                    #),
                    #M("Organization Types", c="org", f="organisation_type",
                    #  restrict=[ADMIN])(
                    #    M("View"),
                    #    M("Create", m="create"),
                    #),
                    M("Administration", c=("org", "hrm"),
                      link = False, restrict = [ADMIN])(
                        M("Organisation Types", c="org", f="organisation_type"),
                        M("Sectors", c="org", f="sector"),
                        M("Service Types", c="org", f="service"),
                    ),
                    #M("Job Title Catalog", c="hrm", f="job_title",
                    #  restrict=[ADMIN])(
                    #    M("View"),
                    #    M("Create", m="create"),
                    #),
                    #M("Skills Catalog", c="hrm", f="skill",
                    #  restrict=[ADMIN])(
                    #    M("View"),
                    #    M("Create", m="create"),
                    #),
                    #M("Organization Approval", c="org", f="organisation",
                    #  m="review", restrict=[ADMIN])(
                    #),
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

    # -------------------------------------------------------------------------
    def inv(self):
        """ Aid Delivery """

        if not current.auth.is_logged_in():
            # No Side Menu
            return None

        ADMIN = current.session.s3.system_roles.ADMIN

        #current.s3db.inv_recv_crud_strings()
        #inv_recv_list = current.response.s3.crud_strings.inv_recv.title_list

        #settings = current.deployment_settings
        #use_adjust = lambda i: not settings.get_inv_direct_stock_edits()
        #use_commit = lambda i: settings.get_req_use_commit()

        return M()(
                    #M("Home", f="index"),
                    #M("Warehouses", c="inv", f="warehouse")(
                    #    M("Create", m="create"),
                    #    M("Import", m="import", p="create"),
                    #),
                    #M("Warehouse Stock", c="inv", f="inv_item")(
                    #    M("Adjust Stock Levels", f="adj", check=use_adjust),
                    #    M("Kitting", f="kitting"),
                    #    M("Import", f="inv_item", m="import", p="create"),
                    #),
                    #M("Reports", c="inv", f="inv_item")(
                    #    M("Warehouse Stock", f="inv_item", m="report"),
                    #    M("Expiration Report", c="inv", f="track_item",
                    #      vars=dict(report="exp")),
                    #    M("Monetization Report", c="inv", f="inv_item",
                    #      vars=dict(report="mon")),
                    #    M("Utilization Report", c="inv", f="track_item",
                    #      vars=dict(report="util")),
                    #    M("Summary of Incoming Supplies", c="inv", f="track_item",
                    #      vars=dict(report="inc")),
                    #    M("Summary of Releases", c="inv", f="track_item",
                    #      vars=dict(report="rel")),
                    #),
                    #M(inv_recv_list, c="inv", f="recv", translate=False)( # Already T()
                    #    M("Create", m="create"),
                    #    M("Timeline", args="timeline"),
                    #),
                    M("Shipments", c="inv", f="send")(
                        M("Create", m="create"),
                        M("Search Shipped Items", f="track_item"),
                        M("Timeline", args="timeline"),
                    ),
                    M("Items", c="supply", f="item", m="summary")(
                        M("Create", m="create"),
                        M("Import", f="catalog_item", m="import", p="create"),
                    ),
                    # Catalog Items moved to be next to the Item Categories
                    #M("Catalog Items", c="supply", f="catalog_item")(
                       #M("Create", m="create"),
                    #),
                    #M("Brands", c="supply", f="brand",
                    #  restrict=[ADMIN])(
                    #    M("Create", m="create"),
                    #),
                    M("Catalogs", c="supply", f="catalog")(
                        M("Create", m="create"),
                    ),
                    M("Item Categories", c="supply", f="item_category",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Suppliers", c="inv", f="supplier")(
                        M("Create", m="create"),
                        M("Import", m="import", p="create"),
                    ),
                    #M("Facilities", c="inv", f="facility")(
                    #    M("Create", m="create", t="org_facility"),
                    #),
                    #M("Facility Types", c="inv", f="facility_type",
                    #  restrict=[ADMIN])(
                    #    M("Create", m="create"),
                    #),
                    #M("Warehouse Types", c="inv", f="warehouse_type",
                    #  restrict=[ADMIN])(
                    #    M("Create", m="create"),
                    #),
                    #M("Requests", c="req", f="req")(
                    #    M("Create", m="create"),
                    #    M("Requested Items", f="req_item"),
                    #),
                    #M("Commitments", c="req", f="commit", check=use_commit)(
                    #),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def req():
        """ REQ / Request Management """

        if not current.auth.is_logged_in():
            # No Side Menu
            return None

        ADMIN = current.session.s3.system_roles.ADMIN
        #settings = current.deployment_settings
        #types = settings.get_req_req_type()
        #if len(types) == 1:
        #    t = types[0]
        #    if t == "Stock":
        #        create_menu = M("Create", m="create", vars={"type": 1})
        #    elif t == "People":
        #        create_menu = M("Create", m="create", vars={"type": 2})
        #    else:
        #        create_menu = M("Create", m="create")
        #else:
        #    create_menu = M("Create", m="create")

        #recurring = lambda i: settings.get_req_recurring()
        #use_commit = lambda i: settings.get_req_use_commit()
        #req_items = lambda i: "Stock" in types
        #req_skills = lambda i: "People" in types

        return M(c="req")(
                    M("Requests", f="req")(
                        M("Create", m="create", vars={"type": 1}),
                        #M("List Recurring Requests", f="req_template", check=recurring),
                        #M("Map", m="map"),
                        #M("Report", m="report"),
                        M("Search All Requested Items", f="req_item",
                          #check=req_items
                          ),
                        #M("Search All Requested Skills", f="req_skill",
                        #  check=req_skills),
                    ),
                    #M("Commitments", f="commit", check=use_commit)(
                    #),
                    M("Items", c="supply", f="item")(
                        M("Create", m="create"),
                        M("Report", m="report"),
                        M("Import", m="import", p="create"),
                    ),
                    # Catalog Items moved to be next to the Item Categories
                    #M("Catalog Items", c="supply", f="catalog_item")(
                       #M("Create", m="create"),
                    #),
                    M("Catalogs", c="supply", f="catalog")(
                        M("Create", m="create"),
                    ),
                    M("Item Categories", c="supply", f="item_category",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def gis():
        """ GIS / GIS Controllers """

        if not current.auth.is_logged_in():
            # No Side Menu
            return None

        MAP_ADMIN = current.session.s3.system_roles.MAP_ADMIN

        settings = current.deployment_settings
        gis_menu = settings.get_gis_menu()
        def pois(i):
            poi_resources = settings.get_gis_poi_create_resources()
            if not poi_resources:
                return False
            for res in poi_resources:
                if res["table"] == "gis_poi":
                    return True
            return False

        def config_menu(i):
            auth = current.auth
            if not auth.is_logged_in():
                # Anonymous users can never cofnigure the Map
                return False
            s3db = current.s3db
            if auth.s3_has_permission("create",
                                      s3db.gis_config):
                # If users can create configs then they can see the menu item
                return True
            # Look for this user's config
            table = s3db.gis_config
            query = (table.pe_id == auth.user.pe_id)
            config = current.db(query).select(table.id,
                                              limitby=(0, 1),
                                              cache=s3db.cache).first()
            if config:
                return True

        def config_args():
            auth = current.auth
            if not auth.user:
                # Won't show anyway due to check
                return []

            if auth.s3_has_role(MAP_ADMIN):
                # Full List
                return []

            # Look for this user's config
            s3db = current.s3db
            table = s3db.gis_config
            query = (table.pe_id == auth.user.pe_id)
            config = current.db(query).select(table.id,
                                              limitby=(0, 1),
                                              cache=s3db.cache).first()
            if config:
                # Link direct to the User's config
                return [config.id, "layer_entity"]
            # Link to the Create form
            return ["create"]

        return M(c="gis")(
                    M("Fullscreen Map", c="gis", f="map_viewing_client"),
                    # Currently not got geocoding support
                    #M("Bulk Uploader", c="doc", f="bulk_upload"),
                    M("Locations", c="gis", f="location")(
                        M("Create", m="create"),
                        #M("Create Location Group", m="create", vars={"group": 1}),
                        M("Import from CSV", m="import", restrict=[MAP_ADMIN]),
                        M("Import from OpenStreetMap", m="import_poi",
                          restrict=[MAP_ADMIN]),
                        #M("Geocode", f="geocode_manual"),
                    ),
                    M("PoIs", c="gis", f="poi", check=pois)(),
                    #M("Population Report", f="location", m="report",
                    # vars=dict(rows="name",
                    #           fact="sum(population)",
                    #           ),
                    # ),
                    M("Configuration", c="gis", f="config", args=config_args(),
                      _id="gis_menu_config",
                      check=config_menu),
                    M("Admin", c="gis", restrict=[MAP_ADMIN])(
                        M("Hierarchy", f="hierarchy"),
                        M("Layers", f="catalog"),
                        M("Markers", f="marker"),
                        M("Menu", f="menu",
                          check=[gis_menu]),
                        M("PoI Types", f="poi_type",
                          check=[pois]),
                        M("Projections", f="projection"),
                        M("Styles", f="style"),
                    )
                )

# END =========================================================================
