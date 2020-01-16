# -*- coding: utf-8 -*-
#
# Validators Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3validators.py
#
import unittest
from gluon import current

from s3.s3datetime import S3Calendar, S3DefaultTZ
from s3.s3fields import *
from s3.s3validators import *
from s3compat import PY2

from unit_tests import run_suite

# =============================================================================
class EAST5(datetime.tzinfo):
    """ Dummy time zone for tests """
    def utcoffset(self, dt):
        return datetime.timedelta(hours=5)

class WEST6(datetime.tzinfo):
    """ Dummy time zone for tests """
    def utcoffset(self, dt):
        return datetime.timedelta(hours=-6)

# =============================================================================
class ISLatTest(unittest.TestCase):
    """
        Latitude has to be in decimal degrees between -90 & 90

        We can convert D/M/S or D°M'S" format into decimal degrees:

          Zero padded, separated by spaces or : or (d, m, s) or (°, ', ") or run
          together and followed by cardinal direction initial (N,S). Only seconds
          can have decimals places. A decimal point with no trailing digits is invalid.
    """

    # -------------------------------------------------------------------------
    def testValid(self):
        """ Test valid latitude expressions """

        assertEqual = self.assertEqual

        validator = IS_LAT()

        # Accepts numeric values inside limit
        value, error = validator(56.75)
        assertEqual(error, None)
        assertEqual(value, 56.75)

        # Accepts decimal degrees as string
        value, error = validator("32.9975")
        assertEqual(error, None)
        assertEqual(value, 32.9975)

        # Accepts correctly formatted DMS strings
        value, error = validator("40:23:15N")
        assertEqual(error, None)
        assertEqual(value, 40.3875)

        value, error = validator(u"81°16'42.348\"N")
        assertEqual(error, None)
        assertEqual(value, 81.27843)

        value, error = validator("40d 023m 15s S")
        assertEqual(error, None)
        assertEqual(value, -40.3875)

        value, error = validator("90 00 00.0")
        assertEqual(error, None)
        assertEqual(value, 90.0)

        value, error = validator("89 59 50.4141 S")
        assertEqual(error, None)
        assertEqual(value, -89.99733725)

        value, error = validator("00 00 00.0")
        assertEqual(error, None)
        assertEqual(value, 0.0)

        value, error = validator("43 23 15S")
        assertEqual(error, None)
        assertEqual(value, -43.3875)

    # -------------------------------------------------------------------------
    def testInvalid(self):
        """ Test invalid latitude expressions """

        assertNotEqual = self.assertNotEqual

        validator = IS_LAT()

        # Doesn't accept None or empty string
        value, error = validator(None)
        assertNotEqual(error, None)

        value, error = validator("")
        assertNotEqual(error, None)

        # Doesn't syntactically incorrect strings
        value, error = validator("   ")
        assertNotEqual(error, None)

        value, error = validator("invalid")
        assertNotEqual(error, None)

        value, error = validator("-43 17 11")
        assertNotEqual(error, None)

        # Doesn't accept invalid cardinal direction
        value, error = validator("43 23 15W")
        assertNotEqual(error, None)

        # Doesn't accept values outside of limits
        value, error = validator(101)
        assertNotEqual(error, None)

        value, error = validator(u"91°16'42.348\"N")
        assertNotEqual(error, None)

        value, error = validator("90 00 00.001 S")
        assertNotEqual(error, None)

        value, error = validator("89 61 50.4121 S") # Minutes excess
        assertNotEqual(error, None)

        value, error = validator("89 59 78.4141") # Seconds excess
        assertNotEqual(error, None)

# =============================================================================
class ISLonTest(unittest.TestCase):
    """
        Longitude has to be in decimal degrees between -180 & 180
        We can convert D/M/S or D°M'S" format into decimal degrees:

          Zero padded, separated by spaces or : or (d, m, s) or (°, ', ") or run
          together and followed by cardinal direction initial (E,W). Only seconds
          can have decimals places. A decimal point with no trailing digits is invalid.
    """

    # -------------------------------------------------------------------------
    def testValid(self):
        """ Test valid latitude expressions """

        assertEqual = self.assertEqual

        validator = IS_LON()

        # Accepts numeric values inside limit
        value, error = validator(116.75)
        assertEqual(error, None)
        assertEqual(value, 116.75)

        # Accepts decimal degrees as string
        value, error = validator("132.9975")
        assertEqual(error, None)
        assertEqual(value, 132.9975)

        # Accepts correctly formatted DMS strings
        value, error = validator("99:23:15E")
        assertEqual(error, None)
        assertEqual(value, 99.3875)

        value, error = validator(u"121°16'42.348\"E")
        assertEqual(error, None)
        assertEqual(value, 121.27843)

        value, error = validator("40d 023m 15s W")
        assertEqual(error, None)
        assertEqual(value, -40.3875)

        value, error = validator("180 00 00.0")
        assertEqual(error, None)
        assertEqual(value, 180.0)

        value, error = validator("179 59 50.4141 W")
        assertEqual(error, None)
        assertEqual(value, -179.99733725)

        value, error = validator("00 00 00.0")
        assertEqual(error, None)
        assertEqual(value, 0.0)

        value, error = validator("143 23 15W")
        assertEqual(error, None)
        assertEqual(value, -143.3875)

    # -------------------------------------------------------------------------
    def testInvalid(self):
        """ Test invalid latitude expressions """

        assertNotEqual = self.assertNotEqual

        validator = IS_LON()

        # Doesn't accept None or empty string
        value, error = validator(None)
        assertNotEqual(error, None)

        value, error = validator("")
        assertNotEqual(error, None)

        # Doesn't syntactically incorrect strings
        value, error = validator("   ")
        assertNotEqual(error, None)

        value, error = validator("invalid")
        assertNotEqual(error, None)

        value, error = validator("-43 17 11")
        assertNotEqual(error, None)

        # Doesn't accept invalid cardinal direction
        value, error = validator("43 23 15S")
        assertNotEqual(error, None)

        # Doesn't accept values outside of limits
        value, error = validator(201)
        assertNotEqual(error, None)

        value, error = validator(u"181°16'42.348\"E")
        assertNotEqual(error, None)

        value, error = validator("180 00 00.001 W")
        assertNotEqual(error, None)

        value, error = validator("179 61 50.4121 W") # Minutes excess
        assertNotEqual(error, None)

        value, error = validator("179 59 78.4141") # Seconds excess
        assertNotEqual(error, None)

# =============================================================================
class ISONEOFLazyRepresentationTests(unittest.TestCase):

    def setUp(self):

        s3db = current.s3db
        settings = current.deployment_settings

        current.auth.override = True

        self.org_branches = settings.get_org_branches()
        settings.org.branches = True

        # Generate some organisation records
        orgs = [Storage(name="ISONEOF%s" % i, acronym="IOO%s" % i) for i in range(5)]

        table = s3db.org_organisation
        ids = []
        for org in orgs:
            org_id = table.insert(**org)
            org["id"] = org_id
            s3db.update_super(table, org)
            ids.append(org_id)

        self.ids = ids
        self.orgs = orgs

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.deployment_settings.org.branches = self.org_branches

        current.auth.override = False
        current.db.rollback()

    # -------------------------------------------------------------------------
    def testIsOneOfBuildSet(self):
        """ Test building of options set """

        assertEqual = self.assertEqual
        assertIn = self.assertIn

        db = current.db
        table = current.s3db.org_organisation

        renderer = S3Represent(lookup="org_organisation")
        validator = IS_ONE_OF(db(table.id.belongs(self.ids)),
                              "org_organisation.id",
                              renderer,
                              )

        # Verify the options set
        options = dict(validator.options())
        for org in self.orgs:
            assertIn(str(org.id), options)
            assertEqual(options[str(org.id)], org.name)

        # IS_ONE_OF passes all rows, no lookups inside renderer
        assertEqual(renderer.queries, 0)

    # -------------------------------------------------------------------------
    def testOrgOrganisationRepresent(self):
        """ Test IS_ONE_OF in combination with org_OrganisationRepresent """

        # @todo: move into s3db/org tests?
        s3db = current.s3db

        assertTrue = self.assertTrue
        assertEqual = self.assertEqual

        db = current.db
        table = s3db.org_organisation

        renderer = s3db.org_OrganisationRepresent()
        validator = IS_ONE_OF(db(table.id.belongs(self.ids)),
                              "org_organisation.id",
                              renderer,
                              )
        options = dict(validator.options())
        for org in self.orgs:
            assertTrue(str(org.id) in options)
            assertEqual(options[str(org.id)], "%s (%s)" % (org.name, org.acronym))
        assertEqual(renderer.queries, 1) # using custom query

        renderer = s3db.org_OrganisationRepresent(parent=False)
        validator = IS_ONE_OF(db(table.id.belongs(self.ids)),
                              "org_organisation.id",
                              renderer,
                              )
        options = dict(validator.options())
        for org in self.orgs:
            assertTrue(str(org.id) in options)
            assertEqual(options[str(org.id)],
                             "%s (%s)" % (org.name, org.acronym))
        assertEqual(renderer.queries, 0) # using default query

        renderer = s3db.org_OrganisationRepresent(parent=False, acronym=False)
        validator = IS_ONE_OF(db(table.id.belongs(self.ids)),
                              "org_organisation.id",
                              renderer,
                              )
        options = dict(validator.options())
        for org in self.orgs:
            assertTrue(str(org.id) in options)
            assertEqual(options[str(org.id)], org.name)
        assertEqual(renderer.queries, 0) # using default query

# =============================================================================
class IS_PHONE_NUMBER_Tests(unittest.TestCase):
    """ Test IS_PHONE_NUMBER single phone number validator """

    def setUp(self):

        settings = current.deployment_settings
        self.intl = settings.get_msg_require_international_phone_numbers()

    def tearDown(self):

        settings = current.deployment_settings
        settings.msg.require_international_phone_numbers = self.intl

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

        settings = current.deployment_settings

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
        assertEqual(error, "Enter phone number in international format like +46783754957")

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
        self.tzinfo = current.response.s3.tzinfo
        self.tzname = current.session.s3.tzname
        self.utc_offset = current.session.s3.utc_offset

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
        current.response.s3.tzinfo = self.tzinfo
        current.session.s3.tzname = self.tzname
        current.session.s3.utc_offset = self.utc_offset

        # Restore current calendar
        current.calendar = self.calendar

    # -------------------------------------------------------------------------
    def testValidation(self):
        """ Test validation with valid datetime string """

        response = current.response
        session = current.session

        response.s3.tzinfo = None
        session.s3.tzname = "America/Detroit"

        validate = IS_UTC_DATETIME()

        assertEqual = self.assertEqual

        # Test timezone-naive string (winter)
        dtstr = "2011-11-19 14:03:00"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 19, 19, 3, 0))

        # Test timezone-naive string (summer)
        dtstr = "2011-06-11 14:00:00"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 6, 11, 18, 0, 0))

        # Test timezone-aware string
        dtstr = "2011-11-19 14:28:22+0500"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 19, 9, 28, 22))

        # Fall back to offset
        response.s3.tzinfo = None
        session.s3.tzname = None
        session.s3.utc_offset = -8

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

        response = current.response
        session = current.session

        response.s3.tzinfo = None
        session.s3.tzname = "Australia/Tasmania"
        session.s3.utc_offset = "+0200"

        validate = IS_UTC_DATETIME()

        assertEqual = self.assertEqual

        # Test timezone-naive datetime (winter, UTC+11 to UTC)
        dt = datetime.datetime(2011, 11, 19, 14, 0, 0)
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 19, 3, 0, 0))

        # Test timezone-naive datetime (summer, UTC+10)
        dt = datetime.datetime(2011, 6, 8, 5, 0, 0)
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 6, 7, 19, 0, 0))

        # Test timezone-aware datetime (UTC+5 to UTC)
        dt = datetime.datetime(2011, 11, 19, 14, 0, 0, tzinfo=EAST5())
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 19, 9, 0, 0))

        # Fall back to fixed offset
        response.s3.tzinfo = None
        session.s3.tzname = None
        session.s3.utc_offset = -8

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

        response = current.response
        session = current.session

        response.s3.tzinfo = None
        session.s3.tzname = "UTC"
        session.s3.utc_offset = "+0200"

        validate = IS_UTC_DATETIME()

        assertEqual = self.assertEqual

        # Check that date defaults to 8:00 hours (UTC)
        dt = datetime.date(2011, 11, 19)
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 19, 8, 0, 0))

        # Change time zone (far West, fixed offset)
        response.s3.tzinfo = None
        session.s3.tzname = None
        session.s3.utc_offset = -8

        # Check that date defaults to 08:00 hours
        dt = datetime.date(2011, 11, 19)
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 19, 16, 0, 0))

        # Change time zone (extreme East, with DST-awareness)
        response.s3.tzinfo = None
        session.s3.tzname = "Australia/Tasmania"
        session.s3.utc_offset = -2

        # Check that date defaults to 08:00 hours
        dt = datetime.date(2011, 11, 19)
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 11, 18, 21, 0, 0))

        # Check that date defaults to 08:00 hours
        dt = datetime.date(2011, 5, 11)
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.datetime(2011, 5, 10, 22, 0, 0))

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

        response = current.response
        session = current.session

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
        response.s3.tzinfo = None
        session.s3.tzname = "Canada/Eastern"
        session.s3.utc_offset = +5

        # Test with default timezone (alternate DST)
        dt = datetime.datetime(2011, 11, 19, 14, 0, 0)
        dtstr = validate.formatter(dt)
        assertEqual(dtstr, "2011-11-19 09:00:00")
        dt = datetime.datetime(2011, 6, 8, 14, 0, 0)
        dtstr = validate.formatter(dt)
        assertEqual(dtstr, "2011-06-08 10:00:00")

        # Test format override
        validate = IS_UTC_DATETIME(format="%d.%m.%Y %I:%M %p",
                                   )
        dt = datetime.datetime(2011, 11, 19, 14, 0, 0)
        dtstr = validate.formatter(dt)
        assertEqual(dtstr, "19.11.2011 09:00 AM")

    # -------------------------------------------------------------------------
    def testLocalizedErrorMessages(self):
        """ Test localized date/time in default error messages """

        response = current.response
        session = current.session

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        # Set default format
        current.deployment_settings.L10n.date_format = "%d/%m/%Y"
        current.deployment_settings.L10n.time_format = "%I:%M %p"

        # Change time zone
        response.s3.tzinfo = None
        session.s3.tzname = "US/Pacific"
        session.s3.utc_offset = +3

        # Minimum/maximum
        mindt = datetime.datetime(2011, 11, 19, 14, 0, 0)
        maxdt = datetime.datetime(2011, 11, 20, 22, 0, 0)

        # Test minimum error
        validate = IS_UTC_DATETIME(minimum=mindt)
        msg = validate.error_message
        assertEqual(validate.minimum, mindt)
        assertTrue(msg.find("19/11/2011 06:00 AM") != -1)

        # Test maximum error
        validate = IS_UTC_DATETIME(maximum=maxdt)
        msg = validate.error_message
        assertEqual(validate.maximum, maxdt)
        assertTrue(msg.find("20/11/2011 02:00 PM") != -1)

        # Test minimum error with custom format
        validate = IS_UTC_DATETIME(minimum=mindt,
                                   format="%Y-%m-%d %H:%M",
                                   )
        msg = validate.error_message
        assertEqual(validate.minimum, mindt)
        assertTrue(msg.find("2011-11-19 06:00") != -1)

        # Test maximum error with custom format
        validate = IS_UTC_DATETIME(maximum=maxdt,
                                   format="%Y-%m-%d %H:%M",
                                   )
        msg = validate.error_message
        assertEqual(validate.maximum, maxdt)
        assertTrue(msg.find("2011-11-20 14:00") != -1)

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
        self.tzinfo = current.response.tzinfo
        self.tzname = current.session.tzname
        self.utc_offset = current.session.s3.utc_offset

    # -------------------------------------------------------------------------
    def tearDown(self):

        settings = current.deployment_settings

        # Reset date and time format settings
        settings.L10n.date_format = self.date_format

        # Reset time zone
        current.response.s3.tzinfo = self.tzinfo
        current.session.s3.tzname = self.tzname
        current.session.s3.utc_offset = self.utc_offset

        # Reset calendar
        current.calendar = self.calendar

    # -------------------------------------------------------------------------
    def testValidation(self):
        """ Test validation with valid datetime string """

        response = current.response

        validate = IS_UTC_DATE()

        assertEqual = self.assertEqual

        # Test UTC
        dtstr = "2011-11-19"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 19))

        # Change time zone
        response.s3.tzinfo = S3DefaultTZ(-6)

        # Test western time zone (6 hours West, same day)
        dtstr = "2011-11-19"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 19))

        # Change time zone
        response.s3.tzinfo = S3DefaultTZ(+5)

        # Test eastern time zone (5 hours East, same day)
        dtstr = "2011-11-19"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 19))

        # Change time zone
        response.s3.tzinfo = S3DefaultTZ(+11)

        # Test eastern time zone (11 hours East, next day)
        dtstr = "2011-11-19"
        value, error = validate(dtstr)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 18))

    # -------------------------------------------------------------------------
    def testValidationWithDateTime(self):
        """ Test validation with datetime """

        response = current.response

        validate = IS_UTC_DATE()

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
        response.s3.tzinfo = S3DefaultTZ(-8)

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

        response = current.response

        assertEqual = self.assertEqual

        validate = IS_UTC_DATE()
        represent = S3DateTime.date_represent

        response.s3.tzinfo = S3DefaultTZ(-10)

        dtstr = "1998-03-21"
        value, error = validate(dtstr)
        assertEqual(error, None)
        representation = validate.formatter(value)
        assertEqual(representation, dtstr)
        representation = represent(value, utc=True)
        assertEqual(representation, dtstr)

        response.s3.tzinfo = S3DefaultTZ(0)

        dtstr = "1998-03-21"
        value, error = validate(dtstr)
        assertEqual(error, None)
        representation = validate.formatter(value)
        assertEqual(representation, dtstr)
        representation = represent(value, utc=True)
        assertEqual(representation, dtstr)

        response.s3.tzinfo = S3DefaultTZ(+6)

        dtstr = "1998-03-21"
        value, error = validate(dtstr)
        assertEqual(error, None)
        representation = validate.formatter(value)
        assertEqual(representation, dtstr)
        representation = represent(value, utc=True)
        assertEqual(representation, dtstr)

        response.s3.tzinfo = S3DefaultTZ(+12)

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

        response = current.response

        validate = IS_UTC_DATE()

        assertEqual = self.assertEqual

        # Test UTC
        dt = datetime.date(2011, 11, 19)
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 19))

        # Test western time zone (5 hours West, same day)
        response.s3.tzinfo = S3DefaultTZ(-5)
        dt = datetime.date(2011, 11, 19)
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 19))

        # Test eastern time zone (5 hours East, same day)
        response.s3.tzinfo = S3DefaultTZ(+5)
        dt = datetime.date(2011, 11, 19)
        value, error = validate(dt)
        assertEqual(error, None)
        assertEqual(value, datetime.date(2011, 11, 19))

        # Test eastern time zone (9 hours East, next day)
        response.s3.tzinfo = S3DefaultTZ(+9)
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

        response = current.response
        session = current.session

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
        response.s3.tzinfo = S3DefaultTZ(-6)

        # Test with default UTC offset (6 hours West, same day)
        dt = datetime.date(2011, 11, 19)
        dtstr = validate.formatter(dt)
        assertEqual(dtstr, "2011-11-19")

        # Change time zone
        response.s3.tzinfo = S3DefaultTZ(+6)

        # Test with default UTC offset (6 hours East, same day)
        dt = datetime.date(2011, 11, 19)
        dtstr = validate.formatter(dt)
        assertEqual(dtstr, "2011-11-19")

        # Change time zone
        response.s3.tzinfo = S3DefaultTZ(+12)

        # Test with default UTC offset (12 hours East, next day)
        dt = datetime.date(2011, 11, 19)
        dtstr = validate.formatter(dt)
        assertEqual(dtstr, "2011-11-20")

        response.s3.tzinfo = None
        session.s3.tzname = "Australia/Melbourne"
        session.s3.utc_offset = +1

        # Test format override
        validate = IS_UTC_DATE(format="%d.%m.%Y",
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

        dt = datetime.date(2011, 5, 19)
        dtstr = validate.formatter(dt)
        assertEqual(dtstr, "20.05.2011")

    # -------------------------------------------------------------------------
    def testLocalizedErrorMessages(self):
        """ Test localized date/time in default error messages """

        response = current.response

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        # Set default format
        current.deployment_settings.L10n.date_format = "%d/%m/%Y"

        # Change time zone
        response.s3.tzinfo = S3DefaultTZ(+3)

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
class IS_DYNAMIC_FIELDNAME_Test(unittest.TestCase):
    """ Test cases for IS_DYNAMIC_FIELDNAME validator """

    # -------------------------------------------------------------------------
    def testPass(self):
        """ Test IS_DYNAMIC_FIELDNAME with valid field names """

        assertEqual = self.assertEqual

        requires = IS_DYNAMIC_FIELDNAME()

        value, error = requires("example")
        assertEqual(value, "example")
        assertEqual(error, None)

        value, error = requires("Another_Example")
        assertEqual(value, "another_example")
        assertEqual(error, None)

    # -------------------------------------------------------------------------
    def testFail(self):
        """ Test IS_DYNAMIC_FIELDNAME with invalid field names """

        assertNotEqual = self.assertNotEqual

        requires = IS_DYNAMIC_FIELDNAME()

        # Must not be None
        value, error = requires(None)
        assertNotEqual(error, None)

        # Must not be empty
        value, error = requires("")
        assertNotEqual(error, None)

        # Must not contain blanks
        value, error = requires("must not contain blanks")
        assertNotEqual(error, None)

        # Must start with a letter
        value, error = requires("_must_start_with_letter")
        assertNotEqual(error, None)

        # Must not contain invalid characters
        value, error = requires("invalid#characters")
        assertNotEqual(error, None)

        # Must not be "id"
        value, error = requires("id")
        assertNotEqual(error, None)

        # Must not be meta-field name
        value, error = requires("modified_by")
        assertNotEqual(error, None)

# =============================================================================
class IS_DYNAMIC_FIELDTYPE_Test(unittest.TestCase):
    """ Test cases for IS_DYNAMIC_FIELDTYPE validator """

    # -------------------------------------------------------------------------
    def testPass(self):
        """ Test IS_DYNAMIC_FIELDTYPE with valid field types """

        assertEqual = self.assertEqual

        requires = IS_DYNAMIC_FIELDTYPE()

        value, error = requires("boolean")
        assertEqual(value, "boolean")
        assertEqual(error, None)

        value, error = requires("String")
        assertEqual(value, "string")
        assertEqual(error, None)

        value, error = requires(" Integer ")
        assertEqual(value, "integer")
        assertEqual(error, None)

        value, error = requires("reference org_organisation")
        assertEqual(value, "reference org_organisation")
        assertEqual(error, None)

    # -------------------------------------------------------------------------
    def testFail(self):
        """ Test IS_DYNAMIC_FIELDTYPE with invalid field types """

        assertNotEqual = self.assertNotEqual

        requires = IS_DYNAMIC_FIELDTYPE()

        # Must not be None
        value, error = requires(None)
        assertNotEqual(error, None)

        # Must not be empty
        value, error = requires("")
        assertNotEqual(error, None)

        # Must be a supported field type
        value, error = requires("nonsense")
        assertNotEqual(error, None)

        # Must not be "id"
        value, error = requires("id")
        assertNotEqual(error, None)

        # Referenced tables must be resolvable
        value, error = requires("reference nonexistent_table")
        assertNotEqual(error, None)

# =============================================================================
class IS_FLOAT_AMOUNT_Tests(unittest.TestCase):
    """
        Tests for the IS_FLOAT_AMOUNT validator
    """

    # -------------------------------------------------------------------------
    def setUp(self):

        settings = current.deployment_settings

        self.dot = settings.get_L10n_decimal_separator()
        self.sep = settings.get_L10n_thousands_separator()
        self.grp = settings.get_L10n_thousands_grouping()

        settings.L10n.decimal_separator = ","
        settings.L10n.thousands_separator = " "
        settings.L10n.thousands_grouping = 3

    def tearDown(self):

        settings = current.deployment_settings

        settings.L10n.decimal_separator = self.dot
        settings.L10n.thousands_separator = self.sep
        settings.L10n.thousands_grouping = self.grp

    # -------------------------------------------------------------------------
    def test_representation(self):
        """ Test the IS_FLOAT_AMOUNT representation function """

        represent = IS_FLOAT_AMOUNT.represent

        samples = ((None, "", None, True),
                   (0.0, "0", 0, True),
                   (0.00325, "0,00", 2, True),
                   (198.05, "198,05", 2, True),
                   (1305.0, "1 305", 0, True),
                   (123456789012.0, "123 456 789 012,000", 3, True),
                   (0, "0", None, True),
                   (1305, "1 305,00", 2, True),
                   (987654321098, "987 654 321 098,00", 2, True),
                   (-0, "0,00", 2, True),
                   (-1305.730, "-1 305,73", None, True),
                   (-123456789012345.0, "-123 456 789 012 345", 2, False),
                   )

        assertEqual = self.assertEqual
        for number, expected, precision, fixed in samples:
            assertEqual(represent(number,
                                  precision = precision,
                                  fixed = fixed,
                                  ),
                        expected,
                        )

    # -------------------------------------------------------------------------
    def test_validation(self):
        """ Test the IS_FLOAT_AMOUNT validation function """

        validate = IS_FLOAT_AMOUNT()

        samples = (("123 456 789 012,00", 123456789012.0),
                   ("0,00", 0.0),
                   ("1 305,00", 1305.0),
                   (12.345, 12.345),
                   )

        assertEqual = self.assertEqual
        for inputstr, expected in samples:
            value, error = validate(inputstr)
            assertEqual(value, expected)
            assertEqual(error, None)

    # -------------------------------------------------------------------------
    def test_ambiguous_validation(self):
        """ Test the ambiguous validation """

        settings = current.deployment_settings

        settings.L10n.decimal_separator = ","
        settings.L10n.thousands_separator = "."
        settings.L10n.thousands_grouping = 3

        validate = IS_FLOAT_AMOUNT()

        samples = (("123.456.789.012,00", 123456789012.0),
                   ("0,00", 0.0),
                   (u"1,305.234", 1.305234),
                   (12.345, 12.345),
                   )

        assertEqual = self.assertEqual
        for inputstr, expected in samples:
            value, error = validate(inputstr)
            assertEqual(value, expected)
            assertEqual(error, None)

# =============================================================================
class IS_INT_AMOUNT_Tests(unittest.TestCase):
    """
        Tests for the IS_INT_AMOUNT validator
    """

    # -------------------------------------------------------------------------
    def setUp(self):

        settings = current.deployment_settings

        self.sep = settings.get_L10n_thousands_separator()
        self.grp = settings.get_L10n_thousands_grouping()

        settings.L10n.thousands_separator = ","
        settings.L10n.thousands_grouping = 3

    def tearDown(self):

        settings = current.deployment_settings

        settings.L10n.thousands_separator = self.sep
        settings.L10n.thousands_grouping = self.grp

    # -------------------------------------------------------------------------
    def test_representation(self):
        """ Test the IS_INT_AMOUNT representation function """

        represent = IS_INT_AMOUNT.represent
        precision = 2
        fixed = True

        samples = ((None, ""),
                   (0, "0"),
                   (-0, "0"),
                   (-12555, "-12,555"),
                   (1305, "1,305"),
                   (1234567.89, "1,234,567"),
                   (123456789012, "123,456,789,012"),
                   (1234567890123456789, "1,234,567,890,123,456,789"),
                   )

        for number, expected in samples:
            self.assertEqual(represent(number), expected)

    # -------------------------------------------------------------------------
    def test_validation(self):
        """ Test the IS_INT_AMOUNT validation function """

        validate = IS_INT_AMOUNT()

        samples = (("123,456,789,012", 123456789012),
                   ("0", 0),
                   ("993667", 993667),
                   )

        assertEqual = self.assertEqual
        for inputstr, expected in samples:
            value, error = validate(inputstr)
            assertEqual(value, expected)
            assertEqual(error, None)

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
        IS_DYNAMIC_FIELDNAME_Test,
        IS_DYNAMIC_FIELDTYPE_Test,
        IS_FLOAT_AMOUNT_Tests,
        IS_INT_AMOUNT_Tests,
    )

# END ========================================================================
