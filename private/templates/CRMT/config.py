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
from s3.s3filter import S3OptionsFilter, S3DateFilter
from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineComponentMultiSelectWidget
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
settings.auth.registration_requests_organisation_group = True
settings.auth.registration_organisation_group_required = True
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

# Uncomment to pass Addresses imported from CSV to a Geocoder to try and automate Lat/Lon
settings.gis.geocode_imported_addresses = "google"

# Uncomment to Hide the Toolbar from the main Map
settings.gis.toolbar = False
# Hide unnecessary Toolbar items
settings.gis.nav_controls = False
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
     "f":"resident",
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
                        "widgets": [{"method": "report2"}]
                        },
                       {"name": "map",
                        "label": "Map",
                        "widgets": [{"method": "map"}]
                        },
                       ]

# -----------------------------------------------------------------------------
# Filter forms
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
def customize_pr_person(**attr):
    """
        Customize pr_person controller
    """

    s3db = current.s3db
    s3 = current.response.s3

    tablename = "pr_person"
    table = s3db.pr_person

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

        if r.interactive or r.representation == "aadata":
            from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent
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

            MOBILE = settings.get_ui_label_mobile_phone()
            EMAIL = T("Email")

            htable = s3db.hrm_human_resource
            htable.organisation_id.widget = None
            site_field = htable.site_id
            represent = S3Represent(lookup="org_site")
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

            # Hide Labels when just 1 column in inline form
            s3db.pr_contact.value.label = ""

            image_field = s3db.pr_image.image
            image_field.label = ""
            # ImageCrop widget doesn't currently work within an Inline Form
            image_field.widget = None

            hr_fields = ["organisation_id",
                         "job_title_id",
                         "site_id",
                         ]
            #if r.method in ("create", "update"):
            #    # Context from a Profile page?"
            #    organisation_id = current.request.get_vars.get("(organisation)", None)
            #    if organisation_id:
            #        field = s3db.hrm_human_resource.organisation_id
            #        field.default = organisation_id
            #        field.readable = field.writable = False
            #        hr_fields.remove("organisation_id")

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
                        filterby = dict(field = "contact_method",
                                        options = "SMS"
                                        )
                    ),
                    S3SQLInlineComponent(
                        "image",
                        name = "image",
                        label = T("Photo"),
                        multiple = False,
                        fields = ["image"],
                    ),
                ]

            list_fields = [(current.messages.ORGANISATION, "human_resource.organisation_id"),
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

            # Return to List view after create/update/delete (unless done via Modal)
            url_next = URL(c="pr", f="person")

            s3db.configure(tablename,
                           create_next = url_next,
                           delete_next = url_next,
                           update_next = url_next,
                           crud_form = crud_form,
                           list_fields = list_fields,
                           # Don't include a Create form in 'More' popups
                           #listadd = False if r.method=="datalist" else True,
                           #list_layout = render_contacts,
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

    request = current.request
    if "summary" in request.args:
        # Default the Coalition Filter
        auth = current.auth
        if auth.is_logged_in():
            org_group_id = auth.user.org_group_id
            if org_group_id:
                coalition = request.get_vars.get("activity_group.group_id__belongs", None)
                if not coalition:
                    request.get_vars["activity_group.group_id__belongs"] = str(org_group_id)

    # Custom PreP
    s3 = current.response.s3
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)

        if r.interactive:
            s3db = current.s3db
            tablename = "project_activity"
            table = s3db[tablename]
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

            if r.method == "summary":
                list_fields = ["date",
                               "name",
                               "activity_type_id",
                               "activity_group$group_id",
                               "location_id",
                               "person_id",
                               "comments",
                               ]

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
                                  S3DateFilter("date",
                                               label=None,
                                               hide_time=True,
                                               input_labels = {"ge": "From", "le": "To"}
                                               )
                                  ]

                s3db.configure(tablename,
                               filter_widgets = filter_widgets,
                               filter_formstyle = filter_formstyle,
                               list_fields = list_fields,
                               )
        return True
    s3.prep = custom_prep

    attr["hide_filter"] = False

    # Remove rheader
    attr["rheader"] = None

    return attr

settings.ui.customize_project_activity = customize_project_activity

# -----------------------------------------------------------------------------
# Incidents (unused)
# -----------------------------------------------------------------------------
def customize_event_incident_report(**attr):
    """
        Customize event_incident_report controller
    """

    request = current.request
    if "summary" in request.args:
        # Default the Coalition Filter
        auth = current.auth
        if auth.is_logged_in():
            org_group_id = auth.user.org_group_id
            if org_group_id:
                coalition = request.get_vars.get("incident_report_group.group_id__belongs", None)
                if not coalition:
                    request.get_vars["incident_report_group.group_id__belongs"] = str(org_group_id)

    # Custom PreP
    s3 = current.response.s3
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)

        if r.interactive:
            s3db = current.s3db
            tablename = "event_incident_report"
            table = s3db[tablename]
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
            field.requires = IS_ADD_PERSON_WIDGET2()
            field.widget = S3AddPersonWidget2(controller="pr")

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

            # Hide Labels when just 1 column in inline form
            s3db.doc_document.file.label = ""
            s3db.event_incident_report_group.group_id.label = ""

            # Custom Crud Form
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

            s3db.configure(tablename,
                           crud_form = crud_form,
                           )

            if r.method == "summary":
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
                               filter_widgets = filter_widgets,
                               filter_formstyle = filter_formstyle,
                               )

        return True
    s3.prep = custom_prep

    attr["hide_filter"] = False

    # Remove rheader
    attr["rheader"] = None

    return attr

settings.ui.customize_event_incident_report = customize_event_incident_report

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
            field = ftable.location_id
            field.label = T("Address")
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
        elif r.method == "validate":
            # Need to override .requires here too
            current.s3db.org_facility.location_id.requires = None

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
def customize_org_facility(**attr):
    """
        Customize org_facility controller
    """

    request = current.request
    if "summary" in request.args:
        # Default the Coalition Filter
        auth = current.auth
        if auth.is_logged_in():
            org_group_id = auth.user.org_group_id
            if org_group_id:
                coalition = request.get_vars.get("site_org_group.group_id__belongs", None)
                if not coalition:
                    request.get_vars["site_org_group.group_id__belongs"] = str(org_group_id)

    # Custom PreP
    s3 = current.response.s3
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)

        s3db = current.s3db
        tablename = "org_facility"
        if r.interactive:

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

            if r.method in ("create", "update"):
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

            elif r.method == "summary":

                #s3db.org_facility_type.name.label = T("Type of Place")
                list_fields = ["name",
                               "facility_type.name",
                               "organisation_id",
                               "facility_group$group_id",
                               "location_id",
                               "comments",
                               ]

                filter_widgets = [S3OptionsFilter("site_org_group.group_id",
                                                  label=T("Coalition"),
                                                  represent="%(name)s",
                                                  widget="multiselect",
                                                  ),
                                  S3OptionsFilter("site_facility_type.facility_type_id",
                                                  label=T("Type of Place"),
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
                               # Hide Open & Delete dataTable action buttons
                               editable = False,
                               deletable = False,
                               filter_widgets = filter_widgets,
                               filter_formstyle = filter_formstyle,
                               list_fields = list_fields,
                               )

        elif r.representation == "plain" and \
             r.method != "search":
            # Map Popups
            table = s3db.org_facility
            table.location_id.label = T("Address")
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
# Residents
#-----------------------------------------------------------------------------
def customize_stats_resident(**attr):
    """
        Customize stats_resident controller
    """

    request = current.request
    if "summary" in request.args:
        # Default the Coalition Filter
        auth = current.auth
        if auth.is_logged_in():
            org_group_id = auth.user.org_group_id
            if org_group_id:
                coalition = request.get_vars.get("resident_group.group_id__belongs", None)
                if not coalition:
                    request.get_vars["resident_group.group_id__belongs"] = str(org_group_id)

    # Custom PreP
    s3 = current.response.s3
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)

        if r.interactive:
            s3db = current.s3db
            tablename = "stats_resident"
            table = s3db[tablename]
            
            #TEMPORARY - replace with another resource?
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
            
            field = table.location_id
            # L3s only
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
            table.location_id.label = "" # Gets replaced by widget
            table.location_id.requires = IS_LOCATION_SELECTOR2(levels=["L3"])
            table.location_id.widget = S3LocationSelectorWidget2(levels=["L3"],
                                                                 hide_lx=False,
                                                                 reverse_lx=True,
                                                                 show_postcode=True,
                                                                 show_map=False,
                                                                 )

            field = table.person_id
            field.comment = None
            field.requires = IS_ADD_PERSON_WIDGET2()
            field.widget = S3AddPersonWidget2(controller="pr")

            # Hide Labels when just 1 column in inline form
            s3db.doc_document.file.label = ""
            current.db.stats_resident_group.group_id.label = ""

            # Custom Crud Form
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

            if r.method == "summary":
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
                               # Hide Open & Delete dataTable action buttons
                               editable = False,
                               deletable = False,
                               filter_widgets = filter_widgets,
                               filter_formstyle = filter_formstyle,
                               )

        return True
    s3.prep = custom_prep

    attr["hide_filter"] = False

    return attr

settings.ui.customize_stats_resident = customize_stats_resident

#-----------------------------------------------------------------------------
# Trained People (unused)
#-----------------------------------------------------------------------------
def customize_stats_trained(**attr):
    """
        Customize stats_trained controller
    """

    request = current.request
    if "summary" in request.args:
        # Default the Coalition Filter
        auth = current.auth
        if auth.is_logged_in():
            org_group_id = auth.user.org_group_id
            if org_group_id:
                coalition = request.get_vars.get("trained_group.group_id__belongs", None)
                if not coalition:
                    request.get_vars["trained_group.group_id__belongs"] = str(org_group_id)

    # Custom PreP
    s3 = current.response.s3
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)

        if r.interactive:
            s3db = current.s3db
            tablename = "stats_trained"
            table = s3db[tablename]
            table.location_id.label = "" # Gets replaced by widget
            table.location_id.requires = IS_LOCATION_SELECTOR2(levels=["L3"])
            table.location_id.widget = S3LocationSelectorWidget2(levels=["L3"],
                                                                 hide_lx=False,
                                                                 reverse_lx=True,
                                                                 show_postcode=True,
                                                                 show_map=False,
                                                                 )

            field = table.person_id
            field.comment = None
            field.requires = IS_ADD_PERSON_WIDGET2()
            field.widget = S3AddPersonWidget2(controller="pr")

            # Hide Labels when just 1 column in inline form
            s3db.doc_document.file.label = ""
            current.db.stats_trained_group.group_id.label = ""

            # Custom Crud Form
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

            s3db.configure(tablename,
                           crud_form = crud_form,
                           )
    
            if r.method == "summary":
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
                               # Hide Open & Delete dataTable action buttons
                               editable = False,
                               deletable = False,
                               filter_widgets = filter_widgets,
                               filter_formstyle = filter_formstyle,
                               )
        return True
    s3.prep = custom_prep

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

    request = current.request
    if "summary" in request.args:
        # Default the Coalition Filter
        auth = current.auth
        if auth.is_logged_in():
            org_group_id = auth.user.org_group_id
            if org_group_id:
                coalition = request.get_vars.get("evac_route_group.group_id__belongs", None)
                if not coalition:
                    request.get_vars["evac_route_group.group_id__belongs"] = str(org_group_id)

    # Custom PreP
    s3 = current.response.s3
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)

        if r.interactive:
            s3db = current.s3db
            tablename = "vulnerability_evac_route"
            table = s3db[tablename]
            table.location_id.label = "" # Gets replaced by widget
            table.location_id.requires = IS_LOCATION_SELECTOR2(levels=["L3"])
            table.location_id.widget = S3LocationSelectorWidget2(levels=["L3"],
                                                                 polygons=True,
                                                                 )

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

            if r.method == "summary":
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
                               # Hide Open & Delete dataTable action buttons
                               editable = False,
                               deletable = False,
                               filter_widgets = filter_widgets,
                               filter_formstyle = filter_formstyle,
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

    request = current.request
    if "summary" in request.args:
        # Default the Coalition Filter
        auth = current.auth
        if auth.is_logged_in():
            org_group_id = auth.user.org_group_id
            if org_group_id:
                coalition = request.get_vars.get("risk_group.group_id__belongs", None)
                if not coalition:
                    request.get_vars["risk_group.group_id__belongs"] = str(org_group_id)

    # Custom PreP
    s3 = current.response.s3
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)

        if r.interactive:
            s3db = current.s3db
            tablename = "vulnerability_risk"
            
            #TEMPORARY - replace with another resource?
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
            
            table = s3db[tablename]
            field = table.location_id
            field.label = "" # Gets replaced by widget
            field.requires = IS_LOCATION_SELECTOR2(levels=["L3"])
            field.widget = S3LocationSelectorWidget2(levels=["L3"],
                                                     hide_lx=False,
                                                     reverse_lx=True,
                                                     polygons=True,
                                                     #show_address=True,
                                                     #show_postcode=True,
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
    
            if r.method == "summary":
                # Not needed now that Risk data is moved to WMS
                # Filter out data not associated with any Coalition
                #from s3.s3resource import S3FieldSelector
                #group_filter = (S3FieldSelector("group.id") != None)
                #r.resource.add_filter(group_filter)

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
                               # Hide Open & Delete dataTable action buttons
                               editable = False,
                               deletable = False,
                               filter_widgets = filter_widgets,
                               filter_formstyle = filter_formstyle,
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
