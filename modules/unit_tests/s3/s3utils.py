# -*- coding: utf-8 -*-
#
# Utils Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3utils.py
#
import unittest

from s3.s3utils import *
from s3.s3data import S3DataTable
from s3.s3datetime import S3Calendar, S3DefaultTZ

from unit_tests import run_suite

# =============================================================================
class S3TypeConverterTests(unittest.TestCase):
    """ Test S3TypeConverter """

    # -------------------------------------------------------------------------
    def setUp(self):

        settings = current.deployment_settings

        # Make sure date+time formats are standard
        self.date_format = settings.get_L10n_date_format()
        self.time_format = settings.get_L10n_time_format()
        settings.L10n.date_format = "%Y-%m-%d"
        settings.L10n.time_format = "%H:%M:%S"

        # Set timezone to UTC
        self.tzinfo = current.response.s3.tzinfo
        current.response.s3.tzinfo = S3DefaultTZ(0)

        # Set calendar to Gregorian
        self.calendar = current.calendar
        current.calendar = S3Calendar("Gregorian")

    # -------------------------------------------------------------------------
    def tearDown(self):

        settings = current.deployment_settings

        # Reset date and time format settings
        settings.L10n.date_format = self.date_format
        settings.L10n.time_format = self.time_format

        # Reset time zone
        current.response.s3.tzinfo = self.tzinfo

        # Restore current calendar
        current.calendar = self.calendar

    # -------------------------------------------------------------------------
    def testDate(self):
        """ Test date conversion """

        assertEqual = self.assertEqual
        settings = current.deployment_settings
        response = current.response

        convert = S3TypeConverter._date

        # Set custom format
        settings.L10n.date_format = "%d.%m.%Y"

        # Verify that ISO format always works
        result = convert("2011-10-01")
        assertEqual(result, datetime.date(2011, 10, 1))

        # Verify that local format always works
        result = convert("01.10.2011")
        assertEqual(result, datetime.date(2011, 10, 1))

        # Verify without offset
        response.s3.tzinfo = S3DefaultTZ(0)
        result = convert("2011-10-01")
        assertEqual(result, datetime.date(2011, 10, 1))

        # Verify with offset
        # => Date without time part means 08:00 local time zone,
        #    so 2 hours East means the same day UTC, 06:00
        response.s3.tzinfo = S3DefaultTZ(+2)
        result = convert("2011-10-01")
        assertEqual(result, datetime.date(2011, 10, 1))
        result = convert("01.05.2015")
        assertEqual(result, datetime.date(2015, 5, 1))

        # Cross into the next day
        # => Date without time part means 08:00 local time zone,
        #    so 11 hours East means previous day UTC, 21:00
        response.s3.tzinfo = S3DefaultTZ(+11)
        result = convert("2011-10-01")
        assertEqual(result, datetime.date(2011, 9, 30))

        # Reset to ISO format
        settings.L10n.date_format = "%Y-%m-%d"

        # Date+Time always convert to the exact UTC date
        # => 11 hours West of 22:00 is the same day
        result = convert("2011-10-01T22:00:00")
        assertEqual(result, datetime.date(2011, 10, 1))
        # => 11 hours West of 09:00 is the previous day
        result = convert("2011-10-01T09:00:00")
        assertEqual(result, datetime.date(2011, 9, 30))

        # Explicit timezone in string overrides default offset
        # => trailing Z means UTC
        result = convert("2011-10-01T09:00:00Z")
        assertEqual(result, datetime.date(2011, 10, 1))

    # -------------------------------------------------------------------------
    def testDateTime(self):
        """ Test date/time conversion """

        assertEqual = self.assertEqual
        settings = current.deployment_settings
        response = current.response

        convert = S3TypeConverter._datetime

        # Set custom format
        settings.L10n.date_format = "%d.%m.%Y"
        settings.L10n.time_format = "%H.%M"

        # Verify that ISO format always works
        result = convert("2011-10-01T16:37:00")
        assertEqual(result, datetime.datetime(2011, 10, 1, 16, 37, 0))

        # Verify that local format always works
        result = convert("01.10.2011 16.37")
        assertEqual(result, datetime.datetime(2011, 10, 1, 16, 37, 0))

        # Reset to ISO format
        settings.L10n.date_format = "%Y-%m-%d"
        settings.L10n.time_format = "%H:%M:S"

        # Verify without offset
        response.s3.tzinfo = S3DefaultTZ(0)
        result = convert("2011-10-01 07:30:00")
        assertEqual(result, datetime.datetime(2011, 10, 1, 7, 30, 0))

        # Verify with offset
        response.s3.tzinfo = S3DefaultTZ(+11)
        result = convert("2011-10-01T22:00:00")
        assertEqual(result, datetime.datetime(2011, 10, 1, 11, 0, 0))
        result = convert("2011-10-01T09:00:00")
        assertEqual(result, datetime.datetime(2011, 9, 30, 22, 0, 0))
        # Explicit timezone in string overrides offset
        result = convert("2011-10-01T09:00:00Z")
        assertEqual(result, datetime.datetime(2011, 10, 1, 9, 0, 0))

# =============================================================================
class S3FKWrappersTests(unittest.TestCase):
    """ Test has_foreign_key and get_foreign_key """

    # -------------------------------------------------------------------------
    def testHasForeignKey(self):
        """ Test has_foreign_key """

        ptable = current.s3db.pr_person
        self.assertFalse(s3_has_foreign_key(ptable.first_name))
        self.assertTrue(s3_has_foreign_key(ptable.pe_id))

        htable = current.s3db.hrm_human_resource
        self.assertFalse(s3_has_foreign_key(htable.start_date))
        self.assertTrue(s3_has_foreign_key(htable.person_id))

        # @todo: restore with a different list:reference
        #otable = s3db.org_organisation
        #self.assertTrue(s3_has_foreign_key(otable.multi_sector_id))
        #self.assertFalse(s3_has_foreign_key(otable.multi_sector_id, m2m=False))

    # -------------------------------------------------------------------------
    def testGetForeignKey(self):

        ptable = current.s3db.pr_person
        ktablename, key, multiple = s3_get_foreign_key(ptable.pe_id)
        self.assertEqual(ktablename, "pr_pentity")
        self.assertEqual(key, "pe_id")
        self.assertFalse(multiple)

        # @todo: restore with a different list:reference
        #otable = s3db.org_organisation
        #ktablename, key, multiple = s3_get_foreign_key(otable.multi_sector_id)
        #self.assertEqual(ktablename, "org_sector")
        #self.assertEqual(key, "id")
        #self.assertTrue(multiple)

        # @todo: restore with a different list:reference
        #ktablename, key, multiple = s3_get_foreign_key(otable.multi_sector_id, m2m=False)
        #self.assertEqual(ktablename, None)
        #self.assertEqual(key, None)
        #self.assertEqual(multiple, None)

# =============================================================================
if __name__ == "__main__":

    run_suite(
        S3TypeConverterTests,
        S3FKWrappersTests,
    )

# END ========================================================================
