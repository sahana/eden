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

        system_roles = current.session.s3.system_roles
        AUTHENTICATED = system_roles.AUTHENTICATED
        VALIDATOR = system_roles.VALIDATOR

        INDIVIDUALS = current.deployment_settings.get_hrm_staff_label()

        return [
            #MM("Dashboard", c="default", f="index",
            #   args=["dashboard"],
            #   restrict=[AUTHENTICATED],
            #   ),
            MM("Stakeholder Network", link=False)(
                #MM("Networks", c="org", f="group"),
                #MM("Groups", c="hrm", f="group"),
                MM("Organizations", c="org", f="organisation", m="summary"),
                MM(INDIVIDUALS, c="hrm", f="staff", m="summary",
                   restrict=[AUTHENTICATED]),
            ),
            MM("Requests for Aid", link=False)(
                MM("Requests", c="req", f="req", m="summary"),
            ),
            MM("Aid Delivery", link=False)(
                MM("Shipments", c="inv", f="send", m="summary"),
            ),
            MM("Map", c="gis", f="index",
               icon="icon-map",
               #restrict=[AUTHENTICATED],
               ),
            MM("Validation", link=False, restrict=[VALIDATOR])(
                    MM("Organizations", c="org", f="organisation", m="review"),
                    MM("Requests", c="req", f="req", m="review"),
                    MM("Shipments", c="inv", f="send", m="review"),
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
                            #SEP(),
                            #MM({"name": current.T("Rapid Data Entry"),
                            #    "id": "rapid_toggle",
                            #    "value": current.session.s3.rapid_data_entry is True,
                            #    },
                            #   f="rapid",
                            #   ),
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
                    #M("Networks", c="org", f="group")(
                    #    M("Search"),
                    #    M("Create", m="create"),
                    #),
                    #M("Groups", c="hrm", f="group")(
                    #    M("Search"),
                    #    M("Create", m="create"),
                    #),
                    M("Organizations", c="org", f="organisation")(
                        M("Search"),
                        M("Create", m="create",
                          restrict=[AUTHENTICATED]),
                    ),
                    M(INDIVIDUALS, c="hrm", f="staff", t="hrm_human_resource")(
                        M("Search"),
                        M("Create", m="create"),
                    ),
                    #M("Your Personal Profile", c="default", f="person",
                    #  m="update")(
                    #),
                    M("Import", link=False,
                      restrict=[ADMIN])(
                        M("Import Contacts", c="hrm", f="person", m="import",
                          vars={"group":"staff"}),
                        M("Import Organizations", c="org", f="organisation",
                          m="import"),
                        #M("Import Groups", c="hrm", f="group", m="import"),
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
