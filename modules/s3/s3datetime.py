# -*- coding: utf-8 -*-

""" S3 Date/Time Toolkit

    @copyright: 2015-2018 (c) Sahana Software Foundation
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
           "S3DateTimeParser",
           "S3DateTimeFormatter",
           "s3_parse_datetime",
           "s3_format_datetime",
           "s3_decode_iso_datetime",
           "s3_encode_iso_datetime",
           "s3_utc",
           "s3_get_utc_offset",
           "s3_relative_datetime",
           )

import datetime
try:
    import dateutil
    import dateutil.parser
    import dateutil.tz
except ImportError:
    import sys
    sys.stderr.write("ERROR: python-dateutil module needed for date handling\n")
    raise
import math
import re
import time

from gluon import current

# =============================================================================
# Constants
#
ISOFORMAT = "%Y-%m-%dT%H:%M:%S" #: ISO 8601 Combined Date+Time format
OFFSET = re.compile(r"([+|-]{0,1})(\d{1,2}):(\d\d)")
RELATIVE = re.compile(r"([+-]{0,1})([0-9]*)([YMDhms])")
SECONDS = {"D": 86400, "h": 3600, "m": 60, "s": 1}

# =============================================================================
class S3DateTime(object):
    """
        Toolkit for date+time parsing/representation
    """

    # -------------------------------------------------------------------------
    @classmethod
    def date_represent(cls, dt, format=None, utc=False, calendar=None):
        """
            Represent the date according to deployment settings &/or T()

            @param dt: the date (datetime.date or datetime.datetime)
            @param format: the format (overrides deployment setting)
            @param utc: the date is given in UTC
            @param calendar: the calendar to use (defaults to current.calendar)
        """

        if not format:
            format = current.deployment_settings.get_L10n_date_format()

        if calendar is None:
            calendar = current.calendar
        elif isinstance(calendar, basestring):
            calendar = S3Calendar(calendar)

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
            dtstr = calendar.format_date(dt, dtfmt=format, local=True)
        else:
            dtstr = current.messages["NONE"]

        return dtstr

    # -----------------------------------------------------------------------------
    @classmethod
    def datetime_represent(cls, dt, format=None, utc=False, calendar=None):
        """
            Represent the datetime according to deployment settings &/or T()

            @param dt: the datetime
            @param utc: the datetime is given in UTC
            @param calendar: the calendar to use (defaults to current.calendar)
        """

        if format is None:
            format = current.deployment_settings.get_L10n_datetime_format()

        if calendar is None:
            calendar = current.calendar
        elif isinstance(calendar, basestring):
            calendar = S3Calendar(calendar)

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
            dtstr = calendar.format_datetime(dt, dtfmt=format, local=True)
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
                raise TypeError("Invalid argument type: %s" % type(time))
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

    # -------------------------------------------------------------------------
    # Constants to be implemented by subclasses
    # -------------------------------------------------------------------------

    JDEPOCH = 1721425.5 # first day of this calendar as Julian Day number

    MONTH_NAME = ("January", "February", "March",
                  "April", "May", "June",
                  "July", "August", "September",
                  "October", "November", "December",
                  )

    MONTH_ABBR = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
                  )

    MONTH_DAYS = (31, (28, 29), 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

    FIRST_DOW = 1 # Monday

    # -------------------------------------------------------------------------
    # Methods to be implemented by subclasses
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
    # Common Interface Methods (must not be implemented by subclasses):
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
    @property
    def first_dow(self):
        """ Get the first day of the week for this calendar """

        calendar = self.calendar

        first_dow = calendar._first_dow
        if first_dow is None:
            # Deployment setting?
            first_dow = current.deployment_settings.get_L10n_firstDOW()
            if first_dow is None:
                # Calendar-specific default
                first_dow = calendar.FIRST_DOW
            calendar._first_dow = first_dow

        return first_dow

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
        from s3utils import s3_str
        dtfmt = s3_str(dtfmt)

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
        from s3utils import s3_str
        dtfmt = s3_str(dtfmt)

        # Remove microseconds
        # - for the case that the calendar falls back to .isoformat
        if isinstance(dt, datetime.datetime):
            dt = dt.replace(microsecond=0)

        return self.calendar._format(dt, dtfmt)

    # -------------------------------------------------------------------------
    # Base class methods (must not be implemented by subclasses):
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
                           "Afghan": S3AfghanCalendar,
                           "Nepali": S3NepaliCalendar,
                           }

        if name is None:
            self._name = None
            self._calendar = None
        elif name == self.CALENDAR:
            self._name = name
            self._calendar = self
        else:
            self._set_calendar(name)

        self._parser = None

        self._first_dow = None

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
    def _get_parser(self, dtfmt):

        # Gregorian calendar does not use a parser
        if self.name == "Gregorian":
            return None

        # Configure the parser
        parser = self._parser
        if parser is None:
            parser = S3DateTimeParser(self, dtfmt)
        else:
            parser.set_format(dtfmt)
        self._parser = parser

        return parser

    # -------------------------------------------------------------------------
    def _parse(self, dtstr, dtfmt):

        # Get the parser
        parser = self._get_parser(dtfmt)

        if not parser:
            # Gregorian calendar - use strptime
            try:
                timetuple = time.strptime(dtstr, dtfmt)
            except ValueError, e:
                # Seconds missing?
                try:
                    timetuple = time.strptime(dtstr + ":00", dtfmt)
                except ValueError:
                    raise e
            return timetuple[:6]

        # Use calendar-specific parser
        return parser.parse(dtstr)

    # -------------------------------------------------------------------------
    def _format(self, dt, dtfmt):
        """
            Get a string representation for a datetime.datetime according
            to this calendar and dtfmt, to be implemented by subclass

            @param dt: the datetime.datetime
            @param dtfmt: the datetime format (strftime)

            @return: the string representation (str)

            @raises TypeError: for invalid argument types
        """

        if self.name == "Gregorian":
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
                raise TypeError("Invalid argument type: %s" % type(dt))

        else:
            if not isinstance(dt, datetime.datetime):
                try:
                    timetuple = (dt.year, dt.month, dt.day, 0, 0, 0)
                except AttributeError:
                    # Invalid argument type
                    raise TypeError("Invalid argument type: %s" % type(dt))
            else:
                timetuple = (dt.year, dt.month, dt.day,
                             dt.hour, dt.minute, dt.second,
                             )

            formatter = S3DateTimeFormatter(self)
            dtstr = formatter.render(self._cdate(timetuple), dtfmt)

        return dtstr

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
    """

    CALENDAR = "Persian"

    JDEPOCH = 1948320.5 # first day of this calendar as Julian Day number

    MONTH_NAME = ("Farvardin", "Ordibehesht", "Khordad",
                  "Tir", "Mordad", "Shahrivar",
                  "Mehr", "Aban", "Azar",
                  "Day", "Bahman", "Esfand",
                  )


    MONTH_ABBR = ("Far", "Ord", "Kho", "Tir", "Mor", "Sha",
                  "Meh", "Aba", "Aza", "Day", "Bah", "Esf",
                  )

    MONTH_DAYS = (31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, (29, 30))

    FIRST_DOW = 6 # Shambe

    # -------------------------------------------------------------------------
    # Methods to be implemented by subclasses
    # -------------------------------------------------------------------------
    @classmethod
    def from_jd(cls, jd):
        """
            Convert a Julian day number to a year/month/day tuple
            of this calendar (matching jQuery calendars algorithm)

            @param jd: the Julian day number
        """

        jd = math.floor(jd) + 0.5

        depoch = jd - cls.to_jd(475, 1, 1)

        cycle = math.floor(depoch / 1029983)
        cyear = depoch % 1029983

        if cyear != 1029982:
            aux1 = math.floor(cyear / 366)
            aux2 = cyear % 366
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
        ep_year = 474 + (ep_base % 2820)

        if month <= 7:
            mm = (month - 1) * 31
        else:
            mm = (month - 1) * 30 + 6

        result = day + mm + math.floor((ep_year * 682 - 110) / 2816) + \
               (ep_year - 1) * 365 + math.floor(ep_base / 2820) * 1029983 + \
               cls.JDEPOCH - 1

        return result

# =============================================================================
class S3AfghanCalendar(S3PersianCalendar):
    """
        Afghan variant of the Solar Hijri calendar - this calendar uses
        the same calendar rules as the "Persian" calendar, but with
        different month names.

        @note: this is using "romanized" Dari month names as translation
               basis (rather than their actual English translation, which
               would simply be the names of the signs of Zodiac the sun is
               passing through in the respective months, e.g. Tawr (Sawr) = Taurus).
               Transcriptions vary widely between sources, though - as do
               the Dari and Pashto spellings :/
    """

    CALENDAR = "Afghan"

    MONTH_NAME = ("Hamal", "Sawr", "Jawza",
                  "Saratan", "Asad", "Sonbola",
                  "Mizan", "Aqrab", "Qaws",
                  "Jadi", "Dalw", "Hut",
                  )

    MONTH_ABBR = ("Ham", "Saw", "Jaw", "Sar", "Asa", "Son",
                  "Miz", "Aqr", "Qaw", "Jad", "Dal", "Hut",
                  )

    FIRST_DOW = 6 # Shambe

# =============================================================================
class S3NepaliCalendar(S3Calendar):
    """
        S3Calendar subclass implementing the Nepali calendar (Bikram Samvat)
    """

    # -------------------------------------------------------------------------
    # Constants to be implemented by subclasses
    # -------------------------------------------------------------------------

    CALENDAR = "Nepali"

    JDEPOCH = 1700709.5 # first day of this calendar as Julian Day number

    MONTH_NAME = ("Baisakh", "Jestha", "Ashadh",
                  "Shrawan", "Bhadra", "Ashwin",
                  "Kartik", "Mangsir", "Paush",
                  "Mangh", "Falgun", "Chaitra",
                  )


    MONTH_ABBR = ("Bai", "Je", "As",
                  "Shra", "Bha", "Ash",
                  "Kar", "Mang", "Pau",
                  "Ma", "Fal", "Chai",
                  )

    MONTH_DAYS = ((30, 31), (31, 32), (31, 32),
                  (31, 32), (31, 32), (30, 31),
                  (29, 30), (29, 30), (29, 30),
                  (29, 30), (29, 30), (30, 31))

    FIRST_DOW = 1 # Sombaar (=Monday)

    # There is no algorithm to predict the days in the individual months
    # of the Bikram Samvat calendar for a particular year, so we have to
    # hardcode this information as a mapping dict (taken from jquery.calendars
    # in order to match the front-end widget's calculations).
    # Outside of the year range of this dict (years A.B.S.), we have to
    # fall back to an approximation formula which may though give a day
    # ahead or behind the actual date
    NEPALI_CALENDAR_DATA = {
        # These data are from http://www.ashesh.com.np
        1970: [18, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        1971: [18, 31, 31, 32, 31, 32, 30, 30, 29, 30, 29, 30, 30],
        1972: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        1973: [19, 30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        1974: [19, 31, 31, 32, 30, 31, 31, 30, 29, 30, 29, 30, 30],
        1975: [18, 31, 31, 32, 32, 30, 31, 30, 29, 30, 29, 30, 30],
        1976: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        1977: [18, 31, 32, 31, 32, 31, 31, 29, 30, 29, 30, 29, 31],
        1978: [18, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        1979: [18, 31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        1980: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        1981: [18, 31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
        1982: [18, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        1983: [18, 31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        1984: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        1985: [18, 31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
        1986: [18, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        1987: [18, 31, 32, 31, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        1988: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        1989: [18, 31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        1990: [18, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        1991: [18, 31, 32, 31, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        # These data are from http://nepalicalendar.rat32.com/index.php
        1992: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        1993: [18, 31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        1994: [18, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        1995: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        1996: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        1997: [18, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        1998: [18, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        1999: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2000: [17, 30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2001: [18, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2002: [18, 31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2003: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2004: [17, 30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2005: [18, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2006: [18, 31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2007: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2008: [17, 31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 29, 31],
        2009: [18, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2010: [18, 31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2011: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2012: [17, 31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
        2013: [18, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2014: [18, 31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2015: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2016: [17, 31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
        2017: [18, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2018: [18, 31, 32, 31, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2019: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2020: [17, 31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2021: [18, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2022: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        2023: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2024: [17, 31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2025: [18, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2026: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2027: [17, 30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2028: [17, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2029: [18, 31, 31, 32, 31, 32, 30, 30, 29, 30, 29, 30, 30],
        2030: [17, 31, 32, 31, 32, 31, 30, 30, 30, 30, 30, 30, 31],
        2031: [17, 31, 32, 31, 32, 31, 31, 31, 31, 31, 31, 31, 31],
        2032: [17, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32],
        2033: [18, 31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2034: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2035: [17, 30, 32, 31, 32, 31, 31, 29, 30, 30, 29, 29, 31],
        2036: [17, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2037: [18, 31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2038: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2039: [17, 31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
        2040: [17, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2041: [18, 31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2042: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2043: [17, 31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
        2044: [17, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2045: [18, 31, 32, 31, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2046: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2047: [17, 31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2048: [17, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2049: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        2050: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2051: [17, 31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2052: [17, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2053: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        2054: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2055: [17, 31, 31, 32, 31, 31, 31, 30, 29, 30, 30, 29, 30],
        2056: [17, 31, 31, 32, 31, 32, 30, 30, 29, 30, 29, 30, 30],
        2057: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2058: [17, 30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2059: [17, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2060: [17, 31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2061: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2062: [17, 30, 32, 31, 32, 31, 31, 29, 30, 29, 30, 29, 31],
        2063: [17, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2064: [17, 31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2065: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2066: [17, 31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 29, 31],
        2067: [17, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2068: [17, 31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2069: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2070: [17, 31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
        2071: [17, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2072: [17, 31, 32, 31, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2073: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2074: [17, 31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2075: [17, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2076: [16, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        2077: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2078: [17, 31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2079: [17, 31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2080: [16, 31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        # These data are from http://www.ashesh.com.np/nepali-calendar/
        2081: [17, 31, 31, 32, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2082: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2083: [17, 31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2084: [17, 31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2085: [17, 31, 32, 31, 32, 31, 31, 30, 30, 29, 30, 30, 30],
        2086: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2087: [16, 31, 31, 32, 31, 31, 31, 30, 30, 29, 30, 30, 30],
        2088: [16, 30, 31, 32, 32, 30, 31, 30, 30, 29, 30, 30, 30],
        2089: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2090: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2091: [16, 31, 31, 32, 31, 31, 31, 30, 30, 29, 30, 30, 30],
        2092: [16, 31, 31, 32, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2093: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2094: [17, 31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2095: [17, 31, 31, 32, 31, 31, 31, 30, 29, 30, 30, 30, 30],
        2096: [17, 30, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2097: [17, 31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2098: [17, 31, 31, 32, 31, 31, 31, 29, 30, 29, 30, 30, 31],
        2099: [17, 31, 31, 32, 31, 31, 31, 30, 29, 29, 30, 30, 30],
        2100: [17, 31, 32, 31, 32, 30, 31, 30, 29, 30, 29, 30, 30],
    }

    # -------------------------------------------------------------------------
    # Methods to be implemented by subclasses
    # -------------------------------------------------------------------------
    @classmethod
    def from_jd(cls, jd):
        """
            Convert a Julian day number to a year/month/day tuple
            of this calendar (matching jQuery calendars algorithm)

            @param jd: the Julian day number
        """

        gyear = cls._jd_to_gregorian(jd)[0]

        gdoy = jd - cls._gregorian_to_jd(gyear, 1, 1) + 1

        year = gyear + 56
        cdata = cls._get_calendar_data(year)

        month = 9
        rdays = cdata[month] - cdata[0] + 1

        while gdoy > rdays:
            month += 1
            if month > 12:
                month = 1
                year += 1
                cdata = cls._get_calendar_data(year)
            rdays += cdata[month]

        day = cdata[month] - (rdays - gdoy)

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

        cmonth = month
        cyear = year

        # Get the Gregorian year
        if cmonth > 9 or cmonth == 9 and day > cls._get_calendar_data(cyear)[0]:
            gyear = year - 56
        else:
            gyear = year - 57

        # Calculate days since January 1st in Gregorian year
        gdoy = 0
        if month != 9:
            gdoy = day
            cmonth -= 1

        cdata = cls._get_calendar_data(cyear)
        while cmonth != 9:
            if cmonth <= 0:
                cmonth = 12
                cyear -= 1
                cdata = cls._get_calendar_data(cyear)
            gdoy += cdata[cmonth]
            cmonth -= 1

        if month == 9:
            gdoy += day - cdata[0]
            if gdoy <= 0:
                gyear_ = gyear + (1 if gyear < 0 else 0)
                gleapyear = gyear_ % 4 == 0 and \
                            (gyear_ % 100 != 0 or gyear_ % 400 == 0)
                gdoy += 366 if gleapyear else 365
        else:
            gdoy += cdata[9] - cdata[0]

        # Convert January 1st of the Gregorian year to JD and
        # add the days that went since then
        return cls._gregorian_to_jd(gyear, 1, 1) + gdoy

    # -------------------------------------------------------------------------
    @classmethod
    def _get_calendar_data(cls, year):
        """
            Helper method to determine the days in the individual months
            of the BS calendar, as well as the start of the year
        """

        default = [17, 31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30]

        return cls.NEPALI_CALENDAR_DATA.get(year, default)

# =============================================================================
class S3DateTimeParser(object):
    """ Date/Time Parser for non-Gregorian calendars """

    def __init__(self, calendar, dtfmt=None):
        """
            Constructor

            @param calendar: the calendar
            @param dtfmt: the date/time format
        """

        # Get the effective calendar
        if not calendar:
            raise TypeError("Invalid calendar: %s (%s)" % (calendar, type(calendar)))
        self.calendar = calendar.calendar

        self.grammar = None
        self.rules = None

        self.set_format(dtfmt)

    # -------------------------------------------------------------------------
    def parse(self, string):
        """
            Parse a date/time string

            @param string: the date/time string
            @return: a timetuple (y, m, d, hh, mm, ss)
        """

        if not isinstance(string, basestring):
            raise TypeError("Invalid argument type: expected str, got %s" % type(string))
        try:
            result = self.grammar.parseString(string)
        except self.ParseException:
            raise ValueError("Invalid date/time: %s" % string)

        return self._validate(result)

    # -------------------------------------------------------------------------
    def set_format(self, dtfmt):
        """
            Update the date/time format for this parser, and generate
            the corresponding pyparsing grammar

            @param dtfmt: the date/time format
        """

        if not isinstance(dtfmt, basestring):
            raise TypeError("Invalid date/time format: %s (%s)" % (dtfmt, type(dtfmt)))

        import pyparsing as pp
        self.ParseException = pp.ParseException

        from s3utils import s3_unicode

        # Get the rules
        rules = self.rules
        if rules is None:
            rules = self.rules = self._get_rules()

        # Interpret the format
        result = []
        sequence = []

        def close(s):
            s = "".join(s).strip()
            if s:
                result.append(pp.Suppress(pp.Literal(s)))

        rule = False
        for c in s3_unicode(dtfmt):
            if rule and c in rules:
                # Close previous sequence
                sequence.pop()
                close(sequence)
                # Append control rule
                result.append(rules[c])
                # Start new sequence
                sequence = []
                # Close rule
                rule = False
                continue

            if c == "%" and not rule:
                rule = True
            else:
                rule = False
            sequence.append(c)
        if sequence:
            close(sequence)

        if result:
            grammar = result[0]
            for item in result[1:]:
                grammar += item
        else:
            # Default = ignore everything
            grammar = pp.Suppress(pp.Regex(".*"))

        self.grammar = grammar
        return grammar

    # -------------------------------------------------------------------------
    def _validate(self, parse_result):
        """
            Validate the parse result and convert it into a time tuple

            @param parse_result: the parse result
            @return: a timetuple (y, m, d, hh, mm, ss)
        """

        calendar = self.calendar

        # Get the current date
        now = current.request.utcnow
        today = (now.year, now.month, now.day, 0, 0, 0)

        # Convert today into current calendar
        cyear, cmonth = calendar._cdate(today)[:2]

        # Year
        year = parse_result.get("year4")
        if year is None:
            year = parse_result.get("year2")
            if year is None:
                # Fall back to current year of the calendar
                year = cyear
            else:
                # Add the current century of the calendar
                current_century = int(cyear / 100) * 100
                year = current_century + year

        # Month
        month = parse_result.get("month") or cmonth

        # Day of Month
        day = parse_result.get("day") or 1

        # Correct the date by converting to JD and back
        year, month, day = calendar.from_jd(calendar.to_jd(year, month, day))

        # Hours
        hour = parse_result.get("hour24")
        if hour is None:
            # 12 hours?
            hour = parse_result.get("hour12")
            if hour is None:
                hour = 0
            else:
                # Do we have am or pm?
                if hour == 12:
                    hour = 0
                if parse_result.get("ampm", "AM") == "PM":
                    hour += 12

        # Minute
        minute = parse_result.get("minute") or 0

        # Second
        second = parse_result.get("second") or 0

        return (year, month, day, hour, minute, second)

    # -------------------------------------------------------------------------
    @staticmethod
    def _parse_int(s, l, tokens):
        """ Parser helper to convert a token into an integer number """

        try:
            return int(tokens[0])
        except (TypeError, ValueError):
            return None

    # -------------------------------------------------------------------------
    def _get_rules(self):
        """
            Generate the general pyparsing rules for this calendar

            @return: the rules dict

            rules = {"d": Day of the month as a zero-padded decimal number
                     "b": Month as locale’s abbreviated name
                     "B": Month as locale’s full name
                     "m": Month as a zero-padded decimal number
                     "y": Year without century as a zero-padded decimal number
                     "Y": Year with century as a decimal number
                     "H": Hour (24-hour clock) as a zero-padded decimal number
                     "I": Hour (12-hour clock) as a zero-padded decimal number
                     "p": Locale’s equivalent of either AM or PM
                     "M": Minute as a zero-padded decimal number
                     "S": Second as a zero-padded decimal number
                     }

            @todo: support day-of-week options (recognize but suppress when parsing)
        """

        import pyparsing as pp

        T = current.T
        calendar = self.calendar

        oneOf = pp.oneOf
        parse_int = self._parse_int

        def numeric(minimum, maximum):
            """ Helper to define rules for zero-padded numeric values """
            zp = " ".join("%02d" % i \
                 for i in xrange(minimum, min(10, maximum + 1)))
            np = " ".join("%d" % i \
                 for i in xrange(minimum, maximum + 1))
            return (oneOf(zp) ^ oneOf(np)).setParseAction(parse_int)

        # Day
        month_days = calendar.MONTH_DAYS
        days = [(max(d) if isinstance(d, tuple) else d) for d in month_days]
        day = numeric(1, max(days)).setResultsName("day")

        # Month
        CaselessLiteral = pp.CaselessLiteral
        replaceWith = pp.replaceWith
        # ...numeric
        num_months = len(calendar.MONTH_NAME)
        month = numeric(1, num_months).setResultsName("month")
        # ...name
        expr = None
        for i, m in enumerate(calendar.MONTH_NAME):
            month_number = str(i+1)
            month_literal = CaselessLiteral(m)
            month_t = str(T(m))
            if month_t != m:
                month_literal |= CaselessLiteral(month_t)
            month_literal.setParseAction(replaceWith(month_number))
            expr = (expr | month_literal) if expr else month_literal
        month_name = expr.setParseAction(parse_int).setResultsName("month")
        # ...abbreviation
        expr = None
        for i, m in enumerate(calendar.MONTH_ABBR):
            month_number = str(i+1)
            month_literal = CaselessLiteral(m)
            month_t = str(T(m))
            if month_t != m:
                month_literal |= CaselessLiteral(month_t)
            month_literal.setParseAction(replaceWith(month_number))
            expr = (expr | month_literal) if expr else month_literal
        month_abbr = expr.setParseAction(parse_int).setResultsName("month")

        # Year
        Word = pp.Word
        nums = pp.nums
        # ...without century
        year2 = Word(nums, min=1, max=2)
        year2 = year2.setParseAction(parse_int).setResultsName("year2")
        # ...with century
        year4 = Word(nums, min=1, max=4)
        year4 = year4.setParseAction(parse_int).setResultsName("year4")

        # Hour
        hour24 = numeric(0, 23).setResultsName("hour24")
        hour12 = numeric(0, 12).setResultsName("hour12")

        # Minute
        minute = numeric(0, 59).setResultsName("minute")

        # Second
        second = numeric(0, 59).setResultsName("second")

        # AM/PM
        am = ("AM", str(T("AM")), "am", str(T("am")))
        am = oneOf(" ".join(am)).setParseAction(pp.replaceWith("AM"))
        pm = ("PM", str(T("PM")), "pm", str(T("pm")))
        pm = oneOf(" ".join(pm)).setParseAction(pp.replaceWith("PM"))
        ampm = (am ^ pm).setResultsName("ampm")

        rules = {"d": day,
                 "b": month_abbr,
                 "B": month_name,
                 "m": month,
                 "y": year2,
                 "Y": year4,
                 "H": hour24,
                 "I": hour12,
                 "p": ampm,
                 "M": minute,
                 "S": second,
                 }

        return rules

# =============================================================================
class S3DateTimeFormatter(object):
    """ Date/Time Formatter for non-Gregorian calendars """

    def __init__(self, calendar):
        """
            Constructor

            @param calendar: the calendar
        """

        # Get the effective calendar
        if not calendar:
            raise TypeError("Invalid calendar: %s (%s)" % (calendar, type(calendar)))
        self.calendar = calendar.calendar

    # -------------------------------------------------------------------------
    def render(self, timetuple, dtfmt):
        """
            Render a timetuple as string according to the given format

            @param timetuple: the timetuple (y, m, d, hh, mm, ss)
            @param dtfmt: the date/time format (string)

            @todo: support day-of-week options
        """

        y, m, d, hh, mm, ss = timetuple

        T = current.T
        calendar = self.calendar

        from s3utils import s3_unicode

        rules = {"d": "%02d" % d,
                 "b": T(calendar.MONTH_ABBR[m - 1]),
                 "B": T(calendar.MONTH_NAME[m - 1]),
                 "m": "%02d" % m,
                 "y": "%02d" % (y % 100),
                 "Y": "%04d" % y,
                 "H": "%02d" % hh,
                 "I": "%02d" % ((hh % 12) or 12),
                 "p": T("AM") if hh < 12 else T("PM"),
                 "M": "%02d" % mm,
                 "S": "%02d" % ss,
                 }

        # Interpret the format
        result = []
        sequence = []

        def close(s):
            s = "".join(s)
            if s:
                result.append(s)

        rule = False
        for c in s3_unicode(dtfmt):
            if rule and c in rules:
                # Close previous sequence
                sequence.pop()
                close(sequence)
                # Append control rule
                result.append(s3_unicode(rules[c]))
                # Start new sequence
                sequence = []
                # Close rule
                rule = False
                continue

            if c == "%" and not rule:
                rule = True
            else:
                rule = False
            sequence.append(c)
        if sequence:
            close(sequence)

        return "".join(result)

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
        (y, m, d, hh, mm, ss) = time.strptime(string, dtfmt)[:6]
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
        Convert date/time string in ISO-8601 format into a datetime object

        @note: this has "iso" in its name for consistency reasons,
               but can actually read a variety of formats

        @param dtstr: the date/time string

        @returns: a timezone-aware datetime.datetime object

        @raises: ValueError if the string cannot be parsed
    """

    # Default seconds/microseconds=zero
    DEFAULT = datetime.datetime.utcnow().replace(second = 0,
                                                 microsecond = 0,
                                                 )

    try:
        dt = dateutil.parser.parse(dtstr, default=DEFAULT)
    except (AttributeError, TypeError, ValueError):
        raise ValueError("Invalid date/time string: %s (%s)" % (dtstr, type(dtstr)))

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=dateutil.tz.tzutc())

    return dt

#--------------------------------------------------------------------------
def s3_encode_iso_datetime(dt):
    """
        Convert a datetime object into a ISO-8601 formatted
        string, omitting microseconds

        @param dt: the datetime object
    """

    if isinstance(dt, (datetime.datetime, datetime.time)):
        dx = dt.replace(microsecond=0)
    else:
        dx = dt
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

# =============================================================================
# Utilities
#
def s3_relative_datetime(dtexpr):
    """
        Return an absolute datetime for a relative date/time expression;

        @param dtexpr: the relative date/time expression,
                       syntax: "[+|-][numeric][Y|M|D|h|m|s]",
                       e.g. "+12M" = twelve months from now,
                       additionally recognizes the string "NOW"

        @return: datetime.datetime (UTC), or None if dtexpr is invalid
    """

    if dtexpr:
        dtexpr = dtexpr.strip()
        now = current.request.utcnow
        if dtexpr.lower() == "now":
            return now
        elif dtexpr[0] not in "+-":
            return None
    else:
        return None

    from dateutil.relativedelta import relativedelta
    timedelta = datetime.timedelta

    f = 1
    valid = False
    then = now
    for m in RELATIVE.finditer(dtexpr):

        (sign, value, unit) = m.group(1,2,3)

        try:
            value = int(value)
        except ValueError:
            continue

        if sign == "-":
            f = -1
        elif sign == "+":
            f = 1

        if unit == "Y":
            then += relativedelta(years = f * value)
        elif unit == "M":
            then += relativedelta(months = f * value)
        else:
            then += timedelta(seconds = f * value * SECONDS[unit])
        valid = True

    return then if valid else None

# END =========================================================================
