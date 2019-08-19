# -*- coding: utf-8 -*-

""" Deployment Settings

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: 2009-2019 (c) Sahana Software Foundation
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

from collections import OrderedDict

from gluon import current, URL
from gluon.storage import Storage

from s3compat import basestring, INTEGER_TYPES
from s3theme import FORMSTYLES

class S3Config(Storage):
    """
        Deployment Settings Helper Class
    """

    # Formats from static/scripts/ui/i18n converted to Python style
    date_formats = {"af": "%d/%m/%Y",
                    "ar": "%d/%m/%Y",
                    "ar-dz": "%d/%m/%Y",
                    "az": "%d.%m.%Y",
                    "be": "%d.%m.%Y",
                    "bg": "%d.%m.%Y",
                    "bs": "%d.%m.%Y",
                    "ca": "%d/%m/%Y",
                    "cs": "%d.%m.%Y",
                    "cy-gb": "%d/%m/%Y",
                    "da": "%d-%m-%Y",
                    "de": "%d.%m.%Y",
                    #"dv": "",
                    "el": "%d/%m/%Y",
                    "eo": "%d/%m/%Y",
                    "es": "%d/%m/%Y",
                    "et": "%d.%m.%Y",
                    "eu": "%Y-%m-%d",
                    "fa": "%Y/%m/%d",
                    "fi": "%d.%m.%Y",
                    "fo": "%d-%m-%Y",
                    "fr": "%d/%m/%Y",
                    "fr-ca": "%Y-%m-%d",
                    "fr-ch": "%d.%m.%Y",
                    "gl": "%d/%m/%Y",
                    "he": "%d/%m/%Y",
                    "hi": "%d/%m/%Y",
                    "hr": "%d.%m.%Y",
                    "hu": "%Y.%m.%d.",
                    "hy": "%d.%m.%Y",
                    "id": "%d/%m/%Y",
                    "is": "%d.%m.%Y",
                    "it": "%d/%m/%Y",
                    "ja": "%Y/%m/%d",
                    "ka": "%d-%m-%Y",
                    "kk": "%d.%m.%Y",
                    "km": "%d-%m-%Y",
                    "ko": "%Y-%m-%d",
                    "ky": "%d.%m.%Y",
                    "lb": "%d.%m.%Y",
                    "lt": "%Y-%m-%d",
                    "lv": "%d.%m.%Y",
                    "mk": "%d.%m.%Y",
                    "ml": "%d/%m/%Y",
                    #"mn": "",
                    "ms": "%d/%m/%Y",
                    #"my": "",
                    "nb": "%d.%m.%Y",
                    "ne": "%d/%m/%Y",
                    "nl": "%d-%m-%Y",
                    "nl-be": "%d/%m/%Y",
                    "nn": "%d.%m.%Y",
                    "no": "%d.%m.%Y",
                    "pl": "%d.%m.%Y",
                    "prs": "%Y/%m/%d",
                    "ps": "%Y/%m/%d",
                    "pt": "%d/%m/%Y",
                    "pt-br": "%d/%m/%Y",
                    "rm": "%d/%m/%Y",
                    "ro": "%d.%m.%Y",
                    "ru": "%d.%m.%Y",
                    #"si": "",
                    "sk": "%d.%m.%Y",
                    "sl": "%d.%m.%Y",
                    "sq": "%d.%m.%Y",
                    "sr": "%d.%m.%Y",
                    "sr-sr": "%d.%m.%Y",
                    "sv": "%Y-%m-%d",
                    "ta": "%d/%m/%Y",
                    #"tet": "",
                    "th": "%d/%m/%Y",
                    "tj": "%d.%m.%Y",
                    #"tl": "",
                    "tr": "%d.%m.%Y",
                    "uk": "%d.%m.%Y",
                    #"ur": "",
                    "vi": "%d/%m/%Y",
                    "zh-cn": "%Y-%m-%d",
                    "zh-hk": "%Y-%m-%d",
                    "zh-tw": "%Y/%m/%d",
                    }

    # PDF fonts for each language
    # fontset format -> [normal-version, bold-version]
    # defaults to ["Helvetica", "Helvetica-Bold"] if not-specified here
    # Requires installation of appropriate font - e.g. using import_font in tasks.cfg
    # Unifont can be downloaded from http://unifoundry.com/pub/unifont-7.0.06/font-builds/unifont-7.0.06.ttf
    fonts = {"ar": ["unifont", "unifont"],
             #"dv": ["unifont", "unifont"],
             #"dz": ["unifont", "unifont"],
             "km": ["unifont", "unifont"],
             "ko": ["unifont", "unifont"],
             "mn": ["unifont", "unifont"],
             "my": ["unifont", "unifont"],
             "ne": ["unifont", "unifont"],
             "prs": ["unifont", "unifont"],
             "ps": ["unifont", "unifont"],
             #"th": ["unifont", "unifont"],
             "tr": ["unifont", "unifont"],
             "vi": ["unifont", "unifont"],
             "zh-cn": ["unifont", "unifont"],
             "zh-tw": ["unifont", "unifont"],
             }

    def __init__(self):

        super(S3Config, self).__init__()

        self.asset = Storage()
        self.auth = Storage()
        self.auth.email_domains = []
        self.base = Storage()
        # Allow templates to append rather than replace
        self.base.prepopulate = ["default/base"]
        self.base.prepopulate_demo = ["default/users"]
        self.br = Storage()
        self.cap = Storage()
        self.cms = Storage()
        self.cr = Storage()
        self.database = Storage()
        self.dc = Storage()
        self.deploy = Storage()
        self.doc = Storage()
        self.dvr = Storage()
        self.edu = Storage()
        self.event = Storage()
        self.fin = Storage()
        # Allow templates to append rather than replace
        self.fin.currencies = {}
        self.fire = Storage()
        # @ToDo: Move to self.ui
        self.frontpage = Storage()
        self.frontpage.rss = []
        self.gis = Storage()
        # Allow templates to append rather than replace
        self.gis.countries = []
        self.hms = Storage()
        self.hrm = Storage()
        self.inv = Storage()
        self.irs = Storage()
        self.L10n = Storage()
        # Allow templates to append rather than replace
        self.L10n.languages = {"en": "English"}
        self.log = Storage()
        self.mail = Storage()
        self.member = Storage()
        self.mobile = Storage()
        self.msg = Storage()
        self.org = Storage()
        self.police = Storage()
        self.pr = Storage()
        self.proc = Storage()
        self.project = Storage()
        self.req = Storage()
        self.search = Storage()
        self.security = Storage()
        self.setup = Storage()
        # Allow templates to append rather than replace
        self.setup.wizard_questions = []
        self.supply = Storage()
        self.sync = Storage()
        self.tasks = Storage()
        self.transport = Storage()
        self.ui = Storage()
        self.vulnerability = Storage()
        self.xforms = Storage()

        # Lazy property
        self._db_params = None

        self._debug = None
        self._lazy_unwrapped = []

        # Provide a minimal list of core modules
        self.modules = {"default": Storage(name_nice = "Home",
                                           ),      # Default
                        "admin": Storage(name_nice = "Administration",
                                         ),        # Admin
                        "gis": Storage(name_nice = "Map",
                                       ),          # GIS
                        "pr": Storage(),           # Person Registry
                        "org": Storage(name_nice = "Organizations",
                                       ),          # Organization Registry
                        }

    # -------------------------------------------------------------------------
    @property
    def db_params(self):
        """
            Current database parameters, with defaults applied (lazy property)

            returns: a dict with database parameters:
                     {type, host, port, database, username, password}
        """

        parameters = self._db_params

        if parameters is None:

            db_type = self.get_database_type()

            get_param = self.database.get
            pool_size = get_param("pool_size", 30)

            if db_type == "sqlite":
                parameters = {}
            else:
                if db_type == "postgres":
                    default_port = "5432"
                elif db_type == "mysql":
                    default_port = "3306"
                else:
                    default_port = None

                parameters = {"host": get_param("host", "localhost"),
                              "port": get_param("port", default_port),
                              "database": get_param("database", "sahana"),
                              "username": get_param("username", "sahana"),
                              "password": get_param("password", "password"),
                              "pool_size": pool_size,
                              }

            parameters["type"] = db_type

            self._db_params = parameters

        return parameters

    # -------------------------------------------------------------------------
    # Debug
    def check_debug(self):
        """
            (Lazy) check debug mode and activate the respective settings
        """

        debug = self._debug
        base_debug = bool(self.get_base_debug())

        # Modify settings only if self.base.debug has changed
        if debug is None or debug != base_debug:
            self._debug = base_debug
            debug = base_debug or \
                    current.request.get_vars.get("debug", False)
            from gluon.custom_import import track_changes
            s3 = current.response.s3
            if debug:
                s3.debug = True
                track_changes(True)
            else:
                s3.debug = False
                track_changes(False)

    # -------------------------------------------------------------------------
    # Template
    def get_template(self):
        """
            Which deployment template to use for config.py, layouts.py, menus.py
            http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Templates
        """
        return self.base.get("template", "default")

    def import_template(self, config="config"):
        """
            Import and invoke the template config (new module pattern). Allows
            to specify multiple templates like:

                settings.template = ("default", "locations.US")

            Configurations will be imported and executed in order of appearance

            @param config: name of the config-module
        """

        names = self.get_template()
        if not isinstance(names, (list, tuple)):
            names = [names]

        for name in names:
            package = "templates.%s" % name

            self.check_debug()

            template = None
            try:
                # Import the template
                template = getattr(__import__(package, fromlist=[config]), config)
            except ImportError:
                raise RuntimeError("Template not found: %s" % name)
            else:
                template.config(self)

        return self

    # -------------------------------------------------------------------------
    # Theme
    #
    def set_theme(self):
        """
            Inspect base.theme_* settings and cache paths in response.s3
            accordingly (this needs to be run only once, getters will then
            use cached paths)

            @returns: the theme name
        """

        s3 = current.response.s3

        path_to = "/".join
        default = self.base.get("theme", "default")

        theme = default.split(".")
        theme_path = path_to(theme)

        # The theme name
        s3.theme = theme_name = theme[-1]

        # Path under modules/templates/ for layouts (views, e.g. layout.html)
        layouts = self.base.get("theme_layouts")
        if layouts:
            s3.theme_layouts = path_to(layouts.split("."))
        else:
            s3.theme_layouts = theme_path

        # Path under static/themes/ for eden.min.css
        styles = self.base.get("theme_styles")
        if styles:
            s3.theme_styles = path_to(styles.split("."))
        else:
            s3.theme_styles = theme_path

        # Path under modules/templates/ for css.cfg
        config = self.base.get("theme_config")
        if config:
            s3.theme_config = path_to(config.split("."))
        else:
            s3.theme_config = s3.theme_styles

        # Path under static/themes/ for base styles (e.g. foundation/*.css)
        base = self.base.get("theme_base")
        if base:
            s3.theme_base = path_to(base.split("."))
        else:
            s3.theme_base = s3.theme_styles

        return theme_name

    def get_theme(self):
        """
            The location of the current theme, relative to modules/templates
            and static/themes, respectively. Uses "." as path separator, e.g.:

                settings.base.theme = "SAMBRO.AlertHub"

            This is the default location of theme components, which can be
            individually adjusted with theme_layouts, theme_styles and
            theme_base settings if required.
        """
        theme = current.response.s3.theme
        if not theme:
            theme = self.set_theme()
        return theme

    def get_theme_layouts(self):
        """
            The location of the layouts for the current theme:
            - modules/templates/[theme_layouts]/layouts.py
            - modules/templates/[theme_layouts]/views

            => defaults to theme
        """
        layouts = current.response.s3.theme_layouts
        if not layouts:
            self.set_theme()
            layouts = current.response.s3.theme_layouts
        return layouts

    def get_theme_styles(self):
        """
            The location of the theme styles:
            - static/themes/[theme_styles]/eden.min.css

            => defaults to theme
        """
        styles = current.response.s3.theme_styles
        if not styles:
            self.set_theme()
            styles = current.response.s3.theme_styles
        return styles

    def get_theme_config(self):
        """
            The location of the theme CSS config:
            - modules/templates/[theme_config]/css.cfg

            => defaults to theme_styles
        """
        config = current.response.s3.theme_config
        if not config:
            self.set_theme()
            config = current.response.s3.theme_config
        return config

    def get_theme_base(self):
        """
            The location of the theme base styles (Foundation):
            - static/themes/[theme_base]/foundation

            => defaults to theme_styles
        """
        base = current.response.s3.theme_base
        if not base:
            self.set_theme()
            base = current.response.s3.theme_base
        return base

    def get_base_xtheme(self):
        """
            Whether there is a custom Ext theme or simply use the default xtheme-gray
            - specified as <themefolder>/xtheme-<filename>.css
        """
        return self.base.get("xtheme")

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

    def customise_home(self, module, alt_function):
        """
            Allow use of a Customised module Home page
            Fallback to cms_index if not configured
            Fallback to an alt_function if defined in the controller
        """
        customise = self.get("customise_%s_home" % module)
        if customise:
            return customise()
        else:
            return current.s3db.cms_index(module, alt_function=alt_function)

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
            Whether a Module is enabled in the current template
        """
        return module_name in self.modules

    # -------------------------------------------------------------------------
    def get_google_analytics_tracking_id(self):
        """
            Google Analytics Key
        """
        return self.base.get("google_analytics_tracking_id")

    # -------------------------------------------------------------------------
    def get_youtube_id(self):
        """
            List of YouTube IDs for the /default/video page
        """
        return self.base.get("youtube_id", [])

    # -------------------------------------------------------------------------
    def is_cd_version(self):
        """
            Whether we're running from a non-writable CD
        """
        return self.base.get("cd_version", False)

    # -------------------------------------------------------------------------
    # Tasks
    # -------------------------------------------------------------------------
    def get_task(self, taskname):
        """
            Ability to define custom Tasks in the Template
        """
        return self.tasks.get(taskname)

    # -------------------------------------------------------------------------
    # Authentication settings
    def get_auth_hmac_key(self):
        """
            salt to encrypt passwords - normally randomised during 1st run
        """
        return self.auth.get("hmac_key", "akeytochange")

    def get_auth_password_changes(self):
        """
            Are password changes allowed?
            - set to False if passwords are being managed externally (OpenID / SMTP / LDAP)
        """
        return self.auth.get("password_changes", True)

    def get_auth_password_retrieval(self):
        """
            Allow password retrieval?
        """
        return self.__lazy("auth", "password_retrieval", default=True)

    def get_auth_password_min_length(self):
        """
            To set the Minimum Password Length
        """
        return self.auth.get("password_min_length", int(4))

    def get_auth_gmail_domains(self):
        """ List of domains which can use GMail SMTP for Authentication """
        return self.auth.get("gmail_domains", [])

    def get_auth_office365_domains(self):
        """ List of domains which can use Office 365 SMTP for Authentication """
        return self.auth.get("office365_domains", [])

    def get_auth_google(self):
        """
            Read the Google OAuth settings
            - if configured, then it is assumed that Google Authentication
              is enabled
        """
        auth_get = self.auth.get

        client_id = auth_get("google_id", False)
        client_secret = auth_get("google_secret", False)

        if client_id and client_secret:
            return {"id": client_id, "secret": client_secret}
        else:
            return False

    def get_auth_humanitarian_id(self):
        """
            Read the Humanitarian.ID OAuth settings
            - if configured, then it is assumed that Humanitarian.ID
              Authentication is enabled
        """
        auth_get = self.auth.get

        client_id = auth_get("humanitarian_id_client_id", False)
        client_secret = auth_get("humanitarian_id_client_secret", False)

        if client_id and client_secret:
            return {"id": client_id, "secret": client_secret}
        else:
            return False

    def get_auth_openid(self):
        """ Use OpenID for Authentication """
        return self.auth.get("openid", False)

    def get_auth_openid_connect(self):
        """
            Use an OpenID Connect authentication service
                - must be configured with a dict like:
                    {"auth_url": authURL,
                     "token_url": tokenURL,
                     "userinfo_url": userinfoURL,
                     "id": clientID,
                     "secret": clientSecret,
                     }
        """
        required = ("auth_url", "token_url", "userinfo_url", "id", "secret")

        setting = self.auth.get("openid_connect")
        if setting and all(setting.get(k) for k in required):
            return setting
        else:
            return None

    def get_auth_masterkey(self):
        """
            Allow authentication with master key (= a single key instead of
            username+password)
        """
        return self.auth.get("masterkey", False)

    def get_auth_masterkey_app_key(self):
        """
            App key for clients using master key authentication
            - a string (recommended length 32 chars, random pattern)
            - specific for the deployment (i.e. not template)
            - should be configured in 000_config.py (alongside hmac_key)
        """
        return self.auth.get("masterkey_app_key")

    def get_auth_masterkey_token_ttl(self):
        """
            The time-to-live for master key auth tokens in seconds
            - tokens must survive two request cycles incl. prep, so
              TTL shouldn't be too short with slow network/server
            - should be short enough to prevent unused tokens from
              lingering
        """
        return self.auth.get("masterkey_token_ttl", 600)

    def get_auth_masterkey_context(self):
        """
            Getter for master key context information
            - a JSON-serializable dict with context data, or
            - a function that takes a master key (Row) and returns such a dict

            NB the getter should not expose the master key itself
               in the context dict!
        """
        return self.auth.get("masterkey_context")

    def get_security_self_registration(self):
        """
            Whether Users can register themselves
            - False to disable self-registration
            - True to use the default registration page at default/user/register
            - "index" to use a cyustom registration page defined in private/templates/<template>/controllers.py

        """
        return self.security.get("self_registration", True)

    def get_security_registration_visible(self):
        visible = self.get_security_self_registration() and \
                  self.security.get("registration_visible", True)
        return visible

    def get_security_version_info(self):
        """
            Whether to show version info on the about page
        """
        return self.security.get("version_info", True)

    def get_security_version_info_requires_login(self):
        """
            Whether the version info on the About page requires login
        """
        return self.security.get("version_info_requires_login", False)

    def get_auth_registration_requires_verification(self):
        return self.auth.get("registration_requires_verification", False)

    def get_auth_registration_requires_approval(self):
        return self.auth.get("registration_requires_approval", False)

    def get_auth_registration_welcome_email(self):
        """
            Send a welcome-email to newly registered users
        """
        return self.auth.get("registration_welcome_email", True)

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
            * staff
            * volunteer
            * member
        """
        return self.auth.get("registration_link_user_to")

    def get_auth_registration_link_user_to_default(self):
        """
            Link User accounts to none or more of:
            * staff
            * volunteer
            * member
            Should be an iterable.
        """
        return self.auth.get("registration_link_user_to_default")

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

    def get_auth_registration_organisation_link_create(self):
        """ Show a link to create new orgs in registration form """
        return self.auth.get("registration_organisation_link_create", True)

    def get_auth_registration_organisation_hidden(self):
        " Hide the Organisation field in the registration form unless an email is entered which isn't whitelisted "
        return self.auth.get("registration_organisation_hidden", False)

    def get_auth_registration_organisation_default(self):
        " Default the Organisation during registration - will return the organisation_id"
        organisation_id = self.__lazy("auth", "registration_organisation_default", default=None)
        if organisation_id:
            try:
                int(organisation_id)
            except (ValueError, TypeError):
                # Must be a Name
                table = current.s3db.org_organisation
                row = current.db(table.name == organisation_id).select(table.id,
                                                                       ).first()
                if row:
                    organisation_id = row.id
                else:
                    organisation_id = table.insert(name = organisation_id)
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
        message = self.auth.get("registration_pending")
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
        message = self.auth.get("registration_pending_approval")
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
            A dictionary of realms, with lists of role UUIDs, to assign to
            newly-registered users
            Use key = 0 to have the roles not restricted to a realm
        """
        return self.auth.get("registration_roles", [])

    def get_auth_org_admin_to_first(self):
        """
            Whether the first user to register for an Org should get the
            ORG_ADMIN role for that Org
        """
        return self.auth.get("org_admin_to_first", False)

    def get_auth_terms_of_service(self):
        """
            Force users to accept Terms of Service before Registering an account
            - uses <template>/views/tos.html
        """
        return self.auth.get("terms_of_service", False)

    def get_auth_consent_tracking(self):
        """ Expose options to track user consent """
        return self.auth.get("consent_tracking", False)

    def get_auth_registration_volunteer(self):
        """ Redirect the newly-registered user to their volunteer details page """
        return self.auth.get("registration_volunteer", False)

    def get_auth_record_approval(self):
        """ Use record approval (False by default) """
        return self.auth.get("record_approval", False)

    def get_auth_record_approval_required_for(self):
        """ Which tables record approval is required for """
        return self.auth.get("record_approval_required_for", [])

    def get_auth_record_approval_manual(self):
        """ Which tables record approval is not automatic for """
        return self.auth.get("record_approval_manual", [])

    def get_auth_realm_entity_types(self):
        """ Which entity types to use as realm entities in role manager """

        default = ("org_group",
                   "org_organisation",
                   "org_office",
                   "inv_warehouse",
                   "pr_group",
                   )
        return self.__lazy("auth", "realm_entity_types", default=default)

    def get_auth_realm_entity(self):
        """ Hook to determine the owner entity of a record """
        return self.auth.get("realm_entity")

    def get_auth_person_realm_human_resource_site_then_org(self):
        """
            Should we set pr_person.realm_entity to that of
            hrm_human_resource.site_id$pe_id
            or
            hrm_human_resource.organisation_id$pe_id if 1st not set
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
    def get_system_name(self):
        """
            System Name - for the UI & Messaging
        """
        return self.base.get("system_name", current.T("Sahana Eden Humanitarian Management Platform"))
    def get_system_name_short(self):
        """
            System Name (Short Version) - for the UI & Messaging
        """
        return self.base.get("system_name_short", "Sahana")

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
        return self.base.get("prepopulate", 1)

    def get_base_prepopulate_demo(self):
        """For demo sites, which additional options to add to the list """
        return self.base.get("prepopulate_demo", 0)

    def get_base_guided_tour(self):
        """ Whether the guided tours are enabled """
        return self.base.get("guided_tour", False)

    def get_base_public_url(self):
        """
            The Public URL for the site - for use in email links, etc
        """
        public_url = self.base.get("public_url")
        if not public_url:
            env = current.request.env
            scheme = env.get("wsgi_url_scheme", "http").lower()
            host = env.get("http_host") or "127.0.0.1:8000"
            self.base.public_url = public_url = "%s://%s" % (scheme, host)
        return public_url

    def get_base_bigtable(self):
        """
            Prefer scalability-optimized over small-table-optimized
            strategies (where alternatives exist)
            - resource/feature-specific overrides possible
      """
        return self.base.get("bigtable", False)

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

        db_string = "%(type)s://%(user)s:%(pass)s@%(host)s:%(port)s/%(name)s"

        chat_server = self.base.get("chat_server", False)
        csget = chat_server.get
        dbget = self.database.get

        db_type = chat_server.get("server_db_type")
        if db_type == "mysql":
            default_port = 3306
        elif db_type == "postgres":
            default_port = 5432
        else:
            from gluon import HTTP
            raise HTTP(501, body="Database type '%s' not recognised - please correct file models/000_config.py." % db_type)

        db_params = {
            "type": db_type,
            "user": csget("server_db_username") or dbget("username", "sahana"),
            "pass": csget("server_db_password") or dbget("password", "password"),
            "host": csget("server_db_ip") or dbget("host", "localhost"),
            "port": csget("server_db_port") or dbget("port", default_port),
            "name": csget("server_db") or dbget("database", "openfiredb"),
        }
        return db_string % db_params

    def get_base_session_db(self):
        """
            Should we store sessions in the database to avoid locking sessions on long-running requests?
        """
        # @ToDo: Set this as the default when running MySQL/PostgreSQL after more testing
        result = self.base.get("session_db", False)
        if result:
            db_type = self.get_database_type()
            if db_type == "sqlite":
                # Never store the sessions in the DB if running SQLite
                result = False
        return result

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

        return None

    # -------------------------------------------------------------------------
    # Logger settings
    def get_log_level(self):
        """
            Minimum severity level for logger: "DEBUG", "INFO", "WARNING",
            "ERROR", "CRITICAL". None = turn off logging
        """
        return "DEBUG" if self.base.get("debug") \
                       else self.log.get("level")

    def get_log_console(self):
        """
            True to enable console logging (sys.stderr)
        """
        return self.log.get("console", True)

    def get_log_logfile(self):
        """
            Log file name, None to turn off log file output
        """
        return self.log.get("logfile")

    def get_log_caller_info(self):
        """
            True to enable detailed caller info in log (filename,
            line number, function name), useful for diagnostics
        """
        return self.log.get("caller_info", False)

    # -------------------------------------------------------------------------
    # Database settings
    #
    def get_database_type(self):
        """
            Get the database type
        """

        return self.database.get("db_type", "sqlite").lower()

    def get_database_string(self):
        """
            Database string and pool-size for PyDAL (models/00_db.py)

            @return: tuple (db_type, db_string, pool_size)
        """

        parameters = self.db_params
        db_type = parameters["type"]

        if db_type == "sqlite":
            db_string = "sqlite://storage.db"

        elif db_type in ("mysql", "postgres"):
            db_string = "%(type)s://%(username)s:%(password)s@%(host)s:%(port)s/%(database)s" % \
                       parameters

        else:
            from gluon import HTTP
            raise HTTP(501, body="Database type '%s' not recognised - please correct file models/000_config.py." % db_type)

        return (db_type, db_string, self.database.get("pool_size", 30))

    def get_database_airegex(self):
        """
            Whether to instead of LIKE use REGEXP with groups of diacritic
            alternatives of characters to enforce accent-insensitive matches
            in text search (for SQLite and PostgreSQL, neither of which
            applies collation rules in LIKE)

            @note: MySQL's REGEXP implementation is not multibyte-safe,
                   so AIRegex is ignored for MySQL.

            @note: However, MYSQL's LIKE applies collation rules, so
                   accent-insensitivity can be achieved by settings a
                   suitable default database collation with:
                     ALTER DATABASE <dbname> DEFAULT COLLATE <collname>
                   Caution: this will trigger a rebuilt of all indices, so
                            on a populated production database this could
                            take quite a long time (but is needed only once)!

            @note: SQLite fails on Windows Python 2.7.10 with current PyDAL
                   (PR coming for PyDAL)

            @note: AIRegex is much less scalable than normal LIKE or even
                   ILIKE, enable/disable on a case-by-case basis in case
                   of performance issues (which is also why this is a lazy
                   setting), or consider switching to MySQL altogether
        """
        if self.get_database_type() != "mysql":
            airegex = self.__lazy("database", "airegex", False)
        else:
            airegex = False
        return airegex

    # -------------------------------------------------------------------------
    # Finance settings
    def get_fin_currency_writable(self):
        """
            Can the user select a Currency?
        """
        return self.fin.get("currency_writable", True)

    def get_fin_currencies(self):
        """
            Which Currencies can the user select?
        """
        currencies = self.__lazy("fin", "currencies", {})
        if currencies == {}:
            currencies = {
                "EUR": "Euros",
                "GBP": "Great British Pounds",
                "USD": "United States Dollars",
            }
        return currencies

    def get_fin_currency_default(self):
        """
            What is the default Currency?
        """
        return self.__lazy("fin", "currency_default", default="USD")

    # -------------------------------------------------------------------------
    # GIS (Map) Settings
    #
    def get_gis_api_bing(self):
        """ API key for Bing """
        return self.gis.get("api_bing")

    def get_gis_api_google(self):
        """
            API key for Google Maps
        """
        return self.gis.get("api_google", "")

    def get_gis_bbox_min_size(self):
        """
            Minimum size for BBOX around Features on Map
            - so that there is always some Map around a Point

            Value is in degrees
        """
        return self.gis.get("bbox_min_size", 0.05)

    def get_gis_bbox_inset(self):
        """
            BBOX inset around Features on Map
            - so that ones on the edge don't get cut-off
        """
        return self.gis.get("bbox_inset", 0.007)

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
        return self.gis.get("cluster_fill")

    def get_gis_cluster_label(self):
        """
            Label Clustered points on Map?
        """
        return self.gis.get("cluster_label", True)

    def get_gis_cluster_stroke(self):
        """
            Stroke for Clustered points on Map, else default
        """
        return self.gis.get("cluster_stroke")

    def get_gis_select_fill(self):
        """
            Fill for Selected points on Map, else default
        """
        return self.gis.get("select_fill")

    def get_gis_select_stroke(self):
        """
            Stroke for Selected points on Map, else default
        """
        return self.gis.get("select_stroke")

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
        return self.gis.get("config_screenshot")

    def get_gis_countries(self):
        """
            Which ISO2 country codes should be accessible to the location selector?
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

    def get_gis_geocode_service(self):
        """
            Which Geocoder Service should be used?
            Supported options:
                "nominatim" (default)
                "google"
        """
        return self.gis.get("geocode_service", "nominatim")

    def get_gis_geocode_imported_addresses(self):
        """
            Should Addresses imported from CSV be passed to a
            Geocoder to try and automate Lat/Lon?
        """
        return self.gis.get("geocode_imported_addresses", False)

    def get_gis_ignore_geocode_errors(self):
        """
            Whether failure to geocode imported addresses shall
            lead to a validation error
        """
        return self.gis.get("ignore_geocode_errors", False)

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
        return self.gis.get("geonames_username")

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
        return self.gis.get("latlon_selector", False)

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

    def get_gis_location_filter_bigtable_lookups(self):
        """
            Location filter to use scalability-optimized option lookups
            - can be overridden by filter widget option (bigtable)
            - defaults to base.bigtable
        """
        setting = self.gis.get("location_filter_bigtable_lookups")
        return setting if setting is not None else self.get_base_bigtable()

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

    def get_gis_map_selector_height(self):
        """ Height of the map selector map """
        return self.gis.get("map_selector_height", 340)

    def get_gis_map_selector_width(self):
        """ Width of the map selector map """
        return self.gis.get("map_selector_width", 480)

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
        return self.__lazy("gis", "postcode_selector", default=True)

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
            - set to 0 to disable
        """
        return self.gis.get("simplify_tolerance", 0.01)

    def get_gis_precision(self):
        """
            Number of Decimal places to put in output
            Increase this to 5 for highly-zoomed maps showing buildings
        """
        return self.gis.get("precision", 4)

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

    def get_gis_popup_location_link(self):
        """
            Whether a Pop-up Window should open on clicking
            Location represent links
            - Default: Map opens in a div
        """
        return self.gis.get("popup_location_link", False)

    def get_gis_xml_wkt(self):
        """
            Whether XML exports should include the bulky WKT
        """
        return self.gis.get("xml_wkt", False)

    # -------------------------------------------------------------------------
    # L10N Settings
    def get_L10n_default_language(self):
        return self.L10n.get("default_language", "en")

    def get_L10n_display_toolbar(self):
        return self.L10n.get("display_toolbar", True)

    def get_L10n_extra_codes(self):
        """
            Extra codes for IS_ISO639_2_LANGUAGE_CODE
            e.g. CAP needs to add "en-US"
        """
        return self.L10n.get("extra_codes", None)

    def get_L10n_languages(self):
        return self.L10n.get("languages")

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

    def get_L10n_timezone(self):
        """
            The default timezone for datetime representation in the UI,
            fallback if the client timezone or UTC offset can not be
            determined (e.g. user not logged in, or not browser-based)

            * A list of available timezones can be retrieved with:

              import os, tarfile, dateutil.zoneinfo
              path = os.path.abspath(os.path.dirname(dateutil.zoneinfo.__file__))
              zonesfile = tarfile.TarFile.open(os.path.join(path, 'dateutil-zoneinfo.tar.gz'))
              zonenames = zonesfile.getnames()
        """
        return self.__lazy("L10n", "timezone")

    def get_L10n_firstDOW(self):
        """
            First day of the week (overrides calendar default)

            0 = Sunday, 1 = Monday, ..., 6 = Saturday

            None = use the calendar's default
        """
        return self.L10n.get("firstDOW", None)

    def get_L10n_calendar(self):
        """
            Which calendar to use (lazy setting)

            Currently supported calendars:
            - "Gregorian"
        """
        return self.__lazy("L10n", "calendar", None)

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
        return self.__lazy("L10n", "mandatory_lastname", False)

    def get_L10n_mandatory_middlename(self):
        """
            e.g. Apellido Paterno in Hispanic names

            Setting this means that auth_user.last_name matches with pr_person.middle_name
            e.g. RMSAmericas
        """
        return self.__lazy("L10n", "mandatory_middlename", False)

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

    def get_L10n_translate_org_organisation(self):
        """
            Whether to translate Organisation names/acronyms
        """
        return self.L10n.get("translate_org_organisation", False)

    def get_L10n_translate_org_site(self):
        """
            Whether to translate Site names
        """
        return self.L10n.get("translate_org_site", False)

    def get_L10n_translate_cap_area(self):
        """
            Whether to translate CAP Area names
        """
        return self.L10n.get("translate_cap_area", False)

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
    #
    def get_pdf_size(self):
        """
            PDF default page size
                * "A4"
                * "Letter"
                * or a tuple (width, height) in points (1 inch = 72 points)
                  => pre-defined tuples in reportlab.lib.pagesizes
        """
        return self.base.get("pdf_size", "A4")

    def get_pdf_orientation(self):
        """
            PDF default page orientation
                * Auto (Portrait if possible, Landscape for wide tables)
                * Portrait
                * Landscape
        """
        return self.base.get("pdf_orientation", "Auto")

    def get_pdf_bidi(self):
        """
            Enable BiDi support for PDF exports
                - without this RTL text will be LTR
                - default off to enhance performance
        """
        return self.__lazy("L10n", "pdf_bidi", False)

    def get_pdf_logo(self):
        return self.ui.get("pdf_logo")

    def get_pdf_export_font(self):
        language = current.session.s3.language
        return self.__lazy("L10n", "pdf_export_font", self.fonts.get(language))

    def get_pdf_excluded_fields(self, resourcename):
        """
            Optical Character Recognition (OCR)
        """

        excluded_fields = self.pdf.get("excluded_fields")
        if excluded_fields is None:
            excluded_fields = {"hms_hospital": ["hrm_human_resource",
                                                ],
                               "pr_group": ["pr_group_membership",
                                            ],
                               }

        return excluded_fields.get(resourcename, [])

    def get_pdf_max_rows(self):
        """
            Maximum number of records in a single PDF table/list export
                - None for unlimited
        """
        return self.base.get("pdf_max_rows", 1000)

    # -------------------------------------------------------------------------
    # XLS Export Settings
    #
    def get_xls_title_row(self):
        """
            Include a title row in XLS Exports
            - default=False to allow easy post-export column sorting
            - uses the "title_list" CRUD string + export date/time
            - standard title can be overridden in exporter call
        """
        return self.base.get("xls_title_row", False)

    # -------------------------------------------------------------------------
    # UI Settings
    #
    @classmethod
    def _get_formstyle(cls, setting):
        """ Helper function to identify a formstyle """

        if callable(setting):
            # A custom formstyle defined in the template
            formstyle = setting
        if setting in FORMSTYLES:
            # One of the standard supported formstyles
            formstyle = FORMSTYLES[setting]
        else:
            # A default web2py formstyle
            formstyle = setting
        return formstyle

    def get_ui_formstyle(self):
        """ Get the current form style """

        setting = self.ui.get("formstyle", "default")
        return self._get_formstyle(setting)

    def get_ui_formstyle_read(self):
        """ Get the current form style for read views """

        setting = self.ui.get("formstyle_read")
        if setting is not None:
            formstyle = self._get_formstyle(setting)
        else:
            # Fall back to default formstyle
            formstyle = self.get_ui_formstyle()
        return formstyle

    def get_ui_filter_formstyle(self):
        """ Get the current filter form style """

        setting = self.ui.get("filter_formstyle", "default_inline")
        return self._get_formstyle(setting)

    def get_ui_report_formstyle(self):
        """ Get the current report form style """

        setting = self.ui.get("report_formstyle")
        return self._get_formstyle(setting)

    def get_ui_inline_formstyle(self):
        """ Get the _inline formstyle for the current formstyle """

        setting = self.ui.get("formstyle", "default")

        if isinstance(setting, basestring):
            # Try to find the corresponding _inline formstyle
            inline_formstyle_name = "%s_inline" % setting
            formstyle = FORMSTYLES.get(inline_formstyle_name)
        else:
            formstyle = None

        if formstyle is None:
            # Fall back to default formstyle
            formstyle = self._get_formstyle(setting)

        return formstyle

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

        return self.ui.get("datatables_initComplete")

    def get_ui_datatables_pagingType(self):
        """
            The style of Paging used by dataTables:
            https://datatables.net/reference/option/pagingType
        """

        return self.ui.get("datatables_pagingType", "full_numbers")

    def get_ui_datatables_responsive(self):
        """ Make data tables responsive (auto-collapsing columns when too wide) """

        return self.ui.get("datatables_responsive", True)

    def get_ui_datatables_double_scroll(self):
        """ Render double scroll bars (top+bottom) for non-responsive data tables """

        return self.ui.get("datatables_double_scroll", False)

    def get_ui_auto_open_update(self):
        """
            Render "Open" action buttons in datatables without explicit
            CRUD-method => this allows automatic per-record decision
            whether to open as update- or read-form based on permissions,
            e.g. if the user doesn't have permission to update for all
            records in the datatable due to oACL or realm-restriction
        """
        return self.ui.get("auto_open_update", False)

    def get_ui_open_read_first(self):
        """
            Render "Open" action buttons with explicit "read" method
            irrespective permissions (i.e. always, even if the user
            were permitted to edit records)
        """
        return self.ui.get("open_read_first", False)

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
            - "font-awesome3"
        """
        return self.ui.get("icons", "font-awesome")

    def get_ui_custom_icons(self):
        """
            Custom icon CSS classes, a dict {abstract name: CSS class},
            can be used to partially override standard icons
        """
        return self.ui.get("custom_icons")

    def get_ui_icon_layout(self):
        """
            Callable to render icon HTML, which takes an ICON instance
            as parameter and returns valid XML as string
        """
        return self.ui.get("icon_layout")

    def get_ui_calendar_clear_icon(self):
        """
            Render clear-button for calendar inputs just as an icon
            (S3CalendarWidget, requires Foundation + font-awesome)
        """
        return self.ui.get("calendar_clear_icon", False)

    # -------------------------------------------------------------------------
    def get_ui_auto_keyvalue(self):
        """
            Should crud_form & list_fields automatically display all Keys in KeyValue tables?
            - can be set to False, True or a list of tablenames for which it is True
        """
        return self.ui.get("auto_keyvalue", False)

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
            - specify a list of export formats to restrict/override
            - each list item can be
              * a string with the format extension
              * a tuple (extension, css-class[, onhover-title])
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
            - set to None to disable
        """
        return self.ui.get("label_permalink", "Link to this result")

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
            - currently respected by Auth Registration & S3LocationSelector

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

    def get_ui_autocomplete_delay(self):
        """
            Time in milliseconds after the last keystroke in an AC field
            to start the search
        """
        return self.__lazy("ui", "autocomplete_delay", 800)

    def get_ui_autocomplete_min_chars(self):
        """
            Minimum charcters in an AC field to start the search
        """
        return self.__lazy("ui", "autocomplete_min_chars", 2)

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

    def get_ui_report_timeout(self):
        """
            Time in milliseconds to wait for a Report's AJAX call to complete
        """
        return self.ui.get("report_timeout", 10000)

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

    def get_ui_hierarchy_cascade_option_in_tree(self):
        """
            Whether hierarchy widgets show a "Select All" option in
            the tree (True) or as context menu of the parent node.
        """
        return self.ui.get("hierarchy_cascade_option_in_tree", True)

    def get_ui_hierarchy_filter_bulk_select_option(self):
        """
            Whether or not to show a bulk-select option in hierarchical
            filter widgets (overrides per-widget setting)
        """
        return self.ui.get("hierarchy_filter_bulk_select_option")

    def get_ui_location_filter_bulk_select_option(self):
        """
            Whether or not to show a bulk-select option in location
            filter widgets (overrides per-widget setting)
        """
        return self.__lazy("ui", "location_filter_bulk_select_option")

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

    def get_ui_inline_cancel_edit(self):
        """
            Behavior of inline components when switching edit rows
            without explicit submit/cancel: cancel|submit|ask|refuse
        """
        return self.ui.get("inline_cancel_edit", "ask")

    def get_ui_profile_header(self, r):
        """
            What Header should be shown in the Profile page
        """

        #profile_header = self.__lazy("ui", "profile_header", None)
        profile_header = self.ui.get("profile_header", None)
        if profile_header:
            profile_header = profile_header(r)
        else:
            # Default
            from gluon import DIV, H2, P
            try:
                title = r.record.name
            except AttributeError:
                title = r.record.id
            try:
                comments = r.record.comments or ""
            except AttributeError:
                comments = ""
            profile_header = DIV(H2(title),
                                 P(comments),
                                 _class="profile-header",
                                 )
        return profile_header

    def get_ui_menu_logo(self):
        """
            The menu logo for the default menu, can be:
                - a string representing an image URL (can use URL())
                - a T()
                - an HTML helper instance (e.g. DIV or SPAN)
                - None (to show system short name instead of a logo)

            NB to override the entire title area, use the template's
               menus.py and specify a title_area attribute for the
               main menu node
        """

        return self.__lazy("ui", "menu_logo",
                           URL(c = "static",
                               f = "img",
                               args = ["S3menu_logo.png"],
                               )
                           )

    def get_ui_organizer_business_hours(self):
        """
            Business hours to indicate in organizer,
            - a dict {dow:[0,1,2,3,4,5,6], start: "HH:MM", end: "HH:MM"},
            - or a list of such dicts
            - dow 0 being Sunday
            - False to disable
        """
        return self.__lazy("ui", "organizer_business_hours", False)

    def get_ui_organizer_time_format(self):
        """
            The time format for organizer (overrides locale default)
        """
        return self.__lazy("ui", "organizer_time_format", None)

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

    def get_msg_basestation_code_unique(self):
        """
            Validate for Unique Basestations Codes
        """
        return self.msg.get("basestation_code_unique", False)

    def get_msg_send_postprocess(self):
        """
            Custom function that processes messages after they have been sent, eg.
            link alert_id in cap module to message_id in message module
            The function can be of form msg_send_postprocess(message_id, **data),
            where message_id is the msg_message_id and
            **data is the additional arguments to pass to s3msg.send_by_pe_id
        """

        return self.msg.get("send_postprocess")

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
        return self.mail.get("sender")

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
        return self.mail.get("limit")

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
        return self.msg.get("notify_renderer")

    def get_msg_notify_attachment(self):
        """
            Custom function that returns the list of document_ids to be sent
            as attachment in email

            The function may be of the form:
            custom_msg_notify_attachment(resource, data, meta_data), where
            resource is the S3Resource, data: the data returned from
            S3Resource.select and meta_data: the meta data for the notification
            (see s3notify for the metadata)
        """

        return self.msg.get("notify_attachment")

    def get_msg_notify_send_data(self):
        """
            Custom function that returns additional arguments to pass to
            s3msg.send_by_pe_id

            The function should be of the form:
            custom_msg_notify_send_data(resource, data, meta_data), where
            resource is the S3Resource, data: the data returned from
            S3Resource.select and meta_data: the meta data for the notification
            (see s3notify for the metadata)
        """

        return self.msg.get("notify_send_data")

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
    #
    def get_search_max_results(self):
        """
            The maximum number of results to return in an Autocomplete Search
            - more than this will prompt the user to enter a more exact match
            Lower this number to get extra performance from an overloaded server.
        """
        return self.search.get("max_results", 200)

    def get_search_dates_auto_range(self):
        """
            Date filters to apply introspective range limits (by
            looking up actual minimum/maximum dates from the records)

            NB has scalability problems, so disabled by default =>
               can be overridden per-widget using the "auto_range"
               option (S3DateFilter)
        """
        return self.search.get("dates_auto_range", False)

    # Filter Manager Widget
    def get_search_filter_manager(self):
        """ Enable the filter manager widget """
        return self.search.get("filter_manager", True)

    def get_search_filter_manager_allow_delete(self):
        """ Allow deletion of saved filters """
        return self.search.get("filter_manager_allow_delete", True)

    def get_search_filter_manager_save(self):
        """ Text for saved filter save-button """
        return self.search.get("filter_manager_save")

    def get_search_filter_manager_update(self):
        """ Text for saved filter update-button """
        return self.search.get("filter_manager_update")

    def get_search_filter_manager_delete(self):
        """ Text for saved filter delete-button """
        return self.search.get("filter_manager_delete")

    def get_search_filter_manager_load(self):
        """ Text for saved filter load-button """
        return self.search.get("filter_manager_load")

    # =========================================================================
    # Setup
    #
    def get_setup_monitor_template(self):
        """
            Which template folder to use to load monitor.py
        """
        return self.setup.get("monitor_template", "default")

    def get_setup_wizard_questions(self):
        """
            Configuration options to see in the Setup Wizard
        """
        return self.setup.get("wizard_questions", [])

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

    def get_sync_upload_filename(self):
        """
            Filename for upload via FTP Sync

            Available placeholders:
                $S = System Name (long)
                $s = System Name (short)
                $r = Resource Name
            Use {} to separate the placeholder from immediately following
            identifier characters (like: ${placeholder}text).
        """
        return self.sync.get("upload_filename", "$s $r")

    def get_sync_data_repository(self):
        """ This deployment is a public data repository """

        return self.sync.get("data_repository", False)

    # =========================================================================
    # Modules

    # -------------------------------------------------------------------------
    # Asset: Asset Management
    #
    def get_asset_telephones(self):
        """
            Whether Assets should include a specific type for Telephones
        """
        return self.asset.get("telephones", False)

    # -------------------------------------------------------------------------
    # BR: Beneficiary Registry
    #
    def get_br_case_terminology(self):
        """
            Terminology to use when referring to cases: Beneficiary|Client|Case
        """
        return self.br.get("case_terminology", "Case")

    def get_br_assistance_terminology(self):
        """
            Terminology to use when referring to measures of assistance: Counseling|Assistance
        """
        return self.br.get("assistance_terminology", "Assistance")

    def get_br_needs_hierarchical(self):
        """
            Need categories are hierarchical
        """
        return self.br.get("needs_hierarchical", False)

    def get_br_needs_org_specific(self):
        """
            Need categories are specific per root organisation
        """
        return self.br.get("needs_org_specific", True)

    def get_br_id_card_layout(self):
        """
            Layout class for beneficiary ID cards
        """
        return self.br.get("id_card_layout")

    def get_br_id_card_export_roles(self):
        """
            User roles permitted to export beneficiary ID cards
        """
        return self.br.get("id_card_export_roles")

    def get_br_case_hide_default_org(self):
        """
            Hide the organisation field in cases if only one allowed
        """
        return self.br.get("case_hide_default_org", True)

    def get_br_case_manager(self):
        """
            Assign cases to individual case managers (staff members)
        """
        return self.br.get("case_manager", True)

    def get_br_case_address(self):
        """
            Document the current address of beneficiaries
        """
        return self.br.get("case_address", False)

    def get_br_case_language_details(self):
        """
            Document languages that can be used when communicating with
            a beneficiary
        """
        return self.br.get("case_language_details", True)

    def get_br_household_size(self):
        """
            Track the number of persons per household (family)

            - False = off
            - True = manual
            - "auto" = count family members automatically
        """
        return self.br.get("household_size", "auto")

    def get_br_case_contacts_tab(self):
        """
            Case file use tab to track beneficiary contact information
        """
        return self.br.get("case_contacts_tab", True)

    def get_br_case_id_tab(self):
        """
            Case file use tab to track identity documents
        """
        return self.br.get("case_id_tab", False)

    def get_br_case_family_tab(self):
        """
            Case file use tab to track family members
        """
        return self.br.get("case_family_tab", True)

    def get_br_service_contacts(self):
        """
            Enable case file tab to track service contacts
        """
        return self.br.get("service_contacts", False)

    def get_br_case_notes_tab(self):
        """
            Use a simple notes journal in case files
        """
        return self.br.get("case_notes_tab", False)

    def get_br_case_photos_tab(self):
        """
            Case file use tab to upload photos

            NB image-component can also be reached by clicking on the
               profile photo (or the placeholder, respectively)
        """
        return self.br.get("case_photos_tab", False)

    def get_br_case_documents_tab(self):
        """
            Case file use tab to upload documents
        """
        return self.br.get("case_documents_tab", True)

    def get_br_case_include_activity_docs(self):
        """
            Documents-tab of case files includes activity attachments
        """
        return self.get_br_case_activity_documents() and \
               self.br.get("case_include_activity_docs", True)

    def get_br_case_include_group_docs(self):
        """
            Documents-tab of case files includes case group attachments
        """
        return self.br.get("case_include_group_docs", True)

    def get_br_case_activities(self):
        """
            Track case activities
        """
        return self.br.get("case_activities", True)

    def get_br_case_activity_manager(self):
        """
            Assign case activities to individual staff members
        """
        return self.br.get("case_activity_manager", True)

    def get_br_case_activity_urgent_option(self):
        """
            Expose features for urgent case activities ("emergencies")
        """
        return self.br.get("case_activity_urgent_option", False)

    def get_br_case_activity_need(self):
        """
            Use need categories for case activities
        """
        return self.br.get("case_activity_need", True)

    def get_br_case_activity_subject(self):
        """
            Have a subject line (title) for case activities
        """
        return self.br.get("case_activity_subject", False)

    def get_br_case_activity_need_details(self):
        """
            Have a text field to document need details in case activities
        """
        return self.br.get("case_activity_need_details", False)

    def get_br_case_activity_status(self):
        """
            Case activities have a status (and possibly an end date)
        """
        return self.br.get("case_activity_status", True)

    def get_br_case_activity_end_date(self):
        """
            Show case activity end date in form
            - True to show, "writable" to allow manual edit
        """
        return self.br.get("case_activity_end_date", False)

    def get_br_case_activity_updates(self):
        """
            Use case activity update journal (inline-component)
        """
        return self.br.get("case_activity_updates", False)

    def get_br_case_activity_outcome(self):
        """
            Show field to track outcomes of case activities (free-text)
        """
        return self.br.get("case_activity_outcome", True)

    def get_br_case_activity_documents(self):
        """
            Case activities have attachments
        """
        return self.br.get("case_activity_documents", False)

    def get_br_manage_assistance(self):
        """
            Track individual measures of assistance
        """
        return self.br.get("manage_assistance", True)

    def get_br_assistance_inline(self):
        """
            Document assistance measures inline in activities
        """
        return self.br.get("assistance_inline", True)

    def get_br_assistance_tab(self):
        """
            Document assistance measures on separate case file tab
        """
        setting = self.br.get("assistance_tab")
        if setting is None:
            # Show the tab if managing assistance without activities
            setting = self.get_br_manage_assistance() and \
                      not self.get_br_case_activities()
        return setting

    def get_br_assistance_manager(self):
        """
            Assign assistance measures to individual staff members
        """
        return self.br.get("assistance_manager", True)

    def get_br_assistance_types(self):
        """
            Use assistance type categories
        """
        return self.br.get("assistance_types", True)

    def get_br_assistance_themes(self):
        """
            Use assistance theme categories
        """
        return self.br.get("assistance_themes", False)

    def get_br_assistance_themes_org_specific(self):
        """
            Assistance themes are specific per root organisation
        """
        return self.br.get("assistance_themes_org_specific", True)

    def get_br_assistance_themes_sectors(self):
        """
            Assistance themes are organized by org sector
        """
        return self.br.get("assistance_themes_sectors", False)

    def get_br_assistance_themes_needs(self):
        """
            Assistance themes are linked to needs
        """
        return self.br.get("assistance_themes_needs", False)

    def get_br_assistance_measures_use_time(self):
        """
            Assistance measures use date+time (instead of just date)
        """
        return self.br.get("assistance_measures_use_time", False)

    def get_br_assistance_measure_default_closed(self):
        """
            Set default status of assistance measures to closed
            (useful if the primary use-case is post-action documentation)
        """
        return self.br.get("assistance_measure_default_closed", False)

    def get_br_assistance_details_per_theme(self):
        """
            Document assistance measure details per theme
            - requires assistance tab
        """
        return self.get_br_assistance_tab() and \
               self.br.get("assistance_details_per_theme", False)

    def get_br_assistance_activity_autolink(self):
        """
            Auto-link assistance details to case activities
            - requires case_activity_need
            - requires assistance_themes and assistance_themes_needs
            - requires assistance_tab and assistance_details_per_theme
        """
        return self.br.get("assistance_activity_autolink", False)

    def get_br_assistance_track_effort(self):
        """
            Track effort (=hours spent) for assistance measures
        """
        return self.br.get("assistance_track_effort", True)

    # -------------------------------------------------------------------------
    # CAP: Common Alerting Protocol
    #
    def get_cap_identifier_oid(self):
        """
            OID for the CAP issuing authority
        """

        # See if the User has an Org-specific OID
        auth = current.auth
        if auth.user and auth.user.organisation_id:
            table = current.s3db.org_organisation_tag
            query = ((table.organisation_id == auth.user.organisation_id) & \
                     (table.tag == "cap_oid"))
            record = current.db(query).select(table.value,
                                              limitby=(0, 1)
                                              ).first()
            if record and record.value:
                return record.value

        # Else fallback to the default OID
        return self.cap.get("identifier_oid", "")

    def get_cap_info_effective_period(self):
        """
            The period (in days) after which alert info segments expire
        """
        return self.cap.get("info_effective_period", 2)

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

        return self.cap.get("languages", OrderedDict([("ar", "Arabic"),
                                                      ("en-US", "English"),
                                                      ("es", "Spanish"),
                                                      ("fr", "French"),
                                                      ("pt", "Portuguese"),
                                                      ("ru", "Russian"),
                                                      ]))

    def get_cap_authorisation(self):
        """
            Authorisation setting whether to display "Submit for Approval" Button
        """

        return self.cap.get("authorisation", True)

    def get_cap_restrict_fields(self):
        """
            Whether to restrict fields for update, cancel or error of alerts
        """

        return self.cap.get("restrict_fields", False)

    def get_cap_post_to_twitter(self):
        """
            Whether to post the alerts in twitter
            @ToDo: enhance this by as well as True,
            being able to specify a specific Twitter channel to tweet on
        """

        return self.cap.get("post_to_twitter", False)

    def get_cap_same_code(self):
        """
            Name of the tag that will be used to lookup in the gis_location_tag
            to extract location_id for the alert
        """

        return self.cap.get("same_code")

    def get_cap_post_to_facebook(self):
        """
            Whether to post the alerts in facebook
        """

        return self.cap.get("post_to_facebook", False)

    def get_cap_rss_use_links(self):
        """
            Whether to use links of entry element if link fail
        """
        return self.cap.get("rss_use_links", False)

    def get_cap_use_ack(self):
        """
            Whether CAP Alerts have workflow for Acknowledgement
        """
        return self.cap.get("use_ack", False)

    def get_cap_alert_hub_title(self):
        """
            Title for the Alert Hub Page
        """

        return self.cap.get("alert_hub_title", current.T("SAMBRO Alert Hub Common Operating Picture"))

    def get_cap_area_default(self):
        """
            During importing from XML, which element(s) to use for the
            record in cap_area_location table
            elements are <polygon> and <geocode>
        """

        return self.cap.get("area_default", ["geocode", "polygon"])

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
        return self.cms.get("organisation_group")

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

    def get_cms_show_attachments(self):
        """
            Whether to show Attachments (such as Sources) in News Feed
        """
        return self.cms.get("show_attachments", True)

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

    def get_cms_hide_index(self, module):
        """
            Whether to hide CMS from module index pages, can be configured
            either as boolean, or as dict per module (with "_default" to
            define the default behavior).
        """

        hide = self.cms.get("hide_index", {})
        if isinstance(hide, dict):
            for m in (module, "_default"):
                if m in hide:
                    return hide[m]
            return False
        else:
            return hide

    # -------------------------------------------------------------------------
    # Shelters
    #
    def get_cr_day_and_night(self):
        """
            Whether Shelter Capacities/Registrations are different for Day and Night
        """
        return self.cr.get("day_and_night", False)

    def get_cr_shelter_people_registration(self):
        """
            Enable functionality to track individuals in shelters
        """
        return self.cr.get("people_registration", True)

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
        if not self.get_cr_shelter_people_registration():
            # Only relevant when using people registration
            return False
        return self.cr.get("shelter_population_dynamic", False)

    def get_cr_shelter_housing_unit_management(self):
        """
            Enable the use of tab "Housing Unit" and enable the housing unit
            selection during client registration.
        """
        return self.cr.get("shelter_housing_unit_management", False)

    def get_cr_check_out_is_final(self):
        """
            Whether checking out of a Shelter frees up the place or is just leaving the site temporarily
        """
        return self.cr.get("check_out_is_final", True)

    def get_cr_tags(self):
        """
            Whether Shelters should show a Tags tab
        """
        return self.cr.get("tags", False)

    def get_cr_shelter_inspection_tasks(self):
        """
            Generate tasks from shelter inspections (requires project module)
        """
        if self.has_module("project"):
            return self.cr.get("shelter_inspection_tasks", False)
        else:
            return False

    def get_cr_shelter_inspection_task_active_statuses(self):
        """
            List of active statuses of shelter inspection tasks
            (subset of project_task_status_opts)
        """
        default = (1, 2, 3, 4, 5, 6, 11)
        return self.cr.get("shelter_inspection_tasks_active_statuses", default)

    def get_cr_shelter_inspection_task_completed_status(self):
        """
            Completed-status for shelter inspection tasks (one value
            of project_task_status_opts), will be set when inspection
            flag is marked as resolved
        """
        return self.cr.get("shelter_inspection_tasks_completed_status", 12)

    # -------------------------------------------------------------------------
    # DC: Data Collection
    #
    def get_dc_response_label(self):
        """
            Label for Responses
            - 'Assessment;
            - 'Response' (default if set to None)
            - 'Survey'
        """
        return self.dc.get("response_label", "Assessment")

    def get_dc_unique_question_names_per_template(self):
        """
            Deduplicate Questions by Name/Template
             - needed for importing multiple translations
        """
        return self.dc.get("unique_question_names_per_template", False)

    def get_dc_mobile_data(self):
        """
            Whether Mobile Clients should download Assessments (Data not just Forms)
            - e.g. when these are created through Targetting
        """
        return self.dc.get("mobile_data", False)

    def get_dc_mobile_inserts(self):
        """
            Whether Mobile Clients should create Assessments locally
        """
        return self.dc.get("mobile_inserts", True)

    def get_dc_sections_hierarchical(self):
        """
            Whether Assessments have nested Sections
        """
        return self.dc.get("sections_hierarchical", False)

    # -------------------------------------------------------------------------
    # Deployments
    #
    def get_deploy_alerts(self):
        """
            Whether the system is used to send Alerts
        """
        return self.__lazy("deploy", "alerts", default=True)

    def get_deploy_cc_groups(self):
        """
            List of Group names that are cc'd on Alerts
        """
        return self.__lazy("deploy", "cc_groups", default=[])

    def get_deploy_hr_label(self):
        """
            Label for deployable Human Resources
            e.g. 'Staff', 'Volunteer' (CERT), 'Member' (RDRT)
        """
        return self.deploy.get("hr_label", "Staff")

    def get_deploy_manual_recipients(self):
        """
            Whether Alert recipients should be selected manually
        """
        return self.deploy.get("manual_recipients", True)

    def get_deploy_member_filters(self):
        """
            Custom set of filter_widgets for members (hrm_human_resource),
            used in custom methods for member selection, e.g. deploy_apply
            or deploy_alert_select_recipients
        """
        return self.__lazy("deploy", "member_filters", default=None)

    def get_deploy_post_to_twitter(self):
        """
            Whether to post the alerts in twitter
            @ToDo: enhance this by as well as True,
            being able to specify a specific Twitter channel to tweet on
        """

        return self.deploy.get("post_to_twitter", False)

    def get_deploy_responses_via_web(self):
        """
            Whether Responses to Alerts come in via the Web
        """

        return self.deploy.get("responses_via_web", True)

    def get_deploy_select_ratings(self):
        """
            Whether to have filters for Ratings when selecting deployables for an Alert
        """
        return self.deploy.get("select_ratings", False)

    def get_deploy_team_label(self):
        """
            Label for deployable Team
            e.g. 'RDRT', 'RIT'
        """
        return self.deploy.get("team_label", "Deployable")

    # -------------------------------------------------------------------------
    # Doc Options
    #
    def get_doc_label(self):
        """
            label for Document/Attachment
        """
        return self.doc.get("label", "Document")

    def get_doc_mailmerge_fields(self):
        """
            Dictionary of mailmerge fields
            - assumes starting from pr_person
        """
        return self.doc.get("mailmerge_fields", {"First Name": "first_name",
                                                 "Last Name": "last_name",
                                                 "Date of Birth": "date_of_birth",
                                                 })

    # -------------------------------------------------------------------------
    # DVR Options
    #
    def get_dvr_label(self):
        """
            Whether Cases are called Cases or Beneficiaries
            - default: None = Case
            - valid options: "Beneficiary"
        """
        return self.dvr.get("label", None)

    def get_dvr_case_flags(self):
        """
            Enable features to manage case flags
        """
        return self.dvr.get("case_flags", False)

    def get_dvr_track_transfer_sites(self):
        """
            Enable features to track transfer origin/destination sites
        """
        return self.dvr.get("track_transfer_sites", False)

    def get_dvr_transfer_site_types(self):
        """
            Site types for case transfer origin/destination
        """
        default = ("cr_shelter",
                   "org_office",
                   "org_facility",
                   )
        return self.dvr.get("transfer_site_types", default)

    def get_dvr_manage_transferability(self):
        """
            Enable features to manage transferability of cases
        """
        return self.dvr.get("manage_transferability", False)

    def get_dvr_household_size(self):
        """
            Register number of persons per household (family)

            False = off
            True = manual
            "auto" = count family members automatically
        """
        return self.dvr.get("household_size", False)

    def get_dvr_mandatory_appointments(self):
        """
            Expose flags to mark appointment types as mandatory
        """
        return self.dvr.get("mandatory_appointments", False)

    def get_dvr_case_events_close_appointments(self):
        """
            Whether case events automatically close appointments
        """
        return self.dvr.get("case_events_close_appointments", False)

    def get_dvr_appointments_update_last_seen_on(self):
        """
            Whether appointments which require presence shall
            automatically update the "last seen on" date when
            set to "completed"
        """
        return self.dvr.get("appointments_update_last_seen_on", False)

    def get_dvr_appointments_update_case_status(self):
        """
            Whether appointments automatically update the case
            status when set to "completed"
        """
        return self.dvr.get("appointments_update_case_status", False)

    def get_dvr_payments_update_last_seen_on(self):
        """
            Whether payments (e.g. allowance) shall automatically update
            the "last seen on" date when set to "paid"
        """
        return self.dvr.get("payments_update_last_seen_on", False)

    def get_dvr_id_code_pattern(self):
        """
            A regular expression pattern to parse ID Codes (QR codes),
            None to disable ID code parsing

            Should return the following groups:
                label                   the PE label, mandatory
                family                  the PE label of the head of family, optional
                first_name              optional
                last_name               optional
                date_of_birth           optional

            Example:
                "(?P<label>[^,]*),(?P<first_name>[^,]*),(?P<last_name>[^,]*),(?P<date_of_birth>[^,]*)"
        """
        return self.dvr.get("id_code_pattern", None)

    def get_dvr_event_registration_checkin_warning(self):
        """
            Warn during event registration when the person is currently
            not checked-in
        """
        return self.dvr.get("event_registration_checkin_warning", False)

    def get_dvr_event_registration_show_picture(self):
        """
            Event registration UI to show profile picture
            by default (True), or only on demand (False):
            - can be set to False (selectively) in order to improve
              responsiveness of the UI and reduce network traffic
        """
        return self.dvr.get("event_registration_show_picture", True)

    def get_dvr_event_registration_exclude_codes(self):
        """
            List of case event type codes to exclude from
            the event registration UI; can use * as wildcard

            Example:
                settings.dvr.event_registration_exclude_codes = ("FOOD*",)
        """
        return self.dvr.get("event_registration_exclude_codes", None)

    def get_dvr_activity_use_service_type(self):
        """
            Use service type in group/case activities
        """
        return self.dvr.get("activity_use_service_type", False)

    def get_dvr_activity_sectors(self):
        """
            Use sectors in group/case activities
        """
        return self.dvr.get("activity_sectors", False)

    def get_dvr_case_activity_use_status(self):
        """
            Use configurable statuses in case activities
            instead of simple completed-flag
        """
        return self.dvr.get("case_activity_use_status", False)

    def get_dvr_case_activity_needs_multiple(self):
        """
            Whether Case Activities link to Multiple Needs
            - e.g. DRK: False
            - e.g. STL: True
        """
        return self.dvr.get("case_activity_needs_multiple", False)

    def get_dvr_case_activity_follow_up(self):
        """
            Enable/disable fields to schedule case activities for follow-up
        """
        return self.__lazy("dvr", "case_activity_follow_up", default=True)

    def get_dvr_case_include_activity_docs(self):
        """
            Documents-tab of beneficiaries includes case activity attachments
        """
        return self.dvr.get("case_include_activity_docs", False)

    def get_dvr_case_include_group_docs(self):
        """
            Documents-tab of beneficiaries includes case group attachments
        """
        return self.dvr.get("case_include_group_docs", False)

    def get_dvr_needs_use_service_type(self):
        """
            Use service type in needs
        """
        return self.dvr.get("needs_use_service_type", False)

    def get_dvr_needs_hierarchical(self):
        """
            Need types are hierarchical
        """
        return self.dvr.get("needs_hierarchical", False)

    def get_dvr_vulnerability_types_hierarchical(self):
        """
            Vulnerability types are hierarchical
        """
        return self.dvr.get("vulnerability_types_hierarchical", False)

    def get_dvr_manage_response_actions(self):
        """
            Manage individual response actions in case activities
        """
        return self.dvr.get("manage_response_actions", False)

    def get_dvr_response_planning(self):
        """
            Response actions can be planned
            (as opposed to being documented in hindsight)
        """
        return self.__lazy("dvr", "response_planning", default=False)

    def get_dvr_response_due_date(self):
        """
            Response planning uses separate due-date field
        """
        return self.get_dvr_response_planning() and \
               self.__lazy("dvr", "response_due_date", default=False)

    def get_dvr_response_types(self):
        """
            Use response type categories
        """
        return self.__lazy("dvr", "response_types", default=True)

    def get_dvr_response_types_hierarchical(self):
        """
            Response types are hierarchical
        """
        return self.dvr.get("response_types_hierarchical", False)

    def get_dvr_response_themes(self):
        """
            Use themes for response actions
        """
        return self.dvr.get("response_themes", False)

    def get_dvr_response_themes_org_specific(self):
        """
            Response themes are org-specific
        """
        return self.dvr.get("response_themes_org_specific", True)

    def get_dvr_response_themes_sectors(self):
        """
            Response themes are organized per org sector
        """
        return self.__lazy("dvr", "response_themes_sectors", default=False)

    def get_dvr_response_themes_needs(self):
        """
            Response themes are linked to needs
        """
        return self.__lazy("dvr", "response_themes_needs", default=False)

    def get_dvr_response_themes_details(self):
        """
            Record response details per theme
        """
        return self.__lazy("dvr", "response_themes_details", default=False)

    def get_dvr_response_activity_autolink(self):
        """
            Automatically link response actions to case activities
            based on matching needs
        """
        return self.get_dvr_response_themes_needs() and \
               self.__lazy("dvr", "response_activity_autolink", default=False)

    # -------------------------------------------------------------------------
    # Education
    #
    def get_edu_school_code_unique(self):
        """
            Validate for Unique School Codes
        """
        return self.edu.get("school_code_unique", False)

    # -------------------------------------------------------------------------
    # Events
    #
    def get_event_label(self):
        """
            Whether Events are called Events or Disasters
            - default: None = Event
            - valid options: "Disaster"
        """
        return self.event.get("label", None)

    def get_event_incident(self):
        """
            Whether Events have Incidents
        """
        return self.event.get("incident", True)

    def get_event_cascade_delete_incidents(self):
        """
            Whether deleting an Event cascades to deleting all Incidents or whether it sets NULL
            - 'normal' workflow is where an Event is created and within that various Incidents,
              so cascading the delete makes sense here ("delete everything associated with this event")
            - WA COP uses Events to group existing Incidents, so here we don't wish to delete the Incidents if the Event is deleted

            NB Changing this setting requires a DB migration
        """
        return self.event.get("cascade_delete_incidents", True)

    def get_event_exercise(self):
        """
            Whether Events can be Exercises
        """
        return self.event.get("exercise", False)

    def get_event_sitrep_dynamic(self):
        """
            Whether the SitRep resource should include a Dynamic Table section
        """
        return self.event.get("sitrep_dynamic", False)

    def get_event_sitrep_edxl(self):
        """
            Whether the SitRep resource should be configured for EDXL-Sitrep mode
        """
        return self.event.get("sitrep_edxl", False)

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

    def get_event_task_notification(self):
        """
            Whether to send Notifications for Tasks linked to Events
            - only used in SaFiRe template currently

            Options: None, contact_method (e.g. "SMS", "EMAIL")
        """
        return self.event.get("task_notification", "EMAIL")

    def get_event_dc_response_tab(self):
        """
            Whether to show the DC response tab for events
        """
        return self.event.get("dc_response_tab", True)

    def get_event_dc_target_tab(self):
        """
            Whether to show the DC target tab for events
        """
        return self.event.get("dc_target_tab", True)

    def get_event_dispatch_tab(self):
        """
            Whether to show the dispatch tab for events
        """
        if self.has_module("msg"):
            return self.event.get("dispatch_tab", False)
        else:
            return False

    def get_event_impact_tab(self):
        """
            Whether to show the impact tab for events
        """
        return self.event.get("impact_tab", True)

    def get_incident_dispatch_tab(self):
        """
            Whether to show the dispatch tab for incidents
        """
        if self.has_module("msg"):
            return self.event.get("incident_dispatch_tab", True)
        else:
            return False

    def get_incident_impact_tab(self):
        """
            Whether to show the impact tab for incidents
        """
        return self.event.get("incident_impact_tab", False)

    def get_incident_teams_tab(self):
        """
            Show tab with teams assigned for incidents, string to
            define the label of the tab or True to use default label
        """
        return self.event.get("incident_teams_tab", False)

    # -------------------------------------------------------------------------
    # Fire
    #

    def get_fire_station_code_unique(self):
        """
            Whether Fire Station code is unique
        """
        return self.fire.get("fire_station_unique", False)

    # -------------------------------------------------------------------------
    # Hospital Registry
    #
    def get_hms_track_ctc(self):
        return self.hms.get("track_ctc", False)

    def get_hms_activity_reports(self):
        return self.hms.get("activity_reports", False)

    # -------------------------------------------------------------------------
    # Human Resource Management

    def get_hrm_course_grades(self):
        """
            Grade options for Courses
            NB Best to keep Pass/Fail on these numbers but can add additional values if-required, e.g.:
            {0: T("No Show"),
             1: T("Left Early"),
             8: T("Pass"),
             9: T("Fail"),
             }
        """
        T = current.T
        return self.__lazy("hrm", "course_grades", default={8: T("Pass"),
                                                            9: T("Fail"),
                                                            })

    def get_hrm_course_pass_marks(self):
        """
            Whether the Pass Mark for a course is defined by the Grade Details
        """
        return self.hrm.get("course_pass_marks", False)

    def get_hrm_course_types(self):
        """
            Which Types to use for Courses
            - allow all by default for prepop
        """
        T = current.T
        return self.__lazy("hrm", "course_types", default={1: T("Staff"),
                                                           2: T("Volunteers"),
                                                           3: T("Deployables"),
                                                           4: T("Members"),
                                                           })

    def get_hrm_event_course_mandatory(self):
        """
            Whether (Training) Events have a Mandatory Course
        """
        return self.__lazy("hrm", "event_course_mandatory", default=True)

    #def get_hrm_event_programme(self):
    #    """
    #        Whether (Training) Events should be linked to Programmes
    #    """
    #    return self.__lazy("hrm", "event_programme", default=False)

    def get_hrm_event_site(self):
        """
            How (Training) Events should be Located:
            - True: use Site
            - False: use Location (e.g. Country or Country/L1)
        """
        return self.__lazy("hrm", "event_site", default=True)

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

        label = self.hrm.get("organisation_label")
        if not label:
            if self.get_org_branches():
                label = "Organization / Branch"
            else:
                label = "Organization"
        return current.T(label)

    def get_hrm_root_organisation_label(self):
        """
            Label for Root Organisations in Human Resources
        """
        return current.T(self.hrm.get("root_organisation_label", "Top-level Organization"))

    def get_hrm_email_required(self):
        """
            If set to True then Staff & Volunteers require an email address
            NB Currently this also acts on Members & Beneficiaries!
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
                ("site_id", "person_id") - Use the HR's Site Location if-available, fallback to the Person's Home Address if-not
            NB This is read onaccept of editing Home Addresses & Assigning Volunteers to Sites so is not a fully-dynamic change
            - onaccept is used for performance (avoiding joins)
        """
        return self.hrm.get("location_vol", "person_id")

    def get_hrm_multiple_contracts(self):
        """
            Whether Staff have multiple contracts recorded
        """
        return self.__lazy("hrm", "multiple_contracts", default=False)

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

    def get_hrm_multiple_orgs(self):
        """
            True: Human Resources are being managed across multiple Organisations
            False: Human Resources are only being managed internally within a single Organisation with no Branches
        """
        return self.hrm.get("multiple_orgs", True)

    def get_hrm_compose_button(self):
        """
            If set to True then HRM dataTables have a 'Send Message' button
                if the messaging module is enabled & users have the permission to access hrm/compose
        """
        return self.hrm.get("compose_button", True)

    def get_hrm_deletable(self):
        """
            If set to True then HRM records are deletable rather than just being able to be marked as obsolete
        """
        return self.hrm.get("deletable", True)

    def get_hrm_event_types(self):
        """
            Whether (Training) Events should be of different Types
        """
        return self.__lazy("hrm", "event_types", default=False)

    def get_hrm_id_cards(self):
        """
            Show buttons to download printable ID cards for staff/volunteers
        """
        return self.__lazy("hrm", "id_cards", default=False)

    def get_hrm_job_title_deploy(self):
        """
            Whether the 'deploy' Job Title type should be used
        """
        job_title_deploy = self.hrm.get("job_title_deploy", None)
        if job_title_deploy is None:
            job_title_deploy = self.has_module("deploy")
        return job_title_deploy

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

    def get_hrm_mix_staff(self):
        """
            If set to True then Staff and Volunteers are shown together
        """
        return self.hrm.get("mix_staff", False)

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

    def get_hrm_staff_departments(self):
        """
            Whether Staff should use Departments
        """
        return self.__lazy("hrm", "staff_departments", default=True)

    def get_hrm_staff_experience(self):
        """
            Whether to use Experience for Staff &, if so, which table to use
            - options are: False, "experience", "missions", "both"
        """
        return self.hrm.get("staff_experience", "experience")

    def get_hrm_salary(self):
        """
            Whether to track salaries of staff
        """
        return self.hrm.get("salary", False)

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
        return self.__lazy("hrm", "teams", default="Teams")

    def get_hrm_teams_orgs(self):
        """
            Whether Human Resource Teams should link to Organisations
            & whether this is a Single Org or Multiple Orgs
            Options:
                None: disable link
                1:    single Org
                2:    multiple Orgs
        """
        return self.__lazy("hrm", "teams_orgs", default=1)

    def get_hrm_trainings_external(self):
        """
            Whether Training Courses should be split into Internal & External
        """
        return self.__lazy("hrm", "trainings_external", default=False)

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
            Whether or not to show the HR record as tab, and with which
            method:

                True = show the default tab (human_resource)
                "record" = consolidate tabs into 1x CV page:
                            * Staff Record
                            * Group Membership
                False = do not show the tab (e.g. when HR record is inline)
        """
        return self.hrm.get("record_tab", True)

    def get_hrm_record_label(self):
        """
            Label to use for the HR record tab
            - string not LazyT
        """
        label = self.__lazy("hrm", "record_label", default=None)
        if not label:
            if current.request.controller == "vol":
                label = "Volunteer Record"
            elif self.get_hrm_mix_staff():
                label = "Staff/Volunteer Record"
            else:
                label = "Staff Record"
        return label

    def get_hrm_use_awards(self):
        """
            Whether Volunteers should use Awards
        """
        return self.hrm.get("use_awards", True)

    def get_hrm_use_certificates(self):
        """
            Whether Human Resources should use Certificates
        """
        return self.__lazy("hrm", "use_certificates", default=True)

    def get_hrm_create_certificates_from_courses(self):
        """
            If set Truthy then Certificates are created automatically for each Course
                True: Create Certificates without an organisation_id
                "organisation_id": Create Certificates with the organisation_id of the Course
        """
        return self.hrm.get("create_certificates_from_courses", False)

    def get_hrm_filter_certificates(self):
        """
            If set to True then Certificates are filtered by (Root) Organisation
            & hence certificates from other Organisations cannot be added to an HR's profile (except by Admins)
        """
        return self.hrm.get("filter_certificates", False)

    def get_hrm_use_address(self):
        """
            Whether Human Resources should show address tab
        """
        use_address = self.hrm.get("use_address", None)

        # Fall back to PR setting if not specified
        if use_address is None:
            use_address = self.get_pr_use_address()

        return use_address

    def get_hrm_use_code(self):
        """
            Whether Human Resources should use Staff/Volunteer IDs,
            either True or False, or "staff" to use code for staff
            only
        """
        return self.__lazy("hrm", "use_code", default=False)

    def get_hrm_use_credentials(self):
        """
            Whether Human Resources should use Credentials
        """
        return self.hrm.get("use_credentials", True)

    def get_hrm_use_description(self):
        """
            Whether Human Resources should use Physical Description
            and what the name of the Tab should be.
            Set to None to disable
        """
        return self.hrm.get("use_description", "Description")

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

    def get_hrm_use_job_titles(self):
        """
            Whether Human Resources should show Job Titles
        """
        return self.hrm.get("use_job_titles", True)

    def get_hrm_use_national_id(self):
        """
            Whether Human Resources should show National IDs in list_fields
            & text_search_fields
            either True or False
        """
        return self.__lazy("hrm", "use_national_id", default=False)

    def get_hrm_use_skills(self):
        """
            Whether Human Resources should use Skills
        """
        return self.__lazy("hrm", "use_skills", default=True)

    def get_hrm_certificate_skill(self):
        """
            Whether Human Resources should use Skill Equivalence for Certificates
        """
        return self.__lazy("hrm", "certificate_skill", default=False)

    def get_hrm_use_trainings(self):
        """
            Whether Human Resources should use Trainings
        """
        return self.hrm.get("use_trainings", True)

    def get_hrm_training_instructors(self):
        """
            How training instructors are managed:
                None: Don't track instructors at all
                internal: Use persons from the registry
                external: Just use free-text Names
                both: Use both fields
                multiple: Use multiple persons from the registry
        """
        return self.__lazy("hrm", "training_instructors", "external")

    def get_hrm_training_filter_and(self):
        """
            How people are filtered based on their Trainings:
                False (default): Std options filter where we do an OR
                    - i.e. we see all people who have done either (or both) Course A or Course B
                True: Contains options filter (basically an AND)
                    - i.e. we see only people who have done both Course A and Course B
        """
        return self.__lazy("hrm", "training_filter_and", False)

    def get_hrm_activity_types(self):
        """
            HRM Activity Types (for experience record),
            a dict {"code": "label"}, None to deactivate (default)
        """
        return self.hrm.get("activity_types")

    def get_hrm_vol_active(self):
        """
            Whether to use a 'Active' field for Volunteers &, if so, whether
            this is set manually or calculated by a function
            - options are: False, True or a function

            NB If using a function, put this inside a Lazy lookup
        """
        return self.__lazy("hrm", "vol_active", default=False)

    def get_hrm_vol_active_tooltip(self):
        """
            The tooltip to show when viewing the Active status in the Volunteer RHeader
        """
        return self.hrm.get("vol_active_tooltip")

    #def get_hrm_vol_affiliation(self):
    #    """
    #        Which affiliation type Volunteers use:
    #            1 = Organisational Unit (=> Hierarchy)
    #            9 = 'Other Role'
    #            None = default ('Other Role')
    #    """
    #    return self.__lazy("hrm", "vol_affiliation", default=None)

    def get_hrm_vol_availability_tab(self):
        """
            Whether to use Availability Tab for Volunteers
            Options:
                None
                True
        """
        return self.__lazy("hrm", "vol_availability_tab", default=None)

    def get_hrm_vol_experience(self):
        """
            Whether to use Experience for Volunteers &, if so, which table to use
            - options are: False, "experience", "activity", "programme" or "both"
        """
        return self.__lazy("hrm", "vol_experience", default="programme")

    def get_hrm_vol_departments(self):
        """
            Whether Volunteers should use Departments
        """
        return self.__lazy("hrm", "vol_departments", default=False)

    def get_hrm_vol_roles(self):
        """
            Whether Volunteers should use Roles
        """
        return self.__lazy("hrm", "vol_roles", default=True)

    def get_hrm_vol_service_record_manager(self):
        """
            What should be put into the 'Manager' field of the Volunteer Service Record
        """
        return self.__lazy("hrm", "vol_service_record_manager",
                           default=current.T("Branch Coordinator"))

    # -------------------------------------------------------------------------
    # Inventory Management Settings
    #
    def get_inv_collapse_tabs(self):
        return self.inv.get("collapse_tabs", True)

    def get_inv_facility_label(self):
        return self.inv.get("facility_label", "Warehouse")

    def get_inv_facility_manage_staff(self):
        """
            Show Staff Management Tabs for Facilities in Inventory Module
        """
        return self.inv.get("facility_manage_staff", True)

    def get_inv_recv_tab_label(self):
        label = self.inv.get("recv_tab_label")
        if not label:
            if self.get_inv_shipment_name() == "order":
                label = "Orders"
            else:
                label = "Receive"
        return label

    def get_inv_send_tab_label(self):
        return self.inv.get("send_tab_label", "Send")

    def get_inv_direct_stock_edits(self):
        """
            Can Stock levels be adjusted directly?
            - defaults to False
        """
        return self.inv.get("direct_stock_edits", False)

    def get_inv_org_dependent_warehouse_types(self):
        """
            Whether Warehouse Types vary by Organisation
        """
        return self.inv.get("org_dependent_warehouse_types", False)

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
        return self.inv.get("item_status", {0: current.messages["NONE"], # Only Items with this Status can be allocated to shipments
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

    def get_inv_warehouse_code_unique(self):
        """
            Validate for Unique Warehouse Codes
        """
        return self.inv.get("warehouse_code_unique", False)

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

    def get_member_membership_types(self):
        """
            Whether to have Membership Types
        """
        return self.__lazy("member", "membership_types", default=True)


    # -------------------------------------------------------------------------
    # Mobile Forms
    #
    def get_mobile_forms(self):
        """
            Configure mobile forms - a list of items, or a callable returning
            a list of items.

            Item formats:
                "tablename"
                ("Title", "tablename")
                ("Title", "tablename", options)

            Format for options:
                {
                    name = name,         ...form name (optional)
                    c = controller,      ...use this controller for form handling
                    f = function,        ...use this function for form handling
                    vars = vars,         ...add these vars to the download URL
                 }

            Example:
                settings.mobile.forms = [("Request", "req_req")]
        """
        return self.__lazy("mobile", "forms", [])

    def get_mobile_dynamic_tables(self):
        """
            Expose mobile forms for dynamic tables
        """
        return self.mobile.get("dynamic_tables", True)

    def get_mobile_masterkey_filter(self):
        """
            Filter mobile forms by master key
        """
        return self.mobile.get("masterkey_filter", False)

    # -------------------------------------------------------------------------
    # Organisations
    #
    def get_org_autocomplete(self):
        """
            Whether organisation_id fields should use an Autocomplete instead of a dropdown
        """
        return self.org.get("autocomplete", False)

    def get_org_default_organisation(self):
        """
            If the system is only used by a single Organisation then this can be defaulted/hidden
            - if-appropriate can also use lazy settings to set this from the user.organisation_id
        """
        default_organisation = self.__lazy("org", "default_organisation", default=None)
        if default_organisation:
            if not isinstance(default_organisation, INTEGER_TYPES):
                # Check Session cache
                default_organisation_id = current.session.s3.default_organisation_id
                if default_organisation_id:
                    default_organisation = default_organisation_id
                else:
                    # Convert Name to ID
                    table = current.s3db.org_organisation
                    org = current.db(table.name == default_organisation).select(table.id,
                                                                                limitby=(0, 1),
                                                                                ).first()
                    try:
                        default_organisation = org.id
                    except AttributeError:
                        # Prepop not done?
                        current.log.error("Default Organisation not found: %s" % default_organisation)
                        default_organisation = None
                    else:
                        # Cache
                        current.session.s3.default_organisation_id = default_organisation
        return default_organisation

    def get_org_default_site(self):
        """
            If the system is only used by a single Site then this can be defaulted/hidden
            - if-appropriate can also use lazy settings to set this from the user.site_id
        """
        default_site = self.org.get("default_site", None)
        if default_site:
            if not isinstance(default_site, INTEGER_TYPES):
                # Check Session cache
                default_site_id = current.session.s3.default_site_id
                if default_site_id:
                    default_site = default_site_id
                else:
                    # Convert Name to ID
                    table = current.s3db.org_site
                    site = current.db(table.name == default_site).select(table.site_id,
                                                                        limitby=(0, 1),
                                                                        ).first()
                    try:
                        default_site = site.site_id
                    except AttributeError:
                        # Prepop not done?
                        current.log.error("Default Site not found: %s" % default_site)
                        default_site = None
                    else:
                        # Cache
                        current.session.s3.default_site_id = default_site
        return default_site

    def get_org_country(self):
        """
            Whether to expose the "country" field of organisations
        """
        return self.org.get("country", True)

    def get_org_sector(self):
        """
            Whether to use an Organization Sector field
        """
        return self.org.get("sector", False)

    def get_org_sector_rheader(self):
        """
            Whether Sectors should be visible in the rheader
        """
        return self.org.get("sector_rheader", self.get_org_sector())

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

    def get_org_organisation_type_rheader(self):
        """
            Whether Organisation Types are visible in the rheader
        """
        return self.org.get("organisation_type_rheader", False)

    def get_org_facilities_tab(self):
        """
            Whether to show a Tab for Facilities
        """
        return self.org.get("facilities_tab", True)

    def get_org_groups(self):
        """
            Whether to support Organisation Groups or not
            & what their name is:
            'Coalition'
            'Network'
        """
        return self.org.get("groups", False)

    def get_org_group_team_represent(self):
        """
            Whether to represent org_group affiliation in team
            references (pr_group_id)
        """
        return self.org.get("group_team_represent", False)

    def get_org_pdf_card_configs(self):
        """
            Show a tab in organisation rheader to manage PDF card configurations
        """
        return self.__lazy("org", "pdf_card_configs", default=False)

    def get_org_documents_tab(self):
        """
            Whether to show a Tab for Documents
        """
        return self.org.get("documents_tab", False)

    def get_org_needs_tab(self):
        """
            Whether to show a Tab for Organisation Needs
        """
        return self.org.get("needs_tab", False)

    def get_org_offices_tab(self):
        """
            Whether to show a Tab for Offices
        """
        return self.org.get("offices_tab", True)

    def get_org_projects_tab(self):
        """
            Whether to show a Tab for Projects
        """
        return self.org.get("projects_tab", True) # Will be hidden anyway if Projects module disabled

    def get_org_regions(self):
        """
            Whether to support Organisation Regions or not
        """
        return self.org.get("regions", False)

    def get_org_region_countries(self):
        """
            Whether Organisation Regions maintain a list of countries
        """
        return self.org.get("region_countries", False)

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

    def get_org_service_locations(self):
        """
            Whether to expose the service locations tab for organisations
        """
        return self.__lazy("org", "service_locations", default=False)

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

    def get_org_site_check(self):
        """
            Get custom tasks for scheduled site checks
        """
        return self.org.get("site_check")

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
        dependent_fields = self.org.get("dependent_fields")
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
            else:
                # Enable if empty list
                enabled = True

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

    def get_org_tags(self):
        """
            Whether Organisations, Offices & Facilities should show a Tags tab
        """
        return self.org.get("tags", False)

    # -------------------------------------------------------------------------
    # Police
    #

    def get_police_station_code_unique(self):
        """
            Whether Police Station code is unique
        """
        return self.police.get("police_station_unique", False)

    # -------------------------------------------------------------------------
    # Persons
    #
    def get_pr_age_group(self, age):
        """
            Function to provide the age group for an age
        """
        fn = self.pr.get("age_group")
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

    def get_pr_person_availability_options(self):
        """
            Dict of integer-keyed options for Person Availability
        """
        return self.__lazy("pr", "person_availability_options", default=None)

    def get_pr_hide_third_gender(self):
        """
            Whether to hide the third gender ("Other")
        """
        return self.__lazy("pr", "hide_third_gender", default=True)

    def get_pr_import_update_requires_email(self):
        """
            During imports, records are only updated if the import
            item contains a (matching) email address
        """
        return self.pr.get("import_update_requires_email", True)

    def get_pr_label_fullname(self):
        """
            Label for the AddPersonWidget2's 'Name' field
        """
        return self.__lazy("pr", "label_fullname", default="Name")

    def get_pr_lookup_duplicates(self):
        """
            Whether the AddPersonWidget2 does a fuzzy search for duplicates

            NB This setting has no effect with the old AddPersonWidget
        """
        return self.pr.get("lookup_duplicates", False)

    def get_pr_request_dob(self):
        """ Include Date of Birth in the AddPersonWidget[2] """
        return self.__lazy("pr", "request_dob", default=True)

    def get_pr_dob_required(self):
        """ Whether Date of Birth is Mandatory, including in the AddPersonWidget2 """
        return self.__lazy("pr", "dob_required", default=False)

    def get_pr_request_email(self):
        """ Include Email in the AddPersonWidget2 """
        return self.__lazy("pr", "request_email", default=True)

    def get_pr_request_father_name(self):
        """ Include Father Name in the AddPersonWidget2 """
        return self.__lazy("pr", "request_father_name", default=False)

    def get_pr_request_grandfather_name(self):
        """ Include GrandFather Name in the AddPersonWidget2 """
        return self.__lazy("pr", "request_grandfather_name", default=False)

    def get_pr_request_gender(self):
        """ Include Gender in the AddPersonWidget[2] """
        return self.__lazy("pr", "request_gender", default=True)

    def get_pr_request_home_phone(self):
        """ Include Home Phone in the AddPersonWidget2 """
        return self.__lazy("pr", "request_home_phone", default=False)

    def get_pr_request_mobile_phone(self):
        """ Include Mobile Phone in the AddPersonWidget2 """
        return self.__lazy("pr", "request_mobile_phone", default=True)

    def get_pr_request_year_of_birth(self):
        """ Include Year of Birth in the AddPersonWidget2 """
        return self.__lazy("pr", "request_year_of_birth", default=False)

    def get_pr_name_format(self):
        """
            Format with which to represent Person Names

            Generally want an option in AddPersonWidget2 to handle the input like this too
        """
        return self.__lazy("pr", "name_format", default="%(first_name)s %(middle_name)s %(last_name)s")

    def get_pr_search_shows_hr_details(self):
        """
            Whether S3PersonAutocompleteWidget results show the details of their HR record
        """
        return self.pr.get("search_shows_hr_details", True)

    def get_pr_select_existing(self):
        """
            Whether the AddPersonWidget allows selecting existing PRs
            - set to True if Persons can be found in multiple contexts
            - set to False if just a single context

            NB This setting has no effect with the new AddPersonWidget2
        """
        return self.pr.get("select_existing", True)

    def get_pr_separate_name_fields(self):
        """
            Whether the AddPersonWidget2 provides separate name fields or not
            Options:
                False (single field)
                2 (first/last)
                3 (first/middle/last)
        """
        return self.__lazy("pr", "separate_name_fields", False)

    def get_pr_use_address(self):
        """
            Whether or not to show an address tab in person details
        """
        return self.pr.get("use_address", True)

    def get_pr_show_emergency_contacts(self):
        """
            Show emergency contacts as well as standard contacts in Person Contacts page
        """
        return self.pr.get("show_emergency_contacts", True)

    def get_pr_contacts_tabs(self):
        """
            Which tabs to show for contacts: all, public &/or private
                - a tuple or list with all|private|public, or
                - a dict with labels per contacts group
                  (defaults see get_pr_contacts_tab_label)
        """
        contacts_tabs = self.pr.get("contacts_tabs", ("all",))
        if not contacts_tabs:
            return () # iterable expected
        return contacts_tabs

    def get_pr_contacts_tab_label(self, group="all"):
        """
            Labels for contacts tabs
        """
        defaults = {"all": "Contacts",
                    "private_contacts": "Private Contacts",
                    "public_contacts": "Public Contacts",
                    }

        tabs = self.get_pr_contacts_tabs()
        label = tabs.get(group) if type(tabs) is dict else None

        if label is None:
            # Use default label
            label = defaults.get(group)

        return current.T(label) if label else label

    def get_pr_multiple_case_groups(self):
        """
            Whether a person can belong to multiple case groups at the same time
        """
        return self.pr.get("multiple_case_groups", False)

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

    def get_project_activity_beneficiaries(self):
        """
            Use Beneficiaries in Activities
        """
        setting = self.project.get("activity_beneficiaries", None)
        if setting is None:
            setting = self.has_module("stats")
        return setting

    def get_project_activity_items(self):
        """
            Use Items in Activities
        """
        setting = self.project.get("activity_items", None)
        if setting is None:
            setting = self.has_module("supply")
        return setting

    def get_project_activity_sectors(self):
        """
            Use Sectors in Activities
        """
        return self.project.get("activity_sectors", False)

    def get_project_activity_types(self):
        """
            Use Activity Types in Activities & Projects
        """
        return self.project.get("activity_types", False)

    def get_project_activity_filter_year(self):
        """
            Filter according to Year in Activities
        """
        return self.project.get("activity_filter_year", False)

    def get_project_assign_staff_tab(self):
        """
            Show the 'Assign Staff' tab in Projects (if the user has permission to do so)
        """
        return self.__lazy("project", "assign_staff_tab", default=True)

    def get_project_budget_monitoring(self):
        """
            Whether to Monitor Project Budgets
        """
        return self.project.get("budget_monitoring", False)

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

    def get_project_community_volunteers(self):
        """
            Manage Community Volunteers in Projects
        """
        return self.project.get("community_volunteers", False)

    def get_project_demographics(self):
        """
            Use Demographics in Projects
        """
        return self.project.get("demographics", False)

    def get_project_details_tab(self):
        """
            Group Tabs on Projects into a single 'Details' page
        """
        return self.project.get("details_tab", False)

    def get_project_event_activities(self):
        """
            Link Activities to Events
        """
        return self.project.get("event_activities", False)

    def get_project_event_projects(self):
        """
            Link Projects to Events
        """
        return self.project.get("event_projects", False)

    def get_project_goals(self):
        """
            Use Goals in Projects
        """
        return self.project.get("goals", False)

    def get_project_hazards(self):
        """
            Use Hazards in DRR Projects
        """
        use_hazards = self.project.get("hazards")
        if use_hazards is None:
            # Default to True if mode_drr
            use_hazards = self.get_project_mode_drr()

        return use_hazards

    def get_project_hfa(self):
        """
            Use HFA Priorities in DRR Projects
        """
        use_hfa = self.project.get("hfa")
        if use_hfa is None:
            # Default to True if mode_drr
            use_hfa = self.get_project_mode_drr()

        return use_hfa

    def get_project_indicators(self):
        """
            Use Indicators in Projects
        """
        return self.project.get("indicators", False)

    def get_project_indicator_criteria(self):
        """
            Use Indicator Criteria in Projects
        """
        return self.project.get("indicator_criteria", False)

    def get_project_status_from_activities(self):
        """
            Use Activity Statuses to build Project Status (instead of Indicator Data)
        """
        return self.project.get("status_from_activities", False)

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

    def get_project_outcomes(self):
        """
            Use Outcomes in Projects
        """
        return self.project.get("outcomes", False)

    def get_project_outputs(self):
        """
            Use Outputs in Projects
        """
        return self.project.get("outputs", "inline")

    def get_project_planning_ondelete(self):
        """
            Whether the Project Planning data should CASCADE ondelete or RESTRICT

            NB This cannot be edited on the fly, or vary by context
               It needs defining before the database is created.
        """
        return self.project.get("planning_ondelete", "CASCADE")

    def get_project_projects(self):
        """
            Link Activities & Tasks to Projects
        """
        return self.project.get("projects", False)

    def get_project_programmes(self):
        """
            Use Programmes in Projects
        """
        return self.project.get("programmes", False)

    def get_project_programme_budget(self):
        """
            Use Budgets in Programmes
        """
        return self.project.get("programme_budget", False)

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
        """
            Organisation roles within projects
        """
        T = current.T
        return self.project.get("organisation_roles", {
                1: T("Lead Implementer"), # T("Host National Society")
                2: T("Partner"),          # T("Partner National Society")
                3: T("Donor"),
                #4: T("Customer"), # T("Beneficiary")?
                #5: T("Supplier")  # T("Beneficiary")?
            })

    def get_project_organisation_lead_role(self):
        """
            The lead role of organisations within projects
        """
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
                                                     7: T("Canceled"),
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

    def get_project_task_time(self):
        """
            Whether to use hours logging for tasks
        """
        return self.project.get("task_time", True)

    def get_project_my_tasks_include_team_tasks(self):
        """
            "My Open Tasks" to include team tasks
        """
        return self.project.get("my_tasks_include_team_tasks", False)

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
        return self.req.get("req_type", ("Stock", "People", "Other"))

    def get_req_type_inv_label(self):
        return current.T(self.req.get("type_inv_label", "Warehouse Stock"))

    def get_req_type_hrm_label(self):
        return current.T(self.req.get("type_hrm_label", "People"))

    def get_req_copyable(self):
        """
            Provide a Copy button for Requests?
        """
        return self.req.get("copyable", False)

    def get_req_recurring(self):
        """
            Do we allow creation of recurring requests?
        """
        return self.req.get("recurring", True)

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

    def get_req_pack_values(self):
        """
            Do we show pack values in Requests?
        """
        return self.req.get("pack_values", True)

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
            Whether Requests module should use inline forms for Items/Skills
        """
        return self.req.get("inline_forms", True)

    def get_req_prompt_match(self):
        """
            Whether a Requester is prompted to match each line item in an Item request
        """
        return self.req.get("prompt_match", True)

    #def get_req_summary(self):
    #    """
    #        Whether to use Summary Needs for Sites (Office/Facility currently):
    #    """
    #    return self.req.get("summary", False)

    def get_req_use_commit(self):
        """
            Whether there is a Commit step in Requests Management
        """
        return self.req.get("use_commit", True)

    def get_req_commit_people(self):
        """
            Whether Skills Requests should be Committed with Named Indviduals
            or just Anonymous Skill

            @ToDo: Make this do something
        """
        return self.req.get("commit_people", False)

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

    def get_req_req_crud_strings(self, req_type=None):
        return self.req.get("req_crud_strings") and \
               self.req.req_crud_strings.get(req_type)

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
        """
            The name of the Default Item Catalog
        """
        return self.supply.get("catalog_default", "Default")

    def get_supply_catalog_multi(self):
        """
            Whether to use Multiple Item Catalogs
        """
        return self.supply.get("catalog_multi", True)

    def get_supply_use_alt_name(self):
        """
            Whether to allow Alternative Items to be defined
        """
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
    # XForms
    #
    def get_xforms_resources(self):
        """
            A list of xform resources

            Item formats:
                "tablename"
                ("Title", "tablename")
                ("Title", "tablename", options)

            Format for options:
                {c=controller,         ...use this controller for form handling
                 f=function,           ...use this function for form handling
                 vars=vars,            ...add these vars to the download URL
                 title=title_field,    ...use this field in template for form title
                 public=public_flag,   ...check this field whether the template is
                                          public or not (must be boolean)
                 }

            Example:
                settings.xforms.resources = [("Request", "req_req")]

            @todo: move this documentation to the wiki?
        """
        return self.xforms.get("resources")

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
    def __lazy(self, subset, key, default=None):
        """
            Resolve a "lazy" setting: when the config setting is callable,
            call it once and store the result. A callable setting takes
            the default value as parameter.

            This method allows settings to depend on user authentication
            (e.g. org-dependent variations), or involve database lookups,
            which is only possible /after/ the initial config.py run.

            Normal pattern:
                return self.<subset>.get(key, default)

            Lazy pattern:
                return self.__lazy(subset, key, default)

            @param subset: the name of the subset of settings (typically the module)
            @param key: the setting name
            @param default: the default value
        """

        setting = self[subset].get(key, default)
        if callable(setting):
            # Check to see if we have already done the lazy lookup
            # (Some settings options are callables themselves)
            _key = "%s_%s" % (subset, key)
            if _key not in self._lazy_unwrapped:
                # Unwrap
                self[subset][key] = setting = setting(default)
                # Mark as unwrapped, so we don't do it a 2nd time
                self._lazy_unwrapped.append(_key)
        return setting

# END =========================================================================
