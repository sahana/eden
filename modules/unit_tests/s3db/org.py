# -*- coding: utf-8 -*-
#
# Org Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3db/org.py
#
import unittest

from gluon import *
from gluon.storage import Storage

# =============================================================================
class RootOrgUpdateTests(unittest.TestCase):
    """ Test update of the root_organisation field in org_organisation """

    # -------------------------------------------------------------------------
    def setUp(self):

        current.auth.override = True

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.db.rollback()
        current.auth.override = False

    # -------------------------------------------------------------------------
    def testRootOrgOnaccept(self):
        """ Test the root organisation is set onaccept """

        db = current.db
        s3db = current.s3db
        otable = s3db.org_organisation

        # Insert new record
        organisation = Storage(name = "RootOrgOnacceptTest")
        record_id = otable.insert(**organisation)
        self.assertNotEqual(record_id, None)

        # Execute update_super and onaccept
        organisation["id"] = record_id
        s3db.update_super(otable, organisation)
        s3db.onaccept(otable, organisation, method="create")

        # Reload the record
        row = db(otable.id == record_id).select(otable.id,
                                                otable.root_organisation,
                                                limitby=(0, 1)).first()
                                                 
        self.assertNotEqual(row, None)
        self.assertEqual(row.root_organisation, row.id)

    # -------------------------------------------------------------------------
    def testRootOrgUpdate(self):
        """ Test the root organisation is updated when adding a branch link """

        db = current.db
        s3db = current.s3db
        otable = s3db.org_organisation
        ltable = s3db.org_organisation_branch

        # Insert organisation records
        org1 = Storage(name = "RootOrgUpdateTest1")
        org1_id = otable.insert(**org1)
        self.assertNotEqual(org1_id, None)
        org1["id"] = org1_id
        s3db.update_super(otable, org1)
        s3db.onaccept(otable, org1, method="create")

        org2 = Storage(name = "RootOrgUpdateTest2")
        org2_id = otable.insert(**org2)
        self.assertNotEqual(org2_id, None)
        org2["id"] = org2_id
        s3db.update_super(otable, org2)
        s3db.onaccept(otable, org2, method="create")

        org3 = Storage(name = "RootOrgUpdateTest3")
        org3_id = otable.insert(**org3)
        self.assertNotEqual(org3_id, None)
        org3["id"] = org3_id
        s3db.update_super(otable, org3)
        s3db.onaccept(otable, org3, method="create")

        # Make org3 a branch of org2
        link = Storage(organisation_id = org2_id,
                       branch_id = org3_id)
        link_id = ltable.insert(**link)
        self.assertNotEqual(link_id, None)
        link["id"] = link_id
        s3db.onaccept(ltable, link, method="create")

        # Check root_organisations
        check = (org2_id, org3_id)
        rows = db(otable.id.belongs(check)).select(otable.id,
                                                   otable.root_organisation)
        self.assertNotEqual(rows, None)
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertEqual(row.root_organisation, org2_id)

        # Make org2 a branch of org1
        link = Storage(organisation_id = org1_id,
                       branch_id = org2_id)
        link_id = ltable.insert(**link)
        self.assertNotEqual(link_id, None)
        link["id"] = link_id
        s3db.onaccept(ltable, link, method="create")

        # Check root_organisations
        check = (org1_id, org2_id, org3_id)
        rows = db(otable.id.belongs(check)).select(otable.id,
                                                   otable.root_organisation)
        self.assertNotEqual(rows, None)
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(row.root_organisation, org1_id)

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
        RootOrgUpdateTests,
    )

# END ========================================================================
