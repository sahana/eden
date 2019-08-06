# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Projects generic template
    """

    T = current.T

    settings.base.system_name = T("Sahana Project Management")
    settings.base.system_name_short = T("Sahana PM")

    # PrePopulate data
    settings.base.prepopulate += ("Projects",)
    #settings.base.prepopulate_demo += ("Projects/Demo",)

    # Theme (folder to use for views/layout.html)
    #settings.base.theme = "Projects"

    # Authentication settings
    # Should users be allowed to register themselves?
    #settings.security.self_registration = False
    # Do new users need to verify their email address?
    #settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    #settings.auth.registration_requests_organisation = True

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"

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

    # -------------------------------------------------------------------------
    # Setup
    settings.setup.wizard_questions += [{"question": "Will you record data for multiple Organisations?",
                                         "setting": "hrm.multiple_orgs",
                                         "options": {True: "Yes", False: "No"},
                                         },
                                        {"question": "Do you need support for Branch Organisations?",
                                         "setting": "org.branches",
                                         "options": {True: "Yes", False: "No"},
                                         },
                                        ]

    # -------------------------------------------------------------------------
    # Projects
    # Uncomment this to use settings suitable for a global/regional organisation (e.g. DRR)
    settings.project.mode_3w = True
    # Uncomment this to use DRR (Disaster Risk Reduction) extensions
    #settings.project.mode_drr = True
    # Uncomment this to use settings suitable for detailed Task management
    settings.project.mode_task = True
    # Uncomment this to use link Projects to Events
    settings.project.event_projects = True
    # Uncomment this to use Activities for Projects & Tasks
    settings.project.activities = True
    # Uncomment this to use link Activities to Events
    #settings.project.event_activities = True
    # Uncomment this to use Activity Types for Activities & Projects
    settings.project.activity_types = True
    # Uncomment this to filter dates in Activities
    #settings.project.activity_filter_year = True
    # Uncomment this to not use Beneficiaries for Activities
    #settings.project.get_project_activity_beneficiaries = False
    # Uncomment this to not use Item Catalog for Distributions
    #settings.project.activity_items = False
    # Uncomment this to use Codes for projects
    #settings.project.codes = True
    # Uncomment this to call project locations 'Communities'
    #settings.project.community = True
    # Uncomment this to enable Demographics in 3W projects
    settings.project.demographics = True
    # Uncomment this to enable Hazards in 3W projects
    settings.project.hazards = True
    # Uncomment this to enable Indicators in projects
    settings.project.indicators = True
    # Uncomment this to enable Milestones in projects
    settings.project.milestones = True
    # Uncomment this to use Projects for Activities & Tasks
    settings.project.projects = True
    # Uncomment this to disable Sectors in projects
    #settings.project.sectors = False
    # Uncomment this to enable Programmes in projects
    settings.project.programmes = True
    # Uncomment this to enable Budgets in Programmes
    settings.project.programme_budget = True
    # Uncomment this to enable Themes in 3W projects
    settings.project.themes = True
    # Uncomment this to use Theme Percentages for projects
    #settings.project.theme_percentages = True
    # Uncomment this to use multiple Budgets per project
    settings.project.multiple_budgets = True
    # Uncomment this to use multiple Organisations per project
    settings.project.multiple_organisations = True
    # Uncomment this to customise
    # Links to Filtered Components for Donors & Partners
    #settings.project.organisation_roles = {
    #    1: T("Lead Implementer"), # T("Host National Society")
    #    2: T("Partner"), # T("Partner National Society")
    #    3: T("Donor"),
    #    4: T("Customer"), # T("Beneficiary")?
    #    5: T("Super"), # T("Beneficiary")?
    #}
    #settings.project.organisation_lead_role = 1
    # Uncomment to customise the list of options for the Priority of a Task.
    # NB Be very cautious about doing this (see docstring in modules/s3cfg.py)
    #settings.project.task_priority_opts =
    # Uncomment to customise the list of options for the Status of a Task.
    # NB Be very cautious about doing this (see docstring in modules/s3cfg.py)
    #settings.project.task_status_opts =

    # -------------------------------------------------------------------------
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
        ("setup", Storage(
            name_nice = T("Setup"),
            #description = "Configuration Wizard",
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
        ("hrm", Storage(
            name_nice = T("Staff"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = 10,
        )),
        #("vol", Storage(
        #    name_nice = T("Volunteers"),
        #    #description = "Human Resources Management",
        #    restricted = True,
        #    module_type = 10,
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
        ("project", Storage(
            name_nice = T("Projects"),
            #description = "Tracking of Projects, Activities and Tasks",
            restricted = True,
            module_type = 1
        )),
        ("budget", Storage(
            name_nice = T("Budgets"),
            #description = "Budgets",
            restricted = True,
            # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
            module_type = None,
        )),
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
        #("cr", Storage(
        #    name_nice = T("Shelters"),
        #    #description = "Tracks the location, capacity and breakdown of victims in Shelters",
        #    restricted = True,
        #    module_type = 10
        #)),
        ("event", Storage(
            name_nice = T("Events"),
            #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
            restricted = True,
            module_type = 10,
        )),
        ("stats", Storage(
            name_nice = T("Statistics"),
            #description = "Manages statistics",
            restricted = True,
            module_type = None,
        )),
    ])

# END =========================================================================