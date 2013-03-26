# -*- coding: utf-8 -*-

from gluon import current, TR, TD, DIV
from gluon.storage import Storage
from gluon.contrib.simplejson.ordered_dict import OrderedDict
settings = current.deployment_settings
T = current.T

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
settings.L10n.time_format = T("%H:%M:%S")
settings.L10n.datetime_format = T("%m-%d-%Y %H:%M")
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

# Request Management
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
# Uncomment to disable the use of HR Teams
#settings.hrm.use_teams = False
# Custom label for Organisations in HR module
#settings.hrm.organisation_label = "National Society / Branch"
settings.hrm.organisation_label = "Organization"

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
    s3db = current.s3db
    s3 = current.response.s3

    tablename = "project_project"
    
    s3db.project_project.code.label = T("Project blurb (max. 100 characters)")
    s3db.project_project.code.max_length = 100 
    s3db.project_project.comments.label = T("How people can help")

    location_id = s3db.project_location.location_id
    # Limit to just Countries
    location_id.requires = s3db.gis_location_id
    # Use dropdown, not AC
    #location_id.widget = s3.s3widgets.S3LocationAutocompleteWidget()

    script = '''$('#project_project_code').attr('maxlength','100')'''
    
    s3.jquery_ready.append(script)

    from s3 import s3forms

    crud_form = s3forms.S3SQLCustomForm(
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
       s3forms.S3SQLInlineComponent(
            "location",
            label = T("Location"),
            fields = ["location_id"],
        ),
        # Partner Orgs
        s3forms.S3SQLInlineComponent(
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
        s3forms.S3SQLInlineComponent(
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
        s3forms.S3SQLInlineComponentCheckbox(
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
    
    s3db.configure(tablename, crud_form = crud_form)
    
    return attr

settings.ui.customize_project_project = customize_project_project

# Uncomment to show created_by/modified_by using Names not Emails
settings.ui.auth_user_represent = "name"
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
