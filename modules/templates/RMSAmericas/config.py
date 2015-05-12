# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Template settings: 'Skeleton' designed to be copied to quickly create
                           custom templates

        All settings which are to configure a specific template are located
        here. Deployers should ideally not need to edit any other files outside
        of their template folder.
    """

    T = current.T

    # -----------------------------------------------------------------------------
    # System Name
    #
    settings.base.system_name = T("Resource Management System")
    settings.base.system_name_short = T("RMS")

    # -----------------------------------------------------------------------------
    # Pre-Populate
    #
    #settings.base.prepopulate = ("IFRC", "IFRC/Train", "IFRC/Demo")
    settings.base.prepopulate = ("IFRC", "IFRC/Train")

    # -----------------------------------------------------------------------------
    # Theme (folder to use for views/layout.html)
    #
    settings.base.theme = "RMSAmericas"

    # Uncomment to disable responsive behavior of datatables
    #settings.ui.datatables_responsive = False

    # @todo: configure custom icons
    #settings.ui.custom_icons = {
    #    "male": "icon-male",
    #    "female": "icon-female",
    #    "medical": "icon-plus-sign-alt",
    #}

    # @todo: verify these:
    settings.gis.map_height = 600
    settings.gis.map_width = 869

    # Display Resources recorded to Admin-Level Locations on the map
    # @ToDo: Move into gis_config?
    settings.gis.display_L0 = True

    # GeoNames username
    settings.gis.geonames_username = "rms_dev"

    # -----------------------------------------------------------------------------
    # Security Policy
    #
    settings.security.policy = 8 # Delegations
    settings.security.map = True

    # -----------------------------------------------------------------------------
    # User Self-Registration
    #
    #settings.security.self_registration = False
    settings.auth.registration_requires_approval = True
    settings.auth.registration_requires_verification = True
    settings.auth.registration_requests_organisation = True
    settings.auth.registration_organisation_required = True
    settings.auth.registration_requests_site = True

    settings.auth.registration_link_user_to = {"staff": T("Staff"),
                                               "volunteer": T("Volunteer"),
                                               "member": T("Member")
                                               }

    # @ToDo: Should we fallback to organisation_id if site_id is None?
    settings.auth.registration_roles = {"site_id": ["reader",
                                                    ],
                                        }

    # -------------------------------------------------------------------------
    # Record Approval
    #
    settings.auth.record_approval = True

    # -------------------------------------------------------------------------
    # Realm Rules
    # @todo: replicate realm rules from IFRC template?
    #
    settings.auth.person_realm_human_resource_site_then_org = True
    settings.auth.person_realm_member_org = True

    # Activate entity role manager tabs for OrgAdmins
    settings.auth.entity_role_manager = True

    # -----------------------------------------------------------------------------
    # L10n (Localization) settings
    # @todo: adjust
    #
    settings.L10n.languages = OrderedDict([
        ("en-gb", "English"),
        ("es", "Español"),
        #("fr", "Français"),
        ("km", "ភាសាខ្មែរ"),        # Khmer
        ("mn", "Монгол хэл"),   # Mongolian
        ("ne", "नेपाली"),          # Nepali
        ("prs", "دری"),         # Dari
        ("ps", "پښتو"),         # Pashto
        #("th", "ภาษาไทย"),        # Thai
        ("vi", "Tiếng Việt"),   # Vietnamese
        ("zh-cn", "中文 (简体)"),
    ])
    # Default Language
    settings.L10n.default_language = "en-gb"
    # Default timezone for users
    settings.L10n.utc_offset = "+0700"
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = ","
    # Unsortable 'pretty' date format (for use in English)
    settings.L10n.date_format = "%d-%b-%Y"
    # Make last name in person/user records mandatory
    settings.L10n.mandatory_lastname = True
    # Uncomment this to Translate Layer Names
    settings.L10n.translate_gis_layer = True
    # Translate Location Names
    settings.L10n.translate_gis_location = True
    # Uncomment this for Alternate Location Names
    settings.L10n.name_alt_gis_location = True
    # Uncomment this to Translate Organisation Names/Acronyms
    settings.L10n.translate_org_organisation = True

    # -----------------------------------------------------------------------------
    # Finance settings
    # @todo: adjust
    #
    settings.fin.currencies = {
       "EUR" : T("Euros"),
       "GBP" : T("Great British Pounds"),
       "USD" : T("United States Dollars"),
    }
    settings.fin.currency_default = "USD"

    # -----------------------------------------------------------------------------
    # Use the label 'Camp' instead of 'Shelter'
    #
    settings.ui.camp = True

    # -----------------------------------------------------------------------------
    # Filter Manager
    #
    settings.search.filter_manager = False

    # -----------------------------------------------------------------------------
    # Default Summary
    #
    settings.ui.summary = ({"common": True,
                            "name": "add",
                            "widgets": [{"method": "create"}],
                            },
                           {"name": "table",
                            "label": "Table",
                            "widgets": [{"method": "datatable"}],
                            },
                           {"name": "charts",
                            "label": "Report",
                            "widgets": [{"method": "report", "ajax_init": True}],
                            },
                           {"name": "map",
                            "label": "Map",
                            "widgets": [{"method": "map", "ajax_init": True}],
                            },
                           )

    # -----------------------------------------------------------------------------
    # Content Management
    #
    settings.cms.hide_index = True
    settings.cms.richtext = True

    # -----------------------------------------------------------------------------
    # Messaging
    # Parser
    settings.msg.parser = "IFRC"

    # =============================================================================
    # Module Settings

    # -----------------------------------------------------------------------------
    # Organisation Management
    # @todo: adjust
    #
    # Enable the use of Organisation Branches
    settings.org.branches = True
    # Set the length of the auto-generated org/site code the default is 10
    settings.org.site_code_len = 3
    # Set the label for Sites
    settings.org.site_label = "Office/Warehouse/Facility"

    # Enable certain fields just for specific Organisations
    #settings.org.dependent_fields = \
    #    {"pr_person.middle_name"                     : (CVTL, VNRC),
    #     "pr_person_details.mother_name"             : (BRCS, ),
    #     "pr_person_details.father_name"             : (ARCS, BRCS),
    #     "pr_person_details.grandfather_name"        : (ARCS, ),
    #     "pr_person_details.affiliations"            : (PRC, ),
    #     "pr_person_details.company"                 : (PRC, ),
    #     "vol_details.availability"                  : (VNRC, ),
    #     "vol_details.card"                          : (ARCS, ),
    #     "vol_volunteer_cluster.vol_cluster_type_id"     : (PRC, ),
    #     "vol_volunteer_cluster.vol_cluster_id"          : (PRC, ),
    #     "vol_volunteer_cluster.vol_cluster_position_id" : (PRC, ),
    #     }

    # -----------------------------------------------------------------------------
    # Human Resource Management
    # @todo: adjust
    #
    # Uncomment to allow Staff & Volunteers to be registered without an email address
    settings.hrm.email_required = False
    # Uncomment to filter certificates by (root) Organisation & hence not allow Certificates from other orgs to be added to a profile (except by Admin)
    settings.hrm.filter_certificates = True
    # Uncomment to show the Organisation name in HR represents
    settings.hrm.show_organisation = True
    # Uncomment to allow HRs to have multiple Job Titles
    settings.hrm.multiple_job_titles = True
    # Uncomment to have each root Org use a different Job Title Catalog
    settings.hrm.org_dependent_job_titles = True
    # Uncomment to disable the use of HR Credentials
    settings.hrm.use_credentials = False
    # Uncomment to enable the use of HR Education
    settings.hrm.use_education = True
    # Custom label for Organisations in HR module
    settings.hrm.organisation_label = "National Society / Branch"
    # Uncomment to consolidate tabs into a single CV
    settings.hrm.cv_tab = True
    # Uncomment to consolidate tabs into Staff Record (set to False to hide the tab)
    settings.hrm.record_tab = "record"

    # Uncomment to do a search for duplicates in the new AddPersonWidget2
    settings.pr.lookup_duplicates = True

    # -----------------------------------------------------------------------------
    # RDRT
    #
    settings.deploy.hr_label = "Member"
    #settings.customise_deploy_home = deploy_index
    # Enable the use of Organisation Regions
    settings.org.regions = True
    # Make Organisation Regions Hierarchical
    settings.org.regions_hierarchical = True
    # Uncomment to allow hierarchical categories of Skills, which each need their own set of competency levels.
    settings.hrm.skill_types = True
    # RDRT overrides these within controller:
    # Uncomment to disable Staff experience
    settings.hrm.staff_experience = False
    # Uncomment to disable the use of HR Skills
    settings.hrm.use_skills = False
    # Activity types for experience record
    settings.hrm.activity_types = {"rdrt": "RDRT Mission"}

    # -----------------------------------------------------------------------------
    # Projects
    # Uncomment this to use settings suitable for a global/regional organisation (e.g. DRR)
    settings.project.mode_3w = True
    # Uncomment this to use DRR (Disaster Risk Reduction) extensions
    settings.project.mode_drr = True
    # Uncomment this to use Activity Types for Activities & Projects
    settings.project.activity_types = True
    # Uncomment this to use Codes for projects
    settings.project.codes = True
    # Uncomment this to call project locations 'Communities'
    settings.project.community = True
    # Uncomment this to enable Hazards in 3W projects
    settings.project.hazards = True
    # Uncomment this to enable Indicators in projects
    # Just HNRC
    #settings.project.indicators = True
    # Uncomment this to use multiple Budgets per project
    settings.project.multiple_budgets = True
    # Uncomment this to use multiple Organisations per project
    settings.project.multiple_organisations = True
    # Uncomment this to enable Programmes in projects
    settings.project.programmes = True
    # Uncomment this to enable Themes in 3W projects
    settings.project.themes = True
    # Uncomment this to customise
    # Links to Filtered Components for Donors & Partners
    settings.project.organisation_roles = {
        1: T("Host National Society"),
        2: T("Partner"),
        3: T("Donor"),
        #4: T("Customer"), # T("Beneficiary")?
        #5: T("Supplier"),
        9: T("Partner National Society"),
    }

    # -----------------------------------------------------------------------------
    # Inventory Management
    settings.inv.show_mode_of_transport = True
    settings.inv.send_show_time_in = True
    #settings.inv.collapse_tabs = True
    # Uncomment if you need a simpler (but less accountable) process for managing stock levels
    settings.inv.direct_stock_edits = True
    settings.inv.org_dependent_warehouse_types = True
    # Settings for HNRC:
    settings.inv.stock_count = False
    settings.inv.item_status = {#0: current.messages["NONE"], # Not defined yet
                                0: T("Good"),
                                1: T("Damaged"),
                                #1: T("Dump"),
                                #2: T("Sale"),
                                #3: T("Reject"),
                                #4: T("Surplus")
                                }
    settings.inv.recv_types = {#0: current.messages["NONE"], In Shipment Types
                               #11: T("Internal Shipment"), In Shipment Types
                               32: T("Donation"),
                               34: T("Purchase"),
                               36: T("Consignment"), # Borrowed
                               37: T("In Transit"),  # Loaning warehouse space to another agency
                               }


    # -----------------------------------------------------------------------------
    # Request Management
    # Uncomment to disable Inline Forms in Requests module
    settings.req.inline_forms = False
    settings.req.req_type = ["Stock"]
    settings.req.use_commit = False
    # Should Requests ask whether Transportation is required?
    settings.req.ask_transport = True
    settings.req.pack_values = False
    # Disable Request Matching as we don't wwant users making requests to see what stock is available
    settings.req.prompt_match = False
    # Uncomment to disable Recurring Request
    settings.req.recurring = False # HNRC

    # =============================================================================
    # Template Modules
    #
    settings.modules = OrderedDict([
        # Core modules which shouldn't be disabled
        ("default", Storage(
                name_nice = "RMS",
                restricted = False, # Use ACLs to control access to this module
                access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
                #module_type = None  # This item is not shown in the menu
            )),
        ("admin", Storage(
                name_nice = T("Administration"),
                #description = "Site Administration",
                restricted = True,
                access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
                #module_type = None  # This item is handled separately for the menu
            )),
        ("appadmin", Storage(
                name_nice = T("Administration"),
                #description = "Site Administration",
                restricted = True,
                #module_type = None  # No Menu
            )),
        ("errors", Storage(
                name_nice = T("Ticket Viewer"),
                #description = "Needed for Breadcrumbs",
                restricted = False,
                #module_type = None  # No Menu
            )),
        ("sync", Storage(
                name_nice = T("Synchronization"),
                #description = "Synchronization",
                restricted = True,
                access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
                #module_type = None  # This item is handled separately for the menu
            )),
        ("translate", Storage(
                name_nice = T("Translation Functionality"),
                #description = "Selective translation of strings based on module.",
                #module_type = None,
            )),
        # Uncomment to enable internal support requests
        ("support", Storage(
                name_nice = T("Support"),
                #description = "Support Requests",
                restricted = True,
                #module_type = None  # This item is handled separately for the menu
            )),
        ("gis", Storage(
                name_nice = T("Map"),
                #description = "Situation Awareness & Geospatial Analysis",
                restricted = True,
                #module_type = 6,     # 6th item in the menu
            )),
        ("pr", Storage(
                name_nice = T("Person Registry"),
                #description = "Central point to record details on People",
                restricted = True,
                access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
                #module_type = 10
            )),
        ("org", Storage(
                name_nice = T("Organizations"),
                #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
                restricted = True,
                #module_type = 1
            )),
        # All modules below here should be possible to disable safely
        ("hrm", Storage(
                name_nice = T("Staff"),
                #description = "Human Resources Management",
                restricted = True,
                #module_type = 2,
            )),
        ("vol", Storage(
                name_nice = T("Volunteers"),
                #description = "Human Resources Management",
                restricted = True,
                #module_type = 2,
            )),
        ("cms", Storage(
                name_nice = T("Content Management"),
                #description = "Content Management System",
                restricted = True,
                module_type = None,
            )),
        ("doc", Storage(
                name_nice = T("Documents"),
                #description = "A library of digital resources, such as photos, documents and reports",
                restricted = True,
                #module_type = 10,
            )),
        ("msg", Storage(
                name_nice = T("Messaging"),
                #description = "Sends & Receives Alerts via Email & SMS",
                restricted = True,
                # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
                #module_type = None,
            )),
        ("supply", Storage(
                name_nice = T("Supply Chain Management"),
                #description = "Used within Inventory Management, Request Management and Asset Management",
                restricted = True,
                #module_type = None, # Not displayed
            )),
        ("inv", Storage(
                name_nice = T("Warehouses"),
                #description = "Receiving and Sending Items",
                restricted = True,
                #module_type = 4
            )),
        ("asset", Storage(
                name_nice = T("Assets"),
                #description = "Recording and Assigning Assets",
                restricted = True,
                #module_type = 5,
            )),
        ("req", Storage(
                name_nice = T("Requests"),
                #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
                restricted = True,
                #module_type = 10,
            )),
        ("project", Storage(
                name_nice = T("Projects"),
                #description = "Tracking of Projects, Activities and Tasks",
                restricted = True,
                #module_type = 2
            )),
        ("budget", Storage(
                name_nice = T("Budgets"),
                #description = "Tracking of Budgets",
                restricted = True,
                #module_type = None
            )),
        ("survey", Storage(
                name_nice = T("Assessments"),
                #description = "Create, enter, and manage surveys.",
                restricted = True,
                #module_type = 5,
            )),
        ("event", Storage(
                name_nice = T("Events"),
                #description = "Events",
                restricted = True,
                #module_type = 10
            )),
        ("member", Storage(
               name_nice = T("Members"),
               #description = "Membership Management System",
               restricted = True,
               #module_type = 10,
           )),
        ("deploy", Storage(
               name_nice = T("Regional Disaster Response Teams"),
               #description = "Alerting and Deployment of Disaster Response Teams",
               restricted = True,
               #module_type = 10,
           )),
        ("po", Storage(
               name_nice = T("Recovery Outreach"),
               #description = "Population Outreach",
               restricted = True,
               #module_type = 10,
           )),
        ("stats", Storage(
                name_nice = T("Statistics"),
                #description = "Manages statistics",
                restricted = True,
                #module_type = None,
            )),
        ("vulnerability", Storage(
                name_nice = T("Vulnerability"),
                #description = "Manages vulnerability indicators",
                restricted = True,
                #module_type = 10,
            )),
    ])

# END =========================================================================