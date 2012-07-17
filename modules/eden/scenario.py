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
           "S3ScenarioOrganisationModel",
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

        add_component = self.add_component

        # ---------------------------------------------------------------------
        # Scenarios
        #
        #  Scenarios are Templates for Incidents to plan what resources are required
        #

        tablename = "scenario_scenario"
        table = self.define_table(tablename,
                                  self.event_incident_type_id(),
                                  Field("name", notnull=True,
                                        length=64,    # Mayon compatiblity
                                        label=T("Name")),
                                  s3_comments(),
                                  *s3_meta_fields())

        self.configure(tablename,
                       # Open Map Config to set the default Location
                       create_next=URL(args=["[id]", "config"]),
                       deduplicate=self.scenario_duplicate,
                       )

        # CRUD strings
        ADD_SCENARIO = T("New Scenario")
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = ADD_SCENARIO,
            title_display = T("Scenario Details"),
            title_list = T("Scenarios"),
            title_update = T("Edit Scenario"),
            title_search = T("Search Scenarios"),
            title_upload = T("Import Scenarios"),
            subtitle_create = T("Add New Scenario"),
            label_list_button = T("List Scenarios"),
            label_create_button = ADD_SCENARIO,
            label_delete_button = T("Delete Scenario"),
            msg_record_created = T("Scenario added"),
            msg_record_modified = T("Scenario updated"),
            msg_record_deleted = T("Scenario deleted"),
            msg_list_empty = T("No Scenarios currently registered"))

        # Components
        # Tasks
        add_component("project_task",
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
        add_component("hrm_human_resource",
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
        add_component("asset_asset",
                      scenario_scenario=Storage(
                                    link="scenario_asset",
                                    joinby="scenario_id",
                                    key="asset_id",
                                    actuate="embed",
                                    autocomplete="name",
                                    autodelete=False))

        # Facilities
        add_component("scenario_site",
                      scenario_scenario="scenario_id")

        # Organisations
        add_component("org_organisation",
                      scenario_scenario=Storage(
                                    link="scenario_organisation",
                                    joinby="scenario_id",
                                    key="organisation_id",
                                    actuate="embed",
                                    autocomplete="name",
                                    autodelete=False))

        # Map Config as a component of Scenarios
        add_component("gis_config",
                      scenario_scenario=Storage(
                                    link="scenario_config",
                                    joinby="scenario_id",
                                    multiple=False,
                                    key="config_id",
                                    actuate="replace",
                                    autocomplete="name",
                                    autodelete=True))

        scenario_id = S3ReusableField("scenario_id", table,
                                      sortby="name",
                                      requires = IS_NULL_OR(
                                                    IS_ONE_OF(db, "scenario_scenario.id",
                                                              self.scenario_represent,
                                                              orderby="scenario_scenario.name",
                                                              sort=True)),
                                      represent = self.scenario_represent,
                                      label = T("Scenario"),
                                      ondelete = "SET NULL",
                                      # Comment these to use a Dropdown & not an Autocomplete
                                      #widget = S3AutocompleteWidget()
                                      #comment = DIV(_class="tooltip",
                                      #              _title="%s|%s" % (T("Scenario"),
                                      #                                T("Enter some characters to bring up a list of possible matches")))
                                    )

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
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

    # ---------------------------------------------------------------------
    @staticmethod
    def scenario_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.scenario_scenario
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    # ---------------------------------------------------------------------
    @staticmethod
    def scenario_duplicate(item):
        """
            Deduplication of Scenarios
        """

        if item.tablename != "scenario_scenario":
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

# =============================================================================
class S3ScenarioAssetModel(S3Model):
    """
        Link Assets to Scenarios
    """

    names = ["scenario_asset"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Assets
        # @ToDo: Use generic Supply Items not Asset instances? (Typed resources)
        #        Depends on the scale of the scenario!
        #           So support both...
        # @ToDo: Search Widget

        tablename = "scenario_asset"
        table = self.define_table(tablename,
                                  self.scenario_scenario_id(),
                                  self.asset_asset_id(),
                                  *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            title_create = T("Add Asset"),
            title_display = T("Asset Details"),
            title_list = T("Assets"),
            title_update = T("Edit Asset"),
            title_search = T("Search Assets"),
            subtitle_create = T("Add New Asset"),
            label_list_button = T("List Assets"),
            label_create_button = T("Add Asset"),
            label_delete_button = T("Remove Asset from this scenario"),
            msg_record_created = T("Asset added"),
            msg_record_modified = T("Asset updated"),
            msg_record_deleted = T("Asset removed"),
            msg_list_empty = T("No assets currently registered in this scenario"))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage()

# =============================================================================
class S3ScenarioHRModel(S3Model):
    """
        Link Human Resources (Staff/Volunteers) to Scenarios
    """

    names = ["scenario_human_resource"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Staff/Volunteers
        # @ToDo: Use Positions, not individual HRs (Typed resources?)
        # @ToDo: Search Widget
        tablename = "scenario_human_resource"
        table = self.define_table(tablename,
                                  self.scenario_scenario_id(),
                                  self.hrm_human_resource_id(),
                                  *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            title_create = T("Add Human Resource"),
            title_display = T("Human Resource Details"),
            title_list = T("Human Resources"),
            title_update = T("Edit Human Resource"),
            title_search = T("Search Human Resources"),
            subtitle_create = T("Add New Human Resource"),
            label_list_button = T("List Human Resources"),
            label_create_button = T("Add Human Resource"),
            label_delete_button = T("Remove Human Resource from this scenario"),
            msg_record_created = T("Human Resource added"),
            msg_record_modified = T("Human Resource updated"),
            msg_record_deleted = T("Human Resource removed"),
            msg_list_empty = T("No Human Resources currently registered in this scenario"))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage()

# =============================================================================
class S3ScenarioMapModel(S3Model):
    """
        Link Map Configs to Scenarios
    """

    names = ["scenario_config"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Link Table for Map Config used in this Scenario
        # @ToDo: Widget suitable for a 1-1 relationship where we can assume
        #        that the Config is pre-created

        tablename = "scenario_config"
        table = self.define_table(tablename,
                                  self.scenario_scenario_id(),
                                  self.gis_config_id(),
                                  *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            title_create = T("Add Map Configuration"),
            title_display = T("Map Configuration Details"),
            title_list = T("Map Configurations"),
            title_update = T("Edit Map Configuration"),
            title_search = T("Search Map Configurations"),
            subtitle_create = T("Add New Map Configuration"),
            label_list_button = T("List Map Configurations"),
            label_create_button = T("Add Map Configuration"),
            label_delete_button = T("Remove Map Configuration from this scenario"),
            msg_record_created = T("Map Configuration added"),
            msg_record_modified = T("Map Configuration updated"),
            msg_record_deleted = T("Map Configuration removed"),
            msg_list_empty = T("No Map Configurations currently registered in this scenario"))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage()

# =============================================================================
class S3ScenarioOrganisationModel(S3Model):
    """
        Link Organisations to Scenarios
        - people to keep informed
        - people to mobilise
    """

    names = ["scenario_organisation"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Organisations
        # @ToDo: Search Widget

        tablename = "scenario_organisation"
        table = self.define_table(tablename,
                                  self.scenario_scenario_id(),
                                  self.org_organisation_id(),
                                  *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            title_create = T("Add Organization"),
            title_display = T("Organization Details"),
            title_list = T("Organizations"),
            title_update = T("Edit Organization"),
            title_search = T("Search Organizations"),
            subtitle_create = T("Add New Organization"),
            label_list_button = T("List Organizations"),
            label_create_button = T("Add Organization"),
            label_delete_button = T("Remove Organization from this scenario"),
            msg_record_created = T("Organization added"),
            msg_record_modified = T("Organization updated"),
            msg_record_deleted = T("Organization removed"),
            msg_list_empty = T("No organizations currently registered in this scenario"))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage()

# =============================================================================
class S3ScenarioSiteModel(S3Model):
    """
        Link Sites (Facilities) to Scenarios
    """

    names = ["scenario_site"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Facilities
        # @ToDo: Search Widget

        tablename = "scenario_site"
        table = self.define_table(tablename,
                                  self.scenario_scenario_id(),
                                  self.org_site_id,
                                  *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            title_create = T("Add Facility"),
            title_display = T("Facility Details"),
            title_list = T("Facilities"),
            title_update = T("Edit Facility"),
            title_search = T("Search Facilities"),
            subtitle_create = T("Add New Facility"),
            label_list_button = T("List Facilities"),
            label_create_button = T("Add Facility"),
            label_delete_button = T("Remove Facility from this scenario"),
            msg_record_created = T("Facility added"),
            msg_record_modified = T("Facility updated"),
            msg_record_deleted = T("Facility removed"),
            msg_list_empty = T("No facilities currently registered in this scenario"))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage()

# =============================================================================
class S3ScenarioTaskModel(S3Model):
    """
        Link Tasks to Scenarios

        @ToDo: Task Templates (like CAP Templates)
    """

    names = ["scenario_task"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Tasks
        # Standing Tasks required for this Scenario
        # @ToDo: Search Widget

        tablename = "scenario_task"
        table = self.define_table(tablename,
                                  self.scenario_scenario_id(),
                                  self.project_task_id(),
                                  *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            title_create = T("Add Task"),
            title_display = T("Task Details"),
            title_list = T("Tasks"),
            title_update = T("Edit Task"),
            title_search = T("Search Tasks"),
            subtitle_create = T("Add New Task"),
            label_list_button = T("List Tasks"),
            label_create_button = T("Add Task"),
            label_delete_button = T("Remove Task from this scenario"),
            msg_record_created = T("Task added"),
            msg_record_modified = T("Task updated"),
            msg_record_deleted = T("Task removed"),
            msg_list_empty = T("No tasks currently registered in this scenario"))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage()

# END =========================================================================
