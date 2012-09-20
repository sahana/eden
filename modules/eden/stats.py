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
           "S3StatsGroupModel",
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
             "stats_rebuild_aggregates",
             ]

    def model(self):

        T = current.T
        db = current.db

        define_table = self.define_table
        location_id = self.gis_location_id
        super_entity = self.super_entity

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        #----------------------------------------------------------------------
        # Super entity: stats_parameter
        #
        sp_types = Storage(
                           vulnerability_indicator = T("Vulnerability Indicator"),
                           vulnerability_aggregated_indicator = T("Vulnerability Aggregated Indicator"),
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
        # Super entity: stats_data
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
                             location_id(
                                    widget = S3LocationAutocompleteWidget(),
                                    requires = IS_LOCATION()
                                ),
                             Field("value", "double",
                                   label = T("Value")),
                             Field("date", "date",
                                   label = T("Date")),
                             self.stats_group_id(),
                             Field("approved_by", "integer",
                                   default = None)
                             )

        self.configure("stats_data",
                       onapprove = self.stats_data_onapprove,
                       requires_approval = True,
                       )
        #----------------------------------------------------------------------
        # Stats Aggregated data
        #

        # The data can be aggregated against:
        # time, all the stats_data values for the same time period.
        #       currently this is just the latest value in the time period
        # location, all the aggregated values across a number of locations
        #           thus for an L2 it will aggregate all the L3 values
        # copy, this is a copy of the previous time aggregation because no
        #       data is currently available for this time period

        aggregate_type = {1 : T("Time"),
                          2 : T("Location"),
                          3 : T("Copy"),
                          4 : T("Indicator"),
                         }

        tablename = "stats_aggregate"
        table = define_table(tablename,
                             param_id(),
                             location_id(widget = S3LocationAutocompleteWidget(),
                                        requires = IS_LOCATION()),
                             Field("agg_type", "integer",
                                   required = True,
                                   requires = IS_IN_SET(aggregate_type),
                                   represent = lambda opt: \
                                            aggregate_type.get(opt, UNKNOWN_OPT),
                                   default = 1,
                                   ),
                             Field("count", "integer",
                                   label = T("The number of aggregated records")
                                   ),
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
                             #      ),
                             #Field("std", "double",
                             #      label = T("Standard Deviation"),
                             #      ),
                             #Field("variance", "double",
                             #      label = T("Variance"),
                             #      ),
                             *s3_meta_fields()
                             )

        # ---------------------------------------------------------------------
        # Pass model-global names to response.s3
        #
        return Storage(
                stats_param_id = param_id,
                stats_rebuild_aggregates = self.stats_rebuild_aggregates,
                stats_update_time_aggregate = self.stats_update_time_aggregate,
                stats_update_aggregate_location = self.stats_update_aggregate_location,
                stats_aggregated_period = self.stats_aggregated_period,
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
    def stats_data_onapprove(row):
        """
           When a stats_data record is approved then the related stats_aggregate
           fields need to be updated so that the results are kept up to date.

           This is done async as this can take some time

           Where appropriate add test cases to modules/unit_tests/eden/stats.py
        """

        current.s3task.async("stats_update_time_aggregate",
                             args = [row.data_id],
                             )

    # ---------------------------------------------------------------------
    @staticmethod
    def stats_rebuild_aggregates():
        """
            This will delete all the stats_aggregate records and then
            rebuild them by triggering off a request for each stats_data
            record.

            @ToDo: This means that we could have a significant period without any agg data at all!
                   - should be reworked to delete old data after new data has been added?
        """

        s3db = current.s3db
        resource = s3db.resource("stats_aggregate")
        resource.delete()
        table = s3db.stats_data
        rows = current.db().select(table.data_id)
        for row in rows:
            current.s3task.async("stats_update_time_aggregate",
                                 args = [row.data_id],
                                 )
    # ---------------------------------------------------------------------
    @staticmethod
    def stats_update_time_aggregate(data_id):
        """
            This will calculate the stats_aggregate for a specific parameter
            at the specified location.

            This will get the raw data from the stats_data and generate a
            stats_aggregate record for this single item for the given time
            period.

            The reason for doing this is so that all aggregated data can be
            obtained from a single table. So when displaying data for a
            particular location it will not be necessary to try the aggregate
            table, and if it's not there then try the data table. Rather just
            look at the aggregate table.

            Once this has run then a complete set of  aggregate records should
            exists for this parameter_id and location for every time period from
            the first data item until the current time period.

           Where appropriate add test cases to modules/unit_tests/eden/stats.py
        """

        from dateutil.rrule import rrule, YEARLY

        db = current.db
        s3db = current.s3db
        dtable = s3db.stats_data
        atable = s3db.stats_aggregate
        s3db.vulnerability_data

        # First get the record that has just been added
        record = db(dtable.data_id == data_id).select(limitby=(0, 1)).first()
        location_id = record.location_id
        parameter_id = record.parameter_id
        (start_date, end_date) = s3db.stats_aggregated_period(record.date)

        # Get all the stats_data record for this location and parameter
        query = (dtable.location_id == location_id) & \
                (dtable.parameter_id == parameter_id) & \
                (dtable.deleted != True) & \
                (dtable.approved_by > 0)
        data_rows = db(query).select()
        # Get each record and store them in a dict keyed on the start date of
        # the aggregated period. The value stored is a list containing the date
        # the data_id and the value. If a record already exists for the
        # reporting period then the most recent value will be stored.
        earliest_period = start_date
        (last_period, end_date) = s3db.stats_aggregated_period(None)
        data = dict()
        data[start_date]=Storage(date = record.date,
                                 id = data_id,
                                 value = record.value)
        for row in data_rows:
            if row.data_id == record.data_id:
                continue
            (start_date, end_date) = s3db.stats_aggregated_period(row.date)
            if start_date in data:
                if row.date <= data[start_date]["date"]:
                    # The indicator on the row is of the same time period as
                    # another which is already stored in data but it is earlier
                    # so ignore this particular record
                    continue
                elif data[start_date]["id"] == data_id:
                    # The newly added indicator is the one currently stored
                    # in data but a more recent value is held on the database
                    # This will not change any of the aggregated data
                    return
            if start_date < earliest_period:
                earliest_period = start_date
            # Store the record from the db in the data storage
            data[start_date] = Storage(date = row.date,
                                       id = row.data_id,
                                       value = row.value)
        # Get all the aggregate record for this parameter and location
        query = (atable.location_id == location_id) & \
                (atable.parameter_id == parameter_id) & \
                (atable.deleted != True)
        aggr_rows = db(query).select()
        aggr = dict()
        for row in aggr_rows:
            (start_date, end_date) = s3db.stats_aggregated_period(row.date)
            aggr[start_date] = Storage(mean = row.mean,
                                       id = row.id,
                                       type = row.agg_type,
                                       end_date = row.end_date)
        # Step through each period and check that aggr is correct
        last_data_period = earliest_period
        last_type_agg = False # The type of previous non-copy record was aggr
        last_data_value = None # The value of the previous aggr record
        # used to keep track of which periods the
        # aggr record has been changed on the database
        changed_periods = []
        for dt in rrule(YEARLY, dtstart=earliest_period, until=last_period):
            # calculate the end of the dt period.
            # (it will be None if this is the last period)
            dt = dt.date()
            if dt != last_period:
                (start_date, end_date) = s3db.stats_aggregated_period(dt)
            else:
                start_date = dt
                end_date = None
            if dt in aggr:
                # The query use to update aggr records
                query = (atable.id == aggr[dt]["id"])
                # Check that the stored aggr data is correct
                type = aggr[dt]["type"]
                if type == 2:
                    # This is built using other location aggregates
                    # so it can be ignored because only time or copy aggregates
                    # are being calculated in this function
                    last_type_agg = True
                    last_data_value = aggr[dt]["mean"]
                    continue
                elif type == 3:
                    # This is a copy aggregate and can be ignored if there is
                    # no data in the data dictionary and the last type was aggr
                    if (dt not in data) and last_type_agg:
                        continue
                    # If there is data in the data dictionary for this period
                    # then then aggregate record needs to be changed
                    if dt in data:
                        value = data[dt]["value"]
                        last_data_value = value
                        db(query).update(agg_type = 1, # time
                                         count = 1, # one record
                                         min = value,
                                         max = value,
                                         mean = value,
                                         median = value,
                                         end_date = end_date,
                                         )
                        changed_periods.append((start_date, end_date))
                    # Check that the data currently stored is correct
                    elif aggr[dt]["mean"] != last_data_value:
                        value = last_data_value
                        db(query).update(agg_type = 3, # copy
                                         count = 1, # one record
                                         min = value,
                                         max = value,
                                         mean = value,
                                         median = value,
                                         end_date = end_date,
                                         )
                        changed_periods.append((start_date, end_date))
                elif type == 1:
                    # The value in the aggr should match the value in data
                    if dt in data:
                        value = data[dt]["value"]
                        last_data_value = value
                        if aggr[dt]["mean"] != value:
                            db(query).update(agg_type = 1, # time
                                             count = 1, # one record
                                             min = value,
                                             max = value,
                                             mean = value,
                                             median = value,
                                             end_date = end_date,
                                             )
                            changed_periods.append((start_date, end_date))
                    # If the data is not there then it must have been deleted
                    # So copy the value from the previous record
                    else:
                        value = last_data_value
                        db(query).update(agg_type = 3, # copy
                                         count = 1, # one record
                                         min = value,
                                         max = value,
                                         mean = value,
                                         median = value,
                                         end_date = end_date,
                                         )
                        changed_periods.append((start_date, end_date))
            # No aggregate record for this time period exists
            # So one needs to be inserted
            else:
                if dt in data:
                    value = data[dt]["value"]
                    type = 1 # time
                    last_data_value = value
                else:
                    value = last_data_value
                    type = 3 # copy
                atable.insert(parameter_id = parameter_id,
                              location_id = location_id,
                              agg_type = type,
                              count = 1, # one record
                              min = value,
                              max = value,
                              mean = value,
                              median = value,
                              date = start_date,
                              end_date = end_date,
                              )
                changed_periods.append((start_date, end_date))
        # Now that the time aggregate types have been set up correctly,
        # fire off requests for the location aggregates to be calculated
        parents = current.gis.get_parents(location_id)
        async = current.s3task.async
        for (start_date, end_date) in changed_periods:
            if parents:
                for location in parents:
                    # Calculate the aggregates for each parent
                    async("stats_update_aggregate_location",
                          args = [location.id,
                                  parameter_id,
                                  str(start_date),
                                  str(end_date),
                                  ]
                          )
            if parameter_id in s3db.vulnerability_ids() or \
               parameter_id == s3db.vulnerability_resilience_id():
                s3db.vulnerability_update_resilience(location_id,
                                                     start_date,
                                                     end_date)

    # ---------------------------------------------------------------------
    @staticmethod
    def stats_update_aggregate_location(location_id,
                                        parameter_id,
                                        start_date,
                                        end_date
                                        ):
        """
           Calculates the stats_aggregate for a specific parameter at a
           specific location.

           Where appropriate add test cases to modules/unit_tests/eden/stats.py
        """

        db = current.db
        s3db = current.s3db
        table = s3db.stats_data
        agg_table = s3db.stats_aggregate

        # Get all the child locations
        child_locations = current.gis.get_children(location_id)
        child_ids = [row.id for row in child_locations]

        # The dates have been converted to a string so the following is needed
        if end_date == "None":
            # Get the most recent stats_data record for each location
            query = (table.location_id.belongs(child_ids)) & \
                    (table.parameter_id == parameter_id) & \
                    (table.deleted != True) & \
                    (table.approved_by > 0)
            end_date = None
        else:
            query = (table.location_id.belongs(child_ids)) & \
                    (table.parameter_id == parameter_id) & \
                    (table.date <= end_date) & \
                    (table.deleted != True) & \
                    (table.approved_by > 0)
        rows = db(query).select(table.value,
                                table.date,
                                table.location_id,
                                orderby=(table.location_id, ~table.date)
                                )
        # The query may return duplicate records for the same location
        # Use the most recent, which because of the ordering will be the first
        rec_cnt = 0
        sum = 0
        last_location = 0
        num_list = []
        append = num_list.append
        for row in rows:
            loc_id = row.location_id
            if loc_id != last_location:
                last_location = loc_id
                value = row.value
                append(value)
                sum += value
                rec_cnt += 1
        if rec_cnt == 0:
            return
        num_list.sort()
        mean = float(sum) / rec_cnt
        min = num_list[0]
        max = num_list[rec_cnt - 1]
        if rec_cnt % 2 == 0:
            median = float(num_list[rec_cnt / 2] + num_list[rec_cnt / 2 - 1]) / 2.0
        else:
            median = num_list[rec_cnt / 2]

        # Add the value to the database
        query = (agg_table.location_id == location_id) & \
                (agg_table.parameter_id == parameter_id) & \
                (agg_table.date == start_date) & \
                (agg_table.end_date == end_date) & \
                (agg_table.deleted == False)
        exists = db(query).select(agg_table.id,
                                  limitby=(0, 1)).first()
        if exists:
            db(query).update(agg_type = 2, # Location
                             count = rec_cnt,
                             min = min,
                             max = max,
                             mean = mean,
                             median = median,
                             )
        else:
            agg_table.insert(parameter_id = parameter_id,
                             location_id = location_id,
                             date = start_date,
                             end_date = end_date,
                             agg_type = 2, # Location
                             count = rec_cnt,
                             min = min,
                             max = max,
                             mean = mean,
                             median = median,
                             )

    # ---------------------------------------------------------------------
    @staticmethod
    def stats_aggregated_period(data_date = None):
        """
           This will return the start and end dates of the aggregated time period.

           Currently the time period is annually so it will return the
           start and end of the current year.
        """

        from datetime import date

        if data_date is None:
            data_date = date.today()
        soap = date(data_date.year, 1, 1)
        eoap = date(data_date.year, 12, 31)
        return (soap, eoap)

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

        configure("stats_demographic",
                  super_entity = "stats_parameter",
                  deduplicate = self.stats_demographic_duplicate,
                  requires_approval = True,
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
                             self.gis_location_id(
                                    widget = S3LocationAutocompleteWidget(),
                                    requires = IS_LOCATION()
                                ),
                             Field("value", "double",
                                   label = T("Value")),
                             Field("date", "date",
                                   label = T("Date")),
                             self.stats_group_id(),
                             *s3_meta_fields()
                             )

        # CRUD Strings
        ADD_DEMOGRAPHIC = T("Add Demographic Data")
        crud_strings[tablename] = Storage(
            title_create = ADD_DEMOGRAPHIC,
            title_display = T("Demographic Data Details"),
            title_list = T("Demographic Data"),
            title_update = T("Edit Demographic Data"),
            title_search = T("Search Demographic Data"),
            title_upload = T("Import Demographic Data"),
            subtitle_create = T("Add New Demographic Data"),
            label_list_button = T("List Demographic Data"),
            label_create_button = ADD_DEMOGRAPHIC,
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
class S3StatsGroupModel(S3Model):
    """
        Table to hold the group details of the different stats records
    """

    names = ["stats_group_type",
             "stats_group",
             "stats_source",
             "stats_group_id",
             "stats_group_type_id",
             "stats_source_id",
             ]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Document-source entities
        #
        source_types = Storage(
                               #pr_pentity = T("Person"),
                               doc_image = T("Image"),
                               doc_document = T("Document"),
                               #flood_gauge = T("Flood Gauge"),
                               #survey_series = T("Survey")
                               )

        tablename = "stats_source"

        table = self.super_entity(tablename, "source_id", source_types,
                                  Field("name",
                                        label=T("Name")),
                                  )
        # Reusable Field
        source_id = S3ReusableField("source_id", table,
                                    requires = IS_NULL_OR(
                                                IS_ONE_OF(current.db,
                                                          "stats_source.source_id",
                                                          stats_source_represent)),
                                    represent = stats_source_represent,
                                    label = T("Source"),
                                    ondelete = "CASCADE")

        # CRUD Strings
        ADD_STAT_SOURCE = T("Add Demographic Source")
        demographic_crud_strings = Storage(
            title_create = ADD_STAT_SOURCE,
            title_display = T("Demographic Source Details"),
            title_list = T("Demographic Sources"),
            title_update = T("Edit Demographic Source"),
            title_search = T("Search Demographic Sources"),
            title_upload = T("Import Demographic Sources"),
            subtitle_create = T("Add New Demographic Source"),
            label_list_button = T("List Demographic Sources"),
            label_create_button = ADD_STAT_SOURCE,
            msg_record_created = T("Demographic source added"),
            msg_record_modified = T("Demographic source updated"),
            msg_record_deleted = T("Demographic source deleted"),
            msg_list_empty = T("No demographic sources currently defined"))

        ADD_VULNERABILITY = T("Add Vulnerability Indicator Source")
        vulnerability_crud_strings = Storage(
            title_create = ADD_VULNERABILITY,
            title_display = T("Vulnerability Indicator Source Details"),
            title_list = T("Vulnerability Indicator Sources"),
            title_update = T("Edit Vulnerability Indicator Sources"),
            title_search = T("Search Vulnerability Indicator Sources"),
            title_upload = T("Import Vulnerability Indicator Sources"),
            subtitle_create = T("Add New Vulnerability Indicator Sources"),
            label_list_button = T("List Vulnerability Indicator Sources"),
            label_create_button = ADD_VULNERABILITY,
            msg_record_created = T("Vulnerability indicator sources added"),
            msg_record_modified = T("Vulnerability indicator sources updated"),
            msg_record_deleted = T("Vulnerability indicator sources deleted"),
            msg_list_empty = T("No vulnerability indicator Sources currently defined"))

        current.response.s3.crud_strings[tablename] = demographic_crud_strings

        # Components
        self.add_component("stats_group", stats_source=self.super_key(table))
        self.configure("stats_source",
                       deduplicate = self.stats_source_duplicate,
                       )

        # ---------------------------------------------------------------------
        # The type of document held as a stats_group.
        #
        tablename = "stats_group_type"
        table = self.define_table(tablename,
                                  Field("stats_group_instance",
                                        label=T("Instance Type")),
                                  Field("name",
                                        label=T("Name")),
                                  Field("display",
                                        label=T("Display")),
                                  *s3_meta_fields()
                                  )
        # Reusable Field
        group_type_id = S3ReusableField("group_type_id", table,
                                    requires = IS_NULL_OR(
                                                IS_ONE_OF(current.db,
                                                          "stats_group_type.id",
                                                          stats_group_type_represent)),
                                    represent = stats_group_type_represent,
                                    label = T("Source Type"),
                                    ondelete = "CASCADE")
        # Resource Configuration
        self.configure("stats_group_type",
                       deduplicate=self.stats_group_type_duplicate,
                       )

        # ---------------------------------------------------------------------
        # Container for documents and stats records
        #
        tablename = "stats_group"
        table = self.define_table(tablename,
                                  # This is a component, so needs to be a super_link
                                  # - can't override field name, ondelete or requires
                                  self.super_link("source_id", "stats_source"),
                                  s3_date(label = T("Date Published")),
                                  self.gis_location_id(),
                                  group_type_id(),
                                  #Field("reliability",
                                  #      label=T("Reliability")),
                                  #Field("review",
                                  #      label=T("Review")),
                                  *s3_meta_fields()
                                  )
        # Reusable Field
        group_id = S3ReusableField("group_id", table,
                                    requires = IS_ONE_OF(current.db,
                                                         "stats_group.id",
                                                         stats_group_represent),
                                    represent = stats_group_represent,
                                    label = T("Stats Group"),
                                    ondelete = "CASCADE")

        table.virtualfields.append(StatsGroupVirtualFields())
        # Resource Configuration
        self.configure("stats_group",
                       deduplicate=self.stats_group_duplicate,
                       requires_approval = True,
                       )

        # ---------------------------------------------------------------------
        # Pass model-global names to response.s3
        #
        return Storage(
                       demographic_source_crud_strings = demographic_crud_strings,
                       vulnerability_source_crud_strings = vulnerability_crud_strings,
                       stats_group_type_id = group_type_id,
                       stats_group_id = group_id,
                       stats_source_id = source_id,
                       )

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults if the module is disabled """

        group_id = S3ReusableField("group_id", "integer",
                                    readable=False,
                                    writable=False)

        group_type_id = S3ReusableField("group_type_id", "integer",
                                         readable=False,
                                         writable=False)

        source_id = S3ReusableField("source_id", "integer",
                                    readable=False,
                                    writable=False)

        return Storage(
                       stats_group_type_id = group_type_id,
                       stats_group_id = group_id,
                       stats_source_id = source_id,
                       )


    # -------------------------------------------------------------------------
    @staticmethod
    def stats_group_type_duplicate(item):
        """ Import item de-duplication """

        if item.tablename == "stats_group_type":
            table = item.table
            name = item.data.get("name", None)
            query = (table.name.lower() == name.lower())
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def stats_group_duplicate(item):
        """ Import item de-duplication """

        if item.tablename == "stats_group":
            table = item.table
            location_id = item.data.get("location_id", None)
            date = item.data.get("date", None)
            query = (table.location_id == location_id) & \
                    (table.date == date)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def stats_source_duplicate(item):
        """ Import item de-duplication """

        if item.tablename == "stats_source":
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


# =============================================================================
def stats_group_type_represent(id, row=None):
    """ FK representation """

    if row:
        return row.display
    elif not id:
        return current.messages.NONE
    elif isinstance(id, Row):
        return id.display

    db = current.db
    table = db.stats_group_type
    r = db(table._id == id).select(table.display,
                                   limitby = (0, 1)).first()
    try:
        return r.display
    except:
        return current.messages.UNKNOWN_OPT

# =============================================================================
def stats_group_represent(id, row=None):
    """ FK representation """

    if row:
        return stats_source_represent(row.source_id)
    elif not id:
        return current.messages.NONE
    elif isinstance(id, Row):
        return stats_source_represent(id.source_id)

    s3db = current.s3db
    table = s3db.stats_group
    stable = s3db.stats_source
    query = (table._id == id) & \
            (stable._id == table.source_id)
    r = current.db(query).select(stable.name,
                                 limitby = (0, 1)).first()
    try:
        return r.name
    except:
        return current.messages.UNKNOWN_OPT

# =============================================================================
def stats_source_represent(id, row=None):
    """ FK representation """

    if row:
        return row.name
    elif not id:
        return current.messages.NONE
    elif isinstance(id, Row):
        return id.name

    table = current.s3db.stats_source
    r = current.db(table._id == id).select(table.name,
                                           limitby = (0, 1)).first()
    try:
        return r.name
    except:
        return current.messages.UNKNOWN_OPT

# =============================================================================
class StatsGroupVirtualFields:
    """ Virtual fields to show the group that the report belongs to
        used by vulnerability/report
    """

    extra_fields = ["group",
                    ]

    def group(self):
        try:
            approved = self.stats_group.approved_by
        except (AttributeError,TypeError):
            # @ToDo: i18n?
            return "Approval pending"
        else:
            if not approved or approved == 0:
                return "Approval pending"
            else:
                # @todo: add conditional branch for VCA report
                return "Report"

# END =========================================================================
