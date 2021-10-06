# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Template settings for a Demo of Sahana Eden
        - simplified Security
        - 'Kitchen Sink' selection of modules
    """

    T = current.T

    # Pre-Populate
    # http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/PrePopulate
    settings.base.prepopulate.append("default/Demo")

    # Enable Guided Tours
    # - defaults to module enabled or not
    #settings.base.guided_tour = True

    # Authentication settings
    # Should users be allowed to register themselves?
    #settings.security.self_registration = True
    # Do new users need to verify their email address?
    #settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    settings.auth.registration_requires_approval = False

    # Allow a new user to be linked to a record (and a new record will be created if it doesn't already exist)
    settings.auth.registration_link_user_to = {"staff": T("Staff"),
                                               "volunteer": T("Volunteer"),
                                               "member": T("Member"),
                                               }

    # Always notify the approver of a new (verified) user, even if the user is automatically approved
    settings.auth.always_notify_approver = False

    # L10n settings
    # Languages used in the deployment (used for Language Toolbar, GIS Locations, etc)
    # http://www.loc.gov/standards/iso639-2/php/code_list.php
    settings.L10n.languages = OrderedDict([
        ("ar", "Arabic"),
        ("bs", "Bosnian"),
        #("crs", "Seychellois Creole"),
        #("dv", "Divehi"), # Maldives
        #("dz", "Dzongkha"), # Bhutan
        ("en", "English"),
        ("fr", "French"),
        ("de", "German"),
        ("el", "Greek"),
        ("es", "Spanish"),
        #("id", "Bahasa Indonesia"),
        ("it", "Italian"),
        ("ja", "Japanese"),
        ("km", "Khmer"), # Cambodia
        ("ko", "Korean"),
        #("lo", "Lao"),
        #("lt", "Lithuanian"),
        #("mg", "Malagasy"),
        ("mn", "Mongolian"),
        #("ms", "Malaysian"),
        ("my", "Burmese"), # Myanmar
        ("ne", "Nepali"),
        ("pl", "Polish"),
        ("prs", "Dari"), # Afghan Persian
        ("ps", "Pashto"), # Afghanistan, Pakistan
        ("pt", "Portuguese"),
        ("pt-br", "Portuguese (Brazil)"),
        ("ru", "Russian"),
        ("tet", "Tetum"),
        #("si", "Sinhala"), # Sri Lanka
        #("so", "Somali"),
        #("ta", "Tamil"), # India, Sri Lanka
        ("th", "Thai"),
        ("tl", "Tagalog"), # Philippines
        ("tr", "Turkish"),
        ("ur", "Urdu"), # Pakistan
        ("vi", "Vietnamese"),
        ("zh-cn", "Chinese (Simplified)"), # Mainland China
        ("zh-tw", "Chinese (Taiwan)"),
    ])

    # AAA Settings

    # Security Policy
    # http://eden.sahanafoundation.org/wiki/S3AAA#System-widePolicy
    # 1: Simple (default): Global as Reader, Authenticated as Editor
    # 2: Editor role required for Update/Delete, unless record owned by session
    # 3: Apply Controller ACLs
    # 4: Apply both Controller & Function ACLs
    # 5: Apply Controller, Function & Table ACLs
    # 6: Apply Controller, Function, Table ACLs and Entity Realm
    # 7: Apply Controller, Function, Table ACLs and Entity Realm + Hierarchy
    settings.security.policy = 1 # Simple Policy

    # Events
    # Uncomment this to use link Projects to Events
    settings.project.event_projects = True

    # -------------------------------------------------------------------------
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
            #description = "WebSetup",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
             module_type = None  # No Menu
        )),
        ("sync", Storage(
            name_nice = T("Synchronization"),
            #description = "Synchronization",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
        #("tour", Storage(
        #    name_nice = T("Guided Tour Functionality"),
        #    module_type = None,
        #)),
        ("translate", Storage(
            name_nice = T("Translation Functionality"),
            #description = "Selective translation of strings based on module.",
            module_type = None,
        )),
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
            name_nice = T("Warehouses"),
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
        #("survey", Storage(
        #    name_nice = T("Surveys"),
        #    #description = "Create, enter, and manage surveys.",
        #    restricted = True,
        #    module_type = 5,
        #)),
        ("dc", Storage(
           name_nice = T("Assessments"),
           #description = "Data collection tool",
           restricted = True,
           module_type = 5
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
        #("disease", Storage(
        #    name_nice = T("Disease Tracking"),
        #    #description = "Helps to track cases and trace contacts in disease outbreaks",
        #    restricted = True,
        #    module_type = 10
        #)),
        ("br", Storage(
            name_nice = T("Beneficiary Registry"),
            #description = "Beneficiary Registry and Case Management",
            restricted = True,
            module_type = 10,
        )),
        ("event", Storage(
            name_nice = T("Events"),
            #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
            restricted = True,
            module_type = 10,
        )),
        #("transport", Storage(
        #    name_nice = T("Transport"),
        #    restricted = True,
        #    module_type = 10,
        #)),
        ("stats", Storage(
            name_nice = T("Statistics"),
            #description = "Manages statistics",
            restricted = True,
            module_type = None,
        )),
        ("member", Storage(
            name_nice = T("Members"),
            #description = "Membership Management System",
            restricted = True,
            module_type = 10,
        )),
        #("budget", Storage(
        #    name_nice = T("Budgeting Module"),
        #    #description = "Allows a Budget to be drawn up",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("deploy", Storage(
        #    name_nice = T("Deployments"),
        #    #description = "Manage Deployments",
        #    restricted = True,
        #    module_type = 10,
        #)),
        # Deprecated: Replaced by event
        #("irs", Storage(
        #    name_nice = T("Incidents"),
        #    #description = "Incident Reporting System",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("dvi", Storage(
        #   name_nice = T("Disaster Victim Identification"),
        #   #description = "Disaster Victim Identification",
        #   restricted = True,
        #   module_type = 10,
        #   #access = "|DVI|",      # Only users with the DVI role can see this module in the default menu & access the controller
        #)),
        #("edu", Storage(
        #    name_nice = T("Schools"),
        #    #description = "Helps to monitor status of schools",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("mpr", Storage(
        #   name_nice = T("Missing Person Registry"),
        #   #description = "Helps to report and search for missing persons",
        #   restricted = True,
        #   module_type = 10,
        #)),
        #("vulnerability", Storage(
        #    name_nice = T("Vulnerability"),
        #    #description = "Manages vulnerability indicators",
        #    restricted = True,
        #    module_type = 10,
        # )),
        #("fire", Storage(
        #   name_nice = T("Fire Stations"),
        #   #description = "Fire Station Management",
        #   restricted = True,
        #   module_type = 1,
        #)),
        #("water", Storage(
        #    name_nice = T("Water"),
        #    #description = "Flood Gauges show water levels in various parts of the country",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("patient", Storage(
        #    name_nice = T("Patient Tracking"),
        #    #description = "Tracking of Patients",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("po", Storage(
        #    name_nice = T("Population Outreach"),
        #    #description = "Population Outreach",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("security", Storage(
        #   name_nice = T("Security"),
        #   #description = "Security Management System",
        #   restricted = True,
        #   module_type = 10,
        #)),
        # These are specialist modules
        #("cap", Storage(
        #    name_nice = T("CAP"),
        #    #description = "Create & broadcast CAP alerts",
        #    restricted = True,
        #    module_type = 10,
        #)),
        # Requires RPy2 & PostgreSQL
        #("climate", Storage(
        #    name_nice = T("Climate"),
        #    #description = "Climate data portal",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("delphi", Storage(
        #    name_nice = T("Delphi Decision Maker"),
        #    #description = "Supports the decision making of large groups of Crisis Management Experts by helping the groups create ranked list.",
        #    restricted = False,
        #    module_type = 10,
        #)),
        # @ToDo: Port these Assessments to the Survey module
        #("building", Storage(
        #    name_nice = T("Building Assessments"),
        #    #description = "Building Safety Assessments",
        #    restricted = True,
        #    module_type = 10,
        #)),
        # Deprecated by Surveys module
        # - depends on CR, IRS & Impact
        #("assess", Storage(
        #    name_nice = T("Assessments"),
        #    #description = "Rapid Assessments & Flexible Impact Assessments",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("impact", Storage(
        #    name_nice = T("Impacts"),
        #    #description = "Used by Assess",
        #    restricted = True,
        #    module_type = None,
        #)),
        #("ocr", Storage(
        #   name_nice = T("Optical Character Recognition"),
        #   #description = "Optical Character Recognition for reading the scanned handwritten paper forms.",
        #   restricted = False,
        #   module_type = None,
        #)),
        #("work", Storage(
        #   name_nice = T("Jobs"),
        #   #description = "Simple Volunteer Jobs Management",
        #   restricted = False,
        #   module_type = None,
        #)),
    ])

# END =========================================================================
