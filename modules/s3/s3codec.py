# -*- coding: utf-8 -*-

""" S3 Encoder/Decoder Base Class

    @copyright: 2011-12 (c) Sahana Software Foundation
    @license: MIT

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

__all__ = ["S3Codec"]

import datetime
try:
    import dateutil
    import dateutil.parser
    import dateutil.tz
except ImportError:
    import sys
    print >> sys.stderr, "ERROR: python-dateutil module needed for date handling"
    raise

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from xml.sax.saxutils import escape, unescape

from gluon import current
from gluon.storage import Storage

# =============================================================================

class S3Codec(object):
    """
        Base class for converting S3Resources into/from external
        data formats, for use with S3Importer/S3Exporter
    """

    ISOFORMAT = "%Y-%m-%dT%H:%M:%S" #: universal timestamp

    # A list of fields which should be skipped from PDF/XLS exports
    indices = ["id", "pe_id", "site_id", "sit_id", "item_entity_id"]

    # -------------------------------------------------------------------------
    @staticmethod
    def get_codec(format):

        # Import the codec classes
        from codecs import S3XLS
        from codecs import S3RL_PDF

        # Register the codec classes
        CODECS = Storage(
            xls = S3XLS,
            pdf = S3RL_PDF,
        )

        if format in CODECS:
            return CODECS[format]()
        else:
            return S3Codec()

    # -------------------------------------------------------------------------
    # API
    #--------------------------------------------------------------------------

    def decode(self, resource, source, **attr):
        """
            API Method to decode a source into an ElementTree, to be
            implemented by the subclass

            @param resource: the S3Resource
            @param source: the source

            @returns: an S3XML ElementTree
        """
        raise NotImplementedError

    def encode(self, resource, **attr):
        """
            API Method to encode an ElementTree into the target format,
            to be implemented by the subclass

            @param resource: the S3Resource

            @returns: a handle to the output
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Utilities
    #--------------------------------------------------------------------------
    PY2XML = {"'": "&apos;", '"': "&quot;"}
    @staticmethod
    def xml_encode(s):
        """
            XML-escape a string

            @param s: the string
        """
        if s:
            s = escape(s, S3Codec.PY2XML)
        return s

    #--------------------------------------------------------------------------
    XML2PY = {"&apos;": "'", "&quot;": '"'}
    @staticmethod
    def xml_decode(s):
        """
            XML-unescape a string

            @param s: the string
        """
        if s:
            s = unescape(s, S3Codec.XML2PY)
        return s

    #--------------------------------------------------------------------------
    @staticmethod
    def decode_iso_datetime(dtstr):
        """
            Convert date/time string in ISO-8601 format into a
            datetime object

            @note: this routine is named "iso" for consistency reasons,
                   but can actually read a broad variety of datetime
                   formats, but may raise a ValueError where not

            @param dtstr: the date/time string
        """
        DEFAULT = datetime.datetime.utcnow()
        dt = dateutil.parser.parse(dtstr, default=DEFAULT)
        if dt.tzinfo is None:
            try:
                dt = dateutil.parser.parse(dtstr + " +0000",
                                           default=DEFAULT)
            except:
                # time part missing?
                dt = dateutil.parser.parse(dtstr + " 00:00 +0000",
                                           default=DEFAULT)
        return dt

    #--------------------------------------------------------------------------
    @staticmethod
    def as_utc(dt):
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
    @staticmethod
    def encode_iso_datetime(dt):
        """
            Convert a datetime object into a ISO-8601 formatted
            string, omitting microseconds

            @param dt: the datetime object
        """
        dx = dt - datetime.timedelta(microseconds=dt.microsecond)
        return dx.isoformat()

    #--------------------------------------------------------------------------
    @staticmethod
    def encode_local_datetime(dt, fmt=None):
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

    # -------------------------------------------------------------------------
    # Error handling
    # -------------------------------------------------------------------------
    @staticmethod
    def json_message(success=True,
                     statuscode=None,
                     message=None,
                     **kwargs):
        """
            Provide a nicely-formatted JSON Message

            @param success: action succeeded or failed
            @param status_code: the HTTP status code
            @param message: the message text
            @param kwargs: other elements for the message

            @keyword tree: error tree to include as JSON object (rather
                           than as string) for easy decoding
        """

        if statuscode is None:
            statuscode = success and 200 or 404

        status = success and "success" or "failed"
        code = str(statuscode)

        output = {"status": status, "statuscode": str(code)}

        tree = kwargs.get("tree", None)
        if message:
            output["message"] = unicode(message)
        for k, v in kwargs.items():
            if k != "tree":
                output[k] = v
        output = json.dumps(output)
        if message and tree:
            output = output[:-1] + ', "tree": %s}' % tree
        return output

# End =========================================================================
