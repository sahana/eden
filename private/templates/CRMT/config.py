# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current, IS_NULL_OR
from gluon.html import *
#from gluon.sqlhtml import formstyle_bootstrap
from gluon.storage import Storage

from s3.s3fields import S3Represent
from s3.s3filter import S3OptionsFilter
from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineComponentCheckbox
from s3.s3validators import IS_ADD_PERSON_WIDGET2, IS_LOCATION_SELECTOR2, IS_ONE_OF
from s3.s3widgets import S3AddPersonWidget2, S3LocationSelectorWidget2

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
settings.security.policy = 5 # Tables
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

# Uncomment to Hide the Toolbar from the main Map
settings.gis.toolbar = False
# Hide unnecessary Toolbar items
settings.gis.nav_controls = False
# Mouse Position: 'normal', 'mgrs' or None
settings.gis.mouse_position = None
# Uncomment to hide the permalink control
settings.gis.permalink = False
# Uncomment to rename Overlays in Layer Tree
settings.gis.label_overlays = "Community Data"

# Set Map to fill the container
settings.gis.map_width = 1170

# Don't simplify Polygons as much to retain their original shape
settings.gis.simplify_tolerance = 0.0001

# -----------------------------------------------------------------------------
# Finance settings
settings.fin.currencies = {
    "USD" : T("United States Dollars"),
}

# Disabled until ready for prime-time
settings.search.save_widget = False

# -----------------------------------------------------------------------------
# Menu
current.response.menu = [
    {"name": T("Locations"),
     "url": URL(c="org", f="facility"),
     "icon": "icon-home"
     },
    {"name": T("Residents"),
     "url": URL(c="stats", f="resident"),
     "icon": "icon-group"
     },
    {"name": T("Incidents"),
     "url": URL(c="event", f="incident_report"),
     "icon": "icon-warning-sign"
     },
    {"name": T("Risks"),
     "url": URL(c="vulnerability", f="risk"),
     "icon": "icon-bolt"
     },
    {"name": T("Activities"),
     "url": URL(c="project", f="activity"),
     "icon": "icon-star-empty"
     },
    #{"name": T("Organizations"),
    # "url": URL(c="org", f="organisation"),
    # "icon": "icon-sitemap"
    # },
    {"name": T("Trained People"),
     "url": URL(c="stats", f="trained"),
     "icon": "icon-user"
     },
    {"name": T("Evacuation Routes"),
     "url": URL(c="vulnerability", f="evac_route"),
     "icon": "icon-road"
     },
    ]

# -----------------------------------------------------------------------------
# Summary Pages
settings.ui.summary = [{"common": True,
                        "name": "cms",
                        "widgets": [{"method": "cms"}]
                        },
                       {"name": "map",
                        "label": "Map",
                        "widgets": [{"method": "map"}]
                        },
                       {"name": "table",
                        "label": "Table",
                        "widgets": [{"method": "datatable"}]
                        },
                       ]

# -----------------------------------------------------------------------------
def filter_formstyle(row_id, label, widget, comment, hidden=False):
        return DIV(label, widget, comment, 
                   _id=row_id,
                   _class="horiz_filter_form")

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
settings.hrm.teams = False

# -----------------------------------------------------------------------------
# Activities
# -----------------------------------------------------------------------------
def customize_project_activity(**attr):
    """
        Customize project_project controller
    """

    s3db = current.s3db
    tablename = "project_activity"
    table = s3db[tablename]
    table.location_id.label = "" # Gets replaced by widget
    table.location_id.requires = IS_LOCATION_SELECTOR2(levels=["L3"])
    table.location_id.widget = S3LocationSelectorWidget2(levels=["L3"],
                                                         hide_lx=False,
                                                         reverse_lx=True,
                                                         show_address=True,
                                                         show_postcode=True,
                                                         )

    # Remove rheader
    attr["rheader"] = None

    list_fields = ["date",
                   "name",
                   "activity_type_id",
                   "activity_group$group_id",
                   "location_id",
                   "person_id",
                   "comments",
                   ]

    # Custom Crud Form
    s3db.project_activity_group.group_id.label = ""
    crud_form = S3SQLCustomForm(
        "date",
        "name",
        "activity_type_id",
        S3SQLInlineComponent(
            "activity_group",
            label = T("Coalition"),
            fields = ["group_id"],
            multiple = False,
        ),
        "location_id",
        "person_id",
        S3SQLInlineComponent(
            "activity_organisation",
            label = T("Participating Organizations"),
            fields = ["organisation_id"],
        ),
        "comments",
    ) 

    filter_widgets = [S3OptionsFilter("activity_group.group_id",
                                      label=T("Coalition"),
                                      represent="%(name)s",
                                      widget="multiselect",
                                      ),
                      S3OptionsFilter("activity_type_id",
                                      label=T("Activity Type"),
                                      represent="%(name)s",
                                      widget="multiselect",
                                      ),
                      ]

    s3db.configure(tablename,
                   list_fields = list_fields,
                   crud_form = crud_form,
                   filter_widgets = filter_widgets,
                   filter_formstyle = filter_formstyle,
                   )

    attr["hide_filter"] = False

    return attr

settings.ui.customize_project_activity = customize_project_activity

# -----------------------------------------------------------------------------
# Incidents
# -----------------------------------------------------------------------------
def customize_event_incident_report(**attr):
    """
        Customize project_project controller
    """

    # Remove rheader
    attr["rheader"] = None

    s3db = current.s3db
    tablename = "event_incident_report"
    table = s3db[tablename]
    table.location_id.label = "" # Gets replaced by widget
    table.location_id.requires = IS_LOCATION_SELECTOR2(levels=["L3"])
    table.location_id.widget = S3LocationSelectorWidget2(levels=["L3"],
                                                         hide_lx=False,
                                                         reverse_lx=True,
                                                         show_address=True,
                                                         show_postcode=True,
                                                         )
    table.person_id.comment = None
    #table.person_id.requires = IS_ADD_PERSON_WIDGET2()
    #table.person_id.widget = S3AddPersonWidget2(controller="pr")
    table.person_id.widget = None
    
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
        msg_list_empty = T("No Incidents currently recorded")
        )

    # Custom Crud Form
    s3db.event_incident_report_group.group_id.label = ""
    crud_form = S3SQLCustomForm(
        "date",
        "name",
        "incident_type_id",
        S3SQLInlineComponent(
            "incident_report_group",
            label = T("Coalition"),
            fields = ["group_id"],
            multiple = False,
        ),
        "location_id",
        "person_id",
        "comments",
    ) 

    filter_widgets = [S3OptionsFilter("incident_report_group.group_id",
                                      label=T("Coalition"),
                                      represent="%(name)s",
                                      widget="multiselect",
                                      ),
                      S3OptionsFilter("incident_type_id",
                                      label=T("Incident Type"),
                                      represent="%(name)s",
                                      widget="multiselect",
                                      ),
                      ]

    s3db.configure(tablename,
                   crud_form = crud_form,
                   filter_widgets = filter_widgets,
                   filter_formstyle = filter_formstyle,
                   )

    attr["hide_filter"] = False

    return attr

settings.ui.customize_event_incident_report = customize_event_incident_report

# -----------------------------------------------------------------------------
# Organisations
# -----------------------------------------------------------------------------
def org_facility_types(row):
    """
        The Types of the Facility
        - requried since we can't have a component within an Inline Component
    """

    if hasattr(row, "org_facility"):
        row = row.org_facility
    try:
       site_id = row.site_id
    except:
        # not available
        return current.messages["NONE"]

    table = s3db.org_facility_type
    ltable = s3db.org_site_facility_type
    query = (ltable.site_id == site_id) & \
            (ltable.facility_type_id == table.id)
    rows = current.db(query).select(table.name)
    return "".join([r.name for r in rows])

# -----------------------------------------------------------------------------
def customize_org_organisation(**attr):
    """
        Customize org_organisation controller
    """

    s3 = current.response.s3

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        if r.interactive and \
           not r.component:
            s3db = current.s3db
            ftable = s3db.org_facility
            ftable.location_id.label = T("Address")
            ftable.location_id.widget = None
            # We don't have a widget capable of creating/editing Locations inline
            s3db.configure("org_facility",
                           editable=False,
                           insertable=False,
                           )
            # We can't include components in an Inline Component
            # Virtual fields also don't work
            #from gluon import Field
            #ftable.facility_types = Field.Lazy(org_facility_types)
            hrtable = s3db.hrm_human_resource
            hrtable.person_id.widget = None
            hrtable.site_id.label = T("Location")

            # Custom Crud Form
            crud_form = S3SQLCustomForm(
                "name",
                "logo",
                S3SQLInlineComponentCheckbox(
                    "group",
                    label = T("Coalitions"),
                    field = "group_id",
                    cols = 3,
                ),
                S3SQLInlineComponentCheckbox(
                    "sector",
                    label = T("Sectors"),
                    field = "sector_id",
                    cols = 4,
                ),
                S3SQLInlineComponentCheckbox(
                    "service",
                    label = T("Services"),
                    field = "service_id",
                    cols = 4,
                ),
                S3SQLInlineComponent(
                    "human_resource",
                    label = T("Organization's Contacts"),
                    fields = ["person_id",
                              "site_id",
                              "job_title_id",
                              #"email",
                              #"phone",
                              ],
                ),
                S3SQLInlineComponent(
                    "facility",
                    label = T("Organization's Locations"),
                    fields = ["name", 
                              # Only fields within the table are supported
                              #"facility_type.facility_type_id",
                              #"facility_types",
                              "location_id",
                              ],
                ),
                S3SQLInlineComponent(
                    "resource",
                    label = T("Organization's Resources"),
                    fields = ["parameter_id", 
                              "value",
                              "comments",
                              ],
                ),
                "comments",
            ) 

            filter_widgets = [S3OptionsFilter("group_membership.group_id",
                                              label=T("Coalition"),
                                              represent="%(name)s",
                                              widget="multiselect",
                                              ),
                              S3OptionsFilter("sector_organisation.sector_id",
                                              label=T("Sector"),
                                              represent="%(name)s",
                                              widget="multiselect",
                                              ),
                              S3OptionsFilter("service_organisation.service_id",
                                              label=T("Service"),
                                              represent="%(name)s",
                                              widget="multiselect",
                                              ),
                              ]

            s3.crud_strings.org_organisation.title_report = T("Organization Matrix")

            # Custom Report Fields
            report_fields = ["name",
                             (T("Sectors"), "sector_organisation.sector_id"),
                             (T("Services"), "service_organisation.service_id"),
                             ]

            report_options = Storage(rows = report_fields,
                                     cols = report_fields,
                                     fact = report_fields,
                                     defaults = Storage(rows = "service_organisation.service_id",
                                                        cols = "sector_organisation.sector_id",
                                                        fact = "count(name)",
                                                        totals = True
                                                        )
                                     )

            s3db.configure("org_organisation",
                           crud_form = crud_form,
                           filter_widgets = filter_widgets,
                           filter_formstyle = filter_formstyle,
                           report_options = report_options,
                           )

        return True
    s3.prep = custom_prep

    # Remove rheader
    attr["rheader"] = None

    attr["hide_filter"] = False
    return attr

settings.ui.customize_org_organisation = customize_org_organisation

# -----------------------------------------------------------------------------
# Coalitions (org_group)
# -----------------------------------------------------------------------------
def customize_org_group(**attr):
    """
        Customize org_group controller
    """

    tablename = "org_group"
    # CRUD Strings
    current.response.s3.crud_strings[tablename] = Storage(
        title_create = T("Add Coalition"),
        title_display = T("Coalition Details"),
        title_list = T("Coalitions"),
        title_update = T("Edit Coalition"),
        title_search = T("Search Coalitions"),
        subtitle_create = T("Add New Coalition"),
        label_list_button = T("List Coalitions"),
        label_create_button = T("Add Coalition"),
        label_delete_button = T("Remove Coalition"),
        msg_record_created = T("Coalition added"),
        msg_record_modified = T("Coalition updated"),
        msg_record_deleted = T("Coalition removed"),
        msg_list_empty = T("No Coalitions currently recorded"))

    return attr

settings.ui.customize_org_group = customize_org_group

#-----------------------------------------------------------------------------
# Location (org_facility)
#-----------------------------------------------------------------------------
def customize_org_facility(**attr):
    """
        Customize org_facility controller
    """

    s3 = current.response.s3

    tablename = "org_facility"

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)

        s3db = current.s3db
        if r.interactive:
            field = s3db.org_facility.location_id
            field.label = "" # Gets replaced by widget
            field.requires = IS_LOCATION_SELECTOR2(levels=["L3"])
            field.widget = S3LocationSelectorWidget2(levels=["L3"],
                                                     hide_lx=False,
                                                     reverse_lx=True,
                                                     show_address=True,
                                                     show_postcode=True,
                                                     )

            s3db.hrm_human_resource.person_id.widget = None
            
            s3.crud_strings[tablename] = Storage(
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

            # Custom Crud Form
            s3db.org_site_org_group.group_id.label = ""
            crud_form = S3SQLCustomForm(
                "name",
                S3SQLInlineComponentCheckbox(
                    "facility_type",
                    label = T("Location Type"),
                    field = "facility_type_id",
                    cols = 3,
                ),
                "organisation_id",
                S3SQLInlineComponent(
                    "site_org_group",
                    label = T("Coalition"),
                    fields = ["group_id"],
                    multiple = False,
                ),
                "location_id",
                S3SQLInlineComponent(
                    "human_resource",
                    label = T("Location's Contacts"),
                    fields = ["person_id",
                              "job_title_id",
                              #"email",
                              #"phone",
                              ],
                ),
                "comments",
            ) 

            filter_widgets = [S3OptionsFilter("site_org_group.group_id",
                                              label=T("Coalition"),
                                              represent="%(name)s",
                                              widget="multiselect",
                                              ),
                              S3OptionsFilter("site_facility_type.facility_type_id",
                                              label=T("Location Type"),
                                              represent="%(name)s",
                                              widget="multiselect",
                                              ),
                              S3OptionsFilter("organisation_id",
                                              label=T("Organization"),
                                              represent="%(name)s",
                                              widget="multiselect",
                                              ),
                              ]

            s3db.configure(tablename,
                           crud_form = crud_form,
                           filter_widgets = filter_widgets,
                           filter_formstyle = filter_formstyle,
                           )

            if r.method == "summary":
                # Hide Open & Delete dataTable action buttons
                s3db.configure(tablename,
                               editable = False,
                               deletable = False,
                               )

        elif r.representation == "plain" and \
             r.method != "search":
            # Map Popups
            table = s3db.org_facility
            table.location_id.label = T("Address")
            table.organisation_id.comment = ""
            s3.crud_strings[tablename].title_display = "Location Details"
            s3db.configure(tablename,
                           popup_url="",
                           )
        return True
    s3.prep = custom_prep
    # Override Custom Map Popup in default PostP
    s3.postp = None

    attr["hide_filter"] = False

    # Remove rheader
    attr["rheader"] = None

    return attr

settings.ui.customize_org_facility = customize_org_facility

#-----------------------------------------------------------------------------
# Residents
#-----------------------------------------------------------------------------
def customize_stats_resident(**attr):
    """
        Customize stats_resident controller
    """

    s3db = current.s3db
    tablename = "stats_resident"
    table = s3db[tablename]
    # L3s only
    field = table.location_id
    field.requires = IS_ONE_OF(current.db, "gis_location.id",
                               S3Represent(lookup="gis_location"),
                               sort = True,
                               filterby = "level",
                               filter_opts = ["L3"]
                               )
    # Don't add new Locations here
    field.comment = None
    # Simple dropdown
    field.widget = None
    field.label = T("City")

    # Custom PreP
    s3 = current.response.s3
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)

        if r.method == "summary":
            # Hide Open & Delete dataTable action buttons
            s3db.configure(tablename,
                           editable = False,
                           deletable = False,
                           )
        return True
    s3.prep = custom_prep

    # Custom Crud Form
    current.db.stats_resident_group.group_id.label = ""
    crud_form = S3SQLCustomForm(
        "name",
        "parameter_id",
        "value",
        S3SQLInlineComponent(
            "resident_group",
            label = T("Coalition"),
            fields = ["group_id"],
            multiple = False,
        ),
        "location_id",
        "person_id",
        "comments",
    )

    filter_widgets = [S3OptionsFilter("resident_group.group_id",
                                      label=T("Coalition"),
                                      represent="%(name)s",
                                      widget="multiselect",
                                      ),
                      S3OptionsFilter("parameter_id",
                                      label=T("Resident Type"),
                                      represent="%(name)s",
                                      widget="multiselect",
                                      ),
                      ]

    s3db.configure(tablename,
                   crud_form = crud_form,
                   filter_widgets = filter_widgets,
                   filter_formstyle = filter_formstyle,
                   )

    attr["hide_filter"] = False

    return attr

settings.ui.customize_stats_resident = customize_stats_resident

#-----------------------------------------------------------------------------
# Trained People
#-----------------------------------------------------------------------------
def customize_stats_trained(**attr):
    """
        Customize stats_trained controller
    """

    s3db = current.s3db
    tablename = "stats_trained"
    table = s3db[tablename]
    table.location_id.label = "" # Gets replaced by widget
    table.location_id.requires = IS_LOCATION_SELECTOR2(levels=["L3"])
    table.location_id.widget = S3LocationSelectorWidget2(levels=["L3"],
                                                         hide_lx=False,
                                                         reverse_lx=True,
                                                         show_address=True,
                                                         show_postcode=True,
                                                         )

    # Custom PreP
    s3 = current.response.s3
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)

        if r.method == "summary":
            # Hide Open & Delete dataTable action buttons
            s3db.configure(tablename,
                           editable = False,
                           deletable = False,
                           )
        return True
    s3.prep = custom_prep

    # Custom Crud Form
    current.db.stats_trained_group.group_id.label = ""
    crud_form = S3SQLCustomForm(
        "name",
        "parameter_id",
        "value",
        S3SQLInlineComponent(
            "trained_group",
            label = T("Coalition"),
            fields = ["group_id"],
            multiple = False,
        ),
        "organisation_id",
        "location_id",
        "person_id",
        "comments",
    )

    filter_widgets = [S3OptionsFilter("trained_group.group_id",
                                      label=T("Coalition"),
                                      represent="%(name)s",
                                      widget="multiselect",
                                      ),
                      S3OptionsFilter("parameter_id",
                                      label=T("Trained Type"),
                                      represent="%(name)s",
                                      widget="multiselect",
                                      ),
                      ]

    s3db.configure(tablename,
                   crud_form = crud_form,
                   filter_widgets = filter_widgets,
                   filter_formstyle = filter_formstyle,
                   )

    attr["hide_filter"] = False

    return attr

settings.ui.customize_stats_trained = customize_stats_trained

#-----------------------------------------------------------------------------
# Evacuation Routes
#-----------------------------------------------------------------------------
def customize_vulnerability_evac_route(**attr):
    """
        Customize vulnerability_evac_route controller
    """

    s3db = current.s3db
    tablename = "vulnerability_evac_route"
    table = s3db[tablename]
    table.location_id.label = "" # Gets replaced by widget
    table.location_id.requires = IS_LOCATION_SELECTOR2(levels=["L3"])
    table.location_id.widget = S3LocationSelectorWidget2(levels=["L3"],
                                                         polygons=True,
                                                         )

    # Custom PreP
    s3 = current.response.s3
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)

        if r.method == "summary":
            # Hide Open & Delete dataTable action buttons
            s3db.configure(tablename,
                           editable = False,
                           deletable = False,
                           )
        return True
    s3.prep = custom_prep

    # Custom Crud Form
    current.db.vulnerability_evac_route_group.group_id.label = ""
    crud_form = S3SQLCustomForm(
        "name",
        "hazard_id",
        S3SQLInlineComponent(
            "evac_route_group",
            label = T("Coalition"),
            fields = ["group_id"],
            multiple = False,
        ),
        "location_id",
        "comments",
    )

    filter_widgets = [S3OptionsFilter("evac_route_group.group_id",
                                      label=T("Coalition"),
                                      represent="%(name)s",
                                      widget="multiselect",
                                      ),
                      S3OptionsFilter("hazard_id",
                                      label=T("Hazard Type"),
                                      represent="%(name)s",
                                      widget="multiselect",
                                      ),
                      ]

    s3db.configure(tablename,
                   crud_form = crud_form,
                   filter_widgets = filter_widgets,
                   filter_formstyle = filter_formstyle,
                   )

    attr["hide_filter"] = False

    return attr

settings.ui.customize_vulnerability_evac_route = customize_vulnerability_evac_route

#-----------------------------------------------------------------------------
# Risks
#-----------------------------------------------------------------------------
def customize_vulnerability_risk(**attr):
    """
        Customize vulnerability_risk controller
    """

    s3db = current.s3db
    tablename = "vulnerability_risk"
    table = s3db[tablename]
    table.location_id.label = "" # Gets replaced by widget
    table.location_id.requires = IS_LOCATION_SELECTOR2(levels=["L3"])
    table.location_id.widget = S3LocationSelectorWidget2(levels=["L3"],
                                                         hide_lx=False,
                                                         reverse_lx=True,
                                                         polygons=True,
                                                         #show_address=True,
                                                         #show_postcode=True,
                                                         )

    # Custom PreP
    s3 = current.response.s3
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)

        if r.method == "summary":
            # Hide Open & Delete dataTable action buttons
            s3db.configure(tablename,
                           editable = False,
                           deletable = False,
                           )
        return True
    s3.prep = custom_prep

    # Custom Crud Form
    current.db.vulnerability_risk_group.group_id.label = ""
    crud_form = S3SQLCustomForm(
        "name",
        "hazard_id",
        S3SQLInlineComponent(
            "risk_group",
            label = T("Coalition"),
            fields = ["group_id"],
            multiple = False,
        ),
        "location_id",
        "comments",
    )

    filter_widgets = [S3OptionsFilter("risk_group.group_id",
                                      label=T("Coalition"),
                                      represent="%(name)s",
                                      widget="multiselect",
                                      ),
                      S3OptionsFilter("hazard_id",
                                      label=T("Hazard Type"),
                                      represent="%(name)s",
                                      widget="multiselect",
                                      ),
                      ]

    s3db.configure(tablename,
                   crud_form = crud_form,
                   filter_widgets = filter_widgets,
                   filter_formstyle = filter_formstyle,
                   )

    attr["hide_filter"] = False

    return attr

settings.ui.customize_vulnerability_risk = customize_vulnerability_risk

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
    ("cms", Storage(
        name_nice = T("Content Management"),
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
])
