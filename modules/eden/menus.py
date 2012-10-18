# -*- coding: utf-8 -*-

""" Sahana Eden Menu Structure and Layout

    @copyright: 2011-2012 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ["S3MainMenu", "S3OptionsMenu"]

import re

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from layouts import *

# =============================================================================
class S3MainMenu(object):
    """ The default configurations for the main application menu """

    @classmethod
    def menu(cls):

        main_menu = MM()(

            # Modules-menu, align-left
            cls.menu_modules(),

            # Service menus, align-right
            # Note: always define right-hand items in reverse order!
            cls.menu_help(right=True),
            cls.menu_auth(right=True),
            cls.menu_lang(right=True),
            cls.menu_admin(right=True),
            cls.menu_gis(right=True)
        )
        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):

        # ---------------------------------------------------------------------
        # Modules Menu
        # @todo: this is very ugly - cleanup or make a better solution
        # @todo: probably define the menu explicitly?
        #
        menu_modules = []
        all_modules = current.deployment_settings.modules

        # Home always 1st
        module = all_modules["default"]
        menu_modules.append(MM(module.name_nice, c="default", f="index"))

        auth = current.auth
        # Modules to hide due to insufficient permissions
        hidden_modules = auth.permission.hidden_modules()

        has_role = auth.s3_has_role

        # The Modules to display at the top level (in order)
        for module_type in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            for module in all_modules:
                if module in hidden_modules:
                    continue
                _module = all_modules[module]
                if (_module.module_type == module_type):
                    if not _module.access:
                        menu_modules.append(MM(_module.name_nice, c=module, f="index"))
                    else:
                        groups = re.split("\|", _module.access)[1:-1]
                        menu_modules.append(MM(_module.name_nice,
                                               c=module,
                                               f="index",
                                               restrict=groups))

        # Modules to display off the 'more' menu
        modules_submenu = []
        for module in all_modules:
            if module in hidden_modules:
                continue
            _module = all_modules[module]
            if (_module.module_type == 10):
                if not _module.access:
                    modules_submenu.append(MM(_module.name_nice, c=module, f="index"))
                else:
                    groups = re.split("\|", _module.access)[1:-1]
                    modules_submenu.append(MM(_module.name_nice,
                                              c=module,
                                              f="index",
                                              restrict=groups))

        if modules_submenu:
            # Only show the 'more' menu if there are entries in the list
            module_more_menu = MM("more", link=False)(modules_submenu)
            menu_modules.append(module_more_menu)

        return menu_modules

    # -------------------------------------------------------------------------
    @classmethod
    def menu_lang(cls, **attr):
        """ Language menu """

        languages = current.response.s3.l10n_languages
        request = current.request

        settings = current.deployment_settings
        if not settings.get_L10n_display_toolbar():
            return None

        menu_lang = MM("Language", **attr)
        for language in languages:
            menu_lang.append(MM(languages[language], r=request,
                                translate=False,
                                vars={"_language":language}))
        return menu_lang

    # -------------------------------------------------------------------------
    @classmethod
    def menu_help(cls, **attr):
        """ Help Menu """

        menu_help = MM("Help", c="default", f="help", **attr)(
            MM("Contact us", f="contact"),
            MM("About", f="about")
        )
        return menu_help

    # -------------------------------------------------------------------------
    @classmethod
    def menu_auth(cls, **attr):
        """ Auth Menu """

        auth = current.auth
        logged_in = auth.is_logged_in()
        self_registration = current.deployment_settings.get_security_self_registration()

        if not logged_in:
            request = current.request
            login_next = URL(args=request.args, vars=request.vars)
            if request.controller == "default" and \
               request.function == "user" and \
               "_next" in request.get_vars:
                login_next = request.get_vars["_next"]

            menu_auth = MM("Login", c="default", f="user", m="login",
                           _id="auth_menu_login",
                           vars=dict(_next=login_next), **attr)(
                            MM("Login", m="login",
                               vars=dict(_next=login_next)),
                            MM("Register", m="register",
                               vars=dict(_next=login_next),
                               check=self_registration),
                            MM("Lost Password", m="retrieve_password")
                        )
        else:
            # Logged-in
            menu_auth = MM(auth.user.email, c="default", f="user",
                           translate=False, link=False, _id="auth_menu_email",
                           **attr)(
                            MM("Logout", m="logout", _id="auth_menu_logout"),
                            MM("User Profile", m="profile"),
                            MM("Personal Data", c="pr", f="person", m="update",
                                vars={"person.pe_id" : auth.user.pe_id}),
                            MM("Contact Details", c="pr", f="person",
                                args="contact",
                                vars={"person.pe_id" : auth.user.pe_id}),
                            #MM("Subscriptions", c="pr", f="person",
                                #args="pe_subscription",
                                #vars={"person.pe_id" : auth.user.pe_id}),
                            MM("Change Password", m="change_password"),
                            SEP(),
                            MM({"name": current.T("Rapid Data Entry"),
                               "id": "rapid_toggle",
                               "value": current.session.s3.rapid_data_entry is True},
                               f="rapid"),
                        )

        return menu_auth

    # -------------------------------------------------------------------------
    @classmethod
    def menu_admin(cls, **attr):
        """ Administrator Menu """

        ADMIN = current.session.s3.system_roles.ADMIN
        settings = current.deployment_settings
        name_nice = settings.modules["admin"].name_nice
        translate = settings.has_module("translate")

        menu_admin = MM(name_nice, c="admin",
                        restrict=[ADMIN], **attr)(
                            MM("Settings", f="setting"),
                            MM("Users", f="user"),
                            MM("Person Registry", c="pr"),
                            MM("Database", c="appadmin", f="index"),
                            MM("Synchronization", c="sync", f="index"),
                            MM("Translation", c="admin", f="translate",
                               check=translate),
                            MM("Test Results", f="result"),
                            MM("Tickets", f="errors"),
                        )

        return menu_admin

    # -------------------------------------------------------------------------
    @classmethod
    def menu_gis(cls, **attr):
        """ GIS Config Menu """

        settings = current.deployment_settings
        if not settings.get_gis_menu():
            return None

        T = current.T
        db = current.db
        auth = current.auth
        s3db = current.s3db
        request = current.request
        s3 = current.session.s3
        _config = s3.gis_config_id

        # See if we need to switch config before we decide which
        # config item to mark as active:
        if "_config" in request.get_vars:
            # The user has just selected a config from the GIS menu
            try:
                config = int(request.get_vars._config)
            except ValueError:
                # Manually-crafted URL?
                pass
            else:
                if _config is None or _config != config:
                    # Set this as the current config
                    s3.gis_config_id = config
                    cfg = current.gis.get_config()
                    s3.location_filter = cfg.region_location_id
                    if settings.has_module("event"):
                        # See if this config is associated with an Event
                        table = s3db.event_config
                        query = (table.config_id == config)
                        incident = db(query).select(table.incident_id,
                                                    limitby=(0, 1)).first()
                        if incident:
                            s3.event = incident.incident_id
                        else:
                            s3.event = None
            # Don't use the outdated cache for this call
            cache = None
        else:
            cache = s3db.cache

        # Check if there are multiple GIS Configs for the user to switch between
        table = s3db.gis_menu
        ctable = s3db.gis_config
        query = (table.pe_id == None)
        if auth.is_logged_in():
            # @ToDo: Search for OUs too (API call)
            query |= (table.pe_id == auth.user.pe_id)
        query &= (table.config_id == ctable.id)
        configs = db(query).select(ctable.id, ctable.name, cache=cache)

        gis_menu = MM(settings.get_gis_menu(),
                      c=request.controller,
                      f=request.function,
                      **attr)
        args = request.args
        if len(configs):
            # Use short names for the site and personal configs else they'll wrap.
            # Provide checkboxes to select between pages
            gis_menu(
                    MM({"name": T("Default"),
                        "id": "gis_menu_id_0",
                        # @ToDo: Show when default item is selected without having
                        # to do a DB query to read the value
                        #"value": _config is 0,
                        "request_type": "load"
                       }, args=args, vars={"_config": 0}
                    )
                )
            for config in configs:
                gis_menu(
                    MM({"name": config.name,
                        "id": "gis_menu_id_%s" % config.id,
                        "value": _config == config.id,
                        "request_type": "load"
                       }, args=args, vars={"_config": config.id}
                    )
                )
        return gis_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_climate(cls, **attr):
        """ Climate module menu """

        name_nice = current.deployment_settings.modules["climate"].name_nice
        ADMIN = current.session.s3.system_roles.ADMIN

        menu_climate = MM(name_nice, c="climate", **attr)(
                MM("Station Parameters", f="station_parameter"),
                #MM("Saved Queries", f="save_query"),
                MM("Purchase Data", f="purchase"),
                MM("DataSet Prices", f="prices", restrict=[ADMIN]),
            )
        return menu_climate

# =============================================================================
class S3OptionsMenu(object):
    """
        The default configurations for options menus

        Define one function per controller with the controller prefix as
        function name and with "self" as its only argument (must be an
        instance method!), and let it return the controller menu
        definition as an instance of the layout (=an S3NavigationItem
        subclass, standard: M).

        In the standard layout, the main item in a controller menu does
        not have a label. If you want to re-use a menu for multiple
        controllers, do *not* define a controller setting (c="xxx") in
        the main item.
    """

    def __init__(self, name):
        """ Constructor """

        try:
            self.menu = getattr(self, name)()
        except:
            self.menu = None

    # -------------------------------------------------------------------------
    def admin(self):
        """ ADMIN menu """

        ADMIN = current.session.s3.system_roles.ADMIN
        settings_messaging = self.settings_messaging()
        translate = current.deployment_settings.has_module("translate")

        # ATTN: Do not specify a controller for the main menu to allow
        #       re-use of this menu by other controllers
        return M(restrict=[ADMIN])(
                    M("Settings", c="admin", f="settings")(
                        settings_messaging,
                    ),
                    M("User Management", c="admin", f="user")(
                        M("New User", m="create"),
                        M("List All Users", f="user"),
                        M("List All Roles", f="role"),
                        M("List All Organization Approvers & Whitelists", f="organisation"),
                        #M("Roles", f="group"),
                        #M("Membership", f="membership"),
                    ),
                    M("Database", c="appadmin", f="index")(
                        M("Raw Database access", c="appadmin", f="index")
                    ),
                    M("Synchronization", c="sync", f="index")(
                        M("Settings", f="config", args=[1], m="update"),
                        M("Repositories", f="repository"),
                        M("Log", f="log"),
                    ),
                    #M("Edit Application", a="admin", c="default", f="design",
                      #args=[request.application]),
                    M("Translation", c="admin", f="translate", check=translate)(
                       M("Select Modules for translation", c="admin", f="translate",
                         m="create", vars=dict(opt="1")),
                       M("Upload translated files", c="admin", f="translate",
                         m="create", vars=dict(opt="2")),
                       M("View Translation Percentage", c="admin", f="translate",
                         m="create", vars=dict(opt="3")),
                       M("Add strings manually", c="admin", f="translate",
                         m="create", vars=dict(opt="4"))
                    ),
                    M("Tickets", c="admin", f="errors"),
                    M("View Test Result Reports", c="admin", f="result"),
                    M("Portable App", c="admin", f="portable")
                )

    # -------------------------------------------------------------------------
    def assess(self):
        """ ASSESS Menu """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="assess")(
                    M("Rapid Assessments", f="rat")(
                        M("New", m="create"),
                        M("List All"),
                        #M("Search", m="search"),
                    ),
                    M("Impact Assessments", f="assess")(
                        #M("New", m="create"),
                        M("New", f="basic_assess", p="create"),
                        M("List All"),
                        M("Mobile", f="mobile_basic_assess"),
                        #M("Search", m="search"),
                    ),
                    #M("Baseline Data")(
                        #M("Population", f="population"),
                    #),
                    M("Edit Options", restrict=ADMIN)(
                        M("List / Add Baseline Types", f="baseline_type"),
                        M("List / Add Impact Types", f="impact_type"),
                    )
                )


    # -------------------------------------------------------------------------
    def asset(self):
        """ ASSET Controller """

        return M(c="asset")(
                    M("Assets", f="asset")(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Report", m="report"),
                        M("Import", m="import", p="create"),
                    ),
                    M("Items", f="item")(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Report", m="report"),
                        M("Import", m="import", p="create"),
                    ),
                    M("Item Categories", f="item_category")(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Suppliers", f="supplier")(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", m="import", p="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    def budget(self):
        """ BUDGET Controller """

        return M(c="budget")(
                    M("Parameters", f="parameters"),
                    M("Items", f="item")(
                        M("New", m="create"),
                        M("List"),
                    ),
                    M("Kits", f="kit")(
                        M("New", m="create"),
                        M("List"),
                    ),
                    M("Bundles", f="bundle")(
                        M("New", m="create"),
                        M("List"),
                    ),
                    M("Staff", f="staff")(
                        M("New", m="create"),
                        M("List"),
                    ),
                    M("Locations", f="location")(
                        M("New", m="create"),
                        M("List"),
                    ),
                    M("Projects", f="project")(
                        M("New", m="create"),
                        M("List"),
                    ),
                    M("Budgets", f="budget")(
                        M("New", m="create"),
                        M("List"),
                    )
                )

    # -------------------------------------------------------------------------
    def building(self):
        """ BUILDING Controller """

        return M(c="building")(
                    M("NZSEE Level 1", f="nzseel1")(
                        M("Submit New (triage)", m="create",
                          vars={"triage":1}),
                        M("Submit New (full form)", m="create"),
                        M("List"),
                        M("Search", m="search"),
                    ),
                    M("NZSEE Level 2", f="nzseel2")(
                        M("Submit New", m="create"),
                        M("List"),
                        M("Search", m="search"),
                    ),
                    M("Report", f="index")(
                        M("Snapshot", f="report"),
                        M("Assessment timeline", f="timeline"),
                        M("Assessment admin level", f="adminLevel"),
                    ),
                )

    # -------------------------------------------------------------------------
    def climate(self):
        """ CLIMATE Controller """

        return M(c="climate")(
                    M("Home", f="index"),
                    M("Station Parameters", f="station_parameter"),
                    M("Saved Queries", f="save_query"),
                    M("Purchase Data", f="purchase"),
                )
    # -------------------------------------------------------------------------
    def cr(self):
        """ CR / Shelter Registry """

        ADMIN = current.session.s3.system_roles.ADMIN

        if current.deployment_settings.get_ui_camp():
            shelter = "Camps"
            types = "Camp Settings"
        else:
            shelter = "Shelters"
            types = "Shelter Settings"

        return M(c="cr")(
                    M(shelter, f="shelter")(
                        M("New", m="create"),
                        M("List All"),
                        M("Map", m="map"),
                        # @ToDo Search by type, services, location, available space
                        #M("Search", m="search"),
                        M("Import", m="import"),
                    ),
                    M(types, restrict=[ADMIN])(
                        M("Types", f="shelter_type"),
                        M("Services", f="shelter_service"),
                    )
                )

    # -------------------------------------------------------------------------
    def cms(self):
        """ CMS / Content Management System """

        return M(c="cms")(
                    M("Series", f="series")(
                        M("New", m="create"),
                        M("List All"),
                        M("View as Pages", f="blog"),
                    ),
                    M("Posts", f="post")(
                        M("New", m="create"),
                        M("List All"),
                        M("View as Pages", f="page"),
                    ),
                )

    # -------------------------------------------------------------------------
    def delphi(self):
        """ DELPHI / Delphi Decision Maker """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="delphi")(
                    M("Active Problems", f="problem")(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Groups", f="group")(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    #M("Solutions", f="solution"),
                    #M("Administration", restrict=[ADMIN])(
                        #M("Groups", f="group"),
                        #M("Group Memberships", f="membership"),
                        #M("Problems", f="problem"),
                    #)
                )

    # -------------------------------------------------------------------------
    def doc(self):
        """ DOC Menu """

        return M(c="doc")(
                    M("Documents", f="document")(
                        M("New", m="create"),
                        M("List All"),
                        #M("Search", m="search")
                    ),
                    M("Photos", f="image")(
                        M("New", m="create"),
                        M("List All"),
                        #M("Bulk Uploader", f="bulk_upload"),
                        #M("Search", m="search")
                    )
                )

    # -------------------------------------------------------------------------
    def dvi(self):
        """ DVI / Disaster Victim Identification """

        return M(c="dvi")(
                    #M("Home", f="index"),
                    M("Body Recovery", f="recreq")(
                        M("New Request", m="create"),
                        M("List Current",
                          vars={"recreq.status":"1,2,3"}),
                        M("List All"),
                    ),
                    M("Dead Bodies", f="body")(
                        M("New", m="create"),
                        M("List all"),
                        M("List unidentified",
                          vars=dict(status="unidentified")),
                        M("Search", m="search"),
                        M("Report by Age/Gender", m="report",
                          vars=dict(rows="age_group",
                                    cols="gender",
                                    fact="pe_label",
                                    aggregate="count")),
                    ),
                    M("Missing Persons", f="person")(
                        M("List all"),
                    ),
                    M("Morgues", f="morgue")(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Dashboard", f="index"),
                )

    # -------------------------------------------------------------------------
    def dvr(self):
        """ DVR Menu """

        return M(c="dvr")(
                    M("Cases", f="case")(
                        M("New", m="create"),
                        M("List All"),
                        #M("Search", m="search")
                    ),
                )

    # -------------------------------------------------------------------------
    def event(self):
        """ EVENT / Event Module """

        return M()(
                    M("Scenarios", c="scenario", f="scenario")(
                        M("New", m="create"),
                        M("Import", m="import", p="create"),
                        M("View All"),
                    ),
                    M("Events", c="event", f="event")(
                        M("New", m="create"),
                        M("View All"),
                    ),
                    M("Incidents", c="event", f="incident")(
                        M("New", m="create"),
                        M("View All"),
                    ),
                    M("Incident Types", c="event", f="incident_type")(
                        M("New", m="create"),
                        M("Import", m="import", p="create"),
                        M("View All"),
                    ),
                )

    # -------------------------------------------------------------------------
    def fire(self):
        """ FIRE """

        return M(c="fire")(
                    M("Fire Stations", f="station")(
                        M("New", m="create"),
                        M("List All"),
                        M("Map", m="map"),
                        M("Search", m="search"),
                        M("Import Stations", m="import"),
                        M("Import Vehicles", f="station_vehicle", m="import"),
                    ),
                    M("Water Sources", f="water_source")(
                        M("New", m="create"),
                        M("List All"),
                        M("Map", m="map"),
                        M("Search", m="search"),
                        M("Import", m="import"),
                    ),
                    M("Hazard Points", f="hazard_point")(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", m="import"),
                    )
                )

    # -------------------------------------------------------------------------
    def flood(self):
        """ FLOOD """

        return M(c="flood")(
                    M("Gauges", f="gauge")(
                        M("New", m="create"),
                        M("List All"),
                        M("Map", m="map"),
                        #M("Search", m="search"),
                        M("Import", m="import"),
                    ),
                )

    # -------------------------------------------------------------------------
    def gis(self):
        """ GIS / GIS Controllers """

        MAP_ADMIN = current.session.s3.system_roles.MAP_ADMIN

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
                    M("Fullscreen Map", f="map_viewing_client"),
                    # Currently not got geocoding support
                    #M("Bulk Uploader", c="doc", f="bulk_upload"),
                    M("Locations", f="location")(
                        M("Add Location", m="create"),
                        #M("Add Location Group", m="create", vars={"group": 1}),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import from CSV", m="import", restrict=[MAP_ADMIN]),
                        M("Import from OpenStreetMap", m="import_poi", restrict=[MAP_ADMIN]),
                        #M("Geocode", f="geocode_manual"),
                    ),
                    M("Population Report", f="location", m="report",
                      vars=dict(rows="name",
                                fact="population",
                                aggregate="sum")),
                    M("Configuration", f="config", args=config_args(),
                      _id="gis_menu_config",
                      check=config_menu),
                    M("Admin", restrict=[MAP_ADMIN])(
                        M("Hierarchy", f="hierarchy"),
                        M("Layers", f="catalog"),
                        M("Markers", f="marker"),
                        M("Projections", f="projection"),
                        M("Symbology", f="symbology"),
                    )
                )

    # -------------------------------------------------------------------------
    def hms(self):
        """ HMS / Hospital Status Assessment and Request Management """

        #s3 = current.response.s3

        return M(c="hms")(
                    M("Hospitals", f="hospital", m="search")(
                        M("New", m="create"),
                        M("List All"),
                        M("Map", m="map"),
                        M("Search", m="search"),
                        #SEP(),
                        #M("Show Map", c="gis", f="map_viewing_client",
                          #vars={"kml_feed" : "%s/hms/hospital.kml" %
                                #s3.base_url, "kml_name" : "Hospitals_"})
                    )
                )

    # -------------------------------------------------------------------------
    def hrm(self):
        """ HRM / Human Resources Management """

        s3 = current.session.s3
        ADMIN = s3.system_roles.ADMIN

        # Custom conditions for the check-hook, as lambdas in order
        # to have them checked only immediately before rendering:
        manager_mode = lambda i: s3.hrm.mode is None
        personal_mode = lambda i: s3.hrm.mode is not None
        is_org_admin = lambda i: s3.hrm.orgs and True or \
                                 ADMIN in s3.roles
        settings = current.deployment_settings
        job_roles = lambda i: settings.get_hrm_job_roles()
        use_teams = lambda i: settings.get_hrm_use_teams()

        return M(c="hrm")(
                    M("Staff", f="staff",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", f="person", m="import",
                          vars={"group":"staff"}, p="create"),
                    ),
                    M("Teams", f="group",
                      check=[manager_mode, use_teams])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Department Catalog", f="department",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Job Role Catalog", f="job_role",
                      check=[manager_mode, job_roles])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Job Title Catalog", f="job_title",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Skill Catalog", f="skill",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                        #M("Skill Provisions", f="skill_provision"),
                    ),
                    M("Training Events", f="training_event",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Search Training Participants", f="training",
                          m="search"),
                        M("Import Participant List", f="training", m="import"),
                    ),
                    M("Training Course Catalog", f="course",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                        #M("Course Certificates", f="course_certificate"),
                    ),
                    M("Certificate Catalog", f="certificate",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                        #M("Skill Equivalence", f="certificate_skill"),
                    ),
                    M("Reports", f="staff", m="report",
                      check=manager_mode)(
                        M("Staff Report", m="report"),
                        M("Expiring Staff Contracts Report",
                          vars=dict(expiring=1)),
                        M("Training Report", f="training", m="report"),
                    ),
                    M("Personal Profile", f="person",
                      check=personal_mode, vars=dict(mode="personal")),
                    # This provides the link to switch to the manager mode:
                    M("Staff Management", f="index",
                      check=[personal_mode, is_org_admin]),
                    # This provides the link to switch to the personal mode:
                    M("Personal Profile", f="person",
                      check=manager_mode, vars=dict(mode="personal"))
                )

    # -------------------------------------------------------------------------
    def vol(self):
        """ Volunteer Management """

        s3 = current.session.s3
        ADMIN = s3.system_roles.ADMIN

        # Custom conditions for the check-hook, as lambdas in order
        # to have them checked only immediately before rendering:
        manager_mode = lambda i: s3.hrm.mode is None
        personal_mode = lambda i: s3.hrm.mode is not None
        is_org_admin = lambda i: s3.hrm.orgs and True or \
                                 ADMIN in s3.roles

        settings = current.deployment_settings
        job_roles = lambda i: settings.get_hrm_job_roles()
        show_programmes = lambda i: settings.get_hrm_vol_experience() == "programme"
        show_tasks = lambda i: settings.has_module("project") and \
                               settings.get_project_mode_task()
        use_teams = lambda i: settings.get_hrm_use_teams()

        if job_roles(""):
            jt_catalog_label = "Job Title Catalog"
        else:
            jt_catalog_label = "Volunteer Role Catalog"

        return M(c="vol")(
                    M("Volunteers", f="volunteer",
                      check=[manager_mode])(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", f="person", m="import",
                          vars={"group":"volunteer"}, p="create"),
                    ),
                    M("Teams", f="group",
                      check=[manager_mode, use_teams])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Department Catalog", f="department",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Job Role Catalog", f="job_role",
                      check=[manager_mode, job_roles])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M(jt_catalog_label, f="job_title",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Skill Catalog", f="skill",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                        #M("Skill Provisions", f="skill_provision"),
                    ),
                    M("Training Events", f="training_event",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Search Training Participants", f="training",
                          m="search"),
                        M("Import Participant List", f="training", m="import"),
                    ),
                    M("Training Course Catalog", f="course",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                        #M("Course Certificates", f="course_certificate"),
                    ),
                    M("Certificate Catalog", f="certificate",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                        #M("Skill Equivalence", f="certificate_skill"),
                    ),
                    M("Programmes", f="programme",
                      check=[manager_mode, show_programmes])(
                        M("New", m="create"),
                        M("List All"),
                        M("Import Hours", f="programme_hours", m="import"),
                    ),
                    M("Reports", f="volunteer", m="report",
                      check=manager_mode)(
                        M("Volunteer Report", m="report"),
                        M("Training Report", f="training", m="report"),
                    ),
                    M("My Profile", f="person",
                      check=personal_mode, vars=dict(mode="personal")),
                    M("My Tasks", f="task",
                      check=[personal_mode, show_tasks],
                      vars=dict(mode="personal",
                                mine=1)),
                    # This provides the link to switch to the manager mode:
                    M("Volunteer Management", f="index",
                      check=[personal_mode, is_org_admin]),
                    # This provides the link to switch to the personal mode:
                    M("Personal Profile", f="person",
                      check=manager_mode, vars=dict(mode="personal"))
                )

    # -------------------------------------------------------------------------
    def inv(self):
        """ INV / Inventory """

        ADMIN = current.session.s3.system_roles.ADMIN

        current.s3db.inv_recv_crud_strings()
        crud_strings = current.response.s3.crud_strings
        inv_recv_list = crud_strings.inv_recv.title_list
        inv_recv_search = crud_strings.inv_recv.title_search

        use_commit = lambda i: current.deployment_settings.get_req_use_commit()

        return M()(
                    #M("Home", f="index"),
                    M("Warehouses", c="inv", f="warehouse")(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", m="import", p="create"),
                    ),
                    M("Warehouse Stock", c="inv", f="inv_item")(
                        M("Search", f="inv_item", m="search"),
                        M("Search Shipped Items", f="track_item", m="search"),
                        M("Adjust Stock Levels", f="adj"),
                        M("Kitting", f="kit"),
                        M("Import", f="inv_item", m="import", p="create"),
                    ),
                    M("Reports", c="inv", f="inv_item")(
                        M("Warehouse Stock", f="inv_item",m="report"),
                        M("Expiration Report", c="inv", f="track_item",
                          m="search", vars=dict(report="exp")),
                        M("Monetization Report", c="inv", f="inv_item",
                          m="search", vars=dict(report="mon")),
                        M("Utilization Report", c="inv", f="track_item",
                          m="search", vars=dict(report="util")),
                        M("Summary of Incoming Supplies", c="inv", f="track_item",
                          m="search", vars=dict(report="inc")),
                        M("Summary of Releases", c="inv", f="track_item",
                          m="search", vars=dict(report="rel")),
                    ),
                    M(inv_recv_list, c="inv", f="recv")(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                    ),
                    M("Sent Shipments", c="inv", f="send")(
                        M("New", m="create"),
                        M("List All"),
                        M("Search Shipped Items", f="track_item", m="search"),
                    ),
                    M("Items", c="supply", f="item")(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Report", m="report"),
                        M("Import", m="import", p="create"),
                    ),
                    # Catalog Items moved to be next to the Item Categories
                    #M("Catalog Items", c="supply", f="catalog_item")(
                       #M("New", m="create"),
                       #M("List All"),
                       #M("Search", m="search"),
                    #),
                    M("Catalogs", c="supply", f="catalog")(
                        M("New", m="create"),
                        M("List All"),
                        #M("Search", m="search"),
                    ),
                    M("Item Categories", c="supply", f="item_category",
                      restrict=[ADMIN])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Suppliers", c="inv", f="supplier")(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", m="import", p="create"),
                    ),
                    M("Facilities", c="inv", f="facility")(
                        M("New", m="create"),
                        M("List All"),
                        #M("Search", m="search"),
                    ),
                    M("Requests", c="req", f="req")(
                        M("New", m="create"),
                        M("List All"),
                        M("Requested Items", f="req_item"),
                        #M("Search Requested Items", f="req_item", m="search"),
                    ),
                    M("Commitments", c="req", f="commit", check=use_commit)(
                        M("List All")
                    ),
                )

    # -------------------------------------------------------------------------
    def irs(self):
        """ IRS / Incident Report System """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="irs")(
                    M("Incident Reports", f="ireport")(
                        M("Add Incident Report", m="create"),
                        M("List All"),
                        M("Open Incidents", vars={"open":1}),
                        M("Map", m="map"),
                        M("Timeline", args="timeline"),
                        M("Import", m="import"),
                        M("Search", m="search"),
                        M("Report", m="report",
                          vars=dict(rows="L1",
                                    cols="category",
                                    fact="datetime",
                                    aggregate="count"))
                    ),
                    M("Incident Categories", f="icategory", restrict=[ADMIN])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Ushahidi Import", f="ireport", restrict=[ADMIN],
                      args="ushahidi")
                )

    # -------------------------------------------------------------------------
    def cap(self):
        """ CAP menu """

        T = current.T

        session = current.session
        ADMIN = session.s3.system_roles.ADMIN

        return M(c="cap")(
                    M("Alerts", f="alert", vars={'alert.is_template': 'false'})(
                        M("List alerts", f="alert", vars={'alert.is_template': 'false'}),
                        M("Create alert", f="alert", m="create"),
                        M("Search & Subscribe", m="search"),
                    ),
                    M("Templates", f="template", vars={'alert.is_template': 'true'})(
                        M("List templates", f="template", vars={'alert.is_template': 'true'}),
                        M("Create template", f="template", m="create"),
                    ),
                    #M("CAP Profile", f="profile")(
                    #    M("Edit profile", f="profile")
                    #)
                )

    # -------------------------------------------------------------------------
    def security(self):
        """ Security Management System """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="security")(
                    M("Incident Reports", c="irs", f="ireport")(
                        M("New", m="create"),
                        M("List All"),
                        M("Open Incidents", vars={"open":1}),
                        M("Map", m="map"),
                        M("Timeline", args="timeline"),
                        M("Import", m="import"),
                        M("Search", m="search"),
                        M("Report", m="report",
                          vars=dict(rows="L1",
                                    cols="category",
                                    fact="datetime",
                                    aggregate="count"))
                    ),
                    M("Incident Categories", c="irs", f="icategory",
                      restrict=[ADMIN])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Facilities", c="org", f="facility")(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Facility Types", c="org", f="facility_type",
                      restrict=[ADMIN])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Zones", f="zone")(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Zone Types", f="zone_type", restrict=[ADMIN])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Personnel", f="staff")(
                        M("New", m="create"),
                        M("List All Security-related Staff"),
                        M("List All Essential Staff", f="essential", m="search"),
                    ),
                    M("Security Staff Types", f="staff_type", restrict=[ADMIN])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    #M("Ushahidi Import", c="irs", f="ireport", restrict=[ADMIN],
                    #  args="ushahidi")
                )

    # -------------------------------------------------------------------------
    def scenario(self):
        """ SCENARIO """

        # Use EVENT menu
        return self.event()

    # -------------------------------------------------------------------------
    def supply(self):
        """ SUPPLY """

        # Use INV menu
        return self.inv()

    # -------------------------------------------------------------------------
    def survey(self):
        """ SURVEY / Survey """

        ADMIN = current.session.s3.system_roles.ADMIN

        # Do we have a series_id?
        series_id = False
        vars = Storage()
        try:
            series_id = int(current.request.args[0])
        except:
            try:
                (dummy, series_id) = current.request.vars["viewing"].split(".")
                series_id = int(series_id)
            except:
                pass
        if series_id:
            vars.viewing = "survey_complete.%s" % series_id

        return M(c="survey")(
                    M("Assessment Templates", f="template")(
                        M("Add Assessment Templates", m="create"),
                        M("List All"),
                    ),
                    #M("Section", f="section")(
                    #    M("New", args="create"),
                    #    M("List All"),
                    #),
                    M("Disaster Assessments", f="series")(
                        M("Add Disaster Assessments", m="create"),
                        M("List All"),
                    ),
                    M("Administration", f="complete", restrict=[ADMIN])(
                        #M("New", m="create"),
                        #M("List All"),
                        M("Import Templates", f="question_list",
                          m="import", p="create"),
                        M("Import Template Layout", f="formatter",
                          m="import", p="create"),
                        M("Import Completed Assessment Forms", f="complete",
                          m="import", p="create", vars=vars, check=series_id),
                    ),
                )

    # -------------------------------------------------------------------------
    def member(self):
        """ Membership Management """

        return M(c="member")(
                    M("Members", f="membership")(
                        M("Add Member", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", f="person", m="import"),
                    ),
                    M("Membership Types", f="membership_type")(
                        M("Add Membership Type", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", f="person", m="import"),
                    ),
                )

    # -------------------------------------------------------------------------
    def mpr(self):
        """ MPR / Missing Person Registry """

        return M(c="mpr")(
                    M("Missing Persons", f="person")(
                        M("New", m="create"),
                        M("Search", f="index"),
                        M("List All"),
                    ),
                )

    # -------------------------------------------------------------------------
    def msg(self):
        """ MSG / Messaging """

        ADMIN = current.session.s3.system_roles.ADMIN

        if current.request.function in ("setting",
                                        "email_settings",
                                        "modem_settings",
                                        "smtp_to_sms_settings",
                                        "api_settings",
                                        "tropo_settings",
                                        "twitter_settings"):
            return self.admin()

        settings_messaging = self.settings_messaging()

        return M(c="msg")(
                    M("Compose", f="compose"),
                    M("Distribution groups", f="group")(
                        M("List/Add", f="group"),
                        M("Group Memberships", f="group_membership"),
                    ),
                    M("Email InBox", f="email_inbox"),
                    M("Twilio SMS InBox", f="twilio_inbox"),
                    M("Log", f="log"),
                    M("Outbox", f="outbox"),
                    M("Search Twitter Tags", f="twitter_search")(
                       M("Keywords", f="keyword"),
                       M("Senders", f="sender"),
                       M("Queries", f="twitter_search"),
                       M("Results", f="twitter_search_results")
                    ),
                    M("CAP", translate=False, f="tbc"),
                    M("Administration", restrict=[ADMIN])(settings_messaging)
                )


    # -------------------------------------------------------------------------
    def org(self):
        """ ORG / Organization Registry """

        ADMIN = current.session.s3.system_roles.ADMIN
        SECTORS = "Clusters" if current.deployment_settings.get_ui_cluster() \
                             else "Sectors"

        return M(c="org")(
                    M("Organizations", f="organisation")(
                        M("Add Organization", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", m="import")
                    ),
                    M("Offices", f="office")(
                        M("New", m="create"),
                        M("List All"),
                        M("Map", m="map"),
                        M("Search", m="search"),
                        M("Import", m="import")
                    ),
                    M("Facilities", f="facility")(
                        M("New", m="create"),
                        M("List All"),
                        M("Map", m="map"),
                        M("Search", m="search"),
                        M("Import", m="import")
                    ),
                    M("Organization Types", f="organisation_type",
                      restrict=[ADMIN])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Office Types", f="office_type",
                      restrict=[ADMIN])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Facility Types", f="facility_type",
                      restrict=[ADMIN])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M(SECTORS, f="sector", restrict=[ADMIN])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                )

    # -------------------------------------------------------------------------
    def patient(self):
        """ PATIENT / Patient Tracking """

        return M(c="patient")(
                    M("Patients", f="patient")(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search")
                    )
                )

    # -------------------------------------------------------------------------
    def pr(self):
        """ PR / Person Registry """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="pr", restrict=ADMIN)(
                    M("Person", f="person")(
                        M("Add Person", m="create"),
                        M("Search", f="index"),
                        M("List All"),
                    ),
                    M("Groups", f="group")(
                        M("New", m="create"),
                        M("List All"),
                    ),
                )

    # -------------------------------------------------------------------------
    def proc(self):
        """ PROC / Procurement """

        return M(c="proc")(
                    M("Home", f="index"),
                    M("Procurement Plans", f="plan")(
                        M("New", m="create"),
                        M("List All"),
                        #M("Search", m="search"),
                    ),
                    M("Suppliers", f="supplier")(
                        M("New", m="create"),
                        M("List All"),
                        #M("Search", m="search")
                    ),
                )

    # -------------------------------------------------------------------------
    def project(self):
        """ PROJECT / Project Tracking & Management """

        ADMIN = current.session.s3.system_roles.ADMIN

        settings = current.deployment_settings
        #activities = settings.get_project_activities()
        community = settings.get_project_community()
        if community:
            IMPORT = "Import Project Communities"
        else:
            IMPORT = "Import Project Locations"

        menu = M(c="project")

        if settings.get_project_mode_3w():
            if community:
                menu(
                     M("Projects", f="project")(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                     ),
                     M("Communities", f="location")(
                        M("List All"),
                        M("Map", m="map"),
                        M("Search", m="search"),
                        M("List All Community Contacts", f="location_contact"),
                        M("Search Community Contacts", f="location_contact",
                          m="search"),
                     ),
                    )
            else:
                menu(
                     M("Projects", f="project")(
                        M("New", m="create"),
                        M("List All"),
                        M("Map", f="location", m="map"),
                        M("Search", m="search"),
                     )
                    )
            stats = lambda i: settings.has_module("stats")
            menu(
                 M("Reports", f="location", m="report")(
                    M("3W", f="location", m="report"),
                    M("Beneficiaries", f="beneficiary", m="report",
                      check = stats,
                      ),
                    M("Funding", f="organisation", args="report"),
                 ),
                 M("Import", f="index", p="create")(
                    M("Import Projects", f="project",
                      m="import", p="create"),
                    M("Import Project Organizations", f="organisation",
                      m="import", p="create"),
                    M(IMPORT, f="location",
                      m="import", p="create"),
                 ),
                M("Partner Organizations",  f="partners")(
                    M("New", m="create"),
                    M("List All"),
                    M("Search", m="search"),
                    M("Import", m="import", p="create"),
                ),
                 M("Themes", f="theme")(
                    M("New", m="create"),
                    M("List All"),
                 ),
                 M("Activity Types", f="activity_type")(
                    M("New", m="create"),
                    M("List All"),
                    #M("Search", m="search")
                 ),
                 M("Beneficiary Types", f="beneficiary_type",
                   check = stats,)(
                    M("New", m="create"),
                    M("List All"),
                 ),
                )

            if settings.get_project_mode_drr():
                menu(
                     M("Hazards", f="hazard")(
                        M("New", m="create"),
                        M("List All"),
                     )
                    )
            # if settings.get_project_sectors():
                # menu(
                     # M("Sectors", c="org", f="sector")(
                        # M("New", m="create"),
                        # M("List All"),
                     # )
                    # )

        elif settings.get_project_mode_task():
            menu(
                 M("Projects", f="project")(
                    M("New", m="create"),
                    M("List All"),
                    M("Open Tasks for Project", vars={"tasks":1}),
                 ),
                 M("Tasks", f="task")(
                    M("New", m="create"),
                    #M("List All Tasks"),
                    M("Search", m="search"),
                 ),
                )
            if current.auth.s3_has_role("STAFF"):
                menu(
                     M("Daily Work", f="time")(
                        M("My Logged Hours", vars={"mine":1}),
                        M("Last Week's Work", m="report",
                          vars=Storage(rows="person_id",
                                       cols="day",
                                       fact="hours",
                                       aggregate="sum",
                                       week=1)),
                        M("My Open Tasks", f="task", vars={"mine":1}),
                     ),
                     M("Admin", restrict=[ADMIN])(
                        M("Activity Types", f="activity_type"),
                        M("Import Tasks", f="task", m="import", p="create"),
                     ),
                     M("Reports", f="report")(
                        M("Activity Report", f="activity", m="report"),
                        M("Project Time Report", f="time", m="report"),
                     ),
                    )
        else:
            menu(
                 M("Projects", f="project")(
                    M("New", m="create"),
                    M("List All"),
                    M("Search", m="search"),
                    M("Import", m="import", p="create"),
                 ),
                )

        return menu

    # -------------------------------------------------------------------------
    def req(self):
        """ REQ / Request Management """

        settings = current.deployment_settings
        use_commit = lambda i: settings.get_req_use_commit()
        req_skills = lambda i: "People" in settings.get_req_req_type()

        return M(c="req")(
                    M("Requests", f="req")(
                        M("New", m="create"),
                        M("List All"),
                        M("List All Requested Items", f="req_item"),
                        M("List All Requested Skills", f="req_skill",
                          check=req_skills),
                        #M("Search Requested Items", f="req_item", m="search"),
                    ),
                    M("Commitments", f="commit", check=use_commit)(
                        M("List All")
                    ),
                )

    # -------------------------------------------------------------------------
    def stats(self):
        """ Statistics """

        return M(c="stats")(
                    M("Demographics", f="demographic")(
                        M("New", m="create"),
                        M("List All"),
                        #M("Search", m="search"),
                    ),
                    M("Demographic Data", f="demographic_data")(
                        M("New", m="create"),
                        M("Import", m="import"),
                        M("List All"),
                        #M("Search", m="search"),
                    ),
                )

    # -------------------------------------------------------------------------
    def sync(self):
        """ SYNC menu """

        # Use admin menu
        return self.admin()

    # -------------------------------------------------------------------------
    def transport(self):
        """ TRANSPORT """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="transport")(
                    M("Airports", f="airport")(
                        M("New", m="create"),
                        M("Import", m="import", restrict=[ADMIN]),
                        M("List All"),
                        M("Map", m="map"),
                        #M("Search", m="search"),
                    ),
                    M("Seaports", f="seaport")(
                        M("New", m="create"),
                        M("Import", m="import", restrict=[ADMIN]),
                        M("List All"),
                        M("Map", m="map"),
                        #M("Search", m="search"),
                    ),
                )

    # -------------------------------------------------------------------------
    def vehicle(self):
        """ VEHICLE / Vehicle Tracking """

        return M(c="vehicle")(
                    M("Vehicles", f="vehicle")(
                        M("New", m="create"),
                        M("List All"),
                        M("Map", m="map"),
                        M("Search", m="search"),
                    ),
                    M("Vehicle Types", f="item")(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                    ),
                )

    # -------------------------------------------------------------------------
    def vulnerability(self):
        """ Vulnerability """

        return M(c="vulnerability")(
                    M("Indicators", f="indicator")(
                        M("New", m="create"),
                        M("List All"),
                        #M("Search", m="search"),
                    ),
                    M("Data", f="data")(
                        M("New", m="create"),
                        M("Import", m="import"),
                        M("List All"),
                        #M("Search", m="search"),
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
        """

        return [
            M("Email Settings", c="msg", f="inbound_email_settings"),
            M("Parsing Settings", c="msg", f="workflow"),
            M("SMS Settings", c="msg", f="setting",
                args=[1], m="update"),
            M("Twilio SMS Settings", c="msg", f="twilio_inbound_settings"),
            M("Twitter Settings", c="msg", f="twitter_settings",
                args=[1], m="update")
        ]

    # -------------------------------------------------------------------------
    @classmethod
    def breadcrumbs(cls):
        """ Breadcrumbs from the current options menu """

        # Configure the layout:
        layout = S3BreadcrumbsLayout

        request = current.request
        controller = request.controller
        function = request.function
        all_modules = current.deployment_settings.modules

        # Start with a link to the homepage - always:
        breadcrumbs = layout()(
            layout(all_modules["default"].name_nice)
        )

        # Append the current module's homepage - always:
        # @note: this may give a breadcrumb for which there's no menu item
        # and should therefore perhaps be replaced by a real path-check in
        # the main menu?
        if controller != "default":
            try:
                breadcrumbs(
                    layout(all_modules[controller].name_nice, c=controller)
                )
            except:
                # Module not defined
                pass

        # This checks the path in the options menu, omitting the top-level item
        # (because that's the menu itself which doesn't have a linked label):
        menu = current.menu.options
        if menu and function != "index":
            branch = menu.branch()
            path = branch.path()
            if len(path) > 1:
                for item in path[1:]:
                    breadcrumbs(
                        layout(item.label,
                               c=item.get("controller"),
                               f=item.get("function"),
                               args=item.args,
                               # Should we retain the request vars in case
                               # the item has no vars? Or shall we merge them
                               # in any case? Didn't see the use-case yet
                               # anywhere...
                               vars=item.vars))
        return breadcrumbs

# END =========================================================================
