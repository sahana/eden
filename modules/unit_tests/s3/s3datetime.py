# -*- coding: utf-8 -*-
#
# S3DateTime Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3datetime.py
#
import unittest

from lxml import etree

from s3dal import Field, Query
from s3.s3datetime import *
from s3.s3utils import *
from s3.s3rest import s3_request
from s3 import FS, S3Hierarchy, S3HierarchyFilter, s3_meta_fields

# =============================================================================
class S3DateTimeTests(unittest.TestCase):
    """ Tests for date/time parsing and formatting """

    def testOffsetParsing(self):

        data = [
            ("00:00", 0),
            ("+05:45", 20700),
            ("-03:00", -10800),
            ("02:00", 7200),
            ("0000", 0),
            ("+0800", 28800),
            ("-0600", -21600),
            ("0730", 27000),
            ("600", 21600),
            ("-130", -5400),
            ("00", 0),
            ("+01", 3600),
            ("-04", -14400),
            ("11", 39600),
            ("0", 0),
            ("+1", 3600),
            ("-4", -14400),
            ("11", 39600),
            ("0.0", 0),
            ("+3.5", 12600),
            ("-4.75", -17100),
            ("8.5", 30600),
            (0, 0),
            (+13, 46800),
            (-7.5, -27000),
            (6, 21600),
            (None, 0),
            ("", 0),
            ("UTC -0500", -18000), # backwards-compatibility
            ("UTC +0800", 28800),  # backwards-compatibility
            ("invalid", 0),
            ({"invalid": "type"}, 0),
        ]

        assertEqual = self.assertEqual
        get_offset_value = S3DateTime.get_offset_value
        for value, expected in data:
            result = get_offset_value(value)
            assertEqual(result, expected,
                        msg = "Invalid UTC offset for '%s' (%s): %s" % \
                              (value, type(value), result)
                        )

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

    run_suite(S3DateTimeTests,
              )

# END ========================================================================
