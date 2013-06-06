# -*- coding: utf-8 -*-

from gluon import current, IS_NULL_OR
from gluon.html import *
from gluon.storage import Storage

from gluon.contrib.simplejson.ordered_dict import OrderedDict

from s3.s3fields import S3Represent
from s3.s3filter import S3OptionsFilter
from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineComponentCheckbox
from s3.s3validators import IS_ONE_OF
from s3.s3widgets import S3LocationAutocompleteWidget

T = current.T
settings = current.deployment_settings

"""
    Template settings for Community Resilience Mapping Tool
"""

# =============================================================================
# US Settings
# -----------------------------------------------------------------------------
# Uncomment to Hide the language toolbar
settings.L10n.display_toolbar = False
# Default timezone for users
settings.L10n.utc_offset = "UTC -0800"
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

# =============================================================================
# System Settings
# -----------------------------------------------------------------------------
# Authorization Settings
settings.auth.registration_requires_approval = True
settings.auth.registration_requires_verification = True
settings.auth.registration_requests_organisation = True
settings.auth.registration_organisation_required = True
settings.auth.registration_requests_site = False

settings.auth.registration_link_user_to = {"staff": T("Staff")}

settings.auth.record_approval = False

# -----------------------------------------------------------------------------
# Security Policy
settings.security.policy = 3 # Controllers
settings.security.map = True

# Owner Entity
settings.auth.person_realm_human_resource_site_then_org = False

# -----------------------------------------------------------------------------
# Pre-Populate
settings.base.prepopulate = ["CRMT"]

settings.base.system_name = T("Community Resilience Mapping Tool")
settings.base.system_name_short = T("CRMT")

# -----------------------------------------------------------------------------
# Theme (folder to use for views/layout.html)
settings.base.theme = "CRMT"
settings.ui.formstyle_row = "bootstrap"
settings.ui.formstyle = "bootstrap"
#settings.gis.map_height = 600
#settings.gis.map_width = 854

# -----------------------------------------------------------------------------
# L10n (Localization) settings
settings.L10n.languages = OrderedDict([
    ("en", "English"),
])
# Default Language
settings.L10n.default_language = "en"
# Number formats (defaults to ISO 31-0)
# Decimal separator for numbers (defaults to ,)
settings.L10n.decimal_separator = "."
# Thousands separator for numbers (defaults to space)
settings.L10n.thousands_separator = ","

# Restrict the Location Selector to just certain countries
# NB This can also be over-ridden for specific contexts later
# e.g. Activities filtered to those of parent Project
settings.gis.countries = ["US"]

# -----------------------------------------------------------------------------
# Finance settings
settings.fin.currencies = {
    "USD" : T("United States Dollars"),
}

# -----------------------------------------------------------------------------
# Save Search Widget
settings.save_search.widget = False

# -----------------------------------------------------------------------------
# Summary Pages
settings.ui.summary = [{"name": "map",
                        "label": "Map",
                        "widgets": [{"method": "map"}]
                        },
                       {"name": "table",
                        "label": "Table",
                        "widgets": [{"method": "datatable"}]
                        },
                       ]

# =============================================================================
# View Settings

current.response.menu = [{"name": T("Residents"),
                 "url": URL(c="stats", f="resident", args="summary"),
                 "icon": "icon-group"
                 },
                {"name": T("Incidents"),
                 "url": URL(c="event", f="incident_report", args="summary"),
                 "icon": "icon-warning-sign"
                 },
                {"name": T("Risks"),
                 "url": URL(c="vulnerability", f="risk", args="summary"),
                 "icon": "icon-bolt"
                 },
                {"name": T("Activities"),
                 "url": URL(c="project", f="activity", args="summary"),
                 "icon": "icon-star-empty"
                 },
                {"name": T("Organizations"),
                 "url": URL(c="org", f="organisation", args="summary"),
                 "icon": "icon-sitemap"
                 },
                {"name": T("Trained People"),
                 "url": URL(c="stats", f="trained", args="summary"),
                 "icon": "icon-user"
                 },
                {"name": T("Locations"),
                 "url": URL(c="org", f="facility", args="summary"),
                 "icon": "icon-home"
                 },
                {"name": T("Evacuation Routes"),
                 "url": URL(c="vulnerability", f="evac_route", args="summary"),
                 "icon": "icon-road"
                 },
                 ]

# =============================================================================
# Module Settings

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
# Uncomment to disable the use of HR Skills
settings.hrm.use_skills = False
# Uncomment to disable the use of HR Teams
settings.hrm.use_teams = False

# -----------------------------------------------------------------------------
# Activity
def customize_project_activity(**attr):
    """
        Customize project_project controller
    """
    
    s3db = current.s3db
    
    tablename = "project_activity"
    table = s3db[tablename]

    # Remove rheader
    attr["rheader"] = None

    # Custom Crud Form
    crud_form = S3SQLCustomForm(
        "date",
        "name",
        "activity_type_id",
        "location_id",
        "person_id",
        S3SQLInlineComponent(
            "activity_organisation",
            label = T("Participating Organizations"),
            #comment = "Bob",
            fields = ["organisation_id"],
        ),
        "comments",
    ) 

    s3db.configure(tablename,
                   crud_form = crud_form)

    return attr

settings.ui.customize_project_activity = customize_project_activity

# -----------------------------------------------------------------------------
# Organisation
def customize_org_organisation(**attr):
    """
        Customize org_organisation controller
    """
    
    s3db = current.s3db

    # Remove rheader
    attr["rheader"] = None

    tablename = "org_organisation"
    table = s3db[tablename]

    s3db.org_facility.location_id.widget = S3LocationAutocompleteWidget()
    s3db.org_facility.location_id.label = T("Address")
    s3db.hrm_human_resource.person_id.widget = None
    s3db.hrm_human_resource.site_id.label = T("Location")

    # Custom Crud Form
    crud_form = S3SQLCustomForm(
        "name",
        "logo",
        "multi_sector_id",
        S3SQLInlineComponentCheckbox(
            "service",
            label = T("Services"),
            field = "service_id",
            cols = 4,
        ),
        S3SQLInlineComponent(
            "human_resource",
            label = T("Organization's Contacts"),
            #comment = "Bob",
            fields = ["person_id",
                      "site_id",
                      "hrm_job_title_id",
                      #"email",
                      #"phone",
                      ],
        ),
        S3SQLInlineComponent(
            "facility",
            label = T("Organization's Locations"),
            #comment = "Bob",
            fields = ["name", 
                      "facility_type_id",
                      "location_id" ],
        ),
        S3SQLInlineComponent(
            "resource",
            label = T("Organization's Resources"),
            #comment = "Bob",
            fields = ["parameter_id", 
                      "value",
                      "comments" ],
        ),
        "comments",
    ) 

    filter_widgets = [S3OptionsFilter("multi_sector_id",
                                      label=T("Sector"),
                                      represent="%(name)s",
                                      widget="multiselect",
                                      ),
                      #S3OptionsFilter("service.service_type_id",
                      #                label=T("Service Type"),
                      #                represent="%(name)s",
                      #                widget="multiselect",
                      #                ),
                      ]

    s3db.configure(tablename,
                   crud_form = crud_form,
                   filter_widgets = filter_widgets,
                   )

    return attr

settings.ui.customize_org_organisation = customize_org_organisation

#-----------------------------------------------------------------------------
# Location (org_facility)
#-----------------------------------------------------------------------------

def customize_org_facility(**attr):
    """
        Customize org_facility controller
    """
    
    s3db = current.s3db
    db = current.db

    # Remove rheader
    attr["rheader"] = None

    tablename = "org_facility"
    table = s3db[tablename]
    
    table.facility_type_id.requires = IS_NULL_OR(IS_ONE_OF(db, "org_facility_type.id",
                                                          S3Represent(lookup=tablename),
                                                          sort=True))
    table.facility_type_id.widget = None

    s3db.hrm_human_resource.person_id.widget = None

    s3db.org_facility.location_id.label = T("Address")

    # Custom Crud Form
    crud_form = S3SQLCustomForm(
        "name",
        "facility_type_id",
        "organisation_id",
        "location_id",
        S3SQLInlineComponent(
            "human_resource",
            label = T("Location's Contacts"),
            #comment = "Bob",
            fields = ["person_id",
                      "hrm_job_title_id",
                      #"email",
                      #"phone",
                      ],
        ),
        "comments",
    ) 

    s3db.configure(tablename,
                   crud_form = crud_form)

    current.response.s3.crud_strings[tablename] = Storage(
                title_create = T("Add Location"),
                title_display = T("Location Details"),
                title_list = T("Locations"),
                title_update = T("Edit Location"),
                title_search = T("Search Locations"),
                subtitle_create = T("Add New Location"),
                label_list_button = T("List Locations"),
                label_create_button = T("Add Location"),
                label_delete_button = T("Remove Location"),
                msg_record_created = T("Location added"),
                msg_record_modified = T("Location updated"),
                msg_record_deleted = T("Location removed"),
                msg_list_empty = T("No Locations currently recorded"))

    return attr

settings.ui.customize_org_facility = customize_org_facility

# -----------------------------------------------------------------------------
# Incidents
# -----------------------------------------------------------------------------
def customize_event_incident_report(**attr):
    """
        Customize project_project controller
    """
    
    s3db = current.s3db


    # Remove rheader
    attr["rheader"] = None

    tablename = "event_incident_report"
    table = s3db[tablename]
    table.location_id.label=T("Address")
    
    current.response.s3.crud_strings[tablename] = Storage(
                title_create = T("Add Incident"),
                title_display = T("Incident Details"),
                title_list = T("Incidents"),
                title_update = T("Edit Incident"),
                title_search = T("Search Incidents"),
                subtitle_create = T("Add New Incident"),
                label_list_button = T("List Incidents"),
                label_create_button = T("Add Incident"),
                label_delete_button = T("Remove Incident"),
                msg_record_created = T("Incident added"),
                msg_record_modified = T("Incident updated"),
                msg_record_deleted = T("Incident removed"),
                msg_list_empty = T("No Incidents currently recorded"))

    return attr

settings.ui.customize_event_incident_report = customize_event_incident_report
# =============================================================================
# Template Modules
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
            module_type = 1,     # 1st item in the menu
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
            module_type = None
        )),
    # All modules below here should be possible to disable safely
    ("hrm", Storage(
            name_nice = T("Staff"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = None,
        )),
    #("cms", Storage(
    #        name_nice = T("Content Management"),
    #        restricted = True,
    #        module_type = None,
    #    )),
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
    ("event", Storage(
            name_nice = T("Events"),
            #description = "Events",
            restricted = True,
            module_type = None
        )),
    ("project", Storage(
            name_nice = T("Projects"),
            restricted = True,
            module_type = None
        )),
    ("stats", Storage(
            name_nice = T("Statistics"),
            restricted = True,
            module_type = None
        )),
    ("vulnerability", Storage(
            name_nice = T("Vulnerability"),
            restricted = True,
            module_type = None
        )),
    #("asset", Storage(
    #        name_nice = T("Assets"),
    #        restricted = True,
    #        module_type = None
    #    )),
    #("supply", Storage(
    #        name_nice = "Supply",
    #        restricted = True,
    #        module_type = None
    #    )),
])
