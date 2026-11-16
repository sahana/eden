"""
    Sahana Eden Menu Structure and Layout

    @copyright: 2011-2021 (c) Sahana Software Foundation
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

__all__ = ("MainMenu",
           "OptionsMenu",
           )

import re

from gluon import current, URL
from gluon.storage import Storage

from ..tools import IS_ISO639_2_LANGUAGE_CODE
from .layouts import M, MM, MP, ML, MA, OM, MOA, BreadcrumbsLayout

# =============================================================================
class MainMenu:
    """ The default configurations for the main application menu """

    # -------------------------------------------------------------------------
    @classmethod
    def menu(cls):

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

        # ---------------------------------------------------------------------
        # Modules Menu
        #
        # Show all enabled modules in a way where it is easy to move them around
        # without having to redefine a full menu
        #
        # @todo: this is very ugly - cleanup or make a better solution
        # @todo: probably define the menu explicitly?
        #
        menu_modules = []
        all_modules = current.deployment_settings.modules

        # Modules to hide due to insufficient permissions
        hidden_modules = current.auth.permission.hidden_modules()

        # The Modules to display at the top level (in order)
        for module_type in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            for module in all_modules:
                if module in hidden_modules:
                    continue
                _module = all_modules[module]
                if _module.get("module_type") == module_type:
                    access = _module.get("access")
                    if access:
                        groups = re.split(r"\|", access)[1:-1]
                        menu_modules.append(MM(_module.get("name_nice"),
                                               c = module,
                                               f = "index",
                                               restrict = groups,
                                               ))
                    else:
                        menu_modules.append(MM(_module.get("name_nice"),
                                               c = module,
                                               f = "index",
                                               ))

        # Modules to display off the 'more' menu
        modules_submenu = []
        for module in all_modules:
            if module in hidden_modules:
                continue
            _module = all_modules[module]
            if _module.get("module_type") == 10:
                access = _module.get("access")
                if access:
                    groups = re.split(r"\|", access)[1:-1]
                    modules_submenu.append(MM(_module.get("name_nice"),
                                              c = module,
                                              f = "index",
                                              restrict = groups,
                                              ))
                else:
                    modules_submenu.append(MM(_module.get("name_nice"),
                                              c = module,
                                              f = "index",
                                              ))

        if modules_submenu:
            # Only show the 'more' menu if there are entries in the list
            module_more_menu = MM("more", link=False)(modules_submenu)
            menu_modules.append(module_more_menu)

        return menu_modules

    # -------------------------------------------------------------------------
    @classmethod
    def menu_org(cls):
        """ Organisation Logo and Name """

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

        ADMIN = current.auth.get_system_roles().ADMIN

        if not auth.is_logged_in():
            request = current.request
            login_next = URL(args=request.args, vars=request.get_vars)
            if request.controller == "default" and request.function == "user":
                login_next = auth.get_vars_next() or login_next

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
            s3_has_role = auth.s3_has_role
            is_org_admin = lambda i: s3_has_role("ORG_ADMIN", include_admin=False)
            menu_personal = MP()(
                        MP("Administration", c="admin", f="index",
                           restrict = ADMIN,
                           ),
                        MP("Administration", c="admin", f="user",
                           check = is_org_admin,
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
            #MA("Privacy", f="index", args=["privacy"]),
            #MA("Legal Notice", f="index", args=["legal"]),
            MA("Version", f="about", restrict = ("ORG_GROUP_ADMIN")),
        )
        return menu_about

    # -------------------------------------------------------------------------
    @classmethod
    def menu_oauth(cls, **attr):
        """
            Menu for authentication with external services
            - used in default/user controller
        """

        T = current.T
        settings = current.deployment_settings

        return MOA(c="default")(
                MOA("Login with Google", f="google",
                    args=["login"],
                    api = "google",
                    check = lambda item: settings.get_auth_google(),
                    title = T("Login using Google account"),
                    ),
                MOA("Login with Humanitarian.ID", f="humanitarian_id",
                    args=["login"],
                    api = "humanitarianid",
                    check = lambda item: settings.get_auth_humanitarian_id(),
                    title = T("Login using Humanitarian.ID account"),
                    ),
                )

# =============================================================================
class OptionsMenu:
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
        except AttributeError:
            if hasattr(self, name):
                # Error inside the menu function, don't obscure it
                raise
            self.menu = None

    # -------------------------------------------------------------------------
    @staticmethod
    def admin():
        """ ADMIN menu """

        if not current.auth.s3_has_role("ADMIN"):
            # OrgAdmin: No Side-menu
            return None

        settings = current.deployment_settings
        consent_tracking = lambda i: settings.get_auth_consent_tracking()
        is_data_repository = lambda i: settings.get_sync_data_repository()

        # NB: Do not specify a controller for the main menu to allow
        #     re-use of this menu by other controllers
        return M()(
                    M("Users and Roles", c="admin", link=False)(
                        M("Manage Users", f="user"),
                        M("Manage Roles", f="role"),
                        # M("List All Organization Approvers & Whitelists", f="organisation"),
                        # M("Roles", f="group"),
                        # M("Membership", f="membership"),
                    ),
                    M("Announcements", c="cms", f="announcement"),
                    M("Content Management", c="cms", f="post"),
                    M("Consent Tracking", c="admin", link=False, check=consent_tracking)(
                        M("Processing Types", f="processing_type"),
                        M("Consent Options", f="consent_option"),
                        M("Consent##plural", f="consent"),
                        ),
                    M("Database", c="appadmin", f="index")(
                        M("Raw Database access", c="appadmin", f="index")
                    ),
                    M("Event Log", c="admin", f="event"),
                    M("Error Tickets", c="admin", f="errors"),
                    M("Scheduler", c="admin", f="task"),
                    # M("Settings", c="admin", f="setting"),
                    M("Synchronization", c="sync", f="index")(
                        M("Settings", f="config", args=[1], m="update"),
                        M("Repositories", f="repository"),
                        M("Public Data Sets", f="dataset", check=is_data_repository),
                        M("Log", f="log"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def asset():
        """ ASSET Controller """

        ADMIN = current.session.s3.system_roles.ADMIN
        telephones = lambda i: current.deployment_settings.get_asset_telephones()

        return M(c="asset")(
                    M("Assets", f="asset", m="summary")(
                        M("Create", m="create"),
                        #M("Map", m="map"),
                        M("Import", m="import", p="create"),
                    ),
                    M("Telephones", f="telephone", m="summary",
                      check=telephones)(
                        M("Create", m="create"),
                        #M("Map", m="map"),
                        M("Import", m="import", p="create"),
                    ),
                    #M("Brands", f="brand",
                    #  restrict=[ADMIN])(
                    #    M("Create", m="create"),
                    #),
                    M("Items", f="item", m="summary")(
                        M("Create", m="create"),
                        M("Import", f="catalog_item", m="import", p="create"),
                    ),
                    M("Item Categories", f="item_category",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Catalogs", f="catalog",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Suppliers", f="supplier")(
                        M("Create", m="create"),
                        M("Import", m="import", p="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def budget():
        """ BUDGET Controller """

        return M(c="budget")(
                    M("Budgets", f="budget")(
                        M("Create", m="create"),
                    ),
                    M("Staff Types", f="staff")(
                        M("Create", m="create"),
                    ),
                    M("Projects", f="project")(
                        M("Create", m="create"),
                    ),
                    M("Locations", f="location")(
                        M("Create", m="create"),
                    ),
                    M("Bundles", f="bundle")(
                        M("Create", m="create"),
                    ),
                    M("Kits", f="kit")(
                        M("Create", m="create"),
                    ),
                    M("Items", f="item")(
                        M("Create", m="create"),
                    ),
                    M("Parameters", f="parameter"),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def cap():
        """ CAP menu """

        return M(c="cap")(
                    M("Alerts", f="alert")(
                        M("Create", m="create"),
                        M("Import from CSV", m="import", p="create"),
                        M("Import from Feed URL", m="import_feed", p="create"),
                    ),
                    M("Templates", f="template")(
                        M("Create", m="create"),
                    ),
                    #M("CAP Profile", f="profile")(
                    #    M("Edit profile", f="profile")
                    #)
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
                        M("Report", m="report"),
                        M("Import", m="import", p="create"),
                    ),
                    M("Shelter Settings", restrict=[ADMIN])(
                        M("Types", f="shelter_type"),
                        M("Services", f="shelter_service"),
                    )
                )

    # -------------------------------------------------------------------------
    @classmethod
    def cms(cls):
        """ CMS / Content Management System """

        auth = current.auth

        f = current.request.function
        if f == "announcement" and auth.s3_has_role("ADMIN"):
            return cls.admin()

        # Newsletter menu
        author = auth.s3_has_permission("create",
                                        "cms_newsletter",
                                        c = "cms",
                                        f = "newsletter",
                                        )

        T = current.T
        inbox_label = T("Inbox") if author else T("Newsletters")

        unread = current.s3db.cms_unread_newsletters()
        if unread:
            from gluon import TAG, SPAN
            inbox_label = TAG[""](inbox_label, SPAN(unread, _class="num-pending"))
        if author:
            cms_menu = M("Newsletters", c="cms", link=False)(
                            M(inbox_label, f="read_newsletter", translate=False),
                            M("Compose and Send", f="newsletter", p="create"),
                        )
        else:
            cms_menu = M(inbox_label, c="cms", f="read_newsletter", translate=False)

        return M(c="cms")(
                    M("Series", f="series")(
                        M("Create", m="create"),
                        M("View as Pages", f="blog"),
                        ),
                    M("Posts", f="post")(
                        M("Create", m="create"),
                        M("View as Pages", f="page"),
                        ),
                    cms_menu,
                    #M("Newsletters", c="cms", f="read_newsletter")(
                        #M("Inbox", f="read_newsletter",
                          #check = lambda this: this.following()[0].check_permission(),
                          #),
                        #M("Compose and Send", f="newsletter", p="create"),
                        #),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def deploy():
        """ Deployments """

        deploy_team = current.deployment_settings.get_deploy_team_label()
        team_menu = "%(team)s Members" % {"team": deploy_team}

        return M()(M("Missions",
                     c="deploy", f="mission", m="summary")(
                        M("Create", m="create"),
                        M("Active Missions", m="summary",
                          vars={"~.status__belongs": "2"}),
                   ),
                   M("Alerts",
                     c="deploy", f="alert")(
                        M("Create", m="create"),
                        M("InBox",
                          c="deploy", f="email_inbox",
                        ),
                        M("Settings",
                          c="deploy", f="email_channel",
                          p="update", t="msg_email_channel",
                          ),
                   ),
                   M("Assignments",
                     c="deploy", f="assignment", m="summary"
                   ),
                   M("Job Titles",
                     c="deploy", f="job_title"
                   ),
                   M(team_menu,
                     c="deploy", f="human_resource", m="summary")(
                        M("Add Member",
                          c="deploy", f="application", m="select",
                          p="create", t="deploy_application",
                          ),
                        M("Import Members",
                          c="deploy", f="person", m="import"),
                   ),
                  )

    # -------------------------------------------------------------------------
    @staticmethod
    def disease():
        """ Disease Case Tracking and Contact Tracing """

        return M(c="disease")(
                    M("Cases",
                      c="disease", f="case", m="summary")(
                        M("Create", m="create"),
                        M("Watch List", m="summary",
                          vars={"~.monitoring_level__belongs": "OBSERVATION,DIAGNOSTICS"}),
                    ),
                    M("Contact Tracing",
                      c="disease", f="tracing")(
                       M("Create", m="create"),
                    ),
                    M("Statistics Data",
                      c="disease", f="stats_data", args="summary")(
                        M("Create", m="create"),
                        M("Time Plot", m="timeplot"),
                        M("Import", m="import"),
                    ),
                    M("Statistics",
                      c="disease", f="statistic")(
                        M("Create", m="create"),
                    ),
                    M("Diseases",
                      c="disease", f="disease")(
                        M("Create", m="create"),
                    ),
               )

    # -------------------------------------------------------------------------
    @staticmethod
    def doc():
        """ DOC Menu """

        return M(c="doc")(
                    M("Documents", f="document")(
                        M("Create", m="create"),
                    ),
                    M("Photos", f="image")(
                        M("Create", m="create"),
                        #M("Bulk Uploader", f="bulk_upload"),
                    )
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def dvi():
        """ DVI / Disaster Victim Identification """

        return M(c="dvi")(
                    M("Recovery Requests", f="recreq")(
                        M("New Request", m="create"),
                        M("List Current",
                          vars={"recreq.status":"1,2,3"}),
                    ),
                    M("Dead Bodies", f="body")(
                        M("Register Body", m="create"),
                        M("List unidentified",
                          vars={"identification.status": "None"}),
                        M("Report by Age/Gender", m="report",
                          vars={"rows": "age_group",
                                "cols": "gender",
                                "fact": "count(pe_label)",
                                },
                          ),
                    ),
                    M("Missing Persons", f="person")(
                        M("List all"),
                    ),
                    M("Morgues", f="morgue")(
                        M("Create", m="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def dvr():
        """ DVR Menu """

        if current.deployment_settings.get_dvr_label(): # == "Beneficiary"
            return M(c="dvr")(
                        M("Beneficiaries", f="person")(
                            M("Create", m="create"),
                        ),
                    )

        return M(c="dvr")(
                    M("Cases", f="person")(
                        M("Create", m="create"),
                        M("Archived Cases", vars={"archived": "1"}),
                    ),
                    #M("Activities", f="case_activity")(
                    #    M("Emergencies", vars = {"~.emergency": "True"}),
                    #    M("All Activities"),
                    #    M("Report", m="report"),
                    #),
                    M("Need Types", f="need")(
                      M("Create", m="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def event():
        """ EVENT / Event Module """

        settings = current.deployment_settings
        if settings.get_event_label(): # == "Disaster"
            EVENTS = "Disasters"
            EVENT_TYPES = "Disaster Types"
        else:
            EVENTS = "Events"
            EVENT_TYPES = "Event Types"

        incidents = lambda i: settings.get_event_incident()

        return M()(
                    #M("Scenarios", c="event", f="scenario")(
                    #    M("Create", m="create"),
                    #    #M("Import", m="import", p="create"),
                    #),
                    M(EVENTS, c="event", f="event")(
                        M("Create", m="create"),
                    ),
                    M(EVENT_TYPES, c="event", f="event_type")(
                        M("Create", m="create"),
                        #M("Import", m="import", p="create"),
                    ),
                    M("Incidents", c="event", f="incident",
                      check=incidents)(
                        M("Create", m="create"),
                    ),
                    M("Incident Reports", c="event", f="incident_report", m="summary",
                      check=incidents)(
                        M("Create", m="create"),
                    ),
                    M("Incident Types", c="event", f="incident_type",
                      check=incidents)(
                        M("Create", m="create"),
                        #M("Import", m="import", p="create"),
                    ),
                    M("Situation Reports", c="event", f="sitrep")(
                        M("Create", m="create"),
                        #M("Import", m="import", p="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def fin():
        """ FINANCES """

        return M(c="fin")(
                    M("Expenses", f="expense")(
                        M("Create", m="create"),
                        ),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def fire():
        """ FIRE """

        return M(c="fire")(
                    M("Fire Stations", f="station")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        M("Import Stations", m="import"),
                        M("Import Vehicles", f="station_vehicle", m="import"),
                    ),
                    M("Fire Zones", f="zone")(
                        M("Create", m="create"),
                        #M("Map", m="map"),
                        #M("Import", m="import"),
                    ),
                    M("Zone Types", f="zone_type")(
                        M("Create", m="create"),
                        #M("Map", m="map"),
                        #M("Import", m="import"),
                    ),
                    M("Water Sources", f="water_source")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        M("Import", m="import"),
                    ),
                    M("Hazard Points", f="hazard_point")(
                        M("Create", m="create"),
                        M("Import", m="import"),
                    )
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def gis():
        """ GIS / GIS Controllers """

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
                # Anonymous users can never configure the Map
                return False
            s3db = current.s3db
            table = s3db.gis_config
            if auth.s3_has_permission("create", table):
                # If users can create configs then they can see the menu item
                return True
            # Look for this user's config
            query = (table.pe_id == auth.user.pe_id)
            config = current.db(query).select(table.id,
                                              limitby=(0, 1),
                                              cache=s3db.cache).first()
            return bool(config)

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
                    # vars={"rows": name",
                    #       "fact": "sum(population)",
                    #       },
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

    # -------------------------------------------------------------------------
    @staticmethod
    def hms():
        """ HMS / Hospital Status Assessment and Request Management """

        #s3 = current.response.s3

        return M(c="hms")(
                    M("Hospitals", f="hospital")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        M("Report", m="report"),
                        M("Import", m="import", p="create"),
                        #SEP(),
                        #M("Show Map", c="gis", f="map_viewing_client",
                          #vars={"kml_feed" : "%s/hms/hospital.kml" %
                                #s3.base_url, "kml_name" : "Hospitals_"})
                    )
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm():
        """ HRM / Human Resources Management """

        # Custom conditions for the check-hook, as lambdas in order
        # to have them checked only immediately before rendering:
        skills = lambda i: settings.get_hrm_use_skills()

        settings = current.deployment_settings
        teams = settings.get_hrm_teams()
        use_teams = lambda i: teams
        vol_enabled = lambda i: settings.has_module("vol")

        return M(c="hrm")(
                    M(settings.get_hrm_staff_label(), f="staff", m="summary")(
                        M("Create", m="create"),
                        M("Search by Skills", f="competency", check=skills),
                        M("Import", f="person", m="import",
                          vars = {"group": "staff"},
                          p = "create",
                          ),
                    ),
                    M("Staff & Volunteers (Combined)",
                      c="hrm", f="human_resource", m="summary", check=vol_enabled),
                    M(teams, f="group", check=use_teams)(
                        M("Create", m="create"),
                        M("Search Members", f="group_membership"),
                        M("Import", f="group_membership", m="import"),
                    ),
                    M("Department Catalog", f="department")(
                        M("Create", m="create"),
                    ),
                    M("Job Title Catalog", f="job_title")(
                        M("Create", m="create"),
                    ),
                    M("Skill Catalog", f="skill", check=skills)(
                        M("Create", m="create"),
                        #M("Skill Provisions", f="skill_provision"),
                    ),
                    M("Training Events", f="training_event")(
                        M("Create", m="create"),
                        M("Search Training Participants", f="training"),
                        M("Import Participant List", f="training", m="import"),
                    ),
                    M("Training Course Catalog", f="course")(
                        M("Create", m="create"),
                        #M("Course Certificates", f="course_certificate"),
                    ),
                    M("Certificate Catalog", f="certificate")(
                        M("Create", m="create"),
                        #M("Skill Equivalence", f="certificate_skill"),
                    ),
                    M("Reports", f="staff", m="report")(
                        M("Staff Report", m="report"),
                        M("Expiring Staff Contracts Report",
                          vars = {"expiring": 1},
                          ),
                        M("Training Report", f="training", m="report"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def vol():
        """ Volunteer Management """

        # Custom conditions for the check-hook, as lambdas in order
        # to have them checked only immediately before rendering:
        settings = current.deployment_settings
        show_programmes = lambda i: settings.get_hrm_vol_experience() == "programme"
        skills = lambda i: settings.get_hrm_use_skills()
        certificates = lambda i: settings.get_hrm_use_certificates()
        departments = lambda i: settings.get_hrm_vol_departments()
        teams = settings.get_hrm_teams()
        use_teams = lambda i: teams
        show_staff = lambda i: settings.get_hrm_show_staff()

        return M(c="vol")(
                    M("Volunteers", f="volunteer", m="summary")(
                        M("Create", m="create"),
                        M("Search by Skills", f="competency", check=skills),
                        M("Import", f="person", m="import",
                          vars = {"group": "volunteer"},
                          p = "create",
                          ),
                    ),
                    M("Staff & Volunteers (Combined)",
                      c="vol", f="human_resource", m="summary", check=show_staff),
                    M(teams, f="group", check=use_teams)(
                        M("Create", m="create"),
                        M("Search Members", f="group_membership"),
                        M("Import", f="group_membership", m="import"),
                    ),
                    M("Department Catalog", f="department", check=departments)(
                        M("Create", m="create"),
                    ),
                    M("Volunteer Role Catalog", f="job_title")(
                        M("Create", m="create"),
                    ),
                    M("Skill Catalog", f="skill", check=skills)(
                        M("Create", m="create"),
                        #M("Skill Provisions", f="skill_provision"),
                    ),
                    M("Training Events", f="training_event")(
                        M("Create", m="create"),
                        M("Search Training Participants", f="training"),
                        M("Import Participant List", f="training", m="import"),
                    ),
                    M("Training Course Catalog", f="course")(
                        M("Create", m="create"),
                        #M("Course Certificates", f="course_certificate"),
                    ),
                    M("Certificate Catalog", f="certificate", check=certificates)(
                        M("Create", m="create"),
                        #M("Skill Equivalence", f="certificate_skill"),
                    ),
                    M("Programs", f="programme", check=show_programmes)(
                        M("Create", m="create"),
                        M("Import Hours", f="programme_hours", m="import"),
                    ),
                    M("Reports", f="volunteer", m="report")(
                        M("Volunteer Report", m="report"),
                        M("Hours by Role Report", f="programme_hours", m="report",
                          vars = {"rows": "job_title_id",
                                  "cols": "month",
                                  "fact": "sum(hours)",
                                  },
                          check = show_programmes,
                          ),
                        M("Hours by Program Report", f="programme_hours", m="report",
                          vars = {"rows": "programme_id",
                                  "cols": "month",
                                  "fact": "sum(hours)",
                                  },
                          check = show_programmes,
                          ),
                        M("Training Report", f="training", m="report"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def inv():
        """ INV / Inventory """

        ADMIN = current.session.s3.system_roles.ADMIN

        current.s3db.inv_recv_crud_strings()
        inv_recv_list = current.response.s3.crud_strings.inv_recv.title_list

        settings = current.deployment_settings
        use_adjust = lambda i: not settings.get_inv_direct_stock_edits()
        use_commit = lambda i: settings.get_req_use_commit()

        return M()(
                    #M("Home", f="index"),
                    M("Warehouses", c="inv", f="warehouse")(
                        M("Create", m="create"),
                        M("Import", m="import", p="create"),
                    ),
                    M("Warehouse Stock", c="inv", f="inv_item")(
                        M("Adjust Stock Levels", f="adj", check=use_adjust),
                        M("Kitting", f="kitting"),
                        M("Import", f="inv_item", m="import", p="create"),
                    ),
                    M("Reports", c="inv", f="inv_item")(
                        M("Warehouse Stock", f="inv_item", m="report"),
                        M("Expiration Report", c="inv", f="track_item",
                          vars={"report": "exp"}),
                        M("Monetization Report", c="inv", f="inv_item",
                          vars={"report": "mon"}),
                        M("Utilization Report", c="inv", f="track_item",
                          vars={"report": "util"}),
                        M("Summary of Incoming Supplies", c="inv", f="track_item",
                          vars={"report": "inc"}),
                        M("Summary of Releases", c="inv", f="track_item",
                          vars={"report": "rel"}),
                    ),
                    M(inv_recv_list, c="inv", f="recv", translate=False)( # Already T()
                        M("Create", m="create"),
                    ),
                    M("Sent Shipments", c="inv", f="send")(
                        M("Create", m="create"),
                        M("Search Shipped Items", f="track_item"),
                    ),
                    M("Distributions", c="supply", f="distribution")(
                        M("Create", m="create"),
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
                    M("Facilities", c="inv", f="facility")(
                        M("Create", m="create", t="org_facility"),
                    ),
                    M("Facility Types", c="inv", f="facility_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Warehouse Types", c="inv", f="warehouse_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Requests", c="req", f="req")(
                        M("Create", m="create"),
                        M("Requested Items", f="req_item"),
                    ),
                    M("Commitments", c="req", f="commit", check=use_commit)(
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def irs():
        """ IRS / Incident Report System """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="irs")(
                    M("Incident Reports", f="ireport")(
                        M("Create Incident Report", m="create"),
                        M("Open Incidents", vars={"open":1}),
                        M("Map", m="map"),
                        M("Import", m="import"),
                        M("Report", m="report")
                    ),
                    M("Incident Categories", f="icategory", restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Ushahidi Import", f="ireport", restrict=[ADMIN],
                      args="ushahidi")
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def security():
        """ Security Management System """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="security")(
                    M("Incident Reports", c="event", f="incident_report", m="summary")(
                        M("Create", m="create"),
                        M("Import", m="import"),
                    ),
                    M("Security Levels", f="level")(
                        M("level", m="create"),
                    ),
                    M("Security Zones", f="zone")(
                        M("Create", m="create"),
                    ),
                    M("Facilities", c="org", f="facility", m="summary")(
                        M("Create", m="create"),
                        M("Import", m="import"),
                    ),
                    M("Personnel", f="staff")(
                        M("Create", m="create"),
                        M("List All Security-related Staff"),
                        M("List All Essential Staff", f="essential"),
                    ),
                    M("Incident Categories", c="event", f="incident_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Facility Types", c="org", f="facility_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Zone Types", f="zone_type", restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Security Staff Types", f="staff_type", restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    #M("Ushahidi Import", c="irs", f="ireport", restrict=[ADMIN],
                    #  args="ushahidi")
                )

    # -------------------------------------------------------------------------
    def supply(self):
        """ SUPPLY """

        # Use INV menu
        return self.inv()

    # -------------------------------------------------------------------------
    @staticmethod
    def med():
        """ Medical Journal """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="med")(
                    M("Current Visits", f="patient")(
                        M("Create", m="create"),
                        M("Concluded Visits", f="patient", vars={"closed": "only"}),
                        ),
                    # M("Persons", f="person"),
                    M("Units", f="unit")(
                        M("Create", m="create"),
                        ),
                    M("Administration", link=False, restrict=[ADMIN])(
                        M("Active Substances", f="substance"),
                        M("Vaccination Types", f="vaccination_type"),
                        ),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def member():
        """ Membership Management """

        types = lambda i: current.deployment_settings.get_member_membership_types()

        return M(c="member")(
                    M("Members", f="membership", m="summary")(
                        M("Create", m="create"),
                        #M("Report", m="report"),
                        M("Import", f="person", m="import"),
                    ),
                    M("Membership Types", f="membership_type", check=types)(
                        M("Create", m="create"),
                        #M("Import", m="import"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def mpr():
        """ MPR / Missing Person Registry """

        return M(c="mpr")(
                    M("Missing Persons", f="person")(
                        M("Create", m="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def msg():
        """ MSG / Messaging """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="msg")(
                    M("Compose", f="compose"),
                    M("InBox", f="inbox")(
                        M("Email", f="email_inbox"),
                        M("RSS", f="rss"),
                        M("SMS", f="sms_inbox"),
                    ),
                    M("Outbox", f="outbox")(
                        M("Email", f="email_outbox"),
                        M("SMS", f="sms_outbox"),
                    ),
                    M("Message Log", f="message"),
                    M("Distribution groups", f="group")(
                        M("Group Memberships", f="group_membership"),
                    ),
                    M("Administration", restrict=[ADMIN], link=False)(
                        M("Email Channels (Inbound)", c="msg", f="email_channel"),
                        M("RSS Channels", c="msg", f="rss_channel"),
                        M("SMS Outbound Gateways", c="msg", f="sms_outbound_gateway"),
                        M("SMS Modem Channels", c="msg", f="sms_modem_channel"),
                        M("SMS SMTP Channels", c="msg", f="sms_smtp_channel"),
                        M("SMS WebAPI Channels", c="msg", f="sms_webapi_channel"),
                        M("Mobile Commons Channels", c="msg", f="mcommons_channel"),
                        M("Twilio Channels", c="msg", f="twilio_channel"),
                        M("Parsers", c="msg", f="parser"),
                        ),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def org():
        """ ORG / Organization Registry """

        settings = current.deployment_settings
        ADMIN = current.session.s3.system_roles.ADMIN

        use_sectors = lambda i: settings.get_org_sector()
        stats = lambda i: settings.has_module("stats")

        return M(c="org")(
                    M("Organizations", f="organisation")(
                        M("Create", m="create"),
                        M("Import", m="import")
                    ),
                    M("Offices", f="office")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        M("Import", m="import")
                    ),
                    M("Facilities", f="facility")(
                        M("Create", m="create"),
                        M("Import", m="import"),
                    ),
                    M("Resources", f="resource", m="summary",
                      check=stats)(
                        M("Create", m="create"),
                        M("Import", m="import")
                    ),
                    M("Organization Types", f="organisation_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Office Types", f="office_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Facility Types", f="facility_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Sectors", f="sector", check=use_sectors,
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Resource Types", f="resource_type",
                      check=stats,
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def patient():
        """ PATIENT / Patient Tracking """

        return M(c="patient")(
                    M("Patients", f="patient")(
                        M("Create", m="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def pr():
        """ PR / Person Registry """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="pr", restrict=ADMIN)(
                    M("Persons", f="person")(
                        M("Create", m="create"),
                    ),
                    M("Groups", f="group")(
                        M("Create", m="create"),
                    ),
                    #M("Forums", f="forum")(
                    #    M("Create", m="create"),
                    #),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def proc():
        """ PROC / Procurement """

        return M(c="proc")(
                    M("Purchase Orders", f="order")(
                        M("Create", m="create"),
                    ),
                    M("Procurement Plans", f="plan")(
                        M("Create", m="create"),
                    ),
                    M("Suppliers", f="supplier")(
                        M("Create", m="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def project():
        """ PROJECT / Project Tracking & Management """

        settings = current.deployment_settings
        activities = lambda i: settings.get_project_activities()
        activity_types = lambda i: settings.get_project_activity_types()
        community = settings.get_project_community()
        if community:
            IMPORT = "Import Project Communities"
        else:
            IMPORT = "Import Project Locations"
        community_volunteers = lambda i: settings.get_project_community_volunteers()
        demographics = lambda i: settings.get_project_demographics()
        hazards = lambda i: settings.get_project_hazards()
        sectors = lambda i: settings.get_project_sectors()
        stats = lambda i: settings.has_module("stats")
        themes = lambda i: settings.get_project_themes()

        menu = M(c="project")

        if settings.get_project_mode_3w():
            if community:
                menu(
                     M("Projects", f="project")(
                        M("Create", m="create"),
                     ),
                     M("Communities", f="location")(
                        # Better created from tab (otherwise Activity Type filter won't work)
                        #M("Create", m="create"),
                        M("Map", m="map"),
                        M("Community Contacts", f="location_contact"),
                        M("Community Volunteers", f="volunteer",
                          check=community_volunteers),
                     ),
                    )
            else:
                menu(
                     M("Projects", f="project")(
                        M("Create", m="create"),
                        M("Map", f="location", m="map"),
                     )
                    )
            menu(
                 M("Reports", f="location", m="report")(
                    M("3W", f="location", m="report"),
                    M("Beneficiaries", f="beneficiary", m="report",
                      check=stats,
                      ),
                    M("Funding", f="organisation", m="report"),
                 ),
                 M("Import", f="project", m="import", p="create")(
                    M("Import Projects", m="import", p="create"),
                    M("Import Project Organizations", f="organisation",
                      m="import", p="create"),
                    M(IMPORT, f="location",
                      m="import", p="create"),
                    M("Import Activities", f="activity",
                      m="import", p="create",
                      check=activities,
                      ),
                 ),
                 M("Partner Organizations",  f="partners")(
                    M("Create", m="create"),
                    M("Import", m="import", p="create"),
                 ),
                 M("Activity Types", f="activity_type",
                   check=activity_types)(
                    M("Create", m="create"),
                 ),
                 M("Beneficiary Types", f="beneficiary_type",
                   check=stats)(
                    M("Create", m="create"),
                 ),
                 M("Demographics", f="demographic",
                   check=demographics)(
                    M("Create", m="create"),
                 ),
                 M("Hazards", f="hazard",
                   check=hazards)(
                    M("Create", m="create"),
                 ),
                 M("Sectors", f="sector",
                   check=sectors)(
                    M("Create", m="create"),
                 ),
                 M("Themes", f="theme",
                   check=themes)(
                    M("Create", m="create"),
                 ),
                )

        elif settings.get_project_mode_task():
            menu(
                 M("Projects", f="project")(
                    M("Create", m="create"),
                    M("Open Tasks for Project", vars={"tasks":1}),
                 ),
                 M("Tasks", f="task")(
                    M("Create", m="create"),
                 ),
                )
            if current.auth.s3_has_role("STAFF"):
                ADMIN = current.session.s3.system_roles.ADMIN
                menu(
                     M("Daily Work", f="time")(
                        M("My Logged Hours", vars={"mine":1}),
                        M("My Open Tasks", f="task", vars={"mine":1}),
                     ),
                     M("Admin", restrict=[ADMIN])(
                        M("Activity Types", f="activity_type"),
                        M("Import Tasks", f="task", m="import", p="create"),
                     ),
                     M("Reports", f="report")(
                        M("Activity Report", f="activity", m="report"),
                        M("Last Week's Work", f="time", m="report",
                          vars=Storage(rows="person_id",
                                       cols="day",
                                       fact="sum(hours)",
                                       week=1)),
                        M("Last Month's Work", f="time", m="report",
                          vars=Storage(rows="person_id",
                                       cols="week",
                                       fact="sum(hours)",
                                       month=1)),
                        M("Project Time Report", f="time", m="report"),
                     ),
                    )
        else:
            menu(
                 M("Projects", f="project")(
                    M("Create", m="create"),
                    M("Import", m="import", p="create"),
                 ),
                )

        return menu

    # -------------------------------------------------------------------------
    @staticmethod
    def req():
        """ REQ / Request Management """

        ADMIN = current.session.s3.system_roles.ADMIN
        settings = current.deployment_settings
        types = settings.get_req_req_type()
        if len(types) == 1:
            t = types[0]
            if t == "Stock":
                create_menu = M("Create", m="create", vars={"type": 1})
            elif t == "People":
                create_menu = M("Create", m="create", vars={"type": 3})
            else:
                create_menu = M("Create", m="create")
        else:
            create_menu = M("Create", m="create")

        if settings.get_req_summary():
            method = "summary"
        else:
            method = None

        recurring = lambda i: settings.get_req_recurring()
        use_commit = lambda i: settings.get_req_use_commit()
        req_items = lambda i: "Stock" in types
        req_skills = lambda i: "People" in types

        return M(c="req")(
                    M("Requests", f="req", m=method)(
                        create_menu,
                        M("List Recurring Requests", f="req_template", check=recurring),
                        M("Map", m="map"),
                        M("Report", m="report"),
                        M("Search All Requested Items", f="req_item",
                          check=req_items),
                        M("Search All Requested Skills", f="req_skill",
                          check=req_skills),
                    ),
                    M("Commitments", f="commit", check=use_commit)(
                    ),
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
    def stats():
        """ Statistics """

        return M(c="stats")(
                    M("Demographics", f="demographic")(
                        M("Create", m="create"),
                    ),
                    M("Demographic Data", f="demographic_data", args="summary")(
                        M("Create", m="create"),
                        # Not usually dis-aggregated
                        M("Time Plot", m="timeplot"),
                        M("Import", m="import"),
                    ),
                )

    # -------------------------------------------------------------------------
    def sync(self):
        """ SYNC menu """

        # Use admin menu
        return self.admin()

    # -------------------------------------------------------------------------
    @staticmethod
    def transport():
        """ TRANSPORT """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="transport")(
                    M("Airports", f="airport")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        M("Import", m="import", restrict=[ADMIN]),
                    ),
                    M("Border Crossings", f="border_crossing")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        M("Import", m="import", restrict=[ADMIN]),
                        M("Control Points", f="border_control_point"),
                    ),
                    M("Heliports", f="heliport")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        M("Import", m="import", restrict=[ADMIN]),
                    ),
                    M("Seaports", f="seaport")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        M("Import", m="import", restrict=[ADMIN]),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def vehicle():
        """ VEHICLE / Vehicle Tracking """

        return M(c="vehicle")(
                    M("Vehicles", f="vehicle")(
                        M("Create", m="create"),
                        # M("Import", m="import", p="create"),
                        # M("Map", m="map"),
                    ),
                    M("Vehicle Types", f="vehicle_type")(
                        M("Create", m="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def water():
        """ Water: Floods, etc """

        return M(c="water")(
                    M("Wells", f="well")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                    ),
                    M("Gauges", f="gauge")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        M("Import", m="import"),
                    ),
                    M("Rivers", f="river")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        #M("Import", m="import"),
                    ),
                    M("Zones", f="zone")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        #M("Import", m="import"),
                    ),
                    M("Zone Types", f="zone_type")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        #M("Import", m="import"),
                    ),
                )

    # -------------------------------------------------------------------------
    @classmethod
    def breadcrumbs(cls):
        """ Breadcrumbs from the current options menu """

        # Configure the layout:
        layout = BreadcrumbsLayout

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
                name_nice = all_modules[controller].get("name_nice", controller)
            except KeyError:
                # Module not defined
                pass
            else:
                breadcrumbs(layout(name_nice, c = controller))

        # This checks the path in the options menu, omitting the top-level item
        # (because that's the menu itself which doesn't have a linked label):
        menu = current.menu.options
        if menu and function != "index":
            branch = menu.branch()
            if branch:
                path = branch.path()
                if len(path) > 1:
                    for item in path[1:]:
                        breadcrumbs(
                            layout(item.label,
                                   c = item.get("controller"),
                                   f = item.get("function"),
                                   args = item.args,
                                   # Should we retain the request vars in case
                                   # the item has no vars? Or shall we merge them
                                   # in any case? Didn't see the use-case yet
                                   # anywhere...
                                   vars = item.vars,
                                   ))
        return breadcrumbs

# END =========================================================================
