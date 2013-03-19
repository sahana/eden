# -*- coding: utf-8 -*-

from gluon import current, URL, TR, TD, DIV
from gluon.storage import Storage
from gluon.contrib.simplejson.ordered_dict import OrderedDict

settings = current.deployment_settings
T = current.T

"""
    Template settings for SSF
"""

# Pre-Populate
settings.base.prepopulate = ["SSF"]

# Theme
#settings.base.theme = "SSF"

# Should users be allowed to register themselves?
settings.security.self_registration = True
settings.auth.registration_requires_verification = False
settings.auth.registration_requires_approval = False

# The name of the teams that users are added to when they opt-in to receive alerts
# settings.auth.opt_in_team_list = ["Updates"]
# Uncomment this to set the opt in default to True
settings.auth.opt_in_default = True
# Uncomment this to request the Mobile Phone when a user registers
#settings.auth.registration_requests_mobile_phone = True
# Uncomment this to have the Mobile Phone selection during registration be mandatory
#settings.auth.registration_mobile_phone_mandatory = True
# Uncomment this to request the Organisation when a user registers
#settings.auth.registration_requests_organisation = True
# Uncomment this to have the Organisation selection during registration be mandatory
#settings.auth.registration_organisation_mandatory = True
# Uncomment this to have the Organisation input hidden unless the user enters a non-whitelisted domain
#settings.auth.registration_organisation_hidden = True
# Uncomment this to default the Organisation during registration
settings.auth.registration_organisation_default = "Sahana Software Foundation"
# Uncomment & populate these to set the default roelsd assigned to newly-registered users
# settings.auth.registration_roles = ["STAFF", "PROJECT_EDIT"]
# Uncomment this to request an image when users register
# settings.auth.registration_requests_image = True
# Uncomment this to direct newly-registered users to their volunteer page to be able to add extra details
# NB This requires Verification/Approval to be Off
# @ToDo: Extend to all optional Profile settings: Homepage, Twitter, Facebook, Mobile Phone, Image
#settings.auth.registration_volunteer = True
# Uncomment this to allow users to Login using OpenID
#settings.auth.openid = True
# Uncomment this to allow users to Login using Gmail's SMTP
#settings.auth.gmail_domains = ["gmail.com"]

# Always notify the approver of a new (verified) user, even if the user is automatically approved
settings.auth.always_notify_approver = True

# Base settings
settings.base.system_name = T("The Sahana Sunflower: A Community Portal")
settings.base.system_name_short = T("Sahana Sunflower")

# Set this to True to use Content Delivery Networks to speed up Internet-facing sites
settings.base.cdn = False


# L10n settings
settings.L10n.languages = OrderedDict([
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
settings.L10n.default_language = "en"
# Display the language toolbar
settings.L10n.display_toolbar = True
# Default timezone for users
settings.L10n.utc_offset = "UTC +0000"
# Default timezone for users
settings.L10n.utc_offset = "UTC +0000"
# Uncomment these to use US-style dates in English (localisations can still convert to local format)
#settings.L10n.date_format = T("%m-%d-%Y")
#settings.L10n.time_format = T("%H:%M:%S")
#settings.L10n.datetime_format = T("%m-%d-%Y %H:%M:%S")
# Religions used in Person Registry
# @ToDo: find a better code
# http://eden.sahanafoundation.org/ticket/594
settings.L10n.religions = {
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
#settings.L10n.mandatory_lastname = True

# Add thousands separator to numbers, eg. 1,000,000
#settings.L10n.thousands_separator = True

# Finance settings
#settings.fin.currencies = {
#    "USD" :T("United States Dollars"),
#    "EUR" :T("Euros"),
#    "GBP" :T("Great British Pounds")
#}
#settings.fin.currency_default = "USD" # Dollars
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
settings.gis.display_L0 = False
# Currently unused
#settings.gis.display_L1 = True
# Set this if there will be multiple areas in which work is being done,
# and a menu to select among them is wanted. With this on, any map
# configuration that is designated as being available in the menu will appear
#settings.gis.menu = T("Maps")
# Maximum Marker Size
# (takes effect only on display)
#settings.gis.marker_max_height = 35
#settings.gis.marker_max_width = 30
# Duplicate Features so that they show wrapped across the Date Line?
# Points only for now
# lon<0 have a duplicate at lon+360
# lon>0 have a duplicate at lon-360
settings.gis.duplicate_features = False
# Mouse Position: 'normal', 'mgrs' or 'off'
settings.gis.mouse_position = "normal"
# Print Service URL: http://eden.sahanafoundation.org/wiki/BluePrintGISPrinting
#settings.gis.print_service = "/geoserver/pdf/"
# Do we have a spatial DB available? (currently unused. Will support PostGIS & Spatialite.)
settings.gis.spatialdb = False
# Bing API Key (for Map layers)
#settings.gis.api_bing = ""
# Google API Key (for Earth & MapMaker Layers)
# default works for localhost
#settings.gis.api_google = ""
# Yahoo API Key (for Geocoder)
#settings.gis.api_yahoo = ""
# GeoServer (Currently used by GeoExplorer. Will allow REST control of GeoServer.)
# NB Needs to be publically-accessible URL for querying via client JS
#settings.gis.geoserver_url = "http://localhost/geoserver"
#settings.gis.geoserver_username = "admin"
#settings.gis.geoserver_password = ""

# Use 'soft' deletes
settings.security.archive_not_delete = True

# AAA Settings

# Security Policy
# http://eden.sahanafoundation.org/wiki/S3AAA#System-widePolicy
# 1: Simple (default): Global as Reader, Authenticated as Editor
# 2: Editor role required for Update/Delete, unless record owned by session
# 3: Apply Controller ACLs
# 4: Apply both Controller & Function ACLs
# 5: Apply Controller, Function & Table ACLs
# 6: Apply Controller, Function, Table & Organisation ACLs
# 7: Apply Controller, Function, Table, Organisation & Facility ACLs
#
#settings.security.policy = 6 # Organisation-ACLs
#acl = settings.aaa.acl
#settings.aaa.default_uacl =  acl.READ   # User ACL
#settings.aaa.default_oacl =  acl.CREATE | acl.READ | acl.UPDATE # Owner ACL

# Lock-down access to Map Editing
#settings.security.map = True
# Allow non-MapAdmins to edit hierarchy locations? Defaults to True if not set.
# (Permissions can be set per-country within a gis_config)
#settings.gis.edit_Lx = False
# Allow non-MapAdmins to edit group locations? Defaults to False if not set.
#settings.gis.edit_GR = True
# Note that editing of locations used as regions for the Regions menu is always
# restricted to MapAdmins.

# Audit settings
# We Audit if either the Global or Module asks us to
# (ignore gracefully if module author hasn't implemented this)
# NB Auditing (especially Reads) slows system down & consumes diskspace
#settings.security.audit_write = False
#settings.security.audit_read = False

# UI/Workflow options
# Should user be prompted to save before navigating away?
#settings.ui.navigate_away_confirm = False
# Should user be prompted to confirm actions?
#settings.ui.confirm = False
# Should potentially large dropdowns be turned into autocompletes?
# (unused currently)
#settings.ui.autocomplete = True
#settings.ui.update_label = "Edit"
# Enable this for a UN-style deployment
#settings.ui.cluster = True
# Enable this to use the label 'Camp' instead of 'Shelter'
#settings.ui.camp = True
# Enable this to change the label for 'Mobile Phone'
#settings.ui.label_mobile_phone = T("Cell Phone")
# Enable this to change the label for 'Postcode'
#settings.ui.label_postcode = T("ZIP Code")
# Enable Social Media share buttons
#settings.ui.social_buttons = True

# Request
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
# Restrict the type of requests that can be made, valid values in the
# list are ["Stock", "People", "Other"]. If this is commented out then
# all types will be valid.
#settings.req.req_type = ["Stock"]

# Custom Crud Strings for specific req_req types
#settings.req.req_crud_strings = dict()
#ADD_ITEM_REQUEST = T("Make a Request for Donations")
#LIST_ITEM_REQUEST = T("List Requests for Donations")
# req_req Crud Strings for Item Request (type=1)
#settings.req.req_crud_strings[1] = Storage(
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
#settings.req.req_crud_strings[3] = Storage(
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
#settings.inv.collapse_tabs = False
# Use the term 'Order' instead of 'Shipment'
#settings.inv.shipment_name = "order"

# Supply
#settings.supply.use_alt_name = False
# Do not edit after deployment
#settings.supply.catalog_default = T("Other Items")

# Human Resource Management
# Uncomment to allow Staff & Volunteers to be registered without an email address
#settings.hrm.email_required = False
# Uncomment to hide the Staff resource
settings.hrm.show_staff = False
# Uncomment to hide the Volunteer resource
#settings.hrm.show_vols = False
# Uncomment to allow hierarchical categories of Skills, which each need their own set of competency levels.
#settings.hrm.skill_types = True

# Project 
# Uncomment this to use settings suitable for detailed Task management
settings.project.mode_task = True
# Uncomment this to use Activities for projects
settings.project.activities = True

# Save Search Widget
#settings.save_search.widget = False

# Terms of Service to be able to Register on the system
#settings.options.terms_of_service = T("Terms of Service\n\nYou have to be eighteen or over to register as a volunteer.")
# Should we use internal Support Requests?
#settings.options.support_requests = True


# Formstyle
def formstyle_row(id, label, widget, comment, hidden=False):
    if hidden:
        hide = "hide"
    else:
        hide = ""
    row = TR(TD(DIV(label,
                _id=id + "1",
                _class="w2p_fl %s" % hide),
            DIV(widget,
                _id=id,
                _class="w2p_fw %s" % hide),
            DIV(comment,
                _id=id, 
                _class="w2p_fc %s" % hide),
           ))
    return row
def form_style(self, xfields):
    """
        @ToDo: Requires further changes to code to use
        - Adding a formstyle_row setting to use for indivdual rows
        Use new Web2Py formstyle to generate form using DIVs & CSS
        CSS can then be used to create MUCH more flexible form designs:
        - Labels above vs. labels to left
        - Multiple Columns 
    """
    form = DIV()

    for id, a, b, c, in xfields:
        form.append(formstyle_row(id, a, b, c))

    return form
settings.ui.formstyle_row = formstyle_row
settings.ui.formstyle = formstyle_row


from s3 import s3forms
settings.ui.crud_form_project_project = s3forms.S3SQLCustomForm(
        "organisation_id",
        "name",
        "description",
        "status_id",
        "start_date",
        "end_date",
        "calendar",
        "human_resource_id",
        s3forms.S3SQLInlineComponentCheckbox(
            "sector",
            label = T("Sectors"),
            field = "sector_id",
            cols = 4,
        ),
        "budget",
        "currency",
        "comments",
    )


# Comment/uncomment modules here to disable/enable them
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
            module_type = 10
        )),
    # All modules below here should be possible to disable safely
    ("hrm", Storage(
            name_nice = T("Volunteers"),
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
    #("supply", Storage(
    #        name_nice = T("Supply Chain Management"),
    #        description = T("Used within Inventory Management, Request Management and Asset Management"),
    #        restricted = True,
    #        module_type = None, # Not displayed
    #    )),
    #("inv", Storage(
    #        name_nice = T("Warehouse"),
    #        description = T("Receiving and Sending Items"),
    #        restricted = True,
    #        module_type = 4
    #    )),
    #("proc", Storage(
    #        name_nice = T("Procurement"),
    #        description = T("Ordering & Purchasing of Goods & Services"),
    #        restricted = True,
    #        module_type = 10
    #    )),
    #("asset", Storage(
    #        name_nice = T("Assets"),
    #        description = T("Recording and Assigning Assets"),
    #        restricted = True,
    #        module_type = 5,
    #    )),
    # Vehicle depends on Assets
    #("vehicle", Storage(
    #        name_nice = T("Vehicles"),
    #        description = T("Manage Vehicles"),
    #        restricted = True,
    #        module_type = 10,
    #    )),
    #("req", Storage(
    #        name_nice = T("Requests"),
    #        description = T("Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested."),
    #        restricted = True,
    #        module_type = 10,
    #    )),
    ("project", Storage(
            name_nice = T("Task Lists"),
            description = T("Tracking of Projects, Activities and Tasks"),
            restricted = True,
            module_type = 1
        )),
    ("survey", Storage(
            name_nice = T("Surveys"),
            description = T("Create, enter, and manage surveys."),
            restricted = True,
            module_type = 5,
        )),
    #("cr", Storage(
    #        name_nice = T("Shelters"),
    #        description = T("Tracks the location, capacity and breakdown of victims in Shelters"),
    #        restricted = True,
    #        module_type = 10
    #    )),
    #("hms", Storage(
    #        name_nice = T("Hospitals"),
    #        description = T("Helps to monitor status of hospitals"),
    #        restricted = True,
    #        module_type = 10
    #    )),
    #("irs", Storage(
    #        name_nice = T("Incidents"),
    #        description = T("Incident Reporting System"),
    #        restricted = False,
    #        module_type = 10
    #    )),
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
    #("scenario", Storage(
    #        name_nice = T("Scenarios"),
    #        description = T("Define Scenarios for allocation of appropriate Resources (Human, Assets & Facilities)."),
    #        restricted = True,
    #        module_type = 10,
    #    )),
    #("event", Storage(
    #        name_nice = T("Events"),
    #        description = T("Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities)."),
    #        restricted = True,
    #        module_type = 10,
    #    )),
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
    #("dvi", Storage(
    #       name_nice = T("Disaster Victim Identification"),
    #       description = T("Disaster Victim Identification"),
    #       restricted = True,
    #       module_type = 10,
    #       #access = "|DVI|",      # Only users with the DVI role can see this module in the default menu & access the controller
    #       #audit_read = True,     # Can enable Audit for just an individual module here
    #       #audit_write = True
    #   )),
    #("mpr", Storage(
    #       name_nice = T("Missing Person Registry"),
    #       description = T("Helps to report and search for missing persons"),
    #       restricted = False,
    #       module_type = 10,
    #   )),
    ("cms", Storage(
           name_nice = T("Content Management"),
           description = T("Content Management System"),
           restricted = True,
           module_type = 3,
       )),
    ("deployment", Storage(
           name_nice = T("Deployments"),
           description = T("Deployment Registry"),
           restricted = True,
           module_type = 4,
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
