# -*- coding: utf-8 -*-
#
# S3 Model Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3model.py
#
import unittest
from gluon import current

from s3.s3fields import s3_meta_fields

# =============================================================================
class S3ModelTests(unittest.TestCase):

    pass

# =============================================================================
class S3SuperEntityTests(unittest.TestCase):

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        s3db = current.s3db

        # Create super-entity
        s3db.super_entity("setest_super",
                          "se_id",
                          {"setest_master": "SE Test Master"})

        # Add components to the SE
        s3db.add_components("setest_super",
                            setest_component_cascade="se_id",
                            setest_component_setnull="se_id",
                            setest_component_restrict="se_id",
                           )

        # Define master table
        s3db.define_table("setest_master",
                          s3db.super_link("se_id", "setest_super"),
                          *s3_meta_fields())

        # Make instance
        s3db.configure("setest_master",
                       super_entity = "setest_super")

        # Define component tables with constraints
        s3db.define_table("setest_component_cascade",
                          s3db.super_link("se_id", "setest_super",
                                          ondelete="CASCADE"),
                          *s3_meta_fields())

        s3db.define_table("setest_component_setnull",
                          s3db.super_link("se_id", "setest_super",
                                          ondelete="SET NULL"),
                          *s3_meta_fields())

        s3db.define_table("setest_component_restrict",
                          s3db.super_link("se_id", "setest_super",
                                          ondelete="RESTRICT"),
                          *s3_meta_fields())

        current.db.commit()

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        db = current.db

        # Drop all test tables
        db.setest_component_cascade.drop()
        db.setest_component_setnull.drop()
        db.setest_component_restrict.drop()
        db.setest_master.drop()
        db.setest_super.drop()

        current.db.commit()

    # -------------------------------------------------------------------------
    def setUp(self):

        s3db = current.s3db

        # Create the master record and link it to the SE
        master_table = s3db.setest_master
        master_id = master_table.insert()
        s3db.update_super(master_table, {"id": master_id})
        self.master_id = master_id

        current.auth.override = True

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.db.rollback()
        current.auth.override = False

    # -------------------------------------------------------------------------
    def testDeleteSuper(self):
        """ Test delete_super without constraints """

        s3db = current.s3db

        # Get the master record
        master_table = s3db.setest_master
        record = master_table[self.master_id]
        se_id = record.se_id

        # Try delete the super-record (returns True)
        success = s3db.delete_super(master_table, record)
        self.assertTrue(success)

        # Super-key is removed
        record = master_table[self.master_id]
        self.assertEqual(record.se_id, None)

        # Super-record is deleted
        super_table = s3db.setest_super
        super_record = super_table[se_id]
        self.assertTrue(super_record.deleted)

    # -------------------------------------------------------------------------
    def testDeleteSuperCascade(self):
        """ Test delete_super with CASCADE constraint """

        s3db = current.s3db

        # Get the master record
        master_table = s3db.setest_master
        record = master_table[self.master_id]
        se_id = record.se_id

        # Create a component record
        component_table = s3db.setest_component_cascade
        component_id = component_table.insert(se_id=se_id)
        component_record = component_table[component_id]
        self.assertNotEqual(component_record, None)

        # Try delete the super-record (returns True)
        success = s3db.delete_super(master_table, record)
        self.assertTrue(success)

        # Super-key is removed
        record = master_table[self.master_id]
        self.assertEqual(record.se_id, None)

        # Component record is deleted
        component_record = component_table[component_id]
        self.assertTrue(component_record.deleted)
        self.assertEqual(component_record.se_id, None)

        # Super-record is deleted
        super_table = s3db.setest_super
        super_record = super_table[se_id]
        self.assertTrue(super_record.deleted)

    # -------------------------------------------------------------------------
    def testDeleteSuperSetNull(self):
        """ Test delete_super with SET NULL constraint """

        s3db = current.s3db

        # Get the master record
        master_table = s3db.setest_master
        record = master_table[self.master_id]
        se_id = record.se_id

        # Create a component record
        component_table = s3db.setest_component_setnull
        component_id = component_table.insert(se_id=se_id)
        component_record = component_table[component_id]
        self.assertNotEqual(component_record, None)

        # Try delete the super-record (returns True)
        success = s3db.delete_super(master_table, record)
        self.assertTrue(success)

        # Super-key is removed
        record = master_table[self.master_id]
        self.assertEqual(record.se_id, None)

        # Component record is not deleted, but unlinked
        component_record = component_table[component_id]
        self.assertFalse(component_record.deleted)
        self.assertEqual(component_record.se_id, None)

        # Super-record is deleted
        super_table = s3db.setest_super
        super_record = super_table[se_id]
        self.assertTrue(super_record.deleted)

    # -------------------------------------------------------------------------
    def testDeleteSuperRestrict(self):
        """ Test delete_super with RESTRICT constraint """

        s3db = current.s3db

        # Get the master record
        master_table = s3db.setest_master
        record = master_table[self.master_id]
        se_id = record.se_id

        # Create a component record
        component_table = s3db.setest_component_restrict
        component_id = component_table.insert(se_id=se_id)
        component_record = component_table[component_id]
        self.assertNotEqual(component_record, None)

        # Try delete the super-record (must return False)
        success = s3db.delete_super(master_table, record)
        self.assertFalse(success)

        # Super-key is retained
        record = master_table[self.master_id]
        self.assertEqual(record.se_id, se_id)

        # Component record is not deleted and still linked
        component_record = component_table[component_id]
        self.assertFalse(component_record.deleted)
        self.assertEqual(component_record.se_id, se_id)

        # Super-record is not deleted
        super_table = s3db.setest_super
        super_record = super_table[se_id]
        self.assertFalse(super_record.deleted)

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
        #S3ModelTests,
        S3SuperEntityTests,
    )

# END ========================================================================
