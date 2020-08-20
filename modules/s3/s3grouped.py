# -*- coding: utf-8 -*-

""" S3 Grouped Items Report Method

    @copyright: 2015-2020 (c) Sahana Software Foundation
    @license: MIT

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

__all__ = ("S3GroupedItemsReport",
           "S3GroupedItemsTable",
           "S3GroupedItems",
           "S3GroupAggregate",
           )

import json
import math

from gluon import current, DIV, H2, INPUT, SPAN, TABLE, TBODY, TD, TFOOT, TH, THEAD, TR

from s3compat import INTEGER_TYPES, basestring
from .s3rest import S3Method
from .s3utils import s3_strip_markup, s3_str

# Compact JSON encoding
SEPARATORS = (",", ":")

DEFAULT = lambda: None

# =============================================================================
class S3GroupedItemsReport(S3Method):
    """
        REST Method Handler for Grouped Items Reports

        @todo: widget method
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Page-render entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        output = {}
        if r.http == "GET":
            return self.report(r, **attr)
        else:
            r.error(405, current.ERROR.BAD_METHOD)
        return output

    # -------------------------------------------------------------------------
    def widget(self, r, method=None, widget_id=None, visible=True, **attr):
        """
            Summary widget method

            @param r: the S3Request
            @param method: the widget method
            @param widget_id: the widget ID
            @param visible: whether the widget is initially visible
            @param attr: controller attributes
        """

        output = {}
        if r.http == "GET":
            r.error(501, current.ERROR.NOT_IMPLEMENTED)
        else:
            r.error(405, current.ERROR.BAD_METHOD)
        return output

    # -------------------------------------------------------------------------
    def report(self, r, **attr):
        """
            Report generator

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        T = current.T
        output = {}

        resource = self.resource
        tablename = resource.tablename

        get_config = resource.get_config

        representation = r.representation

        # Apply filter defaults before rendering the data
        show_filter_form = False
        if representation in ("html", "iframe"):
            filter_widgets = get_config("filter_widgets", None)
            if filter_widgets and not self.hide_filter:
                show_filter_form = True
                from .s3filter import S3FilterForm
                S3FilterForm.apply_filter_defaults(r, resource)

        # Get the report configuration
        report_config = self.get_report_config()

        # Resolve selectors in the report configuration
        fields = self.resolve(report_config)

        # Get extraction method
        extract = report_config.get("extract")
        if not callable(extract):
            extract = self.extract

        selectors = [s for s in fields if fields[s] is not None]
        orderby = report_config.get("orderby_cols")

        # Extract the data
        items = extract(self.resource, selectors, orderby)

        # Group and aggregate
        groupby = report_config.get("groupby_cols")
        aggregate = report_config.get("aggregate_cols")

        gi = S3GroupedItems(items, groupby=groupby, aggregate=aggregate)

        # Report title
        title = report_config.get("title")
        if title is None:
            title = self.crud_string(tablename, "title_report")

        # Generate JSON data
        display_cols = report_config.get("display_cols")
        labels = report_config.get("labels")
        represent = report_config.get("groupby_represent")

        if representation in ("pdf", "xls"):
            as_dict = True
        else:
            as_dict = False

        data = gi.json(fields = display_cols,
                       labels = labels,
                       represent = represent,
                       as_dict = as_dict,
                       )

        group_headers = report_config.get("group_headers", False)

        # Widget ID
        widget_id = "groupeditems"

        # Render output
        if representation in ("html", "iframe"):
            # Page load
            output["report_type"] = "groupeditems"
            output["widget_id"] = widget_id
            output["title"] = title

            # Filter form
            if show_filter_form:

                settings = current.deployment_settings

                # Filter form options
                filter_formstyle = get_config("filter_formstyle", None)
                filter_clear = get_config("filter_clear",
                                          settings.get_ui_filter_clear())
                filter_submit = get_config("filter_submit", True)

                # Instantiate form
                filter_form = S3FilterForm(filter_widgets,
                                           formstyle = filter_formstyle,
                                           submit = filter_submit,
                                           clear = filter_clear,
                                           ajax = True,
                                           _class = "filter-form",
                                           _id = "%s-filter-form" % widget_id,
                                           )

                # Render against unfiltered resource
                fresource = current.s3db.resource(tablename)
                alias = resource.alias if resource.parent else None
                output["filter_form"] = filter_form.html(fresource,
                                                         r.get_vars,
                                                         target = widget_id,
                                                         alias = alias
                                                         )

            # Inject data
            items = INPUT(_type = "hidden",
                          _id = "%s-data" % widget_id,
                          _class = "gi-data",
                          _value = data,
                          )
            output["items"] = items

            # Empty section
            output["empty"] = T("No data available")

            # Export formats
            output["formats"] = self.export_links(r)

            # Script options
            ajaxurl = attr.get("ajaxurl", r.url(method = "grouped",
                                                representation = "json",
                                                vars = r.get_vars,
                                                ))
            totals_label = report_config.get("totals_label", T("Total"))

            options = {"ajaxURL": ajaxurl,
                       "totalsLabel": str(totals_label).upper(),
                       "renderGroupHeaders": group_headers,
                       }

            # Inject script
            self.inject_script(widget_id, options=options)

            # Detect and store theme-specific inner layout
            self._view(r, "grouped.html")

            # View
            response = current.response
            response.view = self._view(r, "report.html")

        elif representation == "json":
            # Ajax reload
            output = data

        elif representation == "pdf":
            # PDF Export
            totals_label = report_config.get("totals_label", T("Total"))
            pdf_header = report_config.get("pdf_header", DEFAULT)
            gi_table = S3GroupedItemsTable(resource,
                                           title = title,
                                           data = data,
                                           group_headers = group_headers,
                                           totals_label = totals_label,
                                           pdf_header = pdf_header,
                                           )
            return gi_table.pdf(r)

        elif representation == "xls":
            # XLS Export
            field_types = report_config.get("ftypes")
            totals_label = report_config.get("totals_label", T("Total"))
            gi_table = S3GroupedItemsTable(resource,
                                           title = title,
                                           data = data,
                                           field_types = field_types,
                                           aggregate = aggregate,
                                           group_headers = group_headers,
                                           totals_label = totals_label,
                                           )
            return gi_table.xls(r)

        else:
            r.error(415, current.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def get_report_config(self):
        """
            Get the configuration for the requested report, updated
            with URL options
        """

        r = self.request
        get_vars = r.get_vars

        # Get the resource configuration
        config = self.resource.get_config("grouped")
        if not config:
            # No reports implemented for this resource
            r.error(405, current.ERROR.NOT_IMPLEMENTED)

        # Which report?
        report = get_vars.get("report", "default")
        if isinstance(report, list):
            report = report[-1]

        # Get the report config
        report_config = config.get(report)
        if not report_config:
            # This report is not implemented
            r.error(405, current.ERROR.NOT_IMPLEMENTED)
        else:
            report_config = dict(report_config)

        # Orderby
        orderby = get_vars.get("orderby")
        if isinstance(orderby, list):
            orderby = ",".join(orderby).split(",")
        if not orderby:
            orderby = report_config.get("orderby")
        if not orderby:
            orderby = report_config.get("groupby")
        report_config["orderby"] = orderby

        return report_config

    # -------------------------------------------------------------------------
    def resolve(self, report_config):
        """
            Get all field selectors for the report, and resolve them
            against the resource

            @param resource: the resource
            @param config: the report config (will be updated)

            @return: a dict {selector: rfield}, where rfield can be None
                     if the selector does not resolve against the resource
        """

        resource = self.resource

        # Get selectors for visible fields
        fields = report_config.get("fields")
        if not fields:
            # Fall back to list_fields
            selectors = resource.list_fields("grouped_fields")
            fields = list(selectors)
        else:
            selectors = list(fields)

        # Get selectors for grouping axes
        groupby = report_config.get("groupby")
        if isinstance(groupby, (list, tuple)):
            selectors.extend(groupby)
        elif groupby:
            selectors.append(groupby)

        # Get selectors for aggregation
        aggregate = report_config.get("aggregate")
        if aggregate:
            for method, selector in aggregate:
                selectors.append(selector)
        else:
            report_config["group_headers"] = True

        # Get selectors for orderby
        orderby = report_config.get("orderby")
        if orderby:
            for selector in orderby:
                s, d = ("%s asc" % selector).split(" ")[:2]
            selectors.append(s)

        # Resolve all selectors against the resource,
        # collect S3ResourceFields, labels and field types
        rfields = {}
        labels = {}
        ftypes = {}
        id_field = str(resource._id)
        for f in selectors:
            label, selector = f if type(f) is tuple else (None, f)
            if selector in rfields:
                # Already resolved
                continue
            try:
                rfield = resource.resolve_selector(selector)
            except (SyntaxError, AttributeError):
                rfield = None
            if label and rfield:
                rfield.label = label
            if id_field and rfield and rfield.colname == id_field:
                id_field = None
            rfields[selector] = rfield
            if rfield:
                labels[rfield.colname] = rfield.label
                ftypes[rfield.colname] = rfield.ftype
            elif label:
                labels[selector] = label
                ftypes[selector] = "virtual"
        report_config["labels"] = labels
        report_config["ftypes"] = ftypes

        # Make sure id field is always included
        if id_field:
            id_name = resource._id.name
            rfields[id_name] = resource.resolve_selector(id_name)

        # Get column names for vsibile fields
        display_cols = []
        for f in fields:
            label, selector = f if type(f) is tuple else (None, f)
            rfield = rfields.get(selector)
            colname = rfield.colname if rfield else selector
            if colname:
                display_cols.append(colname)
        report_config["display_cols"] = display_cols

        # Get column names for orderby
        orderby_cols = []
        orderby = report_config.get("orderby")
        if orderby:
            for selector in orderby:
                s, d = ("%s asc" % selector).split(" ")[:2]
                rfield = rfields.get(s)
                colname = rfield.colname if rfield else None
                if colname:
                    orderby_cols.append("%s %s" % (colname, d))
        if not orderby_cols:
            orderby_cols = None
        report_config["orderby_cols"] = orderby_cols

        # Get column names for grouping
        groupby_cols = []
        groupby_represent = {}
        groupby = report_config.get("groupby")
        if groupby:
            for selector in groupby:
                rfield = rfields.get(selector)
                if rfield:
                    colname = rfield.colname
                    field = rfield.field
                    if field:
                        groupby_represent[colname] = field.represent
                else:
                    colname = selector
                groupby_cols.append(colname)
        report_config["groupby_cols"] = groupby_cols
        report_config["groupby_represent"] = groupby_represent

        # Get columns names for aggregation
        aggregate_cols = []
        aggregate = report_config.get("aggregate")
        if aggregate:
            for method, selector in aggregate:
                rfield = rfields.get(selector)
                colname = rfield.colname if rfield else selector
                aggregate_cols.append((method, colname))
        report_config["aggregate_cols"] = aggregate_cols

        return rfields

    # -------------------------------------------------------------------------
    @staticmethod
    def extract(resource, selectors, orderby):
        """
            Extract the data from the resource (default method, can be
            overridden in report config)

            @param resource: the resource
            @param selectors: the field selectors

            @returns: list of dicts {colname: value} including
                      raw data (_row)
        """

        data = resource.select(selectors,
                               limit = None,
                               orderby = orderby,
                               raw_data = True,
                               represent = True,
                               )
        return data.rows

    # -------------------------------------------------------------------------
    @staticmethod
    def export_links(r):
        """
            Render export links for the report

            @param r: the S3Request
        """

        T = current.T

        formats = DIV(DIV(_title = T("Export as PDF"),
                          _class = "gi-export export_pdf",
                          data = {"url": r.url(method = "grouped",
                                               representation = "pdf",
                                               vars = r.get_vars,
                                               ),
                                  },
                          ),
                      DIV(_title = T("Export as XLS"),
                          _class = "gi-export export_xls",
                          data = {"url": r.url(method = "grouped",
                                               representation = "xls",
                                               vars = r.get_vars,
                                               ),
                                  },
                          ),
                      _class = "gi-export-formats",
                      )

        return formats

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_script(widget_id, options=None):
        """
            Inject the groupedItems script and bind it to the container

            @param widget_id: the widget container DOM ID
            @param options: dict with options for the widget

            @note: options dict must be JSON-serializable
        """

        s3 = current.response.s3

        scripts = s3.scripts
        appname = current.request.application

        # Inject UI widget script
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.ui.groupeditems.js" % appname
            if script not in scripts:
                scripts.append(script)
        else:
            script = "/%s/static/scripts/S3/s3.groupeditems.min.js" % appname
            if script not in scripts:
                scripts.append(script)

        # Inject widget instantiation
        if not options:
            options = {}
        script = """$("#%(widget_id)s").groupedItems(%(options)s)""" % \
                    {"widget_id": widget_id,
                     "options": json.dumps(options),
                     }
        s3.jquery_ready.append(script)

# =============================================================================
class S3GroupedItemsTable(object):
    """
        Helper class to render representations of a grouped items report
    """

    def __init__(self,
                 resource,
                 title = None,
                 data = None,
                 aggregate = None,
                 field_types = None,
                 group_headers = False,
                 totals_label = None,
                 pdf_header = DEFAULT,
                 pdf_footer = None,
                 ):
        """
            Constructor

            @param resource: the resource
            @param title: the report title
            @param data: the JSON data (as dict)
            @param aggregate: the aggregation functions as list of tuples
                              (method, colname)
            @param field_types: the field types as dict {colname: type}
            @param group_headers: render group header rows
            @param totals_label: the label for the aggregated rows
                                 (default: "Total")
            @param pdf_header: callable or static HTML to use as
                               document header, function(r, title=title)
            @param pdf_footer: callable or static HTML to use as
                               document footer, function(r)
        """

        self.resource = resource
        self.title = title
        self.data = data

        self.aggregate = aggregate
        self.field_types = field_types

        self.totals_label = totals_label
        self.group_headers = group_headers

        if pdf_header is DEFAULT:
            self.pdf_header = self._pdf_header
        else:
            self.pdf_header = pdf_header

        self.pdf_footer = pdf_footer

    # -------------------------------------------------------------------------
    def html(self):
        """
            Produce a HTML representation of the grouped table

            @return: a TABLE instance
        """

        table = TABLE()

        self.html_render_table_header(table)

        tbody = TBODY()
        self.html_render_group(tbody, self.data)
        table.append(tbody)

        self.html_render_table_footer(table)

        return table

    # -------------------------------------------------------------------------
    def pdf(self, r, filename=None):
        """
            Produce a PDF representation of the grouped table

            @param r: the S3Request
            @return: the PDF document
        """

        # Styles for totals and group totals rows
        styles = {"tr.gi-column-totals": {
                        "background-color": "black",
                        "color": "white",
                        },
                  "tr.gi-group-footer.gi-level-1": {
                        "background-color": "lightgrey",
                        },
                  "tr.gi-group-header.gi-level-1": {
                        "background-color": "lightgrey",
                        },
                  }

        title = self.title

        pdf_header = self.pdf_header
        if callable(pdf_header):
            pdf_header = lambda r, title=title: self.pdf_header(r, title=title)

        pdf_footer = self.pdf_footer

        from .s3export import S3Exporter
        exporter = S3Exporter().pdf
        return exporter(self.resource,
                        request = r,
                        pdf_title = title,
                        pdf_header = pdf_header,
                        pdf_header_padding = 12,
                        pdf_footer = pdf_footer,
                        pdf_callback = lambda r: self.html(),
                        pdf_table_autogrow = "B",
                        pdf_orientation = "Landscape",
                        pdf_html_styles = styles,
                        pdf_filename = filename,
                        )

    # -------------------------------------------------------------------------
    def xls(self, r, filename=None):
        """
            Produce an XLS sheet of the grouped table

            @param r: the S3Request
            @return: the XLS document
        """

        # Prepare the XLS data array
        field_types = self.field_types

        data = self.data
        columns = data.get("c")
        labels = data.get("l")

        aggregate = self.aggregate
        if aggregate:
            functions = dict((c, m) for m, c in aggregate)
        else:
            functions = {}

        # Get column headers and field types
        types = {}
        for column in columns:

            # For virtual fields with numeric aggregation, designate
            # the field type as "double":
            field_type = field_types.get(column, "virtual")
            if field_type == "virtual":
                method = functions.get(column)
                if method and method != "count":
                    field_type = "double"
            types[column] = field_type

        # Append the rows
        rows = []
        self.xls_group_data(rows, data)

        # Footer row
        self.xls_table_footer(rows)

        xlsdata = {"columns": columns,
                   "headers": labels,
                   "types": types,
                   "rows": rows,
                   }

        # Export as XLS
        from .s3export import S3Exporter
        exporter = S3Exporter().xls
        return exporter(xlsdata,
                        title = self.title,
                        use_colour = True,
                        evenodd = False,
                        )

    # -------------------------------------------------------------------------
    def xls_group_data(self, rows, group, level=0):
        """
            Append a group to the XLS data

            @param rows: the XLS rows array to append to
            @param group: the group dict
            @param level: the grouping level
        """

        subgroups = group.get("d")
        items = group.get("i")

        if self.group_headers and level > 0:
            self.xls_group_header(rows, group, level=level)

        if subgroups:
            for subgroup in subgroups:
                self.xls_group_data(rows, subgroup, level = level + 1)
        elif items:
            for item in items:
                self.xls_item_data(rows, item, level = level)

        if level > 0:
            self.xls_group_footer(rows, group, level=level)

    # -------------------------------------------------------------------------
    def xls_group_header(self, rows, group, level=0):
        """
            Render the group header (=group label)

            @param row: the XLS rows array to append to
            @param group: the group dict
            @param level: the grouping level
        """

        columns = self.data.get("c")
        value = group.get("v")

        if not value:
            value = ""
        row = {"_group": {"label": s3_str(s3_strip_markup(value)),
                          "span": len(columns),
                          "totals": False,
                          },
               "_style": "subheader",
               }
        rows.append(row)

    # -------------------------------------------------------------------------
    def xls_group_footer(self, rows, group, level=0):
        """
            Append a group footer to the XLS data

            @param rows: the XLS rows array to append to
            @param group: the group dict
            @param level: the grouping level
        """

        columns = self.data.get("c")
        totals = group.get("t")

        if self.group_headers:
            value = self.totals_label
        else:
            v = group.get("v")
            value = "%s %s" % (s3_str(s3_strip_markup(v)),
                               self.totals_label,
                               )
        row = {}

        span = 0
        has_totals = False

        if not totals:
            if self.group_headers:
                return
            label = value
        elif columns:
            label = None
            for column in columns:
                has_value = column in totals
                if label is None:
                    if not has_value:
                        span += 1
                        continue
                    else:
                        label = value
                has_totals = True
                row[column] = totals[column] if has_value else ""

        row["_group"] = {"label": label,
                         "span": span,
                         "totals": has_totals,
                         }
        row["_style"] = "subtotals"
        rows.append(row)

    # -------------------------------------------------------------------------
    def xls_table_footer(self, rows):
        """
            Render the table footer

            @param table: the TABLE instance
        """

        data = self.data
        columns = data.get("c")
        totals = data.get("t")

        if not totals:
            return

        row = {}
        if columns:
            label = None
            span = 0
            for column in columns:
                has_value = column in totals
                if label is None:
                    if not has_value:
                        span += 1
                        continue
                    else:
                        label = self.totals_label
                row[column] = totals[column] if has_value else ""

        row["_group"] = {"label": label,
                         "span": span,
                         "totals": True,
                         }
        row["_style"] = "totals"
        rows.append(row)

    # -------------------------------------------------------------------------
    def xls_item_data(self, rows, item, level=0):
        """
            Append an item to the XLS data

            @param rows: the XLS rows array to append to
            @param item: the item dict
            @param level: the grouping level
        """

        columns = self.data["c"]
        cells = {}

        for column in columns:
            cells[column] = item.get(column)

        rows.append(cells)

    # -------------------------------------------------------------------------
    def html_render_table_header(self, table):
        """
            Render the table header

            @param table: the TABLE instance
        """

        data = self.data

        columns = data.get("c")
        labels = data.get("l")

        header_row = TR(_class="gi-column-headers")
        if columns:
            for column in columns:
                label = labels.get(column, column)
                header_row.append(TH(label))
        table.append(THEAD(header_row))

    # -------------------------------------------------------------------------
    def html_render_table_footer(self, table):
        """
            Render the table footer

            @param table: the TABLE instance
        """

        data = self.data

        columns = data.get("c")
        totals = data.get("t")

        if not totals:
            return

        footer_row = TR(_class = "gi-column-totals")
        if columns:
            label = None
            span = 0
            for column in columns:
                has_value = column in totals
                if label is None:
                    if not has_value:
                        span += 1
                        continue
                    else:
                        label = TD(SPAN(self.totals_label),
                                   _class = "gi-column-totals-label",
                                   _colspan = span,
                                   )
                        footer_row.append(label)
                value = totals[column] if has_value else ""
                footer_row.append(TD(value))
        table.append(TFOOT(footer_row))

    # -------------------------------------------------------------------------
    def html_render_group(self, tbody, group, level=0):
        """
            Render a group of rows

            @param tbody: the TBODY or TABLE to append to
            @param group: the group dict
            @param level: the grouping level
        """

        if self.group_headers and level > 0:
            self.html_render_group_header(tbody, group, level=level)

        subgroups = group.get("d")
        items = group.get("i")

        if subgroups:
            for subgroup in subgroups:
                self.html_render_group(tbody, subgroup,
                                       level = level + 1,
                                       )
        elif items:
            for item in items:
                self.html_render_item(tbody, item, level=level)

        if level > 0:
            self.html_render_group_footer(tbody, group, level=level)

    # -------------------------------------------------------------------------
    def html_render_group_header(self, tbody, group, level=0):
        """
            Render the group header (=group label)

            @param tbody: the TBODY or TABLE to append to
            @param group: the group dict
            @param level: the grouping level
        """

        data = self.data

        columns = data.get("c")
        value = group.get("v")

        if not value:
            value = ""
        header = TD(s3_str(s3_strip_markup(value)),
                    _colspan = len(columns) if columns else None,
                    )

        tbody.append(TR(header,
                        _class = "gi-group-header gi-level-%s" % level,
                        ))

    # -------------------------------------------------------------------------
    def html_render_group_footer(self, tbody, group, level=0):
        """
            Render the group footer (=group totals)

            @param tbody: the TBODY or TABLE to append to
            @param group: the group dict
            @param level: the grouping level
        """

        columns = self.data.get("c")
        totals = group.get("t")

        if self.group_headers:
            value = self.totals_label
        else:
            v = group.get("v")
            value = "%s %s" % (s3_str(s3_strip_markup(v)),
                               self.totals_label,
                               )

        footer_row = TR(_class="gi-group-footer gi-level-%s" % level)
        if not totals:
            if not self.group_headers:
                footer_row.append(TD(value, _colspan = len(columns)))
                tbody.append(footer_row)
            return

        if columns:
            label = None
            span = 0
            for column in columns:
                has_value = column in totals
                if label is None:
                    if not has_value:
                        span += 1
                        continue
                    else:
                        label = TD(value,
                                   _class = "gi-group-footer-label",
                                   _colspan = span,
                                   )
                        footer_row.append(label)
                total = totals[column] if has_value else ""
                footer_row.append(TD(total))

        tbody.append(footer_row)

    # -------------------------------------------------------------------------
    def html_render_item(self, tbody, item, level=0):
        """
            Render an item

            @param tbody: the TBODY or TABLE to append to
            @param item: the item dict
            @param level: the grouping level
        """

        columns = self.data["c"]
        cells = []

        for column in columns:
            cells.append(TD(item.get(column, "")))
        tbody.append(TR(cells, _class="gi-item gi-level-%s" % level))

    # -------------------------------------------------------------------------
    @staticmethod
    def _pdf_header(r, title=None):
        """
            Default PDF header (report title as H2)
        """

        return H2(title)

# =============================================================================
class S3GroupedItems(object):
    """
        Helper class representing dict-like items grouped by
        attribute values, used by S3GroupedItemsReport
    """

    def __init__(self, items, groupby=None, aggregate=None, values=None):
        """
            Constructor

            @param items: ordered iterable of items (e.g. list, tuple,
                          iterator, Rows), grouping tries to maintain
                          the original item order
            @param groupby: attribute key or ordered iterable of
                            attribute keys (e.g. list, tuple, iterator)
                            for the items to be grouped by; grouping
                            happens in order of appearance of the keys
            @param aggregate: aggregates to compute, list of tuples
                              (method, key)
            @param value: the grouping values for this group (internal)
        """

        self._groups_dict = {}
        self._groups_list = []

        self.values = values or {}

        self._aggregates = {}

        if groupby:
            if isinstance(groupby, basestring):
                # Single grouping key
                groupby = [groupby]
            else:
                groupby = list(groupby)

            self.key = groupby.pop(0)
            self.groupby = groupby
            self.items = None
            for item in items:
                self.add(item)
        else:
            self.key = None
            self.groupby = None
            self.items = list(items)

        if aggregate:
            if type(aggregate) is tuple:
                aggregate = [aggregate]
            for method, key in aggregate:
                self.aggregate(method, key)

    # -------------------------------------------------------------------------
    @property
    def groups(self):
        """ Generator for iteration over subgroups """

        groups = self._groups_dict
        for value in self._groups_list:
            yield groups.get(value)

    # -------------------------------------------------------------------------
    def __getitem__(self, key):
        """
            Getter for the grouping values dict

            @param key: the grouping key

        """

        if type(key) is tuple:
            return self.aggregate(key[0], key[1]).result
        else:
            return self.values.get(key)

    # -------------------------------------------------------------------------
    def add(self, item):
        """
            Add a new item, either to this group or to a subgroup

            @param item: the item
        """

        # Remove all aggregates
        if self._aggregates:
            self._aggregates = {}

        key = self.key
        if key:

            raw = item.get("_row")
            if raw is None:
                value = item.get(key)
            else:
                # Prefer raw values for grouping over representations
                try:
                    value = raw.get(key)
                except (AttributeError, TypeError):
                    # _row is not a dict
                    value = item.get(key)

            if type(value) is list:
                # list:type => item belongs into multiple groups
                add_to_group = self.add_to_group
                for v in value:
                    add_to_group(key, v, item)
            else:
                self.add_to_group(key, value, item)
        else:
            # No subgroups
            self.items.append(item)

    # -------------------------------------------------------------------------
    def add_to_group(self, key, value, item):
        """
            Add an item to a subgroup. Create that subgroup if it does not
            yet exist.

            @param key: the grouping key
            @param value: the grouping value for the subgroup
            @param item: the item to add to the subgroup
        """

        groups = self._groups_dict
        if value in groups:
            group = groups[value]
            group.add(item)
        else:
            values = dict(self.values)
            values[key] = value
            group = S3GroupedItems([item],
                                   groupby = self.groupby,
                                   values = values,
                                   )
            groups[value] = group
            self._groups_list.append(value)
        return group

    # -------------------------------------------------------------------------
    def get_values(self, key):
        """
            Get a list of attribute values for the items in this group

            @param key: the attribute key
            @return: the list of values
        """

        if self.items is None:
            return None

        values = []
        append = values.append
        extend = values.extend

        for item in self.items:

            raw = item.get("_row")
            if raw is None:
                # Prefer raw values for aggregation over representations
                value = item.get(key)
            else:
                try:
                    value = raw.get(key)
                except (AttributeError, TypeError):
                    # _row is not a dict
                    value = item.get(key)

            if type(value) is list:
                extend(value)
            else:
                append(value)
        return values

    # -------------------------------------------------------------------------
    def aggregate(self, method, key):
        """
            Aggregate item attribute values (recursively over subgroups)

            @param method: the aggregation method
            @param key: the attribute key

            @return: an S3GroupAggregate instance
        """

        aggregates = self._aggregates
        if (method, key) in aggregates:
            # Already computed
            return aggregates[(method, key)]

        if self.items is not None:
            # No subgroups => aggregate values in this group
            values = self.get_values(key)
            aggregate = S3GroupAggregate(method, key, values)
        else:
            # Aggregate recursively over subgroups
            combine = S3GroupAggregate.aggregate
            aggregate = combine(group.aggregate(method, key)
                                    for group in self.groups)

        # Store aggregate
        aggregates[(method, key)] = aggregate

        return aggregate

    # -------------------------------------------------------------------------
    def __repr__(self):
        """ Represent this group and all its subgroups as string """

        return self.__represent()

    # -------------------------------------------------------------------------
    def __represent(self, level=0):
        """
            Represent this group and all its subgroups as string

            @param level: the hierarchy level of this group (for indentation)
        """

        output = ""
        indent = " " * level

        aggregates = self._aggregates
        for aggregate in aggregates.values():
            output = "%s\n%s  %s(%s) = %s" % (output,
                                              indent,
                                              aggregate.method,
                                              aggregate.key,
                                              aggregate.result,
                                              )
        if aggregates:
            output = "%s\n" % output

        key = self.key
        if key:
            for group in self.groups:
                value = group[key]
                if group:
                    group_repr = group.__represent(level = level+1)
                else:
                    group_repr = "[empty group]"
                output = "%s\n%s=> %s: %s\n%s" % \
                         (output, indent, key, value, group_repr)
        else:
            for item in self.items:
                output = "%s\n%s  %s" % (output, indent, item)
            output = "%s\n" % output

        return output

    # -------------------------------------------------------------------------
    def json(self,
             fields = None,
             labels = None,
             represent = None,
             as_dict = False,
             master = True
             ):
        """
            Serialize this group as JSON

            @param fields: the columns to include for each item
            @param labels: columns labels as dict {key: label},
                           including the labels for grouping axes
            @param represent: dict of representation methods for grouping
                              axis values {colname: function}
            @param as_dict: return output as dict rather than JSON string
            @param master: this is the top-level group (internal)

            JSON Format:

            {"c": [key, ...],          ....... list of keys for visible columns
             "g": [key, ...],          ....... list of keys for grouping axes
             "l": [(key, label), ...], ....... list of key-label pairs
             "k": key,                 ....... grouping key for subgroups
             "d": [                    ....... list of sub-groups
                 {"v": string,         ....... the grouping value for this subgroup (represented)
                  "k": key             ....... the grouping key for subgroups
                  "d": [...]           ....... list of subgroups (nested)
                  "i": [               ....... list of items in this group
                       {key: value,    ....... key-value pairs for visible columns
                       }, ...
                  ],
                  "t": {               ....... list of group totals
                      key: value,      ....... key-value pairs for totals
                  }
                 }, ...
                ],
            "i": [...],                ....... list of items (if no grouping)
            "t": [...],                ....... list of grand totals
            "e": boolean               ....... empty-flag
            }
        """

        T = current.T

        output = {}

        if not fields:
            raise SyntaxError

        if master:
            # Add columns and grouping information to top level group
            if labels is None:
                labels = {}

            def check_label(colname):
                if colname in labels:
                    label = labels[colname] or ""
                else:
                    fname = colname.split(".", 1)[-1]
                    label = " ".join([s.strip().capitalize()
                                    for s in fname.split("_") if s])
                    label = labels[colname] = T(label)
                return str(label)

            grouping = []
            groupby = self.groupby
            if groupby:
                for axis in groupby:
                    check_label(axis)
                    grouping.append(axis)
            output["g"] = grouping

            columns = []
            for colname in fields:
                check_label(colname)
                columns.append(colname)
            output["c"] = columns

            output["l"] = {c: str(l) for c, l in labels.items()}

        key = self.key
        if key:
            output["k"] = key

            representations = None
            renderer = represent.get(key) if represent else None

            # Bulk represent?
            if renderer and hasattr(renderer, "bulk"):
                values = [group[key] for group in self.groups]
                representations = renderer.bulk(values)

            data = []
            add_group = data.append
            for group in self.groups:
                # Render subgroup
                gdict = group.json(fields, labels,
                                   represent = represent,
                                   as_dict = True,
                                   master = False,
                                   )

                # Add subgroup attribute value
                value = group[key]
                if representations is not None:
                    value = representations.get(value)
                elif renderer is not None:
                    value = renderer(value)
                gdict["v"] = s3_str(value)
                add_group(gdict)

            if master:
                output["e"] = len(data) == 0
            output["d"] = data
            output["i"] = None

        else:
            oitems = []
            add_item = oitems.append
            for item in self.items:
                # Render item
                oitem = {}
                for colname in fields:
                    if colname in item:
                        value = item[colname] or ""
                    else:
                        # Fall back to raw value
                        raw = item.get("_row")
                        try:
                            value = raw.get(colname)
                        except (AttributeError, TypeError):
                            # _row is not a dict
                            value = None
                    if value is None:
                        value = ""
                    else:
                        value = s3_str(value)
                    oitem[colname] = value
                add_item(oitem)

            if master:
                output["e"] = len(oitems) == 0
            output["d"] = None
            output["i"] = oitems

        # Render group totals
        aggregates = self._aggregates
        totals = {}
        for k, a in aggregates.items():
            method = k[0]
            # @todo: call represent for totals
            totals[colname] = s3_str(a.result)
        output["t"] = totals

        # Convert to JSON unless requested otherwise
        if master and not as_dict:
            output = json.dumps(output, separators=SEPARATORS)
        return output

# =============================================================================
class S3GroupAggregate(object):
    """ Class representing aggregated values """

    def __init__(self, method, key, values):
        """
            Constructor

            @param method: the aggregation method (count, sum, min, max, avg)
            @param key: the attribute key
            @param values: the attribute values
        """

        self.method = method
        self.key = key

        self.values = values
        self.result = self.__compute(method, values)

    # -------------------------------------------------------------------------
    def __compute(self, method, values):
        """
            Compute the aggregated value

            @param method: the aggregation method
            @param values: the values

            @return: the aggregated value
        """

        result = None

        if values is not None:
            try:
                values = [v for v in values if v is not None]
            except TypeError:
                result = None
            else:
                if method == "count":
                    result = len(set(values))
                else:
                    values = [v for v in values
                              if isinstance(v, INTEGER_TYPES + (float,))]
                if method == "sum":
                    try:
                        result = math.fsum(values)
                    except (TypeError, ValueError):
                        result = None
                elif method == "min":
                    try:
                        result = min(values)
                    except (TypeError, ValueError):
                        result = None
                elif method == "max":
                    try:
                        result = max(values)
                    except (TypeError, ValueError):
                        result = None
                elif method == "avg":
                    num = len(values)
                    if num:
                        try:
                            result = sum(values) / float(num)
                        except (TypeError, ValueError):
                            result = None
                    else:
                        result = None
        return result

    # -------------------------------------------------------------------------
    @classmethod
    def aggregate(cls, items):
        """
            Combine sub-aggregates

            @param items: iterable of sub-aggregates

            @return: an S3GroupAggregate instance
        """

        method = None
        key = None
        values = []

        for item in items:

            if method is None:
                method = item.method
                key = item.key

            elif key != item.key or method != item.method:
                raise TypeError

            if item.values:
                values.extend(item.values)

        return cls(method, key, values)

# END =========================================================================
