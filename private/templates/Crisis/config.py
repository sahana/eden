# -*- coding: utf-8 -*-

from gluon import current
from gluon.storage import Storage
from gluon.contrib.simplejson.ordered_dict import OrderedDict
settings = current.deployment_settings
T = current.T

"""
    Template settings for Crisis Portal

    All settings which are to configure a specific template are located here

    Deployers should ideally not need to edit any other files outside of their template folder
"""

# Pre-Populate
settings.base.prepopulate = ["Crisis"]

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
            name_nice = T("Warehouse"),
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
    ("mpr", Storage(
           name_nice = T("Missing Person Registry"),
           #description = "Helps to report and search for missing persons",
           restricted = True,
           module_type = 10,
       )),
    ("dvr", Storage(
           name_nice = T("Disaster Victim Registry"),
           #description = "Allow affected individuals & households to register to receive compensation and distributions",
           restricted = True,
           module_type = 10,
       )),
    #("scenario", Storage(
    #        name_nice = T("Scenarios"),
    #        #description = "Define Scenarios for allocation of appropriate Resources (Human, Assets & Facilities).",
    #        restricted = True,
    #        module_type = 10,
    #    )),
    #("event", Storage(
    #        name_nice = T("Events"),
    #        #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
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
    ("security", Storage(
           name_nice = T("Security"),
           #description = "Security Management System",
           restricted = True,
           module_type = 10,
       )),
    # These are specialist modules
    # Requires RPy2
    #("climate", Storage(
    #        name_nice = T("Climate"),
    #        #description = "Climate data portal",
    #        restricted = True,
    #        module_type = 10,
    #)),
    ("delphi", Storage(
            name_nice = T("Decision Maker"),
            #description = "Supports the decision making of large groups of Crisis Management Experts by helping the groups create ranked list.",
            restricted = False,
            module_type = 10,
        )),
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
