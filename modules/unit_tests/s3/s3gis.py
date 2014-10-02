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
    @classmethod
    def setUpClass(cls):

        current.auth.override = True

        spatialdb = current.deployment_settings.get_gis_spatialdb()
        table = current.s3db.gis_location
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
        if spatialdb:
            fields.append(table.the_geom)
        cls.spatialdb = spatialdb
        cls.table = table
        cls.fields = fields

        cls.L0 = "New Country"
        cls.L1 = "New L1"
        cls.L2 = "New L2"
        cls.L3 = "New L3"
        cls.L4 = "New L4"
        cls.L5 = "New L5"

    # -------------------------------------------------------------------------
    def testL0(self):
        """ Test updating a Country with Polygon """

        POLYGON = "POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))"
        L0 = self.L0

        table = self.table

        # Insert a new Country
        L0_id = table.insert(level = "L0",
                             name = L0,
                             wkt = POLYGON
                             )

        # Update the Location Tree for the L0
        current.gis.update_location_tree(dict(id=L0_id))

        # Read the results
        record = current.db(table.id == L0_id).select(*self.fields,
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
    def testL1(self):
        """ Test updating a normal L1, with L0 Parent """

        POLYGON = "POLYGON ((30 11, 39 39, 21 39, 11 20, 30 11))"
        L0 = self.L0
        L1 = self.L1

        db = current.db
        table = self.table

        # Lookup the Country ID
        L0_id = db(table.name == L0).select(table.id,
                                            limitby=(0, 1)
                                            ).first().id

        # Insert a new L1
        L1_id = table.insert(level = "L1",
                             name = L1,
                             parent = L0_id,
                             wkt = POLYGON
                             )

        # Update the Location Tree for the L1
        current.gis.update_location_tree(dict(id=L1_id))

        # Read the results
        record = db(table.id == L1_id).select(*self.fields,
                                              limitby=(0, 1)
                                              ).first()

        # Compare to what we expect
        self.assertEqual(record.lat, 26.675741710296684)
        self.assertEqual(record.lon, 25.59232111692845)
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
    def testL2(self):
        """ Test updating a normal L2, with normal L1 Parent """

        POLYGON = "POLYGON ((30 12, 38 38, 22 38, 12 20, 30 12))"
        L0 = self.L0
        L1 = self.L1
        L2 = self.L2

        db = current.db
        table = self.table

        # Lookup the L0 ID
        L0_id = db(table.name == L0).select(table.id,
                                            limitby=(0, 1)
                                            ).first().id

        # Lookup the L1 ID
        L1_id = db(table.name == L1).select(table.id,
                                            limitby=(0, 1)
                                            ).first().id

        # Insert a new L2
        L2_id = table.insert(level = "L2",
                             name = L2,
                             parent = L1_id,
                             wkt = POLYGON
                             )

        # Update the Location Tree for the L2
        current.gis.update_location_tree(dict(id=L2_id))

        # Read the results
        record = db(table.id == L2_id).select(*self.fields,
                                              limitby=(0, 1)
                                              ).first()

        # Compare to what we expect
        self.assertEqual(record.lat, 26.37723577235772)
        self.assertEqual(record.lon, 25.73008130081301)
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
    def testL3(self):
        """ Test updating a normal L3, with normal L2 Parent """

        POLYGON = "POLYGON ((30 13, 37 37, 23 37, 13 20, 30 13))"
        L0 = self.L0
        L1 = self.L1
        L2 = self.L2
        L3 = self.L3

        db = current.db
        table = self.table

        # Lookup the L0 ID
        L0_id = db(table.name == L0).select(table.id,
                                            limitby=(0, 1)
                                            ).first().id

        # Lookup the L1 ID
        L1_id = db(table.name == L1).select(table.id,
                                            limitby=(0, 1)
                                            ).first().id

        # Lookup the L2 ID
        L2_id = db(table.name == L2).select(table.id,
                                            limitby=(0, 1)
                                            ).first().id

        # Insert a new L3
        L3_id = table.insert(level = "L3",
                             name = L3,
                             parent = L2_id,
                             wkt = POLYGON
                             )

        # Update the Location Tree for the L3
        current.gis.update_location_tree(dict(id=L3_id))

        # Read the results
        record = db(table.id == L3_id).select(*self.fields,
                                              limitby=(0, 1)
                                              ).first()

        # Compare to what we expect
        self.assertEqual(record.lat, 26.072901678657075)
        self.assertEqual(record.lon, 25.867625899280576)
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
    def testL4(self):
        """ Test updating a normal L4, with normal L3 Parent """

        POLYGON = "POLYGON ((30 14, 36 36, 24 36, 14 20, 30 14))"
        L0 = self.L0
        L1 = self.L1
        L2 = self.L2
        L3 = self.L3
        L4 = self.L4

        db = current.db
        table = self.table

        # Lookup the L0 ID
        L0_id = db(table.name == L0).select(table.id,
                                            limitby=(0, 1)
                                            ).first().id

        # Lookup the L1 ID
        L1_id = db(table.name == L1).select(table.id,
                                            limitby=(0, 1)
                                            ).first().id

        # Lookup the L2 ID
        L2_id = db(table.name == L2).select(table.id,
                                            limitby=(0, 1)
                                            ).first().id

        # Lookup the L3 ID
        L3_id = db(table.name == L3).select(table.id,
                                            limitby=(0, 1)
                                            ).first().id

        # Insert a new L4
        L4_id = table.insert(level = "L4",
                             name = L4,
                             parent = L3_id,
                             wkt = POLYGON
                             )

        # Update the Location Tree for the L4
        current.gis.update_location_tree(dict(id=L4_id))

        # Read the results
        record = db(table.id == L4_id).select(*self.fields,
                                              limitby=(0, 1)
                                              ).first()

        # Compare to what we expect
        self.assertEqual(record.lat, 25.760919540229885)
        self.assertEqual(record.lon, 26.004597701149425)
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
    def testL5(self):
        """ Test updating a normal L5, with normal L4 Parent """

        POLYGON = "POLYGON ((30 15, 35 35, 23 35, 15 20, 30 15))"
        L0 = self.L0
        L1 = self.L1
        L2 = self.L2
        L3 = self.L3
        L4 = self.L4
        L5 = self.L5

        db = current.db
        table = self.table

        # Lookup the L0 ID
        L0_id = db(table.name == L0).select(table.id,
                                            limitby=(0, 1)
                                            ).first().id

        # Lookup the L1 ID
        L1_id = db(table.name == L1).select(table.id,
                                            limitby=(0, 1)
                                            ).first().id

        # Lookup the L2 ID
        L2_id = db(table.name == L2).select(table.id,
                                            limitby=(0, 1)
                                            ).first().id

        # Lookup the L3 ID
        L3_id = db(table.name == L3).select(table.id,
                                            limitby=(0, 1)
                                            ).first().id

        # Lookup the L4 ID
        L4_id = db(table.name == L4).select(table.id,
                                            limitby=(0, 1)
                                            ).first().id

        # Insert a new L5
        L5_id = table.insert(level = "L5",
                             name = L5,
                             parent = L4_id,
                             wkt = POLYGON
                             )

        # Update the Location Tree for the L5
        current.gis.update_location_tree(dict(id=L5_id))

        # Read the results
        record = db(table.id == L5_id).select(*self.fields,
                                              limitby=(0, 1)
                                              ).first()

        # Compare to what we expect
        self.assertEqual(record.lat, 25.70957095709571)
        self.assertEqual(record.lon, 25.834983498349835)
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
