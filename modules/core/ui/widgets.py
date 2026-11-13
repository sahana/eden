"""
    Form Widgets

    Copyright: 2009-2023 (c) Sahana Software Foundation

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

__all__ = ("S3AgeWidget",
           "S3CascadeSelectWidget",
           "S3ColorPickerWidget",
           "S3CalendarWidget",
           "S3DateWidget",
           "S3DateTimeWidget",
           "S3HoursWidget",
           "S3EmbeddedComponentWidget",
           "S3GroupedOptionsWidget",
           "S3HiddenWidget",
           "S3HierarchyWidget",
           "S3ImageCropWidget",
           "ImageUploadWidget",
           "S3InvBinWidget",
           "S3KeyValueWidget",
           # Only used inside this module
           #"S3LatLonWidget",
           "S3LocationDropdownWidget",
           "S3LocationLatLonWidget",
           "S3PasswordWidget",
           "S3PhoneWidget",
           "S3QRInput",
           "S3MultiSelectWidget",
           "EmptyOptionsWidget",
           "S3SelectWidget",
           "S3SliderWidget",
           "S3StringWidget",
           "S3TimeIntervalWidget",
           #"S3UploadWidget",
           "S3WeeklyHoursWidget",
           "CheckboxesWidgetS3",
           "s3_comments_widget",
           "s3_richtext_widget",
           "S3TagCheckboxWidget",
           )

import datetime
import json
import locale
import os
import re

from io import BytesIO
from uuid import uuid4

try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    import sys
    sys.stderr.write("ERROR: dateutil module needed for Date handling\n")
    raise

from gluon import current, URL, Field, \
                  BUTTON, LABEL, A, DIV, FIELDSET, HR, IMG, INPUT, LEGEND, LI, \
                  OPTGROUP, OPTION, SCRIPT, SELECT, SPAN, TABLE, TAG, TD, TEXTAREA, \
                  TR, UL, \
                  IS_EMPTY_OR, IS_FLOAT_IN_RANGE, IS_INT_IN_RANGE, IS_IN_SET
from gluon.languages import lazyT
from gluon.sqlhtml import DoubleWidget, FormWidget, IntegerWidget, ListWidget, \
                          MultipleOptionsWidget, OptionsWidget, StringWidget, \
                          TextWidget, UploadWidget, SQLFORM
from gluon.storage import Storage

from ..tools import s3_get_foreign_key, include_underscore_js, s3_mark_required, \
                    s3_str, s3_strip_markup, JSONERRORS, JSONSEPARATORS, \
                    S3Calendar, S3DateTime, IS_LAT_LON

from .autocomplete import S3AutocompleteWidget
from .icons import ICON

DEFAULT = lambda:None
repr_select = lambda l: len(l.name) > 48 and "%s..." % l.name[:44] or l.name

# =============================================================================
class EdenFormWidget(FormWidget):

    @classmethod
    def widget(cls, field, value, **attributes):

        return cls()

# =============================================================================
class S3AgeWidget(EdenFormWidget):
    """
        Widget to accept and represent date of birth as age in years,
        mapping the age to a pseudo date-of-birth internally so that
        it progresses over time; contains both widget and representation
        method

        Example:
            DateField("date_of_birth",
                      label = T("Age"),
                      widget = S3AgeWidget.widget,
                      represent = lambda v: S3AgeWidget.date_as_age(v) \
                                            if v else current.messages["NONE"],
                      ...
                      )
    """

    @classmethod
    def widget(cls, field, value, **attributes):
        """
            The widget method, renders a simple integer-input

            Args:
                field: the Field
                value: the current or default value
                attributes: additional HTML attributes for the widget
        """

        if isinstance(value, str) and value and not value.isdigit():
            # ISO String
            value = current.calendar.parse_date(value)

        age = cls.date_as_age(value)

        attr = IntegerWidget._attributes(field, {"value": age}, **attributes)

        # Inner validation
        requires = (IS_INT_IN_RANGE(0, 150), cls.age_as_date)

        # Accept empty if field accepts empty
        if isinstance(field.requires, IS_EMPTY_OR):
            requires = IS_EMPTY_OR(requires)
        attr["requires"] = requires

        return INPUT(**attr)

    # -------------------------------------------------------------------------
    @staticmethod
    def date_as_age(value, record_id=None):
        """
            Convert a date value into age in years, can be used as
            representation method

            Args:
                value: the date

            Returns:
                the age in years (integer)
        """

        if value and isinstance(value, datetime.date):
            #from dateutil.relativedelta import relativedelta
            age = relativedelta(current.request.utcnow, value).years
        else:
            age = value
        return age

    # -------------------------------------------------------------------------
    @staticmethod
    def age_as_date(value, error_message="invalid age"):
        """
            Convert age in years into an approximate date of birth, acts
            as inner validator of the widget

            Args:
                value: age value
                error_message: error message (override)

            Returns:
                tuple (date, error)
        """

        try:
            age = int(value)
        except ValueError:
            return None, error_message

        #from dateutil.relativedelta import relativedelta
        date = (current.request.utcnow - relativedelta(years=age)).date()

        # Map back to January 1st of the year of birth
        # => common practice, but needs validation as requirement
        date = date.replace(month=1, day=1)

        return date, None

# =============================================================================
class S3ColorPickerWidget(EdenFormWidget):
    """
        Displays a widget to allow the user to pick a
        color, and falls back to using JSColor or a regular text input if
        necessary.
    """

    DEFAULT_OPTIONS = {
        "showInput": True,
        "showInitial": True,
        "preferredFormat": "hex",
        #"showPalette": True,
        "showPaletteOnly": True,
        "togglePaletteOnly": True,
        "palette": ("red", "orange", "yellow", "green", "blue", "white", "black")
    }

    def __init__(self, options=None):
        """
            Args:
                options: options for the JavaScript widget

            See Also:
                http://bgrins.github.com/spectrum/
        """

        self.options = dict(self.DEFAULT_OPTIONS)
        self.options.update(options or {})

    def __call__(self, field, value, **attributes):

        default = {#"_type": "color", # We don't want to use native HTML5 widget as it doesn't support our options & is worse for documentation
                   "_type": "text",
                   "value": (value is not None and str(value)) or "",
                   }

        attr = StringWidget._attributes(field, default, **attributes)

        widget = INPUT(**attr)

        if "_id" in attr:
            selector = attr["_id"]
        else:
            selector = str(field).replace(".", "_")

        s3 = current.response.s3

        _min = "" if s3.debug else ".min"

        script = "/%s/static/scripts/spectrum%s.js" % \
            (current.request.application, _min)
        style = "plugins/spectrum%s.css" % _min

        if script not in s3.scripts:
            s3.scripts.append(script)

        if style not in s3.stylesheets:
            s3.stylesheets.append(style)

        # i18n of Strings
        T = current.T
        options = self.options
        options.update(cancelText = s3_str(T("cancel")),
                       chooseText = s3_str(T("choose")),
                       togglePaletteMoreText = s3_str(T("more")),
                       togglePaletteLessText = s3_str(T("less")),
                       clearText = s3_str(T("Clear Color Selection")),
                       noColorSelectedText = s3_str(T("No Color Selected")),
                       )

        options = json.dumps(options, separators=JSONSEPARATORS)
        # Ensure we save in rrggbb format not #rrggbb (IS_HTML_COLOUR)
        options = "%s,change:function(c){this.value=c.toHex()}}" % options[:-1]
        script = \
'''$('#%(selector)s').spectrum(%(options)s)''' % {"selector": selector,
                                                  "options": options,
                                                  }
        s3.jquery_ready.append(script)

        return widget

# =============================================================================
class S3CalendarWidget(EdenFormWidget):
    """
        Widget to select a date from a popup calendar, with
        optional time input

        Note:
            This widget must be combined with the IS_UTC_DATE or
            IS_UTC_DATETIME validators to have the value properly
            converted from/to local timezone and format.

        - control script is s3.ui.calendar.js
        - uses jQuery UI DatePicker for Gregorian calendars: https://jqueryui.com/datepicker/
        - uses jQuery UI Timepicker-addon if using times: http://trentrichardson.com/examples/timepicker
        - uses Calendars for non-Gregorian calendars: http://keith-wood.name/calendars.html
            (for this, ensure that css.cfg includes calendars/ui.calendars.picker.css and
                                                    calendars/ui-smoothness.calendars.picker.css)
    """

    def __init__(self,
                 calendar = None,
                 date_format = None,
                 time_format = None,
                 separator = None,
                 minimum = None,
                 maximum = None,
                 past = None,
                 future = None,
                 past_months = None,
                 future_months = None,
                 month_selector = True,
                 year_selector = True,
                 min_year = None,
                 max_year = None,
                 week_number = False,
                 buttons = None,
                 timepicker = False,
                 minute_step = 5,
                 set_min = None,
                 set_max = None,
                 clear_text = None,
                 ):
        """
            Args:
                calendar: which calendar to use (override default)
                date_format: the date format (override default)
                time_format: the time format (override default)
                separator: date-time separator (override default)
                minimum: the minimum selectable date/time (overrides past)
                maximum: the maximum selectable date/time (overrides future)
                past: how many hours into the past are selectable (overrides past_months)
                future: how many hours into the future are selectable (overrides future_months)
                past_months: how many months into the past are selectable
                future_months: how many months into the future are selectable
                month_selector: show a months drop-down
                year_selector: show a years drop-down
                min_year: the minimum selectable year (can be relative to now like "-10")
                max_year: the maximum selectable year (can be relative to now like "+10")
                week_number: show the week number in the calendar
                buttons: show the button panel (defaults to True if the
                         widget has a timepicker, else False)
                timepicker: show a timepicker
                minute_step: minute-step for the timepicker slider
                set_min: CSS selector for another S3Calendar widget for which to
                         dynamically update the minimum selectable date/time from
                         the selected date/time of this widget
                set_max: CSS selector for another S3Calendar widget for which to
                         dynamically update the maximum selectable date/time from
                         the selected date/time of this widget
        """

        self.calendar = calendar

        self.date_format = date_format
        self.time_format = time_format
        self.separator = separator

        self.minimum = minimum
        self.maximum = maximum
        self.past = past
        self.future = future
        self.past_months = past_months
        self.future_months = future_months

        self.month_selector = month_selector
        self.year_selector = year_selector
        self.min_year = min_year
        self.max_year = max_year

        self.week_number = week_number
        self.buttons = buttons if buttons is not None else timepicker

        self.timepicker = timepicker
        self.minute_step = minute_step

        self.set_min = set_min
        self.set_max = set_max

        self.clear_text = clear_text

        self._class = "s3-calendar-widget datetimepicker"

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget builder

            Args:
                field: the Field
                value: the current value
                attributes: the HTML attributes for the widget
        """

        # Modify class as required
        _class = self._class

        # Default attributes
        defaults = {"_type": "text",
                    "_class": _class,
                    "value": value,
                    "requires": field.requires,
                    }
        attr = self._attributes(field, defaults, **attributes)

        # Real input ID
        input_id = attr.get("_id")
        if not input_id:
            if isinstance(field, Field):
                input_id = str(field).replace(".", "_")
            else:
                input_id = field.name.replace(".", "_")
            attr["_id"] = input_id


        # Real input name attribute
        input_name = attr.get("_name")
        if not input_name:
            input_name = field.name.replace(".", "_")
            attr["_name"] = input_name

        # Container ID
        container_id = "%s-calendar-widget" % input_id

        # Script options
        settings = current.deployment_settings

        calendar = self.calendar or current.calendar.name
        calendar = calendar if calendar and calendar != "Gregorian" else "gregorian"

        date_format = self.date_format or \
                      settings.get_L10n_date_format()
        time_format = self.time_format or \
                      settings.get_L10n_time_format()
        separator = self.separator or \
                    settings.get_L10n_datetime_separator()

        c = current.calendar if not self.calendar else S3Calendar(self.calendar)
        firstDOW = c.first_dow

        dtformat = separator.join([date_format, time_format])
        extremes = self.extremes(dtformat = dtformat)

        T = current.T

        clear_text = self.clear_text
        if clear_text is None:
            clear_text = s3_str(T("Clear"))
        else:
            clear_text = s3_str(T(clear_text))

        options = {"calendar": calendar,
                   "dateFormat": str(date_format),
                   "timeFormat": str(time_format),
                   "separator": separator,
                   "firstDOW": firstDOW,
                   "monthSelector": self.month_selector,
                   "yearSelector": self.year_selector,
                   "showButtons": self.buttons,
                   "weekNumber": self.week_number,
                   "timepicker": self.timepicker,
                   "minuteStep": self.minute_step,
                   "todayText": s3_str(T("Today")),
                   "nowText": s3_str(T("Now")),
                   "closeText": s3_str(T("Done")),
                   "clearText": clear_text,
                   "setMin": self.set_min,
                   "setMax": self.set_max,
                   }
        options.update(extremes)

        if settings.get_ui_calendar_clear_icon():
            options["clearButton"] = "icon"

        # Inject JS
        self.inject_script(input_id, options)

        # Construct real input
        real_input = INPUT(**attr)

        # Construct and return the widget
        return TAG[""](DIV(real_input,
                           _id = container_id,
                           _class = "calendar-widget-container",
                           ),
                       )

    # -------------------------------------------------------------------------
    def extremes(self, dtformat=None):
        """
            Compute the minimum/maximum selectable date/time, as well as
            the default time (=the minute-step closest to now)

            Args:
                dtformat: the user datetime format

            Returns:
                a dict {minDateTime, maxDateTime, defaultValue, yearRange}
                with the min/max options as ISO-formatted strings, and the
                defaultValue in user-format (all in local time), to be
                passed as-is to s3.calendarwidget
        """

        extremes = {}
        now = current.request.utcnow

        # RAD : default to something quite generous
        pyears, fyears = 80, 80

        # Minimum
        earliest = None
        fallback = False
        if self.minimum:
            earliest = self.minimum
            if type(earliest) is datetime.date:
                # Consistency with S3Calendar
                earliest = datetime.datetime.combine(earliest, datetime.time(8, 0, 0))
        elif self.past is not None:
            earliest = now - datetime.timedelta(hours=self.past)
        elif self.past_months is not None:
            earliest = now - relativedelta(months=self.past_months)
        else:
            fallback = True
            earliest = now - datetime.timedelta(hours=876000)
        if earliest is not None:
            if not fallback:
                pyears = abs(earliest.year - now.year)
            earliest = S3DateTime.to_local(earliest.replace(microsecond=0))
            extremes["minDateTime"] = earliest.isoformat()

        # Maximum
        latest = None
        fallback = False
        if self.maximum:
            latest = self.maximum
            if type(latest) is datetime.date:
                # Consistency with S3Calendar
                latest = datetime.datetime.combine(latest, datetime.time(8, 0, 0))
        elif self.future is not None:
            latest = now + datetime.timedelta(hours = self.future)
        elif self.future_months is not None:
            latest = now + relativedelta(months = self.future_months)
        else:
            fallback = True
            latest = now + datetime.timedelta(hours = 876000)
        if latest is not None:
            if not fallback:
                fyears = abs(latest.year - now.year)
            latest = S3DateTime.to_local(latest.replace(microsecond = 0))
            extremes["maxDateTime"] = latest.isoformat()

        # Default date/time
        if self.timepicker and dtformat:
            # Pick a start date/time
            if earliest <= now <= latest:
                start = now
            elif now < earliest:
                start = earliest
            elif now > latest:
                start = latest
            # Round to the closest minute-step
            step = self.minute_step * 60
            seconds = (start - start.min).seconds
            rounding = (seconds + step / 2) // step * step
            rounded = start + datetime.timedelta(0,
                                                 rounding - seconds,
                                                 -start.microsecond,
                                                 )
            # Limits
            if rounded < earliest:
                rounded = earliest
            elif rounded > latest:
                rounded = latest
            # Translate into local time
            rounded = S3DateTime.to_local(rounded)
            # Convert into user format
            default = rounded.strftime(dtformat)
            extremes["defaultValue"] = default

        # Year range
        min_year = self.min_year
        if not min_year:
            min_year = "-%s" % pyears
        max_year = self.max_year
        if not max_year:
            max_year = "+%s" % fyears
        extremes["yearRange"] = "%s:%s" % (min_year, max_year)

        return extremes

    # -------------------------------------------------------------------------
    @classmethod
    def inject_script(cls, selector, options):
        """
            Helper function to inject the document-ready-JavaScript for
            this widget.

            Args:
                field: the Field
                value: the current value
                attr: the HTML attributes for the widget
        """

        if not selector:
            return

        s3 = current.response.s3

        scripts, language = cls.global_scripts(options.get("calendar"))
        options["language"] = language

        for script in scripts:
            if script and script not in s3.scripts:
                s3.scripts.append(script)

        # jQuery-ready script
        script = '''$('#%(selector)s').calendarWidget(%(options)s);''' % \
                 {"selector": selector,
                  "options": json.dumps(options, separators=JSONSEPARATORS),
                  }
        s3.jquery_ready.append(script)

    # -------------------------------------------------------------------------
    @staticmethod
    def global_scripts(calendar="gregorian"):

        s3 = current.response.s3
        request = current.request

        folder = request.folder
        appname = request.application

        # Basic scripts
        if s3.debug:
            scripts = ("jquery.plugin.js",
                       "calendars/jquery.calendars.all.js",
                       "calendars/jquery.calendars.picker.ext.js",
                       "S3/s3.ui.calendar.js",
                       )
        else:
            scripts = ("jquery.plugin.min.js",
                       "S3/s3.ui.calendar.min.js",
                       )
        scripts = ["/%s/static/scripts/%s" % (appname, script) for script in scripts]
        append = scripts.append

        # Helper to append a script only if it exists
        def append_if_exists(*plist):
            path = os.path.join(folder, *plist)
            if os.path.exists(path):
                append("/%s/%s" % (appname, "/".join(plist)))

        # Calendar variant
        calendar = calendar.lower()
        if calendar != "gregorian":
            filename = "jquery.calendars.%s.js" % calendar
            append_if_exists("static", "scripts", "calendars", "i18n", filename)

        # Localization scripts
        language = current.session.s3.language
        if language in current.deployment_settings.date_formats:

            if "-" in language:
                parts = language.split("-", 1)
                language = "%s-%s" % (parts[0], parts[1].upper())

            # datePicker regional
            filename = "datepicker-%s.js" % language
            append_if_exists("static", "scripts", "ui", "i18n", filename)

            # timePicker regional
            filename = "jquery-ui-timepicker-%s.js" % language
            append_if_exists("static", "scripts", "ui", "i18n", filename)

            if calendar != "gregorian" and language:
                # calendars regional
                filename = "jquery.calendars.%s-%s.js" % (calendar, language)
                append_if_exists("static", "scripts", "calendars", "i18n", filename)

                # calendarsPicker regional
                filename = "jquery.calendars.picker-%s.js" % language
                append_if_exists("static", "scripts", "calendars", "i18n", filename)
        else:
            language = ""

        return scripts, language

# =============================================================================
class S3DateWidget(EdenFormWidget):
    """
        Standard Date widget
    """

    def __init__(self,
                 format = None,
                 #past=1440,
                 #future=1440,
                 past=None,
                 future=None,
                 start_field = None,
                 default_interval = None,
                 default_explicit = False,
                 ):
        """
            Args:
                format: format of date
                past: how many months into the past the date can be set to
                future: how many months into the future the date can be set to
                start_field: "selector" for start date field
                default_interval: x months from start date
                default_explicit: bool for explicit default
        """

        self.format = format
        self.past = past
        self.future = future
        self.start_field = start_field
        self.default_interval = default_interval
        self.default_explicit = default_explicit

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget builder

            Args:
                field: the Field
                value: the current value
                attributes: the HTML attributes for the widget
        """

        # Need to convert value into ISO-format
        # (widget expects ISO, but value comes in custom format)
        dt = current.calendar.parse_date(value, local=True)
        if dt:
            value = dt.isoformat()

        request = current.request
        settings = current.deployment_settings

        s3 = current.response.s3

        jquery_ready = s3.jquery_ready
        language = current.session.s3.language

        if language in settings.date_formats:
            # Localise if we have configured a Date Format and we have a jQueryUI options file
            # Do we have a suitable locale file?
            if language in ("prs", "ps"):
                # Dari & Pashto use Farsi
                language = "fa"
            #elif language == "ur":
            #    # Urdu uses Arabic
            #    language = "ar"
            elif "-" in language:
                parts = language.split("-", 1)
                language = "%s-%s" % (parts[0], parts[1].upper())
            path = os.path.join(request.folder, "static", "scripts", "ui", "i18n", "datepicker-%s.js" % language)
            if os.path.exists(path):
                lscript = "/%s/static/scripts/ui/i18n/datepicker-%s.js" % (request.application, language)
                if lscript not in s3.scripts:
                    # 1st Datepicker
                    s3.scripts.append(lscript)
                    script = '''$.datepicker.setDefaults($.datepicker.regional["%s"])''' % language
                    jquery_ready.append(script)

        if self.format:
            # default: "yy-mm-dd"
            format = str(self.format)
        else:
            dtfmt = settings.get_L10n_date_format()
            format = dtfmt.replace("%Y", "yy") \
                          .replace("%y", "y") \
                          .replace("%m", "mm") \
                          .replace("%d", "dd") \
                          .replace("%b", "M")

        default = {"_type": "text",
                   "value": (value is not None and str(value)) or "",
                   }

        attr = StringWidget._attributes(field, default, **attributes)

        widget = INPUT(**attr)
        widget.add_class("date")

        if "_id" in attr:
            selector = attr["_id"]
        else:
            selector = str(field).replace(".", "_")

        # Convert to Days
        now = current.request.utcnow
        past = self.past
        if past is None:
            past = ""
        else:
            if past:
                past = now - relativedelta(months=past)
                if now > past:
                    days = (now - past).days
                    minDate = "-%s" % days
                else:
                    days = (past - now).days
                    minDate = "+%s" % days
            else:
                minDate = "-0"
            past = ",minDate:%s" % minDate

        future = self.future
        if future is None:
            future = ""
        else:
            if future:
                future = now + relativedelta(months=future)
                if future > now:
                    days = (future - now).days
                    maxDate = "+%s" % days
                else:
                    days = (now - future).days
                    maxDate = "-%s" % days
            else:
                maxDate = "+0"
            future = ",maxDate:%s" % maxDate

        # Set auto updation of end_date based on start_date if start_field attr are set
        start_field = self.start_field
        default_interval = self.default_interval

        script = \
'''$('#%(selector)s').datepicker('option',{yearRange:'c-100:c+100',dateFormat:'%(format)s'%(past)s%(future)s}).one('click',function(){$(this).focus()})''' % \
            {"selector": selector,
             "format": format,
             "past": past,
             "future": future,
             }

        if script not in jquery_ready: # Prevents loading twice when form has errors
            jquery_ready.append(script)

        if start_field and default_interval:

            T = current.T

            # Setting i18n for labels
            i18n = '''
i18n.interval="%(interval_label)s"
i18n.btn_1_label="%(btn_first_label)s"
i18n.btn_2_label="%(btn_second_label)s"
i18n.btn_3_label="%(btn_third_label)s"
i18n.btn_4_label="%(btn_fourth_label)s"
i18n.btn_clear="%(btn_clear)s"
''' % {"interval_label": T("Interval"),
       "btn_first_label": T("+6 MO"),
       "btn_second_label": T("+1 YR"),
       "btn_third_label": T("+2 YR"),
       "btn_fourth_label": T("+5 YR"),
       "btn_clear": T("Clear"),
       }

            s3.js_global.append(i18n)

            script = '''
$('#%(end_selector)s').end_date_interval({
start_date_selector:"#%(start_selector)s",
interval:%(interval)d
%(default_explicit)s
})
''' % {"end_selector": selector,
       "start_selector": start_field,
       "interval": default_interval,
       "default_explicit": ",default_explicit:true" if self.default_explicit else "",
       }

            if script not in jquery_ready:
                jquery_ready.append(script)

        return TAG[""](widget, requires = field.requires)

# =============================================================================
class S3DateTimeWidget(EdenFormWidget):
    """
        Date and/or time picker widget based on jquery.ui.datepicker and
        jquery.ui.timepicker.addon.js.
    """

    def __init__(self, **opts):
        """
            Args:
                opts: the widget options

            Keyword Args:
                date_format: the date format (falls back to
                             deployment_settings.L10n.date_format)
                time_format: the time format (falls back to
                             deployment_settings.L10n.time_format)
                separator: the date/time separator (falls back to
                           deployment_settings.L10n.datetime_separator)
                min: the earliest selectable datetime (datetime, overrides "past")
                max: the latest selectable datetime (datetime, overrides "future")
                past: the earliest selectable datetime relative to now (hours)
                future: the latest selectable datetime relative to now (hours)
                min_year: the earliest year in the drop-down (default: now-10 years)
                max_year: the latest year in the drop-down (default: now+10 years)
                hide_time: Hide the time selector (default: False)
                minute_step: number of minutes per slider step (default: 5)
                weeknumber: show week number in calendar widget (default: False)
                month_selector: show drop-down selector for month (default: False)
                year_selector: show drop-down selector for year (default: True)
                buttons: show the button panel (default: True)
                set_min: set a minimum for another datetime widget
                set_max: set a maximum for another datetime widget
        """

        self.opts = Storage(opts)
        self._class = "datetimepicker"

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget builder.

            Args:
                field: the Field
                value: the current value
                attributes: the HTML attributes for the widget
        """

        self.inject_script(field, value, **attributes)

        default = {"_type": "text",
                   "_class": self._class,
                   "value": value,
                   }
        attr = StringWidget._attributes(field, default, **attributes)

        if "_id" not in attr:
            attr["_id"] = str(field).replace(".", "_")

        widget = INPUT(**attr)
        widget.add_class(self._class)

        if self.opts.get("hide_time", False):
            widget.add_class("hide-time")

        return TAG[""](widget, requires = field.requires)

    # -------------------------------------------------------------------------
    def inject_script(self, field, value, **attributes):
        """
            Helper function to inject the document-ready-JavaScript for
            this widget.

            Args:
                field: the Field
                value: the current value
                attributes: the HTML attributes for the widget
        """

        ISO = "%Y-%m-%dT%H:%M:%S"
        opts = self.opts
        opts_get = opts.get

        if "_id" in attributes:
            selector = attributes["_id"]
        else:
            selector = str(field).replace(".", "_")

        settings = current.deployment_settings
        date_format = opts_get("date_format",
                               settings.get_L10n_date_format())
        time_format = opts_get("time_format",
                               settings.get_L10n_time_format())
        separator = opts_get("separator",
                             settings.get_L10n_datetime_separator())
        datetime_format = "%s%s%s" % (date_format, separator, time_format)

        request = current.request
        s3 = current.response.s3
        jquery_ready = s3.jquery_ready
        language = current.session.s3.language
        if language in settings.date_formats:
            # Localise if we have configured a Date Format and we have a jQueryUI options file
            # Do we have a suitable locale file?
            if language in ("prs", "ps"):
                # Dari & Pashto use Farsi
                language = "fa"
            #elif language == "ur":
            #    # Urdu uses Arabic
            #    language = "ar"
            elif "-" in language:
                parts = language.split("_", 1)
                language = "%s-%s" % (parts[0], parts[1].upper())
            path = os.path.join(request.folder, "static", "scripts", "ui", "i18n", "datepicker-%s.js" % language)
            if os.path.exists(path):
                lscript = "/%s/static/scripts/ui/i18n/datepicker-%s.js" % (request.application, language)
                if lscript not in s3.scripts:
                    # 1st Datepicker
                    s3.scripts.append(lscript)
                    script = '''$.datepicker.setDefaults($.datepicker.regional["%s"])''' % language
                    jquery_ready.append(script)

        # Option to hide the time slider
        hide_time = opts_get("hide_time", False)
        if hide_time:
            limit = "Date"
            widget = "datepicker"
            dtformat = date_format
        else:
            limit = "DateTime"
            widget = "datetimepicker"
            dtformat = datetime_format

        # Limits
        now = request.utcnow
        timedelta = datetime.timedelta

        if "min" in opts:
            earliest = opts["min"]
        else:
            past = opts_get("past", 876000)
            earliest = now - timedelta(hours = past)
        if "max" in opts:
            latest = opts["max"]
        else:
            future = opts_get("future", 876000)
            latest = now + timedelta(hours = future)

        # Closest minute step as default
        minute_step = opts_get("minute_step", 5)
        if not hide_time:
            if earliest <= now and now <= latest:
                start = now
            elif now < earliest:
                start = earliest
            elif now > latest:
                start = latest
            step = minute_step * 60
            seconds = (start - start.min).seconds
            rounding = (seconds + step / 2) // step * step
            rounded = start + timedelta(0, rounding - seconds,
                                            -start.microsecond)
            if rounded < earliest:
                rounded = earliest
            elif rounded > latest:
                rounded = latest
            rounded = S3DateTime.to_local(rounded)
            default = rounded.strftime(dtformat)
        else:
            default = ""

        # Convert extremes to local time
        earliest = S3DateTime.to_local(earliest)
        latest = S3DateTime.to_local(latest)

        # Update limits of another widget?
        set_min = opts_get("set_min", None)
        set_max = opts_get("set_max", None)
        onclose = '''function(selectedDate){'''
        onclear = ""
        if set_min:
            onclose += '''$('#%s').%s('option','minDate',selectedDate)\n''' % \
                       (set_min, widget)
            onclear += '''$('#%s').%s('option','minDate',null)\n''' % \
                       (set_min, widget)
        if set_max:
            onclose += '''$('#%s').%s('option','maxDate',selectedDate)''' % \
                       (set_max, widget)
            onclear += '''$('#%s').%s('option','minDate',null)''' % \
                       (set_max, widget)
        onclose += '''}'''

        # Translate Python format-strings
        date_format = settings.get_L10n_date_format().replace("%Y", "yy") \
                                                     .replace("%y", "y") \
                                                     .replace("%m", "mm") \
                                                     .replace("%d", "dd") \
                                                     .replace("%b", "M")

        time_format = settings.get_L10n_time_format().replace("%p", "TT") \
                                                     .replace("%I", "hh") \
                                                     .replace("%H", "HH") \
                                                     .replace("%M", "mm") \
                                                     .replace("%S", "ss")

        separator = settings.get_L10n_datetime_separator()

        # Year range
        pyears, fyears = 10, 10
        if "min" in opts or "past" in opts:
            pyears = abs(earliest.year - now.year)
        if "max" in opts or "future" in opts:
            fyears = abs(latest.year - now.year)
        year_range = "%s:%s" % (opts_get("min_year", "-%s" % pyears),
                                opts_get("max_year", "+%s" % fyears))

        # Other options
        firstDOW = settings.get_L10n_firstDOW()

        # Boolean options
        getopt = lambda opt, default: opts_get(opt, default) and "true" or "false"

        script = \
'''$('#%(selector)s').%(widget)s({
 showSecond:false,
 firstDay:%(firstDOW)s,
 min%(limit)s:new Date(Date.parse('%(earliest)s')),
 max%(limit)s:new Date(Date.parse('%(latest)s')),
 dateFormat:'%(date_format)s',
 timeFormat:'%(time_format)s',
 separator:'%(separator)s',
 stepMinute:%(minute_step)s,
 showWeek:%(weeknumber)s,
 showButtonPanel:%(buttons)s,
 changeMonth:%(month_selector)s,
 changeYear:%(year_selector)s,
 yearRange:'%(year_range)s',
 useLocalTimezone:true,
 defaultValue:'%(default)s',
 onClose:%(onclose)s
}).one('click',function(){$(this).focus()})
var clear_button=$('<button id="%(selector)s_clear" class="btn date-clear-btn" type="button">%(clear)s</button>').click(function(){
 $('#%(selector)s').val('');%(onclear)s;$('#%(selector)s').closest('.filter-form').trigger('optionChanged')
})
if($('#%(selector)s_clear').length==0){
 $('#%(selector)s').after(clear_button)
}''' %  {"selector": selector,
         "widget": widget,
         "date_format": date_format,
         "time_format": time_format,
         "separator": separator,
         "weeknumber": getopt("weeknumber", False),
         "month_selector": getopt("month_selector", False),
         "year_selector": getopt("year_selector", True),
         "buttons": getopt("buttons", True),
         "firstDOW": firstDOW,
         "year_range": year_range,
         "minute_step": minute_step,
         "limit": limit,
         "earliest": earliest.strftime(ISO),
         "latest": latest.strftime(ISO),
         "default": default,
         "clear": current.T("clear"),
         "onclose": onclose,
         "onclear": onclear,
         }

        if script not in jquery_ready: # Prevents loading twice when form has errors
            jquery_ready.append(script)

        return

# =============================================================================
class S3HoursWidget(EdenFormWidget):
    """
        Widget to enter a duration in hours (e.g. of a task), supporting
        flexible input format (e.g. "1h 15min", "1.75", "2:10")

        Note:
            Users who frequently enter minutes-fragments sometimes forget
            that the field expects hours, e.g. input of "15" interpreted
            as 15 hours while the user actually meant 15 minutes. To avoid
            this, use the explicit_above parameter to require an explicit
            time unit or colon notation for implausible numbers (e.g. >10)
            - so the user must enter "15h", "15m", "15:00" or "0:15" explicitly.
    """

    PARTS = re.compile(r"((?:[+-]{0,1}\s*)(?:[0-9,.:]+)\s*(?:[^0-9,.:+-]*))")
    TOKEN = re.compile(r"([+-]{0,1}\s*)([0-9,.:]+)([^0-9,.:+-]*)")

    def __init__(self, interval=None, precision=2, explicit_above=None, placeholder=None):
        """
            Args:
                interval: standard interval to round up to (minutes),
                          None to disable rounding
                precision: number of decimal places to keep
                explicit_above: require explicit time unit or colon notation
                                for value fragments above this limit
                placeholder: placeholder for input
        """

        self.interval = interval
        self.precision = precision

        self.explicit_above = explicit_above
        self.placeholder = placeholder

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Entry point for form processing

            Args:
                field: the Field
                value: the current/default value
                attributes: HTML attributes for the widget
        """

        default = {"value": (value != None and str(value)) or ""}
        attr = StringWidget._attributes(field, default, **attributes)

        attr["requires"] = self.validate
        attr["_title"] = current.T("In hours, or formatted like 1h10min, 15min, 0:45...")

        if self.placeholder:
            attr["_placeholder"] = self.placeholder

        widget = INPUT(**attr)
        widget.add_class("hours")

        return widget

    # -------------------------------------------------------------------------
    def validate(self, value):
        """
            Pre-validator to parse the input value before validating it

            Args:
                value: the input value

            Returns:
                tuple (parsed, error)
        """

        try:
            return self.parse_input(value), None
        except SyntaxError as e:
            # Input format violation
            return value, str(e)
        except:
            return value, "invalid value"

    # -------------------------------------------------------------------------
    def parse_input(self, value):
        """
            Function to parse the input value (if it is a string)

            Args:
                value: the value

            Returns:
                the value as float (hours)
        """

        hours = 0.0

        if value is None or value == "":
            return None
        elif not value:
            return hours

        explicit_above = self.explicit_above

        parts = self.PARTS.split(value)
        for part in parts:

            token = part.strip()
            if not token:
                continue

            m = self.TOKEN.match(token)
            if not m:
                continue

            sign = m.group(1).strip()
            num = m.group(2)

            unit = m.group(3).lower()
            unit, implicit = (unit[0], False) if unit else ("h", ":" not in num)
            if unit == "s":
                length = 1
                factor = 3600.0
            elif unit == "m":
                length = 2
                factor = 60.0
            else:
                length = 3
                factor = 1.0

            segments = (num.replace(",", ".").split(":") + ["0", "0", "0"])[:length]
            total = 0.0
            for segment in segments:
                try:
                    v = float(segment)
                except ValueError:
                    v = 0.0
                total += v / factor
                factor *= 60

            if explicit_above is not None and total > explicit_above and implicit:
                msg = current.T("Specify a time unit or use HH:MM format")
                raise SyntaxError(s3_str(msg))
            if sign == "-":
                hours -= total
            else:
                hours += total

        interval = self.interval
        if interval:
            import math
            interval = float(interval)
            hours = math.ceil(hours * 60.0 / interval) * interval / 60.0

        precision = self.precision
        return round(hours, precision) if precision is not None else hours

# =============================================================================
class S3WeeklyHoursWidget(EdenFormWidget):
    """
        Widget to enter weekly time rules (JSON) using a 24/7 hours
        matrix, e.g. opening hours, times of availability, etc.
    """

    def __init__(self, daynames=None, hours=None, ticks=6):
        """
            Args:
                daynames: the weekdays to show and their (localized)
                          names, as dict {daynumber: dayname}, with
                          day number 0 meaning Sunday
                hours: the hours to show (0..23) as tuple (first, last)
                ticks: render tick marks every n hours (0/None=off)
        """

        if daynames:
            self._daynames = daynames
        else:
            self._daynames = self.daynames()

        if hours:
            self.hours = hours
        else:
            self.hours = (0, 23)

        self.ticks = ticks

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget builder

            Args:
                field: the Field
                value: the current field value
                attributes: additional DOM attributes for the widget
        """

        default = {"value": value,
                   }
        attr = TextWidget._attributes(field, default, **attributes)

        widget_id = attr.get("_id")
        if not widget_id:
            widget_id = attr["_id"] = str(field).replace(".", "_")

        widget = TEXTAREA(**attr)
        widget.add_class("hide")

        options = {"weekdays": {k: s3_str(v) for k, v in self._daynames.items()},
                   "hours": self.hours,
                   "ticks": self.ticks,
                   "firstDoW": current.calendar.first_dow,
                   "icons": "fa",
                   "iconSelected": "fa-check-square-o",
                   "iconDeselected": "fa-square-o",
                   }
        self.inject_script(widget_id, options)

        return widget

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_script(selector, options):
        """
            Inject static JS and instantiate client-side UI widget

            Args:
                widget_id: the widget ID
                options: JSON-serializable dict with UI widget options
        """

        s3 = current.response.s3
        appname = current.request.application

        # Global script
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.ui.weeklyhours.js" % appname
        else:
            script = "/%s/static/scripts/S3/s3.ui.weeklyhours.min.js" % appname
        if script not in s3.scripts:
            s3.scripts.append(script)

        # jQuery-ready script
        script = '''$('#%(selector)s').weeklyHours(%(options)s);''' % \
                 {"selector": selector,
                  "options": json.dumps(options, separators=JSONSEPARATORS),
                  }
        s3.jquery_ready.append(script)

    # -------------------------------------------------------------------------
    @staticmethod
    def daynames():
        """
            Default weekday names (abbreviations)

            Returns:
                dict of {daynumber: dayname}
        """

        T = current.T

        return {0: T("Sun##weekday"),
                1: T("Mon##weekday"),
                2: T("Tue##weekday"),
                3: T("Wed##weekday"),
                4: T("Thu##weekday"),
                5: T("Fri##weekday"),
                6: T("Sat##weekday"),
                }

    # -------------------------------------------------------------------------
    @classmethod
    def represent(cls, rules, daynames=None, html=True):
        """
            Represent a set of weekly time rules, as list of rules
            per weekday (HTML)

            Args:
                rules: array of rules, or a JSON string encoding such an array
                daynames: override for default daynames, as dict
                          {daynumber: dayname}, with day number 0 meaning Sunday
                html: produce HTML rather than text (overridable for e.g. XLS export)

            Returns:
                UL instance
        """

        if isinstance(rules, str) and rules:
            try:
                rules = json.loads(rules)
            except JSONERRORS:
                rules = []

        dn = cls.daynames()
        if daynames:
            dn.update(daynames)

        first_dow = 1

        if not rules:
            return ""

        slots_by_day = {}
        for rule in rules:

            # Only include weekly rules
            if rule.get("f") != "WEEKLY" or rule.get("i") != 1:
                continue

            days = rule.get("d")
            if not isinstance(days, list):
                continue

            start = rule.get("s")
            end = rule.get("e")
            if not start or not end:
                continue
            slot = (start[0], end[0])

            for day in days:
                slots = slots_by_day.get(day)
                if not slots:
                    slots = [slot]
                else:
                    slots.append(slot)
                slots_by_day[day] = slots

        output = UL(_class="wh-schedule") if html else []

        for index in range(first_dow, first_dow + 7):

            day = index % 7
            slots = slots_by_day.get(day)

            if slots:
                slots = sorted(slots, key=lambda s: s[0])
                slotsrepr = ", ".join(["%02d-%02d" % (s[0], s[1]) for s in slots])
            else:
                slotsrepr = "-"

            if html:
                output.append(LI(SPAN(dn[day], _class="wh-dayname"),
                                 slotsrepr,
                                 ))
            else:
                output.append("%s: %s" % (dn[day], slotsrepr))

        return output if html else "\n".join(output)

# =============================================================================
class S3QRInput(EdenFormWidget):
    """
        Simple input widget with attached QR-code decoder, using the
        device camera (if available) to capture the code
    """

    def __init__(self,
                 hidden = False,
                 icon = True,
                 label = False,
                 placeholder = None,
                 pattern = None,
                 index = None,
                 keep_original = False,
                 ):
        """
            Args:
                hidden: use a hidden input
                icon: show icon on button
                label: show label on button
                placeholder: placeholder for visible input
                pattern: a JS regular expression to parse the QR code,
                         if specified, the QR contents must match the
                         pattern in order to be accepted
                index: group index or name for the regex match to
                       extract the visible detail; if omitted, the
                       entire contents of the QR code will be shown
                keep_original: submit the original QR contents, unless
                               the user enters a value manually; if
                               set to False, the visible detail will
                               be submitted instead
        """

        self.hidden = hidden
        self.icon = icon
        self.label = label
        self.placeholder = placeholder

        self.pattern = pattern
        self.index = index
        self.keep_original = keep_original

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget builder

            Args:
                field: the Field
                value: the current field value
                attributes: additional DOM attributes for the widget
        """

        T = current.T

        default = {"value": value,
                   }
        if self.hidden:
            default["_type"] = "hidden"

        # Choose input type
        if field.type == "text":
            input_type = TextWidget
        elif field.type == "string":
            input_type = StringWidget
        else:
            input_type = self

        attr = input_type._attributes(field, default, **attributes)
        widget_id = attr.get("_id")
        if not widget_id:
            widget_id = attr["_id"] = str(field).replace(".", "_")
        if self.placeholder:
            attr["_placeholder"] = self.placeholder

        title = T("Scan QR Code")

        icon = self.icon
        if not icon:
            icon = ""
        elif icon is True:
            icon = ICON("fa fa-qrcode")

        label = self.label
        if not label:
            label = "" if icon else title
        elif label is True:
            label = title

        scanbtn = BUTTON(icon,
                         label,
                         _title = title if not label else None,
                         _type = "button",
                         _class = "tiny primary button qrscan-btn",
                         )

        # The hidden input carries the submitted value
        hidden = INPUT(_type = "hidden",
                       _name = attr.pop("_name", widget_id),
                       _class = "qrinput-hidden",
                       requires = attr.pop("requires", None),
                       )

        widget = DIV(INPUT(**attr),
                     SPAN(ICON("fa fa-close"),
                          _class = "postfix clear-btn",
                          _title = T("Clear"),
                          ),
                     scanbtn,
                     hidden,
                     _class = "qrinput",
                     )

        options = {"inputPattern": self.pattern,
                   "inputIndex": self.index,
                   "keepOriginalInput": bool(self.keep_original),
                   }
        self.inject_script(widget_id, options)

        return widget

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_script(selector, options):
        """
            Inject static JS and instantiate client-side UI widget

            Args:
                widget_id: the widget ID
                options: JSON-serializable dict with UI widget options
        """

        s3 = current.response.s3
        appname = current.request.application

        opts = {}
        opts.update(options)
        opts["workerPath"] = "/%s/static/scripts/qr-scanner/qr-scanner-worker.min.js" % appname

        # Global scripts
        scripts = ["/%s/static/scripts/qr-scanner/qr-scanner.umd.min.js",
                   "/%%s/static/scripts/S3/s3.ui.qrinput.%s" % ("js" if s3.debug else "min.js")
                   ]
        for script in scripts:
            path = script % appname
            if path not in s3.scripts:
                s3.scripts.append(path)

        # jQuery-ready script
        script = '''$('#%(selector)s').qrInput(%(options)s);''' % \
                 {"selector": selector,
                  "options": json.dumps(opts, separators=JSONSEPARATORS),
                  }
        s3.jquery_ready.append(script)

# =============================================================================
class S3EmbeddedComponentWidget(EdenFormWidget):
    """
        Widget used by BasicCRUD for link-table components with actuate="embed".
        Uses s3.embed_component.js for client-side processing, and
        BasicCRUD._postprocess_embedded to receive the data.
    """

    def __init__(self,
                 link=None,
                 component=None,
                 autocomplete=None,
                 link_filter=None,
                 select_existing=True):
        """
            Args:
                link: the name of the link table
                component: the name of the component table
                autocomplete: name of the autocomplete field
                link_filter: filter expression to filter out records
                             in the component that are already linked
                             to the main record
                select_existing: allow the selection of existing
                                 component records from the registry
        """

        self.link = link
        self.component = component
        self.autocomplete = autocomplete
        self.select_existing = select_existing
        self.link_filter = link_filter

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget renderer

            Args:
                field: the Field
                value: the current value
                attributes: the HTML attributes for the widget
        """

        T = current.T

        # Input ID
        if "_id" in attributes:
            input_id = attributes["_id"]
        else:
            input_id = str(field).replace(".", "_")

        # Form style and widget style
        s3 = current.response.s3
        formstyle = s3.crud.formstyle
        if not callable(formstyle) or \
           isinstance(formstyle("","","",""), tuple):
            widgetstyle = self._formstyle
        else:
            widgetstyle = formstyle

        # Subform controls
        controls = TAG[""](A(T("Select from Registry"),
                             _id="%s-select" % input_id,
                             _class="action-btn",
                             ),
                           A(T("Remove Selection"),
                             _id="%s-clear" % input_id,
                             _class="action-btn hide",
                             _style="padding-left:15px;",
                             ),
                           A(T("Edit Details"),
                             _id="%s-edit" % input_id,
                             _class="action-btn hide",
                             _style="padding-left:15px;",
                             ),
                           DIV(_class="throbber hide",
                               _style="padding-left:85px;",
                               ),
                           )
        controls = widgetstyle("%s-select-row" % input_id,
                               "",
                               controls,
                               "",
                               )
        controls.add_class("box_top" if self.select_existing else "hide")

        s3db = current.s3db
        ctable = s3db[self.component]
        prefix, resourcename = self.component.split("_", 1)

        # Selector
        autocomplete = self.autocomplete
        if autocomplete:
            # Autocomplete widget
            ac_field = ctable[autocomplete]

            widget = S3AutocompleteWidget(prefix,
                                          resourcename=resourcename,
                                          fieldname=autocomplete,
                                          link_filter=self.link_filter,
                                          )
            selector = widgetstyle("%s-autocomplete-row" % input_id,
                                   LABEL("%s: " % ac_field.label,
                                         _class="hide",
                                         _id="%s-autocomplete-label" % input_id),
                                   widget(field, value),
                                   "",
                                   )
            selector.add_class("box_top")
        else:
            # Options widget
            # @todo: add link_filter here as well
            widget = OptionsWidget.widget(field, None,
                                          _class="hide",
                                          _id="dummy_%s" % input_id,
                                          )
            label = LABEL("%s: " % field.label,
                          _class="hide",
                          _id="%s-autocomplete-label" % input_id,
                          )
            hidden_input = INPUT(_id=input_id, _class="hide")

            selector = widgetstyle("%s-autocomplete-row" % input_id,
                                   label,
                                   TAG[""](widget, hidden_input),
                                   "",
                                   )
            selector.add_class("box_top")

        # Initialize field validators with the correct record ID
        fields = [f for f in ctable
                    if (f.writable or f.readable) and not f.compute]
        request = current.request
        if field.name in request.post_vars:
            selected = request.post_vars[field.name]
        else:
            selected = None
        if selected:
            for f in fields:
                requires = f.requires or []
                if not isinstance(requires, (list, tuple)):
                    requires = [requires]
                for r in requires:
                    if hasattr(r, "set_self_id"):
                        r.set_self_id(selected)

        # Mark required
        labels, required = s3_mark_required(fields)
        if required:
            s3.has_required = True

        # Generate embedded form
        form = SQLFORM.factory(table_name=self.component,
                               labels=labels,
                               formstyle=formstyle,
                               upload="default/download",
                               separator = "",
                               *fields)

        # Re-wrap the embedded form rows in an empty TAG
        formrows = []
        append = formrows.append
        for formrow in form[0]:
            if not formrow.attributes["_id"].startswith("submit_record"):
                if hasattr(formrow, "add_class"):
                    formrow.add_class("box_middle embedded-%s" % input_id)
                append(formrow)
        formrows = TAG[""](formrows)

        # Divider
        divider = widgetstyle("", "", "", "")
        divider.add_class("box_bottom embedded")

        # Widget script
        appname = request.application
        if s3.debug:
            script = "s3.ui.embeddedcomponent.js"
        else:
            script = "s3.ui.embeddedcomponent.min.js"
        script = "/%s/static/scripts/S3/%s" % (appname, script)
        if script not in s3.scripts:
            s3.scripts.append(script)

        # Script options
        url = "/%s/%s/%s/" % (appname, prefix, resourcename)
        options = {"ajaxURL": url,
                   "fieldname": input_id,
                   "component": self.component,
                   "recordID": str(value),
                   "autocomplete": True if autocomplete else False,
                   }

        # Post-process after Selection/Deselection
        post_process = s3db.get_config(self.link, "post_process")
        if post_process:
            try:
                pp = post_process % input_id
            except TypeError:
                pp = post_process
            options["postprocess"] = pp

        # Initialize UI Widget
        script = '''$('#%(input)s').embeddedComponent(%(options)s)''' % \
                 {"input": input_id,
                  "options": json.dumps(options, separators=JSONSEPARATORS),
                  }
        s3.jquery_ready.append(script)

        # Overall layout of components
        return TAG[""](controls, selector, formrows, divider)

    # -------------------------------------------------------------------------
    @staticmethod
    def _formstyle(row_id, label, widget, comments):
        """
            Fallback for legacy formstyles (i.e. not callable or tuple-rows)
        """

        return TR(TD(label, widget, _class="w2p_fw"),
                  TD(comments),
                  _id=row_id,
                  )

    # -------------------------------------------------------------------------
    @staticmethod
    def link_filter_query(table, expression):
        """
            Parse a link filter expression and convert it into an
            S3ResourceQuery that can be added to the search_ac resource.

            Link filter expressions are used to exclude records from
            the (autocomplete-)search that are already linked to the master
            record.

            Args:
                expression: the link filter expression

            General format:
                ?link=<linktablename>.<leftkey>.<id>.<rkey>.<fkey>

            Example:
                ?link=project_organisation.organisation_id.5.project_id.id
        """

        try:
            link, lkey, _id, rkey, fkey = expression.split(".")
        except ValueError:
            # Invalid expression
            return None
        linktable = current.s3db.table(link)
        if linktable:
            fq = (linktable[rkey] == table[fkey]) & \
                 (linktable[lkey] == _id)
            if "deleted" in linktable:
                fq &= (linktable.deleted == False)
            linked = current.db(fq).select(table._id)
            from ..resource import FS
            pkey = FS("id")
            exclude = (~(pkey.belongs([r[table._id.name] for r in linked])))
            return exclude
        return None

#==============================================================================
class S3GroupedOptionsWidget(EdenFormWidget):
    """
        Widget with checkboxes or radio buttons for OptionsFilter
        - checkboxes can be optionally grouped by letter
    """

    def __init__(self,
                 options = None,
                 multiple = True,
                 size = None,
                 cols = None,
                 help_field = None,
                 none = None,
                 sort = True,
                 orientation = None,
                 table = True,
                 no_opts = None,
                 option_comment = None,
                 ):
        """
            Args:
                options: the options for the SELECT, as list of tuples
                         [(value, label)], or as dict {value: label},
                         or None to auto-detect the options from the
                         Field when called
                multiple: multiple options can be selected
                size: maximum number of options in merged letter-groups,
                      None to not group options by initial letter
                cols: number of columns for the options table
                help_field: field in the referenced table to retrieve
                            a tooltip text from (for foreign keys only)
                none: True to render "None" as normal option
                sort: sort the options (only effective if size==None)
                orientation: the ordering orientation, "columns"|"rows"
                table: whether to render options inside a table or not
                no_opts: text to show if no options available
                option_comment: HTML template to render after the LABELs
        """

        self.options = options
        self.multiple = multiple
        self.size = size
        self.cols = cols or 3
        self.help_field = help_field
        self.none = none
        self.sort = sort
        self.orientation = orientation
        self.table = table
        self.no_opts = no_opts
        self.option_comment = option_comment

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Render this widget

            Args:
                field: the Field
                value: the currently selected value(s)
                attributes: HTML attributes for the widget
        """

        fieldname = field.name

        default = {"value": value}
        attr = self._attributes(field, default, **attributes)

        if "_id" in attr:
            _id = attr.pop("_id")
        else:
            _id = "%s-options" % fieldname
        attr["_id"] = _id
        if "_name" not in attr:
            attr["_name"] = fieldname

        options = self._options(field, value)
        if self.multiple:
            attr["_multiple"] = "multiple"
        widget = SELECT(**attr)
        if "empty" not in options:
            groups = options["groups"]
            append = widget.append
            render_group = self._render_group
            for group in groups:
                options = render_group(group)
                for option in options:
                    append(option)

        no_opts = self.no_opts
        if no_opts is None:
            no_opts = s3_str(current.T("No options available"))
        widget.add_class("groupedopts-widget")
        widget_opts = {"columns": self.cols,
                       "emptyText": no_opts,
                       "orientation": self.orientation or "columns",
                       "sort": self.sort,
                       "table": self.table,
                       }

        if self.option_comment:
            widget_opts["comment"] = self.option_comment
            include_underscore_js()

        script = '''$('#%s').groupedopts(%s)''' % \
                 (_id, json.dumps(widget_opts, separators=JSONSEPARATORS))
        jquery_ready = current.response.s3.jquery_ready
        if script not in jquery_ready:
            jquery_ready.append(script)

        return widget

    # -------------------------------------------------------------------------
    def _render_group(self, group):
        """
            Helper method to render an options group

            Args:
                group: the group as dict {label:label, items:[items]}
        """

        items = group["items"]
        if items:
            label = group["label"]
            render_item = self._render_item
            options = [render_item(i) for i in items]
            if label:
                return [OPTGROUP(options, _label=label)]
            else:
                return options
        else:
            return None

    # -------------------------------------------------------------------------
    @staticmethod
    def _render_item(item):
        """
            Helper method to render one option

            Args:
                item: the item as tuple (key, label, value, tooltip),
                      value=True indicates that the item is selected
        """

        key, label, value, tooltip = item
        attr = {"_value": key}
        if value:
            attr["_selected"] = "selected"
        if tooltip:
            attr["_title"] = tooltip
        return OPTION(label, **attr)

    # -------------------------------------------------------------------------
    def _options(self, field, value):
        """
            Find, group and sort the options

            Args:
                field: the Field
                value: the currently selected value(s)
        """

        # Get the options as sorted list of tuples (key, value)
        options = self.options
        if options is None:
            requires = field.requires
            if not isinstance(requires, (list, tuple)):
                requires = [requires]
            if hasattr(requires[0], "options"):
                options = requires[0].options()
            else:
                options = []
        elif isinstance(options, dict):
            options = options.items()
        none = self.none
        exclude = ("",) if none is not None else ("", None)

        options = [(s3_str(k) if k is not None else none,
                    # Not working with multi-byte str components:
                    #v.flatten()
                    #    if hasattr(v, "flatten") else s3_str(v))
                    s3_strip_markup(s3_str(v.xml()))
                        if isinstance(v, DIV) else s3_str(v))
                   for k, v in options if k not in exclude]

        # No options available?
        if not options:
            return {"empty": current.T("no options available")}

        # Get the current values as list of unicode
        if not isinstance(value, (list, tuple)):
            values = [value]
        else:
            values = value
        values = [s3_str(v) for v in values]

        # Get the tooltips as dict {key: tooltip}
        helptext = {}
        help_field = self.help_field
        if help_field:
            if callable(help_field):
                help_field = help_field(options)
            if isinstance(help_field, dict):
                for key in help_field.keys():
                    helptext[s3_str(key)] = help_field[key]
            else:
                ktablename, pkey = s3_get_foreign_key(field)[:2]
                if ktablename is not None:
                    ktable = current.s3db[ktablename]
                    if hasattr(ktable, help_field):
                        keys = [k for k, v in options if k.isdigit()]
                        query = ktable[pkey].belongs(keys)
                        rows = current.db(query).select(ktable[pkey],
                                                        ktable[help_field])
                        for row in rows:
                            helptext[s3_str(row[pkey])] = row[help_field]

        # Get all letters and their options
        letter_options = {}
        for key, label in options:
            letter = label
            if letter:
                letter = s3_str(label).upper()[0]
                if letter in letter_options:
                    letter_options[letter].append((key, label))
                else:
                    letter_options[letter] = [(key, label)]

        # Sort letters
        if letter_options:
            all_letters = sorted(letter_options.keys(), key=locale.strxfrm)
            first_letter = min("A", all_letters[0])
            last_letter = max("Z", all_letters[-1])
        else:
            # No point with grouping if we don't have any labels
            all_letters = []
            size = 0

        size = self.size

        close_group = self._close_group

        if size and len(options) > size and len(letter_options) > 1:
            # Multiple groups

            groups = []
            group = {"letters": [first_letter], "items": []}

            for letter in all_letters:

                group_items = group["items"]
                current_size = len(group_items)
                items = letter_options[letter]

                if current_size and current_size + len(items) > size:

                    # Close + append this group
                    close_group(group, values, helptext)
                    groups.append(group)

                    # Start a new group
                    group = {"letters": [letter], "items": items}

                else:

                    # Append current letter
                    if letter != group["letters"][-1]:
                        group["letters"].append(letter)

                    # Append items
                    group["items"].extend(items)

            if len(group["items"]):
                if group["letters"][-1] != last_letter:
                    group["letters"].append(last_letter)
                close_group(group, values, helptext)
                groups.append(group)

        else:
            # Only one group
            group = {"letters": None, "items": options}
            close_group(group, values, helptext, sort=self.sort)
            groups = [group]

        return {"groups": groups}

    # -------------------------------------------------------------------------
    @staticmethod
    def _close_group(group, values, helptext, sort=True):
        """
            Helper method to finalize an options group, render its label
            and sort the options

            Args:
                group: the group as dict {letters: [], items: []}
                values: the currently selected values as list
                helptext: dict of {key: helptext} for the options
        """

        # Construct the group label
        group_letters = group["letters"]
        if group_letters:
            if len(group_letters) > 1:
                group["label"] = "%s - %s" % (group_letters[0],
                                              group_letters[-1])
            else:
                group["label"] = group_letters[0]
        else:
            group["label"] = None
        del group["letters"]

        # Sort the group items
        if sort:
            group_items = sorted(group["items"],
                                 key = lambda i: i[1].upper()[0] \
                                       if i[1] else None,
                                 )
        else:
            group_items = group["items"]

        # Add tooltips
        items = []
        T = current.T
        for key, label in group_items:
            tooltip = helptext.get(key)
            if tooltip:
                tooltip = s3_str(T(tooltip))
            item = (key, label, key in values, tooltip)
            items.append(item)

        group["items"] = items
        return

# =============================================================================
class S3HiddenWidget(StringWidget):
    """
        Standard String widget, but with a class of hide
        - used by CAP
    """

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):

        default = {"_type": "text",
                   "value": (value is not None and str(value)) or "",
                   }
        attr = StringWidget._attributes(field, default, **attributes)
        attr["_class"] = "hide %s" % attr["_class"]

        return TAG[""](INPUT(**attr),
                       requires = field.requires
                       )

# =============================================================================
class S3ImageCropWidget(EdenFormWidget):
    """
        Allows the user to crop an image and uploads it.
        Cropping & Scaling (if necessary) done client-side
            - currently using JCrop (https://jcrop.com)
            - Uses the IS_PROCESSED_IMAGE validator

        TODO Replace with https://blueimp.github.io/jQuery-File-Upload/ ?
        TODO Doesn't currently work with Inline Component Forms
    """

    def __init__(self, image_bounds=None):
        """
            Args:
                image_bounds: Limits the Size of the Image that can be
                              uploaded, tuple (MaxWidth, MaxHeight)
        """
        self.image_bounds = image_bounds

    # -------------------------------------------------------------------------
    def __call__(self, field, value, download_url=None, **attributes):
        """
            Args:
                field: Field using this widget
                value: value if any
                download_url: Download URL for saved Image
        """

        T = current.T

        script_dir = "/%s/static/scripts" % current.request.application

        s3 = current.response.s3
        debug = s3.debug
        scripts = s3.scripts

        if debug:
            script = "%s/jquery.color.js" % script_dir
            if script not in scripts:
                scripts.append(script)
            script = "%s/jquery.Jcrop.js" % script_dir
            if script not in scripts:
                scripts.append(script)
            script = "%s/S3/s3.imagecrop.widget.js" % script_dir
            if script not in scripts:
                scripts.append(script)
        else:
            script = "%s/S3/s3.imagecrop.widget.min.js" % script_dir
            if script not in scripts:
                scripts.append(script)

        s3.js_global.append('''
i18n.invalid_image='%s'
i18n.supported_image_formats='%s'
i18n.upload_new_image='%s'
i18n.upload_image='%s' ''' % (T("Please select a valid image!"),
                              T("Supported formats"),
                              T("Upload different Image"),
                              T("Upload Image")))

        stylesheets = s3.stylesheets
        sheet = "plugins/jquery.Jcrop.css"
        if sheet not in stylesheets:
            stylesheets.append(sheet)

        attr = self._attributes(field, {"_type": "file",
                                        "_class": "imagecrop-upload"
                                        }, **attributes)

        elements = [INPUT(_type="hidden", _name="imagecrop-points")]
        append = elements.append

        append(DIV(_class="tooltip",
                   _title="%s|%s" % \
                 (T("Crop Image"),
                 T("Select an image to upload. You can crop this later by opening this record."))))

        # Set up the canvas
        # Canvas is used to scale and crop the Image on the client side
        canvas = TAG["canvas"](_class="imagecrop-canvas",
                               _style="display:none",
                               )
        image_bounds = self.image_bounds

        if image_bounds:
            canvas.attributes["_width"] = image_bounds[0]
            canvas.attributes["_height"] = image_bounds[1]
        else:
            # Images are not scaled and are uploaded as it is
            canvas.attributes["_width"] = 0

        append(canvas)

        btn_class = "imagecrop-btn button"

        buttons = [ A(T("Enable Crop"),
                      _id="select-crop-btn",
                      _class=btn_class,
                      _role="button"),
                    A(T("Crop Image"),
                      _id="crop-btn",
                      _class=btn_class,
                      _role="button"),
                    A(T("Cancel"),
                      _id="remove-btn",
                      _class="imagecrop-btn")
                    ]

        parts = [LEGEND(T("Uploaded Image"))] + buttons + \
                [HR(_style="display:none"),
                 IMG(_id="uploaded-image",
                     _style="display:none")
                 ]

        display_div = FIELDSET(parts,
                               _class="image-container")

        crop_data_attr = {"_type": "hidden",
                          "_name": "imagecrop-data",
                          "_class": "imagecrop-data"
                          }

        if value and download_url:
            if callable(download_url):
                download_url = download_url()

            url = "%s/%s" % (download_url, value)
            # Add Image
            crop_data_attr["_value"] = url
            append(FIELDSET(LEGEND(A(T("Upload different Image")),
                                   _id="upload-title"),
                            DIV(INPUT(**attr),
                                DIV(T("or Drop here"),
                                    _class="imagecrop-drag"),
                                _id="upload-container",
                                _style="display:none")))
        else:
            append(FIELDSET(LEGEND(T("Upload Image"),
                                   _id="upload-title"),
                            DIV(INPUT(**attr),
                                DIV(T("or Drop here"),
                                    _class="imagecrop-drag"),
                                _id="upload-container")))

        append(INPUT(**crop_data_attr))
        append(display_div)
        # Prevent multiple widgets on the same page from interfering with each
        # other.
        uid = "cropwidget-%s" % uuid4().hex
        for element in elements:
            element.attributes["_data-uid"] = uid

        return DIV(elements)

# =============================================================================
class ImageUploadWidget(EdenFormWidget):
    """
        Allows the user to select and crop an image for upload
            - cropping & scaling (if necessary) is done client-side
            - currently using JCrop (https://jcrop.com)
    """

    def __init__(self,
                 image_bounds = None,
                 use_camera = True,
                 ):
        """
            Args:
                image_bounds: Limits the Size of the Image that can be
                              uploaded, tuple (MaxWidth, MaxHeight)
                use_camera: activate option to capture images from built-in
                            or connected web camera
        """

        self.image_bounds = image_bounds

        if use_camera:
            # Apply global setting
            self.use_camera = current.deployment_settings.get_ui_image_upload_use_camera()
        else:
            # Never use camera, irrespective global setting
            self.use_camera = False

        self.widget_id = None

    # -------------------------------------------------------------------------
    def __call__(self, field, value, download_url=None, **attributes):
        """
            Args:
                field: Field using this widget
                value: value if any
                download_url: Download URL for saved Image
        """

        T = current.T

        # DOM node ID for the widget
        widget_id = self.widget_id = str(field).replace(".", "_")

        # Determine image URL and file name
        if value and download_url:
            if callable(download_url):
                download_url = download_url()
            url = "%s/%s" % (download_url, value)
            filename = field.retrieve(value, nameonly=True)[0]
        else:
            url = None
            filename = None

        # Configure post-processing of the uploaded image
        postprocess = self.process_image
        requires = field.requires
        if isinstance(requires, (tuple, list)):
            requires = [postprocess] + list(requires)
        elif requires:
            requires = [postprocess, requires]
        else:
            requires = postprocess

        # The file input
        # - not actually uploaded, image is read+processed client-side
        #   and then submitted as b64-encoded image data through hidden
        #   input (crop_data below)
        attr = self._attributes(field, {"_class": "imagecrop-upload",
                                        "_id": widget_id,
                                        "_type": "file",
                                        }, **attributes)
        attr["requires"] = requires
        file_input = INPUT(**attr)

        # The upload area
        # - a normal file input, an area for drag&drop
        if self.use_camera:
            # Add button to capture image from built-in/connected web camera
            capture_btn = BUTTON(ICON("fa fa-video-camera"), T("Capture Image from Video"),
                                 _type = "button",
                                 _class = "primary button action-btn capture-btn",
                                 )
        else:
            capture_btn = ""

        upload_title = T("Upload different Image") if url else T("Upload Image")
        upload_area = FIELDSET(LEGEND(upload_title, _class = "upload-title"),
                               DIV(file_input,
                                   DIV(T("or Drop here"), _class="imagecrop-drag"),
                                   capture_btn,
                                  _class = "upload-container",
                                  _style = "display:none" if url else None,
                                  ),
                               )

        # Hidden canvas
        # - used to scale and crop the image on the client side
        canvas = TAG["canvas"](_class="image-upload-canvas",
                               _style="display:none",
                               )

        image_bounds = self.image_bounds
        if image_bounds:
            canvas.attributes["_width"] = image_bounds[0]
            canvas.attributes["_height"] = image_bounds[1]
        else:
            # Images are not scaled and are uploaded as they are
            canvas.attributes["_width"] = 0

        # Preview + crop area
        btn_class = "imagecrop-btn button"
        crop_area = FIELDSET(LEGEND(T("Uploaded Image")),
                             A(T("Enable Crop"),
                               _class = "select-crop-btn %s" % btn_class,
                               ),
                             A(T("Crop Image"),
                               _class = "crop-btn %s" % btn_class,
                               ),
                             A(T("Cancel"),
                               _class = "remove-btn %s" % btn_class,
                               ),
                             HR(_style = "display:none"),
                             IMG(_class = "uploaded-image",
                                 _style = "display:none",
                                 ),
                             )

        # Hidden input for the cropped image
        crop_data_id = "%s-imagecrop-data" % widget_id
        crop_data_attr = {"_type": "hidden",
                          "_name": crop_data_id,
                          "_id": crop_data_id,
                          "_class": "imagecrop-data"
                          }
        if url and filename:
            crop_data_attr["data"] = {"url": url,
                                      "filename": filename,
                                      }
        crop_data = INPUT(**crop_data_attr)

        # Inject scripts + styles
        widget_opts = {}
        self.inject_script(widget_id, widget_opts)

        return DIV(upload_area,
                   canvas,
                   crop_area,
                   crop_data,
                   _class = "image-upload",
                   )

    # -------------------------------------------------------------------------
    def process_image(self, value):
        """
            Post-processes the uploaded (+cropped) image

            Args:
                value: the input value (=uploaded image)

            Returns:
                a tuple (value, error), with value being the processed
                image as Storage {filename, file} (or a FieldStorage if
                the input already contains a file)
        """

        # If there is an uploaded file, accept it as-is
        if value not in ("", b"", None):
            return value, None

        # Check for cropped image
        variable = "%s-imagecrop-data" % self.widget_id
        cropped_image = current.request.post_vars.get(variable)
        if not cropped_image:
            return None, current.T("No image was specified!")

        # Parse the data
        try:
            metadata, cropped_image = cropped_image.rsplit(",", 1)
            filename = metadata.rsplit(";", 2)[0]
        except (ValueError, TypeError):
            return None, current.T("invalid value!")

        # Decode the base64-encoded image
        import base64
        f = Storage()
        f.filename = filename
        f.file = BytesIO(base64.b64decode(cropped_image))

        return f, None

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_script(widget_id, options):
        """
            Injects scripts and styles used by this widget

            Args:
                widget_id: the DOM node ID of the widget
                options: JSON-serializable dict of widget options
        """

        T = current.T
        s3 = current.response.s3

        # Static JavaScript
        script_dir = "/%s/static/scripts" % current.request.application
        debug = s3.debug
        if debug:
            scripts = ["jquery.color.js",
                       "jquery.Jcrop.js",
                       "S3/s3.ui.imageupload.js",
                       ]
        else:
            scripts = ["S3/s3.ui.imageupload.min.js",
                       ]
        for script in scripts:
            path = "%s/%s" % (script_dir, script)
            if path not in s3.scripts:
                s3.scripts.append(path)

        # CSS used by static scripts
        sheet = "plugins/jquery.Jcrop.css"
        if sheet not in s3.stylesheets:
            s3.stylesheets.append(sheet)

        # I18n strings
        s3.js_global.append('''
i18n.capture_image_from_video='%s'
i18n.capture_image_ok='%s'
i18n.invalid_image='%s'
i18n.supported_image_formats='%s'
i18n.upload_new_image='%s'
i18n.upload_image='%s' ''' % (T("Capture Image from Video"),
                              T("OK"),
                              T("Please select a valid image!"),
                              T("Supported formats"),
                              T("Upload different Image"),
                              T("Upload Image"),
                              ))

        # Widget instantiation
        script = """$('#%s').imageUpload(%s);""" % (widget_id, json.dumps(options))
        if script not in s3.jquery_ready:
            s3.jquery_ready.append(script)

# =============================================================================
class S3InvBinWidget(FormWidget):
    """
        Widget used by BasicCRUD to offer the user matching bins where
        stock items can be placed
    """

    def __init__(self,
                 tablename,):
        self.tablename = tablename

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):

        T = current.T
        request = current.request
        s3db = current.s3db
        tracktable = s3db.inv_track_item
        stocktable = s3db.inv_inv_item

        new_div = INPUT(value = value or "",
                        requires = field.requires,
                        _id = "i_%s_%s" % (self.tablename, field.name),
                        _name = field.name,
                       )
        id = None
        function = self.tablename[4:]
        if len(request.args) > 2:
            if request.args[1] == function:
                id = request.args[2]

        if id == None or tracktable[id] == None:
            return TAG[""](
                           new_div
                          )

        record = tracktable[id]
        site_id = s3db.inv_recv[record.recv_id].site_id
        query = (stocktable.site_id == site_id) & \
                (stocktable.item_id == record.item_id) & \
                (stocktable.item_source_no == record.item_source_no) & \
                (stocktable.item_pack_id == record.item_pack_id) & \
                (stocktable.currency == record.currency) & \
                (stocktable.pack_value == record.pack_value) & \
                (stocktable.expiry_date == record.expiry_date) & \
                (stocktable.supply_org_id == record.supply_org_id)
        rows = current.db(query).select(stocktable.bin,
                                        stocktable.id)
        if len(rows) == 0:
            return TAG[""](
                           new_div
                          )
        bins = []
        for row in rows:
            bins.append(OPTION(row.bin))

        match_lbl = LABEL(T("Select an existing bin"))
        match_div = SELECT(bins,
                           _id = "%s_%s" % (self.tablename, field.name),
                           _name = field.name,
                           )
        new_lbl = LABEL(T("...or add a new bin"))
        return TAG[""](match_lbl,
                       match_div,
                       new_lbl,
                       new_div
                       )

# =============================================================================
class S3KeyValueWidget(ListWidget):
    """
        Allows for input of key-value pairs and stores them as list:string
    """

    def __init__(self, key_label=None, value_label=None):
        """
            Returns a widget with key-value fields
        """
        self._class = "key-value-pairs"
        T = current.T

        self.key_label = key_label or T("Key")
        self.value_label = value_label or T("Value")

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):

        s3 = current.response.s3

        _id = "%s_%s" % (field._tablename, field.name)
        _name = field.name
        _class = "text hide"

        attributes["_id"] = _id
        attributes["_name"] = _name
        attributes["_class"] = _class

        script = SCRIPT(
'''jQuery(document).ready(function(){jQuery('#%s').kv_pairs('%s','%s')})''' % \
    (_id, self.key_label, self.value_label))

        if not value:
            value = "[]"
        if not isinstance(value, str):
            try:
                value = json.dumps(value, separators=JSONSEPARATORS)
            except:
                raise ValueError("Bad value for key-value pair field")
        appname = current.request.application
        jsfile = "/%s/static/scripts/S3/%s" % (appname, "s3.keyvalue.widget.js")

        if jsfile not in s3.scripts:
            s3.scripts.append(jsfile)

        return TAG[""](
                    TEXTAREA(value, **attributes),
                    script
               )

    # -------------------------------------------------------------------------
    @staticmethod
    def represent(value):
        if isinstance(value, str):
            try:
                value = json.loads(value)
                if isinstance(value, str):
                    raise ValueError("key-value JSON is wrong.")
            except:
                # XXX: log this!
                #raise ValueError("Bad json was found as value for a key-value field: %s" % value)
                return ""

        rep = []
        if isinstance(value, (tuple, list)):
            for kv in value:
                rep += ["%s: %s" % (kv["key"], kv["value"])]
        return ", ".join(rep)

# =============================================================================
class S3LatLonWidget(DoubleWidget):
    """
        Widget for latitude or longitude input, gives option to input in terms
        of degrees, minutes and seconds
    """

    def __init__(self, type, switch=False, disabled=False):
        self.type = type
        self.disabled = disabled
        self.switch = switch

    # -------------------------------------------------------------------------
    def widget(self, field, value, **attributes):

        T = current.T
        s3 = current.response.s3
        switch = self.switch

        if field:
            # LocationLatLonWidget
            id = name = "%s_%s" % (str(field).replace(".", "_"), self.type)
        else:
            # LocationSelectorWidget[2]
            id = name = "gis_location_%s" % self.type
        attr = {"value": value,
                "_class": "decimal %s" % self._class,
                "_id": id,
                "_name": name,
                }

        attr_dms = {}

        if self.disabled:
            attr["_disabled"] = "disabled"
            attr_dms["_disabled"] = "disabled"

        dms_boxes = SPAN(INPUT(_class="degrees", **attr_dms), "° ",
                         INPUT(_class="minutes", **attr_dms), "' ",
                         INPUT(_class="seconds", **attr_dms), "\" ",
                         ["",
                          DIV(A(T("Use decimal"),
                                _class="action-btn gis_coord_switch_decimal"))
                          ][switch],
                         _style="display:none",
                         _class="gis_coord_dms",
                         )

        decimal = SPAN(INPUT(**attr),
                       ["",
                        DIV(A(T("Use deg, min, sec"),
                              _class="action-btn gis_coord_switch_dms"))
                        ][switch],
                       _class="gis_coord_decimal",
                       )

        if not s3.lat_lon_i18n_appended:
            s3.js_global.append('''
i18n.gis_only_numbers={degrees:'%s',minutes:'%s',seconds:'%s',decimal:'%s'}
i18n.gis_range_error={degrees:{lat:'%s',lon:'%s'},minutes:'%s',seconds:'%s',decimal:{lat:'%s',lon:'%s'}}
''' %  (T("Degrees must be a number."),
        T("Minutes must be a number."),
        T("Seconds must be a number."),
        T("Degrees must be a number."),
        T("Degrees in a latitude must be between -90 to 90."),
        T("Degrees in a longitude must be between -180 to 180."),
        T("Minutes must be less than 60."),
        T("Seconds must be less than 60."),
        T("Latitude must be between -90 and 90."),
        T("Longitude must be between -180 and 180.")))

            if s3.debug:
                script = "/%s/static/scripts/S3/s3.gis.latlon.js" % \
                            current.request.application
            else:
                script = "/%s/static/scripts/S3/s3.gis.latlon.min.js" % \
                            current.request.application
            s3.scripts.append(script)
            s3.lat_lon_i18n_appended = True

        return SPAN(decimal,
                    dms_boxes,
                    _class="gis_coord_wrap",
                    )

# =============================================================================
class S3LocationDropdownWidget(EdenFormWidget):
    """
        Renders a dropdown for an Lx level of location hierarchy
    """

    def __init__(self,
                 level = "L0",
                 default = None,
                 validate = False,
                 empty = DEFAULT,
                 blank = False,
                 ):
        """
            Args:
                level: the Lx-level (as string)
                default: the default location name
                validate: validate input in-widget (special purpose)
                empty: allow selection to be empty
                blank: start without options (e.g. when options are
                       Ajax-added later by filterOptionsS3)
        """

        self.level = level
        self.default = default
        self.validate = validate
        self.empty = empty
        self.blank = blank

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):

        level = self.level
        default = self.default
        empty = self.empty

        opts = []
        # Get locations
        s3db = current.s3db
        table = s3db.gis_location
        if self.blank:
            query = (table.id == value)
        elif level:
            query = (table.deleted == False) & \
                    (table.level == level)
        else:
            # Workaround for merge form
            query = (table.id == value)
        locations = current.db(query).select(table.name,
                                             table.id,
                                             cache=s3db.cache)

        # Build OPTIONs
        for location in locations:
            opts.append(OPTION(location.name, _value=location.id))
            if not value and default and location.name == default:
                value = location.id

        # Widget attributes
        attr = dict(attributes)
        attr["_type"] = "int"
        attr["value"] = value
        attr = OptionsWidget._attributes(field, attr)

        if self.validate:
            # Validate widget input to enforce Lx subset
            # - not normally needed (Field validation should suffice)
            requires = IS_IN_SET(locations.as_dict())
            if empty is DEFAULT:
                # Introspect the field
                empty = isinstance(field.requires, IS_EMPTY_OR)
            if empty:
                requires = IS_EMPTY_OR(requires)

            # Skip in-widget validation on POST if inline
            widget_id = attr.get("_id")
            if widget_id and widget_id[:4] == "sub_":
                from ..tools import SKIP_VALIDATION
                requires = SKIP_VALIDATION(requires)

            widget = TAG[""](SELECT(*opts, **attr), requires = requires)
        else:
            widget = SELECT(*opts, **attr)

        return widget

# =============================================================================
class S3LocationLatLonWidget(EdenFormWidget):
    """
        Renders a Lat & Lon input for a Location
    """

    def __init__(self, empty=False):

        self.empty = empty

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):

        T = current.T
        empty = self.empty
        requires = IS_LAT_LON(field)
        if empty:
            requires = IS_EMPTY_OR(requires)

        defaults = {"_type": "text",
                    "value": (value is not None and str(value)) or "",
                    }
        attr = StringWidget._attributes(field, defaults, **attributes)
        # Hide the real field
        attr["_class"] = "hide"

        if value:
            db = current.db
            table = db.gis_location
            record = db(table.id == value).select(table.lat,
                                                  table.lon,
                                                  limitby=(0, 1)
                                                  ).first()
            try:
                lat = record.lat
                lon = record.lon
            except AttributeError:
                lat = None
                lon = None
        else:
            lat = None
            lon = None

        rows = TAG[""]()

        formstyle = current.response.s3.crud.formstyle

        comment = ""
        selector = str(field).replace(".", "_")
        row_id = "%s_lat" % selector
        label = T("Latitude")
        widget = S3LatLonWidget("lat").widget(field, lat)
        label = "%s:" % label
        if not empty:
            label = DIV(label,
                        SPAN(" *", _class="req"))

        row = formstyle(row_id, label, widget, comment)
        if isinstance(row, tuple):
            for r in row:
                rows.append(r)
        else:
            rows.append(row)

        row_id = "%s_lon" % selector
        label = T("Longitude")
        widget = S3LatLonWidget("lon", switch=True).widget(field, lon)
        label = "%s:" % label
        if not empty:
            label = DIV(label,
                        SPAN(" *", _class="req"))
        row = formstyle(row_id, label, widget, comment)
        if isinstance(row, tuple):
            for r in row:
                rows.append(r)
        else:
            rows.append(row)

        return TAG[""](INPUT(**attr),
                       *rows,
                       requires = requires
                       )

# =============================================================================
class EmptyOptionsWidget(OptionsWidget):
    """
        Version of OptionsWidget that passes the currently selected option
        additionally as data-attribute; required for IS_ONE_OF_EMPTY_SELECT
        with filterOptionsS3
    """

    @classmethod
    def widget(cls, field, value, **attributes):

        widget = super().widget(field, value, **attributes)
        if value is not None:
            widget["data"] = {"selected": s3_str(value)}

        return widget

# =============================================================================
class S3SelectWidget(OptionsWidget):
    """
        Standard OptionsWidget, but using the jQuery UI SelectMenu:
            http://jqueryui.com/selectmenu/

        Useful for showing Icons against the Options.
    """

    def __init__(self, icons=False):
        """
            Args:
                icons: show icons next to options, can be:
                        - False (don't show icons)
                        - function (function to call add Icon URLs, height and
                          width to the options)
        """

        self.icons = icons

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attr):

        # Widget ID (the DOM node ID for the original SELECT)
        selector = attr.get("_id")
        if not selector:
            if isinstance(field, Field):
                selector = str(field).replace(".", "_")
            else:
                selector = field.name.replace(".", "_")

        # Widget
        _class = attr.get("_class", None)
        if _class:
            if "select-widget" not in _class:
                attr["_class"] = "%s select-widget" % _class
        else:
            attr["_class"] = "select-widget"

        widget = TAG[""](self.widget(field, value, **attr),
                         requires = field.requires)

        if self.icons:
            # Use custom subclass in S3.js
            fn = "iconselectmenu().iconselectmenu('menuWidget').addClass('customicons')"
        else:
            # Use default
            fn = "selectmenu()"
        script = '''$('#%s').%s''' % (selector, fn)

        jquery_ready = current.response.s3.jquery_ready
        if script not in jquery_ready: # Prevents loading twice when form has errors
            jquery_ready.append(script)

        return widget

    # -------------------------------------------------------------------------
    def widget(self, field, value, **attributes):
        """
            Generates a SELECT tag, including OPTIONs (only 1 option allowed)
            see also: `FormWidget.widget`
        """

        default = {"value": value,
                   }
        attr = self._attributes(field, default,
                               **attributes)
        requires = field.requires
        if not isinstance(requires, (list, tuple)):
            requires = [requires]
        if requires:
            if hasattr(requires[0], "options"):
                options = requires[0].options()
            else:
                raise SyntaxError(
                    "widget cannot determine options of %s" % field)
        icons = self.icons
        if icons:
            # Options including Icons
            # Add the Icons to the Options
            options = icons(options)
            opts = []
            oappend = opts.append
            for (k, v, i) in options:
                oattr = {"_value": k,
                         #"_data-class": "select-widget-icon",
                         }
                if i:
                    oattr["_data-style"] = "background-image:url('%s');height:%spx;width:%spx" % \
                        (i[0], i[1], i[2])
                opt = OPTION(v, **oattr)
                oappend(opt)
        else:
            # Standard Options
            opts = [OPTION(v, _value=k) for (k, v) in options]

        return SELECT(*opts, **attr)

# =============================================================================
class S3MultiSelectWidget(MultipleOptionsWidget):
    """
        Standard MultipleOptionsWidget, but using the jQuery UI:
            http://www.erichynds.com/jquery/jquery-ui-multiselect-widget/
            static/scripts/ui/multiselect.js
    """

    def __init__(self,
                 search = "auto",
                 header = True,
                 multiple = True,
                 selectedList = 3,
                 noneSelectedText = "Select",
                 columns = None,
                 create = None,
                 ):
        """
            Args:
                search: show an input field in the widget to search for options,
                        can be:
                            - True (always show search field)
                            - False (never show the search field)
                            - "auto" (show search if more than 10 options)
                            - <number> (show search if more than <number> options)
                header: show a header for the options list, can be:
                            - True (show the default Select All/Deselect All header)
                            - False (don't show a header unless required for search field)
                selectedList: maximum number of individual selected options to show
                              on the widget button (before collapsing into "<number>
                              selected")
                noneSelectedText: text to show on the widget button when no option is
                                  selected (automatic l10n, no T() required)
                columns: set the columns width class for Foundation forms
                create: options to create a new record, a dict like
                            {"c": "controller",
                             "f": "function",
                             "label": "label",
                             "parent": "parent", (optional: which function to lookup options from)
                             "child": "child", (optional: which field to lookup options for)
                             }

            TODO Complete the 'create' feature:
                 * Ensure the Create option doesn't get filtered out when searching for items
                 * Style option to make it clearer that it's an Action item
        """

        self.search = search
        self.header = header
        self.multiple = multiple
        self.selectedList = selectedList
        self.noneSelectedText = noneSelectedText
        self.columns = columns
        self.create = create

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attr):

        T = current.T

        # Widget ID (the DOM node ID for the original SELECT)
        selector = attr.get("_id")
        if not selector:
            if isinstance(field, Field):
                selector = str(field).replace(".", "_")
            else:
                selector = field.name.replace(".", "_")

        # Widget
        _class = attr.get("_class", None)
        if _class:
            if "multiselect-widget" not in _class:
                attr["_class"] = "%s multiselect-widget" % _class
        else:
            attr["_class"] = "multiselect-widget"

        multiple_opt = self.multiple
        if multiple_opt:
            w = MultipleOptionsWidget
        else:
            w = OptionsWidget
            if value:
                # Base widget requires single value, so enforce that
                # if necessary, and convert to string to match options
                value = str(value[0] if type(value) is list else value)

        # Set explicit columns width for the formstyle
        if self.columns:
            attr["s3cols"] = self.columns

        widget = w.widget(field, value, **attr)
        options_len = len(widget)

        # Search field and header for multiselect options list
        search_opt = self.search
        header_opt = self.header
        if not multiple_opt and header_opt is True:
            # Select All / Unselect All doesn't make sense if multiple == False
            header_opt = False
        if not isinstance(search_opt, bool) and \
           (search_opt == "auto" or isinstance(search_opt, int)):
            max_options = 10 if search_opt == "auto" else search_opt
            search_opt = bool(options_len > max_options)
        if search_opt is True and header_opt is False:
            # Must have at least "" as header to show the search field
            header_opt = ""

        # Other options:
        # * Show Selected List
        if header_opt is True:
            header_labels = {"checkAll": T("Select All"),
                             "uncheckAll": T("Clear All"),
                             }
            o, l = [], []
            for k, v in header_labels.items():
                o.append("%sText:'%s'" % (k, str(v)))
                l.append("%s:{text:'%s',title:'%s'}" % (k, str(v), str(v)))
            header = ",".join(o) + ",linkInfo:{%s}" % ",".join(l)

            # header_labels = {"check_all": T("Select All"),
            #                  "uncheck_all": T("Clear All"),
            #                  }
            # header = '''checkAllText:'%(check_all)s',uncheckAllText:'%(uncheck_all)s',linkInfo:{checkAll:{text:'%(check_all)s',title:'%(check_all)s'}, uncheckAll:{text:'%(uncheck_all)s',title:'%(uncheck_all)s'} }''' % header_labels
        elif header_opt is False:
            header = '''header:false'''
        else:
            header = '''header:"%s"''' % header_opt
        noneSelectedText = self.noneSelectedText
        if not isinstance(noneSelectedText, lazyT):
            noneSelectedText = T(noneSelectedText)
        create = self.create or ""
        if create:
            tablename = "%s_%s" % (create["c"], create["f"])
            if current.auth.s3_has_permission("create", tablename):
                create = ",create:%s" % json.dumps(create, separators=JSONSEPARATORS)
            else:
                create = ""
        script = '''$('#%s').multiselect({allSelectedText:'%s',selectedText:'%s',%s,height:300,minWidth:0,selectedList:%s,noneSelectedText:'%s',multiple:%s%s})''' % \
                 (selector,
                  T("All selected"),
                  T("# selected"),
                  header,
                  self.selectedList,
                  noneSelectedText,
                  "true" if multiple_opt else "false",
                  create
                  )

        if search_opt:
            script = '''%s.multiselectfilter({label:'',placeholder:'%s'})''' % \
                (script, T("Search"))
        jquery_ready = current.response.s3.jquery_ready
        if script not in jquery_ready: # Prevents loading twice when form has errors
            jquery_ready.append(script)

        return widget

# =============================================================================
class S3CascadeSelectWidget(EdenFormWidget):
    """ Cascade Selector for Hierarchies """

    def __init__(self,
                 lookup=None,
                 formstyle=None,
                 levels=None,
                 multiple=False,
                 filter=None,
                 leafonly=True,
                 cascade=None,
                 represent=None,
                 inline=False,
                 ):
        """
            Args:
                lookup: the name of the hierarchical lookup-table
                formstyle: the formstyle to use for the inline-selectors
                           (defaults to s3.crud.formstyle)
                levels: list of labels for the hierarchy levels, in
                        top-down order
                multiple: allow selection of multiple options
                filter: resource filter expression to filter the
                        selectable options
                leafonly: allow only leaf-nodes to be selected
                cascade: automatically select child-nodes when a parent node
                         is selected (override option, implied by leafonly
                         if not set explicitly)
                represent: representation function for the nodes
                           (defaults to the represent of the field)
                inline: formstyle uses inline-labels, so add a colon
        """

        self.lookup = lookup
        self.formstyle = formstyle

        self.levels = levels
        self.multiple = multiple

        self.filter = filter
        self.leafonly = leafonly
        self.cascade = cascade

        self.represent = represent
        self.inline = inline

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attr):
        """
            Widget renderer

            Args:
                field: the Field
                value: the current value(s)
                attr: additional HTML attributes for the widget
        """

        # Get the lookup table
        lookup = self.lookup
        if not lookup:
            lookup = s3_get_foreign_key(field)[0]
            if not lookup:
                raise SyntaxError("No lookup table known for %s" % field)

        # Get the representation
        represent = self.represent
        if not represent:
            represent = field.represent

        # Get the hierarchy
        leafonly = self.leafonly
        from ..tools import S3Hierarchy
        h = S3Hierarchy(tablename = lookup,
                        represent = represent,
                        filter = self.filter,
                        leafonly = leafonly,
                        )
        if not h.config:
            raise AttributeError("No hierarchy configured for %s" % lookup)

        # Get the cascade levels
        levels = self.levels
        if not levels:
            levels = current.s3db.get_config(lookup, "hierarchy_levels")
        if not levels:
            levels = [field.label]

        # Get the hierarchy nodes
        nodes = h.json(max_depth=len(levels)-1)

        # Intended DOM-ID of the input field
        if isinstance(field, Field):
            input_id = str(field).replace(".", "_")
        else:
            input_id = field.name.replace(".", "_")

        # Prepare labels and selectors
        selectors = []
        multiple = "multiple" if self.multiple else None
        T = current.T
        for depth, level in enumerate(levels):
            # The selector for this level
            selector = SELECT(data = {"level": depth},
                              _class = "s3-cascade-select",
                              _disabled = "disabled",
                              _multiple = multiple,
                              )

            # The label for the selector
            row_id = "%s_level_%s" % (input_id, depth)
            label = T(level) if isinstance(level, str) else level
            if self.inline:
                label = "%s:" % label
            label = LABEL(label, _for=row_id, _id="%s__label" % row_id)
            selectors.append((row_id, label, selector, None))

        # Build inline-rows from labels+selectors
        formstyle = self.formstyle
        if not formstyle:
            formstyle = current.response.s3.crud.formstyle
        selector_rows = formstyle(None, selectors)

        # Construct the widget
        widget_id = attr.get("_id")
        if not widget_id:
            widget_id = "%s-cascade" % input_id
        widget = DIV(self.hidden_input(input_id, field, value, **attr),
                     INPUT(_type = "hidden",
                           _class = "s3-cascade",
                           _value = json.dumps(nodes, separators=JSONSEPARATORS),
                           ),
                     selector_rows,
                     _class = "s3-cascade-select",
                     _id = widget_id,
                     )

        # Inject static JS and instantiate UI widget
        cascade = self.cascade
        if leafonly and cascade is not False:
            cascade = True

        widget_opts = {"multiple": True if multiple else False,
                       "leafonly": leafonly,
                       "cascade": cascade,
                       }
        self.inject_script(widget_id, widget_opts)

        return widget

    # -------------------------------------------------------------------------
    def hidden_input(self, input_id, field, value, **attr):
        """
            Construct the hidden (real) input and populate it with the
            current field value

            Args:
                input_id: the DOM-ID for the input
                field: the Field
                value: the current value
                attr: widget attributes from caller
        """

        # Currently selected values
        selected = []
        append = selected.append
        if isinstance(value, str) and value and not value.isdigit():
            value = self.parse(value)[0]
        if not isinstance(value, (list, tuple, set)):
            values = [value]
        else:
            values = value
        for v in values:
            if isinstance(v, int) or str(v).isdigit():
                append(v)

        # Prepend value parser to field validator
        requires = field.requires
        if isinstance(requires, (list, tuple)):
            requires = [self.parse] + requires
        elif requires is not None:
            requires = [self.parse, requires]
        else:
            requires = self.parse

        # The hidden input field
        hidden_input = INPUT(_type = "hidden",
                             _name = attr.get("_name") or field.name,
                             _id = input_id,
                             _class = "s3-cascade-input",
                             requires = requires,
                             value = json.dumps(selected, separators=JSONSEPARATORS),
                             )

        return hidden_input

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_script(widget_id, options):
        """
            Inject static JS and instantiate client-side UI widget

            Args:
                widget_id: the widget ID
                options: JSON-serializable dict with UI widget options
        """

        request = current.request
        s3 = current.response.s3

        # Static script
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.ui.cascadeselect.js" % \
                     request.application
        else:
            script = "/%s/static/scripts/S3/s3.ui.cascadeselect.min.js" % \
                     request.application
        scripts = s3.scripts
        if script not in scripts:
            scripts.append(script)

        # Widget options
        opts = {}
        if options:
            opts.update(options)

        # Widget instantiation
        script = '''$('#%(widget_id)s').cascadeSelect(%(options)s)''' % \
                 {"widget_id": widget_id,
                  "options": json.dumps(opts, separators=JSONSEPARATORS),
                  }
        jquery_ready = s3.jquery_ready
        if script not in jquery_ready:
            jquery_ready.append(script)

    # -------------------------------------------------------------------------
    def parse(self, value, record_id=None):
        """
            Value parser for the hidden input field of the widget

            Args:
                value: the value received from the client, JSON string
                record_id: the record ID (unused, for API compatibility)

            Returns:
                a list (if multiple=True) or the value
        """

        default = [] if self.multiple else None

        if value is None:
            return None, None
        try:
            value = json.loads(value)
        except ValueError:
            return default, None
        if not self.multiple and isinstance(value, list):
            value = value[0] if value else None

        return value, None

# =============================================================================
class S3HierarchyWidget(EdenFormWidget):
    """ Selector Widget for Hierarchies """

    def __init__(self,
                 lookup = None,
                 represent = None,
                 multiple = True,
                 leafonly = True,
                 cascade = False,
                 bulk_select = False,
                 filter = None,
                 columns = None,
                 none = None,
                 ):
        """
            Args:
                lookup: name of the lookup table (must have a hierarchy
                        configured)
                represent: alternative representation method (falls back
                           to the field's represent-method)
                multiple: allow selection of multiple options
                leafonly: True = only leaf nodes can be selected (with
                          multiple=True: selection of a parent node will
                          automatically select all leaf nodes of that
                          branch)
                          False = any nodes can be selected independently
                cascade: automatic selection of children when selecting
                         a parent node (if leafonly=False, otherwise
                         this is the standard behavior!), requires
                         multiple=True
                bulk_select: provide option to select/deselect all nodes
                filter: filter query for the lookup table
                columns: set the columns width class for Foundation forms
                none: label for an option that delivers "None" as value
                      (useful for HierarchyFilters with explicit none-selection)
        """

        self.lookup = lookup
        self.represent = represent
        self.filter = filter

        self.multiple = multiple
        self.leafonly = leafonly
        self.cascade = cascade

        self.columns = columns
        self.bulk_select = bulk_select

        self.none = none

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attr):
        """
            Widget renderer

            Args:
                field: the Field
                value: the current value(s)
                attr: additional HTML attributes for the widget
        """

        selector = widget_id = attr.get("_id")
        if not selector:
            if isinstance(field, Field):
                selector = str(field).replace(".", "_")
            else:
                selector = field.name.replace(".", "_")

        # Widget ID
        if not widget_id:
            widget_id = attr["_id"] = "%s-hierarchy" % selector

        # Field name
        name = attr.get("_name")
        if not name:
            name = field.name

        # Get the lookup table
        lookup = self.lookup
        if not lookup:
            lookup = s3_get_foreign_key(field)[0]
            if not lookup:
                raise SyntaxError("No lookup table known for %s" % field)

        # Get the representation
        represent = self.represent
        if not represent:
            represent = field.represent

        # Instantiate the hierarchy
        leafonly = self.leafonly
        from ..tools import S3Hierarchy
        h = S3Hierarchy(tablename = lookup,
                        represent = represent,
                        leafonly = leafonly,
                        filter = self.filter,
                        )
        if not h.config:
            raise AttributeError("No hierarchy configured for %s" % lookup)

        # Set explicit columns width for the formstyle
        if self.columns:
            attr["s3cols"] = self.columns

        # Generate the widget
        settings = current.deployment_settings
        cascade_option_in_tree = settings.get_ui_hierarchy_cascade_option_in_tree()

        if self.multiple and self.bulk_select and \
           not cascade_option_in_tree:
            # Render bulk-select options as separate header
            header = DIV(SPAN(A("Select All",
                                _class = "s3-hierarchy-select-all",
                                ),
                              " | ",
                              A("Deselect All",
                                _class = "s3-hierarchy-deselect-all",
                                ),
                              _class = "s3-hierarchy-bulkselect",
                              ),
                         _class = "s3-hierarchy-header",
                         )
        else:
            header = ""

        # Currently selected values
        selected = []
        append = selected.append
        if isinstance(value, str) and value and not value.isdigit():
            value = self.parse(value)[0]
        if not isinstance(value, (list, tuple, set)):
            values = [value]
        else:
            values = value
        for v in values:
            if isinstance(v, int) or str(v).isdigit():
                append(v)

        # Prepend value parser to field validator
        requires = field.requires
        if isinstance(requires, (list, tuple)):
            requires = [self.parse] + requires
        elif requires is not None:
            requires = [self.parse, requires]
        else:
            requires = self.parse

        # The hidden input field
        hidden_input = INPUT(_type = "hidden",
                             _multiple = "multiple",
                             _name = name,
                             _id = selector,
                             _class = "s3-hierarchy-input",
                             requires = requires,
                             value = json.dumps(selected, separators=JSONSEPARATORS),
                             )

        # The widget
        widget = DIV(hidden_input,
                     DIV(header,
                         DIV(h.html("%s-tree" % widget_id,
                                    none=self.none,
                                    ),
                             _class = "s3-hierarchy-tree",
                             ),
                         _class = "s3-hierarchy-wrapper",
                         ),
                     **attr)
        widget.add_class("s3-hierarchy-widget")

        s3 = current.response.s3
        scripts = s3.scripts
        script_dir = "/%s/static/scripts" % current.request.application

        # Custom theme
        theme = settings.get_ui_hierarchy_theme()

        if s3.debug:
            script = "%s/jstree.js" % script_dir
            if script not in scripts:
                scripts.append(script)
            script = "%s/S3/s3.ui.hierarchicalopts.js" % script_dir
            if script not in scripts:
                scripts.append(script)
            style = "%s/jstree.css" % theme.get("css", "plugins")
            if style not in s3.stylesheets:
                s3.stylesheets.append(style)
        else:
            script = "%s/S3/s3.jstree.min.js" % script_dir
            if script not in scripts:
                scripts.append(script)
            style = "%s/jstree.min.css" % theme.get("css", "plugins")
            if style not in s3.stylesheets:
                s3.stylesheets.append(style)

        T = current.T

        widget_opts = {"selected": selected,
                       "selectedText": str(T("# selected")),
                       "noneSelectedText": str(T("Select")),
                       "noOptionsText": str(T("No options available")),
                       "selectAllText": str(T("Select All")),
                       "deselectAllText": str(T("Deselect All")),
                       }

        # Only include non-default options
        if not self.multiple:
            widget_opts["multiple"] = False
        if not leafonly:
            widget_opts["leafonly"] = False
        if self.cascade:
            widget_opts["cascade"] = True
        if self.bulk_select:
            widget_opts["bulkSelect"] = True
        if not cascade_option_in_tree:
            widget_opts["cascadeOptionInTree"] = False
        icons = theme.get("icons", False)
        if icons:
            widget_opts["icons"] = icons
        stripes = theme.get("stripes", True)
        if not stripes:
            widget_opts["stripes"] = stripes


        script = '''$('#%(widget_id)s').hierarchicalopts(%(widget_opts)s)''' % \
                 {"widget_id": widget_id,
                  "widget_opts": json.dumps(widget_opts, separators=JSONSEPARATORS),
                  }

        s3.jquery_ready.append(script)

        return widget

    # -------------------------------------------------------------------------
    def parse(self, value, record_id=None):
        """
            Value parser for the hidden input field of the widget

            Args:
                value: the value received from the client, JSON string
                record_id: the record ID (unused, for API compatibility)

            Returns:
                a list (if multiple=True) or the value
        """

        default = [] if self.multiple else None

        if value is None:
            return None, None
        try:
            value = json.loads(value)
        except ValueError:
            return default, None
        if not self.multiple and isinstance(value, list):
            value = value[0] if value else None

        return value, None

# =============================================================================
class S3SliderWidget(EdenFormWidget):
    """
        Standard Slider Widget

        The range of the Slider is derived from the Validator
    """

    def __init__(self, step=1, type="int"):

        self.step = step
        self.type = type

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):

        validator = field.requires
        field = str(field)
        fieldname = field.replace(".", "_")
        input_field = INPUT(_name = field.split(".")[1],
                            _disabled = True,
                            _id = fieldname,
                            _style = "border:0",
                            _value = value,
                            )
        slider = DIV(_id="%s_slider" % fieldname, **attributes)

        s3 = current.response.s3

        if isinstance(validator, IS_EMPTY_OR):
            validator = validator.other

        self.min = validator.minimum

        # Max Value depends upon validator type
        if isinstance(validator, IS_INT_IN_RANGE):
            self.max = validator.maximum - 1
        elif isinstance(validator, IS_FLOAT_IN_RANGE):
            self.max = validator.maximum

        if value is None:
            # JSONify
            value = "null"
            script = '''i18n.slider_help="%s"''' % \
                current.T("Click on the slider to choose a value")
            s3.js_global.append(script)

        if self.type == "int":
            script = '''S3.slider('%s',%i,%i,%i,%s)''' % (fieldname,
                                                          self.min,
                                                          self.max,
                                                          self.step,
                                                          value)
        else:
            # Float
            script = '''S3.slider('%s',%f,%f,%f,%s)''' % (fieldname,
                                                          self.min,
                                                          self.max,
                                                          self.step,
                                                          value)
        s3.jquery_ready.append(script)

        return TAG[""](input_field, slider)

# =============================================================================
class S3StringWidget(StringWidget):
    """
        Extend the default Web2Py widget to include a Placeholder
    """

    def __init__(self,
                 columns = 10,
                 placeholder = None,
                 prefix = None,
                 textarea = False,
                 ):
        """
            Args:
                columns: number of grid columns to span (Foundation-themes)
                placeholder: placeholder text for the input field
                prefix: text for prefix button (Foundation-themes)
                textarea: render as textarea rather than string input
        """

        self.columns = columns
        self.placeholder = placeholder
        self.prefix = prefix
        self.textarea = textarea

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):

        default = {"value": (value is not None and str(value)) or "",
                   }

        if self.textarea:
            attr = TextWidget._attributes(field, default, **attributes)
        else:
            attr = StringWidget._attributes(field, default, **attributes)

        placeholder = self.placeholder
        if placeholder:
            attr["_placeholder"] = placeholder

        if self.textarea:
            widget = TEXTAREA(**attr)
        else:
            widget = INPUT(**attr)

        # NB These classes target Foundation Themes
        prefix = self.prefix
        if prefix:
            widget = DIV(DIV(SPAN(prefix, _class="prefix"),
                             _class="small-1 columns",
                             ),
                         DIV(widget,
                             _class="small-11 columns",
                             ),
                         _class="row collapse",
                        )

        # Set explicit columns width for the formstyle
        columns = self.columns
        if columns:
            widget["s3cols"] = columns

        return widget

# =============================================================================
class S3TimeIntervalWidget(FormWidget):
    """
        Simple time interval widget for the scheduler task table
    """

    multipliers = (("weeks", 604800),
                   ("days", 86400),
                   ("hours", 3600),
                   ("minutes", 60),
                   ("seconds", 1))

    # -------------------------------------------------------------------------
    @classmethod
    def widget(cls, field, value, **attributes):
        """
            Widget builder

            Args:
                field: the Field
                value: the current value
                attributes: DOM attributes for the widget
        """

        if value is None:
            value = 0
        elif isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                value = 0

        # Value input
        multiplier = cls.get_multiplier(value)
        inp = IntegerWidget.widget(field, value // multiplier[1],
                                   requires = cls.validate(field),
                                   )

        # Multiplier selector
        multipliers = S3TimeIntervalWidget.multipliers
        options = []
        for i in range(1, len(multipliers) + 1):
            title, opt = multipliers[-i]
            if opt == multiplier[1]:
                option = OPTION(title, _value=opt, _selected="selected")
            else:
                option = OPTION(title, _value=opt)
            options.append(option)

        # Widget
        return DIV(inp,
                   SELECT(options,
                          _name = ("%s_multiplier" % field).replace(".", "_"),
                          ),
                   )

    # -------------------------------------------------------------------------
    @staticmethod
    def validate(field):
        """
            Return an internal validator (converter) for the numeric input

            Args:
                field: the Field

            Returns:
                a validator function
        """

        def requires(value, record_id=None):

            if value is None or value == "":
                return value, None

            try:
                val = int(value)
            except ValueError:
                return (value, current.T("Enter an integer"))

            post_vars = current.request.post_vars
            try:
                mul = int(post_vars[("%s_multiplier" % field).replace(".", "_")])
            except ValueError:
                return (value, current.T("Invalid time unit"))

            return val * mul, None

        return requires

    # -------------------------------------------------------------------------
    @classmethod
    def represent(cls, value):
        """
            Represent the field value in a convenient unit of time

            Args:
                value: the field value (seconds)

            Returns:
                string representation of the field value
        """

        try:
            val = int(value)
        except (ValueError, TypeError):
            val = 0

        multiplier = cls.get_multiplier(val)

        return "%s %s" % (val // multiplier[1],
                          current.T(multiplier[0]),
                          )

    # -------------------------------------------------------------------------
    @classmethod
    def get_multiplier(cls, value):
        """
            Get a convenient multiplier (=unit of time) for a value in seconds

            Args:
                value: the value in seconds

            Returns:
                a tuple (multiplier, multiplier-name)
        """

        multipliers = cls.multipliers

        multiplier = multipliers[-1] # Seconds
        if value >= 60:
            for m in multipliers:
                if value % m[1] == 0:
                    multiplier = m
                    break

        return multiplier

# =============================================================================
class S3UploadWidget(UploadWidget):
    """
        Subclass for use in inline-forms
        - always renders all widget elements (even when empty), so that
          they can be updated from JavaScript
        - adds CSS selectors for widget elements
    """

    # -------------------------------------------------------------------------
    @classmethod
    def widget(cls, field, value, download_url=None, **attributes):
        """
            Generates a INPUT file tag.

            Optionally provides an A link to the file, including a checkbox so
            the file can be deleted. All is wrapped in a DIV.

            Args:
                download_url: Optional URL to link to the file (default = None)
        """

        T = current.T

        # File input
        default = {"_type": "file",
                   }
        attr = cls._attributes(field, default, **attributes)

        # File URL
        base_url = "/default/download"
        if download_url and value:
            if callable(download_url):
                url = download_url(value)
            else:
                base_url = download_url
                url = download_url + "/" + value
        else:
            url = None

        # Download-link
        link = SPAN("[",
                    A(T(cls.GENERIC_DESCRIPTION),
                      _href = url,
                      ),
                    _class = "s3-upload-link",
                    _style = "white-space:nowrap",
                    )

        # Delete-checkbox
        requires = attr["requires"]
        if requires == [] or isinstance(requires, IS_EMPTY_OR):
            name = field.name + cls.ID_DELETE_SUFFIX
            delete_checkbox = TAG[""]("|",
                                      INPUT(_type = "checkbox",
                                            _name = name,
                                            _id = name,
                                            ),
                                      LABEL(T(cls.DELETE_FILE),
                                            _for = name,
                                            _style = "display:inline",
                                            ),
                                      )
            link.append(delete_checkbox)

        # Complete link-element
        link.append("]")
        if not url:
            link.add_class("hide")

        # Image preview
        preview_class = "s3-upload-preview"
        if value and cls.is_image(value):
            preview_url = url
        else:
            preview_url = None
            preview_class = "%s hide" % preview_class
        image = DIV(IMG(_alt = T("Loading"),
                        _src = preview_url,
                        _width = cls.DEFAULT_WIDTH,
                        ),
                    _class = preview_class,
                    )

        # Construct the widget
        inp = DIV(INPUT(**attr),
                  link,
                  image,
                  _class="s3-upload-widget",
                  data = {"base": base_url,
                          },
                  )

        return inp

# =============================================================================
class CheckboxesWidgetS3(OptionsWidget):
    """
        S3 version of gluon.sqlhtml.CheckboxesWidget:
        - configurable number of columns
        - supports also integer-type keys in option sets
        - has an identifiable class for styling

        Used in Sync, Projects, Facilities
    """

    # -------------------------------------------------------------------------
    @classmethod
    def widget(cls, field, value, **attributes):
        """
            Generates a TABLE tag, including INPUT checkboxes (multiple allowed)
        """

        #values = re.compile("[\w\-:]+").findall(str(value))
        values = [value] if not isinstance(value, (list, tuple)) else value
        values = [str(v) for v in values]

        attr = OptionsWidget._attributes(field, {}, **attributes)
        attr["_class"] = "checkboxes-widget-s3"

        requires = field.requires
        if not isinstance(requires, (list, tuple)):
            requires = [requires]

        if hasattr(requires[0], "options"):
            options = requires[0].options()
        else:
            raise SyntaxError("widget cannot determine options of %s" % field)

        options = [(k, v) for k, v in options if k != ""]

        options_help = attributes.get("options_help", {})
        input_index = attributes.get("start_at", 0)

        opts = []
        cols = attributes.get("cols", 1)

        totals = len(options)
        mods = totals % cols
        rows = totals // cols
        if mods:
            rows += 1

        if totals == 0:
            T = current.T
            opts.append(TR(TD(SPAN(T("no options available"),
                                   _class = "no-options-available",
                                   ),
                              INPUT(_name = field.name,
                                    _class = "hide",
                                    _value = None,
                                    )
                              )))

        for r_index in range(rows):
            tds = []

            for k, v in options[r_index * cols:(r_index + 1) * cols]:
                input_id = "id-%s-%s" % (field.name, input_index)
                option_help = options_help.get(str(k), "")
                if option_help:
                    label = LABEL(v, _for=input_id, _title=option_help)
                else:
                    # Don't provide empty client-side popups
                    label = LABEL(v, _for=input_id)

                tds.append(TD(INPUT(_type = "checkbox",
                                    _name = field.name,
                                    _id = input_id,
                                    # Hide checkboxes without a label
                                    _class = "" if v else "hide",
                                    requires = attr.get("requires", None),
                                    hideerror = True,
                                    _value = k,
                                    value = (str(k) in values)),
                              label,
                              ))

                input_index += 1
            opts.append(TR(tds))

        if opts:
            opts[-1][0][0]["hideerror"] = False
        return TABLE(*opts, **attr)

# =============================================================================
class S3PasswordWidget(FormWidget):
    """
        Widget for password fields, allows unmasking of passwords
    """

    @staticmethod
    def widget(field, value, **attributes):

        T = current.T

        tablename = field._tablename
        fieldname = field.name
        js_append = current.response.s3.js_global.append
        js_append('''i18n.password_view="%s"''' % T("View"))
        js_append('''i18n.password_mask="%s"''' % T("Mask"))

        password_input = INPUT(_name = fieldname,
                               _id = "%s_%s" % (tablename, fieldname),
                               _type = "password",
                               _value = value,
                               requires = field.requires,
                               )
        password_unmask = A(T("View"),
                            _class = "s3-unmask",
                            _onclick = '''S3.unmask('%s','%s')''' % (tablename,
                                                                     fieldname),
                            _id = "%s_%s_unmask" % (tablename, fieldname),
                            )
        return DIV(password_input,
                   password_unmask,
                   _class = "s3-password-widget",
                   )

# =============================================================================
class S3PhoneWidget(StringWidget):
    """
        Extend the default Web2Py widget to ensure that the + is at the
        beginning not the end in RTL.
        Adds class to be acted upon by S3.js
    """

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):

        default = {"value": (value is not None and str(value)) or "",
                   }

        attr = StringWidget._attributes(field, default, **attributes)
        attr["_class"] = "string phone-widget"

        widget = INPUT(**attr)

        return widget

# =============================================================================
def s3_comments_widget(field, value, **attr):
    """
        A smaller-than-normal textarea
        - used by the CommentsField & gis.desc_field templates
    """

    _id = attr.get("_id", "%s_%s" % (field._tablename, field.name))

    _name = attr.get("_name", field.name)

    return TEXTAREA(_name = _name,
                    _id = _id,
                    _class = "comments %s" % (field.type),
                    _placeholder = attr.get("_placeholder"),
                    value = value,
                    requires = field.requires)

# =============================================================================
def s3_richtext_widget(field, value):
    """
        A Rich Text field to be used by the CMS Post Body, etc
        - uses CKEditor
        - requires doc module loaded to be able to upload/browse Images
    """

    s3 = current.response.s3
    widget_id = "%s_%s" % (field._tablename, field.name)

    # Load the scripts
    sappend = s3.scripts.append
    ckeditor = URL(c="static", f="ckeditor",
                   args = "ckeditor.js")
    sappend(ckeditor)
    adapter = URL(c="static", f="ckeditor",
                  args = ["adapters",
                          "jquery.js"])
    sappend(adapter)

    table = current.s3db.table("doc_ckeditor")
    if table:
        # Doc module enabled: can upload/browse images
        url = '''filebrowserUploadUrl:'/%(appname)s/doc/ck_upload',filebrowserBrowseUrl:'/%(appname)s/doc/ck_browse',''' \
                % {"appname": current.request.application}
    else:
        # Doc module not enabled: cannot upload/browse images
        url = ""

    # Toolbar options: http://docs.ckeditor.com/#!/guide/dev_toolbar
    js = '''var ck_config={toolbar:[['Format','Bold','Italic','-','NumberedList','BulletedList','-','Link','Unlink','-','Image','Table','-','PasteFromWord','-','Source','Maximize']],toolbarCanCollapse:false,%sremovePlugins:'elementspath'}''' \
            % url
    s3.js_global.append(js)

    js = '''$('#%s').ckeditor(ck_config)''' % widget_id
    s3.jquery_ready.append(js)

    return TEXTAREA(_name = field.name,
                    _id = widget_id,
                    _class = "richtext %s" % (field.type),
                    value = value,
                    requires = field.requires,
                    )

# =============================================================================
class S3TagCheckboxWidget(EdenFormWidget):
    """
        Simple widget to use a checkbox to toggle a string-type Field
        between two values (default "Y"|"N").
        Designed for use with tag.value

        Notes:
            - it is usually better to use a boolean Field with a context-specific
              representation function than this.
            - make sure the field validator accepts the configured on/off values,
              e.g. IS_IN_SET(("Y", "N")) (also for consistency with imports)
            - when using this with a filtered key-value component (e.g.
              pr_person_tag), make the filtered component multiple=False and
              embed *.value as subtable-field (do not use InlineComponent)
    """

    def __init__(self, on="Y", off="N"):
        """
            Args:
                on: the value of the tag for checkbox=on
                off: the value of the tag for checkbox=off
        """

        self.on = on
        self.off = off

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget construction

            Args:
                field: the Field
                value: the current (or default) value
                attributes: overrides for default attributes
        """

        defaults = {"_type": "checkbox",
                    "value": str(value) == self.on,
                    "requires": self.requires,
                    }
        attr = self._attributes(field, defaults, **attributes)
        return INPUT(**attr)

    # -------------------------------------------------------------------------
    def requires(self, value):
        """
            Input-validator to convert the checkbox value into the
            corresponding tag value

            Args:
                value: the checkbox value ("on" if checked)
        """

        v = self.on if value == "on" else self.off
        return v, None

# END =========================================================================
