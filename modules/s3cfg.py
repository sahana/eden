# -*- coding: utf-8 -*-

""" Deployment Settings

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: 2009-2012 (c) Sahana Software Foundation
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

__all__ = ["S3Config"]

from gluon import current, URL
from gluon.storage import Storage

from gluon.contrib.simplejson.ordered_dict import OrderedDict

class S3Config(Storage):

    """
        Deployment Settings Helper Class
    """

    def __init__(self):
        self.auth = Storage()
        self.auth.email_domains=[]
        self.base = Storage()
        self.database = Storage()
        self.frontpage = Storage()
        self.frontpage.rss = []
        self.fin = Storage()
        self.L10n = Storage()
        self.mail = Storage()
        self.msg = Storage()
        self.options = Storage()
        self.save_search = Storage()
        self.security = Storage()
        self.ui = Storage()
        self.cap = Storage()
        self.gis = Storage()
        self.hrm = Storage()
        self.inv = Storage()
        self.irs = Storage()
        self.org = Storage()
        self.proc = Storage()
        self.project = Storage()
        self.req = Storage()
        self.supply = Storage()
        self.hms = Storage()

    # -------------------------------------------------------------------------
    # Template
    def get_template(self):
        """
            Which deployment template to use for config.py, parser.py, menus.py, etc
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
        return

    # -------------------------------------------------------------------------
    # Theme
    def get_theme(self):
        """
            Which templates folder to use for views/layout.html
        """
        return self.base.get("theme", "default")

    # -------------------------------------------------------------------------
    def is_cd_version(self):
        """
            Whether we're running from a non-writable CD
        """
        return self.base.get("cd_version", False)

    # -------------------------------------------------------------------------
    # Auth settings
    def get_auth_hmac_key(self):
        """
            salt to encrypt passwords - normally randomised during 1st run
        """
        return self.auth.get("hmac_key", "akeytochange")

    def get_auth_facebook(self):
        """
            Read the FaceBook OAuth settings
            - if configured, then it is assumed that FaceBook Authentication is enabled
        """
        id = self.auth.get("facebook_id", False)
        secret = self.auth.get("facebook_secret", False)
        if id and secret:
            return dict(id=id, secret=secret)
        else:
            return False

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
    def get_auth_login_next(self):
        """ Which page to go to after login """
        return self.auth.get("login_next", URL(c="default", f="index"))
    def get_auth_registration_requires_verification(self):
        return self.auth.get("registration_requires_verification", False)
    def get_auth_registration_requires_approval(self):
        return self.auth.get("registration_requires_approval", False)
    def get_auth_opt_in_team_list(self):
        return self.auth.get("opt_in_team_list", [])
    def get_auth_opt_in_to_email(self):
        return self.get_auth_opt_in_team_list() != []
    def get_auth_opt_in_default(self):
        return self.auth.get("opt_in_default", False)
    def get_auth_registration_requests_mobile_phone(self):
        return self.auth.get("registration_requests_mobile_phone", False)
    def get_auth_registration_mobile_phone_mandatory(self):
        " Make the selection of Mobile Phone Mandatory during registration "
        return self.auth.get("registration_mobile_phone_mandatory", False)
    def get_auth_registration_requests_organisation(self):
        " Have the registration form request the Organisation "
        return self.auth.get("registration_requests_organisation", False)
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
    def get_auth_registration_requests_site(self):
        " Have the registration form request the Site "
        return self.auth.get("registration_requests_site", False)
    def get_auth_registration_site_required(self):
        " Make the selection of site required during registration "
        return self.auth.get("registration_site_required", False)
    def get_auth_registration_pending(self):
        """ Message someone gets when they register & they need approving """
        return self.auth.get("registration_pending",
            "Registration is still pending approval from Approver (%s) - please wait until confirmation received." % \
                self.get_mail_approver())
    def get_auth_registration_pending_approval(self):
        """ Message someone gets when they register & they need approving """
        return self.auth.get("registration_pending_approval",
            "Thank you for validating your email. Your user account is still pending for approval by the system administator (%s). You will get a notification by email when your account is activated." % \
                self.get_mail_approver())
    def get_auth_registration_requests_image(self):
        """ Have the registration form request an Image """
        return self.auth.get("registration_requests_image", False)
    def get_auth_registration_roles(self):
        """
            A dictionary of realms, with lists of role UUIDs, to assign to newly-registered users
            Use key = 0 to have the roles not restricted to a realm
        """
        return self.auth.get("registration_roles", [])
    def get_auth_registration_volunteer(self):
        """ Redirect the newly-registered user to their volunteer details page """
        return self.auth.get("registration_volunteer", False)
    def get_auth_always_notify_approver(self):
        return self.auth.get("always_notify_approver", True)
    def get_auth_record_approval(self):
        """ Use record approval (False by default) """
        return self.auth.get("record_approval", False)
    def get_auth_record_approval_required_for(self):
        """ Which tables record approval is required for """
        return self.auth.get("record_approval_required_for", None)
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
    def get_auth_role_modules(self):
        """
            Which modules are includes in the Role Manager
            - to assign discrete permissions to via UI
        """
        T = current.T
        return self.auth.get("role_modules", OrderedDict([
            ("staff", "Staff"),
            ("vol", "Volunteers"),
            ("member", "Members"),
            ("inv", "Warehouses"),
            ("asset", "Assets"),
            ("project", "Projects"),
            ("survey", "Assessments"),
            ("irs", "Incidents")
        ]))
    def get_auth_access_levels(self):
        """
            Access levels for the Role Manager UI
        """
        T = current.T
        return self.auth.get("access_levels", OrderedDict([
            ("reader", "Reader"),
            ("data_entry", "Data Entry"),
            ("editor", "Editor"),
            ("super", "Super Editor")
        ]))

    def get_security_archive_not_delete(self):
        return self.security.get("archive_not_delete", True)
    def get_security_audit_read(self):
        return self.security.get("audit_read", False)
    def get_security_audit_write(self):
        return self.security.get("audit_write", False)
    def get_security_policy(self):
        " Default is Simple Security Policy "
        return self.security.get("policy", 1)
    def get_security_map(self):
        return self.security.get("map", False)
    def get_security_self_registration(self):
        return self.security.get("self_registration", True)

    # -------------------------------------------------------------------------
    # Base settings
    def get_system_name(self):
        return self.base.get("system_name", current.T("Sahana Eden Humanitarian Management Platform"))
    def get_system_name_short(self):
        return self.base.get("system_name_short", "Sahana Eden")
    def get_base_debug(self):
        return self.base.get("debug", False)
    def get_base_migrate(self):
        """ Whether to allow Web2Py to migrate the SQL database to the new structure """
        return self.base.get("migrate", True)
    def get_base_fake_migrate(self):
        """ Whether to have Web2Py create the .table files to match the expected SQL database structure """
        return self.base.get("fake_migrate", False)
    def get_base_prepopulate(self):
        """ Whether to prepopulate the database &, if so, which set of data to use for this """
        return self.base.get("prepopulate", 1)
    def get_base_public_url(self):
        return self.base.get("public_url", "http://127.0.0.1:8000")
    def get_base_cdn(self):
        return self.base.get("cdn", False)
    def get_base_session_memcache(self):
        """
            Should we store sessions in a Memcache service to allow sharing
            between multiple instances?
        """
        return self.base.get("session_memcache", False)

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
            db_string = "mysql://%s:%s@%s:%s/%s" % \
                        (self.database.get("username", "sahana"),
                         self.database.get("password", "password"),
                         self.database.get("host", "localhost"),
                         self.database.get("port", None) or "3306",
                         self.database.get("database", "sahana"))
        elif (db_type == "postgres"):
            db_string = "postgres://%s:%s@%s:%s/%s" % \
                        (self.database.get("username", "sahana"),
                         self.database.get("password", "password"),
                         self.database.get("host", "localhost"),
                         self.database.get("port", None) or "5432",
                         self.database.get("database", "sahana"))
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
            "EUR" :T("Euros"),
            "GBP" :T("Great British Pounds"),
            "USD" :T("United States Dollars"),
        }
        return self.fin.get("currencies", currencies)
    def get_fin_currency_default(self):
        return self.fin.get("currency_default", "USD") # Dollars
    def get_fin_currency_writable(self):
        return self.fin.get("currency_writable", True)

    # -------------------------------------------------------------------------
    # GIS (Map) Settings
    def get_gis_api_bing(self):
        """ API key for Bing """
        return self.gis.get("api_bing", None)
    def get_gis_api_google(self):
        """
            API key for Google
            - needed for Earth, MapMaker & GeoCoder
            - defaults to localhost
        """
        return self.gis.get("api_google", "ABQIAAAAgB-1pyZu7pKAZrMGv3nksRTpH3CbXHjuCVmaTc5MkkU4wO1RRhQWqp1VGwrG8yPE2KhLCPYhD7itFw")
    def get_gis_api_yahoo(self):
        """ API key for Yahoo """
        return self.gis.get("api_yahoo", None)
    def get_gis_countries(self):
        return self.gis.get("countries", [])
    def get_gis_building_name(self):
        " Display Building Name when selecting Locations "
        return self.gis.get("building_name", True)
    def get_gis_latlon_selector(self):
        " Display a Lat/Lon boxes when selecting Locations "
        return self.gis.get("latlon_selector", True)
    def get_gis_map_selector(self):
        " Display a Map-based tool to select Locations "
        return self.gis.get("map_selector", True)
    def get_gis_menu(self):
        """
            Should we display a menu of GIS configurations?
            - set to False to not show the menu (default)
            - set to the label to use for the menu to enable it
            e.g. T("Events") or T("Regions")
        """
        return self.gis.get("menu", False)
    def get_gis_display_l0(self):
        return self.gis.get("display_L0", False)
    def get_gis_display_l1(self):
        return self.gis.get("display_L1", True)
    def get_gis_duplicate_features(self):
        return self.gis.get("duplicate_features", False)
    def get_gis_edit_group(self):
        " Edit Location Groups "
        return self.gis.get("edit_GR", False)
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
    def get_gis_marker_max_height(self):
        return self.gis.get("marker_max_height", 35)
    def get_gis_marker_max_width(self):
        return self.gis.get("marker_max_width", 30)
    def get_gis_mouse_position(self):
        return self.gis.get("mouse_position", "normal")
    def get_gis_poi_resources(self):
        """
            List of resources (tablenames) to import/export as PoIs from Admin Locations
            - KML & OpenStreetMap formats
        """
        return self.gis.get("poi_resources",
                            ["cr_shelter", "hms_hospital", "org_office"])
    def get_gis_print_service(self):
        return self.gis.get("print_service", "")
    def get_gis_geoserver_url(self):
        return self.gis.get("geoserver_url", "")
    def get_gis_geoserver_username(self):
        return self.gis.get("geoserver_username", "admin")
    def get_gis_geoserver_password(self):
        return self.gis.get("geoserver_password", "")
    def get_gis_spatialdb(self):
        db_type = self.get_database_type()
        if db_type != "postgres":
            # Only Postgres supported currently
            return False
        else:
            return self.gis.get("spatialdb", False)

    # -------------------------------------------------------------------------
    # L10N Settings
    def get_L10n_default_country_code(self):
        return self.L10n.get("default_country_code", 1)
    def get_L10n_default_language(self):
        return self.L10n.get("default_language", "en")
    def get_L10n_display_toolbar(self):
        return self.L10n.get("display_toolbar", True)
    def get_L10n_languages(self):
        return self.L10n.get("languages",
                             OrderedDict([
                                ("ar", "العربية"),
                                ("zh-cn", "中文 (简体)"),
                                ("zh-tw", "中文 (繁體)"),
                                ("en", "English"),
                                ("fr", "Français"),
                                ("de", "Deutsch"),
                                ("el", "ελληνικά"),
                                ("it", "Italiano"),
                                ("ja", "日本語"),
                                ("ko", "한국어"),
                                ("pt", "Português"),
                                ("pt-br", "Português (Brasil)"),
                                ("ru", "русский"),
                                ("es", "Español"),
                                ("tl", "Tagalog"),
                                ("ur", "اردو"),
                                ("vi", "Tiếng Việt"),
                            ]))
    def get_L10n_religions(self):
        """
            Religions used in Person Registry

            @ToDo: find a better code
            http://eden.sahanafoundation.org/ticket/594
        """
        T = current.T
        return self.L10n.get("religions", {
                "none":T("none"),
                "christian":T("Christian"),
                "muslim":T("Muslim"),
                "jewish":T("Jewish"),
                "buddhist":T("Buddhist"),
                "hindu":T("Hindu"),
                "bahai":T("Bahai"),
                "other":T("other")
            })
    def get_L10n_date_format(self):
        T = current.T
        return self.L10n.get("date_format", T("%Y-%m-%d"))
    def get_L10n_time_format(self):
        T = current.T
        return self.L10n.get("time_format", T("%H:%M:%S"))
    def get_L10n_datetime_format(self):
        T = current.T
        return self.L10n.get("datetime_format", T("%Y-%m-%d %H:%M:%S"))
    def get_L10n_utc_offset(self):
        return self.L10n.get("utc_offset", "UTC +0000")
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
    def get_L10n_languages_readonly(self):
        return self.L10n.get("languages_readonly", True)
    def get_L10n_mandatory_lastname(self):
        return self.L10n.get("mandatory_lastname", False)
    def get_L10n_thousands_separator(self):
        return self.L10n.get("thousands_separator", False)

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
    # Options
    def get_terms_of_service(self):
        return self.options.get("terms_of_service", False)

    # -------------------------------------------------------------------------
    # UI Settings
    def get_ui_navigate_away_confirm(self):
        return self.ui.get("navigate_away_confirm", True)

    def get_ui_confirm(self):
        """
            For Delete actions
            Workaround for this Bug in Selenium with FF4:
                http://code.google.com/p/selenium/issues/detail?id=1604
        """
        return self.ui.get("confirm", True)

    def get_ui_autocomplete(self):
        """ Currently Unused """
        return self.ui.get("autocomplete", False)

    def get_ui_read_label(self):
        """
            Label for buttons in list views which lead to a Read-opnly 'Display' view
        """
        return self.ui.get("read_label", "Open")

    def get_ui_update_label(self):
        """
            Label for buttons in list views which lead to a Read-opnly 'Display' view
        """
        return self.ui.get("update_label", "Open")

    def get_ui_cluster(self):
        """ UN-style deployment? """
        return self.ui.get("cluster", False)

    def get_ui_camp(self):
        """ 'Camp' instead of 'Shelter'? """
        return self.ui.get("camp", False)

    def get_ui_label_mobile_phone(self):
        """
            Label for the Mobile Phone field
            e.g. 'Cell Phone'
        """
        return current.T(self.ui.get("label_mobile_phone", "Mobile Phone"))

    def get_ui_label_postcode(self):
        """
            Label for the Postcode field
            e.g. 'ZIP Code'
        """
        return current.T(self.ui.get("label_postcode", "Postcode"))

    def get_ui_social_buttons(self):
        """ Display social media Buttons in the footer? """
        return self.ui.get("social_buttons", False)

    # =========================================================================
    # Messaging
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
            - unless overridden by per-domain entries in auth_organsiation
        """
        return self.mail.get("approver", "useradmin@example.org")
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
    # Twitter
    def get_msg_twitter_oauth_consumer_key(self):
        return self.msg.get("twitter_oauth_consumer_key", "")
    def get_msg_twitter_oauth_consumer_secret(self):
        return self.msg.get("twitter_oauth_consumer_secret", "")

    # -------------------------------------------------------------------------
    # Save Search and Subscription
    def get_save_search_widget(self):
        """
            Enable the Saved Search widget
        """
        return self.save_search.get("widget", True)

    # =========================================================================
    # Modules

    # -------------------------------------------------------------------------
    # Alert
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

        return self.cap.get("languages",
                             OrderedDict([
                                ("ar", "العربية"),
                                ("en", "English"),
                                ("fr", "Français"),
                                ("pt", "Português"),
                                ("ru", "русский"),
                                ("es", "Español")
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
    # Human Resource Management
    def get_hrm_email_required(self):
        """
            If set to True then Staff & Volunteers require an email address
        """
        return self.hrm.get("email_required", True)

    def get_hrm_deletable(self):
        """
            If set to True then HRM records are deletable rather than just being able to be marked as obsolete
        """
        return self.hrm.get("deletable", True)

    def get_hrm_job_roles(self):
        """
            If set to True then HRs can have multiple Job Roles in addition to their Job Title
        """
        return self.hrm.get("job_roles", False)

    def get_hrm_show_staff(self):
        """
            If set to True then show 'Staff' options when HRM enabled
            - needs a separate setting as vol requires hrm, but we may only wish to show Volunteers
        """
        return self.hrm.get("show_staff", True)

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

    def get_hrm_vol_experience(self):
        """
            Whether to use Experience for Volunteers &, if so, which table to use
            - options are: False, "experience" or "programme"
        """
        return self.hrm.get("vol_experience", "programme")

    def get_hrm_show_organisation(self):
        """
            Whether Human Resource representations should include the Organisation
        """
        return self.hrm.get("show_organisation", False)

    def get_hrm_use_teams(self):
        """
            Whether Human Resources should use Teams
        """
        return self.hrm.get("use_teams", True)

    def get_hrm_use_certificates(self):
        """
            Whether Human Resources should use Certificates
        """
        return self.hrm.get("use_certificates", True)

    def get_hrm_use_credentials(self):
        """
            Whether Human Resources should use Credentials
        """
        return self.hrm.get("use_credentials", True)

    def get_hrm_use_description(self):
        """
            Whether Human Resources should use Description
        """
        return self.hrm.get("use_description", True)

    def get_hrm_use_education(self):
        """
            Whether Human Resources should show Education
        """
        return self.hrm.get("use_education", False)

    def get_hrm_use_id(self):
        """
            Whether Human Resources should use ID
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

    def get_hrm_organisation_label(self):
        """
            Label for Organisations in Human Resources
        """
        return current.T(self.hrm.get("organisation_label", "Organization"))

    # -------------------------------------------------------------------------
    # Inventory Management Settings
    #
    def get_inv_collapse_tabs(self):
        return self.inv.get("collapse_tabs", True)

    def get_inv_item_status(self):
        """
            Item Statuses which can also be Sent Shipment Types
        """
        T = current.T
        return self.inv.get("item_status", {
                0: current.messages.NONE,
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
        return self.inv.get("shipment_type", {
                0 : current.messages.NONE,
                11: current.T("Internal Shipment"),
            })

    def get_inv_send_types(self):
        """
            Shipment types which are just for Send
        """
        return self.inv.get("send_type", {
                21: current.T("Distribution"),
            })

    def get_inv_recv_types(self):
        """
            Shipment types which are just for Receive
        """
        T = current.T
        return self.inv.get("recv_type", {
                #31: T("Other Warehouse"), Same as Internal Shipment
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
    def get_irs_vehicle(self):
        """
            Use Vehicles to respond to Incident Reports
        """
        return self.irs.get("vehicle", False)

    # -------------------------------------------------------------------------
    # Organisation
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

    def get_org_summary(self):
        """
            Whether to use Summary fields for Organisation/Office:
                # National/International staff
        """
        return self.org.get("summary", False)

    def set_org_dependent_field(self,
                                tablename=None,
                                fieldname=None,
                                enable_field =True):
        """
            Enables/Disables optional fields according to a user's Organisation
            - must specify either field or tablename/fieldname
                                           (e.g. for virtual fields)
        """

        auth = current.auth
        if auth.s3_has_role(auth.get_system_roles().ADMIN):
            # Admins see all fields
            enabled = True
        else:
            # Default to disabled
            enabled = False

        #elif not tablename or not fieldname:
        #    raise SyntaxError

        dependent_fields = self.org.get("dependent_fields", None)
        if dependent_fields and not enabled:
            org_name_list = dependent_fields.get("%s.%s" % (tablename,
                                                            fieldname),
                                                 None)

            if org_name_list:
                s3db = current.s3db
                otable = s3db.org_organisation
                root_org_id = auth.root_org()
                root_org = current.db(otable.id == root_org_id).select(otable.name,
                                                                       limitby=(0, 1),
                                                                       cache=s3db.cache
                                                                       ).first()
                if root_org:
                    enabled = root_org.name in org_name_list

        if enable_field:
            field = current.s3db[tablename][fieldname]
            field.readable = enabled
            field.writable = enabled

        return enabled

    # -------------------------------------------------------------------------
    # Proc
    def get_proc_form_name(self):
        return self.proc.get("form_name", "Purchase Order")
    def get_proc_shortname(self):
        return self.proc.get("form_name", "PO")

    # -------------------------------------------------------------------------
    # Projects
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
            Use Activities in Projects
        """
        return self.project.get("activities", False)

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

    def get_project_milestones(self):
        """
            Use Milestones in Projects
        """
        return self.project.get("milestones", False)

    def get_project_sectors(self):
        """
            Use Sectors in Projects
        """
        return self.project.get("sectors", True)

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
                2: T("Partner"), # T("Partner National Society")
                3: T("Donor"),
                4: T("Customer"), # T("Beneficiary")?
                5: T("Supplier"), # T("Beneficiary")?
            })

    def get_project_organisation_lead_role(self):
        return self.project.get("organisation_lead_role", 1)

    # -------------------------------------------------------------------------
    # Request Settings
    def get_req_type_inv_label(self):
        return self.req.get("type_inv_label", current.T("Warehouse Stock"))
    def get_req_type_hrm_label(self):
        return self.req.get("type_hrm_label", current.T("People"))

    def get_req_status_writable(self):
        """ Whether Request Status should be manually editable """
        return self.req.get("status_writable", True)
    def get_req_quantities_writable(self):
        """ Whether Item Quantities should be manually editable """
        return self.req.get("quantities_writable", False)
    def get_req_skill_quantities_writable(self):
        """ Whether People Quantities should be manually editable """
        return self.req.get("skill_quantities_writable", False)
    def get_req_multiple_req_items(self):
        return self.req.get("multiple_req_items", True)
    def get_req_show_quantity_transit(self):
        return self.req.get("show_quantity_transit", True)
    def get_req_use_commit(self):
        return self.req.get("use_commit", True)
    def get_req_req_crud_strings(self, type = None):
        return self.req.get("req_crud_strings") and \
               self.req.req_crud_strings.get(type, None)
    def get_supply_use_alt_name(self):
        return self.supply.get("use_alt_name", True)
    def get_req_use_req_number(self):
        return self.req.get("use_req_number", True)
    def get_req_generate_req_number(self):
        return self.req.get("generate_req_number", True)
    def get_req_req_type(self):
        return self.req.get("req_type", ["Stock", "People", "Other"])
    def get_req_form_name(self):
        return self.req.get("req_form_name", "Requisition Form")
    def get_req_shortname(self):
        return self.req.get("req_shortname", "REQ")

    # -------------------------------------------------------------------------
    # Supply
    def get_supply_catalog_default(self):
        return self.inv.get("catalog_default", "Default")

    # -------------------------------------------------------------------------
    # Hospital Registry
    def get_hms_track_ctc(self):
        return self.hms.get("track_ctc", False)

    def get_hms_activity_reports(self):
        return self.hms.get("activity_reports", False)

    # -------------------------------------------------------------------------
    # Active modules list
    def has_module(self, module_name):
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

# END =========================================================================
