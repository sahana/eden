# -*- coding: utf-8 -*-
#
# PR Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/eden/pr.py
#
import unittest

from gluon import current

# =============================================================================
class PRTests(unittest.TestCase):
    """ PR Tests """

    def setUp(self):
        pass

    def testGetRealmUsers(self):

        try:

            auth.s3_impersonate("admin@example.com")
            admin_id = auth.user.id
            admin_pe_id = auth.s3_user_pe_id(admin_id)
            auth.s3_impersonate("normaluser@example.com")
            user_id = auth.user.id
            user_pe_id = auth.s3_user_pe_id(user_id)
            auth.s3_impersonate(None)

            organisations = s3db.pr_get_entities(types="org_organisation", as_list=True, represent=False)
            org1 = organisations[0]
            org2 = organisations[1]

            users = s3db.pr_realm_users(org1)
            self.assertEqual(users, Storage())

            users = s3db.pr_realm_users(org2)
            self.assertEqual(users, Storage())

            s3db.pr_add_affiliation(org1, admin_pe_id, role="Volunteer", role_type=9)
            s3db.pr_add_affiliation(org2, user_pe_id, role="Staff")

            users = s3db.pr_realm_users(org1)
            self.assertFalse(user_id in users)
            self.assertFalse(admin_id in users)

            users = s3db.pr_realm_users(org2)
            self.assertTrue(user_id in users)
            self.assertFalse(admin_id in users)

            users = s3db.pr_realm_users([org1, org2])
            self.assertTrue(user_id in users)
            self.assertFalse(admin_id in users)

            users = s3db.pr_realm_users(org1, roles="Volunteer")
            self.assertFalse(user_id in users)
            self.assertTrue(admin_id in users)

            users = s3db.pr_realm_users(org2, roles="Volunteer")
            self.assertFalse(user_id in users)
            self.assertFalse(admin_id in users)

            users = s3db.pr_realm_users([org1, org2], roles="Volunteer")
            self.assertFalse(user_id in users)
            self.assertTrue(admin_id in users)

            users = s3db.pr_realm_users(org1, roles="Staff")
            self.assertFalse(user_id in users)
            self.assertFalse(admin_id in users)

            users = s3db.pr_realm_users(org2, roles="Staff")
            self.assertTrue(user_id in users)
            self.assertFalse(admin_id in users)

            users = s3db.pr_realm_users([org1, org2], roles="Staff")
            self.assertTrue(user_id in users)
            self.assertFalse(admin_id in users)

            users = s3db.pr_realm_users([org1, org2], roles=["Staff", "Volunteer"])
            self.assertTrue(user_id in users)
            self.assertTrue(admin_id in users)

            users = s3db.pr_realm_users([org1, org2], role_types=1)
            self.assertTrue(user_id in users)
            self.assertFalse(admin_id in users)

            users = s3db.pr_realm_users([org1, org2], role_types=9)
            self.assertFalse(user_id in users)
            self.assertTrue(admin_id in users)

            users = s3db.pr_realm_users([org1, org2], role_types=None)
            self.assertTrue(user_id in users)
            self.assertTrue(admin_id in users)

            s3db.pr_remove_affiliation(org2, user_pe_id, role="Staff")
            users = s3db.pr_realm_users([org1, org2], role_types=None)
            self.assertFalse(user_id in users)
            self.assertTrue(admin_id in users)

            # None as realm should give a list of all current users
            table = auth.settings.table_user
            query = (table.deleted != True)
            rows = db(query).select(table.id)
            all_users = [row.id for row in rows]
            users = s3db.pr_realm_users(None)
            self.assertTrue(all([u in users for u in all_users]))

        finally:
            db.rollback()

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
        PRTests,
    )

# END ========================================================================
