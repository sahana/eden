# -*- coding: utf-8 -*-

""" Resource Export Tools

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>}

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: 2009-2021 (c) Sahana Software Foundation
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

__all__ = ("S3Exporter",)

from gluon import current

from .s3codec import S3Codec

# =============================================================================
class S3Exporter(object):
    """
        Exporter toolkit
    """

    # -------------------------------------------------------------------------
    def csv(self, resource):
        """
            Export resource as CSV

            Args:
                resource: the resource to export

            Note:
                Export does not include components!

            TODO:
                Implement audit
        """

        request = current.request
        response = current.response

        if response:
            servername = request and "%s_" % request.env.server_name or ""
            filename = "%s%s.csv" % (servername, resource.tablename)
            from gluon.contenttype import contenttype
            response.headers["Content-Type"] = contenttype(".csv")
            response.headers["Content-disposition"] = "attachment; filename=%s" % filename

        rows = resource.select(None, as_rows=True)
        return str(rows)

    # -------------------------------------------------------------------------
    def json(self, resource,
             start = None,
             limit = None,
             fields = None,
             orderby = None,
             represent = False,
             tooltip = None,
             ):
        """
            Export a resource as JSON

            Args:
                resource: the resource to export from
                start: index of the first record to export
                limit: maximum number of records to export
                fields: list of field selectors for fields to include in
                        the export (None for all fields)
                orderby: ORDERBY expression
                represent: whether values should be represented
                tooltip: additional tooltip field, either a field selector
                         or an expression "f(k,v)" where f is a function
                         name that can be looked up from s3db, and k,v are
                         field selectors for the row, f will be called with
                         a list of tuples (k,v) for each row and is expected
                         to return a dict {k:tooltip} => used by
                         filterOptionsS3 to extract onhover-tooltips for
                         Ajax-update of options
        """

        if fields is None:
            # Use json_fields setting, or fall back to list_fields if
            # not defined, or to all readable fields if list_fields is
            # not defined either.
            # Always include the ID field regardless whether it is
            # configured or not => required for S3FilterOptions and
            # similar Ajax lookups.
            fields = resource.list_fields("json_fields", id_column=0)

        if orderby is None:
            orderby = resource.get_config("orderby", None)

        tooltip_function = None
        if tooltip:
            if type(tooltip) is list:
                tooltip = tooltip[-1]
            import re
            match = re.match(r"(\w+)\((\w+),(\w+)\)", tooltip)
            if match:
                function_name, kname, vname = match.groups()
                # Try to resolve the function name
                tooltip_function = current.s3db.get(function_name)
                if tooltip_function:
                    if kname not in fields:
                        fields.append(kname)
                    if vname not in fields:
                        fields.append(vname)
            else:
                if tooltip not in fields:
                    fields.append(tooltip)

        # Get the data
        _rows = resource.select(fields,
                                start = start,
                                limit = limit,
                                orderby = orderby,
                                represent = represent,
                                ).rows

        # Simplify to plain fieldnames for fields in this table
        tn = "%s." % resource.tablename
        rows = []
        rappend = rows.append
        for _row in _rows:
            row = {}
            for f in _row:
                v = _row[f]
                if tn in f:
                    f = f.split(tn, 1)[1]
                row[f] = v
            rappend(row)

        if tooltip:
            if tooltip_function:
                # Resolve key and value names against the resource
                try:
                    krfield = resource.resolve_selector(kname)
                    vrfield = resource.resolve_selector(vname)
                except (AttributeError, SyntaxError):
                    import sys
                    current.log.error(sys.exc_info()[1])
                else:
                    # Extract key and value fields from each row and
                    # build options dict for function call
                    options = []
                    items = {}
                    for row in rows:
                        try:
                            k = krfield.extract(row)
                        except KeyError:
                            break
                        try:
                            v = vrfield.extract(row)
                        except KeyError:
                            break
                        items[k] = row
                        options.append((k, v))
                    # Call tooltip rendering function
                    try:
                        tooltips = tooltip_function(options)
                    except:
                        import sys
                        current.log.error(sys.exc_info()[1])
                    else:
                        # Add tooltips as "_tooltip" to the corresponding rows
                        if isinstance(tooltips, dict):
                            from .s3utils import s3_str
                            for k, v in tooltips.items():
                                if k in items:
                                    items[k]["_tooltip"] = s3_str(v)

            else:
                # Resolve the tooltip field name against the resource
                try:
                    tooltip_rfield = resource.resolve_selector(tooltip)
                except (AttributeError, SyntaxError):
                    import sys
                    current.log.error(sys.exc_info()[1])
                else:
                    # Extract the tooltip field from each row
                    # and add it as _tooltip
                    from .s3utils import s3_str
                    for row in rows:
                        try:
                            value = tooltip_rfield.extract(row)
                        except KeyError:
                            break
                        if value:
                            row["_tooltip"] = s3_str(value)

        # Return as JSON
        response = current.response
        if response:
            response.headers["Content-Type"] = "application/json"

        from gluon.serializers import json as jsons
        return jsons(rows)

    # -------------------------------------------------------------------------
    def pdf(self, *args, **kwargs):

        codec = S3Codec.get_codec("pdf")
        return codec.encode(*args, **kwargs)

    # -------------------------------------------------------------------------
    def pdfcard(self, *args, **kwargs):

        codec = S3Codec.get_codec("card")
        return codec.encode(*args, **kwargs)

    # -------------------------------------------------------------------------
    def shp(self, *args, **kwargs):

        codec = S3Codec.get_codec("shp")
        return codec.encode(*args, **kwargs)

    # -------------------------------------------------------------------------
    def svg(self, *args, **kwargs):

        codec = S3Codec.get_codec("svg")
        return codec.encode(*args, **kwargs)

    # -------------------------------------------------------------------------
    def xls(self, *args, **kwargs):

        codec = S3Codec.get_codec("xls")
        return codec.encode(*args, **kwargs)

# End =========================================================================
