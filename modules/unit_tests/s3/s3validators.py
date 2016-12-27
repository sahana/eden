# -*- coding: utf-8 -*-
#
# Validators Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3validators.py
#
import unittest
from gluon import current

from s3.s3datetime import S3Calendar
from s3.s3fields import *
from s3.s3validators import *

from unit_tests import run_suite

# =============================================================================
class ISLatTest(unittest.TestCase):
    """
        Latitude has to be in decimal degrees between -90 & 90
        - we can convert D/M/S or D�M'S" format into decimal degrees:
        Zero padded, separated by spaces or : or (d, m, s) or (�, ', ") or run together and followed by cardinal direction initial (N,S) Note: Only seconds can have decimals places. A decimal point with no trailing digits is invalid.
        Matches
        40:26:46N | 40�26'47?N | 40d 26m 47s N | 90 00 00.0 | 89 59 50.4141 S | 00 00 00.0
        Non-Matches
        90 00 00.001 N | 9 00 00.00 N | 9 00 00.00 | 90 61 50.4121 S | -90 48 50. N | 90 00 00. N | 00 00 00.
    """

    pass

# =============================================================================
class ISLonTest(unittest.TestCase):
    """
        Longitude has to be in decimal degrees between -180 & 180
        - we can convert D/M/S format into decimal degrees
        Zero padded, separated by spaces or : or (d, m, s) or (�, ', ") or run together and followed by cardinal direction initial (E,W) Note: Only seconds can have decimals places. A decimal point with no trailing digits is invalid.
        Matches
        079:56:55W | 079�58'36?W | 079d 58' 36? W | 180 00 00.0 | 090 29 20.4 E | 000 00 00.0
        Non-Matches
        180 00 00.001 E | 79 00 00.00 E | -79 00 00.00 | 090 29 20.4 E | -090 29 20.4 E | 180 00 00. E | 000 00 00.
    """

    pass

# =============================================================================
class ISONEOFLazyRepresentationTests(unittest.TestCase):

    def setUp(self):

        s3db = current.s3db
        current.auth.override = True
        current.deployment_settings.org.branches = True

        orgs = [Storage(name="ISONEOF%s" % i,
                        acronym="IOO%s" % i)
                for i in xrange(5)]

        ids = []
        table = s3db.org_organisation
        for org in orgs:
            org_id = table.insert(**org)
            org["id"] = org_id
            s3db.update_super(table, org)
            ids.append(org_id)

        self.ids = ids
        self.orgs = orgs

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.deployment_settings.org.branches = False
        current.auth.override = False
        current.db.rollback()

    # -------------------------------------------------------------------------
    def testIsOneOfBuildSet(self):

        renderer = S3Represent(lookup="org_organisation")

        db = current.db
        table = current.s3db.org_organisation
        validator = IS_ONE_OF(db(table.id.belongs(self.ids)),
                              "org_organisation.id",
                              renderer)

        options = Storage(validator.options())
        for org in self.orgs:
            self.assertTrue(str(org.id) in options)
            self.assertEqual(options[str(org.id)], org.name)
        self.assertEqual(renderer.queries, 0)

    # -------------------------------------------------------------------------
    def testOrgOrganisationRepresent(self):

        s3db = current.s3db
        renderer = s3db.org_OrganisationRepresent()

        db = current.db
        table = s3db.org_organisation
        validator = IS_ONE_OF(db(table.id.belongs(self.ids)),
                              "org_organisation.id",
                              renderer)

        options = Storage(validator.options())
        for org in self.orgs:
            self.assertTrue(str(org.id) in options)
            self.assertEqual(options[str(org.id)],
                             "%s (%s)" % (org.name, org.acronym))
        self.assertEqual(renderer.queries, 1) # using custom query

        renderer = s3db.org_OrganisationRepresent(parent=False)

        db = current.db
        table = current.s3db.org_organisation
        validator = IS_ONE_OF(db(table.id.belongs(self.ids)),
                              "org_organisation.id",
                              renderer)

        options = Storage(validator.options())
        for org in self.orgs:
            self.assertTrue(str(org.id) in options)
            self.assertEqual(options[str(org.id)],
                             "%s (%s)" % (org.name, org.acronym))
        self.assertEqual(renderer.queries, 0) # using default query

        renderer = s3db.org_OrganisationRepresent(parent=False,
                                                  acronym=False)

        db = current.db
        table = current.s3db.org_organisation
        validator = IS_ONE_OF(db(table.id.belongs(self.ids)),
                              "org_organisation.id",
                              renderer)

        options = Storage(validator.options())
        for org in self.orgs:
            self.assertTrue(str(org.id) in options)
            self.assertEqual(options[str(org.id)], org.name)
        self.assertEqual(renderer.queries, 0) # using default query

# =============================================================================
class IS_PHONE_NUMBER_Tests(unittest.TestCase):
    """ Test IS_PHONE_NUMBER single phone number validator """

    # -------------------------------------------------------------------------
    def testStandardNotationRequirement(self):
        """ Test phone number validation with standard notation requirement """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        validate = IS_PHONE_NUMBER(international=False)

        number = "(021) 3847589"
        value, error = validate(number)
        assertEqual(error, None)
        assertEqual(value, "(021) 3847589")

        number = "0049-681-5049321"
        value, error = validate(number)
        assertEqual(error, None)
        assertEqual(value, "0049-681-5049321")

        number = " 1-992-883742"
        value, error = validate(number)
        assertEqual(error, None)
        assertEqual(value, "1-992-883742")

        number = "1.123.736489"
        value, error = validate(number)
        assertEqual(error, None)
        assertEqual(value, "1.123.736489")

        number = "+44848958493 "
        value, error = validate(number)
        assertEqual(error, None)
        assertEqual(value, "+44848958493")

        number = "(021) 3ADF589"
        value, error = validate(number)
        assertNotEqual(error, None)

        number = "Test"
        value, error = validate(number)
        assertNotEqual(error, None)

        # @todo: this is still recognized as valid, as is "-1"
        #number = "1"
        #value, error = validate(number)
        #assertNotEqual(error, None)

        number = "+44848958493/+44736282167"
        value, error = validate(number)
        assertNotEqual(error, None)

        number = None
        value, error = validate(number)
        assertNotEqual(error, None)

        number = ""
        value, error = validate(number)
        assertNotEqual(error, None)

    # -------------------------------------------------------------------------
    def testInternationalFormat(self):
        """ Test phone number validation with international notation requirement """

        # Store current setting
        settings = current.deployment_settings
        current_setting = settings.get_msg_require_international_phone_numbers()

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        validate = IS_PHONE_NUMBER(international=True)

        # Turn on notation requirement globally
        settings.msg.require_international_phone_numbers = True

        number = "+46-73-3847589"
        value, error = validate(number)
        assertEqual(error, None)
        assertEqual(value, "+46733847589")

        number = "+49.681.5049321"
        value, error = validate(number)
        assertEqual(error, None)
        assertEqual(value, "+496815049321")

        number = "+1992883742"
        value, error = validate(number)
        assertEqual(error, None)
        assertEqual(value, "+1992883742")

        number = "(021) 36374589"
        value, error = validate(number)
        assertNotEqual(error, None)

        number = "Test"
        value, error = validate(number)
        assertNotEqual(error, None)

        number = "1-364-283745"
        value, error = validate(number)
        assertNotEqual(error, None)

        number = None
        value, error = validate(number)
        assertNotEqual(error, None)

        number = ""
        value, error = validate(number)
        assertNotEqual(error, None)

        # Turn off notation requirement globally
        settings.msg.require_international_phone_numbers = False

        number = "1-364-283745"
        value, error = validate(number)
        assertEqual(error, None)
        assertEqual(value, "1-364-283745")

        # Restore current setting
        settings.msg.require_international_phone_numbers = current_setting

# =============================================================================
class IS_UTC_DATETIME_Tests(unittest.TestCase):
    """ Test IS_UTC_DATETIME validator """

    # -------------------------------------------------------------------------
    def setUp(self):

        settings = current.deployment_settings

        # Make sure date and time formats are standard
        self.date_format = settings.get_L10n_date_format()
        self.time_format = settings.get_L10n_time_format()
        settings.L10n.date_format = "%Y-%m-%d"
        settings.L10n.time_format = "%H:%M:%S"

        # Set timezone to UTC
        session = current.session
        self.utc_offset = session.s3.utc_offset
        session.s3.utc_offset = 0

        # Set current calendar to Gregorian
        self.calendar = current.calendar
        current.calendar = S3Calendar("Gregorian")

    # -------------------------------------------------------------------------
    def tearDown(self):

        settings = current.deployment_settings

        # Reset date and time format settings
        settings.L10n.date_format = self.date_format
        settings.L10n.time_format = self.time_format

        # Reset time zone
        current.session.s3.utc_offset = self.utc_offset

        # Restore current calendar
        current.calendar = self.calendar

    # -------------------------------------------------------------------------
    def testValidation(self):
        """ Test validation with valid datetime string """

        validate = IS_UTC_DATETIME()

        assertEqual = self.assertEqual

        # Test timezone-naive string
        dtstr = "2011-11-19 14:00:00"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 19, 14, 0, 0))

        # Test timezone-aware string
        dtstr = "2011-11-19 14:00:00+0500"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 19, 9, 0, 0))

        # Change time zone
        current.session.s3.utc_offset = -8

        # Test timezone-naive string
        dtstr = "2011-11-19 14:00:00"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 19, 22, 0, 0))

        # Test timezone-aware string
        dtstr = "2011-11-19 14:00:00+0500"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 19, 9, 0, 0))

    # -------------------------------------------------------------------------
    def testValidationWithDateTime(self):
        """ Test validation with datetime """

        validate = IS_UTC_DATETIME()

        class EAST5(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(hours=5)

        assertEqual = self.assertEqual

        # Test timezone-naive datetime
        dt = datetime.datetime(2011, 11, 19, 14, 0, 0)
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 19, 14, 0, 0))

        # Test timezone-aware datetime
        dt = datetime.datetime(2011, 11, 19, 14, 0, 0, tzinfo=EAST5())
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 19, 9, 0, 0))

        # Change time zone
        current.session.s3.utc_offset = -8

        # Test timezone-naive datetime
        dt = datetime.datetime(2011, 11, 19, 14, 0, 0)
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 19, 22, 0, 0))

        # Test timezone-aware datetime
        dt = datetime.datetime(2011, 11, 19, 14, 0, 0, tzinfo=EAST5())
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 19, 9, 0, 0))

    # -------------------------------------------------------------------------
    def testValidationWithDate(self):
        """ Test validation with date """

        validate = IS_UTC_DATETIME()

        class EAST5(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(hours=5)

        assertEqual = self.assertEqual

        # Check that date defaults to 8:00 hours (UTC)
        dt = datetime.date(2011, 11, 19)
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 19, 8, 0, 0))

        # Change time zone
        current.session.s3.utc_offset = -8

        # Check that date defaults to 08:00 hours (Western time zone)
        dt = datetime.date(2011, 11, 19)
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 19, 16, 0, 0))

        # Change time zone
        current.session.s3.utc_offset = +11

        # Check that date defaults to 08:00 hours (Extreme Eastern time zone)
        dt = datetime.date(2011, 11, 19)
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 18, 21, 0, 0))

    # -------------------------------------------------------------------------
    def testValidationDestructive(self):
        """ Test validation with invalid input """

        validate = IS_UTC_DATETIME()

        assertEqual = self.assertEqual

        # Test with invalid datetime string
        dtstr = "Invalid Value"
        value, error = validate(dtstr)
        assertEqual(error, validate.error_message)
        assertEqual(value, dtstr)

        # Test with invalid type
        dtstr = 33
        value, error = validate(dtstr)
        assertEqual(error, validate.error_message)
        assertEqual(value, dtstr)

        # Test with None
        dtstr = None
        value, error = validate(dtstr)
        assertEqual(error, validate.error_message)
        assertEqual(value, dtstr)

        # Test invalid UTC offset
        dtstr = "2011-11-19 14:00:00+3600"
        value, error = validate(dtstr)
        assertEqual(error, validate.offset_error)
        assertEqual(value, dtstr)

    # -------------------------------------------------------------------------
    def testValidationWithAlternativeCalendar(self):
        """ Test validation with calendar-override """

        assertEqual = self.assertEqual

        # Test default=Gregorian, override=Persian
        current.calendar = S3Calendar("Gregorian")
        validate = IS_UTC_DATETIME(calendar="Persian")

        dtstr = "1390-08-28 14:00:00"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 19, 14, 0, 0))

        dtstr_ = validate.formatter(value)
        assertEqual(dtstr_, dtstr)

        # Test default=Persian, override=Gregorian
        current.calendar = S3Calendar("Persian")
        validate = IS_UTC_DATETIME(calendar="Gregorian")

        dtstr = "2011-11-19 14:00:00"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 19, 14, 0, 0))

        dtstr_ = validate.formatter(value)
        assertEqual(dtstr_, dtstr)

    # -------------------------------------------------------------------------
    def testDefaultFormat(self):
        """ Test validation with default format """

        # Set default format
        current.deployment_settings.L10n.date_format = "%d/%m/%Y"
        current.deployment_settings.L10n.time_format = "%H:%M"

        # Instantiate with default format
        validate = IS_UTC_DATETIME()

        assertEqual = self.assertEqual

        # Test valid string
        dtstr = "19/11/2011 14:00"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 19, 14, 0, 0))

        # Test invalid string
        dtstr = "2011-11-19 14:00:00"
        value, error = validate(dtstr)
        assertEqual(error, validate.error_message)
        assertEqual(value, dtstr)

    # -------------------------------------------------------------------------
    def testCustomFormat(self):
        """ Test validation with custom format (overriding settings) """

        # Set default format
        current.deployment_settings.L10n.date_format = "%d/%m/%Y"
        current.deployment_settings.L10n.time_format = "%H:%M:%S"

        # Instantiate with override format
        validate = IS_UTC_DATETIME(format="%d.%m.%Y %I:%M %p")

        assertEqual = self.assertEqual

        # Test valid string
        dtstr = "19.11.2011 02:00 PM"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 19, 14, 0, 0))

        # Test invalid string
        dtstr = "2011-11-19 14:00:00"
        value, error = validate(dtstr)
        assertEqual(error, validate.error_message)
        assertEqual(value, dtstr)

    # -------------------------------------------------------------------------
    def testFormatter(self):
        """ Test formatter """

        validate = IS_UTC_DATETIME()

        assertEqual = self.assertEqual

        # Test with None
        dt = None
        dtstr = validate.formatter(dt)
        assertEqual(dtstr, current.messages["NONE"])

        # Test without UTC offset
        dt = datetime.datetime(2011, 11, 19, 14, 0, 0)
        dtstr = validate.formatter(dt)
        assertEqual(dtstr, "2011-11-19 14:00:00")

        # Change time zone
        current.session.s3.utc_offset = -8

        # Test with default UTC offset
        dt = datetime.datetime(2011, 11, 19, 14, 0, 0)
        dtstr = validate.formatter(dt)
        assertEqual(dtstr, "2011-11-19 06:00:00")

        # Test with UTC offset and format override
        validate = IS_UTC_DATETIME(utc_offset="+0200",
                                   format="%d.%m.%Y %I:%M %p",
                                   )
        dt = datetime.datetime(2011, 11, 19, 14, 0, 0)
        dtstr = validate.formatter(dt)
        assertEqual(dtstr, "19.11.2011 04:00 PM")

    # -------------------------------------------------------------------------
    def testLocalizedErrorMessages(self):
        """ Test localized date/time in default error messages """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        # Set default format
        current.deployment_settings.L10n.date_format = "%d/%m/%Y"
        current.deployment_settings.L10n.time_format = "%I:%M %p"

        # Change time zone
        current.session.s3.utc_offset = +3

        # Minimum/maximum
        mindt = datetime.datetime(2011, 11, 19, 14, 0, 0)
        maxdt = datetime.datetime(2011, 11, 20, 22, 0, 0)

        # Test minimum error
        validate = IS_UTC_DATETIME(minimum=mindt)
        msg = validate.error_message
        assertEqual(validate.minimum, mindt)
        assertTrue(msg.find("19/11/2011 05:00 PM") != -1)

        # Test maximum error
        validate = IS_UTC_DATETIME(maximum=maxdt)
        msg = validate.error_message
        assertEqual(validate.maximum, maxdt)
        assertTrue(msg.find("21/11/2011 01:00 AM") != -1)

        # Test minimum error with custom format
        validate = IS_UTC_DATETIME(minimum=mindt,
                                   format="%Y-%m-%d %H:%M",
                                   )
        msg = validate.error_message
        assertEqual(validate.minimum, mindt)
        assertTrue(msg.find("2011-11-19 17:00") != -1)

        # Test maximum error with custom format
        validate = IS_UTC_DATETIME(maximum=maxdt,
                                   format="%Y-%m-%d %H:%M",
                                   )
        msg = validate.error_message
        assertEqual(validate.maximum, maxdt)
        assertTrue(msg.find("2011-11-21 01:00") != -1)

# =============================================================================
class IS_UTC_DATE_Tests(unittest.TestCase):
    """ Test IS_CALENDAR_DATE validator """

    # -------------------------------------------------------------------------
    def setUp(self):

        settings = current.deployment_settings

        # Set default calendar to Gregorian
        self.calendar = current.calendar
        current.calendar = S3Calendar("Gregorian")

        # Make sure date format is standard
        self.date_format = settings.get_L10n_date_format()
        settings.L10n.date_format = "%Y-%m-%d"

        # Set timezone to UTC
        session = current.session
        self.utc_offset = session.s3.utc_offset
        session.s3.utc_offset = 0

    # -------------------------------------------------------------------------
    def tearDown(self):

        settings = current.deployment_settings

        # Reset date and time format settings
        settings.L10n.date_format = self.date_format

        # Reset time zone
        current.session.s3.utc_offset = self.utc_offset

        # Reset calendar
        current.calendar = self.calendar

    # -------------------------------------------------------------------------
    def testValidation(self):
        """ Test validation with valid datetime string """

        validate = IS_UTC_DATE()

        assertEqual = self.assertEqual

        # Test UTC
        dtstr = "2011-11-19"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 19))

        # Change time zone
        current.session.s3.utc_offset = -6

        # Test western time zone (6 hours West, same day)
        dtstr = "2011-11-19"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 19))

        # Change time zone
        current.session.s3.utc_offset = +5

        # Test eastern time zone (5 hours East, same day)
        dtstr = "2011-11-19"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 19))

        # Change time zone
        current.session.s3.utc_offset = +11

        # Test eastern time zone (11 hours East, next day)
        dtstr = "2011-11-19"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 18))

    # -------------------------------------------------------------------------
    def testValidationWithDateTime(self):
        """ Test validation with datetime """

        validate = IS_UTC_DATE()

        class WEST6(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(hours=-6)

        class EAST5(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(hours=5)

        assertEqual = self.assertEqual

        # Test timezone-naive datetime (UTC, same day)
        dt = datetime.datetime(2011, 11, 19, 2, 0, 0)
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 19))

        # Test timezone-aware datetime (6 hours West, previous day)
        dt = datetime.datetime(2011, 11, 19, 19, 0, 0, tzinfo=WEST6())
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 20))

        # Change time zone
        current.session.s3.utc_offset = -8

        # Test timezone-naive datetime (8 hours West, previous day)
        dt = datetime.datetime(2011, 11, 19, 18, 0, 0)
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 20))

        # Test timezone-aware datetime (5 hours East, next day)
        dt = datetime.datetime(2011, 11, 19, 2, 0, 0, tzinfo=EAST5())
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 18))

    # -------------------------------------------------------------------------
    def testParseRepresent(self):
        """ Parsing-Representation consistency test """

        # Representation of a parsed string must give the same string

        assertEqual = self.assertEqual

        validate = IS_UTC_DATE()
        represent = S3DateTime.date_represent

        current.session.s3.utc_offset = -10

        dtstr = "1998-03-21"
        value, error = validate(dtstr)
        assertEqual(error, None)
        representation = validate.formatter(value)
        assertEqual(representation, dtstr)
        representation = represent(value, utc=True)
        assertEqual(representation, dtstr)

        current.session.s3.utc_offset = 0

        dtstr = "1998-03-21"
        value, error = validate(dtstr)
        assertEqual(error, None)
        representation = validate.formatter(value)
        assertEqual(representation, dtstr)
        representation = represent(value, utc=True)
        assertEqual(representation, dtstr)

        current.session.s3.utc_offset = 6

        dtstr = "1998-03-21"
        value, error = validate(dtstr)
        assertEqual(error, None)
        representation = validate.formatter(value)
        assertEqual(representation, dtstr)
        representation = represent(value, utc=True)
        assertEqual(representation, dtstr)

        current.session.s3.utc_offset = 11

        dtstr = "1998-03-21"
        value, error = validate(dtstr)
        assertEqual(error, None)
        representation = validate.formatter(value)
        assertEqual(representation, dtstr)
        representation = represent(value, utc=True)
        assertEqual(representation, dtstr)

    # -------------------------------------------------------------------------
    def testValidationWithDate(self):
        """ Test validation with date """

        validate = IS_UTC_DATE()

        class EAST5(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(hours=5)

        assertEqual = self.assertEqual

        # Test UTC
        dt = datetime.date(2011, 11, 19)
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 19))

        # Change time zone
        current.session.s3.utc_offset = -5

        # Test western time zone (5 hours West, same day)
        dt = datetime.date(2011, 11, 19)
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 19))

        # Change time zone
        current.session.s3.utc_offset = +5

        # Test eastern time zone (5 hours East, same day)
        dt = datetime.date(2011, 11, 19)
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 19))

        # Change time zone
        current.session.s3.utc_offset = +9

        # Test eastern time zone (9 hours East, next day)
        dt = datetime.date(2011, 11, 19)
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 18))

    # -------------------------------------------------------------------------
    def testValidationDestructive(self):
        """ Test validation with invalid input """

        validate = IS_UTC_DATE()

        assertEqual = self.assertEqual

        # Test with invalid datetime string
        dtstr = "Invalid Value"
        value, error = validate(dtstr)
        assertEqual(error, validate.error_message)
        assertEqual(value, dtstr)

        # Test with invalid type
        dtstr = 33
        value, error = validate(dtstr)
        assertEqual(error, validate.error_message)
        assertEqual(value, dtstr)

        # Test with None
        dtstr = None
        value, error = validate(dtstr)
        assertEqual(error, validate.error_message)
        assertEqual(value, dtstr)

    # -------------------------------------------------------------------------
    def testValidationWithAlternativeCalendar(self):
        """ Test validation with calendar-override """

        assertEqual = self.assertEqual

        # Test default=Gregorian, override=Persian
        current.calendar = S3Calendar("Gregorian")
        validate = IS_UTC_DATE(calendar="Persian")

        dtstr = "1390-08-28"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 19))

        dtstr_ = validate.formatter(value)
        assertEqual(dtstr_, dtstr)

        # Test default=Persian, override=Gregorian
        current.calendar = S3Calendar("Persian")
        validate = IS_UTC_DATE(calendar="Gregorian")

        dtstr = "2011-11-19"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 19))

        dtstr_ = validate.formatter(value)
        assertEqual(dtstr_, dtstr)

    # -------------------------------------------------------------------------
    def testDefaultFormat(self):
        """ Test validation with default format """

        # Set default format
        current.deployment_settings.L10n.date_format = "%d/%m/%Y"

        # Instantiate with default format
        validate = IS_UTC_DATE()

        assertEqual = self.assertEqual

        # Test valid string
        dtstr = "19/11/2011"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 19))

        # Test invalid string
        dtstr = "2011-11-19"
        value, error = validate(dtstr)
        assertEqual(error, validate.error_message)
        assertEqual(value, dtstr)

    # -------------------------------------------------------------------------
    def testCustomFormat(self):
        """ Test validation with custom format (overriding settings) """

        # Set default format
        current.deployment_settings.L10n.date_format = "%d/%m/%Y"

        # Instantiate with override format
        validate = IS_UTC_DATE(format="%d.%m.%Y")

        assertEqual = self.assertEqual

        # Test valid string
        dtstr = "19.11.2011"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 19))

        # Test invalid string
        dtstr = "2011-11-19"
        value, error = validate(dtstr)
        assertEqual(error, validate.error_message)
        assertEqual(value, dtstr)

    # -------------------------------------------------------------------------
    def testFormatter(self):
        """ Test formatter """

        validate = IS_UTC_DATE()

        assertEqual = self.assertEqual

        # Test with None
        dt = None
        dtstr = validate.formatter(dt)
        assertEqual(dtstr, current.messages["NONE"])

        # Test without UTC offset
        dt = datetime.date(2011, 11, 19)
        dtstr = validate.formatter(dt)
        assertEqual(dtstr, "2011-11-19")

        # Change time zone
        current.session.s3.utc_offset = -6

        # Test with default UTC offset (6 hours West, same day)
        dt = datetime.date(2011, 11, 19)
        dtstr = validate.formatter(dt)
        assertEqual(dtstr, "2011-11-19")

        # Change time zone
        current.session.s3.utc_offset = +6

        # Test with default UTC offset (6 hours East, same day)
        dt = datetime.date(2011, 11, 19)
        dtstr = validate.formatter(dt)
        assertEqual(dtstr, "2011-11-19")

        # Change time zone
        current.session.s3.utc_offset = +9

        # Test with default UTC offset (9 hours East, next day)
        dt = datetime.date(2011, 11, 19)
        dtstr = validate.formatter(dt)
        assertEqual(dtstr, "2011-11-20")

        # Test with UTC offset and format override (12 hours East, next day)
        validate = IS_UTC_DATE(utc_offset="+1200",
                               format="%d.%m.%Y",
                               )
        dt = datetime.datetime(2011, 11, 19, 8, 0, 0)
        dtstr = validate.formatter(dt)
        assertEqual(dtstr, "19.11.2011")

        dt = datetime.datetime(2011, 11, 19, 18, 0, 0)
        dtstr = validate.formatter(dt)
        assertEqual(dtstr, "20.11.2011")

        dt = datetime.date(2011, 11, 19)
        dtstr = validate.formatter(dt)
        assertEqual(dtstr, "20.11.2011")

    # -------------------------------------------------------------------------
    def testLocalizedErrorMessages(self):
        """ Test localized date/time in default error messages """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        # Set default format
        current.deployment_settings.L10n.date_format = "%d/%m/%Y"

        # Change time zone
        current.session.s3.utc_offset = +3

        # Minimum/maximum
        mindt = datetime.date(2011, 11, 16)
        maxdt = datetime.date(2011, 11, 20)

        # Test minimum error
        validate = IS_UTC_DATE(minimum=mindt)
        msg = validate.error_message
        assertEqual(validate.minimum, mindt)
        assertTrue(msg.find("16/11/2011") != -1)

        dtstr = "13/11/2011"
        value, error = validate(dtstr)
        assertEqual(value, dtstr)
        assertEqual(error, msg)

        # Test maximum error
        validate = IS_UTC_DATE(maximum=maxdt)
        msg = validate.error_message
        assertEqual(validate.maximum, maxdt)
        assertTrue(msg.find("20/11/2011") != -1)

        # Test minimum error with custom format
        validate = IS_UTC_DATE(minimum=mindt,
                               format="%Y-%m-%d",
                               )
        msg = validate.error_message
        assertEqual(validate.minimum, mindt)
        assertTrue(msg.find("2011-11-16") != -1)

        # Test maximum error with custom format
        validate = IS_UTC_DATE(maximum=maxdt,
                               format="%Y-%m-%d",
                               )
        msg = validate.error_message
        assertEqual(validate.maximum, maxdt)
        assertTrue(msg.find("2011-11-20") != -1)

# =============================================================================
class IS_JSONS3_Tests(unittest.TestCase):
    """ Testing IS_JSONS3 validator """

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(self):

        db = current.db

        # Create a test table
        db.define_table("test_jsons3",
                        Field("value", "json",
                              requires = IS_JSONS3(),
                              ),
                        )

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(self):

        db = current.db

        # Drop the test table
        db.test_jsons3.drop()

    # -------------------------------------------------------------------------
    def testCompatibility(self):
        """ Verify consistency of native JSON implementation """

        db = current.db
        table = db.test_jsons3

        # PyDAL with native JSON support consistently accepts and
        # returns a Python object for "json" fields. Older versions
        # of web2py DAL may raise an exception here:
        record_id = table.insert(value={"a": 1})
        row = db(table.id == record_id).select(table.value,
                                               limitby=(0, 1),
                                               ).first()
        self.assertTrue(isinstance(row.value, dict))

    # -------------------------------------------------------------------------
    def testValidation(self):
        """ Verify correct validation and conversion of JSON strings """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual

        validator = IS_JSONS3()

        jsonstr = """{"a": 1}"""
        value, error = validator(jsonstr)
        assertEqual(error, None)
        assertEqual(value, {"a": 1})

        jsonstr = """not valid"""
        value, error = validator(jsonstr)
        assertNotEqual(error, None)
        assertEqual(value, jsonstr)

        # None is not valid JSON (must use IS_EMPTY_OR to allow it)
        jsonstr = None
        value, error = validator(jsonstr)
        assertNotEqual(error, None)
        assertEqual(value, jsonstr)

    # -------------------------------------------------------------------------
    def testValidationNative(self):
        """ Verify correct validation of JSON strings without conversion """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual

        validator = IS_JSONS3(native_json=True)

        jsonstr = """{"a":1}"""
        value, error = validator(jsonstr)
        assertEqual(error, None)
        assertEqual(value, jsonstr)

        jsonstr = """not valid"""
        value, error = validator(jsonstr)
        assertNotEqual(error, None)
        assertEqual(value, jsonstr)

        # None is not valid JSON (must use IS_EMPTY_OR to allow it)
        jsonstr = None
        value, error = validator(jsonstr)
        assertNotEqual(error, None)
        assertEqual(value, jsonstr)

    # -------------------------------------------------------------------------
    def testValidationCSVSyntax(self):
        """ Verify correct validation and conversion of CSV strings """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual

        # Pretend CSV import
        current.response.s3.bulk = True

        try:
            validator = IS_JSONS3()

            # Invalid syntax (single quotes)
            jsonstr = """{'a': 1}"""
            value, error = validator(jsonstr)
            assertEqual(error, None)
            assertEqual(value, {"a": 1})

            # Invalid syntax (single quotes with nested quotes)
            jsonstr = """{'a': 'this ain\\'t a good "example"'}"""
            value, error = validator(jsonstr)
            assertEqual(error, None)
            assertEqual(value, {"a": "this ain't a good \"example\""})

            # Valid syntax should work too
            jsonstr = """{"a": 1}"""
            value, error = validator(jsonstr)
            assertEqual(error, None)
            assertEqual(value, {"a": 1})

            # Some stuff is just...
            jsonstr = """not valid"""
            value, error = validator(jsonstr)
            assertNotEqual(error, None)
            assertEqual(value, jsonstr)

        finally:
            current.response.s3.bulk = False

    # -------------------------------------------------------------------------
    def testValidationCSVSyntaxNative(self):
        """ Verify correct validation and JSON syntax conversion of CSV strings """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual

        # Pretend CSV import
        current.response.s3.bulk = True

        try:
            validator = IS_JSONS3(native_json=True)

            # Invalid syntax (single quotes) => returns a valid JSON string
            jsonstr = """{'a': 1}"""
            value, error = validator(jsonstr)
            assertEqual(error, None)
            assertEqual(value, """{"a":1}""")

            # Invalid syntax (single quotes with nested quotes)
            jsonstr = """{'a': 'this ain\\'t a good "example"'}"""
            value, error = validator(jsonstr)
            assertEqual(error, None)
            assertEqual(value, """{"a":"this ain't a good \\"example\\""}""")

            # Valid syntax should work too
            jsonstr = """{"a": 1}"""
            value, error = validator(jsonstr)
            assertEqual(error, None)
            assertEqual(value, """{"a":1}""")

            # Some stuff is just...
            jsonstr = """not JSON at all"""
            value, error = validator(jsonstr)
            assertNotEqual(error, None)
            assertEqual(value, jsonstr)

        finally:
            current.response.s3.bulk = False

    # -------------------------------------------------------------------------
    def testFormatter(self):
        """ Verify correct formatting of data with conversion """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual

        validator = IS_JSONS3()

        data = {"a": 1}
        formatted = validator.formatter(data)
        assertEqual(formatted, """{"a":1}""")

        # Exception: None gives None
        # (would give "null" normally, but forms need to know there is no value)
        data = None
        formatted = validator.formatter(data)
        assertEqual(formatted, None)

    # -------------------------------------------------------------------------
    def testFormatterNative(self):
        """ Verify correct formatting of data without conversion """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual

        validator = IS_JSONS3(native_json=True)

        data = {"a": 1}
        formatted = validator.formatter(data)
        assertEqual(formatted, """{"a":1}""")

        data = """{"a":1}"""
        formatted = validator.formatter(data)
        assertEqual(formatted, data)

        # Exception: None gives None
        # (would give "null" normally, but forms need to know there is no value)
        data = None
        formatted = validator.formatter(data)
        assertEqual(formatted, None)

# =============================================================================
if __name__ == "__main__":

    run_suite(
        ISLatTest,
        ISLonTest,
        ISONEOFLazyRepresentationTests,
        IS_PHONE_NUMBER_Tests,
        IS_UTC_DATETIME_Tests,
        IS_UTC_DATE_Tests,
        IS_JSONS3_Tests,
    )

# END ========================================================================
