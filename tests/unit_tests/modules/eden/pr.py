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
