# -*- coding: utf-8 -*-
#
# GIS Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3gis.py
#
import unittest
import datetime
from gluon import *
from gluon.storage import Storage
from s3 import *

# =============================================================================
class S3LocationTreeTests(unittest.TestCase):
    """ Location Tree update tests """

    # -------------------------------------------------------------------------
    def setUp(self):

        current.auth.override = True
        self.spatialdb = current.deployment_settings.get_gis_spatialdb()

    # -------------------------------------------------------------------------
    def testL0(self):
        """ Test updating a Country """

        # Insert a new Country
        table = current.s3db.gis_location
        L0_id = table.insert(level = "L0",
                             name = "New Country",
                             wkt = "POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))"
                             )

        # Update the Location Tree for the L0
        current.gis.update_location_tree(dict(id=L0_id))

        # Read the results
        fields = [table.lat,
                  table.lon,
                  table.lat_min,
                  table.lat_max,
                  table.lon_min,
                  table.lon_max,
                  table.parent,
                  table.path,
                  table.wkt,
                  table.L0,
                  table.L1,
                  table.L2,
                  table.L3,
                  table.L4,
                  table.L5,
                  ]
        if self.spatialdb:
            fields.append(table.the_geom)
        record = current.db(table.id == L0_id).select(*fields,
                                                      limitby=(0, 1)
                                                      ).first()

        # Compare to what we expect
        self.assertEqual(record.lat, 26.969696969696972)
        self.assertEqual(record.lon, 25.454545454545453)
        self.assertEqual(record.lat_min, 10)
        self.assertEqual(record.lat_max, 40)
        self.assertEqual(record.lon_min, 10)
        self.assertEqual(record.lon_max, 40)
        self.assertEqual(record.parent, None)
        self.assertEqual(record.path, "%s" % L0_id)
        self.assertEqual(record.wkt, "POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))")
        self.assertEqual(record.L0, "New Country")
        self.assertEqual(record.L1, None)
        self.assertEqual(record.L2, None)
        self.assertEqual(record.L3, None)
        self.assertEqual(record.L4, None)
        self.assertEqual(record.L5, None)
        if self.spatialdb:
            self.assertTrue(record.the_geom is not None)

    # -------------------------------------------------------------------------
    def tearDown(self):
        current.auth.override = False
        current.db.rollback()

# =============================================================================
def run_suite(*test_classes):
    """ Run the test suite """

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    if suite is not None:
        unittest.TextTestRunner(verbosity=2).run(suite)
    return

if __name__ == "__main__":

    run_suite(
        S3LocationTreeTests,
    )

# END ========================================================================
