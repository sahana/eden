# -*- coding: utf-8 -*-
#
# Stats Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/eden/stats.py
#
import unittest
import datetime

from gluon import *
from gluon.storage import Storage

# =============================================================================
# Stats_aggregate takes too long to test on a populated database
@unittest.skip("Comment or remove this line in modules/unit_tests/eden/stats.py to activate this test")
@unittest.skipIf(not current.deployment_settings.has_module("vulnerability"),
                 "Vulnerability module deactivated")
class StatsTests(unittest.TestCase):
    """ Stats Tests """

    def setUp(self):
        """ Set up location records """
        auth = current.auth
        auth.s3_impersonate("admin@example.com")

        self.location_code = Storage()
        self.location_ids = Storage()
        s3db = current.s3db

        gtable = s3db.gis_location

        gis0 = Storage(name="Test Country",
                       level="L0",
                       )
        gis0_id = gtable.insert(**gis0)
        self.location_code[gis0_id] = "gis0"
        self.location_ids["gis0"] = gis0_id

        # Tests location data, code, name, level, parent
        gis_test_data = [("gis1", "Test Region 1", "L1", "gis0"),
                         ("gis2_1", "Test Province 1", "L2", "gis1"),
                         ("gis2_2", "Test Province 2", "L2", "gis1"),
                         ("gis3_1", "Test District 1", "L3", "gis2_1"),
                         ("gis3_2", "Test District 2", "L3", "gis2_1"),
                         ("gis3_3", "Test District 3", "L3", "gis2_1"),
                         ("gis3_4", "Test District 4", "L3", "gis2_2"),
                         ("gis3_5", "Test District 5", "L3", "gis2_2"),
                         ("gis4_1", "Test Commune 1", "L4", "gis3_1"),
                         ("gis4_2", "Test Commune 2", "L4", "gis3_1"),
                         ("gis4_3", "Test Commune 3", "L4", "gis3_1"),
                         ("gis4_4", "Test Commune 4", "L4", "gis3_2"),
                         ("gis4_5", "Test Commune 5", "L4", "gis3_2"),
                         ("gis4_6", "Test Commune 6", "L4", "gis3_3"),
                         ("gis4_7", "Test Commune 7", "L4", "gis3_3"),
                         ("gis4_8", "Test Commune 8", "L4", "gis3_3"),
                         ("gis4_9", "Test Commune 9", "L4", "gis3_4"),
                         ("gis4_10", "Test Commune 10", "L4", "gis3_4"),
                         ("gis4_11", "Test Commune 11", "L4", "gis3_5"),
                         ("gis4_12", "Test Commune 12", "L4", "gis3_5"),
                         ]
        update_location_tree = current.gis.update_location_tree
        for location in gis_test_data:
            gis_code = location[0]
            gis_data = Storage(name=location[1],
                               level=location[2],
                               parent=self.location_ids[location[3]],
                               )
            gis_id = gtable.insert(**gis_data)
            update_location_tree(dict(id=gis_id,
                                                  level=location[2]))
            self.location_code[gis_id] = gis_code
            self.location_ids[gis_code] = gis_id

        self.indicators = s3db.vulnerability_ids()
        self.statisticList = ["max",
                              "min",
                              "mean",
                              "median",
                              "reported_count",
                              "ward_count"
                              ]
        param_table = s3db.vulnerability_aggregated_indicator
        query = (param_table.uuid == "Resilience") & \
                (param_table.deleted == False)
        row = current.db(query).select(param_table.parameter_id,
                                       limitby=(0, 1)).first()
        self.resilience_id = row.parameter_id

    def approve_record(self, record):
        """
            Helper function to approve the vulnerability indicator and the
            Stats_data reciord that has been inserted

            @param record: the vulnerability indicator record just created
        """
        s3db = current.s3db
        resource = s3db.resource("vulnerability_data", id=record.id, unapproved=True)
        resource.approve()
        resource = s3db.resource("stats_data", id=record.data_id, unapproved=True)
        resource.approve()
        s3db.stats_update_time_aggregate(resource.select())

    def testStats_aggregate(self):
        """
            Test that the stats_aggregate records are being generated correctly.
            Because the stats_aggregate records depend on earlier results it is
            important that all these test are in the same test so that the
            interdependence of the indicators can be checked.

            Summary of test:
            1) Indicator 1 for gis4_1 in 2006 = 3
            2) Indicator 2 for gis4_1 in 2006 = 4
            3) Indicator 1 for gis4_1 in 2009 = 5
            4) Indicator 1 for gis4_2 in 2010 = 2
            5) Indicator 1 for gis4_2 in 2008 = 3
            6) Indicator 1 for gis4_2 in 2009 = 1
        """

        from datetime import date
        s3db = current.s3db
        db = current.db

        vtable = s3db.vulnerability_data

        #---------------------------------------------------------------------
        # Add a vulnerability record for indicator 1 with date in 2006 for gis4_1
        indicator_id = self.indicators[0]
        location_id = self.location_ids["gis4_1"]
        actual_date = date(2006,05,12)

        id = vtable.insert(parameter_id = indicator_id,
                           location_id = location_id,
                           value = 3,
                           date = actual_date,
                           )
        s3db.update_super(vtable, dict(id=id))
        self.approve_record(vtable[id])

        expected = Storage()
        expected["rule1"] = Storage(type={date(2006,01,1):1,
                                          date(2007,01,1):3
                                          },
                                    data={date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 1
                                                           },
                                          }
                                    )
        expected["rule2"] = Storage(
                                    data={self.location_ids["gis3_1"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 3
                                                           },
                                                                       },
                                          self.location_ids["gis2_1"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 8
                                                           },
                                                                       },
                                          self.location_ids["gis1"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          self.location_ids["gis0"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          },
                                    )
        expected["rule3"] = Storage(
                                    data={self.location_ids["gis4_1"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 1
                                                           },
                                                                       },
                                          self.location_ids["gis3_1"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 3
                                                           },
                                                                       },
                                          self.location_ids["gis2_1"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 8
                                                           },
                                                                       },
                                          self.location_ids["gis1"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          self.location_ids["gis0"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          },
                                    )
        self.validateAggregateData(actual_date,
                                   indicator_id,
                                   location_id,
                                   expected,
                                   )

        #---------------------------------------------------------------------
        # Add a vulnerability record for indicator 2 with date in 2006 for gis4_1
        indicator_id = self.indicators[1]
        location_id = self.location_ids["gis4_1"]
        actual_date = date(2006,05,12)

        id = vtable.insert(parameter_id = indicator_id,
                           location_id = location_id,
                           value = 4,
                           date = actual_date,
                           )
        s3db.update_super(vtable, dict(id=id))
        self.approve_record(vtable[id])

        expected = Storage()
        expected["rule1"] = Storage(type={date(2006,01,1):1,
                                          date(2007,01,1):3
                                          },
                                    data={date(2006,01,1):{"max" : 4,
                                                           "min" : 4,
                                                           "mean": 4,
                                                           "median":4,
                                                           "reported_count": 1,
                                                           "ward_count": 1
                                                           },
                                          date(2007,01,1):{"max" : 4,
                                                           "min" : 4,
                                                           "mean": 4,
                                                           "median":4,
                                                           "reported_count": 1,
                                                           "ward_count": 1
                                                           },
                                          }
                                    )
        expected["rule2"] = Storage(
                                    data={self.location_ids["gis3_1"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 4,
                                                           "mean": 4,
                                                           "median":4,
                                                           "reported_count": 1,
                                                           "ward_count": 3
                                                           },
                                                                       },
                                          self.location_ids["gis2_1"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 4,
                                                           "mean": 4,
                                                           "median":4,
                                                           "reported_count": 1,
                                                           "ward_count": 8
                                                           },
                                                                       },
                                          self.location_ids["gis1"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 4,
                                                           "mean": 4,
                                                           "median":4,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          self.location_ids["gis0"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 4,
                                                           "mean": 4,
                                                           "median":4,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          },
                                    )
        expected["rule3"] = Storage(
                                    data={self.location_ids["gis4_1"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 1
                                                           },
                                                                       },
                                          self.location_ids["gis3_1"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 3
                                                           },
                                                                       },
                                          self.location_ids["gis2_1"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 8
                                                           },
                                                                       },
                                          self.location_ids["gis1"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          self.location_ids["gis0"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          },
                                    )
        self.validateAggregateData(actual_date,
                                   indicator_id,
                                   location_id,
                                   expected,
                                   )

        #---------------------------------------------------------------------
        # Add a vulnerability record for indicator 1 with date in 2009 for gis4_1
        indicator_id = self.indicators[0]
        location_id = self.location_ids["gis4_1"]
        actual_date = date(2009,07,23)

        id = vtable.insert(parameter_id = indicator_id,
                           location_id = location_id,
                           value = 5,
                           date = actual_date,
                           )
        s3db.update_super(vtable, dict(id=id))
        self.approve_record(vtable[id])

        expected = Storage()
        expected["rule1"] = Storage(type={date(2006,01,1):1,
                                          date(2007,01,1):3,
                                          date(2009,01,1):1,
                                          date(2010,01,1):3,
                                          },
                                    data={date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 1
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 5,
                                                           "mean": 5,
                                                           "median":5,
                                                           "reported_count": 1,
                                                           "ward_count": 1
                                                           },
                                          }
                                    )
        expected["rule2"] = Storage(
                                    data={self.location_ids["gis3_1"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 3
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 5,
                                                           "mean": 5,
                                                           "median":5,
                                                           "reported_count": 1,
                                                           "ward_count": 3
                                                           },
                                                                       },
                                          self.location_ids["gis2_1"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 8
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 5,
                                                           "mean": 5,
                                                           "median":5,
                                                           "reported_count": 1,
                                                           "ward_count": 8
                                                           },
                                                                       },
                                          self.location_ids["gis1"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 5,
                                                           "mean": 5,
                                                           "median":5,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          self.location_ids["gis0"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 5,
                                                           "mean": 5,
                                                           "median":5,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          },
                                    )
        expected["rule3"] = Storage(
                                    data={self.location_ids["gis4_1"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 1
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 4,
                                                           "mean": 4.5,
                                                           "median":4.5,
                                                           "reported_count": 1,
                                                           "ward_count": 1
                                                           },
                                                                       },
                                          self.location_ids["gis3_1"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 3
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 4,
                                                           "mean": 4.5,
                                                           "median":4.5,
                                                           "reported_count": 1,
                                                           "ward_count": 3
                                                           },
                                                                       },
                                          self.location_ids["gis2_1"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 8
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 4,
                                                           "mean": 4.5,
                                                           "median":4.5,
                                                           "reported_count": 1,
                                                           "ward_count": 8
                                                           },
                                                                       },
                                          self.location_ids["gis1"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 4,
                                                           "mean": 4.5,
                                                           "median":4.5,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          self.location_ids["gis0"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 4,
                                                           "mean": 4.5,
                                                           "median":4.5,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          },
                                    )
        self.validateAggregateData(actual_date,
                                   indicator_id,
                                   location_id,
                                   expected,
                                   )
        #---------------------------------------------------------------------
        # Add a vulnerability record for indicator 1 with date in 2010 for gis4_2
        indicator_id = self.indicators[0]
        location_id = self.location_ids["gis4_2"]
        actual_date = date(2010,03,13)

        id = vtable.insert(parameter_id = indicator_id,
                           location_id = location_id,
                           value = 2,
                           date = actual_date,
                           )
        s3db.update_super(vtable, dict(id=id))
        self.approve_record(vtable[id])

        expected = Storage()
        expected["rule1"] = Storage(type={date(2010,01,1):1,
                                          date(2011,01,1):3,
                                          },
                                    data={date(2010,01,1):{"max" : 2,
                                                           "min" : 2,
                                                           "mean": 2,
                                                           "median":2,
                                                           "reported_count": 1,
                                                           "ward_count": 1
                                                           },
                                          }
                                    )
        expected["rule2"] = Storage(
                                    data={self.location_ids["gis3_1"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 3
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 5,
                                                           "mean": 5,
                                                           "median":5,
                                                           "reported_count": 1,
                                                           "ward_count": 3
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 2,
                                                           "ward_count": 3
                                                           },
                                                                       },
                                          self.location_ids["gis2_1"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 8
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 5,
                                                           "mean": 5,
                                                           "median":5,
                                                           "reported_count": 1,
                                                           "ward_count": 8
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 2,
                                                           "ward_count": 8
                                                           },
                                                                       },
                                          self.location_ids["gis1"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 5,
                                                           "mean": 5,
                                                           "median":5,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          self.location_ids["gis0"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 5,
                                                           "mean": 5,
                                                           "median":5,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          },
                                    )
        expected["rule3"] = Storage(
                                    data={self.location_ids["gis4_2"]:{
                                          date(2010,01,1):{"max" : 2,
                                                           "min" : 2,
                                                           "mean": 2,
                                                           "median":2,
                                                           "reported_count": 1,
                                                           "ward_count": 1
                                                           },
                                                                       },
                                          self.location_ids["gis3_1"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 3
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 4,
                                                           "mean": 4.5,
                                                           "median":4.5,
                                                           "reported_count": 1,
                                                           "ward_count": 3
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 11.0/3,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 3
                                                           },
                                                                       },
                                          self.location_ids["gis2_1"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 8
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 4,
                                                           "mean": 4.5,
                                                           "median":4.5,
                                                           "reported_count": 1,
                                                           "ward_count": 8
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 11.0/3,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 8
                                                           },
                                                                       },
                                          self.location_ids["gis1"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 4,
                                                           "mean": 4.5,
                                                           "median":4.5,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 11.0/3,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          self.location_ids["gis0"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 4,
                                                           "mean": 4.5,
                                                           "median":4.5,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 11.0/3,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          },
                                    )
        self.validateAggregateData(actual_date,
                                   indicator_id,
                                   location_id,
                                   expected,
                                   )


        #---------------------------------------------------------------------
        # Add a vulnerability record for indicator 1 with date in 2008 for gis4_2
        indicator_id = self.indicators[0]
        location_id = self.location_ids["gis4_2"]
        actual_date = date(2008,02,05)

        id = vtable.insert(parameter_id = indicator_id,
                           location_id = location_id,
                           value = 3,
                           date = actual_date,
                           )
        s3db.update_super(vtable, dict(id=id))
        self.approve_record(vtable[id])

        expected = Storage()
        expected["rule1"] = Storage(type={date(2008,01,1):1,
                                          date(2009,01,1):3,
                                          date(2010,01,1):1,
                                          date(2011,01,1):3,
                                          },
                                    data={date(2008,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 1
                                                           },
                                          date(2010,01,1):{"max" : 2,
                                                           "min" : 2,
                                                           "mean": 2,
                                                           "median":2,
                                                           "reported_count": 1,
                                                           "ward_count": 1
                                                           },
                                          }
                                    )
        expected["rule2"] = Storage(
                                    data={self.location_ids["gis3_1"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 3
                                                           },
                                          date(2008,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 2,
                                                           "ward_count": 3
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 3,
                                                           "mean": 4,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 3
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 2,
                                                           "ward_count": 3
                                                           },
                                                                       },
                                          self.location_ids["gis2_1"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 8
                                                           },
                                          date(2008,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 2,
                                                           "ward_count": 8
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 3,
                                                           "mean": 4,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 8
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 2,
                                                           "ward_count": 8
                                                           },
                                                                       },
                                          self.location_ids["gis1"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                          date(2008,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 3,
                                                           "mean": 4,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          self.location_ids["gis0"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                          date(2008,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 3,
                                                           "mean": 4,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          },
                                    )
        expected["rule3"] = Storage(
                                    data={self.location_ids["gis4_2"]:{
                                          date(2008,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 1
                                                           },
                                          date(2010,01,1):{"max" : 2,
                                                           "min" : 2,
                                                           "mean": 2,
                                                           "median":2,
                                                           "reported_count": 1,
                                                           "ward_count": 1
                                                           },
                                                                       },
                                          self.location_ids["gis3_1"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 3
                                                           },
                                          date(2008,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 10.0/3,
                                                           "median":3,
                                                           "reported_count": 2,
                                                           "ward_count": 3
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 3,
                                                           "mean": 4,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 3
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 11.0/3,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 3
                                                           },
                                                                       },
                                          self.location_ids["gis2_1"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 8
                                                           },
                                          date(2008,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 10.0/3,
                                                           "median":3,
                                                           "reported_count": 2,
                                                           "ward_count": 8
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 3,
                                                           "mean": 4,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 8
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 11.0/3,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 8
                                                           },
                                                                       },
                                          self.location_ids["gis1"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                          date(2008,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 10.0/3,
                                                           "median":3,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 3,
                                                           "mean": 4,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 11.0/3,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          self.location_ids["gis0"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                          date(2008,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 10.0/3,
                                                           "median":3,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 3,
                                                           "mean": 4,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 11.0/3,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          },
                                    )
        self.validateAggregateData(actual_date,
                                   indicator_id,
                                   location_id,
                                   expected,
                                   )

        #---------------------------------------------------------------------
        # Add a vulnerability record for indicator 1 with date in 2009 for gis4_2
        indicator_id = self.indicators[0]
        location_id = self.location_ids["gis4_2"]
        actual_date = date(2009,12,05)

        id = vtable.insert(parameter_id = indicator_id,
                           location_id = location_id,
                           value = 1,
                           date = actual_date,
                           )
        s3db.update_super(vtable, dict(id=id))
        self.approve_record(vtable[id])

        expected = Storage()
        expected["rule1"] = Storage(type={date(2008,01,1):1,
                                          date(2009,01,1):1,
                                          date(2010,01,1):1,
                                          date(2011,01,1):3,
                                          },
                                    data={date(2008,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 1
                                                           },
                                          date(2009,01,1):{"max" : 1,
                                                           "min" : 1,
                                                           "mean": 1,
                                                           "median":1,
                                                           "reported_count": 1,
                                                           "ward_count": 1
                                                           },
                                          date(2010,01,1):{"max" : 2,
                                                           "min" : 2,
                                                           "mean": 2,
                                                           "median":2,
                                                           "reported_count": 1,
                                                           "ward_count": 1
                                                           },
                                          }
                                    )
        expected["rule2"] = Storage(
                                    data={self.location_ids["gis3_1"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 3
                                                           },
                                          date(2008,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 2,
                                                           "ward_count": 3
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 1,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 2,
                                                           "ward_count": 3
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 2,
                                                           "ward_count": 3
                                                           },
                                                                       },
                                          self.location_ids["gis2_1"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 8
                                                           },
                                          date(2008,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 2,
                                                           "ward_count": 8
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 1,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 2,
                                                           "ward_count": 8
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 2,
                                                           "ward_count": 8
                                                           },
                                                                       },
                                          self.location_ids["gis1"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                          date(2008,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 1,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          self.location_ids["gis0"]:{
                                          date(2006,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                          date(2008,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 1,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          },
                                    )
        expected["rule3"] = Storage(
                                    data={self.location_ids["gis4_2"]:{
                                          date(2008,01,1):{"max" : 3,
                                                           "min" : 3,
                                                           "mean": 3,
                                                           "median":3,
                                                           "reported_count": 1,
                                                           "ward_count": 1
                                                           },
                                          date(2009,01,1):{"max" : 1,
                                                           "min" : 1,
                                                           "mean": 1,
                                                           "median":1,
                                                           "reported_count": 1,
                                                           "ward_count": 1
                                                           },
                                          date(2010,01,1):{"max" : 2,
                                                           "min" : 2,
                                                           "mean": 2,
                                                           "median":2,
                                                           "reported_count": 1,
                                                           "ward_count": 1
                                                           },
                                                                       },
                                          self.location_ids["gis3_1"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 3
                                                           },
                                          date(2008,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 10.0/3,
                                                           "median":3,
                                                           "reported_count": 2,
                                                           "ward_count": 3
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 1,
                                                           "mean": 10.0/3,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 3
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 11.0/3,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 3
                                                           },
                                                                       },
                                          self.location_ids["gis2_1"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 8
                                                           },
                                          date(2008,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 10.0/3,
                                                           "median":3,
                                                           "reported_count": 2,
                                                           "ward_count": 8
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 1,
                                                           "mean": 10.0/3,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 8
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 11.0/3,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 8
                                                           },
                                                                       },
                                          self.location_ids["gis1"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                          date(2008,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 10.0/3,
                                                           "median":3,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 1,
                                                           "mean": 10.0/3,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 11.0/3,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          self.location_ids["gis0"]:{
                                          date(2006,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 3.5,
                                                           "median":3.5,
                                                           "reported_count": 1,
                                                           "ward_count": 12
                                                           },
                                          date(2008,01,1):{"max" : 4,
                                                           "min" : 3,
                                                           "mean": 10.0/3,
                                                           "median":3,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                          date(2009,01,1):{"max" : 5,
                                                           "min" : 1,
                                                           "mean": 10.0/3,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                          date(2010,01,1):{"max" : 5,
                                                           "min" : 2,
                                                           "mean": 11.0/3,
                                                           "median":4,
                                                           "reported_count": 2,
                                                           "ward_count": 12
                                                           },
                                                                       },
                                          },
                                    )
        self.validateAggregateData(actual_date,
                                   indicator_id,
                                   location_id,
                                   expected,
                                   )

        #---------------------------------------------------------------------

    def validateAggregateData(self,
                              actual_date,
                              indicator_id,
                              location_id,
                              expected):
        """
            We check against three rules:
            1) The aggregate record that matches the newly inserted record
               * Use indicator and location to find the record. It should
                 have a type of 1 for the actual period other periods will
                 have types of 1 or 3, and the data may vary
            2) The records aggregate for each parent location
               * The type will be 2 but the data may vary
            3) The records for the indicator for each location and time period
               * The type will be 4 but the data may vary
        """

        from dateutil.rrule import rrule, YEARLY

        s3db = current.s3db
        db = current.db

        atable = s3db.stats_aggregate

        # Get the start dates for each time period
        (first_period, dummy) = s3db.stats_aggregated_period(actual_date)
        (last_period, dummy) = s3db.stats_aggregated_period()
        # Get the data for checking rule 1, the data collected from the field
        query = (atable.parameter_id == indicator_id) & \
                (atable.location_id == location_id) & \
                (atable.deleted == False)
        rows = db(query).select()
        aggr_data = {}
        for row in rows:
            aggr_data[row.date] = row
        # Rule 1 check the records exist
        for dt in rrule(YEARLY, dtstart=first_period, until=last_period):
            dt = dt.date()
            msg = "Failed to find an aggregate record starting with date %s" % dt
            self.assertTrue(dt in aggr_data, msg)
            record = aggr_data[dt]
            if dt in expected.rule1.type:
                exp_type = expected.rule1.type[dt]
                last_exp_type = exp_type
            else:
                exp_type = last_exp_type
            if dt in expected.rule1.data:
                exp_data = expected.rule1.data[dt]
                last_exp_data = exp_data
            else:
                exp_data = last_exp_data
            # rule 1 check that the type is correct
            msg = "Expecting a type of %s in record %s" % (exp_type,record)
            self.assertTrue(record.agg_type == exp_type, msg)
            # check each statistic
            for statistic in self.statisticList:
                exp_stat = exp_data[statistic]
                msg = "Expecting a %s of %s in record %s" % (statistic, exp_stat, record)
                self.assertTrue(record[statistic] == exp_stat, msg)
        # Get the data for checking rule 2, the data aggregated over location (and time)
        rows = current.gis.get_parents(location_id)
        location_list = [i.id for i in rows]
        self.assertTrue(len(location_list) == len(expected.rule2.data))
        query = (atable.parameter_id == indicator_id) & \
                (atable.location_id.belongs(location_list)) & \
                (atable.deleted == False)
        rows = db(query).select()
        aggr_data = {}
        for row in rows:
            if row.date in aggr_data:
                aggr_data[row.date][row.location_id] = row
            else:
                aggr_data[row.date] = {row.location_id : row}
        # Rule 2 check the records exist
        last_exp_data = {}
        for dt in rrule(YEARLY, dtstart=first_period, until=last_period):
            dt = dt.date()
            for location in location_list:
                msg = "Failed to find an aggregate record starting with date %s" % dt
                self.assertTrue(dt in aggr_data, msg)
                msg = "Failed to find an aggregate record starting with date %s for location %s" % (dt, self.location_code[location])
                self.assertTrue(location in aggr_data[dt], msg)
                record = aggr_data[dt][location]
                msg = "Expecting a type of 2 in record %s" % record
                self.assertTrue(record.agg_type == 2, msg)
                if dt in expected.rule2.data[location]:
                    exp_data = expected.rule2.data[location][dt]
                    last_exp_data[location] = exp_data
                else:
                    exp_data = last_exp_data[location]
                # check each statistic
                for statistic in self.statisticList:
                    exp_stat = exp_data[statistic]
                    msg = "Expecting a %s of %s for location %s in record %s" % (statistic, exp_stat, self.location_code[location], record)
                    self.assertTrue(record[statistic] == exp_stat, msg)
        # Get the data for checking rule 3 - The resilience indicators
        location_list.append(location_id)
        self.assertTrue(len(location_list) == len(expected.rule3.data))
        query = (atable.parameter_id == self.resilience_id) & \
                (atable.location_id.belongs(location_list)) & \
                (atable.deleted == False)
        rows = db(query).select()
        aggr_data = {}
        for row in rows:
            if row.date in aggr_data:
                aggr_data[row.date][row.location_id] = row
            else:
                aggr_data[row.date] = {row.location_id : row}
        # Rule 3 check the records exist
        for location in location_list:
            last_exp_data = None
            for dt in rrule(YEARLY, dtstart=first_period, until=last_period):
                dt = dt.date()
                msg = "Failed to find a resilience record starting with date %s" % dt
                self.assertTrue(dt in aggr_data, msg)
                msg = "Failed to find a resilience record starting with date %s for location %s" % (dt, self.location_code[location])
                self.assertTrue(location in aggr_data[dt], msg)
                record = aggr_data[dt][location]
                msg = "Expecting a type of 4 in record %s" % record
                self.assertTrue(record.agg_type == 4, msg)
                if dt in expected.rule3.data[location]:
                    exp_data = expected.rule3.data[location][dt]
                    last_exp_data = exp_data
                else:
                    exp_data = last_exp_data
                # check each statistic
                for statistic in self.statisticList:
                    exp_stat = exp_data[statistic]
                    msg = "Expecting a %s of %s  for location %s in record %s" % (statistic, exp_stat, self.location_code[location], record)
                    self.assertTrue(record[statistic] - exp_stat < 1e-7, msg)

    def tearDown(self):

        current.db.rollback()
        current.auth.s3_impersonate(None)

# =============================================================================
def run_suite(*test_classes):
    """ Run the test suite """

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    if suite is not None:
        unittest.TextTestRunner().run(suite)
    return

if __name__ == "__main__":

    run_suite(
        StatsTests,
    )

# END ========================================================================
