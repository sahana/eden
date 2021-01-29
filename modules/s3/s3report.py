# -*- coding: utf-8 -*-

""" S3 Pivot Table Reports Method

    @copyright: 2011-2021 (c) Sahana Software Foundation
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

__all__ = ("S3Report",
           "S3PivotTable",
           "S3ReportRepresent",
           )

import datetime
import json
import os
import re
import sys

from itertools import product

from gluon import current
from gluon.contenttype import contenttype
from gluon.html import BUTTON, DIV, FIELDSET, FORM, INPUT, LABEL, LEGEND, TAG, XML
from gluon.languages import regex_translate
from gluon.sqlhtml import OptionsWidget
from gluon.storage import Storage
from gluon.validators import IS_IN_SET, IS_EMPTY_OR

from s3compat import INTEGER_TYPES, basestring, xrange
from .s3query import FS
from .s3rest import S3Method
from .s3utils import s3_flatlist, s3_has_foreign_key, s3_str, S3MarkupStripper, s3_represent_value
from .s3xml import S3XMLFormat
from .s3validators import IS_NUMBER, JSONERRORS

# Compact JSON encoding
DEFAULT = lambda: None
SEPARATORS = (",", ":")

LAYER = re.compile(r"([a-zA-Z]+)\((.*)\)\Z")
FACT = re.compile(r"([a-zA-Z]+)\(([a-zA-Z0-9_.$:\,~]+)\),*(.*)\Z")
SELECTOR = re.compile(r"^[a-zA-Z0-9_.$:\~]+\Z")

# =============================================================================
class S3Report(S3Method):
    """ RESTful method for pivot table reports """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Page-render entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        if r.http == "GET":
            if r.representation == "geojson":
                output = self.geojson(r, **attr)
            else:
                output = self.report(r, **attr)
        elif r.http == "POST":
            if r.representation == "json":
                # NB can additionally check for ?explore=1 to
                # distinguish from other POSTs (if necessary)
                output = self.explore(r, **attr)
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)
        return output

    # -------------------------------------------------------------------------
    def report(self, r, **attr):
        """
            Pivot table report page

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        output = {}

        resource = self.resource
        get_config = resource.get_config

        show_filter_form = False
        if r.representation in ("html", "iframe"):
            filter_widgets = get_config("filter_widgets", None)
            if filter_widgets and not self.hide_filter:
                # Apply filter defaults (before rendering the data!)
                from .s3filter import S3FilterForm
                show_filter_form = True
                S3FilterForm.apply_filter_defaults(r, resource)

        widget_id = "pivottable"

        # @todo: make configurable:
        maxrows = 20
        maxcols = 20

        # Extract the relevant GET vars
        report_vars = ("rows", "cols", "fact", "totals")
        get_vars = {k: v for k, v in r.get_vars.items() if k in report_vars}

        # Fall back to report options defaults
        report_options = get_config("report_options", {})
        defaults = report_options.get("defaults", {})

        if not any (k in get_vars for k in ("rows", "cols", "fact")):
            get_vars = defaults
        get_vars["chart"] = r.get_vars.get("chart",
                              defaults.get("chart", None))
        get_vars["table"] = r.get_vars.get("table",
                              defaults.get("table", None))

        # Generate the pivot table
        if get_vars:

            rows = get_vars.get("rows", None)
            if type(rows) is list:
                rows = rows[-1]
            cols = get_vars.get("cols", None)
            if type(cols) is list:
                cols = cols[-1]

            layer = get_vars.get("fact", "id")
            try:
                facts = S3PivotTableFact.parse(layer)
            except SyntaxError:
                current.log.error(sys.exc_info()[1])
                facts = None
            if not facts or not any([rows, cols]):
                pivottable = None
            else:
                prefix = resource.prefix_selector
                get_vars["rows"] = prefix(rows) if rows else None
                get_vars["cols"] = prefix(cols) if cols else None
                get_vars["fact"] = ",".join("%s(%s)" % (fact.method, fact.selector) for fact in facts)

                pivottable = S3PivotTable(resource, rows, cols, facts,
                                          precision = report_options.get("precision"),
                                          )
        else:
            pivottable = None

        representation = r.representation
        if representation in ("html", "iframe", "json"):

            # Generate JSON-serializable dict
            if pivottable is not None:
                pivotdata = pivottable.json(maxrows=maxrows, maxcols=maxcols)
            else:
                pivotdata = None

        if r.representation in ("html", "iframe"):

            tablename = resource.tablename

            # Filter widgets
            if show_filter_form:
                advanced = False
                for widget in filter_widgets:
                    if not widget:
                        continue
                    if "hidden" in widget.opts and widget.opts.hidden:
                        advanced = resource.get_config("report_advanced", True)
                        break

                filter_formstyle = get_config("filter_formstyle", None)
                filter_form = S3FilterForm(filter_widgets,
                                           formstyle = filter_formstyle,
                                           advanced = advanced,
                                           submit = False,
                                           _class = "filter-form",
                                           _id = "%s-filter-form" % widget_id,
                                           )
                fresource = current.s3db.resource(tablename)
                alias = resource.alias if r.component else None
                filter_widgets = filter_form.fields(fresource,
                                                    r.get_vars,
                                                    alias = alias,
                                                    )
            else:
                # Render as empty string to avoid the exception in the view
                filter_widgets = None

            # Generate the report form
            ajax_vars = Storage(r.get_vars)
            ajax_vars.update(get_vars)
            filter_url = r.url(method = "",
                               representation = "",
                               vars = ajax_vars.fromkeys((k for k in ajax_vars
                                                          if k not in report_vars)))
            ajaxurl = attr.get("ajaxurl", r.url(method = "report",
                                                representation = "json",
                                                vars = ajax_vars,
                                                ))

            output = S3ReportForm(resource).html(pivotdata,
                                                 get_vars = get_vars,
                                                 filter_widgets = filter_widgets,
                                                 ajaxurl = ajaxurl,
                                                 filter_url = filter_url,
                                                 widget_id = widget_id,
                                                 )

            output["title"] = self.crud_string(tablename, "title_report")
            output["report_type"] = "pivottable"

            # Detect and store theme-specific inner layout
            self._view(r, "pivottable.html")

            # View
            current.response.view = self._view(r, "report.html")

        elif r.representation == "json":

            output = json.dumps(pivotdata, separators=SEPARATORS)

        elif r.representation == "xls":

            if pivottable:

                # Report title
                title = self.crud_string(r.tablename, "title_report")
                if title is None:
                    title = current.T("Report")

                # TODO: include current date?
                filename = "%s_%s.xls" % (r.env.server_name,
                                          s3_str(title).replace(" ", "_"),
                                          )
                disposition = "attachment; filename=\"%s\"" % filename

                # Response headers
                response = current.response
                response.headers["Content-Type"] = contenttype(".xls")
                response.headers["Content-disposition"] = disposition

                # Convert pivot table to XLS
                stream = pivottable.xls(title)
                #stream.seek(0) # already done in encoder
                output = stream.read()

            else:
                r.error(400, "No report parameters specified")

        else:
            r.error(415, current.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def geojson(self, r, **attr):
        """
            Render the pivot table data as a dict ready to be exported as
            GeoJSON for display on a Map.

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        resource = self.resource
        response = current.response
        s3 = response.s3

        # Set response headers
        response.headers["Content-Type"] = s3.content_type.get("geojson",
                                                               "application/json")
        if not resource.count():
            # No Data
            return json.dumps({})

        # Extract the relevant GET vars
        get_vars = r.get_vars
        layer_id = r.get_vars.get("layer", None)
        level = get_vars.get("level", "L0")

        # Fall back to report options defaults
        get_config = resource.get_config
        report_options = get_config("report_options", {})
        defaults = report_options.get("defaults", {})

        # The rows dimension
        context = get_config("context")
        if context and "location" in context:
            # @ToDo: We can add sanity-checking using resource.parse_bbox_query() as a guide if-desired
            rows = "(location)$%s" % level
        else:
            # Fallback to location_id
            rows = "location_id$%s" % level
            # Fallback we can add if-required
            #rows = "site_id$location_id$%s" % level

        # Filter out null values
        resource.add_filter(FS(rows) != None)

        # Set XSLT stylesheet
        stylesheet = os.path.join(r.folder, r.XSLT_PATH, "geojson", "export.xsl")

        # Do we have any data at this level of aggregation?
        fallback_to_points = True # @ToDo: deployment_setting?
        output = None
        if fallback_to_points:
            if resource.count() == 0:
                # Show Points
                resource.clear_query()
                # Apply URL filters (especially BBOX)
                resource.build_query(filter=s3.filter, vars=get_vars)

                # Extract the Location Data
                xmlformat = S3XMLFormat(stylesheet)
                include, exclude = xmlformat.get_fields(resource.tablename)
                resource.load(fields=include,
                              skip=exclude,
                              start=0,
                              limit=None,
                              orderby=None,
                              virtual=False,
                              cacheable=True)
                gis = current.gis
                attr_fields = []
                style = gis.get_style(layer_id=layer_id,
                                      aggregate=False)
                popup_format = style.popup_format
                if popup_format:
                    if "T(" in popup_format:
                        # i18n
                        T = current.T
                        items = regex_translate.findall(popup_format)
                        for item in items:
                            titem = str(T(item[1:-1]))
                            popup_format = popup_format.replace("T(%s)" % item,
                                                                titem)
                        style.popup_format = popup_format
                    # Extract the attr_fields
                    parts = popup_format.split("{")
                    # Skip the first part
                    parts = parts[1:]
                    for part in parts:
                        attribute = part.split("}")[0]
                        attr_fields.append(attribute)
                    attr_fields = ",".join(attr_fields)

                location_data = gis.get_location_data(resource,
                                                      attr_fields=attr_fields)

                # Export as GeoJSON
                current.xml.show_ids = True
                output = resource.export_xml(fields=include,
                                             mcomponents=None,
                                             references=[],
                                             stylesheet=stylesheet,
                                             as_json=True,
                                             location_data=location_data,
                                             map_data=dict(style=style),
                                             )
                # Transformation error?
                if not output:
                    r.error(400, "XSLT Transformation Error: %s " % current.xml.error)

        else:
            while resource.count() == 0:
                # Try a lower level of aggregation
                level = int(level[1:])
                if level == 0:
                    # Nothing we can display
                    return json.dumps({})
                resource.clear_query()
                # Apply URL filters (especially BBOX)
                resource.build_query(filter=s3.filter, vars=get_vars)
                level = "L%s" % (level - 1)
                if context and "location" in context:
                    # @ToDo: We can add sanity-checking using resource.parse_bbox_query() as a guide if-desired
                    rows = "(location)$%s" % level
                else:
                    # Fallback to location_id
                    rows = "location_id$%s" % level
                    # Fallback we can add if-required
                    #rows = "site_id$location_id$%s" % level
                resource.add_filter(FS(rows) != None)

        if not output:
            # Build the Pivot Table
            cols = None
            layer = get_vars.get("fact", defaults.get("fact", "count(id)"))
            facts = S3PivotTableFact.parse(layer)[:1]
            pivottable = S3PivotTable(resource, rows, cols, facts,
                                      precision = report_options.get("precision"),
                                      )

            # Extract the Location Data
            #attr_fields = []
            style = current.gis.get_style(layer_id=layer_id,
                                          aggregate=True)
            popup_format = style.popup_format
            if popup_format:
                if"T(" in popup_format:
                    # i18n
                    T = current.T
                    items = regex_translate.findall(popup_format)
                    for item in items:
                        titem = str(T(item[1:-1]))
                        popup_format = popup_format.replace("T(%s)" % item,
                                                            titem)
                    style.popup_format = popup_format
                    # Extract the attr_fields
                    # No need as defaulted inside S3PivotTable.geojson()
                    #parts = popup_format.split("{")
                    ## Skip the first part
                    #parts = parts[1:]
                    #for part in parts:
                    #    attribute = part.split("}")[0]
                    #    attr_fields.append(attribute)
                    #attr_fields = ",".join(attr_fields)

            ids, location_data = pivottable.geojson(fact=facts[0], level=level)

            # Export as GeoJSON
            current.xml.show_ids = True
            gresource = current.s3db.resource("gis_location", id=ids)
            output = gresource.export_xml(fields=[],
                                          mcomponents=None,
                                          references=[],
                                          stylesheet=stylesheet,
                                          as_json=True,
                                          location_data=location_data,
                                          # Tell the client that we are
                                          # displaying aggregated data and
                                          # the level it is aggregated at
                                          map_data=dict(level=int(level[1:]),
                                                        style=style),
                                          )
            # Transformation error?
            if not output:
                r.error(400, "XSLT Transformation Error: %s " % current.xml.error)

        return output

    # -------------------------------------------------------------------------
    def widget(self, r, method=None, widget_id=None, visible=True, **attr):
        """
            Pivot table report widget

            @param r: the S3Request
            @param method: the widget method
            @param widget_id: the widget ID
            @param visible: whether the widget is initially visible
            @param attr: controller attributes
        """

        output = {}

        resource = self.resource
        get_config = resource.get_config

        # @todo: make configurable:
        maxrows = 20
        maxcols = 20

        # Extract the relevant GET vars
        report_vars = ("rows", "cols", "fact", "totals")
        get_vars = {k: v for k, v in r.get_vars.items() if k in report_vars}

        # Fall back to report options defaults
        report_options = get_config("report_options", {})
        defaults = report_options.get("defaults", {})

        if not any (k in get_vars for k in ("rows", "cols", "fact")):
            get_vars = defaults
        get_vars["chart"] = r.get_vars.get("chart",
                              defaults.get("chart", None))
        get_vars["table"] = r.get_vars.get("table",
                              defaults.get("table", None))

        # Generate the pivot table
        if get_vars:

            rows = get_vars.get("rows", None)
            cols = get_vars.get("cols", None)

            layer = get_vars.get("fact", "id")
            try:
                facts = S3PivotTableFact.parse(layer)
            except SyntaxError:
                current.log.error(sys.exc_info()[1])
                facts = None
            if not facts or not any([rows, cols]):
                pivottable = None
            else:
                prefix = resource.prefix_selector
                get_vars["rows"] = prefix(rows) if rows else None
                get_vars["cols"] = prefix(cols) if cols else None
                get_vars["fact"] = ",".join("%s(%s)" % (fact.method, fact.selector) for fact in facts)

                if visible:
                    pivottable = S3PivotTable(resource, rows, cols, facts,
                                              precision = report_options.get("precision"),
                                              )
                else:
                    pivottable = None
        else:
            pivottable = None

        # Render as JSON-serializable dict
        if pivottable is not None:
            pivotdata = pivottable.json(maxrows=maxrows, maxcols=maxcols)
        else:
            pivotdata = None

        if r.representation in ("html", "iframe"):

            # Generate the report form
            ajax_vars = Storage(r.get_vars)
            ajax_vars.update(get_vars)
            filter_form = attr.get("filter_form", None)
            filter_tab = attr.get("filter_tab", None)
            filter_url = r.url(method="",
                               representation="",
                               vars=ajax_vars.fromkeys((k for k in ajax_vars
                                                        if k not in report_vars)),
                               )
            ajaxurl = attr.get("ajaxurl", r.url(method="report",
                                                representation="json",
                                                vars=ajax_vars))
            output = S3ReportForm(resource).html(pivotdata,
                                                 get_vars = get_vars,
                                                 filter_widgets = None,
                                                 ajaxurl = ajaxurl,
                                                 filter_url = filter_url,
                                                 filter_form = filter_form,
                                                 filter_tab = filter_tab,
                                                 widget_id = widget_id)

            # Detect and store theme-specific inner layout
            view = self._view(r, "pivottable.html")

            # Render inner layout (outer page layout is set by S3Summary)
            output["title"] = None
            output = XML(current.response.render(view, output))

        else:
            r.error(415, current.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def explore(self, r, **attr):
        """
            Ajax-lookup of representations for items contributing to the
            aggregate value in a pivot table cell (cell explore)
            - called with a body JSON containing the record IDs to represent,
              and the URL params for the pivot table (rows, cols, fact)

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        # Read+parse body JSON
        s = r.body
        s.seek(0)
        try:
            record_ids = json.load(s)
        except JSONERRORS:
            record_ids = None

        # Must be a list of record IDs
        if not isinstance(record_ids, list):
            r.error(404, current.ERROR.BAD_RECORD)

        # Create filtered resource
        resource = current.s3db.resource(self.tablename, id=record_ids)

        prefix = resource.prefix_selector
        pkey = prefix(resource._id.name)
        pkey_colname = str(resource._id)

        # Parse the facts
        get_vars = r.get_vars
        facts = S3PivotTableFact.parse(get_vars.get("fact"))

        selectors = set()   # all fact selectors other than "id"
        ofacts = []         # all facts other than "count(id)"

        for fact in facts:
            selector = prefix(fact.selector)
            is_pkey = selector == pkey
            if not is_pkey:
                selectors.add(selector)
            if not is_pkey or fact.method != "count":
                ofacts.append(fact)

        # Extract the data
        if len(selectors):
            selectors.add(pkey)
            records = resource.select(selectors,
                                      raw_data = True,
                                      represent = True,
                                      limit = None,
                                      ).rows
        else:
            # All we need is the record IDs, so skip the select and
            # construct some pseudo-rows
            records = []
            for record_id in record_ids:
                record = Storage({pkey_colname: record_id})
                record._row = record
                records.append(record)

        # Get the record representation method and initialize it with the
        # report context (rows, cols, facts)
        represent = resource.get_config("report_represent", S3ReportRepresent)
        if represent:
            rows = get_vars.get("rows")
            cols = get_vars.get("cols")
            represent = represent(resource, rows=rows, cols=cols, facts=facts)

        # Determine what the items list should contain

        rfields = {} # resolved fact selectors

        key = None
        aggregate = True
        if len(ofacts) == 1:

            fact = ofacts[0]

            if fact.method == "count":

                # When counting foreign keys in the master record, then
                # show a list of all unique values of that foreign key
                # rather than the number of unique values per master
                # record (as that would always be 1)

                selector = prefix(fact.selector)
                rfield = resource.resolve_selector(selector)
                field = rfield.field
                if field and s3_has_foreign_key(field):
                    multiple = True
                    if rfield.tname == resource.tablename or \
                       selector[:2] == "~." and "." not in selector[2:]:
                        multiple = False
                    else:
                        # Get the component prefix
                        alias = selector.split("$", 1)[0].split(".", 1)[0]
                        component = resource.components.get(alias)
                        if component:
                            multiple = component.multiple

                    if not multiple:
                        represent = None
                        key = rfield.colname
                        aggregate = False
                rfields[selector] = rfield

        # Get the record representations
        records_repr = represent(record_ids) if represent else None

        # Build the output items (as dict, will be alpha-sorted on client-side)
        output = {}
        UNKNOWN_OPT = current.messages.UNKNOWN_OPT
        for record in records:

            raw = record._row
            record_id = raw[pkey_colname]

            values = []
            for fact in ofacts:

                # Resolve the selector
                selector = prefix(fact.selector)
                rfield = rfields.get(selector)
                if not rfield:
                    rfield = rfields[selector] = resource.resolve_selector(selector)

                # Get the value, sub-aggregate
                if aggregate:
                    value = raw[rfield.colname]
                    if type(value) is list:
                        value = fact.compute(value)
                    else:
                        value = fact.compute([value])
                    if fact.method != "count":
                        field = rfield.field
                        if field and field.represent:
                            value = field.represent(value)
                else:
                    value = record[rfield.colname]

                # Extend values list
                if len(values):
                    values.extend([" / ", value])
                else:
                    values.append(value)

            repr_items = [TAG[""](values)] if values else []

            # Add the record representation
            if records_repr is not None:
                repr_items.insert(0, records_repr.get(record_id, UNKNOWN_OPT))
            if len(repr_items) == 2:
                repr_items.insert(1, ": ")

            # Build output item
            # - using TAG not str.join() to allow representations to contain
            #   XML helpers like A, SPAN or DIV
            repr_str = s3_str(TAG[""](repr_items).xml())
            if key:
                # Include raw field value for client-side de-duplication
                output[record_id] = [repr_str, s3_str(raw[key])]
            else:
                output[record_id] = repr_str

        current.response.headers["Content-Type"] = "application/json"
        return json.dumps(output, separators=SEPARATORS)

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_d3():
        """
            Re-usable helper function to inject D3/NVD3 scripts
            into the current page
        """

        appname = current.request.application
        s3 = current.response.s3

        scripts_append = s3.scripts.append
        if s3.debug:
            if s3.cdn:
                scripts_append("https://cdnjs.cloudflare.com/ajax/libs/d3/3.5.17/d3.js")
                # We use a patched v1.8.5 currently, so can't use the CDN version
                #scripts_append("https://cdnjs.cloudflare.com/ajax/libs/nvd3/1.8.5/nv.d3.js")
            else:
                scripts_append("/%s/static/scripts/d3/d3.js" % appname)
            scripts_append("/%s/static/scripts/d3/nv.d3.js" % appname)
        else:
            if s3.cdn:
                scripts_append("https://cdnjs.cloudflare.com/ajax/libs/d3/3.5.17/d3.min.js")
                # We use a patched v1.8.5 currently, so can't use the CDN version
                #scripts_append("https://cdnjs.cloudflare.com/ajax/libs/nvd3/1.8.5/nv.d3.min.js")
            else:
                scripts_append("/%s/static/scripts/d3/d3.min.js" % appname)
            scripts_append("/%s/static/scripts/d3/nv.d3.min.js" % appname)

# =============================================================================
class S3ReportForm(object):
    """ Helper class to render a report form """

    def __init__(self, resource):

        self.resource = resource
        self.show_totals = True

    # -------------------------------------------------------------------------
    def html(self,
             pivotdata,
             filter_widgets=None,
             get_vars=None,
             ajaxurl=None,
             filter_url=None,
             filter_form=None,
             filter_tab=None,
             widget_id=None):
        """
            Render the form for the report

            @param get_vars: the GET vars if the request (as dict)
            @param widget_id: the HTML element base ID for the widgets
        """

        T = current.T
        appname = current.request.application

        # Report options
        report_options = self.report_options(get_vars = get_vars,
                                             widget_id = widget_id,
                                             )

        # Pivot data
        hidden = {"pivotdata": json.dumps(pivotdata, separators=SEPARATORS)}

        empty = T("No report specified.")
        hide = T("Hide Table")
        show = T("Show Table")

        throbber = "/%s/static/img/indicator.gif" % appname

        # Filter options
        if filter_widgets is not None:
            filter_options = self._fieldset(T("Filter Options"),
                                            filter_widgets,
                                            _id="%s-filters" % widget_id,
                                            _class="filter-form")
        else:
            filter_options = ""

        # Report form submit element
        resource = self.resource
        submit = resource.get_config("report_submit", True)
        if submit:
            _class = "pt-submit"
            if submit is True:
                label = T("Update Report")
            elif isinstance(submit, (list, tuple)):
                label = submit[0]
                _class = "%s %s" % (submit[1], _class)
            else:
                label = submit
            submit = TAG[""](
                        INPUT(_type="button",
                              _value=label,
                              _class=_class))
        else:
            submit = ""

        # Form
        form = FORM(filter_options,
                    report_options,
                    submit,
                    hidden = hidden,
                    _class = "pt-form",
                    _id = "%s-pt-form" % widget_id,
                    )

        # View variables
        output = {"form": form,
                  "throbber": throbber,
                  "hide": hide,
                  "show": show,
                  "empty": empty,
                  "widget_id": widget_id,
                  }

        # Script options
        settings = current.deployment_settings
        opts = {
            #"renderFilter": True,
            #"collapseFilter": False,

            #"renderOptions": True,
            "collapseOptions": settings.get_ui_hide_report_options(),

            "renderTable": True,
            "collapseTable": False,
            "showTotals": self.show_totals,

            "ajaxURL": ajaxurl,

            "renderChart": True,
            "collapseChart": True,
            "defaultChart": None,

            "exploreChart": True,
            "filterURL": filter_url,
            "filterTab": filter_tab,
            "filterForm": filter_form,

            "autoSubmit": settings.get_ui_report_auto_submit(),
            "timeout": settings.get_ui_report_timeout(),

            "thousandSeparator": settings.get_L10n_thousands_separator(),
            "thousandGrouping": settings.get_L10n_thousands_grouping(),
            "textAll": str(T("All")),
            "textRecords": str(T("Records")),
        }
        chart_opt = get_vars["chart"]
        if chart_opt is not None:
            if str(chart_opt).lower() in ("0", "off", "false"):
                opts["renderChart"] = False
            elif ":" in chart_opt:
                opts["collapseChart"] = False
                ctype, caxis = chart_opt.split(":", 1)
                opts["defaultChart"] = {"type": ctype, "axis": caxis}

        table_opt = get_vars["table"]
        if table_opt is not None:
            table_opt = str(table_opt).lower()
            if table_opt in ("0", "off", "false"):
                opts["renderTable"] = False
            elif table_opt == "collapse":
                opts["collapseTable"] = True

        # Scripts
        S3Report.inject_d3()
        s3 = current.response.s3
        scripts = s3.scripts
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.ui.pivottable.js" % appname
            if script not in scripts:
                scripts.append(script)
        else:
            script = "/%s/static/scripts/S3/s3.ui.pivottable.min.js" % appname
            if script not in scripts:
                scripts.append(script)

        # Instantiate widget
        script = '''$('#%(widget_id)s').pivottable(%(opts)s)''' % \
                                        {"widget_id": widget_id,
                                         "opts": json.dumps(opts,
                                                            separators=SEPARATORS,
                                                            ),
                                         }
        s3.jquery_ready.append(script)

        return output

    # -------------------------------------------------------------------------
    def report_options(self, get_vars=None, widget_id="pivottable"):
        """
            Render the widgets for the report options form

            @param get_vars: the GET vars if the request (as dict)
            @param widget_id: the HTML element base ID for the widgets
        """

        T = current.T

        SHOW_TOTALS = T("Show totals")
        REPORT = T("Report of")
        ROWS = T("Grouped by")
        COLS = T("and")

        resource = self.resource
        get_config = resource.get_config
        options = get_config("report_options")

        # Specific formstyle?
        settings = current.deployment_settings
        formstyle = settings.get_ui_report_formstyle()
        # Fall back to inline-variant of current formstyle
        if formstyle is None:
            formstyle = settings.get_ui_inline_formstyle()

        # Helper for labels
        label = lambda s, **attr: LABEL("%s:" % s, **attr)

        formfields = []

        # Layer selector
        layer_id = "%s-fact" % widget_id
        layer_widget = self.layer_options(options=options,
                                          get_vars=get_vars,
                                          widget_id=layer_id)
        formfields.append((layer_id + "-row",
                           label(REPORT, _for=layer_id),
                           layer_widget,
                           "",
                           ))

        # Rows/Columns selectors
        axis_options = self.axis_options
        rows_id = "%s-rows" % widget_id
        cols_id = "%s-cols" % widget_id
        rows_options = axis_options("rows",
                                    options=options,
                                    get_vars=get_vars,
                                    widget_id=rows_id)
        cols_options = axis_options("cols",
                                    options=options,
                                    get_vars=get_vars,
                                    widget_id=cols_id)
        axis_widget = DIV(rows_options,
                          label(COLS, _for=cols_id),
                          cols_options,
                          _class="pt-axis-options",
                          )
        formfields.append(("%s-axis-row" % widget_id,
                           label(ROWS, _for=rows_id),
                           axis_widget,
                           "",
                           ))

        # Show Totals switch
        show_totals = True
        if get_vars and "totals" in get_vars and \
           str(get_vars["totals"]).lower() in ("0", "false", "off"):
            show_totals = False
        self.show_totals = show_totals

        show_totals_id = "%s-totals" % widget_id
        totals_widget = INPUT(_type="checkbox",
                              _id=show_totals_id,
                              _name="totals",
                              _class="pt-totals",
                              value=show_totals
                              )

        formfields.append(("%s-show-totals-row" % widget_id,
                           label(SHOW_TOTALS, _for=show_totals_id),
                           totals_widget,
                           "",
                           ))

        try:
            widgets = formstyle(FIELDSET(), formfields)
        except:
            # Old style (should be avoided)
            widgets = TAG[""]([formstyle(*formfield) for formfield in formfields])

        # Render fieldset
        fieldset = self._fieldset(T("Report Options"),
                                  widgets,
                                  _id="%s-options" % widget_id,
                                  _class="report-options")

        return fieldset

    # -------------------------------------------------------------------------
    def axis_options(self, axis,
                     options=None,
                     get_vars=None,
                     widget_id=None):
        """
            Construct an OptionsWidget for rows or cols axis

            @param axis: "rows" or "cols"
            @param options: the report options
            @param get_vars: the GET vars if the request (as dict)
            @param widget_id: the HTML element ID for the widget
        """

        resource = self.resource
        prefix = resource.prefix_selector

        # Get all selectors
        if options and axis in options:
            fields = options[axis]
        else:
            fields = resource.get_config("list_fields")
        if not fields:
            fields = [f.name for f in resource.readable_fields()]

        # Resolve the selectors
        pkey = str(resource._id)
        resolve_selector = resource.resolve_selector
        rfields = []
        append = rfields.append
        for f in fields:
            if not f:
                continue
            elif isinstance(f, (tuple, list)):
                label, selector = f[:2]
            else:
                label, selector = None, f
            rfield = resolve_selector(selector)
            if rfield.colname == pkey:
                continue
            if label:
                rfield.label = label
            append(rfield)

        # Get current value
        if get_vars and axis in get_vars:
            value = get_vars[axis]
        else:
            value = ""
        if value:
            value = prefix(value)

        # Dummy field
        opts = [(prefix(rfield.selector), rfield.label) for rfield in rfields]
        dummy_field = Storage(name=axis, requires=IS_IN_SET(opts))

        # Construct widget
        return OptionsWidget.widget(dummy_field,
                                    value,
                                    _id=widget_id,
                                    _name=axis,
                                    _class="pt-%s" % axis)

    # -------------------------------------------------------------------------
    def layer_options(self,
                      options=None,
                      get_vars=None,
                      widget_id=None):
        """
            Construct an OptionsWidget for the fact layer

            @param options: the report options
            @param get_vars: the GET vars if the request (as dict)
            @param widget_id: the HTML element ID for the widget
        """

        resource = self.resource

        all_methods = S3PivotTableFact.METHODS

        # Get all layers
        layers = None
        methods = None
        if options:
            if "methods" in options:
                methods = options["methods"]
            if "fact" in options:
                layers = options["fact"]
        if not layers:
            layers = resource.get_config("list_fields")
        if not layers:
            layers = [f.name for f in resource.readable_fields()]
        if not methods:
            methods = all_methods

        # Resolve layer options
        T = current.T
        RECORDS = T("Records")
        mname = S3PivotTableFact._get_method_label

        def layer_label(rfield, method):
            """ Helper to construct a layer label """
            mlabel = mname(method)
            flabel = rfield.label if rfield.label != "Id" else RECORDS
            # @ToDo: Exclude this string from admin/translate exports
            return T("%s (%s)") % (flabel, mlabel)

        prefix = resource.prefix_selector

        layer_opts = []
        for option in layers:

            if not option:
                continue
            elif isinstance(option, tuple):
                title, layer = option
            else:
                title, layer = None, option

            try:
                facts = S3PivotTableFact.parse(layer)
            except SyntaxError:
                continue

            if len(facts) > 1:
                # Multi-fact layer
                labels = []
                expressions = []
                for fact in facts:
                    if not title:
                        rfield = resource.resolve_selector(fact.selector)
                        labels.append(fact.get_label(rfield, layers))
                    expressions.append("%s(%s)" % (fact.method, fact.selector))
                if not title:
                    title = " / ".join(labels)
                layer_opts.append((",".join(expressions), title))
                continue
            else:
                fact = facts[0]

            label = fact.label or title
            if fact.default_method:
                s, m = fact.selector, None
            else:
                s, m = fact.selector, fact.method

            # Resolve the selector
            selector = prefix(s)
            rfield = resource.resolve_selector(selector)
            if not rfield.field and not rfield.virtual:
                continue
            if m is None and label:
                rfield.label = label

            if m is None:
                # Only field given -> auto-detect aggregation methods
                is_amount = None
                ftype = rfield.ftype
                if ftype == "integer":
                    is_amount = True
                    requires = rfield.requires
                    if not isinstance(requires, (list, tuple)):
                        requires = [requires]
                    for r in requires:
                        if isinstance(r, IS_IN_SET) or \
                           isinstance(r, IS_EMPTY_OR) and \
                           isinstance(r.other, IS_IN_SET):
                            is_amount = False
                elif ftype == "double":
                    is_amount = True
                elif ftype[:9] == "reference" or \
                     ftype[:5] == "list:" or \
                     ftype in ("id", "string", "text"):
                    is_amount = False
                if ftype in ("datetime", "date", "time"):
                    mopts = ["min", "max", "list"]
                elif is_amount is None:
                    mopts = ["sum", "min", "max", "avg", "count", "list"]
                elif is_amount:
                    mopts = ["sum", "min", "max", "avg"]
                else:
                    mopts = ["count", "list"]
                for method in mopts:
                    if method in methods:
                        label = layer_label(rfield, method)
                        layer_opts.append(("%s(%s)" % (method, selector), label))
            else:
                # Explicit method specified
                if label is None:
                    label = layer_label(rfield, m)
                layer_opts.append(("%s(%s)" % (m, selector), label))

        # Get current value
        if get_vars and "fact" in get_vars:
            layer = get_vars["fact"]
        else:
            layer = ""
        if layer:
            match = LAYER.match(layer)
            if match is None:
                layer = ""
            else:
                selector, method = match.group(2), match.group(1)
                selector = prefix(selector)
                layer = "%s(%s)" % (method, selector)

        if len(layer_opts) == 1:
            # Field is read-only if there is only 1 option
            default = layer_opts[0]
            widget = TAG[""](default[1],
                             INPUT(_type="hidden",
                                   _id=widget_id,
                                   _name=widget_id,
                                   _value=default[0],
                                   _class="pt-fact-single-option"))
        else:
            # Render Selector
            dummy_field = Storage(name="fact",
                                  requires=IS_IN_SET(layer_opts))
            widget = OptionsWidget.widget(dummy_field,
                                          layer,
                                          _id=widget_id,
                                          _name="fact",
                                          _class="pt-fact")

        return widget

    # -------------------------------------------------------------------------
    @staticmethod
    def _fieldset(title, widgets, **attr):
        """
            Helper method to wrap widgets in a FIELDSET container with
            show/hide option

            @param title: the title for the field set
            @param widgets: the widgets
            @param attr: HTML attributes for the field set
        """

        T = current.T
        SHOW = T("Show")
        HIDE = T("Hide")

        return FIELDSET(LEGEND(title,
                               BUTTON(SHOW,
                                      _type="button",
                                      _class="toggle-text",
                                      ),
                               BUTTON(HIDE,
                                      _type="button",
                                      _class="toggle-text",
                                      )
                        ),
                        widgets,
                        **attr)

# =============================================================================
class S3ReportRepresent(object):
    """
        Method to represent the contributing records in a pivot table
        cell (cell explore)

        The cell-explore record list will typically look like:
            - <record representation>: <fact value(s)>
            - ...
        This method controls the first part of each entry.

        For customization, configure for the table as:
                report_represent = <subclass>
    """

    def __init__(self, resource, rows=None, cols=None, facts=None):
        """
            Constructor, initializes the method with the report context
            to allow it to adapt the representation (e.g. it may often
            be desirable to not repeat the report axes in the record list)

            @param resource: the resource of the report
            @param rows: the rows-selector (can be None)
            @param cols: the columns-selector (can be None)
            @param facts: the list of S3PivotTableFacts showing in
                          the pivot table
        """

        self.resource = resource
        self.rows = rows
        self.cols = cols
        self.facts = facts

    # -------------------------------------------------------------------------
    def __call__(self, record_ids):
        """
            Represent record IDs, can be overloaded in subclasses

            @param record_ids: list of record IDs

            @returns: a JSON-serializable dict {recordID: representation},
                      or None to suppress recordID representation in the
                      cell explorer

            NB default behavior is not sensitive for report axes
        """

        # Take a list of record ids
        resource = self.resource
        table = resource.table

        represent = self.repr_method()
        if represent:
            if hasattr(represent, "bulk"):
                # Bulk-represent the record IDs
                output = represent.bulk(record_ids)
            else:
                # Represent the record IDs one by one
                output = {record_id: represent(record_id)
                          for record_id in record_ids}

        elif "name" in table.fields:
            # Extract the names and return dict {id: name}
            query = table._id.belongs(record_ids)
            rows = current.db(query).select(table._id, table.name)

            output = {}
            UNKNOWN_OPT = current.messages.UNKNOWN_OPT
            for row in rows:
                name = row.name
                if not name:
                    name = UNKNOWN_OPT
                output[row[table._id]] = s3_str(row.name)
        else:
            # No reasonable default

            # Render as record IDs (just as useful as nothing):
            #output = {record_id: s3_str(record_id) for record_id in record_ids}

            # Return None to reduces the list to the fact values
            # NB if fact is ID, this will suppress the record list
            #    altogether and show the number of records instead
            output = None

        return output

    # -------------------------------------------------------------------------
    def repr_method(self):
        """
            Return a representation method for the id-field of
            self.resource, can be overloaded in subclasses (simpler
            than implementing __call__ if producing a representation
            method is sufficient)

            @returns: a representation method (preferrably a S3Represent)
        """

        s3db = current.s3db

        resource = self.resource
        pkey = resource._id

        represent = pkey.represent
        if not represent:
            # Standard representation methods can be listed here
            # (if they don't normally depend on the report context)
            if resource.tablename == "pr_person":
                represent = s3db.pr_PersonRepresent()

        return represent

# =============================================================================
class S3PivotTableFact(object):
    """ Class representing a fact layer """

    #: Supported aggregation methods
    METHODS = {"list": "List",
               "count": "Count",
               "min": "Minimum",
               "max": "Maximum",
               "sum": "Total",
               "avg": "Average",
               #"std": "Standard Deviation"
               }


    def __init__(self, method, selector, label=None, default_method=True):
        """
            Constructor

            @param method: the aggregation method
            @param selector: the field selector
            @param label: the fact label
            @param default_method: using default method (used by parser)
        """

        if method is None:
            method = "count"
            default_method = True
        if method not in self.METHODS:
            raise SyntaxError("Unsupported aggregation function: %s" % method)

        self.method = method
        self.selector = selector

        self._layer = None
        self.label = label

        self.resource = None
        self.rfield = None
        self.column = selector

        self.default_method = default_method

    # -------------------------------------------------------------------------
    @property
    def layer(self):
        """
            @todo: docstring
        """

        layer = self._layer
        if not layer:
            layer = self._layer = (self.selector, self.method)
        return layer

    # -------------------------------------------------------------------------
    def compute(self, values, method=DEFAULT, totals=False, precision=None):
        """
            Aggregate a list of values.

            @param values: iterable of values
            @param method: the aggregation method
            @param totals: this call is computing row/column/grand totals
            @param precision: limit the precision of the computation to this
                              number of decimals (@todo: consider a default of 6)
        """

        if values is None:
            return None

        if method is DEFAULT:
            method = self.method
        if totals and method == "list":
            method = "count"

        if method is None or method == "list":
            return values if values else None

        if method == "count":
            # Count all non-null values
            return len([v for v in values if v is not None])
        else:
            # Numeric values required - some virtual fields
            # return '-' for None, so must type-check here:
            values = [v for v in values if isinstance(v, INTEGER_TYPES + (float,))]

            if method == "min":
                try:
                    result = min(values)
                except (TypeError, ValueError):
                    return None

            elif method == "max":
                try:
                    result = max(values)
                except (TypeError, ValueError):
                    return None

            elif method == "sum":
                try:
                    result = sum(values)
                except (TypeError, ValueError):
                    return None

            elif method == "avg":
                try:
                    number = len(values)
                    if number:
                        result = sum(values) / float(number)
                    else:
                        return 0.0
                except (TypeError, ValueError):
                    return None

            #elif method == "std":
                #import numpy
                #if not values:
                    #return 0.0
                #try:
                    #result = numpy.std(values)
                #except (TypeError, ValueError):
                    #return None

            if type(result) is float and precision is not None:
                return round(result, precision)
            else:
                return result

        return None

    # -------------------------------------------------------------------------
    def aggregate_totals(self, totals):
        """
            Aggregate totals for this fact (hyper-aggregation)

            @param totals: iterable of totals
        """

        if self.method in ("list", "count"):
            total = self.compute(totals, method="sum")
        else:
            total = self.compute(totals)
        return total

    # -------------------------------------------------------------------------
    @classmethod
    def parse(cls, fact):
        """
            Parse fact expression

            @param fact: the fact expression
        """

        if isinstance(fact, tuple):
            label, fact = fact
        else:
            label = None

        if isinstance(fact, list):
            facts = []
            for f in fact:
                facts.extend(cls.parse(f))
            if not facts:
                raise SyntaxError("Invalid fact expression: %s" % fact)
            return facts

        # Parse the fact
        other = None
        default_method = False
        if not fact:
            method, parameters = "count", "id"
        else:
            match = FACT.match(fact)
            if match:
                method, parameters, other = match.groups()
                if other:
                    other = cls.parse((label, other) if label else other)
            elif SELECTOR.match(fact):
                method, parameters, other = "count", fact, None
                default_method = True
            else:
                raise SyntaxError("Invalid fact expression: %s" % fact)

        # Validate method
        if method not in cls.METHODS:
            raise SyntaxError("Unsupported aggregation method: %s" % method)

        # Extract parameters
        parameters = parameters.split(",")

        selector = parameters[0]

        facts = [cls(method,
                     selector,
                     label=label,
                     default_method=default_method,
                     ),
                 ]
        if other:
            facts.extend(other)
        return facts

    # -------------------------------------------------------------------------
    @classmethod
    def _get_method_label(cls, code):
        """
            Get a label for a method

            @param code: the method code
            @return: the label (lazyT), or None for unsupported methods
        """

        methods = cls.METHODS

        if code is None:
            code = "list"
        if code in methods:
            return current.T(methods[code])
        else:
            return None

    # -------------------------------------------------------------------------
    @staticmethod
    def _get_field_label(rfield, fact_options=None):
        """
            Get the label for a field

            @param rfield: the S3ResourceField
            @param fact_options: the corresponding subset of the report
                                 options ("fact", "rows" or "cols")
        """

        label = None

        if not rfield:
            return ""
        resource = rfield.resource

        fields = list(fact_options) if fact_options else []

        list_fields = resource.get_config("list_fields")
        if list_fields:
            fields.extend(list_fields)

        prefix = resource.prefix_selector

        # Search through the field labels in report options
        selector = prefix(rfield.selector)
        for f in fields:
            if type(f) is tuple and \
                isinstance(f[1], basestring) and \
                prefix(f[1]) == selector:
                label = f[0]
                break

        if not label and rfield:
            if rfield.ftype == "id":
                label = current.T("Records")
            else:
                label = rfield.label

        return label if label else ""

    # -------------------------------------------------------------------------
    def get_label(self, rfield, fact_options=None):
        """
            Get a label for this fact

            @param rfield: the S3ResourceField
            @param fact_options: the "fact" list of the report options
        """

        label = self.label
        if label:
            # Already set
            return label


        if fact_options:
            # Lookup the label from the fact options
            prefix = rfield.resource.prefix_selector
            for fact_option in fact_options:
                facts = self.parse(fact_option)
                for fact in facts:
                    if fact.method == self.method and \
                       prefix(fact.selector) == prefix(self.selector):
                        label = fact.label
                        break
                if label:
                    break

        if not label:
            # Construct a label from the field label and the method name
            field_label = self._get_field_label(rfield, fact_options)
            method_label = self._get_method_label(self.method)
            label = "%s (%s)" % (field_label, method_label)

        self.label = label
        return label

# =============================================================================
class S3PivotTable(object):
    """ Class representing a pivot table of a resource """

    def __init__(self, resource, rows, cols, facts, strict=True, precision=None):
        """
            Constructor - extracts all unique records, generates a
            pivot table from them with the given dimensions and
            computes the aggregated values for each cell.

            @param resource: the S3Resource
            @param rows: field selector for the rows dimension
            @param cols: field selector for the columns dimension
            @param facts: list of S3PivotTableFacts to compute
            @param strict: filter out dimension values which don't match
                           the resource filter
            @param precision: maximum precision of aggregate computations,
                              a dict {selector:number_of_decimals}
        """

        # Initialize ----------------------------------------------------------
        #
        if not rows and not cols:
            raise SyntaxError("No rows or columns specified for pivot table")

        self.resource = resource

        self.lfields = None
        self.dfields = None
        self.rfields = None

        self.rows = rows
        self.cols = cols
        self.facts = facts

        self.precision = precision if isinstance(precision, dict) else {}

        # API variables -------------------------------------------------------
        #
        self.records = None
        """ All records in the pivot table as a Storage like:
                {
                 <record_id>: <Row>
                }
        """

        self.empty = False
        """ Empty-flag (True if no records could be found) """
        self.numrows = None
        """ The number of rows in the pivot table """
        self.numcols = None
        """ The number of columns in the pivot table """

        self.cell = None
        """ Array of pivot table cells in [rows[columns]]-order, each
            cell is a Storage like:
                {
                 records: <list_of_record_ids>,
                 (<fact>, <method>): <aggregated_value>, ...per layer
                }
        """
        self.row = None
        """ List of row headers, each header is a Storage like:
                {
                 value: <dimension value>,
                 records: <list_of_record_ids>,
                 (<fact>, <method>): <total value>, ...per layer
                }
        """
        self.col = None
        """ List of column headers, each header is a Storage like:
                {
                 value: <dimension value>,
                 records: <list_of_record_ids>,
                 (<fact>, <method>): <total value>, ...per layer
                }
        """
        self.totals = Storage()
        """ The grand total values for each layer, as a Storage like:
                {
                 (<fact>, <method): <total value>, ...per layer
                }
        """

        self.values = {}

        # Get the fields ------------------------------------------------------
        #
        tablename = resource.tablename

        # The "report_fields" table setting defines which additional
        # fields shall be included in the report base layer. This is
        # useful to provide easy access to the record data behind a
        # pivot table cell.
        fields = current.s3db.get_config(tablename, "report_fields", [])

        self._get_fields(fields=fields)
        rows = self.rows
        cols = self.cols

        # Exclude records with empty axis values ------------------------------
        #
        exclude_empty = current.s3db.get_config(tablename, "report_exclude_empty")
        if exclude_empty is True:
            # Exclude empty axis values for all fields
            query = (FS(rows) != None) & (FS(cols) != None)
            resource.add_filter(query)

        elif type(exclude_empty) is tuple:
            # Exclude empty axis values for some fields
            for axis in (cols, rows):
                if axis in exclude_empty:
                    resource.add_filter(FS(axis) != None)

        # Retrieve the records ------------------------------------------------
        #
        data = resource.select(list(self.rfields.keys()), limit=None)
        drows = data["rows"]
        if drows:

            key = str(resource.table._id)
            records = Storage([(i[key], i) for i in drows])

            # Generate the data frame -----------------------------------------
            #
            gfields = self.gfields
            pkey_colname = gfields[self.pkey]
            rows_colname = gfields[rows]
            cols_colname = gfields[cols]

            if strict:
                rfields = self.rfields
                axes = (rfield
                        for rfield in (rfields[rows], rfields[cols])
                        if rfield != None)
                axisfilter = resource.axisfilter(axes)
            else:
                axisfilter = None

            dataframe = []
            extend = dataframe.extend
            expand = self._expand

            for _id in records:
                row = records[_id]
                item = {key: _id}
                if rows_colname:
                    item[rows_colname] = row[rows_colname]
                if cols_colname:
                    item[cols_colname] = row[cols_colname]
                extend(expand(item, axisfilter=axisfilter))

            self.records = records

            # Group the records -----------------------------------------------
            #
            matrix, rnames, cnames = self._pivot(dataframe,
                                                 pkey_colname,
                                                 rows_colname,
                                                 cols_colname)

            # Initialize columns and rows -------------------------------------
            #
            if cols:
                self.col = [Storage({"value": v}) for v in cnames]
                self.numcols = len(self.col)
            else:
                self.col = [Storage({"value": None})]
                self.numcols = 1

            if rows:
                self.row = [Storage({"value": v}) for v in rnames]
                self.numrows = len(self.row)
            else:
                self.row = [Storage({"value": None})]
                self.numrows = 1

            # Add the layers --------------------------------------------------
            #
            add_layer = self._add_layer
            for fact in self.facts:
                add_layer(matrix, fact)

        else:
            # No items to report on -------------------------------------------
            #
            self.empty = True

    # -------------------------------------------------------------------------
    # API methods
    # -------------------------------------------------------------------------
    def __len__(self):
        """ Total number of records in the report """

        items = self.records
        if items is None:
            return 0
        else:
            return len(self.records)

    # -------------------------------------------------------------------------
    def geojson(self,
                fact=None,
                level="L0"):
        """
            Render the pivot table data as a dict ready to be exported as
            GeoJSON for display on a Map.

            Called by S3Report.geojson()

            @param layer: the layer. e.g. ("id", "count")
                          - we only support methods "count" & "sum"
                          - @ToDo: Support density: 'per sqkm' and 'per population'
            @param level: the aggregation level (defaults to Country)
        """

        if fact is None:
            fact = self.facts[0]
        layer = fact.layer

        # The rows dimension
        # @ToDo: We can add sanity-checking using resource.parse_bbox_query() if-desired
        context = self.resource.get_config("context")
        if context and "location" in context:
            rows_dim = "(location)$%s" % level
        else:
            # Fallback to location_id
            rows_dim = "location_id$%s" % level
            # Fallback we can add if-required
            #rows_dim = "site_id$location_id$%s" % level

        # The data
        attributes = {}
        geojsons = {}

        if self.empty:
            location_ids = []
        else:
            numeric = lambda x: isinstance(x, INTEGER_TYPES + (float,))
            row_repr = s3_str

            ids = {}
            irows = self.row
            rows = []

            # Group and sort the rows
            is_numeric = None
            for i in xrange(self.numrows):
                irow = irows[i]
                total = irow[layer]
                if is_numeric is None:
                    is_numeric = numeric(total)
                if not is_numeric:
                    total = len(irow.records)
                header = Storage(value = irow.value,
                                 text = irow.text if "text" in irow
                                                  else row_repr(irow.value))
                rows.append((i, total, header))

            self._sortdim(rows, self.rfields[rows_dim])

            # Aggregate the grouped values
            db = current.db
            gtable = current.s3db.gis_location
            query = (gtable.level == level) & (gtable.deleted == False)
            for _, rtotal, rtitle in rows:
                rval = rtitle.value
                if rval:
                    # @ToDo: Handle duplicate names ;)
                    if rval in ids:
                        _id = ids[rval]
                    else:
                        q = query & (gtable.name == rval)
                        row = db(q).select(gtable.id,
                                           gtable.parent,
                                           limitby=(0, 1)
                                           ).first()
                        try:
                            _id = row.id
                        except AttributeError:
                            continue
                        # Cache
                        ids[rval] = _id

                    attribute = dict(name=s3_str(rval),
                                     value=rtotal)
                    attributes[_id] = attribute

            location_ids = [ids[r] for r in ids]
            query = (gtable.id.belongs(location_ids))
            geojsons = current.gis.get_locations(gtable,
                                                 query,
                                                 join=False,
                                                 geojson=True)

        # Prepare for export via xml.gis_encode() and geojson/export.xsl
        location_data = {}
        geojsons = dict(gis_location = geojsons)
        location_data["geojsons"] = geojsons
        attributes = dict(gis_location = attributes)
        location_data["attributes"] = attributes
        return location_ids, location_data

    # -------------------------------------------------------------------------
    def json(self, maxrows=None, maxcols=None):
        """
            Render the pivot table data as JSON-serializable dict

            @param layer: the layer
            @param maxrows: maximum number of rows (None for all)
            @param maxcols: maximum number of columns (None for all)
            @param least: render the least n rows/columns rather than
                          the top n (with maxrows/maxcols)

            {
                labels: {
                    layer:
                    rows:
                    cols:
                    total:
                },
                method: <aggregation method>,
                cells: [rows[cols]],
                rows: [rows[index, value, label, total]],
                cols: [cols[index, value, label, total]],

                total: <grand total>,
                filter: [rows selector, cols selector]
            }
        """

        rfields = self.rfields
        resource = self.resource

        T = current.T
        OTHER = "__other__"

        rows_dim = self.rows
        cols_dim = self.cols

        # The output data
        orows = []
        rappend = orows.append
        ocols = []
        cappend = ocols.append
        ocells = []

        lookups = {}
        facts = self.facts

        if not self.empty:

            # Representation methods for row and column keys
            row_repr = self._represent_method(rows_dim)
            col_repr = self._represent_method(cols_dim)

            # Label for the "Others" row/columns
            others = s3_str(T("Others"))

            # Get the layers (fact.selector, fact.method),
            # => used as keys to access the pivot data
            layers = [fact.layer for fact in facts]
            least = facts[0].method == "min"

            # Group and sort the rows (grouping = determine "others")
            irows = self.row
            rows = []
            rtail = (None, None)
            for i in xrange(self.numrows):
                irow = irows[i]
                totals = [irow[layer] for layer in layers]
                sort_total = totals[0]
                header = {"value": irow.value,
                          "text": irow.text if "text" in irow
                                            else row_repr(irow.value),
                          }
                rows.append((i, sort_total, totals, header))
            if maxrows is not None:
                rtail = self._tail(rows, maxrows, least=least, facts=facts)
            self._sortdim(rows, rfields[rows_dim])
            if rtail[1] is not None:
                values = [irows[i]["value"] for i in rtail[0]]
                rows.append((OTHER,
                             rtail[1],
                             rtail[2],
                             {"value": values, "text":others},
                             ))

            # Group and sort the cols (grouping = determine "others")
            icols = self.col
            cols = []
            ctail = (None, None)
            for i in xrange(self.numcols):
                icol = icols[i]
                totals = [icol[layer] for layer in layers]
                sort_total = totals[0]
                header = {"value": icol.value,
                          "text": icol.text if "text" in icol
                                            else col_repr(icol.value),
                          }
                cols.append((i, sort_total, totals, header))
            if maxcols is not None:
                ctail = self._tail(cols, maxcols, least=least, facts=facts)
            self._sortdim(cols, rfields[cols_dim])
            if ctail[1] is not None:
                values = [icols[i]["value"] for i in ctail[0]]
                cols.append((OTHER,
                             ctail[1],
                             ctail[2],
                             {"value": values, "text": others},
                             ))

            rothers = rtail[0] or set()
            cothers = ctail[0] or set()

            # Group and sort the cells accordingly
            # @todo: break up into subfunctions
            icell = self.cell
            cells = {}
            for i in xrange(self.numrows):
                irow = icell[i]
                ridx = (i, OTHER) if rothers and i in rothers else (i,)

                for j in xrange(self.numcols):
                    cell = irow[j]
                    cidx = (j, OTHER) if cothers and j in cothers else (j,)

                    cell_records = cell["records"]

                    for layer_index, layer in enumerate(layers):

                        # Get cell items for the layer
                        # => items can be a single numeric value, or a list
                        items = cell[layer]

                        # Get cell value for the layer
                        if isinstance(items, list):
                            value = len(items)
                        else:
                            value = items

                        for ri in ridx:
                            if ri not in cells:
                                orow = cells[ri] = {}
                            else:
                                orow = cells[ri]
                            for ci in cidx:

                                if ci not in orow:
                                    # Create a new output cell
                                    ocell = orow[ci] = {"values": [],
                                                        "items": [],
                                                        "records": [],
                                                        }
                                else:
                                    ocell = orow[ci]

                                if layer_index == 0:
                                    # Extend the list of records
                                    ocell["records"].extend(cell_records)

                                value_array = ocell["values"]
                                items_array = ocell["items"]
                                if len(value_array) <= layer_index:
                                    value_array.append(value)
                                    items_array.append(items)
                                else:
                                    ovalue = value_array[layer_index]
                                    oitems = items_array[layer_index]
                                    if isinstance(ovalue, list):
                                        ovalue.append(value)
                                        oitems.append(items)
                                    else:
                                        value_array[layer_index] = [ovalue, value]
                                        items_array[layer_index] = [oitems, items]

            # Get field representation methods
            represents = self._represents(layers)

            # Aggregate the grouped values
            add_columns = True # do this only once
            for rindex, rtotal, rtotals, rtitle in rows:

                orow = []

                # Row value for filter construction
                rval = rtitle["value"]
                if rindex == OTHER and isinstance(rval, list):
                    rval = ",".join(s3_str(v) for v in rval)
                elif rval is not None:
                    rval = s3_str(rval)

                # The output row summary
                rappend((rindex,
                         rindex in rothers,
                         rtotals,
                         rval,
                         rtitle["text"],
                         ))

                for cindex, ctotal, ctotals, ctitle in cols:

                    # Get the corresponding cell
                    cell = cells[rindex][cindex]

                    value_array = cell["values"]
                    items_array = cell["items"]

                    # Initialize the output cell
                    ocell = {"i": [], "v": []}
                    okeys = None

                    for layer_index, fact in enumerate(facts):

                        selector, method = fact.layer

                        # The value(s) to render in this cell
                        items = items_array[layer_index]

                        # The cell total for this layer (for charts)
                        value = value_array[layer_index]
                        if type(value) is list:
                            # "Others" cell with multiple totals
                            value = fact.aggregate_totals(value)
                        ocell["v"].append(value)

                        rfield = self.rfields[selector]

                        if method == "list":
                            # Build a look-up table with field value representations
                            if selector not in lookups:
                                lookup = lookups[selector] = {}
                            else:
                                lookup = lookups[selector]

                            represent = represents[selector]

                            keys = []
                            for record_id in cell["records"]:

                                record = self.records[record_id]
                                try:
                                    fvalue = record[rfield.colname]
                                except AttributeError:
                                    continue
                                if fvalue is None:
                                    continue
                                if type(fvalue) is not list:
                                    fvalue = [fvalue]

                                for v in fvalue:
                                    if v is None:
                                        continue
                                    if v not in keys:
                                        keys.append(v)
                                    if v not in lookup:
                                        lookup[v] = represent(v)

                            # Sort the keys by their representations
                            keys.sort(key=lambda i: lookup[i])
                            items = [lookup[key] for key in keys if key in lookup]

                        elif method in ("sum", "count") and okeys is None:
                            # Include only cell records in okeys which actually
                            # contribute to the aggregate
                            okeys = []
                            for record_id in cell["records"]:
                                record = self.records[record_id]
                                try:
                                    fvalue = record[rfield.colname]
                                except AttributeError:
                                    continue
                                if method == "sum" and \
                                   isinstance(fvalue, INTEGER_TYPES + (float,)) and fvalue:
                                    okeys.append(record_id)
                                elif method == "count" and \
                                   fvalue is not None:
                                    okeys.append(record_id)
                        else:
                            # Include all cell records in okeys
                            okeys = cell["records"]

                        ocell["i"].append(items)

                    if okeys:
                        ocell["k"] = okeys
                    orow.append(ocell)

                    if add_columns:

                        # Column value for filter construction
                        cval = ctitle["value"]
                        if cindex == OTHER and isinstance(cval, list):
                            cval = ",".join(s3_str(v) for v in cval)
                        elif cval is not None:
                            cval = s3_str(cval)

                        # The output column summary
                        cappend((cindex,
                                 cindex in cothers,
                                 ctotals,
                                 cval,
                                 ctitle["text"],
                                 ))

                add_columns = False
                ocells.append(orow)

        # Lookup labels
        report_options = resource.get_config("report_options", {})
        if report_options:
            fact_options = report_options.get("fact")
        else:
            fact_options = ()

        # @todo: lookup report title before constructing from fact labels

        fact_data = []
        fact_labels = []
        for fact in facts:
            rfield = rfields[fact.selector]
            fact_label = str(fact.get_label(rfield, fact_options))
            fact_data.append((fact.selector, fact.method, fact_label))
            fact_labels.append(fact_label)

        get_label = S3PivotTableFact._get_field_label
        if rows_dim:
            rows_label = str(get_label(rfields[rows_dim], report_options.get("rows")))
        else:
            rows_label = ""

        if cols_dim:
            cols_label = str(get_label(rfields[cols_dim], report_options.get("cols")))
        else:
            cols_label = ""

        labels = {"total": str(T("Total")),
                  "none": str(current.messages["NONE"]),
                  "per": str(T("per")),
                  "breakdown": str(T("Breakdown")),
                  # @todo: use report title:
                  "layer": " / ".join(fact_labels),
                  "rows": rows_label,
                  "cols": cols_label,
                  }

        # Compile the output dict
        output = {"rows": orows,
                  "cols": ocols,
                  "facts": fact_data,
                  "cells": ocells,
                  "total": self._totals(self.totals, [fact]),
                  "nodata": None if not self.empty else str(T("No data available")),
                  "labels": labels,
                  }

        # Add axis selectors for filter-URL construction
        prefix = resource.prefix_selector
        output["filter"] = (prefix(rows_dim) if rows_dim else None,
                            prefix(cols_dim) if cols_dim else None,
                            )

        return output

    # -------------------------------------------------------------------------
    def xls(self, title):
        """
            Convert this pivot table into an XLS file

            @param title: the title of the report

            @returns: the XLS file as stream
        """

        from .s3codec import S3Codec
        exporter = S3Codec.get_codec("xls")

        return exporter.encode_pt(self, title)

    # -------------------------------------------------------------------------
    def _represents(self, layers):
        """
            Get the representation functions per fact field

            @param layers: the list of layers, tuples (selector, method)
        """

        rfields = self.rfields
        represents = {}

        values = self.values

        for selector, method in layers:
            if selector in represents:
                continue

            # Get the field
            rfield = rfields[selector]
            f = rfield.field

            # Utilize bulk-representation for field values
            if method == "list" and \
               f is not None and hasattr(f.represent, "bulk"):
                all_values = values[(selector, method)]
                if all_values:
                    f.represent.bulk(list(s3_flatlist(all_values)))

            # Get the representation method
            has_fk = f is not None and s3_has_foreign_key(f)
            if has_fk:
                represent = lambda v, f=f: s3_str(f.represent(v))
            else:
                m = self._represent_method(selector)
                represent = lambda v, m=m: s3_str(m(v))

            represents[selector] = represent

        return represents

    # -------------------------------------------------------------------------
    @staticmethod
    def _sortdim(items, rfield, index=3):
        """
            Sort a dimension (sorts items in-place)

            @param items: the items as list of tuples
                          (index, sort-total, totals, header)
            @param rfield: the dimension (S3ResourceField)
            @param index: alternative index of the value/text dict
                          within each item
        """

        if not rfield:
            return

        ftype = rfield.ftype

        sortby = "value"
        if ftype in ("integer", "string"):
            # Sort option keys by their representation
            requires = rfield.requires
            if requires:
                if isinstance(requires, (tuple, list)):
                    requires = requires[0]
                if isinstance(requires, IS_EMPTY_OR):
                    requires = requires.other
                if isinstance(requires, IS_IN_SET):
                    sortby = "text"

        elif ftype[:9] == "reference" or ftype[:8] == "list:ref":
            # Sort foreign keys by their representation
            sortby = "text"

        # Replacements for None when sorting
        minnum = -float('inf')
        minval = {"integer": minnum,
                  "float": minnum,
                  "string": "",
                  "date": datetime.date.min,
                  "datetime": datetime.datetime.min,
                  "boolean": 1,
                  }

        # Sorting key function
        def key(item):
            value = item[index][sortby]
            if value is None:
                return "" if sortby == "text" else minval.get(ftype)
            elif ftype == "boolean":
                return -int(value)
            else:
                return value

        items.sort(key=key)

    # -------------------------------------------------------------------------
    @classmethod
    def _tail(cls, items, length=10, least=False, facts=None):
        """
            Find the top/least <length> items (by total)

            @param items: the items as list of tuples
                          (index, sort-total, totals, header)
            @param length: the maximum number of items
            @param least: find least rather than top
            @param facts: the facts to aggregate the tail totals
        """

        try:
            if len(items) > length:
                l = list(items)
                l.sort(lambda x, y: int(y[1]-x[1]))
                if least:
                    l.reverse()
                keys = [item[0] for item in l[length-1:]]
                totals = []
                for i, fact in enumerate(facts):
                    subtotals = [item[2][i] for item in l[length-1:]]
                    totals.append(fact.aggregate_totals(subtotals))
                return (keys, totals[0], totals)
        except (TypeError, ValueError):
            pass
        return (None, None)

    # -------------------------------------------------------------------------
    @staticmethod
    def _totals(values, facts, append=None):
        """
            Get the totals of a row/column/report

            @param values: the values dictionary
            @param facts: the facts
            @param append: callback to collect the totals for JSON data
                           (currently only collects the first layer)
        """

        totals = []
        number_represent = IS_NUMBER.represent
        for fact in facts:
            value = values[fact.layer]
            #if fact.method == "list":
                #value = value and len(value) or 0
            if not len(totals) and append is not None:
                append(value)
            totals.append(s3_str(number_represent(value)))
        totals = " / ".join(totals)
        return totals

    # -------------------------------------------------------------------------
    # Internal methods
    # -------------------------------------------------------------------------
    @staticmethod
    def _pivot(items, pkey_colname, rows_colname, cols_colname):
        """
            2-dimensional pivoting of a list of unique items

            @param items: list of unique items as dicts
            @param pkey_colname: column name of the primary key
            @param rows_colname: column name of the row dimension
            @param cols_colname: column name of the column dimension

            @return: tuple of (cell matrix, row headers, column headers),
                     where cell matrix is a 2-dimensional array [rows[columns]]
                     and row headers and column headers each are lists (in the
                     same order as the cell matrix)
        """

        rvalues = Storage()
        cvalues = Storage()
        cells = Storage()

        # All unique rows values
        rindex = 0
        cindex = 0
        for item in items:

            rvalue = item[rows_colname] if rows_colname else None
            cvalue = item[cols_colname] if cols_colname else None

            if rvalue not in rvalues:
                r = rvalues[rvalue] = rindex
                rindex += 1
            else:
                r = rvalues[rvalue]
            if cvalue not in cvalues:
                c = cvalues[cvalue] = cindex
                cindex += 1
            else:
                c = cvalues[cvalue]

            if (r, c) not in cells:
                cells[(r, c)] = [item[pkey_colname]]
            else:
                cells[(r, c)].append(item[pkey_colname])

        matrix = []
        for r in xrange(len(rvalues)):
            row = []
            for c in xrange(len(cvalues)):
                row.append(cells[(r, c)])
            matrix.append(row)

        rnames = [None] * len(rvalues)
        for k, v in rvalues.items():
            rnames[v] = k

        cnames = [None] * len(cvalues)
        for k, v in cvalues.items():
            cnames[v] = k

        return matrix, rnames, cnames

    # -------------------------------------------------------------------------
    def _add_layer(self, matrix, fact):
        """
            Compute an aggregation layer, updates:

                - self.cell: the aggregated values per cell
                - self.row: the totals per row
                - self.col: the totals per column
                - self.totals: the overall totals per layer

            @param matrix: the cell matrix
            @param fact: the fact field
            @param method: the aggregation method
        """

        rows = self.row
        cols = self.col
        records = self.records
        extract = self._extract
        resource = self.resource

        RECORDS = "records"
        VALUES = "values"

        table = resource.table
        pkey = table._id.name

        layer = fact.layer
        precision = self.precision.get(fact.selector)

        numcols = len(self.col)
        numrows = len(self.row)

        # Initialize cells
        if self.cell is None:
            self.cell = [[Storage()
                          for i in xrange(numcols)]
                         for j in xrange(numrows)]
        cells = self.cell

        all_values = []
        for r in xrange(numrows):

            # Initialize row header
            row = rows[r]
            row[RECORDS] = []
            row[VALUES] = []

            row_records = row[RECORDS]
            row_values = row[VALUES]

            for c in xrange(numcols):

                # Initialize column header
                col = cols[c]
                if RECORDS not in col:
                    col[RECORDS] = []
                col_records = col[RECORDS]
                if VALUES not in col:
                    col[VALUES] = []
                col_values = col[VALUES]

                # Get the records
                cell = cells[r][c]
                if RECORDS in cell and cell[RECORDS] is not None:
                    ids = cell[RECORDS]
                else:
                    data = matrix[r][c]
                    if data:
                        remove = data.remove
                        while None in data:
                            remove(None)
                        ids = data
                    else:
                        ids = []
                    cell[RECORDS] = ids
                row_records.extend(ids)
                col_records.extend(ids)

                # Get the values
                if fact.selector is None:
                    fact.selector = pkey
                    values = ids
                    row_values = row_records
                    col_values = row_records
                    all_values = list(records.keys())
                else:
                    values = []
                    append = values.append
                    for i in ids:
                        value = extract(records[i], fact.selector)
                        if value is None:
                            continue
                        append(value)
                    values = list(s3_flatlist(values))
                    if fact.method in ("list", "count"):
                        values =  list(set(values))
                    row_values.extend(values)
                    col_values.extend(values)
                    all_values.extend(values)

                # Aggregate values
                value = fact.compute(values, precision=precision)
                cell[layer] = value

            # Compute row total
            row[layer] = fact.compute(row_values,
                                      totals = True,
                                      precision = precision,
                                      )
            del row[VALUES]

        # Compute column total
        for c in xrange(numcols):
            col = cols[c]
            col[layer] = fact.compute(col[VALUES],
                                      totals = True,
                                      precision = precision,
                                      )
            del col[VALUES]

        # Compute overall total
        self.totals[layer] = fact.compute(all_values,
                                          totals = True,
                                          precision = precision,
                                          )
        self.values[layer] = all_values

    # -------------------------------------------------------------------------
    def _get_fields(self, fields=None):
        """
            Determine the fields needed to generate the report

            @param fields: fields to include in the report (all fields)
        """

        resource = self.resource
        table = resource.table

        # Lambda to prefix all field selectors
        alias = resource.alias
        def prefix(s):
            if isinstance(s, (tuple, list)):
                return prefix(s[-1])
            if "." not in s.split("$", 1)[0]:
                return "%s.%s" % (alias, s)
            elif s[:2] == "~.":
                return "%s.%s" % (alias, s[2:])
            else:
                return s

        self.pkey = pkey = prefix(table._id.name)
        self.rows = rows = prefix(self.rows) if self.rows else None
        self.cols = cols = prefix(self.cols) if self.cols else None

        if not fields:
            fields = ()

        # dfields (data-fields): fields to generate the layers
        dfields = [prefix(s) for s in fields]
        if rows and rows not in dfields:
            dfields.append(rows)
        if cols and cols not in dfields:
            dfields.append(cols)
        if pkey not in dfields:
            dfields.append(pkey)

        # Normalize fact selectors
        for fact in self.facts:
            fact.selector = selector = prefix(fact.selector)
            if selector not in dfields:
                dfields.append(selector)
        self.dfields = dfields

        # Normalize precision selectors
        precision = {}
        for selector, decimals in self.precision.items():
            precision[prefix(selector)] = decimals
        self.precision = precision

        # rfields (resource-fields): dfields resolved into a ResourceFields map
        rfields = resource.resolve_selectors(dfields)[0]
        rfields = Storage([(f.selector.replace("~", alias), f) for f in rfields])
        self.rfields = rfields

        # gfields (grouping-fields): fields to group the records by
        self.gfields = {pkey: rfields[pkey].colname,
                        rows: rfields[rows].colname
                                if rows and rows in rfields else None,
                        cols: rfields[cols].colname
                                if cols and cols in rfields else None,
                        }

    # -------------------------------------------------------------------------
    def _represent_method(self, field):
        """
            Get the representation method for a field in the report

            @param field: the field selector
        """

        rfields = self.rfields
        default = lambda value: None

        if field and field in rfields:

            rfield = rfields[field]
            if rfield.field:
                def repr_method(value):
                    return s3_represent_value(rfield.field,
                                              value,
                                              strip_markup = True,
                                              )
            elif rfield.virtual:

                # If rfield defines a represent, use it
                represent = rfield.represent
                if not represent:
                    represent = s3_str

                # Wrap with markup stripper
                stripper = S3MarkupStripper()
                def repr_method(val):
                    if val is None:
                        return "-"
                    text = represent(val)
                    if "<" in text:
                        stripper.feed(text)
                        return stripper.stripped()
                    else:
                        return text
            else:
                repr_method = default
        else:
            repr_method = default

        return repr_method

    # -------------------------------------------------------------------------
    def _extract(self, row, field):
        """
            Extract a field value from a DAL row

            @param row: the row
            @param field: the fieldname (list_fields syntax)
        """

        rfields = self.rfields
        if field not in rfields:
            raise KeyError("Invalid field name: %s" % field)
        rfield = rfields[field]
        try:
            return rfield.extract(row)
        except AttributeError:
            return None

    # -------------------------------------------------------------------------
    def _expand(self, row, axisfilter=None):
        """
            Expand a data frame row into a list of rows for list:type values

            @param row: the row
            @param field: the field to expand (None for all fields)
            @param axisfilter: dict of filtered field values by column names
        """

        pairs = []
        append = pairs.append
        for colname in self.gfields.values():
            if not colname:
                continue
            value = row[colname]
            if type(value) is list:
                if not value:
                    value = [None]
                if axisfilter and colname in axisfilter:
                    p = [(colname, v) for v in value
                                       if v in axisfilter[colname]]
                    if not p:
                        raise RuntimeError("record does not match query")
                    else:
                        append(p)
                else:
                    append([(colname, v) for v in value])
            else:
                append([(colname, value)])
        result = [dict(i) for i in product(*pairs)]
        return result

# END =========================================================================
