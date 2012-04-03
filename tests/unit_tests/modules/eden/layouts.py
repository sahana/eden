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
