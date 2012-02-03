# -*- coding: utf-8 -*-

""" Sahana Eden Event Model

    @copyright: 2009-2012 (c) Sahana Software Foundation
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
           "S3EventAssetModel",
           "S3EventHRModel",
           "S3EventIReportModel",
           "S3EventMapModel",
           #"S3EventRequestModel",
           "S3EventSiteModel",
           "S3EventTaskModel",
        ]

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3EventModel(S3Model):
    """
        Event Model

        http://eden.sahanafoundation.org/wiki/BluePrintScenario

        @ToDo: Event should be a higher-level term
               Incident is the primary unit at which things are managed:
                    Scenarios are designed
                    Resources are assigned
                    Situation Reports are made

        Link tables are in separate classes to increase performance & allow
        the system to be more modular
    """

    names = ["event_event",
             "event_event_id",
             "event_incident_id",
            ]

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3
        settings = current.deployment_settings

        scenario_id = self.scenario_scenario_id

        s3_datetime_format = settings.get_L10n_datetime_format()
        s3_utc_represent = lambda dt: S3DateTime.datetime_represent(dt, utc=True)

        # ---------------------------------------------------------------------
        # Events
        #
        #   Events can be Exercises or real Incidents.
        #   They can be instances of Scenarios (although this should move to the Incident sub-level)
        #
        #   Events will be just a way of grouping many smaller Incidents
        #
        # ---------------------------------------------------------------------
        tablename = "event_event"
        table = self.define_table(tablename,
                                  scenario_id(),
                                  Field("name", notnull=True, # Name could be a code
                                        length=64,    # Mayon compatiblity
                                        label=T("Name")),
                                  #Field("code",       # e.g. to link to WebEOC
                                  #      length=64,    # Mayon compatiblity
                                  #      label=T("Code")),
                                  Field("exercise", "boolean",
                                        represent = lambda opt: "√" if opt else current.messages.NONE,
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Exercise"),
                                                                        # Should!
                                                                        T("Exercises mean all screens have a watermark & all notifications have a prefix."))),
                                        label=T("Exercise?")),
                                  Field("zero_hour", "datetime",
                                        default = current.request.utcnow,
                                        requires = IS_DATETIME(format=s3_datetime_format),
                                        represent = s3_utc_represent,
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Zero Hour"),
                                                                        T("The time at which the Event started."))),
                                        label=T("Zero Hour")),
                                  Field("closed", "boolean",
                                        default = False,
                                        label=T("Closed")),
                                  s3.comments(),
                                  *s3.meta_fields())

        # CRUD strings
        ADD_EVENT = T("New Event")
        LIST_EVENTS = T("List Events")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_EVENT,
            title_display = T("Event Details"),
            title_list = LIST_EVENTS,
            title_update = T("Edit Event"),
            title_search = T("Search Events"),
            subtitle_create = T("Add New Event"),
            subtitle_list = T("Events"),
            label_list_button = LIST_EVENTS,
            label_create_button = ADD_EVENT,
            label_delete_button = T("Delete Event"),
            msg_record_created = T("Event added"),
            msg_record_modified = T("Event updated"),
            msg_record_deleted = T("Event deleted"),
            msg_list_empty = T("No Events currently registered"))

        event_id = S3ReusableField("event_id", db.event_event,
                                   sortby="name",
                                   requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                   "event_event.id",
                                                                   self.event_represent,
                                                                   filterby="closed",
                                                                   filter_opts=[False],
                                                                   orderby="event_event.name",
                                                                   sort=True)),
                                   represent = self.event_represent,
                                   label = T("Event"),
                                   ondelete = "CASCADE",
                                   # Uncomment these to use an Autocomplete & not a Dropdown
                                   #widget = S3AutocompleteWidget()
                                   #comment = DIV(_class="tooltip",
                                   #              _title="%s|%s" % (T("Event"),
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
                       create_onaccept=self.event_create_onaccept,
                       update_onaccept=self.event_update_onaccept,
                       deduplicate=self.event_event_duplicate,
                       list_fields = [ "id",
                                       "name",
                                       "exercise",
                                       "closed",
                                       "comments",
                                    ])

        # Components
        # Incidents
        self.add_component("event_incident", event_event="event_id")

        # Requests
        self.add_component("req_req", event_event="event_id")

        # Tasks
        self.add_component("project_task",
                           event_event=Storage(
                                    link="event_task",
                                    joinby="event_id",
                                    key="task_id",
                                    # @ToDo: Widget to handle embedded LocationSelector
                                    #actuate="embed",
                                    actuate="link",
                                    autocomplete="name",
                                    autodelete=False))

        # Human Resources
        self.add_component("event_human_resource", event_event="event_id")
        self.add_component("hrm_human_resource",
                           event_event=Storage(
                                    link="event_human_resource",
                                    joinby="event_id",
                                    key="human_resource_id",
                                    # @ToDo: Widget to handle embedded AddPersonWidget
                                    #actuate="embed",
                                    actuate="link",
                                    autocomplete="name",
                                    autodelete=False))

        # Assets
        self.add_component("asset_asset",
                           event_event=Storage(
                                    link="event_asset",
                                    joinby="event_id",
                                    key="asset_id",
                                    actuate="embed",
                                    autocomplete="name",
                                    autodelete=False))

        # Facilities
        self.add_component("event_site", event_event="event_id")

        # Map Config
        self.add_component("gis_config",
                           event_event=Storage(
                                    link="event_config",
                                    joinby="event_id",
                                    multiple=False,
                                    key="config_id",
                                    actuate="replace",
                                    autocomplete="name",
                                    autodelete=True))

        # ---------------------------------------------------------------------
        # Incidents
        #
        #  Incidents are a smaller sub-component of an Event
        #  They will be the instances of Scenarios
        #   They can be Exercises or real Incidents.
        #
        tablename = "event_incident"
        table = self.define_table(tablename,
                                  event_id(),
                                  Field("name", notnull=True,
                                        length=64,
                                        label=T("Name")),
                                  *s3.meta_fields())

        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Incident"),
            title_display = T("Incident Details"),
            title_list = T("List Incidents"),
            title_update = T("Edit Incident"),
            title_search = T("Search Incidents"),
            subtitle_create = T("Add New Incident"),
            subtitle_list = T("Incidents"),
            label_list_button = T("List Incidents"),
            label_create_button = T("Add Incident"),
            label_delete_button = T("Remove Incident from this event"),
            msg_record_created = T("Incident added"),
            msg_record_modified = T("Incident updated"),
            msg_record_deleted = T("Incident removed"),
            msg_list_empty = T("No Incidents currently registered in this event"))

        incident_id = S3ReusableField("incident_id", db.event_incident,
                                      sortby="name",
                                      requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                      "event_incident.id",
                                                                      self.incident_represent,
                                                                      orderby="event_incident.name",
                                                                      sort=True)),
                                      represent = self.incident_represent,
                                      label = T("Incident"),
                                      ondelete = "RESTRICT",
                                      # Uncomment these to use an Autocomplete & not a Dropdown
                                      #widget = S3AutocompleteWidget()
                                      #comment = DIV(_class="tooltip",
                                      #              _title="%s|%s" % (T("Incident"),
                                      #                                T("Enter some characters to bring up a list of possible matches")))
                                    )
        self.configure(tablename,
                       deduplicate=self.event_incident_duplicate)
        

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage(
                event_event_id = event_id,
                event_incident_id = incident_id,
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Return safe defaults in case the model has been deactivated.
        """

        return Storage(
            event_event_id = S3ReusableField("event_id",
                                             "integer",
                                             readable=False,
                                             writable=False),
        )

    # ---------------------------------------------------------------------
    @staticmethod
    def event_create_onaccept(form):
        """
            When an Event is instantiated, populate defaults

            @ToDo: Dont't crash if modules not enabled
        """

        db = current.db
        s3db = current.s3db

        vars = form.vars

        event = vars.id
        # Set the Event in the session
        session.s3.event = event
        ctable = s3db.gis_config
        mapconfig = None
        if vars.scenario_id:
            # We have been instantiated from a Scenario, so
            # copy all resources from the Scenario to the Event

            # Read the source resource tables
            table = s3db.scenario_scenario
            htable = s3db.scenario_human_resource # @ToDo: Change to Positions
            ftable = s3db.scenario_site
            mtable = s3db.scenario_config
            query = (table.id == vars.scenario_id)
            hquery = query & (htable.scenario_id == table.id)
            fquery = query & (ftable.scenario_id == table.id)
            mquery = query & (mtable.scenario_id == table.id) & \
                             (ctable.id == mtable.config_id)
            # Attempted to do this all in 1 big query but this produced duplication in the output
            hrms = db(hquery).select(htable.human_resource_id) # @ToDo: Change to Positions
            facilities = db(fquery).select(ftable.site_id)
            mapconfig = db(mquery).select(ctable.ALL).first()

            # Write them to their respective destination tables
            htable = s3db.event_human_resource # @ToDo: Change to Positions
            ftable = s3db.event_site
            for row in hrms:
                htable.insert(event_id=event,
                              human_resource_id=row.human_resource_id)
            for row in facilities:
                ftable.insert(event_id=event,
                              site_id=row.site_id)
            if current.deployment_settings.has_module("asset"):
                atable = s3db.scenario_asset
                aquery = query & (atable.scenario_id == table.id)
                assets = db(aquery).select(atable.asset_id)
                atable = s3db.event_asset
                for row in assets:
                    atable.insert(event_id=event,
                                  asset_id=row.asset_id)
            ttable = s3db.scenario_task
            tquery = query & (ttable.scenario_id == table.id)
            tasks = db(tquery).select(ttable.task_id)
            ttable = s3db.event_task
            for row in tasks:
                ttable.insert(event_id=event,
                              task_id=row.task_id)

        if mapconfig:
            # Event's Map Config is a copy of the Default / Scenario's
            # so that it can be changed within the Event without
            # contaminating the base one
            del mapconfig["id"]
            del mapconfig["uuid"]
            #mapconfig["name"] = "Event %s" % vars.name
            mapconfig["name"] = vars.name
            config = ctable.insert(**mapconfig.as_dict())
            mtable = db.event_config
            mtable.insert(event_id=event,
                          config_id=config)
            # Activate this config
            gis.set_config(config)
            # @ToDo: Add to GIS Menu? Separate Menu?

        else:
            # We have been created without a Scenario or from a Scenario without a Map Config

            # Create a new Map Config
            # Viewport can be saved from the Map's toolbar
            config = ctable.insert(name = vars.name)
            # Activate this config
            gis.set_config(config)
            # @ToDo: Add to GIS Menu? Separate Menu?

    # ---------------------------------------------------------------------
    @staticmethod
    def event_update_onaccept(form):
        """
            When an Event is updated, check for closure
        """

        vars = form.vars
        event = vars.id
        if vars.closed:
            # Ensure this event isn't active in the session
            if session.s3.event == event:
                session.s3.event = None
            # @ToDo: Hide the Event from the Map menu
            config = current.gis.get_config()
            if config == config.config_id: # @ToDo: Doesn't look right!?
                # Reset to the Default Map
                gis.set_config(0)

    # ---------------------------------------------------------------------
    @staticmethod
    def event_represent(id):
        """
        """

        if not id:
            return current.messages.NONE
        s3db = current.s3db
        table = current.s3db.event_event
        query = (table.id == id)
        event = current.db(query).select(table.name,
                                         limitby=(0, 1),
                                         cache = s3db.cache).first()
        if event:
            return event.name
        else:
            return current.messages.UNKNOWN_OPT

    # ---------------------------------------------------------------------
    @staticmethod
    def event_event_duplicate(job):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param job: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update

          Rules for finding a duplicate:
           - If the name exists then it's a duplicate
        """

        # ignore this processing if the id is set
        if job.id:
            return
        if job.tablename == "event_event":
            table = job.table
            if "name" in job.data:
                name = job.data.name
            else:
                return

            query = (table.name == name)
            _duplicate = current.db(query).select(table.id,
                                                  limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def incident_represent(id):
        """
        """

        if not id:
            return current.messages.NONE
        s3db = current.s3db
        table = s3db.event_incident
        query = (table.id == id)
        incident = current.db(query).select(table.name,
                                            limitby=(0, 1),
                                            cache = s3db.cache).first()
        if incident:
            return incident.name
        else:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def event_incident_duplicate(job):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param job: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update

          Rules for finding a duplicate:
           - If the Event & Name exists then it's a duplicate
        """

        # ignore this processing if the id is set
        if job.id:
            return
        if job.tablename == "event_incident":
            table = job.table
            if "name" in job.data and \
               "event_id" in job.data:
                name = job.data.name
                event_id = job.data.event_id
            else:
                return

            query = (table.name == name) & \
                    (table.event_id == event_id)
            _duplicate = current.db(query).select(table.id,
                                                  limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

# =============================================================================
class S3EventAssetModel(S3Model):
    """
        Event Asset Model
    """

    names = ["event_asset"]

    def model(self):

        T = current.T
        s3 = current.response.s3

        event_id = self.event_event_id
        asset_id = self.asset_asset_id

        # ---------------------------------------------------------------------
        # Assets
        # @ToDo: Search Widget

        tablename = "event_asset"
        table = self.define_table(tablename,
                                  event_id(),
                                  # @ToDo: Move this down to the incident level
                                  #incident_id(),
                                  asset_id(),
                                  *s3.meta_fields())

        s3.crud_strings[tablename] = Storage(
            title_create = T("Assign Asset"),
            title_display = T("Asset Details"),
            title_list = T("List Assets"),
            title_update = T("Edit Asset"),
            title_search = T("Search Assets"),
            subtitle_create = T("Add New Asset"),
            subtitle_list = T("Assets"),
            label_list_button = T("List Assets"),
            label_create_button = T("Add Asset"),
            label_delete_button = T("Remove Asset from this event"),
            msg_record_created = T("Asset added"),
            msg_record_modified = T("Asset updated"),
            msg_record_deleted = T("Asset removed"),
            msg_list_empty = T("No Assets currently registered in this event"))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage()

# =============================================================================
class S3EventHRModel(S3Model):
    """
        Event Human Resources Model
    """

    names = ["event_human_resource"]
 
    def model(self):

        T = current.T
        s3 = current.response.s3

        event_id = self.event_event_id
        human_resource_id = self.hrm_human_resource_id

        # ---------------------------------------------------------------------
        # Staff/Volunteers
        # @ToDo: Use Positions, not individual HRs
        # @ToDo: Search Widget

        tablename = "event_human_resource"
        table = self.define_table(tablename,
                                  event_id(),
                                  # @ToDo: Move this down to the incident level
                                  #incident_id(),
                                  human_resource_id(),
                                  *s3.meta_fields())

        s3.crud_strings[tablename] = Storage(
            title_create = T("Assign Human Resource"),
            title_display = T("Human Resource Details"),
            title_list = T("List Assigned Human Resources"),
            title_update = T("Edit Human Resource"),
            title_search = T("Search Assigned Human Resources"),
            subtitle_create = T("Assign New Human Resource"),
            subtitle_list = T("Human Resource Assignments"),
            label_list_button = T("List Assigned Human Resources"),
            label_create_button = T("Assign Human Resource"),
            label_delete_button = T("Remove Human Resource from this event"),
            msg_record_created = T("Human Resource assigned"),
            msg_record_modified = T("Human Resource Assignment updated"),
            msg_record_deleted = T("Human Resource unassigned"),
            msg_list_empty = T("No Human Resources currently assigned to this event"))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage()

# =============================================================================
class S3EventIReportModel(S3Model):
    """
        Event Incident Reports Model
    """

    names = ["event_ireport"]
 
    def model(self):

        T = current.T
        s3 = current.response.s3

        event_id = self.event_event_id
        ireport_id = self.irs_ireport_id

        # ---------------------------------------------------------------------
        # Incident Reports
        tablename = "event_ireport"
        table = self.define_table(tablename,
                                  event_id(),
                                  # @ToDo: Move this down to the incident level
                                  #incident_id(),
                                  ireport_id(),
                                  *s3.meta_fields())

        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Incident Report"),
            title_display = T("Incident Report Details"),
            title_list = T("List Incident Reports"),
            title_update = T("Edit Incident Report"),
            title_search = T("Search Incident Reports"),
            subtitle_create = T("Add New Incident Report"),
            subtitle_list = T("Incident Reports"),
            label_list_button = T("List Incident Reports"),
            label_create_button = T("Add Incident Report"),
            label_delete_button = T("Remove Incident Report from this event"),
            msg_record_created = T("Incident Report added"),
            msg_record_modified = T("Incident Report updated"),
            msg_record_deleted = T("Incident Report removed"),
            msg_list_empty = T("No Incident Reports currently registered in this event"))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage()

# =============================================================================
class S3EventMapModel(S3Model):
    """
        Event Map Model
    """

    names = ["event_config"]
 
    def model(self):

        T = current.T
        s3 = current.response.s3

        event_id = self.event_event_id
        config_id = self.gis_config_id

        # ---------------------------------------------------------------------
        # Map Config
        tablename = "event_config"
        table = self.define_table(tablename,
                                  event_id(),
                                  # @ToDo: Move this down to the incident level
                                  #incident_id(),
                                  config_id(),
                                  *s3.meta_fields())

        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Map Configuration"),
            title_display = T("Map Configuration Details"),
            title_list = T("List Map Configurations"),
            title_update = T("Edit Map Configuration"),
            title_search = T("Search Map Configurations"),
            subtitle_create = T("Add New Map Configuration"),
            subtitle_list = T("Map Configurations"),
            label_list_button = T("List Map Configurations"),
            label_create_button = T("Add Map Configuration"),
            label_delete_button = T("Remove Map Configuration from this event"),
            msg_record_created = T("Map Configuration added"),
            msg_record_modified = T("Map Configuration updated"),
            msg_record_deleted = T("Map Configuration removed"),
            msg_list_empty = T("No Map Configurations currently registered in this event"))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage()

# =============================================================================
class S3EventSiteModel(S3Model):
    """
        Event Facility Model
    """

    names = ["event_site"]
 
    def model(self):

        T = current.T
        s3 = current.response.s3

        event_id = self.event_event_id
        site_id = self.org_site_id

        # ---------------------------------------------------------------------
        # Facilities
        # @ToDo: Search Widget
        tablename = "event_site"
        table = self.define_table(tablename,
                                  event_id(),
                                  # @ToDo: Move this down to the incident level
                                  #incident_id(),
                                  site_id,
                                  *s3.meta_fields())

        table.site_id.readable = table.site_id.writable = True

        s3.crud_strings[tablename] = Storage(
            title_create = T("Assign Facility"),
            title_display = T("Facility Details"),
            title_list = T("List Facilities"),
            title_update = T("Edit Facility"),
            title_search = T("Search Facilities"),
            subtitle_create = T("Add New Facility"),
            subtitle_list = T("Facilities"),
            label_list_button = T("List Facilities"),
            label_create_button = T("Add Facility"),
            label_delete_button = T("Remove Facility from this event"),
            msg_record_created = T("Facility added"),
            msg_record_modified = T("Facility updated"),
            msg_record_deleted = T("Facility removed"),
            msg_list_empty = T("No Facilities currently registered in this event"))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage()

# =============================================================================
class S3EventTaskModel(S3Model):
    """
        Event Tasks Model
    """

    names = ["event_task"]

    def model(self):

        T = current.T
        s3 = current.response.s3

        event_id = self.event_event_id
        task_id = self.project_task_id

        # ---------------------------------------------------------------------
        # Tasks
        # Tasks are to be assigned to resources managed by this EOC
        # - we manage in detail
        # @ToDo: Task Templates
        # @ToDo: Search Widget

        tablename = "event_task"
        table = self.define_table(tablename,
                                  event_id(),
                                  # @ToDo: Move this down to the incident level
                                  #incident_id(),
                                  task_id(),
                                  *s3.meta_fields())

        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Task"),
            title_display = T("Task Details"),
            title_list = T("List Tasks"),
            title_update = T("Edit Task"),
            title_search = T("Search Tasks"),
            subtitle_create = T("Add New Task"),
            subtitle_list = T("Tasks"),
            label_list_button = T("List Tasks"),
            label_create_button = T("Add Task"),
            label_delete_button = T("Remove Task from this event"),
            msg_record_created = T("Task added"),
            msg_record_modified = T("Task updated"),
            msg_record_deleted = T("Task removed"),
            msg_list_empty = T("No Tasks currently registered in this event"))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage()

# END =========================================================================
