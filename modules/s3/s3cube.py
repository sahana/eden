# -*- coding: utf-8 -*-

"""
    S3 RESTful Data Analysis Toolkit

    @author: Dominic König <dominic[at]aidiq[dot]com>

    @copyright: 2011 (c) Sahana Software Foundation
    @license: MIT

    @status: work in progress

    @requires: U{B{I{Python 2.6}} <http://www.python.org>}
    @requires: U{B{I{SciPy}} <http://www.scipy.org>}
    @requires: U{B{I{NumPy}} <http://www.numpy.org>}
    @requires: U{B{I{MatPlotLib}} <http://matplotlib.sourceforge.net>}
    @requires: U{B{I{PyvtTbl}} <http://code.google.com/p/pyvttbl>}
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

from gluon import current
from gluon.storage import Storage
from gluon.html import *
from s3crud import S3CRUD
from s3search import S3Search

# =============================================================================

class S3Cube(S3CRUD):
    """ Module for data analysis """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            RESTful method handler

            @param r: the S3Request instance
            @param attr: controller attributes for the request

            @todo: documentation
            @todo: support automatic generation of dimension classes
            @todo: add form generator for interactive pivoting
            @todo: add search form to interactive pivoting form
            @todo: support JSON output
            @todo: support XLS output (requires extension of the codec)
            @todo: support PDF output
            @todo: support client-side representation as graphs
            @todo: support server-side chart generation
        """

        manager = current.manager

        if r.http in ("GET", "POST"):
            if r.interactive:
                output = self.analyze(r, **attr)
            else:
                r.error(501, manager.ERROR.BAD_FORMAT)
        else:
            r.error(405, manager.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def analyze(self, r, **attr):
        """
            @todo: docstring
            @todo: make Ajax'able
            @todo: add filter form (see design spec)
            @todo: move out JavaScript (s3.analyze.js?)
        """

        T = current.T
        manager = current.manager
        session = current.session
        response = current.response

        table = self.table

        try:
            from pyvttbl import DataFrame
            PYVTTBL = True
        except ImportError:
            print >> sys.stderr, "WARNING: S3Cube unresolved dependencies: scipy, numpy and matplotlib required for analyses"
            PYVTTBL = False

        if not PYVTTBL:
            r.error(501, T("Function not available on this server"))

        _vars = r.get_vars

        show_form = attr.get("interactive_report", False)
        if show_form:
            # Generate form
            form = self._create_form()
            if form.accepts(r.post_vars, session,
                            formname="analyze",
                            keepvalues=True):
                query, errors = self._process_filter_options(form)
                if r.http == "POST" and not errors:
                    self.resource.add_filter(query)
                _vars = form.vars
        else:
            form = None

        # Get rows, cols, fact and aggregate
        rows = _vars.get("rows", None)
        cols = _vars.get("cols", None)
        fact = _vars.get("fact", None)
        aggregate = _vars.get("aggregate", None)

        if rows:
            self.rows = [rows]
        else:
            self.method = "list"

        if cols:
            self.cols = [cols]
        else:
            self.cols = []

        if fact:
            self.fact = fact
        else:
            if "name" in table:
                self.fact = "name"
            else:
                self.fact = table._id.name

        if aggregate:
            self.aggregate = aggregate
        else:
            self.aggregate = "list"

        _show = "%s hide"
        _hide = "%s"

        # Apply method
        if self.method == "analyze":
            output = self.pivot(r, **attr)
            response.s3.dataTable_iDisplayLength = 50
            response.s3.no_formats = True
            response.s3.no_sspag = True
            if r.http == "GET":
                _show = "%s"
                _hide = "%s hide"
            response.s3.actions = []
            output.update(sortby=[[0,'asc']])
        else:
            manager.configure(self.tablename, insertable=False)
            output = self.select(r, **attr)
            response.s3.actions = [
                    dict(url=r.url(method="", id="[id]", vars=r.get_vars),
                         _class="action-btn",
                         label = str(T("Details")))
                ]

        title = self.crud_string(self.tablename, "title_report")
        if not title:
            title = self.crud_string(self.tablename, "title_list")

        subtitle = self.crud_string(self.tablename, "subtitle_report")
        if not subtitle:
            subtitle = self.crud_string(self.tablename, "subtitle_list")

        if form is not None:
            show_link = A(T("Show Report Options"),
                        _href="#",
                        _class=_show % "action-lnk",
                        _id = "show-opts-btn",
                        _onclick="""$('#analyzeform').removeClass('hide'); $('#show-opts-btn').addClass('hide'); $('#hide-opts-btn').removeClass('hide');""")
            hide_link = A(T("Hide Report Options"),
                        _href="#",
                        _class=_hide % "action-lnk",
                        _id = "hide-opts-btn",
                        _onclick="""$('#analyzeform').addClass('hide'); $('#show-opts-btn').removeClass('hide'); $('#hide-opts-btn').addClass('hide');""")
            form = DIV(DIV(show_link, hide_link),
                       DIV(form, _class=_hide % "analyzeform", _id="analyzeform"))
        else:
            form = ""

        output.update(title=title, subtitle=subtitle, form=form)

        response.view = self._view(r, "list_create.html")
        return output

    # -------------------------------------------------------------------------
    def pivot(self, r, **attr):
        """
            Method to generate contingency tables

            @param r: the S3Request instance
            @param attr: controller attributes for the request

            @todo: warn if dimension/fact doesn't belong to table
            @todo: support component fields
            @todo: support automatic generation of dimension classes
            @todo: optimize inner loops
            @todo: make facts inline-expandable
        """

        db = current.db
        T = current.T

        response = current.response

        resource = self.resource
        table = resource.table
        pkey = table._id.name

        # Get the fields
        fields = []
        if self.rows:
            fields.extend([f for f in self.rows if f not in fields])
        if self.cols:
            fields.extend([f for f in self.cols if f not in fields])
        if self.fact and self.fact not in fields:
            fields.append(self.fact)
        list_fields = list(fields)
        if pkey not in list_fields:
            list_fields.append(pkey)
        lfields, join = self.get_list_fields(table, list_fields)
        lfields = Storage([(f.fieldname, f) for f in lfields])

        # Get the items
        items = self.sqltable(list_fields,
                              as_list=True, start=None, limit=None)
        count = None
        if items:
            # Generate the data frame
            aggregate = self.aggregate == "list" and "group_concat" or \
                        self.aggregate
            from pyvttbl import DataFrame
            df = DataFrame()
            fmap = Storage()
            item_list = []
            for row in items:
                try:
                    frow = self.__extract(row, fields, resource, lfields, fmap)
                except KeyError:
                    e = sys.exc_info()[1]
                    msg = T("Could not generate report")
                    if hasattr(e, "message"):
                        e = "%s: %s" % (msg, e.message)
                    r.error(400, e, next=r.url(vars=[]))
                frow = self.__expand(frow)
                for item in frow:
                    if aggregate in ("group_concat", "count"):
                        i = Storage(item)
                        if self.fact != pkey:
                            del i[pkey]
                        # De-duplicate
                        if i not in item_list:
                            item_list.append(i)
                            df.insert(aggregate == "count" and i or item)
                    else:
                        df.insert(item)

            # In group_concat, always group primary keys, and then use
            # fmap to link individual fact values to their corresponding
            # records
            if aggregate == "group_concat" and fmap:
                fact = pkey
            else:
                # Otherwise group the fact value, and delete fmap
                fact = self.fact
                fmap = None

            # Pivoting
            try:
                pt = df.pivot(fact, self.rows, self.cols,
                                aggregate=aggregate)
            except:
                e = sys.exc_info()[1]
                msg = T("Could not generate report")
                if hasattr(e, "message"):
                    e = "%s: %s" % (msg, e.message)
                r.error(400, e, next=r.url(vars=[]))

            if aggregate == "count" or pt.grand_tot is None:
                count = len(item_list)

            # Generate output table
            items = S3ContingencyTable(r,
                                       self.resource,
                                       pt,
                                       rows=self.rows,
                                       cols=self.cols,
                                       fact=self.fact,
                                       lfields=lfields,
                                       fmap=fmap,
                                       count=count,
                                       _id="list",
                                       _class="dataTable display")

        else:
            # No items to analyze
            items = self.crud_string(self.tablename, "msg_no_match")

        return dict(items=items)

    # -------------------------------------------------------------------------
    def __extract(self, row, fields, resource, lfields, fmap):
        """
            Helper method to extract data from a Row

            @param row: the Row
            @param fields: the fields for the contingency table
            @param resource: the S3Resource
            @param lfields: the list fields
            @param fmap: the id/fact map for the rows (Storage)
        """

        table = resource.table
        tname = resource.tablename
        pkey = table._id.name

        if pkey in row:
            pk = row[pkey]
        elif tname in row and pkey in row[tname]:
            pk = row[tname][pkey]
        else:
            pk = None

        frow = Storage()
        for field in fields:
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
            if value is None:
                if field != self.fact:
                    value = "__NONE__"
            frow[field] = value

            # Add entry to the fact map (fmap)
            if field == self.fact and pk:
                fmap[str(pk)] = value

        # Add the primary key to the row
        frow[pkey] = pk

        return frow

    # -------------------------------------------------------------------------
    def __expand(self, row, field=None):
        """
            Helper method to expand a single row for multiple list:type values

            @param row: the row
            @param field: the field to expand for

            @todo: optimize inner loops
        """

        if field is None:
            rows = [row]
            for field in row:
                rows = self.__expand(rows, field=field)
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
    def _create_form(self):
        """
            @todo: docstring
            @todo: move into HTML helper class?
            @todo: improve element IDs
            @todo: add JS logic to remove options which have been selected
                   in another SELECT
            @todo: add RESET-link
            @todo: action buttons instead of action links?
        """

        T = current.T
        resource = self.resource

        # Get list_fields
        list_fields = self._config("list_fields")
        if not list_fields:
            list_fields = [f.name for f in resource.readable_fields()]

        analyze_rows = self._config("analyze_rows", list_fields)
        analyze_cols = self._config("analyze_cols", list_fields)
        analyze_fact = self._config("analyze_fact", list_fields)

        select_rows = self._select_field(analyze_rows, _id="rows", _name="rows")
        select_cols = self._select_field(analyze_cols, _id="cols", _name="cols")
        select_fact = self._select_field(analyze_fact, _id="fact", _name="fact")

        methods = self._config("analyze_method")
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
                        TD(LABEL("Fact:"), _class="w2p_fl"),
                        TD(LABEL("Aggregation Method:"), _class="w2p_fl")
                    ),
                    TR(
                        TD(select_fact),
                        TD(select_method)
                    ),
                    TR(
                        INPUT(_value=T("Submit"), _type="submit"),
                        # @todo: Reset-link to restore pre-defined parameters,
                        # show only if URL vars present
                        #A(T("Reset"), _class="action-lnk"),
                    _colspan=2), _id="report_options")
        form.append(report_options)

        return form

    # -------------------------------------------------------------------------
    def _build_filter_widgets(self):

        request = self.request
        resource = self.resource

        filter_widgets = self._config("analyze_filter", None)
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
            @todo: docstring
        """

        session = current.session
        response = current.response

        query = None
        errors = None

        filter_widgets = self._config("analyze_filter", None)
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
            @todo: docstring
        """

        request = current.request
        value = None
        disable = False
        if request.env.request_method == "GET":
            if "_name" in attr:
                name = attr["_name"]
                if name in request.get_vars:
                    value = request.get_vars[name]

        table = self.table
        lfields, join = self.get_list_fields(table, list_fields)

        options = [OPTION(f.label,
                          _value=f.fieldname,
                          _selected= value == f.fieldname and "selected" or None)
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
            @todo: docstring
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

        options = [OPTION(m[1], _value=m[0]) for m in methods]
        if len(options) < 2:
            options[0].update(_selected="selected")
        else:
            options.insert(0, OPTION("", _value=None))
        select = SELECT(options, **attr)
        return select

# =============================================================================

class S3ContingencyTable(TABLE):
    """
        HTML Helper to generate a contingency table

        @todo: rename class (S3PIVOTTABLE?)
    """

    # -------------------------------------------------------------------------
    def __init__(self,
                 r,
                 resource,
                 ptable,
                 rows=[],
                 cols=[],
                 fact=None,
                 lfields=None,
                 fmap=None,
                 count=None,
                 **attributes):
        """
            Constructor

            @param r: the S3Request
            @param resource: the target resource
            @param ptable: the pivoted table
            @param rows: the row names
            @param cols: the column names
            @param fact: the fact field name
            @param lfields: the list fields
            @param fmap: the id/fact map for the rows
            @param attributes: HTML attributes for the table

            @todo: optimize inner loops
            @todo: make facts inline-expandable
        """

        manager = current.manager
        T = current.T

        TOTAL = T("Total")

        if count is not None:
            gtotal = count
        elif ptable.grand_tot is not None:
            gtotal = ptable.grand_tot
        else:
            gtotal = ""

        TABLE.__init__(self, **attributes)
        self.components = []

        rnames = ptable.rnames
        cnames = ptable.cnames
        components = self.components

        ff = lfields[fact]
        tablename = resource.tablename

        # Table header --------------------------------------------------------

        def col_represent(resource, lf, value):
            if value == "__NONE__":
                value = None
            if lf.field:
                v = manager.represent(lf.field, value, strip_markup=True)
            else:
                v = value
            return str(v)

        thead = THEAD()
        if ptable.col_tots is None:
            count_cols = True
        else:
            count_cols = False
        cquery = []
        ctotal = []
        headers = []
        for i in xrange(len(cnames)):
            colhdr = None
            cn = cnames[i]
            if not count_cols:
                ctotal.append(ptable.col_tots[i])
            else:
                ctotal.append(0)
            fquery = dict()
            if isinstance(cn, list):
                header = None
                for colname, value in cn:
                    lf = lfields[colname]
                    self.__cond(resource, fquery, lf, value)

                    l = self.__get_label(tablename, lf, "analyze_cols")
                    v = col_represent(resource, lf, value)
                    h = "%s=%s" % (l, v)

                    if len(cn) == 1:
                        colhdr = l
                        header = v
                    elif header:
                        header = "%s, %s" % (header, h)
                    else:
                        header = h
                cquery.append(fquery)
            else:
                header = ""
            headers.append(TH(header))
        if len(cols):
            headers.append(TH(TOTAL, _class="totals_header rtotal"))

        if colhdr:
            _style = "border:1px solid #cccccc; font-weight:bold;"
            fflabel = self.__get_label(tablename, ff, "analyze_fact")
            row_headers = TR(TD(fflabel, _style=_style),
                             TD(colhdr, _style=_style,
                                  _colspan=str(len(cnames)+1)))
            thead.append(row_headers)

        headers = [TH(self.__get_label(tablename,
                                       lfields[f],
                                       "analyze_rows"))
                                       for f in rows] + headers
        thead.append(TR(headers))
        components.append(thead)

        # Table body ----------------------------------------------------------

        i = 0
        tbody = TBODY()
        for item in ptable:
            rheaders = rnames[i]
            if ptable.row_tots is not None:
                rtotal = ptable.row_tots[i]
            else:
                rtotal = None
            _class = i % 2 and "odd" or "even"
            tr = TR(_class=_class)
            rquery = dict()

            # Add the row headers
            for colname, value in rheaders:
                if value == "__NONE__":
                    value = None
                lf = lfields[colname]
                self.__cond(resource, rquery, lf, value)
                if lf.field:
                    v = manager.represent(lf.field, value, strip_markup=True)
                else:
                    v = value
                tr.append(TD(v))

            # Add the fact columns
            total = rtotal or 0
            for j in range(len(item)):
                value = item[j]
                if fmap:
                    if value:
                        values = value.split(",")
                    else:
                        values = []
                    count = len(values)
                    if count_cols:
                        ctotal[j] += count
                    if rtotal is None:
                        total += count
                    result = []
                    for _id in values:
                        value = fmap.get(_id, "?")
                        url = r.url(method="", id=_id, vars=dict())
                        v = self.__link(ff, value, url=url)
                        if result:
                            result.append(", ")
                        result.append(v)
                    result = DIV(result)
                    tr.append(TD(result))
                else:
                    try:
                        fquery = Storage(cquery[j])
                    except IndexError:
                        fquery = Storage()
                    fquery.update(rquery)
                    url = r.url(method="", vars=fquery)
                    represent = fmap is not None
                    v = self.__link(ff, value, url=url, represent=represent)
                    tr.append(TD(v))
            if len(cols):
                link = A(str(total), _href=r.url(method="", vars=rquery))
                tr.append(TD(link, _class="rtotal"))
            tbody.append(tr)
            i += 1

        components.append(tbody)

        # Table footer --------------------------------------------------------

        # Column totals
        i += 1
        _class = i % 2 and "odd" or "even"
        _class = "%s %s" % (_class, "totals_row")
        tr = TR(_class=_class)
        tr.append(TD(TOTAL, _class="totals_header"))
        for j in range(len(cnames)):
            try:
                fquery = cquery[j]
            except IndexError:
                fquery = Storage()
            if not len(cols):
                _ctotal = gtotal
            else:
                _ctotal = ctotal[j]
            link = A(str(_ctotal), _href=r.url(method="", vars=fquery))
            tr.append(TD(link))

        # Grand total
        if len(cols):
            link = A(str(gtotal), _href=r.url(method="", vars=dict()))
            tr.append(TD(link, _class="rtotal"))
        tfoot = TFOOT(tr)

        components.append(tfoot)

    # -------------------------------------------------------------------------
    @staticmethod
    def __cond(resource, query, lf, value):
        """
            Helper method to construct a URL query for a row/column/fact value

            @param resource: the S3Resource
            @param query: the query dict
            @param lf: the list field
            @param value: the value
        """

        if not lf.field:
            return

        fn = "%s.%s" % (resource.name, lf.fieldname)
        if lf.field and str(lf.field.type).startswith("list:") and \
           value is not None:
            fn = "%s__in" % fn
        if value is None:
            value = "NONE"
        if value:
            query[fn] = str(value)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def __get_label(tablename, lf, key):

        manager = current.manager
        model = manager.model

        get_config = lambda key, default, tablename=tablename: \
                     model.get_config(tablename, key, default)

        list_fields = get_config("list_fields", None)
        fields = get_config(key, list_fields)
        if fields:
            for f in fields:
                if isinstance(f, (tuple, list)) and f[1] == lf.fieldname:
                    return f[0]
        return lf.label

    # -------------------------------------------------------------------------
    @staticmethod
    def __link(lf, value, url=None, represent=True):
        """
            Helper method to represent a value as a link

            @param lf: the list field
            @param value: the value
            @param url: the URL
            @param represent: use field representation

            @todo: add hover-title
        """

        manager = current.manager

        if value == "__NONE__":
            value = None
        if value is None:
            v = "-"
            url = None
        elif lf.field and value != "?" and represent:
            v = manager.represent(lf.field, value, strip_markup=True)
        else:
            v = value

        if url is not None:
            return A(unicode(v), _href=url)

        return unicode(v)

# =============================================================================
