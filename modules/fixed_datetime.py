# Copyright (c) 2008, Red Innovation Ltd., Finland
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Red Innovation nor the names of its contributors 
#       may be used to endorse or promote products derived from this software 
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY RED INNOVATION ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL RED INNOVATION BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

__doc__    = """
This module provides monkey-patched Python datetime class
that fully supports different time zones and conversions
between them.

See the source for licensing terms.
"""

__author__    = 'Antti Haapala <antti@redinnovation.com>'
__date__      = '24 Jun 2008'
__version__   = '$Revision$'
__copyright__ = '2008 Red Innovation Ltd.'
__license__   = '3-clause BSD'

from datetime import datetime as _datetime, tzinfo as _tzinfo
from pytz import timezone as _timezone

import time as _time
import pytz as _pytz
import math as _math
import re as _re
from pytz import utc, UTC, HOUR, ZERO

_utc = _pytz.utc
_default_tz = _utc


def set_default_timezone(new_tz):
    """Sets the default time zone used by the objects
       contained in this module. new_tz may be either
       a pytz-compatible tzinfo (requires normalize 
       and localize methods), or a time zone name known
       to pytz.
    """

    global _default_tz
    if type(new_tz) is str or type(new_tz) is unicode:
        new_tz = _pytz.timezone(new_tz)

    _default_tz = new_tz

class FixedOffset(_tzinfo):
    """Fixed offset in minutes east from UTC. Based on 
       the python tutorial and pytz test code."""

    def __init__(self, offset, name):
        """Constructor. Create a new tzinfo object
        with given offset in minutes and name."""
        self.__offset = timedelta(minutes = offset)
        self.__name = name

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return ZERO

    def localize(self, dt, is_dst=False):
        """Convert naive time to local time. Copied 
        from pytz tzinfo classes"""

        if dt.tzinfo is not None:
            raise ValueError, 'Not naive datetime (tzinfo is already set)'

        return dt.replace(tzinfo=self)

    def normalize(self, dt, is_dst=False):
        """Correct the timezone information on the 
        given datetime. Copied from pytz tzinfo classes."""

        if dt.tzinfo is None:
            raise ValueError, 'Naive time - no tzinfo set'

        return dt.replace(tzinfo=self)

    def __str__(self):
        return self.__name

    def __repr__(self):
        return '<%s>' % self.__name


_fixed_offset_tzs = { }

def _get_fixed_offset_tz(offsetmins):
    """For internal use only: Returns a tzinfo with 
    the given fixed offset. This creates only one instance
    for each offset; the zones are kept in a dictionary"""

    if offsetmins == 0:
        return _utc

    if not _fixed_offset_tzs.has_key(offsetmins):
       if offsetmins < 0:
           sign = '-'
           absoff = -offsetmins
       else:
           sign = '+'
           absoff = offsetmins

       name = "UTC%s%02d:%02d" % (sign, int(absoff / 60), absoff % 60)
       inst = FixedOffset(offsetmins, name)
       _fixed_offset_tzs[offsetmins] = inst

    return _fixed_offset_tzs[offsetmins]


_iso8601_parser = _re.compile("""
    ^
    (?P<year> [0-9]{4})(?P<ymdsep>-?)
    (?P<month>[0-9]{2})(?P=ymdsep)
    (?P<day>  [0-9]{2})

    (?: # time part... optional... at least hour must be specified
	(?:T|\s+)
        (?P<hour>[0-9]{2})
        (?:
            # minutes, separated with :, or none, from hours
            (?P<hmssep>[:]?)
            (?P<minute>[0-9]{2})
            (?:
                # same for seconds, separated with :, or none, from hours
                (?P=hmssep)
                (?P<second>[0-9]{2})
            )?
        )?
        
        # fractions
        (?: [,.] (?P<frac>[0-9]{1,10}))?

        # timezone, Z, +-hh or +-hh:?mm. MUST BE, but complain if not there.
        (
            (?P<tzempty>Z) 
        | 
            (?P<tzh>[+-][0-9]{2}) 
            (?: :? # optional separator 
                (?P<tzm>[0-9]{2})
            )?
        )?
    )?
    $
""", _re.X) # """

def _parse_iso(timestamp):
    """Internal function for parsing a timestamp in 
    ISO 8601 format"""

    timestamp = timestamp.strip()
    
    m = _iso8601_parser.match(timestamp)
    if not m:
        raise ValueError("Not a proper ISO 8601 timestamp!")

    year  = int(m.group('year'))
    month = int(m.group('month'))
    day   = int(m.group('day'))
    
    h, min, s, us = None, None, None, 0
    frac = 0
    if m.group('tzempty') == None and m.group('tzh') == None:
        raise ValueError("Not a proper ISO 8601 timestamp: " +
                "missing timezone (Z or +hh[:mm])!")

    if m.group('frac'):
        frac = m.group('frac')
        power = len(frac)
        frac  = long(frac) / 10.0 ** power

    if m.group('hour'):
        h = int(m.group('hour'))

    if m.group('minute'):
        min = int(m.group('minute'))

    if m.group('second'):
        s = int(m.group('second'))

    if frac != None:
        # ok, fractions of hour?
        if min == None:
           frac, min = _math.modf(frac * 60.0)
           min = int(min)

        # fractions of second?
        if s == None:
           frac, s = _math.modf(frac * 60.0)
           s = int(s)

        # and extract microseconds...
        us = int(frac * 1000000)

    if m.group('tzempty') == 'Z':
        offsetmins = 0
    else:
        # timezone: hour diff with sign
        offsetmins = int(m.group('tzh')) * 60
        tzm = m.group('tzm')
      
        # add optional minutes
        if tzm != None:
            tzm = long(tzm)
            offsetmins += tzm if offsetmins > 0 else -tzm

    tz = _get_fixed_offset_tz(offsetmins)
    return datetime(year, month, day, h, min, s, us, tz)


class datetime(_datetime):
    """Time zone aware subclass of Python datetime.datetime"""

    __name__ = 'fixed_datetime.datetime'

    def __new__(cls, year, month, day, hour=0, minute=0, second=0, microsecond=0, tzinfo=None, is_dst=False):
        """Creates a localized timestamp with the given parameters.
        If tzinfo is omitted, the default time zone will be used."""

        if tzinfo == None:
            tzinfo = _default_tz

        dt = _datetime(year, month, day, hour, minute, second, microsecond)
        dt = tzinfo.localize(dt, is_dst=is_dst)
        return _datetime.__new__(
            cls, dt.year, dt.month, dt.day, 
            dt.hour, dt.minute, dt.second, 
            dt.microsecond, dt.tzinfo)

    def __radd__(self, addend):
        """Autonormalized addition of datetimes and timedeltas."""

        added = _datetime.__radd__(self, addend)
        added = self.tzinfo.normalize(added)
        return datetime.__from_datetime_with_tz(added)

    def __add__(self, addend):
        """Autonormalized addition of datetimes and timedeltas."""

        added = _datetime.__add__(self, addend)
        added = self.tzinfo.normalize(added)
        return datetime.__from_datetime_with_tz(added)

    def utctimetuple(self):
        """Return UTC time tuple, compatible with time.gmtime().

        Notice: the original datetime documentation is misleading:
        Calling utctimetuple() on a timezone-aware datetime will 
        return the tuple in UTC, not in local time."""
        return _datetime.utctimetuple(self)

    def astimezone(self, tzinfo):
        """Convert to local time in new timezone tz.

        The result is normalized across DST boundaries."""

        dt = _datetime.astimezone(self, tzinfo)
        dt = tzinfo.normalize(dt)
        return datetime.__from_datetime_with_tz(dt)

    @staticmethod
    def __from_datetime_with_tz(dt):
        """Internal: create a datetime instance from
        a timezone-aware instance of the builtin datetime type."""

        if dt.tzinfo == None:
            raise ValueError("The given datetime.datetime is not timezone-aware!")

        return datetime(dt.year, dt.month, dt.day,
            dt.hour, dt.minute, dt.second, dt.microsecond,
            dt.tzinfo)

    @staticmethod
    def fromtimestamp(timestamp, tz=None):
        """Tz's local time from POSIX timestamp."""

        bd = _time.gmtime(long(timestamp))

        us = 0
        if isinstance(timestamp, float):
            us  = timestamp % 1.0
            us *= 1000000

        args  = list(bd[:6])
        args += [ int(us), _utc ]

        _tmp = datetime(*args)

        if tz == None:
            tz = _default_tz

        rv = _tmp.astimezone(tz)
        return datetime.__from_datetime_with_tz(rv)

    @staticmethod
    def today(tz=None):
        """New datetime with tz's local day and time
        If tz is not specified, use the default timezone"""

        return datetime.fromtimestamp(long(_time.time()), tz)

    @staticmethod
    def now(tz=None):
        """New datetime with tz's local day and time
        If tz is not specified, use the default timezone"""

        return datetime.fromtimestamp(_time.time(), tz)

    @staticmethod
    def utcnow():
        """Return a new datetime representing UTC day and time."""

        return datetime.now(tz=_utc)

    @staticmethod
    def utcfromtimestamp():
        """Return a new UTC datetime from a POSIX timestamp (like time.time())."""

        return datetime.utcfromtimestamp(tz=_utc)

    @staticmethod
    def parseisoformat(timestamp):
        """Parses the given ISO 8601 compatible timestamp string 
        and converts it to fixed_datetime.datetime. The timestamp
        must conform to following formats:

             - the format is DATE SEP TIME TIMEZONE without
               any intervening spaces.

             - the date must be in format YYYY-MM-DD

             - the time may be either
                 * HH:MM:SS,FFFF
                 * HH:MM,FFFF
                 * HH,FFFF
               FFFF is the fractional part. Decimal point can be
               used too.

             - the time zone must be either Z, -HH:MM or +HH:MM

             - the date and time must be separated either by
               whitespace or single T letter

             - the separators - and : may all be omitted, or
               must all be present.

             Examples (Unix Epoch):

                 1970-01-01T00:00:00Z 
                 1970-01-01T00Z 
                 1969-12-31 19,5-04:30
                 19700101T030000+0300
        """

        return _parse_iso(timestamp)

    def isoformat(self, sep='T', short=False):
        """Returns the date represented by this instance
        in ISO 8601 conforming format. The separator
        is used to separate the date and time, and defaults
        to 'T'. This method supports both long and short 
        formats. The long format is
 
            YYYY-MM-DD HH:MM:SS[.FFFFFF]=HH:MM

        and short is
     
            YYYYMMDDTHHMMSS[.FFFFFF]=HHMM

        The fractional part is separated with decimal point and
        is omitted if microseconds stored in this datetime are
        0.
        """

        if not short:
            return _datetime.isoformat(self, sep)

        args = [ self.year, self.month, self.day, self.hour, self.minute, self.second ]

        fmt  = "%04d%02d%02dT%02d%02d%02d"
        tz   = "%s%02d%02d"

        if self.microsecond != 0:
            fmt += ".%06d"
            args += [ self.microsecond ]

        offset = self.tzinfo.utcoffset(self)
        tzseconds = offset.seconds + offset.days * 24 * 60 * 60
        sign = '+' if tzseconds >= 0 else '-'
        tzseconds = abs(tzseconds)
        tzout = tz % (sign, int(tzseconds / 3600), int((tzseconds / 60) % 60))

        dtout = fmt % tuple(args)        
        return dtout + tzout

from datetime import date, timedelta, time, tzinfo, MAXYEAR, MINYEAR
