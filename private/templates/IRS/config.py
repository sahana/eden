# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current
from gluon.storage import Storage

T = current.T
settings = current.deployment_settings

"""
    Template settings for an Incident Response System

    Initially targeting Sierra Leone, but easily adapatable for other locations
"""

settings.base.system_name = T("Sierra Leone Incident Response System")
settings.base.system_name_short = T("SL IRS")

# PrePopulate data
settings.base.prepopulate = ("IRS", "default/users")

# Theme (folder to use for views/layout.html)
settings.base.theme = "IRS"

# Authentication settings
# Should users be allowed to register themselves?
#settings.security.self_registration = False
# Do new users need to verify their email address?
settings.auth.registration_requires_verification = True
# Do new users need to be approved by an administrator prior to being able to login?
#settings.auth.registration_requires_approval = True
#settings.auth.registration_requests_organisation = True

# Approval emails get sent to all admins
settings.mail.approver = "ADMIN"

# Restrict the Location Selector to just certain countries
# NB This can also be over-ridden for specific contexts later
# e.g. Activities filtered to those of parent Project
settings.gis.countries = ("SL",)
# Uncomment to display the Map Legend as a floating DIV
settings.gis.legend = "float"

# L10n settings
# Languages used in the deployment (used for Language Toolbar & GIS Locations)
# http://www.loc.gov/standards/iso639-2/php/code_list.php
settings.L10n.languages = OrderedDict([
#    ("ar", "العربية"),
#    ("bs", "Bosanski"),
    ("en_gb", "English"),
#    ("fr", "Français"),
#    ("de", "Deutsch"),
#    ("el", "ελληνικά"),
#    ("es", "Español"),
#    ("it", "Italiano"),
#    ("ja", "日本語"),
#    ("km", "ភាសាខ្មែរ"),
#    ("ko", "한국어"),
#    ("ne", "नेपाली"),          # Nepali
#    ("prs", "دری"), # Dari
#    ("ps", "پښتو"), # Pashto
#    ("pt", "Português"),
#    ("pt-br", "Português (Brasil)"),
#    ("ru", "русский"),
#    ("tet", "Tetum"),
#    ("tl", "Tagalog"),
#    ("ur", "اردو"),
#    ("vi", "Tiếng Việt"),
#    ("zh-cn", "中文 (简体)"),
#    ("zh-tw", "中文 (繁體)"),
])
# Default language for Language Toolbar (& GIS Locations in future)
settings.L10n.default_language = "en_gb"
# Uncomment to Hide the language toolbar
settings.L10n.display_toolbar = False
# Default timezone for users
#settings.L10n.utc_offset = "UTC +0100"
# Number formats (defaults to ISO 31-0)
# Decimal separator for numbers (defaults to ,)
settings.L10n.decimal_separator = "."
# Thousands separator for numbers (defaults to space)
settings.L10n.thousands_separator = ","

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
settings.security.policy = 7 # Organisation-ACLs

# =============================================================================
# Project Settings
# Uncomment this to use settings suitable for a global/regional organisation (e.g. DRR)
settings.project.mode_3w = True
# Uncomment this to use Codes for projects
settings.project.codes = True
# Uncomment this to enable Hazards in 3W projects
#settings.project.hazards = True
# Uncomment this to use multiple Budgets per project
#settings.project.multiple_budgets = True
# Uncomment this to use multiple Organisations per project
settings.project.multiple_organisations = True
# Uncomment this to enable Themes in 3W projects
#settings.project.themes = True
# Uncomment this to customise
# Links to Filtered Components for Donors & Partners
#settings.project.organisation_roles = {
#    1: T("Lead Organization"),
#    2: T("Partner Organization"),
#    3: T("Donor"),
#    #4: T("Customer"), # T("Beneficiary")?
#    #5: T("Supplier"),
#    9: T("Partner Organization"), # Needed for IFRC RMS interop ("Partner National Society")
#}

# =============================================================================
# Requests
#settings.req.use_commit = False
# Restrict the type of requests that can be made, valid values in the
# list are ["Stock", "People", "Other"]. If this is commented out then
# all types will be valid.
settings.req.req_type = ["Stock"]

# -----------------------------------------------------------------------------
def customise_hms_hospital_resource(r, tablename):

    if r.representation == "geojson":
        # Don't represent the facility_status as numbers are smaller to xmit
        current.s3db.hms_status.facility_status.represent = None
        return

    # Limit options to just those used & relabel them for context
    hms_facility_type_opts = {
        1: T("Hospital"),
        #2: T("Field Hospital"),
        #3: T("Specialized Hospital"),
        #11: T("Health center"),
        #12: T("Health center with beds"),
        #13: T("Health center without beds"),
        #21: T("Dispensary"),
        #31: T("Long-term care"),
        #41: T("Emergency Treatment Centre"),
        41: T("ETC"),
        42: T("Triage"),
        43: T("Holding Center"),
        44: T("Transit Center"),
        #98: T("Other"),
        #99: T("Unknown"),
    }

    hms_facility_status_opts = {
        #1: T("Normal"),
        1: T("Functioning"),
        #2: T("Compromised"),
        #3: T("Evacuating"),
        4: T("Closed"),
        5: T("Pending"),
        #99: T("No Response")
    }

    from gluon import IS_EMPTY_OR, IS_IN_SET

    s3db = current.s3db
    NONE = current.messages["NONE"]

    field = s3db.hms_hospital.facility_type
    field.represent = lambda opt: hms_facility_type_opts.get(opt, NONE)
    field.requires = IS_EMPTY_OR(IS_IN_SET(hms_facility_type_opts))

    field = s3db.hms_status.facility_status
    field.represent = lambda opt: hms_facility_status_opts.get(opt, NONE)
    field.requires = IS_EMPTY_OR(IS_IN_SET(hms_facility_status_opts))

settings.customise_hms_hospital_resource = customise_hms_hospital_resource

# -----------------------------------------------------------------------------
def customise_disease_stats_data_resource(r, tablename):

    s3db = current.s3db
    # Load model & set defaults
    table = s3db.disease_stats_data

    # Add a TimePlot tab to summary page
    summary = settings.get_ui_summary()
    settings.ui.summary = list(summary) + [{"name": "timeplot",
                                            "label": "Progression",
                                            "widgets": [{"method": "timeplot",
                                                         "ajax_init": True,
                                                         }
                                                        ],
                                            }]

    # Default parameter filter
    def default_parameter_filter(selector, tablename=None):
        ptable = s3db.stats_parameter
        query = (ptable.deleted == False) & \
                (ptable.name == "Cases")
        row = current.db(query).select(ptable.parameter_id,
                                       limitby = (0, 1)).first()
        if row:
            return row.parameter_id
        else:
            return None

    # Set filter defaults
    resource = r.resource
    filter_widgets = resource.get_config("filter_widgets", [])
    for filter_widget in filter_widgets:
        if filter_widget.field == "parameter_id":
            filter_widget.opts.default = default_parameter_filter
        elif filter_widget.field == "location_id$level":
            filter_widget.opts.default = "L2"

settings.customise_disease_stats_data_resource = customise_disease_stats_data_resource

# -----------------------------------------------------------------------------
def customise_stats_demographic_data_resource(r, tablename):

    s3db = current.s3db
    # Load model & set defaults
    table = s3db.stats_demographic_data

    # Default parameter filter
    def default_parameter_filter(selector, tablename=None):
        ptable = s3db.stats_parameter
        query = (ptable.deleted == False) & \
                (ptable.name == "Population Total")
        row = current.db(query).select(ptable.parameter_id,
                                       limitby = (0, 1)).first()
        if row:
            return row.parameter_id
        else:
            return None

    # Set filter defaults
    resource = r.resource
    filter_widgets = resource.get_config("filter_widgets", [])
    for filter_widget in filter_widgets:
        if filter_widget.field == "parameter_id":
            filter_widget.opts.default = default_parameter_filter
        elif filter_widget.field == "location_id$level":
            filter_widget.opts.default = "L1"
        elif filter_widget.field == "year":
            filter_widget.opts.default = 2004

settings.customise_stats_demographic_data_resource = customise_stats_demographic_data_resource

# -----------------------------------------------------------------------------
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
        module_type = 1,     # 1st item in the menu
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
        module_type = 10
    )),
    ("hrm", Storage(
        name_nice = T("Staff"),
        #description = "Human Resources Management",
        restricted = True,
        module_type = 3,
    )),
    #("vol", Storage(
    #    name_nice = T("Volunteers"),
    #    #description = "Human Resources Management",
    #    restricted = True,
    #    module_type = 2,
    #)),
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
    ("event", Storage(
        name_nice = T("Events"),
        #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
        restricted = True,
        module_type = 2,
    )),
    # Specific for Sierrra Leone:
    ("disease", Storage(
        name_nice = T("Disease"),
        restricted = True,
        module_type = 10
    )),
    ("hms", Storage(
        name_nice = T("Hospitals"),
        #description = "Helps to monitor status of hospitals",
        restricted = True,
        module_type = 10
    )),
    ("dvi", Storage(
        name_nice = T("Burials"),
        restricted = True,
        module_type = 10
    )),
    ("supply", Storage(
        name_nice = T("Supply Chain Management"),
        #description = "Used within Inventory Management, Request Management and Asset Management",
        restricted = True,
        module_type = None, # Not displayed
    )),
    ("asset", Storage(
        name_nice = T("Assets"),
        #description = "Recording and Assigning Assets",
        restricted = True,
        module_type = None, # Just used for Vehicles
    )),
    # Vehicle depends on Assets
    ("vehicle", Storage(
        name_nice = T("Vehicles"),
        #description = "Manage Vehicles",
        restricted = True,
        module_type = 4,
    )),
    # Enable for org_resource?
    ("stats", Storage(
        name_nice = T("Statistics"),
        #description = "Manages statistics",
        restricted = True,
        module_type = 10,
    )),
    ("transport", Storage(
       name_nice = T("Transport"),
       restricted = True,
       module_type = 10,
    )),
    # Enabled as-requested by user
    ("inv", Storage(
        name_nice = T("Warehouses"),
        #description = "Receiving and Sending Items",
        restricted = True,
        module_type = 4
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
    #("cr", Storage(
    #    name_nice = T("Shelters"),
    #    #description = "Tracks the location, capacity and breakdown of victims in Shelters",
    #    restricted = True,
    #    module_type = 10
    #)),
    #("dvr", Storage(
    #   name_nice = T("Disaster Victim Registry"),
    #   #description = "Allow affected individuals & households to register to receive compensation and distributions",
    #   restricted = True,
    #   module_type = 10,
    #)),
])
