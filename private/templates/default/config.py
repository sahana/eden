# -*- coding: utf-8 -*-

from gluon import current
from gluon.storage import Storage
from gluon.contrib.simplejson.ordered_dict import OrderedDict
settings = current.deployment_settings
T = current.T

"""
    Template settings

    All settings which are to configure a specific template are located here

    Deployers should ideally not need to edit any other files outside of their template folder
"""

# Pre-Populate
# http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/PrePopulate
# Configure/disable pre-population of the database.
# To pre-populate the database On 1st run should specify directory(s) in
# /private/templates/
# eg:
# ["default"] (1 is a shortcut for this)
# ["Standard"]
# ["IFRC_Train"]
# ["roles", "user"]
# Unless doing a manual DB migration, where prepopulate = 0
# In Production, prepopulate = 0 (to save 1x DAL hit every page)
#settings.base.prepopulate = 1

# Theme (folder to use for views/layout.html)
#settings.base.theme = "default"

# Authentication settings
# These settings should be changed _after_ the 1st (admin) user is
# registered in order to secure the deployment
# Should users be allowed to register themselves?
#settings.security.self_registration = False
# Do new users need to verify their email address?
#settings.auth.registration_requires_verification = True
# Do new users need to be approved by an administrator prior to being able to login?
#settings.auth.registration_requires_approval = True
# Always notify the approver of a new (verified) user, even if the user is automatically approved
#settings.auth.always_notify_approver = False

# The name of the teams that users are added to when they opt-in to receive alerts
#settings.auth.opt_in_team_list = ["Updates"]
# Uncomment this to set the opt in default to True
#settings.auth.opt_in_default = True
# Uncomment this to request the Mobile Phone when a user registers
#settings.auth.registration_requests_mobile_phone = True
# Uncomment this to have the Mobile Phone selection during registration be mandatory
#settings.auth.registration_mobile_phone_mandatory = True
# Uncomment this to request the Organisation when a user registers
#settings.auth.registration_requests_organisation = True
# Uncomment this to have the Organisation selection during registration be mandatory
#settings.auth.registration_organisation_required = True
# Uncomment this to have the Organisation input hidden unless the user enters a non-whitelisted domain
#settings.auth.registration_organisation_hidden = True
# Uncomment this to default the Organisation during registration
#settings.auth.registration_organisation_default = "My Organisation"
# Uncomment to set the default role UUIDs assigned to newly-registered users
# This is a dictionary of lists, where the key is the realm that the list of roles applies to
# The key 0 implies not realm restricted
# The keys "organisation_id" and "site_id" can be used to indicate the user's "organisation_id" and "site_id"
#settings.auth.registration_roles = { 0: ["STAFF", "PROJECT_EDIT"]}
# Uncomment this to enable record approval
#settings.auth.record_approval = True
# Uncomment this and specify a list of tablenames for which record approval is required
#settings.auth.record_approval_required_for = ["project_project"]
# Uncomment this to request an image when users register
#settings.auth.registration_requests_image = True
# Uncomment this to direct newly-registered users to their volunteer page to be able to add extra details
# NB This requires Verification/Approval to be Off
# @ToDo: Extend to all optional Profile settings: Homepage, Twitter, Facebook, Mobile Phone, Image
#settings.auth.registration_volunteer = True
# Uncomment this to allow users to Login using Gmail's SMTP
#settings.auth.gmail_domains = ["gmail.com"]
# Uncomment this to allow users to Login using OpenID
#settings.auth.openid = True

# L10n settings
# Languages used in the deployment (used for Language Toolbar & GIS Locations)
# http://www.loc.gov/standards/iso639-2/php/code_list.php
#settings.L10n.languages = OrderedDict([
#    ("ar", "العربية"),
#    ("zh-cn", "中文 (简体)"),
#    ("zh-tw", "中文 (繁體)"),
#    ("en", "English"),
#    ("fr", "Français"),
#    ("de", "Deutsch"),
#    ("el", "ελληνικά"),
#    ("it", "Italiano"),
#    ("ja", "日本語"),
#    ("ko", "한국어"),
#    ("pt", "Português"),
#    ("pt-br", "Português (Brasil)"),
#    ("ru", "русский"),
#    ("es", "Español"),
#    ("tl", "Tagalog"),
#    ("ur", "اردو"),
#    ("vi", "Tiếng Việt"),
#])
# Default language for Language Toolbar (& GIS Locations in future)
#settings.L10n.default_language = "en"
# Uncomment to Hide the language toolbar
#settings.L10n.display_toolbar = False
# Default timezone for users
#settings.L10n.utc_offset = "UTC +0000"
# Uncomment these to use US-style dates in English (localisations can still convert to local format)
#settings.L10n.date_format = T("%m-%d-%Y")
#settings.L10n.time_format = T("%H:%M:%S")
#settings.L10n.datetime_format = T("%m-%d-%Y %H:%M:%S")
# Number formats (defaults to ISO 31-0)
# Decimal separator for numbers (defaults to ,)
settings.L10n.decimal_separator = "."
# Thousands separator for numbers (defaults to space)
#settings.L10n.thousands_separator = ","
# Default Country Code for telephone numbers
#settings.L10n.default_country_code = 1
# Make last name in person/user records mandatory
#settings.L10n.mandatory_lastname = True

# Finance settings
#settings.fin.currencies = {
#    "EUR" : T("Euros"),
#    "GBP" : T("Great British Pounds"),
#    "USD" : T("United States Dollars"),
#}
#settings.fin.currency_default = "USD"
#settings.fin.currency_writable = False # False currently breaks things

# PDF settings
# Default page size for reports (defaults to A4)
#settings.base.paper_size = T("Letter")
# Location of Logo used in pdfs headers
#settings.ui.pdf_logo = "static/img/mylogo.png"

# GIS (Map) settings
# Size of the Embedded Map
# Change this if-required for your theme
# NB API can override this in specific modules
#settings.gis.map_height = 600
#settings.gis.map_width = 1000
# Restrict the Location Selector to just certain countries
# NB This can also be over-ridden for specific contexts later
# e.g. Activities filtered to those of parent Project
#settings.gis.countries = ["US"]
# Hide the Map-based selection tool in the Location Selector
#settings.gis.map_selector = False
# Hide LatLon boxes in the Location Selector
#settings.gis.latlon_selector = False
# Use Building Names as a separate field in Street Addresses?
#settings.gis.building_name = False
# Display Resources recorded to Admin-Level Locations on the map
# @ToDo: Move into gis_config?
# Uncomment to fall back to country LatLon to show resources, if nothing better available
#settings.gis.display_L0 = True
# Currently unused
#settings.gis.display_L1 = False
# Set this if there will be multiple areas in which work is being done,
# and a menu to select among them is wanted.
#settings.gis.menu = "Maps"
# Maximum Marker Size
# (takes effect only on display)
#settings.gis.marker_max_height = 35
#settings.gis.marker_max_width = 30
# Duplicate Features so that they show wrapped across the Date Line?
# Points only for now
# lon<0 have a duplicate at lon+360
# lon>0 have a duplicate at lon-360
#settings.gis.duplicate_features = True
# Mouse Position: 'normal', 'mgrs' or 'off'
#settings.gis.mouse_position = "mgrs"
# PoIs to export in KML/OSM feeds from Admin locations
#settings.gis.poi_resources = ["cr_shelter", "hms_hospital", "org_office"]

# Messaging Settings
# If you wish to use a parser.py in another folder than "default"
#settings.msg.parser = "mytemplatefolder"

# Use 'soft' deletes
#settings.security.archive_not_delete = False

# AAA Settings

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
#settings.security.policy = 7 # Organisation-ACLs

# Lock-down access to Map Editing
#settings.security.map = True
# Allow non-MapAdmins to edit hierarchy locations? Defaults to True if not set.
# (Permissions can be set per-country within a gis_config)
#settings.gis.edit_Lx = False
# Allow non-MapAdmins to edit group locations? Defaults to False if not set.
#settings.gis.edit_GR = True
# Note that editing of locations used as regions for the Regions menu is always
# restricted to MapAdmins.

# Enable this for a UN-style deployment
#settings.ui.cluster = True
# Enable this to use the label 'Camp' instead of 'Shelter'
#settings.ui.camp = True
# Enable this to change the label for 'Mobile Phone'
#settings.ui.label_mobile_phone = "Cell Phone"
# Enable this to change the label for 'Postcode'
#settings.ui.label_postcode = "ZIP Code"
# Enable Social Media share buttons
#settings.ui.social_buttons = True

# Organisation Management
# Set the length of the auto-generated org/site code the default is 10
#settings.org.site_code_len = 3
# Set the label for Sites
#settings.org.site_label = "Facility"
# Uncomment to add summary fields for Organisations/Offices for # National/International staff
#settings.org.summary = True
# Enable certain fields just for specific Organisations
# Requires a call to settings.set_org_dependent_field(field)
#settings.org.dependent_fields = \
#    {"<table name>.<field name>"  : ["<Organisation Name>"],
#    ...
#     }

# Human Resource Management
# Uncomment to allow Staff & Volunteers to be registered without an email address
#settings.hrm.email_required = False
# Uncomment to allow HR records to be deletable rather than just marking them as obsolete
#settings.hrm.deletable = True
# Uncomment to allow HRs to have multiple Job Roles in addition to their Job Title
#settings.hrm.job_roles = True
# Uncomment to hide the Staff resource
#settings.hrm.show_staff = False
# Uncomment to allow hierarchical categories of Skills, which each need their own set of competency levels.
#settings.hrm.skill_types = True
# Uncomment to disable Staff experience
#settings.hrm.staff_experience = False
# Uncomment to disable Volunteer experience
#settings.hrm.vol_experience = False
# Uncomment to show the Organisation name in HR represents
#settings.hrm.show_organisation = True
# Uncomment to disable the use of HR Certificates
#settings.hrm.use_certificates = False
# Uncomment to disable the use of HR Credentials
#settings.hrm.use_credentials = False
# Uncomment to disable the use of HR Description
#settings.hrm.use_description = False
# Uncomment to enable the use of HR Education
#settings.hrm.use_education = True
# Uncomment to disable the use of HR ID
#settings.hrm.use_id = False
# Uncomment to disable the use of HR Skills
#settings.hrm.use_skills = False
# Uncomment to disable the use of HR Teams
#settings.hrm.use_teams = False
# Uncomment to disable the use of HR Trainings
#settings.hrm.use_trainings = False

# Inventory Management
#settings.inv.collapse_tabs = False
# Use the term 'Order' instead of 'Shipment'
#settings.inv.shipment_name = "order"
#settings.inv.send_form_name = "Tally Out Sheet"
#settings.inv.send_short_name = "TO"
#settings.inv.send_ref_field_name = "Tally Out Number"
#settings.inv.recv_form_name = "Acknowledgement Receipt for Donations Received Form"
#settings.inv.recv_shortname = "ARDR"
#settings.inv.shipment_types = {
#         0: T("-"),
#         1: T("Other Warehouse"),
#         2: T("Donation"),
#         3: T("Foreign Donation"),
#         4: T("Local Purchases"),
#         5: T("Confiscated Goods from Bureau Of Customs")
#    }

# Requests Management
#settings.req.type_inv_label = T("Donations")
#settings.req.type_hrm_label = T("Volunteers")
# Allow the status for requests to be set manually,
# rather than just automatically from commitments and shipments
#settings.req.status_writable = False
#settings.req.quantities_writable = True
#settings.req.show_quantity_transit = False
#settings.req.multiple_req_items = False
#settings.req.use_commit = False
#settings.req.use_req_number = False
#settings.req.generate_req_number = False
#settings.req.req_form_name = "Request Issue Form"
#settings.req.req_shortname = "RIS"
# Restrict the type of requests that can be made, valid values in the
# list are ["Stock", "People", "Other"]. If this is commented out then
# all types will be valid.
#settings.req.req_type = ["Stock"]

# Custom Crud Strings for specific req_req types
#settings.req.req_crud_strings = dict()
#ADD_ITEM_REQUEST = T("Make a Request for Donations")
# req_req Crud Strings for Item Request (type=1)
#settings.req.req_crud_strings[1] = Storage(
#    title_create = ADD_ITEM_REQUEST,
#    title_display = T("Request for Donations Details"),
#    title_list = T("Requests for Donations"),
#    title_update = T("Edit Request for Donations"),
#    title_search = T("Search Requests for Donations"),
#    subtitle_create = ADD_ITEM_REQUEST,
#    label_list_button = T("List Requests for Donations"),
#    label_create_button = ADD_ITEM_REQUEST,
#    label_delete_button = T("Delete Request for Donations"),
#    msg_record_created = T("Request for Donations Added"),
#    msg_record_modified = T("Request for Donations Updated"),
#    msg_record_deleted = T("Request for Donations Canceled"),
#    msg_list_empty = T("No Requests for Donations"))
#ADD_PEOPLE_REQUEST = T("Make a Request for Volunteers")
# req_req Crud Strings for People Request (type=3)
#settings.req.req_crud_strings[3] = Storage(
#    title_create = ADD_PEOPLE_REQUEST,
#    title_display = T("Request for Volunteers Details"),
#    title_list = T("Requests for Volunteers"),
#    title_update = T("Edit Request for Volunteers"),
#    title_search = T("Search Requests for Volunteers"),
#    subtitle_create = ADD_PEOPLE_REQUEST,
#    label_list_button = T("List Requests for Volunteers"),
#    label_create_button = ADD_PEOPLE_REQUEST,
#    label_delete_button = T("Delete Request for Volunteers"),
#    msg_record_created = T("Request for Volunteers Added"),
#    msg_record_modified = T("Request for Volunteers Updated"),
#    msg_record_deleted = T("Request for Volunteers Canceled"),
#    msg_list_empty = T("No Requests for Volunteers"))

# Supply
#settings.supply.use_alt_name = False
# Do not edit after deployment
#settings.supply.catalog_default = T("Default")

# Projects
# Uncomment this to use settings suitable for a global/regional organisation (e.g. DRR)
#settings.project.mode_3w = True
# Uncomment this to use DRR (Disaster Risk Reduction) extensions
#settings.project.mode_drr = True
# Uncomment this to use settings suitable for detailed Task management
#settings.project.mode_task = True
# Uncomment this to call project locations 'Communities'
#settings.project.community = True
# Uncomment this to use Activities for projects
#settings.project.activities = True
# Uncomment this to use Codes for projects
#settings.project.codes = True
# Uncomment this to use Milestones in project/task.
#settings.project.milestones = True
# Uncomment this to disable Sectors in projects
#settings.project.sectors = False
# Uncomment this to use Theme Percentages for projects
#settings.project.theme_percentages = True
# Uncomment this to use multiple Budgets per project
#settings.project.multiple_budgets = True
# Uncomment this to use multiple Organisations per project
#settings.project.multiple_organisations = True
# Uncomment this to customise
#settings.project.organisation_roles = {
#    1: T("Lead Implementer"), # T("Host National Society")
#    2: T("Partner"), # T("Partner National Society")
#    3: T("Donor"),
#    4: T("Customer"), # T("Beneficiary")?
#    5: T("Super"), # T("Beneficiary")?
#}
#settings.project.organisation_lead_role = 1

# Incidents
# Uncomment this to use vehicles when responding to Incident Reports
#settings.irs.vehicle = True

# Save Search Widget
#settings.save_search.widget = False

# Terms of Service to be able to Register on the system
#settings.options.terms_of_service = T("Terms of Service\n\nYou have to be eighteen or over to register as a volunteer.")

# Comment/uncomment modules here to disable/enable them
# @ToDo: Have the system automatically enable migrate if a module is enabled
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
    ("sync", Storage(
            name_nice = T("Synchronization"),
            #description = "Synchronization",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
    ("translate", Storage(
            name_nice = T("Translation Functionality"),
            #description = "Selective translation of strings based on module.",
            module_type = None,
        )),
    # Uncomment to enable internal support requests
    #("support", Storage(
    #        name_nice = T("Support"),
    #        #description = "Support Requests",
    #        restricted = True,
    #        module_type = None  # This item is handled separately for the menu
    #    )),
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
            module_type = 10
        )),
    ("org", Storage(
            name_nice = T("Organizations"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = 1
        )),
    # All modules below here should be possible to disable safely
    ("hrm", Storage(
            name_nice = T("Staff"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = 2,
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
          module_type = 10,
      )),
    ("doc", Storage(
            name_nice = T("Documents"),
            #description = "A library of digital resources, such as photos, documents and reports",
            restricted = True,
            module_type = 10,
        )),
    ("msg", Storage(
            name_nice = T("Messaging"),
            #description = "Sends & Receives Alerts via Email & SMS",
            restricted = True,
            # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
            module_type = None,
        )),
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
    #("proc", Storage(
    #        name_nice = T("Procurement"),
    #        #description = "Ordering & Purchasing of Goods & Services",
    #        restricted = True,
    #        module_type = 10
    #    )),
    ("asset", Storage(
            name_nice = T("Assets"),
            #description = "Recording and Assigning Assets",
            restricted = True,
            module_type = 5,
        )),
    # Vehicle depends on Assets
    ("vehicle", Storage(
            name_nice = T("Vehicles"),
            #description = "Manage Vehicles",
            restricted = True,
            module_type = 10,
        )),
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
            module_type = 2
        )),
    ("survey", Storage(
            name_nice = T("Surveys"),
            #description = "Create, enter, and manage surveys.",
            restricted = True,
            module_type = 5,
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
            module_type = 10
        )),
    ("irs", Storage(
            name_nice = T("Incidents"),
            #description = "Incident Reporting System",
            restricted = True,
            module_type = 10
        )),
    ("dvi", Storage(
           name_nice = T("Disaster Victim Identification"),
           #description = "Disaster Victim Identification",
           restricted = True,
           module_type = 10,
           #access = "|DVI|",      # Only users with the DVI role can see this module in the default menu & access the controller
           #audit_read = True,     # Can enable Audit for just an individual module here
           #audit_write = True
       )),
    ("dvr", Storage(
           name_nice = T("Disaster Victim Registry"),
           #description = "Allow affected individuals & households to register to receive compensation and distributions",
           restricted = True,
           module_type = 10,
       )),
    ("transport", Storage(
           name_nice = T("Transport"),
           restricted = True,
           module_type = 10,
       )),
    #("mpr", Storage(
    #       name_nice = T("Missing Person Registry"),
    #       #description = "Helps to report and search for missing persons",
    #       restricted = True,
    #       module_type = 10,
    #   )),
    #("stats", Storage(
    #        name_nice = T("Statistics"),
    #        #description = "Manages statistics",
    #        restricted = True,
    #        module_type = None,
    #    )),
    #("vulnerability", Storage(
    #        name_nice = T("Vulnerability"),
    #        #description = "Manages vulnerability indicators",
    #        restricted = True,
    #        module_type = 10,
    #    )),
    #("event", Storage(
    #        name_nice = T("Events"),
    #        #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
    #        restricted = True,
    #        module_type = 10,
    #    )),
    #("scenario", Storage(
    #        name_nice = T("Scenarios"),
    #        #description = "Define Scenarios for allocation of appropriate Resources (Human, Assets & Facilities).",
    #        restricted = True,
    #        module_type = 10,
    #    )),
    #("fire", Storage(
    #       name_nice = T("Fire Stations"),
    #       #description = "Fire Station Management",
    #       restricted = True,
    #       module_type = 1,
    #   )),
    #("flood", Storage(
    #        name_nice = T("Flood Warnings"),
    #        #description = "Flood Gauges show water levels in various parts of the country",
    #        restricted = True,
    #        module_type = 10
    #    )),
    #("member", Storage(
    #       name_nice = T("Members"),
    #       #description = "Membership Management System",
    #       restricted = True,
    #       module_type = 10,
    #   )),
    #("patient", Storage(
    #        name_nice = T("Patient Tracking"),
    #        #description = "Tracking of Patients",
    #        restricted = True,
    #        module_type = 10
    #    )),
    #("security", Storage(
    #       name_nice = T("Security"),
    #       #description = "Security Management System",
    #       restricted = True,
    #       module_type = 10,
    #   )),
    # These are specialist modules
    #("cap", Storage(
    #        name_nice = T("CAP"),
    #        #description = "Create & broadcast CAP alerts",
    #        restricted = True,
    #        module_type = 10,
    #)),
    # Requires RPy2 & PostgreSQL
    #("climate", Storage(
    #        name_nice = T("Climate"),
    #        #description = "Climate data portal",
    #        restricted = True,
    #        module_type = 10,
    #)),
    #("delphi", Storage(
    #        name_nice = T("Delphi Decision Maker"),
    #        #description = "Supports the decision making of large groups of Crisis Management Experts by helping the groups create ranked list.",
    #        restricted = False,
    #        module_type = 10,
    #    )),
    # @ToDo: Rewrite in a modern style
    #("budget", Storage(
    #        name_nice = T("Budgeting Module"),
    #        #description = "Allows a Budget to be drawn up",
    #        restricted = True,
    #        module_type = 10
    #    )),
    # @ToDo: Port these Assessments to the Survey module
    #("building", Storage(
    #        name_nice = T("Building Assessments"),
    #        #description = "Building Safety Assessments",
    #        restricted = True,
    #        module_type = 10,
    #    )),
    # Deprecated by Surveys module
    # - depends on CR, IRS & Impact
    #("assess", Storage(
    #        name_nice = T("Assessments"),
    #        #description = "Rapid Assessments & Flexible Impact Assessments",
    #        restricted = True,
    #        module_type = 10,
    #    )),
    #("impact", Storage(
    #        name_nice = T("Impacts"),
    #        #description = "Used by Assess",
    #        restricted = True,
    #        module_type = None,
    #    )),
    #("ocr", Storage(
    #       name_nice = T("Optical Character Recognition"),
    #       #description = "Optical Character Recognition for reading the scanned handwritten paper forms.",
    #       restricted = False,
    #       module_type = 10
    #   )),
])
