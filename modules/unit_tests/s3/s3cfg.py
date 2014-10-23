# -*- coding: utf-8 -*-
#
# S3CFG Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3cfg.py
#
import unittest
from gluon import current

# =============================================================================
class S3ConfigTests(unittest.TestCase):
    """ Deployment settings tests """

    # -------------------------------------------------------------------------
    def testSetOrgDependentFields(self):
        """ Test organisation-dependent accessibility of fields """

        auth = current.auth
        s3db = current.s3db
        settings = current.deployment_settings

        table = current.s3db.pr_person_details
        s = settings.org.get("dependent_fields", None)

        settings.org.dependent_fields = \
            {"pr_person_details.mother_name" : ["Example Root Org"]}

        # Admin does always see the field
        auth.s3_impersonate("admin@example.com")
        check = settings.set_org_dependent_field("pr_person_details", "mother_name")
        self.assertTrue(check)
        self.assertTrue(table.mother_name.readable)
        self.assertTrue(table.mother_name.writable)

        # Anonymous doesn't belong to an org thus can't see the field
        auth.s3_impersonate(None)
        check = settings.set_org_dependent_field("pr_person_details", "mother_name")
        self.assertFalse(check)
        self.assertFalse(table.mother_name.readable)
        self.assertFalse(table.mother_name.writable)

        try:
            # Create a fake org
            auth.override = True
            xmlstr = """
<s3xml>
    <resource name="org_organisation" uuid="ExampleRootOrg">
        <data field="name">Example Root Org</data>
    </resource>
</s3xml>"""

            from lxml import etree
            tree = etree.ElementTree(etree.fromstring(xmlstr))

            resource = s3db.resource("org_organisation")
            msg = resource.import_xml(tree)

            resource = s3db.resource("org_organisation", uid="ExampleRootOrg")
            org = resource.select(None, as_rows=True)[0]
            auth.override = False

            # Normal user can't see the field by default
            auth.s3_impersonate("normaluser@example.com")
            check = settings.set_org_dependent_field("pr_person_details", "mother_name")
            self.assertFalse(check)
            self.assertFalse(table.mother_name.readable)
            self.assertFalse(table.mother_name.writable)

            # User can see the field if belonging to that org
            auth.user.organisation_id = org.id
            self.assertEqual(auth.root_org(), org.id)
            check = settings.set_org_dependent_field("pr_person_details", "mother_name")
            self.assertTrue(check)
            self.assertTrue(table.mother_name.readable)
            self.assertTrue(table.mother_name.writable)

            # ...but not if we haven't configured it
            settings.org.dependent_fields = None
            check = settings.set_org_dependent_field("pr_person_details", "mother_name")
            self.assertFalse(check)
            self.assertFalse(table.mother_name.readable)
            self.assertFalse(table.mother_name.writable)

        finally:
            current.db.rollback()
            auth.s3_impersonate(None)
            if s:
                settings.org.dependent_fields = s

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
        S3ConfigTests,
    )

# END ========================================================================
