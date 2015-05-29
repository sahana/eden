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
           "s3_encode_local_datetime",
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
    def date_represent(cls, date, format=None, utc=False):
        """
            Represent the date according to deployment settings &/or T()

            @param date: the date
            @param format: the format (overrides deployment setting)
            @param utc: the date is given in UTC
        """

        if not format:
            format = current.deployment_settings.get_L10n_date_format()

        if date:
            if utc and isinstance(date, datetime.datetime):
                offset = cls.get_offset_value(current.session.s3.utc_offset)
                if offset:
                    date = date + datetime.timedelta(seconds=offset)
            try:
                dtstr = date.strftime(str(format))
            except ValueError:
                # Dates < 1900 not supported by strftime
                year = date.year
                eformat = str(format).replace("%Y", "{{Y}}").replace("%y", "{{y}}")
                dtstr = date.replace(year=1900).strftime(eformat)
                dtstr = dtstr.replace("{{Y}}", "%d" % year) \
                             .replace("{{y}}", "%02d" % (year % 100))
                return dtstr
            except AttributeError:
                # Invalid argument type
                raise TypeError("date_represent: invalid argument type: %s" % type(date))
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
    @classmethod
    def datetime_represent(cls, dt, utc=False):
        """
            Represent the datetime according to deployment settings &/or T()

            @param dt: the datetime
            @param utc: the datetime is given in UTC
        """

        if dt and utc:
            offset = cls.get_offset_value(current.session.s3.utc_offset)
            if offset:
                dt = dt + datetime.timedelta(seconds=offset)

        if dt:
            return s3_encode_local_datetime(dt)
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
        Calendar Base Class

        Subclasses define their own CALENDAR name, and are registered
        with this name in the calendars dict in S3Calendar._set_calendar().
    """

    CALENDAR = "Gregorian"

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

        # Gregorian Calendar just uses strptime
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
    def _cdate(timetuple):
        """
            Convert a time tuple from Gregorian calendar to this calendar,
            to be implemented by subclass

            @param timetuple: time tuple (y, m, d, hh, mm, ss)
            @return: time tuple (this calendar)
        """

        # Gregorian Calendar does nothing here
        return timetuple

    # -------------------------------------------------------------------------
    @staticmethod
    def _gdate(timetuple):
        """
            Convert a time tuple from this calendar to Gregorian calendar,
            to be implemented by subclass

            @param timetuple: time tuple (y, m, d, hh, mm, ss)
            @return: time tuple (Gregorian)
        """

        # Gregorian Calendar does nothing here
        return timetuple

    # -------------------------------------------------------------------------
    # Methods to be implemented by subclasses:
    # -------------------------------------------------------------------------
    def _format_date(self, dt):
        """
            Format a date according to this calendar

            @param dt: the date (datetime.date or datetime.datetime)
            @return: the date as string
        """

        raise NotImplementedError

    # -------------------------------------------------------------------------
    def _format_datetime(self, dt):
        """
            Format a datetime according to this calendar

            @param dt: the datetime (datetime.datetime)
            @return: the datetime as string
        """

        raise NotImplementedError

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
    def format_date(self, dt):
        """
            Format a date according to this calendar

            @param dt: the date (datetime.date or datetime.datetime)
            @return: the date as string
        """

        return self.calendar._format_date(dt)

    # -------------------------------------------------------------------------
    def format_datetime(self, dt):
        """
            Format a datetime according to this calendar

            @param dt: the datetime (datetime.datetime)
            @return: the datetime as string
        """

        return self.calendar._format_datetime(dt)

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
# Local Format Date/Time
#
def s3_encode_local_datetime(dt, fmt=None):
    """
        Convert a datetime object into a local date/time formatted
        string, omitting microseconds

        @param dt: the datetime object
    """
    if fmt is None:
        format = current.deployment_settings.get_L10n_datetime_format()
    else:
        format = fmt
    dx = dt - datetime.timedelta(microseconds=dt.microsecond)
    return dx.strftime(str(format))

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

    seconds = datetime.timedelta(seconds=S3DateTime.get_offset_value(offset))
    current.response.s3.local_date = (request.utcnow + seconds).date()

    return offset

# END =========================================================================
