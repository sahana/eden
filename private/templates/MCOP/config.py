# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current
from gluon.html import *
from gluon.storage import Storage

from s3.s3fields import S3Represent
from s3.s3validators import IS_LOCATION_SELECTOR2, IS_ONE_OF
from s3.s3widgets import S3LocationSelectorWidget2
from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent
from s3.s3filter import S3TextFilter, S3OptionsFilter, S3LocationFilter

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
#settings.ui.filter_formstyle = "bootstrap"
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

settings.customise_org_organisation_controller = customise_no_rheader_controller
settings.customise_org_resource_controller = customise_no_rheader_controller
settings.customise_cms_post_controller = customise_no_rheader_controller
settings.customise_project_task_controller = customise_no_rheader_controller
settings.customise_project_activity_controller = customise_no_rheader_controller
settings.customise_project_project_controller = customise_no_rheader_controller
settings.customise_org_office_controller = customise_no_rheader_controller
settings.customise_pr_person_controller = customise_no_rheader_controller

# -----------------------------------------------------------------------------
# Summary Pages
settings.ui.summary = [#{"common": True,
                       # "name": "cms",
                       # "widgets": [{"method": "cms"}]
                       # },
                       {"common": True,
                        "name": "add",
                        "widgets": [{"method": "create"}],
                        },
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
     "f":"office",
     "icon": "building"
     },
    ]

for item in current.response.menu:
    item["url"] = URL(item["c"], 
                      item["f"], 
                      args = ["summary" if item["f"] not in ["organisation","post"]
                                        else "datalist"])
# =============================================================================
# Module Settings

# =============================================================================
# Custom Controllers

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

        crud_form = S3SQLCustomForm("id",
                                    "name",
                                    "organisation_type_id",
                                    "logo",
                                    "phone",
                                    "website",
                                    "comments")
        s3db.configure("org_organisation",
                       crud_form=crud_form
                       )

        if r.method == "datalist":
            # Stakeholder selection page
            # 2-column datalist, 6 rows per page
            s3.dl_pagelength = 12
            s3.dl_rowsize = 2
    
            from s3.s3filter import S3TextFilter, S3OptionsFilter
            filter_widgets = [S3TextFilter(["name",
                                            "acronym",
                                            "website",
                                            "comments",
                                            ],
                                          label = T("Search")),
                              S3OptionsFilter("organisation_type_id",
                                              label = T("Type"),
                                              widget = "multiselect",
                                              ),
                              ]

            s3db.configure("org_organisation",
                           filter_widgets=filter_widgets
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
                                          widget = "multiselect",
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
                       update_next = url_next,
                       # Don't include a Create form in 'More' popups
                       listadd = False if r.method=="datalist" else True,
                       )

        # This is awful in Popups & inconsistent in dataTable view (People/Documents don't have this & it breaks the styling of the main Save button)
        #s3.cancel = URL(c="org", f="resource")

    return True

settings.customise_org_resource_resource = customise_org_resource_resource

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

    s3.crud_strings["cms_post"] = Storage(
        label_create = T("Create News Post"),
        title_display = T("News Post Details"),
        title_list = T("News"),
        title_update = T("Edit News Post"),
        label_list_button = T("List News Posts"),
        label_delete_button = T("Delete News Post"),
        msg_record_created = T("News Post added"),
        msg_record_modified = T("News Post updated"),
        msg_record_deleted = T("News Post deleted"),
        msg_list_empty = T("No News Post currently registered"))


    # CRUD Form
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
    crud_form = S3SQLCustomForm(
        "date",
        "series_id",
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
    #url_next = URL(c="default", f="index", args="newsfeed")

    s3db.configure("cms_post",
                   crud_form = crud_form,
                   )

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
    s3 = current.response.s3
    s3db = current.s3db
    table = s3db.project_task

    list_fields = ["id",
                   "status",
                   "name",
                   "priority",
                   (T("Project"), "task_activity.activity_id"),
                   "date_due",
                   "location_id",
                   ]

    # Custom Form
    table.name.label = T("Name")
    table.description.label = T("Description")
    table.location_id.readable = table.location_id.writable = True
    s3db.project_task_activity.activity_id.label = T("Project")
    crud_form = S3SQLCustomForm("status",
                                "name",
                                "description",
                                "priority",
                                "task_activity.activity_id",
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
                     "pe_id",
                     "task_activity.activity_id",
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

    s3db.configure("project_task",
                   crud_form = crud_form,
                   filter_widgets = filter_widgets,
                   list_fields = list_fields,
                   report_options = report_options,
                   )

settings.customise_project_task_resource = customise_project_task_resource

# -----------------------------------------------------------------------------
def customise_project_activity_resource(r, tablename):
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

    s3 = current.response.s3
    s3db = current.s3db
    table = s3db.project_activity

    # Use activities as projects (Temporary - location widget doesn't yet work inline)
    s3.crud_strings["project_activity"] = s3.crud_strings["project_project"]

    if r.method in ["create", "update"]:
        # Hide inline labels
        s3db.project_activity_organisation.organisation_id.label = ""
        s3db.project_activity_activity_type.activity_type_id.label = ""

    list_fields = ["id",
                   "status_id",
                   "name",
                   "location_id",
                   "activity_organisation.organisation_id",
                   "date",
                   "end_date",
                   ]

    # Custom Form
    table.location_id.requires = IS_LOCATION_SELECTOR2(levels=levels)
    table.location_id.widget = S3LocationSelectorWidget2(levels=levels,
                                                         show_address=True,
                                                         show_map=True)
    # Don't add new Locations here
    table.location_id.comment = None

    table.name.label = T("Name")
    table.comments.label = T("Description")
    
    crud_form = S3SQLCustomForm(
                    "status_id",
                    "name",
                    "comments",
                    "location_id",
                    S3SQLInlineComponent("activity_organisation",
                                         label = T("Organization"),
                                         fields = ["organisation_id"],
                                         multiple = False,
                                         ),
                    #S3SQLInlineComponent("activity_activity_type",
                    #                     label = T("Activity Type"),
                    #                     fields = ["activity_type_id"],
                    #                     multiple = False,
                    #                     ),
                    "date",
                    "end_date",
                    )

    filter_widgets = [S3TextFilter(["name",
                                    ],
                                   label=T("Description"),
                                   _class="filter-search",
                                   ),
                      S3LocationFilter("location_id",
                                       widget="multiselect",
                                       levels = levels,
                                       ),
                      S3OptionsFilter("status_id",
                                      label = T("Status"),
                                      # Doesn't support translation
                                      #represent="%(name)s",
                                      # @ToDo: Introspect cols
                                      cols = 3,
                                      #widget="multiselect",
                                      ),
                      #S3OptionsFilter("activity_activity_type.activity_type_id",
                                      # Doesn't support translation
                                      #represent="%(name)s",
                      #                widget="multiselect",
                      #                ),
                      S3OptionsFilter("activity_organisation.organisation_id",
                                      # Doesn't support translation
                                      #represent="%(name)s",
                                      widget="multiselect",
                                      ),
                      S3OptionsFilter("activity_organisation.organisation_id$organisation_type_id",
                                      # Doesn't support translation
                                      #represent="%(name)s",
                                      widget="multiselect",
                                      ),
                      ]

    # Report options
    report_fields = ["activity_organisation.organisation_id",
                     "status_id",
                     ]

    report_options = Storage(rows = report_fields,
                             cols = report_fields,
                             fact = ["count(id)"
                                     ],
                             defaults=Storage(rows = "activity_organisation.organisation_id",
                                              cols = "status_id",
                                              fact = "count(id)",
                                              totals = True,
                                              chart = "barchart:rows",
                                              #table = "collapse",
                                              )
                             )

    s3db.configure("project_activity",
                   crud_form = crud_form,
                   filter_widgets = filter_widgets,
                   list_fields = list_fields,
                   report_options = report_options,
                   )

settings.customise_project_activity_resource = customise_project_activity_resource

# -----------------------------------------------------------------------------
def customise_project_project_resource(r, tablename):
    """
        Customise org_resource resource
        - Fields
        - Form
        - Filter Widgets
        Runs after controller customisation
        But runs before prep
    """

    s3 = current.response.s3

    # Custom PreP
    standard_prep = s3.prep

    if r.method == "validate":
        from s3.s3validators import IS_LOCATION
        s3db.project_location.location_id.requires = IS_LOCATION()
    else:
        # Custom Form
        location_id_field = s3db.project_location.location_id
        location_id_field.requires = IS_LOCATION_SELECTOR2(levels=levels)
        location_id_field.widget = S3LocationSelectorWidget2(levels=levels,
                                                             show_address=True,
                                                             show_map=True)
        # Don't add new Locations here
        location_id_field.comment = None

        table = s3db.project_project
        table.name.label = T("Description")
        table.comments.label = T("Details")
        #s3db.project_project_organisation.organisation_id.label = ""
        #s3db.project_project_project_type.project_type_id.label = ""
        crud_form = S3SQLCustomForm(
                        "status_id",
                        "name",
                        "description",
                        #"location.location_id",
                        "organisation_id",
                        S3SQLInlineComponent("location",
                                             label = T("Location"),
                                             fields = ["location_id"],
                                             #orderby = "location_id$name",
                                             multiple = False,
                                             ),
                        "start_date",
                        "end_date",
                        )

        filter_widgets = [S3TextFilter(["name",
                                        ],
                                       label=T("Description"),
                                       _class="filter-search",
                                       ),
                          S3LocationFilter("location_id",
                                           widget="multiselect",
                                           levels = levels,
                                           ),
                          S3OptionsFilter("status_id",
                                          label = T("Status"),
                                          # Doesn't support translation
                                          #represent="%(name)s",
                                          # @ToDo: Introspect cols
                                          cols = 3,
                                          #widget="multiselect",
                                          ),
                          S3OptionsFilter("project_project_type.project_type_id",
                                          # Doesn't support translation
                                          #represent="%(name)s",
                                          widget="multiselect",
                                          ),
                          S3OptionsFilter("project_organisation.organisation_id",
                                          # Doesn't support translation
                                          #represent="%(name)s",
                                          widget="multiselect",
                                          ),
                          S3OptionsFilter("project_organisation.organisation_id$organisation_type_id",
                                          # Doesn't support translation
                                          #represent="%(name)s",
                                          widget="multiselect",
                                          ),
                          ]

        s3db.configure("project_project",
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       )

settings.customise_project_project_resource = customise_project_project_resource

# -----------------------------------------------------------------------------
def customise_org_office_resource(r, tablename):
    """
        Customise org_resource resource
        - List Fields
        - Form
        - Report Options
        Runs after controller customisation
        But runs before prep
    """

    s3 = current.response.s3
    s3db = current.s3db
    table = s3db.org_office

    location_id_field = table.location_id
    location_id_field.requires = IS_LOCATION_SELECTOR2(levels=levels)
    location_id_field.widget = S3LocationSelectorWidget2(levels=levels,
                                                         show_address=True,
                                                         show_map=True)
    # Don't add new Locations here
    location_id_field.comment = None

    list_fields = ["name",
                   "organisation_id",
                   "location_id",
                   "phone1",
                   "comments",
                   ]

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

    s3db.configure("org_office",
                   crud_form = crud_form,
                   list_fields = list_fields,
                   report_options = report_options,
                   )

settings.customise_org_office_resource = customise_org_office_resource

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
    represent = S3Represent(lookup="org_site")
    site_field.label = T("Office")
    site_field.represent = represent
    site_field.requires = IS_ONE_OF(current.db, "org_site.site_id",
                                    represent,
                                    orderby = "org_site.name")
    
    from s3layouts import S3AddResourceLink
    site_field.comment = S3AddResourceLink(c="org", f="office",
                                           vars={"child": "site_id"},
                                           label=T("Create Office"),
                                           title=T("Office"),
                                           tooltip=T("If you don't see the Office in the list, you can add a new one by clicking link 'Create Office'."))

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
                   (T("Office"), "human_resource.site_id"),
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
                                      # Doesn't support translation
                                      #represent="%(name)s",
                                      widget="multiselect",
                                      ),
                      S3OptionsFilter("human_resource.job_title_id",
                                      # Doesn't support translation
                                      #represent="%(name)s",
                                      widget="multiselect",
                                      ),
                      S3OptionsFilter("human_resource.site_id",
                                      # Doesn't support translation
                                      #represent="%(name)s",
                                      widget="multiselect",
                                      ),
                      ]


    # Return to List view after create/update/delete (unless done via Modal)
    #url_next = URL(c="pr", f="person", )

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
                   #create_next = url_next,
                   #delete_next = url_next,
                   #update_next = url_next,
                   crud_form = crud_form,
                   filter_widgets = filter_widgets,
                   list_fields = list_fields,
                   report_options = report_options,
                   # Don't include a Create form in 'More' popups
                   #listadd = False if r.method=="datalist" else True,
                   #list_layout = render_contacts,
                   )

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

settings.customise_pr_person_resource = customise_pr_person_resource

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
#    ("sync", Storage(
#        name_nice = "Synchronization",
#        #description = "Synchronization",
#        restricted = True,
#        access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
#        module_type = None  # This item is handled separately for the menu
#    )),
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
