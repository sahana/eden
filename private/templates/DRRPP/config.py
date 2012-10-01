# -*- coding: utf-8 -*-

from gluon import current
from gluon.storage import Storage
from gluon.contrib.simplejson.ordered_dict import OrderedDict
settings = current.deployment_settings
T = current.T

"""
    Template settings for DRRPP
"""

# Pre-Populate
settings.base.prepopulate = ["DRRPP"]

settings.base.system_name = T("DRR Project Portal")
settings.base.system_name_short = T("DRRPP")

# Theme (folder to use for views/layout.html)
settings.base.theme = "DRRPP"

# Auth settings
# Do new users need to verify their email address?
settings.auth.registration_requires_verification = True
# Do new users need to be approved by an administrator prior to being able to login?
settings.auth.registration_requires_approval = True
# Uncomment this to request the Organisation when a user registers
settings.auth.registration_requests_organisation = True
settings.auth.registration_pending = \
"""Registration awaiting approval from Administrator or Organisation Contact.
A confirmation email will be sent to you once approved.
For enquiries contact %s""" % settings.get_mail_approver()

# Record Approval
settings.auth.record_approval = True
settings.auth.record_approval_required_for = ["org_organisation", "project_project", "project_framework"]

# L10n settings
settings.L10n.languages = OrderedDict([
    ("en", "English"),
])
# Default timezone for users
settings.L10n.utc_offset = "UTC +0700"
# Number formats (defaults to ISO 31-0)
# Decimal separator for numbers (defaults to ,)
settings.L10n.decimal_separator = "."
# Thousands separator for numbers (defaults to space)
settings.L10n.thousands_separator = ","
# Unsortable 'pretty' date format
#settings.L10n.date_format = T("%d-%b-%Y")
#settings.L10n.datetime_format = T("%d-%b-%Y %H:%M:%S")

# Finance settings
settings.fin.currencies = {
    "AUD" : T("Australian Dollars"),
    "CAD" : T("Canadian Dollars"),
    "EUR" : T("Euros"),
    "GBP" : T("Great British Pounds"),
    "PHP" : T("Philippine Pesos"),
    "CHF" : T("Swiss Francs"),
    "USD" : T("United States Dollars"),
}

# Security Policy
settings.security.policy = 6 # Realm
settings.security.map = True

# Theme
settings.gis.map_height = 600
settings.gis.map_width = 854

# Display Resources recorded to Admin-Level Locations on the map
# @ToDo: Move into gis_config?
settings.gis.display_L0 = True
# Deployment only covers Asia-Pacific
settings.gis.countries = [ "AF", "AU", "BD", "BN", "CK", "CN", "FJ", "FM", "HK", "ID", "IN", "JP", "KH", "KI", "KP", "KR", "LA", "MH", "MM", "MN", "MV", "MY", "NP", "NZ", "PG", "PH", "PK", "PW", "SB", "SG", "SL", "TH", "TL", "TO", "TV", "TW", "VN", "VU", "WS"]

# Enable this for a UN-style deployment
settings.ui.cluster = True

# Organisations
# Uncomment to add summary fields for Organisations/Offices for # National/International staff
settings.org.summary = True

# Projects
# Uncomment this to use settings suitable for a global/regional organisation (e.g. DRR)
settings.project.mode_3w = True
# Uncomment this to use DRR (Disaster Risk Reduction) extensions
settings.project.mode_drr = True
# Uncomment this to use Codes for projects
settings.project.codes = True
# Uncomment this to call project locations 'Communities'
#settings.project.community = True
# Uncomment this to use multiple Budgets per project
#settings.project.multiple_budgets = True
# Uncomment this to use multiple Organisations per project
settings.project.multiple_organisations = True
# Uncomment this to disable Sectors in projects
settings.project.sectors = False
# Uncomment this to customise
settings.project.organisation_roles = {
    1: T("Lead Organization"),
    2: T("Partner Organization"),
    3: T("Donor"),
}

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
    ("gis", Storage(
            name_nice = T("Map"),
            #description = "Situation Awareness & Geospatial Analysis",
            restricted = True,
            module_type = 3,     # 6th item in the menu
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
            module_type = 2
        )),
    # All modules below here should be possible to disable safely
    ("hrm", Storage(
            name_nice = T("Staff"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = None,
        )),
    ("doc", Storage(
            name_nice = T("Documents"),
            #description = "A library of digital resources, such as photos, documents and reports",
            restricted = True,
            module_type = None,
        )),
    ("msg", Storage(
            name_nice = T("Messaging"),
            #description = "Sends & Receives Alerts via Email & SMS",
            restricted = True,
            # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
            module_type = None,
        )),
    ("project", Storage(
            name_nice = T("Projects"),
            #description = "Tracking of Projects, Activities and Tasks",
            restricted = True,
            module_type = 1
        )),
])
