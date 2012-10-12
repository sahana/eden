# -*- coding: utf-8 -*-

""" S3 Reporting Framework

    @copyright: 2011-2012 (c) Sahana Software Foundation
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
        "sum": T("Sum"),
        "avg": T("Average"),
        #"std": T("Standard Deviation")
    }

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
    @staticmethod
    def _process_report_options(form):
        """
            Onvalidation
        """

        if form.vars.rows == form.vars.cols:
           form.errors.cols = current.T("Duplicate label selected")

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

        # Figure out which set of form values to use
        # POST > GET > session > table defaults > list view
        if r.http == "POST":
            # POST
            form_values = r.post_vars

            # The totals option is used to turn OFF the totals cols/rows but
            # post vars only contain checkboxes that are enabled and checked.
            if "totals" not in r.post_vars:
                form_values["totals"] = "off"
        else:
            url_options = Storage([(k, v) for k, v in r.get_vars.iteritems() if v])
            if url_options:
                # GET
                form_values = url_options
                # Without the _formname the form won't validate
                # we put it in here so that URL query strings don't need to
                if not form_values._formname:
                    form_values._formname = "report"
            else:
                session_options = s3.report_options
                if session_options and tablename in session_options:
                    session_options = session_options[tablename]
                else:
                    session_options = Storage()
                if session_options:
                    form_values = session_options
                else:
                    report_options = self._config("report_options", Storage())
                    if report_options and "defaults" in report_options:
                        default_options = report_options["defaults"]
                    else:
                        default_options = Storage()
                    if default_options:
                        form_values = default_options
                        # Without the _formname the form won't validate
                        # we put it in here so that URL query strings don't need to
                        if not form_values._formname:
                            form_values._formname = "report"
                    else:
                        form_values = Storage()

        # Remove the existing session filter if this is a new
        # search (@todo: do not store the filter in session)
        if r.http == "GET" and r.representation != "aadata":
            if "filter" in s3:
                del s3["filter"]

        # Generate the report and resource filter form
        show_form = attr.get("interactive_report", True)
        if show_form:
            # Build the form and prepopulate with values we've got
            form = self._create_form(form_values)

            # Validate the form. This populates form.vars (values) and
            # form.errors (field errors).
            # We only compare to the session if POSTing to prevent cross-site
            # scripting.
            if r.http == "POST" and \
               form.accepts(form_values,
                            session,
                            formname="report",
                            onvalidation=self._process_report_options):

                # The form is valid so save the form values into the session
                if "report_options" not in s3:
                    s3.report_options = Storage()

                s3.report_options[tablename] = Storage([(k, v) for k, v in
                                                        form_values.iteritems() if v and not k[0] == "_"])

            elif not form.errors:
                form.vars = form_values

            # Use the values to generate the query filter
            query, errors = self._process_filter_options(form)
            if not errors:
                self.resource.add_filter(query)
        else:
            form = None

        # Get rows, cols, facts and aggregate
        rows = form_values.get("rows", None)
        cols = form_values.get("cols", None)
        fact = form_values.get("fact", None)
        aggregate = form_values.get("aggregate", "list")
        if not aggregate:
            aggregate = "list"

        # Fall back to list if no dimensions specified
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

        # Apply method
        _show = "%s hide"
        _hide = "%s"

        resource = self.resource
        representation = r.representation

        if not form.errors and self.method == "report":
            # Generate the report
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
                r.error(400, msg, next=r.url(vars=[]))
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
                r.error(400, msg, next=r.url(vars=[]))

            # Represent the report
            if representation in ("html", "iframe"):
                report_data = None
                if not report.empty:
                    items = S3ContingencyTable(report,
                                               show_totals=show_totals,
                                               _id="list",
                                               _class="dataTable display report")
                    report_data = items.report_data
                else:
                    items = self.crud_string(tablename, "msg_no_match")

                output = dict(items=items,
                              report_data=report_data)

                # Other output options
                s3 = response.s3
                s3.dataTable_iDisplayLength = 50
                s3.no_formats = True
                s3.no_sspag = True
                if r.http == "GET":
                    _show = "%s"
                    _hide = "%s hide"
                s3.actions = []
                output.update(sortby=[[0,'asc']])

            else:
                # @todo: support other formats
                r.error(501, current.manager.ERROR.BAD_FORMAT)

        elif representation in ("html", "iframe"):
                # Fallback to list view
                current.s3db.configure(tablename, insertable=False)
                output = self.select(r, **attr)
                response.s3.actions = [
                        dict(url=r.url(method="", id="[id]", vars=r.get_vars),
                             _class="action-btn",
                             label = str(T("Details")))
                        ]
        else:
            r.error(501, current.manager.ERROR.BAD_METHOD)

        if representation in ("html", "iframe"):
            # Complete the page
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
    def _create_form(self, form_values=None):
        """ Creates the report filter and options form """

        T = current.T
        request = current.request
        resource = self.resource

        # Get list_fields
        _config = self._config
        list_fields = _config("list_fields")
        if not list_fields:
            list_fields = [f.name for f in resource.readable_fields()]

        report_options = _config("report_options", Storage())
        report_rows = report_options.get("rows", list_fields)
        report_cols = report_options.get("cols", list_fields)
        report_fact = report_options.get("facts", list_fields)

        _select_field = self._select_field
        select_rows = _select_field(report_rows,
                                    _id="report-rows",
                                    _name="rows",
                                    form_values=form_values)
        select_cols = _select_field(report_cols,
                                    _id="report-cols",
                                    _name="cols",
                                    form_values=form_values)
        select_fact = _select_field(report_fact,
                                    _id="report-fact",
                                    _name="fact",
                                    form_values=form_values)

        # totals are "on" or True by default
        show_totals = True
        if "totals" in form_values:
            show_totals = form_values["totals"]
            if str(show_totals).lower() in ("false", "off"):
                show_totals = False

        show_totals = INPUT(_type="checkbox", _id="report-totals", _name="totals",
                            value=show_totals)

        methods = report_options.get("methods")
        select_method = self._select_method(methods,
                                            _id="report-aggregate",
                                            _name="aggregate",
                                            form_values=form_values)

        form = FORM()

        SHOW = T("Show")
        HIDE = T("Hide")

        # Append filter widgets, if configured
        filter_widgets = self._build_filter_widgets(form_values)
        if filter_widgets:
            form.append(
                FIELDSET(
                    LEGEND(T("Filter Options"),
                        BUTTON(SHOW, _type="button", _class="toggle-text", _style="display:none"),
                        BUTTON(HIDE, _type="button", _class="toggle-text")
                    ),
                    TABLE(filter_widgets),
                    _id="filter_options"
                )
            )

        # Append report options, always
        form_report_options = FIELDSET(
                LEGEND(T("Report Options"),
                    BUTTON(SHOW, _type="button", _class="toggle-text"),
                    BUTTON(HIDE, _type="button", _class="toggle-text", _style="display:none")
                ),
                TABLE(
                    TR(
                        TD(LABEL("%s:" % T("Rows"), _for="report-rows"), _class="w2p_fl"),
                        TD(select_rows),
                    ),
                    TR(
                        TD(LABEL("%s:" % T("Columns"), _for="report-cols"), _class="w2p_fl"),
                        TD(select_cols),
                    ),
                    TR(
                        TD(LABEL("%s:" % T("Value"), _for="report-fact"), _class="w2p_fl"),
                        TD(select_fact),
                    ),
                    TR(
                        TD(LABEL("%s:" % T("Function for Value"), _for="report-aggregate"), _class="w2p_fl"),
                        TD(select_method),
                    ),
                    TR(
                        TD(LABEL("%s:" % T("Show totals"), _for="report-totals"), _class="w2p_fl"),
                        TD(show_totals)
                    ),
                ),
                _id="report_options"
            )
        form.append(form_report_options)
        form.append(INPUT(_value=T("Submit"), _type="submit"))

        return form

    # -------------------------------------------------------------------------
    def _build_filter_widgets(self, form_values=None):
        """
            Builds the filter form widgets
        """

        resource = self.resource

        report_options = self._config("report_options", None)
        if not report_options:
            return None

        filter_widgets = report_options.get("search", None)
        if not filter_widgets:
            return None

        vars = form_values if form_values else self.request.vars
        trows = []
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
            trows.append(tr)
        return trows

    # -------------------------------------------------------------------------
    def _process_filter_options(self, form):
        """
            Processes the filter widgets into a filter query

            @param form: the filter form

            @rtype: tuple
            @return: A tuple containing (query object, validation errors)
        """

        query = None
        errors = None

        report_options = self._config("report_options", None)
        if not report_options:
            return (None, None)

        filter_widgets = report_options.get("search", None)
        if not filter_widgets:
            return (None, None)

        resource = self.resource
        for widget in filter_widgets:
            if hasattr(widget, "name"):
                name = widget.name
            else:
                name = widget.attr.get("_name", None)

            query, errors = S3Search._build_widget_query(resource,
                                                         name,
                                                         widget,
                                                         form,
                                                         query)
            if errors:
                form.errors.update(errors)
        errors = form.errors
        return (query, errors)

    # -------------------------------------------------------------------------
    def _select_field(self, list_fields, form_values=None, **attr):
        """
            Returns a SELECT of field names

            @param list_fields: the fields to include in the options list
            @param attr: the HTML attributes for the SELECT
        """

        name = attr["_name"]
        if form_values:
            value = form_values.get(name, "")
        else:
            value = ""

        table = self.table
        lfields, joins, left, distinct = self.resource.resolve_selectors(list_fields)

        options = []
        for f in lfields:
            if (f.field is None or f.field.name != table._id.name) and f.show:
                options.append((f.selector, f.label))

        dummy_field = Storage(name=name,
                              requires=IS_IN_SET(options))

        return OptionsWidget.widget(dummy_field, value, **attr)

    # -------------------------------------------------------------------------
    @staticmethod
    def _select_method(methods, form_values=None, **attr):
        """
            Returns a SELECT of aggregation methods

            @param methods: list of methods to show
            @param attr: the HTML attributes for the SELECT
        """

        supported_methods = S3Report.METHODS
        if methods:
            methods = [(m, supported_methods[m])
                       for m in methods
                       if m in supported_methods]
        else:
            methods = supported_methods.items()

        name = attr["_name"]

        if form_values:
            value = form_values[name]
        else:
            value = None

        options = []
        for method, label in methods:
            options.append((method, label))

        dummy_field = Storage(name=name,
                              requires=IS_IN_SET(options))

        return OptionsWidget.widget(dummy_field, value, **attr)

    # -------------------------------------------------------------------------
    @staticmethod
    def mname(code):
        """
            Get the method name for a method code, returns None for
            unsupported methods

            @param code: the method code
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

    def __init__(self, report, show_totals=True, **attributes):
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

        # Table header --------------------------------------------------------
        #

        # Layer titles
        labels = []
        get_mname = S3Report.mname
        for field_name, method in layers:
            label = get_label(rfields, field_name, tablename, "fact")
            mname = get_mname(method)
            if not labels:
                m = method == "list" and get_mname("count") or mname
                layer_label = "%s (%s)" % (label, m)
            labels.append("%s (%s)" % (label, mname))
        layers_title = TH(" / ".join(labels))

        # Columns field title
        if cols:
            col_label = get_label(rfields, cols, tablename, "cols")
            _colspan = numcols + 1
        else:
            col_label = ""
            _colspan = numcols
        cols_title = TH(col_label, _colspan=_colspan, _scope="col")

        titles = TR(layers_title, cols_title)

        # Rows field title
        row_label = get_label(rfields, rows, tablename, "rows")
        rows_title = TH(row_label, _scope="col")

        headers = TR(rows_title)
        add_header = headers.append

        # Column headers
        values = report.col
        for i in xrange(numcols):
            value = values[i].value
            v = represent(cols, value)
            add_col_title(s3_truncate(unicode(v)))
            colhdr = TH(v, _scope="col")
            add_header(colhdr)

        # Row totals header
        if show_totals and cols is not None:
            add_header(TH(TOTAL, _class="totals_header rtotal", _scope="col"))

        thead = THEAD(titles, headers)

        # Table body ----------------------------------------------------------
        #

        tbody = TBODY()
        add_row = tbody.append

        # lookup table for cell list values
        cell_lookup_table = {} # {{}, {}}

        cells = report.cell
        rvals = report.row

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
                            l = "-"
                        else:
                            if type(value) in (int, float):
                                l = IS_NUMBER.represent(value)
                            else:
                                l = unicode(value)
                        add_value(", ".join(l))
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
                        for id in cell.records:
                            # cell.records == [#, #, #]
                            field = rfields[f].field
                            record = report.records[id]

                            if field.tablename in record:
                                fvalue = record[field.tablename][field.name]
                            else:
                                fvalue = record[field.name]

                            if fvalue is not None:
                                if s3_has_foreign_key(field):
                                    if not isinstance(fvalue, list):
                                        fvalue = [fvalue]

                                    # list of foreign keys
                                    for fk in fvalue:
                                        if fk not in layer_ids:
                                            layer_ids.append(fk)
                                            layer_values[fk] = str(field.represent(fk))
                                else:
                                    if id not in layer_ids:
                                        layer_ids.append(id)
                                        layer_values[id] = s3_unicode(represent(f, fvalue))


                    cell_ids.append(layer_ids)
                    cell_lookup_table[layer_idx] = layer_values

                vals = " / ".join(vals)

                if any(cell_ids):
                    cell_attr = {
                        "_data-records": cell_ids
                    }
                    vals = (A(_class="report-cell-zoom"), vals)
                else:
                    cell_attr = {}

                add_cell(TD(vals, **cell_attr))

            # Row total
            totals = get_total(row, layers, append=add_row_total)
            if show_totals and cols is not None:
                add_cell(TD(totals))

            add_row(tr)

        # Table footer --------------------------------------------------------
        #
        i = numrows
        _class = i % 2 and "odd" or "even"
        _class = "%s %s" % (_class, "totals_row")

        col_total = TR(_class=_class)
        add_total = col_total.append
        add_total(TH(TOTAL, _class="totals_header", _scope="row"))

        # Column totals
        for j in xrange(numcols):
            col = report.col[j]
            totals = get_total(col, layers, append=add_col_total)
            add_total(TD(IS_NUMBER.represent(totals)))

        # Grand total
        if cols is not None:
            grand_totals = get_total(report.totals, layers)
            add_total(TD(grand_totals))

        tfoot = TFOOT(col_total)

        # Wrap up -------------------------------------------------------------
        #
        append = components.append
        append(thead)
        append(tbody)
        if show_totals:
            append(tfoot)

        # Chart data ----------------------------------------------------------
        #
        drows = dcols = None
        BY = T("by")
        top = self._top
        if rows and row_titles and row_totals:
            drows = top(zip(row_titles, row_totals))
        if cols and col_titles and col_totals:
            dcols = top(zip(col_titles, col_totals))
        row_label = "%s %s" % (BY, str(row_label))
        if col_label:
            col_label = "%s %s" % (BY, str(col_label))
        layer_label=str(layer_label)

        json_data = json.dumps(dict(rows=drows,
                                    cols=dcols,
                                    row_label=row_label,
                                    col_label=col_label,
                                    layer_label=layer_label,
                                    cell_lookup_table=cell_lookup_table
                                   ))
        self.report_data = Storage(row_label=row_label,
                                   col_label=col_label,
                                   layer_label=layer_label,
                                   json_data=json_data)

    # -------------------------------------------------------------------------
    @staticmethod
    def _top(tl, length=10, least=False):
        """
            From a list of tuples (n, v) containing more than N elements,
            selects the top (or least) N (by v) and sums up the others as
            new element "Others".

            @param tl: the tuple list
            @param length: the maximum length N of the result list
            @param reverse: select the least N instead
        """
        try:
            if len(tl) > length:
                m = length - 1
                l = list(tl)
                l.sort(lambda x, y: int(y[1]-x[1]))
                if least:
                    l.reverse()
                ts = (str(current.T("Others")),
                      reduce(lambda s, t: s+t[1], l[m:], 0))
                l = l[:m] + [ts]
                return l
        except (TypeError, ValueError):
            pass
        return tl

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
            lf = rfields[field]
        else:
            return DEFAULT
        get_config = lambda key, default, tablename=tablename: \
                     current.s3db.get_config(tablename, key, default)
        list_fields = get_config("list_fields", None)
        fields = get_config(key, list_fields)
        if fields:
            for f in fields:
                if isinstance(f, (tuple, list)) and f[1] == lf.selector:
                    return f[0]
        if lf:
            return lf.label
        else:
            return DEFAULT

# END =========================================================================
