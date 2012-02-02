# -*- coding: utf-8 -*-

"""
    Event Module

    http://eden.sahanafoundation.org/wiki/BluePrintScenario

    @author: Fran Boon

    @ToDo: Event should be a higher-level term
           Incident is the primary unit at which things are managed:
                Scenarios are designed
                Resources are assigned
                Situation Reports are made
"""

module = "event"

# Also requires Scenario module
# Can make use of Human Resource, Asset, Project & Request modules
if deployment_settings.has_module(module):

    # Component definitions should be outside the conditional model load

    # Incidents as a component of Events
    s3mgr.model.add_component("event_incident", event_event="event_id")

    # Requests as a component of Events
    s3mgr.model.add_component("req_req", event_event="event_id")

    # Tasks as a component of Events
    s3mgr.model.add_component("project_task",
                              event_event=Storage(
                                    link="event_task",
                                    joinby="event_id",
                                    key="task_id",
                                    # @ToDo: Widget to handle embedded LocationSelector
                                    #actuate="embed",
                                    actuate="link",
                                    autocomplete="name",
                                    autodelete=False))

    # Human Resources as a component of Events
    s3mgr.model.add_component("event_human_resource", event_event="event_id")
    s3mgr.model.add_component("hrm_human_resource",
                              event_event=Storage(
                                    link="event_human_resource",
                                    joinby="event_id",
                                    key="human_resource_id",
                                    # @ToDo: Widget to handle embedded AddPersonWidget
                                    #actuate="embed",
                                    actuate="link",
                                    autocomplete="name",
                                    autodelete=False))

    # Assets as a component of Events
    s3mgr.model.add_component("asset_asset",
                              event_event=Storage(
                                    link="event_asset",
                                    joinby="event_id",
                                    key="asset_id",
                                    actuate="embed",
                                    autocomplete="name",
                                    autodelete=False))

    # Sites as a component of Events
    s3mgr.model.add_component("event_site", event_event="event_id")

    # Activities as a component of Events
    #s3mgr.model.add_component("project_activity",
    #                          event_event=Storage(
    #                                link="event_activity",
    #                                joinby="event_id",
    #                                key="activity_id",
    #                                actuate="embed",
    #                                autocomplete="name",
    #                                autodelete=False))

    # Map Config as a component of Events
    s3mgr.model.add_component("gis_config",
                              event_event=Storage(
                                    link="event_config",
                                    joinby="event_id",
                                    multiple=False,
                                    key="config_id",
                                    actuate="replace",
                                    autocomplete="name",
                                    autodelete=True))

    # Request component added later in models/req.py

    def event_tables():
        """ Load the Event Tables when required """

        module = "event"

        if deployment_settings.has_module("scenario"):
            s3mgr.load("scenario_scenario")
        scenario_id = response.s3.scenario_id
        config_id = s3db.gis_config_id
        site_id = s3db.org_site_id

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
        table = db.define_table(tablename,
                                scenario_id(),
                                Field("name", notnull=True, # Name could be a code
                                      length=64,    # Mayon compatiblity
                                      label=T("Name")),
                                #Field("code",       # e.g. to link to WebEOC
                                #      length=64,    # Mayon compatiblity
                                #      label=T("Code")),
                                Field("exercise", "boolean",
                                      represent = lambda opt: "√" if opt else NONE,
                                      comment = DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Exercise"),
                                                                      T("Exercises mean all screens have a watermark & all notifications have a prefix."))),
                                      label=T("Exercise?")),
                                Field("zero_hour", "datetime",
                                      default = request.utcnow,
                                      requires = IS_DATETIME(format=s3_datetime_format),
                                      comment = DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Zero Hour"),
                                                                      T("The time at which the Event started."))),
                                      label=T("Zero Hour")),
                                Field("closed", "boolean",
                                      default = False,
                                      label=T("Closed")),
                                s3_comments(),
                                *s3_meta_fields())

        def event_create_onaccept(form):
            """ When an Event is instantiated, populate defaults """
            event = form.vars.id
            # Set the Event in the session
            session.s3.event = event
            ctable = s3db.gis_config
            if form.vars.scenario_id:
                # We have been instantiated from a Scenario, so
                # copy all resources from the Scenario to the Event

                # Read the source resource tables
                table = s3db.scenario_scenario
                htable = s3db.scenario_human_resource # @ToDo: Change to Positions
                ftable = s3db.scenario_site
                mtable = s3db.scenario_config
                query = (table.id == form.vars.scenario_id)
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
                if deployment_settings.has_module("asset"):
                    #s3mgr.load("asset_asset")
                    atable = db.scenario_asset
                    aquery = query & (atable.scenario_id == table.id)
                    assets = db(aquery).select(atable.asset_id)
                    atable = s3db.event_asset
                    for row in assets:
                        atable.insert(event_id=event,
                                      asset_id=row.asset_id)
                ttable = db.scenario_task
                tquery = query & (ttable.scenario_id == table.id)
                tasks = db(tquery).select(ttable.task_id)
                ttable = db.event_task
                for row in tasks:
                    ttable.insert(event_id=event,
                                  task_id=row.task_id)

            else:
                # We have been created without a Scenario

                # Read the Map Config
                # Currently this is the Default one
                # @ToDo: Find the best match for the Location of the Event
                query = (ctable.id == 1)
                mapconfig = db(query).select(ctable.ALL).first()

            if mapconfig:
                # Event's Map Config is a copy of the Default / Scenario's
                # so that it can be changed within the Event without
                # contaminating the base one
                del mapconfig["id"]
                del mapconfig["uuid"]
                #mapconfig["name"] = "Event %s" % form.vars.name
                mapconfig["name"] = form.vars.name
                config = ctable.insert(**mapconfig.as_dict())
                mtable = db.event_config
                mtable.insert(event_id=event,
                              config_id=config)
                # Activate this config
                gis.set_config(config)
                # @ToDo: Add to GIS Menu? Separate Menu?

        def event_update_onaccept(form):
            """ When an Event is updated, check for closure """
            event = form.vars.id
            if form.vars.closed:
                # Ensure this event isn't active in the session
                if session.s3.event == event:
                    session.s3.event = None
                # @ToDo: Hide the Event from the Map menu
                config = gis.get_config()
                if config == config.config_id:
                    # Reset to the Default Map
                    gis.set_config(1)

        if deployment_settings.has_module("project"):
            create_next_url = URL(args=["[id]", "task"])
        elif deployment_settings.has_module("hrm"):
            create_next_url = URL(args=["[id]", "huaan_resource"])
        elif deployment_settings.has_module("asset"):
            create_next_url = URL(args=["[id]", "asset"])
        else:
            create_next_url = URL(args=["[id]", "site"])

        s3mgr.configure(tablename,
                        create_onaccept=event_create_onaccept,
                        create_next = create_next_url,
                        update_onaccept=event_update_onaccept,
                        list_fields = [ "id",
                                        "name",
                                        "exercise",
                                        "closed",
                                        "comments",
                                    ])

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

        def event_represent(id):
            if not id:
                return NONE
            table = db.event_event
            query = (table.id == id)
            event = db(query).select(table.name,
                                     limitby=(0, 1)).first()
            if event:
                return event.name
            else:
                return UNKNOWN_OPT

        event_id = S3ReusableField("event_id", db.event_event,
                                   sortby="name",
                                   requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                   "event_event.id",
                                                                   event_represent,
                                                                   filterby="closed",
                                                                   filter_opts=[False],
                                                                   orderby="event_event.name",
                                                                   sort=True)),
                                   represent = event_represent,
                                   label = T("Event"),
                                   ondelete = "CASCADE",
                                   # Uncomment these to use an Autocomplete & not a Dropdown
                                   #widget = S3AutocompleteWidget()
                                   #comment = DIV(_class="tooltip",
                                   #              _title="%s|%s" % (T("Event"),
                                   #                                T("Enter some characters to bring up a list of possible matches")))
                                    )

        # ---------------------------------------------------------------------
        # Incidents
        #
        #  Incidents are a smaller sub-component of an Event
        #  They will be the instances of Scenarios
        #   They can be Exercises or real Incidents.
        #
        tablename = "event_incident"
        table = db.define_table(tablename,
                                event_id(),
                                Field("name", notnull=True,
                                      length=64,
                                      label=T("Name")),
                                *s3_meta_fields())

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

        def incident_represent(id):
            if not id:
                return NONE
            table = db.event_incident
            query = (table.id == id)
            incident = db(query).select(table.name,
                                        limitby=(0, 1)).first()
            if incident:
                return incident.name
            else:
                return UNKNOWN_OPT

        incident_id = S3ReusableField("incident_id", db.event_incident,
                                      sortby="name",
                                      requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                      "event_incident.id",
                                                                      incident_represent,
                                                                      orderby="event_incident.name",
                                                                      sort=True)),
                                      represent = incident_represent,
                                      label = T("Incident"),
                                      ondelete = "RESTRICT",
                                      # Uncomment these to use an Autocomplete & not a Dropdown
                                      #widget = S3AutocompleteWidget()
                                      #comment = DIV(_class="tooltip",
                                      #              _title="%s|%s" % (T("Incident"),
                                      #                                T("Enter some characters to bring up a list of possible matches")))
                                    )


        # =====================================================================
        # Link Tables for Resources used in this Event (@ToDo: Move to Incident)
        # =====================================================================

        # ---------------------------------------------------------------------
        # Incident Reports
        # ---------------------------------------------------------------------
        if deployment_settings.has_module("irs"):
            # Load model
            s3mgr.load("irs_ireport")
            ireport_id = response.s3.irs_ireport_id

            tablename = "event_ireport"
            table = db.define_table(tablename,
                                    event_id(),
                                    # @ToDo: Move this down to the incident level
                                    #incident_id(),
                                    ireport_id(),
                                    *s3_meta_fields())

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
        # Staff/Volunteers
        # @ToDo: Use Positions, not individual HRs
        # @ToDo: Search Widget
        if deployment_settings.has_module("hrm"):
            human_resource_id = s3db.hrm_human_resource_id
            tablename = "event_human_resource"
            table = db.define_table(tablename,
                                    event_id(),
                                    # @ToDo: Move this down to the incident level
                                    #incident_id(),
                                    human_resource_id(),
                                    *s3_meta_fields())

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
        # Assets
        # @ToDo: Search Widget
        if deployment_settings.has_module("asset"):

            asset_id = s3db.asset_asset_id

            tablename = "event_asset"
            table = db.define_table(tablename,
                                    event_id(),
                                    # @ToDo: Move this down to the incident level
                                    #incident_id(),
                                    asset_id(),
                                    *s3_meta_fields())

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
        # Facilities
        # @ToDo: Search Widget
        tablename = "event_site"
        table = db.define_table(tablename,
                                event_id(),
                                # @ToDo: Move this down to the incident level
                                #incident_id(),
                                site_id,
                                *s3_meta_fields())

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
        # Tasks
        # Tasks are to be assigned to resources managed by this EOC
        # - we manage in detail
        # @ToDo: Task Templates
        # @ToDo: Search Widget
        if deployment_settings.has_module("project"):
            s3mgr.load("project_task")
            # Retrieve from the Global
            task_id = response.s3.project_task_id

            tablename = "event_task"
            table = db.define_table(tablename,
                                    event_id(),
                                    # @ToDo: Move this down to the incident level
                                    #incident_id(),
                                    task_id(),
                                    *s3_meta_fields())

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
        # Activities
        # Activities are completed by external Organisations
        # - we only maintain a high-level overview
        # @ToDo: Search Widget
        if deployment_settings.has_module("project"):
            activity_id = s3db.project_activity_id

            tablename = "event_activity"
            table = db.define_table(tablename,
                                    event_id(),
                                    # @ToDo: Move this down to the incident level
                                    #incident_id(),
                                    activity_id(),
                                    *s3_meta_fields())

            s3.crud_strings[tablename] = Storage(
                title_create = T("Add Activity"),
                title_display = T("Activity Details"),
                title_list = T("List Activities"),
                title_update = T("Edit Activity"),
                title_search = T("Search Activities"),
                subtitle_create = T("Add New Activity"),
                subtitle_list = T("Activities"),
                label_list_button = T("List Activities"),
                label_create_button = T("Add Activity"),
                label_delete_button = T("Remove Activity from this event"),
               msg_record_created = T("Activity added"),
                msg_record_modified = T("Activity updated"),
                msg_record_deleted = T("Activity removed"),
                msg_list_empty = T("No Activities currently registered in this event"))

        # ---------------------------------------------------------------------
        # Map Config
        tablename = "event_config"
        table = db.define_table(tablename,
                                event_id(),
                                # @ToDo: Move this down to the incident level
                                #incident_id(),
                                config_id(),
                                *s3_meta_fields())

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

        # Pass variables back to global scope (response.s3.*)
        return dict(
            event_id = event_id,
            incident_id = incident_id
            )

    # Provide a handle to this load function
    s3mgr.loader(event_tables,
                 "event_event",
                 "event_incident",
                 "event_site",
                 "event_config")
    if deployment_settings.has_module("irs"):
        s3mgr.loader(event_tables,
                     "event_ireport")
    if deployment_settings.has_module("hrm"):
        s3mgr.loader(event_tables,
                     "event_human_resource")
    if deployment_settings.has_module("asset"):
        s3mgr.loader(event_tables,
                     "event_asset")
    if deployment_settings.has_module("project"):
        s3mgr.loader(event_tables,
                     "event_task",
                     "event_activity")

    # ---------------------------------------------------------------------
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
            _duplicate = db(query).select(table.id,
                                          limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

    s3mgr.configure("event_event", deduplicate=event_event_duplicate)

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
            _duplicate = db(query).select(table.id,
                                          limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

    s3mgr.configure("event_incident", deduplicate=event_incident_duplicate)

else:
    def event_id(**arguments):
        """ Allow FKs to be added safely to other models in case module disabled """
        return Field("event_id", "integer", readable=False, writable=False)
    response.s3.event_id = event_id
    def incident_id(**arguments):
        """ Allow FKs to be added safely to other models in case module disabled """
        return Field("incident_id", "integer", readable=False, writable=False)
    response.s3.incident_id = incident_id

# END =========================================================================
