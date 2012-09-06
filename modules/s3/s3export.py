# -*- coding: utf-8 -*-

""" Resource Export Tools

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>}

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: 2009-2012 (c) Sahana Software Foundation
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

__all__ = ["S3Exporter"]

from gluon import current
from gluon.storage import Storage

from s3codec import S3Codec

# =============================================================================
class S3Exporter(object):
    """
        Exporter toolkit
    """

    def __init__(self):
        """ Constructor """

        T = current.T

        self.ERROR = Storage(
            REPORTLAB_ERROR = T("%(module)s not installed") % dict(module="ReportLab"),
            NO_RECORDS = T("No records in this resource"),
            XLWT_ERROR = T("%(module)s not installed") % dict(module="xlwt"),
        )

    # -------------------------------------------------------------------------
    def xls(self, *args, **kwargs):

        codec = S3Codec.get_codec("xls").encode
        return codec(*args, **kwargs)

    # -------------------------------------------------------------------------
    def pdf(self, *args, **kwargs):

        codec = S3Codec.get_codec("pdf").encode
        return codec(*args, **kwargs)

    # -------------------------------------------------------------------------
    def csv(self, resource):
        """
            Export resource as CSV

            @param resource: the resource to export

            @note: export does not include components!

            @todo: implement audit
        """

        request = current.request
        response = current.response

        if response:
            servername = request and "%s_" % request.env.server_name or ""
            filename = "%s%s.csv" % (servername, resource.tablename)
            from gluon.contenttype import contenttype
            response.headers["Content-Type"] = contenttype(".csv")
            response.headers["Content-disposition"] = "attachment; filename=%s" % filename

        rows = resource._load()
        return str(rows)

    # -------------------------------------------------------------------------
    def json(self, resource,
             start=None,
             limit=None,
             fields=None,
             orderby=None):
        """
            Export a resource as JSON

            @note: export does not include components!

            @ToDo: Deprecate (after modifying s3search json functions)

            @param resource: the resource to export
            @param start: index of the first record to export (for slicing)
            @param limit: maximum number of records to export (for slicing)
            @param fields: fields to include in the export (None for all fields)
        """

        if fields is None:
            fields = [f for f in resource.table if f.readable]

        attributes = dict()

        if orderby is not None:
            attributes["orderby"] = orderby

        limitby = resource.limitby(start=start, limit=limit)
        if limitby is not None:
            attributes["limitby"] = limitby

        # Get the rows and return as json
        rows = resource._load(*fields, **attributes)

        response = current.response
        if response:
            response.headers["Content-Type"] = "application/json"

        return rows.json()

# End =========================================================================
