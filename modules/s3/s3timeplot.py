# -*- coding: utf-8 -*-

""" S3 TimePlot Reports Method

    @copyright: 2013-2014 (c) Sahana Software Foundation
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
           "S3TimePlotEvent",
           "S3TimePlotEventFrame",
           "S3TimePlotPeriod",
           )

import datetime
import dateutil.tz
import re
import sys

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from dateutil.relativedelta import *
from dateutil.rrule import *
from itertools import izip, tee

from gluon import current
from gluon.storage import Storage
from gluon.html import *
from gluon.validators import IS_IN_SET
from gluon.sqlhtml import OptionsWidget

from s3rest import S3Method
from s3query import FS
from s3report import S3ReportForm
from s3utils import s3_flatlist

tp_datetime = lambda *t: datetime.datetime(tzinfo=dateutil.tz.tzutc(), *t)

tp_tzsafe = lambda dt: dt.replace(tzinfo=dateutil.tz.tzutc()) \
                       if dt and dt.tzinfo is None else dt

# Compact JSON encoding
SEPARATORS = (",", ":")
DEFAULT = lambda: None

# =============================================================================
class S3TimePlot(S3Method):
    """ RESTful method for time plot reports """

    dt_regex = Storage(
        YEAR = re.compile("\A\s*(\d{4})\s*\Z"),
        YEAR_MONTH = re.compile("\A\s*(\d{4})-([0]*[1-9]|[1][12])\s*\Z"),
        MONTH_YEAR = re.compile("\A\s*([0]*[1-9]|[1][12])/(\d{4})\s*\Z"),
        DATE = re.compile("\A\s*(\d{4})-([0]?[1-9]|[1][12])-([012]?[1-9]|[3][01])\s*\Z"),
        DELTA = re.compile("\A\s*([+-]?)\s*(\d+)\s*([ymwdh])\w*\s*\Z"),
    )

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Page-render entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        if r.http == "GET":
            output = self.timeplot(r, **attr)
        else:
            r.error(405, current.ERROR.BAD_METHOD)
        return output

    # -------------------------------------------------------------------------
    # @todo: widget-method
    # -------------------------------------------------------------------------
    def timeplot(self, r, **attr):
        """
            Time plot report page

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        output = {}

        # Extract the relevant GET vars
        # @todo: option for grouping
        report_vars = ("timestamp",
                       "fact",
                       "start",
                       "end",
                       "slots",
                       "baseline",
                       )
        get_vars = dict((k, v) for k, v in r.get_vars.iteritems()
                        if k in report_vars)

        # Execute on component?
        resource = self.resource
        alias = r.get_vars.get("component")
        if alias and alias not in (resource.alias, "~"):
            if alias not in resource.components:
                hook = current.s3db.get_component(resource.tablename, alias)
                if hook:
                    resource._attach(alias, hook)
            if alias in resource.components:
                resource = resource.components[alias]

        tablename = resource.tablename
        get_config = resource.get_config

        # Apply filter defaults (before rendering the data!)
        show_filter_form = False
        if r.representation in ("html", "iframe"):
            filter_widgets = get_config("filter_widgets", None)
            if filter_widgets and not self.hide_filter:
                from s3filter import S3FilterForm
                show_filter_form = True
                S3FilterForm.apply_filter_defaults(r, resource)

        # Fall back to report options defaults
        report_options = resource.get_config("timeplot_options", {})
        defaults = report_options.get("defaults", {})
        if not any(k in get_vars for k in report_vars):
            get_vars = defaults
        else:
            # Optional URL args always fall back to config:
            optional = ("timestamp",)
            for opt in optional:
                if opt not in get_vars and opt in defaults:
                    get_vars[opt] = defaults[opt]

        # Parse event timestamp option
        timestamp = get_vars.get("timestamp")
        try:
            event_start, event_end = self.resolve_timestamp(resource,
                                                            timestamp)
        except (SyntaxError, AttributeError):
            r.error(400, sys.exc_info()[1])

        # Parse fact option
        fact = get_vars.get("fact")
        try:
            method, base, slope, interval = self.resolve_fact(resource, fact)
        except (SyntaxError, AttributeError):
            r.error(400, sys.exc_info()[1])

        # Create event frame
        start = get_vars.get("start")
        end = get_vars.get("end")
        slots = get_vars.get("slots")
        try:
            event_frame = self.create_event_frame(resource,
                                                  event_start,
                                                  event_end,
                                                  start,
                                                  end,
                                                  slots,
                                                  )
        except (SyntaxError, ValueError):
            r.error(400, sys.exc_info()[1])

        # Add event data
        baseline = get_vars.get("baseline")
        try:
            self.add_event_data(event_frame,
                                resource,
                                event_start,
                                event_end,
                                (base, slope),
                                baseline= baseline,
                                cumulative = method == "cumulate",
                                )
        except SyntaxError:
            pass

        # Iterate over the event frame to collect aggregates
        items = []
        new_item = items.append
        for period in event_frame:
            item_start = period.start
            if item_start:
                item_start = item_start.isoformat()
            item_end = period.end
            if item_end:
                item_end = item_end.isoformat()
            value = period.aggregate(method,
                                     base.colname,
                                     slope=slope.colname,
                                     interval=interval,
                                     )
            new_item((item_start, item_end, value))

        # Timeplot data
        data = {"items": items,
                "empty": event_frame.empty,
                "baseline": event_frame.baseline,
                }

        # Widget ID
        widget_id = "timeplot"

        # Render output
        if r.representation in ("html", "iframe"):
            # Page load

            output["title"] = self.crud_string(tablename, "title_report")

            # Filter widgets
            if show_filter_form:
                advanced = False
                for widget in filter_widgets:
                    if "hidden" in widget.opts and widget.opts.hidden:
                        advanced = get_config("report_advanced", True)
                        break
                filter_formstyle = get_config("filter_formstyle", None)
                filter_form = S3FilterForm(filter_widgets,
                                           formstyle=filter_formstyle,
                                           advanced=advanced,
                                           submit=False,
                                           _class="filter-form",
                                           _id="%s-filter-form" % widget_id,
                                           )
                fresource = current.s3db.resource(tablename)
                alias = resource.alias if resource.parent else None
                filter_widgets = filter_form.fields(fresource,
                                                    r.get_vars,
                                                    alias=alias,
                                                    )
            else:
                # Render as empty string to avoid the exception in the view
                filter_widgets = None

            ajax_vars = Storage(r.get_vars)
            ajax_vars.update(get_vars)
            filter_url = url=r.url(method="",
                                   representation="",
                                   vars=ajax_vars.fromkeys((k for k in ajax_vars
                                                            if k not in report_vars)))
            ajaxurl = attr.get("ajaxurl", r.url(method="timeplot",
                                                representation="json",
                                                vars=ajax_vars,
                                                ))

            output["form"] = S3TimePlotForm(resource) \
                                           .html(data,
                                                 get_vars = get_vars,
                                                 filter_widgets = filter_widgets,
                                                 ajaxurl = ajaxurl,
                                                 filter_url = filter_url,
                                                 widget_id = widget_id,
                                                 )

            # View
            response = current.response
            response.view = self._view(r, "timeplot.html")

        elif r.representation == "json":
            # Ajax load

            output = json.dumps(data, separators=SEPARATORS)

        else:
            r.error(501, current.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def add_event_data(self,
                       event_frame,
                       resource,
                       event_start,
                       event_end,
                       facts,
                       cumulative=False,
                       baseline=None):
        """
            Extract event data from resource and add them to the
            event frame

            @param event_frame: the event frame
            @param resource: the resource
            @param event_start: the event start field (S3ResourceField)
            @param event_end: the event_end field (S3ResourceField)
            @param fact: list of fact fields (S3ResourceField)
            @param cumulative: whether the aggregation method is cumulative
            @param baseline: field selector to extract the baseline value (e.g.
                             for burn-down visualization)

            @return: the extracted data (dict from S3Resource.select)
        """

        # Fields to extract
        fields = set(fact.selector for fact in facts if fact is not None)
        if event_start:
            fields.add(event_start.selector)
        else:
            return None
        if event_end:
            fields.add(event_end.selector)
        fields.add(resource._id.name)

        # Filter by event frame start:
        # End date of events must be after the event frame start date
        if not cumulative and event_end:
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
        if baseline:
            try:
                rfield = resource.resolve_selector(baseline)
            except (AttributeError, SyntaxError):
                current.log.error(sys.exc_info[1])
            else:
                if rfield.field and rfield.ftype in ("integer", "double"):
                    # Don't need s3db here - if there's an rfield.field,
                    # then there's also a table!
                    baseline_table = current.db[rfield.tname]
                    pkey = str(baseline_table._id)
                    colname = rfield.colname
                    rows = resource.select([baseline],
                                           groupby = [pkey, colname],
                                           as_rows = True,
                                           )
                    value = 0
                    for row in rows:
                        v = row[colname]
                        if v is not None:
                            value += v
                else:
                    current.log.error("Invalid field type for baseline")
        event_frame.baseline = value

        # Extract the records
        data = resource.select(fields)

        # Remove the filter we just added
        resource.rfilter.filters.pop()
        resource.rfilter.query = None

        # Do we need to convert dates into datetimes?
        convert_start = True if event_start.ftype == "date" else False
        convert_end = True if event_start.ftype == "date" else False
        fromordinal = datetime.datetime.fromordinal
        convert_date = lambda d: fromordinal(d.toordinal())

        # Column names for extractions
        pkey = str(resource._id)
        start_colname = event_start.colname
        end_colname = event_end.colname if event_end else None

        # Use table name as event type
        tablename = resource.tablename

        # Create the events
        events = []
        add_event = events.append
        for row in data.rows:
            values = dict((fact.colname, row[fact.colname])
                          for fact in facts)
            start = row[start_colname]
            if convert_start and start:
                start = convert_date(start)
            end = row[end_colname] if end_colname else None
            if convert_end and end:
                end = convert_date(end)
            event = S3TimePlotEvent(row[pkey],
                                    start = start,
                                    end = end,
                                    values = values)
            add_event(event)

        # Extend the event frame with these events
        if events:
            event_frame.extend(events)
        return data

    # -------------------------------------------------------------------------
    def create_event_frame(self,
                           resource,
                           event_start,
                           event_end,
                           start=None,
                           end=None,
                           slots=None):
        """
            Create an event frame for this report

            @param resource: the target resource
            @param event_start: the event start field (S3ResourceField)
            @param event_end: the event end field (S3ResourceField)
            @param start: the start date/time (string)
            @param end: the end date/time (string)
            @param slots: the slot length (string)

            @return: the event frame
        """

        now = tp_tzsafe(datetime.datetime.utcnow())

        dtparse = self.dtparse

        start_dt = end_dt = None

        STANDARD_SLOT = "1 day"

        # Parse start and end time
        if start:
            start_dt = dtparse(start, start=now)
        if end:
            relative_to = start_dt if start_dt else now
            end_dt = dtparse(end, start=relative_to)

        # Fall back to now if internval end is not specified
        if not end_dt:
            end_dt = now

        if not start_dt and event_start and event_start.field:
            # No interval start => fall back to first event start
            query = FS(event_start.selector) != None
            resource.add_filter(query)
            rows = resource.select([event_start.selector],
                                    limit=1,
                                    orderby=event_start.field,
                                    as_rows=True)
            # Remove the filter we just added
            resource.rfilter.filters.pop()
            resource.rfilter.query = None
            if rows:
                first_event = rows.first()[event_start.colname]
                if isinstance(first_event, datetime.date):
                    first_event = tp_tzsafe(datetime.datetime.fromordinal(first_event.toordinal()))
                start_dt = first_event

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
            resource.rfilter.filters.pop()
            resource.rfilter.query = None
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

        if not slots:
            # No slot length =>
            # Determine optimum slot length automatically
            # @todo: determine from density of events rather than
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

        return S3TimePlotEventFrame(start_dt, end_dt, slots)

    # -------------------------------------------------------------------------
    @classmethod
    def dtparse(cls, timestr, start=None):
        """
            Parse a string for start/end date(time) of an interval

            @param timestr: the time string
            @param start: the start datetime to relate relative times to
        """

        if start is None:
            start = tp_tzsafe(datetime.datetime.utcnow())

        if not timestr:
            return start

        regex = cls.dt_regex

        # Relative to start: [+|-]{n}[year|month|week|day|hour]s
        match = regex.DELTA.match(timestr)
        if match:
            groups = match.groups()
            intervals = {"y": "years",
                         "m": "months",
                         "w": "weeks",
                         "d": "days",
                         "h": "hours"}
            length = intervals.get(groups[2])
            if not length:
                raise SyntaxError("Invalid date/time: %s" % timestr)
            num = int(groups[1])
            if not num:
                return start
            if groups[0] == "-":
                num *= -1
            return start + relativedelta(**{length: num})

        # Month/Year, e.g. "5/2001"
        match = regex.MONTH_YEAR.match(timestr)
        if match:
            groups = match.groups()
            year = int(groups[1])
            month = int(groups[0])
            return tp_datetime(year, month, 1, 0, 0, 0)

        # Year-Month, e.g. "2001-05"
        match = regex.YEAR_MONTH.match(timestr)
        if match:
            groups = match.groups()
            month = int(groups[1])
            year = int(groups[0])
            return tp_datetime(year, month, 1, 0, 0, 0)

        # Year only, e.g. "1996"
        match = regex.YEAR.match(timestr)
        if match:
            groups = match.groups()
            year = int(groups[0])
            return tp_datetime(year, 1, 1, 0, 0, 0)

        # Date, e.g. "2013-01-04"
        match = regex.DATE.match(timestr)
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
        xml = current.xml
        dt = xml.decode_iso_datetime(str(timestr))
        return xml.as_utc(dt)

    # -------------------------------------------------------------------------
    @staticmethod
    def resolve_timestamp(resource, timestamp):
        """
            Resolve a timestamp parameter against the current resource.

            @param resource: the S3Resource
            @param timestamp: the time stamp specifier
        """

        # Parse timestamp option
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

        # Defaults
        if not start:
            table = resource.table
            for fname in ("date", "start_date", "created_on"):
                if fname in table.fields:
                    start = fname
                    break
            if start and not end:
                for fname in ("end_date",):
                    if fname in table.fields:
                        end = fname
                        break
        if not start:
            raise SyntaxError("No time stamps found in %s" % table)

        # Get the fields
        start_rfield = resource.resolve_selector(start)
        if end:
            end_rfield = resource.resolve_selector(end)
        else:
            end_rfield = None
        return start_rfield, end_rfield

    # -------------------------------------------------------------------------
    @staticmethod
    def resolve_fact(resource, fact):
        """
            Resolve a fact parameter of the format "method(selector)"
            against a resource.

            @param resource: the S3Resource
            @param fact: the fact parameter
        """

        # Parse the fact
        if not fact:
            method, parameters = "count", "id"
        else:
            match = re.match("([a-zA-Z]+)\(([a-zA-Z0-9_.$:\,]+)\)\Z", fact)
            if match:
                method, parameters = match.groups()
            else:
                method, parameters = "count", fact

        # Validate method
        if method not in S3TimePlotPeriod.methods:
            raise SyntaxError("Unsupported aggregation method: %s" % method)

        parameters = parameters.split(",")
        base = parameters[0]
        
        cumulate = method == "cumulate"
        
        slope = None
        interval = None
        if cumulate:
            if len(parameters) == 2:
                # Slope, Slots
                slope = base
                base = None
                interval = parameters[1]
            elif len(parameters) > 2:
                # Base, Slope, Slots
                slope = parameters[1]
                interval = parameters[2]
                
        base_rfield = None
        if base:
            try:
                base_rfield = resource.resolve_selector(base)
            except (AttributeError, SyntaxError):
                base_rfield = None
                
        slope_rfield = None
        if slope:
            try:
                slope_rfield = resource.resolve_selector(slope)
            except (AttributeError, SyntaxError):
                slope_rfield = None
            
        if base_rfield is None:
            if not cumulate or slope_rfield is None:
                raise SyntaxError("Invalid fact parameter")
            
        if method != "count":
            # All methods except count require numeric input values
            numeric_types = ("integer", "double")
            if base_rfield and base_rfield.ftype not in numeric_types:
                raise SyntaxError("Fact field type not numeric: %s (%s)" % 
                                  (base, base_rfield.ftype))

            if slope_rfield and slope_rfield.ftype not in numeric_types:
                raise SyntaxError("Fact field type not numeric: %s (%s)" % 
                                  (slope, slope_rfield.ftype))

        return method, base_rfield, slope_rfield, interval

# =============================================================================
class S3TimePlotForm(S3ReportForm):
    """ Helper class to render a report form """

    def __init__(self, resource):

        self.resource = resource

    # -------------------------------------------------------------------------
    def html(self,
             data,
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

        # Filter options
        if filter_widgets is not None:
            filter_options = self._fieldset(T("Filter Options"),
                                            filter_widgets,
                                            _id="%s-filters" % widget_id,
                                            _class="filter-form")
        else:
            filter_options = ""

        # Report options
        report_options = self.report_options(get_vars = get_vars,
                                             widget_id = widget_id)

        hidden = {"tp-data": json.dumps(data, separators=SEPARATORS)}


        # @todo: report options
        # @todo: chart title
        # @todo: empty-section
        # @todo: CSS

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
            submit = TAG[""](
                        INPUT(_type="button",
                              _value=label,
                              _class=_class))
        else:
            submit = ""

        form = DIV(DIV(FORM(filter_options,
                            report_options,
                            submit,
                            hidden = hidden,
                            _class = "tp-form",
                            _id = "%s-tp-form" % widget_id,
                            ),
                       _class="tp-form-container form-container",
                       ),
                   DIV(DIV(_class="inline-throbber tp-throbber"),
                       DIV(#DIV(_class="tp-chart-controls"),
                           DIV(#DIV(_class="tp-hide-chart"),
                               #DIV(_class="tp-chart-title"),
                               DIV(_class="tp-chart"),
                               _class="tp-chart-contents"
                           ),
                           _class="tp-chart-container"
                       ),
                       #DIV(empty, _class="tp-empty"),
                   ),
                   _class="tp-container",
                   _id=widget_id
               )

        # Script to attach the timeplot widget

        settings = current.deployment_settings
        options = {
            "ajaxURL": ajaxurl,
            "autoSubmit": settings.get_ui_report_auto_submit(),
            "emptyMessage": str(T("No data available for this time interval")),
        }
        script = """$("#%(widget_id)s").timeplot(%(options)s)""" % \
                    {"widget_id": widget_id,
                     "options": json.dumps(options),
                    }
        current.response.s3.jquery_ready.append(script)

        return form

    # -------------------------------------------------------------------------
    def report_options(self, get_vars=None, widget_id="timeplot"):
        """
            Render the widgets for the report options form

            @param get_vars: the GET vars if the request (as dict)
            @param widget_id: the HTML element base ID for the widgets
        """

        T = current.T

        timeplot_options = self.resource.get_config("timeplot_options")

        selectors = []

        # @todo: formstyle may not be executable => convert
        formstyle = current.deployment_settings.get_ui_filter_formstyle()

        # Report type selector
        # @todo: implement
        #fact_selector = self.fact_options(options = timeplot_options,
                                          #get_vars = get_vars,
                                          #widget_id = "%s-fact" % widget_id,
                                          #)
        #selectors.append(formstyle("%s-fact__row" % widget_id,
                                   #"Label",
                                   #fact_selector,
                                   #None,
                                   #))

        # Time frame selector
        time_selector = self.time_options(options = timeplot_options,
                                          get_vars = get_vars,
                                          widget_id = "%s-time" % widget_id,
                                          )
        selectors.append(formstyle("%s-time__row" % widget_id,
                                   "Time Frame",
                                   time_selector,
                                   None,
                                   ))

        # Render container according to row type
        if selectors[0].tag == "tr":
            selectors = TABLE(selectors)
        else:
            selectors = TAG[""](selectors)

        # Render field set
        fieldset = self._fieldset(T("Report Options"),
                                  selectors,
                                  _id="%s-options" % widget_id)

        return fieldset

    # -------------------------------------------------------------------------
    def time_options(self,
                     options=None,
                     get_vars=None,
                     widget_id=None):

        T = current.T

        resource = self.resource
        prefix = resource.prefix_selector

        # Time options:
        if options and "time" in options:
            opts = options["time"]
        else:
            # (label, start, end, slots)
            # If you specify a start, then end is relative to that - without start, end is relative to now
            opts = (("All up to now", "", "", ""),
                    ("Last Year", "-1year", "", "months"),
                    ("Last 6 Months", "-6months", "", "weeks"),
                    ("Last Quarter", "-3months", "", "weeks"),
                    ("Last Month", "-1month", "", "days"),
                    ("Last Week", "-1week", "", "days"),
                    ("All/+1 Month", "", "+1month", ""),
                    ("All/+2 Month", "", "+2month", ""),
                    ("-6/+3 Months", "-6months", "+9months", "months"),
                    ("-3/+1 Months", "-3months", "+4months", "weeks"),
                    ("-4/+2 Weeks", "-4weeks", "+6weeks", "weeks"),
                    ("-2/+1 Weeks", "-2weeks", "+3weeks", "days"),
                    )

        widget_opts = []
        for opt in opts:
            label, start, end, slots = opt
            widget_opts.append(("|".join((start, end, slots)), T(label)))

        # Get current value
        if get_vars:
            start = get_vars.get("start", "")
            end = get_vars.get("end", "")
            slots = get_vars.get("slots", "")
        else:
            start = end = slots = ""
        value = "|".join((start, end, slots))

        # Dummy field
        dummy_field = Storage(name="time",
                              requires=IS_IN_SET(widget_opts))

        # Construct widget
        return OptionsWidget.widget(dummy_field,
                                    value,
                                    _id=widget_id,
                                    _name="time",
                                    _class="tp-time",
                                    )

# =============================================================================
class S3TimePlotEvent(object):
    """ Class representing an event """
    
    def __init__(self,
                 event_id,
                 start=None,
                 end=None,
                 values=None,
                 row=DEFAULT,
                 col=DEFAULT):
        """
            Constructor

            @param event_id: a unique identifier for the event (e.g. record ID)
            @param start: start time of the event (datetime.datetime)
            @param end: end time of the event (datetime.datetime)
            @param values: a dict of key-value pairs with the attribute
                           values for the event
            @param row: the series row for this event
            @param col: the series column for this event
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
            
            @param value: the field value
        """

        if value is DEFAULT:
            series = set()
        elif value is None:
            series = set([None])
        elif type(value) is list:
            series = set(s3_flatlist(value))
        else:
            series = set([value])
        return series

    # -------------------------------------------------------------------------
    def __getitem__(self, field):
        """
            Access attribute values of this event

            @param field: the attribute field name
        """

        return self.values.get(field, None)

    # -------------------------------------------------------------------------
    def __lt__(self, other):
        """
            Comparison method to allow sorting of events

            @param other: the event to compare to
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
class S3TimePlotPeriod(object):

    methods = ("count", "cumulate", "sum", "avg", "min", "max")

    def __init__(self, start, end=None):
        """
            Constructor
            
            @param start: the start of the time period (datetime)
            @param end: the end of the time period (datetime)
        """

        self.start = tp_tzsafe(start)
        self.end = tp_tzsafe(end)

        # Event sets
        self.pevents = {}
        self.cevents = {}

        self._reset()

    # -------------------------------------------------------------------------
    def _reset(self):
        """ Reset the event matrix """

        self._matrix = None
        self._rows = None
        self._cols = None

        self._reset_aggregates()

        return

    # -------------------------------------------------------------------------
    def _reset_aggregates(self):
        """ Reset the aggregated values matrix """

        self.matrix = None
        self.rows = None
        self.cols = None
        self.total = None

        return

    # -------------------------------------------------------------------------
    def add_current(self, event):
        """
            Add a current event to this period

            @param event: the S3TimePlotEvent
        """

        self.cevents[event.event_id] = event

    # -------------------------------------------------------------------------
    def add_previous(self, event):
        """
            Add a previous event to this period

            @param event: the S3TimePlotEvent
        """

        self.pevents[event.event_id] = event

    # -------------------------------------------------------------------------
    def group(self, cumulative=False):
        """ 
            Group events by their row and col axis values 

            @param cumulative: include previous events
        """

        if cumulative:
            events = dict(self.pevents)
            events.update(self.cevents)
        else:
            events = self.cevents
        rows = {}
        cols = {}
        matrix = {}
        from itertools import product
        for event_id, event in events.items():
            for key in event.rows:
                row = rows.get(key)
                if row is None:
                    row = rows[key] = set()
                row.add(event_id)
            for key in event.cols:
                col = cols.get(key)
                if col is None:
                    col = cols[key] = set()
                col.add(event_id)
            for key in product(event.rows, event.cols):
                cell = matrix.get(key)
                if cell is None:
                    cell = matrix[key] = set()
                cell.add(event_id)
        self._rows = rows
        self._cols = cols
        self._matrix = matrix

    # -------------------------------------------------------------------------
    def aggregate(self, method, base, slope=None, interval=None):
        """
            Group and aggregate (=pivot) the events in this period

            @param method: the aggregation method
            @param base: column name of the (base) field
            @param slope: column name of the slope field (for cumulative values)
            @param interval: time interval expression for the slope
        """

        # Reset
        self._reset()
        
        # Select events
        if method == "cumulate":
            events = dict(self.pevents)
            events.update(self.cevents)
            cumulative = True
        elif method in self.methods:
            events = self.cevents
            cumulative = False
        else:
            raise SyntaxError("Unsupported aggregation function: %s" % method)

        # Group events
        self.group(cumulative = cumulative)

        _aggregate = self._aggregate
        aggregate = lambda items: _aggregate(items,
                                             method,
                                             base,
                                             slope=slope,
                                             interval=interval,
                                             )

        # Aggregate rows
        rows = self.rows = {}
        for key, event_ids in self._rows.items():
            items = [events[event_id] for event_id in event_ids]
            rows[key] = aggregate(items)

        # Aggregate columns
        cols = self.cols = {}
        for key, event_ids in self._cols.items():
            items = [events[event_id] for event_id in event_ids]
            cols[key] = aggregate(items)

        # Aggregate matrix
        matrix = self.matrix = {}
        for key, event_ids in self._matrix.items():
            items = [events[event_id] for event_id in event_ids]
            matrix[key] = aggregate(items)

        # Aggregate total
        total = aggregate(events.values())

        self.total = total
        return total

    # -------------------------------------------------------------------------
    def _aggregate(self, events, method, base, slope=None, interval=None):
        """
            Aggregate values from events.

            @param events: the events
            @param method: the aggregation method (string)
            @param base: column name of the (base) field
            @param slope: column name of the slope field (for cumulative values)
            @param interval: time interval expression for the slope
        """

        values = []
        append = values.append

        if method == "cumulate":
            
            duration = self._duration

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

                if slope_value and interval:
                    event_duration = duration(event, interval)
                else:
                    event_duration = 1

                append((base_value, slope_value, event_duration))

            result = self._compute(method, values)

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
                result = self._compute(method, values)

        else:
            result = None
            
        return result

    # -------------------------------------------------------------------------
    @staticmethod
    def _compute(method, values):
        """
            Aggregate a list of values with the given method

            @param method: the aggregation method as string
            @param values: iterable of values
        """

        if values is None:
            return None
        else:
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
        elif method in ("avg"):
            try:
                num = len(values)
                if num:
                    return sum(values) / float(num)
            except (TypeError, ValueError):
                return None
        elif method in ("cumulate"):
            try:
                return sum(base + slope * duration
                           for base, slope, duration in values)
            except (TypeError, ValueError):
                return None
        return None

    # -------------------------------------------------------------------------
    def _duration(self, event, interval):
        """
            Compute the total duration of the given event before the end
            of this period, in number of interval

            @param event: the S3TimePlotEvent
            @param interval: the interval expression (string)
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

            @param start: the start of the time period (datetime)
            @param end: the end of the time period (datetime)
            @param interval: time interval expression, like "days" or "2 weeks"
        """

        match = re.match("\s*(\d*)\s*([hdwmy]{1}).*", interval)
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
                             dtstart=start,
                             until=end,
                             interval=num)
        else:
            return None

# =============================================================================
class S3TimePlotEventFrame(object):
    """ Class representing the whole time frame of a time plot """

    def __init__(self, start, end, slots=None):
        """
            Constructor

            @param start: start of the time frame (datetime.datetime)
            @param end: end of the time frame (datetime.datetime)
            @param slot: length of time slots within the event frame,
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

        return S3TimePlotPeriod.get_rule(self.start, self.end, slots)

    # -------------------------------------------------------------------------
    def extend(self, events):
        """
            Extend this time frame with events

            @param events: iterable of events

            @todo: integrate in constructor
            @todo: handle self.rule == None
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
            for index, event in enumerate(events):
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
                period = periods[start] = S3TimePlotPeriod(start, end=end)
            for event in current_events.values():
                period.add_current(event)
            for event in previous_events.values():
                period.add_previous(event)

            empty = False

            # Remaining events
            events = events[index:]
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
                    yield S3TimePlotPeriod(dt, end=end)
        else:
            # @todo: continuous periods
            # sort actual periods and iterate over them
            raise NotImplementedError

        return

# END =========================================================================
