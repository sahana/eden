# -*- coding: utf-8 -*-

from gluon import current
from gluon.storage import Storage
from gluon.contrib.simplejson.ordered_dict import OrderedDict
settings = current.deployment_settings
T = current.T

"""
    Template settings for IFRC
"""
# =============================================================================
# System Settings
# -----------------------------------------------------------------------------
# Authorization Settings
settings.auth.registration_requires_approval = True
settings.auth.registration_requires_verification = True
settings.auth.registration_requests_organisation = True
settings.auth.registration_organisation_required = True
settings.auth.registration_requests_site = True
settings.auth.record_approval = True

settings.auth.registration_roles = {"site_id": ["asset_reader",
                                                "inv_reader",
                                                "irs_reader",
                                                "member_reader",
                                                "project_reader",
                                                "staff_reader",
                                                "vol_reader",
                                                "survey_reader",
                                                "vulnerability_reader",
                                                ],
                                    }

# -----------------------------------------------------------------------------
# Security Policy
settings.security.policy = 8 # Delegations
settings.security.map = True

# Owner Entity
settings.auth.person_realm_human_resource_site_then_org = True
settings.auth.person_realm_member_org = True

def ifrc_realm_entity(table, row):
    """
        Assign a Realm Entity to records
    """

    tablename = table._tablename

    # Do not apply realms for Master Data
    # @ToDo: Restore Realms and add a role/functionality support for Master Data  
    if tablename in ["hrm_department",
                     "hrm_job_role",
                     "hrm_job_title",
                     "hrm_course",
                     "hrm_programme"]:
        return None

    db = current.db
    s3db = current.s3db

    # Entity reference fields
    EID = "pe_id"
    OID = "organisation_id"
    SID = "site_id"
    GID = "group_id"
    PID = "person_id"
    entity_fields = (EID, OID, SID, GID, PID)

    # Entity tables
    otablename = "org_organisation"
    stablename = "org_site"
    gtablename = "pr_group"
    ptablename = "pr_person"

    # Owner Entity Foreign Key
    realm_entity_fks = dict(pr_contact = EID,
                            pr_physical_description = EID,
                            pr_address = EID,
                            pr_image = EID,
                            pr_identity = "person_id",
                            pr_education = "person_id",
                            pr_note = "person_id",
                            hrm_human_resource = "site_id",
                            inv_recv = "site_id",
                            inv_recv_item = "req_id",
                            inv_track_item = "track_org_id",
                            inv_adj_item = "adj_id",
                            req_req_item = "req_id"
                            )

    # Default Foreign Keys (ordered by priority)
    default_fks = ["catalog_id",
                   "project_id",
                   "project_location_id"
                   ]

    # Link Tables
    realm_entity_link_table = dict(
        project_task = Storage(tablename = "project_task_project",
                               link_key = "task_id"
                               )
        )
    if tablename in realm_entity_link_table:
        # Replace row with the record from the link table
        link_table = realm_entity_link_table[tablename]
        table = s3db[link_table.tablename]
        rows = db(table[link_table.link_key] == row.id).select(table.id,
                                                               limitby=(0, 1))
        if rows:
            # Update not Create
            row = rows.first()

    # Check if there is a FK to inherit the realm_entity
    realm_entity = 0
    fk = realm_entity_fks.get(tablename,None)
    for default_fk in [fk] + default_fks:
        if default_fk in table.fields:
            fk = default_fk
            # Inherit realm_entity from parent record
            if fk == EID:
                ftable = s3db.pr_person
                query = ftable[EID] == row[EID]
            else:
                ftablename = table[fk].type[10:] # reference tablename
                ftable = s3db[ftablename]
                query = (table.id == row.id) & \
                        (table[fk] == ftable.id)
            record = db(query).select(ftable.realm_entity,
                                      limitby=(0, 1)).first()
            if record:
                realm_entity = record.realm_entity
                break
            else:
                realm_entity = 0 # Fall back to default get_realm_entity function
                # continue to loop through the rest of the default_fks
                
    
    use_user_organisation = False
    # Suppliers & Partners are owned by the user's organisation
    if realm_entity == 0 and tablename == "org_organisation":
        ott = s3db.org_organisation_type
        row = table[row.id]
        row = db(table.organisation_type_id == ott.id).select(ott.name,
                                                              limitby = (0,1)
                                                              ).first()
        
        if row and row.name != "Red Cross / Red Crescent":
            use_user_organisation = True

    # Groups are owned by the user's organisation
    if tablename in ["pr_group"]:
        use_user_organisation = True

    user = current.auth.user
    if use_user_organisation and user:
        # @ToDo - this might cause issues if the user's org is different from the realm that gave them permissions to create the Org 
        realm_entity = s3db.pr_get_pe_id("org_organisation",
                                         user.organisation_id)

    return realm_entity
settings.auth.realm_entity = ifrc_realm_entity

# -----------------------------------------------------------------------------
# Pre-Populate
settings.base.prepopulate = ["IFRC_Train"]

settings.base.system_name = T("Resource Management System")
settings.base.system_name_short = T("RMS")

# -----------------------------------------------------------------------------
# Theme (folder to use for views/layout.html)
settings.base.theme = "IFRC"
settings.gis.map_height = 600
settings.gis.map_width = 854
# Display Resources recorded to Admin-Level Locations on the map
# @ToDo: Move into gis_config?
settings.gis.display_L0 = True

# -----------------------------------------------------------------------------
# L10n (Localization) settings
settings.L10n.languages = OrderedDict([
    ("en-gb", "English"),
    ("es", "Español"),
])
# Default Language
settings.L10n.default_language = "en-gb"
# Default timezone for users
settings.L10n.utc_offset = "UTC +0700"
# Number formats (defaults to ISO 31-0)
# Decimal separator for numbers (defaults to ,)
settings.L10n.decimal_separator = "."
# Thousands separator for numbers (defaults to space)
settings.L10n.thousands_separator = ","
# Unsortable 'pretty' date format
settings.L10n.date_format = T("%d-%b-%y")
settings.L10n.datetime_format = T("%d-%b-%Y %H:%M:%S")
# Make last name in person/user records mandatory
settings.L10n.mandatory_lastname = True

# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# Enable this for a UN-style deployment
#settings.ui.cluster = True
# Enable this to use the label 'Camp' instead of 'Shelter'
settings.ui.camp = True

# -----------------------------------------------------------------------------
# Save Search Widget
settings.save_search.widget = False


# =============================================================================
# Module Settings

# -----------------------------------------------------------------------------
# Organisation Management
# Set the length of the auto-generated org/site code the default is 10
settings.org.site_code_len = 3
# Set the label for Sites
settings.org.site_label = "Office/Warehouse/Facility"
# Enable certain fields just for specific Organisations
settings.org.dependent_fields = \
    {"pr_person_details.mother_name"             : ["Bangladesh Red Crescent Society"],
     "pr_person_details.father_name"             : ["Bangladesh Red Crescent Society"],
     "pr_person_details.company"                 : ["Philippine Red Cross"],
     "pr_person_details.affiliations"            : ["Philippine Red Cross"],
     "vol_volunteer.active"                      : ["Timor-Leste Red Cross Society"],
     "vol_volunteer_cluster.vol_cluster_type_id"      : ["Philippine Red Cross"],
     "vol_volunteer_cluster.vol_cluster_id"          : ["Philippine Red Cross"],
     "vol_volunteer_cluster.vol_cluster_position_id" : ["Philippine Red Cross"],
     }

# -----------------------------------------------------------------------------
# Human Resource Management
# Uncomment to allow Staff & Volunteers to be registered without an email address
settings.hrm.email_required = False
# Uncomment to show the Organisation name in HR represents
settings.hrm.show_organisation = True
# Uncomment to disable Staff experience
settings.hrm.staff_experience = False
# Uncomment to disable the use of HR Credentials
settings.hrm.use_credentials = False
# Uncomment to enable the use of HR Education
settings.hrm.use_education = True
# Uncomment to disable the use of HR Skills
settings.hrm.use_skills = False
# Uncomment to disable the use of HR Teams
#settings.hrm.use_teams = False
# Custom label for Organisations in HR module
settings.hrm.organisation_label = "National Society / Branch"

# -----------------------------------------------------------------------------
# Projects
# Uncomment this to use settings suitable for a global/regional organisation (e.g. DRR)
settings.project.mode_3w = True
# Uncomment this to use DRR (Disaster Risk Reduction) extensions
settings.project.mode_drr = True
# Uncomment this to call project locations 'Communities'
settings.project.community = True
# Uncomment this to use multiple Budgets per project
settings.project.multiple_budgets = True
# Uncomment this to use multiple Organisations per project
settings.project.multiple_organisations = True
# Uncomment this to customise
settings.project.organisation_roles = {
    1: T("Host National Society"),
    2: T("Partner National Society"),
    3: T("Donor"),
    #4: T("Customer"), # T("Beneficiary")?
    5: T("Partner")
}

# -----------------------------------------------------------------------------
# Request Managemetn
settings.req.req_type = ["Stock"]
settings.req.use_commit = False
#settings.inv.collapse_tabs = True

# =============================================================================
# Template Modules
# Comment/uncomment modules here to disable/enable them
settings.modules = OrderedDict([
    # Core modules which shouldn't be disabled
    ("default", Storage(
            name_nice = "RMS",
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
    # Uncomment to enable internal support requests
    ("support", Storage(
            name_nice = T("Support"),
            #description = "Support Requests",
            restricted = True,
            module_type = None  # This item is handled separately for the menu
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
    ("asset", Storage(
            name_nice = T("Assets"),
            #description = "Recording and Assigning Assets",
            restricted = True,
            module_type = 5,
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
            name_nice = T("Assessments"),
            #description = "Create, enter, and manage surveys.",
            restricted = True,
            module_type = 5,
        )),
    ("irs", Storage(
            name_nice = T("Incidents"),
            #description = "Incident Reporting System",
            restricted = True,
            module_type = 10
        )),
    ("member", Storage(
           name_nice = T("Members"),
           #description = "Membership Management System",
           restricted = True,
           module_type = 10,
       )),
    ("stats", Storage(
            name_nice = T("Statistics"),
            #description = "Manages statistics",
            restricted = True,
            module_type = None,
        )),
    ("vulnerability", Storage(
            name_nice = T("Vulnerability"),
            #description = "Manages vulnerability indicators",
            restricted = True,
            module_type = 10,
        )),
])
