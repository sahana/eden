# -*- coding: utf-8 -*-

from gluon import current, TAG, DIV
from gluon.storage import Storage
from gluon.contrib.simplejson.ordered_dict import OrderedDict
settings = current.deployment_settings
T = current.T

"""
    Template settings for DRRPP
"""

# Pre-Populate
settings.base.prepopulate = ["DRRPP"]

settings.base.system_name = T("DRR Project Portal")
settings.base.system_name_short = T("DRRPP")

# Theme (folder to use for views/layout.html)
settings.base.theme = "DRRPP"

# Auth settings
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
settings.auth.record_approval_required_for = ["org_organisation", "project_project", "project_framework"]

# L10n settings
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

# Security Policy
settings.security.policy = 6 # Realm
settings.security.map = True

# Theme
settings.gis.map_height = 600
settings.gis.map_width = 854

# Display Resources recorded to Admin-Level Locations on the map
# @ToDo: Move into gis_config?
settings.gis.display_L0 = True
# Deployment only covers Asia-Pacific
settings.gis.countries = [ "AF", "AU", "BD", "BN", "CK", "CN", "FJ", "FM", "HK", "ID", "IN", "JP", "KH", "KI", "KP", "KR", "LA", "MH", "MM", "MN", "MV", "MY", "NP", "NZ", "PG", "PH", "PK", "PW", "SB", "SG", "SL", "TH", "TL", "TO", "TV", "TW", "VN", "VU", "WS"]

# Enable this for a UN-style deployment
settings.ui.cluster = True

settings.ui.hide_report_options = False
settings.ui.hide_report_filter_options = True

# Organisations
# Uncomment to add summary fields for Organisations/Offices for # National/International staff
#settings.org.summary = True # Doesn't work with DRRPP formstyle

# Projects
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
}

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

def form_style(self, xfields):
    """
        @ToDo: Requires further changes to code to use
        - Adding a formstyle_row setting to use for individual rows
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
#settings.ui.formstyle = form_style # Breaks e.g. org/organisation/create
settings.ui.formstyle = formstyle_row

def customize_project_project(**attr):
    s3db = current.s3db
    s3 = current.response.s3
    
    s3.crud_strings.project_project.title_search = T("Project List")
    table = s3db.project_project
    table.budget.label = T("Total Funding")

    # For Inline Forms
    location_id = s3db.project_location.location_id
    location_id.requires = s3db.gis_country_requires
    location_id.widget = None

    # In DRRPP this is a free field
    table = s3db.project_organisation
    table.comments.label = T("Role")
    from gluon import SQLFORM
    table.comments.widget = SQLFORM.widgets.string.widget
    table.amount.label = T("Amount")

    table = s3db.doc_document
    table.file.widget = lambda field, value, download_url: \
        SQLFORM.widgets.upload.widget(field, value, download_url, _size = 15)
    #table.file.widget = SQLFORM.widgets.upload.widget
    table.comments.widget = SQLFORM.widgets.string.widget
    
    s3["dataTable_sDom"] = 'ripl<"dataTable_table"t>p'
    
    s3.formats = Storage(xls= None, xml = None)
    
    attr["rheader"] = None
    
    return attr

settings.ui.customize_project_project = customize_project_project

from s3 import s3forms
settings.ui.crud_form_project_project = s3forms.S3SQLCustomForm(
        "name",
        "code",
        "status_id",
        "start_date",
        "end_date",
        "drrpp.duration",
        s3forms.S3SQLInlineComponent(
            "location",
            label=T("Countries"),
            fields=["location_id"],
        ),
        "multi_hazard_id",
        "multi_theme_id",
        "objectives",
        "drrpp.activities",
        # Outputs
        s3forms.S3SQLInlineComponent(
            "output",
            label=T("Outputs"),
            #comment = "Bob",
            fields=["output", "status"],
        ),
        "hfa",
        "drrpp.rfa",
        "organisation_id",
        # Partner Org
        s3forms.S3SQLInlineComponent(
            "organisation",
            name = "partner",
            label=T("Partner Organizations"),
            fields=["organisation_id",
                    # Explicit label as otherwise label from filter comes in!
                    #(T("Comments"), "comments"),
                    "comments",
                    ],
            filterby = dict(field = "role",
                            options = "2"
                            )
        ),
        # Donor
        s3forms.S3SQLInlineComponent(
            "organisation",
            name = "donor",
            label=T("Donor(s)"),
            fields=["organisation_id", "amount", "currency"],
            filterby = dict(field = "role",
                            options = "3"
                            )
        ),
        "budget",
        "currency",
        "drrpp.focal_person",
        "drrpp.organisation_id",
        "drrpp.email",
        # Files - Inline Forms don't support Files
        s3forms.S3SQLInlineComponent(
            "document",
            name = "file",
            label=T("Files"),
            fields=["file", "comments"],
            filterby = dict(field = "file",
                            options = "",
                            invert = True,
                            )
        ),
        # Links
        s3forms.S3SQLInlineComponent(
            "document",
            name = "url",
            label=T("Links"),
            fields=["url", "comments"],
            filterby = dict(field = "url",
                            options = None,
                            invert = True,
                            )
        ),
        "drrpp.parent_project",
        "comments",
        
    )

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
