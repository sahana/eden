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
class DateRepresentationTests(unittest.TestCase):
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
    def testDatetimeRepresentDefaultFormat(self):
        """ Test date representation with default format """

        settings = current.deployment_settings
        date_format = settings.get_L10n_date_format()

        assertEqual = self.assertEqual
        represent = S3DateTime.date_represent

        date = datetime.date(2015, 5, 3)
        try:
            settings.L10n.date_format = "%Y-%m-%d"
            assertEqual(represent(date), "2015-05-03")

            settings.L10n.date_format = "%m/%d/%y"
            assertEqual(represent(date), "05/03/15")

            settings.L10n.date_format = "%a %d %b, %Y"
            assertEqual(represent(date), "Sun 03 May, 2015")

            settings.L10n.date_format = "%d-%b-%Y"
            assertEqual(represent(date), "03-May-2015")

        finally:
            # Restore default format
            settings.L10n.date_format = date_format

    # -------------------------------------------------------------------------
    def testDatetimeRepresentCustomFormat(self):
        """ Test custom formatting of dates (=overriding L10n setting) """

        settings = current.deployment_settings
        date_format = settings.get_L10n_date_format()

        assertEqual = self.assertEqual
        represent = S3DateTime.date_represent

        date = datetime.date(2015, 5, 3)
        try:
            # Set default format
            settings.L10n.date_format = "%Y-%m-%d"

            # Verify default format
            assertEqual(represent(date), "2015-05-03")

            # Override default format in call
            assertEqual(represent(date, format="%a %d %b, %Y"), "Sun 03 May, 2015")

        finally:
            # Restore default format
            settings.L10n.date_format = date_format

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
class TimeRepresentationTests(unittest.TestCase):
    """ Test S3DateTime.time_represent """

    # -------------------------------------------------------------------------
    def setUp(self):

        self.default_format = current.deployment_settings.get_L10n_time_format()
        current.deployment_settings.L10n.date_format = "%H:%M"

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.deployment_settings.L10n.date_format = self.default_format

    # -------------------------------------------------------------------------
    def testTimeRepresent(self):
        """ Test timezone-naive time representation """

        assertEqual = self.assertEqual
        represent = S3DateTime.time_represent

        value = datetime.time(10,45)
        rstr = represent(value)
        assertEqual(rstr, "10:45")

    # -------------------------------------------------------------------------
    def testDateTimeRepresent(self):
        """ Test timezone-naive datetime representation """

        assertEqual = self.assertEqual
        represent = S3DateTime.time_represent

        value = datetime.datetime(1988,9,13,10,45)
        rstr = represent(value)
        assertEqual(rstr, "10:45")

    # -------------------------------------------------------------------------
    def testTZAwareTimeRepresent(self):
        """ Test timezone-aware time representation """

        assertEqual = self.assertEqual
        represent = S3DateTime.time_represent

        session = current.session
        utc_offset = session.s3.utc_offset
        try:
            value = datetime.time(10,45)
            session.s3.utc_offset = +2
            rstr = represent(value, utc=True)
            assertEqual(rstr, "12:45")

            value = datetime.time(19,33)
            session.s3.utc_offset = +5
            rstr = represent(value, utc=True)
            assertEqual(rstr, "00:33")

            value = datetime.time(7,6)
            session.s3.utc_offset = -8
            rstr = represent(value, utc=True)
            assertEqual(rstr, "23:06")
        finally:
            # Restore offset
            session.s3.utc_offset = utc_offset

    # -------------------------------------------------------------------------
    def testTZAwareDateTimeRepresent(self):
        """ Test timezone-aware datetime representation """

        assertEqual = self.assertEqual
        represent = S3DateTime.time_represent

        session = current.session
        utc_offset = session.s3.utc_offset
        try:
            value = datetime.datetime(1988,6,21,10,45)
            session.s3.utc_offset = +2
            rstr = represent(value, utc=True)
            assertEqual(rstr, "12:45")

            value = datetime.datetime(1988,6,21,19,33)
            session.s3.utc_offset = +5
            rstr = represent(value, utc=True)
            assertEqual(rstr, "00:33")

            value = datetime.datetime(1988,6,21,7,6)
            session.s3.utc_offset = -8
            rstr = represent(value, utc=True)
            assertEqual(rstr, "23:06")
        finally:
            # Restore offset
            session.s3.utc_offset = utc_offset

    # -------------------------------------------------------------------------
    def testTimeRepresentDefaultFormat(self):
        """ Test time representation with default format """

        settings = current.deployment_settings
        time_format = settings.get_L10n_time_format()

        assertEqual = self.assertEqual
        represent = S3DateTime.time_represent

        time = datetime.time(16,33,48)
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

        time = datetime.time(16,33,48)
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
        value = datetime.datetime(1423,3,11,19,33)
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
        c.format_date(datetime.date(1977,3,15), dtfmt = "%Y-%m-%d")
        assertEqual(s3.calendar_test_format, S3TestCalendar.CALENDAR)

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
    def testDateTimeParsing(self):
        """ Test S3Calendar.parse_datetime """

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
        S3CalendarTests,
        S3DateTimeTests,
        DateRepresentationTests,
        TimeRepresentationTests,
    )

# END ========================================================================
