# -*- coding: utf-8 -*-
#
# GIS Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3gis.py

import unittest
import datetime
from gluon import *
from gluon.storage import Storage
from s3 import *

# =============================================================================
class S3LocationTreeTests(unittest.TestCase):
    """ Location Tree update tests """

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        current.auth.override = True

        spatialdb = current.deployment_settings.get_gis_spatialdb()
        table = current.s3db.gis_location
        fields = [table.inherited,
                  table.lat,
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
        if spatialdb:
            fields.append(table.the_geom)
        cls.spatialdb = spatialdb
        cls.table = table
        cls.fields = fields

        cls.L0 = "New Country"
        cls.L1 = "Normal L1"
        cls.L2 = "Normal L2"
        cls.L3 = "Normal L3"
        cls.L4 = "Normal L4"
        cls.L5 = "Normal L5"

        cls.ids = {}

    # -------------------------------------------------------------------------
    def testL0_with_level(self):
        """ Test updating a Country with Polygon - including level optimisation """

        self._testL0(with_level=True)

    # -------------------------------------------------------------------------
    def testL0_without_level(self):
        """ Test updating a Country with Polygon - without level optimisation """

        self._testL0(with_level=False)

    # -------------------------------------------------------------------------
    def testL1_with_level(self):
        """ Test updating a normal L1, with L0 Parent - including level optimisation """

        self._testL1(with_level=True)

    # -------------------------------------------------------------------------
    def testL1_without_level(self):
        """ Test updating a normal L1, with L0 Parent - without level optimisation """

        self._testL1(with_level=False)

    # -------------------------------------------------------------------------
    def testL2_with_level(self):
        """ Test updating a normal L2, with normal L1 Parent - including level optimisation """

        self._testL2(with_level=True)

    # -------------------------------------------------------------------------
    def testL2_without_level(self):
        """ Test updating a normal L2, with normal L1 Parent - without level optimisation """

        self._testL2(with_level=False)

    # -------------------------------------------------------------------------
    def testL3_with_level(self):
        """ Test updating a normal L3, with normal L2 Parent - including level optimisation """

        self._testL3(with_level=True)

    # -------------------------------------------------------------------------
    def testL3_without_level(self):
        """ Test updating a normal L3, with normal L2 Parent - without level optimisation """

        self._testL3(with_level=False)

    # -------------------------------------------------------------------------
    def testL4_with_level(self):
        """ Test updating a normal L4, with normal L3 Parent - including level optimisation """

        self._testL4(with_level=True)

    # -------------------------------------------------------------------------
    def testL4_without_level(self):
        """ Test updating a normal L4, with normal L3 Parent - without level optimisation """

        self._testL4(with_level=False)

    # -------------------------------------------------------------------------
    def testL5_with_level(self):
        """ Test updating a normal L5, with normal L4 Parent - including level optimisation """

        self._testL5(with_level=True)

    # -------------------------------------------------------------------------
    def testL5_without_level(self):
        """ Test updating a normal L5, with normal L4 Parent - without level optimisation """

        self._testL5(with_level=False)

    # -------------------------------------------------------------------------
    def testL3_L1_parent_with_level(self):
        """ Test updating an L3, without an L2 Parent, going straight to L1 - including level optimisation """

        self._testL3_L1_parent(with_level=True)

    # -------------------------------------------------------------------------
    def testL3_L1_parent_without_level(self):
        """ Test updating an L3, without an L2 Parent, going straight to L1 - without level optimisation """

        self._testL3_L1_parent(with_level=False)

    # -------------------------------------------------------------------------
    def _testL0(self, with_level):
        """ Test updating a Country with Polygon """

        LEVEL = "L0"
        POLYGON = "POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))"
        L0 = "%s_%s" % (self.L0, with_level)

        table = self.table

        # Insert a new Country
        L0_id = table.insert(level = LEVEL,
                             name = L0,
                             wkt = POLYGON
                             )
        # Store for future tests
        S3LocationTreeTests.ids[L0] = L0_id

        # Update the Location Tree for the L0
        feature = dict(id=L0_id)
        if with_level:
            feature["level"] = LEVEL
        current.gis.update_location_tree(feature)

        # Read the results
        record = current.db(table.id == L0_id).select(*self.fields,
                                                      limitby=(0, 1)
                                                      ).first()

        # Compare to what we expect
        self.assertEqual(record.inherited, False)
        self.assertAlmostEqual(record.lat, 26.969696969696972, 13)
        self.assertAlmostEqual(record.lon, 25.454545454545453, 13)
        self.assertEqual(record.lat_min, 10)
        self.assertEqual(record.lat_max, 40)
        self.assertEqual(record.lon_min, 10)
        self.assertEqual(record.lon_max, 40)
        self.assertEqual(record.parent, None)
        self.assertEqual(record.path, "%s" % L0_id)
        self.assertEqual(record.wkt, POLYGON)
        self.assertEqual(record.L0, L0)
        self.assertEqual(record.L1, None)
        self.assertEqual(record.L2, None)
        self.assertEqual(record.L3, None)
        self.assertEqual(record.L4, None)
        self.assertEqual(record.L5, None)
        if self.spatialdb:
            self.assertTrue(record.the_geom is not None)

    # -------------------------------------------------------------------------
    def _testL1(self, with_level):
        """ Test updating a normal L1, with L0 Parent """

        LEVEL = "L1"
        POLYGON = "POLYGON ((30 11, 39 39, 21 39, 11 20, 30 11))"
        L0 = "%s_%s" % (self.L0, with_level)
        L1 = "%s_%s" % (self.L1, with_level)
        L0_id = self.ids[L0]

        table = self.table

        # Insert a new L1
        L1_id = table.insert(level = LEVEL,
                             name = L1,
                             parent = L0_id,
                             wkt = POLYGON
                             )
        # Store for future tests
        S3LocationTreeTests.ids[L1] = L1_id

        # Update the Location Tree for the L1
        feature = dict(id=L1_id)
        if with_level:
            feature["level"] = LEVEL
        current.gis.update_location_tree(feature)

        # Read the results
        record = current.db(table.id == L1_id).select(*self.fields,
                                                      limitby=(0, 1)
                                                      ).first()

        # Compare to what we expect
        self.assertEqual(record.inherited, False)
        self.assertAlmostEqual(record.lat, 26.675741710296684, 13)
        self.assertAlmostEqual(record.lon, 25.59232111692845, 13)
        self.assertEqual(record.lat_min, 11)
        self.assertEqual(record.lat_max, 39)
        self.assertEqual(record.lon_min, 11)
        self.assertEqual(record.lon_max, 39)
        self.assertEqual(record.parent, L0_id)
        self.assertEqual(record.path, "%s/%s" % (L0_id, L1_id))
        self.assertEqual(record.wkt, POLYGON)
        self.assertEqual(record.L0, L0)
        self.assertEqual(record.L1, L1)
        self.assertEqual(record.L2, None)
        self.assertEqual(record.L3, None)
        self.assertEqual(record.L4, None)
        self.assertEqual(record.L5, None)
        if self.spatialdb:
            self.assertTrue(record.the_geom is not None)

    # -------------------------------------------------------------------------
    def _testL2(self, with_level):
        """ Test updating a normal L2, with normal L1 Parent """

        LEVEL = "L2"
        POLYGON = "POLYGON ((30 12, 38 38, 22 38, 12 20, 30 12))"
        L0 = "%s_%s" % (self.L0, with_level)
        L1 = "%s_%s" % (self.L1, with_level)
        L2 = "%s_%s" % (self.L2, with_level)
        L0_id = self.ids[L0]
        L1_id = self.ids[L1]

        table = self.table

        # Insert a new L2
        L2_id = table.insert(level = LEVEL,
                             name = L2,
                             parent = L1_id,
                             wkt = POLYGON
                             )
        # Store for future tests
        S3LocationTreeTests.ids[L2] = L2_id

        # Update the Location Tree for the L2
        feature = dict(id=L2_id)
        if with_level:
            feature["level"] = LEVEL
        current.gis.update_location_tree(feature)

        # Read the results
        record = current.db(table.id == L2_id).select(*self.fields,
                                                      limitby=(0, 1)
                                                      ).first()

        # Compare to what we expect
        self.assertEqual(record.inherited, False)
        self.assertAlmostEqual(record.lat, 26.37723577235772, 13)
        self.assertAlmostEqual(record.lon, 25.73008130081301, 13)
        self.assertEqual(record.lat_min, 12)
        self.assertEqual(record.lat_max, 38)
        self.assertEqual(record.lon_min, 12)
        self.assertEqual(record.lon_max, 38)
        self.assertEqual(record.parent, L1_id)
        self.assertEqual(record.path, "%s/%s/%s" % (L0_id, L1_id, L2_id))
        self.assertEqual(record.wkt, POLYGON)
        self.assertEqual(record.L0, L0)
        self.assertEqual(record.L1, L1)
        self.assertEqual(record.L2, L2)
        self.assertEqual(record.L3, None)
        self.assertEqual(record.L4, None)
        self.assertEqual(record.L5, None)
        if self.spatialdb:
            self.assertTrue(record.the_geom is not None)

    # -------------------------------------------------------------------------
    def _testL3(self, with_level):
        """ Test updating a normal L3, with normal L2 Parent """

        LEVEL = "L3"
        POLYGON = "POLYGON ((30 13, 37 37, 23 37, 13 20, 30 13))"
        L0 = "%s_%s" % (self.L0, with_level)
        L1 = "%s_%s" % (self.L1, with_level)
        L2 = "%s_%s" % (self.L2, with_level)
        L3 = "%s_%s" % (self.L3, with_level)
        L0_id = self.ids[L0]
        L1_id = self.ids[L1]
        L2_id = self.ids[L2]

        table = self.table

        # Insert a new L3
        L3_id = table.insert(level = LEVEL,
                             name = L3,
                             parent = L2_id,
                             wkt = POLYGON
                             )
        # Store for future tests
        S3LocationTreeTests.ids[L3] = L3_id

        # Update the Location Tree for the L3
        feature = dict(id=L3_id)
        if with_level:
            feature["level"] = LEVEL
        current.gis.update_location_tree(feature)

        # Read the results
        record = current.db(table.id == L3_id).select(*self.fields,
                                                      limitby=(0, 1)
                                                      ).first()

        # Compare to what we expect
        self.assertEqual(record.inherited, False)
        self.assertAlmostEqual(record.lat, 26.072901678657075, 13)
        self.assertAlmostEqual(record.lon, 25.867625899280576, 13)
        self.assertEqual(record.lat_min, 13)
        self.assertEqual(record.lat_max, 37)
        self.assertEqual(record.lon_min, 13)
        self.assertEqual(record.lon_max, 37)
        self.assertEqual(record.parent, L2_id)
        self.assertEqual(record.path, "%s/%s/%s/%s" % (L0_id, L1_id, L2_id, L3_id))
        self.assertEqual(record.wkt, POLYGON)
        self.assertEqual(record.L0, L0)
        self.assertEqual(record.L1, L1)
        self.assertEqual(record.L2, L2)
        self.assertEqual(record.L3, L3)
        self.assertEqual(record.L4, None)
        self.assertEqual(record.L5, None)
        if self.spatialdb:
            self.assertTrue(record.the_geom is not None)

    # -------------------------------------------------------------------------
    def _testL4(self, with_level):
        """ Test updating a normal L4, with normal L3 Parent """

        LEVEL = "L4"
        POLYGON = "POLYGON ((30 14, 36 36, 24 36, 14 20, 30 14))"
        L0 = "%s_%s" % (self.L0, with_level)
        L1 = "%s_%s" % (self.L1, with_level)
        L2 = "%s_%s" % (self.L2, with_level)
        L3 = "%s_%s" % (self.L3, with_level)
        L4 = "%s_%s" % (self.L4, with_level)
        L0_id = self.ids[L0]
        L1_id = self.ids[L1]
        L2_id = self.ids[L2]
        L3_id = self.ids[L3]

        table = self.table

        # Insert a new L4
        L4_id = table.insert(level = LEVEL,
                             name = L4,
                             parent = L3_id,
                             wkt = POLYGON
                             )
        # Store for future tests
        S3LocationTreeTests.ids[L4] = L4_id

        # Update the Location Tree for the L4
        feature = dict(id=L4_id)
        if with_level:
            feature["level"] = LEVEL
        current.gis.update_location_tree(feature)

        # Read the results
        record = current.db(table.id == L4_id).select(*self.fields,
                                                      limitby=(0, 1)
                                                      ).first()

        # Compare to what we expect
        self.assertEqual(record.inherited, False)
        self.assertAlmostEqual(record.lat, 25.760919540229885, 13)
        self.assertAlmostEqual(record.lon, 26.004597701149425, 13)
        self.assertEqual(record.lat_min, 14)
        self.assertEqual(record.lat_max, 36)
        self.assertEqual(record.lon_min, 14)
        self.assertEqual(record.lon_max, 36)
        self.assertEqual(record.parent, L3_id)
        self.assertEqual(record.path, "%s/%s/%s/%s/%s" % (L0_id, L1_id, L2_id, L3_id, L4_id))
        self.assertEqual(record.wkt, POLYGON)
        self.assertEqual(record.L0, L0)
        self.assertEqual(record.L1, L1)
        self.assertEqual(record.L2, L2)
        self.assertEqual(record.L3, L3)
        self.assertEqual(record.L4, L4)
        self.assertEqual(record.L5, None)
        if self.spatialdb:
            self.assertTrue(record.the_geom is not None)

    # -------------------------------------------------------------------------
    def _testL5(self, with_level):
        """ Test updating a normal L5, with normal L4 Parent """

        LEVEL = "L5"
        POLYGON = "POLYGON ((30 15, 35 35, 23 35, 15 20, 30 15))"
        L0 = "%s_%s" % (self.L0, with_level)
        L1 = "%s_%s" % (self.L1, with_level)
        L2 = "%s_%s" % (self.L2, with_level)
        L3 = "%s_%s" % (self.L3, with_level)
        L4 = "%s_%s" % (self.L4, with_level)
        L5 = "%s_%s" % (self.L5, with_level)
        L0_id = self.ids[L0]
        L1_id = self.ids[L1]
        L2_id = self.ids[L2]
        L3_id = self.ids[L3]
        L4_id = self.ids[L4]

        table = self.table

        # Insert a new L5
        L5_id = table.insert(level = LEVEL,
                             name = L5,
                             parent = L4_id,
                             wkt = POLYGON
                             )

        # Update the Location Tree for the L5
        feature = dict(id=L5_id)
        if with_level:
            feature["level"] = LEVEL
        current.gis.update_location_tree(feature)

        # Read the results
        record = current.db(table.id == L5_id).select(*self.fields,
                                                      limitby=(0, 1)
                                                      ).first()

        # Compare to what we expect
        self.assertEqual(record.inherited, False)
        self.assertAlmostEqual(record.lat, 25.70957095709571, 13)
        self.assertAlmostEqual(record.lon, 25.834983498349835, 13)
        self.assertEqual(record.lat_min, 15)
        self.assertEqual(record.lat_max, 35)
        self.assertEqual(record.lon_min, 15)
        self.assertEqual(record.lon_max, 35)
        self.assertEqual(record.parent, L4_id)
        self.assertEqual(record.path, "%s/%s/%s/%s/%s/%s" % (L0_id, L1_id, L2_id, L3_id, L4_id, L5_id))
        self.assertEqual(record.wkt, POLYGON)
        self.assertEqual(record.L0, L0)
        self.assertEqual(record.L1, L1)
        self.assertEqual(record.L2, L2)
        self.assertEqual(record.L3, L3)
        self.assertEqual(record.L4, L4)
        self.assertEqual(record.L5, L5)
        if self.spatialdb:
            self.assertTrue(record.the_geom is not None)

    # -------------------------------------------------------------------------
    def _testL3_L1_parent(self, with_level):
        """ Test updating an L3, without an L2 Parent, going straight to L1
            - this is like Cotabato City & Isabela City in the Philippines
        """

        LEVEL = "L3"
        POLYGON = "POLYGON ((30 13, 37 37, 23 37, 13 20, 30 13))"
        L0 = "%s_%s" % (self.L0, with_level)
        L1 = "%s_%s" % (self.L1, with_level)
        L3 = "Test of Cotabato City"
        L0_id = self.ids[L0]
        L1_id = self.ids[L1]

        table = self.table

        # Insert a new L3
        L3_id = table.insert(level = LEVEL,
                             name = L3,
                             parent = L1_id,
                             wkt = POLYGON
                             )

        # Update the Location Tree for the L3
        feature = dict(id=L3_id)
        if with_level:
            feature["level"] = LEVEL
        current.gis.update_location_tree(feature)

        # Read the results
        record = current.db(table.id == L3_id).select(*self.fields,
                                                      limitby=(0, 1)
                                                      ).first()

        # Compare to what we expect
        self.assertEqual(record.inherited, False)
        self.assertAlmostEqual(record.lat, 26.072901678657075, 13)
        self.assertAlmostEqual(record.lon, 25.867625899280576, 13)
        self.assertEqual(record.lat_min, 13)
        self.assertEqual(record.lat_max, 37)
        self.assertEqual(record.lon_min, 13)
        self.assertEqual(record.lon_max, 37)
        self.assertEqual(record.parent, L1_id)
        self.assertEqual(record.path, "%s/%s/%s" % (L0_id, L1_id, L3_id))
        self.assertEqual(record.wkt, POLYGON)
        self.assertEqual(record.L0, L0)
        self.assertEqual(record.L1, L1)
        self.assertEqual(record.L2, None)
        self.assertEqual(record.L3, L3)
        self.assertEqual(record.L4, None)
        self.assertEqual(record.L5, None)
        if self.spatialdb:
            self.assertTrue(record.the_geom is not None)

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):
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
