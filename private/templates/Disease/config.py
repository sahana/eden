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
    Settings for an outbreak of an infectious disease, such as Ebola:
    http://eden.sahanafoundation.org/wiki/Deployments/Ebola
"""

settings.base.system_name = T("Sahana Ebola Response")
settings.base.system_name_short = T("Sahana")

# PrePopulate data
settings.base.prepopulate = ("Disease", "default/users")

# Theme (folder to use for views/layout.html)
settings.base.theme = "Disease"
# Uncomment to show a default cancel button in standalone create/update forms
settings.ui.default_cancel_button = True

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
settings.gis.countries = ("GN", "LR", "ML", "NG", "SL", "SN")
# Uncomment to display the Map Legend as a floating DIV
settings.gis.legend = "float"

# L10n settings
# Languages used in the deployment (used for Language Toolbar & GIS Locations)
# http://www.loc.gov/standards/iso639-2/php/code_list.php
settings.L10n.languages = OrderedDict([
    ("en", "English"),
    ("fr", "Français"),
])
# Default language for Language Toolbar (& GIS Locations in future)
#settings.L10n.default_language = "en"
# Uncomment to Hide the language toolbar
#settings.L10n.display_toolbar = False
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
#settings.security.policy = 7 # Organisation-ACLs

# RSS feeds
#settings.frontpage.rss = [
#    {"title": "Eden",
#     # Trac timeline
#     "url": "http://eden.sahanafoundation.org/timeline?ticket=on&changeset=on&milestone=on&wiki=on&max=50&daysback=90&format=rss"
#    },
#    {"title": "Twitter",
#     # @SahanaFOSS
#     #"url": "https://search.twitter.com/search.rss?q=from%3ASahanaFOSS" # API v1 deprecated, so doesn't work, need to use 3rd-party service, like:
#     "url": "http://www.rssitfor.me/getrss?name=@SahanaFOSS"
#     # Hashtag
#     #url: "http://search.twitter.com/search.atom?q=%23eqnz" # API v1 deprecated, so doesn't work, need to use 3rd-party service, like:
#     #url: "http://api2.socialmention.com/search?q=%23eqnz&t=all&f=rss"
#    }
#]

# -----------------------------------------------------------------------------
# Summary Pages
# - this is currently the default
#settings.ui.summary = ({"common": True,
#                        "name": "add",
#                        "widgets": [{"method": "create"}],
#                        },
#                       {"common": True,
#                        "name": "cms",
#                        "widgets": [{"method": "cms"}]
#                        },
#                       {"name": "table",
#                        "label": "Table",
#                        "widgets": [{"method": "datatable"}]
#                        },
#                       {"name": "charts",
#                        "label": "Report",
#                        "widgets": [{"method": "report", "ajax_init": True}]
#                        },
#                       {"name": "map",
#                        "label": "Map",
#                        "widgets": [{"method": "map", "ajax_init": True}],
#                        },
#                       )

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
            filter_widget.opts.default = "L2"

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
        module_type = 10
    )),
    ("stats", Storage(
        name_nice = T("Statistics"),
        #description = "Manages statistics",
        restricted = True,
        module_type = 7,
    )),
    # Primary target usecase currently
    ("hms", Storage(
        name_nice = T("Hospitals"),
        #description = "Helps to monitor status of hospitals",
        restricted = True,
        module_type = 2
    )),
    ("disease", Storage(
        name_nice = T("Disease Tracking"),
        #description = "Helps to track cases and trace contacts in disease outbreaks",
        restricted = True,
        module_type = 1
    )),
    # Access to Procedures is key: either attach files or write directly in rich-text forms
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
    # Doesn't seem like an easily-adaptable model:
    #("patient", Storage(
    #    name_nice = T("Patient Tracking"),
    #    #description = "Tracking of Patients",
    #    restricted = True,
    #    module_type = 10
    #)),
    # Possible usecase: HR
    #("hrm", Storage(
    #    name_nice = T("Staff"),
    #    #description = "Human Resources Management",
    #    restricted = True,
    #    module_type = 2,
    #)),
    # Possible usecase: Logistics
    #("supply", Storage(
    #    name_nice = T("Supply Chain Management"),
    #    #description = "Used within Inventory Management, Request Management and Asset Management",
    #    restricted = True,
    #    module_type = None, # Not displayed
    #)),
    #("inv", Storage(
    #    name_nice = T("Warehouses"),
    #    #description = "Receiving and Sending Items",
    #    restricted = True,
    #    module_type = 4
    #)),
    #("req", Storage(
    #    name_nice = T("Requests"),
    #    #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
    #    restricted = True,
    #    module_type = 10,
    #)),
    # Possible support Modules
    #("event", Storage(
    #    name_nice = T("Events"),
    #    #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
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
])
