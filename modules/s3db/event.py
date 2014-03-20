# -*- coding: utf-8 -*-

""" Sahana Eden Event Model

    @copyright: 2009-2013 (c) Sahana Software Foundation
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

__all__ = ["S3EventModel",
           "S3IncidentModel",
           "S3IncidentReportModel",
           "S3IncidentGroupModel",
           "S3IncidentTypeModel",
           "S3IncidentTypeTagModel",
           "S3EventActivityModel",
           "S3EventAssetModel",
           "S3EventCMSModel",
           "S3EventHRModel",
           "S3EventIReportModel",
           "S3EventMapModel",
           #"S3EventRequestModel",
           "S3EventSiteModel",
           "S3EventTaskModel",
           "S3EventShelterModel",
           ]

from gluon import *
from gluon.storage import Storage

from ..s3 import *
from s3layouts import S3AddResourceLink

# =============================================================================
class S3EventModel(S3Model):
    """
        Event Model

        http://eden.sahanafoundation.org/wiki/BluePrintScenario

        Events are a high-level term, such as a 'Disaster'

        Link tables are in separate classes to increase performance & allow
        the system to be more modular
    """

    names = ["event_event_type",
             "event_type_id",
             "event_event",
             "event_event_id",
             "event_event_location",
             "event_event_tag",
             ]

    def model(self):

        T = current.T
        db = current.db

        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        NONE = current.messages["NONE"]

        # ---------------------------------------------------------------------
        # Event Types / Disaster Types
        #
        tablename = "event_event_type"
        define_table(tablename,
                     Field("name", notnull=True,
                           length=64,
                           label=T("Name")),
                     s3_comments(),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Event Type"),
            title_display = T("Event Type Details"),
            title_list = T("Event Types"),
            title_update = T("Edit Event Type"),
            title_upload = T("Import Event Types"),
            label_list_button = T("List Event Types"),
            label_delete_button = T("Remove Event Type from this event"),
            msg_record_created = T("Event Type added"),
            msg_record_modified = T("Event Type updated"),
            msg_record_deleted = T("Event Type removed"),
            msg_list_empty = T("No Event Types currently registered")
            )

        represent = S3Represent(lookup=tablename)
        event_type_id = S3ReusableField("event_type_id", "reference %s" % tablename,
                                        sortby="name",
                                        requires = IS_NULL_OR(
                                                    IS_ONE_OF(db, "event_event_type.id",
                                                              represent,
                                                              orderby="event_event_type.name",
                                                              sort=True)),
                                        represent = represent,
                                        label = T("Event Type"),
                                        ondelete = "RESTRICT",
                                        # Uncomment these to use an Autocomplete & not a Dropdown
                                        #widget = S3AutocompleteWidget()
                                        #comment = DIV(_class="tooltip",
                                        #              _title="%s|%s" % (T("Event Type"),
                                        #                                T("Enter some characters to bring up a list of possible matches")))
                                        )
        configure(tablename,
                  deduplicate=self.event_type_duplicate
                  )

        # ---------------------------------------------------------------------
        # Events / Disasters
        #
        #   Events can be a way of grouping related Incidents or used standalone
        #
        # ---------------------------------------------------------------------
        tablename = "event_event"
        define_table(tablename,
                     Field("name", notnull=True, # Name could be a code
                           length=64,    # Mayon compatiblity
                           label=T("Name")),
                     event_type_id(),
                     Field("exercise", "boolean",
                           represent = lambda opt: "√" if opt else NONE,
                           #comment = DIV(_class="tooltip",
                           #              _title="%s|%s" % (T("Exercise"),
                                                           # Should!
                           #                                T("Exercises mean all screens have a watermark & all notifications have a prefix."))),
                           label=T("Exercise?")),
                     s3_datetime(name="zero_hour",
                                 label = T("Zero Hour"),
                                 default = "now",
                                 comment = DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Zero Hour"),
                                                                 T("The time at which the Event started."))),
                                 ),
                     Field("closed", "boolean",
                           default = False,
                           represent = s3_yes_no_represent,
                           label=T("Closed")),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
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
                                   requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "event_event.id",
                                                          represent,
                                                          filterby="closed",
                                                          filter_opts=[False],
                                                          orderby="event_event.name",
                                                          sort=True)),
                                   represent = represent,
                                   label = T("Event"),
                                   ondelete = "CASCADE",
                                   # Uncomment these to use an Autocomplete & not a Dropdown
                                   #widget = S3AutocompleteWidget()
                                   #comment = DIV(_class="tooltip",
                                   #              _title="%s|%s" % (T("Event"),
                                   #                                T("Enter some characters to bring up a list of possible matches")))
                                   )

        configure(tablename,
                  orderby="event_event.zero_hour desc",
                  list_orderby="event_event.zero_hour desc",
                  update_onaccept=self.event_update_onaccept,
                  deduplicate=self.event_duplicate,
                  context = {"location": "event_location.location_id",
                             },
                  list_fields = ["id",
                                 "name",
                                 "event_type_id$name",
                                 (T("Location"), "location.name"),
                                 "zero_hour",
                                 "exercise",
                                 "closed",
                                 "comments",
                                 ]
                  )

        # Components
        add_components(tablename,
                       event_incident="event_id",
                       gis_location={"link": "event_event_location",
                                     "joinby": "event_id",
                                     "key": "location_id",
                                     "actuate": "hide",
                                    },
                       event_event_location="event_id",
                       req_req="event_id",
                       event_event_tag={"name": "tag",
                                        "joinby": "event_id",
                                        },
                       event_event_shelter="event_id"
                       )

        # ---------------------------------------------------------------------
        # Event Locations (link table)
        #
        tablename = "event_event_location"
        define_table(tablename,
                     event_id(),
                     self.gis_location_id(
                     widget = S3LocationAutocompleteWidget(),
                     requires = IS_LOCATION(),
                     represent = self.gis_LocationRepresent(sep=", "),
                     comment = S3AddResourceLink(c="gis",
                                                 f="location",
                                                 label = T("Create Location"),
                                                 title=T("Location"),
                                                 tooltip=T("Enter some characters to bring up a list of possible matches")),
                     ),
                     *s3_meta_fields())

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
                  deduplicate=self.event_event_tag_deduplicate)

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

        return dict(
                event_event_id = S3ReusableField("event_id", "integer",
                                                 readable=False,
                                                 writable=False),
                event_type_id = S3ReusableField("event_id", "integer",
                                                readable=False,
                                                writable=False),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def event_update_onaccept(form):
        """
            When an Event is updated, check for closure
        """

        vars = form.vars
        if vars.closed:
            event = vars.id
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
            ltable = current.s3db.event_event_post
            table = db.cms_post
            rows = db(ltable.event_id == event).select(ltable.post_id)
            for row in rows:
                db(table.id == row.post_id).update(expired=True)

    # -------------------------------------------------------------------------
    @staticmethod
    def event_duplicate(item):
        """
            Deduplication of Events
        """

        if item.tablename != "event_event":
            return

        data = item.data
        name = data.get("name", None)

        table = item.table
        query = (table.name == name)
        _duplicate = current.db(query).select(table.id,
                                              limitby=(0, 1)).first()
        if _duplicate:
            item.id = _duplicate.id
            item.data.id = _duplicate.id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def event_type_duplicate(item):
        """
            Deduplication of Event Types
        """

        if item.tablename != "event_event_type":
            return

        data = item.data
        name = data.get("name", None)

        if not name:
            return

        table = item.table
        query = (table.name == name)
        _duplicate = current.db(query).select(table.id,
                                              limitby=(0, 1)).first()
        if _duplicate:
            item.id = _duplicate.id
            item.data.id = _duplicate.id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def event_event_tag_deduplicate(item):
        """
           Deduplication of Event Tags
        """

        if item.tablename != "event_event_tag":
            return

        data = item.data
        tag = data.get("tag", None)
        event = data.get("event_id", None)

        if not tag or not event:
            return

        table = item.table
        query = (table.tag.lower() == tag.lower()) & \
                (table.event_id == event)

        _duplicate = current.db(query).select(table.id,
                                              limitby=(0, 1)).first()
        if _duplicate:
            item.id = _duplicate.id
            item.method = item.METHOD.UPDATE

# =============================================================================
class S3IncidentModel(S3Model):
    """
        Incidents
         - the primary unit at which things are managed:
            Scenarios are designed
            Resources are assigned
            Situation Reports are made
    """

    names = ["event_incident",
             "event_incident_id",
             ]

    def model(self):

        T = current.T
        db = current.db
        settings = current.deployment_settings
        
        add_components = self.add_components

        # ---------------------------------------------------------------------
        # Incidents
        #
        #  Incidents are the unit at which responses are managed.
        #  They can be Exercises or real Incidents.
        #  They can be instantiated from Scenario Templates.
        #
        tablename = "event_incident"
        self.define_table(tablename,
                          self.event_event_id(),
                          self.event_incident_type_id(),
                          self.scenario_scenario_id(),
                          Field("name", notnull=True, # Name could be a code
                                length=64,
                                label=T("Name")),
                          Field("exercise", "boolean",
                                represent = lambda opt: "√" if opt else None,
                                #comment = DIV(_class="tooltip",
                                #              _title="%s|%s" % (T("Exercise"),
                                                                 # Should!
                                #                                T("Exercises mean all screens have a watermark & all notifications have a prefix."))),
                                label=T("Exercise?")),
                          s3_datetime(name="zero_hour",
                                      label = T("Zero Hour"),
                                      default = "now",
                                      comment = DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Zero Hour"),
                                                                      T("The time at which the Incident started."))),
                                      ),
                          Field("closed", "boolean",
                                default = False,
                                represent = s3_yes_no_represent,
                                label=T("Closed")),
                          s3_comments(),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Incident"),
            title_display = T("Incident Details"),
            title_list = T("Incidents"),
            title_update = T("Edit Incident"),
            label_list_button = T("List Incidents"),
            label_delete_button = T("Remove Incident from this event"),
            msg_record_created = T("Incident added"),
            msg_record_modified = T("Incident updated"),
            msg_record_deleted = T("Incident removed"),
            msg_list_empty = T("No Incidents currently registered in this event"))

        represent = S3Represent(lookup=tablename)
        incident_id = S3ReusableField("incident_id", "reference %s" % tablename,
                                      sortby="name",
                                      requires = IS_NULL_OR(
                                                    IS_ONE_OF(db, "event_incident.id",
                                                              represent,
                                                              filterby="closed",
                                                              filter_opts=[False],
                                                              orderby="event_incident.name",
                                                              sort=True)),
                                      represent = represent,
                                      label = T("Incident"),
                                      ondelete = "CASCADE",
                                      # Uncomment these to use an Autocomplete & not a Dropdown
                                      #widget = S3AutocompleteWidget()
                                      #comment = DIV(_class="tooltip",
                                      #              _title="%s|%s" % (T("Incident"),
                                      #                                T("Enter some characters to bring up a list of possible matches")))
                                      )

        if settings.has_module("project"):
            create_next_url = URL(args=["[id]", "task"])
        elif settings.has_module("hrm"):
            create_next_url = URL(args=["[id]", "human_resource"])
        elif settings.has_module("asset"):
            create_next_url = URL(args=["[id]", "asset"])
        else:
            create_next_url = URL(args=["[id]", "site"])

        self.configure(tablename,
                       create_next = create_next_url,
                       create_onaccept=self.incident_create_onaccept,
                       deduplicate=self.incident_duplicate,
                       list_fields = ["id",
                                      "name",
                                      "incident_type_id",
                                      "exercise",
                                      "closed",
                                      "comments",
                                      ])

        # Components
        add_components(tablename,
                       project_task={"link": "event_task",
                                     "joinby": "incident_id",
                                     "key": "task_id",
                                     # @ToDo: Widget to handle embedded LocationSelector
                                     #"actuate": "embed",
                                     "actuate": "link",
                                     "autocomplete": "name",
                                     "autodelete": False,
                                    },
                       event_human_resource="incident_id",
                       hrm_human_resource={"link": "event_human_resource",
                                           "joinby": "incident_id",
                                           "key": "human_resource_id",
                                           # @ToDo: Widget to handle embedded AddPersonWidget
                                           #"actuate": "embed",
                                           "actuate": "link",
                                           "autocomplete": "name",
                                           "autodelete": False,
                                          },
                       asset_asset={"link": "event_asset",
                                    "joinby": "incident_id",
                                    "key": "asset_id",
                                    "actuate": "embed",
                                    "autocomplete": "name",
                                    "autodelete": False,
                                    },
                       event_site="incident_id",
                       gis_config={"link": "event_config",
                                   "joinby": "incident_id",
                                   "multiple": False,
                                   "key": "config_id",
                                   "actuate": "replace",
                                   "autocomplete": "name",
                                   "autodelete": True,
                                  },
                      )

        # Pass names back to global scope (s3.*)
        return dict(event_incident_id = incident_id,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Return safe defaults in case the model has been deactivated.
        """

        return dict(
                event_incident_id = S3ReusableField("incident_id", "integer",
                                                    readable=False,
                                                    writable=False),

                )

    # ---------------------------------------------------------------------
    @staticmethod
    def incident_create_onaccept(form):
        """
            When an Incident is instantiated, populate defaults
        """

        vars = form.vars
        incident = vars.get("incident_id", None)
        event = vars.get("event_id", None)
        if event:
            # Set the Event in the session
            current.session.s3.event = event
        s3db = current.s3db
        db = current.db
        ctable = s3db.gis_config
        mapconfig = None
        scenario = vars.get("scenario_id", None)
        if scenario:
            # We have been instantiated from a Scenario, so
            # copy all resources from the Scenario to the Incident

            # Read the source resource tables
            table = db.scenario_scenario
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
            mapconfig["name"] = vars.name
            config = ctable.insert(**mapconfig.as_dict())
            mtable = db.event_config
            mtable.insert(incident_id=incident,
                          config_id=config)
            # Activate this config
            current.gis.set_config(config)
            # @ToDo: Add to GIS Menu? Separate Menu?

        else:
            # We have been created without a Scenario or from a Scenario without a Map Config
            # Create a new Map Config
            config = ctable.insert(name = vars.name)
            mtable = db.event_config
            mtable.insert(incident_id=incident,
                          config_id=config)
            # Activate this config
            current.gis.set_config(config)
            # Viewport can be saved from the Map's toolbar
            # @ToDo: Add to GIS Menu? Separate Menu?

    # -------------------------------------------------------------------------
    @staticmethod
    def incident_duplicate(item):
        """
            Deduplication of Incidents
        """

        if item.tablename != "event_incident":
            return

        data = item.data
        name = data.get("name", None)
        event_id = data.get("event_id", None)

        table = item.table
        query = (table.name == name)
        if event_id:
            query = query & (table.event_id == event_id)

        _duplicate = current.db(query).select(table.id,
                                              limitby=(0, 1)).first()
        if _duplicate:
            item.id = _duplicate.id
            item.data.id = _duplicate.id
            item.method = item.METHOD.UPDATE

# =============================================================================
class S3IncidentReportModel(S3Model):
    """
        Incident Reports
         - reports about incidents

        @ToDo: Deprecate IRS module by porting functionality here
    """

    names = ["event_incident_report"]

    def model(self):

        T = current.T

        add_components = self.add_components

        # ---------------------------------------------------------------------
        # Incident Reports
        #
        tablename = "event_incident_report"
        self.define_table(tablename,
                          self.super_link("doc_id", "doc_entity"),
                          # @ToDo: Use link tables?
                          #self.event_event_id(),
                          #self.event_incident_id(),
                          s3_datetime(),
                          Field("name", notnull=True,
                                label=T("Name")),
                          self.event_incident_type_id(),
                          self.gis_location_id(),
                          self.pr_person_id(label=T("Reported By")),
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

        filter_widgets = [S3OptionsFilter("incident_type_id",
                                          label=T("Type"),
                                          represent="%(name)s",
                                          widget="multiselect",
                                          ),
                          ]

        self.configure(tablename,
                       super_entity="doc_entity",
                       filter_widgets = filter_widgets,
                       )

        # Components
        add_components(tablename,
                       # Coalitions
                       org_group={"link": "event_incident_report_group",
                                  "joinby": "incident_report_id",
                                  "key": "group_id",
                                  "actuate": "hide",
                                 },
                       # Format for InlineComponent/filter_widget
                       event_incident_report_group="incident_report_id",
                      )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3IncidentGroupModel(S3Model):
    """
        Links between Incident Reports & Organisation Groups
    """

    names = ["event_incident_report_group"]

    def model(self):

        represent = S3Represent(lookup="event_incident_report")

        # ---------------------------------------------------------------------
        # Incident Reports <> Coalitions link table
        #
        tablename = "event_incident_report_group"
        self.define_table(tablename,
                          Field("incident_report_id", self.event_incident_report,
                                requires = IS_ONE_OF(current.db, "event_incident_report.id",
                                                     represent,
                                                     sort=True,
                                                     ),
                                represent = represent,
                                ),
                          self.org_group_id(empty=False),
                          *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return dict()

# =============================================================================
class S3IncidentTypeModel(S3Model):
    """
        Incident Types
    """

    names = ["event_incident_type",
             "event_incident_type_id",
             ]

    def model(self):

        T = current.T
        db = current.db

        # ---------------------------------------------------------------------
        # Incident Types
        #
        tablename = "event_incident_type"
        self.define_table(tablename,
                          Field("name", notnull=True,
                                length=64,
                                label=T("Name"),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

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

        represent = S3Represent(lookup=tablename)
        incident_type_id = S3ReusableField("incident_type_id", "reference %s" % tablename,
                                           sortby="name",
                                           requires = IS_NULL_OR(
                                                        IS_ONE_OF(db, "event_incident_type.id",
                                                                  represent,
                                                                  orderby="event_incident_type.name",
                                                                  sort=True)),
                                           represent = represent,
                                           label = T("Incident Type"),
                                           ondelete = "RESTRICT",
                                           # Uncomment these to use an Autocomplete & not a Dropdown
                                           #widget = S3AutocompleteWidget()
                                           #comment = DIV(_class="tooltip",
                                           #              _title="%s|%s" % (T("Incident Type"),
                                           #                                T("Enter some characters to bring up a list of possible matches")))
                                           )
        self.configure(tablename,
                       deduplicate=self.incident_type_duplicate
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

        return dict(
            event_incident_type_id = S3ReusableField("incident_type_id", "integer",
                                                     readable=False,
                                                     writable=False),
        )

    # ---------------------------------------------------------------------
    @staticmethod
    def incident_type_duplicate(item):
        """
            Deduplication of Incident Types
        """

        if item.tablename != "event_incident_type":
            return

        data = item.data
        name = data.get("name", None)

        if not name:
            return

        table = item.table
        query = (table.name.lower() == name.lower())
        _duplicate = current.db(query).select(table.id,
                                              limitby=(0, 1)).first()
        if _duplicate:
            item.id = _duplicate.id
            item.data.id = _duplicate.id
            item.method = item.METHOD.UPDATE

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

    names = ["event_incident_type_tag"]

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
        return dict()

# =============================================================================
class S3EventActivityModel(S3Model):
    """
        Link Activities to Events
    """

    names = ["event_activity"]

    def model(self):

        if not current.deployment_settings.has_module("project"):
            return None

        tablename = "event_activity"
        self.define_table(tablename,
                          self.event_event_id(empty=False),
                          self.project_activity_id(empty=False),
                          *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return dict()

# =============================================================================
class S3EventAssetModel(S3Model):
    """
        Link Assets to Incidents
    """

    names = ["event_asset"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Assets
        # @ToDo: Search Widget

        tablename = "event_asset"
        self.define_table(tablename,
                          self.event_incident_id(),
                          self.asset_asset_id(),
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

        # Pass names back to global scope (s3.*)
        return dict()

# =============================================================================
class S3EventCMSModel(S3Model):
    """
        Link CMS Posts to Events
    """

    names = ["event_event_post"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Posts
        #   Link table for cms_post <> event_event
        # @ToDo: Search Widget

        tablename = "event_event_post"
        self.define_table(tablename,
                          self.event_event_id(),
                          self.cms_post_id(),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Tag Post"),
            title_display = T("Tag Details"),
            title_list = T("Tags"),
            title_update = T("Edit Tag"),
            label_list_button = T("List Tags"),
            label_delete_button = T("Remove Tag for this Event from this Post"),
            msg_record_created = T("Tag added"),
            msg_record_modified = T("Tag updated"),
            msg_record_deleted = T("Tag removed"),
            msg_list_empty = T("No Posts currently tagged to this event"))

        # Pass names back to global scope (s3.*)
        return dict()

# =============================================================================
class S3EventHRModel(S3Model):
    """
        Link Human Resources to Incidents
        @ToDo: Replace with Deployment module
    """

    names = ["event_human_resource"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Staff/Volunteers
        # @ToDo: Use Positions, not individual HRs
        # @ToDo: Search Widget

        tablename = "event_human_resource"
        self.define_table(tablename,
                          self.event_incident_id(),
                          self.hrm_human_resource_id(),
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

        # Pass names back to global scope (s3.*)
        return dict()

# =============================================================================
class S3EventIReportModel(S3Model):
    """
        Link Incident Reports to Incidents
    """

    names = ["event_ireport"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Incident Reports
        tablename = "event_ireport"
        self.define_table(tablename,
                          self.event_incident_id(),
                          self.irs_ireport_id(),
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
        return dict()

# =============================================================================
class S3EventMapModel(S3Model):
    """
        Link Map Configs to Incidents
    """

    names = ["event_config"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Map Config
        tablename = "event_config"
        self.define_table(tablename,
                          self.event_incident_id(),
                          self.gis_config_id(),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Map Configuration"),
            title_display = T("Map Configuration Details"),
            title_list = T("Map Configurations"),
            title_update = T("Edit Map Configuration"),
            label_list_button = T("List Map Configurations"),
            label_delete_button = T("Remove Map Configuration from this incident"),
            msg_record_created = T("Map Configuration added"),
            msg_record_modified = T("Map Configuration updated"),
            msg_record_deleted = T("Map Configuration removed"),
            msg_list_empty = T("No Map Configurations currently registered in this incident"))

        # Pass names back to global scope (s3.*)
        return dict()

# =============================================================================
class S3EventSiteModel(S3Model):
    """
        Link Sites (Facilities) to Incidents
    """

    names = ["event_site"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Facilities
        # @ToDo: Search Widget
        tablename = "event_site"
        self.define_table(tablename,
                          self.event_incident_id(),
                          self.org_site_id,
                          *s3_meta_fields())

        # @todo: make lazy_table
        table = current.db[tablename]
        table.site_id.readable = table.site_id.writable = True

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

        # Pass names back to global scope (s3.*)
        return dict()

# =============================================================================
class S3EventTaskModel(S3Model):
    """
        Link Tasks to Incidents
    """

    names = ["event_task"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Tasks
        # Tasks are to be assigned to resources managed by this EOC
        # - we manage in detail
        # @ToDo: Task Templates
        # @ToDo: Search Widget

        tablename = "event_task"
        self.define_table(tablename,
                          self.event_incident_id(),
                          self.project_task_id(),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Task"),
            title_display = T("Task Details"),
            title_list = T("Tasks"),
            title_update = T("Edit Task"),
            label_list_button = T("List Tasks"),
            label_delete_button = T("Remove Task from this incident"),
            msg_record_created = T("Task added"),
            msg_record_modified = T("Task updated"),
            msg_record_deleted = T("Task removed"),
            msg_list_empty = T("No Tasks currently registered in this incident"))

        # Pass names back to global scope (s3.*)
        return dict()

# =============================================================================
class S3EventShelterModel(S3Model):
    """
        Link Shelters to Events
    """

    names = ["event_event_shelter"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Shelters
        #   Link table for cr_shelter <> event_event
        tablename = "event_event_shelter"
        self.define_table(tablename,
                          self.event_event_id(),
                          self.cr_shelter_id(),
                          *s3_meta_fields()
                          )

        if current.request.function == "event":
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

        elif current.request.function == "shelter":
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
        return dict()

# END =========================================================================
