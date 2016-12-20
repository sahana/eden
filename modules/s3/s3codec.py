# -*- coding: utf-8 -*-

""" S3 Encoder/Decoder Base Class

    @copyright: 2011-2016 (c) Sahana Software Foundation
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

__all__ = ("S3Codec",)

import json

from xml.sax.saxutils import escape, unescape

from gluon import current
from gluon.storage import Storage

from s3utils import s3_unicode

# =============================================================================
class S3Codec(object):
    """
        Base class for converting S3Resources into/from external
        data formats, for use with S3Importer/S3Exporter
    """

    # A list of fields which should be skipped from PDF/XLS exports
    indices = ["id", "pe_id", "site_id", "sit_id", "item_entity_id"]

    # -------------------------------------------------------------------------
    @staticmethod
    def get_codec(format):

        # Import the codec classes
        from s3codecs import S3SHP
        from s3codecs import S3SVG
        from s3codecs import S3XLS
        from s3codecs import S3RL_PDF

        # Register the codec classes
        CODECS = Storage(
            pdf = S3RL_PDF,
            shp = S3SHP,
            svg = S3SVG,
            xls = S3XLS,
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

            @return: an S3XML ElementTree
        """
        raise NotImplementedError

    def encode(self, resource, **attr):
        """
            API Method to encode an ElementTree into the target format,
            to be implemented by the subclass

            @param resource: the S3Resource

            @return: a handle to the output
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Utilities
    #--------------------------------------------------------------------------
    PY2XML = {"'": "&apos;", '"': "&quot;"}
    @classmethod
    def xml_encode(cls, s):
        """
            XML-escape a string

            @param s: the string
        """
        if s:
            s = escape(s, cls.PY2XML)
        return s

    #--------------------------------------------------------------------------
    XML2PY = {"&apos;": "'", "&quot;": '"'}
    @classmethod
    def xml_decode(cls, s):
        """
            XML-unescape a string

            @param s: the string
        """
        if s:
            s = unescape(s, cls.XML2PY)
        return s

    # -------------------------------------------------------------------------
    @staticmethod
    def crud_string(tablename, name):
        """
            Get a CRUD string

            @param tablename: the table name
            @param name: the name of the CRUD string
        """

        crud_strings = current.response.s3.crud_strings
        # CRUD strings for this table
        _crud_strings = crud_strings.get(tablename, crud_strings)
        return _crud_strings.get(name,
                                 # Default fallback
                                 crud_strings.get(name, None))

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
            output["message"] = s3_unicode(message)
        for k, v in kwargs.items():
            if k != "tree":
                output[k] = v
        output = json.dumps(output)
        if message and tree:
            output = output[:-1] + ', "tree": %s}' % tree
        return output

# End =========================================================================
