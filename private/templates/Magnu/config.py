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
    Template settings for a hosted environment to allow NGOs to share data
    Prototype being developed for CAR (Central African Republic)
"""

#settings.base.system_name = T("Magnu")
#settings.base.system_name_short = T("Magnu")
settings.base.system_name = T("Sahana")
settings.base.system_name_short = T("Sahana")

# PrePopulate data
settings.base.prepopulate = ("Magnu", "default/users")

# Theme (folder to use for views/layout.html)
settings.base.theme = "Magnu"

# Authentication settings
# Should users be allowed to register themselves?
#settings.security.self_registration = False
# Do new users need to verify their email address?
settings.auth.registration_requires_verification = True
# Do new users need to be approved by an administrator prior to being able to login?
#settings.auth.registration_requires_approval = True
settings.auth.registration_requests_organisation = True
# @ToDo:
#settings.auth.registration_requests_location = "L0"

# Approval emails get sent to all admins
settings.mail.approver = "ADMIN"

# Restrict the Location Selector to just certain countries
# NB This can also be over-ridden for specific contexts later
# e.g. Activities filtered to those of parent Project
settings.gis.countries = ("CF",) # Initially, will change
# Uncomment to display the Map Legend as a floating DIV
settings.gis.legend = "float"

# L10n settings
# Languages used in the deployment (used for Language Toolbar & GIS Locations)
# http://www.loc.gov/standards/iso639-2/php/code_list.php
settings.L10n.languages = OrderedDict([
#    ("ar", "العربية"),
#    ("bs", "Bosanski"),
    ("en", "English"),
    ("fr", "Français"),
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
#settings.L10n.default_language = "en"
# Uncomment to Hide the language toolbar
#settings.L10n.display_toolbar = False
# @ToDO:These should be modified per-country
# Default timezone for users
settings.L10n.utc_offset = "UTC +0100"
# Number formats (defaults to ISO 31-0)
# Decimal separator for numbers (defaults to ,)
#settings.L10n.decimal_separator = "."
# Thousands separator for numbers (defaults to space)
#settings.L10n.thousands_separator = ","

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

# Resources which can be directly added to the main map
settings.gis.poi_create_resources = \
    (dict(c="event",
          f="incident_report",
          table="event_incident_report",
          type="point",
          label=T("Add Incident"),
          layer="Incident Reports",
          ),
     #dict(c="gis",
     #     f="poi",
     #     table="gis_poi",
     #     type="polygon",
     #     label=T("Add Area"),
     #     layer="Areas",
     #     ),
     #dict(c="gis",
     #     f="poi",
     #     table="gis_poi",
     #     type="line",
     #     label=T("Add Route"),
     #     layer="Routes",
     #     ),
     )

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

settings.org.groups = "Coalition / Consortium"
# @ToDo: Once we go global
# Enable the use of Organisation Branches
#settings.org.branches = True
# Show branches as tree rather than as table
#settings.org.branches_tree_view = True

# Uncomment this to allow multiple site contacts per site (e.g. if needing a separate contact per sector)
settings.hrm.site_contact_unique = False

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
        module_type = 1
    )),
    #("hrm", Storage(
    #    name_nice = T("Staff"),
    #    #description = "Human Resources Management",
    #    restricted = True,
    #    module_type = 2,
    #)),
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
    ("security", Storage(
       name_nice = T("Security"),
       #description = "Security Management System",
       restricted = True,
       module_type = 10,
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
    #("req", Storage(
    #    name_nice = T("Requests"),
    #    #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
    #    restricted = True,
    #    module_type = 10,
    #)),
    ("project", Storage(
        name_nice = T("Projects"),
        #description = "Tracking of Projects, Activities and Tasks",
        restricted = True,
        module_type = 2
    )),
    ("cr", Storage(
        name_nice = T("Camps"),
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
    ("transport", Storage(
       name_nice = T("Transport"),
       restricted = True,
       module_type = 10,
    )),
    ("stats", Storage(
        name_nice = T("Statistics"),
        #description = "Manages statistics",
        restricted = True,
        module_type = None,
    )),
    ("water", Storage(
        name_nice = T("Water"),
        #description = "Flood Gauges show water levels in various parts of the country",
        restricted = True,
        module_type = 10
    )),
    ("event", Storage(
        name_nice = T("Events"),
        #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
        restricted = True,
        module_type = 10,
    )),
    #("dvr", Storage(
    #   name_nice = T("Disaster Victim Registry"),
    #   #description = "Allow affected individuals & households to register to receive compensation and distributions",
    #   restricted = True,
    #   module_type = 10,
    #)),
])
