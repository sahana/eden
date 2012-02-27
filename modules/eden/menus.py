# -*- coding: utf-8 -*-

""" Sahana-Eden Menu Structure and Layout

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
class S3MainMenu:
    """ The default configurations for the main application menu """

    @staticmethod
    def menu_modules():

        request = current.request
        response = current.response
        auth = current.auth
        settings = current.deployment_settings

        s3 = current.response.s3

        # ---------------------------------------------------------------------
        # Modules Menu
        # @todo: this is very ugly - cleanup or make a better solution
        # @todo: probably define the menu explicitly?
        #
        menu_modules = []

        # Home always 1st
        module = settings.modules["default"]
        menu_modules.append(MM(module.name_nice, c="default", f="index"))

        # Modules to hide due to insufficient permissions
        all_modules = settings.modules
        hidden_modules = auth.permission.hidden_modules()

        has_role = auth.s3_has_role

        # The Modules to display at the top level (in order)
        for module_type in [1, 2, 3, 4, 5, 6]:
            for module in all_modules:
                if module in hidden_modules:
                    continue
                _module = all_modules[module]
                if (_module.module_type == module_type):
                    if not _module.access:
                        menu_modules.append(MM(_module.name_nice, c=module, f="index"))
                    else:
                        authorised = False
                        groups = re.split("\|", _module.access)[1:-1]
                        for group in groups:
                            if has_role(group):
                                authorised = True
                                break
                        if authorised == True:
                            menu_modules.append(MM(_module.name_nice, c=module, f="index"))

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
                    authorised = False
                    groups = re.split("\|", _module.access)[1:-1]
                    for group in groups:
                        if has_role(group):
                            authorised = True
                    if authorised == True:
                        modules_submenu.append(MM(_module.name_nice, c=module, f="index"))

        if modules_submenu:
            # Only show the 'more' menu if there are entries in the list
            module_more_menu = MM("more", link=False)(modules_submenu)
            menu_modules.append(module_more_menu)

        return menu_modules

    # -------------------------------------------------------------------------
    @staticmethod
    def menu_lang(**attr):
        """ Language menu """

        s3 = current.response.s3
        request = current.request

        settings = current.deployment_settings
        if not settings.get_L10n_display_toolbar():
            return None

        menu_lang = MM("Language", **attr)
        for language in s3.l10n_languages:
            menu_lang.append(MM(s3.l10n_languages[language], r=request,
                             vars={"_language":language}))
        return menu_lang

    # -------------------------------------------------------------------------
    @staticmethod
    def menu_help(**attr):
        """ Help Menu """

        menu_help = MM("Help", **attr)(
            MM("Contact us", c="default", f="contact"),
            MM("About", c="default", f="about")
        )
        return menu_help

    # -------------------------------------------------------------------------
    @staticmethod
    def menu_auth(**attr):
        """ Auth Menu """

        T = current.T
        session = current.session

        request = current.request
        auth = current.auth
        settings = current.deployment_settings

        logged_in = auth.is_logged_in()
        self_registration = settings.get_security_self_registration()

        if not logged_in:

            login_next = URL(args=request.args, vars=request.vars)
            if request.controller == "default" and \
               request.function == "user" and \
               "_next" in request.get_vars:
                login_next = request.get_vars["_next"]

            menu_auth = MM("Login", c="default", f="user", m="login",
                           vars=dict(_next=login_next), **attr)(
                            MM("Login", m="login",
                               vars=dict(_next=login_next),
                               check=self_registration),
                            MM("Register", m="register",
                               vars=dict(_next=login_next),
                               check=self_registration),
                            MM("Lost Password", m="retrieve_password")
                        )
        else:
            menu_auth = MM(auth.user.email, c="default", f="user",
                           translate=False, link=False, **attr)(
                            MM("Logout", m="logout"),
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
                            MM({"name": T("Rapid Data Entry"),
                               "id": "rapid_toggle",
                               "value": session.s3.rapid_data_entry is True},
                               f="rapid"),
                        )

        return menu_auth

    # -------------------------------------------------------------------------
    @staticmethod
    def menu_admin(**attr):
        """ Administrator Menu """

        session = current.session
        ADMIN = session.s3.system_roles.ADMIN

        settings = current.deployment_settings
        module = settings.modules["admin"]

        menu_admin = MM(module.name_nice, c="admin",
                        restrict=[ADMIN], **attr)(
                            MM("Settings", f="settings"),
                            MM("Users", f="user"),
                            MM("Database", c="appadmin", f="index"),
                            MM("Import", f="import_file"),
                            MM("Synchronization", c="sync", f="index"),
                            MM("Tickets", f="errors"),
                        )

        return menu_admin

    # -------------------------------------------------------------------------
    @staticmethod
    def menu_gis(**attr):
        """ GIS Config Menu """

        settings = current.deployment_settings
        if not settings.get_gis_menu():
            return None

        T = current.T
        db = current.db
        gis = current.gis
        auth = current.auth
        s3db = current.s3db
        request = current.request
        session = current.session

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
                if config != session.s3.gis_config_id:
                    config = gis.set_config(config)
                    if settings.has_module("event"):
                        # See if this config is associated with an Event
                        table = s3db.event_config
                        query = (table.config_id == config)
                        event = db(query).select(table.event_id,
                                                 limitby=(0, 1)).first()
                        if event:
                            session.s3.event = event.event_id
                        else:
                            session.s3.event = None
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

        gis_menu = MM(settings.get_gis_menu(), c="gis", f="config", **attr)
        if len(configs):
            # Use short names for the site and personal configs else they'll wrap.
            # Provide checkboxes to select between pages
            gis_menu(
                    MM({"name": T("Default Map"),
                        "id": "gis_menu_id_0",
                        # @ToDo: Show when default item is selected without having
                        # to do a DB query to read the value
                        #"value": session.s3.gis_config_id == 0,
                        "request_type": "load"
                       }, args=request.args, vars={"_config": 0}
                    )
                )
            for config in configs:
                gis_menu(
                    MM({"name": T(config.name),
                        "id": "gis_menu_id_%s" % config.id,
                        # Currently not working on 1st request afterwards as being set after this (in zz_last.py)
                        "value": session.s3.gis_config_id == config.id,
                        "request_type": "load"
                       }, args=request.args, vars={"_config": config.id}
                    )
                )
        return gis_menu

# =============================================================================
class S3OptionsMenu:
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

        if name in self.__class__.__dict__:
            self.menu = getattr(self, name)()
        else:
            self.menu = None

    # -------------------------------------------------------------------------
    def admin(self):
        """ ADMIN menu """

        session = current.session
        ADMIN = session.s3.system_roles.ADMIN

        settings_messaging = self.settings_messaging()

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
                        M("Import", c="admin", f="import_file"),
                        #M("Import", c="admin", f="import_data"),
                        #M("Export", c="admin", f="export_data"),
                        #M("Import Jobs", c="admin", f="import_job"),
                        M("Raw Database access", c="appadmin", f="index")
                    ),
                    M("Synchronization", c="sync", f="index")(
                        M("Settings", f="config", args=[1], m="update"),
                        M("Repositories", f="repository"),
                        M("Log", f="log"),
                    ),
                    #M("Edit Application", a="admin", c="default", f="design",
                      #args=[request.application]),
                    M("Tickets", c="admin", f="errors"),
                    M("Portable App", c="admin", f="portable")
                )

    # -------------------------------------------------------------------------
    def assess(self):
        """ ASSESS Menu """

        session = current.session
        ADMIN = session.s3.system_roles.ADMIN

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
                        M("Import", m="import", p="create"),
                        M("Report", m="report",
                          vars=dict(rows="item_id$item_category_id",
                                    cols="L1",
                                    fact="number",
                                    aggregate="count")),
                    ),
                    M("Items", f="item")(
                        M("New", m="create"),
                        M("List All"),
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

        session = current.session
        ADMIN = session.s3.system_roles.ADMIN

        # @ToDo - Fix s3.crud_strings["cr_shelter"].subtitle_list
        settings = current.deployment_settings
        if settings.get_ui_camp():
            shelter = "Camps"
            types = "Camp Types and Services"
        else:
            shelter = "Shelters"
            types = "Shelter Types and Services"

        return M(c="cr")(
                    M(shelter, f="shelter")(
                        M("New", m="create"),
                        M("List All"),
                        # @ToDo Search by type, services, location, available space
                        #M("Search", m="search"),
                    ),
                    M(types, f="shelter_type", restrict=[ADMIN])(
                        M("List / Add Services", m="create"),
                        M("List / Add Types"),
                    )
                )

    # -------------------------------------------------------------------------
    def delphi(self):
        """ DELPHI / Delphi Decision Maker """

        session = current.session
        ADMIN = session.s3.system_roles.ADMIN

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
    def event(self):
        """ EVENT / Event Module """

        return M()(
                    M("Scenarios", c="scenario", f="scenario")(
                        M("New Scenario", m="create"),
                        M("View All"),
                    ),
                    M("Events", c="event", f="event")(
                        M("New Event", m="create"),
                        M("View All")
                    )
                )

    # -------------------------------------------------------------------------
    def fire(self):
        """ FIRE """

        return M(c="fire")(
                    M("Fire Stations", f="station")(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import Stations", m="import"),
                        M("Import Vehicles", f="station_vehicle", m="import"),
                    ),
                    M("Water Sources", f="water_source")(
                        M("New", m="create"),
                        M("List All"),
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
    def gis(self):
        """ GIS / GIS Controllers """

        session = current.session
        MAP_ADMIN = session.s3.system_roles.MAP_ADMIN

        return M(c="gis")(
                    M("Fullscreen Map", f="map_viewing_client"),
                    M("Locations", f="location")(
                        M("New Location", m="create"),
                        M("New Location Group", m="create", vars={"group": 1}),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", m="import"),
                        #M("Geocode", f="geocode_manual"),
                    ),
                    M("Configuration", f="config"),
                    # Currently not got geocoding support
                    #M("Bulk Uploader", c="doc", f="bulk_upload")
                    M("Admin", restrict=[MAP_ADMIN])(
                        M("Hierarchy", f="hierarchy"),
                        M("Markers", f="marker"),
                        M("Projections", f="projection"),
                        M("Symbology", f="symbology"),
                    )
                )

    # -------------------------------------------------------------------------
    def hms(self):
        """ HMS / Hospital Status Assessment and Request Management """

        s3 = current.response.s3

        return M(c="hms")(
                    M("Hospitals", f="hospital", m="search")(
                        M("New", m="create"),
                        M("List All"),
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

        session = current.session
        ADMIN = session.s3.system_roles.ADMIN

        # Custom conditions for the check-hook, as lambdas in order
        # to have them checked only immediately before rendering:
        manager_mode = lambda i: session.s3.hrm.mode is None
        personal_mode = lambda i: session.s3.hrm.mode is not None
        is_org_admin = lambda i: session.s3.hrm.orgs and True or \
                                 ADMIN in session.s3.roles

        staff = dict(group="staff")
        volunteers = dict(group="volunteer")

        return M(c="hrm")(
                    M("Staff", f="human_resource",
                      check=manager_mode, vars=staff)(
                        M("New Staff Member", m="create",
                          vars=staff),
                        M("List All",
                          vars=staff),
                        M("Search", m="search",
                          vars=staff),
                        M("Report", m="report",
                          vars=Storage(group="staff",
                                       rows="course",
                                       cols="L1",
                                       fact="person_id",
                                       aggregate="count")),
                        M("Report Expiring Contracts",
                          vars=dict(group="staff", expiring=1)),
                        M("Import", m="import",
                          vars=staff, p="create"),
                        #M("Dashboard", f="index"),
                    ),
                    M("Volunteers", f="human_resource",
                      check=manager_mode, vars=volunteers)(
                        M("New Volunteer", m="create",
                          vars=volunteers),
                        M("List All",
                          vars=volunteers),
                        M("Search", m="search",
                          vars=volunteers),
                        M("Report", m="report",
                          vars=Storage(group="volunteer",
                                       rows="course",
                                       cols="L1",
                                       fact="person_id",
                                       aggregate="count")),
                        M("Import", m="import",
                          vars=volunteers, p="create"),
                    ),
                    M("Teams", f="group",
                      check=manager_mode)(
                        M("New Team", m="create"),
                        M("List All"),
                    ),
                    M("Job Role Catalog", f="job_role",
                      check=manager_mode)(
                        M("New Job Role", m="create"),
                        M("List All"),
                    ),
                    M("Skill Catalog", f="skill",
                      check=manager_mode)(
                        M("New Skill", m="create"),
                        M("List All"),
                        #M("Skill Provisions", f="skill_provision"),
                    ),
                    M("Training Events", f="training_event",
                      check=manager_mode)(
                        M("New Training Event", m="create"),
                        M("List All Training Events"),
                        M("Search Training Events", m="search"),
                        M("Search Training Participants", f="training",
                          m="search"),
                        M("Training Report", f="training", m="report",
                          vars=dict(rows="training_event_id$course_id",
                                    cols="month",
                                    fact="person_id",
                                    aggregate="count")),
                        M("Import Participant List", f="training", m="import"),
                    ),
                    M("Training Course Catalog", f="course",
                      check=manager_mode)(
                        M("New Training Course", m="create"),
                        M("List All"),
                        M("Course Certificates", f="course_certificate"),
                    ),
                    M("Certificate Catalog", f="certificate",
                      check=manager_mode)(
                        M("New Certificate", m="create"),
                        M("List All"),
                        M("Skill Equivalence", f="certificate_skill"),
                    ),
                    M("Profile", f="person",
                      check=personal_mode, vars=dict(mode="personal")),
                    # This provides the link to switch to the manager mode:
                    M("Human Resources", f="index",
                      check=[personal_mode, is_org_admin]),
                    # This provides the link to switch to the personal mode:
                    M("Personal Profile", f="person",
                      check=manager_mode, vars=dict(mode="personal"))
                )

    # -------------------------------------------------------------------------
    def inv(self):
        """ INV / Inventory """

        session = current.session
        ADMIN = session.s3.system_roles.ADMIN

        crud_strings = current.response.s3.crud_strings
        inv_recv_list = crud_strings.inv_recv.subtitle_list
        inv_recv_search = crud_strings.inv_recv.title_search

        return M()(
                    #M("Home", f="index"),
                    M("Warehouses", c="inv", f="warehouse")(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", m="import", p="create"),
                    ),
                    M("Warehouse Stock", c="inv", f="warehouse")(
                        M("Search Warehouse Stock", f="inv_item", m="search"),
                        M("Report", f="inv_item", m="report"),
                        M("Import", f="inv_item", m="import", p="create"),
                    ),
                    M(inv_recv_list, c="inv", f="recv")(
                        M("New", m="create"),
                        M("List All"),
                        M(inv_recv_search, m="search"),
                    ),
                    M("Sent Shipments", c="inv", f="send")(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Items", c="supply", f="item")(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", f="catalog_item", m="search"),
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
                        M("New Item Category", m="create"),
                        M("List All"),
                    )
                )

    # -------------------------------------------------------------------------
    def irs(self):
        """ IRS / Incident Report System """

        T = current.T

        session = current.session
        ADMIN = session.s3.system_roles.ADMIN

        return M(c="irs")(
                    M("Incident Reports", f="ireport")(
                        M("New", m="create"),
                        M("List All"),
                        M("Open Incidents", vars={"open":1}),
                        M("Timeline", args="timeline"),
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
                    M("Ushahidi " + T("Import"), f="ireport", restrict=[ADMIN],
                      args="ushahidi")
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

        session = current.session
        ADMIN = session.s3.system_roles.ADMIN

        return M(c="survey")(
                    M("Assessment Templates", f="template")(
                        #M("New", m="create"),
                        M("List All"),
                    ),
                    #M("Section", f="section")(
                    #    M("New", args="create"),
                    #    M("List All"),
                    #),
                    M("Disaster Assessments", f="series")(
                        M("New", m="create"),
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
                          m="import", p="create"),
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

        session = current.session
        ADMIN = session.s3.system_roles.ADMIN

        request = current.request
        if request.function in ("setting",
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
                    M("Log", f="log"),
                    M("Outbox", f="outbox"),
                    M("Search Twitter Tags", f="twitter_search")(
                       M("Queries", f="twitter_search"),
                       M("Results", f="twitter_search_results")
                    ),
                    M("CAP", translate=False, f="tbc"),
                    M("Administration", restrict=[ADMIN])(settings_messaging)
                )


    # -------------------------------------------------------------------------
    def org(self):
        """ ORG / Organization Registry """

        return M(c="org")(
                    M("Organizations", f="organisation")(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", m="import")
                    ),
                    M("Offices", f="office")(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", m="import")
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

        session = current.session
        ADMIN = session.s3.system_roles.ADMIN

        return M(c="pr", restrict=ADMIN)(
                    M("Person", f="person")(
                        M("New", m="create"),
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

        # @todo: controller does not exist!
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

        auth = current.auth
        session = current.session
        ADMIN = session.s3.system_roles.ADMIN

        settings = current.deployment_settings
        if settings.get_project_community_activity():
            list_activities_label = "List All Communities"
            list_activity_contacts_label = "List All Community Contacts"
            import_activities_label = "Import Project Communities"
        else:
            list_activities_label = "List All Activities"
            # @ToDo: These should always be Community Contacts as that's what they are...however they shouldn't link to Activities...
            list_activity_contacts_label = "List All Activity Contacts"
            import_activities_label = "Import Project Activities"

        project_menu = M(c="project")

        if settings.get_project_drr():
            project_menu(
                    M("Projects", f="project")(
                        M("Add New Project", m="create"),
                        M("List All Projects", f="project"),
                        M(list_activities_label, f="activity"),
                        M(list_activity_contacts_label, f="activity_contact"),
                        M("Search", m="search"),
                    ),
                    M("Reports", f="report")(
                        M("Who is doing What Where", f="activity", m="report"),
                        M("Beneficiaries", f="beneficiary", m="report",
                          vars=Storage(rows="project_id",
                                       cols="beneficiary_type_id$name",
                                       fact="number",
                                       aggregate="sum")),
                        M("Funding", f="organisation", args="report"),
                    ),
                    M("Import", f="index")(
                        M("Import Projects", f="project",
                          m="import", p="create"),
                        M("Import Project Organizations", f="organisation",
                          m="import", p="create"),
                        M(import_activities_label, f="activity",
                          m="import", p="create"),
                    ),
                    M("Activity Types", f="activity_type")(
                        M("Add New Activity Type", m="create"),
                        M("List All Activity Types"),
                        #M("Search", m="search")
                    ),
                    M("Hazards", f="hazard")(
                        M("Add New Hazard", m="create"),
                        M("List All Hazards"),
                    ),
                    M("Project Themes", f="theme")(
                        M("Add New Theme", m="create"),
                        M("List All Themes"),
                    ),
                    M("Beneficiary Types", f="beneficiary_type")(
                        M("Add New Type", m="create"),
                        M("List All Types"),
                    ),
                )

        elif auth.s3_has_role("STAFF"):
            project_menu(
                    M("Projects", f="project")(
                        M("Add New Project", m="create"),
                        M("List All Projects"),
                        M("Open Tasks for Project", vars={"tasks":1}),
                    ),
                    #M("Tasks", f="task")(
                        #M("Add New Task", m="create"),
                        #M("List All Tasks"),
                        #M("Search", m="search"),
                    #),
                    M("Daily Work", f="time")(
                        M("All Tasks", f="task", m="search"),
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
                        M("Organizations", f="organisation"),
                        M("Import Tasks", f="task", m="import", p="create"),
                    ),
                    # Q: Shouldn't this be allowed for HR_ADMINs, too?
                    M("Reports", restrict=[ADMIN], f="report")(
                        M("Activity Report", f="activity", m="report",
                          vars=Storage(rows="project_id",
                                       cols="name",
                                       fact="time_actual",
                                       aggregate="sum")),
                        M("Project Time Report", f="time", m="report",
                          vars=Storage(rows="project",
                                       cols="person_id",
                                       fact="hours",
                                       aggregate="sum")),
                    ),
                )
        else:
            project_menu(
                    M("Projects", f="project")(
                        M("List All Projects"),
                    )
                )

        return project_menu

    # -------------------------------------------------------------------------
    def req(self):
        """ REQ / Request Management """

        return M(c="req")(
                    M("Requests", f="req")(
                        M("New", m="create"),
                        M("List All"),
                        M("List All Requested Items", f="req_item"),
                        M("List All Requested Skills", f="req_skill"),
                        #M("Search Requested Items", f="req_item", m="search"),
                    ),
                    M("Commitments", f="commit")(
                        M("List All")
                    ),
                )

    # -------------------------------------------------------------------------
    def sync(self):
        """ SYNC menu """

        # Use admin menu
        return self.admin()

    # -------------------------------------------------------------------------
    def vehicle(self):
        """ VEHICLE / Vehicle Tracking """

        return M(c="vehicle")(
                    #M("Home", f="index"),
                    M("Vehicles", f="vehicle")(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                    ),
                )

    # -------------------------------------------------------------------------
    def vol(self):
        """ VOL / Volunteer """

        # @todo: this module does not longer exist - remove menu?

        settings = current.deployment_settings

        # Custom conditions
        logged_in = lambda i: current.auth.user is not None
        hrm_enabled = lambda i: settings.has_module("hrm")
        project_enabled = lambda i: settings.has_module("project")

        return M(c="vol")(
                    M("My Details", f="person", check=[logged_in, hrm_enabled]),
                    M("My Tasks", f="task", check=[logged_in, project_enabled]),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def settings_messaging():
        """ Messaging settings menu items:

            These items are used in multiple menus, but each item instance can
            always only belong to one parent, so we need to re-instantiate
            with the same parameters, and therefore this is defined as a
            function here.
        """

        return [
            M("Email Settings", c="msg", f="email_settings",
                args=[1], m="update"),
            M("SMS Settings", c="msg", f="setting",
                args=[1], m="update"),
            M("Twitter Settings", c="msg", f="twitter_settings",
                args=[1], m="update")
        ]

    # -------------------------------------------------------------------------
    @staticmethod
    def breadcrumbs():
        """ Breadcrumbs from the current options menu """

        # Configure the layout:
        layout = S3BreadcrumbsLayout

        request = current.request
        settings = current.deployment_settings
        all_modules = settings.modules
        controller = request.controller
        function = request.function

        # Start with a link to the homepage - always:
        breadcrumbs = layout()(
            layout(all_modules["default"].name_nice)
        )

        # Append the current module's homepage - always:
        # @note: this may give a breadcrumb for which there's no menu item
        # and should therefore perhaps be replaced by a real path-check in
        # the main menu?
        if controller != "default":
            breadcrumbs(
                layout(all_modules[controller].name_nice, c=controller)
            )

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

