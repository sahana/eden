"""
    Data Series CRUD

    - to display observed/measured values along a date/time axis
    - to add a series of observed/measured values for a point in time

    Copyright: 2026 (c) Sahana Software Foundation

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

__all__ = ("DataSeriesCRUD",
           "DataSeriesTable",
           )

import json

from gluon import current, INPUT, DIV, TABLE, FORM, BUTTON

from .crud import BasicCRUD

# =============================================================================
class DataSeriesCRUD(BasicCRUD):
    # TODO docstring

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Page-render entry point for CRUD Controller.

            Args:
                r: the CRUDRequest instance
                attr: controller attributes
        """

        output = {}
        if r.http == "GET":
            output = self.select(r, **attr)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def select(self, r, **attr):
        """
            Render the data series table (HTML method)

            Args:
                r: the CRUDRequest instance
                attr: controller attributes

            Returns:
                dict of values for the view
        """

        output = {}

        widget_id = "dstable"

        # Initial data
        data = self.extract(r)

        # Instantiate Widget
        widget = DataSeriesTable(data=data)
        output["items"] = widget.html(widget_id=widget_id)

        output["form"] = self.create(r, **attr)

        # View
        current.response.view = self._view(r, "dseries.html")

        return output

    # -------------------------------------------------------------------------
    def create(self, r, **attr):
        # TODO docstring

        return DIV(BUTTON('Test',
                          _class='tiny primary button action-btn'
                          ),
                    FORM(_id = 'test'),
                    _class="ds-crud",
                    )

    # -------------------------------------------------------------------------
    def extract(self, r):
        # TODO docstring

        resource = self.resource

        reader = resource.get_config("data_series")

        return reader(resource).results() if reader else {}

# =============================================================================
class DataSeriesTable:
    """ Helper to configure and render the data series table """

    def __init__(self, data=None):
        # TODO docstring

        self.data = data if data else {}

    # -------------------------------------------------------------------------
    def html(self, widget_id):
        # TODO docstring

        widget = DIV(TABLE(_class = "dstable-table",
                           _id = widget_id,
                           ),
                     INPUT(value = json.dumps(self.data),
                           _class = "dstable-data",
                           _id = f"{widget_id}-data",
                           _type = "hidden",
                           ),
                     _class = "dstable-scroll",
                     _id = f"{widget_id}-scroll",
                     )

        # Inject JS
        script_opts = {}
        self.inject_script(widget_id, script_opts)

        return widget

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_script(widget_id, options):
        """
            Inject the necessary JavaScript

            Args:
                widget_id: the container's DOM ID
                options: widget options (JSON-serializable dict)
        """

        s3 = current.response.s3
        scripts = s3.scripts

        appname = current.request.application

        # Inject static script
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.ui.dstable.js" % appname
        else:
            script = "/%s/static/scripts/S3/s3.ui.dstable.min.js" % appname
        if script not in scripts:
            scripts.append(script)

        # Script to instantiate the widget
        script = """$("#%(widget_id)s").dsTable(%(options)s)""" % \
                    {"widget_id": widget_id,
                     "options": json.dumps(options),
                     }
        s3.jquery_ready.append(script)

# END =========================================================================
