# -*- coding: utf-8 -*-

""" S3 Pivot Table Reports Method

    @copyright: 2011-2014 (c) Sahana Software Foundation
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

import os
import re

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
from gluon.languages import regex_translate
from gluon.sqlhtml import OptionsWidget
from gluon.validators import IS_IN_SET, IS_EMPTY_OR

from s3query import FS
from s3rest import S3Method
from s3xml import S3XMLFormat

layer_pattern = re.compile("([a-zA-Z]+)\((.*)\)\Z")

# Compact JSON encoding
SEPARATORS = (",", ":")

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
                from s3filter import S3FilterForm
                show_filter_form = True
                S3FilterForm.apply_filter_defaults(r, resource)

        # Filter
        response = current.response
        s3_filter = response.s3.filter
        if s3_filter is not None:
            resource.add_filter(s3_filter)

        widget_id = "pivottable"

        # @todo: make configurable:
        maxrows = 10
        maxcols = 10

        # Extract the relevant GET vars
        report_vars = ("rows", "cols", "fact", "aggregate", "totals")
        get_vars = dict((k, v) for k, v in r.get_vars.iteritems()
                        if k in report_vars)

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

            if layer is not None:
                m = layer_pattern.match(layer)
                if m is None:
                    # Backward-compatiblity: alternative "aggregate" option
                    selector = layer
                    if get_vars and "aggregate" in get_vars:
                        method = get_vars["aggregate"]
                    else:
                        method = "count"
                else:
                    selector, method = m.group(2), m.group(1)

            if not layer or not any([rows, cols]):
                pivottable = None
            else:
                prefix = resource.prefix_selector
                selector = prefix(selector)
                layer = (selector, method)
                get_vars["rows"] = prefix(rows) if rows else None
                get_vars["cols"] = prefix(cols) if cols else None
                get_vars["fact"] = "%s(%s)" % (method, selector)

                pivottable = resource.pivottable(rows, cols, [layer])
        else:
            pivottable = None

        # Render as JSON-serializable dict
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
                    if "hidden" in widget.opts and widget.opts.hidden:
                        advanced = resource.get_config("report_advanced", True)
                        break

                filter_formstyle = get_config("filter_formstyle", None)
                filter_form = S3FilterForm(filter_widgets,
                                           formstyle=filter_formstyle,
                                           advanced=advanced,
                                           submit=False,
                                           _class="filter-form",
                                           _id="%s-filter-form" % widget_id)
                fresource = current.s3db.resource(tablename)
                alias = resource.alias if r.component else None
                filter_widgets = filter_form.fields(fresource,
                                                    r.get_vars,
                                                    alias=alias)
            else:
                # Render as empty string to avoid the exception in the view
                filter_widgets = None

            # Generate the report form
            ajax_vars = Storage(r.get_vars)
            ajax_vars.update(get_vars)
            filter_url = r.url(method="",
                               representation="",
                               vars=ajax_vars.fromkeys((k for k in ajax_vars
                                                        if k not in report_vars)))
            ajaxurl = attr.get("ajaxurl", r.url(method="report",
                                                representation="json",
                                                vars=ajax_vars))

            output = S3ReportForm(resource).html(pivotdata,
                                                 get_vars = get_vars,
                                                 filter_widgets = filter_widgets,
                                                 ajaxurl = ajaxurl,
                                                 filter_url = filter_url,
                                                 widget_id = widget_id)

            output["title"] = self.crud_string(tablename, "title_report")
            output["report_type"] = "pivottable"

            # Detect and store theme-specific inner layout
            self._view(r, "pivottable.html")

            # View
            response.view = self._view(r, "report.html")

        elif r.representation == "json":

            output = json.dumps(pivotdata, separators=SEPARATORS)

        else:
            r.error(501, current.ERROR.BAD_FORMAT)

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

        # Filter
        s3_filter = s3.filter
        if s3_filter is not None:
            resource.add_filter(s3_filter)

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
                resource.build_query(filter=s3_filter, vars=get_vars)

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
                resource.build_query(filter=s3_filter, vars=get_vars)
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
            layer = get_vars.get("fact",
                                 defaults.get("fact",
                                              "count(id)"))
            m = layer_pattern.match(layer)
            selector, method = m.group(2), m.group(1)
            prefix = resource.prefix_selector
            selector = prefix(selector)
            layer = (selector, method)
            pivottable = resource.pivottable(rows, cols, [layer])

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

            ids, location_data = pivottable.geojson(layer=layer, level=level)

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

        # Filter
        s3_filter = current.response.s3.filter
        if s3_filter is not None:
            resource.add_filter(s3_filter)

        # @todo: make configurable:
        maxrows = 20
        maxcols = 20

        # Extract the relevant GET vars
        report_vars = ("rows", "cols", "fact", "aggregate", "totals")
        get_vars = dict((k, v) for k, v in r.get_vars.iteritems()
                        if k in report_vars)

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

            # Backward-compatiblity: alternative "aggregate" option
            if layer is not None:
                m = layer_pattern.match(layer)
                if m is None:
                    selector = layer
                    if get_vars and "aggregate" in get_vars:
                        method = get_vars["aggregate"]
                    else:
                        method = "count"
                else:
                    selector, method = m.group(2), m.group(1)

            if not layer or not any([rows, cols]):
                pivottable = None
            else:
                prefix = resource.prefix_selector
                selector = prefix(selector)
                layer = (selector, method)
                get_vars["rows"] = prefix(rows) if rows else None
                get_vars["cols"] = prefix(cols) if cols else None
                get_vars["fact"] = "%s(%s)" % (method, selector)

                if visible:
                    pivottable = resource.pivottable(rows, cols, [layer])
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
            r.error(501, current.ERROR.BAD_FORMAT)

        return output

# =============================================================================
class S3ReportForm(object):
    """ Helper class to render a report form """

    def __init__(self, resource):

        self.resource = resource

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
                                             widget_id = widget_id)

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

            "thousandSeparator": settings.get_L10n_thousands_separator(),
            "thousandGrouping": settings.get_L10n_thousands_grouping(),
            "textAll": str(T("All")),
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
        s3 = current.response.s3
        scripts = s3.scripts
        if s3.debug:
            # @todo: support CDN
            script = "/%s/static/scripts/d3/d3.js" % appname
            if script not in scripts:
                scripts.append(script)
            script = "/%s/static/scripts/d3/nv.d3.js" % appname
            if script not in scripts:
                scripts.append(script)
            script = "/%s/static/scripts/S3/s3.ui.pivottable.js" % appname
            if script not in scripts:
                scripts.append(script)
        else:
            script = "/%s/static/scripts/S3/s3.pivotTables.min.js" % appname
            if script not in scripts:
                scripts.append(script)

        script = '''$('#%(widget_id)s').pivottable(%(opts)s)''' % \
                                        dict(widget_id = widget_id,
                                             opts = json.dumps(opts,
                                                               separators=SEPARATORS),
                                             )

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
        FACT = T("Report of")
        ROWS = T("Grouped by")
        COLS = T("and")

        resource = self.resource
        get_config = resource.get_config
        options = get_config("report_options")
        report_formstyle = get_config("report_formstyle", None)

        label = lambda s, **attr: LABEL("%s:" % s, **attr)

        if report_formstyle:
            # @ToDo: Full formstyle support
            selectors = DIV()
        else:
            selectors = TABLE()

        # Layer selector
        layer_id = "%s-fact" % widget_id
        layer, single = self.layer_options(options=options,
                                           get_vars=get_vars,
                                           widget_id=layer_id)
        single_opt = {"_class": "pt-fact-single-option"} if single else {}
        if layer:
            selectors.append(TR(TD(label(FACT, _for=layer_id)),
                                TD(layer),
                                **single_opt
                               )
                             )

        # Rows/Columns selectors
        axis_options = self.axis_options
        rows_id = "%s-rows" % widget_id
        cols_id = "%s-cols" % widget_id
        select_rows = axis_options("rows",
                                   options=options,
                                   get_vars=get_vars,
                                   widget_id=rows_id)
        select_cols = axis_options("cols",
                                   options=options,
                                   get_vars=get_vars,
                                   widget_id=cols_id)

        selectors.append(TR(TD(label(ROWS, _for=rows_id)),
                            TD(select_rows),
                            TD(label(COLS, _for=cols_id)),
                            TD(select_cols)
                           )
                        )

        # Show Totals switch
        show_totals_id = "%s-totals" % widget_id
        show_totals = True
        if get_vars and "totals" in get_vars and \
           str(get_vars["totals"]).lower() in ("0", "false", "off"):
            show_totals = False
        self.show_totals = show_totals

        selectors.append(TR(TD(label(SHOW_TOTALS, _for=show_totals_id)),
                            TD(INPUT(_type="checkbox",
                                     _id=show_totals_id,
                                     _name="totals",
                                     _class="pt-totals",
                                     value=show_totals
                                    )
                              ),
                            _class = "pt-show-totals-option"
                           )
                         )

        # Render field set
        fieldset = self._fieldset(T("Report Options"),
                                  selectors,
                                  _id="%s-options" % widget_id)
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
            if isinstance(f, (tuple, list)):
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

        from s3data import S3PivotTable
        all_methods = S3PivotTable.METHODS

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
        mname = S3PivotTable._get_method_label

        def layer_label(rfield, method):
            """ Helper to construct a layer label """
            mlabel = mname(method)
            flabel = rfield.label if rfield.label != "Id" else RECORDS
            # @ToDo: Exclude this string from admin/translate exports
            return T("%s (%s)") % (flabel, mlabel)

        prefix = resource.prefix_selector

        layer_opts = []
        for layer in layers:

            # Parse option
            if type(layer) is tuple:
                label, s = layer
            else:
                label, s = None, layer
            match = layer_pattern.match(s)
            if match is not None:
                s, m = match.group(2), match.group(1)
            else:
                m = None

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
            match = layer_pattern.match(layer)
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
                                   _value=default[0]))
            single = True
        else:
            # Render Selector
            dummy_field = Storage(name="fact",
                                  requires=IS_IN_SET(layer_opts))
            widget = OptionsWidget.widget(dummy_field,
                                          layer,
                                          _id=widget_id,
                                          _name="fact",
                                          _class="pt-fact")
            single = False

        return widget, single

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

# END =========================================================================
