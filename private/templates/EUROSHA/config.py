# -*- coding: utf-8 -*-

from gluon import current
from gluon.storage import Storage
from gluon.contrib.simplejson.ordered_dict import OrderedDict
settings = current.deployment_settings
T = current.T

"""
    Template settings for EUROSHA: European Open Source Humanitarian Aid
"""

# Pre-Populate
settings.base.prepopulate = ["EUROSHA"]

settings.base.system_name = T("EUROSHA Humanitarian Data Registry")
settings.base.system_name_short = T("EUROSHA")

# Theme (folder to use for views/layout.html)
settings.base.theme = "EUROSHA"

# Auth settings
# Do new users need to verify their email address?
settings.auth.registration_requires_verification = True
# Do new users need to be approved by an administrator prior to being able to login?
settings.auth.registration_requires_approval = True
# Uncomment this to request the Organisation when a user registers
settings.auth.registration_requests_organisation = True

settings.auth.role_modules = OrderedDict([
        ("transport", "Airports and Seaports"),
        ("hms", "Hospitals"),
        ("org", "Organizations, Offices, and Facilities"),
        ("inv", "Warehouses"),
        ("staff", "Staff"),
        ("vol", "Volunteers"),
        ("project", "Projects"),
        #("asset", "Assets"),
        #("vehicle", "Vehicles"),
    ])

# L10n settings
settings.L10n.languages = OrderedDict([
    ("en", "English"),
    ("fr", "French"),
])
# Default timezone for users
settings.L10n.utc_offset = "UTC +0100"
# Number formats (defaults to ISO 31-0)
# Decimal separator for numbers (defaults to ,)
settings.L10n.decimal_separator = "."
# Thousands separator for numbers (defaults to space)
settings.L10n.thousands_separator = ","

# Finance settings
settings.fin.currencies = {
    "EUR" : T("Euros"),
    "GBP" : T("Great British Pounds"),
    "USD" : T("United States Dollars"),
}

# Security Policy
settings.security.policy = 7 # Realm w Hierarchy
settings.security.map = True

# Realm Entity
def eurosha_realm_entity(table, row):
    user = current.auth.user
    if user is not None:
        return current.s3db.pr_get_pe_id("org_organisation",
                                         user.organisation_id)
    else:
        return None
settings.auth.realm_entity = eurosha_realm_entity

# Set this if there will be multiple areas in which work is being done,
# and a menu to select among them is wanted.
settings.gis.menu = "Country"
# PoIs to export in KML/OSM feeds from Admin locations
settings.gis.poi_resources = ["cr_shelter", "hms_hospital", "org_office",
                              "transport_airport", "transport_seaport"
                              ]

# Enable this for a UN-style deployment
settings.ui.cluster = True

settings.frontpage.rss = [
    {"title": "Blog",
     "url": "http://eurosha-volunteers-blog.org/feed/"
    }
]

# Organisation Management
# Uncomment to add summary fields for Organisations/Offices for # National/International staff
settings.org.summary = True

# HRM
# Uncomment to allow HRs to have multiple Job Roles in addition to their Job Title
settings.hrm.job_roles = True
# Uncomment to disable Staff experience
settings.hrm.staff_experience = False
# Uncomment to disable Volunteer experience
settings.hrm.vol_experience = False
# Uncomment to disable the use of HR Certificates
settings.hrm.use_certificates = False
# Uncomment to disable the use of HR Credentials
settings.hrm.use_credentials = False
# Uncomment to disable the use of HR Description
settings.hrm.use_description = False
# Uncomment to disable the use of HR ID
settings.hrm.use_id = False
# Uncomment to disable the use of HR Skills
settings.hrm.use_skills = False
# Uncomment to disable the use of HR Trainings
settings.hrm.use_trainings = False

# Projects
# Uncomment this to use settings suitable for a global/regional organisation (e.g. DRR)
settings.project.mode_3w = True
# Uncomment this to use Codes for projects
settings.project.codes = True
# Uncomment this to call project locations 'Communities'
#settings.project.community = True
# Uncomment this to use multiple Budgets per project
settings.project.multiple_budgets = True
# Uncomment this to use multiple Organisations per project
settings.project.multiple_organisations = True
# Uncomment this to customise
#settings.project.organisation_roles = {
#    1: T("Host National Society"),
#    2: T("Partner National Society"),
#    3: T("Donor"),
#    #4: T("Customer"), # T("Beneficiary")?
#    5: T("Partner")
#}

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
    ("translate", Storage(
            name_nice = T("Translation Functionality"),
            #description = "Selective translation of strings based on module.",
            module_type = None,
        )),
    ("gis", Storage(
            name_nice = T("Map"),
            #description = "Situation Awareness & Geospatial Analysis",
            restricted = True,
            module_type = 1,
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
    #("asset", Storage(
    #        name_nice = T("Assets"),
    #        #description = "Recording and Assigning Assets",
    #        restricted = True,
    #        module_type = 5,
    #    )),
    # Vehicle depends on Assets
    #("vehicle", Storage(
    #        name_nice = T("Vehicles"),
    #        #description = "Manage Vehicles",
    #        restricted = True,
    #        module_type = 6,
    #    )),
    ("project", Storage(
            name_nice = T("Projects"),
            #description = "Tracking of Projects, Activities and Tasks",
            restricted = True,
            module_type = 7
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
    ("transport", Storage(
           name_nice = T("Transport"),
           restricted = True,
           module_type = 10,
       )),

])
