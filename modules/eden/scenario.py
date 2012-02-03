# -*- coding: utf-8 -*-

""" Sahana Eden Scenario Model

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

__all__ = ["S3ScenarioModel",
           "S3ScenarioAssetModel",
           "S3ScenarioHRModel",
           "S3ScenarioMapModel",
           "S3ScenarioSiteModel",
           "S3ScenarioTaskModel",
        ]

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3ScenarioModel(S3Model):
    """
        Scenario Model

        http://eden.sahanafoundation.org/wiki/BluePrintScenario

        Link tables are in separate classes to increase performance & allow
        the system to be more modular
    """

    names = ["scenario_scenario",
             "scenario_scenario_id",
            ]

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3

        # ---------------------------------------------------------------------
        # Scenarios
        #
        #  Scenarios are Templates for Events to plan what resources are required
        #

        tablename = "scenario_scenario"
        table = self.define_table(tablename,
                                  Field("name", notnull=True,
                                        length=64,    # Mayon compatiblity
                                        label=T("Name")),
                                  s3.comments(),
                                  *s3.meta_fields())

        self.configure(tablename,
                       # Open Map Config to set the default Location
                       create_next=URL(args=["[id]", "config"]),
                       deduplicate=self.scenario_scenario_duplicate,
                       )

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

        # Components
        # Tasks
        self.add_component("project_task",
                           scenario_scenario=Storage(
                                link="scenario_task",
                                joinby="scenario_id",
                                key="task_id",
                                # @ToDo: Widget to handle embedded LocationSelector
                                #actuate="embed",
                                actuate="link",
                                autocomplete="name",
                                autodelete=False))

        # Human Resources
        self.add_component("hrm_human_resource",
                           scenario_scenario=Storage(
                                    link="scenario_human_resource",
                                    joinby="scenario_id",
                                    key="human_resource_id",
                                    # @ToDo: Widget to handle embedded AddPersonWidget
                                    #actuate="embed",
                                    actuate="link",
                                    autocomplete="name",
                                    autodelete=False))

        # Assets
        self.add_component("asset_asset",
                           scenario_scenario=Storage(
                                    link="scenario_asset",
                                    joinby="scenario_id",
                                    key="asset_id",
                                    actuate="embed",
                                    autocomplete="name",
                                    autodelete=False))

        # Facilities
        self.add_component("scenario_site",
                           scenario_scenario="scenario_id")

        # Map Config as a component of Scenarios
        self.add_component("gis_config",
                           scenario_scenario=Storage(
                                    link="scenario_config",
                                    joinby="scenario_id",
                                    multiple=False,
                                    key="config_id",
                                    actuate="replace",
                                    autocomplete="name",
                                    autodelete=True))

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
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage(
                scenario_scenario_id = scenario_id,
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Return safe defaults in case the model has been deactivated.
        """

        return Storage(
            scenario_scenario_id = S3ReusableField("scenario_id",
                                                   "integer",
                                                   readable=False,
                                                   writable=False),
        )

    # -------------------------------------------------------------------------
    @staticmethod
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
            _duplicate = current.db(query).select(table.id,
                                                  limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

# =============================================================================
class S3ScenarioAssetModel(S3Model):
    """
        Scenario Asset Model
    """

    names = ["scenario_asset"]

    def model(self):

        T = current.T
        s3 = current.response.s3

        scenario_id = self.scenario_scenario_id
        asset_id = self.asset_asset_id

        # ---------------------------------------------------------------------
        # Assets
        # @ToDo: Use generic Supply Items not Asset instances? (Typed resources)
        #        Depends on the scale of the scenario!
        #           So support both...
        # @ToDo: Search Widget

        tablename = "scenario_asset"
        table = self.define_table(tablename,
                                  scenario_id(),
                                  asset_id(),
                                  *s3.meta_fields())

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
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage()

# =============================================================================
class S3ScenarioHRModel(S3Model):
    """
        Scenario Human Resources Model
    """

    names = ["scenario_human_resource"]
 
    def model(self):

        T = current.T
        s3 = current.response.s3

        scenario_id = self.scenario_scenario_id
        human_resource_id = self.hrm_human_resource_id

        # ---------------------------------------------------------------------
        # Staff/Volunteers
        # @ToDo: Use Positions, not individual HRs (Typed resources?)
        # @ToDo: Search Widget
        tablename = "scenario_human_resource"
        table = self.define_table(tablename,
                                  scenario_id(),
                                  human_resource_id(),
                                  *s3.meta_fields())

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
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage()

# =============================================================================
class S3ScenarioMapModel(S3Model):
    """
        Scenario Map Model
    """

    names = ["scenario_config"]
 
    def model(self):

        T = current.T
        s3 = current.response.s3

        scenario_id = self.scenario_scenario_id
        config_id = self.gis_config_id

        # ---------------------------------------------------------------------
        # Link Table for Map Config used in this Scenario
        # @ToDo: Widget suitable for a 1-1 relationship where we can assume
        #        that the Config is pre-created

        tablename = "scenario_config"
        table = self.define_table(tablename,
                                  scenario_id(),
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
            label_delete_button = T("Remove Map Configuration from this scenario"),
            msg_record_created = T("Map Configuration added"),
            msg_record_modified = T("Map Configuration updated"),
            msg_record_deleted = T("Map Configuration removed"),
            msg_list_empty = T("No Map Configurations currently registered in this scenario"))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage()

# =============================================================================
class S3ScenarioSiteModel(S3Model):
    """
        Scenario Facility Model
    """

    names = ["scenario_site"]
 
    def model(self):

        T = current.T
        s3 = current.response.s3

        scenario_id = self.scenario_scenario_id
        site_id = self.org_site_id

        # ---------------------------------------------------------------------
        # Facilities
        # @ToDo: Search Widget

        tablename = "scenario_site"
        table = self.define_table(tablename,
                                  scenario_id(),
                                  site_id,
                                  *s3.meta_fields())

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
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage()

# =============================================================================
class S3ScenarioTaskModel(S3Model):
    """
        Scenario Tasks Model
    """

    names = ["scenario_task"]

    def model(self):

        T = current.T
        s3 = current.response.s3

        scenario_id = self.scenario_scenario_id
        task_id = self.project_task_id

        # ---------------------------------------------------------------------
        # Tasks
        # Standing Tasks required for this Scenario
        # @ToDo: Search Widget

        tablename = "scenario_task"
        table = self.define_table(tablename,
                                  scenario_id(),
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
            label_delete_button = T("Remove Task from this scenario"),
            msg_record_created = T("Task added"),
            msg_record_modified = T("Task updated"),
            msg_record_deleted = T("Task removed"),
            msg_list_empty = T("No Tasks currently registered in this scenario"))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage()

# END =========================================================================
