# -*- coding: utf-8 -*-
#
# S3DateTime Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3datetime.py
#
import datetime
import dateutil
import dateutil.tz
import unittest

from lxml import etree

from s3dal import Field, Query
from s3.s3datetime import *
from s3.s3utils import *
from s3.s3rest import s3_request
from s3 import FS, S3Hierarchy, S3HierarchyFilter, s3_meta_fields

from unit_tests import run_suite

# =============================================================================
class S3DateTimeTests(unittest.TestCase):
    """ Tests for date/time parsing and formatting """

    # -------------------------------------------------------------------------
    def setUp(self):

        settings = current.deployment_settings

        # Store current timezone info
        self.tzinfo = current.response.s3.tzinfo
        self.tzsetting = settings.L10n.timezone
        self.tzname = current.session.s3.tzname
        self.utc_offset = current.session.s3.utc_offset

    # -------------------------------------------------------------------------
    def tearDown(self):

        settings = current.deployment_settings

        # Restore timezone info
        current.response.s3.tzinfo = self.tzinfo
        if self.tzsetting:
            settings.L10n.timezone = tzsetting
        current.session.s3.tzname = self.tzname
        current.session.s3.utc_offset = self.utc_offset

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    def testToLocal(self):
        """ Test DateTime conversion to local timezone """

        response = current.response
        session = current.session

        assertEqual = self.assertEqual
        to_local = S3DateTime.to_local

        assertEqual(to_local(""), None)
        assertEqual(to_local(None), None)

        # Test with timezone reading from browser
        response.s3.tzinfo = None
        session.s3.tzname = "Europe/Stockholm"
        session.s3.utc_offset = "+0000"

        dt = datetime.datetime(2019, 1, 21, 1, 6, 0, 0)
        local = to_local(dt)
        assertEqual(local.hour, 2)   # UTC+1 in winter
        dt = datetime.datetime(2019, 5, 8, 19, 34, 0, 0)
        local = to_local(dt)
        assertEqual(local.hour, 21)  # UTC+2 in summer

        # Test with tz-aware datetime
        class WEST6(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(hours=-6)
        dt = datetime.datetime(2019, 5, 8, 19, 34, 0, 0, tzinfo=WEST6())
        local = to_local(dt)
        assertEqual(local.hour, 3)   # 6 hours WEST to UTC, then UTC+2 in summer

        # Disable deployment setting for timezone
        settings = current.deployment_settings
        tzsetting = settings.L10n.timezone
        if tzsetting:
            del settings.L10n.timezone

        # Verify fallback to default timezone
        response.s3.tzinfo = None
        session.s3.tzname = None
        session.s3.utc_offset = None
        settings.L10n.timezone = "America/Detroit"

        dt = datetime.datetime(2019, 1, 21, 1, 6, 0, 0)
        local = to_local(dt)
        assertEqual(local.day, 20)   # Previous day
        assertEqual(local.hour, 20)  # UTC-5 in winter

        dt = datetime.datetime(2019, 5, 8, 19, 34, 0, 0)
        local = to_local(dt)
        assertEqual(local.day, 8)    # Same day
        assertEqual(local.hour, 15)  # UTC-4 in summer

        # Verify that UTC offset setting overrides default timezone
        response.s3.tzinfo = None
        session.s3.tzname = None
        session.s3.utc_offset = "-0600"
        settings.L10n.timezone = "America/Detroit"

        dt = datetime.datetime(2019, 1, 21, 1, 6, 0, 0)
        local = to_local(dt)
        assertEqual(local.day, 20)   # Previous day
        assertEqual(local.hour, 19)  # UTC-6 fixed offset

        dt = datetime.datetime(2019, 5, 8, 19, 34, 0, 0)
        local = to_local(dt)
        assertEqual(local.day, 8)    # Same day
        assertEqual(local.hour, 13)  # UTC-6 fixed offset

        del settings.L10n.timezone

    # -------------------------------------------------------------------------
    def testToUTC(self):
        """ Test DateTime conversion to UTC """

        response = current.response
        session = current.session

        assertEqual = self.assertEqual
        to_utc = S3DateTime.to_utc

        assertEqual(to_utc(""), None)
        assertEqual(to_utc(None), None)

        # Test with timezone reading from browser
        response.s3.tzinfo = None
        session.s3.tzname = "Europe/Stockholm"
        session.s3.utc_offset = "+0000"

        dt = datetime.datetime(2019, 1, 21, 1, 6, 0, 0)
        local = to_utc(dt)
        assertEqual(local.hour, 0)   # UTC+1 in winter
        dt = datetime.datetime(2019, 5, 8, 19, 34, 0, 0)
        local = to_utc(dt)
        assertEqual(local.hour, 17)  # UTC+2 in summer

        # Test with tz-aware datetime
        class WEST6(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(hours=-6)
        dt = datetime.datetime(2019, 5, 8, 5, 23, 0, 0, tzinfo=WEST6())
        local = to_utc(dt)
        assertEqual(local.hour, 11)   # 6 hours WEST to UTC, then UTC+2 in summer

        # Disable deployment setting for timezone
        settings = current.deployment_settings
        tzsetting = settings.L10n.timezone
        if tzsetting:
            del settings.L10n.timezone

        # Verify fallback to default timezone
        response.s3.tzinfo = None
        session.s3.tzname = None
        session.s3.utc_offset = None
        settings.L10n.timezone = "America/Detroit"

        dt = datetime.datetime(2019, 1, 20, 20, 6, 0, 0)
        local = to_utc(dt)
        assertEqual(local.day, 21)   # Next day
        assertEqual(local.hour, 1)  # UTC-5 in winter

        dt = datetime.datetime(2019, 5, 8, 19, 34, 0, 0)
        local = to_utc(dt)
        assertEqual(local.day, 8)    # Same day
        assertEqual(local.hour, 23)  # UTC-4 in summer

        # Verify that UTC offset setting overrides default timezone
        response.s3.tzinfo = None
        session.s3.tzname = None
        session.s3.utc_offset = "-0600"
        settings.L10n.timezone = "America/Detroit"

        dt = datetime.datetime(2019, 1, 21, 20, 6, 0, 0)
        local = to_utc(dt)
        assertEqual(local.day, 22)   # Next day
        assertEqual(local.hour, 2)   # UTC-6 fixed offset

        dt = datetime.datetime(2019, 5, 8, 7, 34, 0, 0)
        local = to_utc(dt)
        assertEqual(local.day, 8)    # Same day
        assertEqual(local.hour, 13)  # UTC-6 fixed offset

        del settings.L10n.timezone

    # -------------------------------------------------------------------------
    def testDateToLocal(self):
        """ Test Date-only conversion to local timezone """

        response = current.response
        session = current.session

        assertTrue = self.assertTrue
        assertEqual = self.assertEqual

        response.s3.tzinfo = None
        session.s3.tzname = "Australia/Melbourne"
        session.s3.utc_offset = None

        dt = datetime.date(2019, 1, 21)
        local = S3DateTime.to_local(dt)
        assertTrue(isinstance(local, datetime.datetime)) # always a datetime
        assertEqual(local.day, 22) # Already on next day

        dt = datetime.date(2019, 7, 21)
        local = S3DateTime.to_local(dt)
        assertEqual(local.day, 22) # Already on next day

        # Converting forth and back must give the same date
        # (if time component is retained between conversions)
        assertEqual(dt, S3DateTime.to_utc(S3DateTime.to_local(dt).date()).date())

        response.s3.tzinfo = None
        session.s3.tzname = None
        session.s3.utc_offset = "+1200"

        dt = datetime.date(2019, 7, 21)
        local = S3DateTime.to_local(dt)
        assertEqual(local.day, 22) # Already on next day

        # Converting forth and back must give the same date
        # (if time component is retained between conversions)
        assertEqual(dt, S3DateTime.to_utc(S3DateTime.to_local(dt).date()).date())

        response.s3.tzinfo = None
        session.s3.tzname = "Europe/Berlin"
        session.s3.utc_offset = None

        dt = datetime.date(2019, 1, 20)
        local = S3DateTime.to_local(dt)
        assertEqual(local.day, 20) # Same day

        response.s3.tzinfo = None
        session.s3.tzname = "Pacific/Niue"
        session.s3.utc_offset = None

        dt = datetime.date(2019, 8, 13)
        local = S3DateTime.to_local(dt)
        assertEqual(local.day, 13) # Same day

    # -------------------------------------------------------------------------
    def testDateToUTC(self):
        """ Test Date-only conversion to UTC """

        response = current.response
        session = current.session

        assertTrue = self.assertTrue
        assertEqual = self.assertEqual

        response.s3.tzinfo = None
        session.s3.tzname = "NZ"
        session.s3.utc_offset = None

        dt = datetime.date(2019, 1, 21)
        local = S3DateTime.to_utc(dt)
        assertTrue(isinstance(local, datetime.datetime)) # always a datetime
        assertEqual(local.day, 20) # Still on previous day

        # Converting forth and back must give the same date
        assertEqual(dt, S3DateTime.to_local(S3DateTime.to_utc(dt).date()).date())

        response.s3.tzinfo = None
        session.s3.tzname = None
        session.s3.utc_offset = "+1200"

        dt = datetime.date(2019, 7, 21)
        local = S3DateTime.to_utc(dt)
        assertEqual(local.day, 20) # Still on previous day

        # Converting forth and back must give the same date
        assertEqual(dt, S3DateTime.to_local(S3DateTime.to_utc(dt).date()).date())

        response.s3.tzinfo = None
        session.s3.tzname = "Pacific/Niue"
        session.s3.utc_offset = None

        dt = datetime.date(2019, 8, 21)
        local = S3DateTime.to_utc(dt)
        assertEqual(local.day, 21) # Same day

# =============================================================================
class DateRepresentationTests(unittest.TestCase):
    """ Test S3DateTime.date_represent """

    #NONE = current.messages["NONE"]

    # -------------------------------------------------------------------------
    def setUp(self):

        # Set current calendar to Gregorian
        self.calendar = current.calendar
        current.calendar = S3Calendar("Gregorian")

        # Set default date format to ISO
        self.default_format = current.deployment_settings.get_L10n_date_format()
        current.deployment_settings.L10n.date_format = "%Y-%m-%d"

        # Store current timezone info
        self.tzinfo = current.response.s3.tzinfo

    # -------------------------------------------------------------------------
    def tearDown(self):

        # Restore calendar
        current.calendar = self.calendar

        # Restore default date format
        current.deployment_settings.L10n.date_format = self.default_format

        # Restore timezone info
        current.response.s3.tzinfo = self.tzinfo

    # -------------------------------------------------------------------------
    def testDateRepresent(self):
        """ Test date representation of datetime.date """

        date = datetime.date(2015, 5, 3)
        rstr = S3DateTime.date_represent(date)

        self.assertEqual(rstr, "2015-05-03")

    # -------------------------------------------------------------------------
    def testDateRepresentDefaultFormat(self):
        """ Test date representation with default format """

        settings = current.deployment_settings

        assertEqual = self.assertEqual
        represent = S3DateTime.date_represent

        date = datetime.date(2015, 5, 3)

        settings.L10n.date_format = "%Y-%m-%d"
        assertEqual(represent(date), "2015-05-03")

        settings.L10n.date_format = "%m/%d/%y"
        assertEqual(represent(date), "05/03/15")

        settings.L10n.date_format = "%a %d %b, %Y"
        assertEqual(represent(date), "Sun 03 May, 2015")

        settings.L10n.date_format = "%d-%b-%Y"
        assertEqual(represent(date), "03-May-2015")

    # -------------------------------------------------------------------------
    def testDateRepresentAlternativeCalendar(self):
        """ Test date representation with alternative calendar """

        assertEqual = self.assertEqual
        represent = S3DateTime.date_represent

        date = datetime.date(2015, 5, 3)

        # Represent with default calendar
        assertEqual(represent(date), "2015-05-03")

        # Override default calendar
        assertEqual(represent(date, calendar="Persian"), "1394-02-13")

        # Change default calendar
        current.calendar = S3Calendar("Persian")

        # Represent with default calendar
        assertEqual(represent(date), "1394-02-13")

        # Override default calendar
        assertEqual(represent(date, calendar="Gregorian"), "2015-05-03")

    # -------------------------------------------------------------------------
    def testDateRepresentCustomFormat(self):
        """ Test custom formatting of dates (=overriding L10n setting) """

        assertEqual = self.assertEqual
        represent = S3DateTime.date_represent

        date = datetime.date(2015, 5, 3)

        # Set default format
        current.deployment_settings.L10n.date_format = "%Y-%m-%d"

        # Verify default format
        assertEqual(represent(date), "2015-05-03")

        # Override default format in call
        assertEqual(represent(date, format="%a %d %b, %Y"), "Sun 03 May, 2015")

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

    # -------------------------------------------------------------------------
    def testEarlyDateRepresent(self):
        """ Test early dates representation (<1900) """

        date = datetime.date(1685, 3, 31)
        rstr = S3DateTime.date_represent(date)
        self.assertEqual(rstr, "1685-03-31")

        date = datetime.date(1473, 2, 19)
        rstr = S3DateTime.date_represent(date, format="%d-%b-%Y")
        self.assertEqual(rstr, "19-Feb-1473")

    # -------------------------------------------------------------------------
    def testDateTimeRepresent(self):
        """ Test date representation of datetime.datetime """

        date = datetime.datetime(1993, 6, 17, 22, 0, 0)
        rstr = S3DateTime.date_represent(date)

        self.assertEqual(rstr, "1993-06-17")

    # -------------------------------------------------------------------------
    def testTZAwareDateTimeRepresent(self):
        """ Test date representation of datetime.datetime (timezone-aware) """

        response = current.response
        utc = dateutil.tz.tzutc()

        assertEqual = self.assertEqual
        represent = S3DateTime.date_represent

        # Within same date
        date = datetime.datetime(1973, 4, 21, 15, 30, 0, tzinfo=utc)
        response.s3.tzinfo = S3DefaultTZ(+2)
        rstr = represent(date, utc=True)
        assertEqual(rstr, "1973-04-21")

        # Across date (eastern timezone)
        date = datetime.datetime(1993, 6, 17, 22, 0, 0, tzinfo=utc)
        response.s3.tzinfo = S3DefaultTZ(+6)
        rstr = represent(date, utc=True)
        assertEqual(rstr, "1993-06-18")

        # Across date (western timezone)
        date = datetime.datetime(1995, 4, 1, 3, 0, 0, tzinfo=utc)
        response.s3.tzinfo = S3DefaultTZ(-8)
        rstr = represent(date, utc=True)
        assertEqual(rstr, "1995-03-31")

# =============================================================================
class DateTimeRepresentationTests(unittest.TestCase):
    """ Test S3DateTime.datetime_represent """

    # -------------------------------------------------------------------------
    def setUp(self):

        settings = current.deployment_settings

        self.date_format = settings.get_L10n_date_format()
        self.time_format = settings.get_L10n_time_format()
        current.deployment_settings.L10n.date_format = "%Y-%m-%d"
        current.deployment_settings.L10n.time_format = "%H:%M:%S"

        # Set current calendar to Gregorian
        self.calendar = current.calendar
        current.calendar = S3Calendar("Gregorian")

        # Store current timezone info
        self.tzinfo = current.response.s3.tzinfo

    # -------------------------------------------------------------------------
    def tearDown(self):

        settings = current.deployment_settings

        settings.L10n.date_format = self.date_format
        settings.L10n.time_format = self.time_format

        # Restore current calendar
        current.calendar = self.calendar

        # Restore timezone info
        current.response.s3.tzinfo = self.tzinfo

    # -------------------------------------------------------------------------
    def testDateTimeRepresent(self):
        """ Test datetime representation """

        assertEqual = self.assertEqual
        represent = S3DateTime.datetime_represent

        dt = datetime.datetime(2015, 5, 3, 11, 38, 55)
        dtstr = represent(dt)
        assertEqual(dtstr, "2015-05-03 11:38:55")

    # -------------------------------------------------------------------------
    def testDateTimeRepresentDestructive(self):
        """ Test datetime representation (destructive) """

        assertEqual = self.assertEqual
        assertRaises = self.assertRaises

        represent = S3DateTime.datetime_represent

        dt = None
        dtstr = represent(dt)
        assertEqual(dtstr, current.messages.NONE)

        with assertRaises(TypeError):
            dtstr = represent(15)

        with assertRaises(TypeError):
            dtstr = represent("Invalid Type", utc=True)

    # -------------------------------------------------------------------------
    def testDateTimeRepresentAlternativeCalendar(self):
        """ Test date representation with alternative calendar """

        assertEqual = self.assertEqual
        represent = S3DateTime.datetime_represent

        date = datetime.datetime(2015, 5, 3, 14, 0, 0)

        # Represent with default calendar
        assertEqual(represent(date), "2015-05-03 14:00:00")

        # Override default calendar
        assertEqual(represent(date, calendar="Persian"), "1394-02-13 14:00:00")

        # Change default calendar
        current.calendar = S3Calendar("Persian")

        # Represent with default calendar
        assertEqual(represent(date), "1394-02-13 14:00:00")

        # Override default calendar
        assertEqual(represent(date, calendar="Gregorian"), "2015-05-03 14:00:00")

    # -------------------------------------------------------------------------
    def testTZAwareDateTimeRepresent(self):
        """ Test datetime representation (timezone-aware) """

        response = current.response

        utc = dateutil.tz.tzutc()

        assertEqual = self.assertEqual
        represent = S3DateTime.datetime_represent

        # Within same date
        dt = datetime.datetime(1973, 4, 21, 15, 30, 0, tzinfo=utc)
        response.s3.tzinfo = S3DefaultTZ(+2)
        dtstr = represent(dt, utc=True)
        assertEqual(dtstr, "1973-04-21 17:30:00")

        # Across date (eastern timezone)
        dt = datetime.datetime(1993, 6, 17, 22, 0, 0, tzinfo=utc)
        response.s3.tzinfo = S3DefaultTZ(+6)
        dtstr = represent(dt, utc=True)
        assertEqual(dtstr, "1993-06-18 04:00:00")

        # Across date (western timezone)
        dt = datetime.datetime(1995, 4, 1, 3, 0, 0, tzinfo=utc)
        response.s3.tzinfo = S3DefaultTZ(-8)
        dtstr = represent(dt, utc=True)
        assertEqual(dtstr, "1995-03-31 19:00:00")

        # ...with utc=False (to verify the effectiveness of the parameter)
        dt = datetime.datetime(1995, 4, 1, 3, 0, 0, tzinfo=utc)
        response.s3.tzinfo = S3DefaultTZ(-8)
        dtstr = represent(dt, utc=False)
        assertEqual(dtstr, "1995-04-01 03:00:00")

    # -------------------------------------------------------------------------
    def testDatetimeRepresentDefaultFormat(self):
        """ Test date representation with default format """

        settings = current.deployment_settings
        assertEqual = self.assertEqual
        represent = S3DateTime.datetime_represent

        dt = datetime.datetime(2015, 5, 3, 13, 38, 13)

        settings.L10n.date_format = "%Y-%m-%d"
        settings.L10n.time_format = "%H:%M:%S"
        assertEqual(represent(dt), "2015-05-03 13:38:13")

        settings.L10n.date_format = "%m/%d/%y"
        settings.L10n.time_format = "%I:%M %p"
        assertEqual(represent(dt), "05/03/15 01:38 PM")

    # -------------------------------------------------------------------------
    def testDatetimeRepresentCustomFormat(self):
        """ Test date representation with custom format (=override L10n setting) """

        settings = current.deployment_settings
        assertEqual = self.assertEqual
        represent = S3DateTime.datetime_represent

        dt = datetime.datetime(2015, 5, 3, 13, 38, 13)

        settings.L10n.date_format = "%Y-%m-%d"
        settings.L10n.time_format = "%H:%M:%S"
        assertEqual(represent(dt), "2015-05-03 13:38:13")
        assertEqual(represent(dt, format="%m/%d/%y %I:%M %p"), "05/03/15 01:38 PM")

    # -------------------------------------------------------------------------
    def testEarlyDateTimeRepresent(self):
        """ Test early dates representation (<1900) """

        assertEqual = self.assertEqual
        represent = S3DateTime.datetime_represent

        dt = datetime.datetime(1685, 3, 31, 14, 3, 19)

        dtstr = represent(dt)
        assertEqual(dtstr, "1685-03-31 14:03:19")

        dt = datetime.datetime(1473, 2, 19, 5, 45, 0)
        rstr = represent(dt, format="%d-%b-%Y %H:%M")
        assertEqual(rstr, "19-Feb-1473 05:45")

    # -------------------------------------------------------------------------
    def testMicrosecondElimination(self):
        """ Verify elimination of microseconds in datetime_represent """

        assertEqual = self.assertEqual
        represent = S3DateTime.datetime_represent

        dt = datetime.datetime(2015, 5, 3, 11, 38, 55, 99)
        dtstr = represent(dt, format="%m/%d/%y %I:%M %f")
        assertEqual(dtstr, "05/03/15 11:38 000000")

# =============================================================================
class TimeRepresentationTests(unittest.TestCase):
    """ Test S3DateTime.time_represent """

    # -------------------------------------------------------------------------
    def setUp(self):

        self.default_format = current.deployment_settings.get_L10n_time_format()
        current.deployment_settings.L10n.date_format = "%H:%M"

        # Store current timezone info
        self.tzinfo = current.response.s3.tzinfo

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.deployment_settings.L10n.date_format = self.default_format

        # Restore timezone info
        current.response.s3.tzinfo = self.tzinfo

    # -------------------------------------------------------------------------
    def testTimeRepresent(self):
        """ Test timezone-naive time representation """

        assertEqual = self.assertEqual
        represent = S3DateTime.time_represent

        value = datetime.time(10, 45)
        rstr = represent(value)
        assertEqual(rstr, "10:45")

    # -------------------------------------------------------------------------
    def testDateTimeRepresent(self):
        """ Test timezone-naive datetime representation """

        assertEqual = self.assertEqual
        represent = S3DateTime.time_represent

        value = datetime.datetime(1988, 9, 13, 10, 45)
        rstr = represent(value)
        assertEqual(rstr, "10:45")

    # -------------------------------------------------------------------------
    def testTZAwareTimeRepresent(self):
        """ Test timezone-aware time representation """

        response = current.response

        assertEqual = self.assertEqual
        represent = S3DateTime.time_represent

        value = datetime.time(10, 45)
        response.s3.tzinfo = S3DefaultTZ(+2)
        rstr = represent(value, utc=True)
        assertEqual(rstr, "12:45")

        value = datetime.time(19, 33)
        response.s3.tzinfo = S3DefaultTZ(+5)
        rstr = represent(value, utc=True)
        assertEqual(rstr, "00:33")

        value = datetime.time(7, 6)
        response.s3.tzinfo = S3DefaultTZ(-8)
        rstr = represent(value, utc=True)
        assertEqual(rstr, "23:06")

    # -------------------------------------------------------------------------
    def testTZAwareDateTimeRepresent(self):
        """ Test timezone-aware datetime representation """

        response = current.response

        assertEqual = self.assertEqual
        represent = S3DateTime.time_represent

        value = datetime.datetime(1988, 6, 21, 10, 45)
        response.s3.tzinfo = S3DefaultTZ(+2)
        rstr = represent(value, utc=True)
        assertEqual(rstr, "12:45")

        value = datetime.datetime(1988, 6, 21, 19, 33)
        response.s3.tzinfo = S3DefaultTZ(+5)
        rstr = represent(value, utc=True)
        assertEqual(rstr, "00:33")

        value = datetime.datetime(1988, 6, 21, 7, 6)
        response.s3.tzinfo = S3DefaultTZ(-8)
        rstr = represent(value, utc=True)
        assertEqual(rstr, "23:06")

    # -------------------------------------------------------------------------
    def testTimeRepresentDefaultFormat(self):
        """ Test time representation with default format """

        settings = current.deployment_settings
        time_format = settings.get_L10n_time_format()

        assertEqual = self.assertEqual
        represent = S3DateTime.time_represent

        time = datetime.time(16, 33, 48)
        try:
            settings.L10n.time_format = "%H.%M.%S"
            assertEqual(represent(time), "16.33.48")

            settings.L10n.time_format = "%I:%M %p"
            assertEqual(represent(time), "04:33 PM")

            settings.L10n.time_format = "%H:%M"
            assertEqual(represent(time), "16:33")

        finally:
            # Restore default format
            settings.L10n.time_format = time_format

    # -------------------------------------------------------------------------
    def testTimeRepresentCustomFormat(self):
        """ Test time representation with default format """

        settings = current.deployment_settings
        time_format = settings.get_L10n_time_format()

        assertEqual = self.assertEqual
        represent = S3DateTime.time_represent

        time = datetime.time(16, 33, 48)
        try:
            # Set default format
            settings.L10n.time_format = "%H.%M.%S"

            # Verify default format
            assertEqual(represent(time), "16.33.48")

            # Override default format in call
            assertEqual(represent(time, format="%I:%M %p"), "04:33 PM")

        finally:
            # Restore default format
            settings.L10n.time_format = time_format

    # -------------------------------------------------------------------------
    def testTimeRepresentDestructive(self):
        """ Destructive tests for S3DateTime.time_represent """

        assertEqual = self.assertEqual
        assertRaises = self.assertRaises

        represent = S3DateTime.time_represent

        NONE = current.messages["NONE"]

        # Test with None
        rstr = represent(None)
        assertEqual(rstr, NONE)

        # Test with invalid types
        with assertRaises(TypeError):
            rstr = represent(15)

        with assertRaises(TypeError):
            rstr = represent("Invalid Type", utc=True)

        # Verify behavior for dates<1900
        value = datetime.datetime(1423, 3, 11, 19, 33)
        rstr = represent(value)
        assertEqual(rstr, "19:33")

# =============================================================================
class S3TestCalendar(S3Calendar):
    """ Mockup S3Calendar Subclass """

    CALENDAR = "Test"

    def _parse(self, dtstr, dtfmt):
        """ Custom _parse to set a marker if called """

        current.response.s3.calendar_test_parse = self.CALENDAR
        return super(S3TestCalendar, self)._parse(dtstr, dtfmt)

    def _format(self, dt, dtfmt):
        """ Custom _format to set a marker if called """

        current.response.s3.calendar_test_format = self.CALENDAR
        return super(S3TestCalendar, self)._format(dt, dtfmt)

    def _gdate(self, timetuple):
        """ Custom _gdate to set a marker if called """

        current.response.s3.calendar_test_gdate = self.CALENDAR
        return super(S3TestCalendar, self)._gdate(timetuple)

    def _cdate(self, timetuple):
        """ Custom _gdate to set a marker if called """

        current.response.s3.calendar_test_cdate = self.CALENDAR
        return super(S3TestCalendar, self)._cdate(timetuple)

# =============================================================================
class S3CalendarTests(unittest.TestCase):
    """ Test S3Calendar base class """

    # -------------------------------------------------------------------------
    def setUp(self):

        # Remove the current calendar setting
        settings = current.deployment_settings
        self.calendar_setting = settings.get_L10n_calendar()
        settings.L10n.pop("calendar", None)

    # -------------------------------------------------------------------------
    def tearDown(self):

        # Restore the calendar setting
        calendar_setting = self.calendar_setting
        if calendar_setting:
            current.deployment_settings.L10n.calendar = calendar_setting

    # -------------------------------------------------------------------------
    def testConstructionWithDefaults(self):
        """ Test calendar construction with defaults """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        CALENDAR = S3Calendar.CALENDAR

        # Instantiate a calendar
        c = S3Calendar()

        # Verify lazy behavior
        assertEqual(c._name, None)
        assertEqual(c._calendar, None)

        # Verify defaults
        assertEqual(c.name, CALENDAR)
        assertTrue(type(c.calendar) is S3Calendar)

    # -------------------------------------------------------------------------
    def testConstructionWithSubclass(self):
        """ Test calendar construction with alternative defaults """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        CALENDAR = "Test"
        settings = current.deployment_settings

        # Modify setting
        settings.L10n.calendar = CALENDAR
        assertEqual(settings.get_L10n_calendar(), CALENDAR)

        # Instantiate a calendar
        c = S3Calendar()

        # Verify lazy behavior
        assertEqual(c._name, None)
        assertEqual(c._calendar, None)

        # Register the custom class
        c._calendars[CALENDAR] = S3TestCalendar

        # Verify defaults
        assertEqual(c.name, CALENDAR)
        assertTrue(type(c.calendar) is S3TestCalendar)

    # -------------------------------------------------------------------------
    def testConstructionWithUndefinedSubclass(self):
        """ Test calendar construction with alternative defaults """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        CALENDAR = "Test"
        settings = current.deployment_settings

        # Modify setting
        settings.L10n.calendar = CALENDAR
        assertEqual(settings.get_L10n_calendar(), CALENDAR)

        # Instantiate a calendar
        c = S3Calendar()

        # Verify lazy behavior
        assertEqual(c._name, None)
        assertEqual(c._calendar, None)

        # Verify defaults (name is custom, but calendar is default)
        assertEqual(c.name, CALENDAR)
        assertTrue(type(c.calendar) is S3Calendar)

    # -------------------------------------------------------------------------
    def testSubclassing(self):
        """ Verify that subclass methods are called """

        assertEqual = self.assertEqual
        s3 = current.response.s3

        CALENDAR = "Test"
        settings = current.deployment_settings

        # Modify setting
        settings.L10n.calendar = CALENDAR
        assertEqual(settings.get_L10n_calendar(), CALENDAR)

        # Instantiate a calendar
        c = S3Calendar()

        # Register the custom class
        c._calendars[CALENDAR] = S3TestCalendar

        # Call parse_date
        s3.calendar_test_parse = None
        s3.calendar_test_gdate = None
        c.parse_date("2014-09-21", dtfmt = "%Y-%m-%d")
        assertEqual(s3.calendar_test_parse, S3TestCalendar.CALENDAR)
        assertEqual(s3.calendar_test_gdate, S3TestCalendar.CALENDAR)

        # Call format_date
        s3.calendar_test_format = None
        c.format_date(datetime.date(1977, 3, 15), dtfmt = "%Y-%m-%d")
        assertEqual(s3.calendar_test_format, S3TestCalendar.CALENDAR)
        assertEqual(s3.calendar_test_cdate, S3TestCalendar.CALENDAR)

    # -------------------------------------------------------------------------
    def testParsing(self):
        """ Test parsing of date/time strings """

        c = S3Calendar()

        assertEqual = self.assertEqual
        parse = c.calendar._parse

        tt = parse("2005-04-01T00:00:03", "%Y-%m-%dT%H:%M:%S")
        assertEqual(tt[:6], (2005, 4, 1, 0, 0, 3))

        tt = parse("01/04/05", "%d/%m/%y")
        assertEqual(tt[:6], (2005, 4, 1, 0, 0, 0))

        tt = parse("15:34", "%H:%M")
        assertEqual(tt, (1900, 1, 1, 15, 34, 0))

    # -------------------------------------------------------------------------
    def testParsingDestructive(self):
        """ Test parsing of date/time strings (destructive) """

        c = S3Calendar()

        assertRaises = self.assertRaises
        assertEqual = self.assertEqual
        parse = c.calendar._parse

        with assertRaises(ValueError):
            parse("2005-04-01", "%Y-%m-%dT%H:%M:%S")

        with assertRaises(ValueError):
            parse("1975-30-11 10:30", "%d/%m/%y")

        with assertRaises(TypeError):
            parse(None, "%Y-%m-%d")

        with assertRaises(TypeError):
            parse(633, "%Y-%m-%d")

    # -------------------------------------------------------------------------
    def testCalendarDate(self):
        """ Test conversion of Gregorian time tuple to calendar time tuple """

        c = S3Calendar()

        convert = c.calendar._cdate
        assertEqual = self.assertEqual

        tt = (2018, 5, 8, 11, 38, 0)

        # Convert tuple
        assertEqual(convert(tt), tt) # Gregorian calendar does nothing

    # -------------------------------------------------------------------------
    def testGregorianDate(self):
        """ Test conversion of calendar time tuple to Gregorian time tuple """

        c = S3Calendar()

        convert = c.calendar._gdate
        assertEqual = self.assertEqual

        tt = (2018, 5, 8, 11, 38, 0)

        # Convert tuple
        assertEqual(convert(tt), tt) # Gregorian calendar does nothing

    # -------------------------------------------------------------------------
    def testDateParsing(self):
        """ Test S3Calendar.parse_date """

        c = S3Calendar()
        parse = c.parse_date

        assertEqual = self.assertEqual

        # Test with ISOFORMAT
        dtstr = "1925-11-21"
        dt = parse(dtstr)
        assertEqual(dt, datetime.date(1925, 11, 21))

        # Test with local format
        settings = current.deployment_settings
        date_format = settings.get_L10n_date_format()
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            dtstr = "08/05/1983"
            dt = parse(dtstr, local=True)
            assertEqual(dt, datetime.date(1983, 5, 8))
        finally:
            settings.L10n.date_format = date_format

        # Test with format override
        dtstr = "09.01.2004"
        dt = parse(dtstr, dtfmt="%d.%m.%Y")
        assertEqual(dt, datetime.date(2004, 1, 9))
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            dt = parse(dtstr, dtfmt="%d.%m.%Y", local=True)
            assertEqual(dt, datetime.date(2004, 1, 9))
        finally:
            settings.L10n.date_format = date_format

        # Test with None
        dtstr = None
        dt = parse(dtstr)
        assertEqual(dt, None)

        # Test with invalid type
        dtstr = 96
        dt = parse(dtstr)
        assertEqual(dt, None)

        # Test with invalid value
        dtstr = "Invalid Value"
        dt = parse(dtstr)
        assertEqual(dt, None)

    # -------------------------------------------------------------------------
    def testDateTimeParsing(self):
        """ Test S3Calendar.parse_datetime """

        c = S3Calendar()
        parse = c.parse_datetime

        assertEqual = self.assertEqual

        # Test with ISOFORMAT
        dtstr = "1925-11-21T13:01:41"
        dt = parse(dtstr)
        assertEqual(dt, datetime.datetime(1925, 11, 21, 13, 1, 41))

        # Test with local format
        settings = current.deployment_settings
        date_format = settings.get_L10n_date_format()
        time_format = settings.get_L10n_time_format()
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            settings.L10n.time_format = "%H.%M"
            dtstr = "24/08/1964 13.21"
            dt = parse(dtstr, local=True)
            assertEqual(dt, datetime.datetime(1964, 8, 24, 13, 21, 0))
        finally:
            settings.L10n.date_format = date_format
            settings.L10n.time_format = time_format

        # Test with format override
        dtstr = "09.01.2004 10:13:44"
        dt = parse(dtstr, dtfmt="%d.%m.%Y %H:%M:%S")
        assertEqual(dt, datetime.datetime(2004, 1, 9, 10, 13, 44))
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            settings.L10n.time_format = "%H.%M"
            dt = parse(dtstr,  dtfmt="%d.%m.%Y %H:%M:%S", local=True)
            assertEqual(dt, datetime.datetime(2004, 1, 9, 10, 13, 44))
        finally:
            settings.L10n.date_format = date_format
            settings.L10n.time_format = time_format

        # Test with None
        dtstr = None
        dt = parse(dtstr)
        assertEqual(dt, None)

        # Test with invalid type
        dtstr = 96
        dt = parse(dtstr)
        assertEqual(dt, None)

        # Test with invalid value
        dtstr = "Invalid Value"
        dt = parse(dtstr)
        assertEqual(dt, None)

    # -------------------------------------------------------------------------
    def testDateFormatting(self):
        """ Test S3Calendar.format_date """

        c = S3Calendar()
        render = c.format_date

        assertEqual = self.assertEqual
        assertRaises = self.assertRaises

        # Test with ISOFORMAT
        dt = datetime.date(1925, 11, 21)
        dtstr = render(dt)
        assertEqual(dtstr, "1925-11-21")

        # Test with local format
        settings = current.deployment_settings
        date_format = settings.get_L10n_date_format()
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            dt = datetime.date(1983, 5, 8)
            dtstr = render(dt, local=True)
            assertEqual(dtstr, "08/05/1983")
        finally:
            settings.L10n.date_format = date_format

        # Test with format override
        dt = datetime.date(2004, 1, 9)
        dtstr = render(dt, dtfmt="%d.%m.%Y")
        assertEqual(dtstr, "09.01.2004")
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            dtstr = render(dt, dtfmt="%d.%m.%Y", local=True)
            assertEqual(dtstr, "09.01.2004")
        finally:
            settings.L10n.date_format = date_format

        # Test with None
        dt = None
        dtstr = render(dt)
        assertEqual(dtstr, current.messages.NONE)

        # Test with invalid type
        dt = 96
        with assertRaises(TypeError):
            render(dt)

    # -------------------------------------------------------------------------
    def testDateTimeFormatting(self):
        """ Test S3Calendar.format_datetime """

        c = S3Calendar()
        render = c.format_datetime

        assertEqual = self.assertEqual
        assertRaises = self.assertRaises

        # Test with ISOFORMAT
        dt = datetime.datetime(1925, 11, 21, 13, 1, 41)
        dtstr = render(dt)
        assertEqual(dtstr, "1925-11-21T13:01:41")

        # Test with local format
        settings = current.deployment_settings
        date_format = settings.get_L10n_date_format()
        time_format = settings.get_L10n_time_format()
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            settings.L10n.time_format = "%H.%M"
            dt = datetime.datetime(1964, 8, 24, 13, 21, 0)
            dtstr = render(dt, local=True)
            assertEqual(dtstr, "24/08/1964 13.21")
        finally:
            settings.L10n.date_format = date_format
            settings.L10n.time_format = time_format

        # Test with format override
        dt = datetime.datetime(2004, 1, 9, 10, 13, 44)
        dtstr = render(dt, dtfmt="%d.%m.%Y %H:%M:%S")
        assertEqual(dtstr, "09.01.2004 10:13:44")
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            settings.L10n.time_format = "%H.%M"
            dtstr = render(dt,  dtfmt="%d.%m.%Y %H:%M:%S", local=True)
            assertEqual(dtstr, "09.01.2004 10:13:44")
        finally:
            settings.L10n.date_format = date_format
            settings.L10n.time_format = time_format

        # Test with None
        dt = None
        dtstr = render(dt)
        assertEqual(dtstr, current.messages.NONE)

        # Test with invalid type
        dt = 96
        with assertRaises(TypeError):
            render(dt)

    # -------------------------------------------------------------------------
    def testGregorianJDConversion(self):
        """ Tests for Gregorian Date to/from Julian Day conversion """

        test_dates = ((1973, 4, 21, 2441793.5),
                      (1345, 5, 13, 2212443.5),
                      (2017, 11, 8, 2458065.5),
                      )

        c = S3Calendar()
        gregorian_to_jd = c._gregorian_to_jd
        jd_to_gregorian = c._jd_to_gregorian

        assertEqual = self.assertEqual

        for year, month, day, jd in test_dates:
            assertEqual(gregorian_to_jd(year, month, day), jd)
            assertEqual(jd_to_gregorian(jd), (year, month, day))

# =============================================================================
class S3PersianCalendarTests(unittest.TestCase):
    """ Test cases for Persian (=Solar Hijri) calendar """

    def setUp(self):

        self.test_dates = (((1973, 4, 21), 2441793.5, (1352, 2, 1)),
                           ((1345, 5, 13), 2212443.5, (724, 2, 23)),
                           ((1988, 3, 1), 2447221.5, (1366, 12, 11)),
                           ((2017, 11, 8), 2458065.5, (1396, 8, 17)),
                           )

    # -------------------------------------------------------------------------
    def testJDConversion(self):
        """
            Test conversion of Solar Hijri date to JD and Gregorian date
            (low-level routines)
        """

        test_dates = self.test_dates

        assertEqual = self.assertEqual

        c = S3Calendar("Persian")

        gregorian_to_jd = c._gregorian_to_jd
        jd_to_gregorian = c._jd_to_gregorian

        from_jd = c.calendar.from_jd
        to_jd = c.calendar.to_jd

        for gdate, jd, cdate in test_dates:

            jd_ = gregorian_to_jd(gdate[0], gdate[1], gdate[2])
            assertEqual(jd_, jd)

            cd_ = from_jd(jd_)
            assertEqual(cd_, cdate)

            jd_ = to_jd(cd_[0], cd_[1], cd_[2])
            assertEqual(jd_, jd)

            gd_ = jd_to_gregorian(jd_)
            assertEqual(gd_, gdate)

    # -------------------------------------------------------------------------
    def testCalendarDate(self):
        """
            Test direct conversion between Solar Hijri and Gregorian
            timetuples (cdate/gdate)
        """

        test_dates = self.test_dates

        assertEqual = self.assertEqual

        c = S3Calendar("Persian")
        to_gregorian = c.calendar._gdate
        from_gregorian = c.calendar._cdate

        for gdate, jd, cdate in test_dates:

            # Conversion from Solar Hijri to Gregorian
            timetuple = (cdate[0], cdate[1], cdate[2], 8, 0, 0)
            gdate_ = to_gregorian(timetuple)
            assertEqual(gdate_[:3], gdate)

            # Conversion from Gregorian to Solar Hijri
            timetuple = (gdate[0], gdate[1], gdate[2], 8, 0, 0)
            cdate_ = from_gregorian(timetuple)
            assertEqual(cdate_[:3], cdate)

    # -------------------------------------------------------------------------
    def testDateParsing(self):
        """ Test S3Calendar.parse_date """

        c = S3Calendar("Persian")
        parse = c.parse_date

        assertEqual = self.assertEqual

        # Test with ISOFORMAT
        dtstr = "1304-08-30"
        dt = parse(dtstr)
        assertEqual(dt, datetime.date(1925, 11, 21))

        # Test with local format
        settings = current.deployment_settings
        date_format = settings.get_L10n_date_format()
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            dtstr = "18/02/1362"
            dt = parse(dtstr, local=True)
            assertEqual(dt, datetime.date(1983, 5, 8))
        finally:
            settings.L10n.date_format = date_format

        # Test with format override
        dtstr = "19.10.1382"
        dt = parse(dtstr, dtfmt="%d.%m.%Y")
        assertEqual(dt, datetime.date(2004, 1, 9))
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            dt = parse(dtstr, dtfmt="%d.%m.%Y", local=True)
            assertEqual(dt, datetime.date(2004, 1, 9))
        finally:
            settings.L10n.date_format = date_format

        # Test with None
        dtstr = None
        dt = parse(dtstr)
        assertEqual(dt, None)

        # Test with invalid type
        dtstr = 96
        dt = parse(dtstr)
        assertEqual(dt, None)

        # Test with invalid value
        dtstr = "Invalid Value"
        dt = parse(dtstr)
        assertEqual(dt, None)

    # -------------------------------------------------------------------------
    def testDateTimeParsing(self):
        """ Test S3Calendar.parse_datetime """

        c = S3Calendar("Persian")
        parse = c.parse_datetime

        assertEqual = self.assertEqual

        # Test with ISOFORMAT
        dtstr = "1304-08-30T13:01:41"
        dt = parse(dtstr)
        assertEqual(dt, datetime.datetime(1925, 11, 21, 13, 1, 41))

        # Test with local format
        settings = current.deployment_settings
        date_format = settings.get_L10n_date_format()
        time_format = settings.get_L10n_time_format()
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            settings.L10n.time_format = "%H.%M"
            dtstr = "02/06/1343 13.21"
            dt = parse(dtstr, local=True)
            assertEqual(dt, datetime.datetime(1964, 8, 24, 13, 21, 0))
        finally:
            settings.L10n.date_format = date_format
            settings.L10n.time_format = time_format

        # Test with format override
        dtstr = "19.10.1382 10:13:44"
        dt = parse(dtstr, dtfmt="%d.%m.%Y %H:%M:%S")
        assertEqual(dt, datetime.datetime(2004, 1, 9, 10, 13, 44))
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            settings.L10n.time_format = "%H.%M"
            dt = parse(dtstr,  dtfmt="%d.%m.%Y %H:%M:%S", local=True)
            assertEqual(dt, datetime.datetime(2004, 1, 9, 10, 13, 44))
        finally:
            settings.L10n.date_format = date_format
            settings.L10n.time_format = time_format

        # Test with None
        dtstr = None
        dt = parse(dtstr)
        assertEqual(dt, None)

        # Test with invalid type
        dtstr = 96
        dt = parse(dtstr)
        assertEqual(dt, None)

        # Test with invalid value
        dtstr = "Invalid Value"
        dt = parse(dtstr)
        assertEqual(dt, None)

    # -------------------------------------------------------------------------
    def testDateFormatting(self):
        """ Test S3Calendar.format_date """

        c = S3Calendar("Persian")
        render = c.format_date

        assertEqual = self.assertEqual
        assertRaises = self.assertRaises

        # Test with ISOFORMAT
        dt = datetime.date(1925, 11, 21)
        dtstr = render(dt)
        assertEqual(dtstr, "1304-08-30")

        # Test with local format
        settings = current.deployment_settings
        date_format = settings.get_L10n_date_format()
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            dt = datetime.date(1983, 5, 8)
            dtstr = render(dt, local=True)
            assertEqual(dtstr, "18/02/1362")
        finally:
            settings.L10n.date_format = date_format

        # Test with format override
        dt = datetime.date(2004, 2, 9)
        dtstr = render(dt, dtfmt="%d-%b-%Y")
        assertEqual(dtstr, "20-Bah-1382")
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            dtstr = render(dt, dtfmt="%d.%B %Y", local=True)
            assertEqual(dtstr, "20.Bahman 1382")
        finally:
            settings.L10n.date_format = date_format

        # Test with None
        dt = None
        dtstr = render(dt)
        assertEqual(dtstr, current.messages.NONE)

        # Test with invalid type
        dt = 96
        with assertRaises(TypeError):
            render(dt)

    # -------------------------------------------------------------------------
    def testDateTimeFormatting(self):
        """ Test S3Calendar.format_datetime """

        c = S3Calendar("Persian")
        render = c.format_datetime

        assertEqual = self.assertEqual
        assertRaises = self.assertRaises

        # Test with ISOFORMAT
        dt = datetime.datetime(1925, 11, 21, 13, 1, 41)
        dtstr = render(dt)
        assertEqual(dtstr, "1304-08-30T13:01:41")

        # Test with local format
        settings = current.deployment_settings
        date_format = settings.get_L10n_date_format()
        time_format = settings.get_L10n_time_format()
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            settings.L10n.time_format = "%H.%M"
            dt = datetime.datetime(1964, 8, 24, 13, 21, 0)
            dtstr = render(dt, local=True)
            assertEqual(dtstr, "02/06/1343 13.21")
        finally:
            settings.L10n.date_format = date_format
            settings.L10n.time_format = time_format

        # Test with format override
        dt = datetime.datetime(2004, 1, 9, 10, 13, 44)
        dtstr = render(dt, dtfmt="%d.%m.%Y %H:%M:%S")
        assertEqual(dtstr, "19.10.1382 10:13:44")
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            settings.L10n.time_format = "%H.%M"
            dtstr = render(dt,  dtfmt="%d.%B %Y %H:%M:%S", local=True)
            assertEqual(dtstr, "19.Day 1382 10:13:44")
        finally:
            settings.L10n.date_format = date_format
            settings.L10n.time_format = time_format

        # Test with None
        dt = None
        dtstr = render(dt)
        assertEqual(dtstr, current.messages.NONE)

        # Test with invalid type
        dt = 96
        with assertRaises(TypeError):
            render(dt)

# =============================================================================
class S3NepaliCalendarTests(unittest.TestCase):
    """ Test cases for Nepali (=Bikram Samvat) calendar """

    def setUp(self):

        self.test_dates = (((1973, 4, 21), 2441793.5, (2030, 1, 9)),
                           ((1988, 3, 1), 2447221.5, (2044, 11, 18)),
                           ((2017, 11, 8), 2458065.5, (2074, 7, 22)),
                           )

    # -------------------------------------------------------------------------
    def testJDConversion(self):
        """
            Test conversion of Bikram Samvat date to JD and Gregorian date
            (low-level routines)
        """

        test_dates = self.test_dates

        assertEqual = self.assertEqual

        c = S3Calendar("Nepali")

        gregorian_to_jd = c._gregorian_to_jd
        jd_to_gregorian = c._jd_to_gregorian

        from_jd = c.calendar.from_jd
        to_jd = c.calendar.to_jd

        for gdate, jd, cdate in test_dates:

            jd_ = gregorian_to_jd(gdate[0], gdate[1], gdate[2])
            assertEqual(jd_, jd)

            cd_ = from_jd(jd_)
            assertEqual(cd_, cdate)

            jd_ = to_jd(cd_[0], cd_[1], cd_[2])
            assertEqual(jd_, jd)

            gd_ = jd_to_gregorian(jd_)
            assertEqual(gd_, gdate)

    # -------------------------------------------------------------------------
    def testCalendarDate(self):
        """
            Test direct conversion between Bikram Samvat and Gregorian
            timetuples (cdate/gdate)
        """

        test_dates = self.test_dates

        assertEqual = self.assertEqual

        c = S3Calendar("Nepali")
        to_gregorian = c.calendar._gdate
        from_gregorian = c.calendar._cdate

        for gdate, jd, cdate in test_dates:

            # Conversion from Bikram Samvat to Gregorian
            timetuple = (cdate[0], cdate[1], cdate[2], 8, 0, 0)
            gdate_ = to_gregorian(timetuple)
            assertEqual(gdate_[:3], gdate)

            # Conversion from Gregorian to Bikram Samvat
            timetuple = (gdate[0], gdate[1], gdate[2], 8, 0, 0)
            cdate_ = from_gregorian(timetuple)
            assertEqual(cdate_[:3], cdate)

    # -------------------------------------------------------------------------
    def testDateParsing(self):
        """ Test S3Calendar.parse_date """

        c = S3Calendar("Nepali")
        parse = c.parse_date

        assertEqual = self.assertEqual

        # Test with ISOFORMAT
        dtstr = "1982-08-06"
        dt = parse(dtstr)
        assertEqual(dt, datetime.date(1925, 11, 21))

        # Test with local format
        settings = current.deployment_settings
        date_format = settings.get_L10n_date_format()
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            dtstr = "25/01/2040"
            dt = parse(dtstr, local=True)
            assertEqual(dt, datetime.date(1983, 5, 8))
        finally:
            settings.L10n.date_format = date_format

        # Test with format override
        dtstr = "25.09.2060"
        dt = parse(dtstr, dtfmt="%d.%m.%Y")
        assertEqual(dt, datetime.date(2004, 1, 9))
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            dt = parse(dtstr, dtfmt="%d.%m.%Y", local=True)
            assertEqual(dt, datetime.date(2004, 1, 9))
        finally:
            settings.L10n.date_format = date_format

        # Test with None
        dtstr = None
        dt = parse(dtstr)
        assertEqual(dt, None)

        # Test with invalid type
        dtstr = 96
        dt = parse(dtstr)
        assertEqual(dt, None)

        # Test with invalid value
        dtstr = "Invalid Value"
        dt = parse(dtstr)
        assertEqual(dt, None)

    # -------------------------------------------------------------------------
    def testDateTimeParsing(self):
        """ Test S3Calendar.parse_datetime """

        c = S3Calendar("Nepali")
        parse = c.parse_datetime

        assertEqual = self.assertEqual

        # Test with ISOFORMAT
        dtstr = "1982-08-06T13:01:41"
        dt = parse(dtstr)
        assertEqual(dt, datetime.datetime(1925, 11, 21, 13, 1, 41))

        # Test with local format
        settings = current.deployment_settings
        date_format = settings.get_L10n_date_format()
        time_format = settings.get_L10n_time_format()
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            settings.L10n.time_format = "%H.%M"
            dtstr = "09/05/2021 13.21"
            dt = parse(dtstr, local=True)
            assertEqual(dt, datetime.datetime(1964, 8, 24, 13, 21, 0))
        finally:
            settings.L10n.date_format = date_format
            settings.L10n.time_format = time_format

        # Test with format override
        dtstr = "25.Paush 2060 10:13:44"
        dt = parse(dtstr, dtfmt="%d.%B %Y %H:%M:%S")
        assertEqual(dt, datetime.datetime(2004, 1, 9, 10, 13, 44))
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            settings.L10n.time_format = "%H.%M"
            dt = parse(dtstr,  dtfmt="%d.%B %Y %H:%M:%S", local=True)
            assertEqual(dt, datetime.datetime(2004, 1, 9, 10, 13, 44))
        finally:
            settings.L10n.date_format = date_format
            settings.L10n.time_format = time_format

        # Test with None
        dtstr = None
        dt = parse(dtstr)
        assertEqual(dt, None)

        # Test with invalid type
        dtstr = 96
        dt = parse(dtstr)
        assertEqual(dt, None)

        # Test with invalid value
        dtstr = "Invalid Value"
        dt = parse(dtstr)
        assertEqual(dt, None)

    # -------------------------------------------------------------------------
    def testDateFormatting(self):
        """ Test S3Calendar.format_date """

        c = S3Calendar("Nepali")
        render = c.format_date

        assertEqual = self.assertEqual
        assertRaises = self.assertRaises

        # Test with ISOFORMAT
        dt = datetime.date(1925, 11, 21)
        dtstr = render(dt)
        assertEqual(dtstr, "1982-08-06")

        # Test with local format
        settings = current.deployment_settings
        date_format = settings.get_L10n_date_format()
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            dt = datetime.date(1983, 5, 8)
            dtstr = render(dt, local=True)
            assertEqual(dtstr, "25/01/2040")
        finally:
            settings.L10n.date_format = date_format

        # Test with format override
        dt = datetime.date(2004, 2, 9)
        dtstr = render(dt, dtfmt="%d-%b-%Y")
        assertEqual(dtstr, "26-Ma-2060")
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            dtstr = render(dt, dtfmt="%d.%B %Y", local=True)
            assertEqual(dtstr, "26.Mangh 2060")
        finally:
            settings.L10n.date_format = date_format

        # Test with None
        dt = None
        dtstr = render(dt)
        assertEqual(dtstr, current.messages.NONE)

        # Test with invalid type
        dt = 96
        with assertRaises(TypeError):
            render(dt)

    # -------------------------------------------------------------------------
    def testDateTimeFormatting(self):
        """ Test S3Calendar.format_datetime """

        c = S3Calendar("Nepali")
        render = c.format_datetime

        assertEqual = self.assertEqual
        assertRaises = self.assertRaises

        # Test with ISOFORMAT
        dt = datetime.datetime(1925, 11, 21, 13, 1, 41)
        dtstr = render(dt)
        assertEqual(dtstr, "1982-08-06T13:01:41")

        # Test with local format
        settings = current.deployment_settings
        date_format = settings.get_L10n_date_format()
        time_format = settings.get_L10n_time_format()
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            settings.L10n.time_format = "%H.%M"
            dt = datetime.datetime(1964, 8, 24, 13, 21, 0)
            dtstr = render(dt, local=True)
            assertEqual(dtstr, "09/05/2021 13.21")
        finally:
            settings.L10n.date_format = date_format
            settings.L10n.time_format = time_format

        # Test with format override
        dt = datetime.datetime(2004, 1, 9, 10, 13, 44)
        dtstr = render(dt, dtfmt="%d.%m.%Y %H:%M:%S")
        assertEqual(dtstr, "25.09.2060 10:13:44")
        try:
            settings.L10n.date_format = "%d/%m/%Y"
            settings.L10n.time_format = "%H.%M"
            dtstr = render(dt,  dtfmt="%d.%B %Y %H:%M:%S", local=True)
            assertEqual(dtstr, "25.Paush 2060 10:13:44")
        finally:
            settings.L10n.date_format = date_format
            settings.L10n.time_format = time_format

        # Test with None
        dt = None
        dtstr = render(dt)
        assertEqual(dtstr, current.messages.NONE)

        # Test with invalid type
        dt = 96
        with assertRaises(TypeError):
            render(dt)

# =============================================================================
class S3DateTimeParserTests(unittest.TestCase):
    """ Tests for S3DateTimeParser """

    # -------------------------------------------------------------------------
    def testConstruction(self):
        """ Test parser construction """

        assertRaises = self.assertRaises

        c = S3Calendar()
        dtfmt = "%Y-%m-%d"

        # TypeError for invalid argument lists
        with assertRaises(TypeError):
            parser = S3DateTimeParser()

        with assertRaises(TypeError):
            # Invalid format
            parser = S3DateTimeParser(c)

        with assertRaises(TypeError):
            # Calendar required
            parser = S3DateTimeParser(None, dtfmt)

        with assertRaises(TypeError):
            # Invalid format type
            parser = S3DateTimeParser(c, 8)

        parser = S3DateTimeParser(c, dtfmt)

    # -------------------------------------------------------------------------
    def testDateParsing(self):
        """ Test date parsing """

        assertEqual = self.assertEqual
        assertRaises = self.assertRaises

        now = current.request.utcnow

        test_dates = (("%Y-%m-%d", "2009-04-16", (2009, 4, 16, 0, 0, 0)),
                      ("%d.%m.%Y", "1.8.1936", (1936, 8, 1, 0, 0, 0)),
                      ("%d/%m/%y", None, "TypeError"),
                      ("%d/%m/%y", "16.04.1678", "ValueError"),
                      ("%d/%m/%Y", "31/04/1678", (1678, 5, 1, 0, 0, 0)),
                      ("%d/%m/%Y", "16/04/1678", (1678, 4, 16, 0, 0, 0)),
                      ("%d/%m/%Y", "03/4/1785", (1785, 4, 3, 0, 0, 0)),
                      ("%d/%m/%y", "16/04/78", (1978, 4, 16, 0, 0, 0)),
                      ("%d/%m", "16/04", (now.year, 4, 16, 0, 0, 0)),
                      ("%d.%B", "16.January", (now.year, 1, 16, 0, 0, 0)),
                      ("%d-%b-%Y", "27-Mar-2005", (2005, 3, 27, 0, 0, 0)),
                      )

        c = S3Calendar("Gregorian")

        for dtfmt, string, timetuple in test_dates:

            parser = S3DateTimeParser(c, dtfmt)

            if timetuple == "ValueError":
                with assertRaises(ValueError):
                    result = parser.parse(string)
            elif timetuple == "TypeError":
                with assertRaises(TypeError):
                    result = parser.parse(string)
            else:
                result = parser.parse(string)
                assertEqual(result, timetuple)

    # -------------------------------------------------------------------------
    def testDateTimeParsing(self):
        """ Test date+time parsing """

        assertEqual = self.assertEqual
        assertRaises = self.assertRaises

        now = current.request.utcnow

        test_dates = (("%Y-%m-%d %H:%M:%S", "2009-04-16 13:54:20", (2009, 4, 16, 13, 54, 20)),
                      ("%d.%m.%Y %H:%M", "1.8.1936 15:38", (1936, 8, 1, 15, 38, 0)),
                      ("%d/%m/%Y %H:%M", None, "TypeError"),
                      ("%d/%m/%Y %H:%M", "16/04/1678", "ValueError"),
                      ("%d/%m/%Y %H:%M", "16/04/1678 23:59", (1678, 4, 16, 23, 59, 0)),
                      ("%d/%m %I:%M %p", "16/04 12:30 am", (now.year, 4, 16, 0, 30, 0)),
                      ("%d/%m %I:%M %p", "8/4 12:30 am", (now.year, 4, 8, 0, 30, 0)),
                      ("%d-%b-%Y %I:%M %p", "31-Apr-2005 0:30am", (2005, 5, 1, 0, 30, 0)),
                      )

        c = S3Calendar("Gregorian")

        for dtfmt, string, timetuple in test_dates:

            parser = S3DateTimeParser(c, dtfmt)

            if timetuple == "ValueError":
                with assertRaises(ValueError):
                    result = parser.parse(string)
            elif timetuple == "TypeError":
                with assertRaises(TypeError):
                    result = parser.parse(string)
            else:
                result = parser.parse(string)
                assertEqual(result, timetuple)

    # -------------------------------------------------------------------------
    def testDateParsingPersian(self):
        """ Test date parsing """

        assertEqual = self.assertEqual
        assertRaises = self.assertRaises

        now = current.request.utcnow
        today = (now.year, now.month, now.day, 0, 0, 0)

        c = S3Calendar("Persian")
        cyear, cmonth, cday = c.calendar._cdate(today)[:3]

        test_dates = (("%Y-%m-%d", "1352-02-01", (1352, 2, 1, 0, 0, 0)),
                      ("%d.%m.%Y", "18.5.1384", (1384, 5, 18, 0, 0, 0)),
                      ("%d/%m/%y", None, "TypeError"),
                      ("%d/%m/%y", "32.04.1378", "ValueError"),
                      ("%d.%m.%Y", "32.04.1378", "ValueError"),
                      ("%d/%m/%y", "31/7/84", (1384, 8, 1, 0, 0, 0)),
                      ("%d/%m/%y", "30/12/84", (1385, 1, 1, 0, 0, 0)),
                      ("%d/%m/%Y", "16/04/78", (78, 4, 16, 0, 0, 0)),
                      ("%d.%B", "16. Shahrivar", (cyear, 6, 16, 0, 0, 0)),
                      ("%d-%b-%Y", "27-Tir-1393", (1393, 4, 27, 0, 0, 0)),
                      )

        for dtfmt, string, timetuple in test_dates:

            parser = S3DateTimeParser(c, dtfmt)

            if timetuple == "ValueError":
                with assertRaises(ValueError):
                    result = parser.parse(string)
            elif timetuple == "TypeError":
                with assertRaises(TypeError):
                    result = parser.parse(string)
            else:
                result = parser.parse(string)
                assertEqual(result, timetuple)

    # -------------------------------------------------------------------------
    def testDateTimeParsingPersian(self):
        """ Test date+time parsing """

        assertEqual = self.assertEqual
        assertRaises = self.assertRaises

        now = current.request.utcnow
        today = (now.year, now.month, now.day, 0, 0, 0)

        c = S3Calendar("Persian")
        cyear, cmonth, cday = c.calendar._cdate(today)[:3]

        test_dates = (("%Y-%m-%d %H:%M:%S", "1352-2-1 17:34:20", (1352, 2, 1, 17, 34, 20)),
                      ("%d.%m.%Y %H:%M", "1.8.1394 15:38", (1394, 8, 1, 15, 38, 0)),
                      ("%d/%m/%Y %H:%M", None, "TypeError"),
                      ("%d/%m/%Y %H:%M", "16/04/1378", "ValueError"),
                      ("%d/%m/%Y %H:%M", "16/04/1378 23:59", (1378, 4, 16, 23, 59, 0)),
                      ("%d/%m %I:%M %p", "16/07 12:30 am", (cyear, 7, 16, 0, 30, 0)),
                      ("%d/%m %I:%M %p", "8/4 12:30 am", (cyear, 4, 8, 0, 30, 0)),
                      ("%d-%b-%Y %I:%M %p", "18-Aba-1393 0:30am", (1393, 8, 18, 0, 30, 0)),
                      )

        for dtfmt, string, timetuple in test_dates:

            parser = S3DateTimeParser(c, dtfmt)

            if timetuple == "ValueError":
                with assertRaises(ValueError):
                    result = parser.parse(string)
            elif timetuple == "TypeError":
                with assertRaises(TypeError):
                    result = parser.parse(string)
            else:
                result = parser.parse(string)
                assertEqual(result, timetuple)

# =============================================================================
class RelativeDateTimeTests(unittest.TestCase):

    def test_relative_datetime(self):

        from dateutil.relativedelta import relativedelta
        now = current.request.utcnow

        assertEqual = self.assertEqual

        parse = s3_relative_datetime

        assertEqual(parse("NOW"), now)
        assertEqual(parse("-1D"), now - relativedelta(days=1))
        assertEqual(parse("-5s"), now - relativedelta(seconds=5))
        assertEqual(parse("+24h"), now + relativedelta(hours=24))
        assertEqual(parse("+1Y3M"), now + relativedelta(months=15))
        assertEqual(parse("-10m"), now - relativedelta(minutes=10))
        assertEqual(parse("+1Y-12M"), now)

        assertEqual(parse(None), None)
        assertEqual(parse(""), None)
        assertEqual(parse("invalid"), None)
        assertEqual(parse("1997-11-03T19:55:07"), None)

# =============================================================================
if __name__ == "__main__":

    run_suite(
        S3CalendarTests,
        S3DateTimeTests,
        DateRepresentationTests,
        TimeRepresentationTests,
        DateTimeRepresentationTests,
        S3PersianCalendarTests,
        S3NepaliCalendarTests,
        S3DateTimeParserTests,
        RelativeDateTimeTests,
    )

# END ========================================================================
