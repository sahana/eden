# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current, TR, TD, DIV
from gluon.storage import Storage

T = current.T
settings = current.deployment_settings

"""
    Template settings for US

    All settings which are to configure a specific template are located here

    Deployers should ideally not need to edit any other files outside of their template folder
"""

# Pre-Populate
settings.base.prepopulate = ["SandyRelief"]

settings.base.system_name = "Sandy Relief"
settings.base.system_name_short = "SandyRelief"

# Theme (folder to use for views/layout.html)
settings.base.theme = "SandyRelief"

# Uncomment to Hide the language toolbar
settings.L10n.display_toolbar = False
# Default timezone for users
settings.L10n.utc_offset = "UTC -0500"
# Uncomment these to use US-style dates in English (localisations can still convert to local format)
settings.L10n.date_format = T("%m-%d-%Y")
# Start week on Sunday
settings.L10n.firstDOW = 0
# Number formats (defaults to ISO 31-0)
# Decimal separator for numbers (defaults to ,)
settings.L10n.decimal_separator = "."
# Thousands separator for numbers (defaults to space)
settings.L10n.thousands_separator = ","
# Default Country Code for telephone numbers
settings.L10n.default_country_code = 1
# Enable this to change the label for 'Mobile Phone'
settings.ui.label_mobile_phone = "Cell Phone"
# Enable this to change the label for 'Postcode'
settings.ui.label_postcode = "ZIP Code"
# PDF to Letter
settings.base.paper_size = T("Letter")

# Restrict the Location Selector to just certain countries
# NB This can also be over-ridden for specific contexts later
# e.g. Activities filtered to those of parent Project
settings.gis.countries = ["US"]

settings.fin.currencies = {
    "USD" : T("United States Dollars"),
}

settings.L10n.languages = OrderedDict([
    ("en", "English"),
    ("es", "Español"),
])

# Authentication settings
# These settings should be changed _after_ the 1st (admin) user is
# registered in order to secure the deployment
# Should users be allowed to register themselves?
#settings.security.self_registration = False
# Do new users need to verify their email address?
settings.auth.registration_requires_verification = True
# Do new users need to be approved by an administrator prior to being able to login?
settings.auth.registration_requires_approval = True
# Always notify the approver of a new (verified) user, even if the user is automatically approved
#settings.auth.always_notify_approver = False
# Uncomment this to request the Organisation when a user registers
#settings.auth.registration_requests_organisation = True
# Uncomment this to request the Site when a user registers
settings.auth.registration_requests_site = True

# Roles that newly-registered users get automatically
settings.auth.registration_roles = { 0: ["comms_dispatch"]}

settings.auth.registration_link_user_to = {"staff":T("Staff"),
                                           #"volunteer":T("Volunteer")
                                           }

settings.security.policy = 5 # Controller, Function & Table ACLs

# Resource which need approval
#settings.auth.record_approval_required_for = ["org_facility"]

settings.ui.update_label = "Edit"
settings.ui.label_attachments = "Media"

# Uncomment to disable that LatLons are within boundaries of their parent
settings.gis.check_within_parent_boundaries = False

# -----------------------------------------------------------------------------
# Inventory Management
# Uncomment to customise the label for Facilities in Inventory Management
settings.inv.facility_label = "Facility"
# Uncomment if you need a simpler (but less accountable) process for managing stock levels
#settings.inv.direct_stock_edits = True
# Uncomment to call Stock Adjustments, 'Stock Counts'
settings.inv.stock_count = True
# Uncomment to not track pack values
settings.inv.track_pack_values = False
settings.inv.send_show_org = False
# Types common to both Send and Receive
settings.inv.shipment_types = {
        1: T("Other Warehouse")
    }
settings.inv.send_types = {
        #21: T("Distribution")
    }
settings.inv.send_type_default = 1
settings.inv.item_status = {
        #0: current.messages["NONE"],
        #1: T("Dump"),
        #2: T("Sale"),
        #3: T("Reject"),
        #4: T("Surplus")
   }

# -----------------------------------------------------------------------------
# Requests Management
settings.req.req_type = ["People", "Stock"]#, "Summary"]
settings.req.prompt_match = False
#settings.req.use_commit = False
settings.req.requester_optional = True
settings.req.date_writable = False
settings.req.item_quantities_writable = True
settings.req.skill_quantities_writable = True
settings.req.items_ask_purpose = False
#settings.req.use_req_number = False
# Label for Requester
settings.req.requester_label = "Site Contact"
# Filter Requester as being from the Site 
settings.req.requester_from_site = True
# Label for Inventory Requests
settings.req.type_inv_label = "Supplies"
# Uncomment to enable Summary 'Site Needs' tab for Offices/Facilities
settings.req.summary = True

# -----------------------------------------------------------------------------
# Organisations
# Disable the use of Organisation Branches
settings.org.branches = False
settings.org.site_label = "Facility"
# Uncomment to show the date when a Site (Facilities-only for now) was last contacted
settings.org.site_last_contacted = True
# Enable certain fields just for specific Organisations
# empty list => disabled for all (including Admin)
#settings.org.dependent_fields = { \
#     "pr_person_details.mother_name"             : [],
#     "pr_person_details.father_name"             : [],
#     "pr_person_details.company"                 : [],
#     "pr_person_details.affiliations"            : [],
#     "vol_volunteer.active"                      : [],
#     "vol_volunteer_cluster.vol_cluster_type_id"      : [],
#     "vol_volunteer_cluster.vol_cluster_id"          : [],
#     "vol_volunteer_cluster.vol_cluster_position_id" : [],
#     }
# Uncomment to use an Autocomplete for Site lookup fields
settings.org.site_autocomplete = True
# Uncomment to have Site Autocompletes search within Address fields
settings.org.site_address_autocomplete = True
# Uncomment to hide inv & req tabs from Sites
#settings.org.site_inv_req_tabs = True

# -----------------------------------------------------------------------------
def facility_marker_fn(record):
    """
        Function to decide which Marker to use for Facilities Map
        @ToDo: Legend
        @ToDo: Use Symbology
    """

    db = current.db
    s3db = current.s3db
    table = db.org_facility_type
    ltable = db.org_site_facility_type
    query = (ltable.site_id == record.site_id) & \
            (ltable.facility_type_id == table.id)
    rows = db(query).select(table.name)
    types = [row.name for row in rows]

    # Use Marker in preferential order
    if "Hub" in types:
        marker = "warehouse"
    elif "Medical Clinic" in types:
        marker = "hospital"
    elif "Food" in types:
        marker = "food"
    elif "Relief Site" in types:
        marker = "asset"
    elif "Residential Building" in types:
        marker = "residence"
    #elif "Shelter" in types:
    #    marker = "shelter"
    else:
        # Unknown
        marker = "office"
    if settings.has_module("req"):
        # Colour code by open/priority requests
        reqs = record.reqs
        if reqs == 3:
            # High
            marker = "%s_red" % marker
        elif reqs == 2:
            # Medium
            marker = "%s_yellow" % marker
        elif reqs == 1:
            # Low
            marker = "%s_green" % marker

    mtable = db.gis_marker
    try:
        marker = db(mtable.name == marker).select(mtable.image,
                                                  mtable.height,
                                                  mtable.width,
                                                  cache=s3db.cache,
                                                  limitby=(0, 1)
                                                  ).first()
    except:
        marker = db(mtable.name == "office").select(mtable.image,
                                                    mtable.height,
                                                    mtable.width,
                                                    cache=s3db.cache,
                                                    limitby=(0, 1)
                                                    ).first()
    return marker

def customize_org_facility(**attr):
    # Tell the client to request per-feature markers
    current.s3db.configure("org_facility", marker_fn=facility_marker_fn)

    return attr

settings.ui.customize_org_facility = customize_org_facility

# -----------------------------------------------------------------------------
def customize_org_organisation(**attr):

    s3db = current.s3db
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
            list_fields = ["id",
                           "name",
                           "acronym",
                           "organisation_type_id",
                           (T("Services"), "service.name"),
                           (T("Neighborhoods Served"), "location.name"),
                           ]
            s3db.configure("org_organisation", list_fields=list_fields)
            
        if r.interactive:
            from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineComponentCheckbox
            s3db.pr_address.comments.label = ""
            s3db.pr_contact.value.label = ""
            crud_form = S3SQLCustomForm(
                "name",
                "acronym",
                "organisation_type_id",
                S3SQLInlineComponentCheckbox(
                    "service",
                    label = T("Services"),
                    field = "service_id",
                    cols = 4,
                ),
                S3SQLInlineComponentCheckbox(
                    "group",
                    label = T("Network"),
                    field = "group_id",
                    cols = 3,
                ),
                S3SQLInlineComponent(
                    "address",
                    label = T("Address"),
                    multiple = False,
                    # This is just Text - put into the Comments box for now
                    # Ultimately should go into location_id$addr_street
                    fields = ["comments"],
                ),
                S3SQLInlineComponentCheckbox(
                    "location",
                    label = T("Neighborhoods Served"),
                    field = "location_id",
                    filterby = dict(field = "level",
                                    options = "L4"
                                    ),
                    cols = 5,
                ),
                "phone",
                S3SQLInlineComponent(
                    "contact",
                    name = "phone2",
                    label = T("Phone2"),
                    multiple = False,
                    fields = ["value"],
                    filterby = dict(field = "contact_method",
                                    options = "WORK_PHONE"
                                    )
                ),
                S3SQLInlineComponent(
                    "contact",
                    name = "email",
                    label = T("Email"),
                    multiple = False,
                    fields = ["value"],
                    filterby = dict(field = "contact_method",
                                    options = "EMAIL"
                                    )
                ),
                "website",
                S3SQLInlineComponent(
                    "contact",
                    name = "rss",
                    label = T("RSS"),
                    multiple = False,
                    fields = ["value"],
                    filterby = dict(field = "contact_method",
                                    options = "RSS"
                                    )
                ),
                S3SQLInlineComponent(
                    "contact",
                    name = "twitter",
                    label = T("Twitter"),
                    multiple = False,
                    fields = ["value"],
                    filterby = dict(field = "contact_method",
                                    options = "TWITTER"
                                    )
                ),
                "comments",
            )
            
            from s3.s3filter import S3LocationFilter, S3OptionsFilter, S3TextFilter
            filter_widgets = [
                S3TextFilter(["name", "acronym"],
                             label=T("Name"),
                             _class="filter-search",
                             ),
                S3OptionsFilter("group_membership.group_id",
                                label=T("Network"),
                                represent="%(name)s",
                                widget="multiselect",
                                cols=3,
                                #hidden=True,
                                ),
                S3LocationFilter("organisation_location.location_id",
                                 label=T("Neighborhood"),
                                 levels=["L3", "L4"],
                                 widget="multiselect",
                                 cols=3,
                                 #hidden=True,
                                 ),
                S3OptionsFilter("service_organisation.service_id",
                                label=T("Service"),
                                represent="%(name)s",
                                widget="multiselect",
                                cols=3,
                                #hidden=True,
                                ),
                S3OptionsFilter("organisation_type_id",
                                label=T("Type"),
                                represent="%(name)s",
                                widget="multiselect",
                                cols=3,
                                #hidden=True,
                                ),
                ]
            from s3.s3search import S3Search, S3SearchSimpleWidget, S3SearchOptionsWidget
            search_method = S3Search(
                simple=(),
                advanced=(
                    S3SearchSimpleWidget(
                        name="org_search_text_advanced",
                        label=T("Name"),
                        comment=T("Search for an Organization by name or acronym"),
                        field=["name", "acronym"]
                    ),
                    S3SearchOptionsWidget(
                        name="org_search_network",
                        label=T("Network"),
                        field="group.name",
                        cols=2
                    ),
                    S3SearchOptionsWidget(
                        name="org_search_location",
                        label=T("Neighborhood"),
                        field="location.L4",
                        location_level="L4",
                        cols=2
                    ),
                    S3SearchOptionsWidget(
                        name="org_search_service",
                        label=T("Services"),
                        field="service.name",
                        cols=2
                    ),
                    S3SearchOptionsWidget(
                        name="org_search_type",
                        label=T("Type"),
                        field="organisation_type_id",
                        cols=2
                    ),
                ))
            s3db.configure("org_organisation",
                           crud_form=crud_form,
                           # @ToDo: Style & Enable
                           #filter_widgets = filter_widgets,
                           search_method=search_method,
                           )

        return result
    s3.prep = custom_prep

    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        if r.interactive and isinstance(output, dict):
            if "rheader" in output:
                # Custom Tabs
                tabs = [(T("Basic Details"), None),
                        (T("Contacts"), "human_resource"),
                        (T("Facilities"), "facility"),
                        (T("Projects"), "project"),
                        (T("Assets"), "asset"),
                        ]
                output["rheader"] = s3db.org_rheader(r, tabs=tabs)
        return output
    s3.postp = custom_postp

    attr["hide_filter"] = False
    return attr

settings.ui.customize_org_organisation = customize_org_organisation

# -----------------------------------------------------------------------------
# Networks (org_group)
def customize_org_group(**attr):
    """
        Customize org_group controller
    """

    tablename = "org_group"
    # CRUD Strings
    current.response.s3.crud_strings[tablename] = Storage(
                title_create = T("Add Network"),
                title_display = T("Network Details"),
                title_list = T("Networks"),
                title_update = T("Edit Network"),
                title_search = T("Search Networks"),
                subtitle_create = T("Add New Network"),
                label_list_button = T("List Networks"),
                label_create_button = T("Add Network"),
                label_delete_button = T("Remove Network"),
                msg_record_created = T("Network added"),
                msg_record_modified = T("Network updated"),
                msg_record_deleted = T("Network removed"),
                msg_list_empty = T("No Networks currently recorded"))

    return attr

settings.ui.customize_org_group = customize_org_group

# -----------------------------------------------------------------------------
# Persons
# Uncomment to hide fields in S3AddPersonWidget
settings.pr.request_dob = False
settings.pr.request_gender = False
# Doesn't yet work (form fails to submit)
#settings.pr.select_existing = False

# -----------------------------------------------------------------------------
# Human Resource Management
# Uncomment to chage the label for 'Staff'
settings.hrm.staff_label = "Contacts"
# Uncomment to allow Staff & Volunteers to be registered without an email address
settings.hrm.email_required = False
# Uncomment to allow Staff & Volunteers to be registered without an Organisation
settings.hrm.org_required = False
# Uncomment to show the Organisation name in HR represents
settings.hrm.show_organisation = True
# Uncomment to disable Staff experience
settings.hrm.staff_experience = False
# Uncomment to disable the use of HR Certificates
settings.hrm.use_certificates = False
# Uncomment to disable the use of HR Credentials
settings.hrm.use_credentials = False
# Uncomment to enable the use of HR Education
settings.hrm.use_education = False
# Uncomment to disable the use of HR Skills
#settings.hrm.use_skills = False
# Uncomment to disable the use of HR Trainings
settings.hrm.use_trainings = False
# Uncomment to disable the use of HR Description
settings.hrm.use_description = False
# Change the label of "Teams" to "Groups"
settings.hrm.teams = "Groups"
# Custom label for Organisations in HR module
#settings.hrm.organisation_label = "National Society / Branch"
settings.hrm.organisation_label = "Organization"

def customize_hrm_human_resource(**attr):

    s3 = current.response.s3

    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
        else:
            result = True

        if r.interactive or r.representation == "aadata":
            s3db = current.s3db
            table = r.table
            table.department_id.readable = table.department_id.writable = False
            table.end_date.readable = table.end_date.writable = False
            list_fields = ["id",
                           "person_id",
                           "job_title_id",
                           "organisation_id",
                           (T("Groups"), "person_id$group_membership.group_id"),
                           "site_id",
                           #"site_contact",
                           (T("Email"), "email.value"),
                           (settings.get_ui_label_mobile_phone(), "phone.value"),
                           ]

            s3db.configure("hrm_human_resource", list_fields=list_fields)

        return result
    s3.prep = custom_prep

    return attr

settings.ui.customize_hrm_human_resource = customize_hrm_human_resource

# -----------------------------------------------------------------------------
# Projects
# Use codes for projects
settings.project.codes = True
# Uncomment this to use settings suitable for detailed Task management
settings.project.mode_task = False
# Uncomment this to use Activities for projects
settings.project.activities = True
# Uncomment this to use Milestones in project/task.
settings.project.milestones = False
# Uncomment this to disable Sectors in projects
settings.project.sectors = False
# Multiple partner organizations
settings.project.multiple_organisations = True

def customize_project_project(**attr):

    s3 = current.response.s3

    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
        else:
            result = True

        if r.interactive or r.representation == "aadata":
            from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineComponentCheckbox
            s3db = current.s3db

            table = r.table
            table.code.label = T("Project blurb (max. 100 characters)")
            table.code.max_length = 100 
            table.comments.label = T("How people can help")

            script = '''$('#project_project_code').attr('maxlength','100')'''
            s3.jquery_ready.append(script)

            crud_form = S3SQLCustomForm(
                "organisation_id",
                "name",
                "code",        
                "description",
                "status_id",
                "start_date",
                "end_date",
                "calendar",
                #"drr.hfa",
                #"objectives",
                "human_resource_id",
                # Activities
               S3SQLInlineComponent(
                    "location",
                    label = T("Location"),
                    fields = ["location_id"],
                ),
                # Partner Orgs
                S3SQLInlineComponent(
                    "organisation",
                    name = "partner",
                    label = T("Partner Organizations"),
                    fields = ["organisation_id",
                              "comments", # NB This is labelled 'Role' in DRRPP
                              ],
                    filterby = dict(field = "role",
                    options = "2"
                    )
                ),
                S3SQLInlineComponent(
                    "document",
                    name = "media",
                    label = T("URLs (media, fundraising, website, social media, etc."),
                    fields = ["document_id",
                              "name",
                              "url",
                              "comments",
                              ],
                    filterby = dict(field = "name")
                ),                                                                
                S3SQLInlineComponentCheckbox(
                    "activity_type",
                    label = T("Categories"),
                    field = "activity_type_id",
                    cols = 3,
                    # Filter Activity Type by Project
                    filter = {"linktable": "project_activity_type_project",
                              "lkey": "project_id",
                              "rkey": "activity_type_id",
                              },
                ),
                #"budget",
                #"currency",
                "comments",
            )
            
            s3db.configure("project_project", crud_form=crud_form)

        return result
    s3.prep = custom_prep

    return attr

settings.ui.customize_project_project = customize_project_project

# -----------------------------------------------------------------------------
# Uncomment to show created_by/modified_by using Names not Emails
settings.ui.auth_user_represent = "name"

# -----------------------------------------------------------------------------
# Formstyle
def formstyle_row(id, label, widget, comment, hidden=False):
    if hidden:
        hide = "hide"
    else:
        hide = ""
    row = TR(TD(DIV(label,
                    _id=id + "1",
                    _class="w2p_fl %s" % hide),
                DIV(widget,
                    _id=id,
                    _class="w2p_fw %s" % hide),
                DIV(comment,
                    _id=id, 
                    _class="w2p_fc %s" % hide),
                ))
    return row

def form_style(self, xfields):
    """
        @ToDo: Requires further changes to code to use
        - Adding a formstyle_row setting to use for indivdual rows
        Use new Web2Py formstyle to generate form using DIVs & CSS
        CSS can then be used to create MUCH more flexible form designs:
        - Labels above vs. labels to left
        - Multiple Columns 
    """
    form = DIV()

    for id, a, b, c, in xfields:
        form.append(formstyle_row(id, a, b, c))

    return form

settings.ui.formstyle_row = formstyle_row
settings.ui.formstyle = formstyle_row

# -----------------------------------------------------------------------------
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
            module_type = 9,     # 8th item in the menu
        )),
    ("pr", Storage(
            name_nice = T("Person Registry"),
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = 10
        )),
    ("org", Storage(
            name_nice = T("Locations"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = 4
        )),
    # All modules below here should be possible to disable safely
    ("hrm", Storage(
            name_nice = T("Contacts"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = 3,
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
            module_type = None,
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
            name_nice = T("Inventory"),
            #description = "Receiving and Sending Items",
            restricted = True,
            module_type = 10
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
            module_type = 10,
        )),
    # Vehicle depends on Assets
    #("vehicle", Storage(
    #        name_nice = T("Vehicles"),
    #        #description = "Manage Vehicles",
    #        restricted = True,
    #        module_type = 10,
    #    )),
    ("req", Storage(
            name_nice = T("Requests"),
            #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
            restricted = True,
            module_type = 1,
        )),
    ("project", Storage(
            name_nice = T("Projects"),
            #description = "Tracking of Projects, Activities and Tasks",
            restricted = True,
            module_type = 10
        )),
    ("assess", Storage(
            name_nice = T("Assessments"),
            #description = "Rapid Assessments & Flexible Impact Assessments",
            restricted = True,
            module_type = 5,
        )),
    ("survey", Storage(
            name_nice = T("Surveys"),
            #description = "Create, enter, and manage surveys.",
            restricted = True,
            module_type = 5,
        )),
    #("cr", Storage(
    #        name_nice = T("Shelters"),
    #        #description = "Tracks the location, capacity and breakdown of victims in Shelters",
    #        restricted = True,
    #        module_type = 10
    #    )),
    #("hms", Storage(
    #        name_nice = T("Hospitals"),
    #        #description = "Helps to monitor status of hospitals",
    #        restricted = True,
    #        module_type = 1
    #    )),
    #("irs", Storage(
    #        name_nice = T("Incidents"),
    #        #description = "Incident Reporting System",
    #        restricted = False,
    #        module_type = 10
    #    )),
    #("dvi", Storage(
    #       name_nice = T("Disaster Victim Identification"),
    #       #description = "Disaster Victim Identification",
    #       restricted = True,
    #       module_type = 10,
    #       #access = "|DVI|",      # Only users with the DVI role can see this module in the default menu & access the controller
    #       #audit_read = True,     # Can enable Audit for just an individual module here
    #       #audit_write = True
    #   )),
    #("mpr", Storage(
    #       name_nice = T("Missing Person Registry"),
    #       #description = "Helps to report and search for missing persons",
    #       restricted = False,
    #       module_type = 10,
    #   )),
    #("dvr", Storage(
    #       name_nice = T("Disaster Victim Registry"),
    #       #description = "Allow affected individuals & households to register to receive compensation and distributions",
    #       restricted = False,
    #       module_type = 10,
    #   )),
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
    #        restricted = False,
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
    #("security", Storage(
    #       name_nice = T("Security"),
    #       #description = "Security Management System",
    #       restricted = True,
    #       module_type = 10,
    #   )),
    # These are specialist modules
    # Requires RPy2
    #("climate", Storage(
    #        name_nice = T("Climate"),
    #        #description = "Climate data portal",
    #        restricted = True,
    #        module_type = 10,
    #)),
    #("delphi", Storage(
    #        name_nice = T("Delphi Decision Maker"),
    #        #description = "Supports the decision making of large groups of Crisis Management Experts by helping the groups create ranked list.",
    #        restricted = False,
    #        module_type = 10,
    #    )),
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
    #       module_type = None
    #   )),
])
