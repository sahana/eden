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
           "DataSeries",
           "DataSeriesTable",
           )

import json

from gluon import current, INPUT, DIV, TABLE, FORM, BUTTON

from .crud import BasicCRUD

# =============================================================================
class DataSeriesCRUD(BasicCRUD):
    """ CRUD for data series """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Page-render entry point for CRUD Controller.

            Args:
                r: the CRUDRequest instance
                attr: controller attributes
        """

        output = {}

        # TODO JSON endpoint for pagination
        # TODO GET-action to read parameter details
        # TODO POST-action to submit new results
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
        """
            Generates a form to enter results for a specific date/time
            slot (typically "now") in a data series.

            Args:
                r: the CRUDRequest
                attr: additional controller arguments

            Returns:
                a DIV containing a hidden form and a button to
                reveal/activate it, to be included in the data
                series view
        """

        return "" # Hide until ready

        #return DIV(BUTTON('Test',
        #                  _class='tiny primary button action-btn'
        #                  ),
        #            FORM(_id = 'test'),
        #            _class="ds-crud",
        #            )

    # -------------------------------------------------------------------------
    # Utility functions
    #
    def extract(self, r):
        """
            Extract the results using the configured model-specific data
            series handler (DataSeries subclass)

            Args:
                r: the CRUDRequest

            Returns:
                a JSON-serializable dict, see DataSeries.results
        """

        resource = self.resource

        reader = resource.get_config("data_series")

        return reader(resource).results() if reader else {}

# =============================================================================
class DataSeries:
    """ Data Series Handler (base class) """

    def __init__(self, resource):
        """
            Args:
                resource: the context CRUDResource
        """

        self.resource = resource

    # -------------------------------------------------------------------------
    def results(self, start=0, limit=None):
        """
            Extracts results from context resource and generates the
            JSON output for the client-side table renderer; to be
            implemented by model-specific subclasses, which are then
            configured as "data_series" parameter for the respective
            context table

            Args:
                start: the start index of the page
                limit: the number of records in the page

            Returns:
                a JSON-serializable dict like:
                {"d": [[id, iso_date, title], ...],                           // dates
                 "g": [[id, title], ...]                                      // groups
                 "s": [[id, group-id, title, full-name, range, unit], ...]    // series
                 "v": {slot-id:                                               // values
                        {series-id: [value, status, reason, out-of-range], ...}
                       },
                 }
        """

        raise NotImplementedError

# =============================================================================
class DataSeriesTable:
    """ Helper to configure and render the data series table """

    def __init__(self, data=None):
        """
            Args:
                data: the results as JSON-serializable dict, see
                      DataSeries.results for data format details
        """

        self.data = data if data else {}

    # -------------------------------------------------------------------------
    def html(self, widget_id):
        """
            Produces a TABLE of data series, with one series per row
            along a date/time axis (=columns)

            Args:
                widget_id: the DOM node ID to use for the TABLE

            Returns:
                a double-scrollable DIV containing the (empty) table as
                well as a hidden input with the initial JSON data; also
                injects the necessary JS to render the data and interact
                with the table
        """

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
