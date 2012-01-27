# -*- coding: utf-8 -*-

""" Deployment Settings

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @author: Dominic König <dominic[at]aidiq.com>

    @copyright: 2009-2011 (c) Sahana Software Foundation
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

from gluon import current
from gluon.storage import Storage
from gluon.contrib.simplejson.ordered_dict import OrderedDict

class S3Config(Storage):

    """
        Deployment Settings Helper Class
    """

    def __init__(self):
        self.auth = Storage()
        self.base = Storage()
        self.database = Storage()
        self.frontpage = Storage()
        self.frontpage.rss = []
        self.fin = Storage()
        self.gis = Storage()
        self.osm = Storage()    # Backwards-compatiblity, deprecate soon
        self.mail = Storage()
        self.twitter = Storage()
        self.L10n = Storage()
        self.options = Storage()
        self.security = Storage()
        self.aaa = Storage()
        self.ui = Storage()
        self.req = Storage()
        self.inv = Storage()
        self.supply = Storage()
        self.hrm = Storage()
        self.project = Storage()
        self.save_search = Storage()

        T = current.T

        # These are copied from modules/s3/s3aaa.py
        self.aaa.acl =  Storage(CREATE = 0x0001,
                                READ   = 0x0002,
                                UPDATE = 0x0004,
                                DELETE = 0x0008,
                                ALL = 0x000F    # CREATE | READ | UPDATE | DELETE
                                )
        self.CURRENCIES = {
            "USD" :T("United States Dollars"),
            "EUR" :T("Euros"),
            "GBP" :T("Great British Pounds")
        }

    # -------------------------------------------------------------------------
    # Auth settings
    def get_auth_hmac_key(self):
        return self.auth.get("hmac_key", "akeytochange")
    def get_auth_openid(self):
        return self.auth.get("openid", False)
    def get_auth_registration_requires_verification(self):
        return self.auth.get("registration_requires_verification", False)
    def get_auth_registration_requires_approval(self):
        return self.auth.get("registration_requires_approval", False)
    def get_auth_registration_requests_mobile_phone(self):
        return self.auth.get("registration_requests_mobile_phone", False)
    def get_auth_registration_mobile_phone_mandatory(self):
        " Make the selection of Mobile Phone Mandatory during registration "
        return self.auth.get("registration_mobile_phone_mandatory", False)
    def get_auth_registration_requests_organisation(self):
        " Have the registration form request the Organisation "
        return self.auth.get("registration_requests_organisation", False)
    def get_auth_registration_organisation_mandatory(self):
        " Make the selection of Organisation Mandatory during registration "
        return self.auth.get("registration_organisation_mandatory", False)
    def get_auth_registration_organisation_hidden(self):
        " Hide the Organisation field in the registration form unless an email is entered which isn't whitelisted "
        return self.auth.get("registration_organisation_hidden", False)
    def get_auth_registration_requests_image(self):
        " Have the registration form request an Image "
        return self.auth.get("registration_requests_image", False)
    def get_auth_registration_volunteer(self):
        " Redirect the newly-registered user to their volunteer details page "
        return self.auth.get("registration_volunteer", False)
    def get_auth_always_notify_approver(self):
        return self.auth.get("always_notify_approver", False)

    # @ToDo: Deprecate
    def get_aaa_default_uacl(self):
        return self.aaa.get("default_uacl", self.aaa.acl.READ)
    def get_aaa_default_oacl(self):
        return self.aaa.get("default_oacl", self.aaa.acl.READ |
                                            self.aaa.acl.UPDATE)

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
        return self.base.get("system_name_short", self.get_system_name())
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

    # -------------------------------------------------------------------------
    # Database settings
    def get_database_type(self):
        return self.database.get("db_type", "sqlite")
    def get_database_string(self):
        db_type = self.database.get("db_type", "sqlite")
        pool_size = self.database.get("pool_size", 0)
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
        if pool_size:
            return (db_string, pool_size)
        else:
            return db_string

    # -------------------------------------------------------------------------
    # Finance settings
    # @ToDo: Make these customisable per User/Facility
    def get_fin_currencies(self):
        return self.fin.get("currencies", self.CURRENCIES)
    def get_fin_currency_default(self):
        return self.fin.get("currency_default", "USD") # Dollars
    def get_fin_currency_writable(self):
        return self.fin.get("currency_writable", True)

    # -------------------------------------------------------------------------
    # GIS (Map) Settings
    # No defaults are needed for gis_config deployment settings -- initial
    # defaults come either from the table itself or are added to the site
    # config when it is created. This does not include defaults for the
    # hierarchy labels as that is defined separately in 000_config.
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
    def get_gis_edit_lx(self):
        " Edit Hierarchy Locations "
        return self.gis.get("edit_Lx", True)
    def get_gis_edit_group(self):
        " Edit Location Groups "
        return self.gis.get("edit_GR", False)
    def get_gis_marker_max_height(self):
        return self.gis.get("marker_max_height", 35)
    def get_gis_marker_max_width(self):
        return self.gis.get("marker_max_width", 30)
    def get_gis_mouse_position(self):
        return self.gis.get("mouse_position", "normal")
    def get_gis_print_service(self):
        return self.gis.get("print_service", "")
    def get_gis_geoserver_url(self):
        return self.gis.get("geoserver_url", "")
    def get_gis_geoserver_username(self):
        return self.gis.get("geoserver_username", "admin")
    def get_gis_geoserver_password(self):
        return self.gis.get("geoserver_password", "password")
    def get_gis_spatialdb(self):
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
        return self.L10n.get("languages", { "en":current.T("English") })
    def get_L10n_religions(self):
        T = current.T
        return self.L10n.get("religions", { "none":T("None"),
                                            "other":T("Other") })
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
    def get_L10n_mandatory_lastname(self):
        return self.L10n.get("mandatory_lastname", False)
    def get_L10n_thousands_separator(self):
        return self.L10n.get("thousands_separator", False)

    # -------------------------------------------------------------------------
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
        return self.mail.get("sender", "sahana@your.org")
    def get_mail_approver(self):
        return self.mail.get("approver", "useradmin@your.org")
    def get_mail_limit(self):
        """ A daily limit to the number of messages which can be sent """
        return self.mail.get("limit", None)

    # Twitter settings
    def get_twitter_oauth_consumer_key(self):
        return self.twitter.get("oauth_consumer_key", "")
    def get_twitter_oauth_consumer_secret(self):
        return self.twitter.get("oauth_consumer_secret", "")

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
    def get_options_support_requests(self):
        return self.options.get("support_requests", False)

    # -------------------------------------------------------------------------
    # UI/Workflow Settings
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
    def get_ui_update_label(self):
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
        T = current.T
        label = self.ui.get("label_mobile_phone", T("Mobile Phone"))
        # May need this form for Web Setup
        #return T(label)
        return label

    def get_ui_label_postcode(self):
        """
            Label for the Postcode field
            e.g. 'ZIP Code'
        """
        T = current.T
        label = self.ui.get("label_postcode", T("Postcode"))
        # May need this form for Web Setup
        #return T(label)
        return label

    def get_ui_social_buttons(self):
        """ Display social media Buttons in the footer? """
        return self.ui.get("social_buttons", False)
    # -------------------------------------------------------------------------
    # Modules
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

    # -------------------------------------------------------------------------
    # Inventory Management Setting
    def get_inv_collapse_tabs(self):
        return self.inv.get("collapse_tabs", True)
    def get_inv_shipment_name(self):
        """
            Get the name of Shipments
            - currently supported options are:
            * shipment
            * order
        """
        return self.inv.get("shipment_name", "shipment")

    # -------------------------------------------------------------------------
    # Supply
    def get_supply_catalog_default(self):
        return self.inv.get("catalog_default", "Other Items")

    # -------------------------------------------------------------------------
    # Human Resource Management
    def get_hrm_email_required(self):
        return self.hrm.get("email_required", True)

    def get_hrm_skill_types(self):
        """
            If set to True then Skill Types are exposed to the UI
            - each skill_type needs it's own set of competency levels
            If set to False then Skill Types are hidden from the UI
            - all skills use the same skill_type & hence the same set of competency levels
        """
        return self.hrm.get("skill_types", False)

    # -------------------------------------------------------------------------
    # Project Tracking
    def get_project_drr(self):
        return self.project.get("drr", False)
    def get_project_community_activity(self):
        return self.project.get("community_activity", False)

    # Save Search and Subscription
    def get_save_search_widget(self):
        return self.save_search.get("widget", True)

    # -------------------------------------------------------------------------
    # Active modules list
    def has_module(self, module_name):
        if not self.modules:
            # Provide a minimal list of core modules
            _modules = [
                "admin",        # Admin
                "gis",          # GIS
                "pr",           # Person Registry
                "org"           # Organization Registry
            ]
        else:
            _modules = self.modules

        return module_name in _modules

# END =========================================================================