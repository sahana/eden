# -*- coding: utf-8 -*-

""" S3 Reporting Framework

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

__all__ = ["S3Report", "S3ContingencyTable"]

import datetime

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import current
from gluon.html import *
from gluon.sqlhtml import OptionsWidget
from gluon.storage import Storage
from gluon.languages import lazyT
from gluon.validators import IS_EMPTY_OR

from s3resource import S3TypeConverter
from s3crud import S3CRUD
from s3search import S3Search
from s3utils import s3_truncate, s3_has_foreign_key, s3_unicode
from s3validators import IS_INT_AMOUNT, IS_FLOAT_AMOUNT, IS_NUMBER, IS_IN_SET


# =============================================================================
class S3Report(S3CRUD):
    """ RESTful method for pivot table reports """

    T = current.T
    METHODS = {
        "list": T("List"),
        "count": T("Count"),
        "min": T("Minimum"),
        "max": T("Maximum"),
        "sum": T("Total"),
        "avg": T("Average"),
        #"std": T("Standard Deviation")
    }
    SHOW = T("Show")
    HIDE = T("Hide")

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            API entry point

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        if r.http in ("GET", "POST"):
            output = self.report(r, **attr)
        else:
            r.error(405, current.manager.ERROR.BAD_METHOD)
        return output

    # -------------------------------------------------------------------------
    def report(self, r, **attr):
        """
            Generate a pivot table report

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        T = current.T
        response = current.response
        session = current.session
        s3 = session.s3

        tablename = self.tablename

        # Get the options
        # Figure out which set of options to use:
        # POST > GET > session > table defaults > list view
        if r.http == "POST":
            # Form has been submitted
            form_values = r.post_vars

            # The totals option is used to turn OFF the totals cols/rows but
            # post vars only contain checkboxes that are enabled and checked,
            # hence add it here if not present
            if "totals" not in r.post_vars:
                form_values["totals"] = "off"

        else:
            # Form has been requested

            # Clear session options?
            clear_opts = False
            if "clear_opts" in r.get_vars:
                clear_opts = True
                del r.get_vars["clear_opts"]
            if "clear_opts" in r.vars:
                del r.vars["clear_opts"]

            # Lambda to get the last value in a list
            last = lambda opt: opt[-1] if type(opt) is list else opt


            # Do we have URL options?
            url_options = Storage([(k, last(v))
                                   for k, v in r.get_vars.iteritems() if v and k not in ("table", "chart")])
            if url_options:
                form_values = url_options
                if not form_values._formname:
                    form_values._formname = "report"

            else:
                # Do we have session options?
                session_options = s3.report_options
                if session_options and tablename in session_options:
                    if clear_opts:
                        # Clear all filter options (but not report options)
                        opts = Storage([(o, v)
                                    for o, v in session_options[tablename].items()
                                    if o in ("rows", "cols", "fact", "aggregate", "show_totals")])
                        session_options[tablename] = opts
                        session_options = opts
                    else:
                        session_options = session_options[tablename]
                else:
                    session_options = Storage()
                if session_options:
                    form_values = session_options

                # otherwise, fallback to report_options (table config)
                else:
                    report_options = self._config("report_options", Storage())
                    if report_options and "defaults" in report_options:
                        default_options = report_options["defaults"]
                    else:
                        default_options = Storage()
                    if default_options:
                        form_values = default_options
                        if not form_values._formname:
                            form_values._formname = "report"
                    else:
                        form_values = Storage()

        # Remove the existing session filter if this is a new
        if r.http == "GET" and r.representation != "aadata":
            if "filter" in s3:
                del s3["filter"]

        # Generate the report and resource filter form
        show_form = attr.get("interactive_report", True)
        if show_form:

            # Build the form and prepopulate with values we've got
            opts = Storage(r.get_vars)
            opts["clear_opts"] = "1"
            clear_opts = A(T("Reset all filters"),
                           _href=r.url(vars=opts),
                           _class="action-lnk")
            form = self._create_form(form_values, clear_opts=clear_opts)

            # Validate the form; only compare to the session if
            # POSTing to prevent cross-site scripting.
            if r.http == "POST" and \
               form.accepts(form_values,
                            session,
                            formname="report",
                            onvalidation=self.report_options_validation):

                # Store options in session
                if "report_options" not in s3:
                    s3.report_options = Storage()

                s3.report_options[tablename] = Storage([(k, v)
                                        for k, v in form_values.iteritems()
                                            if v and not k[0] == "_"])

            elif not form.errors:
                form.vars = form_values

            # Use the form values to generate the filter
            dq, vq, errors = self._process_filter_options(form)
            if not errors:
                self.resource.add_filter(dq)
                self.resource.add_filter(vq)
                query = dq
                if vq is not None:
                    if query is not None:
                        query &= vq
                    else:
                        query = vq
            else:
                query = None

        else:
            query = None
            form = None

        # Process the form values
        # Get rows, cols, fact and aggregate
        rows = form_values.get("rows", None)
        cols = form_values.get("cols", None)
        fact = form_values.get("fact", None)
        aggregate = form_values.get("aggregate", "list")
        if not aggregate:
            aggregate = "list"

        # Fall back to list view if no dimensions specified
        if not rows and not cols:
            self.method = "list"

        # Show totals?
        show_totals = form_values.get("totals", True)
        if show_totals and str(show_totals).lower() in ("false", "off"):
            show_totals = False
        else:
            show_totals = True

        # Get the layers
        layers = []
        if not fact:
            table = self.table
            if "name" in table:
                fact = "name"
            else:
                fact = table._id.name
        if fact:
            if not isinstance(fact, list):
                fact = [fact]
            for f in fact:
                f = f.split(",")
                for l in f:
                    if ":" in l:
                        method, layer = l.split(":", 1)
                    else:
                        method = aggregate
                        layer = l
                    layers.append((layer, method))

        # Generate the report
        resource = self.resource
        representation = r.representation

        if not form.errors and self.method == "report":

            # Get a pivot table from the resource
            try:
                report = resource.pivottable(rows, cols, layers)
            except ImportError:
                msg = T("S3Pivottable unresolved dependencies")
                import sys
                e = sys.exc_info()[1]
                if hasattr(e, "message"):
                    e = e.message
                else:
                    e = str(e)
                msg = "%s: %s" % (msg, e)
                r.error(400, msg, next=r.url(vars={"clear":1}))
            except:
                raise
                msg = T("Could not generate report")
                import sys
                e = sys.exc_info()[1]
                if hasattr(e, "message"):
                    e = e.message
                else:
                    e = str(e)
                msg = "%s: %s" % (msg, e)
                r.error(400, msg, next=r.url(vars={"clear":1}))

            # Convert the pivot table into a S3ContingencyTable
            if representation in ("html", "iframe"):
                report_data = None
                if not report.empty:
                    items = S3ContingencyTable(report,
                                               show_totals=show_totals,
                                               filter_query=query,
                                               url=r.url(method=""),
                                               _id="list",
                                               _class="dataTable display report")
                    report_data = items.report_data
                else:
                    items = self.crud_string(tablename, "msg_no_match")

                report_options = self._config("report_options", Storage())

                # Display options

                # Show or hide the pivot table by default?
                # either report_options.table=True|False or URL ?table=1|0
                get_vars = r.get_vars
                hide, show = {}, {"_style": "display:none;"}
                if "table" in get_vars and r.get_vars["table"] != "1" or \
                   report_options and report_options.get("table", False):
                    hide, show = show, hide

                # Which chart to show by default?
                # either report_options.chart="type:dim" or URL ?chart=type:dim
                # type=piechart|barchart|breakdown|hide (defaults to hide)
                # dim=rows|cols (defaults to rows)
                chart_opt = get_vars.get("chart", report_options.get("chart", None))
                chart_dim = "rows"
                if chart_opt:
                    if ":" in chart_opt:
                        chart_type, chart_dim = chart_opt.split(":", 1)
                    else:
                        chart_type = chart_opt
                else:
                    chart_type = "hide"
                chart_opts = '''chart_opts=%s''' % json.dumps({"type":chart_type, "dim": chart_dim})

                # Render the pivot table + controls
                pivot_table = DIV(
                    DIV(
                        DIV(T("Hide Pivot Table"), _class="pivot-table-toggle", **hide),
                        DIV(T("Show Pivot Table"), _class="pivot-table-toggle", **show),
                        _class="pivot-table-control"
                    ),
                    DIV(items, _class="pivot-table-contents", **hide),
                    _id="pivot-table"
                )
                output = dict(pivot_table=pivot_table,
                              chart_opts=chart_opts,
                              report_data=report_data)

                # Other output options
                s3 = response.s3
                s3.dataTable_iDisplayLength = 50
                s3.no_formats = True
                s3.no_sspag = True
                s3.actions = []
                output["sortby"] = [[0, "asc"]]

            else:
                r.error(501, current.manager.ERROR.BAD_FORMAT)

        elif representation in ("html", "iframe"):

            # Fallback to list view
            current.s3db.configure(tablename, insertable=False)
            output = self.select(r, **attr)
            response.s3.actions = [
                dict(url = r.url(method="",
                                 id="[id]",
                                 vars=r.get_vars),
                     label = str(T("Details")),
                     _class="action-btn")
            ]

        else:
            r.error(501, current.manager.ERROR.BAD_METHOD)

        # Complete the page
        if representation in ("html", "iframe"):
            crud_string = self.crud_string
            title = crud_string(tablename, "title_report")
            if not title:
                title = crud_string(tablename, "title_list")
            if form is not None:
                form = DIV(DIV(form,
                               _id="reportform"),
                           _style="margin-bottom: 5px;")
            else:
                form = ""
            output["title"] = title
            output["form"] = form
            response.view = self._view(r, "report.html")

        return output

    # -------------------------------------------------------------------------
    def _create_form(self, form_values=None, clear_opts=""):
        """
            Create the report filter and options form

            @param form_values: the form values to populate the widgets
            @clear_opts: action link to clear all filter opts
        """

        T = current.T

        filter_options = self._filter_options(form_values)
        report_options, hidden = self._report_options(form_values)

        if filter_options is None:
            filter_options = ""
        if report_options is None:
            report_options = ""
        
        form = FORM(filter_options,
                    report_options,
                    DIV(INPUT(_value=current.T("Submit"),
                              _type="submit"
                             ),
                        clear_opts
                       ),
                    hidden=hidden,
                   )

        return form

    # -------------------------------------------------------------------------
    def _filter_options(self, form_values=None):
        """
            Render the filter options for the form

            @param form_values: the form values to populate the widgets
        """

        report_options = self._config("report_options", None)
        if not report_options:
            return None
        filter_widgets = report_options.get("search", None)
        if not filter_widgets:
            return None

        T = current.T

        resource = self.resource
        vars = form_values if form_values else self.request.vars
        trows = []
        tappend = trows.append
        for widget in filter_widgets:
            name = widget.attr["_name"]
            _widget = widget.widget(resource, vars)
            if not name or _widget is None:
                # Skip this widget as we have nothing but the label
                continue
            label = widget.field
            if isinstance(label, (list, tuple)) and len(label):
                label = label[0]
            comment = ""
            if hasattr(widget, "attr"):
                label = widget.attr.get("label", label)
                comment = widget.attr.get("comment", comment)
            if comment:
                comment = DIV(_class="tooltip",
                              _title="%s|%s" % (label, comment))
            tr = TR(TD("%s: " % label, _class="w2p_fl"),
                    TD(widget.widget(resource, vars)),
                    TD(comment))
            tappend(tr)
            
        hide = current.deployment_settings.get_ui_hide_report_filter_options()

        return FIELDSET(
                    LEGEND(T("Filter Options"),
                        BUTTON(self.SHOW,
                               _type="button",
                               _class="toggle-text",
                               _style="display:none" if not hide else None),
                        BUTTON(self.HIDE,
                               _type="button",
                               _class="toggle-text",
                               _style="display:none" if hide else None)
                    ),
                    TABLE(trows,
                          _style="display:none" if hide else None),
                    _id="filter_options"
                )

    # -------------------------------------------------------------------------
    def _report_options(self, form_values=None):
        """
            Render the report options for the form

            @param form_values: the form values to populate the widgets
        """

        T = current.T
        request = current.request
        resource = self.resource

        # Get the config options
        _config = self._config
        report_options = _config("report_options", Storage())

        label = lambda s, **attr: TD(LABEL("%s:" % s, **attr),
                                     _class="w2p_fl")

        # Rows/Columns selector
        fs = self._field_select
        select_rows = fs("rows", report_options, form_values)
        select_cols = fs("cols", report_options, form_values)
        selectors = TABLE(TR(label(T("Report of"), _for="report-rows"),
                             TD(select_rows),
                             label(T("Grouped by"), _for="report-cols"),
                             TD(select_cols)
                            )
                          )

        # Layer selector
        layer, hidden = self._method_select("fact",
                                            report_options, form_values)
        single_opt = {"_class": "report-fact-single-option"} \
                     if hidden else {}
        if layer:
            selectors.append(TR(label(T("Value"), _for="report-fact"),
                                TD(layer), **single_opt))

        # Show Totals switch
        # totals are "on" or True by default
        show_totals = True
        if "totals" in form_values:
            show_totals = form_values["totals"]
            if str(show_totals).lower() in ("false", "off"):
                show_totals = False
        selectors.append(TR(TD(LABEL("%s:" % T("Show totals"),
                                     _for="report-totals"),
                               _class="w2p_fl"),
                            TD(INPUT(_type="checkbox",
                                     _id="report-totals",
                                     _name="totals",
                                     value=show_totals)),
                         _class = "report-show-totals-option")
                         )

        # Render field set
        form_report_options = FIELDSET(
                LEGEND(T("Report Options"),
                    BUTTON(self.SHOW,
                           _type="button",
                           _class="toggle-text",
                           _style="display:none" if not hidden else None),
                    BUTTON(self.HIDE,
                           _type="button",
                           _class="toggle-text",
                           _style="display:none" if hidden else None)
                ),
                selectors, _id="report_options")

        return form_report_options, hidden

    # -------------------------------------------------------------------------
    def _field_select(self, name, options=None, form_values=None, **attr):
        """
            Returns a SELECT of field names

            @param name: the element name
            @param options: the report options
            @param form_values: the form values to populate the widget
            @param attr: the HTML attributes for the widget
        """

        resource = self.resource
        if options and name in options:
            fields = options[name]
        else:
            fields = self._config("list_fields", None)
        if not fields:
            fields = [f.name for f in resource.readable_fields()]

        prefix = lambda v: "%s.%s" % (resource.alias, v) \
                           if "." not in v.split("$", 1)[0] \
                           else v.replace("~", resource.alias)

        attr = Storage(attr)
        if "_name" not in attr:
            attr["_name"] = name
        if "_id" not in attr:
            attr["_id"] = "report-%s" % name

        if form_values:
            value = form_values.get(name, "")
        else:
            value = ""
        if value:
            value = prefix(value)

        table = self.table
        rfields, j, l, d = resource.resolve_selectors(fields)
        opts = [(prefix(f.selector), f.label) for f in rfields
                if f.show and
                   (f.field is None or f.field.name != table._id.name)]
        dummy_field = Storage(name=name, requires=IS_IN_SET(opts))
        return OptionsWidget.widget(dummy_field, value, **attr)

    # -------------------------------------------------------------------------
    def _method_select(self, name, options, form_values=None, **attr):
        """
            Returns a SELECT of (field:method) options

            @param name: the element name
            @param options: the report options
            @param form_values: the form values to populate the widget
            @param attr: the HTML attributes for the widget
        """

        RECORDS = current.T("Records")

        if "methods" in options:
            all_methods = options["methods"]
        else:
            all_methods = S3Report.METHODS

        resource = self.resource
        if options and name in options:
            methods = options[name]
        else:
            methods = self._config("list_fields", None)
        if not methods:
            methods = [f.name for f in resource.readable_fields()]

        prefix = lambda v: "%s.%s" % (resource.alias, v) \
                           if "." not in v.split("$", 1)[0] \
                           else v.replace("~", resource.alias)

        attr = Storage(attr)
        if "_name" not in attr:
            attr["_name"] = name
        if "_id" not in attr:
            attr["_id"] = "report-%s" % name

        if form_values:
            value = form_values.get(name, "")
        else:
            value = ""
        if value:
            value = prefix(value)

        # Backward-compatiblity: render aggregate if given --------------------

        if "aggregate" in form_values and ":" not in value:
            value = "%s:%s" % (form_values["aggregate"], value)

        # Resolve selectors, add method options -------------------------------

        opts = []
        for o in methods:

            if type(o) is tuple and isinstance(o[0], lazyT):
                # Backward compatibility
                opt = [o]
            else:
                opt = list(o) if isinstance(o, (tuple, list)) else [o]
            s = opt[0]
            if isinstance(s, tuple):
                label, selector = s
            else:
                label, selector = None, s
            selector = prefix(selector)
            rfield = resource.resolve_selector(selector)
            if label is not None:
                rfield.label = label
            else:
                label = rfield.label if rfield.label != "Id" else RECORDS

            if len(opt) == 1:
                is_amount = None
                # Only field given -> auto-detect aggregation methods
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
                opts.extend([(rfield, opt[0], m)
                             for m in mopts if m in all_methods])
            else:
                opt.insert(0, rfield)
                opts.append(opt)

        # Construct missing labels --------------------------------------------

        _methods = []
        for opt in opts:
            if len(opt) == 3:
                # field+method -> construct label
                mlabel = self.mname(opt[2])
                flabel = opt[0].label if opt[0].label != "Id" else RECORDS
                label = current.T("%s (%s)") % (flabel, mlabel)
                _methods.append((opt[0].selector, opt[2], label))
            else:
                _methods.append((opt[0].selector, opt[2], opt[3]))

        # Build the widget ----------------------------------------------------

        opts = [("%s:%s" % (m[1], m[0]), m[2]) for m in _methods]
        if len(opts) == 1:
            opt = opts[0]
            return opt[1], {name: opt[0]}
        dummy_field = Storage(name=name, requires=IS_IN_SET(opts))
        return OptionsWidget.widget(dummy_field, value, **attr), {}

    # -------------------------------------------------------------------------
    @staticmethod
    def report_options_validation(form):
        """
            Report options form validation

            @param form: the form
        """

        if form.vars.rows == form.vars.cols:
           form.errors.cols = current.T("Duplicate label selected")

    # -------------------------------------------------------------------------
    def _process_filter_options(self, form):
        """
            Processes the filter widgets into a filter query

            @param form: the filter form

            @rtype: tuple
            @return: tuple containing (query object, validation errors)
        """

        default = (None, None, None)

        report_options = self._config("report_options", None)
        if not report_options:
            return default

        filter_widgets = report_options.get("search", None)
        if not filter_widgets:
            return default

        resource = self.resource
        dq, vq, errors = default
        build_query = S3Search._build_widget_query
        for widget in filter_widgets:
            if hasattr(widget, "name"):
                name = widget.name
            else:
                name = widget.attr.get("_name", None)

            dq, vq, errors = build_query(resource, name, widget, form, dq, vq)
            if errors:
                form.errors.update(errors)

        errors = form.errors
        return (dq, vq, errors)

    # -------------------------------------------------------------------------
    @staticmethod
    def mname(code):
        """
            Get a label for a method

            @param code: the method code
            @return: the label (lazyT), or None for unsupported methods
        """

        methods = S3Report.METHODS

        if code is None:
            code = "list"
        if code in methods:
            return current.T(methods[code])
        else:
            return None

# =============================================================================
class S3ContingencyTable(TABLE):
    """ HTML Helper to generate a contingency table """

    def __init__(self,
                 report,
                 show_totals=True,
                 url=None,
                 filter_query=None,
                 **attributes):
        """
            Constructor

            @param report: the S3Pivottable instance
            @param attributes: the HTML attributes for the table
        """

        T = current.T
        TOTAL = T("Total")

        TABLE.__init__(self, **attributes)
        components = self.components = []
        self.json_data = None

        layers = report.layers
        resource = report.resource
        tablename = resource.tablename

        cols = report.cols
        rows = report.rows
        numcols = report.numcols
        numrows = report.numrows
        rfields = report.rfields

        get_label = self._get_label
        get_total = self._totals
        represent = lambda f, v, d="": \
                    self._represent(rfields, f, v, default=d)

        layer_label = None
        col_titles = []
        add_col_title = col_titles.append
        col_totals = []
        add_col_total = col_totals.append
        row_titles = []
        add_row_title = row_titles.append
        row_totals = []
        add_row_total = row_totals.append

        # Layer titles --------------------------------------------------------

        # Get custom labels from report options
        layer_labels = Storage()
        report_options = resource.get_config("report_options", None)
        if report_options and "fact" in report_options:
            layer_opts = report_options["fact"]
            for item in layer_opts:
                if isinstance(item, (tuple, list)) and len(item) == 3:
                    if not "." in item[0].split("$")[0]:
                        item = ("%s.%s" % (resource.alias, item[0]),
                                item[1],
                                item[2])
                    layer_labels[(item[0], item[1])] = item[2]
                    
        labels = []
        get_mname = S3Report.mname

        for layer in layers:
            if layer in layer_labels:
                # Custom label
                label = layer_labels[layer]
                if not labels:
                    layer_label = label
                labels.append(s3_unicode(label))
            else:
                # Construct label from field-label and method
                label = get_label(rfields, layer[0], tablename, "fact")
                mname = get_mname(layer[1])
                if not labels:
                    m = layer[1] == "list" and get_mname("count") or mname
                    layer_label = "%s (%s)" % (label, m)
                labels.append("%s (%s)" % (label, mname))

        layers_title = TH(" / ".join(labels))

        # Columns field title -------------------------------------------------

        if cols:
            col_label = get_label(rfields, cols, tablename, "cols")
            _colspan = numcols + 1
        else:
            col_label = ""
            _colspan = numcols
        cols_title = TH(col_label, _colspan=_colspan, _scope="col")

        titles = TR(layers_title, cols_title)

        # Rows field title ----------------------------------------------------

        row_label = get_label(rfields, rows, tablename, "rows")
        rows_title = TH(row_label, _scope="col")
        headers = TR(rows_title)

        # Column headers ------------------------------------------------------

        add_header = headers.append
        values = report.col
        for i in xrange(numcols):
            value = values[i].value
            v = represent(cols, value)
            add_col_title(s3_truncate(unicode(v)))
            colhdr = TH(v, _scope="col")
            add_header(colhdr)

        # Row totals header ---------------------------------------------------

        if show_totals and cols is not None:
            add_header(TH(TOTAL, _class="totals_header rtotal", _scope="col"))
        thead = THEAD(titles, headers)

        # Table body ----------------------------------------------------------

        tbody = TBODY()
        add_row = tbody.append

        # lookup table for cell list values
        cell_lookup_table = {} # {{}, {}}

        cells = report.cell
        rvals = report.row

        cell_vals = Storage()

        for i in xrange(numrows):

            # Initialize row
            _class = i % 2 and "odd" or "even"
            tr = TR(_class=_class)
            add_cell = tr.append

            # Row header
            row = rvals[i]
            v = represent(rows, row.value)
            add_row_title(s3_truncate(unicode(v)))
            rowhdr = TD(v)
            add_cell(rowhdr)

            # Result cells
            for j in xrange(numcols):
                cell = cells[i][j]
                vals = []
                cell_ids = []
                add_value = vals.append
                for layer_idx, layer in enumerate(layers):
                    f, m = layer
                    value = cell[layer]
                    if m == "list":
                        if isinstance(value, list):
                            l = [represent(f, v, d="-") for v in value]
                        elif value is None:
                            l = ["-"]
                        else:
                            if type(value) in (int, float):
                                l = IS_NUMBER.represent(value)
                            else:
                                l = unicode(value)
                        #add_value(", ".join(l))
                        add_value(UL([LI(v) for v in l]))
                    else:
                        if type(value) in (int, float):
                            add_value(IS_NUMBER.represent(value))
                        else:
                            add_value(unicode(value))

                    # hold the references
                    layer_ids = []
                    # get previous lookup values for this layer
                    layer_values = cell_lookup_table.get(layer_idx, {})

                    if m == "count":
                        rfield = rfields[f]
                        field = rfield.field
                        colname = rfield.colname
                        has_fk = field is not None and s3_has_foreign_key(field)
                        for id in cell.records:
                            # cell.records == [#, #, #]

                            record = report.records[id]
                            try:
                                fvalue = record[colname]
                            except AttributeError:
                                fvalue = None

                            if fvalue is not None:
                                if has_fk:
                                    if type(fvalue) is not list:
                                        fvalue = [fvalue]
                                    # list of foreign keys
                                    for fk in fvalue:
                                        if fk is not None and fk not in layer_ids:
                                            layer_ids.append(int(fk))
                                            layer_values[fk] = s3_unicode(field.represent(fk))
                                else:
                                    if type(fvalue) is not list:
                                        fvalue = [fvalue]
                                    for val in fvalue:
                                        if val is not None:
                                            if val not in cell_vals:
                                                next_id = len(cell_vals)
                                                cell_vals[val] = next_id
                                                layer_ids.append(next_id)
                                                layer_values[next_id] = s3_unicode(represent(f, val))
                                            else:
                                                prev_id = cell_vals[val]
                                                if prev_id not in layer_ids:
                                                    layer_ids.append(prev_id)

                                    #if id is not None and id not in layer_ids:
                                        #layer_ids.append(int(id))
                                        #layer_values[id] = s3_unicode(represent(f, fvalue))

                    cell_ids.append(layer_ids)
                    cell_lookup_table[layer_idx] = layer_values

                # @todo: with multiple layers - show the first, hide the rest
                #        + render layer selector in the layer title corner to
                #        + switch between layers
                #        OR: give every layer a title row (probably better method)
                vals = [DIV(v, _class="report-cell-value") for v in vals]

                if any(cell_ids):
                    cell_attr = {"_data-records": cell_ids}
                    vals.append(DIV(_class="report-cell-zoom"))
                else:
                    cell_attr = {}

                add_cell(TD(vals, **cell_attr))

            # Row total
            totals = get_total(row, layers, append=add_row_total)
            if show_totals and cols is not None:
                add_cell(TD(totals))

            add_row(tr)

        # Table footer --------------------------------------------------------

        i = numrows
        _class = i % 2 and "odd" or "even"
        _class = "%s %s" % (_class, "totals_row")
        col_total = TR(_class=_class)
        add_total = col_total.append
        add_total(TH(TOTAL, _class="totals_header", _scope="row"))

        # Column totals -------------------------------------------------------

        for j in xrange(numcols):
            col = report.col[j]
            totals = get_total(col, layers, append=add_col_total)
            add_total(TD(IS_NUMBER.represent(totals)))

        # Grand total ---------------------------------------------------------

        if cols is not None:
            grand_totals = get_total(report.totals, layers)
            add_total(TD(grand_totals))
        tfoot = TFOOT(col_total)

        # Wrap up -------------------------------------------------------------

        append = components.append
        append(thead)
        append(tbody)
        if show_totals:
            append(tfoot)

        # Chart data ----------------------------------------------------------

        layer_label = s3_unicode(layer_label)
        BY = T("by")
        row_label = "%s %s" % (BY, s3_unicode(row_label))
        if col_label:
            col_label = "%s %s" % (BY, s3_unicode(col_label))
        if filter_query and hasattr(filter_query, "serialize_url"):
            filter_vars = filter_query.serialize_url(resource=report.resource)
        else:
            filter_vars = {}
        hide_opts = current.deployment_settings.get_ui_hide_report_options()
        json_data = json.dumps(dict(t=layer_label,
                                    x=col_label,
                                    y=row_label,
                                    r=report.rows,
                                    c=report.cols,
                                    d=report.compact(n=50, represent=True),
                                    u=url,
                                    f=filter_vars,
                                    h=hide_opts,
                                    cell_lookup_table=cell_lookup_table))
        self.report_data = Storage(row_label=row_label,
                                   col_label=col_label,
                                   layer_label=layer_label,
                                   json_data=json_data)

    # -------------------------------------------------------------------------
    @staticmethod
    def _totals(values, layers, append=None):
        """
            Get the totals of a row/column/report

            @param values: the values dictionary
            @param layers: the layers
            @param append: callback to collect the totals for JSON data
                           (currently only collects the first layer)
        """

        totals = []
        for layer in layers:
            f, m = layer
            value = values[layer]

            if m == "list":
                value = value and len(value) or 0
            if not len(totals) and append is not None:
                append(value)
            totals.append(IS_NUMBER.represent(value))
        totals = " / ".join(totals)
        return totals

    # -------------------------------------------------------------------------
    @staticmethod
    def _represent(rfields, field, value, default="-"):
        """
            Represent a field value

            @param rfields: the list fields map
            @param field: the field
            @param value: the value
            @param default: the default representation
        """

        if field in rfields:
            lfield = rfields[field]
            if lfield.field:
                f = lfield.field
                ftype = str(f.type)
                if ftype not in ("string", "text") and \
                   isinstance(value, basestring):
                    # pyvttbl converts col/row headers into unicode,
                    # but represent may need the original data type,
                    # hence try to convert it back here:
                    convert = S3TypeConverter.convert
                    try:
                        if ftype == "boolean":
                            value = convert(bool, value)
                        elif ftype == "integer":
                            value = convert(int, value)
                        elif ftype == "float":
                            value = convert(float, value)
                        elif ftype == "date":
                            value = convert(datetime.date, value)
                        elif ftype == "time":
                            value = convert(datetime.time, value)
                        elif ftype == "datetime":
                            value = convert(datetime.datetime, value)
                    except TypeError, ValueError:
                        pass
                return current.manager.represent(lfield.field, value,
                                                 strip_markup=True)
        if value is None:
            return default
        else:
            return unicode(value)

    # -------------------------------------------------------------------------
    @staticmethod
    def _get_label(rfields, field, tablename, key):
        """
            Get the label for a field

            @param rfields: the list fields map
            @param key: the configuration key
        """

        DEFAULT = ""

        if field in rfields:
            rfield = rfields[field]
        else:
            return DEFAULT

        # @todo: cleanup this:
        get_config = lambda key, default, tablename=tablename: \
                     current.s3db.get_config(tablename, key, default)
        list_fields = get_config("list_fields", None)
        fields = get_config(key, list_fields)

        if fields:
            for f in fields:
                if isinstance(f, (tuple, list)) and f[1] == rfield.selector:
                    return f[0]

        if rfield:
            if rfield.ftype == "id":
                return current.T("Records")
            return rfield.label
        else:
            return DEFAULT

# END =========================================================================
