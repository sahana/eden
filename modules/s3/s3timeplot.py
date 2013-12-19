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

    def apply_method(self, r, **attr):

        resource = self.resource
        table = resource.table

        method = "count"

        pkey = resource._id.name
        fields = [pkey]

        start = end = None
        for fname in ("date", "start_date", "created_on"):
            if fname in table.fields:
                start = fname
                fields.append(start)
                break
        for fname in ("end_date",):
            if fname in table.fields:
                end = fname
                fields.append(end)
                break

        data = resource.select(fields)
        rows = data["rows"]

        items = []
        for row in rows:
            item = [row[pkey]]
            if start:
                item.append(str(row[str(table[start])]))
            else:
                item.append(None)
            if end:
                item.append(str(row[str(table[end])]))
            else:
                item.append(None)
            item.append(None)
            items.append(item)

        widget_id = "timeplot"

        form = FORM(
                    DIV(_class="tp-chart", _style="height: 300px;"),
                    INPUT(_type="hidden",
                          _class="tp-data",
                          _value=json.dumps(items)),
                    _class="tp-form",
                    _id = widget_id
               )

        # jQuery-ready script
        script = """$("#%(widget_id)s").timeplot();""" % {"widget_id": widget_id}

        current.response.s3.jquery_ready.append(script)
        current.response.view = "timeplot.html"
        
        return {"form": form}

# END =========================================================================
