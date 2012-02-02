# -*- coding: utf-8 -*-

"""
    Scenario Module

    http://eden.sahanafoundation.org/wiki/BluePrintScenario

    @author: Fran Boon
"""

module = "scenario"

# Also makes use of Human Resource, Asset & Project modules
if deployment_settings.has_module(module):

    # Component definitions should be outside the conditional model load

    # Tasks as a component of Scenarios
    s3mgr.model.add_component("project_task",
                              scenario_scenario=Storage(
                                    link="scenario_task",
                                    joinby="scenario_id",
                                    key="task_id",
                                    # @ToDo: Widget to handle embedded LocationSelector
                                    #actuate="embed",
                                    actuate="link",
                                    autocomplete="name",
                                    autodelete=False))

    # Human Resources as a component of Scenarios
    s3mgr.model.add_component("hrm_human_resource",
                              scenario_scenario=Storage(
                                    link="scenario_human_resource",
                                    joinby="scenario_id",
                                    key="human_resource_id",
                                    # @ToDo: Widget to handle embedded AddPersonWidget
                                    #actuate="embed",
                                    actuate="link",
                                    autocomplete="name",
                                    autodelete=False))

    # Assets as a component of Scenarios
    s3mgr.model.add_component("asset_asset",
                              scenario_scenario=Storage(
                                    link="scenario_asset",
                                    joinby="scenario_id",
                                    key="asset_id",
                                    actuate="embed",
                                    autocomplete="name",
                                    autodelete=False))

    # Sites as a component of Scenarios
    s3mgr.model.add_component("scenario_site", scenario_scenario="scenario_id")

    # Activities as a component of Scenarios
    #s3mgr.model.add_component("project_activity",
    #                          scenario_scenario=Storage(
    #                                link="scenario_activity",
    #                                joinby="scenario_id",
    #                                key="activity_id",
    #                                actuate="embed",
    #                                autocomplete="name",
    #                                autodelete=False))

    # Map Config as a component of Scenarios
    s3mgr.model.add_component("gis_config",
                              scenario_scenario=Storage(
                                    link="scenario_config",
                                    joinby="scenario_id",
                                    multiple=False,
                                    key="config_id",
                                    actuate="replace",
                                    autocomplete="name",
                                    autodelete=True))

    def scenario_tables():
        """ Load the Scenario Tables when required """

        config_id = s3db.gis_config_id
        site_id = s3db.org_site_id

        # -------------------------------------------------------------------------
        # Scenarios
        #
        #  Scenarios are Templates for Events to plan what resources are required
        #
        # -------------------------------------------------------------------------
        tablename = "scenario_scenario"
        table = db.define_table(tablename,
                                Field("name", notnull=True,
                                      length=64,    # Mayon compatiblity
                                      label=T("Name")),
                                #location_id(),
                                s3_comments(),
                                *s3_meta_fields())

        def scenario_onaccept(form):
            """
                When a Scenario is created then clone the default map config

                @ToDo: Clone the Region or Org config
            """
            table = s3db.gis_config

            # Read the Map Config
            # Currently this is the Default one
            # @ToDo: Find the best match for the Location of the Scenario
            query = (table.id == 1)
            mapconfig = db(query).select(table.ALL).first()

            # Create a clone which can be subsequently edited without
            # contamining the base one
            if mapconfig:
                del mapconfig["id"]
                del mapconfig["uuid"]
                mapconfig["name"] = "Scenario %s" % form.vars.name
                config = table.insert(**mapconfig.as_dict())
                db.scenario_config.insert(scenario_id=form.vars.id,
                                          config_id=config)
                # Activate this config
                gis.set_config(config)

        s3mgr.configure(tablename,
                        create_onaccept=scenario_onaccept)

        # CRUD strings
        ADD_SCENARIO = T("New Scenario")
        LIST_SCENARIOS = T("List Scenarios")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_SCENARIO,
            title_display = T("Scenario Details"),
            title_list = LIST_SCENARIOS,
            title_update = T("Edit Scenario"),
            title_search = T("Search Scenarios"),
            subtitle_create = T("Add New Scenario"),
            subtitle_list = T("Scenarios"),
            label_list_button = LIST_SCENARIOS,
            label_create_button = ADD_SCENARIO,
            label_delete_button = T("Delete Scenario"),
            msg_record_created = T("Scenario added"),
            msg_record_modified = T("Scenario updated"),
            msg_record_deleted = T("Scenario deleted"),
            msg_list_empty = T("No Scenarios currently registered"))

        scenario_id = S3ReusableField("scenario_id", db.scenario_scenario,
                                      sortby="name",
                                      requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                      "scenario_scenario.id",
                                                                      "%(name)s",
                                                                      orderby="scenario_scenario.name",
                                                                      sort=True)),
                                      represent = lambda id: \
                                        (id and [db(db.scenario_scenario.id == id).select(db.scenario_scenario.name,
                                                                                          limitby=(0, 1)).first().name] or [NONE])[0],
                                      label = T("Scenario"),
                                      ondelete = "SET NULL",
                                      # Comment these to use a Dropdown & not an Autocomplete
                                      #widget = S3AutocompleteWidget()
                                      #comment = DIV(_class="tooltip",
                                      #              _title="%s|%s" % (T("Scenario"),
                                      #                                T("Enter some characters to bring up a list of possible matches")))
                                    )

        # ---------------------------------------------------------------------
        # Link Tables for Resources used in this Scenario
        # ---------------------------------------------------------------------
        # Staff/Volunteers
        # @ToDo: Use Positions, not individual HRs (Typed resources?)
        # @ToDo: Search Widget
        if deployment_settings.has_module("hrm"):
            human_resource_id = s3db.hrm_human_resource_id
            tablename = "scenario_human_resource"
            table = db.define_table(tablename,
                                    scenario_id(),
                                    human_resource_id(),
                                    *s3_meta_fields())

            s3.crud_strings[tablename] = Storage(
                title_create = T("Add Human Resource"),
                title_display = T("Human Resource Details"),
                title_list = T("List Human Resources"),
                title_update = T("Edit Human Resource"),
                title_search = T("Search Human Resources"),
                subtitle_create = T("Add New Human Resource"),
                subtitle_list = T("Human Resources"),
                label_list_button = T("List Human Resources"),
                label_create_button = T("Add Human Resource"),
                label_delete_button = T("Remove Human Resource from this scenario"),
                msg_record_created = T("Human Resource added"),
                msg_record_modified = T("Human Resource updated"),
                msg_record_deleted = T("Human Resource removed"),
                msg_list_empty = T("No Human Resources currently registered in this scenario"))

        # ---------------------------------------------------------------------
        # Assets
        # @ToDo: Use generic Supply Items not Asset instances? (Typed resources)
        #        Depends on the scale of the scenario!
        # @ToDo: Search Widget
        if deployment_settings.has_module("asset"):

            asset_id = s3db.asset_asset_id

            tablename = "scenario_asset"
            table = db.define_table(tablename,
                                    scenario_id(),
                                    asset_id(),
                                    *s3_meta_fields())

            s3.crud_strings[tablename] = Storage(
                title_create = T("Add Asset"),
                title_display = T("Asset Details"),
                title_list = T("List Assets"),
                title_update = T("Edit Asset"),
                title_search = T("Search Assets"),
                subtitle_create = T("Add New Asset"),
                subtitle_list = T("Assets"),
                label_list_button = T("List Assets"),
                label_create_button = T("Add Asset"),
                label_delete_button = T("Remove Asset from this scenario"),
                msg_record_created = T("Asset added"),
                msg_record_modified = T("Asset updated"),
                msg_record_deleted = T("Asset removed"),
                msg_list_empty = T("No Assets currently registered in this scenario"))

        # ---------------------------------------------------------------------
        # Facilities
        # @ToDo: Search Widget
        tablename = "scenario_site"
        table = db.define_table(tablename,
                                scenario_id(),
                                site_id,
                                *s3_meta_fields())

        table.site_id.readable = table.site_id.writable = True

        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Facility"),
            title_display = T("Facility Details"),
            title_list = T("List Facilities"),
            title_update = T("Edit Facility"),
            title_search = T("Search Facilities"),
            subtitle_create = T("Add New Facility"),
            subtitle_list = T("Facilities"),
            label_list_button = T("List Facilities"),
            label_create_button = T("Add Facility"),
            label_delete_button = T("Remove Facility from this scenario"),
            msg_record_created = T("Facility added"),
            msg_record_modified = T("Facility updated"),
            msg_record_deleted = T("Facility removed"),
            msg_list_empty = T("No Facilities currently registered in this scenario"))

        # ---------------------------------------------------------------------
        # Tasks
        # Standing Tasks required for this Scenario
        # @ToDo: Search Widget
        if deployment_settings.has_module("project"):
            s3mgr.load("project_task")
            # Retrieve from the Global
            task_id = response.s3.project_task_id

            tablename = "scenario_task"
            table = db.define_table(tablename,
                                    scenario_id(),
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
                label_delete_button = T("Remove Task from this scenario"),
                msg_record_created = T("Task added"),
                msg_record_modified = T("Task updated"),
                msg_record_deleted = T("Task removed"),
                msg_list_empty = T("No Tasks currently registered in this scenario"))

        # ---------------------------------------------------------------------
        # Link Table for Map Config used in this Scenario
        # @ToDo: Widget suitable for a 1-1 relationship where we can assume
        #        that the Config is pre-created
        tablename = "scenario_config"
        table = db.define_table(tablename,
                                scenario_id(),
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
            label_delete_button = T("Remove Map Configuration from this scenario"),
            msg_record_created = T("Map Configuration added"),
            msg_record_modified = T("Map Configuration updated"),
            msg_record_deleted = T("Map Configuration removed"),
            msg_list_empty = T("No Map Configurations currently registered in this scenario"))

        # Return vars which need to be accessed in different scopes
        # @ToDo: Append these to s3mgr.model?
        return dict(scenario_id = scenario_id)

    # Provide a handle to this load function
    s3mgr.loader(scenario_tables,
                 "scenario_scenario",
                 "scenario_site",
                 "scenario_config")
    if deployment_settings.has_module("hrm"):
        s3mgr.loader(event_tables,
                     "scenario_human_resource")
    if deployment_settings.has_module("asset"):
        s3mgr.loader(scenario_tables,
                     "scenario_asset")
    if deployment_settings.has_module("project"):
        s3mgr.loader(scenario_tables,
                     "scenario_task",
                     #"scenario_activity"
                     )


    def scenario_scenario_duplicate(job):
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
        if job.tablename == "scenario_scenario":
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

    s3mgr.configure("scenario_scenario", deduplicate=scenario_scenario_duplicate)

else:
    def scenario_id(**arguments):
        """ Allow FKs to be added safely to other models in case module disabled """
        return Field("scenario_id", "integer", readable=False, writable=False)
    response.s3.scenario_id = scenario_id

# END =========================================================================

