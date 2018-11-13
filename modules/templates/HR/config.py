# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Human Resources generic template
    """

    T = current.T

    #settings.base.system_name = T("Sahana Human Resources")
    #settings.base.system_name_short = T("Sahana")

    # PrePopulate data
    settings.base.prepopulate += ("HR",)
    #settings.base.prepopulate_demo += ("HR/Demo",)

    # Theme (folder to use for views/layout.html)
    #settings.base.theme = "HR"

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

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    #settings.gis.countries = ("US",)
    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

    # L10n settings
    # Languages used in the deployment (used for Language Toolbar, GIS Locations, etc)
    # http://www.loc.gov/standards/iso639-2/php/code_list.php
    #settings.L10n.languages = OrderedDict([
    #    ("ar", "Arabic"),
    #    ("bs", "Bosnian"),
    #    #("dv", "Divehi"), # Maldives
    #    ("en", "English"),
    #    ("fr", "French"),
    #    ("de", "German"),
    #    ("el", "Greek"),
    #    ("es", "Spanish"),
    #    #("id", "Bahasa Indonesia"),
    #    ("it", "Italian"),
    #    ("ja", "Japanese"),
    #    ("km", "Khmer"), # Cambodia
    #    ("ko", "Korean"),
    #    #("lo", "Lao"),
    #    #("mg", "Malagasy"),
    #    ("mn", "Mongolian"),
    #    #("ms", "Malaysian"),
    #    ("my", "Burmese"), # Myanmar
    #    ("ne", "Nepali"),
    #    ("prs", "Dari"), # Afghan Persian
    #    ("ps", "Pashto"), # Afghanistan, Pakistan
    #    ("pt", "Portuguese"),
    #    ("pt-br", "Portuguese (Brazil)"),
    #    ("ru", "Russian"),
    #    ("tet", "Tetum"),
    #    #("si", "Sinhala"), # Sri Lanka
    #    #("ta", "Tamil"), # India, Sri Lanka
    #    ("th", "Thai"),
    #    ("tl", "Tagalog"), # Philippines
    #    ("tr", "Turkish"),
    #    ("ur", "Urdu"), # Pakistan
    #    ("vi", "Vietnamese"),
    #    ("zh-cn", "Chinese (Simplified)"), # Mainland China
    #    ("zh-tw", "Chinese (Taiwan)"),
    #])
    # Default language for Language Toolbar (& GIS Locations in future)
    #settings.L10n.default_language = "en"
    # Uncomment to Hide the language toolbar
    #settings.L10n.display_toolbar = False
    # Default timezone for users
    #settings.L10n.utc_offset = "+0100"
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = ","
    # Uncomment this to Translate Layer Names
    #settings.L10n.translate_gis_layer = True
    # Uncomment this to Translate Location Names
    #settings.L10n.translate_gis_location = True
    # Uncomment this to Translate Organisation Names/Acronyms
    #settings.L10n.translate_org_organisation = True
    # Finance settings
    #settings.fin.currencies = {
    #    "EUR" : "Euros",
    #    "GBP" : "Great British Pounds",
    #    "USD" : "United States Dollars",
    #}
    #settings.fin.currency_default = "USD"

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
    # Organisations
    # Uncomment to use an Autocomplete for Organisation lookup fields
    #settings.org.autocomplete = True
    # Enable the Organisation Sector field
    #settings.org.sector = True
    # But hide it from the rheader
    #settings.org.sector_rheader = False
    # Enable the use of Organisation Branches
    #settings.org.branches = True
    # Show branches as tree rather than as table
    #settings.org.branches_tree_view = True
    # Make Facility Types Hierarchical
    #settings.org.facility_types_hierarchical = True
    # Enable the use of Organisation Groups & what their name is
    #settings.org.groups = "Coalition"
    #settings.org.groups = "Network"
    # Organisation Location context
    #settings.org.organisation_location_context = "organisation_location.location_id"
    # Make Organisation Types Hierarchical
    #settings.org.organisation_types_hierarchical = True
    # Make Organisation Types Multiple
    #settings.org.organisation_types_multiple = True
    # Show Organisation Types in the rheader
    #settings.org.organisation_type_rheader = True
    # Enable the use of Organisation Regions
    #settings.org.regions = True
    # Make Organisation Regions Hierarchical
    #settings.org.regions_hierarchical = True
    # Enable the use of Organisation Region Countries
    #settings.org.region_countries = True
    # Uncomment to show a Tab for Organisation Resources
    #settings.org.resources_tab = True
    # Make Services Hierarchical
    #settings.org.services_hierarchical = True
    # Set the length of the auto-generated org/site code the default is 10
    #settings.org.site_code_len = 3
    # Set the label for Sites
    #settings.org.site_label = "Facility"
    # Uncomment to show the date when a Site (Facilities-only for now) was last contacted
    #settings.org.site_last_contacted = True
    # Uncomment to use an Autocomplete for Site lookup fields
    #settings.org.site_autocomplete = True
    # Extra fields to search in Autocompletes & display in Representations
    #settings.org.site_autocomplete_fields = ("instance_type", "location_id$L1", "location_id$addr_street", "organisation_id$name")
    # Uncomment to hide inv & req tabs from Sites
    #settings.org.site_inv_req_tabs = False
    # Uncomment to allow Sites to be staffed by Volunteers
    #settings.org.site_volunteers = True
    # Uncomment to add summary fields for Organisations/Offices for # National/International staff
    #settings.org.summary = True
    # Enable certain fields just for specific Organisations
    # Requires a call to settings.set_org_dependent_field(field)
    # empty list => disabled for all (including Admin)
    #settings.org.dependent_fields = \
    #    {#"<table name>.<field name>"  : ["<Organisation Name>"],
    #     "pr_person_details.mother_name"             : [],
    #     "pr_person_details.father_name"             : [],
    #     "pr_person_details.company"                 : [],
    #     "pr_person_details.affiliations"            : [],
    #     "vol_volunteer.active"                      : [],
    #     "vol_volunteer_cluster.vol_cluster_type_id"      : [],
    #     "vol_volunteer_cluster.vol_cluster_id"          : [],
    #     "vol_volunteer_cluster.vol_cluster_position_id" : [],
    #     }
    # Uncomment to make Office codes unique
    #settings.org.office_code_unique = True
    # Uncomment to make Facility codes unique
    #settings.org.facility_code_unique = True
    # Uncomment to use Tags for Organisations, Offices & Facilities
    #settings.org.tags = True

    # -------------------------------------------------------------------------
    # Human Resource Management
    # Uncomment to change the label for 'Staff'
    #settings.hrm.staff_label = "Contacts"
    # Uncomment to allow Staff & Volunteers to be registered without an email address
    #settings.hrm.email_required = False
    # Uncomment to allow Staff & Volunteers to be registered without an Organisation
    #settings.hrm.org_required = False
    # Uncomment if their are only Staff & Volunteers from a single Organisation with no Branches
    #settings.hrm.multiple_orgs = False
    # Uncomment to disable the 'Send Message' action button
    #settings.hrm.compose_button = False
    # Uncomment to allow HR records to be deletable rather than just marking them as obsolete
    #settings.hrm.deletable = True
    # Uncomment to hide Job Titles
    #settings.hrm.use_job_titles = False
    # Uncomment to allow HRs to have multiple Job Titles
    #settings.hrm.multiple_job_titles = True
    # Uncomment to have each root Org use a different Job Title Catalog
    #settings.hrm.org_dependent_job_titles = True
    # Uncomment to display & search by National ID
    #settings.hrm.use_national_id = True
    # Uncomment to hide the Staff resource
    #settings.hrm.show_staff = False
    # Uncomment to have Staff use their Home Address as fallback if they have no Site defined
    #settings.hrm.location_staff = ("site_id", "person_id")
    # Uncomment to have Volunteers use their Site Address as fallback if they have no Home Address defined
    #settings.hrm.location_vol = ("person_id", "site_id")
    # Uncomment this to allow multiple site contacts per site (e.g. if needing a separate contact per sector)
    #settings.hrm.site_contact_unique = False
    # Uncomment to allow hierarchical categories of Skills, which each need their own set of competency levels.
    #settings.hrm.skill_types = True
    # Uncomment to disable Staff experience
    #settings.hrm.staff_experience = False
    # Uncomment to enable Volunteer 'active' field
    # - can also be made a function which is called to calculate the status based on recorded hours
    # Custom label for Organisations in HR module
    #settings.hrm.organisation_label = "Organization / Branch"
    # Custom label for Top-level Organisations in HR module
    #settings.hrm.root_organisation_label = "Organization"
    #settings.hrm.vol_active = True
    # Uncomment to define a Tooltip to show when viewing the Volunteer 'active' field
    #settings.hrm.vol_active_tooltip = "A volunteer is defined as active if they've participated in an average of 8 or more hours of Program work or Trainings per month in the last year"
    # Uncomment to disable Volunteer experience
    #settings.hrm.vol_experience = False
    # Uncomment to show the Organisation name in HR represents
    #settings.hrm.show_organisation = True
    # Uncomment to consolidate tabs into a single CV
    #settings.hrm.cv_tab = True
    # Uncomment to consolidate tabs into Staff Record (set to False to hide the tab)
    #settings.hrm.record_tab = "record"
    # Uncomment to disable the use of Volunteer Awards
    #settings.hrm.use_awards = False
    # Uncomment to disable the use of HR Certificates
    #settings.hrm.use_certificates = False
    # Uncomment to filter certificates by (root) Organisation & hence not allow Certificates from other orgs to be added to a profile (except by Admin)
    #settings.hrm.filter_certificates = True
    # Uncomment to auto-create certificates for courses
    #settings.hrm.create_certificates_from_courses = True
    # Uncomment to enable the use of Staff/Volunteer IDs
    #settings.hrm.use_code = True
    # Uncomment to disable the use of HR Credentials
    #settings.hrm.use_credentials = False
    # Uncomment to disable the use of HR Description
    #settings.hrm.use_description = None
    # Uncomment to enable the use of HR Education
    #settings.hrm.use_education = True
    # Uncomment to disable the use of HR ID Tab
    #settings.hrm.use_id = False
    # Uncomment to disable the use of HR Address Tab
    #settings.hrm.use_address = False
    # Uncomment to disable the use of HR Skills
    #settings.hrm.use_skills = False
    # Uncomment to enable tracking of staff salaries
    #settings.hrm.salary = True
    # Uncomment to disable the use of HR Teams
    #settings.hrm.teams = False
    # Uncomment to disable the use of HR Trainings
    #settings.hrm.use_trainings = False
    # Uncomment this to configure tracking of internal/external training instructors
    #settings.hrm.training_instructors = "external"
    # Uncomment this to modify the training filter to be AND not OR
    #settings.hrm.training_filter_and = True
    # Uncomment this to have Pass marks defined by Course
    #settings.hrm.course_pass_marks = True
    # Uncomment to use activity types in experience record, specify as {"code":"label", ...}
    #settings.hrm.activity_types = {"rdrt": "RDRT Mission"}

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
            module_type = 1
        )),
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
        #("project", Storage(
        #    name_nice = T("Projects"),
        #    #description = "Tracking of Projects, Activities and Tasks",
        #    restricted = True,
        #    module_type = 2
        #)),
        #("cr", Storage(
        #    name_nice = T("Shelters"),
        #    #description = "Tracks the location, capacity and breakdown of victims in Shelters",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("hms", Storage(
        #    name_nice = T("Hospitals"),
        #    #description = "Helps to monitor status of hospitals",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("dvr", Storage(
        #   name_nice = T("Disaster Victim Registry"),
        #   #description = "Allow affected individuals & households to register to receive compensation and distributions",
        #   restricted = True,
        #   module_type = 10,
        #)),
        ("event", Storage(
            name_nice = T("Events"),
            #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
            restricted = True,
            module_type = 10,
        )),
        #("transport", Storage(
        #   name_nice = T("Transport"),
        #   restricted = True,
        #   module_type = 10,
        #)),
        #("stats", Storage(
        #    name_nice = T("Statistics"),
        #    #description = "Manages statistics",
        #    restricted = True,
        #    module_type = None,
        #)),
    ])

# END =========================================================================