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
            org = organisations[0]

            users = s3db.pr_realm_users(org)
            self.assertEqual(users, Storage())

            s3db.pr_add_affiliation(org, admin_pe_id, role="Volunteer", role_type=9)
            s3db.pr_add_affiliation(org, user_pe_id, role="Staff")

            users = s3db.pr_realm_users(org)
            self.assertTrue(user_id in users)
            self.assertFalse(admin_id in users)

            users = s3db.pr_realm_users(org, roles="Volunteer")
            self.assertFalse(user_id in users)
            self.assertTrue(admin_id in users)

            users = s3db.pr_realm_users(org, roles="Staff")
            self.assertTrue(user_id in users)
            self.assertFalse(admin_id in users)

            users = s3db.pr_realm_users(org, roles=["Staff", "Volunteer"])
            self.assertTrue(user_id in users)
            self.assertTrue(admin_id in users)

            users = s3db.pr_realm_users(org, role_types=1)
            self.assertTrue(user_id in users)
            self.assertFalse(admin_id in users)

            users = s3db.pr_realm_users(org, role_types=9)
            self.assertFalse(user_id in users)
            self.assertTrue(admin_id in users)

            users = s3db.pr_realm_users(org, role_types=None)
            self.assertTrue(user_id in users)
            self.assertTrue(admin_id in users)

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
