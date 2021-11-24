# -*- coding: utf-8 -*-

""" S3 TimePlot Report Method and Time Series Toolkit

    @copyright: 2013-2021 (c) Sahana Software Foundation
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

__all__ = ("S3TimePlot",
           #"S3TimePlotForm",
           "S3TimeSeries",
           #"S3TimeSeriesEvent",
           #"S3TimeSeriesEventFrame",
           #"S3TimeSeriesFact",
           #"S3TimeSeriesPeriod",
           )

import datetime
import dateutil.tz
import json
import re
import sys

from dateutil.relativedelta import relativedelta
from dateutil.rrule import DAILY, HOURLY, MONTHLY, WEEKLY, YEARLY, rrule

from gluon import current
from gluon.storage import Storage
from gluon.html import DIV, FORM, INPUT, LABEL, SPAN, TAG, XML
from gluon.validators import IS_IN_SET
from gluon.sqlhtml import OptionsWidget, SQLFORM

from .s3datetime import s3_decode_iso_datetime, s3_utc
from .s3rest import S3Method
from .s3query import FS
from .s3report import S3Report, S3ReportForm
from .s3utils import s3_flatlist, s3_represent_value, s3_str, S3MarkupStripper

tp_datetime = lambda year, *t: datetime.datetime(year, *t, tzinfo=dateutil.tz.tzutc())

tp_tzsafe = lambda dt: dt.replace(tzinfo = dateutil.tz.tzutc()) \
                       if dt and dt.tzinfo is None else dt

# Compact JSON encoding
SEPARATORS = (",", ":")

DEFAULT = lambda: None
NUMERIC_TYPES = ("integer", "double", "id")

dt_regex = Storage(
    YEAR = re.compile(r"\A\s*(\d{4})\s*\Z"),
    YEAR_MONTH = re.compile(r"\A\s*(\d{4})-([0]*[1-9]|[1][12])\s*\Z"),
    MONTH_YEAR = re.compile(r"\A\s*([0]*[1-9]|[1][12])/(\d{4})\s*\Z"),
    DATE = re.compile(r"\A\s*(\d{4})-([0]?[1-9]|[1][12])-([012]?[1-9]|[3][01])\s*\Z"),
    DELTA = re.compile(r"\A\s*([<>]?)([+-]?)\s*(\d+)\s*([ymwdh])\w*\s*\Z"),
)

FACT = re.compile(r"([a-zA-Z]+)\(([a-zA-Z0-9_.$:\,~]+)\),*(.*)\Z")
SELECTOR = re.compile(r"^[a-zA-Z0-9_.$:\~]+\Z")

# =============================================================================
class S3TimePlot(S3Method):
    """ RESTful method for time plot reports """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Page-render entry point for REST interface.

            Args:
                r: the CRUDRequest instance
                attr: controller attributes for the request
        """

        if r.http == "GET":
            output = self.timeplot(r, **attr)
        else:
            r.error(405, current.ERROR.BAD_METHOD)
        return output

    # -------------------------------------------------------------------------
    def widget(self, r, method=None, widget_id=None, visible=True, **attr):
        """
            Widget-render entry point for S3Summary.

            Args:
                r: the S3Request
                method: the widget method
                widget_id: the widget ID
                visible: whether the widget is initially visible
                attr: controller attributes
        """

        # Get the target resource
        resource = self.get_target(r)

        # Read the relevant GET vars
        report_vars, get_vars = self.get_options(r, resource)
        get_vars_get = get_vars.get

        # Parse event timestamp option
        timestamp = get_vars_get("timestamp")
        event_start, event_end = self.parse_timestamp(timestamp)

        # Parse fact option
        fact = get_vars_get("fact")
        try:
            facts = S3TimeSeriesFact.parse(fact)
        except SyntaxError:
            r.error(400, sys.exc_info()[1])
        baseline = get_vars_get("baseline")

        # Parse grouping axes
        rows = get_vars_get("rows")
        cols = get_vars_get("cols")

        # Parse event frame parameters
        start = get_vars_get("start")
        end = get_vars_get("end")
        slots = get_vars_get("slots")

        if visible:
            # Create time series
            # @todo: should become resource.timeseries()
            ts = S3TimeSeries(resource,
                              start = start,
                              end = end,
                              slots = slots,
                              event_start = event_start,
                              event_end = event_end,
                              rows = rows,
                              cols = cols,
                              facts = facts,
                              baseline = baseline,
                              # @todo: add title
                              #title = title,
                              )

            # Extract aggregated results as JSON-serializable dict
            data = ts.as_dict()
        else:
            data = None

        # Render output
        if r.representation in ("html", "iframe"):

            ajax_vars = Storage(r.get_vars)
            ajax_vars.update(get_vars)
            filter_url = r.url(method = "",
                               representation = "",
                               vars = ajax_vars.fromkeys((k for k in ajax_vars
                                                          if k not in report_vars)
                                                         )
                               )
            ajaxurl = attr.get("ajaxurl", r.url(method = "timeplot",
                                                representation = "json",
                                                vars = ajax_vars,
                                                ))
            output = S3TimePlotForm(resource).html(data,
                                                   get_vars = get_vars,
                                                   filter_widgets = None,
                                                   ajaxurl = ajaxurl,
                                                   filter_url = filter_url,
                                                   widget_id = widget_id,
                                                   )

            # Detect and store theme-specific inner layout
            view = self._view(r, "timeplot.html")

            # Render inner layout (outer page layout is set by S3Summary)
            output["title"] = None
            output = XML(current.response.render(view, output))

        else:
            r.error(415, current.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def timeplot(self, r, **attr):
        """
            Time plot report page

            Args:
                r: the S3Request instance
                attr: controller attributes for the request
        """

        output = {}

        # Get the target resource
        resource = self.get_target(r)
        tablename = resource.tablename
        get_config = resource.get_config

        # Apply filter defaults (before rendering the data!)
        show_filter_form = False
        if r.representation in ("html", "iframe"):
            filter_widgets = get_config("filter_widgets", None)
            if filter_widgets and not self.hide_filter:
                from .s3filter import S3FilterForm
                show_filter_form = True
                S3FilterForm.apply_filter_defaults(r, resource)

        # Read the relevant GET vars
        report_vars, get_vars = self.get_options(r, resource)

        get_vars_get = get_vars.get

        # Parse event timestamp option
        timestamp = get_vars_get("timestamp")
        event_start, event_end = self.parse_timestamp(timestamp)

        # Parse fact option
        fact = get_vars_get("fact")
        try:
            facts = S3TimeSeriesFact.parse(fact)
        except SyntaxError:
            r.error(400, sys.exc_info()[1])
        baseline = get_vars_get("baseline")

        # Parse grouping axes
        rows = get_vars_get("rows")
        cols = get_vars_get("cols")

        # Parse event frame parameters
        start, end, slots = get_timeframe(get_vars)

        # Create time series
        # @todo: should become resource.timeseries()
        ts = S3TimeSeries(resource,
                          start = start,
                          end = end,
                          slots = slots,
                          event_start = event_start,
                          event_end = event_end,
                          rows = rows,
                          cols = cols,
                          facts = facts,
                          baseline = baseline,
                          # @todo: add title
                          #title = title,
                          )

        # Extract aggregated results as JSON-serializable dict
        data = ts.as_dict()

        # Widget ID
        widget_id = "timeplot"

        # Render output
        if r.representation in ("html", "iframe"):
            # Page load

            crud_string = self.crud_string
            output["title"] = crud_string(tablename, "title_report")

            # Filter widgets
            if show_filter_form:
                advanced = False
                for widget in filter_widgets:
                    if "hidden" in widget.opts and widget.opts.hidden:
                        advanced = get_config("report_advanced", True)
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
                alias = resource.alias if resource.parent else None
                filter_widgets = filter_form.fields(fresource,
                                                    r.get_vars,
                                                    alias = alias,
                                                    )
            else:
                # Render as empty string to avoid the exception in the view
                filter_widgets = None

            ajax_vars = Storage(r.get_vars)
            ajax_vars.update(get_vars)
            filter_url = r.url(method = "",
                               representation = "",
                               vars = ajax_vars.fromkeys((k for k in ajax_vars
                                                          if k not in report_vars)
                                                         )
                               )
            ajaxurl = attr.get("ajaxurl", r.url(method = "timeplot",
                                                representation = "json",
                                                vars = ajax_vars,
                                                ))

            output = S3TimePlotForm(resource).html(data,
                                                   get_vars = get_vars,
                                                   filter_widgets = filter_widgets,
                                                   ajaxurl = ajaxurl,
                                                   filter_url = filter_url,
                                                   widget_id = widget_id,
                                                   )

            output["title"] = crud_string(tablename, "title_report")
            output["report_type"] = "timeplot"

            # Detect and store theme-specific inner layout
            self._view(r, "timeplot.html")

            # View
            response = current.response
            response.view = self._view(r, "report.html")

        elif r.representation == "json":
            # Ajax load
            output = json.dumps(data, separators=SEPARATORS)

        else:
            r.error(415, current.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def get_target(self, r):
        """
            Identify the target resource

            Args:
                r: the S3Request
        """

        # Fallback
        resource = self.resource

        # Read URL parameter
        alias = r.get_vars.get("component")

        # Identify target component
        if alias and alias not in (resource.alias, "~"):
            component = resource.components.get(alias)
            if component:
                resource = component

        return resource

    # -------------------------------------------------------------------------
    @staticmethod
    def get_options(r, resource):
        """
            Read the relevant GET vars for the timeplot

            Args:
                r: the S3Request
                resource: the target S3Resource
        """

        # Extract the relevant GET vars
        report_vars = ("timestamp",
                       "start",
                       "end",
                       "slots",
                       "fact",
                       "baseline",
                       "rows",
                       "cols",
                       )
        get_vars = {k: v for k, v in r.get_vars.items() if k in report_vars}

        # Fall back to report options defaults
        report_options = resource.get_config("timeplot_options", {})
        defaults = report_options.get("defaults", {})
        if not any(k in get_vars for k in report_vars):
            get_vars = defaults
        else:
            # Optional URL args always fall back to config:
            optional = ("timestamp",
                        "fact",
                        "baseline",
                        "rows",
                        "cols",
                        )
            for opt in optional:
                if opt not in get_vars and opt in defaults:
                    get_vars[opt] = defaults[opt]

        return report_vars, get_vars

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_timestamp(timestamp):
        """
            Parse timestamp expression

            Args:
                timestamp: the timestamp expression
        """

        if timestamp:
            fields = timestamp.split(",")
            if len(fields) > 1:
                start = fields[0].strip()
                end = fields[1].strip()
            else:
                start = fields[0].strip()
                end = None
        else:
            start = None
            end = None

        return start, end

# =============================================================================
class S3TimePlotForm(S3ReportForm):
    """ Helper class to render a report form """

    # -------------------------------------------------------------------------
    def html(self,
             data,
             filter_widgets = None,
             get_vars = None,
             ajaxurl = None,
             filter_url = None,
             filter_form = None,
             filter_tab = None,
             widget_id = None,
             ):
        """
            Render the form for the report

            Args:
                get_vars: the GET vars if the request (as dict)
                widget_id: the HTML element base ID for the widgets
        """

        T = current.T

        # Filter options
        if filter_widgets is not None:
            filter_options = self._fieldset(T("Filter Options"),
                                            filter_widgets,
                                            _id = "%s-filters" % widget_id,
                                            _class = "filter-form",
                                            )
        else:
            filter_options = ""

        # Report options
        report_options = self.report_options(get_vars = get_vars,
                                             widget_id = widget_id,
                                             )

        hidden = {"tp-data": json.dumps(data, separators=SEPARATORS)}

        # @todo: chart title
        empty = T("No data available")

        # Report form submit element
        resource = self.resource
        submit = resource.get_config("report_submit", True)
        if submit:
            _class = "tp-submit"
            if submit is True:
                label = T("Update Report")
            elif isinstance(submit, (list, tuple)):
                label = submit[0]
                _class = "%s %s" % (submit[1], _class)
            else:
                label = submit
            submit = TAG[""](INPUT(_type = "button",
                                   _value = label,
                                   _class = _class,
                                   ))
        else:
            submit = ""

        # @todo: use view template (see S3ReportForm)
        form = FORM(filter_options,
                    report_options,
                    submit,
                    hidden = hidden,
                    _class = "tp-form",
                    _id = "%s-tp-form" % widget_id,
                    )

        # View variables
        output = {"form": form,
                  "empty": empty,
                  "widget_id": widget_id,
                  }

        # D3/Timeplot scripts (injected so that they are available for summary)
        S3Report.inject_d3()
        s3 = current.response.s3
        scripts = s3.scripts
        appname = current.request.application
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.ui.timeplot.js" % appname
            if script not in scripts:
                scripts.append(script)
        else:
            script = "/%s/static/scripts/S3/s3.ui.timeplot.min.js" % appname
            if script not in scripts:
                scripts.append(script)

        # Script to attach the timeplot widget
        settings = current.deployment_settings
        options = {"ajaxURL": ajaxurl,
                   "autoSubmit": settings.get_ui_report_auto_submit(),
                   "emptyMessage": str(empty),
                   }
        script = """$("#%(widget_id)s").timeplot(%(options)s)""" % \
                    {"widget_id": widget_id,
                     "options": json.dumps(options),
                    }
        s3.jquery_ready.append(script)

        return output

    # -------------------------------------------------------------------------
    def report_options(self,
                       get_vars = None,
                       widget_id = "timeplot",
                       ):
        """
            Render the widgets for the report options form

            Args:
                get_vars: the GET vars if the request (as dict)
                widget_id: the HTML element base ID for the widgets
        """

        T = current.T

        timeplot_options = self.resource.get_config("timeplot_options")

        label = lambda l, **attr: LABEL("%s:" % l, **attr)
        selectors = []

        # Fact options
        selector = self.fact_options(options = timeplot_options,
                                     get_vars = get_vars,
                                     widget_id = widget_id,
                                     )
        selectors.append(("%s-fact__row" % widget_id,
                          label(T("Report of"),
                                _for = selector["_id"],
                                ),
                          selector,
                          None,
                          ))

        # Timestamp options
        selector = self.timestamp_options(options = timeplot_options,
                                          get_vars = get_vars,
                                          widget_id = widget_id,
                                          )
        selectors.append(("%s-timestamp__row" % widget_id,
                          label(T("Mode"),
                                _for = selector["_id"]
                                ),
                          selector,
                          None,
                          ))

        # Time frame and slots options
        tf_selector = self.time_options(options = timeplot_options,
                                        get_vars = get_vars,
                                        widget_id = widget_id,
                                        )
        ts_selector = self.slot_options(options = timeplot_options,
                                        get_vars = get_vars,
                                        widget_id = widget_id,
                                        )
        if ts_selector:
            selector = DIV(tf_selector,
                           label(T("Intervals"), _for=ts_selector["_id"]),
                           ts_selector,
                           _class = "tp-time-options",
                           )
        else:
            selector = tf_selector
        selectors.append(("%s-time__row" % widget_id,
                          label(T("Time Frame"), _for=tf_selector["_id"]),
                          selector,
                          None,
                          ))

        # Build field set
        formstyle = current.deployment_settings.get_ui_filter_formstyle()
        if not callable(formstyle):
            formstyle = SQLFORM.formstyles[formstyle]

        selectors = formstyle(FORM(), selectors)

        return self._fieldset(T("Report Options"),
                              selectors,
                              _id = "%s-options" % widget_id,
                              _class = "report-options",
                              )

    # -------------------------------------------------------------------------
    def fact_options(self,
                     options = None,
                     get_vars = None,
                     widget_id = None,
                     ):
        """
            Generate a selector for fact options (multiple allowed)

            Args:
                options: the timeplot options for the target table
                get_vars: the current GET vars with selected options
                          or defaults, respectively
                widget_id: the main widget DOM ID

            Returns:
                a multi-select widget
        """

        T = current.T
        table = self.resource.table

        default = "count(%s)" % (table._id.name)

        # Options
        if options and "facts" in options:
            opts = options["facts"]
        else:
            from .s3fields import s3_all_meta_field_names
            meta_fields = s3_all_meta_field_names()

            opts = [(T("Number of Records"), default)]
            for fn in table.fields:
                if fn in meta_fields:
                    continue
                field = table[fn]
                if not field.readable:
                    continue
                requires = field.requires
                if field.type == "integer" and not hasattr(requires, "options") or \
                    field.type == "double":
                    label = T("%(field)s (total)") % {"field": field.label}
                    opts.append((label, "sum(%s)" % fn))

        # Currently selected option(s)
        value = []
        if get_vars:
            selected = get_vars.get("fact")
            if not isinstance(selected, list):
                selected = [selected]
            for item in selected:
                if isinstance(item, (tuple, list)):
                    value.append(item[-1])
                elif isinstance(item, str):
                    value.extend(item.split(","))
        if not value:
            value = default

        # Dummy field
        widget_opts = [(opt, label) for (label, opt) in opts]
        dummy_field = Storage(name = "timeplot-fact",
                              requires = IS_IN_SET(widget_opts, zero=None),
                              )

        # Widget
        from .s3widgets import S3MultiSelectWidget
        return S3MultiSelectWidget()(dummy_field,
                                     value,
                                     _id = "%s-fact" % widget_id,
                                     _name = "fact",
                                     _class = "tp-fact",
                                     )

    # -------------------------------------------------------------------------
    def timestamp_options(self,
                          options = None,
                          get_vars = None,
                          widget_id = None,
                          ):
        """
            Generate a selector for timestamp options

            Args:
                options: the timeplot options for the target table
                get_vars: the current GET vars with selected options
                          or defaults, respectively
                widget_id: the main widget DOM ID

            Returns:
                an options widget
        """

        T = current.T
        table = self.resource.table

        # Options
        if options and "timestamp" in options:
            opts = options["timestamp"]
        else:
            start, end = S3TimeSeries.default_timestamp(table)
            if not start:
                return None
            separate = (start, end) if end else (start, start)
            opts = [(T("per interval"), ",".join(separate)),
                    (T("cumulative"), start),
                    ]

        if not opts:
            return SPAN(T("no options available"),
                        _class = "no-options-available",
                        )

        # Currently selected option
        value = get_vars.get("timestamp") if get_vars else None
        if not value:
            start, end = S3TimeSeries.default_timestamp(table)
            if start and end:
                value = "%s,%s" % (start, end)
            elif start:
                value = start

        # Dummy field
        widget_opts = [(opt, label) for (label, opt) in opts]
        dummy_field = Storage(name = "timestamp",
                              requires = IS_IN_SET(widget_opts, zero=None),
                              )

        # Widget
        return OptionsWidget.widget(dummy_field,
                                    value,
                                    _id = "%s-timestamp" % widget_id,
                                    _name = "timestamp",
                                    _class = "tp-timestamp",
                                    )

    # -------------------------------------------------------------------------
    @classmethod
    def time_options(cls,
                     options = None,
                     get_vars = None,
                     widget_id = None,
                     ):
        """
            Generate a selector for the report time frame

            Args:
                options: the timeplot options for the target table
                get_vars: the current GET vars with selected options
                          or defaults, respectively
                widget_id: the main widget DOM ID
           

            Returns:
                an options widget
        """

        T = current.T

        # Time options:
        if options and "time" in options:
            opts = options["time"]
                                      
        else:
            # (label, start, end, slots)
            # - if start is specified, end is relative to start
            # - otherwise, end is relative to now
            # - start "" means the date of the earliest recorded event
            # - end "" means now
            opts = ((T("All up to now"), "", "", ""),
                    (T("Last Year"), "<-1 year", "+1 year", "months"),
                    (T("This Year"), "<-0 years", "", "months"),
                    (T("Next Year"), "<-0 years", "+1year", "months"),
                    (T("Next 5 Years"), "<-0 years", "+5years", "years"),
                    (T("Last Month"), "<-1 month", "+1 month", "days"),
                    (T("This Month"), "<-0 months", "", "days"),
                    (T("Last Week"), "<-1 week", "+1 week", "days"),
                    (T("This Week"), "<-0 weeks", "", "days"),
                    #(T("Past 12 Months"), "-12months", "", "months"),
                    #(T("Past 6 Months"), "-6months", "", "weeks"),
                    #(T("Past 3 Months"), "-3months", "", "weeks"),
                    #(T("Past Month"), "-1month", "", "days"),
                    #(T("Past Week"), "-1week", "", "days"),
                    #("All/+1 Month", "", "+1month", ""),
                    #("All/+2 Month", "", "+2month", ""),
                    #("-6/+3 Months", "-6months", "+9months", "months"),
                    #("-3/+1 Months", "-3months", "+4months", "weeks"),
                    #("-4/+2 Weeks", "-4weeks", "+6weeks", "weeks"),
                    #("-2/+1 Weeks", "-2weeks", "+3weeks", "days"),
                    )

        widget_opts = []
        for opt in opts:
            label, start, end, slots = opt
            widget_opts.append(("|".join((start, end, slots)), T(label)))

        # Currently selected value
        if get_vars:
            start, end, slots = get_timeframe(get_vars)
        else:
            start = end = slots = ""
        value = "|".join((start, end, slots))

        # Dummy field
        dummy_field = Storage(name = "time",
                              requires = IS_IN_SET(widget_opts, zero=None),
                              )

        # Widget
        return OptionsWidget.widget(dummy_field,
                                    value,
                                    _id = "%s-time" % widget_id,
                                    _name = "time",
                                    _class = "tp-time",
                                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def slot_options(options=None, get_vars=None, widget_id=None):
        """
            Generates a selector for the time slots

            Args:
                options: the timeplot options for the target table
                get_vars: the current GET vars with selected options
                          or defaults, respectively
                widget_id: the main widget DOM ID

            Returns:
                an options widget, or None if there is only
                the "auto" option available
                                  
        """
                                               
        T = current.T

        automatic = (T("Automatic"), "auto")

        if options and "slots" in options:
            opts = options["slots"]
                                                                               
        else:
            # Do not render by default
            return None
            #opts = (automatic,
                    #(T("Days"), "days"),
                    #(T("Weeks"), "weeks"),
                    #(T("2 Weeks"), "2 weeks"),
                    #(T("Months"), "months"),
                    #(T("3 Months"), "3 months"),
                    #)

        if not any(opt[1] == "auto" for opt in opts):
            explicit = opts
            opts = [automatic]
            opts.extend(explicit)
        if len(opts) == 1:
            return None

        # Currently selected value
        value = get_vars.get("slots") if get_vars else None
        if not value:
            value = "auto"

        # Dummy field
        widget_opts = [(opt, label) for (label, opt) in opts]
        dummy_field = Storage(name = "slots",
                              requires = IS_IN_SET(widget_opts, zero=None),
                              )
        # Widget
        return OptionsWidget.widget(dummy_field,
                                    value,
                                    _id = "%s-slots" % widget_id,
                                    _name = "slots",
                                    _class = "tp-slots",
                                    )

# =============================================================================
def get_timeframe(get_vars):
    """
        Get the report time frame from GET vars; can be encoded either
        as a query parameter "time" with start|end|slots (i.e. |-separated),
        or as separate start, end and slots parameters.

        Args:
            get_vars: the GET vars

        Returns:
            tuple (start, end, slots)
    """

    timeframe = get_vars.get("time")
    if timeframe:
        if isinstance(timeframe, str):
            timeframe = timeframe.split("|")
        start, end, slots = (list(timeframe[-3:]) + ["", "", ""])[:3]
    else:
        start = get_vars.get("start", "")
        end = get_vars.get("end", "")
        slots = get_vars.get("slots", "")
                        
    return start, end, slots

# =============================================================================
class S3TimeSeries:
    """ A series of grouped values, aggregated over a time axis """

    def __init__(self,
                 resource,
                 start = None,
                 end = None,
                 slots = None,
                 event_start = None,
                 event_end = None,
                 rows = None,
                 cols = None,
                 facts = None,
                 baseline = None,
                 title = None,
                 ):
        """
            Args:
                resource: the resource
                start: the start of the series (datetime or string expression)
                end: the end of the time series (datetime or string expression)
                slots: the slot size (string expression)

                event_start: the event start field (field selector)
                event_end: the event end field (field selector)

                rows: the rows axis for event grouping (field selector)
                cols: the columns axis for event grouping (field selector)
                facts: an array of facts (S3TimeSeriesFact)

                baseline: the baseline field (field selector)

                title: the time series title
        """

        self.resource = resource
        self.rfields = {}

        self.title = title

        # Resolve timestamp
        self.resolve_timestamp(event_start, event_end)

        # Resolve grouping axes
        self.resolve_axes(rows, cols)

        # Resolve facts
        if not facts:
            facts = [S3TimeSeriesFact("count", resource._id.name)]
        self.facts = [fact.resolve(resource) for fact in facts]

        # Resolve baseline
        self.resolve_baseline(baseline)

        # Create event frame
        self.event_frame = self._event_frame(start, end, slots)

        # ...and fill it with data
        self._select()

    # -------------------------------------------------------------------------
    def as_dict(self):
        """ Return the time series as JSON-serializable dict """

        rfields = self.rfields
        rfields_get = rfields.get

        # Fact Data
        fact_data = []
        for fact in self.facts:
            fact_data.append((str(fact.label),
                              fact.method,
                              fact.base,
                              fact.slope,
                              fact.interval,
                              ))

        # Event start and end selectors
        rfield = rfields_get("event_start")
        if rfield:
            event_start = rfield.selector
        else:
            event_start = None
        rfield = rfields_get("event_end")
        if rfield:
            event_end = rfield.selector
        else:
            event_end = None

        # Rows
        rows = rfields_get("rows")
        if rows:
            rows_sorted = self._represent_axis(rows, self.rows_keys)
            rows_keys = [row[0] for row in rows_sorted]
            rows_data = {"s": rows.selector,
                         "l": str(rows.label),
                         "v": rows_sorted,
                         }
        else:
            rows_keys = None
            rows_data = None

        # Columns
        cols = rfields_get("cols")
        if cols:
            cols_sorted = self._represent_axis(cols, self.cols_keys)
            cols_keys = [col[0] for col in cols_sorted]
            cols_data = {"s": cols.selector,
                         "l": str(cols.label),
                         "v": cols_sorted,
                         }
        else:
            cols_keys = None
            cols_data = None

        # Iterate over the event frame to collect aggregates
        event_frame = self.event_frame
        periods_data = []
        append = periods_data.append
        #fact = self.facts[0]
        for period in event_frame:
            # Aggregate
            period.aggregate(self.facts)
            # Extract
            item = period.as_dict(rows = rows_keys,
                                  cols = cols_keys,
                                  )
            append(item)

        # Baseline
        rfield = rfields_get("baseline")
        if rfield:
            baseline = (rfield.selector,
                        str(rfield.label),
                        event_frame.baseline,
                        )
        else:
            baseline = None

        # Output dict
        data = {"f": fact_data,
                "t": (event_start, event_end),
                "s": event_frame.slots,
                "e": event_frame.empty,
                "l": self.title,
                "r": rows_data,
                "c": cols_data,
                "p": periods_data,
                "z": baseline,
                }

        return data

    # -------------------------------------------------------------------------
    @staticmethod
    def _represent_axis(rfield, values):
        """
            Represent and sort the values of a pivot axis (rows or cols)

            Args:
                rfield: the axis rfield
                values: iterable of values
        """

        if rfield.virtual:

            representations = []
            append = representations.append()
            stripper = S3MarkupStripper()

            represent = rfield.represent
            if not represent:
                represent = s3_str

            for value in values:
                if value is None:
                    append((value, "-"))
                text = represent(value)
                if "<" in text:
                    stripper.feed(text)
                    append((value, stripper.stripped()))
                else:
                    append((value, text))
        else:
            field = rfield.field
            represent = field.represent
            if represent and hasattr(represent, "bulk"):
                representations = represent.bulk(list(values),
                                                 list_type = False,
                                                 show_link = False,
                                                 ).items()
            else:
                representations = []
                for value in values:
                    append((value, s3_represent_value(field,
                                                      value,
                                                      strip_markup = True,
                                                      )))

        return sorted(representations, key = lambda item: item[1])

    # -------------------------------------------------------------------------
    def _represent_method(self, field):
        """
            Get the representation method for a field in the report

            Args:
                field: the field selector
        """

        rfields = self.rfields
        default = lambda value: None

        if field and field in rfields:

            rfield = rfields[field]

            if rfield.field:
                def repr_method(value):
                    return s3_represent_value(rfield.field, value,
                                              strip_markup=True)

            elif rfield.virtual:
                stripper = S3MarkupStripper()
                def repr_method(val):
                    if val is None:
                        return "-"
                    text = s3_str(val)
                    if "<" in text:
                        stripper.feed(text)
                        return stripper.stripped() # = totally naked ;)
                    else:
                        return text
            else:
                repr_method = default
        else:
            repr_method = default

        return repr_method

    # -------------------------------------------------------------------------
    def _event_frame(self,
                     start = None,
                     end = None,
                     slots = None,
                     ):
        """
            Create an event frame for this report

            Args:
                start: the start date/time (string, date or datetime)
                end: the end date/time (string, date or datetime)
                slots: the slot length (string)

            Returns:
                the event frame
        """

        resource = self.resource
        rfields = self.rfields

        STANDARD_SLOT = "1 day"
        now = tp_tzsafe(datetime.datetime.utcnow())

        # Parse start and end time
        dtparse = self.dtparse
        start_dt = end_dt = None
        if start:
            if isinstance(start, str):
                start_dt = dtparse(start, start=now)
            else:
                if isinstance(start, datetime.datetime):
                    start_dt = tp_tzsafe(start)
                else:
                    # Date only => start at midnight
                    start_dt = tp_tzsafe(datetime.datetime.fromordinal(start.toordinal()))
        if end:
            if isinstance(end, str):
                relative_to = start_dt if start_dt else now
                end_dt = dtparse(end, start=relative_to)
            else:
                if isinstance(end, datetime.datetime):
                    end_dt = tp_tzsafe(end)
                else:
                    # Date only => end at midnight
                    end_dt = tp_tzsafe(datetime.datetime.fromordinal(end.toordinal()))

        # Fall back to now if end is not specified
        if not end_dt:
            end_dt = now

        event_start = rfields["event_start"]
        if not start_dt and event_start and event_start.field:
            # No interval start => fall back to first event start
            query = FS(event_start.selector) != None
            resource.add_filter(query)
            rows = resource.select([event_start.selector],
                                    limit=1,
                                    orderby=event_start.field,
                                    as_rows=True)
            # Remove the filter we just added
            rfilter = resource.rfilter
            rfilter.filters.pop()
            rfilter.query = None
            rfilter.transformed = None
            if rows:
                first_event = rows.first()[event_start.colname]
                if isinstance(first_event, datetime.date):
                    first_event = tp_tzsafe(datetime.datetime.fromordinal(first_event.toordinal()))
                start_dt = first_event

        event_end = rfields["event_end"]
        if not start_dt and event_end and event_end.field:
            # No interval start => fall back to first event end minus
            # one standard slot length:
            query = FS(event_end.selector) != None
            resource.add_filter(query)
            rows = resource.select([event_end.selector],
                                    limit=1,
                                    orderby=event_end.field,
                                    as_rows=True)
            # Remove the filter we just added
            rfilter = resource.rfilter
            rfilter.filters.pop()
            rfilter.query = None
            rfilter.transformed = None
            if rows:
                last_event = rows.first()[event_end.colname]
                if isinstance(last_event, datetime.date):
                    last_event = tp_tzsafe(datetime.datetime.fromordinal(last_event.toordinal()))
                start_dt = dtparse("-%s" % STANDARD_SLOT, start=last_event)

        if not start_dt:
            # No interval start => fall back to interval end minus
            # one slot length:
            if not slots:
                slots = STANDARD_SLOT
            try:
                start_dt = dtparse("-%s" % slots, start=end_dt)
            except (SyntaxError, ValueError):
                slots = STANDARD_SLOT
                start_dt = dtparse("-%s" % slots, start=end_dt)

        # Fall back for slot length
        if not slots:
            # No slot length specified => determine optimum automatically
            # @todo: determine from density of events rather than from
            #        total interval length?
            seconds = abs(end_dt - start_dt).total_seconds()
            day = 86400
            if seconds < day:
                slots = "hours"
            elif seconds < 3 * day:
                slots = "6 hours"
            elif seconds < 28 * day:
                slots = "days"
            elif seconds < 90 * day:
                slots = "weeks"
            elif seconds < 730 * day:
                slots = "months"
            elif seconds < 2190 * day:
                slots = "3 months"
            else:
                slots = "years"

        # Create event frame
        ef = S3TimeSeriesEventFrame(start_dt, end_dt, slots)

        return ef

    # -------------------------------------------------------------------------
    def _select(self):
        """
            Select records from the resource and store them as events in
            this time series
        """

        resource = self.resource
        rfields = self.rfields
        rfields_get = rfields.get

        # Fields to extract
        cumulative = False
        event_start = rfields_get("event_start")
        fields = {event_start.selector}
        event_end = rfields_get("event_end")
        if event_end:
            fields.add(event_end.selector)
        rows_rfield = rfields_get("rows")
        if rows_rfield:
            fields.add(rows_rfield.selector)
        cols_rfield = rfields_get("cols")
        if cols_rfield:
            fields.add(cols_rfield.selector)
        fact_columns = []
        for fact in self.facts:
            if fact.method == "cumulate":
                cumulative = True
            if fact.resource is None:
                fact.resolve(resource)
            for rfield in (fact.base_rfield, fact.slope_rfield):
                if rfield:
                    fact_columns.append(rfield.colname)
                    fields.add(rfield.selector)
        fields.add(resource._id.name)

        # Get event frame
        event_frame = self.event_frame

        # Filter by event frame start:
        if not cumulative and event_end:
            # End date of events must be after the event frame start date
            end_selector = FS(event_end.selector)
            start = event_frame.start
            query = (end_selector == None) | (end_selector >= start)
        else:
            # No point if events have no end date, and wrong if
            # method is cumulative
            query = None

        # Filter by event frame end:
        # Start date of events must be before event frame end date
        start_selector = FS(event_start.selector)
        end = event_frame.end
        q = (start_selector == None) | (start_selector <= end)
        query = query & q if query is not None else q

        # Add as temporary filter
        resource.add_filter(query)

        # Compute baseline
        value = None
        baseline_rfield = rfields_get("baseline")
        if baseline_rfield:
            baseline_table = current.db[baseline_rfield.tname]
            pkey = str(baseline_table._id)
            colname = baseline_rfield.colname
            rows = resource.select([baseline_rfield.selector],
                                    groupby = [pkey, colname],
                                    as_rows = True,
                                    )
            value = 0
            for row in rows:
                v = row[colname]
                if v is not None:
                    value += v
        event_frame.baseline = value

        # Extract the records
        data = resource.select(fields)

        # Remove the filter we just added
        rfilter = resource.rfilter
        rfilter.filters.pop()
        rfilter.query = None
        rfilter.transformed = None

        # Do we need to convert dates into datetimes?
        convert_start = True if event_start.ftype == "date" else False
        convert_end = True if event_start.ftype == "date" else False
        fromordinal = datetime.datetime.fromordinal
        convert_date = lambda d: fromordinal(d.toordinal())

        # Column names for extractions
        pkey = str(resource._id)
        start_colname = event_start.colname
        end_colname = event_end.colname if event_end else None
        rows_colname = rows_rfield.colname if rows_rfield else None
        cols_colname = cols_rfield.colname if cols_rfield else None

        # Create the events
        events = []
        add_event = events.append
        rows_keys = set()
        cols_keys = set()
        for row in data.rows:

            # Extract values
            values = dict((colname, row[colname]) for colname in fact_columns)

            # Extract grouping keys
            grouping = {}
            if rows_colname:
                grouping["row"] = row[rows_colname]
            if cols_colname:
                grouping["col"] = row[cols_colname]

            # Extract start/end date
            start = row[start_colname]
            if convert_start and start:
                start = convert_date(start)
            end = row[end_colname] if end_colname else None
            if convert_end and end:
                end = convert_date(end)

            # values = (base, slope)
            event = S3TimeSeriesEvent(row[pkey],
                                      start = start,
                                      end = end,
                                      values = values,
                                      **grouping)
            add_event(event)
            rows_keys |= event.rows
            cols_keys |= event.cols

        # Extend the event frame with these events
        if events:
            event_frame.extend(events)

        # Store the grouping keys
        self.rows_keys = rows_keys
        self.cols_keys = cols_keys

        return data

    # -------------------------------------------------------------------------
    @staticmethod
    def default_timestamp(table, event_end=None):
        """
            Get the default timestamp for a table

            Args:
                table: the Table
                event_end: event_end, if not default (field selector)

            Returns:
                tuple (event_start, event_end), field selectors
        """

        event_start = None
        fields = table.fields
        for fname in ("date", "start_date", "created_on"):
            if fname in fields:
                event_start = fname
                break
        if event_start and not event_end:
            for fname in ("end_date",):
                if fname in fields:
                    event_end = fname
                    break

        return event_start, event_end

    # -------------------------------------------------------------------------
    def resolve_timestamp(self, event_start, event_end):
        """
            Resolve the event_start and event_end field selectors

            Args:
                event_start: the field selector for the event start field
                event_end: the field selector for the event end field
        """

        resource = self.resource
        rfields = self.rfields

        # Defaults                              
        if not event_start:
            table = resource.table
            event_start, event_end = self.default_timestamp(table)
        if not event_start:
            raise SyntaxError("No time stamps found in %s" % table)

        # Get the fields
        start_rfield = resource.resolve_selector(event_start)
        if event_end:
            end_rfield = resource.resolve_selector(event_end)
        else:
            end_rfield = None

        rfields["event_start"] = start_rfield
        rfields["event_end"] = end_rfield

    # -------------------------------------------------------------------------
    def resolve_baseline(self, baseline):
        """
            Resolve the baseline field selector

            Args:
                baseline: the baseline selector
        """

        resource = self.resource
        rfields = self.rfields

        # Resolve baseline selector
        baseline_rfield = None
        if baseline:
            try:
                baseline_rfield = resource.resolve_selector(baseline)
            except (AttributeError, SyntaxError):
                baseline_rfield = None

        if baseline_rfield and \
           baseline_rfield.ftype not in NUMERIC_TYPES:
            # Invalid field type - log and ignore
            current.log.error("Invalid field type for baseline: %s (%s)" %
                              (baseline, baseline_rfield.ftype))
            baseline_rfield = None

        rfields["baseline"] = baseline_rfield

    # -------------------------------------------------------------------------
    def resolve_axes(self, rows, cols):
        """
            Resolve the grouping axes field selectors

            Args:
                rows: the rows field selector
                cols: the columns field selector
        """

        resource = self.resource
        rfields = self.rfields

        # Resolve rows selector
        rows_rfield = None
        if rows:
            try:
                rows_rfield = resource.resolve_selector(rows)
            except (AttributeError, SyntaxError):
                rows_rfield = None

        # Resolve columns selector
        cols_rfield = None
        if cols:
            try:
                cols_rfield = resource.resolve_selector(cols)
            except (AttributeError, SyntaxError):
                cols_rfield = None

        rfields["rows"] = rows_rfield
        rfields["cols"] = cols_rfield

    # -------------------------------------------------------------------------
    @staticmethod
    def dtparse(timestr, start=None):
        """
            Parse a string for start/end date(time) of an interval

            Args:
                timestr: the time string
                start: the start datetime to relate relative times to
        """

        if start is None:
            start = tp_tzsafe(datetime.datetime.utcnow())

        if not timestr:
            return start

        # Relative to start: [+|-]{n}[year|month|week|day|hour]s
        match = dt_regex.DELTA.match(timestr)
        if match:
            groups = match.groups()
            intervals = {"y": "years",
                         "m": "months",
                         "w": "weeks",
                         "d": "days",
                         "h": "hours",
                         }
            length = intervals.get(groups[3])
            if not length:
                raise SyntaxError("Invalid date/time: %s" % timestr)

            num = int(groups[2])
            if groups[1] == "-":
                num *= -1
            delta = {length: num}

            end = groups[0]
            if end == "<":
                delta.update(minute=0, second=0, microsecond=0)
                if length != "hours":
                    delta.update(hour=0)
                if length == "weeks":
                    delta.update(weeks=num-1, weekday=0)
                elif length == "months":
                    delta.update(day=1)
                elif length == "years":
                    delta.update(month=1, day=1)
            elif end == ">":
                delta.update(minute=59, second=59, microsecond=999999)
                if length != "hours":
                    delta.update(hour=23)
                if length == "weeks":
                    delta.update(weekday=6)
                elif length == "months":
                    delta.update(day=31)
                elif length == "years":
                    delta.update(month=12, day=31)

            return start + relativedelta(**delta)

        # Month/Year, e.g. "5/2001"
        match = dt_regex.MONTH_YEAR.match(timestr)
        if match:
            groups = match.groups()
            year = int(groups[1])
            month = int(groups[0])
            return tp_datetime(year, month, 1, 0, 0, 0)

        # Year-Month, e.g. "2001-05"
        match = dt_regex.YEAR_MONTH.match(timestr)
        if match:
            groups = match.groups()
            month = int(groups[1])
            year = int(groups[0])
            return tp_datetime(year, month, 1, 0, 0, 0)

        # Year only, e.g. "1996"
        match = dt_regex.YEAR.match(timestr)
        if match:
            groups = match.groups()
            year = int(groups[0])
            return tp_datetime(year, 1, 1, 0, 0, 0)

        # Date, e.g. "2013-01-04"
        match = dt_regex.DATE.match(timestr)
        if match:
            groups = match.groups()
            year = int(groups[0])
            month = int(groups[1])
            day = int(groups[2])
            try:
                return tp_datetime(year, month, day)
            except ValueError:
                # Day out of range
                return tp_datetime(year, month, 1) + \
                       datetime.timedelta(days = day-1)

        # ISO datetime
        dt = s3_decode_iso_datetime(str(timestr))
        return s3_utc(dt)

# =============================================================================
class S3TimeSeriesEvent:
    """ A single event in a time series """

    def __init__(self,
                 event_id,
                 start = None,
                 end = None,
                 values = None,
                 row = DEFAULT,
                 col = DEFAULT,
                 ):
        """
            Args:
                event_id: a unique identifier for the event (e.g. record ID)
                start: start time of the event (datetime.datetime)
                end: end time of the event (datetime.datetime)
                values: a dict of key-value pairs with the attribute
                        values for the event
                row: the series row for this event
                col: the series column for this event
        """

        self.event_id = event_id

        self.start = tp_tzsafe(start)
        self.end = tp_tzsafe(end)

        if isinstance(values, dict):
            self.values = values
        else:
            self.values = {}

        self.row = row
        self.col = col

        self._rows = None
        self._cols = None

    # -------------------------------------------------------------------------
    @property
    def rows(self):
        """
            Get the set of row axis keys for this event
        """

        rows = self._rows
        if rows is None:
            rows = self._rows = self.series(self.row)
        return rows

    # -------------------------------------------------------------------------
    @property
    def cols(self):
        """
            Get the set of column axis keys for this event
        """

        cols = self._cols
        if cols is None:
            cols = self._cols = self.series(self.col)
        return cols

    # -------------------------------------------------------------------------
    @staticmethod
    def series(value):
        """
            Convert a field value into a set of series keys

            Args:
                value: the field value
        """

        if value is DEFAULT:
            series = set()
        elif value is None:
            series = {None}
        elif type(value) is list:
            series = set(s3_flatlist(value))
        else:
            series = {value}
        return series

    # -------------------------------------------------------------------------
    def __getitem__(self, field):
        """
            Access attribute values of this event

            Args:
                field: the attribute field name
        """

        return self.values.get(field, None)

    # -------------------------------------------------------------------------
    def __lt__(self, other):
        """
            Comparison method to allow sorting of events

            Args:
                other: the event to compare to
        """

        this = self.start
        that = other.start
        if this is None:
            result = that is not None
        elif that is None:
            result = False
        else:
            result = this < that
        return result

# =============================================================================
class S3TimeSeriesFact:
    """ A formula for a datum (fact) in a time series """

    #: Supported aggregation methods
    METHODS = {"count": "Count",
               "sum": "Total",
               "cumulate": "Cumulative Total",
               "min": "Minimum",
               "max": "Maximum",
               "avg": "Average",
               }

    def __init__(self, method, base, slope=None, interval=None, label=None):
        """
            Args:
                method: the aggregation method
                base: column name of the (base) field
                slope: column name of the slope field (for cumulate method)
                interval: time interval expression for the slope
        """

        if method not in self.METHODS:
            raise SyntaxError("Unsupported aggregation function: %s" % method)

        self.method = method
        self.base = base
        self.slope = slope
        self.interval = interval

        self.label = label

        self.resource = None

        self.base_rfield = None
        self.base_column = base

        self.slope_rfield = None
        self.slope_column = slope

    # -------------------------------------------------------------------------
    def aggregate(self, period, events):
        """
            Aggregate values from events

            Args:
                period: the period
                events: the events
        """

        values = []
        append = values.append

        method = self.method
        base = self.base_column

        if method == "cumulate":

            slope = self.slope_column
            duration = period.duration

            for event in events:

                if event.start == None:
                    continue

                if base:
                    base_value = event[base]
                else:
                    base_value = None

                if slope:
                    slope_value = event[slope]
                else:
                    slope_value = None

                if base_value is None:
                    if not slope or slope_value is None:
                        continue
                    else:
                        base_value = 0
                elif type(base_value) is list:
                    try:
                        base_value = sum(base_value)
                    except (TypeError, ValueError):
                        continue

                if slope_value is None:
                    if not base or base_value is None:
                        continue
                    else:
                        slope_value = 0
                elif type(slope_value) is list:
                    try:
                        slope_value = sum(slope_value)
                    except (TypeError, ValueError):
                        continue

                interval = self.interval
                if slope_value and interval:
                    event_duration = duration(event, interval)
                else:
                    event_duration = 1

                append((base_value, slope_value, event_duration))

            result = self.compute(values)

        elif base:

            for event in events:
                value = event[base]
                if value is None:
                    continue
                elif type(value) is list:
                    values.extend([v for v in value if v is not None])
                else:
                    values.append(value)

            if method == "count":
                result = len(values)
            else:
                result = self.compute(values)

        else:
            result = None

        return result

    # -------------------------------------------------------------------------
    def compute(self, values):
        """
            Aggregate a list of values.

            Args:
                values: iterable of values
        """

        if values is None:
            return None

        method = self.method
        values = [v for v in values if v != None]

        if method == "count":
            return len(values)
        elif method == "min":
            try:
                return min(values)
            except (TypeError, ValueError):
                return None
        elif method == "max":
            try:
                return max(values)
            except (TypeError, ValueError):
                return None
        elif method == "sum":
            try:
                return sum(values)
            except (TypeError, ValueError):
                return None
        elif method == "avg":
            try:
                num = len(values)
                if num:
                    return sum(values) / float(num)
            except (TypeError, ValueError):
                return None
        elif method == "cumulate":
            try:
                return sum(base + slope * duration
                           for base, slope, duration in values)
            except (TypeError, ValueError):
                return None
        return None

    # -------------------------------------------------------------------------
    @classmethod
    def parse(cls, fact):
        """
            Parse fact expression

            Args:
                fact: the fact expression
        """

        if isinstance(fact, list):
            facts = []
            for f in fact:
                facts.extend(cls.parse(f))
            if not facts:
                raise SyntaxError("Invalid fact expression: %s" % fact)
            return facts

        if isinstance(fact, tuple):
            label, fact = fact
        else:
            label = None

        # Parse the fact
        other = None
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
            else:
                raise SyntaxError("Invalid fact expression: %s" % fact)

        # Validate method
        if method not in cls.METHODS:
            raise SyntaxError("Unsupported aggregation method: %s" % method)

        # Extract parameters
        parameters = parameters.split(",")

        base = parameters[0]
        slope = None
        interval = None

        if method == "cumulate":
            if len(parameters) == 2:
                # Slope, Slots
                slope = base
                base = None
                interval = parameters[1]
            elif len(parameters) > 2:
                # Base, Slope, Slots
                slope = parameters[1]
                interval = parameters[2]

        facts = [cls(method, base, slope=slope, interval=interval, label=label)]
        if other:
            facts.extend(other)
        return facts

    # -------------------------------------------------------------------------
    def resolve(self, resource):
        """
            Resolve the base and slope selectors against resource

            Args:
                resource: the resource
        """

        self.resource = None

        base = self.base
        self.base_rfield = None
        self.base_column = base

        slope = self.slope
        self.slope_rfield = None
        self.slope_column = slope

        # Resolve base selector
        base_rfield = None
        if base:
            try:
                base_rfield = resource.resolve_selector(base)
            except (AttributeError, SyntaxError):
                base_rfield = None

        # Resolve slope selector
        slope_rfield = None
        if slope:
            try:
                slope_rfield = resource.resolve_selector(slope)
            except (AttributeError, SyntaxError):
                slope_rfield = None

        method = self.method

        # At least one field parameter must be resolvable
        if base_rfield is None:
            if method != "cumulate" or slope_rfield is None:
                raise SyntaxError("Invalid fact parameter")

        # All methods except count require numeric input values
        if method != "count":
            numeric_types = NUMERIC_TYPES
            if base_rfield and base_rfield.ftype not in numeric_types:
                raise SyntaxError("Fact field type not numeric: %s (%s)" %
                                  (base, base_rfield.ftype))

            if slope_rfield and slope_rfield.ftype not in numeric_types:
                raise SyntaxError("Fact field type not numeric: %s (%s)" %
                                  (slope, slope_rfield.ftype))

        if base_rfield:
            self.base_rfield = base_rfield
            self.base_column = base_rfield.colname

        if slope_rfield:
            self.slope_rfield = slope_rfield
            self.slope_column = slope_rfield.colname

        if not self.label:
            # Lookup the label from the timeplot options
            label = self.lookup_label(resource,
                                      method,
                                      base,
                                      slope,
                                      self.interval)
            if not label:
                # Generate a default label
                label = self.default_label(base_rfield, self.method)
            self.label = label

        self.resource = resource
        return self

    # -------------------------------------------------------------------------
    @classmethod
    def lookup_label(cls,
                     resource,
                     method,
                     base,
                     slope = None,
                     interval = None,
                     ):
        """
            Lookup the fact label from the timeplot options of resource

            Args:
                resource: the resource (CRUDResource)
                method: the aggregation method (string)
                base: the base field selector (string)
                slope: the slope field selector (string)
                interval: the interval expression (string)
        """

        fact_opts = None
        if resource:
            config = resource.get_config("timeplot_options")
            if config:
                fact_opts = config.get("fact")

        label = None
        if fact_opts:
            parse = cls.parse
            for opt in fact_opts:
                if isinstance(opt, tuple):
                    title, facts = opt
                else:
                    title, facts = None, opt
                facts = parse(facts)
                match = None
                for fact in facts:
                    if fact.method == method and \
                       fact.base == base and \
                       fact.slope == slope and \
                       fact.interval == interval:
                        match = fact
                        break
                if match:
                    if match.label:
                        label = match.label
                    elif len(facts) == 1:
                        label = title
                if label:
                    break

        return label

    # -------------------------------------------------------------------------
    @classmethod
    def default_label(cls, rfield, method):
        """
            Generate a default fact label

            Args:
                rfield: the S3ResourceField (alternatively the field label)
                method: the aggregation method
        """

        T = current.T

        if hasattr(rfield, "ftype") and \
           rfield.ftype == "id" and \
           method == "count":
            field_label = T("Records")
        elif hasattr(rfield, "label"):
            field_label = rfield.label
        else:
            field_label = rfield

        method_label = cls.METHODS.get(method)
        if not method_label:
            method_label = method
        else:
            method_label = T(method_label)

        return "%s (%s)" % (field_label, method_label)

# =============================================================================
class S3TimeSeriesEventFrame:
    """ The time frame of a time series """

    def __init__(self, start, end, slots=None):
        """
            Args:
                start: start of the time frame (datetime.datetime)
                end: end of the time frame (datetime.datetime)
                slot: length of time slots within the event frame,
                      format: "{n }[hour|day|week|month|year]{s}",
                      examples: "1 week", "3 months", "years"
        """

        # Start time is required
        if start is None:
            raise SyntaxError("start time required")
        self.start = tp_tzsafe(start)

        # End time defaults to now
        if end is None:
            end = datetime.datetime.utcnow()
        self.end = tp_tzsafe(end)

        self.empty = True
        self.baseline = None

        self.slots = slots
        self.periods = {}

        self.rule = self.get_rule()

    # -------------------------------------------------------------------------
    def get_rule(self):
        """
            Get the recurrence rule for the periods
        """

        slots = self.slots
        if not slots:
            return None

        return S3TimeSeriesPeriod.get_rule(self.start, self.end, slots)

    # -------------------------------------------------------------------------
    def extend(self, events):
        """
            Extend this time frame with events

            Args:
                events: iterable of events

            TODO integrate in constructor
            TODO handle self.rule == None
        """

        if not events:
            return
        empty = self.empty

        # Order events by start datetime
        events = sorted(events)

        rule = self.rule
        periods = self.periods

        # No point to loop over periods before the first event:
        start = events[0].start
        if start is None or start <= self.start:
            first = rule[0]
        else:
            first = rule.before(start, inc=True)

        current_events = {}
        previous_events = {}
        for start in rule.between(first, self.end, inc=True):

            # Compute end of this period
            end = rule.after(start)
            if not end:
                if start < self.end:
                    end = self.end
                else:
                    # Period start is at the end of the event frame
                    break

            # Find all current events
            last_index = None
            for index, event in enumerate(events):
                last_index = index
                if event.end and event.end < start:
                    # Event ended before this period
                    previous_events[event.event_id] = event
                elif event.start is None or event.start < end:
                    # Event starts before or during this period
                    current_events[event.event_id] = event
                else:
                    # Event starts only after this period
                    break

            # Add current events to current period
            period = periods.get(start)
            if period is None:
                period = periods[start] = S3TimeSeriesPeriod(start, end=end)
            for event in current_events.values():
                period.add_current(event)
            for event in previous_events.values():
                period.add_previous(event)

            empty = False

            # Remaining events
            events = events[last_index:] if last_index is not None else None
            if not events:
                # No more events
                break

            # Remove events which end during this period
            remaining = {}
            for event_id, event in current_events.items():
                if not event.end or event.end > end:
                    remaining[event_id] = event
                else:
                    previous_events[event_id] = event
            current_events = remaining

        self.empty = empty
        return

    # -------------------------------------------------------------------------
    def __iter__(self):
        """
            Iterate over all periods within this event frame
        """

        periods = self.periods

        rule = self.rule
        if rule:
            for dt in rule:
                if dt >= self.end:
                    break
                if dt in periods:
                    yield periods[dt]
                else:
                    end = rule.after(dt)
                    if not end:
                        end = self.end
                    yield S3TimeSeriesPeriod(dt, end=end)
        else:
            # @todo: continuous periods
            # sort actual periods and iterate over them
            raise NotImplementedError

        return

# =============================================================================
class S3TimeSeriesPeriod:
    """ A time period (slot) within an event frame """

    def __init__(self, start, end=None):
        """
            Args:
                start: the start of the time period (datetime)
                end: the end of the time period (datetime)
        """

        self.start = tp_tzsafe(start)
        self.end = tp_tzsafe(end)

        # Event sets
        self.pevents = {}
        self.cevents = {}

        self._matrix = None
        self._rows = None
        self._cols = None

        self.matrix = None
        self.rows = None
        self.cols = None
        self.totals = None

    # -------------------------------------------------------------------------
    def _reset(self):
        """ Reset the event matrix """

        self._matrix = None
        self._rows = None
        self._cols = None

        self.matrix = None
        self.rows = None
        self.cols = None
        self.totals = None

    # -------------------------------------------------------------------------
    def add_current(self, event):
        """
            Add a current event to this period

            Args:
                event: the S3TimeSeriesEvent
        """

        self.cevents[event.event_id] = event

    # -------------------------------------------------------------------------
    def add_previous(self, event):
        """
            Add a previous event to this period

            Args:
                event: the S3TimeSeriesEvent
        """

        self.pevents[event.event_id] = event

    # -------------------------------------------------------------------------
    def as_dict(self,
                rows = None,
                cols = None,
                isoformat = True,
                ):
        """
            Convert the aggregated results into a JSON-serializable dict

            Args:
                rows: the row keys for the result
                cols: the column keys for the result
                isoformat: convert datetimes into ISO-formatted strings
        """

        # Start and end datetime
        start = self.start
        if start and isoformat:
            start = start.isoformat()
        end = self.end
        if end and isoformat:
            end = end.isoformat()

        # Row totals
        row_totals = None
        if rows is not None:
            row_data = self.rows
            row_totals = [row_data.get(key) for key in rows]

        # Column totals
        col_totals = None
        if cols is not None:
            col_data = self.cols
            col_totals = [col_data.get(key) for key in cols]

        # Matrix
        matrix = None
        if rows is not None and cols is not None:
            matrix_data = self.matrix
            matrix = []
            for row in rows:
                matrix_row = []
                for col in cols:
                    matrix_row.append(matrix_data.get((row, col)))
                matrix.append(matrix_row)

        # Output
        return {"t": (start, end),
                "v": self.totals,
                "r": row_totals,
                "c": col_totals,
                "x": matrix,
                }

    # -------------------------------------------------------------------------
    def group(self, cumulative=False):
        """
            Group events by their row and col axis values

            Args:
                cumulative: include previous events
        """

        event_sets = [self.cevents]
        if cumulative:
            event_sets.append(self.pevents)

        rows = {}
        cols = {}
        matrix = {}
        from itertools import product
        for index, events in enumerate(event_sets):
            for event_id, event in events.items():
                for key in event.rows:
                    row = rows.get(key)
                    if row is None:
                        row = rows[key] = (set(), set())
                    row[index].add(event_id)
                for key in event.cols:
                    col = cols.get(key)
                    if col is None:
                        col = cols[key] = (set(), set())
                    col[index].add(event_id)
                for key in product(event.rows, event.cols):
                    cell = matrix.get(key)
                    if cell is None:
                        cell = matrix[key] = (set(), set())
                    cell[index].add(event_id)
        self._rows = rows
        self._cols = cols
        self._matrix = matrix

    # -------------------------------------------------------------------------
    def aggregate(self, facts):
        """
            Group and aggregate the events in this period

            Args:
                facts: list of facts to aggregate
        """

        # Reset
        self._reset()

        rows = self.rows = {}
        cols = self.cols = {}
        matrix = self.matrix = {}

        totals = []

        if not isinstance(facts, (list, tuple)):
            facts = [facts]
        if any(fact.method == "cumulate" for fact in facts):
            self.group(cumulative=True)
        else:
            self.group()

        for fact in facts:

            method = fact.method

            # Select events
            if method == "cumulate":
                events = dict(self.pevents)
                events.update(self.cevents)
                cumulative = True
            else:
                events = self.cevents
                cumulative = False

            aggregate = fact.aggregate

            # Aggregate rows
            for key, event_sets in self._rows.items():
                event_ids = event_sets[0]
                if cumulative:
                    event_ids |= event_sets[1]
                items = [events[event_id] for event_id in event_ids]
                if key not in rows:
                    rows[key] = [aggregate(self, items)]
                else:
                    rows[key].append(aggregate(self, items))

            # Aggregate columns
            for key, event_sets in self._cols.items():
                event_ids = event_sets[0]
                if cumulative:
                    event_ids |= event_sets[1]
                items = [events[event_id] for event_id in event_ids]
                if key not in cols:
                    cols[key] = [aggregate(self, items)]
                else:
                    cols[key].append(aggregate(self, items))

            # Aggregate matrix
            for key, event_sets in self._matrix.items():
                event_ids = event_sets[0]
                if cumulative:
                    event_ids |= event_sets[1]
                items = [events[event_id] for event_id in event_ids]
                if key not in matrix:
                    matrix[key] = [aggregate(self, items)]
                else:
                    matrix[key].append(aggregate(self, items))

            # Aggregate total
            totals.append(aggregate(self, list(events.values())))

        self.totals = totals
        return totals

    # -------------------------------------------------------------------------
    def duration(self, event, interval):
        """
            Compute the total duration of the given event before the end
            of this period, in number of interval

            Args:
                event: the S3TimeSeriesEvent
                interval: the interval expression (string)
        """

        if event.end is None or event.end > self.end:
            end_date = self.end
        else:
            end_date = event.end
        if event.start is None or event.start >= end_date:
            result = 0
        else:
            rule = self.get_rule(event.start, end_date, interval)
            if rule:
                result = rule.count()
            else:
                result = 1
        return result

    # -------------------------------------------------------------------------
    @staticmethod
    def get_rule(start, end, interval):
        """
            Convert a time slot string expression into a dateutil rrule
            within the context of a time period

            Args:
                start: the start of the time period (datetime)
                end: the end of the time period (datetime)
                interval: time interval expression, like "days" or "2 weeks"
        """

        match = re.match(r"\s*(\d*)\s*([hdwmy]{1}).*", interval)
        if match:
            num, delta = match.groups()
            deltas = {
                "h": HOURLY,
                "d": DAILY,
                "w": WEEKLY,
                "m": MONTHLY,
                "y": YEARLY,
            }
            if delta not in deltas:
                return None
            else:
                num = int(num) if num else 1
                return rrule(deltas[delta],
                             dtstart = start,
                             until = end,
                             interval = num,
                             )
        else:
            return None

# END =========================================================================
