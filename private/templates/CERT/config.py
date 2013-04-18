# -*- coding: utf-8 -*-

from gluon import current
from gluon.storage import Storage
from gluon.contrib.simplejson.ordered_dict import OrderedDict
settings = current.deployment_settings
T = current.T

"""
    Template settings for US

    All settings which are to configure a specific template are located here

    Deployers should ideally not need to edit any other files outside of their template folder
"""

# Pre-Populate
settings.base.prepopulate = ["CERT"]

# Theme
settings.base.theme = "CERT"

# Uncomment to Hide the language toolbar
settings.L10n.display_toolbar = False
# Default timezone for users
settings.L10n.utc_offset = "UTC -0600"
# Uncomment these to use US-style dates in English (localisations can still convert to local format)
settings.L10n.date_format = T("%m-%d-%Y")
# Start week on Sunday
settings.L10n.firstDOW = 0
# Number formats (defaults to ISO 31-0)
# Decimal separator for numbers (defaults to ,)
settings.L10n.decimal_separator = "."
# Thousands separator for numbers (defaults to space)
settings.L10n.thousands_separator = ","
# Default Country Code for telephone numbers
settings.L10n.default_country_code = 1
# Enable this to change the label for 'Mobile Phone'
settings.ui.label_mobile_phone = "Cell Phone"
# Enable this to change the label for 'Postcode'
settings.ui.label_postcode = "ZIP Code"
# PDF to Letter
settings.base.paper_size = T("Letter")

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
    # All modules below here should be possible to disable safely
    ("hrm", Storage(
            name_nice = T("Staff"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = None,
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
    #("project", Storage(
    #        name_nice = T("Projects"),
    #        #description = "Tracking of Projects, Activities and Tasks",
    #        restricted = True,
    #        module_type = 2
    #    )),
    ("scenario", Storage(
            name_nice = T("Scenarios"),
            #description = "Define Scenarios for allocation of appropriate Resources (Human, Assets & Facilities).",
            restricted = True,
            module_type = None,
        )),
    ("event", Storage(
            name_nice = T("Events"),
            #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
            restricted = True,
            module_type = 10,
        )),
    ("irs", Storage(
            name_nice = T("Incidents"),
            #description = "Incident Reporting System",
            restricted = False,
            module_type = 10
        )),
])
