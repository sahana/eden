# -*- coding: utf-8 -*-

""" S3 Pivot Table Reports Method

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

    @status: work in progress
"""

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
from gluon.sqlhtml import OptionsWidget
from gluon.validators import IS_IN_SET
from gluon.languages import lazyT

from s3rest import S3Method

layer_pattern = re.compile("([a-zA-Z]+)\((.*)\)\Z")

# =============================================================================
class S3Report2(S3Method):
    """ RESTful method for pivot table reports """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Pivot table report page

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        if r.http == "GET":
            output = self.report(r, **attr)
        else:
            r.error(405, current.manager.ERROR.BAD_METHOD)
        return output

    # -------------------------------------------------------------------------
    def report(self, r, **attr):

        output = {}
        
        resource = self.resource
        get_config = resource.get_config

        widget_id = "pivottable"

        # Extract the relevant GET vars
        get_vars = dict((k, v) for k, v in r.get_vars.iteritems()
                        if k in ("rows",
                                 "cols",
                                 "fact",
                                 "aggregate",
                                 "totals"))

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
                    
            if not all([rows, cols, layer]):
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

        if r.representation in ("html", "iframe"):

            output["title"] = current.T("Report")

            # Fall back to report options defaults
            if not get_vars:
                report_options = get_config("report_options")
                if report_options and "defaults" in report_options:
                    get_vars = report_options["defaults"]

            # Filter widgets
            hide_filter = attr.get("hide_filter", False)
            filter_widgets = get_config("filter_widgets", None)
            if filter_widgets and not hide_filter:

                from s3filter import S3FilterForm
                filter_formstyle = get_config("filter_formstyle", None)
                filter_form = S3FilterForm(filter_widgets,
                                           formstyle=filter_formstyle,
                                           submit=False,
                                           _class="filter-form",
                                           _id="%s-filter-form" % widget_id)
                fresource = current.s3db.resource(resource.tablename)
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
            ajaxurl = r.url(representation="json", vars=ajax_vars)
            output["form"] = S3ReportForm(resource) \
                                    .html(pivottable,
                                          get_vars = get_vars,
                                          filter_widgets = filter_widgets,
                                          ajaxurl = ajaxurl,
                                          widget_id = widget_id)

            # @todo: if pivottable is None: render a datatable instead

            # View
            current.response.view = self._view(r, "report2.html")

        elif r.representation == "json":

            if pivottable:
                output = json.dumps(pivottable.json())
            else:
                output = "null"
            
        elif r.representation == "aadata":
            r.error(501, r.ERROR.BAD_FORMAT)
            
        else:
            r.error(501, r.ERROR.BAD_FORMAT)
            
        return output

    # -------------------------------------------------------------------------
    def widget(self, r, method=None, widget_id=None, **attr):
        """
            Pivot table report widget
        
            @param method: the widget method
            @param widget_id: the widget ID
            @param r: the S3Request
            @param attr: controller attributes
        """

        r.error(405, current.manager.ERROR.BAD_METHOD)
        
# =============================================================================
class S3ReportForm(object):
    """ Helper class to render a report form """

    def __init__(self, resource):

        self.resource = resource

    # -------------------------------------------------------------------------
    def html(self,
             pivottable,
             filter_widgets=None,
             get_vars=None,
             ajaxurl=None,
             widget_id=None):
        """
            Render the form for the report 

            @param get_vars: the GET vars if the request (as dict)
            @param widget_id: the HTML element base ID for the widgets
        """

        report_options, hidden = self.report_options(get_vars = get_vars,
                                                     widget_id = widget_id)

        if pivottable:
            hidden["pivotdata"] = json.dumps(pivottable.json())
            empty = ""
        else:
            hidden["pivotdata"] = """null"""
            empty = current.T("Please select report options.")
            
        throbber = "/%s/static/img/indicator.gif" % current.request.application


        if filter_widgets is not None:
            filter_options = self._fieldset(current.T("Filter Options"),
                                            filter_widgets,
                                            _id="%s-filters" % widget_id)
        else:
            filter_options = ""

        resource = self.resource
        submit = resource.get_config("report_submit", True)
        if submit:
            _class = "pt-submit"
            if submit is True:
                label = current.T("Update Report")
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

        # @todo: move CSS into static .css
        form = DIV(
                 DIV(
                   FORM(filter_options,
                        report_options,
                        submit,
                        hidden = hidden,
                        _class = "pt-controls"
                   ),
                   _class="form-container"
                 ),
                 DIV(
                    IMG(_src=throbber,
                        _alt=current.T("Processing"),
                        _class="pt-throbber",
                        _style="position: absolute; left: 8; top: 8;"),
                    DIV(_class="pt-table",
                        _style="position: relative; left: 0; top: 0;"),
                    _style="position: relative; left: 0; top: 0;"
                 ),
                 DIV(empty, _class="pt-empty"),
                 _class="pt-container",
                 _id=widget_id
               )

        # Settings
        settings = current.deployment_settings
        collapse = settings.get_ui_hide_report_options()

        # jQuery-ready script
        script = """
$("#%(widget_id)s").pivottable({
  showTotals: %(totals)s,
  collapseForm: %(collapse)s,
  ajaxURL: %(ajaxurl)s
});""" % {
            "widget_id": widget_id,
            "totals": "true" if self.show_totals else "false",
            "collapse": "true" if collapse else "false",
            "ajaxurl": "'%s'" % ajaxurl if ajaxurl else "null",
         }
         
        current.response.s3.jquery_ready.append(script)
               
        return form

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
        options = resource.get_config("report_options")

        label = lambda s, **attr: TD(LABEL("%s:" % s, **attr),
                                     _class="w2p_fl")

        # @todo: use formstyle
        selectors = TABLE()

        # Layer selector
        layer_id = "%s-fact" % widget_id
        layer, hidden = self.layer_options(options=options,
                                           get_vars=get_vars,
                                           widget_id=layer_id)
        single_opt = {"_class": "pt-fact-single-option"} \
                     if hidden else {}
        if layer:
            selectors.append(TR(label(FACT, _for=layer_id),
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

        selectors.append(TR(label(ROWS, _for=rows_id),
                            TD(select_rows),
                            label(COLS, _for=cols_id),
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

        selectors.append(TR(label(SHOW_TOTALS,
                                  _for=show_totals_id),
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

        return fieldset, hidden

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

        # Resolve layers
        prefix = resource.prefix_selector
        opts = []
        for layer in layers:

            # Extract layer option
            if type(layer) is tuple and \
               (isinstance(layer[0], lazyT) or layer[1] not in all_methods):
                opt = [layer]
            else:
                opt = list(layer) \
                      if isinstance(layer, (tuple, list)) else [layer]

            # Get field label and selector
            s = opt[0]
            if isinstance(s, tuple):
                label, selector = s
            else:
                label, selector = None, s
            selector = prefix(selector)

            # Resolve the selector
            rfield = resource.resolve_selector(selector)
            if not rfield.field and not rfield.virtual:
                continue
            if label is not None:
                rfield.label = label

            # Autodetect methods?
            if len(opt) == 1:
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
                opts.extend([(rfield, selector, m)
                             for m in mopts if m in methods])
            else:
                # Explicit method specified
                opt.insert(0, rfield)
                opts.append(opt)

        # Construct default labels
        T = current.T
        RECORDS = T("Records")
        layer_opts = []
        mname = S3PivotTable._get_method_label
        for opt in opts:
            rfield, selector, method = opt[:3]
            if method not in methods:
                continue
            if len(opt) == 4:
                layer_label = opt[3]
            else:
                mlabel = mname(method)
                flabel = rfield.label if rfield.label != "Id" else RECORDS
                layer_label = T("%s (%s)") % (flabel, mlabel)
            layer_opts.append(("%s(%s)" % (method, selector), layer_label))

        # Get current value
        if get_vars and "fact" in get_vars:
            layer = get_vars["fact"]
        else:
            layer = ""
        if layer:
            m = layer_pattern.match(layer)
            if m is None:
                layer = ""
            else:
                selector, method = m.group(2), m.group(1)
                selector = prefix(selector)
                layer = "%s(%s)" % (method, selector)

        # Field is read-only if there is only 1 option
        if len(layer_opts) == 1:
            default = layer_opts[0]
            return default[1], {"fact": default[0]}

        # Dummy field
        dummy_field = Storage(name="fact",
                              requires=IS_IN_SET(layer_opts))

        # Construct widget
        widget = OptionsWidget.widget(dummy_field,
                                      layer,
                                      _id=widget_id,
                                      _name="fact",
                                      _class="pt-fact")
        return widget, {}

    # -------------------------------------------------------------------------
    @staticmethod
    def _fieldset(title, widgets, **attr):

        T = current.T
        SHOW = T("Show")
        HIDE = T("Hide")
        
        return FIELDSET(LEGEND(title,
                               BUTTON(SHOW,
                                      _type="button",
                                      _class="toggle-text",
                                      _style="display:none"),
                               BUTTON(HIDE,
                                      _type="button",
                                      _class="toggle-text")
                        ),
                        widgets,
                        **attr)

# END =========================================================================
