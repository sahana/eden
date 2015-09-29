# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current
from gluon.html import *
from gluon.storage import Storage
from s3 import S3CustomController
from templates.Nepal.layouts import IndexMenuLayout

def config(settings):
    """
        Template settings: 'Skeleton' designed to be copied to quickly create
                           custom templates

        All settings which are to configure a specific template are located
        here. Deployers should ideally not need to edit any other files outside
        of their template folder.
    """

    T = current.T

    settings.base.system_name = T("Nepal Sahana Disaster Management Platform")
    settings.base.system_name_short = T("Sahana")

    # PrePopulate data
    settings.base.prepopulate = ("Nepal", "default/users")

    # Theme (folder to use for views/layout.html)
    #settings.base.theme = "Nepal"

    # Authentication settings
    # Should users be allowed to register themselves?
    #settings.security.self_registration = False
    # Do new users need to verify their email address?
    settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    settings.auth.registration_requests_organisation = True
    settings.auth.registration_requests_site = True

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    settings.gis.countries = ("NP",)
    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

    # L10n settings
    # Languages used in the deployment (used for Language Toolbar & GIS Locations)
    # http://www.loc.gov/standards/iso639-2/php/code_list.php
    settings.L10n.languages = OrderedDict([
    #    ("ar", "العربية"),
    #    ("bs", "Bosanski"),
        ("en", "English"),
    #    ("fr", "Français"),
    #    ("de", "Deutsch"),
    #    ("el", "ελληνικά"),
    #    ("es", "Español"),
    #    ("it", "Italiano"),
    #    ("ja", "日本語"),
    #    ("km", "ភាសាខ្មែរ"),
    #    ("ko", "한국어"),
        ("ne", "नेपाली"),          # Nepali
    #    ("prs", "دری"), # Dari
    #    ("ps", "پښتو"), # Pashto
    #    ("pt", "Português"),
    #    ("pt-br", "Português (Brasil)"),
    #    ("ru", "русский"),
    #    ("tet", "Tetum"),
    #    ("tl", "Tagalog"),
    #    ("tr", "Türkçe"),
    #    ("ur", "اردو"),
    #    ("vi", "Tiếng Việt"),
    #    ("zh-cn", "中文 (简体)"),
    #    ("zh-tw", "中文 (繁體)"),
    ])
    # Default language for Language Toolbar (& GIS Locations in future)
    #settings.L10n.default_language = "en"
    # Uncomment to Hide the language toolbar
    #settings.L10n.display_toolbar = False
    # Default timezone for users
    settings.L10n.utc_offset = "+0545"
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = ","
    # Uncomment this to Translate Layer Names
    #settings.L10n.translate_gis_layer = True
    # Uncomment this to Translate Location Names
    #settings.L10n.translate_gis_location = True
    # Uncomment this to Translate Organisation Names/Acronyms
    #settings.L10n.translate_org_organisation = True

    # Finance settings
    settings.fin.currencies = {
        "NPR" : T("Nepalese Rupee"),
        "AUD" : T("Australian Dollar"),
        "EUR" : T("Euro"),
        "GBP" : T("British Pound"),
        "INR" : T("Indian Rupee"),
        "KRW" : T("South-Korean Won"),
        "JPY" : T("Japanese Yen"),
        "NZD" : T("New Zealand Dollar"),
        "USD" : T("United States Dollars"),
    }
    settings.fin.currency_default = "NPR"

    # Security Policy
    # http://eden.sahanafoundation.org/wiki/S3AAA#System-widePolicy
    # 1: Simple (default): Global as Reader, Authenticated as Editor
    # 2: Editor role required for Update/Delete, unless record owned by session
    # 3: Apply Controller ACLs
    # 4: Apply both Controller & Function ACLs
    # 5: Apply Controller, Function & Table ACLs
    # 6: Apply Controller, Function, Table ACLs and Entity Realm
    # 7: Apply Controller, Function, Table ACLs and Entity Realm + Hierarchy
    # 8: Apply Controller, Function, Table ACLs, Entity Realm + Hierarchy and Delegations
    #
    settings.security.policy = 6 # Organisation-ACLs

    # User Interface
    settings.ui.icons = "font-awesome4"
    settings.ui.custom_icons = {
        "ambulance": "fa fa-ambulance",
        "create":"fa fa-plus",
        "hospital":"fa fa-hospital-o",
        "receive": "fa fa-sign-in",
        "recv_shipments": "fa fa-indent",
        "resource": "fa fa-cube",
        "send": "fa fa-sign-out",
        "sent_shipments": "fa fa-outdent",
        "shelter": "fa fa-home",
        "site-current": "fa fa-square",
        "sites-all": "fa fa-th",
        "stock": "fa fa-cubes",
        "user": "fa fa-user",
        "volunteer": "fa fa-user",
        "volunteers": "fa fa-users",
    }
    # -------------------------------------------------------------------------
    # Module Settings
    settings.org.sector = True
    settings.ui.cluster = True

    # Simple Requests
    settings.req.req_type = ("Other",)
    # Uncomment to disable the Commit step in the workflow & simply move direct to Ship
    settings.req.use_commit = False

    # Doesn't appear to work... Need inline field and/or component tab?
    settings.hrm.multi_job_titles = True

    # =========================================================================
    def customise_inv_index():
        """ Custom Inventory Index Page"""
        response = current.response
        response.title = T("Sahana : Warehouse Management")
        s3 = response.s3
        s3db = current.s3db
        s3.stylesheets.append("../themes/Nepal/index.css")
        s3.stylesheets.append("../styles/font-awesome.css")
        S3CustomController._view("Nepal","inv_index.html")

        site_id = current.auth.user.site_id
        if site_id:
            current_site = DIV(XML(T("You are currently managing stock for: %(site)s") % \
                                {"site":s3db.org_site_represent(site_id,
                                                                show_link = True)}),
                                _title = T("Contact Administrator to change your default facility."),
                                )
        else:
            current_site = ""
        is_current_site = lambda i: site_id
        
        IM = IndexMenuLayout
        index_menu = IM()(IM("Receive", c="inv", f="recv", args="create", 
                             vars={"recv.status":2},
                             icon="receive",
                             description=T("Receive a New shipment or an Existing shipment at your site."),
                             )(IM("Existing", args="summary", icon="list",vars={"recv.status":2}),
                               IM("New",args="create",icon="create")),
                          IM("Send", c="inv", f="send",
                             description=T("Send a shipment from your site."),
                             )(IM("Create",args="create",icon="create")),
                          IM("Stock", c="inv", f="inv_item",
                             icon="stock",
                             description=T("List of stock at sites."),
                             )(IM("Your Site",icon="your-site", check = is_current_site),
                               IM("All Sites",icon="all-sites")),
                          IM("Recvd. Shipments", c="inv", f="recv", args="summary",
                             vars={"recv.status__ne":2},
                             icon="recv_shipments",
                             description=T("List of received shipments."),
                             )(IM("Your Site",icon="your-site", check = is_current_site),
                               IM("All Sites",icon="all-sites")),
                          IM("Sent Shipments", c="inv", f="sent", args="summary",
                             icon="sent_shipments",
                             description=T("List of sent shipments."),
                             )(IM("Your Site",icon="your-site", check = is_current_site),
                               IM("All Sites",icon="all-sites")),
                          IM("Warehouse", c="inv", f="warehouse", args="summary",
                             icon="warehouse",
                             description=T("List of Warehouses."),
                             )(IM("View",args="summary",icon="list"),
                               IM("Create",args="create",icon="create"))
                          )

        return dict(current_site = current_site,
                    index_menu = index_menu)
    settings.customise_inv_home = customise_inv_index
    # -------------------------------------------------------------------------
    def customise_inv_recv_controller(**attr):
        s3 = current.response.s3
        # Custom PreP
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False

            # Customise titles 
            if r.vars.get("recv.status") == "2":
                s3.crud_strings.inv_recv.title_list = T("Existing Shipments to Received")
            if r.vars.get("recv.status__ne") == "2":
                s3.crud_strings.inv_recv.title_list = T("Received Shipments")
            return True
        s3.prep = custom_prep
        return attr
    settings.customise_inv_recv_controller = customise_inv_recv_controller

    # -------------------------------------------------------------------------
    # Comment/uncomment modules here to disable/enable them
    # Modules menu is defined in modules/eden/menu.py
    settings.modules = OrderedDict([
        # Core modules which shouldn't be disabled
        ("default", Storage(
            name_nice = T("Home"),
            restricted = False, # Use ACLs to control access to this module
            access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
            module_type = None  # This item is not shown in the menu
        )),
        ("admin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
        ("appadmin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
            module_type = None  # No Menu
        )),
        ("errors", Storage(
            name_nice = T("Ticket Viewer"),
            #description = "Needed for Breadcrumbs",
            restricted = False,
            module_type = None  # No Menu
        )),
        #("sync", Storage(
        #    name_nice = T("Synchronization"),
        #    #description = "Synchronization",
        #    restricted = True,
        #    access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
        #    module_type = None  # This item is handled separately for the menu
        #)),
        #("tour", Storage(
        #    name_nice = T("Guided Tour Functionality"),
        #    module_type = None,
        #)),
        #("translate", Storage(
        #    name_nice = T("Translation Functionality"),
        #    #description = "Selective translation of strings based on module.",
        #    module_type = None,
        #)),
        ("gis", Storage(
            name_nice = T("Map"),
            #description = "Situation Awareness & Geospatial Analysis",
            restricted = True,
            module_type = 6,     # 6th item in the menu
        )),
        ("pr", Storage(
            name_nice = T("Person Registry"),
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = None
        )),
        ("org", Storage(
            name_nice = T("Organizations"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = 1
        )),
        ("hrm", Storage(
            name_nice = T("Staff"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = 10,
        )),
        ("vol", Storage(
            name_nice = T("Volunteers"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = 2,
        )),
        ("cms", Storage(
          name_nice = T("Content Management"),
          #description = "Content Management System",
          restricted = True,
          module_type = None,
        )),
        #("doc", Storage(
        #    name_nice = T("Documents"),
        #    #description = "A library of digital resources, such as photos, documents and reports",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("msg", Storage(
        #    name_nice = T("Messaging"),
        #    #description = "Sends & Receives Alerts via Email & SMS",
        #    restricted = True,
        #    # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
        #    module_type = None,
        #)),
        # Needed for Req
        ("supply", Storage(
            name_nice = T("Supply Chain Management"),
            #description = "Used within Inventory Management, Request Management and Asset Management",
            restricted = True,
            module_type = None, # Not displayed
        )),
        ("inv", Storage(
            name_nice = T("Warehouses"),
            #description = "Receiving and Sending Items",
            restricted = True,
            module_type = 4
        )),
        #("asset", Storage(
        #    name_nice = T("Assets"),
        #    #description = "Recording and Assigning Assets",
        #    restricted = True,
        #    module_type = 5,
        #)),
        # Vehicle depends on Assets
        #("vehicle", Storage(
        #    name_nice = T("Vehicles"),
        #    #description = "Manage Vehicles",
        #    restricted = True,
        #    module_type = 10,
        #)),
        ("req", Storage(
            name_nice = T("Requests"),
            #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
            restricted = True,
            module_type = 10,
        )),
        ("project", Storage(
            name_nice = T("Projects"),
            #description = "Tracking of Projects, Activities and Tasks",
            restricted = True,
            module_type = 10
        )),
        ("cr", Storage(
            name_nice = T("Shelters"),
            #description = "Tracks the location, capacity and breakdown of victims in Shelters",
            restricted = True,
            module_type = 10
        )),
        ("hms", Storage(
            name_nice = T("Hospitals"),
            #description = "Helps to monitor status of hospitals",
            restricted = True,
            module_type = 3
        )),
        ("patient", Storage(
            name_nice = T("Patients"),
            #description = "Tracking of Patients",
            restricted = True,
            module_type = 10
        )),
        #("dvr", Storage(
        #   name_nice = T("Disaster Victim Registry"),
        #   #description = "Allow affected individuals & households to register to receive compensation and distributions",
        #   restricted = True,
        #   module_type = 10,
        #)),
        ("event", Storage(
            name_nice = T("Events"),
            #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
            restricted = True,
            module_type = 10,
        )),
        #("transport", Storage(
        #   name_nice = T("Transport"),
        #   restricted = True,
        #   module_type = 10,
        #)),
        ("stats", Storage(
            name_nice = T("Statistics"),
            #description = "Manages statistics",
            restricted = True,
            module_type = None,
        )),
    ])

# END =========================================================================