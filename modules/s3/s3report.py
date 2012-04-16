# -*- coding: utf-8 -*-

"""
    S3 Reporting Framework

    @author: Dominic König <dominic[at]aidiq[dot]com>

    @copyright: 2011-2012 (c) Sahana Software Foundation
    @license: MIT

    @status: work in progress

    @requires: U{B{I{Python 2.6}} <http://www.python.org>}
    @requires: U{B{I{SQLite3}} <http://www.sqlite.org>}

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

__all__ = ["S3Cube"]

import sys
import datetime
import gluon.contrib.simplejson as json

from gluon import current
from gluon.storage import Storage
from gluon.html import *
from s3rest import S3TypeConverter
from s3crud import S3CRUD
from s3search import S3Search
from s3utils import s3_truncate
from s3validators import IS_INT_AMOUNT, IS_FLOAT_AMOUNT


# =============================================================================

class S3Cube(S3CRUD):
    """ RESTful method for pivot table reports """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            API entry point

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        manager = current.manager
        if r.http in ("GET", "POST"):
            output = self.report(r, **attr)
        else:
            r.error(405, manager.ERROR.BAD_METHOD)
        return output

    # -------------------------------------------------------------------------
    def report(self, r, **attr):
        """
            Generate a pivot table report

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        T = current.T
        manager = current.manager
        session = current.session
        response = current.response

        table = self.table

        _vars = r.get_vars

        # Generate form -------------------------------------------------------
        # @todo: do this only in interactive formats
        #
        show_form = attr.get("interactive_report", False)
        if show_form:
            form = self._create_form()
            if form.accepts(r.post_vars, session,
                            formname="report",
                            keepvalues=True):
                query, errors = self._process_filter_options(form)
                if r.http == "POST" and not errors:
                    self.resource.add_filter(query)
                _vars = form.vars
        else:
            form = None

        # Get rows, cols, fact and aggregate ----------------------------------
        #
        rows = _vars.get("rows", None)
        cols = _vars.get("cols", None)
        fact = _vars.get("fact", None)
        aggregate = _vars.get("aggregate", None)
        show_totals = _vars.get("totals", "on")

        if not rows:
            rows = None
        if not cols:
            cols = None
        if not rows and not cols:
            self.method = "list"
        if not aggregate:
            aggregate = "list"
        if show_totals is None or \
           str(show_totals).lower() in ("false", "off"):
            show_totals = False
        else:
            show_totals = True
        layers = []
        if not fact:
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

        # Apply method --------------------------------------------------------
        #
        _show = "%s hide"
        _hide = "%s"

        resource = self.resource
        representation = r.representation

        if self.method == "report":

            # Generate the report ---------------------------------------------
            #
            try:
                report = S3Report(resource, rows, cols, layers)
            except ImportError:
                msg = T("S3Cube unresolved dependencies")
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
                e = sys.exc_info()[1]
                if hasattr(e, "message"):
                    e = e.message
                else:
                    e = str(e)
                msg = "%s: %s" % (msg, e)
                r.error(400, msg, next=r.url(vars=[]))

            # Represent the report --------------------------------------------
            #
            if representation == "html":
                report_data = None
                if not report.empty:
                    items = S3ContingencyTable(report,
                                               show_totals=show_totals,
                                               _id="list",
                                               _class="dataTable display")
                    report_data = items.report_data
                else:
                    items = self.crud_string(self.tablename, "msg_no_match")

                output = dict(items=items,
                              report_data=report_data)

                # Other output options ----------------------------------------
                #
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
                r.error(501, manager.ERROR.BAD_FORMAT)

        elif representation == "html":

                # Fallback to list view ---------------------------------------
                #
                manager.configure(self.tablename, insertable=False)
                output = self.select(r, **attr)
                response.s3.actions = [
                        dict(url=r.url(method="", id="[id]", vars=r.get_vars),
                             _class="action-btn",
                             label = str(T("Details")))
                ]
        else:
            r.error(501, manager.ERROR.BAD_METHOD)

        # Complete the page ---------------------------------------------------
        #
        if representation == "html":
            crud_string = self.crud_string
            title = crud_string(self.tablename, "title_report")
            if not title:
                title = crud_string(self.tablename, "title_list")

            subtitle = crud_string(self.tablename, "subtitle_report")
            if not subtitle:
                subtitle = crud_string(self.tablename, "subtitle_list")

            # @todo: move JavaScript into s3.report.js
            if form is not None:
                show_link = A(T("Show Report Options"),
                            _href="#",
                            _class=_show % "action-lnk",
                            _id = "show-opts-btn",
                            _onclick="""$('#reportform').removeClass('hide'); $('#show-opts-btn').addClass('hide'); $('#hide-opts-btn').removeClass('hide');""")
                hide_link = A(T("Hide Report Options"),
                            _href="#",
                            _class=_hide % "action-lnk",
                            _id = "hide-opts-btn",
                            _onclick="""$('#reportform').addClass('hide'); $('#show-opts-btn').removeClass('hide'); $('#hide-opts-btn').addClass('hide');""")
                form = DIV(DIV(show_link, hide_link),
                           DIV(form,
                               _class=_hide % "reportform",
                               _id="reportform"),
                               _style="margin-bottom: 5px;")
            else:
                form = ""

            output["title"] = title
            output["subtitle"] = subtitle
            output["form"] = form
            response.view = self._view(r, "report.html")

        return output

    # -------------------------------------------------------------------------
    def _create_form(self):
        """ Creates the report filter and options form """

        T = current.T
        request = current.request
        resource = self.resource

        # Get list_fields
        _config = self._config
        list_fields = _config("list_fields")
        if not list_fields:
            list_fields = [f.name for f in resource.readable_fields()]

        report_rows = _config("report_rows", list_fields)
        report_cols = _config("report_cols", list_fields)
        report_fact = _config("report_fact", list_fields)

        _select_field = self._select_field
        select_rows = _select_field(report_rows, _id="rows", _name="rows")
        select_cols = _select_field(report_cols, _id="cols", _name="cols")
        select_fact = _select_field(report_fact, _id="fact", _name="fact")

        show_totals = True
        if request.env.request_method == "GET" and \
           "show_totals" in request.get_vars:
            show_totals = request.get_vars["show_totals"]
            if show_totals.lower() in ("false", "off"):
                show_totals = False

        show_totals = INPUT(_type="checkbox", _id="totals", _name="totals",
                            value=show_totals)

        methods = _config("report_method")
        select_method = self._select_method(methods,
                                            _id="aggregate",
                                            _name="aggregate")

        form = FORM()

        # Append filter widgets, if configured
        filter_widgets = self._build_filter_widgets()
        if filter_widgets:
            form.append(TABLE(filter_widgets, _id="filter_options"))

        # Append report options, always
        report_options = TABLE(
                    TR(
                        TD(LABEL("Rows:"), _class="w2p_fl"),
                        TD(LABEL("Columns:"), _class="w2p_fl"),
                    ),
                    TR(
                        TD(select_rows),
                        TD(select_cols),
                    ),
                    TR(
                        TD(LABEL("Value:"), _class="w2p_fl"),
                        TD(LABEL("Function for Value:"), _class="w2p_fl"),
                    ),
                    TR(
                        TD(select_fact),
                        TD(select_method),
                    ),
                    TR(
                        TD(LABEL("Show totals:"), _class="w2p_fl")
                    ),
                    TR(
                        TD(show_totals)
                    ),
                    TR(
                        INPUT(_value=T("Submit"), _type="submit"),
                        # @todo: Reset-link to restore pre-defined parameters,
                        #        show only if URL vars present
                        #A(T("Reset"), _class="action-lnk"),
                        _colspan=3), _id="report_options")
        form.append(report_options)

        return form

    # -------------------------------------------------------------------------
    def _build_filter_widgets(self):
        """
            Builds the filter form widgets
        """

        request = self.request
        resource = self.resource
        filter_widgets = self._config("report_filter", None)
        if not filter_widgets:
            return None
        vars = request.vars
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
            tr = TR(TD("%s: " % label, _class="w2p_fl"),
                    widget.widget(resource, vars))
            if comment:
                tr.append(DIV(DIV(_class="tooltip",
                                  _title="%s|%s" % (label, comment))))
            trows.append(tr)
        return trows

    # -------------------------------------------------------------------------
    def _process_filter_options(self, form):
        """
            Processes the filter widgets into a filter query

            @param form: the filter form
        """

        session = current.session
        response = current.response

        query = None
        errors = None

        filter_widgets = self._config("report_filter", None)
        if not filter_widgets:
            return (None, None)

        for widget in filter_widgets:
            name = widget.attr["_name"]
            query, errors = S3Search._build_widget_query(self.resource,
                                                         name,
                                                         widget,
                                                         form,
                                                         query)
            if errors:
                form.errors.update(errors)
        errors = form.errors
        return (query, errors)

    # -------------------------------------------------------------------------
    def _select_field(self, list_fields, **attr):
        """
            Returns a SELECT of field names

            @param list_fields: the fields to include in the options list
            @param attr: the HTML attributes for the SELECT
        """

        request = current.request
        resource = self.resource
        value = None
        disable = False
        if request.env.request_method == "GET":
            if "_name" in attr:
                name = attr["_name"]
                if name in request.get_vars:
                    value = request.get_vars[name]
        table = self.table
        lfields, joins, left, distinct = resource.resolve_selectors(list_fields)
        options = [OPTION(f.label,
                          _value=f.selector,
                          _selected= value == f.selector and "selected" or None)
                   for f in lfields
                    if (f.field is None or f.field.name != table._id.name) and f.show]
        if len(options) < 2:
            options[0].update(_selected="selected")
        else:
            options.insert(0, OPTION("", _value=None))
        select = SELECT(options, **attr)
        return select

    # -------------------------------------------------------------------------
    def _select_method(self, methods, **attr):
        """
            Returns a SELECT of aggregation methods

            @param methods: list of methods to show
            @param attr: the HTML attributes for the SELECT
        """

        T = current.T
        supported_methods = {
            "list": T("List"),
            "count": T("Count"),
            "sum": T("Sum"),
            "avg": T("Average")
        }
        if methods:
            methods = [(m, supported_methods[m])
                       for m in methods
                       if m in supported_methods]
        else:
            methods = supported_methods.items()
        selected = current.request.vars.aggregate
        options = [OPTION(m[1],
                          _value=m[0],
                          _selected= m[0] == selected and "selected" or None)
                   for m in methods]
        if len(options) < 2:
            options[0].update(_selected="selected")
        else:
            options.insert(0, OPTION("", _value=None))
        select = SELECT(options, **attr)
        return select

# =============================================================================

class S3Report:
    """ Class representing reports """

    def __init__(self, resource, rows, cols, layers):
        """
            Constructor

            @param resource: the S3Resource
            @param rows: the rows dimension
            @param cols: the columns dimension
            @param layers: the report layers as [(fact, aggregate_method)]
        """

        manager = current.manager
        model = manager.model

        # Initialize ----------------------------------------------------------
        #
        if not rows and not cols:
            raise SyntaxError("No rows or columns for report specified")

        self.resource = resource
        self.rows = rows
        self.cols = cols
        self.layers = layers

        self.records = None
        self.empty = False

        self.lfields = None
        self.dfields = None
        self.rfields = None

        self.row = None
        self.col = None
        self.cell = None

        self.numrows = None
        self.numcols = None
        self.totals = Storage()

        # Get the fields ------------------------------------------------------
        #
        fields = model.get_config(resource.tablename, "report_fields",
                 model.get_config(resource.tablename, "list_fields"))
        self._get_fields(fields=fields)

        # Retrieve the records --------------------------------------------------
        #
        records = resource.sqltable(self.rfields,
                                    as_list=True, start=None, limit=None)
        table = resource.table
        pkey = table._id.name

        # Generate the report -------------------------------------------------
        #
        if records:

            try:
                extract = self._extract
                self.records = Storage([(extract(i, pkey), i) for i in records])
            except KeyError:
                raise KeyError("Could not retrieve primary key values of %s" %
                               resource.tablename)

            # Generate the data frame -----------------------------------------
            #
            from pyvttbl import DataFrame
            df = DataFrame()
            insert = df.insert

            item_list = []
            seen = item_list.append

            flatten = self._flatten
            expand = self._expand

            for row in records:
                item = expand(flatten(row))
                for i in item:
                    if i not in item_list:
                        seen(i)
                        insert(i)

            # Group the items -------------------------------------------------
            #
            rows = self.rows and [self.rows] or []
            cols = self.cols and [self.cols] or []
            pt = df.pivot(pkey, rows, cols, aggregate="tolist")

            # Initialize columns and rows -------------------------------------
            #
            if cols:
                self.col = [Storage({"value": v != "__NONE__" and v or None})
                            for v in [n[0][1] for n in pt.cnames]]
                self.numcols = len(self.col)
            else:
                self.col = [Storage({"value": None})]
                self.numcols = 1

            if rows:
                self.row = [Storage({"value": v != "__NONE__" and v or None})
                            for v in [n[0][1] for n in pt.rnames]]
                self.numrows = len(self.row)
            else:
                self.row = [Storage({"value": None})]
                self.numrows = 1

            # Add the layers --------------------------------------------------
            #
            add_layer = self._add_layer
            layers = list(self.layers)
            for f, m in self.layers:
                add_layer(pt, f, m)
        else:
            # No items to report on -------------------------------------------
            #
            self.empty = True

    # -------------------------------------------------------------------------
    def _get_fields(self, fields=None):
        """
            Determine the fields needed to generate the report

            @param fields: fields to include in the report (all fields)
        """

        resource = self.resource
        table = resource.table

        pkey = table._id.name
        rows = self.rows
        cols = self.cols

        if fields is None:
            fields = []

        # dfields: fields to group the records
        dfields = []
        if rows and rows not in dfields:
            dfields.append(rows)
        if cols and cols not in dfields:
            dfields.append(cols)
        if pkey not in dfields:
            dfields.append(pkey)
        self.dfields = dfields

        # rfields: fields to generate the layers
        rfields = list(fields)
        if rows and rows not in rfields:
            rfields.append(rows)
        if cols and cols not in rfields:
            rfields.append(cols)
        if pkey not in rfields:
            rfields.append(pkey)
        for f, m in self.layers:
            if f not in rfields:
                rfields.append(f)
        self.rfields = rfields

        # lfields: rfields resolved into list fields map
        lfields, joins, left, distinct = resource.resolve_selectors(rfields)
        lfields = Storage([(f.selector, f) for f in lfields])
        self.lfields = lfields

        return

    # -------------------------------------------------------------------------
    def _flatten(self, row):
        """
            Prepare a DAL Row for the data frame

            @param row: the row
        """

        fields = self.dfields
        resource = self.resource
        table = resource.table
        pkey = table._id.name
        item = Storage()
        extract = self._extract
        pk = extract(row, pkey)
        for field in fields:
            value = extract(row, field)
            if value is None and field != pkey:
                value = "__NONE__"
            if type(value) is str:
                value = unicode(value.decode("utf-8"))
            item[field] = value
        item[pkey] = pk
        return item

    # -------------------------------------------------------------------------
    def _extract(self, row, field):
        """
            Extract a field value from a DAL row

            @param row: the row
            @param field: the fieldname (list_fields syntax)
        """

        lfields = self.lfields
        if field not in lfields:
            raise KeyError("Invalid field name: %s" % field)
        lfield = lfields[field]
        tname = lfield.tname
        fname = lfield.fname
        if fname in row:
            value = row[fname]
        elif tname in row and fname in row[tname]:
            value = row[tname][fname]
        else:
            value = None
        return value

    # -------------------------------------------------------------------------
    def _expand(self, row, field=None):
        """
            Expand a data frame row into a list of rows for list:type values

            @param row: the row
            @param field: the field to expand (None for all fields)
        """

        if field is None:
            rows = [row]
            for field in row:
                rows = self._expand(rows, field=field)
            return rows
        else:
            results = []
            rows = row
            for r in rows:
                value = r[field]
                if isinstance(value, (list, tuple)):
                    if not len(value):
                        # Always have at least a None-entry
                        value.append(None)
                    for v in value:
                        result = Storage(r)
                        result[field] = v
                        results.append(result)
                else:
                    results.append(r)
            return results

    # -------------------------------------------------------------------------
    def _add_layer(self, pt, fact, method):
        """
            Compute a new layer from the base layer (pt+items)

            @param pt: the pivot table with record IDs
            @param fact: the fact field for the layer
            @param method: the aggregation method of the layer
        """

        if self.mname(method) is None:
            raise SyntaxError("Unsupported aggregation method: %s" % method)

        items = self.records
        lfields = self.lfields
        rows = self.row
        cols = self.col
        records = self.records
        extract = self._extract
        aggregate = self._aggregate
        resource = self.resource

        RECORDS = "records"
        VALUES = "values"

        table = resource.table
        pkey = table._id.name

        if method is None:
            method = "list"
        layer = (fact, method)

        numcols = len(pt.cnames)
        numrows = len(pt.rnames)

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
                    data = pt[r][c]
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
                if fact is None:
                    fact = pkey
                    values = ids
                    row_values = row_records
                    col_values = row_records
                    all_values = self.records.keys()
                else:
                    values = []
                    append = values.append
                    for i in ids:
                        value = extract(records[i], fact)
                        if value is None:
                            continue
                        append(value)
                    if len(values) and type(values[0]) is list:
                        values = reduce(lambda x, y: x.extend(y) or x, values)
                    if method in ("list", "count"):
                        values =  list(set(values))
                    row_values.extend(values)
                    col_values.extend(values)
                    all_values.extend(values)

                # Aggregate values
                value = aggregate(values, method)
                cell[layer] = value

            # Compute row total
            row[layer] = aggregate(row_values, method)
            del row[VALUES]

        # Compute column total
        for c in xrange(numcols):
            col = cols[c]
            col[layer] = aggregate(col[VALUES], method)
            del col[VALUES]

        # Compute overall total
        self.totals[layer] = aggregate(all_values, method)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def _aggregate(values, method):
        """
            Compute an aggregation of atomic values

            @param values: the values
            @param method: the aggregation method
        """

        if values is None:
            return None

        if method is None or method == "list":
            if values:
                return values
            else:
                return None

        elif method == "count":
            return len(values)

        elif method == "min":
            try:
                return min(values)
            except TypeError:
                return None

        elif method == "max":
            try:
                return max(values)
            except TypeError, ValueError:
                return None

        elif method == "sum":
            try:
                return sum(values)
            except TypeError, ValueError:
                return None

        elif method in ("avg", "mean"):
            try:
                if len(values):
                    return sum(values) / float(len(values))
                else:
                    return 0.0
            except TypeError, ValueError:
                return None

        #elif method == "std":
            #import numpy
            #if not values:
                #return 0.0
            #try:
                #return numpy.std(values)
            #except TypeError, ValueError:
                #return None

        else:
            return None

    # -------------------------------------------------------------------------
    def __len__(self):
        """ Total number of records in the report """

        items = self.records
        if items is None:
            return 0
        else:
            return len(self.records)

    # -------------------------------------------------------------------------
    @staticmethod
    def mname(code):
        """
            Get the method name for a method code, returns None for
            unsupported methods

            @param code: the method code
        """

        T = current.T
        mnames = {
            "list": T("List"),
            "count": T("Count"),
            "min": T("Minimum"),
            "max": T("Maximum"),
            "sum": T("Sum"),
            "avg": T("Average"),
            "mean": T("Average"),
            #"std": T("Standard Deviation")
        }
        if code is None:
            code = "list"
        return mnames.get(code, None)

# =============================================================================

class S3ContingencyTable(TABLE):
    """ HTML Helper to generate a contingency table """

    def __init__(self, report, show_totals=True, **attributes):
        """
            Constructor

            @param report: the S3Report
            @param attributes: the HTML attributes for the table
        """

        manager = current.manager

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
        lfields = report.lfields

        get_label = self._get_label
        get_total = self._totals
        represent = lambda f, v, d="": \
                    self._represent(lfields, f, v, default=d)

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
        # @todo: make class and move into CSS:
        _style = "border:1px solid #cccccc; font-weight:bold;"

        # Layer titles
        labels = []
        get_mname = report.mname
        for field, method in layers:
            label = get_label(lfields, field, tablename, "report_fact")
            mname = get_mname(method)
            if not labels:
                m = method == "list" and get_mname("count") or mname
                layer_label = "%s (%s)" % (label, m)
            labels.append("%s (%s)" % (label, mname))
        layers_title = TD(" / ".join(labels), _style=_style)

        # Columns field title
        if cols:
            col_label = get_label(lfields, cols, tablename, "report_cols")
            _colspan = numcols + 1
        else:
            col_label = ""
            _colspan = numcols
        cols_title = TD(col_label, _style=_style, _colspan=_colspan)

        titles = TR(layers_title, cols_title)

        # Rows field title
        row_label = get_label(lfields, rows, tablename, "report_rows")
        rows_title = TH(row_label, _style=_style)

        headers = TR(rows_title)
        add_header = headers.append

        # Column headers
        values = report.col
        for i in xrange(numcols):
            value = values[i].value
            v = represent(cols, value)
            add_col_title(s3_truncate(unicode(v)))
            colhdr = TH(v, _style=_style)
            add_header(colhdr)

        # Row totals header
        if show_totals and cols is not None:
            add_header(TH(TOTAL, _class="totals_header rtotal"))

        thead = THEAD(titles, headers)

        # Table body ----------------------------------------------------------
        #
        tbody = TBODY()
        add_row = tbody.append

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
                add_value = vals.append
                for layer in layers:
                    f, m = layer
                    value = cell[layer]
                    if m == "list":
                        if isinstance(value, list):
                            l = [represent(f, v, d="-") for v in value]
                        elif value is None:
                            l = "-"
                        else:
                            if type(value) is int:
                                l = IS_INT_AMOUNT.represent(value)
                            elif type(value) is float:
                                l = IS_FLOAT_AMOUNT.represent(value, precision=2)
                            else:
                                l = unicode(value)
                        add_value(", ".join(l))
                    else:
                        if type(value) is int:
                            add_value(IS_INT_AMOUNT.represent(value))
                        elif type(value) is float:
                            add_value(IS_FLOAT_AMOUNT.represent(value, precision=2))
                        else:
                            add_value(unicode(value))
                vals = " / ".join(vals)
                add_cell(TD(vals))

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
        add_total(TD(TOTAL, _class="totals_header"))

        # Column totals
        for j in xrange(numcols):
            col = report.col[j]
            totals = get_total(col, layers, append=add_col_total)
            add_total(TD(totals))

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
        col_label = "%s %s" % (BY, str(col_label))
        layer_label=str(layer_label)
        json_data = json.dumps(dict(rows=drows,
                                    cols=dcols,
                                    row_label=row_label,
                                    col_label=col_label,
                                    layer_label=layer_label
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
        T = current.T
        try:
            if len(tl) > length:
                m = length - 1
                l = list(tl)
                l.sort(lambda x, y: int(y[1]-x[1]))
                if least:
                    l.reverse()
                ts = (str(T("Others")), reduce(lambda s, t: s+t[1], l[m:], 0))
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
            totals.append(str(value))
        totals = " / ".join(totals)
        return totals

    # -------------------------------------------------------------------------
    @staticmethod
    def _represent(lfields, field, value, default="-"):
        """
            Represent a field value

            @param lfields: the list fields map
            @param field: the field
            @param value: the value
            @param default: the default representation
        """

        manager = current.manager
        if field in lfields:
            lfield = lfields[field]
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
                return manager.represent(lfield.field, value,
                                         strip_markup=True)
        if value is None:
            return default
        else:
            return unicode(value)

    # -------------------------------------------------------------------------
    @staticmethod
    def _get_label(lfields, field, tablename, key):
        """
            Get the label for a field

            @param lfields: the list fields map
            @param key: the configuration key
        """

        DEFAULT = ""

        manager = current.manager
        model = manager.model

        if field in lfields:
            lf = lfields[field]
        else:
            return DEFAULT
        get_config = lambda key, default, tablename=tablename: \
                     model.get_config(tablename, key, default)
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
