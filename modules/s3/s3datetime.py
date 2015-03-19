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

__all__ = ("S3DateTime",
           "s3_utc",
           "s3_decode_iso_datetime",
           "s3_encode_iso_datetime",
           "s3_encode_local_datetime",
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

from gluon import *

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
            @param format: the format if wishing to override deployment_settings
            @param utc: the date is given in UTC
        """

        if not format:
            format = current.deployment_settings.get_L10n_date_format()

        if date and isinstance(date, datetime.datetime) and utc:
            offset = cls.get_offset_value(current.session.s3.utc_offset)
            if offset:
                date = date + datetime.timedelta(seconds=offset)

        if date:
            try:
                return date.strftime(str(format))
            except:
                # e.g. dates < 1900
                date = date.isoformat()
                current.log.warning("Date cannot be formatted - using isoformat", date)
                return date
        else:
            return current.messages["NONE"]

    # -----------------------------------------------------------------------------
    @classmethod
    def time_represent(cls, time, utc=False):
        """
            Represent the date according to deployment settings &/or T()

            @param time: the time
            @param utc: the time is given in UTC
        """

        session = current.session
        settings = current.deployment_settings
        format = settings.get_L10n_time_format()

        if time and utc:
            offset = cls.get_offset_value(session.s3.utc_offset)
            if offset:
                time = time + datetime.timedelta(seconds=offset)

        if time:
            return time.strftime(str(format))
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

#--------------------------------------------------------------------------
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

#--------------------------------------------------------------------------
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

#--------------------------------------------------------------------------
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

# END =========================================================================
