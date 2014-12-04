# -*- coding: utf-8 -*-

""" Sahana Eden Stats Model

    @copyright: 2012-14 (c) Sahana Software Foundation
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

from __future__ import division

__all__ = ("S3StatsModel",
           "S3StatsDemographicModel",
           "S3StatsImpactModel",
           "S3StatsPeopleModel",
           "stats_demographic_data_controller",
           "stats_quantile",
           "stats_year",
           "stats_year_options",
           #"stats_SourceRepresent",
           )

import datetime

try:
    # try stdlib (Python 2.6)
    import json
except ImportError:
    try:
        # try external module
        import simplejson as json
    except:
        # fallback to pure-Python module
        import gluon.contrib.simplejson as json

from gluon import *
from gluon.storage import Storage

from ..s3 import *
from s3layouts import S3AddResourceLink

# =============================================================================
class S3StatsModel(S3Model):
    """
        Statistics Data
    """

    names = ("stats_parameter",
             "stats_data",
             "stats_source",
             "stats_source_superlink",
             "stats_source_id",
             #"stats_source_details",
             )

    def model(self):

        T = current.T
        db = current.db

        super_entity = self.super_entity
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Super entity: stats_parameter
        #
        sp_types = Storage(disease_statistic = T("Disease Statistic"),
                           org_resource_type = T("Organization Resource Type"),
                           project_beneficiary_type = T("Project Beneficiary Type"),
                           project_campaign_keyword = T("Project Campaign Keyword"),
                           stats_demographic = T("Demographic"),
                           stats_impact_type = T("Impact Type"),
                           # @ToDo; Deprecate
                           stats_people_type = T("Types of People"),
                           supply_distribution_item = T("Distribution Item"),
                           vulnerability_indicator = T("Vulnerability Indicator"),
                           vulnerability_aggregated_indicator = T("Vulnerability Aggregated Indicator"),
                           #survey_question_type = T("Survey Question Type"),
                           #climate_parameter = T("Climate Parameter"),
                           )

        tablename = "stats_parameter"
        super_entity(tablename, "parameter_id",
                     sp_types,
                     Field("name",
                           label = T("Name"),
                           ),
                     Field("description",
                           label = T("Description"),
                           ),
                     )
        # @todo: make lazy_table
        table = db[tablename]
        table.instance_type.readable = True

        # ---------------------------------------------------------------------
        # Super entity: stats_data
        #
        sd_types = Storage(disease_stats_data = T("Disease Data"),
                           org_resource = T("Organization Resource"),
                           project_beneficiary = T("Project Beneficiary"),
                           project_campaign_response_summary = T("Project Campaign Response Summary"),
                           stats_demographic_data = T("Demographic Data"),
                           stats_impact = T("Impact"),
                           # @ToDo: Deprecate
                           stats_people = T("People"),
                           supply_distribution = T("Distribution"),
                           vulnerability_data = T("Vulnerability Data"),
                           #survey_answer = T("Survey Answer"),
                           #climate_data = T("Climate Data"),
                           )

        tablename = "stats_data"
        super_entity(tablename, "data_id",
                     sd_types,
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     super_link("parameter_id", "stats_parameter"),
                     self.gis_location_id(
                        requires = IS_LOCATION(),
                        widget = S3LocationAutocompleteWidget(),
                     ),
                     Field("value", "double",
                           label = T("Value"),
                           #represent = lambda v: \
                           # IS_FLOAT_AMOUNT.represent(v, precision=2),
                           ),
                     # @ToDo: This will need to be a datetime for some usecases
                     s3_date(),
                     s3_date("end_date",
                             label = T("End Date"),
                             ),
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
        super_entity(tablename, "source_id", source_types,
                     Field("name",
                           label = T("Name"),
                           ),
                     )

        # For use by Instances or Components
        source_superlink = super_link("source_id", "stats_source")

        # For use by other FKs
        represent = stats_SourceRepresent(show_link = True)
        source_id = S3ReusableField("source_id", "reference %s" % tablename,
                                    label = T("Source"),
                                    represent = represent,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "stats_source.source_id",
                                                          represent,
                                                          sort=True)),
                                    )

        #self.add_components(tablename,
        #                    stats_source_details="source_id",
        #                   )

        # ---------------------------------------------------------------------
        # Stats Source Details
        #
        #tablename = "stats_source_details"
        #define_table(tablename,
        #             # Component
        #             source_superlink,
        #             #Field("reliability",
        #             #      label=T("Reliability")),
        #             #Field("review",
        #             #      label=T("Review")),
        #             )

        # Pass names back to global scope (s3.*)
        return dict(stats_source_superlink = source_superlink,
                    stats_source_id = source_id,
                    )

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults if module is disabled """

        return dict(
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

        @ToDo: Don't aggregate data for locations which don't exist in time window
    """

    names = ("stats_demographic",
             "stats_demographic_data",
             "stats_demographic_aggregate",
             "stats_demographic_rebuild_all_aggregates",
             "stats_demographic_update_aggregates",
             "stats_demographic_update_location_aggregate",
             )

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        location_id = self.gis_location_id

        stats_parameter_represent = S3Represent(lookup="stats_parameter",
                                                translate=True)

        # ---------------------------------------------------------------------
        # Demographic
        #
        tablename = "stats_demographic"
        define_table(tablename,
                     # Instance
                     super_link("parameter_id", "stats_parameter"),
                     Field("name",
                           label = T("Name"),
                           represent = lambda v: T(v) if v is not None \
                                                    else NONE,
                           ),
                     s3_comments("description",
                                 label = T("Description"),
                                 ),
                     # Link to the Demographic which is the Total, so that we can calculate percentages
                     Field("total_id", self.stats_parameter,
                           label = T("Total"),
                           represent = stats_parameter_represent,
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "stats_parameter.parameter_id",
                                                  stats_parameter_represent,
                                                  instance_types = ("stats_demographic",),
                                                  sort=True)),
                           ),
                     *s3_meta_fields()
                     )

        # CRUD Strings
        ADD_DEMOGRAPHIC = T("Add Demographic")
        crud_strings[tablename] = Storage(
            label_create = ADD_DEMOGRAPHIC,
            title_display = T("Demographic Details"),
            title_list = T("Demographics"),
            title_update = T("Edit Demographic"),
            #title_upload = T("Import Demographics"),
            label_list_button = T("List Demographics"),
            msg_record_created = T("Demographic added"),
            msg_record_modified = T("Demographic updated"),
            msg_record_deleted = T("Demographic deleted"),
            msg_list_empty = T("No demographics currently defined"))

        configure(tablename,
                  deduplicate = self.stats_demographic_duplicate,
                  requires_approval = True,
                  super_entity = "stats_parameter",
                  )

        # ---------------------------------------------------------------------
        # Demographic Data
        #
        tablename = "stats_demographic_data"
        define_table(tablename,
                     # Instance
                     super_link("data_id", "stats_data"),
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     super_link("parameter_id", "stats_parameter",
                                instance_types = ("stats_demographic",),
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
                         requires = IS_LOCATION(),
                         widget = S3LocationAutocompleteWidget(),
                     ),
                     Field("value", "double",
                           label = T("Value"),
                           represent = lambda v: \
                            IS_FLOAT_AMOUNT.represent(v, precision=2),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_date(empty = False),
                     Field("end_date", "date",
                           # Just used for the year() VF
                           readable = False,
                           writable = False
                           ),
                     Field("year", "list:integer",
                           compute = lambda row: \
                             stats_year(row, "stats_demographic_data"),
                           label = T("Year"),
                           ),
                     # Link to Source
                     self.stats_source_id(),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Demographic Data"),
            title_display = T("Demographic Data Details"),
            title_list = T("Demographic Data"),
            title_update = T("Edit Demographic Data"),
            title_upload = T("Import Demographic Data"),
            label_list_button = T("List Demographic Data"),
            msg_record_created = T("Demographic Data added"),
            msg_record_modified = T("Demographic Data updated"),
            msg_record_deleted = T("Demographic Data deleted"),
            msg_list_empty = T("No demographic data currently available"))

        levels = current.gis.get_relevant_hierarchy_levels()

        location_fields = ["location_id$%s" % level for level in levels]

        list_fields = ["parameter_id"]
        list_fields.extend(location_fields)
        list_fields.extend((("value",
                             "date",
                             "source_id",
                             )))

        filter_widgets = [S3OptionsFilter("parameter_id",
                                          label = T("Type"),
                                          multiple = False,
                                          # Not translateable
                                          #represent = "%(name)s",
                                          ),
                          S3OptionsFilter("year",
                                          #multiple = False,
                                          operator = "anyof",
                                          options = lambda: \
                                            stats_year_options("stats_demographic_data"),
                                          ),
                          S3OptionsFilter("location_id$level",
                                          label = T("Level"),
                                          multiple = False,
                                          # Not translateable
                                          #represent = "%(name)s",
                                          ),
                          S3LocationFilter("location_id",
                                           levels = levels,
                                           ),
                          ]

        report_options = Storage(rows = location_fields + ["year"],
                                 cols = ["parameter_id"],
                                 fact = [(T("Average"), "avg(value)"),
                                         (T("Total"), "sum(value)"),
                                         ],
                                 defaults = Storage(rows = location_fields[0], # => L0 for multi-country, L1 for single country
                                                    cols = "parameter_id",
                                                    fact = "sum(value)",
                                                    totals = True,
                                                    chart = "breakdown:rows",
                                                    table = "collapse",
                                                    )
                                 )

        configure(tablename,
                  deduplicate = self.stats_demographic_data_duplicate,
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  # @ToDo: Wrapper function to call this for the record linked
                  # to the relevant place depending on whether approval is
                  # required or not. Disable when auth.override is True.
                  #onaccept = self.stats_demographic_update_aggregates,
                  #onapprove = self.stats_demographic_update_aggregates,
                  report_options = report_options,
                  # @ToDo: deployment_setting
                  requires_approval = True,
                  super_entity = "stats_data",
                  # If using dis-aggregated data
                  #timeplot_options = {"defaults": {"event_start": "date",
                  #                                 "event_end": "end_date",
                  #                                 "fact": "cumulate(value)",
                  #                                 },
                  #                    },
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
        define_table(tablename,
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     super_link("parameter_id", "stats_parameter",
                                empty = False,
                                instance_types = ("stats_demographic",),
                                label = T("Demographic"),
                                represent = S3Represent(lookup="stats_parameter"),
                                readable = True,
                                writable = True,
                                ),
                     location_id(
                        requires = IS_LOCATION(),
                        widget = S3LocationAutocompleteWidget(),
                     ),
                     Field("agg_type", "integer",
                           default = 1,
                           label = T("Aggregation Type"),
                           represent = lambda opt: \
                            aggregate_types.get(opt,
                                                current.messages.UNKNOWN_OPT),
                           requires = IS_IN_SET(aggregate_types),
                           ),
                     s3_date("date",
                             label = T("Start Date"),
                             ),
                     s3_date("end_date",
                             label = T("End Date"),
                             ),
                     # Sum is used by Vulnerability as a fallback if we have no data at this level
                     Field("sum", "double",
                           label = T("Sum"),
                           represent = lambda v: \
                            IS_FLOAT_AMOUNT.represent(v, precision=2),
                           ),
                     # Percentage is used to compare an absolute value against a total
                     Field("percentage", "double",
                           label = T("Percentage"),
                           represent = lambda v: \
                            IS_FLOAT_AMOUNT.represent(v, precision=2),
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
        return dict(
            stats_demographic_rebuild_all_aggregates = self.stats_demographic_rebuild_all_aggregates,
            stats_demographic_update_aggregates = self.stats_demographic_update_aggregates,
            stats_demographic_update_location_aggregate = self.stats_demographic_update_location_aggregate,
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def stats_demographic_duplicate(item):
        """ Import item de-duplication """

        name = item.data.get("name")
        table = item.table
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

        data = item.data
        parameter_id = data.get("parameter_id")
        location_id = data.get("location_id")
        date = data.get("date")
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

        # Read all the approved stats_demographic_data records
        dtable = db.stats_demographic
        ddtable = db.stats_demographic_data
        query = (ddtable.deleted != True) & \
                (ddtable.parameter_id == dtable.parameter_id) & \
                (ddtable.approved_by != None)
        # @ToDo: deployment_setting for whether records need to be approved
        #   query &= (ddtable.approved_by != None)
        records = db(query).select(ddtable.data_id,
                                   ddtable.parameter_id,
                                   ddtable.date,
                                   ddtable.location_id,
                                   ddtable.value,
                                   dtable.total_id,
                                   )

        # Fire off a rebuild task
        current.s3task.async("stats_demographic_update_aggregates",
                             vars = dict(records=records.json()),
                             timeout = 21600 # 6 hours
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

        date = datetime.date
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
            This will calculate the stats_demographic_aggregates for the
            specified records. Either all (when rebuild_all is invoked) or for
            the individual parameter(s) at the specified location(s) when run
            onapprove - which currently happens inside the vulnerability
            approve_report() controller.
            @ToDo: onapprove/onaccept wrapper function for other workflows.

            This will get the raw data from stats_demographic_data and generate
            a stats_demographic_aggregate record for the given time period.

            The reason for doing this is so that all aggregated data can be
            obtained from a single table. So when displaying data for a
            particular location it will not be necessary to try the aggregate
            table, and if it's not there then try the data table. Rather just
            look at the aggregate table.

            Once this has run then a complete set of aggregate records should
            exists for this parameter_id and location for every time period from
            the first data item until the current time period.

            @ToDo: Add test cases to modules/unit_tests/s3db/stats.py
        """

        if not records:
            return

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
        if isinstance(records, basestring):
            from_json = True
            from dateutil.parser import parse
            records = json.loads(records)
        elif isinstance(records[0]["stats_demographic_data"]["date"],
                        (datetime.date, datetime.datetime)):
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
                current.log.warning("Skipping bad stats_demographic_data record with data_id %s " % data_id)
                continue
            if total_id and parameter_id not in param_total_dict:
                param_total_dict[parameter_id] = total_id
            if from_json:
                date = parse(record["date"]) # produces a datetime
                date = date.date()
            else:
                date = record["date"]
            (start_date, end_date) = aggregated_period(date)

            # Get all the approved stats_demographic_data records for this location and parameter
            query = (dtable.location_id == location_id) & \
                    (dtable.deleted != True) & \
                    (dtable.approved_by != None)
            # @ToDo: deployment_setting for whether records need to be approved
            #   query &= (dtable.approved_by != None)
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
        # @ToDo: Optimise by rewriting as custom routine rather than using this wrapper
        # - we only need immediate children not descendants, so can use parent not path
        # - look at disease_stats_update_aggregates()
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

        # Get all the child locations (immediate children only, not all descendants)
        child_locations = current.gis.get_children(location_id, location_level)
        child_ids = [row.id for row in child_locations]

        # Get the most recent stats_demographic_data record for all child locations
        query = (dtable.parameter_id == parameter_id) & \
                (dtable.deleted != True) & \
                (dtable.location_id.belongs(child_ids)) & \
                (dtable.approved_by != None)
        # @ToDo: deployment_setting for whether records need to be approved
        #   query &= (dtable.approved_by != None)
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
        #if total_id == "None": # converted to string as async parameter
        #    total_id = None

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
class S3StatsImpactModel(S3Model):
    """
        Used to record Impacts of Events &/or Incidents
        - might link to Assessments module in future
    """

    names = ("stats_impact",
             "stats_impact_type",
             "stats_impact_id",
             )

    def model(self):

        T = current.T

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Impact Types
        #
        tablename = "stats_impact_type"
        define_table(tablename,
                     # Instance
                     super_link("doc_id", "doc_entity"),
                     super_link("parameter_id", "stats_parameter"),
                     Field("name",
                           label = T("Name"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        ADD_IMPACT_TYPE = T("Add Impact Type")
        crud_strings[tablename] = Storage(
            label_create=ADD_IMPACT_TYPE,
            title_display=T("Impact Type Details"),
            title_list=T("Impact Types"),
            title_update=T("Edit Impact Type"),
            #title_upload=T("Import Impact Types"),
            label_list_button=T("Impact Types"),
            label_delete_button=T("Delete Impact Type"),
            msg_record_created=T("Impact Type added"),
            msg_record_modified=T("Impact Type updated"),
            msg_record_deleted=T("Impact Type deleted"),
            msg_list_empty=T("No Impact Types defined"))

        # Resource Configuration
        configure(tablename,
                  deduplicate = self.stats_impact_type_duplicate,
                  super_entity = ("doc_entity", "stats_parameter"),
                  )

        represent = S3Represent(lookup=tablename)

        # ---------------------------------------------------------------------
        # Impact
        #
        tablename = "stats_impact"
        define_table(tablename,
                     # Instance
                     super_link("data_id", "stats_data"),
                     # Instance (link to Photos/Reports)
                     super_link("doc_id", "doc_entity"),
                     Field("name", #notnull=True,
                           label = T("Name"),
                           ),
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     super_link("parameter_id", "stats_parameter",
                                label = T("Impact Type"),
                                instance_types = ("stats_impact_type",),
                                represent = S3Represent(lookup="stats_parameter"),
                                readable = True,
                                writable = True,
                                empty = False,
                                comment = S3AddResourceLink(c="stats",
                                                            f="impact_type",
                                                            vars = dict(child = "parameter_id"),
                                                            title=ADD_IMPACT_TYPE),
                                ),
                     Field("value", "double",
                           label = T("Value"),
                           represent = lambda v: \
                            IS_FLOAT_AMOUNT.represent(v, precision=2),
                           requires = IS_NOT_EMPTY(),
                           ),
                     #self.gis_location_id(),
                     s3_comments(),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create=T("Add Impact"),
            title_display=T("Impact Details"),
            title_list=T("Impacts"),
            title_update=T("Edit Impact"),
            title_upload=T("Import Impacts"),
            label_list_button=T("Impacts"),
            label_delete_button=T("Delete Impact"),
            msg_record_created=T("Impact added"),
            msg_record_modified=T("Impact updated"),
            msg_record_deleted=T("Impact deleted"),
            msg_list_empty=T("No Impacts defined"))

        filter_widgets = [S3OptionsFilter("parameter_id",
                                          label = T("Type"),
                                          # Doesn't support Translation
                                          #represent = "%(name)s",
                                          ),
                          ]

        # Reusable Field
        impact_id = S3ReusableField("impact_id", "reference %s" % tablename,
                                     label = T("Impact"),
                                     requires = IS_EMPTY_OR(
                                        IS_ONE_OF_EMPTY(db, "stats_impact.id")),
                                     represent = S3Represent(lookup=tablename),
                                     ondelete = "CASCADE")

        configure(tablename,
                  filter_widgets = filter_widgets,
                  super_entity = ("doc_entity", "stats_data"),
                  )

        # Pass names back to global scope (s3.*)
        return dict(stats_impact_id = impact_id,
                    )

    # ---------------------------------------------------------------------
    @staticmethod
    def stats_impact_type_duplicate(item):
        """
            Deduplication of Impact Type
        """

        name = item.data.get("name", None)
        if not name:
            return

        table = item.table
        query = (table.name.lower() == name.lower())
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

# =============================================================================
class S3StatsPeopleModel(S3Model):
    """
        Used to record people in the CRMT (Community Resilience Mapping Tool) template

        @ToDo: Deprecate
    """

    names = ("stats_people",
             "stats_people_type",
             "stats_people_group",
             )

    def model(self):

        T = current.T

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Type of Peoples
        #
        tablename = "stats_people_type"
        define_table(tablename,
                     # Instance
                     super_link("doc_id", "doc_entity"),
                     super_link("parameter_id", "stats_parameter"),
                     Field("name",
                           label = T("Name"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        ADD_PEOPLE_TYPE = T("Add Type of People")
        crud_strings[tablename] = Storage(
            label_create=ADD_PEOPLE_TYPE,
            title_display=T("Type of People Details"),
            title_list=T("Type of Peoples"),
            title_update=T("Edit Type of People"),
            #title_upload=T("Import Type of Peoples"),
            label_list_button=T("Type of Peoples"),
            label_delete_button=T("Delete Type of People"),
            msg_record_created=T("Type of People added"),
            msg_record_modified=T("Type of People updated"),
            msg_record_deleted=T("Type of People deleted"),
            msg_list_empty=T("No Type of Peoples defined"))

        # Resource Configuration
        configure(tablename,
                  deduplicate = self.stats_people_type_duplicate,
                  super_entity = ("doc_entity", "stats_parameter"),
                  )

        represent = S3Represent(lookup=tablename)

        # ---------------------------------------------------------------------
        # People
        #
        tablename = "stats_people"
        define_table(tablename,
                     # Instance
                     super_link("data_id", "stats_data"),
                     # Instance (link to Photos)
                     super_link("doc_id", "doc_entity"),
                     Field("name", #notnull=True,
                           label = T("Name"),
                           ),
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     super_link("parameter_id", "stats_parameter",
                                label = T("Type of People"),
                                instance_types = ("stats_people_type",),
                                represent = S3Represent(lookup="stats_parameter"),
                                readable = True,
                                writable = True,
                                empty = False,
                                comment = S3AddResourceLink(c="stats",
                                                            f="people_type",
                                                            vars = dict(child = "parameter_id"),
                                                            title=ADD_PEOPLE_TYPE),
                                ),
                     Field("value", "integer",
                           label = T("Number of People"),
                           represent = IS_INT_AMOUNT.represent,
                           requires = IS_INT_IN_RANGE(0, 999999),
                           ),
                     self.gis_location_id(label = T("Address"),
                                          ),
                     self.pr_person_id(label = T("Contact Person"),
                                       requires = IS_ADD_PERSON_WIDGET2(allow_empty=True),
                                       widget = S3AddPersonWidget2(controller="pr"),
                                       ),
                     s3_comments(),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create=T("Add People"),
            title_display=T("People Details"),
            title_list=T("People"),
            title_update=T("Edit People"),
            title_upload=T("Import People"),
            label_list_button=T("People"),
            label_delete_button=T("Delete People"),
            msg_record_created=T("People added"),
            msg_record_modified=T("People updated"),
            msg_record_deleted=T("People deleted"),
            msg_list_empty=T("No People defined"))

        filter_widgets = [S3OptionsFilter("people_group.group_id",
                                          label = T("Coalition"),
                                          represent = "%(name)s",
                                          ),
                          S3OptionsFilter("parameter_id",
                                          label = T("Type"),
                                          # Doesn't support Translation
                                          #represent = "%(name)s",
                                          ),
                          ]

        configure(tablename,
                  filter_widgets = filter_widgets,
                  super_entity = ("doc_entity", "stats_data"),
                  )

        # Components
        self.add_components(tablename,
                            # Coalitions
                            org_group = {"link": "stats_people_group",
                                         "joinby": "people_id",
                                         "key": "group_id",
                                         "actuate": "hide",
                                         },
                            # Format for InlineComponent/filter_widget
                            stats_people_group = "people_id",
                            )

        represent = S3Represent(lookup=tablename)

        # ---------------------------------------------------------------------
        # People <> Coalitions link table
        #
        tablename = "stats_people_group"
        define_table(tablename,
                     Field("people_id", "reference stats_people",
                           requires = IS_ONE_OF(current.db, "stats_people.id",
                                                represent,
                                                sort=True,
                                                ),
                           represent = represent,
                           ),
                     self.org_group_id(empty=False),
                     *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return dict()

    # ---------------------------------------------------------------------
    @staticmethod
    def stats_people_type_duplicate(item):
        """
            Deduplication of Type of Peoples
        """

        name = item.data.get("name", None)
        if not name:
            return

        table = item.table
        query = (table.name.lower() == name.lower())
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

# =============================================================================
def stats_quantile(data, q):
    """
        Return the specified quantile(s) q of the supplied list.
        The function can be called with either a single value for q or a
        list of values. In the latter case, the returned value is a tuple.
    """

    sx = sorted(data)
    def get_quantile(q1):
        pos = (len(sx) - 1) * q1
        if abs(pos - int(pos) - 0.5) < 0.1:
            # quantile in the middle between two values, average them
            return (sx[int(pos)] + sx[int(pos) + 1]) * 0.5
        else:
            # otherwise return the nearest value
            return sx[int(pos + 0.5)]

    if hasattr(q, "__iter__"):
        return tuple([get_quantile(qi) for qi in q])
    else:
        return get_quantile(q)

# =============================================================================
def stats_year(row, tablename):
    """
        Function to calculate computed field for stats_data
        - returns the year of this entry

        @param row: a dict of the Row
    """

    NOT_PRESENT = lambda: None

    try:
        start_date = row["date"]
    except AttributeError:
        start_date = NOT_PRESENT
    try:
        end_date = row["end_date"]
    except AttributeError:
        end_date = NOT_PRESENT

    if start_date is NOT_PRESENT or end_date is NOT_PRESENT:
        if tablename == "project_beneficiary":
            # Fallback to the Project's
            try:
                project_id = row["project_id"]
            except KeyError:
                pass
            else:
                table = current.s3db.project_project
                project = current.db(table.id == project_id).select(table.start_date,
                                                                    table.end_date,
                                                                    limitby=(0, 1)
                                                                    ).first()
                if project:
                    if start_date is NOT_PRESENT:
                        start_date = project.start_date
                    if end_date is NOT_PRESENT:
                        end_date = project.end_date


    if start_date is NOT_PRESENT and end_date is NOT_PRESENT:
        # Partial record update without dates => let it fail so
        # we do not override the existing value
        raise AttributeError("no data available")

    if not start_date and not end_date:
        return []
    elif end_date is NOT_PRESENT or not end_date:
        return [start_date.year]
    elif start_date is NOT_PRESENT or not start_date :
        return [end_date.year]
    else:
        return list(xrange(start_date.year, end_date.year + 1))

# =============================================================================
def stats_year_options(tablename):
    """
        returns a dict of the options for the year computed field
        used by the filter widget

        orderby needed for postgres
    """

    db = current.db
    s3db = current.s3db
    table = s3db[tablename]
    # @ToDo: use auth.s3_accessible_query
    query = (table.deleted == False)
    min_field = table.date.min()
    start_date_min = db(query).select(min_field,
                                      orderby=min_field,
                                      limitby=(0, 1)).first()[min_field]
    max_field = table.end_date.max()
    end_date_max = db(query).select(max_field,
                                    orderby=max_field,
                                    limitby=(0, 1)).first()[max_field]

    if tablename == "project_beneficiary":
        # Use the Project's Years as well, as the dates may not be filled in the project_beneficiary table
        ptable = s3db.project_project
        pquery = (ptable.deleted == False)
        pmin = ptable.start_date.min()
        pmax = ptable.end_date.max()
        p_start_date_min = db(pquery).select(pmin,
                                             orderby=pmin,
                                             limitby=(0, 1)).first()[pmin]
        p_end_date_max = db(pquery).select(pmax,
                                           orderby=pmax,
                                           limitby=(0, 1)).first()[pmax]
        if p_start_date_min and start_date_min:
            start_year = min(p_start_date_min,
                             start_date_min).year
        else:
            start_year = (p_start_date_min and p_start_date_min.year) or \
                         (start_date_min and start_date_min.year)
        if p_end_date_max and end_date_max:
            end_year = max(p_end_date_max,
                           end_date_max).year
        else:
            end_year = (p_end_date_max and p_end_date_max.year) or \
                       (end_date_max and end_date_max.year)

    else:
        start_year = start_date_min and start_date_min.year
        end_year = end_date_max and end_date_max.year

    if not start_year or not end_year:
        return {start_year:start_year} or {end_year:end_year}
    years = {}
    for year in xrange(start_year, end_year + 1):
        years[year] = year
    return years

# =============================================================================
class stats_SourceRepresent(S3Represent):
    """ Representation of Stats Sources """

    def __init__(self,
                 translate = False,
                 show_link = False,
                 multiple = False,
                 ):

        if show_link:
            # Need a custom lookup
            self.lookup_rows = self.custom_lookup_rows
        # Need a custom representation
        fields = ["name"]

        super(stats_SourceRepresent,
              self).__init__(lookup="stats_source",
                             fields=fields,
                             show_link=show_link,
                             translate=translate,
                             multiple=multiple)

    # -------------------------------------------------------------------------
    def bulk(self, values, rows=None, list_type=False, show_link=True, include_blank=True):
        """
            Represent multiple values as dict {value: representation}

            @param values: list of values
            @param rows: the referenced rows (if values are foreign keys)
            @param show_link: render each representation as link
            @param include_blank: Also include a blank value

            @return: a dict {value: representation}
        """

        show_link = show_link and self.show_link
        if show_link and not rows:
            # Retrieve the rows
            rows = self.custom_lookup_rows(None, values)

        self._setup()

        # Get the values
        if rows and self.table:
            values = [row["stats_source.source_id"] for row in rows]
        else:
            values = [values] if type(values) is not list else values

        # Lookup the representations
        if values:
            labels = self._lookup(values, rows=rows)
            if show_link:
                link = self.link
                rows = self.rows
                labels = dict((k, link(k, v, rows.get(k)))
                               for k, v in labels.items())
            for v in values:
                if v not in labels:
                    labels[v] = self.default
        else:
            labels = {}
        if include_blank:
            labels[None] = self.none
        return labels

    # -------------------------------------------------------------------------
    def custom_lookup_rows(self, key, values, fields=[]):
        """
            Custom lookup method for site rows, does a
            left join with any instance_types found. Parameters
            key and fields are not used, but are kept for API
            compatibility reasons.

            @param values: the site IDs
        """

        db = current.db
        s3db = current.s3db
        stable = s3db.stats_source

        qty = len(values)
        if qty == 1:
            query = (stable.id == values[0])
            limitby = (0, 1)
        else:
            query = (stable.id.belongs(values))
            limitby = (0, qty)

        if self.show_link:
            # We need the instance_type IDs
            # Do a first query to see which instance_types we have
            rows = db(query).select(stable.instance_type,
                                    limitby=limitby)
            instance_types = []
            for row in rows:
                if row.instance_type not in instance_types:
                    instance_types.append(row.instance_type)

            # Now do a second query which left-joins with all the instance tables we have
            fields = [stable.source_id,
                      stable.name,
                      ]
            left = []
            for instance_type in instance_types:
                table = s3db[instance_type]
                fields.append(table.id)
                left.append(table.on(table.source_id == stable.source_id))
                if instance_type == "doc_document":
                    # We need the URL
                    fields.append(table.url)

            rows = db(query).select(*fields,
                                    left=left,
                                    limitby=limitby)

        else:
            # Normal lookup
            rows = db(query).select(stable.source_id,
                                    stable.name,
                                    limitby=limitby)

        self.queries += 1
        return rows

    # -------------------------------------------------------------------------
    def link(self, k, v, row=None):
        """
            Represent a (key, value) as hypertext link.

            @param k: the key (site_id)
            @param v: the representation of the key
            @param row: the row with this key
        """

        if row:
            try:
                url = row["doc_document.url"]
            except AttributeError:
                return v
            else:
                if url:
                    return A(v, _href=url, _target="blank")

        # We have no way to determine the linkto
        return v

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a single Row

            @param row: the org_site Row
        """

        name = row["stats_source.name"]
        if not name:
            return self.default

        return s3_unicode(name)

# END =========================================================================
