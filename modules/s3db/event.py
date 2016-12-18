# -*- coding: utf-8 -*-

""" Sahana Eden Event Model

    @copyright: 2009-2016 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ("S3EventModel",
           "S3IncidentModel",
           "S3IncidentReportModel",
           "S3IncidentReportOrganisationGroupModel",
           "S3IncidentTypeModel",
           "S3IncidentTypeTagModel",
           "S3EventActivityModel",
           "S3EventAssetModel",
           "S3EventBookmarkModel",
           "S3EventCMSModel",
           "S3EventDCModel",
           "S3EventHRModel",
           "S3EventTeamModel",
           "S3EventImpactModel",
           #"S3EventIReportModel",
           "S3EventMapModel",
           "S3EventOrganisationModel",
           "S3EventProjectModel",
           #"S3EventRequestModel",
           "S3EventResourceModel",
           "S3EventSiteModel",
           "S3EventSitRepModel",
           "S3EventTagModel",
           "S3EventTaskModel",
           "S3EventShelterModel",
           "event_notification_dispatcher",
           "event_event_list_layout",
           "event_incident_list_layout",
           "event_rheader",
           )

from gluon import *
from gluon.storage import Storage

from ..s3 import *
from s3layouts import S3PopupLink

# =============================================================================
class S3EventModel(S3Model):
    """
        Event Model

        http://eden.sahanafoundation.org/wiki/BluePrintScenario

        Events are a high-level term, such as a 'Disaster'

        Link tables are in separate classes to increase performance & allow
        the system to be more modular
    """

    names = ("event_event_type",
             "event_type_id",
             "event_event",
             "event_event_id",
             "event_event_location",
             "event_event_tag",
             )

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3

        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        settings = current.deployment_settings

        messages = current.messages
        NONE = messages["NONE"]
        AUTOCOMPLETE_HELP = messages.AUTOCOMPLETE_HELP

        disaster = settings.get_event_label() # If we add more options in future then == "Disaster"
        exercise = settings.get_event_exercise()
        hierarchical_event_types = settings.get_event_types_hierarchical()

        # ---------------------------------------------------------------------
        # Event Types
        #
        tablename = "event_event_type"
        define_table(tablename,
                     Field("name", notnull=True, length=64,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     Field("parent", "reference event_event_type", # This form of hierarchy may not work on all Databases
                           label = T("SubType of"),
                           ondelete = "RESTRICT",
                           readable = hierarchical_event_types,
                           writable = hierarchical_event_types,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        type_represent = S3Represent(lookup=tablename, translate=True)

        if hierarchical_event_types:
            hierarchy = "parent"
            # Can't be defined in-line as otherwise get a circular reference
            table = db[tablename]
            table.parent.represent = type_represent
            table.parent.requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "event_event_type.id",
                                                  type_represent,
                                                  # If limiting to just 1 level of parent
                                                  #filterby="parent",
                                                  #filter_opts=(None,),
                                                  orderby="event_event_type.name"))
            event_type_widget = S3HierarchyWidget(lookup = "event_event_type",
                                                  represent = type_represent,
                                                  multiple = False,
                                                  leafonly = True,
                                                  )
            event_type_comment = None
        else:
            hierarchy = None
            event_type_widget = None
            event_type_comment = None
            # Uncomment these to use an Autocomplete & not a Dropdown
            #event_type_widget = S3AutocompleteWidget()
            #event_typecomment = DIV(_class="tooltip",
            #                        _title="%s|%s" % (T("Event Type"),
            #                                          AUTOCOMPLETE_HELP))

        if disaster:
            label = T("Disaster Type")
            crud_strings[tablename] = Storage(
                label_create = T("Create Disaster Type"),
                title_display = T("Disaster Type Details"),
                title_list = T("Disaster Types"),
                title_update = T("Edit Disaster Type"),
                title_upload = T("Import Disaster Types"),
                label_list_button = T("List Disaster Types"),
                label_delete_button = T("Delete Disaster Type"),
                msg_record_created = T("Disaster Type added"),
                msg_record_modified = T("Disaster Type updated"),
                msg_record_deleted = T("Disaster Type removed"),
                msg_list_empty = T("No Disaster Types currently registered")
                )
        else:
            label = T("Event Type")
            crud_strings[tablename] = Storage(
                label_create = T("Create Event Type"),
                title_display = T("Event Type Details"),
                title_list = T("Event Types"),
                title_update = T("Edit Event Type"),
                title_upload = T("Import Event Types"),
                label_list_button = T("List Event Types"),
                label_delete_button = T("Delete Event Type"),
                msg_record_created = T("Event Type added"),
                msg_record_modified = T("Event Type updated"),
                msg_record_deleted = T("Event Type removed"),
                msg_list_empty = T("No Event Types currently registered")
                )

        event_type_id = S3ReusableField("event_type_id", "reference %s" % tablename,
                                        label = label,
                                        ondelete = "RESTRICT",
                                        represent = type_represent,
                                        requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "event_event_type.id",
                                                              type_represent,
                                                              orderby="event_event_type.name",
                                                              sort=True)),
                                        sortby = "name",
                                        widget = event_type_widget,
                                        comment = event_type_comment,
                                        )

        configure(tablename,
                  deduplicate = S3Duplicate(),
                  hierarchy = hierarchy,
                  )

        # ---------------------------------------------------------------------
        # Events / Disasters
        #
        #   Events can be a way of grouping related Incidents or used standalone
        #
        # ---------------------------------------------------------------------
        tablename = "event_event"
        define_table(tablename,
                     self.super_link("doc_id", "doc_entity"),
                     Field("name",      # Name could be a code
                           length = 64,   # Mayon compatibility
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     event_type_id(),
                     #Field("intensity",
                     #      label = T("Intensity"),
                     #      comment = DIV(_class="tooltip",
                     #                    _title="%s|%s" % (T("Intensity"),
                     #                                      T("e.g. Category for a Typhoon or Magnitude for an Earthquake"))),
                     #      ),
                     self.org_organisation_id(
                        comment = DIV(_class="tooltip",
                                       _title="%s|%s" % (T("Organization"),
                                                         T("The organization managing this event"))),
                        # Enable in the template if-required
                        readable = False,
                        writable = False,
                        ),
                     Field("exercise", "boolean",
                           default = False,
                           label = T("Exercise?"),
                           represent = lambda opt: "√" if opt else NONE,
                           readable = exercise,
                           writable = exercise,
                           #comment = DIV(_class="tooltip",
                           #              _title="%s|%s" % (T("Exercise"),
                                                           # Should!
                           #                                T("Exercises mean all screens have a watermark & all notifications have a prefix."))),
                           ),
                     s3_datetime("start_date",
                                 default = "now",
                                 label = T("Start Date"),
                                 represent = "date",
                                 widget = "date",
                                 set_min = "#event_event_end_date",
                                 ),
                     s3_datetime("end_date",
                                 label = T("End Date"),
                                 represent = "date",
                                 widget = "date",
                                 set_max = "#event_event_start_date",
                                 ),
                     Field.Method("year", self.event_event_year),
                     Field("closed", "boolean",
                           default = False,
                           label = T("Closed"),
                           represent = s3_yes_no_represent,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        if disaster:
            label = T("Disaster")
            ADD_EVENT = T("New Disaster")
            crud_strings[tablename] = Storage(
                label_create = ADD_EVENT,
                title_display = T("Disaster Details"),
                title_list = T("Disasters"),
                title_update = T("Edit Disaster"),
                label_list_button = T("List Disasters"),
                label_delete_button = T("Delete Disaster"),
                msg_record_created = T("Disaster added"),
                msg_record_modified = T("Disaster updated"),
                msg_record_deleted = T("Disaster deleted"),
                msg_list_empty = T("No Disasters currently registered"))
        else:
            label = T("Event")
            ADD_EVENT = T("New Event")
            crud_strings[tablename] = Storage(
                label_create = ADD_EVENT,
                title_display = T("Event Details"),
                title_list = T("Events"),
                title_update = T("Edit Event"),
                label_list_button = T("List Events"),
                label_delete_button = T("Delete Event"),
                msg_record_created = T("Event added"),
                msg_record_modified = T("Event updated"),
                msg_record_deleted = T("Event deleted"),
                msg_list_empty = T("No Events currently registered"))

        represent = S3Represent(lookup=tablename)
        event_id = S3ReusableField("event_id", "reference %s" % tablename,
                                   sortby="name",
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "event_event.id",
                                                          represent,
                                                          filterby="closed",
                                                          filter_opts=(False,),
                                                          orderby="event_event.name",
                                                          sort=True)),
                                   represent = represent,
                                   label = label,
                                   ondelete = "CASCADE",
                                   # Uncomment these to use an Autocomplete & not a Dropdown
                                   #widget = S3AutocompleteWidget()
                                   #comment = DIV(_class="tooltip",
                                   #              _title="%s|%s" % (T("Event"),
                                   #                                AUTOCOMPLETE_HELP))
                                   )

        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()

        filter_widgets = [S3LocationFilter("event_location.location_id",
                                           levels = levels,
                                           label = T("Location"),
                                           ),
                          # @ToDo: Filter for events which are open within a date range
                          #S3DateFilter("start_date",
                          #             label = None,
                          #             hide_time = True,
                          #             input_labels = {"ge": "From", "le": "To"}
                          #             ),
                          # Typically we just need to filter by Year
                          S3OptionsFilter("year",
                                          label = T("Year"),
                                          ),
                          S3OptionsFilter("closed",
                                          label = T("Status"),
                                          options = OrderedDict([(False, T("Open")),
                                                                 (True, T("Closed")),
                                                                 ]),
                                          cols = 2,
                                          sort = False,
                                          ),
                          ]

        if hierarchical_event_types:
            filter_widgets.insert(0, S3HierarchyFilter("event_type_id",
                                                       label = T("Type"),
                                                       ))
        else:
            filter_widgets.insert(0, S3OptionsFilter("event_type_id",
                                                     label = T("Type"),
                                                     #multiple = False,
                                                     #options = lambda: \
                                                     #  s3_get_filter_opts("event_event_type",
                                                     #                     translate = True)
                                                     ))
        report_fields = ["event_type_id",
                         ]
        rappend = report_fields.append
        for level in levels:
            rappend("event_location.location_id$%s" % level)
        rappend((T("Year"), "year"))

        report_options = Storage(
            rows = report_fields,
            cols = report_fields,
            fact = [(T("Number of Disasters"), "count(id)")],
            defaults = Storage(
                rows = "event_type_id",
                cols = "event_location.location_id$%s" % levels[0], # Highest-level of hierarchy
                fact = "count(id)",
                totals = True,
                chart = "breakdown:rows",
                table = "collapse",
                ),
            )

        # Custom Form
        crud_fields = ["name",
                       "event_type_id",
                       "start_date",
                       "closed",
                       "end_date",
                       S3SQLInlineComponent("event_location",
                                            label = T("Locations"),
                                            #multiple = False,
                                            fields = [("", "location_id")],
                                            ),
                       "comments",
                       ]

        list_fields = ["name",
                       (T("Type"), "event_type_id$name"),
                       (T("Location"), "location.name"),
                       "start_date",
                       "closed",
                       "comments",
                       ]

        if exercise:
            crud_fields.insert(1, "exercise")
            list_fields.insert(4, "exercise")
            filter_widgets.insert(2, S3OptionsFilter("exercise",
                                                     label = T("Exercise"),
                                                     options = OrderedDict([(True, T("Yes")),
                                                                            (False, T("No")),
                                                                            ]),
                                                     cols = 2,
                                                     sort = False,
                                                     ))

        crud_form = S3SQLCustomForm(*crud_fields)

        configure(tablename,
                  context = {"location": "event_location.location_id",
                             },
                  crud_form = crud_form,
                  deduplicate = S3Duplicate(primary = ("name",
                                                       ),
                                            secondary = ("event_type_id",
                                                         "start_date",
                                                         ),
                                            ),
                  extra_fields = ["start_date"],
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  list_layout = event_event_list_layout,
                  list_orderby = "event_event.start_date desc",
                  orderby = "event_event.start_date desc",
                  report_options = report_options,
                  super_entity = "doc_entity",
                  update_onaccept = self.event_update_onaccept,
                  )

        # Components
        self.add_components(tablename,
                            event_incident = "event_id",
                            dc_collection = {"link": "event_collection",
                                             "joinby": "event_id",
                                             "key": "collection_id",
                                             "actuate": "replace",
                                             },
                            dc_target = {"link": "event_target",
                                         "joinby": "event_id",
                                         "key": "target_id",
                                         "actuate": "replace",
                                         },
                            doc_sitrep = {"link": "event_sitrep",
                                          "joinby": "event_id",
                                          "key": "sitrep_id",
                                          "actuate": "replace",
                                          },
                            gis_location = {"link": "event_event_location",
                                            "joinby": "event_id",
                                            "key": "location_id",
                                            "actuate": "hide",
                                            },
                            event_activity = {"name": "event_activity",
                                              "joinby": "event_id",
                                              },
                            project_activity = {"link": "event_activity",
                                                "joinby": "event_id",
                                                "key": "activity_id",
                                                "actuate": "replace",
                                                },
                            event_project = {"name": "event_project",
                                             "joinby": "event_id",
                                             },
                            project_project = {"link": "event_project",
                                               "joinby": "event_id",
                                               "key": "project_id",
                                               "actuate": "replace",
                                               },
                            event_event_location = "event_id",
                            event_post = "event_id",
                            event_event_tag = {"name": "tag",
                                               "joinby": "event_id",
                                               },
                            event_team = "event_id",
                            pr_group = {"link": "event_team",
                                        "joinby": "event_id",
                                        "key": "group_id",
                                        "actuate": "hide",
                                        "autodelete": False,
                                        },
                            req_req = "event_id",
                            stats_impact = {"link": "event_event_impact",
                                            "joinby": "event_id",
                                            "key": "impact_id",
                                            "actuate": "replace",
                                            },
                            event_event_impact = "event_id",
                            )

        self.set_method("event", "event",
                        method = "dispatch",
                        action = event_notification_dispatcher)

        # ---------------------------------------------------------------------
        # Event Locations (link table)
        #
        tablename = "event_event_location"
        define_table(tablename,
                     event_id(),
                     self.gis_location_id(
                        widget = S3LocationSelector(show_map=False),
                        #widget = S3LocationAutocompleteWidget(),
                        requires = IS_LOCATION(),
                        represent = self.gis_LocationRepresent(sep=", "),
                        #comment = S3PopupLink(c = "gis",
                        #                      f = "location",
                        #                      label = T("Create Location"),
                        #                      title = T("Location"),
                        #                      tooltip = AUTOCOMPLETE_HELP,
                        #                      ),
                        ),
                     *s3_meta_fields())

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("event_id",
                                                       "location_id",
                                                       ),
                                            ),
                  )

        # ---------------------------------------------------------------------
        # Event Tags
        # - Key-Value extensions
        # - can be used to identify a Source
        # - can be used to add extra attributes (e.g. Area, Population)
        # - can link Events to other Systems, such as:
        #   * GLIDE (http://glidenumber.net/glide/public/about.jsp)
        #   * OCHA Financial Tracking System, for HXL (http://fts.unocha.org/api/v1/emergency/year/2013.xml)
        #   * Mayon
        #   * WebEOC
        # - can be a Triple Store for Semantic Web support
        #
        tablename = "event_event_tag"
        define_table(tablename,
                     event_id(),
                     # key is a reserved word in MySQL
                     Field("tag", label=T("Key")),
                     Field("value", label=T("Value")),
                     s3_comments(),
                     *s3_meta_fields())

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("event_id",
                                                       "tag",
                                                       ),
                                            ),
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(event_type_id = event_type_id,
                    event_event_id = event_id,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Return safe defaults in case the model has been deactivated.
        """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return dict(event_event_id = lambda **attr: dummy("event_id"),
                    event_type_id = lambda **attr: dummy("event_type_id"),
                    )

    # =============================================================================
    @staticmethod
    def event_event_year(row):
        """
            Virtual field for event_event - returns the year of this entry
            used for report.

            Requires "start_date" to be in extra_fields

            @param row: the Row

            @ToDo: Extend this to show multiple years if open for multiple?
        """

        try:
            thisdate = row["event_event.start_date"]
        except AttributeError:
            return current.messages["NONE"]
        if not thisdate:
            return current.messages["NONE"]

        return thisdate.year

    # -------------------------------------------------------------------------
    @staticmethod
    def event_update_onaccept(form):
        """
            When an Event is updated, check for closure
        """

        form_vars = form.vars
        if form_vars.closed:
            event = form_vars.id
            # Ensure this event isn't active in the session
            s3 = current.session.s3
            if s3.event == event:
                s3.event = None

            # @ToDo: Hide the Event from the Map menu
            #gis = current.gis
            #config = gis.get_config()
            #if config == config.config_id:
            #    # Reset to the Default Map
            #    gis.set_config(0)

            # Expire all related Posts
            db = current.db
            ltable = current.s3db.event_post
            table = db.cms_post
            rows = db(ltable.event_id == event).select(ltable.post_id)
            for row in rows:
                db(table.id == row.post_id).update(expired=True)

# =============================================================================
class S3IncidentModel(S3Model):
    """
        Incidents
         - the primary unit at which things are managed:
            Scenarios are designed
            Resources are assigned
            Situation Reports are made
    """

    names = ("event_incident",
             "event_incident_id",
             )

    def model(self):

        T = current.T
        db = current.db
        settings = current.deployment_settings
        set_method = self.set_method

        if settings.get_event_cascade_delete_incidents():
            ondelete = "CASCADE"
        else:
            ondelete = "SET NULL"

        # ---------------------------------------------------------------------
        # Incidents
        #
        #  Incidents are the unit at which responses are managed.
        #  They can be Exercises or real Incidents.
        #  They can be instantiated from Scenario Templates.
        #
        tablename = "event_incident"
        self.define_table(tablename,
                          self.super_link("doc_id", "doc_entity"),
                          # Enable in template if-required
                          self.event_event_id(ondelete = ondelete,
                                              readable = False,
                                              writable = False,
                                              ),
                          self.event_incident_type_id(),
                          self.scenario_scenario_id(),
                          Field("name", notnull=True, # Name could be a code
                                length = 64,
                                label = T("Name"),
                                requires = [IS_NOT_EMPTY(),
                                            IS_LENGTH(64),
                                            ],
                                ),
                          Field("exercise", "boolean",
                                label = T("Exercise?"),
                                represent = lambda opt: "√" if opt else None,
                                #comment = DIV(_class="tooltip",
                                #              _title="%s|%s" % (T("Exercise"),
                                                                 # Should!
                                #                                T("Exercises mean all screens have a watermark & all notifications have a prefix."))),
                                ),
                          s3_datetime(default = "now",
                                      comment = DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Date"),
                                                                      T("The time at which the Incident started."))),
                                      ),
                          s3_datetime(name = "end_date",
                                      label = T("Closed at"),
                                      comment = DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Closed at"),
                                                                      T("The time when the Incident was closed."))),
                                      ),
                          Field("closed", "boolean",
                                default = False,
                                label = T("Closed"),
                                represent = s3_yes_no_represent,
                                ),
                          # Enable this field in templates if-required
                          self.org_organisation_id(label = T("Lead Organization"), # Lead Responder
                                                   readable = False,
                                                   writable = False,
                                                   ),
                          self.gis_location_id(),
                          s3_comments(),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Incident"),
            title_display = T("Incident Details"),
            title_list = T("Incidents"),
            title_update = T("Edit Incident"),
            label_list_button = T("List Incidents"),
            label_delete_button = T("Delete Incident"),
            msg_record_created = T("Incident added"),
            msg_record_modified = T("Incident updated"),
            msg_record_deleted = T("Incident removed"),
            msg_list_empty = T("No Incidents currently registered"))

        represent = S3Represent(lookup=tablename)
        incident_id = S3ReusableField("incident_id", "reference %s" % tablename,
                                      label = T("Incident"),
                                      ondelete = "RESTRICT",
                                      represent = represent,
                                      requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "event_incident.id",
                                                              represent,
                                                              filterby="closed",
                                                              filter_opts=(False,),
                                                              orderby="event_incident.name",
                                                              sort=True)),
                                      sortby = "name",
                                      # Uncomment these to use an Autocomplete & not a Dropdown
                                      #widget = S3AutocompleteWidget()
                                      #comment = DIV(_class="tooltip",
                                      #              _title="%s|%s" % (T("Incident"),
                                      #                                current.messages.AUTOCOMPLETE_HELP))
                                      )

        # @ToDo: Move this workflow into Templates?
        # - or useful to have good defaults
        if settings.has_module("project"):
            create_next_url = URL(c="event", f="incident",
                                  args=["[id]", "task"])
        elif settings.has_module("hrm"):
            create_next_url = URL(c="event", f="incident",
                                  args=["[id]", "human_resource"])
        elif settings.has_module("asset"):
            create_next_url = URL(c="event", f="incident",
                                  args=["[id]", "asset"])
        else:
            create_next_url = URL(c="event", f="incident",
                                  args=["[id]", "site"])

        self.configure(tablename,
                       create_next = create_next_url,
                       create_onaccept = self.incident_create_onaccept,
                       deduplicate = S3Duplicate(),
                       list_fields = ["date",
                                      "name",
                                      "incident_type_id",
                                      "exercise",
                                      "closed",
                                      "comments",
                                      ],
                       list_layout = event_incident_list_layout,
                       # Most recent Incident first
                       orderby = "event_incident.date desc",
                       super_entity = "doc_entity",
                       update_onaccept = self.incident_update_onaccept,
                       )

        # Components
        self.add_components(tablename,
                            event_asset = "incident_id",
                            asset_asset = {"link": "event_asset",
                                           "joinby": "incident_id",
                                           "key": "asset_id",
                                           #"actuate": "embed",
                                           "actuate": "hide",
                                           #"autocomplete": "number",
                                           "autodelete": False,
                                           },
                            event_human_resource = "incident_id",
                            hrm_human_resource = ({"link": "event_human_resource",
                                                   "joinby": "incident_id",
                                                   "key": "human_resource_id",
                                                   "actuate": "hide",
                                                   "autodelete": False,
                                                   },
                                                  {"name": "assign",
                                                   "link": "event_human_resource",
                                                   "joinby": "incident_id",
                                                   "key": "human_resource_id",
                                                   "actuate": "hide",
                                                   "autodelete": False,
                                                   },
                                                  ),
                            event_organisation = "incident_id",
                            org_organisation = {"link": "event_organisation",
                                                "joinby": "incident_id",
                                                "key": "organisation_id",
                                                #"actuate": "embed",
                                                "actuate": "hide",
                                                #"autocomplete": "name",
                                                "autodelete": False,
                                                },
                            event_team = "incident_id",
                            pr_group = {"link": "event_team",
                                        "joinby": "incident_id",
                                        "key": "group_id",
                                        "actuate": "hide",
                                        "autodelete": False,
                                        },
                            event_post = "incident_id",
                            event_site = "incident_id",
                            event_sitrep = {"name": "incident_sitrep",
                                            "joinby": "incident_id",
                                            },
                            doc_sitrep = {"link": "event_sitrep",
                                          "joinby": "incident_id",
                                          "key": "sitrep_id",
                                          "actuate": "replace",
                                          #"autocomplete": "name",
                                          "autodelete": True,
                                          },
                            event_task = {"name": "incident_task",
                                          "joinby": "incident_id",
                                          },
                            project_task = {"link": "event_task",
                                            "joinby": "incident_id",
                                            "key": "task_id",
                                            "actuate": "replace",
                                            #"autocomplete": "name",
                                            "autodelete": True,
                                            },
                            gis_config = {"link": "event_config",
                                          "joinby": "incident_id",
                                          "multiple": False,
                                          "key": "config_id",
                                          "actuate": "replace",
                                          "autocomplete": "name",
                                          "autodelete": True,
                                          },
                            stats_impact = {"link": "event_event_impact",
                                            "joinby": "incident_id",
                                            "key": "impact_id",
                                            "actuate": "replace",
                                            "autodelete": True,
                                            },
                            )

        # Custom Methods
        set_method("event", "incident",
                   method = "add_tag",
                   action = self.incident_add_tag)

        set_method("event", "incident",
                   method = "remove_tag",
                   action = self.incident_remove_tag)

        set_method("event", "incident",
                   method = "add_bookmark",
                   action = self.incident_add_bookmark)

        set_method("event", "incident",
                   method = "remove_bookmark",
                   action = self.incident_remove_bookmark)

        # Custom Method to Assign HRs
        set_method("event", "incident",
                   method = "assign",
                   action = self.hrm_AssignMethod(component="human_resource"))

        # Custom Method to Dispatch HRs
        set_method("event", "incident",
                   method = "dispatch",
                   action = event_notification_dispatcher)

        # Pass names back to global scope (s3.*)
        return dict(event_incident_id = incident_id,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Return safe defaults in case the model has been deactivated.
        """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return dict(event_incident_id = lambda **attr: dummy("incident_id"),
                    )

    # ---------------------------------------------------------------------
    @staticmethod
    def incident_create_onaccept(form):
        """
            When an Incident is instantiated, populate defaults
        """

        form_vars = form.vars

        closed = form_vars.get("closed", False)

        incident = form_vars.get("id")
        if incident and not closed:
            # Set the Incident in the session
            current.session.s3.incident = incident
        event = form_vars.get("event_id")
        if event and not closed:
            # Set the Event in the session
            current.session.s3.event = event

        s3db = current.s3db
        db = current.db
        ctable = s3db.gis_config
        mapconfig = None
        scenario = form_vars.get("scenario_id")
        if scenario:
            # We have been instantiated from a Scenario, so
            # copy all resources from the Scenario to the Incident

            # Read the source resource tables
            table = s3db.scenario_scenario
            otable = s3db.scenario_organisation
            stable = s3db.scenario_site
            mtable = s3db.scenario_config
            query = (table.id == scenario)
            squery = query & (stable.scenario_id == table.id)
            mquery = query & (mtable.scenario_id == table.id) & \
                             (ctable.id == mtable.config_id)
            facilities = db(squery).select(stable.site_id)
            mapconfig = db(mquery).select(ctable.ALL).first()

            # Write them to their respective destination tables
            stable = s3db.event_site
            for row in facilities:
                stable.insert(incident_id=incident,
                              site_id=row.site_id)

            # Modules which can be disabled
            htable = s3db.table("scenario_human_resource", None) # @ToDo: Change to Positions
            if htable:
                hquery = query & (htable.scenario_id == table.id)
                hrms = db(hquery).select(htable.human_resource_id)
                htable = s3db.event_human_resource
                for row in hrms:
                    htable.insert(incident_id=incident,
                                  human_resource_id=row.human_resource_id)

            atable = s3db.table("scenario_asset", None)
            if atable:
                aquery = query & (atable.scenario_id == table.id)
                assets = db(aquery).select(atable.asset_id)
                atable = s3db.event_asset
                for row in assets:
                    atable.insert(incident_id=incident,
                                  asset_id=row.asset_id)

            ttable = s3db.table("scenario_task", None)
            if ttable:
                tquery = query & (ttable.scenario_id == table.id)
                tasks = db(tquery).select(ttable.task_id)
                ttable = s3db.event_task
                for row in tasks:
                    ttable.insert(incident_id=incident,
                                  task_id=row.task_id)

        if mapconfig:
            # Incident's Map Config is a copy of the Default / Scenario's
            # so that it can be changed within the Incident without
            # contaminating the base one
            del mapconfig["id"]
            del mapconfig["uuid"]
            mapconfig["name"] = form_vars.name
            config = ctable.insert(**mapconfig.as_dict())
            mtable = s3db.event_config
            mtable.insert(incident_id = incident,
                          config_id = config,
                          )
            # Activate this config
            if not closed:
                current.gis.set_config(config)
            # @ToDo: Add to GIS Menu? Separate Menu?

        else:
            # We have been created without a Scenario or from a Scenario without a Map Config
            # Create a new Map Config
            config = ctable.insert(name = form_vars.name)
            mtable = s3db.event_config
            mtable.insert(incident_id=incident,
                          config_id=config)
            # Activate this config
            if not closed:
                current.gis.set_config(config)
            # Viewport can be saved from the Map's toolbar
            # @ToDo: Add to GIS Menu? Separate Menu?

    # -------------------------------------------------------------------------
    @staticmethod
    def incident_update_onaccept(form):
        """
            When an Incident is updated, check for closure
        """

        form_vars = form.vars
        if form_vars.closed:
            incident = form_vars.id
            # Ensure this incident isn't active in the session
            s3 = current.session.s3
            if s3.incident == incident:
                s3.incident = None

            # @ToDo: Hide the Incident from the Map menu
            #gis = current.gis
            #config = gis.get_config()
            #if config == config.config_id:
            #    # Reset to the Default Map
            #    gis.set_config(0)

            # Expire all related Posts
            db = current.db
            ltable = current.s3db.event_post
            table = db.cms_post
            rows = db(ltable.incident_id == incident).select(ltable.post_id)
            for row in rows:
                db(table.id == row.post_id).update(expired=True)

    # -----------------------------------------------------------------------------
    @staticmethod
    def incident_add_tag(r, **attr):
        """
            Add a Tag to an Incident

            S3Method for interactive requests
            - designed to be called as an afterTagAdded callback to tag-it.js
        """

        incident_id = r.id
        if not incident_id or len(r.args) < 3:
            raise HTTP(405, current.ERROR.BAD_METHOD)

        tag = r.args[2]
        db = current.db
        s3db = current.s3db
        ttable = s3db.cms_tag
        ltable = s3db.event_tag
        exists = db(ttable.name == tag).select(ttable.id,
                                               ttable.deleted,
                                               ttable.deleted_fk,
                                               limitby=(0, 1)
                                               ).first()
        if exists:
            tag_id = exists.id
            if exists.deleted:
                if exists.deleted_fk:
                    data = json.loads(exists.deleted_fk)
                    data["deleted"] = False
                else:
                    data = dict(deleted=False)
                db(ttable.id == tag_id).update(**data)
        else:
            tag_id = ttable.insert(name=tag)
        query = (ltable.tag_id == tag_id) & \
                (ltable.incident_id == incident_id)
        exists = db(query).select(ltable.id,
                                  ltable.deleted,
                                  ltable.deleted_fk,
                                  limitby=(0, 1)
                                  ).first()
        if exists:
            if exists.deleted:
                if exists.deleted_fk:
                    data = json.loads(exists.deleted_fk)
                    data["deleted"] = False
                else:
                    data = dict(deleted=False)
                db(ltable.id == exists.id).update(**data)
        else:
            ltable.insert(incident_id = incident_id,
                          tag_id = tag_id,
                          )

        output = current.xml.json_message(True, 200, "Tag Added")
        current.response.headers["Content-Type"] = "application/json"
        return output

    # -----------------------------------------------------------------------------
    @staticmethod
    def incident_remove_tag(r, **attr):
        """
            Remove a Tag from an Incident

            S3Method for interactive requests
            - designed to be called as an afterTagRemoved callback to tag-it.js
        """

        incident_id = r.id
        if not incident_id or len(r.args) < 3:
            raise HTTP(405, current.ERROR.BAD_METHOD)

        tag = r.args[2]
        db = current.db
        s3db = current.s3db
        ttable = s3db.cms_tag
        exists = db(ttable.name == tag).select(ttable.id,
                                               ttable.deleted,
                                               limitby=(0, 1)
                                               ).first()
        if exists:
            tag_id = exists.id
            ltable = s3db.event_tag
            query = (ltable.tag_id == tag_id) & \
                    (ltable.incident_id == incident_id)
            exists = db(query).select(ltable.id,
                                      ltable.deleted,
                                      limitby=(0, 1)
                                      ).first()
            if exists and not exists.deleted:
                resource = s3db.resource("event_tag", id=exists.id)
                resource.delete()

        output = current.xml.json_message(True, 200, "Tag Removed")
        current.response.headers["Content-Type"] = "application/json"
        return output

    # -----------------------------------------------------------------------------
    @staticmethod
    def incident_add_bookmark(r, **attr):
        """
            Bookmark an Incident

            S3Method for interactive requests
        """

        incident_id = r.id
        user = current.auth.user
        user_id = user and user.id
        if not incident_id or not user_id:
            raise HTTP(405, current.ERROR.BAD_METHOD)

        db = current.db
        s3db = current.s3db
        ltable = s3db.event_bookmark
        query = (ltable.incident_id == incident_id) & \
                (ltable.user_id == user_id)
        exists = db(query).select(ltable.id,
                                  ltable.deleted,
                                  ltable.deleted_fk,
                                  limitby=(0, 1)
                                  ).first()
        if exists:
            link_id = exists.id
            if exists.deleted:
                if exists.deleted_fk:
                    data = json.loads(exists.deleted_fk)
                    data["deleted"] = False
                else:
                    data = dict(deleted=False)
                db(ltable.id == link_id).update(**data)
        else:
            link_id = ltable.insert(incident_id = incident_id,
                                    user_id = user_id,
                                    )

        output = current.xml.json_message(True, 200, "Bookmark Added")
        current.response.headers["Content-Type"] = "application/json"
        return output

    # -----------------------------------------------------------------------------
    @staticmethod
    def incident_remove_bookmark(r, **attr):
        """
            Remove a Bookmark for an Incident

            S3Method for interactive requests
        """

        incident_id = r.id
        user = current.auth.user
        user_id = user and user.id
        if not incident_id or not user_id:
            raise HTTP(405, current.ERROR.BAD_METHOD)

        s3db = current.s3db
        ltable = s3db.event_bookmark
        query = (ltable.incident_id == incident_id) & \
                (ltable.user_id == user_id)
        exists = current.db(query).select(ltable.id,
                                          ltable.deleted,
                                          limitby=(0, 1)
                                          ).first()
        if exists and not exists.deleted:
            resource = s3db.resource("event_bookmark", id=exists.id)
            resource.delete()

        output = current.xml.json_message(True, 200, "Bookmark Removed")
        current.response.headers["Content-Type"] = "application/json"
        return output


# =============================================================================
class S3IncidentReportModel(S3Model):
    """
        Incident Reports
         - reports about incidents
         - useful for busy call centres which may receive many reports about a
           single incident and may receive calls which need logging but don't
           get responded to as an Incident (e.g. Out of Scope)

        @ToDo: Deprecate IRS module by porting functionality here
    """

    names = ("event_incident_report",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Incident Reports
        #
        tablename = "event_incident_report"
        self.define_table(tablename,
                          self.super_link("doc_id", "doc_entity"),
                          # @ToDo: Use link tables?
                          self.event_event_id(ondelete = "CASCADE"),
                          #self.event_incident_id(ondelete = "CASCADE"),
                          s3_datetime(default="now"),
                          Field("name", notnull=True,
                                label = T("Title"),
                                requires = IS_NOT_EMPTY(),
                                ),
                          self.event_incident_type_id(),
                          self.gis_location_id(),
                          self.pr_person_id(label = T("Reported By"),
                                            ),
                          Field("closed", "boolean",
                                default = False,
                                label = T("Closed"),
                                represent = s3_yes_no_represent,
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Incident Report"),
            title_display = T("Incident Report Details"),
            title_list = T("Incident Reports"),
            title_update = T("Edit Incident Report"),
            label_list_button = T("List Incident Reports"),
            label_delete_button = T("Remove Incident Report from this event"),
            msg_record_created = T("Incident Report added"),
            msg_record_modified = T("Incident Report updated"),
            msg_record_deleted = T("Incident Report removed"),
            msg_list_empty = T("No Incident Reports currently registered for this event"))

        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()

        report_fields = ["name",
                         "incident_type_id",
                         "closed",
                         ]

        text_fields = ["name",
                       "comments",
                       #"organisation_id$name",
                       #"organisation_id$acronym",
                       "location_id$name",
                       ]

        list_fields = ["name",
                       "date",
                       "incident_type_id",
                       "closed",
                       ]

        for level in levels:
            lfield = "location_id$%s" % level
            report_fields.append(lfield)
            text_fields.append(lfield)
            list_fields.append(lfield)

        filter_widgets = [S3TextFilter(text_fields,
                                       label = T("Search"),
                                       ),
                          S3OptionsFilter("incident_type_id",
                                          label = T("Type"),
                                          ),
                          S3LocationFilter("location_id",
                                           levels = levels,
                                           ),
                          ]

        self.configure(tablename,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       report_options = Storage(
                        rows=report_fields,
                        cols=report_fields,
                        fact=report_fields,
                        defaults=Storage(rows = "location_id$L1", #lfield, # Lowest-level of hierarchy
                                         cols = "incident_type_id",
                                         fact = "count(name)",
                                         totals = True)
                        ),
                       super_entity = "doc_entity",
                       )

        # Components
        self.add_components(tablename,
                            # Coalitions
                            org_group = {"link": "event_incident_report_group",
                                         "joinby": "incident_report_id",
                                         "key": "group_id",
                                         "actuate": "hide",
                                         },
                            # Format for InlineComponent/filter_widget
                            event_incident_report_group = "incident_report_id",
                            )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventActivityModel(S3Model):
    """
        Link Project Activities to Events
    """

    names = ("event_activity",
             )

    def model(self):

        tablename = "event_activity"
        self.define_table(tablename,
                          self.event_event_id(empty = False,
                                              ondelete = "CASCADE"),
                          #self.event_incident_id(ondelete = "CASCADE"),
                          self.project_activity_id(#ondelete = "CASCADE", # default anyway
                                                   ),
                          *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventResourceModel(S3Model):
    """
        Resources Assigned to Events/Incidents
        - depends on Stats module

        Whilst there is a Quantity option, this is envisaged to usually be 1
        - these are typically named, trackable resources

        @ToDo: Optional link to org_resource to e.g. mark resources as assigned
    """

    names = ("event_resource",)

    def model(self):

        if not current.deployment_settings.has_module("stats"):
            current.log.warning("Event Resource Model needs Stats module enabling")
            return {}

        T = current.T
        super_link = self.super_link

        status_opts = {1: T("Available"),
                       2: T("Assigned"),
                       3: T("En Route"),
                       }

        # ---------------------------------------------------------------------
        # Resources
        #
        tablename = "event_resource"
        self.define_table(tablename,
                          # Instance
                          super_link("data_id", "stats_data"),
                          super_link("track_id", "sit_trackable"),
                          # Resources are normally managed at the Incident level
                          #self.event_event_id(ondelete = ondelete,
                          #                    # enable in template if-required
                          #                    readable = False,
                          #                    writable = False,
                          #                    ),
                          self.event_incident_id(ondelete = "CASCADE"),
                          # This is a component, so needs to be a super_link
                          # - can't override field name, ondelete or requires
                          super_link("parameter_id", "stats_parameter",
                                     empty = False,
                                     instance_types = ("org_resource_type",),
                                     label = T("Resource Type"),
                                     represent = S3Represent(lookup="stats_parameter",
                                                             translate=True),
                                     readable = True,
                                     writable = True,
                                     comment = S3PopupLink(c = "org",
                                                           f = "resource_type",
                                                           vars = {"child": "parameter_id"},
                                                           title = T("Create Resource Type"),
                                                           ),
                                     ),
                          Field("status", "integer",
                                label = T("Status"),
                                represent = lambda opt: \
                                    status_opts.get(opt) or current.messages.UNKNOWN_OPT,
                                requires = IS_IN_SET(status_opts),
                                ),
                          Field("name",
                                label = T("Name"),
                                ),
                          Field("value", "integer",
                                default = 1,
                                label = T("Quantity"),
                                requires = IS_INT_IN_RANGE(0, 999),
                                ),
                          self.org_organisation_id(),
                          self.pr_person_id(label = T("Contact")),
                          # @ToDo: Make use of S3Track:
                          # Base Location: Enable field only in Create form
                          self.gis_location_id(#readable = False,
                                               #writable = False,
                                               ),
                          #Field.Method("location", lambda row: self.sit_location(row, tablename)),
                          # @ToDo: Deprecate once we start using S3Track
                          s3_datetime(default = "now"),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create=T("Add Resource"),
            title_display=T("Resource Details"),
            title_list=T("Resources"),
            title_update=T("Edit Resource"),
            title_map=T("Map of Resources"),
            title_upload=T("Import Resources"),
            label_list_button=T("List Resources"),
            label_delete_button=T("Delete Resource"),
            msg_record_created=T("Resource added"),
            msg_record_modified=T("Resource updated"),
            msg_record_deleted=T("Resource deleted"),
            msg_list_empty=T("No Resources assigned to Incident"))

        # Custom Methods
        #self.set_method("event", "resource",
        #                method = "check-in",
        #                action = S3CheckInMethod())

        # List Fields
        #list_fields = ["id",
        #               "incident_id",
        #               "parameter_id",
        #               "status",
        #               "name",
        #               "value",
        #               "organisation_id",
        #               "person_id",
        #               "location_id",
        #               #(T("Location"), "location"),
        #               "comments",
        #               ]

        # Filter Widgets
        filter_widgets = [S3TextFilter(["organisation_id$name",
                                        "location_id",
                                        "parameter_id$name",
                                        "comments",
                                        ],
                                       label = T("Search"),
                                       ),
                          S3OptionsFilter("parameter_id",
                                          label = T("Type"),
                                          ),
                          ]

        # Report options
        report_fields = ["incident_id",
                         "organisation_id",
                         "parameter_id",
                         ]

        report_options = Storage(rows = report_fields,
                                 cols = report_fields,
                                 fact = [(T("Total Number of Resources"), "sum(value)"),
                                         (T("Number of Resources"), "count(value)"),
                                         ],
                                 defaults = Storage(rows = "incident_id",
                                                    cols = "parameter_id",
                                                    fact = "sum(value)",
                                                    totals = True,
                                                    chart = "barchart:rows",
                                                    #table = "collapse",
                                                    )
                                 )

        self.configure(tablename,
                       context = {#"event": "event_id",
                                  "incident": "incident_id",
                                  "location": "location_id",
                                  "organisation": "organisation_id",
                                  },
                       filter_widgets = filter_widgets,
                       #list_fields = list_fields,
                       list_layout = event_resource_list_layout,
                       orderby = "event_resource.date desc",
                       report_options = report_options,
                       super_entity = ("stats_data", "sit_trackable"),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3IncidentReportOrganisationGroupModel(S3Model):
    """
        Links between Incident Reports & Organisation Groups
    """

    names = ("event_incident_report_group",
             )

    def model(self):

        represent = S3Represent(lookup="event_incident_report")

        # ---------------------------------------------------------------------
        # Incident Reports <> Coalitions link table
        #
        tablename = "event_incident_report_group"
        self.define_table(tablename,
                          Field("incident_report_id", self.event_incident_report,
                                represent = represent,
                                requires = IS_ONE_OF(current.db, "event_incident_report.id",
                                                     represent,
                                                     sort=True,
                                                     ),
                                ),
                          self.org_group_id(empty=False),
                          *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3IncidentTypeModel(S3Model):
    """
        Incident Types
    """

    names = ("event_incident_type",
             "event_incident_type_id",
             )

    def model(self):

        T = current.T
        db = current.db

        hierarchical_incident_types = \
            current.deployment_settings.get_incident_types_hierarchical()

        # ---------------------------------------------------------------------
        # Incident Types
        #
        tablename = "event_incident_type"
        self.define_table(tablename,
                          Field("name", notnull=True, length=64,
                                label = T("Name"),
                                requires = [IS_NOT_EMPTY(),
                                            IS_LENGTH(64),
                                            ],
                                ),
                          Field("parent", "reference event_incident_type", # This form of hierarchy may not work on all Databases
                                label = T("SubType of"),
                                ondelete = "RESTRICT",
                                readable = hierarchical_incident_types,
                                writable = hierarchical_incident_types,
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        type_represent = S3Represent(lookup=tablename, translate=True)

        if hierarchical_incident_types:
            hierarchy = "parent"
            # Can't be defined in-line as otherwise get a circular reference
            table = db[tablename]
            table.parent.represent = type_represent
            table.parent.requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "event_incident_type.id",
                                                  type_represent,
                                                  # If limiting to just 1 level of parent
                                                  #filterby="parent",
                                                  #filter_opts=(None,),
                                                  orderby="event_incident_type.name"))
            incident_type_widget = S3HierarchyWidget(lookup = "event_incident_type",
                                                     represent = type_represent,
                                                     multiple = False,
                                                     leafonly = True,
                                                     )
            incident_type_comment = None
        else:
            hierarchy = None
            incident_type_widget = None
            incident_type_comment = None
            # Uncomment these to use an Autocomplete & not a Dropdown
            #incident_type_widget = S3AutocompleteWidget()
            #incident_type_comment = DIV(_class="tooltip",
            #                             _title="%s|%s" % (T("Event Type"),
            #                                               AUTOCOMPLETE_HELP))

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Incident Type"),
            title_display = T("Incident Type Details"),
            title_list = T("Incident Types"),
            title_update = T("Edit Incident Type"),
            title_upload = T("Import Incident Types"),
            label_list_button = T("List Incident Types"),
            label_delete_button = T("Remove Incident Type from this event"),
            msg_record_created = T("Incident Type added"),
            msg_record_modified = T("Incident Type updated"),
            msg_record_deleted = T("Incident Type removed"),
            #msg_list_empty = T("No Incident Types currently registered in this event")
            msg_list_empty = T("No Incident Types currently registered")
            )

        incident_type_id = S3ReusableField("incident_type_id", "reference %s" % tablename,
                                           label = T("Incident Type"),
                                           ondelete = "RESTRICT",
                                           represent = type_represent,
                                           requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "event_incident_type.id",
                                                                  type_represent,
                                                                  orderby="event_incident_type.name",
                                                                  sort=True)),
                                           sortby = "name",
                                           widget = incident_type_widget,
                                           comment = incident_type_comment,
                                           )
        self.configure(tablename,
                       deduplicate = S3Duplicate(),
                       hierarchy = hierarchy,
                       )

        # Pass names back to global scope (s3.*)
        return dict(event_incident_type_id = incident_type_id,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Return safe defaults in case the model has been deactivated.
        """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return dict(event_incident_type_id = lambda **attr: dummy("incident_type_id"),
                    )

# =============================================================================
class S3IncidentTypeTagModel(S3Model):
    """
        Incident Type Tags
         - Key-Value extensions
         - can be used to provide conversions to external systems, such as:
           * CAP
           * NIMS
         - can be a Triple Store for Semantic Web support
    """

    names = ("event_incident_type_tag",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Incident Type Tags
        #
        tablename = "event_incident_type_tag"
        self.define_table(tablename,
                          self.event_incident_type_id(),
                          # key is a reserved word in MySQL
                          Field("tag", label=T("Key")),
                          Field("value", label=T("Value")),
                          s3_comments(),
                          *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventAlertModel(S3Model):
    """
        Alerts for Events/Incidents

        @ToDo: Optional links to CAP broker & Messaging
               Push: like deploy_alert? via deploy_alert?
               Pull: Subscription/Notification
    """

    names = ("event_alert",
             )

    def model(self):

        T = current.T
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        tablename = "event_alert"
        define_table(tablename,
                     # PE representing its Recipients
                     self.super_link("pe_id", "pr_pentity"),
                     self.event_event_id(ondelete = "CASCADE"),
                     #self.event_incident_id(ondelete = "CASCADE"),
                     Field("name",
                           comment = T("This isn't visible to the recipients"),
                           label = T("Name"),
                           ),
                     Field("subject", length=78,    # RFC 2822
                           comment = T("The subject of the alert (optional)"),
                           label = T("Subject"),
                           requires = IS_LENGTH(78),
                           ),
                     Field("body", "text",
                           label = T("Message"),
                           requires = IS_NOT_EMPTY(),
                           represent = lambda v: v or current.messages["NONE"],
                           ),
                     # Link to the Message once sent
                     self.msg_message_id(readable = False),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Alert"),
            title_display = T("Alert Details"),
            title_list = T("Alerts"),
            title_update = T("Edit Alert Details"),
            title_upload = T("Import Recipients"),
            label_list_button = T("List Alerts"),
            label_delete_button = T("Delete Alert"),
            msg_record_created = T("Alert added"),
            msg_record_modified = T("Alert Details updated"),
            msg_record_deleted = T("Alert deleted"),
            msg_list_empty = T("No Alerts currently defined"))

        # Custom method to send alerts
        #self.set_method("event", "alert",
        #                method = "send",
        #                action = self.event_alert_send)

        # Reusable field
        represent = S3Represent(lookup=tablename)
        alert_id = S3ReusableField("alert_id", "reference %s" % tablename,
                                   label = T("Alert"),
                                   ondelete = "CASCADE",
                                   represent = represent,
                                   requires = IS_ONE_OF(db, "event_alert.id",
                                                        represent),
                                   )

        # ---------------------------------------------------------------------
        # Recipients of the Alert
        #
        tablename = "event_alert_recipient"
        define_table(tablename,
                     alert_id(),
                     self.pr_person_id(empty = False,
                                       label = T("Recipient")),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Recipient"),
            title_display = T("Recipient Details"),
            title_list = T("Recipients"),
            title_update = T("Edit Recipient Details"),
            title_upload = T("Import Recipients"),
            label_list_button = T("List Recipients"),
            label_delete_button = T("Delete Recipient"),
            msg_record_created = T("Recipient added"),
            msg_record_modified = T("Recipient Details updated"),
            msg_record_deleted = T("Recipient removed"),
            msg_list_empty = T("No Recipients currently defined"))

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventAssetModel(S3Model):
    """
        Link Assets to Incidents
    """

    names = ("event_asset",
             )

    def model(self):

        T = current.T

        status_opts = {1: T("Alerted"),
                       2: T("Standing By"),
                       3: T("Active"),
                       4: T("Deactivated"),
                       5: T("Unable to activate"),
                       }

        # ---------------------------------------------------------------------
        # Assets
        # @ToDo: Search Widget

        tablename = "event_asset"
        self.define_table(tablename,
                          # Instance table
                          self.super_link("cost_item_id", "budget_cost_item"),
                          self.event_incident_id(empty = False,
                                                 ondelete = "CASCADE"),
                          # @ToDo: Notification
                          self.asset_asset_id(empty = False,
                                              ondelete = "RESTRICT",
                                              ),
                          Field("status", "integer",
                                default = 1,
                                represent = lambda opt: \
                                       status_opts.get(opt, current.messages.UNKNOWN_OPT),
                                requires = IS_IN_SET(status_opts),
                                ),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Assign Asset"),
            title_display = T("Asset Details"),
            title_list = T("Assets"),
            title_update = T("Edit Asset"),
            label_list_button = T("List Assets"),
            label_delete_button = T("Remove Asset from this incident"),
            msg_record_created = T("Asset added"),
            msg_record_modified = T("Asset updated"),
            msg_record_deleted = T("Asset removed"),
            msg_list_empty = T("No Assets currently registered in this incident"))

        if current.deployment_settings.has_module("budget"):
            crud_form = S3SQLCustomForm("incident_id",
                                        "asset_id",
                                        "status",
                                        S3SQLInlineComponent("allocation",
                                                             label = T("Budget"),
                                                             fields = ["budget_id",
                                                                       "start_date",
                                                                       "end_date",
                                                                       "daily_cost",
                                                                       ],
                                                             ),
                                        )
        else:
            crud_form = None

        self.configure(tablename,
                       crud_form = crud_form,
                       deduplicate = S3Duplicate(primary = ("incident_id",
                                                            "asset_id",
                                                            ),
                                                 ),
                       list_fields = [#"incident_id", # Not being dropped in component view
                                      "asset_id",
                                      "status",
                                      "allocation.budget_id",
                                      "allocation.start_date",
                                      "allocation.end_date",
                                      "allocation.daily_cost",
                                      ],
                       super_entity = "budget_cost_item",
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventBookmarkModel(S3Model):
    """
        Bookmarks for Events &/or Incidents
    """

    names = ("event_bookmark",
             )

    def model(self):

        #T = current.T

        # ---------------------------------------------------------------------
        # Bookamrks: Link table between Users & Events/Incidents
        tablename = "event_bookmark"
        self.define_table(tablename,
                          #self.event_event_id(ondelete = "CASCADE"),
                          self.event_incident_id(ondelete = "CASCADE"),
                          Field("user_id", current.auth.settings.table_user),
                          *s3_meta_fields())

        #current.response.s3.crud_strings[tablename] = Storage(
        #    label_create = T("Bookmark Incident"),
        #    title_display = T("Bookmark Details"),
        #    title_list = T("Bookmarks"),
        #    title_update = T("Edit Bookmark"),
        #    label_list_button = T("List Bookmarks"),
        #    label_delete_button = T("Remove Bookmark for this Incident"),
        #    msg_record_created = T("Bookmark added"),
        #    msg_record_modified = T("Bookmark updated"),
        #    msg_record_deleted = T("Bookmark removed"),
        #    msg_list_empty = T("No Incidents currently bookmarked"))

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventCMSModel(S3Model):
    """
        Link CMS Posts to Events &/or Incidents
    """

    names = ("event_post",
             "event_post_incident_type",
             )

    def model(self):

        #T = current.T

        post_id = self.cms_post_id

        # ---------------------------------------------------------------------
        # Link table between Posts & Events/Incidents
        tablename = "event_post"
        self.define_table(tablename,
                          self.event_event_id(ondelete = "CASCADE"),
                          self.event_incident_id(ondelete = "CASCADE"),
                          post_id(empty = False,
                                  ondelete = "CASCADE",
                                  ),
                          *s3_meta_fields())

        #current.response.s3.crud_strings[tablename] = Storage(
        #    label_create = T("Tag Post"),
        #    title_display = T("Tag Details"),
        #    title_list = T("Tags"),
        #    title_update = T("Edit Tag"),
        #    label_list_button = T("List Tags"),
        #    label_delete_button = T("Remove Tag for this Event from this Post"),
        #    msg_record_created = T("Tag added"),
        #    msg_record_modified = T("Tag updated"),
        #    msg_record_deleted = T("Tag removed"),
        #    msg_list_empty = T("No Posts currently tagged to this event"))

        # ---------------------------------------------------------------------
        # Link table between Posts & Incident Types
        tablename = "event_post_incident_type"
        self.define_table(tablename,
                          post_id(empty = False,
                                  ondelete = "CASCADE",
                                  ),
                          self.event_incident_type_id(empty = False,
                                                      ondelete = "CASCADE",
                                                      ),
                          *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventDCModel(S3Model):
    """
        Link Data Collections to Events &/or Incidents
    """

    names = ("event_collection",
             "event_target",
             )

    def model(self):

        #T = current.T

        event_id = self.event_event_id
        incident_id = self.event_incident_id

        # ---------------------------------------------------------------------
        # Link table between Collections & Events/Incidents
        tablename = "event_collection"
        self.define_table(tablename,
                          event_id(ondelete = "CASCADE"),
                          incident_id(ondelete = "CASCADE"),
                          self.dc_collection_id(empty = False,
                                                ondelete = "CASCADE",
                                                ),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Link table between Targets & Events/Incidents
        tablename = "event_target"
        self.define_table(tablename,
                          event_id(ondelete = "CASCADE"),
                          incident_id(ondelete = "CASCADE"),
                          self.dc_target_id(empty = False,
                                            ondelete = "CASCADE",
                                            ),
                          *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventHRModel(S3Model):
    """
        Link Human Resources to Events/Incidents
        @ToDo: Replace with Deployment module
    """

    names = ("event_human_resource",
             )

    def model(self):

        T = current.T

        status_opts = {1: T("Alerted"),
                       2: T("Standing By"),
                       3: T("Active"),
                       4: T("Deactivated"),
                       5: T("Unable to activate"),
                       }

        # ---------------------------------------------------------------------
        # Staff/Volunteers
        # @ToDo: Use Positions, not individual HRs
        # @ToDo: Search Widget

        tablename = "event_human_resource"
        self.define_table(tablename,
                          # Instance table
                          self.super_link("cost_item_id", "budget_cost_item"),
                          #self.event_event_id(ondelete = "CASCADE",
                          #                    # Enable in template if-desired
                          #                    readable = False,
                          #                    writable = False,
                          #                    ),
                          self.event_incident_id(ondelete = "CASCADE"),
                          # @ToDo: Add Warning?
                          self.hrm_human_resource_id(empty = False,
                                                     ondelete = "RESTRICT",
                                                     ),
                          Field("status", "integer",
                                default = 1,
                                represent = lambda opt: \
                                       status_opts.get(opt, current.messages.UNKNOWN_OPT),
                                requires = IS_IN_SET(status_opts),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Assign Human Resource"),
            title_display = T("Human Resource Details"),
            title_list = T("Assigned Human Resources"),
            title_update = T("Edit Human Resource"),
            label_list_button = T("List Assigned Human Resources"),
            label_delete_button = T("Remove Human Resource from this incident"),
            msg_record_created = T("Human Resource assigned"),
            msg_record_modified = T("Human Resource Assignment updated"),
            msg_record_deleted = T("Human Resource unassigned"),
            msg_list_empty = T("No Human Resources currently assigned to this incident"))

        if current.deployment_settings.has_module("budget"):
            crud_form = S3SQLCustomForm("incident_id",
                                        "human_resource_id",
                                        "status",
                                        S3SQLInlineComponent("allocation",
                                                             label = T("Budget"),
                                                             fields = ["budget_id",
                                                                       "start_date",
                                                                       "end_date",
                                                                       "daily_cost",
                                                                       ],
                                                             ),
                                        )
        else:
            crud_form = None

        self.configure(tablename,
                       crud_form = crud_form,
                       deduplicate = S3Duplicate(primary = ("incident_id",
                                                            "human_resource_id",
                                                            ),
                                                 ),
                       list_fields = [#"incident_id", # Not being dropped in component view
                                      "human_resource_id",
                                      "status",
                                      "allocation.budget_id",
                                      "allocation.start_date",
                                      "allocation.end_date",
                                      "allocation.daily_cost",
                                      ],
                       super_entity = "budget_cost_item",
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventTeamModel(S3Model):
    """ Link teams to incidents """

    names = ("event_team_status",
             "event_team",
             )

    def model(self):

        T = current.T
        db = current.db

        define_table = self.define_table
        configure = self.configure
        crud_strings = current.response.s3.crud_strings

        if current.deployment_settings.get_event_cascade_delete_incidents():
            ondelete = "CASCADE"
        else:
            ondelete = "SET NULL"

        # ---------------------------------------------------------------------
        # Event Team Statuses
        #
        # @ToDo: May need to categorise these by Organisation
        #
        tablename = "event_team_status"
        define_table(tablename,
                     Field("name",
                           length = 64,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        CREATE_STATUS = T("Create Group Status")
        crud_strings[tablename] = Storage(
            label_create = CREATE_STATUS,
            title_display = T("Group Status Details"),
            title_list = T("Group Statuses"),
            title_update = T("Edit Group Status"),
            label_list_button = T("List Group Statuses"),
            label_delete_button = T("Delete Group Status"),
            msg_record_created = T("Group Status added"),
            msg_record_modified = T("Group Status updated"),
            msg_record_deleted = T("Group Status deleted"),
            msg_list_empty = T("No Group Statuses currently defined"),
            )

        represent = S3Represent(lookup=tablename)
        status_id = S3ReusableField("status_id", "reference %s" % tablename,
                                    label = T("Status"),
                                    ondelete = "RESTRICT",
                                    represent = represent,
                                    requires = IS_ONE_OF(db, "event_team_status.id",
                                                         represent,
                                                         orderby="event_team_status.name",
                                                         sort=True,
                                                         ),
                                    sortby = "name",
                                    )

        configure(tablename,
                  # All name duplicates are updates (=default rule):
                  deduplicate = S3Duplicate(),
                  )

        # ---------------------------------------------------------------------
        # Link table incident<=>team
        #
        tablename = "event_team"
        define_table(tablename,
                     self.event_event_id(ondelete = ondelete),
                     self.event_incident_id(empty = False,
                                            ondelete = "CASCADE",
                                            ),
                     self.pr_group_id(empty = False,
                                      ondelete = "RESTRICT",
                                      # Dropdown, not Autocomplete
                                      widget = None,
                                      ),
                     status_id(),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Assign Team"),
            title_display = T("Team Details"),
            title_list = T("Assigned Teams"),
            title_update = T("Edit Team"),
            label_list_button = T("List Assigned Teams"),
            label_delete_button = T("Remove Team from this incident"),
            msg_record_created = T("Team assigned"),
            msg_record_modified = T("Team Assignment updated"),
            msg_record_deleted = T("Team Assignment removed"),
            msg_list_empty = T("No Teams currently assigned to this incident"))

        configure(tablename,
                  # Team can be assigned to multiple incidents,
                  # so updates must match both incident_id and group_id:
                  deduplicate = S3Duplicate(primary=("incident_id",
                                                     "group_id",
                                                     )),
                  onaccept = self.event_team_onaccept,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return {}

    #--------------------------------------------------------------------------    
    @staticmethod
    def event_team_onaccept(form):
        """
            Set the event_id from the incident_id
        """

        form_vars = form.vars
        event_id = form_vars.get("event_id")
        incident_id = form_vars.get("incident_id")
        if incident_id and not event_id:
            db = current.db
            s3db = current.s3db
            itable = s3db.event_incident
            incident = db(itable.id == incident_id).select(itable.event_id,
                                                           limitby=(0, 1)
                                                           ).first()
            try:
                event_id = incident.event_id
            except:
                # Nothing we can do if Incident is invalid
                pass
            else:
                if not event_id:
                    return
                db(s3db.event_team.id == form_vars.get("id")).update(event_id = event_id)

# =============================================================================
class S3EventImpactModel(S3Model):
    """
        Link Events &/or Incidents with Impacts
    """

    names = ("event_event_impact",
             )

    def model(self):

        if not current.deployment_settings.has_module("stats"):
            current.log.warning("Event Impact Model needs Stats module enabling")
            return {}

        #T = current.T

        # ---------------------------------------------------------------------
        # Event Impact

        tablename = "event_event_impact"
        self.define_table(tablename,
                          self.event_event_id(ondelete = "CASCADE"),
                          self.event_incident_id(ondelete = "CASCADE"),
                          self.stats_impact_id(empty = False,
                                               ondelete = "CASCADE",
                                               ),
                          *s3_meta_fields())

        # Table configuration
        self.configure(tablename,
                       onaccept = self.event_impact_onaccept,
                       )

        # Not accessed directly
        #current.response.s3.crud_strings[tablename] = Storage(
        #    label_create = T("Add Impact"),
        #    title_display = T("Impact Details"),
        #    title_list = T("Impacts"),
        #    title_update = T("Edit Impact"),
        #    label_list_button = T("List Impacts"),
        #    label_delete_button = T("Delete Impact"),
        #    msg_record_created = T("Impact added"),
        #    msg_record_modified = T("Impact updated"),
        #    msg_record_deleted = T("Impact removed"),
        #    msg_list_empty = T("No Impacts currently registered in this Event"))

        # Pass names back to global scope (s3.*)
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def event_impact_onaccept(form):
        """
            Onaccept-routine for event_impact links:
                - populate event_id from incident if empty
        """

        try:
            form_vars = form.vars
            record_id = form_vars.id
        except KeyError:
            return
        if not record_id:
            return

        db = current.db
        s3db = current.s3db

        table = s3db.event_event_impact

        # Make sure we have both keys
        if any(f not in form_vars for f in ("event_id", "incident_id")):
            query = (table.id == record_id)
            record = db(query).select(table.id,
                                      table.event_id,
                                      table.incident_id,
                                      limitby=(0, 1)).first()
            if not record:
                return
        else:
            record = form_vars

        # If event_id is empty - populate it from the incident
        if not record.event_id and record.incident_id:
            itable = s3db.event_incident
            query = (itable.id == record.incident_id)
            incident = db(query).select(itable.event_id,
                                        limitby=(0, 1)).first()
            if incident:
                db(table.id == record_id).update(event_id = incident.event_id)

# =============================================================================
class S3EventIReportModel(S3Model):
    """
        Link Incident Reports to Incidents

        @ToDo: Deprecate
    """

    names = ("event_ireport",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Incident Reports
        tablename = "event_ireport"
        self.define_table(tablename,
                          self.event_incident_id(empty = False,
                                                 ondelete = "CASCADE",
                                                 ),
                          self.irs_ireport_id(empty = False,
                                              ondelete = "CASCADE",
                                              ),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Incident Report"),
            title_display = T("Incident Report Details"),
            title_list = T("Incident Reports"),
            title_update = T("Edit Incident Report"),
            label_list_button = T("List Incident Reports"),
            label_delete_button = T("Remove Incident Report from this incident"),
            msg_record_created = T("Incident Report added"),
            msg_record_modified = T("Incident Report updated"),
            msg_record_deleted = T("Incident Report removed"),
            msg_list_empty = T("No Incident Reports currently registered in this incident"))

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventMapModel(S3Model):
    """
        Link Map Configs to Incidents
    """

    names = ("event_config",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Map Config
        tablename = "event_config"
        self.define_table(tablename,
                          self.event_incident_id(empty = False,
                                                 ondelete = "CASCADE",
                                                 ),
                          self.gis_config_id(empty = False,
                                             ondelete = "CASCADE",
                                             ),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Map Profile"),
            title_display = T("Map Profile Details"),
            title_list = T("Map Profiles"),
            title_update = T("Edit Map Profile"),
            label_list_button = T("List Map Profiles"),
            label_delete_button = T("Remove Map Profile from this incident"),
            msg_record_created = T("Map Profile added"),
            msg_record_modified = T("Map Profile updated"),
            msg_record_deleted = T("Map Profile removed"),
            msg_list_empty = T("No Map Profiles currently registered in this incident"))

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventOrganisationModel(S3Model):
    """
        Link Organisations to Incidents
    """

    names = ("event_organisation",
             )

    def model(self):

        T = current.T

        status_opts = {1: T("Alerted"),
                       2: T("Standing By"),
                       3: T("Active"),
                       4: T("Deactivated"),
                       5: T("Unable to activate"),
                       }

        # ---------------------------------------------------------------------
        # Organisations linked to this Incident
        #

        tablename = "event_organisation"
        self.define_table(tablename,
                          #self.event_event_id(),
                          self.event_incident_id(empty = False,
                                                 ondelete = "CASCADE",
                                                 ),
                          self.org_organisation_id(empty = False,
                                                   ondelete = "CASCADE",
                                                   ),
                          Field("status", "integer",
                                default = 1,
                                represent = lambda opt: \
                                       status_opts.get(opt, current.messages.UNKNOWN_OPT),
                                requires = IS_IN_SET(status_opts),
                                ),
                          # @ToDo: Role?
                          s3_comments(),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Organization"),
            title_display = T("Organization Details"),
            title_list = T("Organizations"),
            title_update = T("Edit Organization"),
            label_list_button = T("List Organizations"),
            label_delete_button = T("Remove Organization from this incident"),
            msg_record_created = T("Organization added"),
            msg_record_modified = T("Organization updated"),
            msg_record_deleted = T("Organization removed"),
            msg_list_empty = T("No Organizations currently registered in this incident"))

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventProjectModel(S3Model):
    """
        Link Projects to Events
    """

    names = ("event_project",
             )

    def model(self):

        tablename = "event_project"
        self.define_table(tablename,
                          self.event_event_id(empty = False,
                                              ondelete = "CASCADE"),
                          #self.event_incident_id(ondelete = "CASCADE"),
                          self.project_project_id(#ondelete = "CASCADE", # default anyway
                                                  ),
                          *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventSiteModel(S3Model):
    """
        Link Sites (Facilities) to Incidents
    """

    names = ("event_site",
             )

    def model(self):

        T = current.T
        super_link = self.super_link

        status_opts = {1: T("Alerted"),
                       2: T("Standing By"),
                       3: T("Active"),
                       4: T("Deactivated"),
                       5: T("Unable to activate"),
                       }

        SITE_LABEL = current.deployment_settings.get_org_site_label()

        # ---------------------------------------------------------------------
        # Facilities
        # @ToDo: Filter Widgets
        tablename = "event_site"
        self.define_table(tablename,
                          # Instance table
                          super_link("cost_item_id", "budget_cost_item"),
                          self.event_incident_id(empty = False,
                                                 ondelete = "CASCADE",
                                                 ),
                          # This is a component, so needs to be a super_link
                          # - can't override field name, ondelete or requires
                          super_link("site_id", "org_site",
                                     #default = auth.user.site_id if auth.is_logged_in() else None,
                                     empty = False,
                                     label = SITE_LABEL,
                                     ondelete = "CASCADE",
                                     represent = self.org_site_represent,
                                     readable = True,
                                     writable = True,
                                     # Comment these to use a Dropdown & not an Autocomplete
                                     #widget = S3SiteAutocompleteWidget(),
                                     #comment = DIV(_class="tooltip",
                                     #              _title="%s|%s" % (SITE_LABEL,
                                     #                                messages.AUTOCOMPLETE_HELP)),
                                     ),
                          Field("status", "integer",
                                default = 1,
                                represent = lambda opt: \
                                       status_opts.get(opt, current.messages.UNKNOWN_OPT),
                                requires = IS_IN_SET(status_opts),
                                ),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Assign Facility"),
            title_display = T("Facility Details"),
            title_list = T("Facilities"),
            title_update = T("Edit Facility"),
            label_list_button = T("List Facilities"),
            label_delete_button = T("Remove Facility from this incident"),
            msg_record_created = T("Facility added"),
            msg_record_modified = T("Facility updated"),
            msg_record_deleted = T("Facility removed"),
            msg_list_empty = T("No Facilities currently registered in this incident"))

        if current.deployment_settings.has_module("budget"):
            crud_form = S3SQLCustomForm("incident_id",
                                        "site_id",
                                        "status",
                                        S3SQLInlineComponent("allocation",
                                                             label = T("Budget"),
                                                             fields = ["budget_id",
                                                                       "start_date",
                                                                       "end_date",
                                                                       "daily_cost",
                                                                       ],
                                                             ),
                                        )
        else:
            crud_form = None

        self.configure(tablename,
                       crud_form = crud_form,
                       deduplicate = S3Duplicate(primary = ("incident_id",
                                                            "site_id",
                                                            ),
                                                 ),
                       list_fields = [#"incident_id", # Not being dropped in component view
                                      "site_id",
                                      "status",
                                      "allocation.budget_id",
                                      "allocation.start_date",
                                      "allocation.end_date",
                                      "allocation.daily_cost",
                                      ],
                       super_entity = "budget_cost_item",
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventSitRepModel(S3Model):
    """
        Link SitReps to Events &/or Incidents
    """

    names = ("event_sitrep",
             "event_sitrep_id",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # SitReps
        #

        tablename = "event_sitrep"
        self.define_table(tablename,
                          # @ToDo: Validate that SitRep is linked to either an Event or an Incident
                          self.event_event_id(ondelete = "CASCADE",
                                              ),
                          self.event_incident_id(ondelete = "CASCADE",
                                                 ),
                          self.doc_sitrep_id(empty = False,
                                             ondelete = "CASCADE",
                                             ),
                          *s3_meta_fields())

        # Not used as we actuate = replace
        #current.response.s3.crud_strings[tablename] = Storage(
        #    label_create = T("Create SitRep"),
        #    title_display = T("SitRep Details"),
        #    title_list = T("SitReps"),
        #    title_update = T("Edit Task"),
        #    label_list_button = T("List SitReps"),
        #    label_delete_button = T("Remove SitRep from this incident"),
        #    msg_record_created = T("SitRep added"),
        #    msg_record_modified = T("SitRep updated"),
        #    msg_record_deleted = T("SitRep removed"),
        #    msg_list_empty = T("No SitReps currently registered in this incident"))

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("event_id",
                                                            "incident_id",
                                                            "sitrep_id",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventTagModel(S3Model):
    """
        Link Tags to Incidents
    """

    names = ("event_tag",
             )

    def model(self):

        #T = current.T

        # ---------------------------------------------------------------------
        # Tasks
        # Tasks are to be assigned to resources managed by this EOC
        # - we manage in detail
        # @ToDo: Task Templates

        tablename = "event_tag"
        self.define_table(tablename,
                          #self.event_event_id(ondelete = "CASCADE"),
                          self.event_incident_id(empty = False,
                                                 ondelete = "CASCADE",
                                                 ),
                          self.cms_tag_id(empty = False,
                                          ondelete = "CASCADE",
                                          ),
                          *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventTaskModel(S3Model):
    """
        Link Tasks to Incidents
    """

    names = ("event_task",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Tasks
        # Tasks are to be assigned to resources managed by this EOC
        # - we manage in detail
        # @ToDo: Task Templates

        tablename = "event_task"
        self.define_table(tablename,
                          #self.event_event_id(ondelete = "CASCADE"),
                          self.event_incident_id(empty = False,
                                                 ondelete = "CASCADE",
                                                 ),
                          self.project_task_id(empty = False,
                                               ondelete = "CASCADE",
                                               ),
                          *s3_meta_fields())

        # Not used as we actuate = replace
        #current.response.s3.crud_strings[tablename] = Storage(
        #    label_create = T("Create Task"),
        #    title_display = T("Task Details"),
        #    title_list = T("Tasks"),
        #    title_update = T("Edit Task"),
        #    label_list_button = T("List Tasks"),
        #    label_delete_button = T("Remove Task from this incident"),
        #    msg_record_created = T("Task added"),
        #    msg_record_modified = T("Task updated"),
        #    msg_record_deleted = T("Task removed"),
        #    msg_list_empty = T("No Tasks currently registered in this incident"))

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("incident_id",
                                                            "task_id",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventShelterModel(S3Model):
    """
        Link Shelters to Events / Incidents
    """

    names = ("event_event_shelter",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Shelters
        #   Link table for cr_shelter <> event_event
        tablename = "event_event_shelter"
        self.define_table(tablename,
                          self.event_event_id(ondelete = "CASCADE"),
                          #self.event_incident_id(ondelete = "CASCADE"),
                          self.cr_shelter_id(empty = False,
                                             ondelete = "CASCADE",
                                             ),
                          *s3_meta_fields()
                          )

        function = current.request.function
        if function == "event":
            current.response.s3.crud_strings[tablename] = Storage(
                label_create = T("Add Shelter"),
                title_display = T("Shelter Details"),
                title_list = T("Shelters"),
                title_update = T("Edit Shelter"),
                label_list_button = T("List Shelters"),
                label_delete_button = T("Remove Shelter for this Event"),
                msg_record_created = T("Shelter added"),
                msg_record_modified = T("Shelter updated"),
                msg_record_deleted = T("Shelter removed"),
                msg_list_empty = T("No Shelters currently tagged to this event")
                )

        elif function == "shelter":
            current.response.s3.crud_strings[tablename] = Storage(
                label_create = T("Associate Event"),
                title_display = T("Event Details"),
                title_list = T("Events"),
                title_update = T("Edit Event"),
                label_list_button = T("List Events"),
                label_delete_button = T("Remove Event for this Shelter"),
                msg_record_created = T("Event added"),
                msg_record_modified = T("Event updated"),
                msg_record_deleted = T("Event removed"),
                msg_list_empty = T("No Events currently tagged to this Shelter")
                )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
def event_notification_dispatcher(r, **attr):
    """
        Send a Dispatch notice from an Incident Report
      - this will be formatted as an OpenGeoSMS
    """

    if r.representation == "html" and \
        r.id and not r.component:

        T = current.T
        msg = current.msg
        s3db = current.s3db

        ctable = s3db.pr_contact
        itable = s3db.event_incident
        etable = s3db.event_event

        message = ""
        text = ""

        if r.name == "event":

            record = r.record
            id = record.id
            eventName = record.name
            startDate = record.start_date
            exercise = record.exercise
            status = record.closed

            text += "************************************************"
            text += "\n%s " % T("Automatic Message")
            text += "\n%s: %s, " % (T("Event ID"), id)
            text += " %s: %s" % (T("Event name"), eventName)
            text += "\n%s: %s " % (T("Event started"), startDate)
            text += "\n%s= %s, " % (T("Exercise"), exercise)
            text += "%s= %s" % (T("Status open"), exercise)
            text += "\n************************************************\n"

            # URL to redirect to after message sent
            url = URL(c="event", f="event", args=r.id)

        if r.name == "incident":

            record = r.record
            id = record.id
            incName = record.name
            zeroHour = record.start_date
            exercise = record.exercise
            event_id = record.event_id
            closed = record.closed

            if event_id != None:
                event = current.db(itable.id == event_id).select(etable.name,
                                                                 limitby=(0, 1)
                                                                 ).first()
                eventName = event.name
            else:
                eventName = T("Not Defined")

            text += "************************************************"
            text += "\n%s " % T("Automatic Message")
            text += "\n%s: %s,  " % (T("Incident ID"), id)
            text += " %s: %s" % (T("Incident name"), incName)
            text += "\n%s: %s " % (T("Related event"), eventName)
            text += "\n%s: %s " % (T("Incident started"), zeroHour)
            text += "\n%s %s, " % (T("Exercise?"), exercise)
            text += "%s %s" % (T("Closed?"), closed)
            text += "\n************************************************\n"

            url = URL(c="event", f="incident", args=r.id)

        # Create the form
        opts = dict(type="SMS",
                    # @ToDo: deployment_setting
                    subject = T("Deployment Request"),
                    message = message + text,
                    url = url,
                    )

        #query = (ctable.pe_id == id)
        #recipients = current.db(query).select(ctable.pe_id)

        #if not recipients:
        #    # Provide an Autocomplete the select the person to send the notice to
        #    opts["recipient_type"] = "pr_person"

        #elif len(recipients) == 1:
        #    # Send to this person
        #    opts["recipient"] = recipients.first()["pr_person"].pe_id
        #else:
        #    # Send to the Incident Commander
        #    ic = False
        #    for row in recipients:
        #        if row["irs_ireport_human_resource"].incident_commander == True:
        #            opts["recipient"] = row["pr_person"].pe_id
        #            ic = True
        #            break
        #        if not ic:
        #            # Provide an Autocomplete to select the person to send the notice to
        #            opts["recipient_type"] = "pr_person"

        output = msg.compose(**opts)

        # Maintain RHeader for consistency
        if attr.get("rheader"):
            rheader = attr["rheader"](r)
            if rheader:
                output["rheader"] = rheader

        output["title"] = T("Send Event Update")
        current.response.view = "msg/compose.html"
        return output

    else:
        raise HTTP(501, current.messages.BADMETHOD)

# =============================================================================
def event_event_list_layout(list_id, item_id, resource, rfields, record,
                            icon="event"):
    """
        Default dataList item renderer for Incidents on Profile pages

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["event_event.id"]
    item_class = "thumbnail"

    raw = record._row
    author = record["event_event.modified_by"]
    #date = record["event_event.modified_on"]

    name = record["event_event.name"]
    event_type = record["event_event.event_type_id"] or ""
    description = record["event_event.comments"]
    start_date = record["event_event.start_date"]

    location = record["event_event_location.location_id"] or ""
    #location_id = raw["event_event.location_id"]

    comments = raw["event_event.comments"]

    # Edit Bar
    # @ToDo: Consider using S3NavigationItem to hide the auth-related parts
    permit = current.auth.s3_has_permission
    table = current.db.event_event
    if permit("update", table, record_id=record_id):
        edit_btn = A(ICON("edit"),
                     _href=URL(c="event", f="event",
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id},
                               ),
                     _class="s3_modal",
                     _title=S3CRUD.crud_string(resource.tablename,
                                               "title_update"),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(ICON("delete"),
                       _class="dl-item-delete",
                       _title=S3CRUD.crud_string(resource.tablename,
                                                 "label_delete_button"),
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    item = DIV(DIV(ICON(icon),
                   SPAN(event_type, _class="type-title"),
                   SPAN(location, _class="location-title"),
                   SPAN(start_date, _class="date-title"),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(DIV(A(name,
                          _href=URL(c="event", f="event",
                                    args=[record_id, "profile"])),
                        _class="card-title"),
                   DIV(DIV((description or ""),
                           DIV(author or "",
                               _class="card-person",
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
def event_incident_list_layout(list_id, item_id, resource, rfields, record,
                               icon="incident"):
    """
        Default dataList item renderer for Incidents on Profile pages

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    raw = record._row
    record_id = raw["event_incident.id"]
    item_class = "thumbnail"

    author = record["event_incident.modified_by"]
    #date = record["event_incident.modified_on"]

    name = record["event_incident.name"]
    description = record["event_incident.comments"]
    start_date = record["event_incident.start_date"]

    organisation = record["event_incident.organisation_id"]
    organisation_id = raw["event_incident.organisation_id"]
    location = record["event_incident.location_id"]
    location_id = raw["event_incident.location_id"]

    comments = raw["event_incident.comments"]

    org_url = URL(c="org", f="organisation", args=[organisation_id, "profile"])
    org_logo = raw["org_organisation.logo"]
    if org_logo:
        org_logo = A(IMG(_src=URL(c="default", f="download", args=[org_logo]),
                         _class="media-object",
                         ),
                     _href=org_url,
                     _class="pull-left",
                     )
    else:
        # @ToDo: use a dummy logo image
        org_logo = A(IMG(_class="media-object"),
                     _href=org_url,
                     _class="pull-left",
                     )

    # Edit Bar
    # @ToDo: Consider using S3NavigationItem to hide the auth-related parts
    permit = current.auth.s3_has_permission
    table = current.db.event_incident
    if permit("update", table, record_id=record_id):
        edit_btn = A(ICON("edit"),
                     _href=URL(c="event", f="incident",
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id},
                               ),
                     _class="s3_modal",
                     _title=S3CRUD.crud_string(resource.tablename,
                                               "title_update"),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(ICON("delete"),
                       _class="dl-item-delete",
                       _title=S3CRUD.crud_string(resource.tablename,
                                                 "label_delete_button"),
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    item = DIV(DIV(ICON(icon),
                   SPAN(location, _class="location-title"),
                   SPAN(start_date, _class="date-title"),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(DIV(A(name,
                          _href=URL(c="event", f="incident",
                                    args=[record_id, "profile"])),
                        _class="card-title"),
                   DIV(DIV((description or ""),
                           DIV(author or "",
                               " - ",
                               A(organisation,
                                 _href=org_url,
                                 _class="card-organisation",
                                 ),
                               _class="card-person",
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
def event_resource_list_layout(list_id, item_id, resource, rfields, record):
    """
        Default dataList item renderer for Resources on Profile pages

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    raw = record._row
    record_id = raw["event_resource.id"]
    item_class = "thumbnail"

    author = record["event_resource.modified_by"]
    date = record["event_resource.date"]
    quantity = record["event_resource.value"]
    resource_type = record["event_resource.parameter_id"]
    comments = raw["event_resource.comments"]
    organisation = record["event_resource.organisation_id"]
    organisation_id = raw["event_resource.organisation_id"]
    location = record["event_resource.location_id"]
    location_id = raw["event_resource.location_id"]
    location_url = URL(c="gis", f="location",
                       args=[location_id, "profile"])

    org_url = URL(c="event", f="organisation", args=[organisation_id, "profile"])
    logo = raw["org_organisation.logo"]
    if logo:
        logo = A(IMG(_src=URL(c="default", f="download", args=[logo]),
                     _class="media-object",
                     ),
                 _href=org_url,
                 _class="pull-left",
                 )
    else:
        # @ToDo: use a dummy logo image
        logo = A(IMG(_class="media-object"),
                 _href=org_url,
                 _class="pull-left",
                 )

    # Edit Bar
    permit = current.auth.s3_has_permission
    table = current.db.event_resource
    if permit("update", table, record_id=record_id):
        vars = {"refresh": list_id,
                "record": record_id,
                }
        f = current.request.function
        if f == "organisation" and organisation_id:
            vars["(organisation)"] = organisation_id
        elif f == "location" and location_id:
            vars["(location)"] = location_id
        edit_btn = A(ICON("edit"),
                     _href=URL(c="event", f="resource",
                               args=[record_id, "update.popup"],
                               vars=vars),
                     _class="s3_modal",
                     _title=S3CRUD.crud_string(resource.tablename,
                                               "title_update"),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(ICON("delete"),
                       _class="dl-item-delete",
                       _title=S3CRUD.crud_string(resource.tablename,
                                                 "label_delete_button"),
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    avatar = logo

    item = DIV(DIV(SPAN(A(location,
                          _href=location_url,
                          ),
                        _class="location-title",
                        ),
                   SPAN(date,
                        _class="date-title",
                        ),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(#avatar,
                   DIV("%s %s" % (quantity, current.T(resource_type)), _class="card-title"),
                   DIV(DIV(comments,
                           DIV(author or "" ,
                               " - ",
                               A(organisation,
                                 _href=org_url,
                                 _class="card-organisation",
                                 ),
                               _class="card-person",
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
def event_rheader(r):
    """ Resource headers for component views """

    rheader = None

    if r.representation == "html":

        T = current.T
        settings = current.deployment_settings

        if r.name == "event":
            # Event Controller
            if settings.get_event_label(): # == "Disaster"
                label = T("Disaster Details")
            else:
                label = T("Event Details")
            tabs = [(label, None),
                    ]
            if settings.has_module("doc"):
                tabs += [(T("Documents"), "document"),
                         (T("Photos"), "image"),
                         ]
            if settings.get_event_impact_tab():
                tabs.append((T("Impact"), "impact"))
            if settings.get_event_target_tab():
                tabs.append((T("Targets"), "target"))
            if settings.get_event_collection_tab():
                tabs.append((T("Assessments"), "collection"))
            if settings.get_project_event_projects():
                tabs.append((T("Projects"), "project"))
            if settings.get_project_event_activities():
                tabs.append((T("Activities"), "activity"))
            if settings.has_module("cr"):
                tabs.append((T("Shelters"), "event_shelter"))
            #if settings.has_module("req"):
            #    tabs.append((T("Requests"), "req"))
            if settings.get_event_dispatch_tab():
                tabs.append((T("Send Notification"), "dispatch"))

            rheader_tabs = s3_rheader_tabs(r, tabs)

            event = r.record
            if event:
                if event.exercise:
                    exercise = TH(T("EXERCISE"))
                else:
                    exercise = TH()
                if event.closed:
                    closed = TH(T("CLOSED"))
                else:
                    closed = TH()
                table = r.table
                rheader = DIV(TABLE(TR(exercise),
                                    TR(TH("%s: " % table.name.label),
                                       event.name),
                                    TR(TH("%s: " % table.comments.label),
                                       event.comments),
                                    TR(TH("%s: " % table.start_date.label),
                                       table.start_date.represent(event.start_date)),
                                    TR(closed),
                                    ), rheader_tabs)

        elif r.name == "incident":
            # Incident Controller
            tabs = [(T("Incident Details"), None)]
            append = tabs.append

            # Impact tab
            if settings.get_incident_impact_tab():
                append((T("Impact"), "impact"))

            # Tasks tab
            if settings.has_module("project"):
                append((T("Tasks"), "task"))

            # Staff tab
            if settings.has_module("hrm"):
                STAFF = settings.get_hrm_staff_label()
                append((STAFF, "human_resource"))
                if current.auth.s3_has_permission("create", "event_human_resource"):
                     append((T("Assign %(staff)s") % dict(staff=STAFF), "assign"))

            # Teams tab:
            teams_tab = settings.get_incident_teams_tab()
            if teams_tab:
                tab_label = T("Teams") if teams_tab is True else T(teams_tab)
                append((tab_label, "group"))

            # Asset tab
            if settings.has_module("asset"):
                append((T("Assets"), "asset"))

            # Other tabs
            tabs.extend(((T("Facilities"), "site"), # Inc Shelters
                         (T("Organizations"), "organisation"),
                         (T("SitReps"), "sitrep"),
                         (T("Map Profile"), "config"),
                         ))

            # Messaging tab
            if settings.get_incident_dispatch_tab():
                append((T("Send Notification"), "dispatch"))

            rheader_tabs = s3_rheader_tabs(r, tabs)

            record = r.record
            if record:
                if record.exercise:
                    exercise = TH(T("EXERCISE"))
                else:
                    exercise = TH()
                if record.closed:
                    closed = TH(T("CLOSED"))
                else:
                    closed = TH()
                table = r.table
                rheader = DIV(TABLE(TR(exercise),
                                    TR(TH("%s: " % table.name.label),
                                       record.name),
                                    TR(TH("%s: " % table.comments.label),
                                       record.comments),
                                    TR(TH("%s: " % table.date.label),
                                       table.date.represent(record.date)),
                                    TR(closed),
                                    ), rheader_tabs)

    return rheader

# END =========================================================================
