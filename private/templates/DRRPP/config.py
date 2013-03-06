# -*- coding: utf-8 -*-

from gluon import current, TAG, DIV, H3, SQLFORM
from gluon.storage import Storage
from gluon.contrib.simplejson.ordered_dict import OrderedDict
from s3 import s3forms, s3search

settings = current.deployment_settings
T = current.T

"""
    Template settings for DRRPP
"""
# =============================================================================
# Base Deployment Settings

# Pre-Populate
settings.base.prepopulate = ["DRRPP"]

settings.base.system_name = T("DRR Project Portal")
settings.base.system_name_short = T("DRRPP")

# Theme (folder to use for views/layout.html)
settings.base.theme = "DRRPP"

# =============================================================================
# Auth Deployment Settings

# Security Policy
settings.security.policy = 6 # Realm
settings.security.map = True

# Do new users need to verify their email address?
settings.auth.registration_requires_verification = True
# Do new users need to be approved by an administrator prior to being able to login?
settings.auth.registration_requires_approval = True
# Uncomment this to request the Organisation when a user registers
settings.auth.registration_requests_organisation = True
settings.auth.registration_pending = \
"""Registration awaiting approval from Administrator or Organisation Contact.
A confirmation email will be sent to you once approved.
For enquiries contact %s""" % settings.get_mail_approver()

# Record Approval
settings.auth.record_approval = True
settings.auth.record_approval_required_for = ["org_organisation",
                                              "project_project",
                                              "project_framework"
                                              ]

# =============================================================================
# L10n Deployment Settings
settings.L10n.languages = OrderedDict([
    ("en-gb", "English"),
])
settings.L10n.default_language = "en-gb"
# Default timezone for users
settings.L10n.utc_offset = "UTC +0700"
# Number formats (defaults to ISO 31-0)
# Decimal separator for numbers (defaults to ,)
settings.L10n.decimal_separator = "."
# Thousands separator for numbers (defaults to space)
settings.L10n.thousands_separator = ","
# Unsortable 'pretty' date format
#settings.L10n.date_format = T("%d-%b-%Y")
#settings.L10n.datetime_format = T("%d-%b-%Y %H:%M:%S")

# =============================================================================
# Finance Deployment Settings
settings.fin.currencies = {
    #"AUD" : T("Australian Dollars"),
    #"CAD" : T("Canadian Dollars"),
    #"EUR" : T("Euros"),
    #"GBP" : T("Great British Pounds"),
    #"PHP" : T("Philippine Pesos"),
    #"CHF" : T("Swiss Francs"),
    "USD" : T("United States Dollars"),
    "NZD" : T("New Zealand Dollars"),
}

# =============================================================================
# GIS Deployment Settings
# Theme
settings.gis.map_height = 600
settings.gis.map_width = 854

# Display Resources recorded to Admin-Level Locations on the map
# @ToDo: Move into gis_config?
settings.gis.display_L0 = True
# Deployment only covers Asia-Pacific
settings.gis.countries = [ "AF", "AU", "BD", "BN", "CK", "CN", "FJ", "FM", "HK", "ID", "IN", "JP", "KH", "KI", "KP", "KR", "LA", "MH", "MM", "MN", "MV", "MY", "NP", "NZ", "PG", "PH", "PK", "PW", "SB", "SG", "SL", "TH", "TL", "TO", "TV", "TW", "VN", "VU", "WS"]

# =============================================================================
# Project Deployment Settings
# Uncomment this to use settings suitable for a global/regional organisation (e.g. DRR)
settings.project.mode_3w = True
# Uncomment this to use DRR (Disaster Risk Reduction) extensions
settings.project.mode_drr = True
# Uncomment this to use Codes for projects
settings.project.codes = True
# Uncomment this to call project locations 'Communities'
#settings.project.community = True
# Uncomment this to create a project_location for each country which is a project is implemented in
# - done via Custom Form instead
#settings.project.locations_from_countries = True
# Uncomment this to use multiple Budgets per project
#settings.project.multiple_budgets = True
# Uncomment this to use multiple Organisations per project
settings.project.multiple_organisations = True
# Uncomment this to disable Sectors in projects
settings.project.sectors = False
# Uncomment this to customise
# Links to Filtered Components for Donors & Partners
settings.project.organisation_roles = {
    1: T("Lead Organization"),
    2: T("Partner Organization"),
    3: T("Donor"),
    #4: T("Customer"), # T("Beneficiary")?
    #5: T("Partner")
}

# =============================================================================
# UI Deployment Settings
# Enable this for a UN-style deployment
settings.ui.cluster = True

settings.ui.hide_report_options = False
settings.ui.hide_report_filter_options = True

# Uncomment to restrict the export formats available
settings.ui.export_formats = ["xls", "xml"]

# -----------------------------------------------------------------------------
# Formstyle
def formstyle_row(id, label, widget, comment, hidden=False):
    if hidden:
        hide = "hide"
    else:
        hide = ""
    row = DIV(DIV(comment, label,
                  _id=id + "1",
                  _class="w2p_fl %s" % hide),
              DIV(widget,
                  _id=id,
                  _class="w2p_fw %s" % hide),
              _class = "w2p_r",
              )
    return row

# -----------------------------------------------------------------------------
def form_style(self, xfields):
    """
        Use new Web2Py formstyle to generate form using DIVs & CSS
        CSS can then be used to create MUCH more flexible form designs:
        - Labels above vs. labels to left
        - Multiple Columns 
        @ToDo: Requires further changes to code to use
    """
    form = DIV()

    for id, a, b, c, in xfields:
        form.append(formstyle_row(id, a, b, c))

    return form

settings.ui.formstyle_row = formstyle_row
#settings.ui.formstyle = form_style # Breaks e.g. org/organisation/create
settings.ui.formstyle = formstyle_row

# -----------------------------------------------------------------------------
def customize_project_project(**attr):
    """
        Customize project_project controller
    """

    s3db = current.s3db
    s3 = current.response.s3
    tablename = "project_project"
    # Load normal model
    table = s3db[tablename]

    # Custom Components
    add_component = s3db.add_component
    add_component("project_drrpp",
                  project_project=Storage(joinby="project_id",
                                          multiple = False))
    add_component("project_output", project_project="project_id")

    # Custom CRUD Strings
    crud_strings = s3.crud_strings
    crud_strings.project_project.title_search = T("Project List")

    # Custom Fields
    table.name.label = T("Project Title")
    s3db.project_project.budget.label = T("Total Funding")
    location_id = s3db.project_location.location_id
    location_id.label = ""
    # Limit to just Countries
    location_id.requires = s3db.gis_country_requires
    # Use dropdown, not AC
    location_id.widget = None
    # In DRRPP this is a free field
    table = s3db.project_organisation
    table.comments.label = T("Role")
    table.comments.widget = SQLFORM.widgets.string.widget
    table.amount.label = T("Amount")
    table = s3db.doc_document
    table.file.widget = lambda field, value, download_url: \
        SQLFORM.widgets.upload.widget(field, value, download_url, _size = 15)
    table.comments.widget = SQLFORM.widgets.string.widget

    # Custom dataTable
    s3["dataTable_sDom"] = 'ripl<"dataTable_table"t>p'

    # Don't show export buttons for XLS/XML    
    s3.formats = Storage(xls= None, xml = None)
    
    # Remove rheader
    attr["rheader"] = None
    
    # Custom PreP
    standard_prep = s3.prep
    def drrpp_prep(r):
        # Call standard prep
        if callable(standard_prep):
            output = standard_prep(r)
        else:
            output = True
        if r.interactive:
            # Don't show Update/Delete button on Search table 
            if r.method == "search":
                s3db.configure(tablename,
                               editable = False,
                               deletable = False
                               )

            # Is Cook Islands in the Locations?
            pltable = s3db.project_location
            ltable = s3db.gis_location
            query = (pltable.project_id == r.id) & \
                    (pltable.location_id == ltable.id) & \
                    (ltable.name =="Cook Islands")
            if current.db(query).select(pltable.id,
                                        limitby=(0, 1)).first() is None:
                drrpptable = s3db.project_drrpp
                drrpptable.pifacc.readable = False
                drrpptable.pifacc.writable = False
                drrpptable.jnap.readable = False
                drrpptable.jnap.writable = False
                drrpptable.L1.readable = False
                drrpptable.L1.writable = False
            else:
                # If no Cook Islands are checked, then check them all
                script = '''
if($('[name=sub_drrpp_L1]').is(':checked')==false){
 $('[name=sub_drrpp_L1]').attr('checked','checked')}'''
                s3.jquery_ready.append(script)
        elif r.representation == "xls":
            # All readable Fields should be exported
            list_fields = ["id",
                           "name",
                           "code",
                           "status_id",
                           "start_date",
                           "end_date",
                           "drrpp.duration",
                           (T("Countries"), "location.location_id"),
                           "drrpp.L1",
                           (T("Hazards"), "hazard.name"),
                           (T("Themes"), "theme.name"),
                           "objectives",
                           "drrpp.activities",
                           "output.name",
                           "drr.hfa",
                           "drrpp.rfa",
                           "drrpp.pifacc",
                           "drrpp.jnap",
                           (T("Lead Organization"), "organisation_id"),
                           (T("Partners"), "partner.organisation_id"),
                           (T("Donors"), "donor.organisation_id"),
                           "budget",
                           "currency",
                           "drrpp.focal_person",
                           "drrpp.organisation_id",
                           "drrpp.email",
                           "url.url",
                           "drrpp.parent_project",
                           "comments",
                           ]
            s3db.configure(tablename,
                           list_fields = list_fields)
        return output
    s3.prep = drrpp_prep

    # Custom List Fields
    list_fields = ["id",
                   "name",
                   "start_date",
                   (T("Countries"), "location.location_id"),
                   (T("Hazards"), "hazard.name"),
                   (T("Lead Organization"), "organisation_id"),
                   (T("Donors"), "donor.organisation_id"),
                   ]

    # Custom Search Fields
    S3SearchSimpleWidget = s3search.S3SearchSimpleWidget
    S3SearchOptionsWidget = s3search.S3SearchOptionsWidget
    simple = [
        S3SearchSimpleWidget(name = "project_search_text_advanced",
                             label = T("Search Projects"),
                             comment = T("Search for a Project by name, code, or description."),
                             field = ["name",
                                      "code",
                                      "description",
                                      ]
                             ),
        S3SearchOptionsWidget(name = "project_search_status",
                              label = T("Status"),
                              field = "status_id",
                              cols = 4,
                              )
        ]

    project_hfa_opts = s3db.project_hfa_opts()
    hfa_options = {}
    #hfa_options = {None:NONE} To search NO HFA
    for key in project_hfa_opts.keys():
        hfa_options[key] = "HFA %s" % key
    project_rfa_opts = s3db.project_rfa_opts()
    rfa_options = {}
    #rfa_options = {None:NONE} To search NO RFA
    for key in project_rfa_opts.keys():
        rfa_options[key] = "RFA %s" % key

    advanced = [
        S3SearchOptionsWidget(name = "project_search_location",
                              label = T("Country"),
                              field = "location.location_id",
                              cols = 3
                              ),
        S3SearchOptionsWidget(name = "project_search_hazard",
                              label = T("Hazard"),
                              field = "hazard.id",
                              options = s3db.project_hazard_opts,
                              help_field = s3db.project_hazard_helps,
                              cols = 4
                              ),
        S3SearchOptionsWidget(name = "project_search_theme",
                              label = T("Theme"),
                              field = "theme.id",
                              options = s3db.project_theme_opts,
                              help_field = s3db.project_theme_helps,
                              cols = 4
                              ),
        S3SearchOptionsWidget(name = "project_search_hfa",
                              label = T("HFA"),
                              field = "drr.hfa",
                              options = hfa_options,
                              help_field = project_hfa_opts,
                              cols = 5
                              ),
       S3SearchOptionsWidget(name = "project_search_rfa",
                             label = T("RFA"),
                             field = "drrpp.rfa",
                             options = rfa_options,
                             help_field = project_rfa_opts,
                             cols = 6
                             ),
       S3SearchOptionsWidget(name = "project_search_organisation_id",
                             label = T("Lead Organisation"),
                             field = "organisation_id",
                             cols = 3
                             ),
       S3SearchOptionsWidget(name = "project_search_partners",
                             field = "partner.organisation_id",
                             label = T("Partners"),
                             cols = 3,
                             ),
       S3SearchOptionsWidget(name = "project_search_donors",
                             field = "donor.organisation_id",
                             label = T("Donors"),
                             cols = 3,
                             )
     ]
    project_search = s3search.S3Search(simple = simple,
                                       advanced = simple + advanced)

    # Custom Report Fields
    report_fields = [(T("Countries"), "location.location_id"),
                     (T("Hazards"), "hazard.name"),
                     (T("Themes"), "theme.name"),
                     (T("HFA Priorities"), "drr.hfa"),
                     (T("RFA Priorities"), "drrpp.rfa"),
                     (T("Lead Organization"), "organisation_id"),
                     (T("Partner Organizations"), "partner.organisation_id"),
                     (T("Donors"), "donor.organisation_id"),
                     ]
    # Report Settings for charts
    if "chart" in current.request.vars:
        crud_strings[tablename].title_report  = T("Project Graph")
        report_fact_fields = [("project.id", "count")]
        report_fact_default = "project.id"
    else:
        crud_strings[tablename].title_report  = T("Project Matrix")
        report_fact_fields = [(field, "count") for field in report_fields]
        report_fact_default = "theme.name"
    report_options = Storage(search = advanced,
                             rows = report_fields,
                             cols = report_fields,
                             fact = report_fact_fields,
                             defaults = Storage(rows = "hazard.name",
                                                cols = "location.location_id",
                                                fact = report_fact_default,
                                                aggregate = "count",
                                                totals = True
                                                )
                             )

    # Custom Crud Form
    crud_form = s3forms.S3SQLCustomForm(
        "name",
        "code",
        "status_id",
        "start_date",
        "end_date",
        "drrpp.duration",
        s3forms.S3SQLInlineComponent(
            "location",
            label = T("Countries"),
            fields = ["location_id"],
            orderby = "location_id$name"
        ),
        "drrpp.L1",
        s3forms.S3SQLInlineComponentCheckbox(
            "hazard",
            label = T("Hazards"),
            field = "hazard_id",
            cols = 4,
        ),
        s3forms.S3SQLInlineComponentCheckbox(
            "theme",
            label = T("Themes"),
            field = "theme_id",
            cols = 3,
        ),
        "objectives",
        "drrpp.activities",
        # Outputs
        s3forms.S3SQLInlineComponent(
            "output",
            label = T("Outputs"),
            #comment = "Bob",
            fields = ["name", "status"],
        ),
        "drr.hfa",
        "drrpp.rfa",
        "drrpp.pifacc",
        "drrpp.jnap",
        "organisation_id",
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
        # Donors
        s3forms.S3SQLInlineComponent(
            "organisation",
            name = "donor",
            label = T("Donor(s)"),
            fields = ["organisation_id", "amount", "currency"],
            filterby = dict(field = "role",
                            options = "3"
                            )
        ),
        "budget",
        "currency",
        "drrpp.focal_person",
        "drrpp.organisation_id",
        "drrpp.email",
        # Files
        s3forms.S3SQLInlineComponent(
            "document",
            name = "file",
            label = T("Files"),
            fields = ["file", "comments"],
            filterby = dict(field = "file",
                            options = "",
                            invert = True,
                            )
        ),
        # Links
        s3forms.S3SQLInlineComponent(
            "document",
            name = "url",
            label = T("Links"),
            fields = ["url", "comments"],
            filterby = dict(field = "url",
                            options = None,
                            invert = True,
                            )
        ),
        "drrpp.parent_project",
        "comments",
    )

    s3db.configure(tablename,
                   crud_form = crud_form,
                   list_fields = list_fields,
                   report_options = report_options,
                   search_method = project_search,
                   subheadings = {1: "hazard",
                                  2: "theme",
                                  3: "objectives",
                                  4: "drr_hfa",
                                  5: "drrpp_rfa",
                                  6: "drrpp_pifacc",
                                  7: "drrpp_jnap",
                                  8: "organisation_id",
                                  },
                   )
    
    return attr

settings.ui.customize_project_project = customize_project_project

# -----------------------------------------------------------------------------
def customize_project_framework(**attr):
    """
        Customize project_framework controller
    """

    s3db = current.s3db
    s3 = current.response.s3

    # Load normal model
    table = s3db.project_framework

    # Custom CRUD Strings
    s3.crud_strings.project_framework.title_list = \
        T("Policies & Strategies List")

    # Custom PreP
    standard_prep = s3.prep
    def drrpp_prep(r):
        # Call standard prep
        if callable(standard_prep):
            output = standard_prep(r)
        else:
            output = True
        if r.interactive:
            # Don't show Update/Delete button on List View
            if r.method is None:
                s3db.configure("project_framework",
                               insertable = False,
                               editable = False,
                               deletable = False
                               )
        return output
    s3.prep = drrpp_prep

    return attr

settings.ui.customize_project_framework = customize_project_framework

# -----------------------------------------------------------------------------
def customize_project_location(**attr):
    """
        Customize project_location controller
    """

    s3db = current.s3db
    s3 = current.response.s3

    # Load normal model
    table = s3db.project_location

    # Custom Components
    add_component = s3db.add_component
    add_component("project_drrpp",
                  project_project=Storage(joinby="project_id",
                                          multiple = False))
    add_component("project_output", project_project="project_id")

    # Custom CRUD Strings
    s3.crud_strings.project_location.title_map = \
        T("Project Map")

    # Custom Search Fields
    S3SearchSimpleWidget = s3search.S3SearchSimpleWidget
    S3SearchOptionsWidget = s3search.S3SearchOptionsWidget
    simple = [
        S3SearchSimpleWidget(name = "project_search_text_advanced",
                             label = T("Search Projects"),
                             comment = T("Search for a Project by name, code, or description."),
                             field = ["project_id$name",
                                      "project_id$code",
                                      "project_id$description",
                                      ]
                             ),
        S3SearchOptionsWidget(name = "project_search_status",
                              label = T("Status"),
                              field = "project_id$status_id",
                              cols = 4,
                              )
        ]

    project_hfa_opts = s3db.project_hfa_opts()
    hfa_options = {}
    #hfa_options = {None:NONE} To search NO HFA
    for key in project_hfa_opts.keys():
        hfa_options[key] = "HFA %s" % key
    project_rfa_opts = s3db.project_rfa_opts()
    rfa_options = {}
    #rfa_options = {None:NONE} To search NO RFA
    for key in project_rfa_opts.keys():
        rfa_options[key] = "RFA %s" % key

    advanced = [
        S3SearchOptionsWidget(name = "project_search_location",
                              label = T("Country"),
                              field = "location_id",
                              cols = 3
                              ),
        S3SearchOptionsWidget(name = "project_search_hazard",
                              label = T("Hazard"),
                              field = "project_id$hazard.name",
                              options = s3db.project_hazard_opts,
                              help_field="comments",
                              cols = 4
                              ),
        S3SearchOptionsWidget(name = "project_search_theme",
                              label = T("Theme"),
                              field = "project_id$theme.name",
                              options = s3db.project_theme_opts,
                              help_field="comments",
                              cols = 4
                              ),
        S3SearchOptionsWidget(name = "project_search_hfa",
                              label = T("HFA"),
                              field = "project_id$drr.hfa",
                              options = hfa_options,
                              help_field = project_hfa_opts,
                              cols = 5
                              ),
       S3SearchOptionsWidget(name = "project_search_rfa",
                             label = T("RFA"),
                             field = "project_id$drrpp.rfa",
                             options = rfa_options,
                             help_field = project_rfa_opts,
                             cols = 6
                             ),
       S3SearchOptionsWidget(name = "project_search_organisation_id",
                             label = T("Lead Organisation"),
                             field = "project_id$organisation_id",
                             cols = 3
                             ),
       S3SearchOptionsWidget(name = "project_search_partners",
                             field = "project_id$partner.organisation_id",
                             label = T("Partners"),
                             cols = 3,
                             ),
       S3SearchOptionsWidget(name = "project_search_donors",
                             field = "project_id$donor.organisation_id",
                             label = T("Donors"),
                             cols = 3,
                             )
     ]
    search_method = s3search.S3Search(simple = simple,
                                      advanced = simple + advanced)

    s3db.configure("project_location",
                   search_method = search_method,
                   )
    
    return attr

settings.ui.customize_project_framework = customize_project_framework

# -----------------------------------------------------------------------------
def customize_pr_person(**attr):
    """
        Customize pr_person controller
    """

    # Load normal model
    table = current.s3db.pr_person

    # Custom CRUD Strings
    current.response.s3.crud_strings.pr_person.title_display = T("My Page")

    attr["rheader"] = H3(T("Saved Searches"))
    return attr

settings.ui.customize_pr_person = customize_pr_person

# =============================================================================
# Enabled Modules
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
    ("gis", Storage(
            name_nice = T("Map"),
            #description = "Situation Awareness & Geospatial Analysis",
            restricted = True,
            module_type = 3,     # 6th item in the menu
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
    ("project", Storage(
            name_nice = T("Projects"),
            #description = "Tracking of Projects, Activities and Tasks",
            restricted = True,
            module_type = 1
        )),
])
