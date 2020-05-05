# -*- coding: utf-8 -*-

""" S3 Encoder/Decoder Base Class

    @copyright: 2011-2020 (c) Sahana Software Foundation
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

from .s3utils import s3_str

# =============================================================================
class S3Codec(object):
    """
        Base class for converting S3Resources into/from external
        data formats, for use with S3Importer/S3Exporter
    """

    # A list of fields which should be skipped from PDF/XLS exports
    indices = ["id", "pe_id", "site_id", "sit_id", "item_entity_id"]

    CODECS = {"pdf": "S3RL_PDF",
              "shp": "S3SHP",
              "svg": "S3SVG",
              "xls": "S3XLS",
              "card": "S3PDFCard",
              }

    # -------------------------------------------------------------------------
    @classmethod
    def get_codec(cls, fmt):
        """
            Get a codec by representation format

            @param fmt: the representation format (string)
        """

        codec = cls

        name = cls.CODECS.get(fmt)
        if name:
            package = "applications.%s.modules.s3.codecs.%s" % \
                      (current.request.application, fmt)
            try:
                codec = getattr(__import__(package, fromlist=[name]), name)
            except (ImportError, AttributeError):
                current.log.error("Codec not available: %s" % name)
        else:
            current.log.error("No codec found for '%s' format" % fmt)

        return codec()

    # -------------------------------------------------------------------------
    # API
    #--------------------------------------------------------------------------
    def encode(self, resource, **attr):
        """
            API Method to encode a resource in the target format,
            to be implemented by the subclass (mandatory)

            @param resource: the S3Resource

            @return: a handle to the output
        """
        raise NotImplementedError

    def decode(self, resource, source, **attr):
        """
            API Method to decode a source into an S3XML ElementTree,
            to be implemented by the subclass (if the class does decode)

            @param resource: the S3Resource
            @param source: the source

            @return: an S3XML ElementTree
        """
        return current.xml.tree()

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
            statuscode = 200 if success else 404

        output = {"status": "success" if success else "failed",
                  "statuscode": str(statuscode),
                  }

        tree = kwargs.get("tree", None)
        if message:
            output["message"] = s3_str(message)
        for k, v in kwargs.items():
            if k != "tree":
                output[k] = v
        output = json.dumps(output)
        if message and tree:
            output = output[:-1] + ', "tree": %s}' % tree
        return output

# End =========================================================================
