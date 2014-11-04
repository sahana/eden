# -*- coding: utf-8 -*-

""" Sahana Eden Scenario Model

    @copyright: 2009-2014 (c) Sahana Software Foundation
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

__all__ = ("S3ScenarioModel",
           "S3ScenarioAssetModel",
           "S3ScenarioHRModel",
           "S3ScenarioMapModel",
           "S3ScenarioOrganisationModel",
           "S3ScenarioSiteModel",
           "S3ScenarioTaskModel",
           )

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from ..s3layouts import S3AddResourceLink

# =============================================================================
class S3ScenarioModel(S3Model):
    """
        Scenario Model

        http://eden.sahanafoundation.org/wiki/BluePrintScenario

        Link tables are in separate classes to increase performance & allow
        the system to be more modular
    """

    names = ("scenario_scenario",
             "scenario_scenario_id",
             )

    def model(self):

        T = current.T
        db = current.db

        # ---------------------------------------------------------------------
        # Scenarios
        #
        #  Scenarios are Templates for Incidents to plan what resources are required
        #

        tablename = "scenario_scenario"
        self.define_table(tablename,
                          self.event_incident_type_id(),
                          Field("name", notnull=True,
                                length=64,    # Mayon compatiblity
                                label = T("Name"),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       # Open Map Config to set the default Location
                       create_next = URL(args=["[id]", "config"]),
                       deduplicate = self.scenario_duplicate,
                       )

        # CRUD strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Scenario"),
            title_display = T("Scenario Details"),
            title_list = T("Scenarios"),
            title_update = T("Edit Scenario"),
            title_upload = T("Import Scenarios"),
            label_list_button = T("List Scenarios"),
            label_delete_button = T("Delete Scenario"),
            msg_record_created = T("Scenario added"),
            msg_record_modified = T("Scenario updated"),
            msg_record_deleted = T("Scenario deleted"),
            msg_list_empty = T("No Scenarios currently registered"))

        # Components
        self.add_components(tablename,
                            # Tasks
                            project_task = {"link": "scenario_task",
                                            "joinby": "scenario_id",
                                            "key": "task_id",
                                            # @ToDo: Widget to handle embedded LocationSelector
                                            #"actuate": "embed",
                                            "actuate": "link",
                                            "autocomplete": "name",
                                            "autodelete": False,
                                            },
                            # Human Resources
                            hrm_human_resource = {"link": "scenario_human_resource",
                                                  "joinby": "scenario_id",
                                                  "key": "human_resource_id",
                                                  # @ToDo: Widget to handle embedded AddPersonWidget
                                                  #"actuate": "embed",
                                                  "actuate": "link",
                                                  "autocomplete": "name",
                                                  "autodelete": False,
                                                  },
                            # Assets
                            asset_asset = {"link": "scenario_asset",
                                           "joinby": "scenario_id",
                                           "key": "asset_id",
                                           "actuate": "embed",
                                           "autocomplete": "name",
                                           "autodelete": False,
                                           },
                            # Facilities
                            scenario_site = "scenario_id",
                            # Organisations
                            org_organisation = {"link": "scenario_organisation",
                                                "joinby": "scenario_id",
                                                "key": "organisation_id",
                                                "actuate": "embed",
                                                "autocomplete": "name",
                                                "autodelete": False,
                                                },
                            # Map Config as a component of Scenarios
                            gis_config = {"link": "scenario_config",
                                          "joinby": "scenario_id",
                                          "multiple": False,
                                          "key": "config_id",
                                          "actuate": "replace",
                                          "autocomplete": "name",
                                          "autodelete": True,
                                          },
                            )

        represent = S3Represent(lookup=tablename)
        scenario_id = S3ReusableField("scenario_id", "reference %s" % tablename,
                                      label = T("Scenario"),
                                      ondelete = "SET NULL",
                                      represent = represent,
                                      requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "scenario_scenario.id",
                                                              represent,
                                                              orderby = "scenario_scenario.name",
                                                              sort = True,
                                                              )),
                                      sortby = "name",
                                      # Comment these to use a Dropdown & not an Autocomplete
                                      #widget = S3AutocompleteWidget()
                                      #comment = DIV(_class="tooltip",
                                      #              _title="%s|%s" % (T("Scenario"),
                                      #                                current.messages.AUTOCOMPLETE_HELP))
                                    )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(scenario_scenario_id = scenario_id,
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

        return dict(scenario_scenario_id = lambda **attr: dummy("scenario_id"),
                    )

    # ---------------------------------------------------------------------
    @staticmethod
    def scenario_duplicate(item):
        """
            Deduplication of Scenarios
        """

        data = item.data
        name = data.get("name")

        table = item.table
        query = (table.name == name)
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

# =============================================================================
class S3ScenarioAssetModel(S3Model):
    """
        Link Assets to Scenarios
    """

    names = ("scenario_asset",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Assets
        # @ToDo: Use generic Supply Items not Asset instances? (Typed resources)
        #        Depends on the scale of the scenario!
        #           So support both...
        # @ToDo: Search Widget

        tablename = "scenario_asset"
        self.define_table(tablename,
                          self.scenario_scenario_id(),
                          self.asset_asset_id(
                            comment = S3AddResourceLink(c="asset", f="asset",
                                                        tooltip = T("If you don't see the asset in the list, you can add a new one by clicking link 'Create Asset'.")),
                            ),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Asset"),
            title_display = T("Asset Details"),
            title_list = T("Assets"),
            title_update = T("Edit Asset"),
            label_list_button = T("List Assets"),
            label_delete_button = T("Remove Asset from this scenario"),
            msg_record_created = T("Asset added"),
            msg_record_modified = T("Asset updated"),
            msg_record_deleted = T("Asset removed"),
            msg_list_empty = T("No assets currently registered in this scenario"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return Storage()

# =============================================================================
class S3ScenarioHRModel(S3Model):
    """
        Link Human Resources (Staff/Volunteers) to Scenarios
    """

    names = ("scenario_human_resource",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Staff/Volunteers
        # @ToDo: Use Positions, not individual HRs (Typed resources?)
        # @ToDo: Search Widget
        tablename = "scenario_human_resource"
        self.define_table(tablename,
                          self.scenario_scenario_id(),
                          self.hrm_human_resource_id(),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Human Resource"),
            title_display = T("Human Resource Details"),
            title_list = T("Human Resources"),
            title_update = T("Edit Human Resource"),
            label_list_button = T("List Human Resources"),
            label_delete_button = T("Remove Human Resource from this scenario"),
            msg_record_created = T("Human Resource added"),
            msg_record_modified = T("Human Resource updated"),
            msg_record_deleted = T("Human Resource removed"),
            msg_list_empty = T("No Human Resources currently registered in this scenario"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return Storage()

# =============================================================================
class S3ScenarioMapModel(S3Model):
    """
        Link Map Configs to Scenarios
    """

    names = ("scenario_config",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Link Table for Map Config used in this Scenario
        # @ToDo: Widget suitable for a 1-1 relationship where we can assume
        #        that the Config is pre-created

        tablename = "scenario_config"
        self.define_table(tablename,
                          self.scenario_scenario_id(),
                          self.gis_config_id(),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Map Configuration"),
            title_display = T("Map Configuration Details"),
            title_list = T("Map Configurations"),
            title_update = T("Edit Map Configuration"),
            label_list_button = T("List Map Configurations"),
            label_delete_button = T("Remove Map Configuration from this scenario"),
            msg_record_created = T("Map Configuration added"),
            msg_record_modified = T("Map Configuration updated"),
            msg_record_deleted = T("Map Configuration removed"),
            msg_list_empty = T("No Map Configurations currently registered in this scenario"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return Storage()

# =============================================================================
class S3ScenarioOrganisationModel(S3Model):
    """
        Link Organisations to Scenarios
        - people to keep informed
        - people to mobilise
    """

    names = ("scenario_organisation",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Organisations
        # @ToDo: Search Widget

        tablename = "scenario_organisation"
        self.define_table(tablename,
                          self.scenario_scenario_id(),
                          self.org_organisation_id(),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Organization"),
            title_display = T("Organization Details"),
            title_list = T("Organizations"),
            title_update = T("Edit Organization"),
            label_list_button = T("List Organizations"),
            label_delete_button = T("Remove Organization from this scenario"),
            msg_record_created = T("Organization added"),
            msg_record_modified = T("Organization updated"),
            msg_record_deleted = T("Organization removed"),
            msg_list_empty = T("No organizations currently registered in this scenario"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return Storage()

# =============================================================================
class S3ScenarioSiteModel(S3Model):
    """
        Link Sites (Facilities) to Scenarios
    """

    names = ("scenario_site",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Facilities
        # @ToDo: Search Widget

        tablename = "scenario_site"
        self.define_table(tablename,
                          self.scenario_scenario_id(),
                          self.org_site_id,
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Facility"),
            title_display = T("Facility Details"),
            title_list = T("Facilities"),
            title_update = T("Edit Facility"),
            label_list_button = T("List Facilities"),
            label_delete_button = T("Remove Facility from this scenario"),
            msg_record_created = T("Facility added"),
            msg_record_modified = T("Facility updated"),
            msg_record_deleted = T("Facility removed"),
            msg_list_empty = T("No facilities currently registered in this scenario"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return Storage()

# =============================================================================
class S3ScenarioTaskModel(S3Model):
    """
        Link Tasks to Scenarios

        @ToDo: Task Templates (like CAP Templates)
    """

    names = ("scenario_task",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Tasks
        # Standing Tasks required for this Scenario
        # @ToDo: Search Widget

        tablename = "scenario_task"
        self.define_table(tablename,
                          self.scenario_scenario_id(),
                          self.project_task_id(),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Task"),
            title_display = T("Task Details"),
            title_list = T("Tasks"),
            title_update = T("Edit Task"),
            label_list_button = T("List Tasks"),
            label_delete_button = T("Remove Task from this scenario"),
            msg_record_created = T("Task added"),
            msg_record_modified = T("Task updated"),
            msg_record_deleted = T("Task removed"),
            msg_list_empty = T("No tasks currently registered in this scenario"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return Storage()

# END =========================================================================
