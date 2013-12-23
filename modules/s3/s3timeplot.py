# -*- coding: utf-8 -*-

""" S3 TimePlot Reports Method

    @copyright: 2011-2013 (c) Sahana Software Foundation
    @license: MIT

    @requires: U{B{I{Python 2.6}} <http://www.python.org>}

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

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import current
from gluon.storage import Storage
from gluon.html import *

from s3rest import S3Method

# =============================================================================
class S3TimePlot(S3Method):
    """ RESTful method for time plot reports """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Page-render entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        if r.http == "GET":
            output = self.timeplot(r, **attr)
        else:
            r.error(405, current.manager.ERROR.BAD_METHOD)
        return output

    # -------------------------------------------------------------------------
    def timeplot(self, r, **attr):
        """
            Pivot table report page

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """
        
        resource = self.resource
        table = resource.table

        method = "count"

        # Extract the relevant GET vars
        get_vars = dict((k, v) for k, v in r.get_vars.iteritems()
                        if k in ("timestamp",))

        # Fall back to report options defaults
        if not any (k in get_vars for k in ("timestamp",)):
            timeplot_options = resource.get_config("timeplot_options", {})
            get_vars = timeplot_options.get("defaults", {})

        # Parse timestamp option
        timestamp = get_vars.get("timestamp", None)
        if timestamp:
            if "," in timestamp:
                start, end = timestamp.split(",", 1)
            else:
                start, end = timestamp, None
        else:
            start, end = None, None

        # Defaults
        if not start:
            for fname in ("date", "start_date", "created_on"):
                if fname in table.fields:
                    start = fname
                    break
            if not end:
                for fname in ("end_date",):
                    if fname in table.fields:
                        end = fname
                        break
        if not start:
            r.error(405, T("No time stamps found in this resource"))

        # Get the fields
        fields = [resource._id.name]
        start_colname = end_colname = None
        try:
            start_rfield = resource.resolve_selector(start)
        except AttributeError, SyntaxError:
            r.error(405, T("Invalid start selector: %(selector)s" % {"selector": start}))
        else:
            fields.append(start)
            start_colname = start_rfield.colname
        if end:
            try:
                end_rfield = resource.resolve_selector(end)
            except AttributeError, SyntaxError:
                r.error(405, T("Invalid end selector: %(selector)s" % {"selector": end}))
            else:
                fields.append(end)
                end_colname = end_rfield.colname

        data = resource.select(fields)
        rows = data["rows"]

        items = []
        for row in rows:
            item = [row[str(resource._id)]]
            if start_colname:
                item.append(str(row[start_colname]))
            else:
                item.append(None)
            if end_colname:
                item.append(str(row[end_colname]))
            else:
                item.append(None)
            item.append(None)
            items.append(item)
        items = json.dumps(items)

        widget_id = "timeplot"

        if r.representation in ("html", "iframe"):
            
            title = self.crud_string(resource.tablename, "title_report")
            
            output = {"title": title}
            
            form = FORM(DIV(_class="tp-chart", _style="height: 300px;"),
                        INPUT(_type="hidden",
                              _class="tp-data",
                              _value=items),
                        _class="tp-form",
                        _id = widget_id)

            output["form"] = form

            # View
            response = current.response
            response.view = self._view(r, "timeplot.html")

            # Script to attach the timeplot widget
            script = """$("#%(widget_id)s").timeplot();""" % {"widget_id": widget_id}
            response.s3.jquery_ready.append(script)
        
        elif r.representation == "json":

            output = items

        else:
            r.error(501, r.ERROR.BAD_FORMAT)

        return output

# END =========================================================================
