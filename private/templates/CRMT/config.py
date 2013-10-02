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

from s3.s3utils import s3_avatar_represent

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
settings.auth.registration_requires_verification = False
settings.auth.registration_requests_organisation = True
settings.auth.registration_organisation_required = False
settings.auth.registration_requests_organisation_group = True
settings.auth.registration_organisation_group_required = False
settings.auth.registration_requests_site = False

settings.auth.registration_link_user_to = {"staff": T("Staff")}
settings.auth.registration_link_user_to_default = "staff"

settings.auth.record_approval = False

# Approval emails get sent to all admins
settings.mail.approver = "ADMIN"

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
    if tablename in ("gis_config",
                     "org_facility",
                     "org_organisation",
                     "pr_filter",
                     "project_activity",
                     "stats_people",
                     "vulnerability_evac_route",
                     "vulnerability_risk",
                     ):
        # Perform normal Audit
        return True
    else:
        # Don't Audit non user-visible resources
        return False

settings.security.audit_write = audit_write

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
settings.ui.hide_report_options = False
#settings.gis.map_height = 600
#settings.gis.map_width = 854

settings.base.youtube_id = "HR-FtR2XkBU"
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

# Uncomment to pass Addresses imported from CSV to a Geocoder to try and automate Lat/Lon
settings.gis.geocode_imported_addresses = "google"

# Uncomment to Hide the Toolbar from the main Map
settings.gis.toolbar = False
# Hide unnecessary Toolbar items
#settings.gis.nav_controls = False
# Uncomment to use CMS to provide Metadata on Map Layers
settings.gis.layer_metadata = True
# Uncomment to hide Layer Properties tool
settings.gis.layer_properties = False
# Uncomment to hide the Base Layers folder in the LayerTree
settings.gis.layer_tree_base = False
# Uncomment to hide the Overlays folder in the LayerTree
settings.gis.layer_tree_overlays = False
# Uncomment to not expand the folders in the LayerTree by default
settings.gis.layer_tree_expanded = False
# Uncomment to have custom folders in the LayerTree use Radio Buttons
settings.gis.layer_tree_radio = True
settings.gis.layers_label = "Map Data"
# Uncomment to display the Map Legend as a floating DIV
settings.gis.legend = "float"
# Mouse Position: 'normal', 'mgrs' or None
settings.gis.mouse_position = None
# Uncomment to hide the Overview map (doesn't work with Google Maps)
settings.gis.overview = False
# Uncomment to hide the permalink control (we have our own saved maps functionality)
settings.gis.permalink = False
# Uncomment to rename Overlays in Layer Tree
#settings.gis.label_overlays = "Community Data"

# Set Map to fill the container
settings.gis.map_width = 1170

# Don't simplify Polygons as much to retain their original shape
settings.gis.simplify_tolerance = 0.0001

# Add Person Widget
settings.pr.request_dob = False
settings.pr.request_gender = False

# -----------------------------------------------------------------------------
# Finance settings
settings.fin.currencies = {
    "USD" : T("United States Dollars"),
}

settings.search.filter_manager = True
settings.search.filter_manager_save = "Save"
settings.search.filter_manager_update = "Update"

# -----------------------------------------------------------------------------
# Menu
current.response.menu = [
    {"name": T("Organizations"),
     "c":"org", 
     "f":"organisation",
     "icon": "icon-sitemap"
     },
    {"name": T("Places"),
     "c":"org", 
     "f":"facility",
     "icon": "icon-home"
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
    ]

for item in current.response.menu:
    item["url"] = URL(item["c"], item["f"])
# -----------------------------------------------------------------------------
# Summary Pages
settings.ui.summary = [{"common": True,
                        "name": "cms",
                        "widgets": [{"method": "cms"}]
                        },
                       {"name": "table",
                        "label": "Table",
                        "widgets": [{"method": "datatable"}]
                        },
                       {"name": "charts",
                        "label": "Charts",
                        "widgets": [{"method": "report2", "ajax_init": True}]
                        },
                       {"name": "map",
                        "label": "Map",
                        "widgets": [{"method": "map", "ajax_init": True}],
                        },
                       ]

settings.ui.filter_auto_submit = 750
settings.ui.report_auto_submit = 750
                       
# -----------------------------------------------------------------------------
# Filter forms - style for Summary pages
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
# Contacts
# -----------------------------------------------------------------------------
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

def customize_pr_person(**attr):
    """
        Customize pr_person controller
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
                           (T("Job Title"), "human_resource.job_title_id"),
                           (T("Office"), "human_resource.site_id"),
                           ]
            is_logged_in = current.auth.is_logged_in()
            if is_logged_in:
                # Don't include Email/Phone for unauthenticated users
                MOBILE = settings.get_ui_label_mobile_phone()
                EMAIL = T("Email")

                list_fields += [(MOBILE, "phone.value"),
                                (EMAIL, "email.value"),
                                ]
            s3db.configure(tablename,
                           list_fields = list_fields,
                           )

        if r.interactive:
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

            # Custom Form (Read/Create/Update)
            from s3.s3fields import S3Represent
            from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent
            if r.method in ("create", "update"):
                # Custom Widgets/Validators
                widgets = True
                from s3.s3validators import IS_ONE_OF
                from s3layouts import S3AddResourceLink
            else:
                widgets = False

            htable = s3db.hrm_human_resource
            htable.organisation_id.widget = None
            site_field = htable.site_id
            represent = S3Represent(lookup="org_site")
            site_field.represent = represent
            if widgets:
                site_field.requires = IS_ONE_OF(db, "org_site.site_id",
                                                represent,
                                                orderby = "org_site.name")
                site_field.comment = S3AddResourceLink(c="org", f="office",
                                                       vars={"child": "site_id"},
                                                       label=T("Add New Office"),
                                                       title=T("Office"),
                                                       tooltip=T("If you don't see the Office in the list, you can add a new one by clicking link 'Add New Office'."))

            # Hide Labels when just 1 column in inline form
            s3db.pr_contact.value.label = ""

            s3db.pr_image.profile.default = True
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
            s3db.pr_person_user.org_group_id = Field.Lazy(user_coalition)

            s3_sql_custom_fields = [
                    "first_name",
                    #"middle_name",
                    "last_name",
                    S3SQLInlineComponent(
                        "human_resource",
                        name = "human_resource",
                        label = "" if widgets else T("Organization"),
                        multiple = False,
                        fields = hr_fields,
                        filterby = dict(field = "contact_method",
                                        options = "SMS"
                                        )
                    ),
                    S3SQLInlineComponent(
                        "user",
                        name = "user",
                        label = T("Coalition"),
                        multiple = False,
                        fields = [],
                        # Fields needed to load for Virtual Fields
                        extra_fields = ["user_id"],
                        virtual_fields = [("", "org_group_id"),
                                          ],
                    ),
                    S3SQLInlineComponent(
                        "image",
                        name = "image",
                        label = T("Photo"),
                        multiple = False,
                        fields = ["image"],
                    ),
                ]

            # Don't include Email/Phone for unauthenticated users
            if is_logged_in:
                s3_sql_custom_fields.insert(4,
                                            S3SQLInlineComponent(
                                            "contact",
                                            name = "phone",
                                            label = MOBILE,
                                            multiple = False,
                                            fields = ["value"],
                                            filterby = dict(field = "contact_method",
                                                            options = "SMS")),
                                            )
                s3_sql_custom_fields.insert(4,
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

            # Return to List view after create/update/delete (unless done via Modal)
            url_next = URL(c="pr", f="person")

            s3db.configure(tablename,
                           create_next = url_next,
                           delete_next = url_next,
                           update_next = url_next,
                           crud_form = crud_form,
                           # Don't include a Create form in 'More' popups
                           #listadd = False if r.method=="datalist" else True,
                           )

            # Move fields to their desired Locations
            # Disabled as breaks submission of inline_component
            #i18n = []
            #iappend = i18n.append
            #iappend('''i18n.office="%s"''' % T("Office"))
            #iappend('''i18n.organisation="%s"''' % T("Organization"))
            #iappend('''i18n.job_title="%s"''' % T("Job Title"))
            #i18n = '''\n'''.join(i18n)
            #s3.js_global.append(i18n)
            #s3.scripts.append('/%s/static/themes/DRMP/js/contacts.js' % current.request.application)

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
            actions = [dict(label=str(T("Open")),
                            _class="action-btn",
                            url=URL(c="pr", f="person",
                                    args=["[id]", "read"]))
                       ]
            # All users just get "Open"
            #db = current.db
            #auth = current.auth
            #has_permission = auth.s3_has_permission
            #ownership_required = auth.permission.ownership_required
            #s3_accessible_query = auth.s3_accessible_query
            #table = s3db.pr_person
            #if has_permission("update", table):
            #    action = dict(label=str(T("Edit")),
            #                  _class="action-btn",
            #                  url=URL(c="pr", f="person",
            #                          args=["[id]", "update"]),
            #                  )
            #    if ownership_required("update", table):
            #        # Check which records can be updated
            #        query = s3_accessible_query("update", table)
            #        rows = db(query).select(table._id)
            #        restrict = []
            #        rappend = restrict.append
            #        for row in rows:
            #            row_id = row.get("id", None)
            #            if row_id:
            #                rappend(str(row_id))
            #        action["restrict"] = restrict
            #    actions.append(action)
            #if has_permission("delete", table):
            #    action = dict(label=str(T("Delete")),
            #                  _class="action-btn",
            #                  url=URL(c="pr", f="person",
            #                          args=["[id]", "delete"]),
            #                  )
            #    if ownership_required("delete", table):
            #        # Check which records can be deleted
            #        query = s3_accessible_query("delete", table)
            #        rows = db(query).select(table._id)
            #        restrict = []
            #        rappend = restrict.append
            #        for row in rows:
            #            row_id = row.get("id", None)
            #            if row_id:
            #                rappend(str(row_id))
            #        action["restrict"] = restrict
            #    actions.append(action)
            s3.actions = actions
            if "form" in output:
                output["form"].add_class("pr_person")
            elif "item" in output and hasattr(output["item"], "add_class"):
                output["item"].add_class("pr_person")

        return output
    s3.postp = custom_postp

    return attr

settings.ui.customize_pr_person = customize_pr_person

# -----------------------------------------------------------------------------
# Activities
# -----------------------------------------------------------------------------
def customize_project_activity(**attr):
    """
        Customize project_activity controller
    """

    s3db = current.s3db
    request = current.request
    if "summary" in request.args:
        coalition = request.get_vars.get("activity_group.group_id__belongs", None)
        if not coalition:
            # Default the Coalition Filter
            auth = current.auth
            org_group_id = auth.is_logged_in() and auth.user.org_group_id
            if org_group_id:
                request.get_vars["activity_group.group_id__belongs"] = str(org_group_id)
            else:
                # Filter to all Coalitions
                gtable = s3db.org_group
                rows = current.db(gtable.deleted == False).select(gtable.id)
                request.get_vars["activity_group.group_id__belongs"] = ",".join([str(row.id) for row in rows])

    # Custom PreP
    s3 = current.response.s3
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)

        tablename = "project_activity"
        table = s3db[tablename]

        if r.method == "summary" or r.representation == "aadata":
            # Modify list_fields
            list_fields = ["date",
                           "name",
                           "activity_type_id",
                           "activity_group.group_id",
                           "location_id",
                           "person_id",
                           "comments",
                           ]

            s3db.configure(tablename,
                           list_fields = list_fields,
                           )

        elif r.method == "report2":
            s3db.project_activity_group.group_id.label = T("Coalition")

        if r.interactive or r.representation == "json":
            # CRUD Strings / Represent
            table.location_id.label = T("Address")
            table.location_id.represent = s3db.gis_LocationRepresent(address_only=True)
            s3db.project_activity_group.group_id.label = T("Coalition")

            if r.method in ("summary", "report2"):
                from s3.s3filter import S3OptionsFilter, S3DateFilter
                filter_widgets = [S3OptionsFilter("activity_group.group_id",
                                                  label=T("Coalition"),
                                                  represent="%(name)s",
                                                  widget="multiselect",
                                                  header=True,
                                                  ),
                                  S3OptionsFilter("activity_type_id",
                                                  label=T("Activity Type"),
                                                  represent="%(name)s",
                                                  widget="multiselect",
                                                  header=True,
                                                  ),
                                  S3DateFilter("date",
                                               label=None,
                                               hide_time=True,
                                               input_labels = {"ge": "From", "le": "To"}
                                               )
                                  ]

                # @ToDo: Month/Year Lazy virtual fields (like in PM tool)
                report_fields = [#"name",
                                 "activity_type_id",
                                 "activity_group.group_id",
                                 "location_id$L3",
                                 ]

                report_options = Storage(
                    rows=report_fields,
                    cols=report_fields,
                    fact=[("count(name)", T("Number of Activities"))],
                    defaults=Storage(rows="activity.activity_type_id",
                                     #cols="activity_group.group_id",
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

            else:
                # Custom Form (Read/Create/Update)
                from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent
                if r.method in ("create", "update"):
                    # Custom Widgets/Validators
                    widgets = True
                    from s3.s3validators import IS_ADD_PERSON_WIDGET2, IS_LOCATION_SELECTOR2
                    from s3.s3widgets import S3AddPersonWidget2, S3LocationSelectorWidget2
                else:
                    widgets = False

                if widgets:
                    field = table.location_id
                    field.label = "" # Gets replaced by widget
                    field.requires = IS_LOCATION_SELECTOR2(levels=["L3"])
                    field.widget = S3LocationSelectorWidget2(levels=["L3"],
                                                             hide_lx=False,
                                                             reverse_lx=True,
                                                             show_address=True,
                                                             show_postcode=True,
                                                             )
                field = table.person_id
                field.comment = None
                if widgets:
                    field.requires = IS_ADD_PERSON_WIDGET2()
                    field.widget = S3AddPersonWidget2(controller="pr")
                
                # Hide Labels when just 1 column in inline form
                s3db.doc_document.file.label = ""
                s3db.project_activity_group.group_id.label = ""
    
                # Custom Crud Form
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
                    S3SQLInlineComponent(
                        "document",
                        name = "file",
                        label = T("Files"),
                        fields = ["file",
                                  #"comments",
                                  ],
                    ),
                    "comments",
                )

                s3db.configure(tablename,
                               crud_form = crud_form,
                               )

        return True
    s3.prep = custom_prep

    attr["hide_filter"] = False

    # Remove rheader
    attr["rheader"] = None

    return attr

settings.ui.customize_project_activity = customize_project_activity

# -----------------------------------------------------------------------------
# Organisations
# -----------------------------------------------------------------------------
def org_facility_types(row):
    """
        The Types of the Facility
        - required since we can't have a component within an Inline Component
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
def customize_org_organisation(**attr):
    """
        Customize org_organisation controller
    """

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

        if r.method == "validate":
            # Need to override .requires here too
            current.s3db.org_facility.location_id.requires = None

        elif r.method == "summary" or r.representation == "aadata":
            # Modify list_fields
            list_fields = ["id",
                           "name",
                           (T("Coalitions"), "group_membership.group_id"),
                           (T("Sectors"), "sector_organisation.sector_id"),
                           (T("Services"), "service_organisation.service_id"),
                           "comments",
                           ]

            s3db.configure(tablename,
                           list_fields = list_fields,
                           )

        elif r.method == "report2":
            s3db.org_group_membership.group_id.label = T("Coalition")

        if (r.interactive or r.representation=="json") and not r.component:
            # CRUD Strings / Represent

            if r.method in ("summary", "report2"):
                from s3.s3filter import S3OptionsFilter
                filter_widgets = [S3OptionsFilter("group_membership.group_id",
                                                  label=T("Coalition"),
                                                  represent="%(name)s",
                                                  widget="multiselect",
                                                  header=True,
                                                  ),
                                  S3OptionsFilter("sector_organisation.sector_id",
                                                  label=T("Sector"),
                                                  represent="%(name)s",
                                                  widget="multiselect",
                                                  header=True,
                                                  ),
                                  S3OptionsFilter("service_organisation.service_id",
                                                  label=T("Service"),
                                                  represent="%(name)s",
                                                  widget="multiselect",
                                                  header=True,
                                                  ),
                                  ]

                s3.crud_strings.org_organisation.title_report = T("Organization Matrix")

                # Custom Report Fields
                report_fields = [#"name",
                                 (T("Coalitions"), "group_membership.group_id"),
                                 (T("Sectors"), "sector_organisation.sector_id"),
                                 (T("Services"), "service_organisation.service_id"),
                                 ]

                report_options = Storage(
                    rows = report_fields,
                    cols = report_fields,
                    fact = [("count(name)", T("Number of Organizations"))],
                    defaults = Storage(rows = "sector_organisation.sector_id",
                                       #cols = "service_organisation.service_id",
                                       fact = "count(name)",
                                       totals = True,
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
                               # No Map for Organisations
                               summary = [s for s in settings.ui.summary if s["name"] != "map"],
                               )

            else:
                # Custom Form (Read/Create/Update)
                from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineComponentMultiSelectWidget

                ftable = s3db.org_facility
                field = ftable.location_id
                field.label = T("Address")
                field.represent = s3db.gis_LocationRepresent(address_only=True)
                # We don't have a widget capable of creating/editing Locations inline
                field.widget = None
                field.writable = False
                # s3forms passes even read-only fields through validation
                field.requires = None
                s3db.configure("org_facility",
                               #editable=False,
                               insertable=False,
                               )
                # We can't include components in an Inline Component
                # => use a readonly virtual field instead
                from gluon import Field
                ftable.facility_types = Field.Lazy(org_facility_types)

                hrtable = s3db.hrm_human_resource
                hrtable.person_id.widget = None
                hrtable.site_id.label = T("Place")

                # Custom Crud Form
                crud_form = S3SQLCustomForm(
                    "name",
                    "logo",
                    S3SQLInlineComponentMultiSelectWidget(
                        "group",
                        label = T("Coalitions"),
                        field = "group_id",
                    ),
                    S3SQLInlineComponentMultiSelectWidget(
                        "sector",
                        label = T("Sectors"),
                        field = "sector_id",
                    ),
                    S3SQLInlineComponentMultiSelectWidget(
                        "service",
                        label = T("Services"),
                        field = "service_id",
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
                        label = T("Organization's Places"),
                        fields = ["name", 
                                  # Only fields within the table are supported
                                  #"facility_type.facility_type_id",
                                  "location_id",
                                  ],
                        # Fields needed to load for Virtual Fields
                        extra_fields = ["site_id"],
                        virtual_fields = [(T("Facility Type"), "facility_types"),
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

                s3db.configure(tablename,
                               crud_form = crud_form,
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
# Places (org_facility)
#-----------------------------------------------------------------------------
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
                    s3_debug("S3GIS", "Upgrade Shapely for Performance enhancements")
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
                    ltable.insert(group_id=p[ctable].id,
                                  site_id=site_id,
                                  )

    # Normal onaccept:
    # Update Affiliation, record ownership and component ownership
    from s3db.org import S3FacilityModel
    S3FacilityModel.org_facility_onaccept(form)

# Ensure callback is accessible to CLI Imports as well as those going via Controller
settings.base.import_callbacks = {"org_facility": {"onaccept": facility_onaccept,
                                                   },
                                  }

def customize_org_facility(**attr):
    """
        Customize org_facility controller
    """

    s3db = current.s3db
    request = current.request
    if "summary" in request.args:
        coalition = request.get_vars.get("site_org_group.group_id__belongs", None)
        if not coalition:
            # Default the Coalition Filter
            auth = current.auth
            org_group_id = auth.is_logged_in() and auth.user.org_group_id
            if org_group_id:
                request.get_vars["site_org_group.group_id__belongs"] = str(org_group_id)
            else:
                # Filter to all Coalitions
                gtable = s3db.org_group
                rows = current.db(gtable.deleted == False).select(gtable.id)
                request.get_vars["site_org_group.group_id__belongs"] = ",".join([str(row.id) for row in rows])

    # Custom PreP
    s3 = current.response.s3
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)

        tablename = "org_facility"
        table = s3db[tablename]

        if r.method == "summary" or r.representation == "aadata":
            # Modify list_fields
            list_fields = ["name",
                           (T("Type of Place"),"facility_type.name"),
                           "organisation_id",
                           "site_org_group.group_id",
                           "location_id",
                           "comments",
                           ]

            s3db.configure(tablename,
                           list_fields=list_fields,
                           )

        elif r.method == "report2":
            s3db.org_site_org_group.group_id.label = T("Coalition")

        if r.interactive or r.representation == "json":
            # CRUD Strings / Represent
            table.location_id.label = T("Address")
            table.location_id.represent = s3db.gis_LocationRepresent(address_only=True)
            s3db.org_site_org_group.group_id.label = T("Coalition")

            s3.crud_strings[tablename] = Storage(
                title_create = T("Add Place"),
                title_display = T("Place Details"),
                title_list = T("Places"),
                title_update = T("Edit Place"),
                title_search = T("Search Places"),
                subtitle_create = T("Add New Place"),
                label_list_button = T("List Places"),
                label_create_button = T("Add Place"),
                label_delete_button = T("Remove Place"),
                msg_record_created = T("Place added"),
                msg_record_modified = T("Place updated"),
                msg_record_deleted = T("Place removed"),
                msg_list_empty = T("No Places currently recorded"))

            if r.method in ("summary", "report2"):
                from s3.s3filter import S3OptionsFilter
                filter_widgets = [S3OptionsFilter("site_org_group.group_id",
                                                  label=T("Coalition"),
                                                  represent="%(name)s",
                                                  widget="multiselect",
                                                  header=True,
                                                  ),
                                  S3OptionsFilter("site_facility_type.facility_type_id",
                                                  label=T("Type of Place"),
                                                  represent="%(name)s",
                                                  widget="multiselect",
                                                  header=True,
                                                  ),
                                  S3OptionsFilter("organisation_id",
                                                  label=T("Organization"),
                                                  represent="%(name)s",
                                                  widget="multiselect",
                                                  header=True,
                                                  ),
                                  ]

                report_fields = [#"name",
                                 (T("Type of Place"),"site_facility_type.facility_type_id"),
                                 "site_org_group.group_id",
                                 "location_id$L3",
                                 "organisation_id",
                                 ]

                report_options = Storage(
                    rows=report_fields,
                    cols=report_fields,
                    fact=[("count(name)", T("Number of Places"))],
                    defaults=Storage(rows="site_facility_type.facility_type_id",
                                     #cols="site_org_group.group_id",
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
            else:
                # Custom Form (Read/Create/Update)
                from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineComponentMultiSelectWidget
                if r.method in ("create", "update"):
                    # Custom Widgets/Validators
                    widgets = True
                    from s3.s3validators import IS_LOCATION_SELECTOR2
                    from s3.s3widgets import S3LocationSelectorWidget2
                else:
                    widgets = False

                if widgets:
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

                # Hide Labels when just 1 column in inline form
                s3db.doc_document.file.label = ""
                s3db.org_site_org_group.group_id.label = ""

                # Custom Crud Form
                crud_form = S3SQLCustomForm(
                    "name",
                    S3SQLInlineComponentMultiSelectWidget(
                        "facility_type",
                        label = T("Type of Place"),
                        field = "facility_type_id",
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
                        label = T("Place's Contacts"),
                        fields = ["person_id",
                                  "job_title_id",
                                  #"email",
                                  #"phone",
                                  ],
                    ),
                    S3SQLInlineComponent(
                        "document",
                        name = "file",
                        label = T("Files"),
                        fields = ["file",
                                  #"comments",
                                  ],
                    ),
                    "comments",
                )
                s3db.configure(tablename,
                               crud_form = crud_form,
                               )

        elif r.representation == "plain" and \
             r.method != "search":
            # Map Popups
            table.location_id.label = T("Address")
            table.location_id.represent = s3db.gis_LocationRepresent(address_only=True)
            table.organisation_id.comment = ""
            s3.crud_strings[tablename].title_display = T("Place Details")
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
# People
#-----------------------------------------------------------------------------
def customize_stats_people(**attr):
    """
        Customize stats_people controller
    """

    s3db = current.s3db
    request = current.request
    if "summary" in request.args:
        coalition = request.get_vars.get("people_group.group_id__belongs", None)
        if not coalition:
            # Default the Coalition Filter
            auth = current.auth
            org_group_id = auth.is_logged_in() and auth.user.org_group_id
            if org_group_id:
                request.get_vars["people_group.group_id__belongs"] = str(org_group_id)
            else:
                # Filter to all Coalitions
                gtable = s3db.org_group
                rows = current.db(gtable.deleted == False).select(gtable.id)
                request.get_vars["people_group.group_id__belongs"] = ",".join([str(row.id) for row in rows])

    # Custom PreP
    s3 = current.response.s3
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)

        tablename = "stats_people"
        table = s3db[tablename]

        # Disable name
        table.name.readable = False
        table.name.writable = False

        if r.method == "summary" or r.representation == "aadata":
            # Modify list_fields
            list_fields = ["id",
                           #"name",
                           "parameter_id",
                           "value",
                           "people_group.group_id",
                           "location_id",
                           "person_id",
                           "comments",
                           ]

            s3db.configure(tablename,
                           list_fields = list_fields,
                           )

            s3db.stats_people_group.group_id.label = T("Coalition")

        elif r.method == "report2":
            s3db.stats_people_group.group_id.label = T("Coalition")

        if r.interactive or r.representation == "json":
            # CRUD Strings / Represent
            #table.location_id.label = T("Address")
            #table.location_id.represent = s3db.gis_LocationRepresent(address_only=True)

            s3.crud_strings[tablename] = Storage(
                title_create = T("Add People"),
                title_display = T("People Details"),
                title_list = T("People"),
                title_update = T("Edit People"),
                title_search = T("Search People"),
                subtitle_create = T("Add New People"),
                label_list_button = T("List People"),
                label_create_button = T("Add People"),
                label_delete_button = T("Remove People"),
                msg_record_created = T("People added"),
                msg_record_modified = T("People updated"),
                msg_record_deleted = T("People removed"),
                msg_list_empty = T("No People currently recorded"))
            
            if r.method in ("summary", "report2"):
                from s3.s3filter import S3OptionsFilter
                filter_widgets = [S3OptionsFilter("people_group.group_id",
                                                  label=T("Coalition"),
                                                  represent="%(name)s",
                                                  widget="multiselect",
                                                  header=True,
                                                  ),
                                  S3OptionsFilter("parameter_id",
                                                  label=T("Type of People"),
                                                  represent="%(name)s",
                                                  widget="multiselect",
                                                  header=True,
                                                  ),
                                  ]

                report_fields = [#"name",
                                 "parameter_id",
                                 "people_group.group_id",
                                 "location_id$L3",
                                 ]

                report_options = Storage(
                    rows=report_fields,
                    cols=report_fields,
                    fact=[("sum(value)", T("Number of People"))],
                    defaults=Storage(rows="people.parameter_id",
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
            else:
                # Custom Form (Read/Create/Update)
                from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent
                if r.method in ("create", "update"):
                    # Custom Widgets/Validators
                    widgets = True
                    from s3.s3validators import IS_ADD_PERSON_WIDGET2, IS_LOCATION_SELECTOR2
                    from s3.s3widgets import S3AddPersonWidget2, S3LocationSelectorWidget2
                else:
                    widgets = False

                if widgets:
                    field = table.location_id
                    field.label = "" # Gets replaced by widget
                    field.requires = IS_LOCATION_SELECTOR2(levels=["L3"])
                    field.widget = S3LocationSelectorWidget2(levels=["L3"],
                                                             hide_lx=False,
                                                             reverse_lx=True,
                                                             show_postcode=True,
                                                             show_map=False,
                                                             )
    
                    # L3s only
                    #from s3.s3fields import S3Represent
                    #from s3.s3validators import IS_ONE_OF
                    #field.requires = IS_ONE_OF(current.db, "gis_location.id",
                    #                           S3Represent(lookup="gis_location"),
                    #                           sort = True,
                    #                           filterby = "level",
                    #                           filter_opts = ["L3"]
                    #                           )
                    # Don't add new Locations here
                    #field.comment = None
                    # Simple dropdown
                    #field.widget = None
                    #field.label = T("City")

                    field = table.person_id
                    field.comment = None
                    field.requires = IS_ADD_PERSON_WIDGET2()
                    field.widget = S3AddPersonWidget2(controller="pr")
    
                # Hide Labels when just 1 column in inline form
                s3db.doc_document.file.label = ""
                current.db.stats_people_group.group_id.label = ""
    
                # Custom Crud Form
                crud_form = S3SQLCustomForm(
                    "name",
                    "parameter_id",
                    "value",
                    S3SQLInlineComponent(
                        "people_group",
                        label = T("Coalition"),
                        fields = ["group_id"],
                        multiple = False,
                    ),
                    "location_id",
                    "person_id",
                    S3SQLInlineComponent(
                        "document",
                        name = "file",
                        label = T("Files"),
                        fields = ["file",
                                  #"comments",
                                  ],
                    ),
                    "comments",
                )
    
                s3db.configure(tablename,
                               crud_form = crud_form,
                               )

        return True
    s3.prep = custom_prep

    attr["hide_filter"] = False

    return attr

settings.ui.customize_stats_people = customize_stats_people

#-----------------------------------------------------------------------------
# Evacuation Routes
#-----------------------------------------------------------------------------
def customize_vulnerability_evac_route(**attr):
    """
        Customize vulnerability_evac_route controller
    """

    s3db = current.s3db
    request = current.request
    if "summary" in request.args:
        coalition = request.get_vars.get("evac_route_group.group_id__belongs", None)
        if not coalition:
            # Default the Coalition Filter
            auth = current.auth
            org_group_id = auth.is_logged_in() and auth.user.org_group_id
            if org_group_id:
                request.get_vars["evac_route_group.group_id__belongs"] = str(org_group_id)
            else:
                # Filter to all Coalitions
                gtable = s3db.org_group
                rows = current.db(gtable.deleted == False).select(gtable.id)
                request.get_vars["evac_route_group.group_id__belongs"] = ",".join([str(row.id) for row in rows])

    # Custom PreP
    s3 = current.response.s3
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)

        tablename = "vulnerability_evac_route"
        table = s3db[tablename]

        if r.method == "summary" or r.representation == "aadata":
            # Modify list_fields
            list_fields = ["id",
                           "name",
                           (T("Hazard Type"),"hazard_id"),
                           "evac_route_group.group_id",
                           "location_id",
                           "comments",
                           ]

            s3db.configure(tablename,
                           list_fields = list_fields,
                           )

        elif r.method == "report2":
            s3db.vulnerability_evac_route_group.group_id.label = T("Coalition")

        if r.interactive or r.representation == "json":
            # CRUD Strings / Represent
            table.location_id.label = T("Address")
            table.location_id.represent = s3db.gis_LocationRepresent(address_only=True)
            s3db.vulnerability_evac_route_group.group_id.label = T("Coalition")

            if r.method in ("summary", "report2"):
                from s3.s3filter import S3OptionsFilter
                filter_widgets = [S3OptionsFilter("evac_route_group.group_id",
                                                  label=T("Coalition"),
                                                  represent="%(name)s",
                                                  widget="multiselect",
                                                  header=True,
                                                  ),
                                  S3OptionsFilter("hazard_id",
                                                  label=T("Hazard Type"),
                                                  represent="%(name)s",
                                                  widget="multiselect",
                                                  header=True,
                                                  ),
                                  ]

                report_fields = [#"name",
                                 (T("Hazard Type"),"hazard_id"),
                                 "evac_route_group.group_id",
                                 "location_id$L3",
                                 ]

                report_options = Storage(
                    rows=report_fields,
                    cols=report_fields,
                    fact=[("count(name)", T("Number of Evacuation Routes"))],
                    defaults=Storage(rows="evac_route.hazard_id",
                                     #cols="evac_route_group.group_id",
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

            else:
                # Custom Form (Read/Create/Update)
                from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent
                if r.method in ("create", "update"):
                    # Custom Widgets/Validators
                    from s3.s3validators import IS_LOCATION_SELECTOR2
                    from s3.s3widgets import S3LocationSelectorWidget2
                    from s3layouts import S3AddResourceLink

                    table.location_id.label = "" # Gets replaced by widget
                    table.location_id.requires = IS_LOCATION_SELECTOR2(levels=["L3"])
                    table.location_id.widget = S3LocationSelectorWidget2(levels=["L3"],
                                                                         polygons=True,
                                                                         )

                    table.hazard_id.comment = S3AddResourceLink(c="vulnerability",
                                                                f="hazard",
                                                                title=T("Add Hazard Type")),

                # Hide Labels when just 1 column in inline form
                s3db.doc_document.file.label = ""
                current.db.vulnerability_evac_route_group.group_id.label = ""

                # Custom Crud Form
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
                    S3SQLInlineComponent(
                        "document",
                        name = "file",
                        label = T("Files"),
                        fields = ["file",
                                  #"comments",
                                  ],
                    ),
                    "comments",
                )
    
                s3db.configure(tablename,
                               crud_form = crud_form,
                               )

        return True
    s3.prep = custom_prep

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
    request = current.request
    if "summary" in request.args:
        coalition = request.get_vars.get("risk_group.group_id__belongs", None)
        if not coalition:
            # Default the Coalition Filter
            auth = current.auth
            org_group_id = auth.is_logged_in() and auth.user.org_group_id
            if org_group_id:
                request.get_vars["risk_group.group_id__belongs"] = str(org_group_id)
            else:
                # Filter to all Coalitions
                gtable = s3db.org_group
                rows = current.db(gtable.deleted == False).select(gtable.id)
                request.get_vars["risk_group.group_id__belongs"] = ",".join([str(row.id) for row in rows])

    # Custom PreP
    s3 = current.response.s3
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)

        tablename = "vulnerability_risk"
        table = s3db[tablename]

        if r.method == "summary" or r.representation == "aadata":
            # Modify list_fields
            list_fields = ["id",
                           "name",
                           (T("Hazard Type"),"hazard_id"),
                           "risk_group.group_id",
                           "location_id",
                           "comments",
                           ]

            s3db.configure(tablename,
                           list_fields = list_fields,
                           )

        elif r.method == "report2":
            s3db.vulnerability_risk_group.group_id.label = T("Coalition")

        if r.interactive or r.representation == "json":
            # CRUD Strings / Represent
            table.location_id.label = T("Address")
            table.location_id.represent = s3db.gis_LocationRepresent(address_only=True)
            s3db.vulnerability_risk_group.group_id.label = T("Coalition")

            s3.crud_strings[tablename] = Storage(
                title_create = T("Add Hazard"),
                title_display = T("Hazard Details"),
                title_list = T("Hazards"),
                title_update = T("Edit Hazard"),
                title_search = T("Search Hazards"),
                subtitle_create = T("Add New Hazard"),
                label_list_button = T("List Hazards"),
                label_create_button = T("Add Hazard"),
                label_delete_button = T("Remove Hazard"),
                msg_record_created = T("Hazard added"),
                msg_record_modified = T("Hazard updated"),
                msg_record_deleted = T("Hazard removed"),
                msg_list_empty = T("No Hazards currently recorded"))
            
            if r.method in ("summary", "report2"):
                # Not needed now that Risk data is moved to WMS
                # Filter out data not associated with any Coalition
                #from s3.s3resource import S3FieldSelector
                #group_filter = (S3FieldSelector("group.id") != None)
                #r.resource.add_filter(group_filter)

                from s3.s3filter import S3OptionsFilter
                filter_widgets = [S3OptionsFilter("risk_group.group_id",
                                                  label=T("Coalition"),
                                                  represent="%(name)s",
                                                  widget="multiselect",
                                                  header=True,
                                                  ),
                                  S3OptionsFilter("hazard_id",
                                                  label=T("Hazard Type"),
                                                  represent="%(name)s",
                                                  widget="multiselect",
                                                  header=True,
                                                  ),
                                  ]

                report_fields = [#"name",
                                 (T("Hazard Type"),"hazard_id"),
                                 "risk_group.group_id",
                                 "location_id$L3",
                                 ]

                report_options = Storage(
                    rows=report_fields,
                    cols=report_fields,
                    fact=[("count(name)", T("Number of Risks"))],
                    defaults=Storage(rows="risk.hazard_id",
                                     #cols="risk_group.group_id",
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

            else:
                # Custom Form (Read/Create/Update)
                from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent
                if r.method in ("create", "update"):
                    # Custom Widgets/Validators
                    from s3.s3validators import IS_LOCATION_SELECTOR2
                    from s3.s3widgets import S3LocationSelectorWidget2

                    field = table.location_id
                    field.label = "" # Gets replaced by widget
                    field.requires = IS_LOCATION_SELECTOR2(levels=["L3"])
                    field.widget = S3LocationSelectorWidget2(levels=["L3"],
                                                             hide_lx=False,
                                                             reverse_lx=True,
                                                             polygons=True,
                                                             show_address=True,
                                                             show_postcode=True,
                                                             )
    
                # Hide Labels when just 1 column in inline form
                s3db.doc_document.file.label = ""
                current.db.vulnerability_risk_group.group_id.label = ""
    
                # Custom Crud Form
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
                    S3SQLInlineComponent(
                        "document",
                        name = "file",
                        label = T("Files"),
                        fields = ["file",
                                  #"comments",
                                  ],
                    ),
                    "comments",
                )
    
                s3db.configure(tablename,
                               crud_form = crud_form,
                               )
    
        # Not needed now that Risk data is moved to WMS
        #elif r.representation== "geojson":
        #    layer = current.request.get_vars.get("layer", None)
        #    if not layer:
        #        # Filter out data not associated with any Coalition
        #        from s3.s3resource import S3FieldSelector
        #        group_filter = (S3FieldSelector("group.id") != None)
        #        r.resource.add_filter(group_filter)

        return True
    s3.prep = custom_prep

    attr["hide_filter"] = False
    attr["rheader"] = None

    return attr

settings.ui.customize_vulnerability_risk = customize_vulnerability_risk

#-----------------------------------------------------------------------------
# Site Activity Log
# -----------------------------------------------------------------------------
def render_log(listid, resource, rfields, record, **attr):
    """
        Custom dataList item renderer for 'Site Activity Logs' on the Home page

        @param listid: the HTML ID for this list
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

    pkey = "s3_audit.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        item_id = "%s-[id]" % listid

    #item_class = "thumbnail"
    item_class = ""

    raw = record._row
    author = record["s3_audit.user_id"]
    author_id = raw["s3_audit.user_id"]
    method = raw["s3_audit.method"]
    tablename = raw["s3_audit.tablename"]
    record_id = raw["s3_audit.record_id"]

    T = current.T
    db = current.db
    s3db = current.s3db

    if tablename == "pr_filter":
        label = T("Saved Filters")
        url = URL(c="default", f="index", args=["filters"])
        if method == "create":
            body = T("Saved a Filter")
        elif method == "update":
            body = T("Updated a Filter")
    elif tablename == "gis_config":
        table = s3db[tablename]
        row = db(table.id == record_id).select(table.name,
                                               limitby=(0, 1)
                                               ).first()
        if row:
            label = row.name or ""
        else:
            label = ""
        url = URL(c="gis", f="index", vars={"config": record_id})
        if method == "create":
            body = T("Saved a Map")
        elif method == "update":
            body = T("Updated a Map")
    else:
        table = s3db[tablename]
        row = db(table.id == record_id).select(table.name,
                                               limitby=(0, 1)
                                               ).first()
        if row:
            label = row.name or ""
        else:
            label = ""
        c, f = tablename.split("_")
        url = URL(c=c, f=f, args=[record_id, "read"])
        if tablename == "org_facility":
            if method == "create":
                body = T("Added a Place")
            elif method == "update":
                body = T("Edited a Place")
        elif tablename == "org_organisation":
            if method == "create":
                body = T("Added an Organization")
            elif method == "update":
                body = T("Edited an Organization")
        elif tablename == "project_activity":
            if method == "create":
                body = T("Added an Activity")
            elif method == "update":
                body = T("Edited an Activity")
        elif tablename == "stats_people":
            if method == "create":
                body = T("Added People")
            elif method == "update":
                body = T("Edited People")
        elif tablename == "vulnerability_evac_route":
            if method == "create":
                body = T("Added an Evacuation Route")
            elif method == "update":
                body = T("Edited an Evacuation Route")
        elif tablename == "vulnerability_risk":
            if method == "create":
                body = T("Added a Hazard")
            elif method == "update":
                body = T("Edited a Hazard")

    body = P(body,
             BR(),
             A(label,
               _href=url),
             )

    # @ToDo: Optimise by not doing DB lookups (especially duplicate) within render, but doing these in the bulk query
    avatar = s3_avatar_represent(author_id,
                                 _class="media-object",
                                 _style="width:50px;padding:5px;padding-top:0px;")
    ptable = s3db.pr_person
    ltable = db.pr_person_user
    query = (ltable.user_id == author_id) & \
            (ltable.pe_id == ptable.pe_id)
    row = db(query).select(ptable.id,
                           limitby=(0, 1)
                           ).first()
    if row:
        person_url = URL(c="pr", f="person", args=[row.id])
    else:
        person_url = "#"
    author = A(author,
               _href=person_url,
               )
    avatar = A(avatar,
               _href=person_url,
               _class="pull-left",
               )

    # Render the item
    item = DIV(DIV(avatar,
  		           DIV(H5(author,
                          _class="media-heading"),
                       body,
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               _class=item_class,
               _id=item_id,
               )

    return item

# For access from custom controllers
current.response.s3.render_log = render_log

# -----------------------------------------------------------------------------
def customize_s3_audit(**attr):
    """
        Customize s3_audit controller
    """

    from s3.s3utils import s3_auth_user_represent_name
    current.db.s3_audit.user_id.represent = s3_auth_user_represent_name

    from s3.s3resource import S3FieldSelector
    current.response.s3.filter = (S3FieldSelector("~.method") != "delete")

    tablename = "s3_audit"
    current.s3db.configure(tablename,
                           list_layout = render_log,
                           orderby = "s3_audit.timestmp desc",
                           insertable = False,
                           list_fields = ["id",
                                          "method",
                                          "user_id",
                                          "tablename",
                                          "record_id",
                                          ],
                           )

    return attr

settings.ui.customize_s3_audit = customize_s3_audit

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
])
