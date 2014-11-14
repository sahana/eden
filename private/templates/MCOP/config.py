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

from s3 import s3_avatar_represent

T = current.T
s3 = current.response.s3
settings = current.deployment_settings

"""
    Puget Sound Common Maritime Operating Picture (MCOP)
"""

# -----------------------------------------------------------------------------
# Pre-Populate
settings.base.prepopulate = ("MCOP", "default/users")

settings.base.system_name = T("Sahana: Puget Sound Common Maritime Operating Picture (MCOP)")
settings.base.system_name_short = T("Sahana")

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
settings.auth.registration_requests_organisation = True
settings.auth.registration_organisation_required = True

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
settings.security.policy = 7 # Apply Controller, Function and Table ACLs
settings.security.map = True

# -----------------------------------------------------------------------------
# Theme (folder to use for views/layout.html)
settings.base.theme = "MCOP"
settings.ui.formstyle_row = "bootstrap"
settings.ui.formstyle = "bootstrap"
settings.ui.filter_formstyle = "bootstrap"
settings.ui.hide_report_options = False
# Uncomment to use S3MultiSelectWidget on all dropdowns (currently the Auth Registration page & LocationSelectorWidget2 listen to this)
settings.ui.multiselect_widget = "search"

# @ToDo: Investigate
settings.ui.use_button_icons = True

# Uncomment to show a default cancel button in standalone create/update forms
settings.ui.default_cancel_button = True

# Uncomment to disable responsive behavior of datatables
# - Disabled until tested
settings.ui.datatables_responsive = False

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

# -----------------------------------------------------------------------------
# GIS settings
# Restrict the Location Selector to just certain countries
settings.gis.countries = ("US",)
# Levels for the LocationSelector
levels = ("L1", "L2", "L3")

# Uncomment to pass Addresses imported from CSV to a Geocoder to try and automate Lat/Lon
#settings.gis.geocode_imported_addresses = "google"

# Until we add support to LocationSelector2 to set dropdowns from LatLons
settings.gis.check_within_parent_boundaries = False
# GeoNames username
settings.gis.geonames_username = "mcop"
# Uncomment to hide Layer Properties tool
#settings.gis.layer_properties = False
# Uncomment to display the Map Legend as a floating DIV
settings.gis.legend = "float"
# Uncomment to prevent showing LatLon in Location Represents
settings.gis.location_represent_address_only = "icon"
# Resources which can be directly added to the main map
settings.gis.poi_create_resources = None

# -----------------------------------------------------------------------------
# Module settings
# Uncomment to customise the list of options for the Priority of a Task.
# NB Be very cautious about doing this (see docstring in modules/s3cfg.py)
# MCOP sets these to match Wrike
settings.project.task_priority_opts = {2: T("High"),
                                       3: T("Normal"),
                                       4: T("Low")
                                       }
# Uncomment to customise the list of options for the Status of a Task.
# NB Be very cautious about doing this (see docstring in modules/s3cfg.py)
# MCOP sets these to match Wrike
settings.project.task_status_opts = {2: T("Active"),
                                     6: T("Deferred"),
                                     7: T("Cancelled"),
                                    12: T("Completed"),
                                    }
# -----------------------------------------------------------------------------
# Enable this for a UN-style deployment
#settings.ui.cluster = True
# Enable this to use the label 'Camp' instead of 'Shelter'
#settings.ui.camp = True

# -----------------------------------------------------------------------------
# Uncomment to restrict the export formats available
#settings.ui.export_formats = ("xls",)

settings.ui.update_label = "Edit"
# -----------------------------------------------------------------------------
# Mariner CommandBridge resource identifiers
settings.sync.mcb_resource_identifiers = {"event_incident": "802017D4-08D1-40EA-A03D-4FCFC26883A4",
                                          "project_task": "06831BE6-7B49-47F0-80CD-5FB27DEEC330",
                                          "cms_post": "A6E68F53-72B8-415A-A50F-BB26D363CD30",
                                          }
# Mariner CommandBridge domain identifiers
settings.sync.mcb_domain_identifiers = {"sahana": "9197B3DC-07DD-4922-96CA-9B6D8A1FC2D2",
                                        "wrike": "69A069D9-23E8-422D-BB18-2A3A92FE291C",
                                        }
# -----------------------------------------------------------------------------
# Disable rheaders
def customise_no_rheader_controller(**attr):
    # Remove rheader
    attr["rheader"] = None
    return attr

settings.customise_org_facility_controller = customise_no_rheader_controller
settings.customise_org_organisation_controller = customise_no_rheader_controller
settings.customise_org_resource_controller = customise_no_rheader_controller

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
# Customise Resources

# -----------------------------------------------------------------------------
# Alerts (cms_post)
# -----------------------------------------------------------------------------
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
def customise_cms_post_controller(**attr):

    # Make GeoJSON output smaller
    current.s3db.gis_location.gis_feature_type.represent = None

    # Remove rheader
    attr["rheader"] = None
    return attr

settings.customise_cms_post_controller = customise_cms_post_controller

def customise_cms_post_resource(r, tablename):
    """
        Customise cms_post resource
        - CRUD Strings
        - Datatable
        - Fields
        - Form
        Runs after controller customisation
        But runs before prep
    """

    s3 = current.response.s3
    db = current.db
    s3db = current.s3db
    table = s3db.cms_post

    s3.dl_pagelength = 12
    list_id = r.get_vars.get("list_id", None)
    if list_id != "cms_post_datalist":
        # Default page, not homepage
        s3.dl_rowsize = 2

    #from s3 import FS
    #s3.filter = FS("series_id$name").belongs(["Alert"])

    s3.crud_strings["cms_post"] = Storage(
        label_create = T("Add"),
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
    from s3 import IS_LOCATION_SELECTOR2, S3LocationSelectorWidget2
    table.location_id.requires = IS_LOCATION_SELECTOR2(levels=levels)
    table.location_id.widget = S3LocationSelectorWidget2(levels=levels,
                                                         show_address=True,
                                                         show_map=True,
                                                         points = True,
                                                         polygons = True,
                                                         )
    # Don't add new Locations here
    table.location_id.comment = None

    #table.series_id.readable = table.series_id.writable = True
    #table.series_id.label = T("Type")
    stable = s3db.cms_series
    try:
        series_id = db(stable.name == "Alert").select(stable.id,
                                                      limitby=(0, 1)
                                                      ).first().id
        table.series_id.default = series_id
    except:
        # No suitable prepop
        pass

    table.body.label = T("Description")
    table.body.widget = None

    from s3 import S3SQLCustomForm, S3SQLInlineComponent
    crud_fields = ["date",
                   #"series_id",
                   "body",
                   "location_id",
                   #S3SQLInlineComponent(
                   #    "document",
                   #    name = "file",
                   #    label = T("Files"),
                   #    fields = [("", "file"),
                   #              #"comments",
                   #              ],
                   #    ),
                   ]

    incident_id = r.get_vars.get("~.(incident)", None)
    if incident_id:
        # Coming from Profile page
        # Default location to Incident Location
        itable = s3db.event_incident
        incident = db(itable.id == incident_id).select(itable.location_id,
                                                       limitby=(0, 1)
                                                       ).first()
        if incident:
            table.location_id.default = incident.location_id

        # Add link onaccept
        def create_onaccept(form):
            current.s3db.event_post.insert(incident_id=incident_id,
                                           post_id=form.vars.id)

        s3db.configure("cms_post",
                       create_onaccept = create_onaccept,
                       )
    else:
        # Insert into Form
        crud_fields.insert(0, S3SQLInlineComponent("incident_post",
                                                   label = T("Incident"),
                                                   fields = [("", "incident_id")],
                                                   multiple = False,
                                                   ))

    crud_form = S3SQLCustomForm(*crud_fields)

    from s3 import S3OptionsFilter
    filter_widgets = s3db.get_config("cms_post", "filter_widgets")
    # Remove the Type filter
    # @ToDo: More robust way to identify it
    del filter_widgets[1]
    filter_widgets.insert(1, S3OptionsFilter("incident_post.incident_id"))

    # Return to List view after create/update/delete
    # We do all this in Popups
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
# Incidents (event_incident)
# -----------------------------------------------------------------------------
def open_incident_filter(selector, tablename=None):
    """
        Default filter for Incidents (callback)
    """

    return [False]

# -----------------------------------------------------------------------------
def customise_event_incident_controller(**attr):

    if "summary" in current.request.args:
        settings.gis.legend = None
        # Not working
        from s3 import s3_set_default_filter
        s3_set_default_filter("~.closed",
                              open_incident_filter,
                              tablename = "event_incident")

    # Make GeoJSON output smaller
    current.s3db.gis_location.gis_feature_type.represent = None

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

    s3db = current.s3db
    table = s3db[tablename]
    crud_strings = current.response.s3.crud_strings

    # Enable 'Lead Organisation' field
    table.organisation_id.readable = table.organisation_id.writable = True

    if r.interactive:
        table.zero_hour.label = T("Date")
        table.comments.label = T("Description")

        crud_strings["event_incident"].label_delete_button = T("Delete Incident")

    list_fields = ["zero_hour",
                   "name",
                   "location_id",
                   "comments",
                   "organisation_id",
                   "closed",
                   ]

    # Custom Form
    location_id_field = table.location_id
    # Don't add new Locations here
    location_id_field.comment = None

    #from gluon.validators import IS_EMPTY_OR
    #table.organisation_id.requires = IS_EMPTY_OR(table.organisation_id.requires)
    from s3 import S3SQLCustomForm, S3SQLInlineComponent
    crud_fields = ["zero_hour",
                   "name",
                   "location_id",
                   "comments",
                   "organisation_id",
                   S3SQLInlineComponent(
                       "document",
                       name = "file",
                       label = T("Documents"),
                       fields = [("", "file"),
                                 #"comments",
                                 ],
                       ),
                   ]
    if r.method != "create":
        crud_fields.append("closed")
    crud_form = S3SQLCustomForm(*crud_fields)

    from s3 import S3TextFilter, S3OptionsFilter, S3LocationFilter
    filter_widgets = [S3TextFilter(["name",
                                    "comments"
                                    ],
                                   #label = T("Description"),
                                   label = T("Search"),
                                   _class = "filter-search",
                                   ),
                      S3OptionsFilter("closed",
                                      cols = 2,
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
                                      represent = "%(name)s",
                                      ),
                      ]

    url_next = URL(c="event", f="incident", args=["[id]", "profile"])

    s3db.configure("event_incident",
                   create_next = url_next,
                   crud_form = crud_form,
                   delete_next = URL(c="event", f="incident", args="summary"),
                   filter_widgets = filter_widgets,
                   list_fields = list_fields,
                   update_next = url_next,
                   )

    if r.method == "profile":
        # Customise tables used by widgets
        customise_project_task_resource(r, "project_task")

        from s3 import FS
        map_widget = dict(label = "Map",
                          type = "map",
                          context = "incident",
                          icon = "icon-map",
                          # Tall/thin fits Puget Sound best
                          height = 600,
                          width = 200,
                          colspan = 1,
                          )
        alerts_widget = dict(label = "Alerts",
                             label_create = "Create Alert",
                             type = "datalist",
                             tablename = "cms_post",
                             context = "incident",
                             # Only show Active Alerts
                             filter = FS("expired") == False,
                             icon = "icon-alert",
                             colspan = 1,
                             layer = "Alerts",
                             #list_layout = s3db.cms_post_list_layout,
                             )
        resources_widget = dict(label = "Resources",
                                label_create = "Add Resource",
                                type = "datalist",
                                tablename = "event_resource",
                                context = "incident",
                                #filter = FS("status").belongs(event_resource_active_statuses),
                                icon = "icon-wrench",
                                colspan = 1,
                                #list_layout = s3db.event_resource_list_layout,
                                )
        tasks_widget = dict(label = "Tasks",
                            label_create = "Create Task",
                            type = "datalist",
                            tablename = "project_task",
                            context = "incident",
                            # Only show Active Tasks
                            filter = FS("status").belongs(s3db.project_task_active_statuses),
                            icon = "icon-tasks",
                            colspan = 1,
                            #list_layout = s3db.project_task_list_layout,
                            )
        record = r.record
        record_id = record.id
        record_name = record.name
        title = "%s: %s" % (T("Incident"), record_name)
        marker = current.gis.get_marker(controller = "event",
                                        function = "incident")
        layer = dict(name = record_name,
                     id = "profile-header-%s-%s" % (tablename, record_id),
                     active = True,
                     tablename = tablename,
                     url = "/%s/event/incident.geojson?incident.id=%s" % \
                        (r.application, record_id),
                     marker = marker,
                     )
        if current.auth.s3_has_permission("update", table, record_id=record_id):
            edit_btn = A(I(_class="icon icon-edit"),
                         _href=URL(c="event", f="incident",
                                   args=[record_id, "update.popup"],
                                   vars={"refresh": "datalist"}),
                         _class="s3_modal",
                         _title=s3.crud_strings["event_incident"].title_update,
                         )
        else:
            edit_btn = ""
        # Dropdown of available documents
        # @ToDo: Use resource.components instead of DAL for security (not required here but good practise)
        dtable = s3db.doc_document
        rows = current.db(dtable.doc_id == r.record.doc_id).select(dtable.file)
        documents = [row.file for row in rows]
        if documents:
            doc_list = UL(_class="dropdown-menu",
                          _role="menu",
                          )
            retrieve = dtable.file.retrieve
            for doc in documents:
                try:
                    doc_name = retrieve(doc)[0]
                except (IOError, TypeError):
                    doc_name = current.messages["NONE"]
                doc_url = URL(c="default", f="download",
                              args=[doc])
                doc_item = LI(A(I(_class="icon-file"),
                                " ",
                                doc_name,
                                _href=doc_url,
                                ),
                              _role="menuitem",
                              )
                doc_list.append(doc_item)
            docs = DIV(A(I(_class="icon-paper-clip"),
                         SPAN(_class="caret"),
                         _class="btn dropdown-toggle",
                         _href="#",
                         **{"_data-toggle": "dropdown"}
                         ),
                       doc_list,
                       _class="btn-group attachments dropdown pull-right",
                       )
        else:
            docs = ""
        s3db.configure("event_incident",
                       profile_title = title,
                       profile_header = DIV(edit_btn,
                                            H2(title),
                                            docs,
                                            _class="profile-header",
                                            ),
                       profile_layers = (layer,),
                       profile_widgets = (alerts_widget,
                                          resources_widget,
                                          tasks_widget,
                                          map_widget,
                                          ),
                       profile_cols = 4
                       )

settings.customise_event_incident_resource = customise_event_incident_resource

# -----------------------------------------------------------------------------
# Facilities (org_facility)
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
        label_create = T("Add"),
        title_display = T("Facility Details"),
        title_list = T("Facilities"),
        title_update = T("Edit Facility Details"),
        label_list_button = T("List Facilities"),
        label_delete_button = T("Delete Facility"),
        msg_record_created = T("Facility added"),
        msg_record_modified = T("Facility details updated"),
        msg_record_deleted = T("Facility deleted"),
        msg_list_empty = T("No Facilities currently registered"))

    from s3 import IS_LOCATION_SELECTOR2, S3LocationSelectorWidget2
    location_id_field = table.location_id
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

    from s3 import S3SQLCustomForm
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
                   list_layout = render_facilities,
                   report_options = report_options,
                   summary = settings.ui.summary,
                   update_next = url_next,
                   )

    if r.method == "summary":
        settings.gis.legend = None

settings.customise_org_facility_resource = customise_org_facility_resource

# -----------------------------------------------------------------------------
# Stakeholders (org_organisation)
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
            label_create = T("Add"),
            title_display = T("Stakeholder Details"),
            title_list = T("Stakeholders"),
            title_update = T("Edit Stakeholder"),
            label_list_button = T("List Stakeholders"),
            label_delete_button = T("Delete Stakeholder"),
            msg_record_created = T("Stakeholder added"),
            msg_record_modified = T("Stakeholder updated"),
            msg_record_deleted = T("Stakeholder deleted"),
            msg_list_empty = T("No Stakeholders currently registered"))

        from s3 import S3SQLCustomForm, S3SQLInlineLink
        crud_form = S3SQLCustomForm("id",
                                    "name",
                                    S3SQLInlineLink(
                                        "organisation_type",
                                        field = "organisation_type_id",
                                        label = T("Type"),
                                        multiple = False,
                                        #widget = "hierarchy",
                                    ),
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

            from s3 import S3TextFilter, S3OptionsFilter
            filter_widgets = [S3TextFilter(["name",
                                            "acronym",
                                            "website",
                                            "comments",
                                            ],
                                          label = T("Search")),
                              S3OptionsFilter("organisation_organisation_type.organisation_type_id",
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

            #from s3 import FS
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
            #map_widget = dict(label = "Map",
            #                  type = "map",
            #                  context = "organisation",
            #                  icon = "icon-map",
            #                  height = 383,
            #                  width = 568,
            #                  )
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
                                    #list_layout = s3db.org_resource_list_layout,
                                    )
            projects_widget = dict(label = "Incidents",
                                   label_create = "Create Incident",
                                   type = "datalist",
                                   tablename = "event_incident",
                                   context = "organisation",
                                   icon = "icon-incident",
                                   show_on_map = False, # No Marker yet & only show at L1-level anyway
                                   #list_layout = s3db.event_incident_list_layout,
                                   )
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
                                                _class="profile-header",
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
# Resource Inventory (org_resource)
# -----------------------------------------------------------------------------
def customise_org_resource_resource(r, tablename):
    """
        Customise org_resource resource
        - Fields
        - Filter
        Runs after controller customisation
        But runs before prep
    """

    if r.representation == "geojson":
        # Make GeoJSON output smaller
        current.s3db.gis_location.gis_feature_type.represent = None

    elif r.interactive:
        s3 = current.response.s3
        s3db = current.s3db
        table = s3db.org_resource

        s3.crud_strings[tablename] = Storage(
            label_create = T("Add"),
            title_display = T("Inventory Resource"),
            title_list = T("Resource Inventory"),
            title_update = T("Edit Inventory Resource"),
            label_list_button = T("Resource Inventory"),
            label_delete_button = T("Delete Inventory Resource"),
            msg_record_created = T("Inventory Resource added"),
            msg_record_modified = T("Inventory Resource updated"),
            msg_record_deleted = T("Inventory Resource deleted"),
            msg_list_empty = T("No Resources in Inventory"))

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
        from s3 import IS_LOCATION_SELECTOR2, S3LocationSelectorWidget2
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
        s3.cancel = URL(c="org", f="resource")

    if r.method == "summary":
        settings.gis.legend = None

settings.customise_org_resource_resource = customise_org_resource_resource

# -----------------------------------------------------------------------------
def customise_event_resource_resource(r, tablename):
    """
        Customise org_resource resource
        - Fields
        - Filter
        Runs after controller customisation
        But runs before prep
    """

    if r.representation == "geojson":
        # Make GeoJSON output smaller
        current.s3db.gis_location.gis_feature_type.represent = None

    elif r.interactive:
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add"),
            title_display = T("Resource Responding"),
            title_list = T("Resources Responding"),
            title_update = T("Edit Resource Responding"),
            label_list_button = T("Resources Responding"),
            label_delete_button = T("Delete Resource Responding"),
            msg_record_created = T("Resource Responding added"),
            msg_record_modified = T("Resource Responding updated"),
            msg_record_deleted = T("Resource Responding deleted"),
            msg_list_empty = T("No Resources Responding"))

    if r.method == "summary":
        settings.gis.legend = None

settings.customise_event_resource_resource = customise_event_resource_resource

# -----------------------------------------------------------------------------
# Tasks (project_task)
# -----------------------------------------------------------------------------
def active_status_filter(selector, tablename=None):
    """
        Default filter for Tasks (callback)
    """

    return current.s3db.project_task_active_statuses

# -----------------------------------------------------------------------------
def customise_project_task_controller(**attr):

    if "summary" in current.request.args:
        settings.gis.legend = None
        # Not working
        from s3 import s3_set_default_filter
        s3_set_default_filter("~.status",
                              active_status_filter,
                              tablename = "project_task")

    # Make GeoJSON output smaller
    current.s3db.gis_location.gis_feature_type.represent = None

    # Remove rheader
    attr["rheader"] = None
    return attr

settings.customise_project_task_controller = customise_project_task_controller

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
        list_fields = ["name",
                       "description",
                       "location_id",
                       "date_due",
                       "pe_id",
                       "incident.incident_id",
                       #"organisation_id$logo",
                       "pe_id",
                       "source_url",
                       "modified_by",
                       "status",
                       "priority",
                       ]
    else:
        list_fields = ["id",
                       "status",
                       "priority",
                       "incident.incident_id",
                       (T("Task"), "name"),
                       "location_id",
                       "date_due",
                       (T("Wrike Permalink"), "source_url"),
                       ]

    # Custom Form
    table.name.label = T("Name")
    table.description.label = T("Description")
    table.description.comment = None
    table.location_id.readable = table.location_id.writable = True
    from s3 import S3SQLCustomForm, S3SQLInlineComponent
    crud_fields = ["source_url",
                   "status",
                   "priority",
                   "name",
                   "description",
                   "pe_id",
                   "date_due",
                   "location_id",
                   ]

    incident_id = r.get_vars.get("~.(incident)", None)
    if incident_id:
        # Coming from Profile page
        # Add link onaccept
        def create_onaccept(form):
            current.s3db.event_task.insert(incident_id=incident_id,
                                           task_id=form.vars.id)

        s3db.configure("project_task",
                       create_onaccept = create_onaccept,
                       )
    else:
        # Insert into Form
        crud_fields.insert(0, S3SQLInlineComponent("incident",
                                                   label = T("Incident"),
                                                   fields = [("", "incident_id")],
                                                   multiple = False,
                                                   ))

    if (r.method == None or r.method == "update") and \
       r.record and r.record.source_url:
        # Task imported from Wrike
        # - lock all fields which should only be edited within Wrike
        #crud_fields.insert(0, "source_url")
        current.s3db.event_task.incident_id.writable = False
        for fieldname in ["source_url",
                          "status",
                          "priority",
                          "name",
                          "description",
                          "pe_id",
                          "date_due"]:
            table[fieldname].writable = False

    crud_form = S3SQLCustomForm(*crud_fields)

    # Filter Widgets
    from s3 import S3OptionsFilter
    filter_widgets = s3db.get_config("project_task", "filter_widgets")
    filter_widgets.insert(2, S3OptionsFilter("incident.incident_id"))

    # Report options
    report_fields = ["status",
                     "priority",
                     "incident.incident_id",
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
                   list_fields = list_fields,
                   onvalidation = None, # don't check pe_id if status Active
                   orderby = "project_task.date_due asc",
                   report_options = report_options,
                   update_next = url_next,
                   )

settings.customise_project_task_resource = customise_project_task_resource

# -----------------------------------------------------------------------------
# Contacts (pr_person)
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

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        label_create = T("Add"),
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
    from s3 import S3Represent, IS_ONE_OF
    represent = S3Represent(lookup="org_site")
    site_field.label = T("Facility")
    site_field.represent = represent
    site_field.requires = IS_ONE_OF(current.db, "org_site.site_id",
                                    represent,
                                    orderby = "org_site.name")

    from s3layouts import S3AddResourceLink
    site_field.comment = S3AddResourceLink(c="org", f="facility",
                                           vars={"child": "site_id"},
                                           label=T("Create Facility"),
                                           title=T("Facility"),
                                           tooltip=T("If you don't see the Facility in the list, you can add a new one by clicking link 'Create Facility'."))

    # ImageCrop widget doesn't currently work within an Inline Form
    image_field = s3db.pr_image.image
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


    from s3 import S3SQLCustomForm, S3SQLInlineComponent
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
                fields = [("", "image")],
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
                                    fields = [("", "value")],
                                    filterby = dict(field = "contact_method",
                                                    options = "SMS")),
                                    )
        s3_sql_custom_fields.insert(3,
                                    S3SQLInlineComponent(
                                    "contact",
                                    name = "email",
                                    label = EMAIL,
                                    multiple = False,
                                    fields = [("", "value")],
                                    filterby = dict(field = "contact_method",
                                                    options = "EMAIL")),
                                    )

    crud_form = S3SQLCustomForm(*s3_sql_custom_fields)

    from s3 import S3TextFilter, S3OptionsFilter
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
                   listadd = True,
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
    #date = record["hrm_human_resource.modified_on"]
    fullname = record["hrm_human_resource.person_id"]
    job_title = raw["hrm_human_resource.job_title_id"] or ""
    if job_title:
        job_title = "- %s" % record["hrm_human_resource.job_title_id"]
    #organisation = record["hrm_human_resource.organisation_id"]
    organisation_id = raw["hrm_human_resource.organisation_id"]
    #org_url = URL(c="org", f="organisation", args=[organisation_id, "profile"])
    person_id = raw["hrm_human_resource.person_id"]
    #location = record["org_site.location_id"]
    #location_id = raw["org_site.location_id"]
    #location_url = URL(c="gis", f="location",
    #                   args=[location_id, "profile"])
    #address = raw["gis_location.addr_street"] or T("no facility assigned")
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
    #author = record["org_facility.modified_by"]
    #date = record["org_facility.modified_on"]
    #organisation = record["org_facility.organisation_id"]
    organisation_id = raw["org_facility.organisation_id"]
    #location = record["org_facility.location_id"]
    #location_id = raw["org_facility.location_id"]
    #location_url = URL(c="gis", f="location",
    #                   args=[location_id, "profile"])
    address = raw["gis_location.addr_street"]
    phone = raw["org_facility.phone1"]
    #facility_type = record["org_facility.facility_type_id"]
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
    #avatar = logo
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
