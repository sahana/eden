# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

from s3 import S3CRUD

def config(settings):
    """
        Template for WA-COP + CAD Cloud Integration
    """

    T = current.T

    # =========================================================================
    # System Settings
    #
    settings.base.system_name = T("Sahana: Washington Common Operating Picture (WA-COP)")
    settings.base.system_name_short = T("Sahana")

    # Prepop default
    settings.base.prepopulate += ("WACOP", "default/users", "WACOP/Demo")

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "WACOP"

    # -------------------------------------------------------------------------
    # Self-Registration and User Profile
    #
    # Users can self-register
    settings.security.self_registration = False
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

    # -------------------------------------------------------------------------
    # Security Policy
    #
    settings.security.policy = 7 # Apply Controller, Function and Table ACLs
    settings.security.map = True

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    #
    settings.L10n.languages = OrderedDict([
        ("en", "English"),
        ("es", "Español"),
    ])
    # Default Language
    settings.L10n.default_language = "en"
    # Default timezone for users
    settings.L10n.utc_offset = "-0800"
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

    # -------------------------------------------------------------------------
    # GIS settings
    #
    # Restrict the Location Selector to just certain countries
    settings.gis.countries = ("US",)
    # Levels for the LocationSelector
    levels = ("L1", "L2", "L3")

    # Uncomment to pass Addresses imported from CSV to a Geocoder to try and automate Lat/Lon
    #settings.gis.geocode_imported_addresses = "google"

    # Until we add support to S3LocationSelector to set dropdowns from LatLons
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

    # -------------------------------------------------------------------------
    # Modules
    #
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
            module_type = 10
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
                module_type = 10,
            )),
        ("event", Storage(
                name_nice = "Events",
                restricted = True,
                module_type = 2,
            )),
        ("fire", Storage(
                name_nice = "Fire",
                restricted = True,
                module_type = None,
            )),
        ("police", Storage(
                name_nice = "Police",
                restricted = True,
                module_type = None,
            )),
        ("project", Storage(
                name_nice = "Tasks",
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

    # -------------------------------------------------------------------------
    # CMS Content Management
    #
    settings.cms.bookmarks = True
    settings.cms.show_tags = True

    # -------------------------------------------------------------------------
    # Event/Incident Management
    #
    settings.event.incident_teams_tab = "Units"
    # Uncomment to preserve linked Incidents when an Event is deleted
    settings.event.cascade_delete_incidents = False

    # -------------------------------------------------------------------------
    def customise_event_event_controller(**attr):

        s3db = current.s3db

        # Modify Components
        s3db.add_components("event_event",
                            # Events have just a single Location
                            event_event_location = {"joinby": "event_id",
                                                    "multiple": False,
                                                    },
                            # Incidents are linked to Events, not created from them
                            # - not a link table though, so can't change the actuation
                            #event_incident = {"joinby": "event_id",
                            #                  },
                            )

        # Custom Profile
        #s3db.set_method("event", "event",
        #                method = "custom",
        #                action = event_Profile)

        # Custom rheader tabs
        attr = dict(attr)
        attr["rheader"] = wacop_event_rheader

        return attr

    settings.customise_event_event_controller = customise_event_event_controller

    # -------------------------------------------------------------------------
    def customise_event_incident_controller(**attr):

        s3db = current.s3db
        s3 = current.response.s3

        # Load normal model to be able to override configuration
        table = s3db.event_incident

        def status_represent(value):
            " Represent the closed field as a Status Open/Closed instead of True/False "

            if value is True:
                return T("Closed")
            elif value is False:
                return T("Open")
            else:
                return current.messages["NONE"]

        table.closed.label = T("Status")
        table.closed.represent = status_represent

        # Custom Profile
        s3db.set_method("event", "incident",
                        method = "custom",
                        action = incident_Profile)

        s3.crud_strings["event_incident"].title_list =  T("Browse Incidents")

        from s3 import S3OptionsFilter, S3TextFilter
        filter_widgets = [S3TextFilter(["name",
                                        "comments",
                                        ],
                                       formstyle = text_filter_formstyle,
                                       label = T("Search"),
                                       _placeholder = T("Enter search term…"),
                                       ),
                          S3OptionsFilter("organisation_id",
                                          label = "",
                                          noneSelectedText = "Lead Organization",
                                          widget = "multiselect",
                                          ),
                          S3OptionsFilter("closed",
                                          formstyle = filter_formstyle,
                                          options = {"*": T("All"),
                                                     False: T("Open"),
                                                     True: T("Closed"),
                                                     },
                                          cols = 1,
                                          multiple = False,
                                          ),
                          S3OptionsFilter("incident_type_id",
                                          formstyle = filter_formstyle,
                                          label = T("Incident Type"),
                                          noneSelectedText = "All",
                                          widget = "multiselect",
                                          ),
                          ]

        list_fields = ["closed",
                       "name",
                       (T("Type"), "incident_type_id"),
                       "location_id",
                       (T("Start"), "date"),
                       (T("End"), "end_date"),
                       ]

        s3db.configure("event_incident",
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

        # Custom postp
        standard_postp = s3.postp
        def custom_postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.interactive and isinstance(output, dict):
                # Open the Custom profile page instead of the normal one
                from gluon import URL
                from s3 import S3CRUD
                custom_url = URL(args = ["[id]", "custom"])
                S3CRUD.action_buttons(r,
                                      read_url=custom_url,
                                      update_url=custom_url)
                # Additional styles
                s3.external_stylesheets += ["https://cdn.knightlab.com/libs/timeline3/latest/css/timeline.css",
                                            "https://fonts.googleapis.com/css?family=Merriweather:400,700|Source+Sans+Pro:400,700",
                                            ]

            return output
        s3.postp = custom_postp

        # Custom rheader tabs
        attr = dict(attr)
        attr["rheader"] = wacop_event_rheader

        # Display events in the header
        etable = s3db.event_event
        query = (etable.closed == False) & \
                (etable.deleted == False)
        events = current.db(query).select(etable.id, etable.name)
        attr["events"] = events

        # No sidebar menu
        current.menu.options = None

        return attr

    settings.customise_event_incident_controller = customise_event_incident_controller

    # -------------------------------------------------------------------------
    def customise_event_team_resource(r, tablename):
        # @ToDo: Have both Team & Event_Team in 1 form

        s3db = current.s3db

        #s3db.event_team.group_id.label = T("Resource")

        from s3 import S3SQLCustomForm
        crud_form = S3SQLCustomForm("incident_id",
                                    "group_id",
                                    "status_id",
                                    )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

    settings.customise_event_team_resource = customise_event_team_resource

    # -------------------------------------------------------------------------
    def customise_pr_group_resource(r, tablename):

        s3db = current.s3db

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Resource"),
            title_display = T("Resource Details"),
            title_list = T("Resources"),
            title_update = T("Edit Resource"),
            label_list_button = T("List Resources"),
            label_delete_button = T("Delete Resource"),
            msg_record_created = T("Resource added"),
            msg_record_modified = T("Resource updated"),
            msg_record_deleted = T("Resource deleted"),
            msg_list_empty = T("No Resources currently registered"))

        field = s3db.pr_group.status_id
        field.readable = field.writable = True

        from s3 import S3SQLCustomForm
        crud_form = S3SQLCustomForm((T("Name"), "name"),
                                    "status_id",
                                    "comments",
                                    )

        list_fields = [(T("Name"), "name"),
                       "status_id",
                       "comments",
                       ]

        s3db.configure(tablename,
                       crud_form = crud_form,
                       list_fields = list_fields,
                       )

    settings.customise_pr_group_resource = customise_pr_group_resource

# =============================================================================
def wacop_event_rheader(r, tabs=[]):
    """ EVENT custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    from s3 import s3_rheader_resource, S3ResourceHeader

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "event_event":

            if not tabs:
                tabs = [(T("Event Details"), None),
                        (T("Incidents"), "incident"),
                        (T("Units"), "group"),
                        (T("Tasks"), "task"),
                        (T("Updates"), "post"),
                        ]

            rheader_fields = [["name",
                               ],
                              ["start_date",
                               ],
                              ["comments",
                               ],
                              ]

        elif tablename == "event_incident":

            if not tabs:
                tabs = [(T("Incident Details"), None),
                        (T("Units"), "group"),
                        (T("Tasks"), "task"),
                        (T("Updates"), "post"),
                        ]

            rheader_fields = [["name",
                               ],
                              ["date",
                               ],
                              ["comments",
                               ],
                              ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table=resource.table,
                                                         record=record,
                                                         )
    return rheader

# =============================================================================
class incident_Profile(S3CRUD):
    """
        Custom profile page for an Incident
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        incident_id = r.id

        if incident_id and \
           r.name == "incident" and \
           not r.component:

            s3db = current.s3db
            ptable = s3db.cms_post

            if r.http == "POST":
                # Process the Updates form
                from gluon import SQLFORM
                form = SQLFORM(ptable)
                #onvalidation = 
                if form.accepts(r.post_vars,
                                current.session,
                                #onvalidation=onvalidation
                                ):
                    # Insert new record
                    accept_id = ptable.insert(**data)
                    # @ToDo: onaccept / record ownership / audit if-required
                    # @ToDo:
                    #s3db.update_super()

                    #response.confirmation = message

                    if form.errors:
                        # Revert any records created within widgets/validators
                        current.db.rollback()

            representation = r.representation
            if representation == "html":

                T = current.T
                db = current.db
                auth = current.auth
                response = current.response
                s3 = response.s3

                gtable = s3db.gis_location
                itable = s3db.event_incident
                #rtable = s3db.pr_group
                ertable = s3db.event_team
                eptable = s3db.event_post

                record = r.record

                from gluon import A, DIV, I, TAG, URL
                from s3 import FS, S3DateTime, S3FilterForm, S3DateFilter, S3OptionsFilter, S3TextFilter

                date_represent = lambda dt: S3DateTime.date_represent(dt,
                                                                      format = "%b %d %Y %H:%M",
                                                                      utc = True,
                                                                      #calendar = calendar,
                                                                      )

                output = {}

                # Is this Incident part of an Event?
                event_id = record.event_id
                output["event_id"] = event_id
                if event_id:
                    # Read Event details
                    etable = s3db.event_event
                    event = db(etable.id == event_id).select(etable.name,
                                                             etable.start_date,
                                                             etable.end_date,
                                                             limitby = (0, 1),
                                                             ).first()
                    output["event_name"] = event.name
                    output["event_start_date"] = date_represent(event.start_date)
                    end_date = event.end_date
                    if end_date:
                        output["event_active"] = False
                        output["event_end_date"] = date_represent(end_date)
                    else:
                        output["event_active"] = True
                        output["event_end_date"] = "n/a"

                    eltable = s3db.event_event_location
                    query = (eltable.event_id == event_id) & \
                            (eltable.deleted == False)
                    event_location = db(query).select(eltable.location_id,
                                                      limitby = (0, 1),
                                                      ).first()
                    if event_location:
                        output["event_location"] = eltable.location_id.represent(event_location.location_id)
                    else:
                        output["event_location"] = ""

                    query = (itable.event_id == event_id) & \
                            (itable.deleted == False)
                    output["incidents"] = db(query).count()

                    query = (ertable.event_id == event_id) & \
                            (ertable.deleted == False)
                    output["event_resources"] = db(query).count()

                    query = (eptable.event_id == event_id) & \
                            (eptable.deleted == False)
                    output["event_posts"] = db(query).count()

                # Incident Details
                output["name"] = record.name

                output["modified_on"] = date_represent(record.modified_on)

                output["start_date"] = date_represent(record.date)

                end_date = record.end_date
                if end_date:
                    output["active"] = False
                    output["end_date"] = date_represent(end_date)
                else:
                    output["active"] = True
                    output["end_date"] = ""
                
                output["description"] = record.comments

                location = db(gtable.id == record.location_id).select(gtable.L1,
                                                                      gtable.L3,
                                                                      gtable.addr_street,
                                                                      gtable.addr_postcode,
                                                                      gtable.lat,
                                                                      gtable.lon,
                                                                      limitby = (0, 1),
                                                                      ).first()
                if location:
                    output["L1"] = location.L1 or ""
                    output["L3"] = location.L3 or ""
                    output["addr_street"] = location.addr_street or ""
                    output["postcode"] = location.addr_postcode or ""
                    output["lat"] = location.lat or ""
                    output["lon"] = location.lon or ""
                    # @ToDo: BBOX should include the resources too
                    bbox = current.gis.get_bounds(features=[location])
                    output["lat_max"] = bbox["lat_max"]
                    output["lat_min"] = bbox["lat_min"]
                    output["lon_max"] = bbox["lon_max"]
                    output["lon_min"] = bbox["lon_min"]
                else:
                    output["L1"] = ""
                    output["L3"] = ""
                    output["addr_street"] = ""
                    output["postcode"] = ""
                    output["lat"] = ""
                    output["lon"] = ""
                    # @ToDo: Defaults for Seattle
                    output["lat_max"] = ""
                    output["lat_min"] = ""
                    output["lon_max"] = ""
                    output["lon_min"] = ""

                messages = current.messages
                permit = auth.s3_has_permission
                updateable = permit("update", itable, record_id=incident_id, c="event", f="incident")

                settings = current.deployment_settings
                # Uncomment to control the dataTables layout: https://datatables.net/reference/option/dom
                #settings.ui.datatables_dom = "<'data-info row'<'large-4 columns'i><'large-3 columns'l><'large-3 columns search'f><'large-2 columns right'>r><'dataTable_table't><'row'p>"
                # Uncomment for dataTables to use a different paging style:
                settings.ui.datatables_pagingType = "bootstrap"
                dt_init = ['''$('.dataTables_filter label,.dataTables_length,.dataTables_info').hide();''']

                get_vars = r.get_vars
                start = get_vars.get("start", None)
                limit = get_vars.get("limit", 0)
                if limit:
                    if limit.lower() == "none":
                        limit = None
                    else:
                        try:
                            start = int(start)
                            limit = int(limit)
                        except (ValueError, TypeError):
                            start = None
                            limit = 0 # use default
                else:
                    # Use defaults
                    start = None

                # How many records per page?
                if s3.dataTable_pageLength:
                    display_length = s3.dataTable_pageLength
                else:
                    display_length = 10

                # Server-side pagination?
                if not s3.no_sspag:
                    dt_pagination = "true"
                    if not limit and display_length is not None:
                        limit = 2 * display_length
                    else:
                        limit = None
                else:
                    dt_pagination = "false"

                s3.no_formats = True

                def _datatable(tablename, list_fields, orderby):

                    c, f = tablename.split("_", 1)

                    resource = s3db.resource(tablename)
                    resource.add_filter(FS("event_%s.incident_id" % f) == incident_id)

                    list_id = "custom-list-%s" % tablename

                    # Update the datatables init
                    dt_init.append('''$('#dt-%(tablename)s .dataTables_filter').prependTo($('#dt-search-%(tablename)s'));$('#dt-search-%(tablename)s .dataTables_filter input').attr('placeholder','Enter search term…').attr('name','%(tablename)s-search').prependTo($('#dt-search-%(tablename)s .dataTables_filter'));$('.custom-list-%(tablename)s_length').hide();''' % \
                        dict(tablename = tablename))

                    # Move the search boxes into the design
                    settings.ui.datatables_initComplete = "".join(dt_init)

                    # Get the data table
                    dt, totalrows, ids = resource.datatable(fields=list_fields,
                                                            start=start,
                                                            limit=limit,
                                                            orderby=orderby)
                    displayrows = totalrows

                    if dt.empty:
                        empty_str = self.crud_string(tablename,
                                                     "msg_list_empty")
                    else:
                        empty_str = self.crud_string(tablename,
                                                     "msg_no_match")
                    empty = DIV(empty_str, _class="empty")

                    dtargs = attr.get("dtargs", {})

                    # @ToDo: Permissions
                    dtargs["dt_row_actions"] = [{"label": messages.READ,
                                                 "url": URL(c="event", f="incident",
                                                            args=[incident_id, f, "[id].popup"]),
                                                 "icon": "fa fa-eye",
                                                 "_class": "s3_modal",
                                                 },
                                                # @ToDo: AJAX delete
                                                {"label": messages.DELETE,
                                                 "url": URL(c="event", f="incident",
                                                            args=[incident_id, f, "[id]", "delete"]),
                                                 "icon": "fa fa-trash",
                                                 },
                                                ]
                    dtargs["dt_action_col"] = len(list_fields)
                    dtargs["dt_pagination"] = dt_pagination
                    dtargs["dt_pageLength"] = display_length
                    dtargs["dt_base_url"] = r.url(method="", vars={})
                    dtargs["dt_ajax_url"] = r.url(vars={"update": tablename},
                                                  representation="aadata")

                    datatable = dt.html(totalrows,
                                        displayrows,
                                        id=list_id,
                                        **dtargs)

                    if dt.data:
                        empty.update(_style="display:none")
                    else:
                        datatable.update(_style="display:none")
                    contents = DIV(datatable, empty, _class="dt-contents")

                    # Link for create-popup
                    if updateable and permit("create", tablename):
                        output["create_%s_popup" % tablename] = \
                            A(TAG[""](I(_class="fa fa-plus"),
                                      T("Add"),
                                      ),
                              _href = URL(c="event", f="incident",
                                          args=[incident_id, f, "create.popup"],
                                          vars={"refresh": list_id},
                                          ),
                              _class = "button tiny postfix s3_modal", 
                              )
                    else:
                        output["create_%s_popup" % tablename] = ""

                    # Render the widget
                    output["%s_datatable" % tablename] = DIV(contents,
                                                             _class="card-holder",
                                                             )

                # Resources dataTable
                tablename = "event_team"
                list_fields = ["id", #(T("Actions"), "id"), @ToDo: Label
                               "group_id",
                               "status_id",
                               ]
                orderby = "pr_group.name"
                _datatable(tablename, list_fields, orderby)

                # Tasks dataTable
                tablename = "project_task"
                list_fields = ["status",
                               (T("Description"), "name"),
                               (T("Created"), "created_on"),
                               (T("Due"), "date_due"),
                               ]
                orderby = "project_task.date_due"
                _datatable(tablename, list_fields, orderby)

                # Staff dataTable
                tablename = "event_human_resource"
                list_fields = [(T("Name"), "human_resource_id"),
                               (T("Title"), "human_resource_id$job_title_id"),
                               "human_resource_id$organisation_id",
                                (T("Email"), "human_resource_id$person_id$email.value"),
                                (T("Phone"), "human_resource_id$person_id$phone.value"),
                               "status",
                               (T("Notes"), "comments"),
                               ]
                orderby = "event_human_resource.human_resource_id"
                _datatable(tablename, list_fields, orderby)

                # Organisations dataTable
                tablename = "event_organisation"
                list_fields = [(T("Name"), "organisation_id"),
                               "status",
                               "comments",
                               ]
                orderby = "event_organisation.organisation_id"
                _datatable(tablename, list_fields, orderby)

                # Updates DataList
                tablename = "cms_post"
                c, f = tablename.split("_", 1)
                resource = s3db.resource(tablename)
                resource.add_filter(FS("event_%s.incident_id" % f) == incident_id)

                list_fields = ["series_id",
                               "date",
                               "body",
                               "created_by",
                               "tag_post.tag_id",
                               ]
                datalist, numrows, ids = resource.datalist(fields=list_fields,
                                                           start=None,
                                                           limit=5,
                                                           list_id="updates_datalist",
                                                           orderby="date desc",
                                                           layout=cms_post_list_layout)
                if numrows == 0:
                    # Empty table or just no match?
                    if "deleted" in ptable:
                        available_records = db(ptable.deleted != True)
                    else:
                        available_records = db(ptable._id > 0)
                    if available_records.select(ptable._id,
                                                limitby=(0, 1)).first():
                        msg = DIV(self.crud_string(tablename,
                                                   "msg_no_match"),
                                  _class="empty")
                    else:
                        msg = DIV(self.crud_string(tablename,
                                                   "msg_list_empty"),
                                  _class="empty")
                    data = msg
                else:
                    # Render the list
                    data = datalist.html()

                # Render the widget
                output["updates_datalist"] = data

                # Filter Form
                date_filter = S3DateFilter("date",
                                           label = "",
                                           #hide_time = True,
                                           )
                date_filter.input_labels = {"ge": "Start Time/Date", "le": "End Time/Date"}

                filter_widgets = [S3TextFilter(["body",
                                                ],
                                               formstyle = text_filter_formstyle,
                                               label = T("Search"),
                                               _placeholder = T("Enter search term…"),
                                               ),
                                  S3OptionsFilter("bookmark.user_id",
                                                  label = "",
                                                  options = {"*": T("All"),
                                                             auth.user.id: T("My Bookmarks"),
                                                             },
                                                  cols = 2,
                                                  multiple = False,
                                                  ),
                                  S3OptionsFilter("series_id",
                                                  label = "",
                                                  noneSelectedText = "Type",
                                                  widget = "multiselect",
                                                  ),
                                  S3OptionsFilter("created_by$organisation_id",
                                                  label = "",
                                                  noneSelectedText = "Source",
                                                  ),
                                  S3OptionsFilter("tag_post.tag_id",
                                                  label = "",
                                                  noneSelectedText = "Tag",
                                                  ),
                                  date_filter,
                                  ]

                filter_form = S3FilterForm(filter_widgets)
                output["filter_form"] = filter_form.html(resource, get_vars,
                                                         target="updates_datalist",
                                                         alias=None)
                # @ToDo: Move to static or apply styles in theme
                s3.jquery_ready.append('''$('.filter-clear, .show-filter-manager').addClass('button tiny secondary')''')

                #  Create Form
                if updateable and permit("create", tablename):
                    #from gluon import SQLFORM
                    from gluon.html import FORM, LABEL, TEXTAREA, SELECT, OPTION, INPUT, HR

                    stable = db.cms_series
                    series = db(stable.deleted == False).select(stable.name,
                                                                stable.id,
                                                                )
                    select = SELECT(OPTION("Choose an update type…",
                                           _disabled=True,
                                           ),
                                    _id="cms_post_series_id",
                                    _name="series_id",
                                    )
                    for s in series:
                        # @ToDo: Option for T()
                        select.append(OPTION(s.name,
                                             _value=s.id,
                                             ))

                    #form = SQLFORM(table)
                    #hidden_fields = form.hidden_fields()
                    #custom = form.custom
                    #widgets = custom.widget
                    form = FORM(LABEL("Write new Update Post:",
                                      _for="body",
                                      ),
                                TEXTAREA(_id="cms_post_body",
                                         _name="body",
                                         _placeholder="Write something…",
                                         _rows="4",
                                         ),
                                DIV(DIV(select,
                                        _class="large-4 columns",
                                        ),
                                    DIV(INPUT(_type="text",
                                              _name="tag",
                                              _value="",
                                              _placeholder="Add tags here…",
                                              ),
                                        _class="large-3 columns",
                                        ),
                                    DIV(INPUT(_type="submit",
                                              _class="button tiny default right",
                                              _value="Post Update",
                                              ),
                                        _class="large-5 columns",
                                        ),
                                    _class="row",
                                    ),
                                #hidden_fields, # Only needed for updates
                                _class="form",
                                action="#",
                                enctype="multipart/form-data",
                                method="post",
                                )

                    form_div = DIV(form,
                                   _class="compose-update panel",
                                   )
                    output["create_post_form"] = form_div
                else:
                    output["create_post_form"] = ""

                import os
                response.view = os.path.join(r.folder,
                                             "modules", "templates",
                                             "WACOP", "views",
                                             "incident_profile.html")
                # Done for the whole controller
                #current.menu.options = None
                return output

            elif representation == "aadata":
                # DataTables updates
    
                get_vars = r.get_vars
                tablename = get_vars.get("update")
                c, f = tablename.split("_", 1)

                if tablename == "event_team":
                    list_fields = ["group_id",
                                   "status_id",
                                   ]
                    orderby = "pr_group.name"

                elif tablename == "project_task":
                    list_fields = ["status",
                                   "name",
                                   "created_on",
                                   "date_due",
                                   ]
                    orderby = "project_task.date_due"
    
                elif tablename == "event_human_resource":
                    list_fields = ["human_resource_id",
                                   "human_resource_id$job_title_id",
                                   "human_resource_id$organisation_id",
                                   "human_resource_id$person_id$email.value",
                                   "human_resource_id$person_id$phone.value",
                                   "status",
                                   "comments",
                                   ]
                    orderby = "event_human_resource.human_resource_id"

                elif tablename == "event_organisation":
                    list_fields = ["organisation_id",
                                   "status",
                                   "comments",
                                   ]
                    orderby = "event_organisation.organisation_id"

                else:
                    raise HTTP(405, current.ERROR.BAD_METHOD)

                from s3 import FS
    
                response = current.response
                s3 = response.s3
                
                resource = current.s3db.resource(tablename)
                resource.add_filter(FS("event_%s.incident_id" % f) == incident_id)
    
                list_id = "custom-list-%s" % tablename

                # Parse datatable filter/sort query
                searchq, orderby_not, left = resource.datatable_filter(list_fields,
                                                                       get_vars)
    
                # DataTable filtering
                if searchq is not None:
                    totalrows = resource.count()
                    resource.add_filter(searchq)
                else:
                    totalrows = None
    
                # Get the data table
                if totalrows != 0:
                    start = get_vars.get("displayStart", None)
                    limit = get_vars.get("pageLength", 0)
                    dt, displayrows, ids = resource.datatable(fields=list_fields,
                                                              start=start,
                                                              limit=limit,
                                                              left=left,
                                                              orderby=orderby,
                                                              getids=False)
                else:
                    dt, displayrows, limit = None, 0, 0
    
                if totalrows is None:
                    totalrows = displayrows
    
                # Echo
                draw = int(get_vars.get("draw") or 0)
    
                # How many records per page?
                if s3.dataTable_pageLength:
                    display_length = s3.dataTable_pageLength
                else:
                    display_length = 10

                # Server-side pagination?
                if not s3.no_sspag:
                    dt_pagination = "true"
                    if not limit and display_length is not None:
                        limit = 2 * display_length
                    else:
                        limit = None
                else:
                    dt_pagination = "false"

                dtargs = attr.get("dtargs", {})
                dtargs["dt_action_col"] = len(list_fields)
                dtargs["dt_pagination"] = dt_pagination
                dtargs["dt_pageLength"] = display_length
                #dtargs["dt_base_url"] = r.url(method="", vars={})
                #dtargs["dt_ajax_url"] = r.url(#vars={"update": 0}, # If we need to update multiple dataTables
                #                              representation="aadata")

                # Representation
                if dt is not None:
                    data = dt.json(totalrows,
                                   displayrows,
                                   list_id,
                                   draw,
                                   **dtargs)
                else:
                    data = '{"recordsTotal":%s,' \
                           '"recordsFiltered":0,' \
                           '"dataTable_id":"%s",' \
                           '"draw":%s,' \
                           '"data":[]}' % (totalrows, list_id, draw)
    
                response.headers["Content-Type"] = "application/json"
                return data

            elif representation == "dl":
                # DataList updates
                # @ToDo
                pass

        raise HTTP(405, current.ERROR.BAD_METHOD)

# =============================================================================
def cms_post_list_layout(list_id, item_id, resource, rfields, record):
    """
        dataList item renderer for Updates on the Incident Profile page.

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    from gluon.html import A, DIV, I, LI, P, SPAN, TAG, UL, URL
    from s3 import ICON

    record_id = record["cms_post.id"]
    item_class = "thumbnail"

    T = current.T
    db = current.db
    s3db = current.s3db
    settings = current.deployment_settings
    permit = current.auth.s3_has_permission

    raw = record._row
    date = record["cms_post.date"]
    body = record["cms_post.body"]
    series_id = raw["cms_post.series_id"]

    # Allow records to be truncated
    # (not yet working for HTML)
    body = DIV(body,
               _class="s3-truncate",
               )

    if series_id:
        series = record["cms_post.series_id"]
        translate = settings.get_L10n_translate_cms_series()
        if translate:
            series_title = T(series)
        else:
            series_title = series
    else:
        series_title = series = ""

    author_id = raw["cms_post.created_by"]
    person = record["cms_post.created_by"]

    # @ToDo: Bulk lookup
    ltable = s3db.pr_person_user
    ptable = db.pr_person
    query = (ltable.user_id == author_id) & \
            (ltable.pe_id == ptable.pe_id)
    row = db(query).select(ptable.id,
                           limitby=(0, 1)
                           ).first()
    if row:
        person_id = row.id
    else:
        person_id = None

    if person:
        if person_id:
            # @ToDo: deployment_setting for controller to use?
            person_url = URL(c="hrm", f="person", args=[person_id])
        else:
            person_url = "#"
        person = A(person,
                   _href=person_url,
                   )

    table = db.cms_post
    updateable = permit("update", table, record_id=record_id)

    # Toolbar
    if updateable:
        edit_btn = A(ICON("edit"),
                     SPAN("edit",
                          _class = "show-for-sr",
                          ),
                     _href=URL(c="cms", f="post",
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id}
                               ),
                     _class="s3_modal",
                     _title=T("Edit %(type)s") % dict(type=series_title),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(ICON("delete"),
                       SPAN("delete",
                           _class = "show-for-sr",
                           ),
                      _class="dl-item-delete",
                      _title=T("Delete"),
                      )
    else:
        delete_btn = ""

    user = current.auth.user
    if user and settings.get_cms_bookmarks():
        ltable = s3db.cms_post_user
        query = (ltable.post_id == record_id) & \
                (ltable.user_id == user.id)
        exists = db(query).select(ltable.id,
                                  limitby=(0, 1)
                                  ).first()
        if exists:
            bookmark_btn = A(ICON("bookmark"),
                             SPAN("remove bookmark",
                                  _class = "show-for-sr",
                                  ),
                             _onclick="$.getS3('%s',function(){$('#%s').datalist('ajaxReloadItem',%s)})" %
                                (URL(c="cms", f="post",
                                     args=[record_id, "remove_bookmark"]),
                                 list_id,
                                 record_id),
                             _title=T("Remove Bookmark"),
                             )
        else:
            bookmark_btn = A(ICON("bookmark-empty"),
                             SPAN("bookmark",
                                  _class = "show-for-sr",
                                  ),
                             _onclick="$.getS3('%s',function(){$('#%s').datalist('ajaxReloadItem',%s)})" %
                                (URL(c="cms", f="post",
                                     args=[record_id, "add_bookmark"]),
                                 list_id,
                                 record_id),
                             _title=T("Add Bookmark"),
                             )
    else:
        bookmark_btn = ""

    divider = LI("|")
    divider["_aria-hidden"] = "true"

    toolbar = UL(LI(A(ICON("share"),
                      " Share",
                      _href="#",
                      _class="button secondary tiny",
                      ),
                    _class="item",
                    ),
                 LI(A(ICON("flag"), # @ToDo: Use flag-lat if not flagged & flag if already flagged (like for bookmarks)
                      SPAN("flag this",
                           _class = "show-for-sr",
                           ),
                      _href="#",
                      _title=T("Flag"),
                      ),
                    _class="item",
                    ),
                 LI(bookmark_btn,
                    _class="item",
                    ),
                 divider,
                 LI(A(I(_class="fa fa-users",
                        ),
                      SPAN("make public",
                           _class = "show-for-sr",
                           ),
                      _href="#",
                      _title=T("Make Public"),
                      ),
                    _class="item",
                    ),
                 LI(edit_btn,
                    _class="item",
                    ),
                 LI(delete_btn,
                    _class="item",
                    ),
                 _class="inline-list right",
                 )

    #if settings.get_cms_show_tags():
    tag_list = UL(_class="left inline-list s3-tags",
                  )
    tag_list["_data-post_id"] = record_id
    tags = raw["cms_tag.name"]
    if tags:
        if not isinstance(tags, list):
            tags = [tags]
        for tag in tags:
            tag_list.append(LI(A(tag,
                                 _href="#",
                                 ),
                               ))

    item = LI(TAG["HEADER"](P(SPAN(series_title,
                                   _class="label info",
                                   ),
                              TAG["TIME"](date),
                              " by %s" % person,
                              _class="left update-meta-text",
                              ),
                            toolbar,
                            _class="clearfix",
                            ),
              P(body),
              TAG["FOOTER"](SPAN("Tags:",
                                 _class="left",
                                 ),
                            tag_list,
                            P(A("0 Comments",
                                _href="#update-1-comments",
                                ),
                              _class="right",
                              ),
                            _class="clearfix",
                            ),
              _class="panel",
              _id=item_id,
              )

    return item

# =============================================================================
def text_filter_formstyle(form, fields, *args, **kwargs):
    """
        Custom formstyle for S3TextFilter
    """

    from gluon.html import DIV, LABEL, TAG

    def render_row(row_id, label, widget, comment, hidden=False):

        controls = DIV(DIV(LABEL("Search:",
                                 _class="prefix",
                                 ),
                           _class="large-4 columns",
                           _for=widget[1].attributes["_name"],
                           ),
                       DIV(widget,
                           _class="large-8 columns",
                           ),
                       _class="row collapse prefix-radius",
                       _id=row_id,
                       )
        return controls

    if args:
        row_id = form
        label = fields
        widget, comment = args
        hidden = kwargs.get("hidden", False)
        return render_row(row_id, label, widget, comment, hidden)
    else:
        parent = TAG[""]()
        for row_id, label, widget, comment in fields:
            parent.append(render_row(row_id, label, widget, comment))
        return parent

# =============================================================================
def filter_formstyle(form, fields, *args, **kwargs):
    """
        Custom formstyle for filters on the Incident Summary page
    """

    from gluon.html import DIV, FIELDSET, LEGEND

    def render_row(row_id, label, widget, comment, hidden=False):

        controls = FIELDSET(LEGEND(label),
                            widget,
                            )
        return DIV(controls, _id=row_id)

    if args:
        row_id = form
        label = fields
        widget, comment = args
        hidden = kwargs.get("hidden", False)
        return render_row(row_id, label, widget, comment, hidden)
    else:
        parent = TAG[""]()
        for row_id, label, widget, comment in fields:
            parent.append(render_row(row_id, label, widget, comment))
        return parent

# END =========================================================================
