# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from datetime import timedelta

from gluon import current, Field, URL
from gluon.html import *
from gluon.storage import Storage
from gluon.validators import IS_NULL_OR, IS_NOT_EMPTY

from s3.s3fields import S3Represent
from s3.s3resource import S3FieldSelector
from s3.s3utils import S3DateTime, s3_auth_user_represent_name, s3_avatar_represent, s3_unicode
from s3.s3validators import IS_INT_AMOUNT, IS_LOCATION_SELECTOR2, IS_ONE_OF
from s3.s3widgets import S3LocationSelectorWidget2
from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineComponentMultiSelectWidget
from s3.s3filter import S3TextFilter, S3OptionsFilter, S3LocationFilter

T = current.T
s3 = current.response.s3
settings = current.deployment_settings

"""
    Puget Sound Common Maritime Operating Picture (MCOP) 

    All settings which are to configure a specific template are located here

    Deployers should ideally not need to edit any other files outside of their template folder
"""

datetime_represent = lambda dt: S3DateTime.datetime_represent(dt, utc=True)

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
# Summary Pages
settings.ui.summary = [#{"common": True,
                       # "name": "cms",
                       # "widgets": [{"method": "cms"}]
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
                        "widgets": [{"method": "report2", "ajax_init": True}]
                        },
                       ]

settings.search.filter_manager = False
# =============================================================================
# Menu
current.response.menu = [
    {"name": T("Stakeholders"),
     "c":"org", 
     "f":"organisation",
     "icon": "sitemap"
     },
    {"name": T("News Feed"),
     "c":"cms", 
     "f":"post",
     "icon": "news"
     },
    {"name": T("Resources"),
     "c":"org", 
     "f":"resource",
     "icon": "wrench"
     },
    {"name": T("Projects"),
     "c":"project", 
     "f":"activity",
     "icon": "tasks"
     },
    {"name": T("Tasks"),
     "c":"project", 
     "f":"task",
     "icon": "check"
     },
    {"name": T("Offices"),
     "c":"org", 
     "f":"office",
     "icon": "building"
     },
    {"name": T("Contacts"),
     "c":"pr", 
     "f":"person",
     "icon": "group"
     }
    ]

for item in current.response.menu:
    item["url"] = URL(item["c"], 
                      item["f"], 
                      args = ["summary" if item["f"] not in ["organisation","post"]
                                        else "datalist"])
# =============================================================================
# Module Settings

# -----------------------------------------------------------------------------
# =============================================================================
# Custom Controllers

# -----------------------------------------------------------------------------
def customize_org_organisation(**attr):
    """
        Customize org_organisation controller
        - List Fields
        - Form
        - Filter
        - Report 
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

        if r.interactive or r.representation == "aadata":
            # Load normal Model
            s3db = current.s3db
            table = s3db.org_organisation

            ADD_ORGANISATION = T("New Stakeholder")
            s3.crud_strings["org_organisation"] = Storage(
                title_create = ADD_ORGANISATION,
                title_display = T("Stakeholder Details"),
                title_list = T("Stakeholders"),
                title_update = T("Edit Stakeholder"),
                title_search = T("Search Stakeholders"),
                subtitle_create = T("Add New Stakeholder"),
                label_list_button = T("List Stakeholders"),
                label_create_button = ADD_ORGANISATION,
                label_delete_button = T("Delete Stakeholder"),
                msg_record_created = T("Stakeholder added"),
                msg_record_modified = T("Stakeholder updated"),
                msg_record_deleted = T("Stakeholder deleted"),
                msg_list_empty = T("No Stakeholders currently registered"))

            list_fields = ["id",
                           "name",
                           "logo",
                           "phone",
                           "website",
                           ]

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

            # Labels
            table.comments.label = T("Description")

            crud_form = S3SQLCustomForm("id",
                                        "name",
                                        "organisation_type_id",
                                         #S3SQLInlineComponentMultiSelectWidget(
                                         #    "sector",
                                         #    label = T("Sectors"),
                                         #    field = "sector_id",
                                         #),
                                         #S3SQLInlineComponentMultiSelectWidget(
                                         #    "service",
                                         #    label = T("Services"),
                                         #    field = "service_id",
                                         #),
                                        "logo",
                                        "phone",
                                        "website",
                                        "comments")
            
            # Return to List view after create/update/delete (unless done via Modal)
            url_next = URL(c="org", f="organisation", args="datalist")

            s3db.configure("org_organisation",
                           create_next = url_next,
                           delete_next = url_next,
                           update_next = url_next,
                           # We want the Create form to be in a modal, not inline, for consistency
                           #listadd = False,
                           list_fields = list_fields,
                           list_layout = org_organisations_list_layout,
                           crud_form = crud_form,
                           )

        return True
    s3.prep = custom_prep

    attr["hide_filter"] = False
    # Remove rheader
    attr["rheader"] = None
    return attr

settings.ui.customize_org_organisation = customize_org_organisation

# -----------------------------------------------------------------------------
def customize_org_resource(**attr):
    """
        Customize org_resource controller
    """

    s3 = current.response.s3
    s3db = current.s3db
    table = s3db.org_resource

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        if r.interactive or r.representation == "aadata":
            s3db.org_customize_org_resource_fields(r.method)
    
            # Configure fields
            #table.site_id.readable = table.site_id.readable = False
            location_field = table.location_id
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
            levels = ["L1","L2"]
            location_field.requires = IS_LOCATION_SELECTOR2(levels=levels)
            location_field.widget = S3LocationSelectorWidget2(levels=levels,
                                                              show_address=True,
                                                              show_map=True)

            # Don't add new Locations here
            location_field.comment = None

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
    s3.prep = custom_prep

    attr["hide_filter"] = False
    # Remove rheader
    attr["rheader"] = None
    return attr

settings.ui.customize_org_resource = customize_org_resource

# -----------------------------------------------------------------------------
def customize_cms_post(**attr):
    """
        Customize cms_post controller
    """

    s3 = current.response.s3
    s3db = current.s3db
    table = s3db.cms_post

    s3.dl_pagelength = 12
    s3.dl_rowsize = 2
    # CRUD Form
    
    levels = ["L1","L2"]
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
            #label = T("Disaster(s)"),
            label = T("Disaster"),
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

    attr["hide_filter"] = False
    # Remove rheader
    attr["rheader"] = None
    return attr

settings.ui.customize_cms_post = customize_cms_post

# -----------------------------------------------------------------------------
def customize_project_task(**attr):
    """
        Customize project_task controller
    """

    s3 = current.response.s3
    s3db = current.s3db
    table = s3db.project_task


    # In Custom PreP to over-write defaults
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            # Called first so that we can unhide the Type field
            result = standard_prep(r)
            if not result:
                return False

        list_fields = ["id",
                       "status",
                       "name",
                       "priority",
                       (T("Project"),"task_activity.activity_id"),
                       "date_due",
                       ]
    
        # Custom Form
        table.name.label = T("Name")
        table.description.label = T("Description")
        s3db.project_task_activity.activity_id.label = T("Project")
        crud_form = S3SQLCustomForm(
                        "status",
                        "name",
                        "description",
                        "priority",
                        "task_activity.activity_id",
                        "pe_id",
                        "date_due",
                        )
    
        #Filter Widgets
        filter_widgets = s3db.get_config("project_task", 
                                         "filter_widgets")
        # Remove Project Fitler
        filter_widgets.pop(2)
    
        # Report options
        report_fields = ["status",
                         "priority",
                         "pe_id",
                         "task_activity.activity_id",
                         ]
    
        report_options = Storage(rows = report_fields,
                                 cols = report_fields,
                                 fact = ["count(name)"
                                         ],
                                 defaults=Storage(rows = "status",
                                                  cols = "priority",
                                                  fact = "count(name)",
                                                  totals = True,
                                                  chart = "barchart:rows",
                                                  #table = "collapse",
                                                  )
                                 )
    
        s3db.configure("project_task",
                       crud_form = crud_form,
                       list_fields = list_fields,
                       report_options = report_options,
                       )
        return True
    s3.prep = custom_prep

    attr["hide_filter"] = False
    # Remove rheader
    attr["rheader"] = None
    return attr

settings.ui.customize_project_task = customize_project_task

# -----------------------------------------------------------------------------

def customize_project_activity(**attr):
    """
        Customize project_activity controller
    """

    s3 = current.response.s3
    s3db = current.s3db
    table = s3db.project_activity

    #Use activities as projects (Temporary - location widget broken inline
    s3.crud_strings["project_activity"] = s3.crud_strings["project_project"]

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        if r.method in ["create", "update"]:
            # hide inline labels
            s3db.project_activity_organisation.organisation_id.label = ""
            s3db.project_activity_activity_type.activity_type_id.label = ""
        return True
    s3.prep = custom_prep

    list_fields = ["id",
                   "status_id",
                   "name",
                   "location_id",
                   "activity_organisation.organisation_id",
                   "date",
                   "end_date",
                   ]

    # Custom Form

    levels = ["L1","L2"]
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
                   list_fields = list_fields,
                   crud_form = crud_form,
                   filter_widgets = filter_widgets,
                   report_options = report_options,
                   )

    attr["hide_filter"] = False
    # Remove rheader
    attr["rheader"] = None
    return attr

settings.ui.customize_project_activity = customize_project_activity

# -----------------------------------------------------------------------------
def customize_project_project(**attr):
    """
        Customize project_project controller
    """

    s3 = current.response.s3
    s3db = current.s3db
    table = s3db.project_project
    
    # Custom Form

    # Which levels of Hierarchy are we using?
    levels = ["L1","L2"]
    location_id_field = s3db.project_location.location_id
    location_id_field.requires = IS_LOCATION_SELECTOR2(levels=levels)
    location_id_field.widget = S3LocationSelectorWidget2(levels=levels,
                                                      show_address=True,
                                                      show_map=True)
    # Don't add new Locations here
    location_id_field.comment = None

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
                                         orderby = "location_id$name",
                                         #multiple = False,
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
                   #filter_widgets = filter_widgets,
                   )

    attr["hide_filter"] = False
    # Remove rheader
    attr["rheader"] = None
    return attr

settings.ui.customize_project_project = customize_project_project

# -----------------------------------------------------------------------------
def customize_org_office(**attr):
    """
        Customize org_office controller
    """

    s3 = current.response.s3
    s3db = current.s3db
    table = s3db.org_office

    levels = ["L1","L2"]
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

    attr["hide_filter"] = False
    # Remove rheader
    attr["rheader"] = None
    return attr

settings.ui.customize_org_office = customize_org_office

# -----------------------------------------------------------------------------
def customize_pr_person(**attr):
    """
        Customize pr_person controller
    """

    s3db = current.s3db
    request = current.request
    s3 = current.response.s3

    tablename = "pr_person"
    table = s3db.pr_person

    # CRUD Strings
    ADD_CONTACT = T("Add New Contact")
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Contact"),
        title_display = T("Contact Details"),
        title_list = T("Contact Directory"),
        title_update = T("Edit Contact Details"),
        title_search = T("Search Contacts"),
        subtitle_create = ADD_CONTACT,
        label_list_button = T("List Contacts"),
        label_create_button = ADD_CONTACT,
        label_delete_button = T("Delete Contact"),
        msg_record_created = T("Contact added"),
        msg_record_modified = T("Contact details updated"),
        msg_record_deleted = T("Contact deleted"),
        msg_list_empty = T("No Contacts currently registered"))

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

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
                                           label=T("Add New Office"),
                                           title=T("Office"),
                                           tooltip=T("If you don't see the Office in the list, you can add a new one by clicking link 'Add New Office'."))

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
            output["rheader"] = ""
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

    # Remove rheader
    attr["rheader"] = None

    return attr

# -----------------------------------------------------------------------------
settings.ui.customize_pr_person = customize_pr_person
# -----------------------------------------------------------------------------
# @ToDo: make this more reusable
def org_organisations_list_layout(list_id, item_id, resource, rfields, record):
    """
        Custom dataList item renderer for Organisations on the Stakeholder Selection Page

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["org_organisation.id"]
    item_class = "thumbnail" # span6 for 2 cols

    raw = record._row
    name = record["org_organisation.name"]
    logo = raw["org_organisation.logo"]
    phone = raw["org_organisation.phone"] or ""
    website = raw["org_organisation.website"] or ""
    if website:
        website = A(website, _href=website)

    org_url = URL(c="org", f="organisation", args=[record_id, "profile"])
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

    db = current.db
    permit = current.auth.s3_has_permission
    table = db.org_organisation
    if permit("update", table, record_id=record_id):
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=URL(c="org", f="organisation",
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id}),
                     _class="s3_modal dl-item-edit",
                     _title=current.response.s3.crud_strings.org_organisation.title_update,
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(I(" ", _class="icon icon-trash"),
                       _class="dl-item-delete",
                      )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )
    # Render the item
    item = DIV(DIV(logo,
                   DIV(SPAN(A(name,
                              _href=org_url,
                              _class="media-heading"
                              ),
                            ),
                       edit_bar,
                       _class="card-header-select",
                       ),
                   DIV(P(I(_class="icon icon-phone"),
                         " ",
                         phone,
                         _class="card_1_line",
                         ),
                       P(I(_class="icon icon-map"),
                         " ",
                         website,
                         _class="card_1_line",
                         ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               _class=item_class,
               _id=item_id,
               )

    return item

# For access from custom controllers
s3.org_organisations_list_layout = org_organisations_list_layout
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