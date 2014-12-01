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

from s3 import s3_avatar_represent, S3DataListLayout

T = current.T
settings = current.deployment_settings

"""
    Template settings for Community Resilience Mapping Tool
"""

# -----------------------------------------------------------------------------
# Pre-Populate
settings.base.prepopulate = ("CRMT", "default/users", "CRMT/Demo")

settings.base.system_name = T("Community Resilience Mapping Tool")
settings.base.system_name_short = T("CRMT")

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
# Uncomment to disable responsive behavior of datatables
# - Disabled until tested
settings.ui.datatables_responsive = False
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
# Audit
def audit_write(method, tablename, form, record, representation):
    if not current.auth.user:
        # Don't include prepop
        return False
    if tablename in ("org_facility",
                     "org_organisation",
                     "pr_filter",
                     "project_activity",
                     "stats_people",
                     "vulnerability_evac_route",
                     "vulnerability_risk",
                     ):
        # Perform normal Audit
        return True
    elif tablename == "gis_config":
        if form.vars.get("temp") != "1":
            # Perform normal Audit
            return True
    # Don't Audit non user-visible resources
    return False

settings.security.audit_write = audit_write

# -----------------------------------------------------------------------------
# Theme (folder to use for views/layout.html)
settings.base.theme = "CRMT"
settings.ui.formstyle_row = "bootstrap"
settings.ui.formstyle = "bootstrap"
settings.ui.hide_report_options = False
settings.ui.update_label = "Update"
settings.ui.export_formats = ("xls", "xml")
# Uncomment to use S3MultiSelectWidget on all dropdowns (currently the Auth Registration page & LocationSelectorWidget2 listen to this)
settings.ui.multiselect_widget = True
settings.ui.use_button_icons = True

# Set Map to fill the container
settings.gis.map_width = 1178
# Set map to be able to open Census Data & still view root labels
settings.gis.map_height = 816

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
# Menu
menu = (
    {"name": T("Organizations"),
     "c":"org",
     "f":"organisation",
     "icon": "icon-sitemap"
     },
    {"name": T("Places"),
     "c":"org",
     "f":"facility",
     "icon": "icon-map-marker"
     },
    {"name": T("People"),
     "c":"stats",
     "f":"people",
     "icon": "icon-group"
     },
    #{"name": T("Incidents"),
    # "url": URL(c="event", f="incident_report"),
    # "icon": "icon-warning-sign"
    # },
    {"name": T("Hazards"),
     "c":"vulnerability",
     "f":"risk",
     "icon": "icon-bolt"
     },
    {"name": T("Activities"),
     "c":"project",
     "f":"activity",
     "icon": "icon-star-empty"
     },
    #{"name": T("Organizations"),
    # "url": URL(c="org", f="organisation"),
    # "icon": "icon-sitemap"
    # },
    #{"name": T("Trained People"),
    # "url": URL(c="stats", f="trained"),
    # "icon": "icon-user"
    # },
    {"name": T("Evacuation Routes"),
     "c":"vulnerability",
     "f":"evac_route",
     "icon": "icon-road"
     },
    )

for item in menu:
    item["url"] = URL(item["c"], item["f"])

current.response.menu = menu

# -----------------------------------------------------------------------------
# Summary Pages
settings.ui.summary = ({"common": True,
                        "name": "add",
                        "widgets": [{"method": "create"}],
                        },
                       {"common": True,
                        "name": "cms",
                        "widgets": [{"method": "cms"}]
                        },
                       {"name": "table",
                        "label": "Table",
                        "widgets": [{"method": "datatable"}]
                        },
                       {"name": "charts",
                        "label": "Charts",
                        "widgets": [{"method": "report", "ajax_init": True}]
                        },
                       {"name": "map",
                        "label": "Map",
                        "widgets": [{"method": "map", "ajax_init": True}],
                        },
                       )

settings.search.filter_manager = True
settings.search.filter_manager_allow_delete = False
settings.search.filter_manager_save = "Save"
settings.search.filter_manager_update = "Update"

# -----------------------------------------------------------------------------
# Filter forms - style for Summary pages
def filter_formstyle(row_id, label, widget, comment, hidden=False):
    return DIV(label, widget, comment,
               _id=row_id,
               _class="horiz_filter_form")

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
settings.gis.label_overlays = "Places"
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
settings.gis.poi_create_resources = None
# Uncomment to rename Overlays in Layer Tree
#settings.gis.label_overlays = "Community Data"
# Uncomment to show the Print control:
# http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
settings.gis.print_button = True
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
settings.org.site_label = "Place"

# -----------------------------------------------------------------------------
# projects
#
# Uncomment this to disable Sectors in projects
settings.project.sectors = False

# -----------------------------------------------------------------------------
# Contacts
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
                    label_create = T("Add"),
                    title_display = T("Contact Details"),
                    title_list = T("Contact Directory"),
                    title_update = T("Update Contact Details"),
                    label_list_button = T("List Contacts"),
                    label_delete_button = T("Delete Contact"),
                    msg_record_created = T("Contact added"),
                    msg_record_modified = T("Contact details updated"),
                    msg_record_deleted = T("Contact deleted"),
                    msg_list_empty = T("No Contacts currently registered"))

            # Custom Form (Read/Create/Update)
            from s3 import S3Represent, S3SQLCustomForm, S3SQLInlineComponent
            if r.method in ("create", "update"):
                # Custom Widgets/Validators
                widgets = True
            else:
                widgets = False

            htable = s3db.hrm_human_resource
            htable.organisation_id.widget = None
            site_field = htable.site_id
            site_field.label = T("Place")
            represent = S3Represent(lookup="org_site")
            site_field.represent = represent
            if widgets:
                from s3 import IS_ONE_OF, S3MultiSelectWidget
                from s3layouts import S3AddResourceLink
                htable.organisation_id.widget = S3MultiSelectWidget(multiple=False)
                site_field.widget = S3MultiSelectWidget(multiple=False)
                site_field.requires = IS_ONE_OF(db, "org_site.site_id",
                                                represent,
                                                orderby = "org_site.name")
                site_field.comment = S3AddResourceLink(c="org", f="office",
                                                       vars={"child": "site_id"},
                                                       label=T("Add New Place"),
                                                       title=T("Place"),
                                                       tooltip=T("If you don't see the Place in the list, you can add a new one by clicking link 'Add New Place'."))

            s3db.pr_image.profile.default = True
            # ImageCrop widget doesn't currently work within an Inline Form
            from gluon.validators import IS_IMAGE
            image_field = s3db.pr_image.image
            image_field.requires = IS_IMAGE()
            image_field.widget = None

            hr_fields = ["organisation_id",
                         #"job_title_id",
                         "site_id",
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
                        label = "",
                        multiple = False,
                        fields = hr_fields,
                    ),
                    S3SQLInlineComponent(
                        "user",
                        name = "user",
                        label = T("Coalition"),
                        multiple = False,
                        fields = [],
                        # Fields needed to load for Virtual Fields
                        extra_fields = ["user_id"],
                        virtual_fields = [("", "org_group_id")],
                    ),
                    S3SQLInlineComponent(
                        "image",
                        name = "image",
                        label = T("Photo"),
                        multiple = False,
                        fields = [("", "image")],
                        filterby = dict(field = "profile",
                                        options=[True]
                                        ),
                        ),
                    S3SQLInlineComponent("contact",
                        name = "email",
                        label = T("Email"),
                        multiple = False,
                        fields = [("", "value")],
                        filterby = dict(field = "contact_method",
                                        options = "EMAIL"),
                        ),
                    S3SQLInlineComponent("contact",
                        name = "phone",
                        label = settings.get_ui_label_mobile_phone(),
                        multiple = False,
                        fields = [("", "value")],
                        filterby = dict(field = "contact_method",
                                        options = "SMS"),
                        ),
                    S3SQLInlineComponent("contact",
                        name = "home",
                        label = T("Home Phone"),
                        multiple = False,
                        fields = [("", "value")],
                        filterby = dict(field = "contact_method",
                                        options = "HOME_PHONE"),
                        ),
                    ]

            crud_form = S3SQLCustomForm(*s3_sql_custom_fields)

            # Return to List view after create/update/delete (unless done via Modal)
            url_next = URL(c="pr", f="person")

            s3db.configure(tablename,
                           create_next = url_next,
                           crud_form = crud_form,
                           delete_next = url_next,
                           # Don't include a Create form in 'More' popups
                           #listadd = False if r.method=="datalist" else True,
                           update_next = url_next,
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
            output["rheader"] = ""
            # All users just get "Open"
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
                           list_fields = list_fields,
                           )

        table.location_id.represent = s3db.gis_LocationRepresent(address_only=True)
        if r.interactive or representation == "json" or \
                            representation == "plain":
            # CRUD Strings / Represent
            s3.crud_strings[tablename].title_update = T("Update Activities")
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
                    label = T("Activity Type"),
                    fields = [("", "activity_type_id")],
                    multiple = False,
                ),
                S3SQLInlineComponent(
                    "activity_group",
                    label = T("Coalition"),
                    fields = [("", "group_id")],
                    multiple = False,
                ),
                "location_id",
                "person_id",
                S3SQLInlineComponent(
                    "activity_organisation",
                    label = T("Participating Organizations"),
                    fields = [("", "organisation_id")],
                ),
                S3SQLInlineComponent(
                    "beneficiary",
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
                           crud_form = crud_form,
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
                from s3 import IS_LOCATION, S3LocationSelector, S3MultiSelectWidget

                s3db.project_activity_activity_type.activity_type_id.widget = S3MultiSelectWidget(multiple=False)
                s3db.project_activity_group.group_id.widget = S3MultiSelectWidget(multiple=False)
                s3db.project_activity_organisation.organisation_id.widget = S3MultiSelectWidget(multiple=False)

                field = table.location_id
                field.label = "" # Gets replaced by widget
                levels = ("L3",)
                field.requires = IS_LOCATION()
                field.widget = S3LocationSelector(levels=levels,
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
            places_widget = dict(label = "Organization's Places",
                                 label_create = "Add Place",
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
                           (T("Coalition Member"), "group_membership.group_id"),
                           (T("Organization's Places"), "facility.location_id"),
                           #"facility.location_id$addr_postcode",
                           (T("Sectors"), "sector_organisation.sector_id"),
                           (T("Services"), "service_organisation.service_id"),
                           "phone",
                           "website",
                           "comments",
                           ]

            s3db.configure(tablename,
                           list_fields = list_fields,
                           # Hide Open & Delete dataTable action buttons
                           deletable = False,
                           editable = False,
                           )

        if (r.interactive or r.representation == "json") and not r.component:

            # CRUD Strings / Represent
            s3.crud_strings[tablename].title_update = T("Update Organization")
            table.logo.readable = table.logo.writable = False
            table.name.label = T("Organization Name")

            if method in ("summary", "report"):

                # Filter form
                from s3 import S3OptionsFilter, S3TextFilter, S3HierarchyFilter
                filter_widgets = [S3TextFilter(["name",
                                                "group_membership.group_id",
                                                "sector_organisation.sector_id",
                                                "service_organisation.service_id",
                                                "comments"
                                                ],
                                                label = T("Search"),
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
                                                    ),
                                  #S3HierarchyFilter("organisation_organisation_type.organisation_type_id",
                                  #                  label = T("Type of Organization"),
                                  #                  #multiple = False,
                                  #                  )
                                  ]

                s3.crud_strings.org_organisation.title_report = T("Organization Matrix")

                # Report Options
                report_fields = [# Only 1 Axis so use singular name
                                 #"name",
                                 (T("Coalition Member"), "group_membership.group_id"),
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

                from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineComponentMultiSelectWidget, S3SQLInlineLink
                form_fields = ["name",
                               "logo",
                               S3SQLInlineComponent(
                                    "group_membership",
                                    label = T("Coalition Member"),
                                    fields = [("", "group_id"),
                                              ("", "status_id"),
                                              ],
                                    ),
                               S3SQLInlineComponentMultiSelectWidget(
                                    "sector",
                                    label = T("Sectors"),
                                    field = "sector_id",
                                    ),
                               S3SQLInlineLink(
                                    "service",
                                    label = T("Services"),
                                    field = "service_id",
                                    leafonly = False,
                                    widget = "hierarchy",
                                    ),
                               S3SQLInlineComponent(
                                    "resource",
                                    label = T("Organization's Resources"),
                                    fields = ["parameter_id",
                                              "value",
                                              "comments",
                                              ],
                                    ),
                               "phone",
                               "website",
                               S3SQLInlineComponent(
                                    "contact",
                                    name = "twitter",
                                    label = T("Twitter"),
                                    multiple = False,
                                    fields = [("", "value")],
                                    filterby = dict(field = "contact_method",
                                                    options = "TWITTER"
                                                    )
                                    ),
                               "comments",
                               ]

                # Allow free-text in Phone
                table.phone.requires = None

                # Organisation's Resources
                from s3 import S3MultiSelectWidget
                s3db.org_resource.parameter_id.widget = S3MultiSelectWidget(multiple=False)

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
                                                              # NB Has no permissions checks
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
                                                label = T("Organization's Places"),
                                                fields = [("", "location_id"),
                                                        ],
                                                multiple = False,
                                       ))

                    ftable = s3db.org_facility
                    ftable.name.default = "TEMP" # replace in form postprocess
                    field = ftable.location_id
                    field.label = T("Address")
                    field.represent = s3db.gis_LocationRepresent(address_only=True)
                    from s3 import IS_LOCATION, S3LocationSelector
                    levels = ("L3",)
                    field.requires = IS_LOCATION()
                    field.widget = S3LocationSelector(levels=levels,
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
                               crud_form = crud_form,
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
            from s3 import IS_LOCATION, S3LocationSelector
            table = current.s3db.org_group
            table.name.label = T("Coalition Name")
            field = table.location_id
            field.label = "" # Gets replaced by widget
            levels = ("L2",)
            field.requires = IS_LOCATION()
            field.widget = S3LocationSelector(levels = levels,
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
                from s3 import IS_LOCATION, S3LocationSelector, S3MultiSelectWidget

                # Allow free-text in Phone
                table.phone1.requires = None

                field = table.location_id
                field.label = "" # Gets replaced by widget
                levels = ("L3",)
                field.requires = IS_LOCATION()
                field.widget = S3LocationSelector(levels=levels,
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
                               filter_widgets = filter_widgets,
                               filter_formstyle = filter_formstyle,
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
# People (Stats People)
#
def customise_stats_people_controller(**attr):

    if "summary" in current.request.args:
        settings.gis.toolbar = False
        from s3 import s3_set_default_filter
        s3_set_default_filter("people_group.group_id",
                              default_coalition_filter,
                              tablename = "stats_people")

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
        tablename = "stats_people"
        table = s3db[tablename]

        # Disable name
        table.name.label = T("Description")
        #table.name.writable = False

        method = r.method
        representation = r.representation
        if method == "summary" or representation == "aadata":
            # Modify list_fields
            list_fields = ["id",
                           "name",
                           "parameter_id",
                           "value",
                           "people_group.group_id",
                           (T("Address"), "location_id"),
                           "location_id$addr_postcode",
                           "person_id",
                           "comments",
                           ]

            s3db.configure(tablename,
                           list_fields = list_fields,
                           )

        if r.interactive or representation == "json": #or representation == "plain"
            # CRUD Strings / Represent
            #table.location_id.represent = s3db.gis_LocationRepresent(address_only=True)

            s3.crud_strings[tablename] = Storage(
                label_create = T("Add"),
                title_display = T("People Details"),
                title_list = T("People"),
                title_update = T("Update People"),
                label_list_button = T("List People"),
                label_delete_button = T("Remove People"),
                msg_record_created = T("People added"),
                msg_record_modified = T("People updated"),
                msg_record_deleted = T("People removed"),
                msg_list_empty = T("No People currently recorded"))

            # Custom Form (Read/Create/Update inc embedded Summary)
            from s3 import S3SQLCustomForm, S3SQLInlineComponent
            if method in ("create", "update", "summary"):
                # Custom Widgets/Validators
                from s3 import IS_LOCATION, S3LocationSelector, S3MultiSelectWidget

                table.parameter_id.widget = S3MultiSelectWidget(multiple=False)
                s3db.stats_people_group.group_id.widget = S3MultiSelectWidget(multiple=False)

                field = table.location_id
                field.label = "" # Gets replaced by widget
                levels = ("L3",)
                field.requires = IS_LOCATION()
                # Inform S3LocationSelector of the record_id
                s3.record_id = r.id
                field.widget = S3LocationSelector(levels = levels,
                                                  hide_lx = False,
                                                  polygons = True,
                                                  color_picker = True,
                                                  reverse_lx = True,
                                                  show_postcode = True,
                                                  #show_map = False,
                                                  )
                # L3s only
                #from s3 import S3Represent, IS_ONE_OF
                #field.requires = IS_ONE_OF(current.db, "gis_location.id",
                #                           S3Represent(lookup="gis_location"),
                #                           sort = True,
                #                           filterby = "level",
                #                           filter_opts = ("L3",)
                #                           )
                # Don't add new Locations here
                #field.comment = None
                # Simple dropdown
                #field.widget = None
                #field.label = T("City")

                table.person_id.comment = None

            # Custom Crud Form
            crud_form = S3SQLCustomForm("name",
                                        "parameter_id",
                                        "value",
                                        S3SQLInlineComponent(
                                            "people_group",
                                            label = T("Coalition"),
                                            fields = [("", "group_id")],
                                            multiple = False,
                                            ),
                                        "location_id",
                                        "person_id",
                                        S3SQLInlineComponent(
                                            "document",
                                            name = "file",
                                            label = T("Files"),
                                            fields = [("", "file"),
                                                      #"comments",
                                                      ],
                                            ),
                                        "comments",
                                        postprocess = s3db.gis_style_postprocess,
                                        )

            s3db.configure(tablename,
                           crud_form = crud_form,
                           )

            if method in ("summary", "report"):
                from s3 import S3OptionsFilter, S3TextFilter
                filter_widgets = [S3TextFilter(["name",
                                                "people_group.group_id",
                                                "parameter_id",
                                                "organisation_id",
                                                "location_id",
                                                "person_id",
                                                "comments"
                                                ],
                                                label = T("Search"),
                                               ),
                                  S3OptionsFilter("people_group.group_id",
                                                  represent = "%(name)s",
                                                  header = True,
                                                  ),
                                  S3OptionsFilter("parameter_id",
                                                  label = T("Type of People"),
                                                  header = True,
                                                  ),
                                  ]

                report_fields = [#"name",
                                 "parameter_id",
                                 "people_group.group_id",
                                 "location_id$L3",
                                 ]

                report_options = Storage(
                    rows=report_fields,
                    cols=[],
                    fact=[(T("Groups of People"), "count(id)"),
                          (T("Number of People"), "sum(value)"),
                          ],
                    defaults=Storage(# Only 1 Parameter currently!
                                     #rows="people.parameter_id",
                                     rows="people_group.group_id",
                                     #cols="people_group.group_id",
                                     fact="sum(value)",
                                     totals=True,
                                     chart = "barchart:rows",
                                     table = "collapse",
                                     )
                    )

                s3db.configure(tablename,
                               # Hide Open & Delete dataTable action buttons
                               editable = False,
                               deletable = False,
                               filter_widgets = filter_widgets,
                               filter_formstyle = filter_formstyle,
                               report_options = report_options,
                               # No Map for People
                               #summary = [s for s in settings.ui.summary if s["name"] != "map"],
                               )

            elif r.representation == "plain":
                # Map Popups
                table.location_id.label = T("Address")

        return True
    s3.prep = custom_prep

    return attr

settings.customise_stats_people_controller = customise_stats_people_controller

# -----------------------------------------------------------------------------
# Evacuation Routes
#
def customise_vulnerability_evac_route_controller(**attr):

    if "summary" in current.request.args:
        settings.gis.toolbar = False
        from s3 import s3_set_default_filter
        s3_set_default_filter("evac_route_group.group_id",
                              default_coalition_filter,
                              tablename = "vulnerability_evac_route")

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
        tablename = "vulnerability_evac_route"
        table = s3db[tablename]

        method = r.method
        representation = r.representation
        if method == "summary" or representation == "aadata":
            # Modify list_fields
            list_fields = ["id",
                           "name",
                           #(T("Hazard Type"), "hazard_id"),
                           "evac_route_group.group_id",
                           #"location_id",
                           "comments",
                           ]

            s3db.configure(tablename,
                           list_fields = list_fields,
                           )

        if r.interactive or representation == "json" or representation == "plain":
            # CRUD Strings / Represent
            s3.crud_strings[tablename].title_update = T("Update Evacuation Route")

            table.name.label = T("Description")
            table.location_id.readable = False

            # Custom Form (Read/Create/Update inc embedded summary)
            from s3 import S3SQLCustomForm, S3SQLInlineComponent
            if method in ("create", "update", "summary"):
                # Custom Widgets/Validators
                #from s3layouts import S3AddResourceLink
                from s3 import IS_LOCATION, S3LocationSelector, S3MultiSelectWidget

                s3db.vulnerability_evac_route_group.group_id.widget = S3MultiSelectWidget(multiple=False)

                table.location_id.label = "" # Gets replaced by widget
                levels = ("L3",)
                table.location_id.requires = IS_LOCATION()
                table.location_id.widget = S3LocationSelector(levels=levels,
                                                              lines=True,
                                                              )

                #table.hazard_id.comment = S3AddResourceLink(c="vulnerability",
                #                                            f="hazard",
                #                                            title=T("Add Hazard Type"))

            # Custom Crud Form
            crud_form = S3SQLCustomForm(
                "name",
                #"hazard_id",
                S3SQLInlineComponent(
                    "evac_route_group",
                    label = T("Coalition"),
                    fields = [("", "group_id")],
                    multiple = False,
                ),
                "location_id",
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
                from s3 import S3OptionsFilter, S3TextFilter
                filter_widgets = [S3TextFilter(["name",
                                                "evac_route_group.group_id",
                                                "location_id",
                                                "comments"
                                                ],
                                                label = T("Search"),
                                               ),
                                  S3OptionsFilter("evac_route_group.group_id",
                                                  represent = "%(name)s",
                                                  header = True,
                                                  ),
                                  #S3OptionsFilter("hazard_id",
                                  #                label = T("Hazard Type"),
                                  #                header = True,
                                  #                ),
                                  ]

                report_fields = [#"name",
                                 #(T("Hazard Type"),"hazard_id"),
                                 "evac_route_group.group_id",
                                 "location_id$L3",
                                 ]

                report_options = Storage(
                    rows=report_fields,
                    cols=[],
                    fact=[(T("Number of Evacuation Routes"), "count(name)")],
                    defaults=Storage(rows="evac_route_group.group_id",
                                     #cols="evac_route.hazard_id",
                                     fact="count(name)",
                                     totals=True,
                                     chart = "barchart:rows",
                                     table = "collapse",
                                     )
                    )

                s3db.configure(tablename,
                               # Hide Open & Delete dataTable action buttons
                               editable = False,
                               deletable = False,
                               filter_widgets = filter_widgets,
                               filter_formstyle = filter_formstyle,
                               report_options = report_options,
                               )

        return True
    s3.prep = custom_prep

    return attr

settings.customise_vulnerability_evac_route_controller = customise_vulnerability_evac_route_controller

# -----------------------------------------------------------------------------
# Hazards (vulnerability_risk)
#
def customise_vulnerability_risk_controller(**attr):

    if "summary" in current.request.args:
        settings.gis.toolbar = False
        from s3 import s3_set_default_filter
        s3_set_default_filter("risk_group.group_id",
                              default_coalition_filter,
                              tablename = "vulnerability_risk")

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
        tablename = "vulnerability_risk"
        table = s3db[tablename]

        method = r.method
        representation = r.representation
        if method == "summary" or representation == "aadata":
            # Modify list_fields
            list_fields = ["id",
                           "name",
                           #(T("Hazard Type"), "hazard_id"),
                           "risk_group.group_id",
                           (T("Address"), "location_id"),
                           "location_id$addr_postcode",
                           "comments",
                           ]

            s3db.configure(tablename,
                           list_fields = list_fields,
                           )

        table.location_id.represent = s3db.gis_LocationRepresent(address_only=True)
        if r.interactive or representation == "json" or \
                            representation == "plain":
            # CRUD Strings / Represent
            table.name.label = T("Description")

            s3.crud_strings[tablename] = Storage(
                label_create = T("Add"),
                title_display = T("Hazard Details"),
                title_list = T("Hazards"),
                title_update = T("Update Hazard"),
                label_list_button = T("List Hazards"),
                label_delete_button = T("Remove Hazard"),
                msg_record_created = T("Hazard added"),
                msg_record_modified = T("Hazard updated"),
                msg_record_deleted = T("Hazard removed"),
                msg_list_empty = T("No Hazards currently recorded"))

            # Custom Form (Read/Create/Update inc embedded summary)
            from s3 import S3SQLCustomForm, S3SQLInlineComponent
            if method in ("create", "update", "summary"):
                # Custom Widgets/Validators
                from s3 import IS_LOCATION, S3LocationSelector, S3MultiSelectWidget

                s3db.vulnerability_risk_group.group_id.widget = S3MultiSelectWidget(multiple=False)

                field = table.location_id
                field.label = "" # Gets replaced by widget
                levels = ("L3",)
                field.requires = IS_LOCATION()
                # Inform S3LocationSelector of the record_id
                s3.record_id = r.id
                field.widget = S3LocationSelector(levels = levels,
                                                  hide_lx = False,
                                                  reverse_lx = True,
                                                  #points = False,
                                                  polygons = True,
                                                  color_picker = True,
                                                  show_address = True,
                                                  show_postcode = True,
                                                  )

            # Custom Crud Form
            crud_form = S3SQLCustomForm("name",
                                        #"hazard_id",
                                        S3SQLInlineComponent(
                                            "risk_group",
                                            label = T("Coalition"),
                                            fields = [("", "group_id")],
                                            multiple = False,
                                            ),
                                        "location_id",
                                        S3SQLInlineComponent(
                                            "document",
                                            name = "file",
                                            label = T("Files"),
                                            fields = [("", "file"),
                                                      #"comments",
                                                      ],
                                            ),
                                        "comments",
                                        postprocess = s3db.gis_style_postprocess,
                                        )

            s3db.configure(tablename,
                           crud_form = crud_form,
                           )

            if method in ("summary", "report"):
                # Not needed now that Risk data is moved to WMS
                # Filter out data not associated with any Coalition
                #from s3 import FS
                #group_filter = (FS("group.id") != None)
                #r.resource.add_filter(group_filter)

                from s3 import S3OptionsFilter, S3TextFilter
                filter_widgets = [S3TextFilter(["name",
                                                "risk_group.group_id",
                                                "location_id",
                                                "comments"
                                                ],
                                                label = T("Search"),
                                               ),
                                  S3OptionsFilter("risk_group.group_id",
                                                  represent = "%(name)s",
                                                  header = True,
                                                  ),
                                  #S3OptionsFilter("hazard_id",
                                  #                label = T("Hazard Type"),
                                  #                header = True,
                                  #                ),
                                  ]

                report_fields = [#"name",
                                 #(T("Hazard Type"),"hazard_id"),
                                 "risk_group.group_id",
                                 "location_id$L3",
                                 ]

                report_options = Storage(
                    rows = report_fields,
                    cols = [],
                    fact = [(T("Number of Hazards"), "count(name)")],
                    defaults = Storage(rows = "risk_group.group_id",
                                       #cols = "risk.hazard_id",
                                       fact = "count(name)",
                                       totals = True,
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

        # Not needed now that Risk data is moved to WMS
        #elif r.representation== "geojson":
        #    layer = current.request.get_vars.get("layer", None)
        #    if not layer:
        #        # Filter out data not associated with any Coalition
        #        from s3 import FS
        #        group_filter = (FS("group.id") != None)
        #        r.resource.add_filter(group_filter)

        return True
    s3.prep = custom_prep

    attr["rheader"] = None

    return attr

settings.customise_vulnerability_risk_controller = customise_vulnerability_risk_controller

# -----------------------------------------------------------------------------
# Saved Maps
#
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

        if r.interactive:
            auth = current.auth
            coalition = auth.user.org_group_id
            if not coalition:
                return True

            db = current.db
            s3db = current.s3db
            utable = db.auth_user
            ltable = s3db.pr_person_user
            table = s3db.gis_config
            query = (table.deleted == False) & \
                    (table.pe_id == ltable.pe_id) & \
                    (ltable.user_id == utable.id) & \
                    (utable.org_group_id == coalition)
            rows = db(query).select(ltable.pe_id,
                                    distinct=True)
            if rows:
                coalition_pe_ids = ",".join([str(row.pe_id) for row in rows])
                from s3 import S3OptionsFilter
                filter_widgets = [
                    S3OptionsFilter("pe_id",
                                    label = "",
                                    options = {"*": T("All"),
                                               coalition_pe_ids: T("My Coalition's Maps"),
                                               auth.user.pe_id: T("My Maps"),
                                               },
                                    cols = 3,
                                    multiple = False,
                                    )
                    ]
                s3db.configure("gis_config",
                               filter_widgets = filter_widgets,
                               )

        return True
    s3.prep = custom_prep

    return attr

settings.customise_gis_config_controller = customise_gis_config_controller

# -----------------------------------------------------------------------------
# Site Activity Log
#
class ActivityLogLayout(S3DataListLayout):

    item_class = ""

    # -------------------------------------------------------------------------
    def __init__(self):
        """ Constructor """

        super(ActivityLogLayout, self).__init__()

        self.names = {}
        self.authors = {}

    # ---------------------------------------------------------------------
    def prep(self, resource, records):

        # Lookup "name" field for each record if table != pr_filter
        names = {}
        authors = {}
        for record in records:
            raw = record._row
            tablename = raw["s3_audit.tablename"]
            if tablename == "pr_filter":
                continue
            if tablename not in names:
                names[tablename] = {}
            names[tablename][raw["s3_audit.record_id"]] = ""
            authors[raw["s3_audit.user_id"]] = (None, None)

        db = current.db
        s3db = current.s3db
        for tablename, records in names.items():
            table = s3db[tablename]
            if "name" not in table.fields:
                continue
            query = table._id.belongs(records)
            rows = db(query).select(table._id, table.name)
            for row in rows:
                names[tablename][row[table._id]] = row[table.name]

        # Lookup avatars and person_id for each author_id
        ptable = s3db.pr_person
        ltable = db.pr_person_user
        query = (ltable.user_id.belongs(authors.keys())) & \
                (ltable.pe_id == ptable.pe_id)
        rows = db(query).select(ltable.user_id, ptable.id)

        for row in rows:
            user_id = row[ltable.user_id]
            avatar = s3_avatar_represent(user_id,
                                         _class="media-object",
                                         # @ToDo: Move to CSS
                                         _style="width:50px;padding:5px;padding-top:0px;")
            person_id = row[ptable.id]
            if person_id:
                person_url = URL(c="pr", f="person", args=[person_id])
            else:
                person_url = "#"
            authors[user_id] = (avatar, person_url)

        self.authors = authors
        self.names = names
        return

    # ---------------------------------------------------------------------
    def activity_label(self, tablename, method):
        """
            Get a label for the activity

            @param tablename: the tablename
            @param method: the method ("create" or "update")
        """

        T = current.T

        activity = None
        if tablename == "pr_filter":
            if method == "create":
                activity = T("Saved a Filter")
            elif method == "update":
                activity = T("Updated a Filter")
        elif tablename == "gis_config":
            if method == "create":
                activity = T("Saved a Map")
            elif method == "update":
                activity = T("Updated a Map")
        elif tablename == "org_facility":
            if method == "create":
                activity = T("Added a Place")
            elif method == "update":
                activity = T("Edited a Place")
        elif tablename == "org_organisation":
            if method == "create":
                activity = T("Added an Organization")
            elif method == "update":
                activity = T("Edited an Organization")
        elif tablename == "project_activity":
            if method == "create":
                activity = T("Added an Activity")
            elif method == "update":
                activity = T("Edited an Activity")
        elif tablename == "stats_people":
            if method == "create":
                activity = T("Added People")
            elif method == "update":
                activity = T("Edited People")
        elif tablename == "vulnerability_evac_route":
            if method == "create":
                activity = T("Added an Evacuation Route")
            elif method == "update":
                activity = T("Edited an Evacuation Route")
        elif tablename == "vulnerability_risk":
            if method == "create":
                activity = T("Added a Hazard")
            elif method == "update":
                activity = T("Edited a Hazard")
        return activity

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

        raw = record._row
        author = record["s3_audit.user_id"]
        timestmp = record["s3_audit.timestmp"]
        author_id = raw["s3_audit.user_id"]
        method = raw["s3_audit.method"]
        tablename = raw["s3_audit.tablename"]
        record_id = raw["s3_audit.record_id"]

        T = current.T

        if tablename == "pr_filter":
            label = T("Saved Filters")
            url = URL(c="default", f="index", args=["filters"])
        elif tablename == "gis_config":
            label = self.names[tablename][record_id]
            url = URL(c="gis", f="index", vars={"config": record_id})
        else:
            label = self.names[tablename][record_id]
            c, f = tablename.split("_", 1)
            url = URL(c=c, f=f, args=[record_id, "read"])

        body = P(self.activity_label(tablename, method),
                 BR(),
                 A(label, _href=url),
                 )

        avatar, person_url = self.authors[author_id]
        author = A(author, _href=person_url)
        avatar = A(avatar, _href=person_url, _class="pull-left")

        # Render the item
        item = DIV(avatar,
                   DIV(H5(author,
                          _class="media-heading",
                          ),
                       P(timestmp, _class="activity-timestmp"),
                       body,
                       _class="media-body",
                       ),
                   _class="media",
                   )

        return item

# For access from custom controllers (e.g. homepage)
current.response.s3.render_log = ActivityLogLayout()

# -----------------------------------------------------------------------------
def customise_s3_audit_controller(**attr):

    from s3 import s3_auth_user_represent_name, FS, S3OptionsFilter, S3DateFilter
    current.db.s3_audit.user_id.represent = s3_auth_user_represent_name

    T = current.T
    tablename = "s3_audit"

    s3 = current.response.s3
    s3.filter = (FS("~.method") != "delete")
    s3.crud_strings[tablename] = {
        "title_list": T("Activity Log"),
    }

    USER = T("User")
    filter_widgets = [S3OptionsFilter("user_id",
                                      label = USER,
                                      ),
                      S3OptionsFilter("tablename"),
                      S3OptionsFilter("method"),
                      S3DateFilter("timestmp",
                                   label = None,
                                   hide_time = True,
                                   input_labels = {"ge": "From", "le": "To"},
                                   ),
                      ]

    report_fields = ["tablename", "method", (USER, "user_id")]
    report_options = Storage(
            rows = report_fields,
            cols = report_fields,
            fact = [(T("Number of Records"), "count(id)"),
                    (T("Number of Tables"), "count(tablename)"),
                    ],
            defaults = Storage(rows = "tablename",
                               cols = "method",
                               fact = "count(id)",
                               chart = "breakdown:rows",
                               table = "collapse",
                               totals = True,
                               )
                )
    current.s3db.configure(tablename,
                           filter_widgets = filter_widgets,
                           filter_formstyle = filter_formstyle,
                           insertable = False,
                           list_fields = ["id",
                                          (T("Date/Time"), "timestmp"),
                                          (T("User"), "user_id"),
                                          "method",
                                          "tablename",
                                          (T("Record ID"), "record_id"),
                                          ],
                           list_layout = s3.render_log,
                           orderby = "s3_audit.timestmp desc",
                           report_options = report_options,
                           summary = [{"name": "table",
                                       "label": "Table",
                                       "widgets": [{"method": "datatable"}]
                                       },
                                      {"name": "charts",
                                       "label": "Charts",
                                       "widgets": [{"method": "report", "ajax_init": True}]
                                       },
                                      ],
                           )

    return attr

settings.customise_s3_audit_controller = customise_s3_audit_controller

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
    #("event", Storage(
    #    name_nice = T("Events"),
    #    #description = "Events",
    #    restricted = True,
    #    module_type = None
    #)),
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
    #("water", Storage(
    #    name_nice = T("Water"),
    #    restricted = True,
    #    module_type = None
    #)),
])
