# -*- coding: utf-8 -*-

"""
    Resource Export Tools

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>}

    @requires: U{B{I{gluon}} <http://web2py.com>}
    @requires: U{B{I{lxml}} <http://codespeak.net/lxml>}
    @requires: U{B{I{xlwt}} <http://pypi.python.org/pypi/xlwt>}

    @author: Dominic König <dominic[at]aidiq.com>

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
from gluon.contenttype import contenttype

from s3codec import S3Codec

# =============================================================================
class S3Exporter(object):
    """
        Exporter toolkit
    """

    def __init__(self):
        """
            Constructor

            @param manager: the S3ResourceController

            @todo 2.3: error message completion
        """

        T = current.T

        self.ERROR = Storage(
            REPORTLAB_ERROR = T("%(module)s not installed") % dict(module="ReportLab"),
            NO_RECORDS = T("No records in this resource"),
            XLWT_ERROR = T("%(module)s not installed") % dict(module="xlwt"),
        )

        self.xls = S3Codec.get_codec("xls").encode
        self.pdf = S3Codec.get_codec("pdf").encode

    # -------------------------------------------------------------------------
    def csv(self, resource):
        """
            Export resource as CSV

            @param resource: the resource to export

            @note: export does not include components!

            @todo: implement audit
        """

        db = current.db
        request = current.request
        response = current.response
        tablename = resource.tablename

        if response:
            servername = request and "%s_" % request.env.server_name or ""
            filename = "%s%s.csv" % (servername, tablename)
            response.headers["Content-Type"] = contenttype(".csv")
            response.headers["Content-disposition"] = "attachment; filename=%s" % filename

        rows = resource.select()
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

            @param resource: the resource to export
            @param start: index of the first record to export (for slicing)
            @param limit: maximum number of records to export (for slicing)
            @param fields: fields to include in the export (None for all fields)
        """

        response = current.response

        if fields is None:
            fields = [f for f in resource.table if f.readable]

        attributes = dict()

        if orderby is not None:
            attributes.update(orderby=orderby)

        limitby = resource.limitby(start=start, limit=limit)
        if limitby is not None:
            attributes.update(limitby=limitby)

        # Get the rows and return as json
        rows = resource.select(*fields, **attributes)

        if response:
            response.headers["Content-Type"] = "application/json"

        return rows.json()

# End =========================================================================
