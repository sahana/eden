# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

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
        #("translate", Storage(
        #    name_nice = "Translation Functionality",
        #    #description = "Selective translation of strings based on module.",
        #    module_type = None,
        #)),
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
    def customise_cms_post_resource(r, tablename):

        s3db = current.s3db
        table = s3db.cms_post

        from s3 import S3SQLCustomForm, S3SQLInlineComponent
        crud_form = S3SQLCustomForm((T("Text"), "body"),
                                    # @ToDo: Tags widget
                                    S3SQLInlineComponent("tag_post",
                                                         fields = [("", "tag_id")],
                                                         label = T("Tags"),
                                                         ),
                                    )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

    settings.customise_cms_post_resource = customise_cms_post_resource

    # -------------------------------------------------------------------------
    # Event/Incident Management
    #
    settings.event.incident_teams_tab = "Units"
    # Uncomment to preserve linked Incidents when an Event is deleted
    settings.event.cascade_delete_incidents = False

    # -------------------------------------------------------------------------
    def customise_event_event_controller(**attr):

        s3db = current.s3db
        s3 = current.response.s3

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

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard postp
            if callable(standard_prep):
                result = standard_prep(r)

            if r.representation == "popup":
                # Popups for lists in Parent Event of Incident Screen

                # No Title since this is on the Popup
                s3.crud_strings["event_event"].title_display = ""
                # No create button & Tweak list_fields
                cname = r.component_name
                if cname == "incident":
                    list_fields = ["date",
                                   "name",
                                   "incident_type_id",
                                   ]
                elif cname == "team":
                    list_fields = ["incident_id",
                                   "group_id",
                                   "status_id",
                                   ]
                elif cname == "post":
                    list_fields = ["date",
                                   "series_id",
                                   "priority",
                                   "status_id",
                                   "body",
                                   ]
                else:
                    # Shouldn't get here but want to avoid crashes
                    list_fields = []
                r.component.configure(insertable = False,
                                      list_fields = list_fields,
                                      )

            return True
        s3.prep = custom_prep

        # Custom rheader tabs
        attr = dict(attr)
        attr["rheader"] = wacop_event_rheader

        return attr

    settings.customise_event_event_controller = customise_event_event_controller

    # -------------------------------------------------------------------------
    def customise_event_incident_controller(**attr):

        s3db = current.s3db
        response = current.response
        s3 = response.s3

        # Load normal model to be able to override configuration
        table = s3db.event_incident

        def status_represent(value):
            " Represent the closed field as Status Open/Closed instead of True/False "

            if value is True:
                return T("Closed")
            elif value is False:
                return T("Open")
            else:
                return current.messages["NONE"]

        table.closed.label = T("Status")
        table.closed.represent = status_represent
        table.event_id.readable = table.event_id.writable = True

        # Custom Profile
        from templates.WACOP.controllers import incident_Profile
        s3db.set_method("event", "incident",
                        method = "custom",
                        action = incident_Profile)

        #s3.crud_strings["event_incident"].title_list =  T("Browse Incidents")

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard postp
            if callable(standard_prep):
                result = standard_prep(r)

            if r.method == "summary":
                # Map (only) in common area
                settings.ui.summary = ({"name": "table",
                                        "label": "Table",
                                        "widgets": [{"method": "datatable"}]
                                        },
                                       {"name": "charts",
                                        "label": "Report",
                                        "widgets": [{"method": "report",
                                                     "ajax_init": True}]
                                        },
                                       {"common": True,
                                        "name": "map",
                                        "label": "Map",
                                        "widgets": [{"method": "map",
                                                     "ajax_init": True}],
                                        },
                                       )

                from s3 import S3DateFilter, S3OptionsFilter, S3TextFilter
                from templates.WACOP.controllers import filter_formstyle_summary, text_filter_formstyle

                # @ToDo: This should use date/end_date not just date
                date_filter = S3DateFilter("date",
                                           #formstyle = filter_formstyle_summary,
                                           label = "",
                                           #hide_time = True,
                                           )
                date_filter.input_labels = {"ge": "Start Time/Date", "le": "End Time/Date"}

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
                                                  formstyle = filter_formstyle_summary,
                                                  options = {"*": T("All"),
                                                             False: T("Open"),
                                                             True: T("Closed"),
                                                             },
                                                  cols = 1,
                                                  multiple = False,
                                                  ),
                                  S3OptionsFilter("incident_type_id",
                                                  formstyle = filter_formstyle_summary,
                                                  label = T("Incident Type"),
                                                  noneSelectedText = "All",
                                                  widget = "multiselect",
                                                  ),
                                  date_filter,
                                  ]

                list_fields = ["closed",
                               "name",
                               (T("Type"), "incident_type_id"),
                               "location_id",
                               (T("Start"), "date"),
                               (T("End"), "end_date"),
                               "event_id",
                               ]

                s3db.configure("event_incident",
                               filter_widgets = filter_widgets,
                               list_fields = list_fields,
                               )

                # @ToDo: Configure Timeline
                # Last 5 days (@ToDo: Configurable Start/End & deduce appropriate unit)
                # Qty of Newly-opened Incidents per Unit
                pass

            elif r.method == "assign":
                current.menu.main = ""

            elif r.representation == "popup":
                # Popup just used to link to Event

                #s3.crud_strings["event_incident"].title_update =  T("Add to Event")

                from s3 import S3SQLCustomForm

                crud_form = S3SQLCustomForm("event_id",
                                            )

                s3db.configure("event_incident",
                               crud_form = crud_form,
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
                if r.method == "assign":
                    # No Top Menu
                    current.menu.main = ""
                    # Custom View to waste less space inside popup
                    import os
                    response.view = os.path.join(r.folder,
                                                 "modules", "templates",
                                                 "WACOP", "views",
                                                 "assign.html")
                else:
                    # Summary or Profile pages
                    # Additional styles
                    s3.external_stylesheets += ["https://cdn.knightlab.com/libs/timeline3/latest/css/timeline.css",
                                                "https://fonts.googleapis.com/css?family=Merriweather:400,700|Source+Sans+Pro:400,700",
                                                ]

                    if r.method == "summary":
                        # Open the Custom profile page instead of the normal one
                        from gluon import URL
                        from s3 import S3CRUD
                        custom_url = URL(args = ["[id]", "custom"])
                        S3CRUD.action_buttons(r,
                                              read_url=custom_url,
                                              update_url=custom_url)

                    # System-wide Alert
                    if current.auth.s3_has_role("ADMIN"):
                        # Admin user can edit system_wide alert
                        output["ADMIN"] = True
                    else:
                        output["ADMIN"] = False

                    ptable = s3db.cms_post
                    system_wide = current.db(ptable.name == "SYSTEM_WIDE").select(ptable.body,
                                                                                  limitby=(0, 1)
                                                                                  ).first()
                    if system_wide:
                        output["system_wide"] = system_wide.body
                    else:
                        output["system_wide"] = False

            return output
        s3.postp = custom_postp

        # Custom rheader tabs
        #attr = dict(attr)
        #attr["rheader"] = wacop_event_rheader
        attr["rheader"] = None

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

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        # Custom Profile
        from templates.WACOP.controllers import person_Dashboard
        current.s3db.set_method("pr", "person",
                                method = "dashboard",
                                action = person_Dashboard)

        # No sidebar menu
        current.menu.options = None

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

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

# END =========================================================================
