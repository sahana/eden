# -*- coding: utf-8 -*-
#
# Sahana Eden Unit Tests
#
# To run this test suite use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/suite.py

import unittest
import sys

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
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        status_code = len(result.failures) + len(result.errors)
        sys.exit(status_code)

    return

if __name__ == "__main__":

    run_suite("modules",
              "s3",
              "s3db",
              )

# END ========================================================================
