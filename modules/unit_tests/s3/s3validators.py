# -*- coding: utf-8 -*-
#
# Validators Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/s3/s3validators.py
#
import unittest
from gluon import current
from gluon.dal import Query
from s3.s3fields import *

# =============================================================================
class ISLatTest(unittest.TestCase):
    """
        Latitude has to be in decimal degrees between -90 & 90
        - we can convert D/M/S or D°M'S" format into decimal degrees:
        Zero padded, separated by spaces or : or (d, m, s) or (°, ', ") or run together and followed by cardinal direction initial (N,S) Note: Only seconds can have decimals places. A decimal point with no trailing digits is invalid.
        Matches	
        40:26:46N | 40°26'47?N | 40d 26m 47s N | 90 00 00.0 | 89 59 50.4141 S | 00 00 00.0
        Non-Matches	
        90 00 00.001 N | 9 00 00.00 N | 9 00 00.00 | 90 61 50.4121 S | -90 48 50. N | 90 00 00. N | 00 00 00.
    """

    pass

# =============================================================================
class ISLonTest(unittest.TestCase):
    """
        Longitude has to be in decimal degrees between -180 & 180
        - we can convert D/M/S format into decimal degrees
        Zero padded, separated by spaces or : or (d, m, s) or (°, ', ") or run together and followed by cardinal direction initial (E,W) Note: Only seconds can have decimals places. A decimal point with no trailing digits is invalid.
        Matches	
        079:56:55W | 079°58'36?W | 079d 58' 36? W | 180 00 00.0 | 090 29 20.4 E | 000 00 00.0
        Non-Matches	
        180 00 00.001 E | 79 00 00.00 E | -79 00 00.00 | 090 29 20.4 E | -090 29 20.4 E | 180 00 00. E | 000 00 00.
    """

    pass

# =============================================================================
class ISONEOFLazyRepresentationTests(unittest.TestCase):

    def setUp(self):

        s3db = current.s3db

        orgs = [Storage(name="ISONEOF%s" % i,
                        acronym="IOO%s" % i)
                for i in xrange(5)]

        ids = []
        table = s3db.org_organisation
        for org in orgs:
            org_id = table.insert(**org)
            org["id"] = org_id
            s3db.update_super(table, org)
            ids.append(org_id)

        current.auth.override = True
        self.ids = ids
        self.orgs = orgs

    # -------------------------------------------------------------------------
    def testIsOneOfBuildSet(self):

        renderer = S3Represent(lookup="org_organisation")

        db = current.db
        table = current.s3db.org_organisation
        validator = IS_ONE_OF(db(table.id.belongs(self.ids)),
                              "org_organisation.id",
                              renderer)

        options = Storage(validator.options())
        for org in self.orgs:
            self.assertTrue(str(org.id) in options)
            self.assertEqual(options[str(org.id)], org.name)
        self.assertEqual(renderer.queries, 0)

    # -------------------------------------------------------------------------
    def testOrgOrganisationRepresent(self):

        s3db = current.s3db
        renderer = s3db.org_OrganisationRepresent()

        db = current.db
        table = s3db.org_organisation
        validator = IS_ONE_OF(db(table.id.belongs(self.ids)),
                              "org_organisation.id",
                              renderer)

        options = Storage(validator.options())
        for org in self.orgs:
            self.assertTrue(str(org.id) in options)
            self.assertEqual(options[str(org.id)],
                             "%s (%s)" % (org.name, org.acronym))
        self.assertEqual(renderer.queries, 1) # using custom query

        renderer = s3db.org_OrganisationRepresent(parent=False)

        db = current.db
        table = current.s3db.org_organisation
        validator = IS_ONE_OF(db(table.id.belongs(self.ids)),
                              "org_organisation.id",
                              renderer)

        options = Storage(validator.options())
        for org in self.orgs:
            self.assertTrue(str(org.id) in options)
            self.assertEqual(options[str(org.id)],
                             "%s (%s)" % (org.name, org.acronym))
        self.assertEqual(renderer.queries, 0) # using default query

        renderer = s3db.org_OrganisationRepresent(parent=False,
                                                  acronym=False)

        db = current.db
        table = current.s3db.org_organisation
        validator = IS_ONE_OF(db(table.id.belongs(self.ids)),
                              "org_organisation.id",
                              renderer)

        options = Storage(validator.options())
        for org in self.orgs:
            self.assertTrue(str(org.id) in options)
            self.assertEqual(options[str(org.id)], org.name)
        self.assertEqual(renderer.queries, 0) # using default query

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
        ISLatTest,
        ISLonTest,
        ISONEOFLazyRepresentationTests,
    )

# END ========================================================================
