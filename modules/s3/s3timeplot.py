# -*- coding: utf-8 -*-

""" S3 TimePlot Reports Method

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

import datetime
import re

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from dateutil.rrule import *
from itertools import izip, tee

from gluon import current
from gluon.storage import Storage
from gluon.html import *

from s3rest import S3Method

# =============================================================================
class S3TimePlot(S3Method):
    """ RESTful method for time plot reports """

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
            r.error(405, current.manager.ERROR.BAD_METHOD)
        return output

    # -------------------------------------------------------------------------
    def timeplot(self, r, **attr):
        """
            Pivot table report page

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """
        
        resource = self.resource
        table = resource.table

        method = "count"

        # Extract the relevant GET vars
        get_vars = dict((k, v) for k, v in r.get_vars.iteritems()
                        if k in ("timestamp", "fact"))

        # Fall back to report options defaults
        if not any (k in get_vars for k in ("timestamp", "fact")):
            timeplot_options = resource.get_config("timeplot_options", {})
            get_vars = timeplot_options.get("defaults", {})

        # Parse timestamp option
        timestamp = get_vars.get("timestamp", None)
        if timestamp:
            if "," in timestamp:
                start, end = timestamp.split(",", 1)
            else:
                start, end = timestamp, None
        else:
            start, end = None, None

        # Defaults
        if not start:
            for fname in ("date", "start_date", "created_on"):
                if fname in table.fields:
                    start = fname
                    break
            if not end:
                for fname in ("end_date",):
                    if fname in table.fields:
                        end = fname
                        break
        if not start:
            r.error(405, T("No time stamps found in this resource"))

        # Get the fields
        fields = [resource._id.name]
        start_colname = end_colname = fact_colname = None
        try:
            start_rfield = resource.resolve_selector(start)
        except (AttributeError, SyntaxError):
            r.error(405, T("Invalid start selector: %(selector)s" % {"selector": start}))
        else:
            fields.append(start)
            start_colname = start_rfield.colname
        if end:
            try:
                end_rfield = resource.resolve_selector(end)
            except (AttributeError, SyntaxError):
                r.error(405, T("Invalid end selector: %(selector)s" % {"selector": end}))
            else:
                fields.append(end)
                end_colname = end_rfield.colname
        fact = get_vars.get("fact", None)
        if fact:
            try:
                fact_rfield = resource.resolve_selector(fact)
            except (AttributeError, SyntaxError):
                r.error(405, T("Invalid fact selector: %(selector)s" % {"selector": fact}))
            else:
                fields.append(fact)
                fact_colname = fact_rfield.colname
                method = "sum"

        data = resource.select(fields)
        rows = data["rows"]

        items = []
        for row in rows:
            item = [row[str(resource._id)]]
            if start_colname:
                item.append(str(row[start_colname]))
            else:
                item.append(None)
            if end_colname:
                item.append(str(row[end_colname]))
            else:
                item.append(None)
            if fact:
                item.append(str(row[fact_colname]))
            else:
                item.append(None)
            items.append(item)
        items = json.dumps(items)

        widget_id = "timeplot"

        if r.representation in ("html", "iframe"):
            
            title = self.crud_string(resource.tablename, "title_report")
            
            output = {"title": title}
            
            form = FORM(DIV(_class="tp-chart", _style="height: 300px;"),
                        INPUT(_type="hidden",
                              _class="tp-data",
                              _value=items),
                        _class="tp-form",
                        _id = widget_id)

            output["form"] = form

            # View
            response = current.response
            response.view = self._view(r, "timeplot.html")

            # Script to attach the timeplot widget
            options = {"method": method}
            script = """$("#%(widget_id)s").timeplot(%(options)s);""" % \
                        {"widget_id": widget_id,
                         "options": json.dumps(options)
                        }
            response.s3.jquery_ready.append(script)
        
        elif r.representation == "json":

            output = items

        else:
            r.error(501, r.ERROR.BAD_FORMAT)

        return output

# =============================================================================
class S3TimePlotEvent(object):
    """ Class representing an event """

    def __init__(self,
                 event_id,
                 start=None,
                 end=None,
                 values=None,
                 event_type=None):
        """
            Constructor

            @param event_id: the event identifier
            @param start: start time of the event (datetime.datetime)
            @param end: end time of the event (datetime.datetime)
            @param values: a dict of attribute values for the event
            @param event_type: the event type identifier
        """

        self.event_type = event_type
        self.event_id = event_id

        self.start = start
        self.end = end
        
        self.values = values if values is not None else {}
        
    # -------------------------------------------------------------------------
    def __lt__(self, other):

        this = self.start
        that = other.start
        if this is None:
            result = that is not None
        elif that is None:
            result = False
        else:
            result = this < that
        return result
        
    # -------------------------------------------------------------------------
    def __getitem__(self, field):
        """
            Access attribute values of this event

            @param field: the attribute field name
        """

        return self.values.get(field, None)

# =============================================================================
class S3TimePlotPeriod(object):
    """ Class representing a period within the time frame """

    def __init__(self, start, end=None):
        """
            Constructor

            @param start: start time of the period (datetime.datetime)
            @param end: end time of the period (datetime.datetime)
        """

        self.start = start
        self.end = end

        # Event sets, structure: {event_type: {event_id: event}}
        self.sets = {}

    # -------------------------------------------------------------------------
    def add(self, event):
        """
            Add an event to this period

            @param event: the event (S3TimePlotEvent)
        """

        sets = self.sets
        
        # Find the event set by type
        event_type = event.event_type
        if event_type not in sets:
            events = sets[event_type] = {}
        else:
            events = sets[event_type]

        # Add the event to the set
        events[event.event_id] = event
        return

    # -------------------------------------------------------------------------
    def aggregate(self, method="count", field=None, event_type=None):
        """
            Aggregate event data in this period

            @param event_type: the event type
            @param field: the attribute to aggregate
            @param method: the aggregation method
        """

        if field is None and method == "count":
            return self.count(event_type)
        else:
            events = self.events(event_type)

            if field:
                values = []
                for event in events:
                    value = event[field]
                    if value is None:
                        continue
                    elif type(value) is list:
                        values.extend([v for v in value if v is not None])
                    else:
                        values.append(value)
                if method == "count":
                    return len(values)
                else:
                    return self._aggregate(method, values)
            else:
                return None

    # -------------------------------------------------------------------------
    @staticmethod
    def _aggregate(method, values):
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
        return None

    # -------------------------------------------------------------------------
    def events(self, event_type=None):
        """
            Return a list of all events

            @param event_type: the event type identifier (string)
        """
        
        events = {}
        sets = self.sets
        if event_type in sets:
            events = sets[event_type]
        return events.values()

    # -------------------------------------------------------------------------
    def count(self, event_type=None):
        """
            Get the number of events of the given type within this period

            @param event_type: the event type identifier (string)
        """

        sets = self.sets
        if event_type in sets:
            return len(sets[event_type])
        else:
            return 0

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
        self.start = start

        # End time defaults to now
        if end is None:
            end = datetime.datetime.utcnow()
        self.end = end

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

        match = re.match("\s*(\d*)\s*([hdwmy]{1}).*", slots)
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
                # @todo: handle "continuous" and "automatic"
                return None
            else:
                num = int(num) if num else 1
                return rrule(deltas[delta],
                             dtstart=self.start,
                             until=self.end,
                             interval=num)
        else:
            return None

    # -------------------------------------------------------------------------
    def extend(self, events):
        """
            Extend this time frame with events

            @param events: iterable of events

            @todo: integrate in constructor
            @todo: handle self.rule == None
        """

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

        current = []
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
                    # Event ends before this period
                    continue
                elif event.start is None or event.start < end:
                    # Event starts before or during this period
                    current.append(event)
                else:
                    # Event starts only after this period
                    break

            # Add current events to current period
            period = periods.get(start)
            if period is None:
                period = periods[start] = S3TimePlotPeriod(start, end=end)
            for event in current:
                period.add(event)

            # Remaining events
            events = events[index:]
            if not events:
                # No more events
                break

            # Remove events which end during this period
            current = [event for event in current
                       if not event.end or event.end > end]
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
