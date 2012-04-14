# -*- coding: utf-8 -*-

"""
    Deployment settings
    All settings which are typically edited for a deployment should be done here
    Deployers shouldn't typically need to edit any other files.
    NOTE FOR DEVELOPERS:
    /models/000_config.py is NOT in the Git repository, as this file will be changed
    during deployments.
    To for changes to be committed to trunk, please also edit:
    deployment-templates/models/000_config.py
"""

# Remind admin to edit this file
FINISHED_EDITING_CONFIG_FILE = False # change to True after you finish editing this file

# Database settings
deployment_settings.database.db_type = "sqlite"
deployment_settings.database.host = "localhost"
deployment_settings.database.port = None # use default
deployment_settings.database.database = "sahana"
deployment_settings.database.username = "sahana"
deployment_settings.database.password = "password" # NB Web2Py doesn't like passwords with an @ in them
deployment_settings.database.pool_size = 30

# Authentication settings
# This setting should be changed _before_ registering the 1st user
deployment_settings.auth.hmac_key = "akeytochange"
# These settings should be changed _after_ the 1st (admin) user is
# registered in order to secure the deployment
# Should users be allowed to register themselves?
deployment_settings.security.self_registration = True
deployment_settings.auth.registration_requires_verification = False
deployment_settings.auth.registration_requires_approval = False

# The name of the teams that users are added to when they opt-in to receive alerts
#deployment_settings.auth.opt_in_team_list = ["Updates"]
# Uncomment this to set the opt in default to True
#deployment_settings.auth.opt_in_default = True
# Uncomment this to request the Mobile Phone when a user registers
#deployment_settings.auth.registration_requests_mobile_phone = True
# Uncomment this to have the Mobile Phone selection during registration be mandatory
#deployment_settings.auth.registration_mobile_phone_mandatory = True
# Uncomment this to request the Organisation when a user registers
#deployment_settings.auth.registration_requests_organisation = True
# Uncomment this to have the Organisation selection during registration be mandatory
#deployment_settings.auth.registration_organisation_mandatory = True
# Uncomment this to have the Organisation input hidden unless the user enters a non-whitelisted domain
#deployment_settings.auth.registration_organisation_hidden = True
# Uncomment this to default the Organisation during registration
#deployment_settings.auth.registration_organisation_default = "My Organisation"
# Uncomment & populate these to set the default roelsd assigned to newly-registered users
#deployment_settings.auth.registration_roles = ["STAFF", "PROJECT_EDIT"]
# Uncomment this to request an image when users register
#deployment_settings.auth.registration_requests_image = True
# Uncomment this to direct newly-registered users to their volunteer page to be able to add extra details
# NB This requires Verification/Approval to be Off
# @ToDo: Extend to all optional Profile settings: Homepage, Twitter, Facebook, Mobile Phone, Image
#deployment_settings.auth.registration_volunteer = True
# Uncomment this to allow users to Login using Gmail's SMTP
#deployment_settings.auth.gmail_domains = ["gmail.com"]
# Fill these to allow users to Login using Facebook
# https://developers.facebook.com/apps
#deployment_settings.auth.facebook_id = ""
#deployment_settings.auth.facebook_secret = ""
# Fill these to allow users to Login using Google
# https://code.google.com/apis/console/
#deployment_settings.auth.google_id = ""
#deployment_settings.auth.google_secret = ""
# Uncomment this to allow users to Login using OpenID
#deployment_settings.auth.openid = True

# Always notify the approver of a new (verified) user, even if the user is automatically approved
deployment_settings.auth.always_notify_approver = True

# Base settings
deployment_settings.base.system_name = T("Sahana Eden Humanitarian Management Platform")
deployment_settings.base.system_name_short = T("Sahana Eden")

# Set this to the Public URL of the instance
deployment_settings.base.public_url = "http://127.0.0.1:8000"

# Switch to "False" in Production for a Performance gain
# (need to set to "True" again when Table definitions are changed)
deployment_settings.base.migrate = True
# To just create the .table files:
#deployment_settings.base.fake_migrate = True

# Enable/disable pre-population of the database.
# Should be non-zero on 1st_run to pre-populate the database
# - unless doing a manual DB migration
# Then set to zero in Production (to save 1x DAL hit every page)
# NOTE: the web UI will not be accessible while the DB is empty,
# instead run:
#   python web2py.py -N -S eden -M
# to create the db structure, then exit and re-import the data.
# This is a simple status flag with the following meanings
# 0 - No pre-population
# 1 - Base data entered in the database
# 2 - Regression (data used by the regression tests)
# 3 - Scalability testing
# 4-9 Reserved
# 10 - User (data required by the user typically for specialised test)
# 11-19 Reserved
# 20+ Demo (Data required for a default demo)
#     Each subsequent Demos can take any unique number >= 20
#     The actual demo will be defined by the file demo_folders.cfg
deployment_settings.base.prepopulate = 1


# Set this to True to use Content Delivery Networks to speed up Internet-facing sites
deployment_settings.base.cdn = False

# Set this to True to switch to Debug mode
# Debug mode means that uncompressed CSS/JS files are loaded
# JS Debug messages are also available in the Console
# can also load an individual page in debug mode by appending URL with
# ?debug=1
deployment_settings.base.debug = False

# Email settings
# Outbound server
deployment_settings.mail.server = "127.0.0.1:25"
#deployment_settings.mail.tls = True
# Useful for Windows Laptops:
#deployment_settings.mail.server = "smtp.gmail.com:587"
#deployment_settings.mail.tls = True
#deployment_settings.mail.login = "username:password"
# From Address
deployment_settings.mail.sender = "'Sahana' <sahana@your.org>"
# Default email address to which requests to approve new user accounts gets sent
# This can be overridden for specific domains/organisations via the auth_domain table
deployment_settings.mail.approver = "useradmin@your.org"
# Daily Limit on Sending of emails
#deployment_settings.mail.limit = 1000

# Frontpage settings
# RSS feeds
deployment_settings.frontpage.rss = [
    {"title": "Eden",
     # Trac timeline
     "url": "http://eden.sahanafoundation.org/timeline?ticket=on&changeset=on&milestone=on&wiki=on&max=50&daysback=90&format=rss"
    },
    {"title": "Twitter",
     # @SahanaFOSS
     # Find ID via http://api.twitter.com/users/show/username.json
     "url": "http://twitter.com/statuses/user_timeline/96591754.rss"
     # Hashtag
     #url: "http://search.twitter.com/search.atom?q=%23eqnz"
    }
]

# L10n settings
#deployment_settings.L10n.default_country_code = 1
# Languages used in the deployment (used for Language Toolbar & GIS Locations)
# http://www.loc.gov/standards/iso639-2/php/code_list.php
deployment_settings.L10n.languages = OrderedDict([
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
])
# Default language for Language Toolbar (& GIS Locations in future)
deployment_settings.L10n.default_language = "en"
# Display the language toolbar
deployment_settings.L10n.display_toolbar = True
# Default timezone for users
deployment_settings.L10n.utc_offset = "UTC +0000"
# Uncomment these to use US-style dates in English (localisations can still convert to local format)
#deployment_settings.L10n.date_format = T("%m-%d-%Y")
#deployment_settings.L10n.time_format = T("%H:%M:%S")
#deployment_settings.L10n.datetime_format = T("%m-%d-%Y %H:%M:%S")
# Religions used in Person Registry
# @ToDo: find a better code
# http://eden.sahanafoundation.org/ticket/594
deployment_settings.L10n.religions = {
    "none":T("none"),
    "christian":T("Christian"),
    "muslim":T("Muslim"),
	"jewish":T("Jewish"),
    "buddhist":T("Buddhist"),
    "hindu":T("Hindu"),
    "bahai":T("Bahai"),
    "other":T("other")
}
# Make last name in person/user records mandatory
#deployment_settings.L10n.mandatory_lastname = True

# Number formats (defaults to ISO 31-0)
# Decimal separator for numbers (defaults to ,)
deployment_settings.L10n.decimal_separator = "."
# Thousands separator for numbers (defaults to space)
#deployment_settings.L10n.thousands_separator = ","

# Finance settings
#deployment_settings.fin.currencies = {
#    "USD" :T("United States Dollars"),
#    "EUR" :T("Euros"),
#    "GBP" :T("Great British Pounds")
#}
#deployment_settings.fin.currency_default = "USD" # Dollars
#deployment_settings.fin.currency_writable = False # False currently breaks things

# PDF settings
# Default page size for reports (defaults to A4)
#deployment_settings.base.paper_size = T("Letter")
# Location of Logo used in pdfs headers
#deployment_settings.ui.pdf_logo = "static/img/mylogo.png"

# GIS (Map) settings
# Size of the Embedded Map
# Change this if-required for your theme
# NB API can override this in specific modules
#deployment_settings.gis.map_height = 600
#deployment_settings.gis.map_width = 1000
# Restrict the Location Selector to just certain countries
# NB This can also be over-ridden for specific contexts later
# e.g. Activities filtered to those of parent Project
#deployment_settings.gis.countries = ["US"]
# Hide the Map-based selection tool in the Location Selector
#deployment_settings.gis.map_selector = False
# Hide LatLon boxes in the Location Selector
#deployment_settings.gis.latlon_selector = False
# Use Building Names as a separate field in Street Addresses?
#deployment_settings.gis.building_name = False
# Display Resources recorded to Admin-Level Locations on the map
# @ToDo: Move into gis_config?
deployment_settings.gis.display_L0 = False
# Currently unused
#deployment_settings.gis.display_L1 = True
# Set this if there will be multiple areas in which work is being done,
# and a menu to select among them is wanted. With this on, any map
# configuration that is designated as being available in the menu will appear
#deployment_settings.gis.menu = T("Maps")
# Maximum Marker Size
# (takes effect only on display)
#deployment_settings.gis.marker_max_height = 35
#deployment_settings.gis.marker_max_width = 30
# Duplicate Features so that they show wrapped across the Date Line?
# Points only for now
# lon<0 have a duplicate at lon+360
# lon>0 have a duplicate at lon-360
#deployment_settings.gis.duplicate_features = True
# Mouse Position: 'normal', 'mgrs' or 'off'
#deployment_settings.gis.mouse_position = "mgrs"
# Print Service URL: http://eden.sahanafoundation.org/wiki/BluePrintGISPrinting
#deployment_settings.gis.print_service = "/geoserver/pdf/"
# Do we have a spatial DB available? (currently supports PostGIS. Spatialite to come.)
#deployment_settings.gis.spatialdb = True
# Bing API Key (for Map layers)
#deployment_settings.gis.api_bing = ""
# Google API Key (for Earth & MapMaker Layers)
# default works for localhost
#deployment_settings.gis.api_google = ""
# Yahoo API Key (for Geocoder)
#deployment_settings.gis.api_yahoo = ""
# GeoServer (Currently used by GeoExplorer. Will allow REST control of GeoServer.)
# NB Needs to be publically-accessible URL for querying via client JS
#deployment_settings.gis.geoserver_url = "http://localhost/geoserver"
#deployment_settings.gis.geoserver_username = "admin"
#deployment_settings.gis.geoserver_password = ""

# Twitter settings:
# Register an app at http://twitter.com/apps
# (select Aplication Type: Client)
# You'll get your consumer_key and consumer_secret from Twitter
#deployment_settings.twitter.oauth_consumer_key = ""
#deployment_settings.twitter.oauth_consumer_secret = ""

# Use 'soft' deletes
#deployment_settings.security.archive_not_delete = False

# AAA Settings

# Security Policy
# http://eden.sahanafoundation.org/wiki/S3AAA#System-widePolicy
# 1: Simple (default): Global as Reader, Authenticated as Editor
# 2: Editor role required for Update/Delete, unless record owned by session
# 3: Apply Controller ACLs
# 4: Apply both Controller & Function ACLs
# 5: Apply Controller, Function & Table ACLs
# 6: Apply Controller, Function, Table & Organisation ACLs
#
#deployment_settings.security.policy = 6 # Organisation-ACLs
#acl = deployment_settings.aaa.acl
#deployment_settings.aaa.default_uacl =  acl.READ   # User ACL
#deployment_settings.aaa.default_oacl =  acl.CREATE | acl.READ | acl.UPDATE # Owner ACL

# Lock-down access to Map Editing
#deployment_settings.security.map = True
# Allow non-MapAdmins to edit hierarchy locations? Defaults to True if not set.
# (Permissions can be set per-country within a gis_config)
#deployment_settings.gis.edit_Lx = False
# Allow non-MapAdmins to edit group locations? Defaults to False if not set.
#deployment_settings.gis.edit_GR = True
# Note that editing of locations used as regions for the Regions menu is always
# restricted to MapAdmins.

# Audit settings
# We Audit if either the Global or Module asks us to
# (ignore gracefully if module author hasn't implemented this)
# NB Auditing (especially Reads) slows system down & consumes diskspace
#deployment_settings.security.audit_write = False
#deployment_settings.security.audit_read = False

# UI/Workflow options
# Should user be prompted to save before navigating away?
#deployment_settings.ui.navigate_away_confirm = False
# Should user be prompted to confirm actions?
#deployment_settings.ui.confirm = False
# Should potentially large dropdowns be turned into autocompletes?
# (unused currently)
#deployment_settings.ui.autocomplete = True
#deployment_settings.ui.update_label = "Edit"
# Enable this for a UN-style deployment
#deployment_settings.ui.cluster = True
# Enable this to use the label 'Camp' instead of 'Shelter'
#deployment_settings.ui.camp = True
# Enable this to change the label for 'Mobile Phone'
#deployment_settings.ui.label_mobile_phone = T("Cell Phone")
# Enable this to change the label for 'Postcode'
#deployment_settings.ui.label_postcode = T("ZIP Code")
# Enable Social Media share buttons
#deployment_settings.ui.social_buttons = True

# Request
#deployment_settings.req.type_inv_label = T("Donations")
#deployment_settings.req.type_hrm_label = T("Volunteers")
# Allow the status for requests to be set manually,
# rather than just automatically from commitments and shipments
#deployment_settings.req.status_writable = False
#deployment_settings.req.quantities_writable = True
#deployment_settings.req.show_quantity_transit = False
#deployment_settings.req.multiple_req_items = False
#deployment_settings.req.use_commit = False
#deployment_settings.req.use_req_number = False
# Restrict the type of requests that can be made, valid values in the
# list are ["Stock", "People", "Other"]. If this is commented out then
# all types will be valid.
#deployment_settings.req.req_type = ["Stock"]

# Custom Crud Strings for specific req_req types
#deployment_settings.req.req_crud_strings = dict()
#ADD_ITEM_REQUEST = T("Make a Request for Donations")
#LIST_ITEM_REQUEST = T("List Requests for Donations")
# req_req Crud Strings for Item Request (type=1)
#deployment_settings.req.req_crud_strings[1] = Storage(
#    title_create = ADD_ITEM_REQUEST,
#    title_display = T("Request for Donations Details"),
#    title_list = LIST_ITEM_REQUEST,
#    title_update = T("Edit Request for Donations"),
#    title_search = T("Search Requests for Donations"),
#    subtitle_create = ADD_ITEM_REQUEST,
#    subtitle_list = T("Requests for Donations"),
#    label_list_button = LIST_ITEM_REQUEST,
#    label_create_button = ADD_ITEM_REQUEST,
#    label_delete_button = T("Delete Request for Donations"),
#    msg_record_created = T("Request for Donations Added"),
#    msg_record_modified = T("Request for Donations Updated"),
#    msg_record_deleted = T("Request for Donations Canceled"),
#    msg_list_empty = T("No Requests for Donations"))
#ADD_PEOPLE_REQUEST = T("Make a Request for Volunteers")
#LIST_PEOPLE_REQUEST = T("List Requests for Volunteers")
# req_req Crud Strings for People Request (type=3)
#deployment_settings.req.req_crud_strings[3] = Storage(
#    title_create = ADD_PEOPLE_REQUEST,
#    title_display = T("Request for Volunteers Details"),
#    title_list = LIST_PEOPLE_REQUEST,
#    title_update = T("Edit Request for Volunteers"),
#    title_search = T("Search Requests for Volunteers"),
#    subtitle_create = ADD_PEOPLE_REQUEST,
#    subtitle_list = T("Requests for Volunteers"),
#    label_list_button = LIST_PEOPLE_REQUEST,
#    label_create_button = ADD_PEOPLE_REQUEST,
#    label_delete_button = T("Delete Request for Volunteers"),
#    msg_record_created = T("Request for Volunteers Added"),
#    msg_record_modified = T("Request for Volunteers Updated"),
#    msg_record_deleted = T("Request for Volunteers Canceled"),
#    msg_list_empty = T("No Requests for Volunteers"))

# Inventory Management
#deployment_settings.inv.collapse_tabs = False
# Use the term 'Order' instead of 'Shipment'
#deployment_settings.inv.shipment_name = "order"

# Supply
#deployment_settings.supply.use_alt_name = False
# Do not edit after deployment
#deployment_settings.supply.catalog_default = T("Other Items")

# Organsiation Management
# Set the length of the auto-generated org/site code the default is 10
#deployment_settings.org.site_code_len = 3

# Human Resource Management
# Uncomment to allow Staff & Volunteers to be registered without an email address
#deployment_settings.hrm.email_required = False
# Uncomment to hide the Staff resource
#deployment_settings.hrm.show_staff = False
# Uncomment to hide the Volunteer resource
#deployment_settings.hrm.show_vols = False
# Uncomment to allow hierarchical categories of Skills, which each need their own set of competency levels.
#deployment_settings.hrm.skill_types = True

# Project Tracking
# Uncomment this to use settings suitable for a global/regional organisation (e.g. DRR)
#deployment_settings.project.drr = True
# Uncomment this to use Milestones in project/task.
#deployment_settings.project.milestones = True

# Save Search Widget
#deployment_settings.save_search.widget = False

# Terms of Service to be able to Register on the system
#deployment_settings.options.terms_of_service = T("Terms of Service\n\nYou have to be eighteen or over to register as a volunteer.")

# Comment/uncomment modules here to disable/enable them
# @ToDo: have the system automatically enable migrate if a module is enabled
# Modules menu is defined in 01_menu.py
deployment_settings.modules = OrderedDict([
    # Core modules which shouldn't be disabled
    ("default", Storage(
            name_nice = T("Home"),
            restricted = False, # Use ACLs to control access to this module
            access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
            module_type = None  # This item is not shown in the menu
        )),
    ("admin", Storage(
            name_nice = T("Administration"),
            description = T("Site Administration"),
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
    ("appadmin", Storage(
            name_nice = T("Administration"),
            description = T("Site Administration"),
            restricted = True,
            module_type = None  # No Menu
        )),
    ("errors", Storage(
            name_nice = T("Ticket Viewer"),
            description = T("Needed for Breadcrumbs"),
            restricted = False,
            module_type = None  # No Menu
        )),
    ("sync", Storage(
            name_nice = T("Synchronization"),
            description = T("Synchronization"),
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
     # Uncomment to enable internal support requests
     #("support", Storage(
     #        name_nice = T("Support"),
     #        description = T("Support Requests"),
     #        restricted = True,
     #        module_type = None  # This item is handled separately for the menu
     #    )),
     ("gis", Storage(
            name_nice = T("Map"),
            description = T("Situation Awareness & Geospatial Analysis"),
            restricted = True,
            module_type = 6,     # 6th item in the menu
        )),
    ("pr", Storage(
            name_nice = T("Person Registry"),
            description = T("Central point to record details on People"),
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = 10
        )),
    ("org", Storage(
            name_nice = T("Organizations"),
            description = T('Lists "who is doing what & where". Allows relief agencies to coordinate their activities'),
            restricted = True,
            module_type = 1
        )),
    # All modules below here should be possible to disable safely
    ("hrm", Storage(
            name_nice = T("Staff & Volunteers"),
            description = T("Human Resource Management"),
            restricted = True,
            module_type = 2,
        )),
    ("doc", Storage(
            name_nice = T("Documents"),
            description = T("A library of digital resources, such as photos, documents and reports"),
            restricted = True,
            module_type = 10,
        )),
    ("msg", Storage(
            name_nice = T("Messaging"),
            description = T("Sends & Receives Alerts via Email & SMS"),
            restricted = True,
            # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
            module_type = None,
        )),
    ("supply", Storage(
            name_nice = T("Supply Chain Management"),
            description = T("Used within Inventory Management, Request Management and Asset Management"),
            restricted = True,
            module_type = None, # Not displayed
        )),
    ("inv", Storage(
            name_nice = T("Warehouse"),
            description = T("Receiving and Sending Items"),
            restricted = True,
            module_type = 4
        )),
    #("proc", Storage(
    #        name_nice = T("Procurement"),
    #        description = T("Ordering & Purchasing of Goods & Services"),
    #        restricted = True,
    #        module_type = 10
    #    )),
    ("asset", Storage(
            name_nice = T("Assets"),
            description = T("Recording and Assigning Assets"),
            restricted = True,
            module_type = 5,
        )),
    # Vehicle depends on Assets
    ("vehicle", Storage(
            name_nice = T("Vehicles"),
            description = T("Manage Vehicles"),
            restricted = True,
            module_type = 10,
        )),
    ("req", Storage(
            name_nice = T("Requests"),
            description = T("Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested."),
            restricted = True,
            module_type = 10,
        )),
    ("project", Storage(
            name_nice = T("Projects"),
            description = T("Tracking of Projects, Activities and Tasks"),
            restricted = True,
            module_type = 2
        )),
    ("survey", Storage(
            name_nice = T("Surveys"),
            description = T("Create, enter, and manage surveys."),
            restricted = True,
            module_type = 5,
        )),
    ("cr", Storage(
            name_nice = T("Shelters"),
            description = T("Tracks the location, capacity and breakdown of victims in Shelters"),
            restricted = True,
            module_type = 10
        )),
    ("hms", Storage(
            name_nice = T("Hospitals"),
            description = T("Helps to monitor status of hospitals"),
            restricted = True,
            module_type = 10
        )),
    ("irs", Storage(
            name_nice = T("Incidents"),
            description = T("Incident Reporting System"),
            restricted = False,
            module_type = 10
        )),
    #("impact", Storage(
    #        name_nice = T("Impacts"),
    #        description = T("Used by Assess"),
    #        restricted = True,
    #        module_type = None,
    #    )),
    # Assess currently depends on CR, IRS & Impact
    # Deprecated by Surveys module
    #("assess", Storage(
    #        name_nice = T("Assessments"),
    #        description = T("Rapid Assessments & Flexible Impact Assessments"),
    #        restricted = True,
    #        module_type = 10,
    #    )),
    ("scenario", Storage(
            name_nice = T("Scenarios"),
            description = T("Define Scenarios for allocation of appropriate Resources (Human, Assets & Facilities)."),
            restricted = True,
            module_type = 10,
        )),
    ("event", Storage(
            name_nice = T("Events"),
            description = T("Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities)."),
            restricted = True,
            module_type = 10,
        )),
    # NB Budget module depends on Project Tracking Module
    # @ToDo: Rewrite in a modern style
    #("budget", Storage(
    #        name_nice = T("Budgeting Module"),
    #        description = T("Allows a Budget to be drawn up"),
    #        restricted = True,
    #        module_type = 10
    #    )),
    # @ToDo: Port these Assessments to the Survey module
    #("building", Storage(
    #        name_nice = T("Building Assessments"),
    #        description = T("Building Safety Assessments"),
    #        restricted = True,
    #        module_type = 10,
    #    )),
    # These are specialist modules
    # Requires RPy2
    #("climate", Storage(
    #    name_nice = T("Climate"),
    #    description = T("Climate data portal"),
    #    restricted = True,
    #    module_type = 10,
    #)),
    #("delphi", Storage(
    #        name_nice = T("Delphi Decision Maker"),
    #        description = T("Supports the decision making of large groups of Crisis Management Experts by helping the groups create ranked list."),
    #        restricted = False,
    #        module_type = 10,
    #    )),
    ("dvi", Storage(
           name_nice = T("Disaster Victim Identification"),
           description = T("Disaster Victim Identification"),
           restricted = True,
           module_type = 10,
           #access = "|DVI|",      # Only users with the DVI role can see this module in the default menu & access the controller
           #audit_read = True,     # Can enable Audit for just an individual module here
           #audit_write = True
       )),
    ("mpr", Storage(
           name_nice = T("Missing Person Registry"),
           description = T("Helps to report and search for missing persons"),
           restricted = False,
           module_type = 10,
       )),
    ("cms", Storage(
          name_nice = T("Content Management"),
          description = T("Content Management System"),
          restricted = True,
          module_type = 10,
      )),
    ("member", Storage(
           name_nice = T("Members"),
           description = T("Membership Management System"),
           restricted = True,
           module_type = 10,
       )),
    #("fire", Storage(
    #       name_nice = T("Fire Stations"),
    #       description = T("Fire Station Management"),
    #       restricted = True,
    #       module_type = 1,
    #   )),
    #("patient", Storage(
    #        name_nice = T("Patient Tracking"),
    #        description = T("Tracking of Patients"),
    #        restricted = True,
    #        module_type = 10
    #    )),
    #("ocr", Storage(
    #       name_nice = T("Optical Character Recognition"),
    #       description = T("Optical Character Recognition for reading the scanned handwritten paper forms."),
    #       restricted = False,
    #       module_type = 10
    #   )),
    # This module has very limited functionality
    #("flood", Storage(
    #        name_nice = T("Flood Alerts"),
    #        description = T("Flood Alerts show water levels in various parts of the country"),
    #        restricted = False,
    #        module_type = 10
    #    )),
])
