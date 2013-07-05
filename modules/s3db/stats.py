# -*- coding: utf-8 -*-

""" Sahana Eden Stats Model

    @copyright: 2012-13 (c) Sahana Software Foundation
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
           "S3StatsResidentModel",
           "S3StatsTrainedPeopleModel",
           "stats_demographic_data_controller",
           ]

from datetime import date

from gluon import *
from gluon.storage import Storage

from ..s3 import *
from s3layouts import S3AddResourceLink

# =============================================================================
class S3StatsModel(S3Model):
    """
        Statistics Data
    """

    names = ["stats_parameter",
             "stats_data",
             "stats_source",
             "stats_source_superlink",
             "stats_source_id",
             #"stats_source_details",
             ]

    def model(self):

        T = current.T
        db = current.db

        super_entity = self.super_entity
        super_link = self.super_link

        #----------------------------------------------------------------------
        # Super entity: stats_parameter
        #
        sp_types = Storage(org_resource_type = T("Organization Resource Type"),
                           project_beneficiary_type = T("Project Beneficiary Type"),
                           project_campaign_keyword = T("Project Campaign Keyword"),
                           stats_demographic = T("Demographic"),
                           stats_resident_type = T("Types of Residents"),
                           stats_trained_type = T("Types of Trained People"),
                           vulnerability_indicator = T("Vulnerability Indicator"),
                           vulnerability_aggregated_indicator = T("Vulnerability Aggregated Indicator"),
                           #survey_question_type = T("Survey Question Type"),
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
        table.instance_type.readable = True

        #----------------------------------------------------------------------
        # Super entity: stats_data
        #
        sd_types = Storage(org_resource = T("Organization Resource"),
                           project_beneficiary = T("Project Beneficiary"),
                           project_campaign_response_summary = T("Project Campaign Response Summary"),
                           stats_demographic_data = T("Demographic Data"),
                           stats_resident = T("Residents"),
                           stats_trained = T("Trained People"),
                           vulnerability_data = T("Vulnerability Data"),
                           #survey_answer = T("Survey Answer"),
                           #climate_data = T("Climate Data"),
                           )

        tablename = "stats_data"
        table = super_entity(tablename, "data_id",
                             sd_types,
                             # This is a component, so needs to be a super_link
                             # - can't override field name, ondelete or requires
                             super_link("parameter_id", "stats_parameter"),
                             self.gis_location_id(
                                widget = S3LocationAutocompleteWidget(),
                                requires = IS_LOCATION()
                             ),
                             Field("value", "double",
                                   label = T("Value")),
                             # @ToDo: This will need to be a datetime for some usecases
                             s3_date(),
                             s3_date("date_end",
                                     label = T("End Date")),
                             )

        # ---------------------------------------------------------------------
        # Stats Source Super-Entity
        #
        source_types = Storage(doc_document = T("Document"),
                               #org_organisation = T("Organization"),
                               #pr_person = T("Person"),
                               #flood_gauge = T("Flood Gauge"),
                               #survey_series = T("Survey")
                               )

        tablename = "stats_source"
        table = super_entity(tablename, "source_id", source_types,
                             Field("name",
                                   label=T("Name")),
                             )

        # For use by Instances or Components
        source_superlink = super_link("source_id", "stats_source")

        # For use by other FKs
        represent = S3Represent(lookup="stats_source")
        source_id = S3ReusableField("source_id", table,
                                    label=T("Source"),
                                    requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "stats_source.source_id",
                                                          represent,
                                                          sort=True)),
                                    represent=represent,
                                    )

        #self.add_component("stats_source_details", stats_source="source_id")

        # ---------------------------------------------------------------------
        # Stats Source Details
        #
        #tablename = "stats_source_details"
        #table = self.define_table(tablename,
        #                          # Component
        #                          source_superlink,
        #                          #Field("reliability",
        #                          #      label=T("Reliability")),
        #                          #Field("review",
        #                          #      label=T("Review")),
        #                          )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return Storage(
                stats_source_superlink = source_superlink,
                stats_source_id = source_id,
            )

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults if module is disabled """

        return Storage(
                # Needed for doc
                stats_source_superlink = S3ReusableField("source_id", "integer",
                                                         readable=False,
                                                         writable=False,
                                                         )(),
            )

# =============================================================================
class S3StatsDemographicModel(S3Model):
    """
        Baseline Demographics
    """

    names = ["stats_demographic",
             "stats_demographic_data",
             "stats_demographic_aggregate",
             "stats_demographic_rebuild_all_aggregates",
             "stats_demographic_update_aggregates",
             "stats_demographic_update_location_aggregate",
             ]

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        location_id = self.gis_location_id

        stats_parameter_represent = S3Represent(lookup="stats_parameter"),

        #----------------------------------------------------------------------
        # Demographic
        #
        tablename = "stats_demographic"
        table = define_table(tablename,
                             # Instance
                             super_link("parameter_id", "stats_parameter"),
                             Field("name",
                                   label = T("Name")),
                             s3_comments("description",
                                         label = T("Description")),
                             # Link to the Demographic which is the Total, so that we can calculate percentages
                             Field("total_id", self.stats_parameter,
                                   requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "stats_parameter.parameter_id",
                                                          stats_parameter_represent,
                                                          instance_types = ["stats_demographic"],
                                                          sort=True)),
                                   represent=stats_parameter_represent,
                                   label=T("Total")),
                             *s3_meta_fields()
                             )

        # CRUD Strings
        ADD_DEMOGRAPHIC = T("Add Demographic")
        crud_strings[tablename] = Storage(
            title_create = ADD_DEMOGRAPHIC,
            title_display = T("Demographic Details"),
            title_list = T("Demographics"),
            title_update = T("Edit Demographic"),
            #title_search = T("Search Demographics"),
            #title_upload = T("Import Demographics"),
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
                  requires_approval = True,
                  )

        #----------------------------------------------------------------------
        # Demographic Data
        #
        tablename = "stats_demographic_data"
        table = define_table(tablename,
                             # Instance
                             super_link("data_id", "stats_data"),
                             # This is a component, so needs to be a super_link
                             # - can't override field name, ondelete or requires
                             super_link("parameter_id", "stats_parameter",
                                        instance_types = ["stats_demographic"],
                                        label = T("Demographic"),
                                        represent = stats_parameter_represent,
                                        readable = True,
                                        writable = True,
                                        empty = False,
                                        comment = S3AddResourceLink(c="stats",
                                                                    f="demographic",
                                                                    vars = dict(child = "parameter_id"),
                                                                    title=ADD_DEMOGRAPHIC,
                                                                    ),
                                        ),
                             location_id(
                                widget = S3LocationAutocompleteWidget(),
                                requires = IS_LOCATION(),
                                required = True,
                                ),
                             Field("value", "double",
                                   required = True,
                                   label = T("Value"),
                                   ),
                             s3_date(required = True),
                             # Unused but needed for the stats_data SE
                             #Field("date_end", "date",
                             #      readable=False,
                             #      writable=False
                             #      ),
                             # Link to Source
                             self.stats_source_id(),
                             s3_comments(),
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
                  deduplicate = self.stats_demographic_data_duplicate,
                  requires_approval=True,
                  )

        #----------------------------------------------------------------------
        # Demographic Aggregated data
        #

        # The data can be aggregated against:
        # location, all the aggregated values across a number of locations
        #           thus for an L2 it will aggregate all the L3 values
        # time, all the demographic_data values for the same time period.
        #       currently this is just the latest value in the time period
        # copy, this is a copy of the previous time aggregation because no
        #       data is currently available for this time period

        aggregate_types = {1 : T("Time"),
                           2 : T("Location"),
                           3 : T("Copy"),
                           }

        tablename = "stats_demographic_aggregate"
        table = define_table(tablename,
                             # This is a component, so needs to be a super_link
                             # - can't override field name, ondelete or requires
                             super_link("parameter_id", "stats_parameter",
                                        label = T("Demographic"),
                                        instance_types = ["stats_demographic"],
                                        represent = S3Represent(lookup="stats_parameter"),
                                        readable = True,
                                        writable = True,
                                        empty = False,
                                        ),
                             location_id(
                                widget = S3LocationAutocompleteWidget(),
                                requires = IS_LOCATION()
                                ),
                             Field("agg_type", "integer",
                                   requires = IS_IN_SET(aggregate_types),
                                   represent = lambda opt: \
                                        aggregate_types.get(opt, UNKNOWN_OPT),
                                   default = 1,
                                   label = T("Aggregation Type"),
                                   ),
                             Field("date", "date",
                                   label = T("Start Date"),
                                   ),
                             Field("end_date", "date",
                                   label = T("End Date"),
                                   ),
                             # Sum is used by Vulnerability as a fallback if we have no data at this level
                             Field("sum", "double",
                                   label = T("Sum"),
                                   ),
                             # Percentage is used to compare an absolute value against a total
                             Field("percentage", "double",
                                   label = T("Percentage"),
                                   ),
                             #Field("min", "double",
                             #      label = T("Minimum"),
                             #      ),
                             #Field("max", "double",
                             #      label = T("Maximum"),
                             #      ),
                             #Field("mean", "double",
                             #      label = T("Mean"),
                             #      ),
                             #Field("median", "double",
                             #      label = T("Median"),
                             #      ),
                             #Field("mad", "double",
                             #      label = T("Median Absolute Deviation"),
                             #      default = 0.0,
                             #      ),
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
        # Pass names back to global scope (s3.*)
        #
        return Storage(
            stats_demographic_rebuild_all_aggregates = self.stats_demographic_rebuild_all_aggregates,
            stats_demographic_update_aggregates = self.stats_demographic_update_aggregates,
            stats_demographic_update_location_aggregate = self.stats_demographic_update_location_aggregate,
            )

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

    # -------------------------------------------------------------------------
    @staticmethod
    def stats_demographic_data_duplicate(item):
        """ Import item de-duplication """

        if item.tablename == "stats_demographic_data":
            data = item.data
            parameter_id = data.get("parameter_id", None)
            location_id = data.get("location_id", None)
            date = data.get("date", None)
            table = item.table
            query = (table.date == date) & \
                    (table.location_id == location_id) & \
                    (table.parameter_id == parameter_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def stats_demographic_rebuild_all_aggregates():
        """
            This will delete all the stats_demographic_aggregate records and
            then rebuild them by triggering off a request for each
            stats_demographic_data record.

            This function is normally only run during prepop or postpop so we
            don't need to worry about the aggregate data being unavailable for
            any length of time
        """

        # Check to see whether an existing task is running and if it is then kill it
        db = current.db
        ttable = db.scheduler_task
        rtable = db.scheduler_run
        wtable = db.scheduler_worker
        query = (ttable.task_name == "stats_demographic_update_aggregates") & \
                (rtable.task_id == ttable.id) & \
                (rtable.status == "RUNNING")
        rows = db(query).select(rtable.id,
                                rtable.task_id,
                                rtable.worker_name)
        now = current.request.utcnow
        for row in rows:
            db(wtable.worker_name == row.worker_name).update(status="KILL")
            db(rtable.id == row.id).update(stop_time=now,
                                           status="STOPPED")
            db(ttable.id == row.task_id).update(stop_time=now,
                                                status="STOPPED")

        # Delete the existing aggregates
        current.s3db.stats_demographic_aggregate.truncate()

        # Read all the approved vulnerability_data records
        dtable = db.stats_demographic
        ddtable = db.stats_demographic_data
        query = (ddtable.deleted != True) & \
                (ddtable.approved_by != None) & \
                (ddtable.parameter_id == dtable.parameter_id)
        records = db(query).select(ddtable.data_id,
                                   ddtable.parameter_id,
                                   ddtable.date,
                                   ddtable.location_id,
                                   ddtable.value,
                                   dtable.total_id,
                                   )

        # Fire off a rebuild task
        current.s3task.async("stats_demographic_update_aggregates",
                             vars=dict(records=records.json()),
                             timeout=21600 # 6 hours
                             )

    # -------------------------------------------------------------------------
    @staticmethod
    def stats_demographic_aggregated_period(data_date=None):
        """
            This will return the start and end dates of the aggregated time
            period.

            Currently the time period is annually so it will return the start
            and end of the current year.
        """

        if data_date is None:
            data_date = date.today()
        year = data_date.year
        soap = date(year, 1, 1)
        eoap = date(year, 12, 31)
        return (soap, eoap)

    # -------------------------------------------------------------------------
    @staticmethod
    def stats_demographic_update_aggregates(records=None):
        """
            This will calculate the stats_demographic_aggregate for the
            specified parameter(s) at the specified location(s).

            This will get the raw data from stats_demographic_data and generate
            a stats_demographic_aggregate record for the given time period.

            The reason for doing this is so that all aggregated data can be
            obtained from a single table. So when displaying data for a
            particular location it will not be necessary to try the aggregate
            table, and if it's not there then try the data table. Rather just
            look at the aggregate table.

            Once this has run then a complete set of  aggregate records should
            exists for this parameter_id and location for every time period from
            the first data item until the current time period.

            Where appropriate add test cases to modules/unit_tests/s3db/stats.py
        """

        if not records:
            return

        import datetime
        from dateutil.rrule import rrule, YEARLY

        db = current.db
        s3db = current.s3db
        dtable = s3db.stats_demographic_data
        atable = db.stats_demographic_aggregate
        gtable = db.gis_location

        # Data Structures used for the OPTIMISATION
        param_total_dict = {} # the total_id for each parameter
        param_location_dict = {} # a list of locations for each parameter
        location_dict = {} # a list of locations
        loc_level_list = {} # a list of levels for each location

        aggregated_period = S3StatsDemographicModel.stats_demographic_aggregated_period
        (last_period, year_end) = aggregated_period(None)

        # Test to see which date format we have based on how we were called
        if isinstance(records[0]["stats_demographic_data"]["date"], (datetime.date, datetime.datetime)):
            from_json = False
        else:
            from_json = True
            from dateutil.parser import parse

        for record in records:
            total_id = record["stats_demographic"]["total_id"]
            record = record["stats_demographic_data"]
            data_id = record["data_id"]
            location_id = record["location_id"]
            parameter_id = record["parameter_id"]
            # Skip if either the location or the parameter is not valid
            if not location_id or not parameter_id:
                s3_debug("Skipping bad stats_demographic_data record with data_id %s " % data_id)
                continue
            if total_id and parameter_id not in param_total_dict:
                param_total_dict[parameter_id] = total_id
            if from_json:
                date = parse(record["date"])
            else:
                date = record["date"]
            (start_date, end_date) = aggregated_period(date)

            # Get all the approved stats_demographic_data records for this location and parameter
            query = (dtable.location_id == location_id) & \
                    (dtable.deleted != True) & \
                    (dtable.approved_by != None)
            fields = [dtable.data_id,
                      dtable.date,
                      dtable.value,
                      ]
            if total_id:
                # Also get the records for the Total to use to calculate the percentage
                query &= (dtable.parameter_id.belongs([parameter_id, total_id]))
                fields.append(dtable.parameter_id)
            else:
                percentage = None
                query &= (dtable.parameter_id == parameter_id)
            data_rows = db(query).select(*fields)

            if total_id:
                # Separate out the rows relating to the Totals
                total_rows = data_rows.exclude(lambda row: row.parameter_id == total_id)
                # Get each record and store them in a dict keyed on the start date
                # of the aggregated period. If a record already exists for the
                # reporting period then the most recent value will be stored.
                earliest_period = current.request.utcnow.date()
                end_date = year_end
                totals = {}
                for row in total_rows:
                    row_date = row.date
                    (start_date, end_date) = aggregated_period(row_date)
                    if start_date in totals:
                        if row_date <= totals[start_date]["date"]:
                            # The indicator in the row is of the same time period as
                            # another which is already stored in totals but it is earlier
                            # so ignore this particular record
                            continue
                    elif start_date < earliest_period:
                        earliest_period = start_date
                    # Store the record from the db in the totals storage
                    totals[start_date] = Storage(date = row_date,
                                                 id = row.data_id,
                                                 value = row.value)

            # Get each record and store them in a dict keyed on the start date
            # of the aggregated period. If a record already exists for the
            # reporting period then the most recent value will be stored.
            earliest_period = start_date
            end_date = year_end
            data = {}
            data[start_date] = Storage(date = date,
                                       id = data_id,
                                       value = record["value"])
            for row in data_rows:
                if row.data_id == data_id:
                    # This is the record we started with, so skip
                    continue
                row_date = row.date
                (start_date, end_date) = aggregated_period(row_date)
                if start_date in data:
                    if row_date <= data[start_date]["date"]:
                        # The indicator in the row is of the same time period as
                        # another which is already stored in data but it is earlier
                        # so ignore this particular record
                        continue
                elif start_date < earliest_period:
                    earliest_period = start_date
                # Store the record from the db in the data storage
                data[start_date] = Storage(date = row_date,
                                           id = row.data_id,
                                           value = row.value)

            # Get all the aggregate records for this parameter and location
            query = (atable.location_id == location_id) & \
                    (atable.parameter_id == parameter_id)
            aggr_rows = db(query).select(atable.id,
                                         atable.agg_type,
                                         atable.date,
                                         atable.end_date,
                                         atable.sum,
                                         )

            aggr = {}
            for row in aggr_rows:
                (start_date, end_date) = aggregated_period(row.date)
                aggr[start_date] = Storage(id = row.id,
                                           type = row.agg_type,
                                           end_date = row.end_date,
                                           sum = row.sum,
                                           )

            # Step through each period and check that aggr is correct
            last_data_period = earliest_period
            last_type_agg = False # Whether the type of previous non-copy record was aggr
            last_data_value = None # The value of the previous aggr record
            last_total = None # The value of the previous aggr record for the totals param
            # Keep track of which periods the aggr record has been changed in
            # the database
            changed_periods = []
            for dt in rrule(YEARLY, dtstart=earliest_period, until=last_period):
                # Calculate the end of the dt period.
                # - it will be None if this is the last period
                dt = dt.date()
                if dt != last_period:
                    (start_date, end_date) = aggregated_period(dt)
                else:
                    start_date = dt
                    end_date = None
                if dt in aggr:
                    # Check that the stored aggr data is correct
                    agg_type = aggr[dt]["type"]
                    if agg_type == 2:
                        # This is built using other location aggregates
                        # so it can be ignored because only time or copy aggregates
                        # are being calculated in this function
                        last_type_agg = True
                        last_data_value = aggr[dt]["sum"]
                        continue
                    # Query to use to update aggr records
                    query = (atable.id == aggr[dt]["id"])
                    if agg_type == 3:
                        # This is a copy aggregate
                        if dt in data:
                            # There is data in the data dictionary for this period
                            # so aggregate record needs to be changed
                            value = data[dt]["value"]
                            last_data_value = value
                            if total_id:
                                if dt in totals:
                                    last_total = totals[dt]["value"]
                                if last_total:
                                    percentage = 100 * value / last_total
                                    percentage = round(percentage, 3)
                            db(query).update(agg_type = 1, # time
                                             #reported_count = 1, # one record
                                             #ward_count = 1, # one ward
                                             end_date = end_date,
                                             percentage = percentage,
                                             sum = value,
                                             #min = value,
                                             #max = value,
                                             #mean = value,
                                             #median = value,
                                             )
                            changed_periods.append((start_date, end_date))
                        elif last_type_agg:
                            # No data in the data dictionary and the last type was aggr
                            continue
                        # Check that the data currently stored is correct
                        elif aggr[dt]["sum"] != last_data_value:
                            value = last_data_value
                            if total_id:
                                if dt in totals:
                                    last_total = totals[dt]["value"]
                                if last_total:
                                    percentage = 100 * value / last_total
                                    percentage = round(percentage, 3)
                            db(query).update(agg_type = 3, # copy
                                             #reported_count = 1, # one record
                                             #ward_count = 1, # one ward
                                             end_date = end_date,
                                             percentage = percentage,
                                             sum = value,
                                             #min = value,
                                             #max = value,
                                             #mean = value,
                                             #median = value,
                                             )
                            changed_periods.append((start_date, end_date))
                    elif agg_type == 1:
                        # The value in the aggr should match the value in data
                        if dt in data:
                            value = data[dt]["value"]
                            last_data_value = value
                            if total_id and dt in totals:
                                last_total = totals[dt]["value"]
                            if aggr[dt]["sum"] != value:
                                if total_id and last_total:
                                    percentage = 100 * value / last_total
                                    percentage = round(percentage, 3)
                                db(query).update(agg_type = 1, # time
                                                 #reported_count = 1, # one record
                                                 #ward_count = 1, # one ward
                                                 end_date = end_date,
                                                 percentage = percentage,
                                                 sum = value,
                                                 #min = value,
                                                 #max = value,
                                                 #mean = value,
                                                 #median = value,
                                                 )
                                changed_periods.append((start_date, end_date))
                        else:
                            # The data is not there so it must have been deleted
                            # Copy the value from the previous record
                            value = last_data_value
                            if total_id:
                                if dt in totals:
                                    last_total = totals[dt]["value"]
                                if last_total:
                                    percentage = 100 * value / last_total
                                    percentage = round(percentage, 3)
                            db(query).update(agg_type = 3, # copy
                                             #reported_count = 1, # one record
                                             #ward_count = 1, # one ward
                                             end_date = end_date,
                                             percentage = percentage,
                                             sum = value,
                                             #min = value,
                                             #max = value,
                                             #mean = value,
                                             #median = value,
                                             )
                            changed_periods.append((start_date, end_date))
                # No aggregate record for this time period exists
                # So one needs to be inserted
                else:
                    if dt in data:
                        value = data[dt]["value"]
                        agg_type = 1 # time
                        last_data_value = value
                    else:
                        value = last_data_value
                        agg_type = 3 # copy
                    if total_id:
                        if dt in totals:
                            last_total = totals[dt]["value"]
                        if last_total:
                            percentage = 100 * value / last_total
                            percentage = round(percentage, 3)
                    atable.insert(parameter_id = parameter_id,
                                  location_id = location_id,
                                  agg_type = agg_type,
                                  #reported_count = 1, # one record
                                  #ward_count = 1, # one ward
                                  date = start_date,
                                  end_date = end_date,
                                  percentage = percentage,
                                  sum = value,
                                  #min = value,
                                  #max = value,
                                  #mean = value,
                                  #median = value,
                                  )
                    changed_periods.append((start_date, end_date))
            # End of loop through each time period

            if changed_periods == []:
                continue
            # The following structures are used in the OPTIMISATION step later
            location = db(gtable.id == location_id).select(gtable.level,
                                                           limitby=(0, 1)
                                                           ).first()
            loc_level_list[location_id] = location.level
            if parameter_id not in param_location_dict:
                param_location_dict[parameter_id] = {location_id : changed_periods}
            elif location_id not in param_location_dict[parameter_id]:
                param_location_dict[parameter_id][location_id] = changed_periods
            else:
                # Store the older of the changed periods (the end will always be None)
                # Only need to check the start date of the first period
                if changed_periods[0][0] < param_location_dict[parameter_id][location_id][0][0]:
                    param_location_dict[parameter_id][location_id] = changed_periods
            if location_id not in location_dict:
                location_dict[location_id] = changed_periods
            else:
                # Store the older of the changed periods (the end will always be None)
                # Only need to check the start date of the first period
                if changed_periods[0][0] < location_dict[location_id][0][0]:
                    location_dict[location_id] = changed_periods

        # End of loop through each stats_demographic_data record

        # OPTIMISATION
        # The following code will get all the locations for which a parameter
        # has been changed. This will remove duplicates which will occur when
        # items are being imported for many communes in the same district.
        # Take an import of 12 communes in the same district, without this the
        # district will be updated 12 times, the province will be updated 12
        # times and the country will be updated 12 times that is 33 unnecessary
        # updates (for each time period) (i.e. 15 updates rather than 48)

        # Get all the parents
        parents = {}
        get_parents = current.gis.get_parents
        for loc_id in location_dict.keys():
            _parents = get_parents(loc_id)
            if parents:
                parents[loc_id] = _parents
        # Expand the list of locations for each parameter
        parents_data = {}
        for (param_id, loc_dict) in param_location_dict.items():
            for (loc_id, periods) in loc_dict.items():
                if loc_id in parents: # There won't be a parent if this is a L0
                    for p_loc_row in parents[loc_id]:
                        p_loc_id = p_loc_row.id
                        if param_id in parents_data:
                            if p_loc_id in parents_data[param_id]:
                                # Store the older of the changed periods (the end will always be None)
                                # Only need to check the start date of the first period
                                if periods[0][0] < parents_data[param_id][p_loc_id][0][0][0]:
                                    parents_data[param_id][p_loc_id][0] = periods
                            else:
                                parents_data[param_id][p_loc_id] = [periods,
                                                                    loc_level_list[loc_id]
                                                                    ]
                        else:
                            parents_data[param_id] = {p_loc_id : [periods,
                                                                  loc_level_list[loc_id]
                                                                  ]
                                                      }

        # Now that the time aggregate types have been set up correctly,
        # fire off requests for the location aggregates to be calculated
        async = current.s3task.async
        for (param_id, loc_dict) in parents_data.items():
            total_id = param_total_dict[param_id]
            for (loc_id, (changed_periods, loc_level)) in loc_dict.items():
                for (start_date, end_date) in changed_periods:
                    s, e = str(start_date), str(end_date)
                    async("stats_demographic_update_aggregate_location",
                          args = [loc_level, loc_id, param_id, total_id, s, e],
                          timeout = 1800 # 30m
                          )

    # -------------------------------------------------------------------------
    @staticmethod
    def stats_demographic_update_location_aggregate(location_level,
                                                    location_id,
                                                    parameter_id,
                                                    total_id,
                                                    start_date,
                                                    end_date
                                                    ):
        """
            Calculates the stats_demographic_aggregate for a specific parameter at a
            specific location.

            @param location_id: the location record ID
            @param parameter_id: the parameter record ID
            @param total_id: the parameter record ID for the percentage calculation
            @param start_date: the start date of the time period (as string)
            @param end_date: the end date of the time period (as string)
        """

        db = current.db
        dtable = current.s3db.stats_demographic_data
        atable = db.stats_demographic_aggregate

        # Get all the child locations
        child_locations = current.gis.get_children(location_id, location_level)
        child_ids = [row.id for row in child_locations]

        # Get the most recent stats_demographic_data record for all child locations
        query = (dtable.parameter_id == parameter_id) & \
                (dtable.deleted != True) & \
                (dtable.approved_by != None) & \
                (dtable.location_id.belongs(child_ids))
        if end_date == "None": # converted to string as async parameter
            end_date = None
        else:
            query &= (dtable.date <= end_date)
        rows = db(query).select(dtable.value,
                                dtable.date,
                                dtable.location_id,
                                orderby=(dtable.location_id, ~dtable.date),
                                # groupby avoids duplicate records for the same
                                # location, but is slightly slower than just
                                # skipping the duplicates in the loop below
                                #groupby=(dtable.location_id)
                                )

        # Get the most recent aggregate for this location for the total parameter
        if total_id == "None": # converted to string as async parameter
            total_id = None
        
        # Collect the values, skip duplicate records for the
        # same location => use the most recent one, which is
        # the first row for each location as per the orderby
        # in the query above
        last_location = None
        values = []
        append = values.append
        for row in rows:
            new_location_id = row.location_id
            if new_location_id != last_location:
                last_location = new_location_id
                append(row.value)

        # Aggregate the values
        values_len = len(values)
        if not values_len:
            return

        values_sum = sum(values)
        #values_min = min(values)
        #values_max = max(values)
        #values_avg = float(values_sum) / values_len

        percentage = 100 * values_sum / values_total
        values_percentage = round(percentage, 3)

        #from numpy import median
        #values_med = median(values)
        #values_mad = median([abs(v - values_med) for v in values])

        # Add or update the aggregated values in the database

        # Do we already have a record?
        query = (atable.location_id == location_id) & \
                (atable.parameter_id == parameter_id) & \
                (atable.date == start_date) & \
                (atable.end_date == end_date)
        exists = db(query).select(atable.id, limitby=(0, 1)).first()

        attr = dict(agg_type = 2, # Location
                    #reported_count = values_len,
                    #ward_count = len(child_ids),
                    #min = values_min,
                    #max = values_max,
                    #mean = values_avg,
                    #median = values_med,
                    #mad = values_mad,
                    sum = values_sum,
                    percentage = values_percentage,
                    )
        if exists:
            # Update
            db(query).update(**attr)
        else:
            # Insert new
            atable.insert(parameter_id = parameter_id,
                          location_id = location_id,
                          date = start_date,
                          end_date = end_date,
                          **attr
                          )
        return

# =============================================================================
def stats_demographic_data_controller():
    """
        Function to be called from controller functions
        - display all demographic data for a location as a tab.
        - options.s3json lookups for AddResourceLink
    """

    request = current.request
    if "options.s3json" in request.args:
        # options.s3json lookups for AddResourceLink
        output = current.rest_controller("stats", "demographic_data")
        return output

    # Only viewing is valid
    vars = request.get_vars
    if "viewing" not in vars:
        error = current.xml.json_message(False, 400, message="viewing not in vars")
        raise HTTP(400, error)
    else:
        viewing = vars.viewing
    if "." in viewing:
        tablename, id = viewing.split(".", 1)
    else:
        error = current.xml.json_message(False, 400, message="viewing needs a period")
        raise HTTP(400, error)

    s3db = current.s3db
    table = s3db[tablename]
    location_id = current.db(table.id == id).select(table.location_id,
                                                    limitby=(0, 1)
                                                    ).first().location_id

    s3 = current.response.s3
    dtable = s3db.stats_demographic_data

    field = dtable.location_id
    s3.filter = (field == location_id)
    field.default = location_id
    field.readable = field.writable = False

    # Post-process
    def postp(r, output):
        if r.representation == "html":
            output["title"] = s3.crud_strings[tablename].title_display
        return output
    s3.postp = postp

    if tablename == "project_location":
        rheader = s3db.project_rheader
    else:
        rheader = None

    output = current.rest_controller("stats", "demographic_data",
                                     rheader=rheader)

    return output

# =============================================================================
class S3StatsResidentModel(S3Model):
    """
        Used to record residents in the CRMT (Community Resilience Mapping Tool) template
    """

    names = ["stats_resident",
             "stats_resident_type",
             ]

    def model(self):

        T = current.T

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        tablename = "stats_resident_type"
        table = define_table(tablename,
                             # Instance
                             super_link("parameter_id", "stats_parameter"),
                             Field("name",
                                   label=T("Name")),
                             s3_comments(),
                             *s3_meta_fields())

        ADD_RESIDENT_TYPE = T("Add New Resident Type")
        crud_strings[tablename] = Storage(
            title_create=T("Add Resident Type"),
            title_display=T("Resident Type Details"),
            title_list=T("Resident Types"),
            title_update=T("Edit Resident Type"),
            #title_search=T("Search Resident Types"),
            #title_upload=T("Import Resident Types"),
            subtitle_create=ADD_RESIDENT_TYPE,
            label_list_button=T("Resident Types"),
            label_create_button=ADD_RESIDENT_TYPE,
            label_delete_button=T("Delete Resident Type"),
            msg_record_created=T("Resident Type added"),
            msg_record_modified=T("Resident Type updated"),
            msg_record_deleted=T("Resident Type deleted"),
            msg_list_empty=T("No Resident Types defined"))

        # Resource Configuration
        configure(tablename,
                  super_entity = "stats_parameter",
                  )

        represent = S3Represent(lookup=tablename)

        tablename = "stats_resident"
        table = define_table(tablename,
                             # Instance
                             super_link("data_id", "stats_data"),
                             # Instance (link to Photos)
                             super_link("doc_id", "doc_entity"),
                             Field("name", notnull=True,
                                   label=T("Name")),
                             # This is a component, so needs to be a super_link
                             # - can't override field name, ondelete or requires
                             super_link("parameter_id", "stats_parameter",
                                        label = T("Resident Type"),
                                        instance_types = ["stats_resident_type"],
                                        represent = S3Represent(lookup="stats_parameter"),
                                        readable = True,
                                        writable = True,
                                        empty = True,
                                        comment = S3AddResourceLink(c="stats",
                                                                    f="resident_type",
                                                                    vars = dict(child = "parameter_id"),
                                                                    title=ADD_RESIDENT_TYPE),
                                        ),
                             Field("value", "integer", 
                                   requires=IS_NULL_OR(
                                               IS_INT_IN_RANGE(0, 999999)
                                               ),
                                   label=T("Number of Residents")),
                             self.gis_location_id(label=T("Address")),
                             self.pr_person_id(label=T("Contact Person")),
                             s3_comments(),
                             *s3_meta_fields())

        ADD_RESIDENT = T("Add New Resident")
        crud_strings[tablename] = Storage(
            title_create=T("Add Resident"),
            title_display=T("Resident Details"),
            title_list=T("Residents"),
            title_update=T("Edit Resident"),
            title_search=T("Search Residents"),
            title_upload=T("Import Residents"),
            subtitle_create=ADD_RESIDENT,
            label_list_button=T("Residents"),
            label_create_button=ADD_RESIDENT,
            label_delete_button=T("Delete Resident"),
            msg_record_created=T("Resident added"),
            msg_record_modified=T("Resident updated"),
            msg_record_deleted=T("Resident deleted"),
            msg_list_empty=T("No Residents defined"))

        filter_widgets = [S3OptionsFilter("parameter_id",
                                          label=T("Type"),
                                          represent="%(name)s",
                                          widget="multiselect",
                                          ),
                          ]

        configure(tablename,
                  super_entity=["doc_entity", "stats_data"],
                  filter_widgets = filter_widgets,
                  )

        return Storage(
        )
# =============================================================================
class S3StatsTrainedPeopleModel(S3Model):
    """
        Used to record trained people in the CRMT (Community Resilience Mapping Tool) template
    """

    names = ["stats_trained",
             "stats_trained_type",
             ]

    def model(self):

        T = current.T

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        tablename = "stats_trained_type"
        table = define_table(tablename,
                             # Instance
                             super_link("parameter_id", "stats_parameter"),
                             Field("name",
                                   label=T("Name")),
                             s3_comments(),
                             *s3_meta_fields())

        ADD_TRAINED_PEOPLE_TYPE = T("Add New Type of Trained People")
        crud_strings[tablename] = Storage(
            title_create=T("Add Type of Trained People"),
            title_display=T("Type of Trained People  Details"),
            title_list=T("Types of Trained People"),
            title_update=T("Edit Type of Trained People"),
            #title_search=T("Search Trained People Types"),
            #title_upload=T("Import Types of Trained People"),
            subtitle_create=ADD_TRAINED_PEOPLE_TYPE,
            label_list_button=T("Types of Trained People"),
            label_create_button=ADD_TRAINED_PEOPLE_TYPE,
            label_delete_button=T("Delete Type of Trained People "),
            msg_record_created=T("Type of Trained People added"),
            msg_record_modified=T("Type of Trained People updated"),
            msg_record_deleted=T("Type of Trained People deleted"),
            msg_list_empty=T("No Types of Trained People defined"))

        # Resource Configuration
        configure(tablename,
                  super_entity = "stats_parameter",
                  )

        represent = S3Represent(lookup=tablename)

        tablename = "stats_trained"
        table = define_table(tablename,
                             # Instance
                             super_link("data_id", "stats_data"),
                             # Instance (link to Photos)
                             super_link("doc_id", "doc_entity"),
                             Field("name", notnull=True,
                                   label=T("Name")),
                             # This is a component, so needs to be a super_link
                             # - can't override field name, ondelete or requires
                             super_link("parameter_id", "stats_parameter",
                                        label = T("Type of Trained People"),
                                        instance_types = ["stats_trained_type"],
                                        represent = S3Represent(lookup="stats_parameter"),
                                        readable = True,
                                        writable = True,
                                        empty = True,
                                        comment = S3AddResourceLink(c="stats",
                                                                    f="trained_type",
                                                                    vars = dict(child = "parameter_id"),
                                                                    title=ADD_TRAINED_PEOPLE_TYPE),
                                        ),
                             Field("value", "integer", 
                                   requires=IS_NULL_OR(
                                               IS_INT_IN_RANGE(0, 999999)
                                               ),
                                   label=T("Number of Trained People")),
                             self.org_organisation_id(),
                             self.gis_location_id(label=T("Address")),
                             # Which contact is this?
                             # Training Org should be a human_resource_id
                             # Team Leader should also be a human_resource_id
                             # Either way label should be clear
                             self.pr_person_id(label=T("Contact Person")),
                             s3_comments(),
                             *s3_meta_fields())

        ADD_TRAINED_PEOPLE = T("Add Trained People")
        crud_strings[tablename] = Storage(
            title_create=ADD_TRAINED_PEOPLE,
            title_display=T("Trained People Details"),
            title_list=T("Trained People"),
            title_update=T("Edit Trained People"),
            title_search=T("Search Trained People"),
            title_upload=T("Import Trained People"),
            subtitle_create=ADD_TRAINED_PEOPLE,
            label_list_button=T("Trained People"),
            label_create_button=ADD_TRAINED_PEOPLE,
            label_delete_button=T("Delete Trained People"),
            msg_record_created=T("Trained People added"),
            msg_record_modified=T("Trained People updated"),
            msg_record_deleted=T("Trained People deleted"),
            msg_list_empty=T("No Trained People defined"))

        filter_widgets = [S3OptionsFilter("parameter_id",
                                          label=T("Type"),
                                          represent="%(name)s",
                                          widget="multiselect",
                                          ),
                          ]

        configure(tablename,
                  super_entity=["doc_entity", "stats_data"],
                  filter_widgets = filter_widgets,
                  )

        return Storage(
        )

# END =========================================================================
