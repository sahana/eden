# -*- coding: utf-8 -*-

""" Sahana Eden Stats Model

    @copyright: 2012 (c) Sahana Software Foundation
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

__all__ = ["S3StatsModel",
           "S3StatsDemographicModel",
           "stats_parameter_represent",
           ]

from gluon import *
from gluon.storage import Storage

from ..s3 import *

# =============================================================================
class S3StatsModel(S3Model):
    """
        Statistics Management
    """

    names = ["stats_parameter",
             "stats_data",
             "stats_aggregate",
             "stats_param_id",
             ]

    def model(self):

        T = current.T
        db = current.db

        define_table = self.define_table
        location_id = self.gis_location_id
        super_entity = self.super_entity

        #----------------------------------------------------------------------
        # The super entity - stats_parameter
        #
        sp_types = Storage(
                           vulnerability_indicator = T("Vulnerability Indicator"),
                           stats_demographic = T("Demographic"),
                           #survey_question_type = T("Survey Question Type"),
                           #project_beneficary_type = T("Project Beneficiary Type"),
                           #climate_parameter = T("Climate Parameter"),
                          )

        tablename = "stats_parameter"
        table = super_entity(tablename, "parameter_id",
                             sp_types,
                             Field("name",
                                   label = T("Name")),
                             Field("description",
                                   label = T("Description")),
                             )

        # Reusable Field
        param_id = S3ReusableField("parameter_id", table,
                                   sortby="name",
                                   requires = IS_ONE_OF(db, "stats_parameter.parameter_id",
                                                        stats_parameter_represent,
                                                        orderby="stats_parameter.name",
                                                        sort=True),
                                   represent = stats_parameter_represent,
                                   label = T("Statistics Parameter"),
                                   ondelete = "CASCADE"
                                   )

        #----------------------------------------------------------------------
        # The super entity - stats_data
        #
        sd_types = Storage(
                           vulnerability_data = T("Vulnerability Data"),
                           stats_demographic_data = T("Demographic Data"),
                           #survey_answer = T("Survey Answer"),
                           #project_beneficary = T("Project Beneficiary"),
                           #climate_data = T("Climate Data"),
                           )

        tablename = "stats_data"
        table = super_entity(tablename,
                             "data_id",
                             sd_types,
                             param_id(),
                             location_id(),
                             Field("value", "double",
                                   label = T("Value")),
                             Field("date", "date",
                                   label = T("Date")),
                             self.doc_source_id(),
                             )

        self.configure("stats_data",
                        onaccept = self.stats_data_onaccept,
                        )
        #----------------------------------------------------------------------
        # Stats Aggregated data
        #
        tablename = "stats_aggregate"
        table = define_table(tablename,
                             param_id(),
                             location_id(),
                             Field("date", "date",
                                   label = T("Start Date"),
                                   ),
                             Field("end_date", "date",
                                   label = T("End Date"),
                                   ),
                             Field("min", "double",
                                   label = T("Minimum"),
                                  ),
                             Field("max", "double",
                                   label = T("Maximum"),
                                  ),
                             Field("mean", "double",
                                   label = T("Mean"),
                                  ),
                             Field("median", "double",
                                   label = T("Median"),
                                  ),
                             #Field("mean_ad", "double",
                             #      label = T("Mean Absolute Deviation"),
                             #     ),
                             #Field("std", "double",
                             #      label = T("Standard Deviation"),
                             #     ),
                             #Field("variance", "double",
                             #      label = T("Variance"),
                             #     ),
                             *s3_meta_fields()
                             )

        # ---------------------------------------------------------------------
        # Pass model-global names to response.s3
        #
        return Storage(
                stats_param_id = param_id,
                stats_update_aggregate_location = self.stats_update_aggregate_location,
            )

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults if the module is disabled """

        param_id = S3ReusableField("parameter_id", "integer",
                                   readable=False,
                                   writable=False
                                   )

        return Storage(stats_param_id = param_id)

    # ---------------------------------------------------------------------
    @staticmethod
    def stats_data_onaccept(form):
        """
           When a stats_data record is created then the related stats_aggregate
           fields need to be updated so that the results are kept up to date.

           This is done async as this can take some time
        """

        location_id = form.vars.location_id
        if location_id is None:
            return

        parameter_id = form.vars.parameter_id
        parents = current.gis.get_parents(location_id)
        async = current.s3task.async
        for location in parents:
            # calculate the aggregates for each parent
            async("stats_update_aggregate_location",
                  args = [location.id, parameter_id])

    # ---------------------------------------------------------------------
    @staticmethod
    def stats_update_aggregate_location(location_id, parameter_id):
        """
           Calculates the stats_aggregate for a specific parameter at a
           specific location.
        """

        db = current.db
        s3db = current.s3db

        # Get all the child locations
        child_locations = current.gis.get_children(location_id)
        child_ids = []
        append = child_ids.append
        for row in child_locations:
            append(row.id)

        # Get the most recent stats_data record for each location
        table = s3db.stats_data
        query = (table.location_id.belongs(child_ids)) & \
                (table.parameter_id == parameter_id) & \
                (table.deleted != True)
        rows = db(query).select(table.date,
                                table.location_id,
                                table.value,
                                table.date.max(),
                                groupby=table.location_id)
        if len(rows) == 0:
            return
        sum = 0
        num_list = []
        append = num_list.append
        start_date = rows[0].stats_data.date
        for row in rows:
            _data = row.stats_data
            if _data.date > start_date:
                start_date = _data.date
            value = _data.value
            append(value)
            sum += value
        num_list.sort()
        count = len(num_list)
        mean = float(sum) / count
        min = num_list[0]
        max = num_list[count - 1]
        if count % 2 == 0:
            median = float(num_list[count / 2] + num_list[count / 2 - 1]) / 2.0
        else:
            median = num_list[count / 2]

        # Add the value to the database
        agg_table = s3db.stats_aggregate
        query = (agg_table.location_id == location_id) & \
                (agg_table.parameter_id == parameter_id)
        exists = db(query).select(agg_table.id,
                                  limitby=(0, 1)).first()
        if exists:
            db(query).update(min = min,
                             max = max,
                             mean = mean,
                             median = median,
                             date = start_date
                             )
        else:
            agg_table.insert(parameter_id = parameter_id,
                             location_id = location_id,
                             min = min,
                             max = max,
                             mean = mean,
                             median = median,
                             date = start_date,
                             )

# =============================================================================
class S3StatsDemographicModel(S3Model):
    """
        Demographic Management
    """

    names = ["stats_demographic",
             "stats_demographic_data",
             ]

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        #----------------------------------------------------------------------
        # Demographic
        #
        tablename = "stats_demographic"
        table = define_table(tablename,
                             super_link("parameter_id", "stats_parameter"),
                             Field("name",
                                   label = T("Name")),
                             s3_comments("description",
                                         label = T("Description")),
                             *s3_meta_fields()
                             )

        # CRUD Strings
        ADD_DEMOGRAPHIC = T("Add Demographic")
        crud_strings[tablename] = Storage(
            title_create = ADD_DEMOGRAPHIC,
            title_display = T("Demographic Details"),
            title_list = T("Demographics"),
            title_update = T("Edit Demographic"),
            title_search = T("Search Demographics"),
            title_upload = T("Import Demographic"),
            subtitle_create = T("Add New Demographic"),
            label_list_button = T("List Demographics"),
            label_create_button = ADD_DEMOGRAPHIC,
            msg_record_created = T("Demographic added"),
            msg_record_modified = T("Demographic updated"),
            msg_record_deleted = T("Demographic deleted"),
            msg_list_empty = T("No demographics currently defined"))

        configure(tablename,
                  super_entity = "stats_parameter",
                  deduplicate = self.stats_demographic_duplicate,
                  )

        #----------------------------------------------------------------------
        # Demographic Data
        #
        tablename = "stats_demographic_data"
        table = define_table(tablename,
                             super_link("data_id", "stats_data"),
                             self.stats_param_id(
                                    label=T("Demographic"),
                                    requires = IS_ONE_OF(db, "stats_parameter.parameter_id",
                                                         stats_parameter_represent,
                                                         filterby="instance_type",
                                                         filter_opts=["stats_demographic"],
                                                         orderby="stats_parameter.name",
                                                         sort=True)
                                ),
                             self.gis_location_id(),
                             Field("value", "double",
                                   label = T("Value")),
                             Field("date", "date",
                                   label = T("Date")),
                             self.doc_source_id(),
                             *s3_meta_fields()
                             )

        # CRUD Strings
        ADD_DATA = T("Add Demographic Data")
        crud_strings[tablename] = Storage(
            title_create = ADD_DATA,
            title_display = T("Demographic Data Details"),
            title_list = T("Demographic Data"),
            title_update = T("Edit Demographic Data"),
            title_search = T("Search Demographic Data"),
            title_upload = T("Import Demographic Data"),
            subtitle_create = T("Add New Demographic Data"),
            label_list_button = T("List Demographic Data"),
            label_create_button = ADD_DATA,
            msg_record_created = T("Demographic Data added"),
            msg_record_modified = T("Demographic Data updated"),
            msg_record_deleted = T("Demographic Data deleted"),
            msg_list_empty = T("No demographic data currently defined"))

        configure(tablename,
                  super_entity = "stats_data",
                  )

        # ---------------------------------------------------------------------
        # Pass model-global names to response.s3
        #
        return Storage()

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults if the module is disabled """

        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def stats_demographic_duplicate(item):
        """ Import item de-duplication """

        if item.tablename == "stats_demographic":
            table = item.table
            name = item.data.get("name", None)
            query = (table.name.lower() == name.lower())
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

# =============================================================================
def stats_parameter_represent(id, row=None):
    """ FK representation """

    if row:
        return row.name
    elif not id:
        return current.messages.NONE
    elif isinstance(id, Row):
        return id.name

    db = current.db
    table = db.stats_parameter
    r = db(table._id == id).select(table.name,
                                   limitby = (0, 1)).first()
    try:
        return r.name
    except:
        return current.messages.UNKNOWN_OPT

# END =========================================================================
