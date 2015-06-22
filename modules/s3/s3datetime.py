# -*- coding: utf-8 -*-

""" S3 Date/Time Toolkit

    @copyright: 2015 (c) Sahana Software Foundation
    @license: MIT

    @requires: U{B{I{gluon}} <http://web2py.com>}

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ("ISOFORMAT",
           "S3DateTime",
           "S3Calendar",
           "s3_parse_datetime",
           "s3_format_datetime",
           "s3_decode_iso_datetime",
           "s3_encode_iso_datetime",
           "s3_utc",
           "s3_get_utc_offset",
           )

import datetime
try:
    import dateutil
    import dateutil.parser
    import dateutil.tz
except ImportError:
    import sys
    print >> sys.stderr, "ERROR: python-dateutil module needed for date handling"
    raise
import math
import re
import time

from gluon import *

# =============================================================================
# Constants
#
ISOFORMAT = "%Y-%m-%dT%H:%M:%S" #: ISO 8601 Combined Date+Time format
OFFSET = re.compile("([+|-]{0,1})(\d{1,2}):(\d\d)")

# =============================================================================
class S3DateTime(object):
    """
        Toolkit for date+time parsing/representation
    """

    # -------------------------------------------------------------------------
    @classmethod
    def date_represent(cls, dt, format=None, utc=False):
        """
            Represent the date according to deployment settings &/or T()

            @param dt: the date (datetime.date or datetime.datetime)
            @param format: the format (overrides deployment setting)
            @param utc: the date is given in UTC
        """

        if not format:
            format = current.deployment_settings.get_L10n_date_format()

        if dt:
            if utc:
                offset = cls.get_offset_value(current.session.s3.utc_offset)
                if offset:
                    delta = datetime.timedelta(seconds=offset)
                    if not isinstance(dt, datetime.datetime):
                        combine = datetime.datetime.combine
                        # Compute the break point
                        bp = (combine(dt, datetime.time(8, 0, 0)) - delta).time()
                        dt = combine(dt, bp)
                    dt = dt + delta
            dtstr = current.calendar.format_date(dt, dtfmt=format, local=True)
        else:
            dtstr = current.messages["NONE"]

        return dtstr

    # -----------------------------------------------------------------------------
    @classmethod
    def datetime_represent(cls, dt, format=None, utc=False):
        """
            Represent the datetime according to deployment settings &/or T()

            @param dt: the datetime
            @param utc: the datetime is given in UTC
        """

        if format is None:
            format = current.deployment_settings.get_L10n_datetime_format()

        if dt:
            if utc:
                offset = cls.get_offset_value(current.session.s3.utc_offset)
                if offset:
                    delta = datetime.timedelta(seconds=offset)
                    if not isinstance(dt, datetime.datetime):
                        combine = datetime.datetime.combine
                        bp = (combine(dt, datetime.time(8, 0, 0)) - delta).time()
                        dt = combine(dt, bp)
                    dt = dt + datetime.timedelta(seconds=offset)
            dtstr = current.calendar.format_datetime(dt, dtfmt=format, local=True)
        else:
            dtstr = current.messages["NONE"]

        return dtstr

    # -----------------------------------------------------------------------------
    @classmethod
    def time_represent(cls, time, format=None, utc=False):
        """
            Represent the date according to deployment settings &/or T()

            @param time: the time
            @param format: the time format (overrides deployment setting)
            @param utc: the time is given in UTC
        """

        settings = current.deployment_settings

        if format is None:
            format = settings.get_L10n_time_format()

        if time and utc:
            # Make sure to use datetime.datetime (to support timedelta)
            if not isinstance(time, datetime.datetime):
                today = datetime.datetime.utcnow().date()
                time = datetime.datetime.combine(today, time)
            # Add UTC offset
            offset = cls.get_offset_value(current.session.s3.utc_offset)
            if offset:
                time = time + datetime.timedelta(seconds=offset)
        if isinstance(time, datetime.datetime):
            # Prevent error with dates<1900: convert into datetime.time
            time = time.time()
        if time:
            try:
                return time.strftime(str(format))
            except AttributeError:
                # Invalid argument type
                raise TypeError("time_represent: invalid argument type: %s" % type(time))
        else:
            return current.messages["NONE"]

    # -----------------------------------------------------------------------------
    @staticmethod
    def get_offset_value(string):
        """
            Convert an UTC offset string into a UTC offset value in seconds

            @param string: the UTC offset in hours as string, valid formats
                           are: "+HH:MM", "+HHMM", "+HH" (positive sign can
                           be omitted), can also recognize decimal notation
                           with "." as mark
        """

        if not string:
            return 0

        sign = 1
        offset_hrs = offset_min = 0

        if isinstance(string, (int, long, float)):
            offset_hrs = string
        elif isinstance(string, basestring):
            if string[:3] == "UTC":
                string = string[3:]
            string = string.strip()
            match = OFFSET.match(string)
            if match:
                groups = match.groups()
                if groups[0] == "-":
                    sign = -1
                offset_hrs = int(groups[1])
                offset_min = int(groups[2])
            elif "." not in string:
                try:
                    offset_hrs = int(string)
                except ValueError:
                    return 0
                if offset_hrs < -99 or offset_hrs > 99:
                    if offset_hrs < 0:
                        sign = -1
                    offset_hrs, offset_min = divmod(abs(offset_hrs), 100)
            else:
                try:
                    offset_hrs = float(string)
                except ValueError:
                    return 0
        else:
            return 0
        return sign * (3600 * offset_hrs + 60 * offset_min)

# =============================================================================
class S3Calendar(object):
    """
        Calendar Base Class (implementing the Gregorian Calendar)

        Subclasses define their own CALENDAR name, and are registered
        with this name in the calendars dict in S3Calendar._set_calendar().
    """

    CALENDAR = "Gregorian"

    JDEPOCH = 1721425.5 # first day of this calendar as Julian Day number

    # -------------------------------------------------------------------------
    # Methods to be implemented by subclasses
    # -------------------------------------------------------------------------
    @staticmethod
    def _parse(dtstr, dtfmt):
        """
            Convert a datetime string into a time tuple (time.struct_time),
            to be implemented by subclass (e.g. using pyparsing).

            @param dtstr: the datetime string
            @param dtfmt: the datetime format (strptime)

            @return: a time tuple like (y, m, d, hh, mm, ss)
        """

        # Gregorian Calendar uses strptime
        try:
            timetuple = time.strptime(dtstr, dtfmt)
        except ValueError, e:
            # Seconds missing?
            try:
                timetuple = time.strptime(dtstr + ":00", dtfmt)
            except ValueError:
                raise e
        return timetuple[:6]

    # -------------------------------------------------------------------------
    @staticmethod
    def _format(dt, dtfmt):
        """
            Get a string representation for a datetime.datetime according
            to this calendar and dtfmt, to be implemented by subclass

            @param dt: the datetime.datetime
            @param dtfmt: the datetime format (strftime)

            @return: the string representation (str)

            @raises TypeError: for invalid argument types
        """

        # Gregorian Calendar uses strftime
        fmt = str(dtfmt)
        try:
            dtstr = dt.strftime(fmt)
        except ValueError:
            # Dates < 1900 not supported by strftime
            year = "%04i" % dt.year
            fmt = fmt.replace("%Y", year).replace("%y", year[-2:])
            dtstr = dt.replace(year=1900).strftime(fmt)
        except AttributeError:
            # Invalid argument type
            raise TypeError("invalid argument type: %s" % type(dt))
        return dtstr

    # -------------------------------------------------------------------------
    @classmethod
    def from_jd(cls, jd):
        """
            Convert a Julian day number to a year/month/day tuple
            of this calendar, to be implemented by subclass

            @param jd: the Julian day number
        """

        # Gregorian calendar uses default method
        return cls._jd_to_gregorian(jd)

    # -------------------------------------------------------------------------
    @classmethod
    def to_jd(cls, year, month, day):
        """
            Convert a year/month/day tuple of this calendar into
            a Julian day number, to be implemented by subclass

            @param year: the year number
            @param month: the month number
            @param day: the day-of-month number
        """

        # Gregorian calendar uses default method
        return cls._gregorian_to_jd(year, month, day)

    # -------------------------------------------------------------------------
    # Common Interface Methods (should not be implemented by subclasses):
    # -------------------------------------------------------------------------
    @property
    def name(self):
        """ Get the name of the current """

        name = self._name
        if not name:
            name = current.deployment_settings.get_L10n_calendar()
        if not name:
            name = self.CALENDAR
        return name

    # -------------------------------------------------------------------------
    @property
    def calendar(self):
        """ Get the current calendar """

        calendar = self._calendar
        if calendar is None:
            calendar = self._set_calendar(self.name)
        return calendar

    # -------------------------------------------------------------------------
    def parse_date(self, dtstr, dtfmt=None, local=False):
        """
            Parse a datetime string according to this calendar

            @param dtstr: the datetime as string
            @param dtfmt: the datetime format (strptime), overrides default
            @param local: whether the default format is local (=deployment
                          setting) or ISO
            @return: the datetime (datetime.datetime)
        """

        if dtstr is None:
            return None

        # Default format
        if dtfmt is None:
            if local:
                dtfmt = current.deployment_settings.get_L10n_date_format()
            else:
                dtfmt = "%Y-%m-%d" # ISO Date Format

        # Use the current calendar
        calendar = self.calendar

        # Parse the dtstr
        try:
            timetuple = calendar._parse(dtstr, dtfmt)
        except (ValueError, TypeError):
            return None

        # Convert timetuple to Gregorian calendar
        timetuple = calendar._gdate(timetuple)

        # Convert into datetime
        dt = datetime.datetime(*timetuple)
        return dt.date()

    # -------------------------------------------------------------------------
    def parse_datetime(self, dtstr, dtfmt=None, local=False):
        """
            Parse a datetime string according to this calendar

            @param dtstr: the datetime as string
            @param dtfmt: the datetime format (strptime)
            @param local: whether the default format is local (=deployment
                          setting) or ISO
            @return: the datetime (datetime.datetime)
        """

        if dtstr is None:
            return None

        # Default format
        if dtfmt is None:
            if local:
                dtfmt = current.deployment_settings.get_L10n_datetime_format()
            else:
                dtfmt = ISOFORMAT # ISO Date/Time Format

        # Use the current calendar
        calendar = self.calendar

        # Parse the dtstr
        try:
            timetuple = calendar._parse(dtstr, dtfmt)
        except (ValueError, TypeError):
            return None

        # Convert timetuple to Gregorian calendar
        timetuple = calendar._gdate(timetuple)

        # Convert into datetime
        dt = datetime.datetime(*timetuple)
        return dt

    # -------------------------------------------------------------------------
    def format_date(self, dt, dtfmt=None, local=False):
        """
            Format a date according to this calendar

            @param dt: the date (datetime.date or datetime.datetime)
            @return: the date as string
        """

        if dt is None:
            return current.messages["NONE"]

        # Default format
        if dtfmt is None:
            if local:
                dtfmt = current.deployment_settings.get_L10n_date_format()
            else:
                dtfmt = "%Y-%m-%d" # ISO Date Format

        # Deal with T's
        try:
            dtfmt = str(dtfmt)
        except (UnicodeDecodeError, UnicodeEncodeError):
            dtfmt = s3_unicode(dtfmt).encode("utf-8")

        return self.calendar._format(dt, dtfmt)

    # -------------------------------------------------------------------------
    def format_datetime(self, dt, dtfmt=None, local=False):
        """
            Format a datetime according to this calendar

            @param dt: the datetime (datetime.datetime)
            @return: the datetime as string
        """

        if dt is None:
            return current.messages["NONE"]

        # Default format
        if dtfmt is None:
            if local:
                dtfmt = current.deployment_settings.get_L10n_datetime_format()
            else:
                dtfmt = ISOFORMAT # ISO Date/Time Format

        # Deal with T's
        try:
            dtfmt = str(dtfmt)
        except (UnicodeDecodeError, UnicodeEncodeError):
            dtfmt = s3_unicode(dtfmt).encode("utf-8")

        # Remove microseconds
        # - for the case that the calendar falls back to .isoformat
        if isinstance(dt, datetime.datetime):
           dt = dt.replace(microsecond=0)

        return self.calendar._format(dt, dtfmt)

    # -------------------------------------------------------------------------
    # Base class methods (should not be implemented by subclasses):
    # -------------------------------------------------------------------------
    def __init__(self, name=None):
        """
            Constructor

            @param name: the name of the calendar (see _set_calendar for
                         supported calendars). If constructed without name,
                         the L10.calendar deployment setting will be used
                         instead.
        """

        # Supported calendars
        self._calendars = {"Gregorian": S3Calendar,
                           "Persian": S3PersianCalendar,
                           }

        if name is None:
            self._name = None
            self._calendar = None
        elif name == self.CALENDAR:
            self._name = name
            self._calendar = self
        else:
            self._set_calendar(name)

    # -------------------------------------------------------------------------
    def _set_calendar(self, name=None):
        """
            Set the current calendar

            @param name: the name of the calendar (falls back to CALENDAR)
        """

        calendars = self._calendars

        # Fallback
        if name not in calendars:
            name = self.CALENDAR

        # Instantiate the Calendar
        if name == self.CALENDAR:
            calendar = self
        else:
            calendar = calendars[name](name)

        self._name = name
        self._calendar = calendar

        return calendar

    # -------------------------------------------------------------------------
    @staticmethod
    def _gregorian_to_jd(year, month, day):
        """
            Convert a Gregorian date into a Julian day number (matching
            jQuery calendars algorithm)

            @param year: the year number
            @param month: the month number
            @param day: the day number
        """

        if year < 0:
            year = year + 1

        if month < 3:
            month = month + 12
            year = year - 1

        a = math.floor(year/100)
        b = 2 - a + math.floor(a / 4)

        return math.floor(365.25 * (year + 4716)) + \
               math.floor(30.6001 * (month + 1)) + day + b - 1524.5

    # -------------------------------------------------------------------------
    @staticmethod
    def _jd_to_gregorian(jd):
        """
            Convert a Julian day number to a Gregorian date (matching
            jQuery calendars algorithm)

            @param jd: the Julian day number
            @return: tuple (year, month, day)
        """

        z = math.floor(jd + 0.5)
        a = math.floor((z - 1867216.25) / 36524.25)

        a = z + 1 + a - math.floor(a / 4)
        b = a + 1524
        c = math.floor((b - 122.1) / 365.25)
        d = math.floor(365.25 * c)
        e = math.floor((b - d) / 30.6001)

        day = b - d - math.floor(e * 30.6001)
        if e > 13.5:
            month = e - 13
        else:
            month = e - 1

        if month > 2.5:
            year = c - 4716
        else:
            year = c - 4715

        if year <= 0:
            year = year - 1

        return (int(year), int(month), int(day))

    # -------------------------------------------------------------------------
    def _cdate(self, timetuple):
        """
            Convert a time tuple from Gregorian calendar to this calendar

            @param timetuple: time tuple (y, m, d, hh, mm, ss)
            @return: time tuple (this calendar)
        """

        if self.name == "Gregorian":
            # Gregorian Calendar does nothing here
            return timetuple

        y, m, d, hh, mm, ss = timetuple
        jd = self._gregorian_to_jd(y, m, d)
        y, m, d = self.from_jd(jd)

        return (y, m, d, hh, mm, ss)

    # -------------------------------------------------------------------------
    def _gdate(self, timetuple):
        """
            Convert a time tuple from this calendar to Gregorian calendar

            @param timetuple: time tuple (y, m, d, hh, mm, ss)
            @return: time tuple (Gregorian)
        """

        if self.name == "Gregorian":
            # Gregorian Calendar does nothing here
            return timetuple

        y, m, d, hh, mm, ss = timetuple
        jd = self.to_jd(y, m, d)
        y, m, d = self._jd_to_gregorian(jd)

        return (y, m, d, hh, mm, ss)

# =============================================================================
class S3PersianCalendar(S3Calendar):
    """
        S3Calendar subclass implementing the Solar Hijri calendar

        @note: this calendar is called "Persian" in jQuery calendars despite
               it actually implements the modern Iranian (=algorithmic Solar
               Hijri) rather than the traditional Persian (=observation-based
               Jalali) variant. However, we use the name "Persian" to match
               the jQuery calendars naming of calendars, in order to avoid
               confusion about naming differences between these two components.

        @note: Afghanistan uses the same calendar, but with the names of the
               signs of Zodiac as month names. This variant will be implemented
               as subclass of S3PersianCalendar (=>@todo)
    """

    CALENDAR = "Persian"

    JDEPOCH = 1948320.5 # first day of this calendar as Julian Day number

    # -------------------------------------------------------------------------
    # @todo: implement _parse

    # -------------------------------------------------------------------------
    # @todo: implement _format

    # -------------------------------------------------------------------------
    @classmethod
    def from_jd(cls, jd):
        """
            Convert a Julian day number to a year/month/day tuple
            of this calendar (matching jQuery calendars algorithm)

            @param jd: the Julian day number
        """

        jd = math.floor(jd) + 0.5;

        depoch = jd - cls.to_jd(475, 1, 1)

        cycle = math.floor(depoch / 1029983)
        cyear = math.fmod(depoch, 1029983)

        if cyear != 1029982:
            aux1 = math.floor(cyear / 366)
            aux2 = math.fmod(cyear, 366)
            ycycle = math.floor(((2134 * aux1) + (2816 * aux2) + 2815) / 1028522) + aux1 + 1
        else:
            ycycle = 2820

        year = ycycle + (2820 * cycle) + 474
        if year <= 0:
            year -= 1

        yday = jd - cls.to_jd(year, 1, 1) + 1
        if yday <= 186:
            month = math.ceil(yday / 31)
        else:
            month = math.ceil((yday - 6) / 30)

        day = jd - cls.to_jd(year, month, 1) + 1

        return (int(year), int(month), int(day))

    # -------------------------------------------------------------------------
    @classmethod
    def to_jd(cls, year, month, day):
        """
            Convert a year/month/day tuple of this calendar into
            a Julian day number (matching jQuery calendars algorithm)

            @param year: the year number
            @param month: the month number
            @param day: the day-of-month number
        """

        if year >= 0:
            ep_base = year - 474
        else:
            ep_base = year - 473
        ep_year = 474 + math.fmod(ep_base, 2820)

        if month <= 7:
            mm = (month - 1) * 31
        else:
            mm = (month - 1) * 30 + 6

        return day + mm + math.floor((ep_year * 682 - 110) / 2816) + \
               (ep_year - 1) * 365 + math.floor(ep_base / 2820) * 1029983 + \
               cls.JDEPOCH - 1

# =============================================================================
# Date/Time Parser and Formatter (@todo: integrate with S3Calendar)
#
def s3_parse_datetime(string, dtfmt=None):
    """
        Parse a date/time string according to the given format.

        @param string: the string
        @param dtfmt: the string format (defaults to ISOFORMAT)

        @return: a datetime object, or None if the string is invalid
    """

    if not string:
        return None
    if dtfmt is None:
        dtfmt = ISOFORMAT
    try:
        (y, m, d, hh, mm, ss, t0, t1, t2) = time.strptime(string, dtfmt)
        dt = datetime.datetime(y, m, d, hh, mm, ss)
    except ValueError:
        dt = None
    return dt

#--------------------------------------------------------------------------
def s3_format_datetime(dt=None, dtfmt=None):
    """
        Format a datetime object according to the given format.

        @param dt: the datetime object, defaults to datetime.datetime.utcnow()
        @param dtfmt: the string format (defaults to ISOFORMAT)

        @return: a string
    """

    if not dt:
        dt = datetime.datetime.utcnow()
    if dtfmt is None:
        dtfmt = ISOFORMAT
    return dt.strftime(dtfmt)

# =============================================================================
# ISO-8601 Format Date/Time
#
def s3_decode_iso_datetime(dtstr):
    """
        Convert date/time string in ISO-8601 format into a
        datetime object

        @note: this routine is named "iso" for consistency reasons,
                but can actually read a broad variety of datetime
                formats, but may raise a ValueError where not

        @param dtstr: the date/time string
    """

    # Default seconds/microseconds=zero
    DEFAULT = datetime.datetime.utcnow().replace(second=0,
                                                 microsecond=0)

    dt = dateutil.parser.parse(dtstr, default=DEFAULT)
    if dt.tzinfo is None:
        try:
            dt = dateutil.parser.parse(dtstr + " +0000",
                                       default=DEFAULT)
        except:
            # time part missing?
            dt = dateutil.parser.parse(dtstr + " 00:00:00 +0000",
                                       default=DEFAULT)
    return dt

#--------------------------------------------------------------------------
def s3_encode_iso_datetime(dt):
    """
        Convert a datetime object into a ISO-8601 formatted
        string, omitting microseconds

        @param dt: the datetime object
    """
    dx = dt - datetime.timedelta(microseconds=dt.microsecond)
    return dx.isoformat()

# =============================================================================
# Time Zone Handling
#
def s3_utc(dt):
    """
        Get a datetime object for the same date/time as the
        datetime object, but in UTC

        @param dt: the datetime object
    """
    if dt:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=dateutil.tz.tzutc())
        return dt.astimezone(dateutil.tz.tzutc())
    else:
        return None

#--------------------------------------------------------------------------
def s3_get_utc_offset():
    """ Get the current UTC offset for the client """

    offset = None
    session = current.session
    request = current.request

    logged_in = current.auth.is_logged_in()
    if logged_in:
        # 1st choice is the personal preference (useful for GETs if user
        # wishes to see times in their local timezone)
        offset = session.auth.user.utc_offset
        if offset:
            offset = offset.strip()

    if not offset:
        # 2nd choice is what the client provides in the hidden form
        # field (for form POSTs)
        offset = request.post_vars.get("_utc_offset", None)
        if offset:
            offset = int(offset)
            utcstr = offset < 0 and "+" or "-"
            hours = abs(int(offset/60))
            minutes = abs(int(offset % 60))
            offset = "%s%02d%02d" % (utcstr, hours, minutes)
            # Make this the preferred value during this session
            if logged_in:
                session.auth.user.utc_offset = offset

    if not offset:
        # 3rd choice is the server default (what most clients should see
        # the timezone as)
        offset = current.deployment_settings.L10n.utc_offset

    session.s3.utc_offset = offset
    return offset

# END =========================================================================
