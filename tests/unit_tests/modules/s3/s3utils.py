# -*- coding: utf-8 -*-
#
# REST Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/s3/s3utils.py
#
import unittest
from gluon.dal import Query
from s3.s3utils import *

# =============================================================================
class S3FKWrappersTests(unittest.TestCase):

    def testHasForeignKey(self):

        ptable = s3db.pr_person
        self.assertFalse(s3_has_foreign_key(ptable.first_name))
        self.assertTrue(s3_has_foreign_key(ptable.pe_id))

        htable = s3db.hrm_human_resource
        self.assertFalse(s3_has_foreign_key(htable.start_date))
        self.assertTrue(s3_has_foreign_key(htable.person_id))

        otable = s3db.org_organisation
        self.assertTrue(s3_has_foreign_key(otable.sector_id))
        self.assertFalse(s3_has_foreign_key(otable.sector_id, m2m=False))

    def testGetForeignKey(self):

        ptable = s3db.pr_person
        ktablename, key, multiple = s3_get_foreign_key(ptable.pe_id)
        self.assertEqual(ktablename, "pr_pentity")
        self.assertEqual(key, "pe_id")
        self.assertFalse(multiple)

        otable = s3db.org_organisation
        ktablename, key, multiple = s3_get_foreign_key(otable.sector_id)
        self.assertEqual(ktablename, "org_sector")
        self.assertEqual(key, "id")
        self.assertTrue(multiple)

        ktablename, key, multiple = s3_get_foreign_key(otable.sector_id, m2m=False)
        self.assertEqual(ktablename, None)
        self.assertEqual(key, None)
        self.assertEqual(multiple, None)

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
        S3FKWrappersTests,
    )

# END ========================================================================
