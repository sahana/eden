# -*- coding: utf-8 -*-

from gluon import current
from gluon.storage import Storage
from gluon.contrib.simplejson.ordered_dict import OrderedDict
settings = current.deployment_settings
T = current.T

"""
    Template settings for Delphi Decision Maker
"""

settings.base.system_name = T("Decision Support 2.0")
settings.base.system_name_short = T("Decision Support 2.0")

# Pre-Populate
settings.base.prepopulate = ["Delphi"]

# Uncomment to Hide the language toolbar
#settings.L10n.display_toolbar = False

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
            module_type = None,
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
            module_type = None
        )),
    # All modules below here should be possible to disable safely
    ("delphi", Storage(
            name_nice = T("Delphi Decision Maker"),
            #description = "Supports the decision making of large groups of Crisis Management Experts by helping the groups create ranked list.",
            restricted = False,
            module_type = 1,
        )),
    #("cms", Storage(
    #      name_nice = T("Content Management"),
    #      #description = "Content Management System",
    #      restricted = True,
    #      module_type = 10,
    #  )),
    #("doc", Storage(
    #        name_nice = T("Documents"),
    #        #description = "A library of digital resources, such as photos, documents and reports",
    #        restricted = True,
    #        module_type = 10,
    #    )),
    #("hrm", Storage(
    #        name_nice = T("Staff"),
    #        #description = "Human Resources Management",
    #        restricted = True,
    #        module_type = 2,
    #    )),
    #("vol", Storage(
    #        name_nice = T("Volunteers"),
    #        #description = "Human Resources Management",
    #        restricted = True,
    #        module_type = 2,
    #    )),
    #("msg", Storage(
    #        name_nice = T("Messaging"),
    #        #description = "Sends & Receives Alerts via Email & SMS",
    #        restricted = True,
    #        # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
    #        module_type = None,
    #    )),
    #("project", Storage(
    #        name_nice = T("Projects"),
    #        #description = "Tracking of Projects, Activities and Tasks",
    #        restricted = True,
    #        module_type = 2
    #    )),
    #("survey", Storage(
    #        name_nice = T("Surveys"),
    #        #description = "Create, enter, and manage surveys.",
    #        restricted = True,
    #        module_type = 5,
    #    )),
])
