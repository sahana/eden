# -*- coding: utf-8 -*-
#
# s3fields unit tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3fields.py
#
import unittest
from gluon.languages import lazyT
from gluon.dal import Query
from s3.s3fields import *

# =============================================================================
class S3RepresentTests(unittest.TestCase):

    def setUp(self):

        T = current.T
        self.test_opts = {
            1: "Test1",
            2: "Test2",
            3: "Test3"
        }

        current.auth.override = True

        s3db = current.s3db

        otable = s3db.org_organisation
        org1 = Storage(name="Represent Test Organisation1")
        org1_id = otable.insert(**org1)
        org1.update(id=org1_id)
        s3db.update_super(otable, org1)

        org2 = Storage(name="Represent Test Organisation2")
        org2_id = otable.insert(**org2)
        org2.update(id=org2_id)
        s3db.update_super(otable, org2)

        self.id1 = org1_id
        self.id2 = org2_id
      
        self.name1 = org1.name
        self.name2 = org2.name

    def testSetup(self):
        """ Check lazy setup method """

        # Check for options
        r = S3Represent(options=self.test_opts)
        self.assertFalse(r.setup)
        r._setup()
        self.assertTrue(r.setup)
        self.assertEqual(r.tablename, None)
        self.assertEqual(r.options, self.test_opts)

        # Check for lookups
        r = S3Represent(lookup="org_organisation")
        self.assertFalse(r.setup)
        self.assertEqual(r.options, None)
        self.assertEqual(r.tablename, "org_organisation")
        self.assertEqual(r.key, None)
        self.assertEqual(r.fields, None)
        self.assertEqual(r.labels, None)
        self.assertEqual(r.table, None)
        r._setup()
        self.assertTrue(r.setup)
        self.assertEqual(r.options, None)
        self.assertEqual(r.tablename, "org_organisation")
        self.assertEqual(r.key, "id")
        self.assertEqual(r.fields, ["name"])
        self.assertEqual(r.labels, None)
        self.assertEqual(r.table, current.db.org_organisation)

    def testOptions(self):
        """ Test option field representation """

        r = S3Represent(options=self.test_opts, none="NONE")

        # Standard variants
        self.assertEqual(r(1), "Test1")
        self.assertEqual(r.multiple([1,2,3]), "Test1, Test2, Test3")
        self.assertEqual(r.bulk([1,2,3]),
                         {
                            1: "Test1",
                            2: "Test2",
                            3: "Test3",
                            None: "NONE",
                         }
        )

        # list:type
        r = S3Represent(options=self.test_opts,
                        none="NONE", multiple=True)

        # Should work with both, single value and list
        self.assertEqual(r(1), "Test1")
        self.assertEqual(r([1,2]), "Test1, Test2")

        # Multiple does always expect list of lists
        self.assertRaises(ValueError, r.multiple, [1,2,3])

        # Check multiple with list:type
        result = r.multiple([[1,2]]).split(", ")
        self.assertTrue("Test1" in result)
        self.assertTrue("Test2" in result)
        self.assertEqual(len(result), 2)

        # Check that multiple with list:type de-duplicates properly
        result = r.multiple([[1,2], [2,3]]).split(", ")
        self.assertTrue("Test1" in result)
        self.assertTrue("Test2" in result)
        self.assertTrue("Test3" in result)
        self.assertEqual(len(result), 3)

        # Check bulk with list:type
        result = r.bulk([[1,2], [2,3]])
        self.assertEqual(len(result), 4)
        self.assertTrue(1 in result)
        self.assertEqual(result[1], "Test1")
        self.assertTrue(2 in result)
        self.assertEqual(result[2], "Test2")
        self.assertTrue(3 in result)
        self.assertEqual(result[3], "Test3")
        self.assertTrue(None in result)
        self.assertEqual(result[None], "NONE")

    def testForeignKeys(self):
        """ Test foreign key lookup representation """

        r = S3Represent(lookup="org_organisation")

        # Check lookup value by value
        self.assertEqual(r(self.id1), self.name1)
        self.assertEqual(r(self.id2), self.name2)
        self.assertEqual(r.queries, 2)

        # Check lookup of multiple values
        self.assertEqual(r.multiple([self.id1, self.id2]),
                         "%s, %s" % (self.name1, self.name2))
        # Should not have needed any additional queries
        self.assertEqual(r.queries, 2)

        # Check bulk lookup
        result = r.bulk([self.id1, self.id2])
        self.assertTrue(len(result), 3)
        self.assertEqual(result[self.id1], self.name1)
        self.assertEqual(result[self.id2], self.name2)
        self.assertTrue(None in result)
        # Should still not have needed any additional queries
        self.assertEqual(r.queries, 2)

        # Check that only one query is used for multiple values
        r = S3Represent(lookup="org_organisation")
        result = r.bulk([self.id1, self.id2])
        self.assertTrue(len(result), 3)
        self.assertEqual(r.queries, 1)

        # Check translation
        r = S3Represent(lookup="org_organisation", translate=True)
        result = r(self.id1)
        self.assertTrue(isinstance(result, lazyT))
        self.assertEqual(result, current.T(self.name1))

    def tearDown(self):

        current.db.rollback()
        current.auth.override = False
        
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
        S3RepresentTests,
    )

# END ========================================================================
