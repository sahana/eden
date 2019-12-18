# -*- coding: utf-8 -*-

""" Sahana Eden Menu Structure and Layout

    @copyright: 2011-2019 (c) Sahana Software Foundation
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

__all__ = ("S3MainMenu",
           "S3OptionsMenu",
           )

import re

from gluon import current, URL
from gluon.storage import Storage

from s3 import IS_ISO639_2_LANGUAGE_CODE
from s3layouts import M, MM, MOA, S3BreadcrumbsLayout, SEP

# =============================================================================
class S3MainMenu(object):
    """ The default configurations for the main application menu """

    # -------------------------------------------------------------------------
    @classmethod
    def menu(cls):

        main_menu = MM()(

            # Modules-menu, align-left
            cls.menu_modules(),

            # Service menus, align-right
            # Note: always define right-hand items in reverse order!
            cls.menu_help(right=True),
            cls.menu_lang(right=True),
            cls.menu_gis(right=True),
            cls.menu_auth(right=True),
            cls.menu_admin(right=True),
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

        # Home always 1st (commented because redundant/unnecessary)
        #module = all_modules["default"]
        #menu_modules.append(MM(module.name_nice, c="default", f="index"))

        # Modules to hide due to insufficient permissions
        hidden_modules = current.auth.permission.hidden_modules()

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
                        groups = re.split(r"\|", _module.access)[1:-1]
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
                    groups = re.split(r"\|", _module.access)[1:-1]
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

        settings = current.deployment_settings
        if not settings.get_L10n_display_toolbar():
            return None

        request = current.request
        languages = settings.get_L10n_languages()
        represent_local = IS_ISO639_2_LANGUAGE_CODE.represent_local

        menu_lang = MM("Language", **attr)
        for language in languages:
            # Show Language in it's own Language
            menu_lang.append(MM(represent_local(language),
                                r = request,
                                translate = False,
                                selectable = False,
                                vars = {"_language": language},
                                ltr = True
                                ))
        return menu_lang

    # -------------------------------------------------------------------------
    @classmethod
    def menu_help(cls, **attr):
        """ Help Menu """

        menu_help = MM("Help", c="default", f="help", **attr)(
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

            menu_auth = MM("Login", c="default", f="user", m="login",
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

    # -------------------------------------------------------------------------
    @classmethod
    def menu_admin(cls, **attr):
        """ Administrator Menu """

        has_role = current.auth.s3_has_role
        settings = current.deployment_settings
        name_nice = settings.modules["admin"].name_nice

        if has_role("ADMIN"):
            translate = settings.has_module("translate")
            menu_admin = MM(name_nice, c="admin", **attr)(
                                MM("Setup", c="setup"),
                                MM("Settings", f="setting"),
                                MM("Users", f="user"),
                                MM("Person Registry", c="pr"),
                                MM("CMS", c="cms", f="post"),
                                MM("Database", c="appadmin", f="index"),
                                MM("Error Tickets", f="errors"),
                                MM("Synchronization", c="sync", f="index"),
                                MM("Translation", c="admin", f="translate",
                                   check=translate),
                                MM("Test Results", f="result"),
                            )
        elif has_role("ORG_ADMIN"):
            menu_admin = MM(name_nice, c="admin", f="user", **attr)()
        else:
            menu_admin = None

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
                        # See if this config is associated with an Incident
                        table = s3db.event_config
                        query = (table.config_id == config)
                        incident = db(query).select(table.incident_id,
                                                    limitby=(0, 1)).first()
                        if incident:
                            s3.incident = incident.incident_id
                        else:
                            s3.incident = None
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
    def menu_oauth(cls, **attr):
        """
            Menu for authentication with external services
            - used in default/user controller
        """

        T = current.T
        settings = current.deployment_settings

        return MOA(c="default")(
                MOA("Login with Facebook", f="facebook",
                    args=["login"],
                    api = "facebook",
                    check = lambda item: current.s3db.msg_facebook_login(),
                    title = T("Login using Facebook account"),
                    ),
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
        except AttributeError:
            if hasattr(self, name):
                # Error inside the menu function, don't obscure it
                raise
            self.menu = None

    # -------------------------------------------------------------------------
    def admin(self):
        """ ADMIN menu """

        if not current.auth.s3_has_role("ADMIN"):
            # OrgAdmin: No Side-menu
            return None

        settings_messaging = self.settings_messaging()

        settings = current.deployment_settings
        consent_tracking = lambda i: settings.get_auth_consent_tracking()
        is_data_repository = lambda i: settings.get_sync_data_repository()
        translate = settings.has_module("translate")

        # NB: Do not specify a controller for the main menu to allow
        #     re-use of this menu by other controllers
        return M()(
                    M("Setup", c="setup", f="deployment")(
                        #M("Create", m="create"),
                        #M("Servers", f="server")(
                        #),
                        #M("Instances", f="instance")(
                        #),
                    ),
                    M("Settings", c="admin", f="setting")(
                        settings_messaging,
                    ),
                    M("User Management", c="admin", f="user")(
                        M("Create User", m="create"),
                        M("List All Users"),
                        M("Import Users", m="import"),
                        M("List All Roles", f="role"),
                        M("List All Organization Approvers & Whitelists", f="organisation"),
                        #M("Roles", f="group"),
                        #M("Membership", f="membership"),
                    ),
                    M("Consent Tracking", c="admin", link=False, check=consent_tracking)(
                        M("Processing Types", f="processing_type"),
                        M("Consent Options", f="consent_option"),
                        ),
                    M("CMS", c="cms", f="post")(
                    ),
                    M("Database", c="appadmin", f="index")(
                        M("Raw Database access", c="appadmin", f="index")
                    ),
                    M("Error Tickets", c="admin", f="errors"),
                    M("Monitoring", c="setup", f="server")(
                        M("Checks", f="monitor_check"),
                        M("Servers", f="server"),
                        M("Tasks", f="monitor_task"),
                        M("Logs", f="monitor_run"),
                    ),
                    M("Synchronization", c="sync", f="index")(
                        M("Settings", f="config", args=[1], m="update"),
                        M("Repositories", f="repository"),
                        M("Public Data Sets", f="dataset", check=is_data_repository),
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
                    M("View Test Result Reports", c="admin", f="result"),
                    M("Portable App", c="admin", f="portable")
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def assess():
        """ ASSESS Menu """

        #ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="assess")(
                    M("Building Assessments", f="building")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                    ),
                    M("Canvassing", f="canvass")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                    ),
                    #M("Rapid Assessments", f="rat")(
                    #    M("Create", m="create"),
                    #),
                    #M("Impact Assessments", f="assess")(
                    #    #M("Create", m="create"),
                    #    M("Create", f="basic_assess", p="create"),
                    #    #M("Search"),
                    #    M("Mobile", f="mobile_basic_assess"),
                    #),
                    ##M("Baseline Data")(
                    #    #M("Population", f="population"),
                    ##),
                    #M("Edit Options", restrict=ADMIN)(
                    #    M("List / Add Baseline Types", f="baseline_type"),
                    #    M("List / Add Impact Types", f="impact_type"),
                    #)
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
    def br():
        """ Beneficiary Registry """

        ADMIN = current.auth.get_system_roles().ADMIN

        s3db = current.s3db
        labels = s3db.br_terminology()
        crud_strings = s3db.br_crud_strings("pr_person")

        settings = current.deployment_settings
        use_activities = settings.get_br_case_activities()
        urgent_activities = use_activities and settings.get_br_case_activity_urgent_option()

        manage_assistance = settings.get_br_manage_assistance()

        return M(c="br")(
                M(labels.CURRENT, f="person", vars={"closed": "0"})(
                    M(crud_strings.label_create, m="create"),
                    M("Activities", f="case_activity", check=use_activities,
                      ),
                    M("Emergencies", f="case_activity",
                      vars={"~.priority": "0"}, check=urgent_activities,
                      ),
                    ),
                 M("Measures", f="assistance_measure", check=manage_assistance)(
                    #M("Overview"),
                    ),
                 #M("Appointments"),
                 M("Statistics", link=False)(
                    M("Cases", f="person", m="report"),
                    M("Activities", f="case_activity", m="report", check=use_activities),
                    M("Measures", f="assistance_measure", m="report", check=manage_assistance),
                    ),
                 M("Compilations", link=False)(
                    M("All Cases", f="person"),
                    ),
                 M("Archive", link=False)(
                    M(labels.CLOSED, f="person", vars={"closed": "1"}),
                    M("Invalid Cases", f="person", vars={"invalid": "1"}, restrict=[ADMIN]),
                    ),
                 M("Administration", link=False, restrict=[ADMIN])(
                    M("Case Statuses", f="case_status"),
                    M("Case Activity Statuses", f="case_activity_status",
                      check = lambda i: use_activities and settings.get_br_case_activity_status(),
                      ),
                    M("Need Types", f="need",
                      check = lambda i: not settings.get_br_needs_org_specific(),
                      ),
                    M("Assistance Statuses", f="assistance_status",
                      check = manage_assistance,
                      ),
                    M("Assistance Types", f="assistance_type",
                      check = lambda i: manage_assistance and \
                                        settings.get_br_assistance_types(),
                      ),
                    M(labels.THEMES, f="assistance_theme",
                      check = lambda i: manage_assistance and \
                                        settings.get_br_assistance_themes() and \
                                        not settings.get_br_assistance_themes_org_specific(),
                      ),
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
    def building():
        """ BUILDING Controller """

        return M(c="building")(
                    M("NZSEE Level 1", f="nzseel1")(
                        M("Submit New (triage)", m="create",
                          vars={"triage":1}),
                        M("Submit New (full form)", m="create"),
                    ),
                    M("NZSEE Level 2", f="nzseel2")(
                        M("Submit New", m="create"),
                    ),
                    M("Report", f="index")(
                        M("Snapshot", f="report"),
                        M("Assessment timeline", f="timeline"),
                        M("Assessment admin level", f="adminLevel"),
                    ),
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

        if current.deployment_settings.get_ui_label_camp():
            shelter = "Camps"
            types = "Camp Settings"
        else:
            shelter = "Shelters"
            types = "Shelter Settings"

        return M(c="cr")(
                    M(shelter, f="shelter")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        M("Report", m="report"),
                        M("Import", m="import", p="create"),
                    ),
                    M(types, restrict=[ADMIN])(
                        M("Types", f="shelter_type"),
                        M("Services", f="shelter_service"),
                    )
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def cms():
        """ CMS / Content Management System """

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
    def dc():
        """ Data Collection Tool """

        #ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="dc")(
                    M("Templates", f="template")(
                        M("Create", m="create"),
                        M("Import", f="question", m="import"),
                    ),
                    M("Targets", f="target")(
                        M("Create", m="create"),
                    ),
                    # @ToDo: Use settings for label
                    M("Responses", f="respnse")(
                        M("Create", m="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def delphi():
        """ DELPHI / Delphi Decision Maker """

        #ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="delphi")(
                    M("Active Problems", f="problem")(
                        M("Create", m="create"),
                    ),
                    M("Groups", f="group")(
                        M("Create", m="create"),
                    ),
                    #M("Solutions", f="solution"),
                    #M("Administration", restrict=[ADMIN])(
                        #M("Groups", f="group"),
                        #M("Group Memberships", f="membership"),
                        #M("Problems", f="problem"),
                    #)
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def deploy():
        """ Deployments """

        deploy_team = current.deployment_settings.get_deploy_team_label()
        team_menu = "%(team)s Members" % dict(team=deploy_team)

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
                    #M("Home", f="index"),
                    M("Recovery Requests", f="recreq")(
                        M("New Request", m="create"),
                        M("List Current",
                          vars={"recreq.status":"1,2,3"}),
                    ),
                    M("Dead Bodies", f="body")(
                        M("Add", m="create"),
                        M("List unidentified",
                          vars={"identification.status": "None"}),
                        M("Report by Age/Gender", m="report",
                          vars=dict(rows="age_group",
                                    cols="gender",
                                    fact="count(pe_label)",
                                    ),
                          ),
                    ),
                    M("Missing Persons", f="person")(
                        M("List all"),
                    ),
                    M("Morgues", f="morgue")(
                        M("Create", m="create"),
                    ),
                    M("Dashboard", f="index"),
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
                    M("Case Types", f="case_type")(
                       M("Create", m="create"),
                    ),
                    M("Need Types", f="need")(
                      M("Create", m="create"),
                    ),
                    M("Housing Types", f="housing_type")(
                      M("Create", m="create"),
                    ),
                    M("Income Sources", f="income_source")(
                      M("Create", m="create"),
                    ),
                    M("Beneficiary Types", f="beneficiary_type")(
                      M("Create", m="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def edu():
        """ Education Module """

        return M()(
                    M("Schools", c="edu", f="school")(
                        M("Create", m="create"),
                        M("Import", m="import", p="create"),
                    ),
                    M("School Types", c="edu", f="school_type")(
                        M("Create", m="create"),
                        M("Import", m="import", p="create"),
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
            return True if config else False

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
                          vars=dict(report="exp")),
                        M("Monetization Report", c="inv", f="inv_item",
                          vars=dict(report="mon")),
                        M("Utilization Report", c="inv", f="track_item",
                          vars=dict(report="util")),
                        M("Summary of Incoming Supplies", c="inv", f="track_item",
                          vars=dict(report="inc")),
                        M("Summary of Releases", c="inv", f="track_item",
                          vars=dict(report="rel")),
                    ),
                    M(inv_recv_list, c="inv", f="recv", translate=False)( # Already T()
                        M("Create", m="create"),
                        M("Timeline", args="timeline"),
                    ),
                    M("Sent Shipments", c="inv", f="send")(
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
                        M("Timeline", args="timeline"),
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
    def survey():
        """ SURVEY / Survey """

        ADMIN = current.session.s3.system_roles.ADMIN

        # Do we have a series_id?
        series_id = False
        get_vars = Storage()
        try:
            series_id = int(current.request.args[0])
        except:
            try:
                (dummy, series_id) = current.request.get_vars["viewing"].split(".")
                series_id = int(series_id)
            except:
                pass
        if series_id:
            get_vars.viewing = "survey_complete.%s" % series_id

        return M(c="survey")(
                    M("Assessment Templates", f="template")(
                        M("Create", m="create"),
                    ),
                    #M("Section", f="section")(
                    #    M("Create", args="create"),
                    #),
                    M("Disaster Assessments", f="series")(
                        M("Create", m="create"),
                    ),
                    M("Administration", f="admin", restrict=[ADMIN])(
                        M("Import Templates", f="question_list",
                          m="import", p="create"),
                        M("Import Template Layout", f="formatter",
                          m="import", p="create"),
                        M("Import Completed Assessment Forms", f="complete",
                          m="import", p="create", vars=get_vars, check=series_id),
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
    def msg(self):
        """ MSG / Messaging """

        ADMIN = current.session.s3.system_roles.ADMIN

        if current.request.function in ("sms_outbound_gateway",
                                        "email_channel",
                                        "facebook_channel",
                                        "sms_modem_channel",
                                        "sms_smtp_channel",
                                        "sms_webapi_channel",
                                        "tropo_channel",
                                        "twitter_channel"):
            return self.admin()

        settings_messaging = self.settings_messaging()

        return M(c="msg")(
                    M("Compose", f="compose"),
                    M("InBox", f="inbox")(
                        M("Email", f="email_inbox"),
                        #M("Facebook", f="facebook_inbox"),
                        M("RSS", f="rss"),
                        M("SMS", f="sms_inbox"),
                        M("Twitter", f="twitter_inbox"),
                    ),
                    M("Outbox", f="outbox")(
                        M("Email", f="email_outbox"),
                        M("Facebook", f="facebook_outbox"),
                        M("SMS", f="sms_outbox"),
                        M("Twitter", f="twitter_outbox"),
                    ),
                    M("Message Log", f="message"),
                    M("Distribution groups", f="group")(
                        M("Group Memberships", f="group_membership"),
                    ),
                    M("Twitter Search", f="twitter_result")(
                       M("Search Queries", f="twitter_search"),
                       M("Results", f="twitter_result"),
                       # @ToDo KeyGraph Results
                    ),
                    M("Administration", restrict=[ADMIN])(settings_messaging)
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def org():
        """ ORG / Organization Registry """

        settings = current.deployment_settings
        ADMIN = current.session.s3.system_roles.ADMIN
        SECTORS = "Clusters" if settings.get_ui_label_cluster() \
                             else "Sectors"
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
                    M(SECTORS, f="sector", check=use_sectors,
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
    def po():
        """ PO / Population Outreach """

        due_followups = current.s3db.po_due_followups()
        DUE_FOLLOWUPS = current.T("Due Follow-ups")
        if due_followups:
            follow_up_label = "%s (%s)" % (DUE_FOLLOWUPS, due_followups)
        else:
            follow_up_label = DUE_FOLLOWUPS

        return M(c="po")(
                    M("Overview", f="index"),
                    M("Households", f="household", m="summary")(
                        M("Create", m="create"),
                        M("Import", m="import"),
                    ),
                    M(follow_up_label, f="due_followups",
                      translate=False,
                      ),
                    M("Areas", f="area")(
                        M("Create", m="create"),
                    ),
                    M("Referral Agencies", f="organisation")(
                        M("Create", m="create"),
                    ),
                    M("Emotional Needs", f="emotional_need")(
                        M("Create", m="create"),
                    ),
                    M("Practical Needs", f="practical_need")(
                        M("Create", m="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def police():
        """ Police """

        return M(c="police")(
                    M("Police Stations", f="station")(
                        M("Create", m="create"),
                    ),
                    #M("Station Types", f="station_type")(
                    #    M("Create", m="create"),
                    #),
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
        #indicators = lambda i: settings.get_project_indicators()
        programmes = lambda i: settings.get_project_programmes()
        sectors = lambda i: settings.get_project_sectors()
        stats = lambda i: settings.has_module("stats")
        themes = lambda i: settings.get_project_themes()

        menu = M(c="project")

        if settings.get_project_mode_3w():
            if community:
                menu(
                     M("Programs", f="programme",
                       check=programmes)(
                        M("Create", m="create"),
                     ),
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
                     M("Programs", f="programme",
                       check=programmes)(
                        M("Create", m="create"),
                     ),
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
                    #M("Indicators", f="indicator", m="report",
                    #  check=indicators,
                    #  ),
                    #M("Indicators over Time", f="indicator", m="timeplot",
                    #  check=indicators,
                    #  ),
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
                 #M("Indicators", f="indicator",
                 #  check=indicators)(
                 #   M("Create", m="create"),
                 #),
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

        recurring = lambda i: settings.get_req_recurring()
        use_commit = lambda i: settings.get_req_use_commit()
        req_items = lambda i: "Stock" in types
        req_skills = lambda i: "People" in types

        return M(c="req")(
                    M("Requests", f="req")(
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
    def setup(self):
        """ Setup """

        return self.admin()

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
    @staticmethod
    def stdm():
        """ Social Tenure Domain Model """
        ADMIN = current.session.s3.system_roles.ADMIN
        has_role = current.auth.s3_has_role

        informal = lambda i: has_role("INFORMAL_SETTLEMENT")
        gov = lambda i: has_role("LOCAL_GOVERNMENT")
        rural = lambda i: has_role("RURAL_AGRICULTURE")

        return M(c="stdm")(
                    M("Administrative Units", c="gis", f="location",
                                              vars={"~.level__ne": None},
                      restrict=ADMIN)(
                        M("Create", m="create",
                                    vars={"~.level__ne": None}),
                    ),
                    #M("Spatial Units", c="gis", f="location",
                    #                   vars={"~.level": None})(
                    #    M("Create", m="create", vars={"~.level": None}),
                    #),
                    M("Gardens", f="garden",
                      check=rural)(
                        M("Create", m="create"),
                        M("Import", m="import"),
                    ),
                    M("Parcels", f="parcel",
                      check=gov)(
                        M("Create", m="create"),
                        M("Import", m="import"),
                    ),
                    M("Structures", f="structure",
                      check=informal)(
                        M("Create", m="create"),
                        M("Import", m="import"),
                    ),
                    M("Parties")(
                        M("People", f="person"),
                        M("Groups", f="group"),
                        M("Farmers", f="farmer", check=rural),
                        M("Planners", f="planner", check=gov),
                        M("Surveyors", f="surveyor", check=gov),
                    ),
                    M("Surveys", f="gov_survey", check=gov)(
                        M("Create", m="create"),
                    ),
                    M("Surveys", f="rural_survey", check=rural)(
                        M("Create", m="create"),
                    ),
                    M("Tenures", f="tenure")(
                        M("Create", m="create"),
                    ),
                    M("Lookup Lists", restrict=ADMIN)(
                        M("Disputes", f="dispute"),
                        M("Household Relations", f="group_member_role"),
                        M("Input Services", f="input_service"),
                        M("Land Uses", f="landuse"),
                        M("Officer Ranks", f="job_title"),
                        M("Ownership Types", f="ownership_type"),
                        M("Parcel Types", f="parcel_type"),
                        M("Socio-economic Impacts", f="socioeconomic_impact"),
                        M("Tenure Types", f="tenure_type"),
                    ),
                )

    # -------------------------------------------------------------------------
    def sync(self):
        """ SYNC menu """

        # Use admin menu
        return self.admin()

    # -------------------------------------------------------------------------
    @staticmethod
    def tour():
        """ Guided Tour """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="tour")(
                    M("Configuration", f="config", restrict=[ADMIN])(
                        M("Import", m="import", restrict=[ADMIN]),
                        ),
                    M("Detail", f="details", restrict=[ADMIN]),
                    M("User", f="user", restrict=[ADMIN]),
                )


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
                        M("Import", m="import", p="create"),
                        M("Map", m="map"),
                    ),
                    M("Vehicle Types", f="vehicle_type")(
                        M("Create", m="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def vulnerability():
        """ Vulnerability """

        return M(c="vulnerability")(
                    M("Indicators", f="indicator")(
                        M("Create", m="create"),
                    ),
                    M("Data", f="data")(
                        M("Create", m="create"),
                        M("Import", m="import"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def water():
        """ Water: Floods, etc """

        return M(c="water")(
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
    @staticmethod
    def work():
        """ WORK: Simple Volunteer Jobs Management """

        return M(c="work")(
                    # @todo: my jobs
                    M("Joblist", f="job", m="datalist"),
                    M("Jobs", f="job")(
                        M("Create", m="create"),
                    ),
                    M("Assignments", f="assignment")(
                        M("Create", m="create"),
                    ),
                    # Hide until implemented:
                    #M("Contexts", f="context")(
                    #    M("Create", m="create"),
                    #),
                    M("Job Types", f="job_type")(
                        M("Create", m="create"),
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
            M("Email Channels (Inbound)", c="msg", f="email_channel"),
            M("Facebook Channels", c="msg", f="facebook_channel"),
            M("RSS Channels", c="msg", f="rss_channel"),
            M("SMS Outbound Gateways", c="msg", f="sms_outbound_gateway")(
                M("SMS Modem Channels", c="msg", f="sms_modem_channel"),
                M("SMS SMTP Channels", c="msg", f="sms_smtp_channel"),
                M("SMS WebAPI Channels", c="msg", f="sms_webapi_channel"),
            ),
            M("Mobile Commons Channels", c="msg", f="mcommons_channel"),
            M("Twilio Channels", c="msg", f="twilio_channel"),
            M("Twitter Channels", c="msg", f="twitter_channel"),
            M("Parsers", c="msg", f="parser"),
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
            if branch:
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
