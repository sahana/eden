# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from datetime import timedelta

from gluon import current
from gluon.html import *
from gluon.storage import Storage

from s3.s3utils import s3_avatar_represent

T = current.T
s3 = current.response.s3
settings = current.deployment_settings

"""
    Puget Sound Common Maritime Operating Picture (MCOP) 

    All settings which are to configure a specific template are located here

    Deployers should ideally not need to edit any other files outside of their template folder
"""

# =============================================================================
# System Settings
# -----------------------------------------------------------------------------
# Authorization Settings
# Users can self-register
#settings.security.self_registration = False
# Users need to verify their email
settings.auth.registration_requires_verification = True
# Users need to be approved
settings.auth.registration_requires_approval = True
#settings.auth.registration_requests_organisation = True
#settings.auth.registration_organisation_required = True

# Approval emails get sent to all admins
settings.mail.approver = "ADMIN"

settings.auth.registration_link_user_to = {"staff": T("Staff")}
settings.auth.registration_link_user_to_default = ["staff"]
settings.auth.registration_roles = {"organisation_id": ["USER"],
                                    }

settings.auth.show_utc_offset = False
settings.auth.show_link = False

# -----------------------------------------------------------------------------
# Security Policy
settings.security.policy = 5 # Apply Controller, Function and Table ACLs
settings.security.map = True

# -----------------------------------------------------------------------------
# Pre-Populate
settings.base.prepopulate = ["MCOP"]

settings.base.system_name = T("Sahana: Puget Sound Common Maritime Operating Picture (MCOP)")
settings.base.system_name_short = T("Sahana")

# -----------------------------------------------------------------------------
# Theme (folder to use for views/layout.html)
settings.base.theme = "MCOP"
settings.ui.formstyle_row = "bootstrap"
settings.ui.formstyle = "bootstrap"
settings.ui.filter_formstyle = "bootstrap"
settings.ui.hide_report_options = False
#settings.gis.map_height = 600
#settings.gis.map_width = 854

# -----------------------------------------------------------------------------
# L10n (Localization) settings
settings.L10n.languages = OrderedDict([
    ("en", "English"),
])
# Default Language
settings.L10n.default_language = "en"
# Default timezone for users
settings.L10n.utc_offset = "UTC -0800"
# Unsortable 'pretty' date format
settings.L10n.date_format = "%b %d %Y"
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

settings.msg.require_international_phone_numbers = False
# PDF to Letter
settings.base.paper_size = T("Letter")

# Uncomment this to Translate CMS Series Names
# - we want this on when running s3translate but off in normal usage as we use the English names to lookup icons in render_posts
#settings.L10n.translate_cms_series = True
# Uncomment this to Translate Location Names
#settings.L10n.translate_gis_location = True

# Restrict the Location Selector to just certain countries
settings.gis.countries = ["US"]
# Levels for the LocationSelector
levels = ("L1", "L2", "L3")

# Uncomment to pass Addresses imported from CSV to a Geocoder to try and automate Lat/Lon
#settings.gis.geocode_imported_addresses = "google"

# Until we add support to LocationSelector2 to set dropdowns from LatLons
#settings.gis.check_within_parent_boundaries = False
# Uncomment to hide Layer Properties tool
#settings.gis.layer_properties = False
# Hide unnecessary Toolbar items
settings.gis.nav_controls = False
# Uncomment to display the Map Legend as a floating DIV
settings.gis.legend = "float"

# -----------------------------------------------------------------------------
# Enable this for a UN-style deployment
#settings.ui.cluster = True
# Enable this to use the label 'Camp' instead of 'Shelter'
#settings.ui.camp = True

# -----------------------------------------------------------------------------
# Uncomment to restrict the export formats available
#settings.ui.export_formats = ["xls"]

settings.ui.update_label = "Edit"
# -----------------------------------------------------------------------------
# Disable rheaders
def customise_no_rheader_controller(**attr):
    # Remove rheader
    attr["rheader"] = None
    return attr

settings.customise_cms_post_controller = customise_no_rheader_controller
settings.customise_project_task_controller = customise_no_rheader_controller
settings.customise_org_facility_controller = customise_no_rheader_controller
settings.customise_org_organisation_controller = customise_no_rheader_controller
settings.customise_org_resource_controller = customise_no_rheader_controller

# -----------------------------------------------------------------------------
# Summary Pages
settings.ui.summary = [#{"common": True,
                       # "name": "cms",
                       # "widgets": [{"method": "cms"}]
                       # },
                       # Embedded Location Selector Widgets are conflicting with Summary Map
                       #{"common": True,
                       # "name": "add",
                       # "widgets": [{"method": "create"}],
                       # },
                       {"name": "table",
                        "label": "Table",
                        "widgets": [{"method": "datatable"}]
                        },
                       {"name": "map",
                        "label": "Map",
                        "widgets": [{"method": "map", "ajax_init": True}],
                        },
                       {"name": "charts",
                        "label": "Reports",
                        "widgets": [{"method": "report", "ajax_init": True}]
                        },
                       ]

settings.search.filter_manager = False
# =============================================================================
# Menu
current.response.menu = [
    {"name": T("Events"),
     "c":"event", 
     "f":"event",
     "icon": "incident"
     },
    {"name": T("Tasks"),
     "c":"project", 
     "f":"task",
     "icon": "check"
     },
    {"name": T("Resources"),
     "c":"org", 
     "f":"resource",
     "icon": "wrench"
     },
    {"name": T("News"),
     "c":"cms", 
     "f":"post",
     "icon": "news"
     },
    {"name": T("Map"),
     "c":"gis", 
     "f":"index",
     "icon": "map"
     },
#    {"name": T("Projects"),
#     "c":"project", 
#     "f":"activity",
#     "icon": "tasks"
#     },
    {"name": T("Contact Directory"),
     "c":"pr", 
     "f":"person",
     "icon": "group"
     },
    {"name": T("Stakeholders"),
     "c":"org", 
     "f":"organisation",
     "icon": "sitemap"
     },
    {"name": T("Facilities"),
     "c":"org", 
     "f":"facility",
     "icon": "building"
     },
    ]

for item in current.response.menu:
    item["url"] = URL(item["c"], 
                      item["f"], 
                      args = ["summary" if item["f"] not in ["organisation","post"]
                                        else "datalist"])

# =============================================================================
# Customise Resources

# -----------------------------------------------------------------------------
def customise_org_organisation_resource(r, tablename):
    """
        Customise org_organisation resource
        - List Fields
        - CRUD Strings
        - Form
        - Filter
        Runs after controller customisation
        But runs before prep
    """
    # Load normal Model
    s3db = current.s3db
    table = s3db.org_organisation

    list_fields = ["id",
                   "name",
                   "logo",
                   "phone",
                   "website",
                   ]

    if r.interactive:
        # Labels
        table.comments.label = T("Description")

        s3.crud_strings["org_organisation"] = Storage(
            label_create = T("Create Stakeholder"),
            title_display = T("Stakeholder Details"),
            title_list = T("Stakeholders"),
            title_update = T("Edit Stakeholder"),
            label_list_button = T("List Stakeholders"),
            label_delete_button = T("Delete Stakeholder"),
            msg_record_created = T("Stakeholder added"),
            msg_record_modified = T("Stakeholder updated"),
            msg_record_deleted = T("Stakeholder deleted"),
            msg_list_empty = T("No Stakeholders currently registered"))

        from s3.s3forms import S3SQLCustomForm
        crud_form = S3SQLCustomForm("id",
                                    "name",
                                    "organisation_type_id",
                                    "logo",
                                    "phone",
                                    "website",
                                    "comments",
                                    )

        s3db.configure("org_organisation",
                       crud_form = crud_form,
                       )

        if r.method == "datalist":
            # Stakeholder selection page
            # 2-column datalist, 6 rows per page
            s3.dl_pagelength = 12
            s3.dl_rowsize = 3
    
            from s3.s3filter import S3TextFilter, S3OptionsFilter
            filter_widgets = [S3TextFilter(["name",
                                            "acronym",
                                            "website",
                                            "comments",
                                            ],
                                          label = T("Search")),
                              S3OptionsFilter("organisation_type_id",
                                              label = T("Type"),
                                              ),
                              ]

            s3db.configure("org_organisation",
                           filter_widgets = filter_widgets,
                           )

        if r.method == "profile":
            # Ensure the correct list_fields are set
            # @ToDo: Have profile method call these automatically
            customise_pr_person_resource(r, "pr_person")
            customise_event_incident_resource(r, "event_incident")
            # Customise tables used by widgets
            #customise_cms_post_fields()
            #customise_hrm_human_resource_fields()
            #customise_org_office_fields()
            s3db.org_customise_org_resource_fields("profile")

            from s3.s3resource import S3FieldSelector
            contacts_widget = dict(label = "Directory",
                                   label_create = "Create Contact",
                                   type = "datalist",
                                   tablename = "hrm_human_resource",
                                   context = "organisation",
                                   create_controller = "pr",
                                   create_function = "person",
                                   icon = "icon-contact",
                                   show_on_map = False, # Since they will show within Offices
                                   list_layout = render_contacts,
                                   )
            map_widget = dict(label = "Map",
                              type = "map",
                              context = "organisation",
                              icon = "icon-map",
                              height = 383,
                              width = 568,
                              )
            facilities_widget = dict(label = "Facilities",
                                     label_create = "Create Facility",
                                     type = "datalist",
                                     tablename = "org_facility",
                                     context = "organisation",
                                     icon = "icon-building",
                                     layer = "Facilities",
                                     # provided by Catalogue Layer
                                     #marker = "office",
                                     list_layout = render_facilities,
                                     )
            resources_widget = dict(label = "Resources",
                                    label_create = "Create Resource",
                                    type = "datalist",
                                    tablename = "org_resource",
                                    context = "organisation",
                                    icon = "icon-resource",
                                    show_on_map = False, # No Marker yet & only show at L1-level anyway
                                    list_layout = s3db.org_resource_list_layout,
                                    )
            projects_widget = dict(label = "Incidents",
                                   label_create = "Create Incident",
                                   type = "datalist",
                                   tablename = "event_incident",
                                   context = "organisation",
                                   icon = "icon-incident",
                                   show_on_map = False, # No Marker yet & only show at L1-level anyway
                                   list_layout = s3db.event_incident_list_layout,
                                   )
            #activities_widget = dict(label = "Activities",
            #                         label_create = "Create Activity",
            #                         type = "datalist",
            #                         tablename = "cms_post",
            #                         context = "organisation",
            #                         filter = S3FieldSelector("series_id$name") == "Activity",
            #                         icon = "icon-activity",
            #                         layer = "Activities",
                                     # provided by Catalogue Layer
                                     #marker = "activity",
            #                         list_layout = render_profile_posts,
            #                         )
            #reports_widget = dict(label = "Reports",
            #                      label_create = "Add New Report",
            #                      type = "datalist",
            #                      tablename = "cms_post",
            #                      context = "organisation",
            #                      filter = S3FieldSelector("series_id$name") == "Report",
            #                      icon = "icon-report",
            #                      layer = "Reports",
            #                      # provided by Catalogue Layer
            #                      #marker = "report",
            #                      list_layout = render_profile_posts,
            #                      )
            #assessments_widget = dict(label = "Assessments",
            #                          label_create = "Add New Assessment",
            #                          type = "datalist",
            #                          tablename = "cms_post",
            #                          context = "organisation",
            #                          filter = S3FieldSelector("series_id$name") == "Assessment",
            #                          icon = "icon-assessment",
            #                          layer = "Assessments",
                                      # provided by Catalogue Layer
                                      #marker = "assessment",
            #                          list_layout = render_profile_posts,
            #                          )
            record = r.record
            title = "%s : %s" % (s3.crud_strings["org_organisation"].title_list, record.name)
            if record.logo:
                logo = URL(c="default", f="download", args=[record.logo])
            else:
                logo = ""
            s3db.configure("org_organisation",
                           profile_title = title,
                           profile_header = DIV(A(IMG(_class="media-object",
                                                      _src=logo,
                                                      ),
                                                  _class="pull-left",
                                                  #_href=org_url,
                                                  ),
                                                H2(title),
                                                _class="profile_header",
                                                ),
                           profile_widgets = [contacts_widget,
                                              #map_widget,
                                              facilities_widget,
                                              resources_widget,
                                              projects_widget,
                                              #activities_widget,
                                              #reports_widget,
                                              #assessments_widget,
                                              ],
                           #profile_cols = 3
                           )

    # Return to List view after create/update/delete (unless done via Modal)
    url_next = URL(c="org", f="organisation", args="datalist")

    s3db.configure("org_organisation",
                   create_next = url_next,
                   delete_next = url_next,
                   # We want the Create form to be in a modal, not inline, for consistency
                   #listadd = False,
                   list_fields = list_fields,
                   update_next = url_next,
                   )

settings.customise_org_organisation_resource = customise_org_organisation_resource

# -----------------------------------------------------------------------------
def customise_org_resource_resource(r, tablename):
    """
        Customise org_resource resource
        - Fields
        - Filter
        Runs after controller customisation
        But runs before prep
    """

    s3 = current.response.s3
    s3db = current.s3db
    table = s3db.org_resource

    if r.interactive:
        location_field = table.location_id
        # Filter from a Profile page?
        # If so, then default the fields we know
        get_vars = current.request.get_vars
        location_id = get_vars.get("~.(location)", None)
        organisation_id = get_vars.get("~.(organisation)", None)
        if organisation_id:
            org_field = table.organisation_id
            org_field.default = organisation_id
            org_field.readable = org_field.writable = False
        if location_id:
            location_field.default = location_id
            # We still want to be able to specify a precise location
            #location_field.readable = location_field.writable = False    
        from s3.s3validators import IS_LOCATION_SELECTOR2
        from s3.s3widgets import S3LocationSelectorWidget2
        location_field.requires = IS_LOCATION_SELECTOR2(levels=levels)
        location_field.widget = S3LocationSelectorWidget2(levels=levels,
                                                          show_address=True,
                                                          show_map=True)

        # Don't add new Locations here
        location_field.comment = None

        s3db.org_customise_org_resource_fields(r.method)

        # Configure fields
        #table.site_id.readable = table.site_id.readable = False
        #location_field.label = T("District")

        from s3.s3filter import S3TextFilter, S3OptionsFilter
        filter_widgets = [S3TextFilter(["organisation_id$name",
                                        "location_id",
                                        "parameter_id$name",
                                        "comments",
                                        ],
                                      label = T("Search")),
                          S3OptionsFilter("parameter_id",
                                          label = T("Type"),
                                          ),
                          ]

        s3db.configure("org_resource",
                       filter_widgets=filter_widgets
                       )

        # Return to Sumamry view after create/update/delete (unless done via Modal)
        url_next = URL(c="org", f="resource", args="summary")

        s3db.configure("org_resource",
                       create_next = url_next,
                       delete_next = url_next,
                       # Don't include a Create form in 'More' popups
                       listadd = False if r.method=="datalist" else True,
                       update_next = url_next,
                       )

        # This is awful in Popups & inconsistent in dataTable view (People/Documents don't have this & it breaks the styling of the main Save button)
        #s3.cancel = URL(c="org", f="resource")

    return True

settings.customise_org_resource_resource = customise_org_resource_resource

# =============================================================================
def cms_post_age(row):
    """
        The age of the post
        - used for colour-coding markers of Alerts
    """

    if hasattr(row, "cms_post"):
        row = row.cms_post
    try:
        date = row.date
    except:
        # not available
        return current.messages["NONE"]

    now = current.request.utcnow
    age = now - date
    if age < timedelta(days=2):
        return 1
    elif age < timedelta(days=7):
        return 2
    else:
        return 3

# -----------------------------------------------------------------------------
def customise_cms_post_resource(r, tablename):
    """
        Customise cms_post resource
        - CRD Strings
        - Datatable
        - Fields
        - Form
        Runs after controller customisation
        But runs before prep
    """

    s3 = current.response.s3
    s3db = current.s3db
    table = s3db.cms_post

    s3.dl_pagelength = 12
    s3.dl_rowsize = 2

    from s3.s3resource import S3FieldSelector
    s3.filter = S3FieldSelector("series_id$name").belongs(["Alert"])

    s3.crud_strings["cms_post"] = Storage(
        label_create = T("Create Alert"),
        title_display = T("Alert Details"),
        title_list = T("Alerts"),
        title_update = T("Edit Alert"),
        label_list_button = T("List Alerts"),
        label_delete_button = T("Delete Alert"),
        msg_record_created = T("Alert added"),
        msg_record_modified = T("Alert updated"),
        msg_record_deleted = T("Alert deleted"),
        msg_list_empty = T("No Alerts currently registered"))

    # CRUD Form
    from s3.s3validators import IS_LOCATION_SELECTOR2
    from s3.s3widgets import S3LocationSelectorWidget2
    table.location_id.requires = IS_LOCATION_SELECTOR2(levels=levels)
    table.location_id.widget = S3LocationSelectorWidget2(levels=levels,
                                                         show_address=True,
                                                         show_map=True)
    # Don't add new Locations here
    table.location_id.comment = None

    table.series_id.readable = table.series_id.writable = True
    table.series_id.label = T("Type")

    table.body.label = T("Description")
    table.body.widget = None
    s3db.event_event_post.event_id.label = ""
    s3db.doc_document.file.label = ""
    from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent
    crud_form = S3SQLCustomForm(
        "date",
        #"series_id",
        "body",
        "location_id",
        S3SQLInlineComponent(
            "event_post",
            label = T("Event"),
            multiple = False,
            fields = ["event_id"],
            orderby = "event_id$name",
        ),
        S3SQLInlineComponent(
            "document",
            name = "file",
            label = T("Files"),
            fields = ["file",
                      #"comments",
                      ],
        ),
    )

    # Return to List view after create/update/delete
    # We now do all this in Popups
    url_next = URL(c="cms", f="post", args="datalist")

    s3db.configure("cms_post",
                   create_next = url_next,
                   crud_form = crud_form,
                   delete_next = url_next,
                   update_next = url_next,
                   )

    if r.representation == "geojson":
        # Add Virtual field to allow colour-coding by age
        from gluon.dal import Field
        table.age = Field.Method("age", cms_post_age)

settings.customise_cms_post_resource = customise_cms_post_resource

# -----------------------------------------------------------------------------
def customise_project_task_resource(r, tablename):
    """
        Customise org_resource resource
        - List Fields
        - Fields
        - Form
        - Filter Widgets
        - Report Options
        Runs after controller customisation
        But runs before prep
    """

    s3db = current.s3db
    table = s3db.project_task

    if r.tablename == "event_incident" and r.method == "profile":
        # Set list_fields for renderer (project_task_list_layout)
        s3db.configure("project_task",
                       list_fields = ["name",
                                      "description",
                                      "location_id",
                                      "date_due",
                                      "pe_id",
                                      #"event_task.incident_id",
                                      #"organisation_id$logo",
                                      "pe_id",
                                      "modified_by",
                                      ],
                       )
    else:
        list_fields = ["id",
                       "status",
                       "priority",
                       #(T("Incident"), "event_task.incident_id"),
                       "name",
                       (T("Location"), "location_id"),
                       "date_due",
                       ]
        s3db.configure("project_task",
                       list_fields = list_fields,
                       )

    # Custom Form
    table.name.label = T("Name")
    table.description.label = T("Description")
    #table.location_id.readable = table.location_id.writable = True
    from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent
    crud_form = S3SQLCustomForm("status",
                                "priority",
                                "name",
                                "description",
                                #"task_activity.activity_id",
                                #S3SQLInlineComponent("event_task",
                                #                     label = T("Incident"),
                                #                     fields = ["project_id"],
                                #                     multiple = False,
                                #                     ),
                                "pe_id",
                                "date_due",
                                "location_id",
                                )

    # Remove Project Filter
    filter_widgets = s3db.get_config("project_task", 
                                     "filter_widgets")
    filter_widgets.pop(2)

    # Report options
    report_fields = ["status",
                     "priority",
                     #"event_task.incident_id"
                     "pe_id",
                     "location_id",
                     ]

    report_options = Storage(rows = report_fields,
                             cols = report_fields,
                             fact = ["count(name)"],
                             defaults=Storage(rows = "status",
                                              cols = "priority",
                                              fact = "count(name)",
                                              totals = True,
                                              chart = "barchart:rows",
                                              )
                             )

    url_next = URL(c="project", f="task", args="summary")

    s3db.configure("project_task",
                   create_next = url_next,
                   crud_form = crud_form,
                   delete_next = url_next,
                   filter_widgets = filter_widgets,
                   #list_fields = list_fields,
                   report_options = report_options,
                   update_next = url_next,
                   )

settings.customise_project_task_resource = customise_project_task_resource

# -----------------------------------------------------------------------------
def customise_event_incident_controller(**attr):

    s3 = current.response.s3

    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        if r.interactive and isinstance(output, dict):
            actions = [dict(label=str(T("Open")),
                            _class="action-btn",
                            url=URL(c="event", f="incident",
                                    args=["[id]", "profile"])),
                       dict(label=str(T("Edit")),
                            _class="action-btn",
                            url=URL(c="event", f="incident",
                                    args=["[id]", "update"]))
                       ]
            s3.actions = actions

        return output
    s3.postp = custom_postp

    # Remove RHeader
    attr["rheader"] = None
    return attr

settings.customise_event_incident_controller = customise_event_incident_controller

# -----------------------------------------------------------------------------
def customise_event_incident_resource(r, tablename):
    """
        Customise org_resource resource
        - Customize Fi
        - List Fields
        - Form
        - Filter Widgets
        Runs after controller customisation
        But runs before prep
    """

    s3 = current.response.s3
    s3db = current.s3db
    table = r.table

    if r.interactive:
        table.zero_hour.label = T("Date")
        table.comments.label = T("Description")
        
        s3.crud_strings["event_incident"].label_delete_button = T("Delete Incident"),

    if r.method == "validate":
        from s3.s3validators import IS_LOCATION
        table.location_id.requires = IS_LOCATION()
    else:
        list_fields = ["zero_hour",
                       "name",
                       "location_id",
                       "comments",
                       "organisation_id",
                       ]
        
        # Custom Form
        # Disable until LocationSelectorWidget can be made to work Inline
        #location_id_field = s3db.project_location.location_id
        #location_id_field.label = ""
        #from s3.s3validators import IS_LOCATION_SELECTOR2
        #from s3.s3widgets import S3LocationSelectorWidget2
        #location_id_field.requires = IS_LOCATION_SELECTOR2(levels=levels)
        #location_id_field.widget = S3LocationSelectorWidget2(levels=levels,
        #                                                     show_address=True,
        #                                                     show_map=True)
        ## Don't add new Locations here
        #location_id_field.comment = None

        #from gluon.validators import IS_EMPTY_OR
        #table.organisation_id.requires = IS_EMPTY_OR(table.organisation_id.requires)
        table.zero_hour.label = T("Date")
        #s3db.event_incident_organisation.organisation_id.label = ""
        #s3db.event_incident_project_type.project_type_id.label = ""
        from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent
        crud_form = S3SQLCustomForm(
                        "zero_hour",
                        "name",
                        "location_id",
                        "comments",
                        "organisation_id",
                        )

        from s3.s3filter import S3TextFilter, S3OptionsFilter, S3LocationFilter
        filter_widgets = [S3TextFilter(["name",
                                        "comments"
                                        ],
                                       label=T("Description"),
                                       _class="filter-search",
                                       ),
                          S3LocationFilter("location_id",
                                           #label = T("Location"),
                                           levels = levels,
                                           ),
                          #S3OptionsFilter("status_id",
                          #                label = T("Status"),
                          #                # @ToDo: Introspect cols
                          #                cols = 3,
                          #                ),
                          S3OptionsFilter("organisation_id",
                                          represent="%(name)s",
                                          ),
                          #S3OptionsFilter("project_organisation.organisation_id$organisation_type_id",
                          #                ),
                          ]

        url_next = URL(c="event", f="incident", args="summary")

        s3db.configure("event_incident",
                       create_next = url_next,
                       crud_form = crud_form,
                       delete_next = url_next,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       update_next = url_next,
                       )

        if r.method == "profile":
            # Customise tables used by widgets
            #customise_cms_post_fields()
            #customise_hrm_human_resource_fields()
            #customise_org_office_fields()
            customise_project_task_resource(r, "project_task")
            
            s3db.org_customise_org_resource_fields("profile")
            #customise_event_incident_fields()

            # Set list_fields for renderer (project_task_list_layout)
            s3db.configure("project_task",
                           list_fields = ["name",
                                          "description",
                                          "location_id",
                                          "date_due",
                                          "pe_id",
                                          "task_project.project_id",
                                          #"organisation_id$logo",
                                          "pe_id",
                                          "modified_by",
                                          ],
                           )

            from s3.s3resource import S3FieldSelector
            tasks_widget = dict(label = "Tasks",
                                label_create = "Create Task",
                                type = "datalist",
                                tablename = "project_task",
                                # @ToDo - do this with context? Not clear how with link table
                                # But this WORKS! So don't change without testing!
                                #context = "project",
                                filter = S3FieldSelector("task_project.project_id") == r.id,
                                icon = "icon-task",
                                show_on_map = False, # No Marker yet & only show at L1-level anyway
                                colspan = 2,
                                list_layout = s3db.project_task_list_layout,
                                )
            record = r.record
            title = "%s : %s" % (s3.crud_strings["event_incident"].title_list, record.name)
            s3db.configure("event_incident",
                           profile_title = title,
                           profile_header = DIV(H2(title),
                                                _class="profile_header",
                                                ),
                           profile_widgets = [tasks_widget,
                                              ],
                           #profile_cols = 3
                           )

            # Set list_fields for renderer (project_project_list_layout)
            # @ ToDo: move this to somewhere in trunk where it is called when projects are used in a profile page
            #s3db.configure("event_incident",
            #               list_fields = ["name",
            #                              "description",
            #                              "location.location_id",
            #                              "start_date",
            #                              "organisation_id",
            #                              "organisation_id$logo",
            #                              "modified_by",
            #                              ]
            #               )

settings.customise_event_incident_resource = customise_event_incident_resource

# -----------------------------------------------------------------------------
def customise_org_facility_resource(r, tablename):
    """
        Customise org_resource resource
        - CRUD Strings
        - List Fields
        - Form
        - Report Options
        Runs after controller customisation
        But runs before prep
    """

    s3 = current.response.s3
    s3db = current.s3db
    table = s3db.org_facility

    s3.crud_strings[tablename] = Storage(
        label_create = T("Create Facility"),
        title_display = T("Facility Details"),
        title_list = T("Facilities"),
        title_update = T("Edit Facility Details"),
        label_list_button = T("List Facilities"),
        label_delete_button = T("Delete Facility"),
        msg_record_created = T("Facility added"),
        msg_record_modified = T("Facility details updated"),
        msg_record_deleted = T("Facility deleted"),
        msg_list_empty = T("No Facilities currently registered"))

    location_id_field = table.location_id
    from s3.s3validators import IS_LOCATION_SELECTOR2
    from s3.s3widgets import S3LocationSelectorWidget2
    location_id_field.requires = IS_LOCATION_SELECTOR2(levels=levels)
    location_id_field.widget = S3LocationSelectorWidget2(levels=levels,
                                                         show_address=True,
                                                         show_map=True)
    # Don't add new Locations here
    location_id_field.comment = None

    list_fields = ["name",
                   "organisation_id",
                   #(T("Type"), "facility_type.name"),
                   "location_id",
                   "phone1",
                   "comments",
                   ]

    from s3.s3forms import S3SQLCustomForm
    crud_form = S3SQLCustomForm(*list_fields)

    # Report options
    report_fields = ["organisation_id",
                     ]

    report_options = Storage(rows = report_fields,
                             cols = report_fields,
                             fact = ["count(id)"
                                     ],
                             defaults=Storage(rows = "organisation_id",
                                              cols = "",
                                              fact = "count(id)",
                                              totals = True,
                                              chart = "barchart:rows",
                                              #table = "collapse",
                                              )
                             )

    url_next = URL(c="org", f="facility", args="summary")

    s3db.configure("org_facility",
                   create_next = url_next,
                   crud_form = crud_form,
                   delete_next = url_next,
                   list_fields = list_fields,
                   report_options = report_options,
                   list_layout = render_facilities,
                   update_next = url_next,
                   )

settings.customise_org_facility_resource = customise_org_facility_resource

# -----------------------------------------------------------------------------
def customise_pr_person_controller(**attr):

    s3 = current.response.s3

    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        if r.interactive and isinstance(output, dict):
            actions = [dict(label=str(T("Open")),
                            _class="action-btn",
                            url=URL(c="pr", f="person",
                                    args=["[id]", "read"]))
                       ]
            s3.actions = actions

            if "form" in output:
                output["form"].add_class("pr_person")
            elif "item" in output and hasattr(output["item"], "add_class"):
                output["item"].add_class("pr_person")

        return output
    s3.postp = custom_postp

    # Remove RHeader
    attr["rheader"] = None
    return attr

settings.customise_pr_person_controller = customise_pr_person_controller

# -----------------------------------------------------------------------------
def customise_pr_person_resource(r, tablename):
    """
        Customise org_resource resource
        - List Fields
        - Fields
        - Form
        - Filter Widgets
        - Report Options
        Runs after controller customisation
        But runs before prep
    """

    s3db = current.s3db
    request = current.request
    s3 = current.response.s3

    tablename = "pr_person"
    table = s3db.pr_person

    # CRUD Strings
    ADD_CONTACT = T("Create Contact")
    s3.crud_strings[tablename] = Storage(
        label_create = T("Create Contact"),
        title_display = T("Contact Details"),
        title_list = T("Contact Directory"),
        title_update = T("Edit Contact Details"),
        label_list_button = T("List Contacts"),
        label_delete_button = T("Delete Contact"),
        msg_record_created = T("Contact added"),
        msg_record_modified = T("Contact details updated"),
        msg_record_deleted = T("Contact deleted"),
        msg_list_empty = T("No Contacts currently registered"))

    if r.method == "validate":
        # Can't validate image without the file
        image_field = s3db.pr_image.image
        image_field.requires = None

    MOBILE = settings.get_ui_label_mobile_phone()
    EMAIL = T("Email")

    htable = s3db.hrm_human_resource
    htable.organisation_id.widget = None
    site_field = htable.site_id
    from s3.s3fields import S3Represent
    represent = S3Represent(lookup="org_site")
    site_field.label = T("Facility")
    site_field.represent = represent
    from s3.s3validators import IS_ONE_OF
    site_field.requires = IS_ONE_OF(current.db, "org_site.site_id",
                                    represent,
                                    orderby = "org_site.name")
    
    from s3layouts import S3AddResourceLink
    site_field.comment = S3AddResourceLink(c="org", f="facility",
                                           vars={"child": "site_id"},
                                           label=T("Create Facility"),
                                           title=T("Facility"),
                                           tooltip=T("If you don't see the Facility in the list, you can add a new one by clicking link 'Create Facility'."))

    # Best to have no labels when only 1 field in the row
    s3db.pr_contact.value.label = ""
    image_field = s3db.pr_image.image
    image_field.label = ""
    # ImageCrop widget doesn't currently work within an Inline Form
    from gluon.validators import IS_IMAGE
    image_field.requires = IS_IMAGE()
    image_field.widget = None

    hr_fields = ["organisation_id",
                 "job_title_id",
                 "site_id",
                 ]

    # Context from a Profile page?"
    organisation_id = request.get_vars.get("(organisation)", None)
    if organisation_id:
        field = s3db.hrm_human_resource.organisation_id
        field.default = organisation_id
        field.readable = field.writable = False
        hr_fields.remove("organisation_id")

    
    from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent
    s3_sql_custom_fields = [
            "first_name",
            #"middle_name",
            "last_name",
            S3SQLInlineComponent(
                "human_resource",
                name = "human_resource",
                label = "",
                multiple = False,
                fields = hr_fields,
            ),
            S3SQLInlineComponent(
                "image",
                name = "image",
                label = T("Photo"),
                multiple = False,
                fields = ["image"],
                filterby = dict(field = "profile",
                                options=[True]
                                )
            ),
        ]

    list_fields = ["human_resource.organisation_id",
                   "first_name",
                   #"middle_name",
                   "last_name",
                   (T("Job Title"), "human_resource.job_title_id"),
                   (T("Facility"), "human_resource.site_id"),
                   ]
    
    # Don't include Email/Phone for unauthenticated users
    if current.auth.is_logged_in():
        list_fields += [(MOBILE, "phone.value"),
                        (EMAIL, "email.value"),
                        ]
        s3_sql_custom_fields.insert(3,
                                    S3SQLInlineComponent(
                                    "contact",
                                    name = "phone",
                                    label = MOBILE,
                                    multiple = False,
                                    fields = ["value"],
                                    filterby = dict(field = "contact_method",
                                                    options = "SMS")),
                                    )
        s3_sql_custom_fields.insert(3,
                                    S3SQLInlineComponent(
                                    "contact",
                                    name = "email",
                                    label = EMAIL,
                                    multiple = False,
                                    fields = ["value"],
                                    filterby = dict(field = "contact_method",
                                                    options = "EMAIL")),
                                    )

    crud_form = S3SQLCustomForm(*s3_sql_custom_fields)

    from s3.s3filter import S3TextFilter, S3OptionsFilter
    filter_widgets = [S3TextFilter(["pe_label",
                                    "first_name",
                                    "middle_name",
                                    "last_name",
                                    "local_name",
                                    "identity.value",
                                    "human_resource.organisation_id",
                                    "human_resource.job_title_id",
                                    "human_resource.site_id",
                                    ],
                                   label=T("Search"),
                                   ),
                      S3OptionsFilter("human_resource.organisation_id",
                                      ),
                      S3OptionsFilter("human_resource.job_title_id",
                                      ),
                      S3OptionsFilter("human_resource.site_id",
                                      ),
                      ]


    # Return to List view after create/update/delete (unless done via Modal)
    url_next = URL(c="pr", f="person", )

    # Report options
    report_fields = ["organisation_id",
                     ]

    report_options = Storage(rows = report_fields,
                             cols = report_fields,
                             fact = ["count(id)"
                                     ],
                             defaults=Storage(rows = "organisation_id",
                                              cols = "",
                                              fact = "count(id)",
                                              totals = True,
                                              chart = "barchart:rows",
                                              #table = "collapse",
                                              )
                             )

    s3db.configure(tablename,
                   create_next = url_next,
                   crud_form = crud_form,
                   delete_next = url_next,
                   filter_widgets = filter_widgets,
                   list_fields = list_fields,
                   report_options = report_options,
                   # Don't include a Create form in 'More' popups
                   #listadd = False if r.method=="datalist" else True,
                   #list_layout = render_contacts,
                   update_next = url_next,
                   )

    # HR Fields For dataList Cards
    list_fields = ["person_id",
                   "organisation_id",
                   "site_id$location_id",
                   "site_id$location_id$addr_street",
                   "job_title_id",
                   "email.value",
                   "phone.value",
                   #"modified_by",
                   "modified_on",
                   ]

    s3db.configure("hrm_human_resource",
                   list_fields = list_fields,
                   )

settings.customise_pr_person_resource = customise_pr_person_resource

# =============================================================================
# Custom list_layout renders (Copy & Pasted from DRMP)
# @ToDo: re-factor

# -----------------------------------------------------------------------------
def render_contacts(list_id, item_id, resource, rfields, record):
    """
        Custom dataList item renderer for Contacts on the Profile pages

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["hrm_human_resource.id"]
    item_class = "thumbnail"

    raw = record._row
    #author = record["hrm_human_resource.modified_by"]
    date = record["hrm_human_resource.modified_on"]
    fullname = record["hrm_human_resource.person_id"]
    job_title = raw["hrm_human_resource.job_title_id"] or ""
    if job_title:
        job_title = "- %s" % record["hrm_human_resource.job_title_id"]
    #organisation = record["hrm_human_resource.organisation_id"]
    organisation_id = raw["hrm_human_resource.organisation_id"]
    #org_url = URL(c="org", f="organisation", args=[organisation_id, "profile"])
    person_id = raw["hrm_human_resource.person_id"]
    location = record["org_site.location_id"]
    location_id = raw["org_site.location_id"]
    location_url = URL(c="gis", f="location",
                       args=[location_id, "profile"])
    address = raw["gis_location.addr_street"] or T("no facility assigned")
    email = raw["pr_email_contact.value"] or T("no email address")
    if isinstance(email, list):
        email = email[0]
    phone = raw["pr_phone_contact.value"] or T("no phone number")
    if isinstance(phone, list):
        phone = phone[0]

    if person_id:
        # Use Personal Avatar
        # @ToDo: Optimise by not doing DB lookups within render, but doing these in the bulk query
        avatar = s3_avatar_represent(person_id,
                                     tablename="pr_person",
                                     _class="media-object")
    else:
        avatar = IMG(_src=URL(c="static", f="img", args="blank-user.gif"),
                     _class="media-object")

    # Edit Bar
    permit = current.auth.s3_has_permission
    table = current.s3db.pr_person
    if permit("update", table, record_id=person_id):
        vars = {"refresh": list_id,
                "record": record_id,
                }
        f = current.request.function
        if f == "organisation" and organisation_id:
            vars["(organisation)"] = organisation_id
        edit_url = URL(c="hrm", f="person",
                       args=[person_id, "update.popup"],
                       vars=vars)
        title_update = current.response.s3.crud_strings.hrm_human_resource.title_update
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=edit_url,
                     _class="s3_modal",
                     _title=title_update,
                     )
    else:
        edit_btn = ""
        edit_url = "#"
        title_update = ""
    # Deletions failing due to Integrity Errors
    #if permit("delete", table, record_id=person_id):
    #    delete_btn = A(I(" ", _class="icon icon-remove-sign"),
    #                   _class="dl-item-delete",
    #                   )
    #else:
    delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    avatar = A(avatar,
               _href=edit_url,
               _class="pull-left s3_modal",
               _title=title_update,
               )

    # Render the item
    body = TAG[""](P(I(_class="icon-phone"),
                     " ",
                     SPAN(phone),
                     " ",
                     ),
                   P(I(_class="icon-envelope-alt"),
                     " ",
                     SPAN(email),
                     _class="main_contact_ph",
                     ),
                   #P(I(_class="icon-home"),
                   #  " ",
                   #  address,
                   #  _class="main_office-add",
                   #  )
                   )

    item = DIV(DIV(SPAN(fullname,
                        " ",
                        job_title, 
                        _class="card-title"),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(avatar,
                   DIV(DIV(body,
                           # Organisation only needed if displaying elsewhere than org profile
                           # Author confusing with main contact record
                           #DIV(#author,
                           #    #" - ",
                           #    A(organisation,
                           #      _href=org_url,
                           #      _class="card-organisation",
                           #      ),
                           #    _class="card-person",
                           #    ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               #docs,
               _class=item_class,
               _id=item_id,
               )

    return item
# -----------------------------------------------------------------------------
def render_facilities(list_id, item_id, resource, rfields, record):
    """
        Custom dataList item renderer for Facilities on the Profile pages

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["org_facility.id"]
    item_class = "thumbnail"

    raw = record._row
    name = record["org_facility.name"]
    author = record["org_facility.modified_by"]
    date = record["org_facility.modified_on"]
    organisation = record["org_facility.organisation_id"]
    organisation_id = raw["org_facility.organisation_id"]
    location = record["org_facility.location_id"]
    location_id = raw["org_facility.location_id"]
    location_url = URL(c="gis", f="location",
                       args=[location_id, "profile"])
    address = raw["gis_location.addr_street"]
    phone = raw["org_facility.phone1"]
    facility_type = record["org_facility.facility_type_id"]
    logo = raw["org_organisation.logo"]

    org_url = URL(c="org", f="organisation", args=[organisation_id, "profile"])
    if logo:
        logo = A(IMG(_src=URL(c="default", f="download", args=[logo]),
                     _class="media-object",
                     ),
                 _href=org_url,
                 _class="pull-left",
                 )
    else:
        logo = DIV(IMG(_class="media-object"),
                   _class="pull-left")

    # Edit Bar
    permit = current.auth.s3_has_permission
    table = current.db.org_facility
    if permit("update", table, record_id=record_id):
        vars = {"refresh": list_id,
                "record": record_id,
                }
        f = current.request.function
        if f == "organisation" and organisation_id:
            vars["(organisation)"] = organisation_id
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=URL(c="org", f="facility",
                               args=[record_id, "update.popup"],
                               vars=vars),
                     _class="s3_modal",
                     _title=current.response.s3.crud_strings.org_facility.title_update,
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(I(" ", _class="icon icon-remove-sign"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    avatar = logo
    body = TAG[""](#P(I(_class="icon-flag"),
                   #  " ",
                   #  SPAN(facility_type),
                   #  " ",
                   #  _class="main_contact_ph",
                   #  ),
                   P(I(_class="icon-phone"),
                     " ",
                     SPAN(phone or T("no phone number")),
                     " ",
                     ),
                   P(I(_class="icon-home"),
                     " ",
                     address,
                     _class="main_facility-add",
                     ))

    item = DIV(DIV(SPAN(name, _class="card-title"),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(#avatar,
                   DIV(DIV(body,
                           DIV(#author,
                               #" - ",
                               #A(organisation,
                               #  _href=org_url,
                               #  _class="card-organisation",
                               #  ),
                               #_class="card-person",
                               ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               #docs,
               _class=item_class,
               _id=item_id,
               )

    return item
# =============================================================================
# Modules
# Comment/uncomment modules here to disable/enable them
settings.modules = OrderedDict([
    # Core modules which shouldn't be disabled
    ("default", Storage(
        name_nice = "Home",
        restricted = False, # Use ACLs to control access to this module
        access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
        module_type = None  # This item is not shown in the menu
    )),
    ("admin", Storage(
        name_nice = "Administration",
        #description = "Site Administration",
        restricted = True,
        access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
        module_type = None  # This item is handled separately for the menu
    )),
    ("appadmin", Storage(
        name_nice = "Administration",
        #description = "Site Administration",
        restricted = True,
        module_type = None  # No Menu
    )),
#    ("errors", Storage(
#        name_nice = "Ticket Viewer",
#        #description = "Needed for Breadcrumbs",
#        restricted = False,
#        module_type = None  # No Menu
#    )),
   ("sync", Storage(
       name_nice = "Synchronization",
       #description = "Synchronization",
       restricted = True,
       access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
       module_type = None  # This item is handled separately for the menu
   )),
    ("translate", Storage(
        name_nice = "Translation Functionality",
        #description = "Selective translation of strings based on module.",
        module_type = None,
    )),
    ("gis", Storage(
        name_nice = "Map",
        #description = "Situation Awareness & Geospatial Analysis",
        restricted = True,
        module_type = 1,     # 1st item in the menu
    )),
    ("pr", Storage(
        name_nice = "Persons",
        description = "Central point to record details on People",
        restricted = True,
        access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
        module_type = None
    )),
    ("org", Storage(
        name_nice = "Organizations",
        #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
        restricted = True,
        module_type = None
    )),
    # All modules below here should be possible to disable safely
    ("hrm", Storage(
        name_nice = "Contacts",
        #description = "Human Resources Management",
        restricted = True,
        module_type = None,
    )),
    ("cms", Storage(
            name_nice = "Content Management",
            restricted = True,
            module_type = None,
        )),
    ("event", Storage(
            name_nice = "Event Management",
            restricted = True,
            module_type = None,
        )),
    ("project", Storage(
            name_nice = "Project Management",
            restricted = True,
            module_type = None,
        )),
    ("doc", Storage(
        name_nice = "Documents",
        #description = "A library of digital resources, such as photos, documents and reports",
        restricted = True,
        module_type = None,
    )),
    ("stats", Storage(
        name_nice = "Statistics",
        restricted = True,
        module_type = None
    )),
])
