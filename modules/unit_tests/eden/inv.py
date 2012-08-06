# -*- coding: utf-8 -*-
#
# Inv Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/eden/inv.py
#
import unittest
import datetime

from gluon import *
from gluon.storage import Storage

# =============================================================================
class InvTests(unittest.TestCase):
    """ Inv Tests """

    def setUp(self):
        """ Set up location records """
        auth = current.auth
        auth.override = True

        self.location_code = Storage()
        self.location_ids = Storage()
        s3db = current.s3db


        #---------------------------------------------------------------------


        
    def tearDown(self):

        current.db.rollback()
        current.auth.override = False

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
        StatsTests,
    )

# END ========================================================================
