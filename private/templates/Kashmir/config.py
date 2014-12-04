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
    Template settings

    All settings which are to configure a specific template are located here

    Deployers should ideally not need to edit any other files outside of their template folder
"""

settings.base.system_name = "Athewaas"
settings.base.system_name_short = "Athewaas"

# PrePopulate data
settings.base.prepopulate = ("Kashmir", "Kashmir/Demo", "default/users")

# Theme (folder to use for views/layout.html)
settings.base.theme = "Kashmir"

# Authentication settings
# Should users be allowed to register themselves?
#settings.security.self_registration = False
# Do new users need to verify their email address?
settings.auth.registration_requires_verification = True
# Do new users need to be approved by an administrator prior to being able to login?
settings.auth.registration_requires_approval = True
settings.auth.registration_requests_organisation = True

# Ensure that Users have Staff records in their Org
settings.auth.registration_link_user_to = {"staff": T("Staff")}
settings.auth.registration_link_user_to_default = "staff"

# Configure frontpage request email address
#settings.frontpage.request_email = "athewaas.requests@revivekashmir.org"
# Configure frontpage phone number
settings.frontpage.phone_number = "#0194-230-0452"

# Uncomment to set the default role UUIDs assigned to newly-registered users
# This is a dictionary of lists, where the key is the realm that the list of roles applies to
# The key 0 implies not realm restricted
# The keys "organisation_id" and "site_id" can be used to indicate the user's "organisation_id" and "site_id"
#settings.auth.registration_roles = { "organisation_id": ["EDITOR"]}

# Approval emails get sent to all admins
settings.mail.approver = "ADMIN"

# Restrict the Location Selector to just certain countries
# NB This can also be over-ridden for specific contexts later
# e.g. Activities filtered to those of parent Project
settings.gis.countries = ("IN",)

# L10n settings
# Languages used in the deployment (used for Language Toolbar & GIS Locations)
# http://www.loc.gov/standards/iso639-2/php/code_list.php
settings.L10n.languages = OrderedDict([
#    ("ar", "العربية"),
#    ("bs", "Bosanski"),
    ("en-gb", "English"),
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
    ("ur", "اردو"),
#    ("vi", "Tiếng Việt"),
#    ("zh-cn", "中文 (简体)"),
#    ("zh-tw", "中文 (繁體)"),
])
# Default language for Language Toolbar (& GIS Locations in future)
settings.L10n.default_language = "en-gb"
# Uncomment to Hide the language toolbar
settings.L10n.display_toolbar = False
# Default timezone for users
settings.L10n.utc_offset = "UTC +0530"

settings.fin.currencies = {
    "EUR" : T("Euros"),
    "GBP" : T("Great British Pounds"),
    "INR" : T("Indian Rupees"),
    "USD" : T("United States Dollars"),
}
settings.fin.currency_default = "INR"

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
settings.security.policy = 7

# RSS feeds
settings.frontpage.rss = []

# Disable people registration in shelters
settings.cr.people_registration = False

# Disable Emergency Contacts
settings.pr.show_emergency_contacts = False

# Restrict the type of requests that can be made, valid values in the
# list are ["Stock", "People", "Other"]. If this is commented out then
# all types will be valid.
#settings.req.req_type = ("Stock", "People")
settings.req.req_type = ("Stock",)

# Uncomment to show a default cancel button in standalone create/update forms
settings.ui.default_cancel_button = True

# -----------------------------------------------------------------------------
def customise_event_incident_report_resource(r, tablename):

    s3db = current.s3db

    table = s3db.event_incident_report
    table.name.label = T("Description")

    # ImageCrop widget doesn't currently work within an Inline Form
    from gluon.validators import IS_IMAGE
    image_field = s3db.doc_image.file
    image_field.requires = IS_IMAGE()
    image_field.widget = None

    from s3 import S3SQLCustomForm, S3SQLInlineComponent
    crud_form = S3SQLCustomForm(S3SQLInlineComponent(
                                    "image",
                                    label = T("Photo"),
                                    fields = [("", "file"),
                                              ],
                                    ),
                                "name",
                                "location_id",
                                )

    list_fields = ["location_id",
                   "name",
                   ]

    s3db.configure("event_incident_report",
                   crud_form = crud_form,
                   list_fields = list_fields,
                   )

settings.customise_event_incident_report_resource = customise_event_incident_report_resource

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
        module_type = 10 # Accessible via Admin menu
    )),
    ("org", Storage(
        name_nice = T("Organizations"),
        #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
        restricted = True,
        module_type = 5
    )),
    ("hrm", Storage(
       name_nice = T("Staff"),
       #description = "Human Resources Management",
       restricted = True,
       module_type = 10,
    )),
    ("cr", Storage(
        name_nice = T("Shelters"),
        #description = "Tracks the location, capacity and breakdown of victims in Shelters",
        restricted = True,
        module_type = 3
    )),
    ("doc", Storage(
        name_nice = T("Documents"),
        #description = "A library of digital resources, such as photos, documents and reports",
        restricted = True,
        module_type = None,
    )),
    ("event", Storage(
        name_nice = T("Incident Reports"),
        restricted = True,
        module_type = 3
    )),
    ("req", Storage(
        name_nice = T("Requests"),
        #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
        restricted = True,
        module_type = 2,
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
    ("vol", Storage(
        name_nice = T("Volunteers"),
        #description = "",
        restricted = True,
        module_type = 7
    )),
    ("stats", Storage(
        name_nice = T("Statis"),
        #description = "Enabled because organization resourse model needs this",
        restricted = True,
        module_type = 8
    )),
    ("project", Storage(
        name_nice = T("Project"),
        #description = "",
        restricted = True,
        module_type = 9
    )),
])
