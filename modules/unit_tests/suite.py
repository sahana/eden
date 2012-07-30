# -*- coding: utf-8 -*-
#
# Sahana Eden Unit Tests
#
# To run this test suite use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/suite.py

import unittest

# =============================================================================
def run_suite(*modules):
    """ Run the test suite """

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for name in modules:
        path = "applications.%s.modules.unit_tests.%s" % (current.request.application, name)
        tests = loader.loadTestsFromName(path)
        suite.addTests(tests)
    if suite is not None:
        unittest.TextTestRunner(verbosity=2).run(suite)
    return

if __name__ == "__main__":

    run_suite(
        "eden",
        "s3"
    )

# END ========================================================================
