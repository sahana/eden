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

        # Load normal model to be able to override configuration
        s3db.event_incident

        # Custom Profile
        s3db.set_method("event", "incident",
                        method = "custom",
                        action = incident_Profile)

        list_fields = ["date",
                       "name",
                       "incident_type_id",
                       "event_id",
                       "closed",
                       "comments",
                       ]

        s3db.configure("event_incident",
                       list_fields = list_fields,
                       )

        # Custom rheader tabs
        attr = dict(attr)
        attr["rheader"] = wacop_event_rheader

        return attr

    settings.customise_event_incident_controller = customise_event_incident_controller

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
            representation = r.representation
            if representation == "html":

                T = current.T
                db = current.db
                s3db = current.s3db
                request = self.request
                response = current.response
                s3 = response.s3

                gtable = s3db.gis_location
                itable = s3db.event_incident
                #rtable = s3db.pr_group
                ertable = s3db.event_team
                #ptable = s3db.cms_post
                eptable = s3db.event_post

                record = r.record

                from gluon import DIV
                from s3 import FS, S3DateTime, s3_str

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

                # Resources dataTable
                tablename = "event_team"
                resource = s3db.resource(tablename)
                resource.add_filter(FS("incident_id") == incident_id)

                list_id = "custom-list-%s" % tablename

                get_vars = request.get_vars.get
                #if representation == "aadata":
                #    start = get_vars("displayStart", None)
                #    limit = get_vars("pageLength", 0)
                #else:
                start = get_vars("start", None)
                limit = get_vars("limit", 0)
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

                dtargs = attr.get("dtargs", {})

                # How many records per page?
                if s3.dataTable_pageLength:
                    display_length = s3.dataTable_pageLength
                else:
                    display_length = 10
                dtargs["dt_lengthMenu"] = [[10, 25, 50, -1],
                                           [10, 25, 50, s3_str(T("All"))]
                                           ]

                list_fields = ["group_id",
                               "status_id",
                               ]

                orderby = "pr_group.name"

                # Server-side pagination?
                if not s3.no_sspag:
                    dt_pagination = "true"
                    if not limit and display_length is not None:
                        limit = 2 * display_length
                    else:
                        limit = None
                else:
                    dt_pagination = "false"

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

                dtargs["dt_pagination"] = dt_pagination
                dtargs["dt_pageLength"] = display_length
                # @todo: fix base URL (make configurable?) to fix export options
                s3.no_formats = True
                dtargs["dt_base_url"] = r.url(method="", vars={})
                dtargs["dt_ajax_url"] = r.url(#vars={"update": 0}, # If we need to update multiple dataTables
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
                #create_popup = self._create_popup(r,
                #                                  widget,
                #                                  list_id,
                #                                  resource,
                #                                  context,
                #                                  totalrows)

                # Render the widget
                output["resources"] = DIV(contents,
                                          _class="card-holder",
                                          )

                import os
                response.view = os.path.join(request.folder,
                                             "modules", "templates",
                                             "WACOP", "views",
                                             "incident_profile.html")
                return output

        elif representation == "aadata":

            # Resources dataTable
            # @ToDo: Complete

            # Parse datatable filter/sort query
            searchq, orderby, left = resource.datatable_filter(list_fields,
                                                               get_vars)

            # ORDERBY fallbacks - datatable->widget->resource->default
            if not orderby:
                orderby = widget.get("orderby")
            if not orderby:
                orderby = resource.get_config("orderby")
            if not orderby:
                orderby = default_orderby()

            # DataTable filtering
            if searchq is not None:
                totalrows = resource.count()
                resource.add_filter(searchq)
            else:
                totalrows = None

            # Get the data table
            if totalrows != 0:
                dt, displayrows, ids = resource.datatable(fields=list_fields,
                                                          start=start,
                                                          limit=limit,
                                                          left=left,
                                                          orderby=orderby,
                                                          getids=False)
            else:
                dt, displayrows = None, 0

            if totalrows is None:
                totalrows = displayrows

            # Echo
            draw = int(get_vars.get("draw") or 0)

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

            return data

        raise HTTP(405, current.ERROR.BAD_METHOD)

# END =========================================================================
