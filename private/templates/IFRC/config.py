# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from datetime import timedelta

from gluon import current
from gluon.storage import Storage

T = current.T
settings = current.deployment_settings

"""
    Template settings for IFRC
"""

# -----------------------------------------------------------------------------
# Pre-Populate
settings.base.prepopulate = ("IFRC", "IFRC/Train")

settings.base.system_name = T("Resource Management System")
settings.base.system_name_short = T("RMS")

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
    if tablename in ("hrm_certificate",
                     "hrm_department",
                     "hrm_job_title",
                     "hrm_course",
                     "hrm_programme",
                     "member_membership_type",
                     "vol_award",
                     ):
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
                            pr_contact_emergency = EID,
                            pr_physical_description = EID,
                            pr_address = EID,
                            pr_image = EID,
                            pr_identity = PID,
                            pr_education = PID,
                            pr_note = PID,
                            hrm_human_resource = SID,
                            inv_recv = SID,
                            inv_send = SID,
                            inv_track_item = "track_org_id",
                            inv_adj_item = "adj_id",
                            req_req_item = "req_id"
                            )

    # Default Foreign Keys (ordered by priority)
    default_fks = ("catalog_id",
                   "project_id",
                   "project_location_id",
                   )

    # Link Tables
    #realm_entity_link_table = dict(
    #    project_task = Storage(tablename = "project_task_project",
    #                           link_key = "task_id"
    #                           )
    #    )
    #if tablename in realm_entity_link_table:
    #    # Replace row with the record from the link table
    #    link_table = realm_entity_link_table[tablename]
    #    table = s3db[link_table.tablename]
    #    rows = db(table[link_table.link_key] == row.id).select(table.id,
    #                                                           limitby=(0, 1))
    #    if rows:
    #        # Update not Create
    #        row = rows.first()

    # Check if there is a FK to inherit the realm_entity
    realm_entity = 0
    fk = realm_entity_fks.get(tablename, None)
    fks = [fk]
    fks.extend(default_fks)
    for default_fk in fks:
        if default_fk in table.fields:
            fk = default_fk
            # Inherit realm_entity from parent record
            if fk == EID:
                ftable = s3db.pr_person
                query = (ftable[EID] == row[EID])
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
        ottable = s3db.org_organisation_type
        ltable = db.org_organisation_organisation_type
        query = (ltable.organisation_id == row.id) & \
                (ltable.organisation_type_id == ottable.id)
        row = db(query).select(ottable.name,
                               limitby=(0, 1)
                               ).first()
        if row and row.name != "Red Cross / Red Crescent":
            use_user_organisation = True

    # Groups are owned by the user's organisation
    #elif tablename in ("pr_group",):
    elif tablename == "pr_group":
        use_user_organisation = True

    user = current.auth.user
    if use_user_organisation and user:
        # @ToDo - this might cause issues if the user's org is different from the realm that gave them permissions to create the Org 
        realm_entity = s3db.pr_get_pe_id("org_organisation",
                                         user.organisation_id)

    return realm_entity

settings.auth.realm_entity = ifrc_realm_entity

# -----------------------------------------------------------------------------
# Theme (folder to use for views/layout.html)
settings.base.theme = "IFRC"
settings.base.xtheme = "IFRC/xtheme-ifrc.css"
settings.gis.map_height = 600
settings.gis.map_width = 869
# Display Resources recorded to Admin-Level Locations on the map
# @ToDo: Move into gis_config?
settings.gis.display_L0 = True
# GeoNames username
settings.gis.geonames_username = "rms_dev"

# -----------------------------------------------------------------------------
# L10n (Localization) settings
settings.L10n.languages = OrderedDict([
    ("en-gb", "English"),
    ("es", "Español"),
    ("km", "ភាសាខ្មែរ"),       # Khmer
    ("ne", "नेपाली"),         # Nepali
    ("prs", "دری"),         # Dari
    ("ps", "پښتو"),         # Pashto
    ("vi", "Tiếng Việt"),   # Vietnamese
    ("zh-cn", "中文 (简体)"),
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
# Unsortable 'pretty' date format (for use in English)
settings.L10n.date_format = "%d-%b-%Y"
# Make last name in person/user records mandatory
settings.L10n.mandatory_lastname = True
# Uncomment this to Translate Layer Names
settings.L10n.translate_gis_layer = True
# Translate Location Names
settings.L10n.translate_gis_location = True

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
# Filter Manager
settings.search.filter_manager = False

# -----------------------------------------------------------------------------
# Messaging
# Parser
settings.msg.parser = "IFRC"

# =============================================================================
# Module Settings

# -----------------------------------------------------------------------------
# Organisation Management
# Enable the use of Organisation Branches
settings.org.branches = True
# Set the length of the auto-generated org/site code the default is 10
settings.org.site_code_len = 3
# Set the label for Sites
settings.org.site_label = "Office/Warehouse/Facility"
# Enable certain fields just for specific Organisations
ARCS = "Afghan Red Crescent Society"
BRCS = "Bangladesh Red Crescent Society"
CVTL = "Timor-Leste Red Cross Society (Cruz Vermelha de Timor-Leste)"
PMI = "Indonesian Red Cross Society (Pelang Merah Indonesia)"
PRC = "Philippine Red Cross"
VNRC = "Viet Nam Red Cross"
settings.org.dependent_fields = \
    {"pr_person.middle_name"                     : (CVTL, VNRC),
     "pr_person_details.mother_name"             : (BRCS, ),
     "pr_person_details.father_name"             : (ARCS, BRCS),
     "pr_person_details.affiliations"            : (PRC, ),
     "pr_person_details.company"                 : (PRC, ),
     "vol_details.availability"                  : (VNRC, ),
     "vol_details.card"                          : (ARCS, ),
     "vol_volunteer_cluster.vol_cluster_type_id"     : (PRC, ),
     "vol_volunteer_cluster.vol_cluster_id"          : (PRC, ),
     "vol_volunteer_cluster.vol_cluster_position_id" : (PRC, ),
     }

# -----------------------------------------------------------------------------
# Human Resource Management
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
# Uncomment to consolidate tabs into Staff Record
settings.hrm.record_tab = True

# Uncomment to do a search for duplicates in the new AddPersonWidget2
settings.pr.lookup_duplicates = True

# RDRT
settings.deploy.hr_label = "Member"
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

# -----------------------------------------------------------------------------
def ns_only(f, required=True, branches=True, updateable=True):
    """
        Function to configure an organisation_id field to be restricted to just
        NS/Branch
    """

    # Label
    if branches:
        f.label = T("National Society / Branch")
    else:
        f.label = T("National Society")

    # Requires
    db = current.db
    ttable = db.org_organisation_type
    try:
        type_id = db(ttable.name == "Red Cross / Red Crescent").select(ttable.id,
                                                                       limitby=(0, 1)
                                                                       ).first().id
    except:
        # No IFRC prepop done - skip (e.g. testing impacts of CSS changes in this theme)
        return

    # Filter by type
    ltable = db.org_organisation_organisation_type
    rows = db(ltable.organisation_type_id == type_id).select(ltable.organisation_id)
    filter_opts = [row.organisation_id for row in rows]

    auth = current.auth
    s3_has_role = auth.s3_has_role
    Admin = s3_has_role("ADMIN")
    if branches:
        if Admin:
            parent = True
        else:
            # @ToDo: Set the represent according to whether the user can see resources of just a single NS or multiple
            # @ToDo: Consider porting this into core
            user = auth.user
            if user:
                realms = user.realms
                delegations = user.delegations
                if realms:
                    parent = True
                else:
                    parent = False
            else:
                parent = True

    else:
        # Keep the represent function as simple as possible
        parent = False
        # Exclude branches
        btable = current.s3db.org_organisation_branch
        rows = db((btable.deleted != True) &
                  (btable.branch_id.belongs(filter_opts))).select(btable.branch_id)
        filter_opts = list(set(filter_opts) - set(row.branch_id for row in rows))

    organisation_represent = current.s3db.org_OrganisationRepresent
    represent = organisation_represent(parent=parent)
    f.represent = represent

    from s3.s3validators import IS_ONE_OF
    requires = IS_ONE_OF(db, "org_organisation.id",
                         represent,
                         filterby = "id",
                         filter_opts = filter_opts,
                         updateable = updateable,
                         orderby = "org_organisation.name",
                         sort = True)
    if not required:
        from gluon import IS_EMPTY_OR
        requires = IS_EMPTY_OR(requires)
    f.requires = requires

    if parent:
        # Use hierarchy-widget
        from s3 import FS, S3HierarchyWidget
        # No need for parent in represent (it's a hierarchy view)
        node_represent = organisation_represent(parent=False)
        # Filter by type
        node_filter = (FS("organisation_organisation_type.organisation_type_id") == type_id)
        # No need to exclude branches (we wouldn't be here if we didn't use branches)
        f.widget = S3HierarchyWidget(lookup="org_organisation",
                                     filter=node_filter,
                                     represent=node_represent,
                                     multiple=False,
                                     leafonly=False,
                                     )
        # @todo: Dynamic update of HierarchyWidget not supported yet
        #        => hide the add-resource link until fixed
        skip_add_resource_link = True
    else:
        # Dropdown not Autocomplete
        f.widget = None
        skip_add_resource_link = False

    # Comment
    if (Admin or s3_has_role("ORG_ADMIN")) and not skip_add_resource_link:
        # Need to do import after setting Theme
        from s3layouts import S3AddResourceLink
        from s3.s3navigation import S3ScriptItem
        add_link = S3AddResourceLink(c="org", f="organisation",
                                     vars={"organisation_type.name":"Red Cross / Red Crescent"},
                                     label=T("Create National Society"),
                                     title=T("National Society"),
                                     )
        comment = f.comment
        if not comment or isinstance(comment, S3AddResourceLink):
            f.comment = add_link
        elif isinstance(comment[1], S3ScriptItem):
            # Don't overwrite scripts
            f.comment[0] = add_link
        else:
            f.comment = add_link
    else:
        # Not allowed to add NS/Branch
        f.comment = ""

# -----------------------------------------------------------------------------
def user_org_default_filter(selector, tablename=None):
    """
        Default filter for organisation_id:
        * Use the user's organisation if logged-in and associated with an
          organisation.
    """

    auth = current.auth
    user_org_id = auth.is_logged_in() and auth.user.organisation_id
    if user_org_id:
        return user_org_id
    else:
        # no default
        return {}

# -----------------------------------------------------------------------------
def customise_asset_asset_resource(r, tablename):

    s3db = current.s3db
    table = s3db.asset_asset

    # Organisation needs to be an NS/Branch
    ns_only(table.organisation_id,
            required = True,
            branches = True,
            )

    # Custom CRUD Form to allow ad-hoc Kits & link to Teams
    from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent
    table.kit.readable = table.kit.writable = True
    crud_form = S3SQLCustomForm("number",
                                "type",
                                "item_id",
                                "organisation_id",
                                "site_id",
                                "kit",
                                # If not ad-hoc Kit
                                "sn",
                                "supply_org_id",
                                "purchase_date",
                                "purchase_price",
                                "purchase_currency",
                                # If ad-hoc Kit
                                S3SQLInlineComponent(
                                    "item",
                                    label = T("Items"),
                                    fields = ["item_id",
                                              "quantity",
                                              "sn",
                                              # These are too wide for the screen & hence hide the AddResourceLinks
                                              #"supply_org_id",
                                              #"purchase_date",
                                              #"purchase_price",
                                              #"purchase_currency",
                                              "comments",
                                              ],
                                    ),
                                S3SQLInlineComponent(
                                    "group",
                                    label = T("Team"),
                                    fields = [("", "group_id")],
                                    filterby = dict(field = "group_type",
                                                    options = 3
                                                    ),
                                    multiple = False,
                                    ),
                                "comments",
                                )

    from s3.s3filter import S3OptionsFilter
    filter_widgets = s3db.get_config(tablename, "filter_widgets")
    filter_widgets.insert(-2, S3OptionsFilter("group.group_id",
                                              label = T("Team"),
                                              represent = "%(name)s",
                                              hidden = True,
                                              ))

    s3db.configure(tablename,
                   crud_form = crud_form,
                   )

settings.customise_asset_asset_resource = customise_asset_asset_resource

# -----------------------------------------------------------------------------
def customise_auth_user_controller(**attr):
    """
        Customise admin/user() and default/user() controllers
    """

    #if "arg" in attr and attr["arg"] == "register":
    # Organisation needs to be an NS/Branch
    ns_only(current.db.auth_user.organisation_id,
            required = True,
            branches = True,
            updateable = False, # Need to see all Orgs in Registration screens
            )

    # Different settings for different NS
    # Not possible for registration form, so fake with language!
    root_org = current.auth.root_org_name()
    if root_org == VNRC or current.session.s3.language == "vi":
        # Too late to do via settings
        #settings.org.site_label = "Office/Center"
        current.db.auth_user.site_id.label = T("Office/Center")

    return attr

settings.customise_auth_user_controller = customise_auth_user_controller

# -----------------------------------------------------------------------------
def customise_deploy_alert_resource(r, tablename):

    current.s3db.deploy_alert_recipient.human_resource_id.label = T("Member")

settings.customise_deploy_alert_resource = customise_deploy_alert_resource

# -----------------------------------------------------------------------------
def customise_deploy_application_resource(r, tablename):

    r.table.human_resource_id.label = T("Member")

settings.customise_deploy_application_resource = customise_deploy_application_resource

# -----------------------------------------------------------------------------
def _customise_assignment_fields(**attr):

    MEMBER = T("Member")
    from gluon.html import DIV
    hr_comment =  \
        DIV(_class="tooltip",
            _title="%s|%s" % (MEMBER,
                              current.messages.AUTOCOMPLETE_HELP))

    from s3.s3validators import IS_ONE_OF
    atable = current.s3db.deploy_assignment
    atable.human_resource_id.label = MEMBER
    atable.human_resource_id.comment = hr_comment
    field = atable.job_title_id
    field.comment = None
    field.label = T("Sector")
    field.requires = IS_ONE_OF(current.db, "hrm_job_title.id",
                               field.represent,
                               filterby = "type",
                               filter_opts = (4,),
                               )
    return

# -----------------------------------------------------------------------------
def customise_deploy_assignment_controller(**attr):

    s3db = current.s3db
    table = s3db.deploy_assignment

    # Labels
    table.job_title_id.label = T("RDRT Type")
    table.start_date.label = T("Deployment Date")
    #table.end_date.label = T("EOM")

    # List fields
    list_fields = [(T("Mission"), "mission_id$name"),
                   (T("Appeal Code"), "mission_id$code"),
                   (T("Country"), "mission_id$location_id"),
                   (T("Disaster Type"), "mission_id$event_type_id"),
                   # @todo: replace by date of first alert?
                   (T("Date"), "mission_id$created_on"),
                   "job_title_id",
                   (T("Member"), "human_resource_id$person_id"),
                   (T("Deploying NS"), "human_resource_id$organisation_id"),
                   "start_date",
                   "end_date",
                   "appraisal.rating",
                   # @todo: Comments of the mission (=>XLS only)
                  ]

    # Report options
    report_fact = [(T("Number of Deployments"), "count(human_resource_id)"),
                   (T("Average Rating"), "avg(appraisal.rating)"),
                   ]
    report_axis = [(T("Appeal Code"), "mission_id$code"),
                   (T("Country"), "mission_id$location_id"),
                   (T("Disaster Type"), "mission_id$event_type_id"),
                   (T("RDRT Type"), "job_title_id"),
                   (T("Deploying NS"), "human_resource_id$organisation_id"),
                  ]
    report_options = Storage(
        rows=report_axis,
        cols=report_axis,
        fact=report_fact,
        defaults=Storage(rows="mission_id$location_id",
                         cols="mission_id$event_type_id",
                         fact="count(human_resource_id)",
                         totals=True
                         )
        )
            
    s3db.configure("deploy_assignment",
                   list_fields = list_fields,
                   report_options = report_options,
                   )
    
    
    # CRUD Strings
    current.response.s3.crud_strings["deploy_assignment"] = Storage(
        label_create = T("Add Deployment"),
        title_display = T("Deployment Details"),
        title_list = T("Deployments"),
        title_update = T("Edit Deployment Details"),
        title_upload = T("Import Deployments"),
        label_list_button = T("List Deployments"),
        label_delete_button = T("Delete Deployment"),
        msg_record_created = T("Deployment added"),
        msg_record_modified = T("Deployment Details updated"),
        msg_record_deleted = T("Deployment deleted"),
        msg_list_empty = T("No Deployments currently registered"))

    _customise_assignment_fields()
    
    # Restrict Location to just Countries
    from s3.s3fields import S3Represent
    field = s3db.deploy_mission.location_id
    field.represent = S3Represent(lookup="gis_location", translate=True)
    
    return attr

settings.customise_deploy_assignment_controller = customise_deploy_assignment_controller

# -----------------------------------------------------------------------------
def customise_deploy_mission_controller(**attr):

    db = current.db
    s3db = current.s3db
    s3 = current.response.s3
    MEMBER = T("Member")
    from gluon.html import DIV
    hr_comment =  \
        DIV(_class="tooltip",
            _title="%s|%s" % (MEMBER,
                              current.messages.AUTOCOMPLETE_HELP))

    table = s3db.deploy_mission
    table.code.label = T("Appeal Code")
    table.event_type_id.label = T("Disaster Type")
    table.organisation_id.readable = table.organisation_id.writable = False

    # Restrict Location to just Countries
    from s3.s3fields import S3Represent
    from s3.s3widgets import S3MultiSelectWidget
    field = table.location_id
    field.label = current.messages.COUNTRY
    field.requires = s3db.gis_country_requires
    field.widget = S3MultiSelectWidget(multiple=False)
    field.represent = S3Represent(lookup="gis_location", translate=True)

    rtable = s3db.deploy_response
    rtable.human_resource_id.label = MEMBER
    rtable.human_resource_id.comment = hr_comment

    _customise_assignment_fields()

    # Report options
    report_fact = [(T("Number of Missions"), "count(id)"),
                   (T("Number of Countries"), "count(location_id)"),
                   (T("Number of Disaster Types"), "count(event_type_id)"),
                   (T("Number of Responses"), "sum(response_count)"),
                   (T("Number of Deployments"), "sum(hrquantity)"),
                  ]
    report_axis = ["code",
                   "location_id",
                   "event_type_id",
                   "status",
                   ]
    report_options = Storage(rows = report_axis,
                             cols = report_axis,
                             fact = report_fact,
                             defaults = Storage(rows = "location_id",
                                                cols = "event_type_id",
                                                fact = "sum(hrquantity)",
                                                totals = True,
                                                ),
                             )

    s3db.configure("deploy_mission",
                   report_options = report_options,
                   )

    # CRUD Strings
    s3.crud_strings["deploy_assignment"] = Storage(
        label_create = T("New Deployment"),
        title_display = T("Deployment Details"),
        title_list = T("Deployments"),
        title_update = T("Edit Deployment Details"),
        title_upload = T("Import Deployments"),
        label_list_button = T("List Deployments"),
        label_delete_button = T("Delete Deployment"),
        msg_record_created = T("Deployment added"),
        msg_record_modified = T("Deployment Details updated"),
        msg_record_deleted = T("Deployment deleted"),
        msg_list_empty = T("No Deployments currently registered"))

    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
        else:
            result = True

        if not r.component and r.method == "create":
            # Org is always IFRC
            otable = s3db.org_organisation
            query = (otable.name == "International Federation of Red Cross and Red Crescent Societies")
            organisation = db(query).select(otable.id,
                                            limitby = (0, 1),
                                            ).first()
            if organisation:
                r.table.organisation_id.default = organisation.id

        return result
    s3.prep = custom_prep

    return attr

settings.customise_deploy_mission_controller = customise_deploy_mission_controller

# -----------------------------------------------------------------------------
def poi_marker_fn(record):
    """
        Function to decide which Marker to use for PoI KML export
    """

    db = current.db
    table = db.gis_poi_type
    type = db(table.id == record.poi_type_id).select(table.name,
                                                     limitby=(0, 1)
                                                     ).first()
    if type:
        marker = type.name.lower().replace(" ", "_")\
                                  .replace("_cccm", "_CCCM")\
                                  .replace("_nfi_", "_NFI_")\
                                  .replace("_ngo_", "_NGO_")\
                                  .replace("_wash", "_WASH")
        marker = "OCHA/%s_40px.png" % marker
    else:
        # Fallback
        marker = "marker_red.png"

    return Storage(image=marker)

# -----------------------------------------------------------------------------
def customise_gis_poi_resource(r, tablename):

    if r.representation == "kml":
        # Custom Marker function
        current.s3db.configure("gis_poi",
                               marker_fn = poi_marker_fn,
                               )

settings.customise_gis_poi_resource = customise_gis_poi_resource

# -----------------------------------------------------------------------------
def customise_hrm_certificate_controller(**attr):

    # Organisation needs to be an NS/Branch
    ns_only(current.s3db.hrm_certificate.organisation_id,
            required = False,
            branches = False,
            )

    return attr

settings.customise_hrm_certificate_controller = customise_hrm_certificate_controller

# -----------------------------------------------------------------------------
def customise_hrm_course_controller(**attr):

    # Organisation needs to be an NS/Branch
    ns_only(current.s3db.hrm_course.organisation_id,
            required = False,
            branches = False,
            )

    return attr

settings.customise_hrm_course_controller = customise_hrm_course_controller

# -----------------------------------------------------------------------------
def customise_hrm_credential_controller(**attr):

    # Currently just used by RDRT
    table = current.s3db.hrm_credential
    field = table.job_title_id
    field.comment = None
    field.label = T("Sector")
    from s3.s3validators import IS_ONE_OF
    field.requires = IS_ONE_OF(current.db, "hrm_job_title.id",
                               field.represent,
                               filterby = "type",
                               filter_opts = (4,),
                               )
    table.organisation_id.readable = table.organisation_id.writable = False
    table.performance_rating.readable = table.performance_rating.writable = False
    table.start_date.readable = table.start_date.writable = False
    table.end_date.readable = table.end_date.writable = False

    return attr

settings.customise_hrm_credential_controller = customise_hrm_credential_controller

# -----------------------------------------------------------------------------
def customise_hrm_department_controller(**attr):

    # Organisation needs to be an NS/Branch
    ns_only(current.s3db.hrm_department.organisation_id,
            required = False,
            branches = False,
            )

    return attr

settings.customise_hrm_department_controller = customise_hrm_department_controller

# -----------------------------------------------------------------------------
def customise_hrm_human_resource_controller(**attr):

    # Default Filter
    from s3 import s3_set_default_filter
    s3_set_default_filter("~.organisation_id",
                          user_org_default_filter,
                          tablename = "hrm_human_resource")

    arcs = False
    vnrc = False
    if current.request.controller == "vol":
        # Special cases for different NS
        root_org = current.auth.root_org_name()
        if root_org == ARCS:
            arcs = True
            settings.L10n.mandatory_lastname = False
            settings.hrm.use_code = True
            settings.hrm.use_skills = True
            settings.hrm.vol_active = True
        elif root_org in (CVTL, PMI, PRC):
            settings.hrm.vol_active = vol_active
        elif root_org == VNRC:
            vnrc = True
            settings.pr.name_format = "%(last_name)s %(middle_name)s %(first_name)s"
            # @ToDo: Make this use the same lookup as in ns_only to check if user can see HRs from multiple NS
            settings.org.regions = False
    #elif vnrc:
    #    settings.org.site_label = "Office/Center"

    s3db = current.s3db
    s3db.org_organisation.root_organisation.label = T("National Society")

    # Organisation needs to be an NS/Branch
    ns_only(s3db.hrm_human_resource.organisation_id,
            required = True,
            branches = True,
            )

    s3 = current.response.s3

    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        if arcs:
            field = s3db.vol_details.card
            field.readable = field.writable = True
        elif vnrc:
            field = r.table.job_title_id
            field.readable = field.writable = False

        if r.controller == "deploy":

            # Custom list fields for RDRT
            phone_label = settings.get_ui_label_mobile_phone()
            list_fields = ["id",
                           "person_id",
                           "organisation_id$root_organisation",
                           "type",
                           "job_title_id",
                           (T("Email"), "email.value"),
                           (phone_label, "phone.value"),
                           "person_id$gender",
                           (T("Passport Number"), "person_id$passport.value"),
                           (T("Passport Expires"), "person_id$passport.valid_until"),
                           (T("Sectors"), "credential.job_title_id"),
                           (T("Trainings"), "training.course_id"),
                           # @todo: Languages (once implemented)
                           ]
            r.resource.configure(list_fields = list_fields)

        return True
    s3.prep = custom_prep

    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        if isinstance(output, dict):
            if r.controller == "deploy" and \
               "title" in output:
                output["title"] = T("RDRT Members")
            elif vnrc and \
                 r.method != "report" and \
                 "form" in output and \
                 (r.controller == "vol" or \
                  r.component_name == "human_resource"):
                # Remove the injected Programme field
                del output["form"][0].components[4]
                del output["form"][0].components[4]

        return output
    s3.postp = custom_postp

    return attr

settings.customise_hrm_human_resource_controller = customise_hrm_human_resource_controller

# -----------------------------------------------------------------------------
def customise_hrm_job_title_controller(**attr):

    s3 = current.response.s3
    table = current.s3db.hrm_job_title
    controller = current.request.controller
    if controller == "deploy":
        # Filter to just deployables
        s3.filter = (table.type == 4)
    else:
        # Organisation needs to be an NS/Branch
        ns_only(table.organisation_id,
                required = False,
                branches = False,
                )
    
    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
        else:
            result = True

        if controller == "deploy":
            field = table.type
            field.default = 4
            field.readable = field.writable = False
            table.organisation_id.readable = False
            table.organisation_id.writable = False

            SECTOR = T("Sector")
            ADD_SECTOR = T("Create Sector")
            help = T("If you don't see the Sector in the list, you can add a new one by clicking link 'Create Sector'.")
            s3.crud_strings["hrm_job_title"] = Storage(
                label_create=T("Create Sector"),
                title_display=T("Sector Details"),
                title_list=T("Sectors"),
                title_update=T("Edit Sector"),
                label_list_button=T("List Sectors"),
                label_delete_button=T("Delete Sector"),
                msg_record_created=T("Sector added"),
                msg_record_modified=T("Sector updated"),
                msg_record_deleted=T("Sector deleted"),
                msg_list_empty=T("No Sectors currently registered"))

        return result
    s3.prep = custom_prep

    return attr

settings.customise_hrm_job_title_controller = customise_hrm_job_title_controller

# -----------------------------------------------------------------------------
def customise_hrm_programme_controller(**attr):

    s3db = current.s3db

    # Organisation needs to be an NS/Branch
    ns_only(s3db.hrm_programme.organisation_id,
            required = False,
            branches = False,
            )

    # Special cases for different NS
    root_org = current.auth.root_org_name()
    if root_org == ARCS:
        settings.L10n.mandatory_lastname = False
        settings.hrm.vol_active = True
    elif root_org in (CVTL, PMI, PRC):
        settings.hrm.vol_active = vol_active
        settings.hrm.vol_active_tooltip = "A volunteer is defined as active if they've participated in an average of 8 or more hours of Program work or Trainings per month in the last year"
    elif root_org == VNRC:
        settings.pr.name_format = "%(last_name)s %(middle_name)s %(first_name)s"
        field = s3db.hrm_programme_hours.job_title_id
        field.readable = field.writable = False
        # @ToDo
        # def vn_age_group(age):
        # settings.pr.age_group = vn_age_group

    return attr

settings.customise_hrm_programme_controller = customise_hrm_programme_controller

# -----------------------------------------------------------------------------
def customise_hrm_programme_hours_controller(**attr):

    # Default Filter
    from s3 import s3_set_default_filter
    s3_set_default_filter("~.person_id$human_resource.organisation_id",
                          user_org_default_filter,
                          tablename = "hrm_programme_hours")

    # Special cases for different NS
    root_org = current.auth.root_org_name()
    if root_org == ARCS:
        settings.L10n.mandatory_lastname = False
        settings.hrm.vol_active = True
    elif root_org in (CVTL, PMI, PRC):
        settings.hrm.vol_active = vol_active
    elif root_org == VNRC:
        settings.pr.name_format = "%(last_name)s %(middle_name)s %(first_name)s"
        field = current.s3db.hrm_programme_hours.job_title_id
        field.readable = field.writable = False
        # Remove link to download Template
        attr["csv_template"] = "hide"

    return attr

settings.customise_hrm_programme_hours_controller = customise_hrm_programme_hours_controller

# -----------------------------------------------------------------------------
def customise_hrm_training_controller(**attr):

    # Default Filter
    from s3 import s3_set_default_filter
    s3_set_default_filter("~.person_id$human_resource.organisation_id",
                          user_org_default_filter,
                          tablename = "hrm_training")

    # Special cases for different NS
    root_org = current.auth.root_org_name()
    if root_org == ARCS:
        settings.L10n.mandatory_lastname = False
        settings.hrm.vol_active = True
    elif root_org in (CVTL, PMI, PRC):
        settings.hrm.vol_active = vol_active
    elif root_org == VNRC:
        settings.pr.name_format = "%(last_name)s %(middle_name)s %(first_name)s"
        # Remove link to download Template
        attr["csv_template"] = "hide"

    return attr

settings.customise_hrm_training_controller = customise_hrm_training_controller

# -----------------------------------------------------------------------------
def customise_hrm_training_event_controller(**attr):

    # Special cases for different NS
    root_org = current.auth.root_org_name()
    if root_org == ARCS:
        settings.L10n.mandatory_lastname = False
        settings.hrm.vol_active = True
    elif root_org in (CVTL, PMI, PRC):
        settings.hrm.vol_active = vol_active
    elif root_org == VNRC:
        settings.pr.name_format = "%(last_name)s %(middle_name)s %(first_name)s"
        # Remove link to download Template
        attr["csv_template"] = "hide"

    return attr

settings.customise_hrm_training_event_controller = customise_hrm_training_event_controller

# -----------------------------------------------------------------------------
def customise_inv_warehouse_resource(r, tablename):

    # Special cases for different NS
    root_org = current.auth.root_org_name()
    if root_org == "Australian Red Cross":
        # AusRC use proper Logistics workflow
        settings.inv.direct_stock_edits = False

settings.customise_inv_warehouse_resource = customise_inv_warehouse_resource

# -----------------------------------------------------------------------------
def customise_member_membership_controller(**attr):

    # @ToDo: If these NS start using Membership module
    #s3db = current.s3db
    #
    # Special cases for different NS
    #root_org = current.auth.root_org_name()
    #if root_org == ARCS:
    #    settings.L10n.mandatory_lastname = False
    #elif root_org == VNRC:
    #    settings.pr.name_format = "%(last_name)s %(middle_name)s %(first_name)s"
    #    # Remove link to download Template
    #    attr["csv_template"] = "hide"

    # Organisation needs to be an NS/Branch
    ns_only(current.s3db.member_membership.organisation_id,
            required = True,
            branches = True,
            )

    return attr

settings.customise_member_membership_controller = customise_member_membership_controller

# -----------------------------------------------------------------------------
def customise_member_membership_type_controller(**attr):

    # Organisation needs to be an NS/Branch
    ns_only(current.s3db.member_membership_type.organisation_id,
            required = False,
            branches = False,
            )

    return attr

settings.customise_member_membership_type_controller = customise_member_membership_type_controller

# -----------------------------------------------------------------------------
def customise_org_office_controller(**attr):

    # Organisation needs to be an NS/Branch
    ns_only(current.s3db.org_office.organisation_id,
            required = True,
            branches = True,
            )

    return attr

settings.customise_org_office_controller = customise_org_office_controller

# -----------------------------------------------------------------------------
def customise_org_organisation_controller(**attr):

    s3 = current.response.s3

    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
        else:
            result = True

        if not r.component or r.component_name == "branch":
            if r.interactive or r.representation == "aadata":
                s3db = current.s3db
                list_fields = ["id",
                               "name",
                               "acronym",
                               "organisation_organisation_type.organisation_type_id",
                               "country",
                               "website"
                               ]
                
                type_filter = r.get_vars.get("organisation_type.name",
                                             None)
                type_label = T("Type")
                if type_filter:
                    type_names = type_filter.split(",")
                    if len(type_names) == 1:
                        # Strip Type from list_fields
                        list_fields.remove("organisation_organisation_type.organisation_type_id")
                        type_label = ""

                    if type_filter == "Red Cross / Red Crescent":
                        # Modify filter_widgets
                        filter_widgets = s3db.get_config("org_organisation",
                                                         "filter_widgets")
                        # Remove type (always 'RC')
                        filter_widgets.pop(1)
                        # Remove sector (not relevant)
                        filter_widgets.pop(1)

                        # Modify CRUD Strings
                        s3.crud_strings.org_organisation = Storage(
                            label_create = T("Create National Society"),
                            title_display = T("National Society Details"),
                            title_list = T("Red Cross & Red Crescent National Societies"),
                            title_update = T("Edit National Society"),
                            title_upload = T("Import Red Cross & Red Crescent National Societies"),
                            label_list_button = T("List Red Cross & Red Crescent National Societies"),
                            label_delete_button = T("Delete National Society"),
                            msg_record_created = T("National Society added"),
                            msg_record_modified = T("National Society updated"),
                            msg_record_deleted = T("National Society deleted"),
                            msg_list_empty = T("No Red Cross & Red Crescent National Societies currently registered")
                            )
                        # Add Region to list_fields
                        list_fields.insert(-1, "region_id")
                        # Region is required
                        r.table.region_id.requires = r.table.region_id.requires.other
                    else:
                        r.table.region_id.readable = r.table.region_id.writable = False

                s3db.configure("org_organisation",
                               list_fields = list_fields,
                               )

                if r.interactive:
                    r.table.country.label = T("Country")
                    from s3.s3forms import S3SQLCustomForm, S3SQLInlineLink
                    crud_form = S3SQLCustomForm(
                        "name",
                        "acronym",
                        S3SQLInlineLink(
                            "organisation_type",
                            field = "organisation_type_id",
                            label = type_label,
                            multiple = False,
                            #widget = "hierarchy",
                        ),
                        "region_id",
                        "country",
                        "phone",
                        "website",
                        "logo",
                        "comments",
                        )
                    s3db.configure("org_organisation", crud_form=crud_form)

        return result
    s3.prep = custom_prep

    return attr

settings.customise_org_organisation_controller = customise_org_organisation_controller

# -----------------------------------------------------------------------------
def customise_pr_contact_resource(r, tablename):

    # Special cases for different NS
    root_org = current.auth.root_org_name()
    if root_org == VNRC:
        # Hard to translate in Vietnamese
        current.s3db.pr_contact.value.label = ""

settings.customise_pr_contact_resource = customise_pr_contact_resource

# -----------------------------------------------------------------------------
def customise_pr_group_controller(**attr):

    s3db = current.s3db

    # Organisation needs to be an NS/Branch
    ns_only(s3db.org_organisation_team.organisation_id,
            required = False,
            branches = True,
            )

    s3 = current.response.s3

    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
        else:
            result = True

        if r.component_name == "group_membership":
            # Special cases for different NS
            root_org = current.auth.root_org_name()
            if root_org == VNRC:
                settings.pr.name_format = "%(last_name)s %(middle_name)s %(first_name)s"
                # Update the represent as already set
                s3db.pr_group_membership.person_id.represent = s3db.pr_PersonRepresent()

        return result
    s3.prep = custom_prep

    return attr

settings.customise_pr_group_controller = customise_pr_group_controller

# =============================================================================
def vol_active(person_id):
    """
        Whether a Volunteer counts as 'Active' based on the number of hours
        they've done (both Trainings & Programmes) per month, averaged over
        the last year.
        If nothing recorded for the last 3 months, don't penalise as assume
        that data entry hasn't yet been done.

        @ToDo: This should be based on the HRM record, not Person record
               - could be active with Org1 but not with Org2
        @ToDo: allow to be calculated differently per-Org
    """

    now = current.request.utcnow

    # Time spent on Programme work
    htable = current.s3db.hrm_programme_hours
    query = (htable.deleted == False) & \
            (htable.person_id == person_id) & \
            (htable.date != None)
    programmes = current.db(query).select(htable.hours,
                                          htable.date,
                                          orderby=htable.date)
    if programmes:
        # Ignore up to 3 months of records
        three_months_prior = (now - timedelta(days=92))
        end = max(programmes.last().date, three_months_prior.date())
        last_year = end - timedelta(days=365)
        # Is this the Volunteer's first year?
        if programmes.first().date > last_year:
            # Only start counting from their first month
            start = programmes.first().date
        else:
            # Start from a year before the latest record
            start = last_year

        # Total hours between start and end
        programme_hours = 0
        for programme in programmes:
            if programme.date >= start and programme.date <= end and programme.hours:
                programme_hours += programme.hours

        # Average hours per month
        months = max(1, (end - start).days / 30.5)
        average = programme_hours / months

        # Active?
        if average >= 8:
            return True
        else:
            return False
    else:
        return False

# -----------------------------------------------------------------------------
def customise_pr_person_controller(**attr):

    s3db = current.s3db

    # Special cases for different NS
    arcs = False
    vnrc = False
    root_org = current.auth.root_org_name()
    if root_org == ARCS:
        arcs = True
        settings.L10n.mandatory_lastname = False
        # Override what has been set in the model already
        s3db.pr_person.last_name.requires = None
        settings.hrm.use_code = True
        settings.hrm.use_skills = True
        settings.hrm.vol_active = True
    elif root_org == PMI:
        settings.hrm.use_skills = True
        settings.hrm.staff_experience = "experience"
        settings.hrm.vol_experience = "both"
        settings.hrm.vol_active = vol_active
        settings.hrm.vol_active_tooltip = "A volunteer is defined as active if they've participated in an average of 8 or more hours of Program work or Trainings per month in the last year"
    elif root_org in (CVTL, PRC):
        settings.hrm.vol_active = vol_active
        settings.hrm.vol_active_tooltip = "A volunteer is defined as active if they've participated in an average of 8 or more hours of Program work or Trainings per month in the last year"
        if root_org == CVTL:
            settings.member.cv_tab = True
    elif root_org == VNRC:
        vnrc = True
        # Remove 'Commune' level for Addresses
        #gis = current.gis
        #gis.get_location_hierarchy()
        #try:
        #    gis.hierarchy_levels.pop("L3")
        #except:
        #    # Must be already removed
        #    pass
        settings.gis.postcode_selector = False # Needs to be done before prep as read during model load
        settings.hrm.use_skills = True
        settings.hrm.vol_experience = "both"
        settings.pr.name_format = "%(last_name)s %(middle_name)s %(first_name)s"
        try:
            settings.modules.pop("asset")
        except:
            # Must be already removed
            pass

    if current.request.controller == "deploy":
        # Replace default title in imports:
        attr["retitle"] = lambda r: {"title": T("Import Members")} \
                            if r.method == "import" else None

    s3 = current.response.s3

    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        component_name = r.component_name
        if component_name == "appraisal":
            atable = r.component.table
            atable.organisation_id.readable = atable.organisation_id.writable = False
            # Organisation needs to be an NS
            #ns_only(atable.organisation_id,
            #        required = True,
            #        branches = False,
            #        )
            field = atable.supervisor_id
            field.readable = field.writable = False
            field = atable.job_title_id
            field.comment = None
            field.label = T("Sector") # RDRT-specific
            from s3.s3validators import IS_ONE_OF
            field.requires = IS_ONE_OF(current.db, "hrm_job_title.id",
                                       field.represent,
                                       filterby = "type",
                                       filter_opts = (4,),
                                       )
        elif r.method == "cv" or component_name == "education":
            if vnrc:
                # Don't enable Legacy Freetext field
                # Hide the 'Name of Award' field
                field = s3db.pr_education.award
                field.readable = field.writable = False
            elif arcs:
                # Don't enable Legacy Freetext field
                pass
            else:
                # Enable Legacy Freetext field
                field = s3db.pr_education.level
                field.readable = field.writable = True
                field.label = T("Other Level")
                field.comment = T("Use main dropdown whenever possible")

        elif r.method =="record" or component_name == "human_resource":
            # Organisation needs to be an NS/Branch
            ns_only(s3db.hrm_human_resource.organisation_id,
                    required = True,
                    branches = True,
                    )

        if arcs:
            if not r.component:
                s3db.pr_person_details.father_name.label = T("Name of Grandfather")

        elif vnrc:
            if not r.component:
                # Use a free-text version of religion field
                field = s3db.pr_person_details.religion_other
                field.label = T("Religion")
                field.readable = field.writable = True
                # Also hide some other fields
                from s3.s3forms import S3SQLCustomForm
                crud_form = S3SQLCustomForm("first_name",
                                            "middle_name",
                                            "last_name",
                                            "date_of_birth",
                                            #"initials",
                                            #"preferred_name",
                                            #"local_name",
                                            "gender",
                                            "person_details.marital_status",
                                            "person_details.nationality",
                                            "person_details.religion_other",
                                            "person_details.mother_name",
                                            "person_details.father_name",
                                            #"person_details.occupation",
                                            #"person_details.company",
                                            "person_details.affiliations",
                                            "comments",
                                            )
                s3db.configure("pr_person",
                               crud_form = crud_form,
                               )
            if r.method == "record" or \
               component_name == "human_resource":
                field = s3db.hrm_human_resource.job_title_id
                field.readable = field.writable = False
                field = s3db.hrm_programme_hours.job_title_id
                field.readable = field.writable = False

            elif component_name == "address":
                settings.gis.building_name = False
                settings.gis.latlon_selector = False
                settings.gis.map_selector = False

            elif component_name == "identity":
                table = s3db.pr_identity
                table.description.readable = False
                table.description.writable = False
                pr_id_type_opts = {1: T("Passport"),
                                   2: T("National ID Card"),
                                   }
                from gluon.validators import IS_IN_SET
                table.type.requires = IS_IN_SET(pr_id_type_opts,
                                                zero=None)

            elif component_name == "hours":
                field = s3db.hrm_programme_hours.job_title_id
                field.readable = field.writable = False

            elif component_name == "physical_description":
                # Add the less-specific blood types (as that's all the data currently available in some cases)
                field = s3db.pr_physical_description.blood_type
                from gluon.validators import IS_EMPTY_OR, IS_IN_SET
                blood_type_opts = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "A", "B", "AB", "O")
                field.requires = IS_EMPTY_OR(IS_IN_SET(blood_type_opts))

            elif r.method == "cv" or component_name == "experience":
                table = s3db.hrm_experience
                # Use simple free-text variants
                table.organisation.readable = True
                table.organisation.writable = True
                table.job_title.readable = True
                table.job_title.writable = True
                table.comments.label = T("Main Duties")
                from s3.s3forms import S3SQLCustomForm
                crud_form = S3SQLCustomForm("organisation",
                                            "job_title",
                                            "comments",
                                            "start_date",
                                            "end_date",
                                            )
                s3db.configure("hrm_experience",
                               crud_form = crud_form,
                               list_fields = ["id",
                                              "organisation",
                                              "job_title",
                                              "comments",
                                              "start_date",
                                              "end_date",
                                              ],
                               )

        return True
    s3.prep = custom_prep

    attr["rheader"] = lambda r, vnrc=vnrc: pr_rheader(r, vnrc)
    if vnrc:
        # Link to customised download Template
        #attr["csv_template"] = ("../../themes/IFRC/formats", "volunteer_vnrc")
        # Remove link to download Template
        attr["csv_template"] = "hide"
    return attr

settings.customise_pr_person_controller = customise_pr_person_controller

# -----------------------------------------------------------------------------
def pr_rheader(r, vnrc):
    """
        Custom rheader for vol/person for vnrc
    """

    controller = current.request.controller
    if vnrc and controller == "vol":
        # Simplify RHeader
        settings.hrm.vol_experience = None

    if controller == "member":
        return current.s3db.member_rheader(r)
    else:
        s3db = current.s3db
        s3db.hrm_vars()
        return s3db.hrm_rheader(r)

# -----------------------------------------------------------------------------
def customise_req_commit_controller(**attr):

    # Request is mandatory
    field = current.s3db.req_commit.req_id
    field.requires = field.requires.other

    return attr

settings.customise_req_commit_controller = customise_req_commit_controller

# -----------------------------------------------------------------------------
def customise_req_req_controller(**attr):

    # Request is mandatory
    field = current.s3db.req_commit.req_id
    field.requires = field.requires.other

    return attr

settings.customise_req_req_controller = customise_req_req_controller

# -----------------------------------------------------------------------------
def customise_survey_series_controller(**attr):

    # Organisation needs to be an NS/Branch
    ns_only(current.s3db.survey_series.organisation_id,
            required = False,
            branches = True,
            )

    return attr

settings.customise_survey_series_controller = customise_survey_series_controller

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
# Uncomment this to enable Hazards in 3W projects
settings.project.hazards = True
# Uncomment this to use multiple Budgets per project
settings.project.multiple_budgets = True
# Uncomment this to use multiple Organisations per project
settings.project.multiple_organisations = True
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
def customise_project_project_controller(**attr):

    # Default Filter
    from s3 import s3_set_default_filter
    s3_set_default_filter("~.organisation_id",
                          user_org_default_filter,
                          tablename = "project_project")

    s3db = current.s3db
    tablename = "project_project"
    # Load normal model
    table = s3db[tablename]

    # @ToDo: S3SQLInlineComponent for Project orgs
    # Get IDs for PartnerNS/Partner-Donor
    # db = current.db
    # ttable = db.org_organisation_type
    # rows = db(ttable.deleted != True).select(ttable.id,
    #                                          ttable.name,
    #                                          )
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
            required = True,
            branches = False,
            )
    f.label = T("Host National Society")

    # Custom Crud Form
    from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineComponentCheckbox
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
            translate = True,
        ),
        S3SQLInlineComponentCheckbox(
            "sector",
            label = T("Sectors"),
            field = "sector_id",
            cols = 4,
            translate = True,
        ),
        S3SQLInlineComponentCheckbox(
            "theme",
            label = T("Themes"),
            field = "theme_id",
            cols = 4,
            translate = True,
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
        # & also rewriting for organisation_type_id via link table
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

    # Set the Host NS filter as Visible so that the default filter works
    filter_widgets = s3db.get_config(tablename, "filter_widgets")
    for widget in filter_widgets:
        if widget.field == "organisation_id":
            widget.opts.hidden = False
            break

    s3db.configure(tablename,
                   crud_form = crud_form,
                   )

    return attr

settings.customise_project_project_controller = customise_project_project_controller

# -----------------------------------------------------------------------------
def customise_project_location_resource(r, tablename):

    from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponentCheckbox
    crud_form = S3SQLCustomForm(
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
            translate = True,
            ),
        "comments",
        )

    current.s3db.configure(tablename,
                           crud_form = crud_form,
                           )

settings.customise_project_location_resource = customise_project_location_resource

# -----------------------------------------------------------------------------
# Inventory Management
settings.inv.show_mode_of_transport = True
settings.inv.send_show_time_in = True
#settings.inv.collapse_tabs = True
# Uncomment if you need a simpler (but less accountable) process for managing stock levels
settings.inv.direct_stock_edits = True

# -----------------------------------------------------------------------------
# Request Management
# Uncomment to disable Inline Forms in Requests module
settings.req.inline_forms = False
settings.req.req_type = ["Stock"]
settings.req.use_commit = False
# Should Requests ask whether Transportation is required?
settings.req.ask_transport = True

# -----------------------------------------------------------------------------
def customise_vulnerability_data_resource(r, tablename):

    # Date is required: We don't store modelled data
    r.table.date.requires = r.table.date.requires.other

settings.customise_vulnerability_data_resource = customise_vulnerability_data_resource

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
    ("deploy", Storage(
           name_nice = T("Regional Disaster Response Teams"),
           #description = "Alerting and Deployment of Disaster Response Teams",
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
