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
settings.security.policy = 8 # Delegations
settings.security.map = True

# Realm Entity (old)
#def eurosha_realm_entity(table, row):
#    user = current.auth.user
#    if user is not None:
#        return current.s3db.pr_get_pe_id("org_organisation",
#                                         user.organisation_id)
#    else:
#        return None
#settings.auth.realm_entity = eurosha_realm_entity

def eurosha_realm_entity(table, row):
    """
        Assign a Realm Entity to records
    """

    tablename = table._tablename

    # Do not apply realms for Master Data
    # @ToDo: Restore Realms and add a role/functionality support for Master Data  
    if tablename in [#"hrm_certificate",
                     "hrm_department",
                     "hrm_job_role",
                     "hrm_job_title",
                     "hrm_course",
                     "hrm_programme",
                     ]:
        return None

    db = current.db
    s3db = current.s3db

    # Entity reference fields
    EID = "pe_id"
    #OID = "organisation_id"
    SID = "site_id"
    #GID = "group_id"
    PID = "person_id"

    # Owner Entity Foreign Key
    realm_entity_fks = dict(pr_contact = EID,
                            pr_physical_description = EID,
                            pr_address = EID,
                            pr_image = EID,
                            pr_identity = PID,
                            pr_education = PID,
                            pr_note = PID,
                            hrm_human_resource = SID,
                            inv_recv = SID,
                            inv_recv_item = "req_id",
                            inv_send = SID,
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
    fk = realm_entity_fks.get(tablename, None)
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
            #else:
            # Continue to loop through the rest of the default_fks
            # Fall back to default get_realm_entity function

    # EUROSHA should never use User organsiation (since volunteers editing on behalf of other Orgs)
    #use_user_organisation = False
    ## Suppliers & Partners are owned by the user's organisation
    #if realm_entity == 0 and tablename == "org_organisation":
    #    ott = s3db.org_organisation_type
    #    row = table[row.id]
    #    row = db(table.organisation_type_id == ott.id).select(ott.name,
    #                                                          limitby=(0, 1)
    #                                                          ).first()
    #    
    #    if row and row.name != "Red Cross / Red Crescent":
    #        use_user_organisation = True

    ## Groups are owned by the user's organisation
    #elif tablename in ["pr_group"]:
    #    use_user_organisation = True

    #user = current.auth.user
    #if use_user_organisation and user:
    #    # @ToDo - this might cause issues if the user's org is different from the realm that gave them permissions to create the Org 
    #    realm_entity = s3db.pr_get_pe_id("org_organisation",
    #                                     user.organisation_id)

    return realm_entity
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
    ("stats", Storage(
            name_nice = "Stats",
            #description = "Needed for Project Benficiaries",
            restricted = True,
            module_type = None
        )),
])
