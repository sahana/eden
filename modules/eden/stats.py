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
           "stats_demographic_data_controller",
           ]

from gluon import *
from gluon.dal import Row, Rows
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
             "stats_update_time_aggregate",
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
                           project_beneficiary_type = T("Project Beneficiary Type"),
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
                           project_beneficiary = T("Project Beneficiary"),
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
                             s3_date(),
                             s3_date("date_end",
                                     label = T("End Date")),
                             self.stats_group_id(),
                             Field("approved_by", "integer",
                                   default = None)
                             )

        self.configure(tablename,
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
                                   requires = IS_IN_SET(aggregate_type),
                                   represent = lambda opt: \
                                            aggregate_type.get(opt, UNKNOWN_OPT),
                                   default = 1,
                                   ),
                             Field("reported_count", "integer",
                                   label = T("The number of aggregated records")
                                   ),
                             Field("ward_count", "integer",
                                   label = T("The number geographical units that may be part of the aggregation")
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
                             Field("mad", "double",
                                   label = T("Median Absolute Deviation"),
                                   default = 0.0,
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
        def rebuild_aggregates():
            return

        return Storage(
                stats_param_id = param_id,
                stats_rebuild_aggregates = rebuild_aggregates
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

        # Check to see whether an existing task is running and if it is then kill it
        # - this is only run during prepop (fast) & postpop, so shouldn't be needed
        # db = current.db
        # ttable = db.scheduler_task
        # rtable = db.scheduler_run
        # wtable = db.scheduler_worker
        # query = (ttable.task_name == "stats_group_clean") & \
                # (rtable.scheduler_task == ttable.id) & \
                # (rtable.status == "RUNNING")
        # rows = db(query).select(rtable.id,
                                # rtable.scheduler_task,
                                # rtable.worker_name)
        # now = current.request.utcnow
        # for row in rows:
            # db(wtable.worker_name == row.worker_name).update(status="KILL")
            # db(rtable.id == row.id).update(stop_time=now,
                                           # status="STOPPED")
            # db(ttable.id == row.scheduler_task).update(stop_time=now,
                                                       # status="STOPPED")

        # Mark all stats_group records as needing to be updated
        s3db = current.s3db
        current.db(s3db.stats_group.deleted != True).update(dirty=True)

        # Delete the existing data
        resource = s3db.resource("stats_aggregate")
        resource.delete()

        # Fire off a rebuild task
        current.s3task.async("stats_group_clean",
                             timeout=21600 # 6 hours
                             )

    # ---------------------------------------------------------------------
    @classmethod
    def stats_update_time_aggregate(cls, data_id=None):
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
        dtable = db.stats_data
        atable = db.stats_aggregate
        gis_table = db.gis_location

        stats_aggregated_period = cls.stats_aggregated_period

        if not data_id:
            query = (dtable.deleted != True) & \
                    (dtable.approved_by != None)
            records = db(query).select(dtable.location_id,
                                       dtable.parameter_id,
                                       dtable.data_id,
                                       dtable.date,
                                       dtable.value,
                                       )
        elif isinstance(data_id, Rows):
            records = data_id
        elif not isinstance(data_id, Row):
            records = db(dtable.data_id == data_id).select(dtable.location_id,
                                                           dtable.parameter_id,
                                                           dtable.data_id,
                                                           dtable.date,
                                                           dtable.value,
                                                           limitby=(0, 1))
        else:
            records = [data_id]
            data_id = data_id.data_id

        # Data Structures used for the OPTIMISATION steps
        param_location_dict = {} # a list of locations for each parameter
        location_dict = {} # a list of locations
        loc_level_list = {} # a list of levels for each location

        if current.deployment_settings.has_module("vulnerability"):
            vulnerability = True
            vulnerability_id_list = s3db.vulnerability_ids()
        else:
            vulnerability = False
            vulnerability_id_list = []
        for record in records:
            location_id = record.location_id
            parameter_id = record.parameter_id
            # Exit if either the location or the parameter is not valid
            if not location_id or not parameter_id:
                continue
            (start_date, end_date) = stats_aggregated_period(record.date)

            # Get all the stats_data records for this location and parameter
            query = (dtable.location_id == location_id) & \
                    (dtable.parameter_id == parameter_id) & \
                    (dtable.deleted != True) & \
                    (dtable.approved_by != None)
            data_rows = db(query).select()

            # Get each record and store them in a dict keyed on the start date of
            # the aggregated period. The value stored is a list containing the date
            # the data_id and the value. If a record already exists for the
            # reporting period then the most recent value will be stored.
            earliest_period = start_date
            (last_period, end_date) = stats_aggregated_period(None)
            data = dict()
            data[start_date]=Storage(date = record.date,
                                     id = data_id,
                                     value = record.value)
            for row in data_rows:
                if row.data_id == record.data_id:
                    continue
                row_date = row.date
                (start_date, end_date) = stats_aggregated_period(row_date)
                if start_date in data:
                    if row_date <= data[start_date]["date"]:
                        # The indicator on the row is of the same time period as
                        # another which is already stored in data but it is earlier
                        # so ignore this particular record
                        continue
                    elif data[start_date]["id"] == data_id:
                        # The newly added indicator is the one currently stored
                        # in data but a more recent value is held on the database
                        # This will not change any of the aggregated data
                        break
                if start_date < earliest_period:
                    earliest_period = start_date
                # Store the record from the db in the data storage
                data[start_date] = Storage(date = row_date,
                                           id = row.data_id,
                                           value = row.value)

            # Get all the aggregate records for this parameter and location
            query = (atable.location_id == location_id) & \
                    (atable.parameter_id == parameter_id) & \
                    (atable.deleted != True)
            aggr_rows = db(query).select(atable.id,
                                         atable.agg_type,
                                         atable.date,
                                         atable.end_date,
                                         atable.mean)

            aggr = dict()
            for row in aggr_rows:
                (start_date, end_date) = stats_aggregated_period(row.date)
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
                    (start_date, end_date) = stats_aggregated_period(dt)
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
                                             reported_count = 1, # one record
                                             ward_count = 1, # one ward
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
                                             reported_count = 1, # one record
                                             ward_count = 1, # one ward
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
                                                 reported_count = 1, # one record
                                                 ward_count = 1, # one ward
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
                                             reported_count = 1, # one record
                                             ward_count = 1, # one ward
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
                                  reported_count = 1, # one record
                                  ward_count = 1, # one ward
                                  min = value,
                                  max = value,
                                  mean = value,
                                  median = value,
                                  date = start_date,
                                  end_date = end_date,
                                  )
                    changed_periods.append((start_date, end_date))
            # End of loop through each time period

            if changed_periods == []:
                continue
            # The following structures are used in the OPTIMISATION steps later
            loc_level_list[location_id] = db(gis_table.id == location_id).select(gis_table.level,
                                                                                 limitby=(0, 1)
                                                                                 ).first().level
            if parameter_id not in param_location_dict:
                param_location_dict[parameter_id] = {location_id : changed_periods}
            elif location_id not in param_location_dict[parameter_id]:
                param_location_dict[parameter_id][location_id] = changed_periods
            else:
                # Store the older of the changed periods (the end will always be None)
                # Only need to check the start date of the first period
                if changed_periods[0][0] < param_location_dict[parameter_id][location_id][0][0]:
                    param_location_dict[parameter_id][location_id] = changed_periods
            if parameter_id in vulnerability_id_list:
                if location_id not in location_dict:
                    location_dict[location_id] = changed_periods
                else:
                    # Store the older of the changed periods (the end will always be None)
                    # Only need to check the start date of the first period
                    if changed_periods[0][0] < location_dict[location_id][0][0]:
                        location_dict[location_id] = changed_periods

        # End of loop through each stats_data record

        # OPTIMISATION step 1
        # The following code will get all the locations for which a parameter
        # has been changed. This will remove duplicates which will occur when
        # items are being imported for many communes in the same district.
        # Take an import of 12 communes in the same district, without this the
        # district will be updated 12 times, the province will be updated 12
        # times and the country will be updated 12 times that is 33 unnecessary
        # updates (for each time period) (i.e. 15 updates rather than 48)

        # Now get all the parents
        parents = {}
        get_parents = current.gis.get_parents
        for loc_id in location_dict.keys():
            parents[loc_id] = get_parents(loc_id)
        # Expand the list of locations for each parameter
        parents_data = {}
        for (param_id, loc_dict) in param_location_dict.items():
            for (loc_id, periods) in loc_dict.items():
                if loc_id in parents: # There won't be a parent if this is a L0
                    for p_loc_row in parents[loc_id]:
                        p_loc_id = p_loc_row.id
                        if param_id in parents_data:
                            if p_loc_id in parents_data[param_id]:
                                # store the older of the changed periods (the end will always be None)
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


        # OPTIMISATION step 2
        # The following code will get all the locations for which the
        # resilence indicator needs to be recalculated. Without this
        # the calculations will be triggered for each parameter and for each
        # location unnecessarily.
        # For example an import of 12 communes in the same district with data
        # for the 10 parameters that make up the resilence calculation will trigger
        # 480 updates, rather than the optimal 15, for each time period.
        resilence_parents = {}
        for (loc_id, periods) in location_dict.items():
            resilence_parents[loc_id] = (periods, loc_level_list[loc_id], True)
            for p_loc_row in parents[loc_id]:
                p_loc_id = p_loc_row.id
                if p_loc_id in resilence_parents:
                    # store the older of the changed periods (the end will always be None)
                    # Only need to check the start date of the first period
                    if periods[0][0] < resilence_parents[p_loc_id][0][0][0]:
                        resilence_parents[p_loc_id][0] = periods
                else:
                    resilence_parents[p_loc_id] = [periods, loc_level_list[loc_id], False]

        # Now that the time aggregate types have been set up correctly,
        # fire off requests for the location aggregates to be calculated
        async = current.s3task.async
        for (param_id, loc_dict) in parents_data.items():
            for (loc_id, (changed_periods,loc_level)) in loc_dict.items():
                for (start_date, end_date) in changed_periods:
                    s, e = str(start_date), str(end_date)
                    async("stats_update_aggregate_location",
                          args = [loc_level, loc_id, param_id, s, e],
                          timeout = 1800 # 30m
                          )
        if vulnerability:
            # Now calculate the resilence indicators
            vulnerability_resilience = s3db.vulnerability_resilience
            resilience_pid = s3db.vulnerability_resilience_id()
            for (location_id, (period, loc_level, use_location)) in resilence_parents.items():
                for (start_date, end_date) in changed_periods:
                    vulnerability_resilience(loc_level,
                                             location_id,
                                             resilience_pid,
                                             vulnerability_id_list,
                                             start_date,
                                             end_date,
                                             use_location)

    # ---------------------------------------------------------------------
    @staticmethod
    def stats_update_aggregate_location(location_level,
                                        location_id,
                                        parameter_id,
                                        start_date,
                                        end_date
                                        ):
        """
           Calculates the stats_aggregate for a specific parameter at a
           specific location.

            @param location_id: the location record ID
            @param parameter_id: the parameter record ID
            @param start_date: the start date of the time period (as string)
            @param end_date: the end date of the time period (as string)
        """

        db = current.db
        #s3db = current.s3db

        dtable = db.stats_data
        atable = db.stats_aggregate

        # Get all the child locations
        child_locations = current.gis.get_children(location_id, location_level)
        child_ids = [row.id for row in child_locations]

        # Get the (most recent) stats_data record for all child locations
        if end_date == "None": # converted to string as async parameter
            query = (dtable.parameter_id == parameter_id) & \
                    (dtable.deleted != True) & \
                    (dtable.approved_by != None) & \
                    (dtable.location_id.belongs(child_ids))
            end_date = None
        else:
            query = (dtable.parameter_id == parameter_id) & \
                    (dtable.location_id.belongs(child_ids)) & \
                    (dtable.deleted != True) & \
                    (dtable.approved_by != None) & \
                    (dtable.date <= end_date)
        rows = db(query).select(dtable.value,
                                dtable.date,
                                dtable.location_id,
                                orderby=(dtable.location_id, ~dtable.date),
                                # groupby avoids duplicate records for the same
                                # location, but is slightly slower than just
                                # skipping the duplicates in the loop below
                                #groupby=(dtable.location_id)
                                )

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

        import numpy

        values_sum = sum(values)
        values_min = min(values)
        values_max = max(values)
        values_avg = float(values_sum) / values_len
        values_med = numpy.median(values)
        values_mad = numpy.median([abs(v - values_med) for v in values])

        # Add or update the aggregated values in the database

        # Do we already have a record?
        query = (atable.location_id == location_id) & \
                (atable.parameter_id == parameter_id) & \
                (atable.date == start_date) & \
                (atable.end_date == end_date) & \
                (atable.deleted != True)
        exists = db(query).select(atable.id, limitby=(0, 1)).first()

        if exists:
            # Update
            db(query).update(agg_type = 2, # Location
                             reported_count = values_len,
                             ward_count = len(child_ids),
                             min = values_min,
                             max = values_max,
                             mean = values_avg,
                             median = values_med,
                             mad = values_mad
                             )
        else:
            # Insert new
            atable.insert(agg_type = 2, # Location
                          parameter_id = parameter_id,
                          location_id = location_id,
                          date = start_date,
                          end_date = end_date,
                          reported_count = values_len,
                          ward_count = len(child_ids),
                          min = values_min,
                          max = values_max,
                          mean = values_avg,
                          median = values_med,
                          mad = values_mad
                          )

        return

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
        year = data_date.year
        soap = date(year, 1, 1)
        eoap = date(year, 12, 31)
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
        Tables to hold the group details of the different stats records
    """

    names = ["stats_group_type",
             "stats_group",
             "stats_source",
             "stats_group_id",
             "stats_group_type_id",
             "stats_source_id",
             "stats_group_clean",
             ]

    def model(self):

        T = current.T
        db = current.db
        configure = self.configure
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Document-source entities
        #
        source_types = Storage(
                               doc_document = T("Document"),
                               # @ToDo: Remove - Images aren't stats sources!
                               doc_image = T("Image"),
                               #pr_pentity = T("Person"),
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
                                                IS_ONE_OF(db,
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
        configure("stats_source",
                  deduplicate = self.stats_source_duplicate,
                  )

        # ---------------------------------------------------------------------
        # The type of document held as a stats_group.
        #
        tablename = "stats_group_type"
        table = define_table(tablename,
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
                                        IS_ONE_OF(db,
                                                  "stats_group_type.id",
                                                  stats_group_type_represent)),
                            represent = stats_group_type_represent,
                            label = T("Source Type"),
                            ondelete = "CASCADE")
        # Resource Configuration
        configure("stats_group_type",
                  deduplicate=self.stats_group_type_duplicate,
                  )

        # ---------------------------------------------------------------------
        # Container for documents and stats records
        #
        tablename = "stats_group"
        table = define_table(tablename,
                             # This is a component, so needs to be a super_link
                             # - can't override field name, ondelete or requires
                             self.super_link("source_id", "stats_source"),
                             s3_date(label = T("Date Published")),
                             self.gis_location_id(),
                             group_type_id(),
                             # Used to indicate if the record has not yet
                             # been used in aggregate calculations
                             Field("dirty", "boolean",
                                   #label = T("Dirty"),
                                   default=True,
                                   readable=False,
                                   writable=False),
                             #Field("reliability",
                             #      label=T("Reliability")),
                             #Field("review",
                             #      label=T("Review")),
                             *s3_meta_fields()
                             )
        # Reusable Field
        group_id = S3ReusableField("group_id", table,
                                   requires = IS_ONE_OF(db,
                                                        "stats_group.id",
                                                        stats_group_represent),
                                   represent = stats_group_represent,
                                   label = T("Stats Group"),
                                   ondelete = "CASCADE")

        table.virtualfields.append(StatsGroupVirtualFields())
        # Resource Configuration
        configure("stats_group",
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
                       stats_group_clean = self.stats_group_clean,
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

    # ---------------------------------------------------------------------
    @staticmethod
    def stats_group_clean():
        """
            This will get all the "dirty" approved stats_group records and from
            the related stats_data records calculate the stats_aggregate records.
        """

        db = current.db
        s3db = current.s3db
        gtable = db.stats_group
        dtable = s3db.stats_data

        query = (gtable.deleted != True) & \
                (gtable.dirty == True) & \
                (gtable.approved_by != None) & \
                (gtable.id == dtable.group_id)
        data_list = db(query).select(dtable.id,
                                     dtable.parameter_id,
                                     dtable.date,
                                     dtable.location_id,
                                     dtable.value)
        S3StatsModel.stats_update_time_aggregate(data_list)

        query = (gtable.deleted != True) & \
                (gtable.dirty == True) & \
                (gtable.approved_by != None)
        db(query).update(dirty=False)

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
                                   limitby=(0, 1)).first()
    try:
        return r.name
    except:
        return current.messages.UNKNOWN_OPT

# =============================================================================
def stats_demographic_data_controller():
    """
        Function to be called from controller functions to display all
        requests as a tab for a site.
    """

    vars = current.request.vars

    output = dict()

    if "viewing" not in vars:
        return output
    else:
        viewing = vars.viewing
    if "." in viewing:
        tablename, id = viewing.split(".", 1)
    else:
        return output

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
    field.readable = False
    field.writable = False

    dtable.group_id.readable = False
    dtable.group_id.writable = False

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
                                   limitby=(0, 1)).first()
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
                                 limitby=(0, 1)).first()
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
                                           limitby=(0, 1)).first()
    try:
        return r.name
    except:
        return current.messages.UNKNOWN_OPT

# =============================================================================
class StatsGroupVirtualFields:
    """ Virtual fields to show the group that the report belongs to
        used by vulnerability/report
    """

    extra_fields = ["group"]

    def group(self):
        try:
            approved = self.stats_group.approved_by
        except (AttributeError, TypeError):
            # @ToDo: i18n?
            return "Approval pending"
        else:
            if approved is None:
                return "Approval pending"
            else:
                sgtype = current.s3db.stats_group_type
                query = (self.stats_group.group_type_id == sgtype.id)
                r = current.db(query).select(sgtype.name,
                                             limitby=(0, 1)).first()
                if  (r.name == "stats_vca"):
                    return "VCA Report"
                # @todo: add conditional branch for VCA report
                return "Report"

# END =========================================================================
