# -*- coding: utf-8 -*-

""" Deployment Settings

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: 2009-2014 (c) Sahana Software Foundation
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

__all__ = ("S3Config",)

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current, URL
from gluon.storage import Storage

from s3theme import *

class S3Config(Storage):
    """
        Deployment Settings Helper Class
    """

    # Used by modules/s3theme.py
    FORMSTYLE = {"default": formstyle_foundation,
                 "default_inline": formstyle_foundation_inline,
                 "bootstrap": formstyle_bootstrap,
                 "foundation": formstyle_foundation,
                 "foundation_2col": formstyle_foundation_2col,
                 "foundation_inline": formstyle_foundation_inline,
                 "table": formstyle_table,
                 "table_inline": formstyle_table_inline,
                 }

    # Formats from static/scripts/ui/i18n converted to Python style
    date_formats = {"ar": "%d/%m/%Y",
                    "bs": "%d.%m.%Y",
                    "de": "%d.%m.%Y",
                    "el": "%d/%m/%Y",
                    "es": "%d/%m/%Y",
                    "fr": "%d/%m/%Y",
                    "hr": "%d.%m.%Y",
                    "it": "%d/%m/%Y",
                    "ja": "%Y/%m/%d",
                    "km": "%d-%m-%Y",
                    "ko": "%Y-%m-%d",
                    #"mn": "",
                    #"ne": "",
                    "prs": "%Y/%m/%d",
                    "ps": "%Y/%m/%d",
                    "pt": "%d/%m/%Y",
                    "pt-br": "%d/%m/%Y",
                    "ru": "%d.%m.%Y",
                    #"si": "",
                    "sr": "%d.%m.%Y",
                    "sv": "%Y-%m-%d",
                    "ta": "%d/%m/%Y",
                    #"tet": "",
                    "th": "%d/%m/%Y",
                    #"tl": "",
                    #"ur": "",
                    "vi": "%d/%m/%Y",
                    "zh-cn": "%Y-%m-%d",
                    "zh-tw": "%Y/%m/%d",
                    }

    def __init__(self):
        self.auth = Storage()
        self.auth.email_domains = []
        self.base = Storage()
        self.cap = Storage()
        self.cms = Storage()
        self.cr = Storage()
        self.database = Storage()
        self.deploy = Storage()
        self.event = Storage()
        self.evr = Storage()
        self.fin = Storage()
        # @ToDo: Move to self.ui
        self.frontpage = Storage()
        self.frontpage.rss = []
        self.gis = Storage()
        self.hms = Storage()
        self.hrm = Storage()
        self.inv = Storage()
        self.irs = Storage()
        self.L10n = Storage()
        self.log = Storage()
        self.mail = Storage()
        self.member = Storage()
        self.msg = Storage()
        self.org = Storage()
        self.pr = Storage()
        self.proc = Storage()
        self.project = Storage()
        self.req = Storage()
        self.supply = Storage()
        self.search = Storage()
        self.security = Storage()
        self.sync = Storage()
        self.ui = Storage()
        self.vulnerability = Storage()
        self.transport = Storage()

    # -------------------------------------------------------------------------
    # Template
    def get_template(self):
        """
            Which deployment template to use for config.py, layouts.py, menus.py
            http://eden.sahanafoundation.org/wiki/BluePrint/Templates
        """
        return self.base.get("template", "default")

    def exec_template(self, path):
        """
            Execute the template
        """
        from gluon.fileutils import read_file
        from gluon.restricted import restricted
        code = read_file(path)
        restricted(code, layer=path)

    # -------------------------------------------------------------------------
    # Theme
    def get_theme(self):
        """
            Which templates folder to use for views/layout.html
        """
        return self.base.get("theme", "default")

    def get_base_xtheme(self):
        """
            Whether there is a custom Ext theme or simply use the default xtheme-gray
            - specified as <themefolder>/xtheme-<filename>.css
        """
        return self.base.get("xtheme", None)

    # -------------------------------------------------------------------------
    # Customise Hooks
    def customise_controller(self, tablename, **attr):
        """
            Customise a Controller
            - runs before resource customisation
            - but prep runs after resource customisation
        """
        customise = self.get("customise_%s_controller" % tablename)
        if customise:
            return customise(**attr)
        else:
            return attr

    def customise_resource(self, tablename):
        """
            Get customisation callback for a resource
            - runs after controller customisation
            - but runs before prep
        """
        return self.get("customise_%s_resource" % tablename)

    # -------------------------------------------------------------------------
    def has_module(self, module_name):
        """
            List of Active Modules
        """
        if not self.modules:
            # Provide a minimal list of core modules
            _modules = [
                "default",      # Default
                "admin",        # Admin
                "gis",          # GIS
                "pr",           # Person Registry
                "org"           # Organization Registry
            ]
        else:
            _modules = self.modules

        return module_name in _modules

    # -------------------------------------------------------------------------
    def is_cd_version(self):
        """
            Whether we're running from a non-writable CD
        """
        return self.base.get("cd_version", False)

    # -------------------------------------------------------------------------
    def get_google_analytics_tracking_id(self):
        """
            Google Analytics Key
        """
        return self.base.get("google_analytics_tracking_id", None)

    # -------------------------------------------------------------------------
    def get_youtube_id(self):
        """
            List of YouTube IDs for the /default/video page
        """
        return self.base.get("youtube_id", [])

    # -------------------------------------------------------------------------
    # Authentication settings
    def get_auth_hmac_key(self):
        """
            salt to encrypt passwords - normally randomised during 1st run
        """
        return self.auth.get("hmac_key", "akeytochange")

    def get_auth_password_min_length(self):
        """
            To set the Minimum Password Length
        """
        return self.auth.get("password_min_length", int(4))

    def get_auth_gmail_domains(self):
        """ List of domains which can use GMail SMTP for Authentication """
        return self.auth.get("gmail_domains", [])

    def get_auth_google(self):
        """
            Read the Google OAuth settings
            - if configured, then it is assumed that Google Authentication is enabled
        """
        id = self.auth.get("google_id", False)
        secret = self.auth.get("google_secret", False)
        if id and secret:
            return dict(id=id, secret=secret)
        else:
            return False

    def get_auth_openid(self):
        """ Use OpenID for Authentication """
        return self.auth.get("openid", False)

    def get_security_self_registration(self):
        """
            Whether Users can register themselves
            - False to disable self-registration
            - True to use the default registration page at default/user/register
            - "index" to use a cyustom registration page defined in private/templates/<template>/controllers.py

        """
        return self.security.get("self_registration", True)
    def get_auth_registration_requires_verification(self):
        return self.auth.get("registration_requires_verification", False)
    def get_auth_registration_requires_approval(self):
        return self.auth.get("registration_requires_approval", False)
    def get_auth_always_notify_approver(self):
        return self.auth.get("always_notify_approver", True)

    def get_auth_login_next(self):
        """ Which page to go to after login """
        return self.auth.get("login_next", URL(c="default", f="index"))

    def get_auth_show_link(self):
        return self.auth.get("show_link", True)
    def get_auth_registration_link_user_to(self):
        """
            Link User accounts to none or more of:
            * Staff
            * Volunteer
            * Member
        """
        return self.auth.get("registration_link_user_to", None)
    def get_auth_registration_link_user_to_default(self):
        """
            Link User accounts to none or more of:
            * Staff
            * Volunteer
            * Member
        """
        return self.auth.get("registration_link_user_to_default", None)

    def get_auth_opt_in_team_list(self):
        return self.auth.get("opt_in_team_list", [])

    def get_auth_opt_in_to_email(self):
        return self.get_auth_opt_in_team_list() != []

    def get_auth_opt_in_default(self):
        return self.auth.get("opt_in_default", False)

    def get_auth_registration_requests_home_phone(self):
        return self.auth.get("registration_requests_home_phone", False)

    def get_auth_registration_requests_mobile_phone(self):
        return self.auth.get("registration_requests_mobile_phone", False)

    def get_auth_registration_mobile_phone_mandatory(self):
        " Make the selection of Mobile Phone Mandatory during registration "
        return self.auth.get("registration_mobile_phone_mandatory", False)

    def get_auth_registration_requests_organisation(self):
        " Have the registration form request the Organisation "
        return self.auth.get("registration_requests_organisation", False)

    def get_auth_admin_sees_organisation(self):
        " See Organisations in User Admin"
        return self.auth.get("admin_sees_organisation",
                             self.get_auth_registration_requests_organisation())

    def get_auth_registration_organisation_required(self):
        " Make the selection of Organisation required during registration "
        return self.auth.get("registration_organisation_required", False)

    def get_auth_registration_organisation_hidden(self):
        " Hide the Organisation field in the registration form unless an email is entered which isn't whitelisted "
        return self.auth.get("registration_organisation_hidden", False)

    def get_auth_registration_organisation_default(self):
        " Default the Organisation during registration "
        return self.auth.get("registration_organisation_default", None)

    def get_auth_registration_organisation_id_default(self):
        " Default the Organisation during registration - will return the organisation_id"
        name = self.auth.get("registration_organisation_default", None)
        if name:
            otable = current.s3db.org_organisation
            orow = current.db(otable.name == name).select(otable.id).first()
            if orow:
                organisation_id = orow.id
            else:
                organisation_id = otable.insert(name = name)
        else:
            organisation_id = None
        return organisation_id

    def get_auth_registration_requests_organisation_group(self):
        " Have the registration form request the Organisation Group "
        return self.auth.get("registration_requests_organisation_group", False)

    def get_auth_registration_organisation_group_required(self):
        " Make the selection of Organisation Group required during registration "
        return self.auth.get("registration_organisation_group_required", False)

    def get_auth_registration_requests_site(self):
        " Have the registration form request the Site "
        return self.auth.get("registration_requests_site", False)

    def get_auth_registration_site_required(self):
        " Make the selection of site required during registration "
        return self.auth.get("registration_site_required", False)

    def get_auth_registration_requests_image(self):
        """ Have the registration form request an Image """
        return self.auth.get("registration_requests_image", False)

    def get_auth_registration_pending(self):
        """ Message someone gets when they register & they need approving """
        message = self.auth.get("registration_pending", None)
        if message:
            return current.T(message)

        approver = self.get_mail_approver()
        if "@" in approver:
            m = "Registration is still pending approval from Approver (%s) - please wait until confirmation received." % \
                approver
        else:
            m = "Registration is still pending approval from the system administrator - please wait until confirmation received."
        return current.T(m)

    def get_auth_registration_pending_approval(self):
        """ Message someone gets when they register & they need approving """
        message = self.auth.get("registration_pending_approval", None)
        if message:
            return current.T(message)

        approver = self.get_mail_approver()
        if "@" in approver:
            m = "Thank you for validating your email. Your user account is still pending for approval by the system administrator (%s). You will get a notification by email when your account is activated." % \
                approver
        else:
            m = "Thank you for validating your email. Your user account is still pending for approval by the system administrator. You will get a notification by email when your account is activated."
        return current.T(m)

    def get_auth_registration_roles(self):
        """
            A dictionary of realms, with lists of role UUIDs, to assign to newly-registered users
            Use key = 0 to have the roles not restricted to a realm
        """
        return self.auth.get("registration_roles", [])

    def get_auth_terms_of_service(self):
        """
            Force users to accept Terms of Servcie before Registering an account
            - uses <template>/views/tos.html
        """
        return self.auth.get("terms_of_service", False)

    def get_auth_registration_volunteer(self):
        """ Redirect the newly-registered user to their volunteer details page """
        return self.auth.get("registration_volunteer", False)

    def get_auth_record_approval(self):
        """ Use record approval (False by default) """
        return self.auth.get("record_approval", False)

    def get_auth_record_approval_required_for(self):
        """ Which tables record approval is required for """
        return self.auth.get("record_approval_required_for", [])

    def get_auth_realm_entity(self):
        """ Hook to determine the owner entity of a record """
        return self.auth.get("realm_entity", None)

    def get_auth_person_realm_human_resource_site_then_org(self):
        """
            Should we set pr_person.realm_entity to that of
            hrm_human_resource.site_id$pe_id
        """
        return self.auth.get("person_realm_human_resource_site_then_org", False)

    def get_auth_person_realm_member_org(self):
        """
            Sets pr_person.realm_entity to
            organisation.pe_id of member_member
        """
        return self.auth.get("person_realm_member_org", False)

    def get_auth_entity_role_manager(self):
        """
            Activate Entity Role Manager (=embedded Role Manager Tab for OrgAdmins)
        """
        return self.auth.get("entity_role_manager", False)

    def get_auth_role_modules(self):
        """
            Which modules are included in the Role Manager
            - to assign discrete permissions to via UI
        """
        T = current.T
        return self.auth.get("role_modules", OrderedDict([
            ("staff", T("Staff")),
            ("vol", T("Volunteers")),
            ("member", T("Members")),
            ("inv", T("Warehouses")),
            ("asset", T("Assets")),
            ("project", T("Projects")),
            ("survey", T("Assessments")),
            ("irs", T("Incidents"))
        ]))

    def get_auth_access_levels(self):
        """
            Access levels for the Role Manager UI
        """
        T = current.T
        return self.auth.get("access_levels", OrderedDict([
            ("reader", T("Reader")),
            ("data_entry", T("Data Entry")),
            ("editor", T("Editor")),
            ("super", T("Super Editor"))
        ]))

    def get_auth_set_presence_on_login(self):
        return self.auth.get("set_presence_on_login", False)
    def get_auth_ignore_levels_for_presence(self):
        return self.auth.get("ignore_levels_for_presence", ("L0",))
    def get_auth_create_unknown_locations(self):
        return self.auth.get("create_unknown_locations", False)

    def get_auth_show_utc_offset(self):
        return self.auth.get("show_utc_offset", True)

    def get_security_archive_not_delete(self):
        return self.security.get("archive_not_delete", True)
    def get_security_audit_read(self):
        return self.security.get("audit_read", False)
    def get_security_audit_write(self):
        return self.security.get("audit_write", False)
    def get_security_policy(self):
        " Default is Simple Security Policy "
        return self.security.get("policy", 1)
    def get_security_strict_ownership(self):
        """
            Ownership-rule for records without owner:
            True = not owned by any user (strict ownership, default)
            False = owned by any authenticated user
        """
        return self.security.get("strict_ownership", True)
    def get_security_map(self):
        return self.security.get("map", False)

    # -------------------------------------------------------------------------
    # Base settings
    def get_instance_name(self):
        """
            Instance Name - for management scripts. e.g. prod or test
        """
        return self.base.get("instance_name", "")
    def get_system_name(self):
        """
            System Name - for the UI & Messaging
        """
        return self.base.get("system_name", current.T("Sahana Eden Humanitarian Management Platform"))
    def get_system_name_short(self):
        """
            System Name (Short Version) - for the UI & Messaging
        """
        return self.base.get("system_name_short", "Sahana Eden")

    def get_base_debug(self):
        """
            Debug mode: Serve CSS/JS in separate uncompressed files
        """
        return self.base.get("debug", False)

    def get_base_allow_testing(self):
        """
            Allow testing of Eden using EdenTest
        """

        return self.base.get("allow_testing", True)

    def get_base_migrate(self):
        """ Whether to allow Web2Py to migrate the SQL database to the new structure """
        return self.base.get("migrate", True)

    def get_base_fake_migrate(self):
        """ Whether to have Web2Py create the .table files to match the expected SQL database structure """
        return self.base.get("fake_migrate", False)

    def get_base_prepopulate(self):
        """ Whether to prepopulate the database &, if so, which set of data to use for this """
        base = self.base
        setting = base.get("prepopulate", 1)
        if setting:
            options = base.get("prepopulate_options")
            return self.resolve_profile(options, setting)
        else:
            # Pre-populate off (production mode), don't bother resolving
            return 0

    def get_base_guided_tour(self):
        """ Whether the guided tours are enabled """
        return self.base.get("guided_tour", False)

    def get_base_public_url(self):
        """
            The Public URL for the site - for use in email links, etc
        """
        return self.base.get("public_url", "http://127.0.0.1:8000")

    def get_base_cdn(self):
        """
            Should we use CDNs (Content Distribution Networks) to serve some common CSS/JS?
        """
        return self.base.get("cdn", False)

    def get_chat_server(self):
        """
            Get the IP:port of the chat server if enabled or return False
        """
        return self.base.get("chat_server", False)

    def get_chatdb_string(self):
        chat_server = self.base.get("chat_server", False)
        db_get = self.database.get

        if (chat_server["server_db_type"] == "mysql"):
            db_string = "mysql://%s:%s@%s:%s/%s" % \
            (chat_server["server_db_username"] if chat_server["server_db_username"] else db_get("username", "sahana"),
                chat_server["server_db_password"] if chat_server["server_db_password"] else db_get("password", "password"),
                chat_server["server_db_ip"] if chat_server["server_db_ip"] else db_get("host", "localhost"),
                chat_server["server_db_port"] if chat_server["server_db_port"] else db_get("port", 3306),
                chat_server["server_db"] if chat_server["server_db"] else db_get("database", "openfiredb"))
        elif (chat_server["server_db_type"] == "postgres"):
            db_string = "postgres://%s:%s@%s:%s/%s" % \
            (chat_server["server_db_username"] if chat_server["server_db_username"] else db_get("username", "sahana"),
                chat_server["server_db_password"] if chat_server["server_db_password"] else db_get("password", "password"),
                chat_server["server_db_ip"] if chat_server["server_db_ip"] else db_get("host", "localhost"),
                chat_server["server_db_port"] if chat_server["server_db_port"] else db_get("port", 5432),
                chat_server["server_db"] if chat_server["server_db"] else db_get("database", "openfiredb"))
        else:
            from gluon import HTTP
            raise HTTP(501, body="Database type '%s' not recognised - please correct file models/000_config.py." % db_type)
        return db_string

    def get_base_session_memcache(self):
        """
            Should we store sessions in a Memcache service to allow sharing
            between multiple instances?
        """
        return self.base.get("session_memcache", False)

    def get_base_solr_url(self):
        """
            URL to connect to solr server
        """
        return self.base.get("solr_url", False)

    def get_import_callback(self, tablename, callback):
        """
            Lookup callback to use for imports in the following order:
                - custom [create, update]_onxxxx
                - default [create, update]_onxxxx
                - custom onxxxx
                - default onxxxx
            NB: Currently only onaccept is actually used
        """
        callbacks = self.base.get("import_callbacks", [])
        if tablename in callbacks:
            callbacks = callbacks[tablename]
            if callback in callbacks:
                return callbacks[callback]

        get_config = current.s3db.get_config
        default = get_config(tablename, callback)
        if default:
            return default

        if callback[:2] != "on":
            callback = callback[7:]

            if callback in callbacks:
                return callbacks[callback]

            default = get_config(tablename, callback)
            if default:
                return default

    # -------------------------------------------------------------------------
    # Logger settings
    def get_log_level(self):
        """
            Minimum severity level for logger: "DEBUG", "INFO", "WARNING",
            "ERROR", "CRITICAL". None = turn off logging
        """
        return "DEBUG" if self.base.get("debug") \
                       else self.log.get("level", None)

    def get_log_console(self):
        """
            True to enable console logging (sys.stderr)
        """
        return self.log.get("console", True)

    def get_log_logfile(self):
        """
            Log file name, None to turn off log file output
        """
        return self.log.get("logfile", None)

    def get_log_caller_info(self):
        """
            True to enable detailed caller info in log (filename,
            line number, function name), useful for diagnostics
        """
        return self.log.get("caller_info", False)

    # -------------------------------------------------------------------------
    # Database settings
    def get_database_type(self):
        return self.database.get("db_type", "sqlite").lower()

    def get_database_string(self):
        db_type = self.database.get("db_type", "sqlite").lower()
        pool_size = self.database.get("pool_size", 30)
        if (db_type == "sqlite"):
            db_string = "sqlite://storage.db"
        elif (db_type == "mysql"):
            db_get = self.database.get
            db_string = "mysql://%s:%s@%s:%s/%s" % \
                        (db_get("username", "sahana"),
                         db_get("password", "password"),
                         db_get("host", "localhost"),
                         db_get("port", None) or "3306",
                         db_get("database", "sahana"))
        elif (db_type == "postgres"):
            db_get = self.database.get
            db_string = "postgres://%s:%s@%s:%s/%s" % \
                        (db_get("username", "sahana"),
                         db_get("password", "password"),
                         db_get("host", "localhost"),
                         db_get("port", None) or "5432",
                         db_get("database", "sahana"))
        else:
            from gluon import HTTP
            raise HTTP(501, body="Database type '%s' not recognised - please correct file models/000_config.py." % db_type)
        return (db_string, pool_size)

    # -------------------------------------------------------------------------
    # Finance settings
    # @ToDo: Make these customisable per Organisation
    # => Move to a Table like hrm_course
    def get_fin_currencies(self):
        T = current.T
        currencies = {
            "EUR" : T("Euros"),
            "GBP" : T("Great British Pounds"),
            "USD" : T("United States Dollars"),
        }
        return self.fin.get("currencies", currencies)

    def get_fin_currency_default(self):
        return self.fin.get("currency_default", "USD") # Dollars

    def get_fin_currency_writable(self):
        return self.fin.get("currency_writable", True)

    # -------------------------------------------------------------------------
    # GIS (Map) Settings
    #
    def get_gis_api_bing(self):
        """ API key for Bing """
        return self.gis.get("api_bing", None)

    def get_gis_api_google(self):
        """
            API key for Google
            - needed for Earth, MapMaker & GeoCoder
            - defaults to localhost
        """
        return self.gis.get("api_google",
                            "ABQIAAAAgB-1pyZu7pKAZrMGv3nksRTpH3CbXHjuCVmaTc5MkkU4wO1RRhQWqp1VGwrG8yPE2KhLCPYhD7itFw")

    def get_gis_api_yahoo(self):
        """
            API key for Yahoo
            - deprecated
        """
        return self.gis.get("api_yahoo", None)

    def get_gis_building_name(self):
        """
            Display Building Name when selecting Locations
        """
        return self.gis.get("building_name", True)

    def get_gis_check_within_parent_boundaries(self):
        """
            Whether location Lat/Lons should be within the boundaries of the parent
        """
        return self.gis.get("check_within_parent_boundaries", True)

    def get_gis_cluster_fill(self):
        """
            Fill for Clustered points on Map, else default
        """
        return self.gis.get("cluster_fill", None)

    def get_gis_cluster_label(self):
        """
            Label Clustered points on Map?
        """
        return self.gis.get("cluster_label", True)

    def get_gis_cluster_stroke(self):
        """
            Stroke for Clustered points on Map, else default
        """
        return self.gis.get("cluster_stroke", None)

    def get_gis_select_fill(self):
        """
            Fill for Selected points on Map, else default
        """
        return self.gis.get("select_fill", None)

    def get_gis_select_stroke(self):
        """
            Stroke for Selected points on Map, else default
        """
        return self.gis.get("select_stroke", None)

    def get_gis_clear_layers(self):
        """
            Display Clear Layers Tool
            - defaults to being above Map's Layer Tree, but can also be set to "toolbar"
        """
        return self.gis.get("clear_layers", False)

    def get_gis_config_screenshot(self):
        """
            Should GIS configs save a screenshot when saved?
            - set the size if True: (width, height)
        """
        return self.gis.get("config_screenshot", None)

    def get_gis_countries(self):
        """
            Which country codes should be accessible to the location selector?
        """
        return self.gis.get("countries", [])

    def get_gis_display_l0(self):
        return self.gis.get("display_L0", False)
    def get_gis_display_l1(self):
        return self.gis.get("display_L1", True)

    def get_gis_duplicate_features(self):
        """
            Display duplicate features either side of the International date line?
        """
        return self.gis.get("duplicate_features", False)

    def get_gis_edit_group(self):
        """
            Edit Location Groups
        """
        return self.gis.get("edit_GR", False)

    def get_gis_geocode_imported_addresses(self):
        """
            Should Addresses imported from CSV be passed to a Geocoder to try and automate Lat/Lon?
        """
        return self.gis.get("geocode_imported_addresses", False)

    def get_gis_geolocate_control(self):
        """
            Whether the map should have a Geolocate control
            - also requires the presence of a Toolbar
        """
        return self.gis.get("geolocate_control", True)

    def get_gis_geonames_username(self):
        """
            Username for the GeoNames search box
        """
        return self.gis.get("geonames_username", None)

    def get_gis_geoserver_url(self):
        return self.gis.get("geoserver_url", "")
    def get_gis_geoserver_username(self):
        return self.gis.get("geoserver_username", "admin")
    def get_gis_geoserver_password(self):
        return self.gis.get("geoserver_password", "")

    def get_gis_getfeature_control(self):
        """
            Whether the map should have a WMS GetFeatureInfo control
            - also requires the presence of a Toolbar and queryable WMS layers
        """
        return self.gis.get("getfeature_control", True)

    def get_gis_latlon_selector(self):
        """
            Display Lat/Lon form fields when selecting Locations
        """
        return self.gis.get("latlon_selector", True)

    def get_gis_layer_metadata(self):
        """
            Use CMS to provide Metadata on Map Layers
        """
        return self.has_module("cms") and self.gis.get("layer_metadata", False)

    def get_gis_layer_properties(self):
        """
            Display Layer Properties Tool above Map's Layer Tree
        """
        return self.gis.get("layer_properties", True)

    def get_gis_layer_tree_base(self):
        " Display Base Layers folder in the Map's Layer Tree "
        return self.gis.get("layer_tree_base", True)

    def get_gis_layer_tree_overlays(self):
        " Display Overlays folder in the Map's Layer Tree "
        return self.gis.get("layer_tree_overlays", True)

    def get_gis_layer_tree_expanded(self):
        " Display folders in the Map's Layer Tree Open by default "
        return self.gis.get("layer_tree_expanded", True)

    def get_gis_layer_tree_radio(self):
        " Use a radio button for custom folders in the Map's Layer Tree "
        return self.gis.get("layer_tree_radio", False)

    def get_gis_layers_label(self):
        " Label for the Map's Layer Tree "
        return self.gis.get("layers_label", "Layers")

    def get_gis_location_represent_address_only(self):
        """
            Never use LatLon for Location Represents
        """
        return self.gis.get("location_represent_address_only", False)

    def get_gis_map_height(self):
        """
            Height of the Embedded Map
            Change this if-required for your theme
            NB API can override this in specific modules
        """
        return self.gis.get("map_height", 600)

    def get_gis_map_width(self):
        """
            Width of the Embedded Map
            Change this if-required for your theme
            NB API can override this in specific modules
        """
        return self.gis.get("map_width", 1000)

    def get_gis_map_selector(self):
        " Display a Map-based tool to select Locations "
        return self.gis.get("map_selector", True)

    def get_gis_marker_max_height(self):
        return self.gis.get("marker_max_height", 35)

    def get_gis_marker_max_width(self):
        return self.gis.get("marker_max_width", 30)

    def get_gis_max_features(self):
        """
            The maximum number of features to return in a Map Layer
            - more than this will prompt the user to zoom in to load the layer
            Lower this number to get extra performance from an overloaded server.
        """
        return self.gis.get("max_features", 2000)

    def get_gis_legend(self):
        """
            Should we display a Legend on the Map?
            - set to True to show a GeoExt Legend (default)
            - set to False to not show a Legend
            - set to "float" to use a floating DIV
        """
        return self.gis.get("legend", True)

    def get_gis_menu(self):
        """
            Should we display a menu of GIS configurations?
            - set to False to not show the menu (default)
            - set to the label to use for the menu to enable it
            e.g. T("Events") or T("Regions")
        """
        return self.gis.get("menu", False)

    def get_gis_mouse_position(self):
        """
            What style of Coordinates for the current Mouse Position
            should be shown on the Map?

            'normal', 'mgrs' or False
        """
        return self.gis.get("mouse_position", "normal")

    def get_gis_nav_controls(self):
        """
            Should the Map Toolbar display Navigation Controls?
        """
        return self.gis.get("nav_controls", False)

    def get_gis_label_overlays(self):
        """
            Label for the Map Overlays in the Layer Tree
        """
        return self.gis.get("label_overlays", "Overlays")

    def get_gis_overview(self):
        """
            Should the Map display an Overview Map?
        """
        return self.gis.get("overview", True)

    def get_gis_permalink(self):
        """
            Should the Map display a Permalink control?
        """
        return self.gis.get("permalink", True)

    def get_gis_poi_create_resources(self):
        """
            List of resources which can be directly added to the main map.
            Includes the type (point, line or polygon) and where they are to be
            accessed from (button, menu or popup)

            Defaults to the generic 'gis_poi' resource as a point from a button

            @ToDo: Complete the button vs menu vs popup
            @ToDo: S3PoIWidget() to allow other resources to pickup the passed Lat/Lon/WKT
        """
        T = current.T
        return self.gis.get("poi_create_resources",
                            [{"c": "gis",               # Controller
                              "f": "poi",               # Function
                              "table": "gis_poi",       # For permissions check
                              # Default:
                              #"type": "point",          # Feature Type: point, line or polygon
                              "label": T("Add PoI"),    # Label
                              #"tooltip": T("Add PoI"),  # Tooltip
                              "layer": "PoIs",          # Layer Name to refresh
                              "location": "button",     # Location to access from
                              },
                              ]
                            )

    def get_gis_poi_export_resources(self):
        """
            List of resources (tablenames) to import/export as PoIs from Admin Locations
            - KML & OpenStreetMap formats
        """
        return self.gis.get("poi_export_resources",
                            ["cr_shelter", "hms_hospital", "org_office"])

    def get_gis_postcode_selector(self):
        """
            Display Postcode form field when selecting Locations
        """
        return self.gis.get("postcode_selector", True)

    def get_gis_print(self):
        """
            Should the Map display a Print control?

            NB Requires installation of additional components:
               http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
        """
        return self.gis.get("print_button", False)

    #def get_gis_print_service(self):
    #    """
    #        URL for an external Print Service (based on the MapFish plugin for GeoServer)
    #         http://eden.sahanafoundation.org/wiki/BluePrint/GIS/Printing
    #    """
    #    return self.gis.get("print_service", "")

    def get_gis_save(self):
        """
            Should the main Map display a Save control?
            If there is a Toolbar, then this defaults to being inside the Toolbar, otherwise floating.
            If you wish it to float even when there is a toolbar, then specify "float"
        """
        return self.gis.get("save", True)

    def get_gis_scaleline(self):
        """
            Should the Map display a ScaleLine control?
        """
        return self.gis.get("scaleline", True)

    def get_gis_search_geonames(self):
        """
            Whether the GeoNames search box should be visible on the map
        """
        return self.gis.get("search_geonames", True)

    def get_gis_simplify_tolerance(self):
        """
            Default Tolerance for the Simplification of Polygons
            - a lower value means less simplification, which is suitable for higher-resolution local activities
            - a higher value is suitable for global views
        """
        return self.gis.get("simplify_tolerance", 0.01)

    def get_gis_spatialdb(self):
        """
            Does the database have Spatial extensions?
        """
        db_type = self.get_database_type()
        if db_type != "postgres":
            # Only Postgres supported currently
            return False
        else:
            return self.gis.get("spatialdb", False)

    def get_gis_widget_catalogue_layers(self):
        """
            Should Map Widgets display Catalogue Layers?
            - e.g. Profile & Summary pages
        """
        return self.gis.get("widget_catalogue_layers", False)

    def get_gis_widget_wms_browser(self):
        """
            Should Map Widgets display a WMS Browser?
            - e.g. Profile & Summary pages
            NB This also requires the active gis_config to have one configured
        """
        return self.gis.get("widget_wms_browser", False)

    def get_gis_toolbar(self):
        """
            Should the main Map display a Toolbar?
        """
        return self.gis.get("toolbar", True)

    def get_gis_zoomcontrol(self):
        """
            Should the Map display a Zoom control?
        """
        return self.gis.get("zoomcontrol", True)

    def get_gis_lookup_code(self):
        """
            Should the gis_location deduplication try codes as well as names?
            - if-desired, set to the Key of a Key/Value pair (e.g. "PCode")
        """
        return self.gis.get("lookup_code", False)

    # -------------------------------------------------------------------------
    # L10N Settings
    def get_L10n_default_language(self):
        return self.L10n.get("default_language", "en")

    def get_L10n_display_toolbar(self):
        return self.L10n.get("display_toolbar", True)

    def get_L10n_languages(self):
        return self.L10n.get("languages", OrderedDict([("ar", "العربية"),
                                                       ("zh-cn", "中文 (简体)"),
                                                       ("zh-tw", "中文 (繁體)"),
                                                       ("bs", "Bosanski"),
                                                       ("en", "English"),
                                                       ("fr", "Français"),
                                                       ("de", "Deutsch"),
                                                       ("el", "ελληνικά"),
                                                       ("es", "Español"),
                                                       ("it", "Italiano"),
                                                       ("ja", "日本語"),
                                                       ("km", "ភាសាខ្មែរ"),         # Khmer
                                                       ("ko", "한국어"),
                                                       ("mn", "Монгол хэл"),   # Mongolian
                                                       ("ne", "नेपाली"),          # Nepali
                                                       ("prs", "دری"),         # Dari
                                                       ("ps", "پښتو"),         # Pashto
                                                       ("pt", "Português"),
                                                       ("pt-br", "Português (Brasil)"),
                                                       ("ru", "русский"),
                                                       #("si", "සිංහල"),                # Sinhala
                                                       #("ta", "தமிழ்"),               # Tamil
                                                       #("th", "ภาษาไทย"),        # Thai
                                                       ("tl", "Tagalog"),
                                                       ("ur", "اردو"),
                                                       ("vi", "Tiếng Việt"),
                                                       ]))

    def get_L10n_languages_readonly(self):
        return self.L10n.get("languages_readonly", True)

    def get_L10n_religions(self):
        """
            Religions used in Person Registry

            @ToDo: find a better code
            http://eden.sahanafoundation.org/ticket/594
        """
        T = current.T
        return self.L10n.get("religions", {"none": T("none"),
                                           "christian": T("Christian"),
                                           "muslim": T("Muslim"),
                                           "jewish": T("Jewish"),
                                           "buddhist": T("Buddhist"),
                                           "hindu": T("Hindu"),
                                           "bahai": T("Bahai"),
                                           "other": T("other")
                                           })

    def get_L10n_date_format(self):
        """
            Lookup the Date Format - either by locale or by global setting
        """
        language = current.session.s3.language
        if language in self.date_formats:
            return self.date_formats.get(language)
        else:
            return self.L10n.get("date_format", "%Y-%m-%d")

    def get_L10n_time_format(self):
        return self.L10n.get("time_format", "%H:%M")

    def get_L10n_datetime_separator(self):
        return self.L10n.get("datetime_separator", " ")

    def get_L10n_datetime_format(self):
        return "%s%s%s" % (self.get_L10n_date_format(),
                           self.get_L10n_datetime_separator(),
                           self.get_L10n_time_format()
                           )

    def get_L10n_utc_offset(self):
        return self.L10n.get("utc_offset", "UTC +0000")

    def get_L10n_firstDOW(self):
        return self.L10n.get("firstDOW", 1)

    def get_L10n_lat_lon_format(self):
        """
            This is used to format latitude and longitude fields when they are
            displayed by eden. The format string may include the following
            placeholders:
            - %d -- Degress (integer)
            - %m -- Minutes (integer)
            - %s -- Seconds (double)
            - %f -- Degrees in decimal (double)
        """
        return self.L10n.get("lat_lon_display_format", "%f")

    def get_L10n_default_country_code(self):
        """ Default Telephone Country Code """
        return self.L10n.get("default_country_code", 1)

    def get_L10n_mandatory_lastname(self):
        return self.L10n.get("mandatory_lastname", False)

    def get_L10n_decimal_separator(self):
        """
            What should the decimal separator be in formatted numbers?
            - falls back to ISO standard of a comma
        """
        return self.L10n.get("decimal_separator", ",")

    def get_L10n_thousands_separator(self):
        """
            What should the thousands separator be in formatted numbers?
            - falls back to ISO standard of a space
        """
        return self.L10n.get("thousands_separator", " ")
    def get_L10n_thousands_grouping(self):
        return self.L10n.get("thousands_grouping", 3)

    def get_L10n_translate_cms_series(self):
        """
            Whether to translate CMS Series names
        """
        return self.L10n.get("translate_cms_series", False)

    def get_L10n_translate_gis_layer(self):
        """
            Whether to translate Layer names
        """
        return self.L10n.get("translate_gis_layer", False)

    def get_L10n_translate_gis_location(self):
        """
            Whether to translate Location names
        """
        return self.L10n.get("translate_gis_location", False)
    def get_L10n_name_alt_gis_location(self):
        """
            Whether to use Alternate Location names
        """
        return self.L10n.get("name_alt_gis_location", False)
    def get_L10n_pootle_url(self):
        """ URL for Pootle server """
        return self.L10n.get("pootle_url", "http://pootle.sahanafoundation.org/")
    def get_L10n_pootle_username(self):
        """ Username for Pootle server """
        return self.L10n.get("pootle_username", False)
    def get_L10n_pootle_password(self):
        """ Password for Pootle server """
        return self.L10n.get("pootle_password", False)

    # -------------------------------------------------------------------------
    # PDF settings
    def get_paper_size(self):
        return self.base.get("paper_size", "A4")
    def get_pdf_logo(self):
        return self.ui.get("pdf_logo", None)

    # Optical Character Recognition (OCR)
    def get_pdf_excluded_fields(self, resourcename):
        excluded_fields_dict = {
            "hms_hospital" : [
                "hrm_human_resource",
                ],

            "pr_group" : [
                "pr_group_membership",
                ],
            }
        excluded_fields =\
                excluded_fields_dict.get(resourcename, [])

        return excluded_fields

    # -------------------------------------------------------------------------
    # UI Settings
    #
    def get_ui_formstyle(self):
        """ Get the current form style """

        setting = self.ui.get("formstyle", "default")
        if setting in self.FORMSTYLE:
            # One of the standard supported formstyles
            return self.FORMSTYLE[setting]
        elif callable(setting):
            # A custom formstyle defined in the template
            return setting
        else:
            # A default web2py formstyle
            return setting

    def get_ui_filter_formstyle(self):
        """ Get the current filter form style """

        setting = self.ui.get("filter_formstyle", "default_inline")
        if callable(setting):
            return setting
        elif setting in self.FORMSTYLE:
            return self.FORMSTYLE[setting]
        else:
            return setting

    def get_ui_report_formstyle(self):
        """ Get the current report form style """

        setting = self.ui.get("report_formstyle", None)
        formstyles = self.FORMSTYLE
        if callable(setting):
            return setting
        elif setting in formstyles:
            return formstyles[setting]
        else:
            return setting

    def get_ui_inline_formstyle(self):
        """ Get the _inline formstyle for the current formstyle """

        setting = self.ui.get("formstyle", "default")

        formstyles = self.FORMSTYLE

        if isinstance(setting, basestring):
            inline_formstyle_name = "%s_inline" % setting
            if inline_formstyle_name in formstyles:
                return formstyles[inline_formstyle_name]
            elif setting in formstyles:
                return formstyles[setting]
        return setting

    def get_ui_datatables_dom(self):
        """
            DOM layout for dataTables:
            https://datatables.net/reference/option/dom
        """

        return self.ui.get("datatables_dom", "fril<'dataTable_table't>pi")

    def get_ui_datatables_initComplete(self):
        """
            Callback for dataTables
            - allows moving objects such as data_exports
        """

        return self.ui.get("datatables_initComplete", None)

    def get_ui_datatables_pagingType(self):
        """
            The style of Paging used by dataTables:
            https://datatables.net/reference/option/pagingType
        """

        return self.ui.get("datatables_pagingType", "full_numbers")

    def get_ui_datatables_responsive(self):
        """ Whether dataTables should be responsive when resized """

        return self.ui.get("datatables_responsive", True)

    def get_ui_default_cancel_button(self):
        """
            Whether to show a default cancel button in standalone
            create/update forms
        """
        return self.ui.get("default_cancel_button", False)

    def get_ui_filter_clear(self):
        """
            Whether to show a clear button in default FilterForms
            - and allows possibility to relabel &/or add a class
        """
        return self.ui.get("filter_clear", True)

    def get_ui_icons(self):
        """
            Standard icon set, one of:
            - "font-awesome"
            - "foundation"
        """
        return self.ui.get("icons", "font-awesome")

    def get_ui_custom_icons(self):
        """
            Custom icon CSS classes, a dict {abstract name: CSS class},
            can be used to partially override standard icons
        """
        return self.ui.get("custom_icons", None)

    def get_ui_icon_layout(self):
        """
            Callable to render icon HTML, which takes an ICON instance
            as parameter and returns valid XML as string
        """
        return self.ui.get("icon_layout", None)

    # -------------------------------------------------------------------------
    def get_ui_auth_user_represent(self):
        """
            Should the auth_user created_by/modified_by be represented by Name or Email?
            - defaults to email
        """
        return self.ui.get("auth_user_represent", "email")

    def get_ui_confirm(self):
        """
            For Delete actions
            Workaround for this Bug in Selenium with FF4:
                http://code.google.com/p/selenium/issues/detail?id=1604
        """
        return self.ui.get("confirm", True)

    def get_ui_export_formats(self):
        """
            Which export formats should we display?
            - specify a list of export formats to restrict
        """
        return self.ui.get("export_formats",
                           ("cap", "have", "kml", "map", "pdf", "rss", "xls", "xml"))

    def get_ui_hide_report_filter_options(self):
        """
            Show report filter options form by default
        """
        return self.ui.get("hide_report_filter_options", False)

    def get_ui_hide_report_options(self):
        """
            Hide report options form by default
        """
        return self.ui.get("hide_report_options", True)

    def get_ui_iframe_opens_full(self):
        """
            Open links in IFrames should open a full page in a new tab
        """
        return self.ui.get("iframe_opens_full", False)

    def get_ui_interim_save(self):
        """
            Render interim-save button in CRUD forms by default
        """
        return self.ui.get("interim_save", False)

    def get_ui_label_attachments(self):
        """
            Label for attachments tab
        """
        return current.T(self.ui.get("label_attachments", "Attachments"))

    def get_ui_label_camp(self):
        """ 'Camp' instead of 'Shelter'? """
        return self.ui.get("camp", False)

    def get_ui_label_cluster(self):
        """ UN-style deployment? """
        return self.ui.get("cluster", False)

    def get_ui_label_locationselector_map_point_add(self):
        """
            Label for the Location Selector button to add a Point to the Map
            e.g. 'Place on Map'
        """
        return current.T(self.ui.get("label_locationselector_map_point_add", "Place on Map"))

    def get_ui_label_locationselector_map_point_view(self):
        """
            Label for the Location Selector button to view a Point on the Map
            e.g. 'View on Map'
        """
        return current.T(self.ui.get("label_locationselector_map_point_view", "View on Map"))

    def get_ui_label_locationselector_map_polygon_add(self):
        """
            Label for the Location Selector button to draw a Polygon on the Map
            e.g. 'Draw on Map'
        """
        return current.T(self.ui.get("label_locationselector_map_polygon_add", "Draw on Map"))

    def get_ui_label_locationselector_map_polygon_view(self):
        """
            Label for the Location Selector button to view a Polygon on the Map
            e.g. 'View on Map'
        """
        return current.T(self.ui.get("label_locationselector_map_polygon_view", "View on Map"))

    def get_ui_label_mobile_phone(self):
        """
            Label for the Mobile Phone field
            e.g. 'Cell Phone'
        """
        return current.T(self.ui.get("label_mobile_phone", "Mobile Phone"))

    def get_ui_label_permalink(self):
        """
            Label for the Permalink on dataTables
        """
        return current.T(self.ui.get("label_permalink", "Link to this result"))

    def get_ui_label_postcode(self):
        """
            Label for the Postcode field
            e.g. 'ZIP Code'
        """
        return current.T(self.ui.get("label_postcode", "Postcode"))

    def get_ui_label_read(self):
        """
            Label for buttons in list views which lead to a Read-only 'Display' page
        """
        return self.ui.get("read_label", "Open")

    def get_ui_label_update(self):
        """
            Label for buttons in list views which lead to an Editable 'Update' page
        """
        return self.ui.get("update_label", "Open")

    def get_ui_multiselect_widget(self):
        """
            Whether all dropdowns should use the S3MultiSelectWidget
            - currently respected by Auth Registration & S3LocationSelectorWidget2

            Options:
                False (default): No widget
                True: Widget, with no header
                "search": Widget with the search header
        """
        return self.ui.get("multiselect_widget", False)

    def get_ui_navigate_away_confirm(self):
        """
            Whether to enable a warning when users navigate away from a page with unsaved changes
        """
        return self.ui.get("navigate_away_confirm", True)

    def get_ui_search_submit_button(self):
        """
            Class for submit buttons in search views
        """
        return self.ui.get("search_submit_button", "search-button")

    def get_ui_social_buttons(self):
        """
            Display social media Buttons in the footer?
            - requires support in the Theme
        """
        return self.ui.get("social_buttons", False)

    def get_ui_summary(self):
        """
            Default Summary Page Configuration (can also be
            configured per-resource using s3db.configure)

            @example:

            settings.ui.summary = [
                {
                    "name": "table",    # the section name

                    "label": "Table",   # the section label, will
                                        # automatically be translated

                    "common": False,    # show this section on all tabs

                    "translate": True,  # turn automatic label translation on/off

                    "widgets": [        # list of widgets for this section
                        {
                            "method": "datatable",  # widget method, either a
                                                    # name that resolves into
                                                    # a S3Method, or a callable
                                                    # to render the widget

                            "filterable": True,     # Whether the widget can
                                                    # be filtered by the summary
                                                    # filter form
                        }
                    ]
                }
            ]

        """

        return self.ui.get("summary", ({"common": True,
                                        "name": "add",
                                        "widgets": [{"method": "create"}],
                                        },
                                       {"common": True,
                                        "name": "cms",
                                        "widgets": [{"method": "cms"}]
                                        },
                                       {"name": "table",
                                        "label": "Table",
                                        "widgets": [{"method": "datatable"}]
                                        },
                                       {"name": "charts",
                                        "label": "Report",
                                        "widgets": [{"method": "report",
                                                     "ajax_init": True}]
                                        },
                                       {"name": "map",
                                        "label": "Map",
                                        "widgets": [{"method": "map",
                                                     "ajax_init": True}],
                                        },
                                       ))

    def get_ui_filter_auto_submit(self):
        """
            Time in milliseconds after the last filter option change to
            automatically update the filter target(s), set to 0 to disable
        """
        return self.ui.get("filter_auto_submit", 800)

    def get_ui_report_auto_submit(self):
        """
            Time in milliseconds after the last filter option change to
            automatically update the filter target(s), set to 0 to disable
        """
        return self.ui.get("report_auto_submit", 800)

    def get_ui_use_button_icons(self):
        """
            Use icons on action buttons (requires corresponding CSS)
        """
        return self.ui.get("use_button_icons", False)

    def get_ui_hierarchy_theme(self):
        """
            Theme for the S3HierarchyWidget.
            'css' is a folder relative to static/styles
            - /jstree.css or /jstree.min.css is added as-required
        """
        return self.ui.get("hierarchy_theme", dict(css = "plugins",
                                                   icons = False,
                                                   stripes = True,
                                                   ))

    def get_ui_inline_component_layout(self):
        """
            Layout for S3SQLInlineComponent
        """
        # Use this to also catch old-style classes (not recommended):
        #import types
        #elif isinstance(layout, (type, types.ClassType)):

        layout = self.ui.get("inline_component_layout")
        if not layout:
            from s3 import S3SQLSubFormLayout
            layout = S3SQLSubFormLayout()
        elif isinstance(layout, type):
            # Instantiate only now when it's actually requested
            # (because it may inject JS which is not needed if unused)
            layout = layout()
        # Replace so it doesn't get instantiated twice
        self.ui.inline_component_layout = layout
        return layout

    # =========================================================================
    # Messaging
    #
    def get_msg_max_send_retries(self):
        """
            Maximum number of retries to send a message before
            it is regarded as permanently failing; set to None
            to retry forever.
        """
        return self.msg.get("max_send_retries", 9)

    # -------------------------------------------------------------------------
    # Mail settings
    def get_mail_server(self):
        return self.mail.get("server", "127.0.0.1:25")

    def get_mail_server_login(self):
        return self.mail.get("login", False)

    def get_mail_server_tls(self):
        """
            Does the Mail Server use TLS?
             - default Debian is False
             - GMail is True
        """
        return self.mail.get("tls", False)
    def get_mail_sender(self):
        """
            The From Address for all Outbound Emails
        """
        return self.mail.get("sender", None)
    def get_mail_approver(self):
        """
            The default Address to send Requests for New Users to be Approved
            OR
            UUID of Role of users who should receive Requests for New Users to be Approved
            - unless overridden by per-domain entries in auth_organsiation
        """
        return self.mail.get("approver", "useradmin@example.org")

    def get_mail_default_subject(self):
        """
            Use system_name_short as default email subject (Appended).
        """
        return self.mail.get("default_email_subject", False)

    def get_mail_auth_user_in_subject(self):
        """
            Append name and surname of logged in user to email subject
        """
        return self.mail.get("mail.auth_user_in_email_subject", False)

    def get_mail_limit(self):
        """
            A daily limit to the number of messages which can be sent
        """
        return self.mail.get("limit", None)

    # -------------------------------------------------------------------------
    # Parser
    def get_msg_parser(self):
        """
            Which template folder to use to load parser.py
        """
        return self.msg.get("parser", "default")

    # -------------------------------------------------------------------------
    # Notifications
    def get_msg_notify_subject(self):
        """
            Template for the subject line in update notifications.

            Available placeholders:
                $S = System Name (long)
                $s = System Name (short)
                $r = Resource Name

            Use {} to separate the placeholder from immediately following
            identifier characters (like: ${placeholder}text).
        """
        return self.msg.get("notify_subject",
                            "$s %s: $r" % current.T("Update Notification"))

    def get_msg_notify_email_format(self):
        """
            The preferred email format for update notifications,
            "text" or "html".
        """
        return self.msg.get("notify_email_format", "text")

    def get_msg_notify_renderer(self):
        """
            Custom content renderer function for update notifications,
            function()
        """
        return self.msg.get("notify_renderer", None)

    # -------------------------------------------------------------------------
    # SMS
    #
    def get_msg_require_international_phone_numbers(self):
        """
            Requires the E.123 international phone number
            notation where needed (e.g. SMS)
        """

        return self.msg.get("require_international_phone_numbers", True)

    # =========================================================================
    # Search

    # -------------------------------------------------------------------------
    def get_search_max_results(self):
        """
            The maximum number of results to return in an Autocomplete Search
            - more than this will prompt the user to enter a more exact match
            Lower this number to get extra performance from an overloaded server.
        """
        return self.search.get("max_results", 200)

    # -------------------------------------------------------------------------
    # Filter Manager Widget
    def get_search_filter_manager(self):
        """ Enable the filter manager widget """
        return self.search.get("filter_manager", True)

    def get_search_filter_manager_allow_delete(self):
        """ Allow deletion of saved filters """
        return self.search.get("filter_manager_allow_delete", True)

    def get_search_filter_manager_save(self):
        """ Text for saved filter save-button """
        return self.search.get("filter_manager_save", None)

    def get_search_filter_manager_update(self):
        """ Text for saved filter update-button """
        return self.search.get("filter_manager_update", None)

    def get_search_filter_manager_delete(self):
        """ Text for saved filter delete-button """
        return self.search.get("filter_manager_delete", None)

    def get_search_filter_manager_load(self):
        """ Text for saved filter load-button """
        return self.search.get("filter_manager_load", None)

    # =========================================================================
    # Sync
    #
    def get_sync_mcb_resource_identifiers(self):
        """
            Resource (=data type) identifiers for synchronization with
            Mariner CommandBridge, a dict {tablename:id}
        """

        return self.sync.get("mcb_resource_identifiers", {})

    def get_sync_mcb_domain_identifiers(self):
        """
            Domain (of origin) identifiers for synchronization with
            Mariner CommandBridge, a dict {domain: id} where
            "domain" means the domain prefix of the record UUID
            (e.g. uuid "wrike/IKY0192834" => domain "wrike"),
            default domain is "sahana"
        """

        return self.sync.get("mcb_domain_identifiers", {})

    # =========================================================================
    # Modules

    # -------------------------------------------------------------------------
    # CAP: Common Alerting Protocol
    #
    def get_cap_identifier_prefix(self):
        """
            Prefix to be prepended to identifiers of CAP alerts
        """
        return self.cap.get("identifier_prefix", "")

    def get_cap_identifier_suffix(self):
        """
            Suffix to be appended to identifiers of CAP alerts
        """
        return self.cap.get("identifier_suffix", "")

    def get_cap_codes(self):
        """
            Default codes for CAP alerts

            should return a list of dicts:
            [ {"key": "<ValueName>, "value": "<Value>",
               "comment": "<Help string>", "mutable": True|False},
              ...]
        """
        return self.cap.get("codes", [])

    def get_cap_event_codes(self):
        """
            Default alert codes for CAP info segments

            should return a list of dicts:
            [ {"key": "<ValueName>, "value": "<Value>",
               "comment": "<Help string>", "mutable": True|False},
              ...]
        """
        return self.cap.get("event_codes", [])

    def get_cap_parameters(self):
        """
            Default parameters for CAP info segments

            should return a list of dicts:
            [ {"key": "<ValueName>, "value": "<Value>",
               "comment": "<Help string>", "mutable": True|False},
              ...]
        """
        return self.cap.get("parameters", [])

    def get_cap_geocodes(self):
        """
            Default geocodes.

            should return a list of dicts:
            [ {"key": "<ValueName>, "value": "<Value>",
               "comment": "<Help string>", "mutable": True|False},
              ...]
        """
        return self.cap.get("geocodes", [])

    def get_cap_base64(self):
        """
            Should CAP resources be base64 encoded and embedded in the alert message?
        """
        return self.cap.get("base64", False)

    def get_cap_languages(self):
        """
            Languages for CAP info segments.
            This gets filled in the drop-down for selecting languages.
            These values should conform to RFC 3066.

            For a full list of languages and their codes, see:
                http://www.i18nguy.com/unicode/language-identifiers.html
        """

        return self.cap.get("languages", OrderedDict([("ar", "العربية"),
                                                      ("en-US", "English"),
                                                      ("es", "Español"),
                                                      ("fr", "Français"),
                                                      ("pt", "Português"),
                                                      ("ru", "русский"),
                                                      ]))

    def get_cap_priorities(self):
        """
            Settings for CAP priorities

            Should be an ordered dict of the format
            OrderedDict([
                            ("<value>, "<Translated title>", <urgency>, <severity>, <certainty>, <color>),
                             ...
                        ]) """
        T = current.T
        return self.cap.get("priorities", [
                ("Urgent", T("Urgent"), "Immediate", "Extreme", "Observed", "red"),
                ("High", T("High"), "Expected", "Severe", "Observed", "orange"),
                ("Low", T("Low"), "Expected", "Moderate", "Observed", "green")
                ])

    # -------------------------------------------------------------------------
    # CMS: Content Management System
    #
    def get_cms_bookmarks(self):
        """
            Whether to allow users to bookmark Posts in News feed
        """
        return self.cms.get("bookmarks", False)

    def get_cms_filter_open(self):
        """
            Whether the filter form on the Newsfeed should default to Open or Closed
        """
        return self.cms.get("filter_open", False)

    def get_cms_location_click_filters(self):
        """
            Whether clicking on a location in the Newsfeed should activate
            the filter to that location, instead of opening the profile page
        """
        return self.cms.get("location_click_filters", False)

    def get_cms_organisation(self):
        """
            Which field to use for the Organisation of Posts:
                * None
                * created_by$organisation_id
                * post_organisation.organisation_id
        """
        return self.cms.get("organisation", "created_by$organisation_id")

    def get_cms_organisation_group(self):
        """
            Which field to use for the Organisation Group of Posts:
                * None
                * created_by$org_group_id
                * post_organisation_group.group_id
        """
        return self.cms.get("organisation_group", None)

    def get_cms_person(self):
        """
            Which field to use for the Author of Posts:
                * None
                * created_by
                * person_id
        """
        return self.cms.get("person", "created_by")

    def get_cms_richtext(self):
        """
            Whether to use RichText editor in News feed
        """
        return self.cms.get("richtext", False)

    def get_cms_show_events(self):
        """
            Whether to show Events in News Feed
        """
        return self.cms.get("show_events", False)

    def get_cms_show_links(self):
        """
            Whether to show Links (such as Sources) in News Feed
        """
        return self.cms.get("show_links", False)

    def get_cms_show_tags(self):
        """
            Whether to show Tags in News Feed
        """
        return self.cms.get("show_tags", False)

    def get_cms_show_titles(self):
        """
            Whether to show post Titles in News Feed
        """
        return self.cms.get("show_titles", False)

    # -------------------------------------------------------------------------
    # Shelters
    #
    def get_cr_shelter_population_dynamic(self):
        """
            Whether Shelter Population should be done manually (False)
            or automatically based on the registrations (True)
            and displaying all fields used by the automatic evaluation of current
            shelter population:
            "available_capacity_day",
            "available_capacity_night",
            "population_day",
            "population_night".
        """
        # Only together with people registration:
        if not self.get_cr_shelter_people_registration():
            return False
        return self.cr.get("shelter_population_dynamic", False)

    def get_cr_shelter_people_registration(self):
        """
            Disable functionality to track individuals in shelters
        """
        return self.cr.get("people_registration", True)

    def get_cr_shelter_housing_unit_management(self):
        """
            Enable the use of tab "Housing Unit" and enable the housing unit
            selection during evacuees registration.
        """
        return self.cr.get("shelter_housing_unit_management", False)

    # -------------------------------------------------------------------------
    # Deployments
    #
    def get_deploy_hr_label(self):
        """
            Label for deployable Human Resources
            e.g. 'Staff', 'Volunteer' (CERT), 'Member' (RDRT)
        """
        return self.deploy.get("hr_label", "Staff")

    # -------------------------------------------------------------------------
    # Events
    #
    def get_event_types_hierarchical(self):
        """
            Whether Event Types are Hierarchical or not
        """
        return self.event.get("types_hierarchical", False)

    def get_incident_types_hierarchical(self):
        """
            Whether Incident Types are Hierarchical or not
        """
        return self.event.get("incident_types_hierarchical", False)

    # -------------------------------------------------------------------------
    # Evacuees
    #
    def get_evr_group_types(self):
        """
            Evacuees Group Types
        """
        T = current.T
        return self.evr.get("group_types", {1: T("other"),
                                            2: T("Family"),
                                            3: T("Tourist group"),
                                            4: T("Society"),
                                            5: T("Company"),
                                            6: T("Convent"),
                                            7: T("Hotel"),
                                            8 :T("Hospital"),
                                            9 :T("Orphanage")
                                            })

    def get_evr_show_physical_description(self):
        """
            Show Evacuees physical description
        """
        return self.evr.get("physical_description", True)

    def get_evr_link_to_organisation(self):
        """
            Link evacuees to Organisations.
        """
        return self.evr.get("link_to_organisation", False)


    # -------------------------------------------------------------------------
    # Hospital Registry
    #
    def get_hms_track_ctc(self):
        return self.hms.get("track_ctc", False)

    def get_hms_activity_reports(self):
        return self.hms.get("activity_reports", False)

    # -------------------------------------------------------------------------
    # Human Resource Management
    #
    #def get_hrm_human_resource_label(self):
    #    """
    #        Label for 'Human Resources'
    #        e.g. 'Contacts'
    #    """
    #    return current.T(self.hrm.get("human_resource_label", "Staff"))

    def get_hrm_staff_label(self):
        """
            Label for 'Staff'
            e.g. 'Contacts'
        """
        return current.T(self.hrm.get("staff_label", "Staff"))

    def get_hrm_organisation_label(self):
        """
            Label for Organisations in Human Resources
        """
        return current.T(self.hrm.get("organisation_label", "Organization"))

    def get_hrm_email_required(self):
        """
            If set to True then Staff & Volunteers require an email address
        """
        return self.hrm.get("email_required", True)

    def get_hrm_location_staff(self):
        """
            What to use to position Staff on the Map when not Tracking them
            - valid options are:
                "site_id" - Use the HR's Site Location
                "person_id" - Use the HR's Person Location (i.e. Home Address)
                ("person_id", "site_id") - Use the HR's Person Location if-available, fallback to the Site if-not
                ("site_id","person_id") - Use the HR's Site Location if-available, fallback to the Person's Home Address if-not
            NB This is read onaccept of editing Home Addresses & Assigning Staff to Sites so is not a fully-dynamic change
            - onaccept is used for performance (avoiding joins)
        """
        return self.hrm.get("location_staff", "site_id")

    def get_hrm_location_vol(self):
        """
            What to use to position Volunteers on the Map when not Tracking them
            - valid options are:
                "site_id" - Use the HR's Site Location
                "person_id" - Use the HR's Person Location (i.e. Home Address)
                ("person_id", "site_id") - Use the HR's Person Location if-available, fallback to the Site if-not
                ("site_id","person_id") - Use the HR's Site Location if-available, fallback to the Person's Home Address if-not
            NB This is read onaccept of editing Home Addresses & Assigning Volunteers to Sites so is not a fully-dynamic change
            - onaccept is used for performance (avoiding joins)
        """
        return self.hrm.get("location_vol", "person_id")

    def get_hrm_org_dependent_job_titles(self):
        """
            If set to True then the Job Titles Catalog is Organisation-dependent (i.e. each root org sees a different Catalog)
        """
        return self.hrm.get("org_dependent_job_titles", False)

    def get_hrm_org_required(self):
        """
            If set to True then Staff & Volunteers require an Organisation
        """
        return self.hrm.get("org_required", True)

    def get_hrm_deletable(self):
        """
            If set to True then HRM records are deletable rather than just being able to be marked as obsolete
        """
        return self.hrm.get("deletable", True)

    def get_hrm_filter_certificates(self):
        """
            If set to True then Certificates are filtered by (Root) Organisation
            & hence certificates from other Organisations cannot be added to an HR's profile (except by Admins)
        """
        return self.hrm.get("filter_certificates", False)

    def get_hrm_multiple_job_titles(self):
        """
            If set to True then HRs can have multiple Job Titles
        """
        return self.hrm.get("multi_job_titles", False)

    def get_hrm_show_staff(self):
        """
            If set to True then show 'Staff' options when HRM enabled
            - needs a separate setting as vol requires hrm, but we may only wish to show Volunteers
        """
        return self.hrm.get("show_staff", True)

    def get_hrm_site_contact_unique(self):
        """
            Whether there can be multiple site contacts per site
            - disable this if needing a separate contact per sector
        """
        return self.hrm.get("site_contact_unique", True)

    def get_hrm_skill_types(self):
        """
            If set to True then Skill Types are exposed to the UI
            - each skill_type needs it's own set of competency levels
            If set to False then Skill Types are hidden from the UI
            - all skills use the same skill_type & hence the same set of competency levels
        """
        return self.hrm.get("skill_types", False)

    def get_hrm_staff_experience(self):
        """
            Whether to use Experience for Staff &, if so, which table to use
            - options are: False, "experience"
        """
        return self.hrm.get("staff_experience", "experience")

    def get_hrm_salary(self):
        """
            Whether to track salaries of staff
        """
        return self.hrm.get("salary", False)

    def get_hrm_vol_active(self):
        """
            Whether to use a 'Active' field for Volunteers &, if so, whether
            this is set manually or calculated by a function
            - options are: False, True or a function
        """
        return self.hrm.get("vol_active", False)

    def get_hrm_vol_active_tooltip(self):
        """
            The tooltip to show when viewing the Active status in the Volunteer RHeader
        """
        return self.hrm.get("vol_active_tooltip", None)

    def get_hrm_vol_experience(self):
        """
            Whether to use Experience for Volunteers &, if so, which table to use
            - options are: False, "experience", "programme" or "both"
        """
        return self.hrm.get("vol_experience", "programme")

    def get_hrm_show_organisation(self):
        """
            Whether Human Resource representations should include the Organisation
        """
        return self.hrm.get("show_organisation", False)

    def get_hrm_teams(self):
        """
            Whether Human Resources should use Teams
            & what to call them (Teams or Groups currently supported)
        """
        return self.hrm.get("teams", "Teams")

    def get_hrm_cv_tab(self):
        """
            Whether Human Resources should consolidate tabs into 1x CV page:
            * Awards
            * Education
            * Experience
            * Training
            * Skills
        """
        return self.hrm.get("cv_tab", False)

    def get_hrm_record_tab(self):
        """
            Whether Human Resources should consolidate tabs into 1x CV page:
            * Staff Record
            * Group Membership
        """
        return self.hrm.get("record_tab", False)

    def get_hrm_use_awards(self):
        """
            Whether Volunteers should use Awards
        """
        return self.hrm.get("use_awards", True)

    def get_hrm_use_certificates(self):
        """
            Whether Human Resources should use Certificates
        """
        return self.hrm.get("use_certificates", True)

    def get_hrm_use_code(self):
        """
            Whether Human Resources should use Staff/Volunteer IDs
        """
        return self.hrm.get("use_code", False)

    def get_hrm_use_credentials(self):
        """
            Whether Human Resources should use Credentials
        """
        return self.hrm.get("use_credentials", True)

    def get_hrm_use_description(self):
        """
            Whether Human Resources should use Physical Description
        """
        return self.hrm.get("use_description", True)

    def get_hrm_use_education(self):
        """
            Whether Human Resources should show Education
        """
        return self.hrm.get("use_education", False)

    def get_hrm_use_id(self):
        """
            Whether Human Resources should show ID Tab
        """
        return self.hrm.get("use_id", True)

    def get_hrm_use_skills(self):
        """
            Whether Human Resources should use Skills
        """
        return self.hrm.get("use_skills", True)

    def get_hrm_use_trainings(self):
        """
            Whether Human Resources should use Trainings
        """
        return self.hrm.get("use_trainings", True)

    def get_hrm_activity_types(self):
        """
            HRM Activity Types (for experience record),
            a dict {"code": "label"}, None to deactivate (default)
        """
        return self.hrm.get("activity_types", None)

    # -------------------------------------------------------------------------
    # Inventory Management Settings
    #
    def get_inv_collapse_tabs(self):
        return self.inv.get("collapse_tabs", True)

    def get_inv_facility_label(self):
        return self.inv.get("facility_label", current.T("Warehouse"))

    def get_inv_direct_stock_edits(self):
        """
            Can Stock levels be adjusted directly?
            - defaults to False
        """
        return self.inv.get("direct_stock_edits", False)

    def get_inv_send_show_mode_of_transport(self):
        """
            Show mode of transport on Sent Shipments
        """
        return self.inv.get("show_mode_of_transport", False)

    def get_inv_send_show_org(self):
        """
            Show Organisation on Sent Shipments
        """
        return self.inv.get("send_show_org", True)

    def get_inv_send_show_time_in(self):
        """
            Show Time In on Sent Shipments
        """
        return self.inv.get("send_show_time_in", False)

    def get_inv_stock_count(self):
        """
            Call Stock Adjustments 'Stock Counts'
        """
        return self.inv.get("stock_count", True)

    def get_inv_track_pack_values(self):
        """
            Whether or not Pack values are tracked
        """
        return self.inv.get("track_pack_values", True)

    def get_inv_item_status(self):
        """
            Item Statuses which can also be Sent Shipment Types
        """
        T = current.T
        return self.inv.get("item_status", {0: current.messages["NONE"],
                                            1: T("Dump"),
                                            2: T("Sale"),
                                            3: T("Reject"),
                                            4: T("Surplus")
                                            })

    def get_inv_shipment_name(self):
        """
            Get the name of Shipments
            - currently supported options are:
            * shipment
            * order
        """
        return self.inv.get("shipment_name", "shipment")

    def get_inv_shipment_types(self):
        """
            Shipment types which are common to both Send & Receive
        """
        return self.inv.get("shipment_types", {
                                0 : current.messages["NONE"],
                                11: current.T("Internal Shipment"),
                                })

    def get_inv_send_types(self):
        """
            Shipment types which are just for Send
        """
        return self.inv.get("send_types", {21: current.T("Distribution"),
                                           })

    def get_inv_send_type_default(self):
        """
            Which Shipment type is default
        """
        return self.inv.get("send_type_default", 0)

    def get_inv_recv_types(self):
        """
            Shipment types which are just for Receive
        """
        T = current.T
        return self.inv.get("recv_types", {#31: T("Other Warehouse"), Same as Internal Shipment
                                           32: T("Donation"),
                                           #33: T("Foreign Donation"),
                                           34: T("Purchase"),
                                           })

    def get_inv_send_form_name(self):
        return self.inv.get("send_form_name", "Waybill")

    def get_inv_send_ref_field_name(self):
        return self.inv.get("send_ref_field_name", "Waybill Number")

    def get_inv_send_shortname(self):
        return self.inv.get("send_shortname", "WB")

    def get_inv_recv_form_name(self):
        return self.inv.get("recv_form_name", "Goods Received Note")

    def get_inv_recv_shortname(self):
        return self.inv.get("recv_shortname", "GRN")

    # -------------------------------------------------------------------------
    # IRS
    #
    def get_irs_vehicle(self):
        """
            Use Vehicles to respond to Incident Reports?
        """
        return self.irs.get("vehicle", False)

    # -------------------------------------------------------------------------
    # Members
    #
    def get_member_cv_tab(self):
        """
            Whether Members should consolidate tabs into 1x CV page:
            * Awards
            * Education
            * Experience
            * Training
            * Skills
        """
        return self.member.get("cv_tab", False)

    # -------------------------------------------------------------------------
    # Organisations
    #
    def get_org_autocomplete(self):
        """
            Whether organisation_id fields should use an Autocomplete instead of a dropdown
        """
        return self.org.get("autocomplete", False)

    def get_org_branches(self):
        """
            Whether to support Organisation Branches or not
        """
        return self.org.get("branches", False)

    def get_org_branches_tree_view(self):
        """
            Show branches of an organisation as tree rather than as table
        """
        return self.org.get("branches_tree_view", False)

    def get_org_facility_types_hierarchical(self):
        """
            Whether Facility Types are Hierarchical or not
        """
        return self.org.get("facility_types_hierarchical", False)

    def get_org_organisation_location_context(self):
        """
            The Context to use for displaying Organisation Locations
            - defaults to the Organisation's Sites
            - can also set to "organisation_location.location_id"
        """
        return self.org.get("organisation_location_context", "site.location_id")

    def get_org_organisation_types_hierarchical(self):
        """
            Whether Organisation Types are Hierarchical or not
        """
        return self.org.get("organisation_types_hierarchical", False)

    def get_org_organisation_types_multiple(self):
        """
            Whether Organisation Types are Multiple or not
        """
        return self.org.get("organisation_types_multiple", False)

    def get_org_groups(self):
        """
            Whether to support Organisation Groups or not
            & what their name is:
            'Coalition'
            'Network'
        """
        return self.org.get("groups", False)

    def get_org_regions(self):
        """
            Whether to support Organisation Regions or not
        """
        return self.org.get("regions", False)

    def get_org_regions_hierarchical(self):
        """
            Whether Organisation Regions are Hierarchical or not
        """
        return self.org.get("regions_hierarchical", False)

    def get_org_resources_tab(self):
        """
            Whether to show a Tab for Organisation Resources
        """
        return self.org.get("resources_tab", False)

    def get_org_services_hierarchical(self):
        """
            Whether Organisation Servics are Hierarchical or not
        """
        return self.org.get("services_hierarchical", False)

    def get_org_site_code_len(self):
        """
            Length of auto-generated Codes for Facilities (org_site)
        """
        return self.org.get("site_code_len", 10)

    def get_org_site_label(self):
        """
            Label for site_id fields
        """
        return current.T(self.org.get("site_label", "Facility"))

    def get_org_site_inv_req_tabs(self):
        """
            Whether Sites should have Tabs for Inv/Req
        """
        return self.org.get("site_inv_req_tabs", True)

    def get_org_site_autocomplete(self):
        """
            Whether site_id fields should use an Autocomplete instead of a dropdown
        """
        return self.org.get("site_autocomplete", False)

    def get_org_site_autocomplete_fields(self):
        """
            Which extra fields should be returned in S3SiteAutocompleteWidget
        """
        return self.org.get("site_autocomplete_fields", ("instance_type",))

    def get_org_site_last_contacted(self):
        """
            Whether to display the last_contacted field for a Site
        """
        return self.org.get("site_last_contacted", False)

    def get_org_site_volunteers(self):
        """
            Whether volunteers can be assigned to Sites
        """
        return self.org.get("site_volunteers", False)

    def get_org_summary(self):
        """
            Whether to use Summary fields for Organisation/Office:
                # National/International staff
        """
        return self.org.get("summary", False)

    def set_org_dependent_field(self,
                                tablename=None,
                                fieldname=None,
                                enable_field=True):
        """
            Enables/Disables optional fields according to a user's Organisation
            - must specify either field or tablename/fieldname
                                           (e.g. for virtual fields)
        """

        enabled = False
        dependent_fields = self.org.get("dependent_fields", None)
        if dependent_fields:
            org_name_list = dependent_fields.get("%s.%s" % (tablename,
                                                            fieldname),
                                                 None)

            if org_name_list:
                auth = current.auth
                if auth.s3_has_role(auth.get_system_roles().ADMIN):
                    # Admins see all fields unless disabled for all orgs in this deployment
                    enabled = True
                else:
                    root_org = auth.root_org_name()
                    enabled = root_org in org_name_list

        if enable_field:
            field = current.s3db[tablename][fieldname]
            field.readable = enabled
            field.writable = enabled

        return enabled

    def get_org_office_code_unique(self):
        """
            Whether Office code is unique
        """
        return self.org.get("office_code_unique", False)

    def get_org_facility_code_unique(self):
        """
            Whether Facility code is unique
        """
        return self.org.get("facility_code_unique", False)

    # -------------------------------------------------------------------------
    # Persons
    #
    def get_pr_age_group(self, age):
        """
            Function to provide the age group for an age
        """
        fn = self.pr.get("age_group", None)
        if fn:
            group = fn(age)
        else:
            # Default
            if age < 18 :
                group = "-17" # "< 18"/" < 18" don't sort correctly
            elif age < 25 :
                group = "18-24"
            elif age < 40:
                group = "25-39"
            elif age < 60:
                group = "40-59"
            else:
                group = "60+"
        return group

    def get_pr_import_update_requires_email(self):
        """
            During imports, records are only updated if the import
            item contains a (matching) email address
        """
        return self.pr.get("import_update_requires_email", True)

    def get_pr_lookup_duplicates(self):
        """
            Whether the AddPersonWidget2 does a fuzzy search for duplicates

            NB This setting has no effect with the old AddPersonWidget
        """
        return self.pr.get("lookup_duplicates", False)

    def get_pr_request_dob(self):
        """ Include Date of Birth in the AddPersonWidget[2] """
        return self.pr.get("request_dob", True)

    def get_pr_request_gender(self):
        """ Include Gender in the AddPersonWidget[2] """
        return self.pr.get("request_gender", True)

    def get_pr_request_home_phone(self):
        """ Include Home Phone in the AddPersonWidget2 """
        return self.pr.get("request_home_phone", False)

    def get_pr_name_format(self):
        """ Format with which to represent Person Names """
        return self.pr.get("name_format", "%(first_name)s %(middle_name)s %(last_name)s")

    def get_pr_select_existing(self):
        """
            Whether the AddPersonWidget allows selecting existing PRs
            - set to True if Persons can be found in multiple contexts
            - set to False if just a single context

            NB This setting has no effect with the new AddPersonWidget2
        """
        return self.pr.get("select_existing", True)

    def get_pr_search_shows_hr_details(self):
        """
            Whether S3PersonAutocompleteWidget results show the details of their HR record
        """
        return self.pr.get("search_shows_hr_details", True)

    def get_pr_show_emergency_contacts(self):
        """
            Show emergency contacts as well as standard contacts in Person Contacts page
        """
        return self.pr.get("show_emergency_contacts", True)

    def get_pr_contacts_tabs(self):
        """
            Which tabs to show for contacts: all, public &/or private
        """
        return self.pr.get("contacts_tabs", ("all",))

    # -------------------------------------------------------------------------
    # Proc
    #
    def get_proc_form_name(self):
        return self.proc.get("form_name", "Purchase Order")

    def get_proc_shortname(self):
        return self.proc.get("form_name", "PO")

    # -------------------------------------------------------------------------
    # Projects
    #
    def get_project_mode_3w(self):
        """
            Enable 3W mode in the projects module
        """
        return self.project.get("mode_3w", False)

    def get_project_mode_task(self):
        """
            Enable Tasks mode in the projects module
        """
        return self.project.get("mode_task", False)

    def get_project_mode_drr(self):
        """
            Enable DRR extensions in the projects module
        """
        return self.project.get("mode_drr", False)

    def get_project_activities(self):
        """
            Use Activities in Projects & Tasks
        """
        return self.project.get("activities", False)

    def get_project_activity_types(self):
        """
            Use Activity Types in Activities & Projects
        """
        return self.project.get("activity_types", False)

    def get_project_codes(self):
        """
            Use Codes in Projects
        """
        return self.project.get("codes", False)

    def get_project_community(self):
        """
            Label project_location as 'Community'
        """
        return self.project.get("community", False)

    def get_project_hazards(self):
        """
            Use Hazards in 3W Projects
        """
        return self.project.get("hazards", False)

    #def get_project_locations_from_countries(self):
    #    """
    #        Create a project_location for each country that a Project is
    #        implemented in
    #    """
    #    return self.project.get("locations_from_countries", False)

    def get_project_milestones(self):
        """
            Use Milestones in Projects & Tasks
        """
        return self.project.get("milestones", False)

    def get_project_task_tag(self):
        """
            Use Tags in Tasks
        """
        return self.project.get("task_tag", False)

    def get_project_projects(self):
        """
            Link Activities & Tasks to Projects
        """
        return self.project.get("projects", False)

    def get_project_sectors(self):
        """
            Use Sectors in Projects
        """
        return self.project.get("sectors", True)

    def get_project_themes(self):
        """
            Use Themes in 3W Projects
        """
        return self.project.get("themes", False)

    def get_project_theme_percentages(self):
        """
            Use Theme Percentages in Projects
        """
        return self.project.get("theme_percentages", False)

    def get_project_multiple_budgets(self):
        """
            Use Multiple Budgets in Projects
        """
        return self.project.get("multiple_budgets", False)

    def get_project_multiple_organisations(self):
        """
            Use Multiple Organisations in Projects
        """
        return self.project.get("multiple_organisations", False)

    def get_project_organisation_roles(self):
        T = current.T
        return self.project.get("organisation_roles", {
                1: T("Lead Implementer"), # T("Host National Society")
                2: T("Partner"),          # T("Partner National Society")
                3: T("Donor"),
                #4: T("Customer"), # T("Beneficiary")?
                #5: T("Supplier")  # T("Beneficiary")?
            })

    def get_project_organisation_lead_role(self):
        return self.project.get("organisation_lead_role", 1)

    def get_project_task_status_opts(self):
        """
            The list of options for the Status of a Task.
            NB Whilst the list can be customised, doing so makes it harder to
            do synchronization.
            There are also hard-coded elements within XSL & styling of
            project_task_list_layout which will break if these are changed.
            Best bet is simply to comment statuses that you don't wish to use
            & tweak the label (whilst keeping the meaning) of those you retain
            Those which are deemed as 'active' are currently not customisable
            for this reason.
        """
        T = current.T
        return self.project.get("task_status_opts", {1: T("Draft"),
                                                     2: T("New"),
                                                     3: T("Assigned"),
                                                     4: T("Feedback"),
                                                     5: T("Blocked"),
                                                     6: T("On Hold"),
                                                     7: T("Cancelled"),
                                                     8: T("Duplicate"),
                                                     9: T("Ready"),
                                                    10: T("Verified"),
                                                    11: T("Reopened"),
                                                    12: T("Completed"),
                                                    })

    def get_project_task_priority_opts(self):
        """
            The list of options for the Priority of a Task.
            NB Whilst the list can be customised, doing so makes it harder to
            do synchronization.
            There are also hard-coded elements within XSL & styling of
            project_task_list_layout which will break if these are changed.
            Best bet is simply to comment statuses that you don't wish to use
            & tweak the label (whilst keeping the meaning) of those you retain
        """
        T = current.T
        return self.project.get("task_priority_opts", {1: T("Urgent"),
                                                       2: T("High"),
                                                       3: T("Normal"),
                                                       4: T("Low")
                                                       })

    # -------------------------------------------------------------------------
    # Requests Management Settings
    #
    def get_req_req_type(self):
        """
            The Types of Request which can be made.
            Select one or more from:
            * People
            * Stock
            * Other
            tbc: Assets, Shelter, Food
        """
        return self.req.get("req_type", ["Stock", "People", "Other"])

    def get_req_type_inv_label(self):
        return current.T(self.req.get("type_inv_label", "Warehouse Stock"))

    def get_req_type_hrm_label(self):
        return current.T(self.req.get("type_hrm_label", "People"))

    def get_req_requester_label(self):
        return current.T(self.req.get("requester_label", "Requester"))

    def get_req_requester_optional(self):
        return self.req.get("requester_optional", False)

    def get_req_requester_is_author(self):
        """
            Whether the User Account logging the Request is normally the Requester
        """
        return self.req.get("requester_is_author", True)

    def get_req_requester_from_site(self):
        """
            Whether the Requester has to be a staff of the site making the Request
        """
        return self.req.get("requester_from_site", False)

    def get_req_requester_to_site(self):
        """
            Whether to set the Requester as being an HR for the Site if no HR record yet & as Site contact if none yet exists
        """
        return self.req.get("requester_to_site", False)

    def get_req_date_writable(self):
        """ Whether Request Date should be manually editable """
        return self.req.get("date_writable", True)

    def get_req_status_writable(self):
        """ Whether Request Status should be manually editable """
        return self.req.get("status_writable", True)

    def get_req_item_quantities_writable(self):
        """ Whether Item Quantities should be manually editable """
        return self.req.get("item_quantities_writable", False)

    def get_req_skill_quantities_writable(self):
        """ Whether People Quantities should be manually editable """
        return self.req.get("skill_quantities_writable", False)

    def get_req_multiple_req_items(self):
        """
            Can a Request have multiple line items?
            - e.g. ICS says that each request should be just for items of a single Type
        """
        return self.req.get("multiple_req_items", True)

    def get_req_show_quantity_transit(self):
        return self.req.get("show_quantity_transit", True)

    def get_req_inline_forms(self):
        """
            Whether Requests module should use inline forms for Items
        """
        return self.req.get("inline_forms", True)

    def get_req_prompt_match(self):
        """
            Whether a Requester is prompted to match each line item in an Item request
        """
        return self.req.get("prompt_match", True)

    def get_req_summary(self):
        """
            Whether to use Summary Needs for Sites (Office/Facility currently):
        """
        return self.req.get("summary", False)

    def get_req_use_commit(self):
        """
            Whether there is a Commit step in Requests Management
        """
        return self.req.get("use_commit", True)

    def get_req_commit_value(self):
        """
            Whether Donations should have a Value field
        """
        return self.req.get("commit_value", False)

    def get_req_commit_without_request(self):
        """
            Whether to allow Donations to be made without a matching Request
        """
        return self.req.get("commit_without_request", False)

    def get_req_committer_is_author(self):
        """ Whether the User Account logging the Commitment is normally the Committer """
        return self.req.get("committer_is_author", True)

    def get_req_ask_security(self):
        """
            Should Requests ask whether Security is required?
        """
        return self.req.get("ask_security", False)

    def get_req_ask_transport(self):
        """
            Should Requests ask whether Transportation is required?
        """
        return self.req.get("ask_transport", False)

    def get_req_items_ask_purpose(self):
        """
            Should Requests for Items ask for Purpose?
        """
        return self.req.get("items_ask_purpose", True)

    def get_req_req_crud_strings(self, type = None):
        return self.req.get("req_crud_strings") and \
               self.req.req_crud_strings.get(type, None)

    def get_req_use_req_number(self):
        return self.req.get("use_req_number", True)

    def get_req_generate_req_number(self):
        return self.req.get("generate_req_number", True)

    def get_req_form_name(self):
        return self.req.get("req_form_name", "Requisition Form")

    def get_req_shortname(self):
        return self.req.get("req_shortname", "REQ")

    def get_req_restrict_on_complete(self):
        """
            To restrict adding new commits to the Completed commits.
        """
        return self.req.get("req_restrict_on_complete", False)

    # -------------------------------------------------------------------------
    # Supply
    #
    def get_supply_catalog_default(self):
        return self.inv.get("catalog_default", "Default")

    def get_supply_use_alt_name(self):
        return self.supply.get("use_alt_name", True)

    # -------------------------------------------------------------------------
    # Vulnerability
    #
    def get_vulnerability_indicator_hierarchical(self):
        return self.vulnerability.get("indicator_hierarchical", False)

    # -------------------------------------------------------------------------
    # Transport
    #
    def get_transport_airport_code_unique(self):
        """
            Whether Airport code is unique
        """
        return self.transport.get("airport_code_unique", False)

    def get_transport_heliport_code_unique(self):
        """
            Whether Heliport code is unique
        """
        return self.transport.get("heliport_code_unique", False)

    def get_transport_seaport_code_unique(self):
        """
            Whether Seaport code is unique
        """
        return self.transport.get("seaport_code_unique", False)

    # -------------------------------------------------------------------------
    # Frontpage Options
    #
    def get_frontpage(self, key=None, default=None):
        """
            Template-specific frontpage configuration options
        """

        if key:
            return self.frontpage.get(key, default)
        else:
            return default

    # -------------------------------------------------------------------------
    # Utilities
    #
    def resolve_profile(self, options, setting, resolved=None):
        """
            Resolve option profile (e.g. prepopulate)

            @param options: the template options as dict like:
                            {"name": ("item1", "item2",...),...},
                            The "mandatory" list will always be
                            added, while the "default" list will
                            be added only if setting is None.
            @param setting: the active setting, as single item
                            or tuple/list, items with a "template:"
                            prefix (like "template:name") refer to
                            the respective list in options
            @param resolved: internal (for recursion)

            @example:

                # Template provides:
                settings.base.prepopulate_options = {
                    "mandatory": "locations/intl",
                    "brazil": "locations/brazil",
                    "germany": "locations/germany",
                    "default": "default",
                    "demo": ("template:default", "demo/users"),
                }

                # Set up a demo for Brazil:
                settings.base.prepopulate = ("template:brazil", "template:demo")
                # result:
                ["locations/intl", "locations/brazil", "default", "demo/users"]

                # Set up a production instance for Germany:
                settings.base.prepopulate = ("template:germany", "template:default")
                # result:
                ["locations/intl", "locations/germany", "default"]

                # Default setup:
                settings.base.prepopulate = None
                # result:
                ["locations/intl", "default"]

                # Custom options:
                settings.base.prepopulate = ["template:demo", "IFRC/Train"]
                # result:
                ["locations/intl", "default", "demo/users", "IFRC/Train"]

            @note: the result list is deduplicated, maintaining the original
                   order by first occurrence
        """

        default = resolved is None
        if default:
            resolved = set()
        seen = resolved.add

        result = []

        def append(item):
            if item not in resolved:
                seen(item)
                if isinstance(item, basestring) and item[:9] == "template:":
                    if options:
                        option = options.get(item[9:])
                        if option:
                            result.extend(self.resolve_profile(options,
                                                               option,
                                                               resolved=resolved))
                else:
                    result.append(item)
            return

        if default:
            append("template:mandatory")
        if setting is not None:
            if not isinstance(setting, (tuple, list)):
                setting = (setting,)
            for item in setting:
                append(item)
        elif default:
            append("template:default")
        return result

# END =========================================================================
