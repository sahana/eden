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

from s3 import S3DataListLayout, s3_unicode, S3SQLSubFormLayout

T = current.T
settings = current.deployment_settings

"""
    Template settings for Community Resilience Mapping Tool
"""

# -----------------------------------------------------------------------------
# Pre-Populate
settings.base.prepopulate = ("CRMT2", "default/users", "CRMT2/Demo")

settings.base.system_name = T("Sahana LA Community Resilience Mapping Tool")
settings.base.system_name_short = T("CRMT")

# =============================================================================
# US Settings
# -----------------------------------------------------------------------------
# Default timezone for users
settings.L10n.utc_offset = "UTC -0800"
# Uncomment these to use US-style dates
settings.L10n.date_format = "%m-%d-%Y"
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
settings.auth.registration_requires_verification = False
settings.auth.registration_requests_organisation = True
settings.auth.registration_organisation_required = False
settings.auth.registration_requests_organisation_group = True
settings.auth.registration_organisation_group_required = False
settings.auth.registration_requests_site = False
# Uncomment this to request the Home Phone when a user registers
settings.auth.registration_requests_home_phone = True
# Uncomment this to request the Mobile Phone when a user registers
settings.auth.registration_requests_mobile_phone = True

settings.auth.registration_link_user_to = {"staff": T("Staff")}
settings.auth.registration_link_user_to_default = "staff"

# Approval emails get sent to all admins
settings.mail.approver = "ADMIN"

# Record Approval
settings.auth.record_approval = True
# If an anonymous user creates a new org when registering then the org will be unapproved until the user is approved
settings.auth.record_approval_required_for = ("org_organisation",)

# -----------------------------------------------------------------------------
# Security Policy
settings.security.policy = 5 # Tables
settings.security.map = True

# Owner Entity
settings.auth.person_realm_human_resource_site_then_org = False

# -----------------------------------------------------------------------------
# Theme (folder to use for views/layout.html)
settings.base.theme = "CRMT2"
settings.ui.formstyle = "foundation_2col"
settings.ui.hide_report_options = False
settings.ui.read_label = "" # replaced with icon
#settings.ui.update_label = "Update"
# Uncomment to control the dataTables layout: https://datatables.net/reference/option/dom
settings.ui.datatables_dom = "<'data-info row'<'large-4 columns'i><'large-3 columns'l><'large-3 columns search'f><'large-2 columns right'>r><'dataTable_table't><'row'p>"
# Move the export_formats inside the row above it
settings.ui.datatables_initComplete = \
'''
$('.dataTables_paginate').after($('.dt-export-options'))
$('.dataTables_wrapper').prepend($('#filter-form'))
$('#filter-form').addClass('data-sort')
$('#summary-filter-form').children().first().addClass('row').wrap('<div class="data-filter"></div>')
$('#summary-filter-form').prepend($('.dataTables_wrapper .data-info'))
$('.data-filter').hide()
$('.data-sort .large-3.columns select').addClass('large-5')
$('.data-sort .search').append('<div class="row collapse"><div class="small-10 columns"></div></div>')
$('.data-sort .search .small-10').after($('.search_text')).remove()
$('.search_text').wrap('<div class="small-10 columns"></div>')
$('.data-sort .search .small-10').after('<div class="small-2 columns"><a class="button postfix" href="#"><i class="fi-magnifying-glass"></i></a></div>')
$('.data-sort .right').html('<a id="js-toggle-filters" class="button tiny right">%s</a>')
$('#js-toggle-filters').click(function(){$('.data-filter').slideToggle()})
''' % T("Filter")
# Uncomment for dataTables to use a different paging style:
settings.ui.datatables_pagingType = "bootstrap"
settings.ui.export_formats = ("xls", "xml")
# Uncomment to change the label/class of FilterForm clear buttons
settings.ui.filter_clear = "Clear"
settings.ui.hierarchy_theme = dict(css = "../themes/CRMT2",
                                   icons = True,
                                   stripes = False,
                                   )
# Uncomment to use S3MultiSelectWidget on all dropdowns (currently the Auth Registration page & LocationSelectorWidget2 listen to this)
settings.ui.multiselect_widget = "search"
settings.ui.use_button_icons = True
# Uncomment to disable responsive behavior of datatables
# - Disabled until tested
settings.ui.datatables_responsive = False
# Uncomment to modify the label of the Permalink
settings.ui.label_permalink = "Permalink"
# Uncomment to configure the LocationSelector labels for the Map button with Points
settings.label_locationselector_map_point_add = "Find on Map"
settings.label_locationselector_map_point_view = "Find on Map"

# Set Map to fill the container
#settings.gis.map_width = 1178
# Set map to be able to open Census Data & still view root labels
#settings.gis.map_height = 816
settings.gis.map_height = 750

settings.base.youtube_id = (dict(id = "introduction",
                                 title = T("Introduction"),
                                 video_id = "HR-FtR2XkBU" ),
                            dict(id = "expanding-your-coalition",
                                 title = T("Expanding Your Coalition"),
                                 video_id = "HR-FtR2XkBU" ),
                            dict(id = "mapping-vulnerable-groups",
                                 title = T("Mapping Vulnerable Groups"),
                                 video_id = "HR-FtR2XkBU" ),
                            dict(id = "mapping-hazards",
                                 title = T("Mapping Hazards"),
                                 video_id = "HR-FtR2XkBU" ),
                            dict(id = "managing-trainings",
                                 title = T("Managing Trainings"),
                                 video_id = "HR-FtR2XkBU" ),
                            dict(id = "tracking-outreach",
                                 title = T("Tracking Outreach"),
                                 video_id = "HR-FtR2XkBU" ),
                            )

# -----------------------------------------------------------------------------
# Summary Pages
settings.ui.summary = (#{"common": True,    # Added in View instead
                       # "name": "add",
                       # "widgets": [{"method": "create"}],
                       # },
                       {"common": True,
                        "name": "cms",
                        "widgets": [{"method": "cms"}]
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
                        "label": "Chart",
                        "widgets": [{"method": "report", "ajax_init": True}]
                        },
                       )

settings.search.filter_manager = False
#settings.search.filter_manager_allow_delete = False
#settings.search.filter_manager_save = "Save"
#settings.search.filter_manager_update = "Update"

# -----------------------------------------------------------------------------
# Filter forms - style for Summary pages
def filter_formstyle(row_id, label, widget, comment, hidden=False):
    return DIV(label, widget, comment,
               _id=row_id,
               _class="large-3 columns")

# -----------------------------------------------------------------------------
# L10n (Localization) settings
settings.L10n.languages = OrderedDict([
    ("en", "English"),
    ("es", "Español"),
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
settings.gis.countries = ("US",)

# Uncomment to pass Addresses imported from CSV to a Geocoder to try and automate Lat/Lon
settings.gis.geocode_imported_addresses = "google"

# Uncomment to Hide the Toolbar from the main Map
#settings.gis.toolbar = False
# Uncomment to use CMS to provide Metadata on Map Layers
settings.gis.layer_metadata = True
# Uncomment to show Clear Layers tool
settings.gis.clear_layers = "toolbar"
# Uncomment to hide the Geolocation control
settings.gis.geolocate_control = False
# Uncomment to hide the WMS GetFeatureInfo control
settings.gis.getfeature_control = False
# Uncomment to hide Layer Properties tool
settings.gis.layer_properties = False
# Uncomment to hide the Base Layers folder in the LayerTree
#settings.gis.layer_tree_base = False
# Uncomment to hide the Overlays folder in the LayerTree
#settings.gis.layer_tree_overlays = False
# Uncomment to change the label of the Overlays folder in the LayerTree
#settings.gis.label_overlays = "Places"
# Uncomment to not expand the folders in the LayerTree by default
settings.gis.layer_tree_expanded = False
# Uncomment to have custom folders in the LayerTree use Radio Buttons
settings.gis.layer_tree_radio = True
settings.gis.layers_label = "Map Layers"
# Uncomment to display the Map Legend as a floating DIV
settings.gis.legend = "float"
# Mouse Position: 'normal', 'mgrs' or None
settings.gis.mouse_position = None
# Uncomment to hide the Overview map (doesn't work with Google Maps)
settings.gis.overview = False
# Uncomment to hide the permalink control (we have our own saved maps functionality)
settings.gis.permalink = False
# Resources which can be directly added to the main map
settings.gis.poi_create_resources = \
    (dict(c="gis",
          f="poi",
          table="gis_poi",
          type="point",
          label=T("Add Point"),
          layer="Points",
          ),
     dict(c="gis",
          f="poi",
          table="gis_poi",
          type="polygon",
          label=T("Add Area"),
          layer="Areas",
          ),
     dict(c="gis",
          f="poi",
          table="gis_poi",
          type="line",
          label=T("Add Route"),
          layer="Routes",
          ),
     )
# Uncomment to rename Overlays in Layer Tree
#settings.gis.label_overlays = "Community Data"
# Uncomment to show the Print control:
# http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
settings.gis.print_button = True
# Uncomment to save a screenshot whenever a saved map is saved
settings.gis.config_screenshot = (820, 410)
# Uncomment to hide the Save control, or set to "float"
settings.gis.save = "float"
# Uncomment to hide the GeoNames search box
settings.gis.search_geonames = False
# GeoNames username
#settings.gis.geonames_username = "lacrmt"

# Don't simplify Polygons as much to retain their original shape
settings.gis.simplify_tolerance = 0.0001

# Add Person Widget
# Uncomment to hide fields in S3AddPersonWidget[2]
settings.pr.request_dob = False
settings.pr.request_gender = False
# Uncomment to show field in S3AddPersonWidget
settings.pr.request_home_phone = True

# -----------------------------------------------------------------------------
# Finance settings
settings.fin.currencies = {
    "USD" : T("United States Dollars"),
}

# =============================================================================
# Module Settings

# -----------------------------------------------------------------------------
# Human Resource Management
#
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
# Uncomment to have Staff use their Home Address as their base location, with a fallback to their site
settings.hrm.location_staff = ("person_id", "site_id")

# -----------------------------------------------------------------------------
# Organisation Registry
#
# Make Facility Types Hierarchical
settings.org.facility_types_hierarchical = True
# Make Organisation Types Hierarchical
#settings.org.organisation_types_hierarchical = True
# Make Organisation Types Multiple
#settings.org.organisation_types_multiple = True
# Make Services Hierarchical
settings.org.services_hierarchical = True
# Enable the use of Organisation Groups
settings.org.groups = "Coalition"
# Set the label for Sites
settings.org.site_label = "Location"

# -----------------------------------------------------------------------------
# projects
#
# Uncomment this to disable Sectors in projects
settings.project.sectors = False

# -----------------------------------------------------------------------------
# People
#
def user_coalition(row):
    """
        The Coalition of the user
        - required since Inline Component uses the link table
    """

    if hasattr(row, "pr_person_user"):
        row = row.pr_person_user
    try:
        user_id = row.user_id
    except:
        # not available
        return current.messages["NONE"]

    db = current.db
    table = db.auth_user
    row = db(table.id == user_id).select(table.org_group_id,
                                         limitby=(0, 1)
                                         ).first()
    if row:
        return current.s3db.org_group_represent(row.org_group_id)
    else:
        return current.messages["NONE"]

def customise_pr_person_controller(**attr):

    s3 = current.response.s3

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        s3db = current.s3db
        tablename = "pr_person"

        if r.method == "validate":
            # Can't validate image without the file
            image_field = s3db.pr_image.image
            image_field.requires = None

        elif r.interactive or r.representation == "aadata":
            # Modify list_fields
            db = current.db
            field = db.auth_user.org_group_id
            field.readable = True
            field.represent = s3db.org_group_represent
            list_fields = [(current.messages.ORGANISATION, "human_resource.organisation_id"),
                           (T("Coalition"), "user.org_group_id"),
                           "first_name",
                           #"middle_name",
                           "last_name",
                           #(T("Job Title"), "human_resource.job_title_id"),
                           (T("Place"), "human_resource.site_id"),
                           ]
            is_logged_in = current.auth.is_logged_in()
            # Don't include Email/Phone for unauthenticated users
            if is_logged_in:
                # Custom filtered component for list_fields/CRUD form
                s3db.add_components("pr_pentity",
                                    pr_contact = ({"name": "home",
                                                   "joinby": "pe_id",
                                                   "filterby": "contact_method",
                                                   "filterfor": ["HOME_PHONE"],
                                                   }),
                                    )
                list_fields.extend(((T("Email"), "email.value"),
                                    (settings.get_ui_label_mobile_phone(), "phone.value"),
                                    (T("Home Phone"), "home.value"),
                                    ))
            s3db.configure(tablename,
                           list_fields = list_fields,
                           )

        if r.interactive:
            if r.controller != "default":
                # CRUD Strings
                s3.crud_strings[tablename] = Storage(
                    label_create = T("Add Person"),
                    title_display = T("Person Details"),
                    title_list = T("People"),
                    title_update = T("Update Person Details"),
                    label_list_button = T("List People"),
                    label_delete_button = T("Delete Person"),
                    msg_record_created = T("Person added"),
                    msg_record_modified = T("Person details updated"),
                    msg_record_deleted = T("Person deleted"),
                    msg_list_empty = T("No People currently registered"))

            # Custom Form (Read/Create/Update)
            from s3 import S3Represent, S3SQLCustomForm, S3SQLInlineComponent
            if r.method in ("create", "update"):
                # Custom Widgets/Validators
                widgets = True
            else:
                widgets = False

            htable = s3db.hrm_human_resource
            htable.organisation_id.widget = None
            #site_field = htable.site_id
            #site_field.label = T("Place")
            #represent = S3Represent(lookup="org_site")
            #site_field.represent = represent
            if widgets:
                from s3 import IS_ONE_OF, S3MultiSelectWidget, S3StringWidget
                from s3layouts import S3AddResourceLink
                htable.organisation_id.widget = S3MultiSelectWidget(multiple=False)
                #site_field.widget = S3MultiSelectWidget(multiple=False)
                #site_field.requires = IS_ONE_OF(db, "org_site.site_id",
                #                                represent,
                #                                orderby = "org_site.name")
                #site_field.comment = S3AddResourceLink(c="org", f="office",
                #                                       vars={"child": "site_id"},
                #                                       label=T("Add New Place"),
                #                                       title=T("Place"),
                #                                       tooltip=T("If you don't see the Place in the list, you can add a new one by clicking link 'Add New Place'."))
                table = s3db[tablename]
                table.first_name.widget = S3StringWidget(placeholder=T("Text"))
                table.last_name.widget = S3StringWidget(placeholder=T("Text"))
                if r.method == "update":
                    # Normal Submit buttons
                    s3.crud.submit_button = T("Save & Close")
                    create_next = r.url(method="summary", id=0)
                    create_next_close = None
                else:
                    s3.crud.submit_button = T("Save & Add Another")
                    s3.crud.custom_submit = (("save_close", T("Save & Close"), "button small secondary"),
                                             #("cancel", T("Cancel"), "button small secondary cancel"),
                                             )
                    create_next = r.url(method="create")
                    create_next_close = r.url(method="summary", id=0)

                s3.cancel = A(T("Cancel"),
                              _class="button small secondary cancel",
                              _href=r.url(method="summary", id=0),
                              )

                # ImageCrop widget doesn't currently work within an Inline Form
                from gluon.validators import IS_IMAGE
                itable = s3db.pr_image
                itable.profile.default = True
                image_field = itable.image
                image_field.requires = IS_IMAGE()
                image_field.widget = None

            else:
                create_next = create_next_close = None

            hr_fields = ["organisation_id",
                         #"job_title_id",
                         #"site_id",
                         ]
            #if widgets:
            #    # Context from a Profile page?"
            #    organisation_id = current.request.get_vars.get("(organisation)", None)
            #    if organisation_id:
            #        field = s3db.hrm_human_resource.organisation_id
            #        field.default = organisation_id
            #        field.readable = field.writable = False
            #        hr_fields.remove("organisation_id")

            # S3SQLInlineComponent uses the link table, so cannot access org_group_id
            # => use a readonly virtual field instead
            from gluon import Field
            s3db.pr_person_user.org_group_id = Field.Method("org_group_id", user_coalition)

            s3_sql_custom_fields = [
                    "first_name",
                    #"middle_name",
                    "last_name",
                    S3SQLInlineComponent(
                        "human_resource",
                        name = "human_resource",
                        columns = (4,),
                        label = "",
                        multiple = False,
                        fields = hr_fields,
                    ),
                    # Not working currently
                    #S3SQLInlineComponent(
                    #    "user",
                    #    name = "user",
                    #    label = T("Coalition"),
                    #    multiple = False,
                    #    fields = [],
                    #    # Fields needed to load for Virtual Fields
                    #    extra_fields = ["user_id"],
                    #    virtual_fields = [("", "org_group_id")],
                    #),
                    S3SQLInlineComponent(
                        "image",
                        name = "image",
                        columns = (4,),
                        label = T("Photo"),
                        multiple = False,
                        fields = [("", "image")],
                        filterby = dict(field = "profile",
                                        options=[True]
                                        ),
                        ),
                    S3SQLInlineComponent("contact",
                        name = "email",
                        columns = (4,),
                        label = T("Email"),
                        multiple = False,
                        #fields = [("", "value")],
                        fields = [("", "value", S3StringWidget(columns=0,
                                                               placeholder=T("username@domain")))],
                        filterby = dict(field = "contact_method",
                                        options = "EMAIL"),
                        ),
                    S3SQLInlineComponent("contact",
                        name = "phone",
                        columns = (4,),
                        label = settings.get_ui_label_mobile_phone(),
                        multiple = False,
                        #fields = [("", "value")],
                        fields = [("", "value", S3StringWidget(columns=0,
                                                               placeholder=T("+1 800-555-1212")))],
                        filterby = dict(field = "contact_method",
                                        options = "SMS"),
                        ),
                    S3SQLInlineComponent("contact",
                        name = "home",
                        columns = (4,),
                        label = T("Home Phone"),
                        multiple = False,
                        #fields = [("", "value")],
                        fields = [("", "value", S3StringWidget(columns=0,
                                                               placeholder=T("+1 800-555-1212")))],
                        filterby = dict(field = "contact_method",
                                        options = "HOME_PHONE"),
                        ),
                    ]

            crud_form = S3SQLCustomForm(*s3_sql_custom_fields)

            s3db.configure(tablename,
                           create_next = create_next,
                           create_next_close = create_next_close,
                           crud_form = crud_form,
                           delete_next = r.url(method="summary", id=0),
                           # Hide Open & Delete dataTable action buttons
                           deletable = False,
                           editable = False,
                           icon = "person", # Used for Create Icon in Summary View
                           # Don't include a Create form in 'More' popups
                           #listadd = False if r.method=="datalist" else True,
                           update_next = r.url(method="summary", id=0),
                           )

        return True
    s3.prep = custom_prep

    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        if r.interactive and isinstance(output, dict):
            # All users just get "Open"
            #actions = [dict(label=str(T("Open")),
            #                _class="action-btn",
            #                url=URL(c="pr", f="person",
            #                        args=["[id]", "read"]))
            #           ]
            #s3.actions = actions
            if "form" in output:
                output["form"].add_class("pr_person")
            elif "item" in output and hasattr(output["item"], "add_class"):
                output["item"].add_class("pr_person")

        return output
    s3.postp = custom_postp

    # Remove rheader
    attr["rheader"] = None

    return attr

settings.customise_pr_person_controller = customise_pr_person_controller

# -----------------------------------------------------------------------------
def default_coalition_filter(selector, tablename=None):
    """
        Default filter for coalitions (callback)
    """

    auth = current.auth
    org_group_id = auth.is_logged_in() and auth.user.org_group_id
    if org_group_id:
        return org_group_id
    else:
        # Filter to all Coalitions
        gtable = current.s3db.org_group
        rows = current.db(gtable.deleted == False).select(gtable.id)
        return [row.id for row in rows]

# -----------------------------------------------------------------------------
# Activities
#
def customise_project_activity_controller(**attr):

    if "summary" in current.request.args:
        settings.gis.toolbar = False
        from s3 import s3_set_default_filter
        s3_set_default_filter("activity_group.group_id",
                              default_coalition_filter,
                              tablename = "project_activity")

    # Custom PreP
    s3 = current.response.s3
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        s3db = current.s3db
        tablename = "project_activity"
        table = s3db[tablename]

        s3.crud_strings[tablename].label_create = T("Add Activity")

        from s3 import S3StringWidget
        table.name.widget = S3StringWidget(placeholder=T("Text"))
        table.comments.widget = S3StringWidget(placeholder=T("Comments"), textarea=True)
        if r.method == "update":
            # Normal Submit buttons
            s3.crud.submit_button = T("Save & Close")
            create_next = r.url(method="summary", id=0)
            create_next_close = None
        else:
            s3.crud.submit_button = T("Save & Add Another")
            s3.crud.custom_submit = (("save_close", T("Save & Close"), "button small secondary"),
                                     #("cancel", T("Cancel"), "button small secondary cancel"),
                                     )
            create_next = r.url(method="create")
            create_next_close = r.url(method="summary", id=0)
        s3.cancel = A(T("Cancel"),
                      _class="button small secondary cancel",
                      _href=r.url(method="summary", id=0),
                      )

        method = r.method
        representation = r.representation
        if method == "summary" or representation == "aadata":
            # Modify list_fields for interactive views
            list_fields = ["date",
                           "name",
                           "activity_activity_type.activity_type_id",
                           "activity_group.group_id",
                           (T("Address"), "location_id"),
                           "location_id$addr_postcode",
                           "person_id",
                           (T("Number of People"), "beneficiary.value"),
                           "comments",
                           ]

            s3db.configure(tablename,
                           icon = "activity", # Used for Create Icon in Summary View
                           list_fields = list_fields,
                           )

        table.location_id.represent = s3db.gis_LocationRepresent(address_only=True)
        if r.interactive or representation == "json" or \
                            representation == "plain":
            # CRUD Strings / Represent
            table.date.label = T("Date")
            table.name.label = T("Activity Name")
            table.comments.label = T("Description")

            # Custom Form (Read/Create/Update inc embedded Summary)
            from s3 import S3SQLCustomForm, S3SQLInlineComponent

            table.person_id.comment = None

            bttable = s3db.project_beneficiary_type
            total = current.db(bttable.name == "Total").select(bttable.parameter_id,
                                                               limitby=(0, 1)).first()
            if total:
                parameter_id = total.parameter_id
            else:
                parameter_id = None
            crud_form = S3SQLCustomForm(
                "date",
                "name",
                S3SQLInlineComponent(
                    "activity_activity_type",
                    columns = (4,),
                    fields = [("", "activity_type_id")],
                    label = T("Activity Type"),
                    multiple = False,
                ),
                S3SQLInlineComponent(
                    "activity_group",
                    columns = (4,),
                    fields = [("", "group_id")],
                    label = T("Coalition"),
                    multiple = False,
                ),
                "location_id",
                "person_id",
                S3SQLInlineComponent(
                    "activity_organisation",
                    columns = (4,),
                    label = T("Participating Organizations"),
                    fields = [("", "organisation_id")],
                ),
                S3SQLInlineComponent(
                    "beneficiary",
                    columns = (4,),
                    label = T("Number of People Reached"),
                    link = False,
                    multiple = False,
                    fields = [("", "value")],
                    filterby = dict(field = "parameter_id",
                                    options = parameter_id
                                    ),
                ),
                S3SQLInlineComponent(
                    "document",
                    columns = (4,),
                    name = "file",
                    label = T("Files"),
                    fields = [("", "file"),
                              ],
                    comment =  DIV(_class="tooltip",
                                   _title="%s|%s" %
                                          (T("Files"),
                                           T("Upload Photos, Promotional Material, Documents or Reports related to the Activity")
                                           )
                                   )
                ),
                "comments",
            )

            s3db.configure(tablename,
                           create_next = create_next,
                           create_next_close = create_next_close,
                           crud_form = crud_form,
                           delete_next = r.url(method="summary", id=0),
                           update_next = r.url(method="summary", id=0),
                           )

            if method in ("summary", "report"):
                from s3 import S3OptionsFilter, S3DateFilter
                filter_widgets = [S3OptionsFilter("activity_group.group_id",
                                                  represent = "%(name)s",
                                                  header = True,
                                                  ),
                                  S3OptionsFilter("activity_activity_type.activity_type_id",
                                                  # Doesn't allow Translation
                                                  #represent = "%(name)s",
                                                  header = True,
                                                  ),
                                  S3DateFilter("date",
                                               label = None,
                                               hide_time = True,
                                               input_labels = {"ge": "From", "le": "To"}
                                               )
                                  ]

                # @ToDo: Month/Year Lazy virtual fields (like in PM tool)
                report_fields = ["activity_activity_type.activity_type_id",
                                 "activity_group.group_id",
                                 "location_id$L3",
                                 ]

                report_options = Storage(
                    rows = report_fields,
                    cols = [],
                    fact = [(T("Number of Activities"), "count(name)"),
                            (T("Number of People"), "sum(beneficiary.value)"),
                            ],
                    defaults = Storage(rows="activity_activity_type.activity_type_id",
                                       #cols="activity_group.group_id",
                                        fact="count(name)",
                                       totals=True,
                                       chart = "barchart:rows",
                                       table = "collapse",
                                       )
                    )

                s3db.configure(tablename,
                               # Hide Open & Delete dataTable action buttons
                               deletable = False,
                               editable = False,
                               filter_formstyle = filter_formstyle,
                               filter_widgets = filter_widgets,
                               report_options = report_options,
                               )

            if method in ("create", "update", "summary"):
                # Custom Widgets/Validators
                from s3 import IS_LOCATION_SELECTOR2, S3LocationSelectorWidget2, S3MultiSelectWidget

                s3db.project_activity_activity_type.activity_type_id.widget = S3MultiSelectWidget(multiple=False)
                s3db.project_activity_group.group_id.widget = S3MultiSelectWidget(multiple=False)
                s3db.project_activity_organisation.organisation_id.widget = S3MultiSelectWidget(multiple=False)

                field = table.location_id
                field.label = "" # Gets replaced by widget
                levels = ("L3",)
                field.requires = IS_LOCATION_SELECTOR2(levels=levels)
                field.widget = S3LocationSelectorWidget2(levels=levels,
                                                         hide_lx=False,
                                                         reverse_lx=True,
                                                         show_address=True,
                                                         show_postcode=True,
                                                         )

        return True
    s3.prep = custom_prep

    # Remove rheader
    attr["rheader"] = None

    return attr

settings.customise_project_activity_controller = customise_project_activity_controller

def customise_project_activity_type_controller(**attr):

    from s3 import S3SQLCustomForm
    current.s3db.configure("project_activity_type",
                           crud_form = S3SQLCustomForm("name",
                                                       "comments"),
                           )

    return attr

settings.customise_project_activity_type_controller = customise_project_activity_type_controller

# -----------------------------------------------------------------------------
# Organisations
#
def org_facility_types(row):
    """
        The Types of the Facility
        - required since we can't have a component within an Inline Component
        UNUSED
    """

    if hasattr(row, "org_facility"):
        row = row.org_facility
    try:
        site_id = row.site_id
    except:
        # not available
        return current.messages["NONE"]

    s3db = current.s3db
    table = s3db.org_facility_type
    ltable = s3db.org_site_facility_type
    query = (ltable.site_id == site_id) & \
            (ltable.facility_type_id == table.id)
    rows = current.db(query).select(table.name)
    return ",".join([r.name for r in rows])

# -----------------------------------------------------------------------------
def org_organisation_postprocess(form):
    """
        onaccept for the Custom Form:
        - replace the name of the Fac with the name of the Org
    """

    form_vars = form.vars
    organisation_id = form_vars.get("id", None)
    name = form_vars.get("name", None)
    ftable = current.s3db.org_facility
    current.db(ftable.organisation_id == organisation_id).update(name = name)

# -----------------------------------------------------------------------------
def customise_org_organisation_controller(**attr):

    # Filter defaults
    if "summary" in current.request.args:
        settings.gis.toolbar = False
        from s3 import s3_set_default_filter
        s3_set_default_filter("org_group_membership.group_id",
                              default_coalition_filter,
                              tablename = "org_organisation")

    # Custom PreP
    s3 = current.response.s3
    standard_prep = s3.prep

    def custom_prep(r):

        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        s3db = current.s3db
        tablename = "org_organisation"
        table = s3db[tablename]

        method = r.method
        if method == "validate":
            # Need to override .requires here too
            current.s3db.org_facility.location_id.requires = None

        elif method == "profile":

            # Profile page configuration
            profile_layout = OrganisationProfileLayout()
            places_widget = dict(label = "Location(s)",
                                 label_create = "Add Location",
                                 type = "datalist",
                                 tablename = "org_facility",
                                 context = "organisation",
                                 list_fields = ["location_id",
                                                ],
                                 list_layout = profile_layout,
                                 )

            s3db.configure(tablename,
                           profile_cols = 1,
                           profile_update = "visible",
                           profile_widgets = [places_widget,
                                              ],
                           )

        elif method == "summary" or r.representation == "aadata":

            # Data table configuration
            list_fields = ["id",
                           "name",
                           (T("Coalition"), "group_membership.group_id"),
                           (T("Location(s)"), "facility.location_id"),
                           #"facility.location_id$addr_postcode",
                           (T("Sectors"), "sector_organisation.sector_id"),
                           (T("Services"), "service_organisation.service_id"),
                           (T("Phone"), "phone"),
                           "website",
                           "comments",
                           ]

            s3db.configure(tablename,
                           # Hide Open & Delete dataTable action buttons
                           deletable = False,
                           editable = False,
                           list_fields = list_fields,
                           )

        if (r.interactive or r.representation == "json") and not r.component:

            # CRUD Strings / Represent
            s3.crud_strings[tablename].update(
                label_create = T("Add Organization"),
                title_report = T("Organization Matrix"),
                title_update = T("Update Organization"),
                )
            table.logo.readable = table.logo.writable = False
            #table.name.label = T("Organization Name")
            table.phone.label = T("Phone")

            from s3 import S3StringWidget
            table.name.widget = S3StringWidget(placeholder=T("Text"))
            table.phone.widget = S3StringWidget(placeholder=T("+1 800-555-1212"))
            table.website.widget = S3StringWidget(placeholder=T("URL"), prefix="http://")
            s3db.pr_contact.value.widget = S3StringWidget(placeholder=T("username"), prefix="@")
            table.comments.widget = S3StringWidget(placeholder=T("Comments"), textarea=True)
            if r.method == "update":
                # Normal Submit buttons
                s3.crud.submit_button = T("Save & Close")
                create_next = r.url(method="summary", id=0)
                create_next_close = None
            else:
                s3.crud.submit_button = T("Save & Add Another")
                s3.crud.custom_submit = (("save_close", T("Save & Close"), "button small secondary"),
                                         #("cancel", T("Cancel"), "button small secondary cancel"),
                                         )
                create_next = r.url(method="create")
                create_next_close = r.url(method="summary", id=0)
            s3.cancel = A(T("Cancel"),
                          _class="button small secondary cancel",
                          _href=r.url(method="summary", id=0),
                          )

            if method in ("summary", "report"):

                # Filter form
                from s3 import S3Represent, S3OptionsFilter, S3TextFilter, S3HierarchyFilter
                filter_widgets = [S3TextFilter(["name",
                                                "group_membership.group_id",
                                                "sector_organisation.sector_id",
                                                "service_organisation.service_id",
                                                "comments"
                                                ],
                                                label = "",
                                                _class = "search_text",
                                                _placeholder = T("Search"),
                                                ),
                                  S3OptionsFilter("group_membership.group_id",
                                                  represent = "%(name)s",
                                                  header = True,
                                                  ),
                                  S3OptionsFilter("sector_organisation.sector_id",
                                                  label = T("Sector"),
                                                  header = True,
                                                  ),
                                  S3HierarchyFilter("service_organisation.service_id",
                                                    label = T("Service"),
                                                    header = True,
                                                    represent = S3Represent(lookup="org_service",
                                                                            # Disable the Hierarchy here as ugly
                                                                            #hierarchy = True,
                                                                            translate = True),
                                                    ),
                                  #S3HierarchyFilter("organisation_organisation_type.organisation_type_id",
                                  #                  label = T("Type of Organization"),
                                  #                  #multiple = False,
                                  #                  )
                                  ]

                # Report Options
                report_fields = [# Only 1 Axis so use singular name
                                 #"name",
                                 (T("Coalition"), "group_membership.group_id"),
                                 (T("Sector"), "sector_organisation.sector_id"),
                                 (T("Service"), "service_organisation.service_id"),
                                 ]

                report_options = Storage(
                    rows = report_fields,
                    cols = [],
                    fact = [(T("Number of Organizations"), "count(name)")],
                    defaults = Storage(rows = "sector_organisation.sector_id",
                                       #cols = "service_organisation.service_id",
                                       fact = "count(name)",
                                       totals = True,
                                       chart = "barchart:rows",
                                       table = "collapse",
                                       )
                    )

                s3db.configure(tablename,
                               filter_formstyle = filter_formstyle,
                               filter_widgets = filter_widgets,
                               icon = "organization", # Used for Create Icon in Summary View
                               report_options = report_options,
                               # No Map for Organisations
                               #summary = [s for s in settings.ui.summary if s["name"] != "map"],
                               )

            # Custom CRUD Form
            if not current.auth.is_logged_in():

                # Anonymous user creating Org: Keep Simple
                from s3 import S3SQLCustomForm
                crud_form = S3SQLCustomForm("name",
                                            "website",
                                            "comments",
                                            )
                s3db.configure(tablename,
                               crud_form = crud_form,
                               )

            elif method in ("read", "create", "update", "summary", "import", "profile"):

                from s3 import S3Represent, S3SQLCustomForm, S3SQLInlineComponent, \
                               S3SQLInlineComponentMultiSelectWidget, S3SQLInlineLink
                form_fields = ["name",
                               "logo",
                               S3SQLInlineComponent(
                                    "group_membership",
                                    columns = (3, 3),
                                    label = T("Coalition"),
                                    fields = [("", "group_id"),
                                              ("", "status_id"),
                                              ],
                                    ),
                               S3SQLInlineComponentMultiSelectWidget(
                                    "sector",
                                    columns = 4,
                                    label = T("Sectors"),
                                    field = "sector_id",
                                    ),
                               S3SQLInlineLink(
                                    "service",
                                    columns = 4,
                                    label = T("Services"),
                                    field = "service_id",
                                    leafonly = False,
                                    widget = "hierarchy",
                                    ),
                               #S3SQLInlineComponent(
                               #     "resource",
                               #     label = T("Organization's Resources"),
                               #     fields = ["parameter_id",
                               #               "value",
                               #               "comments",
                               #               ],
                               #     ),
                               "phone",
                               "website",
                               S3SQLInlineComponent(
                                    "contact",
                                    name = "twitter",
                                    columns = (10,),
                                    fields = [("", "value")],
                                    filterby = dict(field = "contact_method",
                                                    options = "TWITTER"
                                                    ),
                                    label = T("Twitter"),
                                    multiple = False,
                                    ),
                               "comments",
                               ]

                # Allow free-text in Phone
                table.phone.requires = None

                from s3 import S3MultiSelectWidget

                # Organisation's Resources
                #s3db.org_resource.parameter_id.widget = S3MultiSelectWidget(multiple=False)

                # Services show hierarchy in dataTables represent
                s3db.org_service_organisation.service_id.represent = S3Represent(lookup="org_service",
                                                                                 hierarchy = True,
                                                                                 translate = True)

                # Coalition Memberships
                mtable = s3db.org_group_membership
                mtable.group_id.widget = S3MultiSelectWidget(multiple=False)
                #from s3layouts import S3AddResourceLink
                #mtable.status_id.comment = S3AddResourceLink(c="org",
                #                                             f="group_membership_status",
                #                                             vars={"child": "status_id"},
                #                                             title=T("Add New Status"))
                mtable.status_id.comment = T("Status of the Organization in the Coalition")
                mtable.status_id.widget = S3MultiSelectWidget(multiple=False,
                                                              create=dict(c="org",
                                                                          f="group_membership_status",
                                                                          label=str(T("Add New Status")),
                                                                          parent="group_membership",
                                                                          child="status_id"
                                                                          ))

                # Organization's Places (create only once profile is ready)
                #if method in ("create", "summary"):
                if method != "profile":
                    form_fields.insert(-1,
                                       # Not fully ready yet
                                       S3SQLInlineComponent("facility",
                                                #label = T("Address"),
                                                label = T("Location(s)"),
                                                fields = [("", "location_id"),
                                                        ],
                                                # @ToDo: Fix
                                                multiple = False,
                                       ))

                    ftable = s3db.org_facility
                    ftable.name.default = "TEMP" # replace in form postprocess
                    field = ftable.location_id
                    field.label = T("Address")
                    field.represent = s3db.gis_LocationRepresent(address_only=True)
                    from s3 import IS_LOCATION_SELECTOR2, S3LocationSelectorWidget2
                    levels = ("L3",)
                    field.requires = IS_LOCATION_SELECTOR2(levels=levels)
                    field.widget = S3LocationSelectorWidget2(levels=levels,
                                                             hide_lx=False,
                                                             reverse_lx=True,
                                                             show_address=True,
                                                             show_postcode=True,
                                                             )

                # Human resource (currently only in read because S3AddPersonWidget
                # not working inside inline component => consider HRAutoComplete
                # with AddResourceLink instead?)
                if r.record and method not in ("update", "profile"):

                    hrtable = s3db.hrm_human_resource
                    hrtable.person_id.widget = None
                    hrtable.site_id.label = T("Place")

                    hr_fields = ["person_id",
                                 "site_id",
                                 #"job_title_id",
                                 #"email",
                                 #"phone",
                                 ]

                    #if method in ("update", "profile"):
                    #    # Filter the options for site_id in the organisation
                    #    # contacts inline component to just the sites of this
                    #    # organisation
                    #    from s3 import IS_ONE_OF
                    #    auth = current.auth
                    #    realms = auth.permission.permitted_realms("hrm_human_resource",
                    #                                              method="create")
                    #    instance_types = auth.org_site_types
                    #    hrtable.site_id.requires = IS_ONE_OF(current.db, "org_site.site_id",
                    #                                         label=s3db.org_site_represent,
                    #                                         orderby="org_site.name",
                    #                                         filterby="organisation_id",
                    #                                         filter_opts=(r.id,),
                    #                                         instance_types=instance_types,
                    #                                         realms=realms,
                    #                                         not_filterby="obsolete",
                    #                                         not_filter_opts=(True,)
                    #                                         )

                    form_fields.insert(6, S3SQLInlineComponent(
                        "human_resource",
                        label = T("Organization's Contacts"),
                        fields = hr_fields,
                    ))

                elif r.record:
                    s3.cancel = r.url(method="read")

                crud_form = S3SQLCustomForm(*form_fields,
                                            postprocess = org_organisation_postprocess)

                s3db.configure(tablename,
                               create_next = create_next,
                               create_next_close = create_next_close,
                               crud_form = crud_form,
                               delete_next = r.url(method="summary", id=0),
                               update_next = r.url(method="summary", id=0),
                               )

        return True
    s3.prep = custom_prep

    # Uncomment this to use the profile page to update organisations:
    #standard_postp = s3.postp
    #def custom_postp(r, output):
    #    # Call standard postp
    #    if callable(standard_postp):
    #        output = standard_postp(r, output)
    #    if r.record and isinstance(output, dict):
    #        buttons = output.get("buttons")
    #        if buttons and "edit_btn" in buttons:
    #            # Override Edit-button (to go to the profile page)
    #            from s3 import S3CRUD
    #            buttons["edit_btn"] = S3CRUD.crud_button(
    #                                        current.messages.UPDATE,
    #                                        icon="icon-edit",
    #                                        _href=r.url(method="profile"),
    #                                        _id="edit-btn",
    #                                        )
    #    return output
    #s3.postp = custom_postp

    # Remove rheader
    attr["rheader"] = None

    return attr

settings.customise_org_organisation_controller = customise_org_organisation_controller

# -----------------------------------------------------------------------------
# Coalitions (org_group)
#
def customise_org_group_controller(**attr):

    s3 = current.response.s3

    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        if r.interactive:
            from s3 import IS_LOCATION_SELECTOR2, S3LocationSelectorWidget2
            table = current.s3db.org_group
            table.name.label = T("Coalition Name")
            field = table.location_id
            field.label = "" # Gets replaced by widget
            levels = ("L2",)
            field.requires = IS_LOCATION_SELECTOR2(levels = levels)
            field.widget = S3LocationSelectorWidget2(levels = levels,
                                                     points = False,
                                                     polygons = True,
                                                     )

        return True
    s3.prep = custom_prep

    attr["rheader"] = None
    return attr

settings.customise_org_group_controller = customise_org_group_controller

#-----------------------------------------------------------------------------
# Places (org_facility)
#
def facility_onaccept(form):
    """
        Custom onaccept for Imports:
        * Auto-lookup of Coalition based on LatLon
    """

    # Check if we already have a Coalition
    db = current.db
    s3db = current.s3db
    site_id = form.vars.site_id
    ltable = s3db.org_site_org_group
    exists = db(ltable.site_id == site_id).select(ltable.id, limitby=(0, 1))
    if not exists:
        # Have we got a LatLon?
        location_id = form.vars.location_id
        if location_id:
            gtable = db.gis_location
            location = db(gtable.id == location_id).select(gtable.lat,
                                                           gtable.lon,
                                                           limitby=(0, 1)
                                                           ).first()
            if location and location.lat is not None \
                        and location.lon is not None:
                # Read all the Coalition Polygons
                ctable = db.org_group
                query = (ctable.deleted == False) & \
                        (ctable.location_id == gtable.id)
                polygons = db(query).select(ctable.id,
                                            gtable.wkt,
                                            cache=s3db.cache,
                                            )
                match = False
                from shapely.geometry import point
                from shapely.wkt import loads as wkt_loads
                try:
                    # Enable C-based speedups available from 1.2.10+
                    from shapely import speedups
                    speedups.enable()
                except:
                    current.log.info("S3GIS",
                                     "Upgrade Shapely for Performance enhancements")
                pnt = point.Point(location.lon, location.lat)
                for p in polygons:
                    wkt = p[gtable].wkt
                    if not wkt:
                        continue
                    poly = wkt_loads(wkt)
                    match = pnt.intersects(poly)
                    if match:
                        break
                if match:
                    group_id = p[ctable].id
                    ltable.insert(group_id = group_id,
                                  site_id = site_id,
                                  )
                    # Also update the Organisation
                    stable = db.org_site
                    site = db(stable.id == site_id).select(stable.organisation_id,
                                                           limitby = (0, 1)
                                                           ).first()
                    if not site:
                        return
                    organisation_id = site.organisation_id
                    ltable = db.org_group_membership
                    query = (ltable.organisation_id == organisation_id) & \
                            (ltable.group_id == group_id)
                    exists = db(query).select(ltable.id,
                                              limitby=(0, 1))
                    if not exists:
                        stable = db.org_group_membership_status
                        status = db(stable.name == "Located within Coalition").select(stable.id,
                                                                                      cache = s3db.cache,
                                                                                      limitby = (0, 1)
                                                                                      ).first()
                        if status:
                            status_id = status.id
                        else:
                            # Prepop failed or Status deleted/renamed
                            status_id = None
                        ltable.insert(group_id = group_id,
                                      organisation_id = organisation_id,
                                      status_id = status_id,
                                      )

    # Normal onaccept:
    # Update Affiliation, record ownership and component ownership
    from s3db.org import S3FacilityModel
    S3FacilityModel.org_facility_onaccept(form)

# Ensure callback is accessible to CLI Imports as well as those going via Controller
settings.base.import_callbacks = {"org_facility": {"onaccept": facility_onaccept,
                                                   },
                                  }

#-----------------------------------------------------------------------------
def customise_org_facility_controller(**attr):

    if "summary" in current.request.args:
        settings.gis.toolbar = False
        from s3 import s3_set_default_filter
        s3_set_default_filter("site_org_group.group_id",
                              default_coalition_filter,
                              tablename = "org_facility")

    # Custom PreP
    s3 = current.response.s3
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        s3db = current.s3db
        tablename = "org_facility"
        table = s3db[tablename]

        method = r.method
        representation = r.representation
        if method == "summary" or representation == "aadata":
            # Modify list_fields
            list_fields = ["name",
                           (T("Type of Place"), "site_facility_type.facility_type_id"),
                           "organisation_id",
                           "site_org_group.group_id",
                           (T("Address"), "location_id"),
                           "location_id$addr_postcode",
                           "contact",
                           "phone1",
                           "email",
                           "comments",
                           ]

            s3db.configure(tablename,
                           list_fields = list_fields,
                           # Override std summary page
                           summary = settings.ui.summary,
                           )

        table.location_id.represent = s3db.gis_LocationRepresent(address_only=True)
        if r.interactive or representation == "json":
            # CRUD Strings / Represent
            table.name.label = T("Place Name")
            table.phone1.label = T("Phone")

            s3.crud_strings[tablename] = Storage(
                label_create = T("Add Place"),
                title_display = T("Place Details"),
                title_list = T("Places"),
                title_update = T("Update Place"),
                label_list_button = T("List Places"),
                label_delete_button = T("Remove Place"),
                msg_record_created = T("Place added"),
                msg_record_modified = T("Place updated"),
                msg_record_deleted = T("Place removed"),
                msg_list_empty = T("No Places currently recorded"))

            # Custom Form (Read/Create/Update inc embedded Summary)
            from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink
            if method in ("create", "update", "summary", "import"):
                # Custom Widgets/Validators
                from s3 import IS_LOCATION_SELECTOR2, S3LocationSelectorWidget2, S3MultiSelectWidget

                # Allow free-text in Phone
                table.phone1.requires = None

                field = table.location_id
                field.label = "" # Gets replaced by widget
                levels = ("L3",)
                field.requires = IS_LOCATION_SELECTOR2(levels=levels)
                field.widget = S3LocationSelectorWidget2(levels=levels,
                                                         hide_lx=False,
                                                         reverse_lx=True,
                                                         show_address=True,
                                                         show_postcode=True,
                                                         )

                table.organisation_id.widget = S3MultiSelectWidget(multiple=False)
                s3db.org_site_org_group.group_id.widget = S3MultiSelectWidget(multiple=False)

            # Custom Crud Form
            crud_form = S3SQLCustomForm("name",
                                        S3SQLInlineLink(
                                            "facility_type",
                                            label = T("Type of Place"),
                                            field = "facility_type_id",
                                            widget = "hierarchy",
                                            ),
                                        "organisation_id",
                                        S3SQLInlineComponent(
                                            "site_org_group",
                                            label = T("Coalition"),
                                            fields = [("", "group_id")],
                                            multiple = False,
                                            ),
                                        "location_id",
                                        #S3SQLInlineComponent(
                                        #    "human_resource",
                                        #    label = T("Place's Contacts"),
                                        #    fields = ["person_id",
                                        #              #"job_title_id",
                                        #              #"email",
                                        #              #"phone",
                                        #              ],
                                        #),
                                        # Can't have Components of Components Inline, so just use simple fields
                                        "contact",
                                        "phone1",
                                        "email",
                                        S3SQLInlineComponent(
                                            "document",
                                            name = "file",
                                            label = T("Files"),
                                            fields = [("", "file"),
                                                      #"comments",
                                                      ],
                                            ),
                                        "comments",
                                        )

            s3db.configure(tablename,
                           crud_form = crud_form,
                           )

            if method in ("summary", "report"):
                from s3 import S3OptionsFilter, S3TextFilter, S3HierarchyFilter
                filter_widgets = [S3TextFilter(["name",
                                                "site_org_group.group_id",
                                                "site_facility_type.facility_type_id",
                                                "organisation_id",
                                                "location_id",
                                                "contact",
                                                "phone1",
                                                "email",
                                                "comments"
                                                ],
                                                label = T("Search"),
                                               ),
                                  S3OptionsFilter("site_org_group.group_id",
                                                  represent = "%(name)s",
                                                  header = True,
                                                  ),
                                  S3HierarchyFilter("site_facility_type.facility_type_id",
                                                    label = T("Type of Place"),
                                                    ),
                                  S3OptionsFilter("organisation_id",
                                                  represent = "%(name)s",
                                                  header = True,
                                                  ),
                                  ]

                report_fields = [#"name",
                                 (T("Type of Place"), "site_facility_type.facility_type_id"),
                                 "site_org_group.group_id",
                                 "location_id$L3",
                                 "organisation_id",
                                 ]

                report_options = Storage(
                    rows = report_fields,
                    cols = [],
                    fact = [(T("Number of Places"), "count(name)")],
                    defaults = Storage(rows = "site_facility_type.facility_type_id",
                                       #cols = "site_org_group.group_id",
                                       fact = "count(name)",
                                       chart = "barchart:rows",
                                       table = "collapse",
                                       totals = True,
                                       )
                    )

                s3db.configure(tablename,
                               # Hide Open & Delete dataTable action buttons
                               editable = False,
                               deletable = False,
                               filter_formstyle = filter_formstyle,
                               filter_widgets = filter_widgets,
                               report_options = report_options,
                               )

        elif representation == "plain":
            # Map Popups
            table.location_id.label = T("Address")
            table.location_id.represent = s3db.gis_LocationRepresent(address_only=True)
            table.organisation_id.comment = ""
            s3.crud_strings[tablename].title_display = T("Place Details")
            # Disable Open on Places.
            # - Not sure why this was done & have now been requested to undo it.
            #s3db.configure(tablename,
            #               popup_url = "",
            #               )

        return True
    s3.prep = custom_prep

    # Override Custom Map Popup in default PostP
    s3.postp = None

    # Remove rheader
    attr["rheader"] = None

    return attr

settings.customise_org_facility_controller = customise_org_facility_controller

# -----------------------------------------------------------------------------
# Shared Stories
#
def cms_post_list_layout(list_id, item_id, resource, rfields, record):
    """
        Custom dataList item renderer for Shared Stories

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["cms_post.id"]

    raw = record._row
    title = record["cms_post.title"]
    body = record["cms_post.body"]
    comments = raw["cms_post.comments"] or ""
    #if comments:
    #    # Format them, if-formatted
    #    comments = record["cms_post.comments"]
    author = record["cms_post.created_by"]
    coalition = raw["auth_user.org_group_id"] or ""
    if coalition:
        # Use Represent
        coalition = record["auth_user.org_group_id"]
    date = record["cms_post.created_on"]
    image = raw["doc_image.file"] or ""
    if image:
        image = IMG(_src="/%s/default/download/%s" % \
                        (current.request.application, image))
    tag_ids = raw["cms_tag_post.tag_id"]
    if tag_ids:
        tags = record["cms_tag_post.tag_id"]
        if isinstance(tag_ids, (tuple, list)):
            tags = tags.xml().split(", ")
        else:
            tag_ids = (tag_ids,)
            tags = (tags,)
        _tags = []
        index = 0
        for tag_id in tag_ids:
            _tags.append(A(tags[index],
                           _href=URL(c="cms", f="post",
                                     args="datalist",
                                     vars={"tag_post.tag_id__belongs": tag_id}),
                           ).xml())
            index += 1
        tags = H6(XML(s3_unicode(T("More about %(tags)s") % dict(tags=" | ".join(_tags)))))
    else:
        tags = ""

    item = TAG.article(H2(A(title,
                            _href=URL(c="cms", f="post",
                                      args=[record_id], #"datalist",
                                      #vars={"~.id": record_id},
                                      ),
                            ),
                          ),
                       H6(author,
                          BR(),
                          coalition,
                          BR(),
                          date,
                          ),
                       image,
                       P(body),
                       P(comments),
                       tags,
                       )

    return DIV(item,
               HR(),
               )

def customise_cms_post_controller(**attr):

    s3 = current.response.s3

    get_vars = current.request.get_vars
    mod = get_vars.get("module")
    if not mod:
        layer = get_vars.get("layer_id")
        if not layer:
            from s3 import FS
            # Hide Posts linked to Modules and Maps
            s3.filter = (FS("post_module.module") == None) & (FS("post_layer.layer_id") == None)
            # Only show Blog Posts
            #s3.filter = (FS("cms_post.series_id$name") == "Blog")

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        s3db = current.s3db
        tablename = "cms_post"
        table = s3db[tablename]

        # Look up the Blog series
        #stable = s3db.cms_series
        #try:
        #    blog = current.db(stable.name == "Blog").select(stable.id,
        #                                                    limitby=(0, 1),
        #                                                    cache = s3db.cache,
        #                                                    ).first().series_id
        #except:
        #    # Prepop not run - e.g. just testing Theme
        #    pass
        #else:
        #    table.series_id.default = blog

        s3.crud_strings[tablename] = Storage(
            label_create = T("Add Story"),
            title_display = T("Story Details"),
            title_list = T("Stories"),
            title_update = T("Update Story Details"),
            label_list_button = T("List Stories"),
            label_delete_button = T("Delete Story"),
            msg_record_created = T("Story added"),
            msg_record_modified = T("Story details updated"),
            msg_record_deleted = T("Story deleted"),
            msg_list_empty = T("No Stories currently registered"))

        # Custom Form
        from gluon import IS_NOT_EMPTY
        from s3 import S3ImageCropWidget, S3StringWidget, S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink
        # Not yet working Inline
        #s3db.doc_image.file.widget = S3ImageCropWidget((400, 240))
        s3db.doc_image.file.widget = None
        s3db.doc_image.file.requires = None
        table.title.requires = IS_NOT_EMPTY()
        table.body.label = T("Challenges")
        table.body.widget = S3StringWidget(placeholder=T("In building your community's resilience, what particular challenges did you face? (Up to 200 words)"),
                                           textarea=True)
        table.comments.label = T("Lessons")
        table.comments.widget = S3StringWidget(placeholder=T("What strategies, tactics, or lessons did you learn? (Up to 200 words)"),
                                               textarea=True)
        crud_form = S3SQLCustomForm("title",
                                    S3SQLInlineLink("tag",
                                                    cols = 4,
                                                    label = T("Topic(s)"),
                                                    field = "tag_id",
                                                    translate = True,
                                                    ),
                                    "body",
                                    "comments",
                                    S3SQLInlineComponent(
                                            "image",
                                            #name = "image",
                                            columns = (4,),
                                            fields = [("", "file"),
                                                      #"comments",
                                                      ],
                                            ),
                                            label = T("Add an Image"),
                                            multiple = False,
                                    )
        s3.cancel = A(T("Cancel"),
                      _class="button small secondary cancel",
                      _href=r.url(method="datalist", id=0),
                      )

        # Tweak DataList options
        s3.dl_no_header = True
        list_fields = ("title",
                       "body",
                       "comments",
                       "date",
                       "created_on",
                       "created_by",
                       "created_by$org_group_id",
                       "image.file",
                       "tag_post.tag_id",
                       )

        settings.L10n.date_format = "%B %d, %Y"
        from s3 import S3DateTime, s3_auth_user_represent_name
        table.created_by.represent = s3_auth_user_represent_name
        table.created_on.represent = lambda dt: S3DateTime.date_represent(dt, utc=True)

        from s3 import S3OptionsFilter
        filter_widgets = (
            S3OptionsFilter("tag_post.tag_id",
                            label = "",
                            cols = 1,
                            multiple = False,
                            ),
            )

        # Filter Widgets should override any URL filters
        # (this allows overriding the single-page filter)
        s3.js_global.append('''S3.search.stripFilters=1''')

        s3db.configure(tablename,
                       crud_form = crud_form,
                       delete_next = r.url(method="datalist", id=0),
                       filter_clear = False,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       list_layout = cms_post_list_layout,
                       )

        return True
    if mod or layer:
        # Resource or Map layer
        pass
    else:
        # Story
        s3.prep = custom_prep

    attr["rheader"] = None

    return attr

settings.customise_cms_post_controller = customise_cms_post_controller

# -----------------------------------------------------------------------------
# Saved Maps
#
def gis_config_list_layout(list_id, item_id, resource, rfields, record):
    """
        Custom dataList item renderer for Saved Maps

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["gis_config.id"]

    raw = record._row
    name = record["gis_config.name"]
    author = record["gis_config.pe_id"]
    image = raw["gis_config.image"]

    item = DIV(A(IMG(_src="/%s/static/cache/jpg/%s" % \
                                        (current.request.application, image),
                     _width="820",
                     _height="410",
                     _alt=name,
                     _tabindex="0",
                     ),
                    TAG.figcaption(name,
                                   " ",
                                   TAG.small(str(T("by %(person)s")) % \
                                                        dict(person=author),
                                             _tabindex="0",
                                             ),
                                   ),
                _href=URL(c="gis", f="index",
                          vars={"config": record_id}),
                _tabindex="0",
                ))

    return item

def customise_gis_config_controller(**attr):

    # Custom PreP
    s3 = current.response.s3
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        s3db = current.s3db
        table = s3db.gis_config

        # Tweak DataList options
        s3.dl_no_header = True
        s3.dl_rowsize = 3
        list_fields = s3db.get_config("gis_config", "list_fields")
        list_fields.append("image")

        field = table.image
        field.readable = True
        #field.readable = field.writable = True
        field.label = T("Image")
        #from s3 import S3ImageCropWidget
        #field.widget = S3ImageCropWidget((820, 410))

        table.pe_id.represent = s3db.pr_PersonEntityRepresent(show_label = False,
                                                              show_type = False,
                                                              show_link = False, # We're rendering inside another A()
                                                              )
        # NB This page needs checking for responsiveness.
        # Should be small-block-grid-1 medium-block-grid-2 large-block-grid-3
        s3db.configure("gis_config",
                       list_layout = gis_config_list_layout,
                       )

        auth = current.auth
        coalition = auth.user.org_group_id

        if coalition:
            db = current.db
            utable = db.auth_user
            ltable = s3db.pr_person_user
            query = (table.deleted == False) & \
                    (table.pe_id == ltable.pe_id) & \
                    (ltable.user_id == utable.id) & \
                    (utable.org_group_id == coalition)
            rows = db(query).select(ltable.pe_id,
                                    distinct = True)
            if rows:
                coalition_pe_ids = ",".join([str(row.pe_id) for row in rows] + \
                                            [str(coalition)])
            else:
                coalition_pe_ids = str(coalition)


        from s3 import S3OptionsFilter
        if coalition:
            filter_widgets = [
                S3OptionsFilter("pe_id",
                                label = "",
                                options = OrderedDict([(auth.user.pe_id, T("Your Maps")),
                                                       (coalition_pe_ids, T("Your Coalition's Maps")),
                                                       ("*", T("All Maps")),
                                                       ]),
                                cols = 3,
                                multiple = False,
                                # Not working
                                sort = False,
                                )
                ]
        else:
            filter_widgets = [
                S3OptionsFilter("pe_id",
                                label = "",
                                options = OrderedDict([(auth.user.pe_id, T("Your Maps")),
                                                       ("*", T("All Maps")),
                                                       ]),
                                cols = 2,
                                multiple = False,
                                # Not working
                                sort = False,
                                )
                ]

        s3db.configure("gis_config",
                       filter_clear = False,
                       filter_formstyle = filter_formstyle,
                       filter_widgets = filter_widgets,
                       )

        return True
    s3.prep = custom_prep

    return attr

settings.customise_gis_config_controller = customise_gis_config_controller

# -----------------------------------------------------------------------------
# Points, Routes and Areas
#
def customise_gis_poi_controller(**attr):

    # Custom PreP
    s3 = current.response.s3
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        if r.interactive:
            s3db = current.s3db
            tablename = "gis_poi"
            table = s3db.gis_poi

            if r.record:
                gtable = s3db.gis_location
                row = current.db(gtable.id == r.record.location_id).select(gtable.gis_feature_type,
                                                                           limitby=(0, 1)
                                                                           ).first()
                try:
                    feature_type = row.gis_feature_type
                except:
                    # No location?
                    feature_type = 1
            else:
                feature_type = r.get_vars.get("~.location_id$gis_feature_type")
                if feature_type:
                    feature_type = int(feature_type)
                else:
                    feature_type = 1

            if feature_type == 1:
                # Point
                icon = "point"
                color_picker = False
                points = True
                lines = False
                polygons = False
                s3.crud_strings[tablename] = Storage(
                    label_create = T("Add Point"),
                    title_display = T("Point Details"),
                    title_list = T("Points"),
                    title_update = T("Update Point Details"),
                    label_list_button = T("List Points"),
                    label_delete_button = T("Delete Point"),
                    msg_record_created = T("Point added"),
                    msg_record_modified = T("Point details updated"),
                    msg_record_deleted = T("Point deleted"),
                    msg_list_empty = T("No Points currently registered"))
            elif feature_type == 2:
                # Route
                icon = "route"
                color_picker = True
                points = False
                lines = True
                polygons = False
                s3.crud_strings[tablename] = Storage(
                    label_create = T("Add Route"),
                    title_display = T("Route Details"),
                    title_list = T("Routes"),
                    title_update = T("Update Route Details"),
                    label_list_button = T("List Routes"),
                    label_delete_button = T("Delete Route"),
                    msg_record_created = T("Route added"),
                    msg_record_modified = T("Route details updated"),
                    msg_record_deleted = T("Route deleted"),
                    msg_list_empty = T("No Routes currently registered"))
            elif feature_type == 3:
                # Area
                icon = "area"
                color_picker = True
                points = False
                lines = False
                polygons = True
                s3.crud_strings[tablename] = Storage(
                    label_create = T("Add Area"),
                    title_display = T("Area Details"),
                    title_list = T("Areas"),
                    title_update = T("Update Area Details"),
                    label_list_button = T("List Areas"),
                    label_delete_button = T("Delete Area"),
                    msg_record_created = T("Area added"),
                    msg_record_modified = T("Area details updated"),
                    msg_record_deleted = T("Area deleted"),
                    msg_list_empty = T("No Areas currently registered"))

            from s3 import IS_ADD_PERSON_WIDGET2, IS_LOCATION_SELECTOR2, \
                           S3AddPersonWidget2, S3LocationSelectorWidget2, S3MultiSelectWidget, S3StringWidget, \
                           S3SQLCustomForm, S3SQLInlineComponent
            table.name.widget = S3StringWidget(placeholder=T("Text"))
            table.comments.widget = S3StringWidget(placeholder=T("Description"), textarea=True)
            table.poi_type_id.widget = S3MultiSelectWidget(multiple=False)
            field = table.organisation_id
            field.readable = field.writable = True
            field.widget = S3MultiSelectWidget(multiple=False)
            field = table.person_id
            field.readable = field.writable = True
            field.label = T("Contact Person")
            field.requires = IS_ADD_PERSON_WIDGET2(allow_empty=True)
            field.widget = S3AddPersonWidget2(controller="pr")
            s3db.gis_poi_group.group_id.widget = S3MultiSelectWidget(multiple=False)
            if r.repesentation != "popup":
                field = table.location_id
                field.label = "" # Gets replaced by widget
                levels = ("L3",)
                field.requires = IS_LOCATION_SELECTOR2(levels=levels)
                field.widget = S3LocationSelectorWidget2(levels=levels,
                                                         hide_lx=False,
                                                         color_picker=color_picker,
                                                         lines=lines,
                                                         points=points,
                                                         polygons=polygons,
                                                         reverse_lx=True,
                                                         show_address=True,
                                                         show_postcode=True,
                                                         )
            if r.method == "update":
                # Normal Submit buttons
                s3.crud.submit_button = T("Save & Close")
                create_next = r.url(method="summary", id=0)
                create_next_close = None
            else:
                s3.crud.submit_button = T("Save & Add Another")
                s3.crud.custom_submit = (("save_close", T("Save & Close"), "button small secondary"),
                                         #("cancel", T("Cancel"), "button small secondary cancel"),
                                         )
                create_next = r.url(method="create")
                create_next_close = r.url(method="summary", id=0)
            s3.cancel = A(T("Cancel"),
                          _class="button small secondary cancel",
                          _href=r.url(method="summary", id=0),
                          )

            crud_form = S3SQLCustomForm("name",
                                        "comments",
                                        "organisation_id",
                                        S3SQLInlineComponent(
                                            "poi_group",
                                            columns = (4,),
                                            label = T("Coalition"),
                                            fields = [("", "group_id")],
                                            multiple = False,
                                            ),
                                        "person_id",
                                        "location_id",
                                        )

            s3db.configure(tablename,
                           create_next = create_next,
                           create_next_close = create_next_close,
                           crud_form = crud_form,
                           icon = icon,
                           delete_next = r.url(method="summary", id=0),
                           update_next = r.url(method="summary", id=0),
                           )
        return True
    s3.prep = custom_prep

    return attr

settings.customise_gis_poi_controller = customise_gis_poi_controller

# =============================================================================
class CRMTSubFormLayout(S3SQLSubFormLayout):
    """ Custom Layout for S3SQLInlineComponent """

    # -------------------------------------------------------------------------
    def subform(self,
                data,
                item_rows,
                action_rows,
                empty=False,
                readonly=False):
        """
            Outer container for the subform

            @param data: the data dict (as returned from extract())
            @param item_rows: the item rows
            @param action_rows: the (hidden) action rows
            @param empty: no data in this component
            @param readonly: render read-only
        """

        if empty:
            subform = current.T("No entries currently available")
        else:
            subform = DIV(_class="embeddedComponent")
            headers = self.headers(data, readonly=readonly)
            if headers:
                subform.append(headers)
            subform.append(DIV(item_rows, _class="inline-items"))
            if action_rows:
                subform.append(DIV(action_rows, _class="inline-edit"))
        return subform

    # -------------------------------------------------------------------------
    def readonly(self, resource, data):
        """
            Render this component read-only (table-style)

            @param resource: the S3Resource
            @param data: the data dict (as returned from extract())
        """

        audit = current.audit
        prefix, name = resource.prefix, resource.name

        xml_decode = current.xml.xml_decode

        items = data["data"]
        fields = data["fields"]

        item_rows = []

        columns = self.columns
        for item in items:
            if "_id" in item:
                record_id = item["_id"]
            else:
                continue
            audit("read", prefix, name,
                  record=record_id, representation="html")
            # Render a read-row
            row = DIV(_class="read-row row")
            for i, f in enumerate(fields):
                # Determine column width
                if columns and len(columns) > i:
                    width = columns[i]
                else:
                    width = 1
                column_class = "small-%s columns" % width
                # Last column?
                if i == len(fields) - 1:
                    column_class = "%s end" % column_class
                # Add the column to the row
                text = xml_decode(item[f["name"]]["text"])
                row.append(DIV(XML(xml_decode(text)),
                               _class=column_class,
                               ))
            # Append the row
            item_rows.append(row)

        return self.subform(data, item_rows, [], empty=False, readonly=True)

    # -------------------------------------------------------------------------
    def headers(self, data, readonly=False):
        """
            Render the header row with field labels

            @param data: the input field data as Python object
            @param readonly: whether the form is read-only
            @param attributes: HTML attributes for the header row
        """

        fields = data["fields"]

        # Don't render a header row if there are no labels
        render_header = False
        header_row = DIV(_class="label-row row")

        happend = header_row.append
        numfields = len(fields)
        columns = self.columns
        for i, f in enumerate(fields):
            label = f["label"]
            if label:
                render_header = True
            # Determine column width
            if columns and len(columns) > i:
                width = columns[i]
            else:
                width = 1
            column_class = "small-%s columns" % width
            # Last column?
            if i == len(fields) - 1:
                column_class = "%s end" % column_class
            label = DIV(LABEL(label), _class=column_class)
            happend(label)

        if render_header:
            return DIV(header_row)
        else:
            return None

    # -------------------------------------------------------------------------
    @staticmethod
    def actions(subform,
                formname,
                index,
                item = None,
                readonly=True,
                editable=True,
                deletable=True):
        """
            Render subform row actions into the row

            @param subform: the subform row
            @param formname: the form name
            @param index: the row index
            @param item: the row data
            @param readonly: this is a read-row
            @param editable: this row is editable
            @param deletable: this row is deletable
        """

        T = current.T
        action_id = "%s-%s" % (formname, index)

        # Action button helper
        def action(title, name, throbber=False):
            btn = DIV(_id="%s-%s" % (name, action_id),
                      _class="inline-%s" % name)
            if throbber:
                return DIV(btn,
                        DIV(_class="inline-throbber hide",
                            _id="throbber-%s" % action_id))
            else:
                return DIV(btn)

        # Render the action icons for this row
        action_col = DIV(_class="inline-actions small-1 columns end")
        append = action_col.append
        if readonly:
            if editable:
                append(action(T("Edit this entry"), "edt"))
            if deletable:
                append(action(T("Remove this entry"), "rmv"))
        else:
            if index != "none" or item:
                append(action(T("Update this entry"), "rdy", throbber=True))
                append(action(T("Cancel editing"), "cnc"))
            else:
                append(action(T("Add this entry"), "add", throbber=True))
        subform.append(action_col)

    # -------------------------------------------------------------------------
    def rowstyle(self, form, fields, *args, **kwargs):
        """
            Formstyle for subform rows
        """

        def render_col(col_id, label, widget, comment, width=None, end=False):

            # Render column
            if comment:
                col = DIV(DIV(widget, comment), _id=col_id)
            else:
                col = DIV(widget, _id=col_id)
            # Add CSS class for column width
            if width:
                column_class = "small-%s columns" % width
                if end:
                    column_class = "%s end" % column_class
                col.add_class(column_class)
            return col

        if args:
            col_id = form
            label = fields
            widget, comment = args
            return render_col(col_id, label, widget, comment)
        else:
            # Parent is always a row
            parent = DIV(_class="row")
            columns = self.columns
            row_actions = self.row_actions
            for i, (col_id, label, widget, comment) in enumerate(fields):
                # Determine column width
                if columns and len(columns) > i:
                    width = columns[i]
                else:
                    width = 1
                # Last column?
                end = not row_actions and i == len(fields) - 1
                # Render and append column
                parent.append(render_col(col_id,
                                         label,
                                         widget,
                                         comment,
                                         width=width,
                                         end=end,
                                         ))
            return parent

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_script():
        """ Inject custom JS to render new read-rows """

        appname = current.request.application
        scripts = current.response.s3.scripts

        # @todo: support minified script in non-debug mode
        script = "/%s/static/themes/CRMT2/js/inlinecomponent.layout.js" % appname
        if script not in scripts:
            scripts.append(script)
        return

# Configure this layout for this template
settings.ui.inline_component_layout = CRMTSubFormLayout

# =============================================================================
class OrganisationProfileLayout(S3DataListLayout):
    """ DataList layout for Organisation Profile """

    # -------------------------------------------------------------------------
    def __init__(self, profile="org_organisation"):
        """ Constructor """

        super(OrganisationProfileLayout, self).__init__(profile=profile)

    # -------------------------------------------------------------------------
    def render_header(self, list_id, item_id, resource, rfields, record):
        """
            Render the card header

            @param list_id: the HTML ID of the list
            @param item_id: the HTML ID of the item
            @param resource: the S3Resource to render
            @param rfields: the S3ResourceFields to render
            @param record: the record as dict
        """

        toolbox = self.render_toolbox(list_id, resource, record)

        tablename = resource.tablename
        if tablename == "org_facility":
            icon_class = "icon-globe"
            title = record["org_facility.location_id"]
        else:
            icon_class = "icon"
            title = ""

        return DIV(I(_class=icon_class),
                   SPAN(" %s" % title, _class="card-title"),
                   toolbox,
                   _class="card-header",
                   )

    # ---------------------------------------------------------------------
    def render_body(self, list_id, item_id, resource, rfields, record):
        """
            Render the card body

            @param list_id: the HTML ID of the list
            @param item_id: the HTML ID of the item
            @param resource: the S3Resource to render
            @param rfields: the S3ResourceFields to render
            @param record: the record as dict
        """

        # No body in this layout so far (org_facility is header-only)
        return None

    # -------------------------------------------------------------------------
    def render_toolbox(self, list_id, resource, record):
        """
            Render the toolbox

            @param list_id: the HTML ID of the list
            @param resource: the S3Resource to render
            @param record: the record as dict
        """

        table = resource.table
        tablename = resource.tablename
        record_id = record[str(resource._id)]

        open_url = update_url = None
        if tablename == "org_facility":
            update_url = URL(f="facility",
                             args=[record_id, "update.popup"],
                             vars={"refresh": list_id,
                                   "record": record_id,
                                   "profile": self.profile,
                                   },
                             )

        has_permission = current.auth.s3_has_permission

        from s3 import S3Method
        crud_string = S3Method.crud_string

        toolbox = DIV(_class="edit-bar fright")

        if update_url and \
           has_permission("update", table,
                          record_id=record_id, c="org", f="facility"):
            btn = A(I(" ", _class="icon icon-edit"),
                    _href=update_url,
                    _class="s3_modal",
                    _title=crud_string(tablename, "title_update"))
            toolbox.append(btn)

        elif open_url:
            btn = A(I(" ", _class="icon icon-file-alt"),
                    _href=open_url,
                    _title=crud_string(tablename, "title_display"))
            toolbox.append(btn)

        if has_permission("delete", table,
                          record_id=record_id, c="org", f="facility"):
            btn = A(I(" ", _class="icon icon-trash"),
                    _class="dl-item-delete",
                    _title=crud_string(tablename, "label_delete_button"))
            toolbox.append(btn)

        return toolbox

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
    ("project", Storage(
        name_nice = T("Projects"),
        restricted = True,
        module_type = None
    )),
    # Needed for Activity Beneficiaries
    ("stats", Storage(
        name_nice = "Statistics",
        restricted = True,
        module_type = None
    )),
])
