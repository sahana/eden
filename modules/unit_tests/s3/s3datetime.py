# -*- coding: utf-8 -*-
#
# S3DateTime Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3datetime.py
#
import datetime
import dateutil
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
class S3DateRepresentationTests(unittest.TestCase):
    """ Test S3DateTime.date_represent """

    #NONE = current.messages["NONE"]

    # -------------------------------------------------------------------------
    def setUp(self):

        self.default_format = current.deployment_settings.get_L10n_date_format()
        current.deployment_settings.L10n.date_format = "%Y-%m-%d"

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.deployment_settings.L10n.date_format = self.default_format

    # -------------------------------------------------------------------------
    def testDateRepresent(self):
        """ Test date representation of datetime.date """

        date = datetime.date(2015, 5, 3)
        rstr = S3DateTime.date_represent(date)

        self.assertEqual(rstr, "2015-05-03")

    # -------------------------------------------------------------------------
    def testDateRepresentDestructive(self):
        """ Destructive tests for S3DateTime.date_represent """

        assertEqual = self.assertEqual
        assertRaises = self.assertRaises
        represent = S3DateTime.date_represent

        NONE = current.messages["NONE"]

        rstr = represent(None)
        assertEqual(rstr, NONE)

        with assertRaises(TypeError):
            rstr = represent(15)

        with assertRaises(TypeError):
            rstr = represent("Invalid Type", utc=True)

        date = datetime.datetime(1874, 6, 7, 12, 0, 0)
        rstr = S3DateTime.date_represent(date)
        self.assertEqual(rstr, "1874-06-07")

    # -------------------------------------------------------------------------
    def testDatetimeRepresent(self):
        """ Test date representation of datetime.datetime """

        date = datetime.datetime(1993, 6, 17, 22, 0, 0)
        rstr = S3DateTime.date_represent(date)

        self.assertEqual(rstr, "1993-06-17")

    # -------------------------------------------------------------------------
    def testTZAwareDatetimeRepresent(self):
        """ Test date representation of datetime.datetime (timezone-aware) """

        session = current.session

        utc = dateutil.tz.tzutc()

        assertEqual = self.assertEqual
        represent = S3DateTime.date_represent

        utc_offset = session.s3.utc_offset
        try:
            # Within same date
            date = datetime.datetime(1973, 4, 21, 15, 30, 0, tzinfo=utc)
            session.s3.utc_offset = +2
            rstr = represent(date, utc=True)
            assertEqual(rstr, "1973-04-21")

            # Across date (eastern timezone)
            date = datetime.datetime(1993, 6, 17, 22, 0, 0, tzinfo=utc)
            session.s3.utc_offset = +6
            rstr = represent(date, utc=True)
            assertEqual(rstr, "1993-06-18")

            # Across date (western timezone)
            date = datetime.datetime(1995, 4, 1, 03, 0, 0, tzinfo=utc)
            session.s3.utc_offset = -8
            rstr = represent(date, utc=True)
            assertEqual(rstr, "1995-03-31")

        finally:
            # Restore offset
            session.s3.utc_offset = utc_offset

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
        S3DateTimeTests,
        S3DateRepresentationTests,
    )

# END ========================================================================
