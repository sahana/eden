# -*- coding: utf-8 -*-

from gluon import current, IS_EMPTY_OR
from gluon.storage import Storage
from gluon.contrib.simplejson.ordered_dict import OrderedDict
from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineComponentCheckbox

T = current.T
settings = current.deployment_settings

"""
    Template settings for IFRC
"""
# =============================================================================
# System Settings
# -----------------------------------------------------------------------------
# Security Policy
settings.security.policy = 8 # Delegations
settings.security.map = True

# Authorization Settings
settings.auth.registration_requires_approval = True
settings.auth.registration_requires_verification = True
settings.auth.registration_requests_organisation = True
settings.auth.registration_organisation_required = True
settings.auth.registration_requests_site = True

settings.auth.registration_link_user_to = {"staff": T("Staff"),
                                           "volunteer": T("Volunteer"),
                                           "member": T("Member")
                                           }

settings.auth.record_approval = True

# @ToDo: Should we fallback to organisation_id if site_id is None?
settings.auth.registration_roles = {"site_id": ["reader",
                                                ],
                                    }

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
    if tablename in ["hrm_certificate",
                     "hrm_department",
                     "hrm_job_role",
                     "hrm_job_title",
                     "hrm_course",
                     "hrm_programme",
                     "member_membership_type",
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
    
    use_user_organisation = False
    # Suppliers & Partners are owned by the user's organisation
    if realm_entity == 0 and tablename == "org_organisation":
        ott = s3db.org_organisation_type
        query = (table.id == row.id) & \
                (table.organisation_type_id == ott.id)
        row = db(query).select(ott.name,
                               limitby=(0, 1)
                               ).first()

        if row and row.name != "Red Cross / Red Crescent":
            use_user_organisation = True

    # Groups are owned by the user's organisation
    elif tablename in ["pr_group"]:
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
settings.base.prepopulate = ["IFRC", "IFRC_Train"]

settings.base.system_name = T("Resource Management System")
settings.base.system_name_short = T("RMS")

# -----------------------------------------------------------------------------
# Theme (folder to use for views/layout.html)
settings.base.theme = "IFRC"
settings.base.xtheme = "IFRC/xtheme-ifrc.css"
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
    ("vi", "Tiếng Việt"),
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
settings.search.save_widget = False


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
     "vol_details.active"                        : ["Timor-Leste Red Cross Society (Cruz Vermelha de Timor-Leste)"],
     "vol_volunteer_cluster.vol_cluster_type_id"     : ["Philippine Red Cross"],
     "vol_volunteer_cluster.vol_cluster_id"          : ["Philippine Red Cross"],
     "vol_volunteer_cluster.vol_cluster_position_id" : ["Philippine Red Cross"],
     }

# -----------------------------------------------------------------------------
# Human Resource Management
# Uncomment to allow Staff & Volunteers to be registered without an email address
settings.hrm.email_required = False
# Uncomment to filter certificates by (root) Organisation & hence not allow Certificates from other orgs to be added to a profile (except by Admin)
settings.hrm.filter_certificates = True
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
# Custom label for Organisations in HR module
settings.hrm.organisation_label = "National Society / Branch"

# -----------------------------------------------------------------------------
def ns_only(f, required=True, branches=True, updateable=True):
    """
        Function to configure an organisation_id field to be restricted to just NS/Branch
    """

    # Label
    if branches:
        f.label = T("National Society / Branch")
    else:
        f.label = T("National Society")
    # Requires
    db = current.db
    ttable = db.org_organisation_type
    type_id = db(ttable.name == "Red Cross / Red Crescent").select(ttable.id,
                                                                   limitby=(0, 1)
                                                                   ).first().id
    if branches:
        not_filterby = None
        not_filter_opts = []
    else:
        btable = db.org_organisation_branch
        rows = db(btable.deleted != True).select(btable.branch_id)
        branches = [row.branch_id for row in rows]
        not_filterby = "id"
        not_filter_opts = branches

    from s3.s3validators import IS_ONE_OF
    requires = IS_ONE_OF(db, "org_organisation.id",
                         current.s3db.org_OrganisationRepresent(),
                         filterby="organisation_type_id",
                         filter_opts=[type_id],
                         not_filterby=not_filterby,
                         not_filter_opts=not_filter_opts,
                         updateable = updateable,
                         orderby = "org_organisation.name",
                         sort = True)
    if not required:
        requires = IS_EMPTY_OR(requires)
    f.requires = requires
    # Dropdown not Autocomplete
    f.widget = None
    # Comment
    s3_has_role = current.auth.s3_has_role
    if s3_has_role("ADMIN") or \
       s3_has_role("ORG_ADMIN"):
        # Need to do import after setting Theme
        from s3layouts import S3AddResourceLink
        f.comment = S3AddResourceLink(c="org",
                                      f="organisation",
                                      vars={"organisation.organisation_type_id$name":"Red Cross / Red Crescent"},
                                      label=T("Add National Society"),
                                      title=T("National Society"),
                                      )
    else:
        # Not allowed to add NS
        f.comment = ""

# -----------------------------------------------------------------------------
def customize_asset_asset(**attr):
    """
        Customize asset_asset controller
    """

    # Organisation needs to be an NS/Branch
    ns_only(current.s3db.asset_asset.organisation_id,
            required=True,
            branches=True,
            )

    return attr

settings.ui.customize_asset_asset = customize_asset_asset

# -----------------------------------------------------------------------------
def customize_auth_user(**attr):
    """
        Customize admin/user() and default/user() controllers
    """

    if "arg" in attr and attr["arg"] == "register":
        # Organisation needs to be an NS/Branch
        ns_only(current.db.auth_user.organisation_id,
                required=True,
                branches=True,
                updateable=False, # Need to see all Orgs in Registration screens
                )

    return attr

settings.ui.customize_auth_user = customize_auth_user

# -----------------------------------------------------------------------------
def customize_hrm_certificate(**attr):
    """
        Customize hrm_certificate controller
    """

    # Organisation needs to be an NS/Branch
    ns_only(current.s3db.hrm_certificate.organisation_id,
            required=False,
            branches=False,
            )

    return attr

settings.ui.customize_hrm_certificate = customize_hrm_certificate

# -----------------------------------------------------------------------------
def customize_hrm_course(**attr):
    """
        Customize hrm_course controller
    """

    # Organisation needs to be an NS/Branch
    ns_only(current.s3db.hrm_course.organisation_id,
            required=False,
            branches=False,
            )

    return attr

settings.ui.customize_hrm_course = customize_hrm_course

# -----------------------------------------------------------------------------
def customize_hrm_department(**attr):
    """
        Customize hrm_department controller
    """

    # Organisation needs to be an NS/Branch
    ns_only(current.s3db.hrm_department.organisation_id,
            required=False,
            branches=False,
            )

    return attr

settings.ui.customize_hrm_department = customize_hrm_department

# -----------------------------------------------------------------------------
def customize_hrm_human_resource(**attr):
    """
        Customize hrm_human_resource controller
    """

    # Organisation needs to be an NS/Branch
    ns_only(current.s3db.hrm_human_resource.organisation_id,
            required=True,
            branches=True,
            )

    return attr

settings.ui.customize_hrm_human_resource = customize_hrm_human_resource

# -----------------------------------------------------------------------------
def customize_hrm_job_title(**attr):
    """
        Customize hrm_job_title controller
    """

    # Organisation needs to be an NS/Branch
    ns_only(current.s3db.hrm_job_title.organisation_id,
            required=False,
            branches=False,
            )

    return attr

settings.ui.customize_hrm_job_title = customize_hrm_job_title

# -----------------------------------------------------------------------------
def customize_hrm_programme(**attr):
    """
        Customize hrm_programme controller
    """

    # Organisation needs to be an NS/Branch
    ns_only(current.s3db.hrm_programme.organisation_id,
            required=False,
            branches=False,
            )

    return attr

settings.ui.customize_hrm_programme = customize_hrm_programme

# -----------------------------------------------------------------------------
def customize_member_membership(**attr):
    """
        Customize member_membership controller
    """

    # Organisation needs to be an NS/Branch
    ns_only(current.s3db.member_membership.organisation_id,
            required=True,
            branches=True,
            )

    return attr

settings.ui.customize_member_membership = customize_member_membership

# -----------------------------------------------------------------------------
def customize_member_membership_type(**attr):
    """
        Customize member_membership_type controller
    """

    # Organisation needs to be an NS/Branch
    ns_only(current.s3db.member_membership_type.organisation_id,
            required=False,
            branches=False,
            )

    return attr

settings.ui.customize_member_membership_type = customize_member_membership_type

# -----------------------------------------------------------------------------
def customize_org_office(**attr):
    """
        Customize org_office controller
    """

    # Organisation needs to be an NS/Branch
    ns_only(current.s3db.org_office.organisation_id,
            required=True,
            branches=True,
            )

    return attr

settings.ui.customize_org_office = customize_org_office

# -----------------------------------------------------------------------------
def customize_survey_series(**attr):
    """
        Customize survey_series controller
    """

    # Organisation needs to be an NS/Branch
    ns_only(current.s3db.survey_series.organisation_id,
            required=False,
            branches=True,
            )

    return attr

settings.ui.customize_survey_series = customize_survey_series

# -----------------------------------------------------------------------------
def customize_org_organisation(**attr):

    s3 = current.response.s3

    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
        else:
            result = True

        if r.interactive or r.representation.lower() == "aadata":
            s3db = current.s3db
            list_fields = ["id",
                           "name",
                           "acronym",
                           "organisation_type_id",
                           #(T("Sectors"), "sector.name"),
                           "country",
                           "website"
                           ]
            
            s3db.configure("org_organisation", list_fields=list_fields)
        
        if r.interactive:
            crud_form = S3SQLCustomForm(
                "name",
                "acronym",
                "organisation_type_id",
                "region",
                "country",
                #S3SQLInlineComponentCheckbox(
                #    "sector",
                #    label = T("Sectors"),
                #    field = "sector_id",
                #    cols = 3,
                #),
                "phone",
                "website",
                "logo",
                "comments",
            )
            current.s3db.configure("org_organisation", crud_form=crud_form)
            
        return result
    s3.prep = custom_prep

    return attr

settings.ui.customize_org_organisation = customize_org_organisation

# -----------------------------------------------------------------------------
# Projects
# Uncomment this to use settings suitable for a global/regional organisation (e.g. DRR)
settings.project.mode_3w = True
# Uncomment this to use DRR (Disaster Risk Reduction) extensions
settings.project.mode_drr = True
# Uncomment this to use Codes for projects
settings.project.codes = True
# Uncomment this to call project locations 'Communities'
settings.project.community = True
# Uncomment this to use multiple Budgets per project
settings.project.multiple_budgets = True
# Uncomment this to use multiple Organisations per project
settings.project.multiple_organisations = True
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
def customize_project_project(**attr):
    """
        Customize project_project controller
    """

    s3db = current.s3db
    tablename = "project_project"
    # Load normal model
    table = s3db[tablename]

    # @ToDo: S3SQLInlineComponent for Project orgs
    # Get IDs for PartnerNS/Partner-Donor
    # db = current.db
    # ttable = db.org_organisation_type
    # rows = db(ttable.deleted != True).select(ttable.id,
                                             # ttable.name,
                                             # )
    # rc = []
    # not_rc = []
    # nappend = not_rc.append
    # for row in rows:
        # if row.name == "Red Cross / Red Crescent":
            # rc.append(row.id)
        # elif row.name == "Supplier":
            # pass
        # else:
            # nappend(row.id)

    # Custom Fields
    # Organisation needs to be an NS (not a branch)
    f = table.organisation_id
    ns_only(f,
            required=True,
            branches=False,
            )
    f.label = T("Host National Society")

    # Custom Crud Form
    crud_form = S3SQLCustomForm(
        "organisation_id",
        "name",
        "code",
        "description",
        "status_id",
        "start_date",
        "end_date",
        #S3SQLInlineComponent(
        #    "location",
        #    label = T("Countries"),
        #    fields = ["location_id"],
        #),
        # Outputs
        S3SQLInlineComponent(
            "output",
            label = T("Outputs"),
            #comment = "Bob",
            fields = ["name", "status"],
        ),
        S3SQLInlineComponentCheckbox(
            "hazard",
            label = T("Hazards"),
            field = "hazard_id",
            cols = 4,
        ),
        S3SQLInlineComponentCheckbox(
            "sector",
            label = T("Sectors"),
            field = "sector_id",
            cols = 4,
        ),
        S3SQLInlineComponentCheckbox(
            "theme",
            label = T("Themes"),
            field = "theme_id",
            cols = 4,
            # Filter Theme by Sector
            filter = {"linktable": "project_theme_sector",
                      "lkey": "theme_id",
                      "rkey": "sector_id",
                      },
            script = '''
S3OptionsFilter({
 'triggerName':'defaultsector-sector_id',
 'targetName':'defaulttheme-theme_id',
 'targetWidget':'defaulttheme-theme_id_widget',
 'lookupResource':'theme',
 'lookupURL':S3.Ap.concat('/project/theme_sector_widget?sector_ids='),
 'getWidgetHTML':true,
 'showEmptyField':false
})'''
        ),
        "drr.hfa",
        "objectives",
        "human_resource_id",
        # Disabled since we need organisation_id filtering to either organisation_type_id == RC or NOT
        # & also hiding Branches from RCs
        # Partner NS
        # S3SQLInlineComponent(
            # "organisation",
            # name = "partnerns",
            # label = T("Partner National Societies"),
            # fields = ["organisation_id",
                      # "comments",
                      # ],
            # Filter Organisation by Type
            # filter = ["organisation_id": {"filterby": "organisation_type_id",
                                          # "filterfor": rc,
                                          # }],
            # filterby = dict(field = "role",
                            # options = [9])
        # ),
        # Partner Orgs
        # S3SQLInlineComponent(
            # "organisation",
            # name = "partner",
            # label = T("Partner Organizations"),
            # fields = ["organisation_id",
                      # "comments",
                      # ],
            # Filter Organisation by Type
            # filter = ["organisation_id": {"filterby": "organisation_type_id",
                                          # "filterfor": not_rc,
                                          # }],
            # filterby = dict(field = "role",
                            # options = [2])
        # ),
        # Donors
        # S3SQLInlineComponent(
            # "organisation",
            # name = "donor",
            # label = T("Donor(s)"),
            # fields = ["organisation_id",
                      # "amount",
                      # "currency"],
            # Filter Organisation by Type
            # filter = ["organisation_id": {"filterby": "organisation_type_id",
                                          # "filterfor": not_rc,
                                          # }],
            # filterby = dict(field = "role",
                            # options = [3])
        # ),
        #"budget",
        #"currency",
        "comments",
    )

    s3db.configure(tablename,
                   crud_form = crud_form)

    return attr

settings.ui.customize_project_project = customize_project_project

settings.ui.crud_form_project_location = S3SQLCustomForm(
        "project_id",
        "location_id",
        # @ToDo: Grouped Checkboxes
        S3SQLInlineComponentCheckbox(
            "activity_type",
            label = T("Activity Types"),
            field = "activity_type_id",
            cols = 3,
            # Filter Activity Type by Sector
            filter = {"linktable": "project_activity_type_sector",
                      "lkey": "activity_type_id",
                      "rkey": "sector_id",
                      "lookuptable": "project_project",
                      "lookupkey": "project_id",
                      },
        ),
        "comments",
    )

# -----------------------------------------------------------------------------
# Inventory Management
settings.inv.show_mode_of_transport = True
settings.inv.send_show_time_in = True

# -----------------------------------------------------------------------------
# Request Management
# Uncomment to disable Inline Forms in Requests module
settings.req.inline_forms = False
settings.req.req_type = ["Stock"]
settings.req.use_commit = False
#settings.inv.collapse_tabs = True
# Should Requests ask whether Transportation is required?
settings.req.ask_transport = True

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
    ("event", Storage(
            name_nice = T("Events"),
            #description = "Events",
            restricted = True,
            module_type = 10
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
