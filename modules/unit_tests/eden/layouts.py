# -*- coding: utf-8 -*-
#
# Layouts Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/eden/layouts.py
#
import unittest

from gluon import current
from eden.layouts import *

# =============================================================================
class LayoutTests(unittest.TestCase):
    """ Layout Tests """

    def setUp(self):
        pass

    def testHomepageFunction(self):

        # Test existing module
        hp = homepage("pr")
        self.assertTrue(hp is not None)

        # Test non-existent (deactivated) module
        hp = homepage("nonexistent")
        self.assertTrue(hp is not None)
        self.assertFalse(hp.check_active())
        rendered_hp = hp.xml()
        self.assertEqual(rendered_hp, "")

    def testAddResourceLink(self):

        auth = current.auth
        deployment_settings = current.deployment_settings

        comment = S3AddResourceLink(c="pr", f="person")

        # If the module is active, the comment should always be active
        self.assertEqual(comment.check_active(),
                         deployment_settings.has_module("pr"))
        self.assertEqual(comment.method, "create")

        # Label should fall back to CRUD string
        from s3.s3crud import S3CRUD
        crud_string = S3CRUD.crud_string("pr_person", "label_create_button")
        self.assertEqual(comment.label, crud_string)

        if "dvi" in deployment_settings.modules:
            comment = S3AddResourceLink(c="dvi", f="body")
            # Deactivate module
            dvi = deployment_settings.modules["dvi"]
            del deployment_settings.modules["dvi"]
            # Comment should auto-deactivate
            self.assertFalse(comment.check_active())
            # Restore module
            deployment_settings.modules["dvi"] = dvi
            # Comment should auto-reactivate
            self.assertTrue(comment.check_active())

        self.assertFalse(comment.check_permission())
        self.assertEqual(comment.xml(), "")
        auth.s3_impersonate("admin@example.com")
        self.assertTrue(comment.check_permission())
        output = comment.xml()
        self.assertTrue(type(output) is str)
        self.assertNotEqual(output, "")

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
        LayoutTests,
    )

# END ========================================================================
