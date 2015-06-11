/**
 * jQuery UI Widget for S3CalendarWidget
 *
 * @copyright 2015 (c) Sahana Software Foundation
 * @license MIT
 *
 * requires jQuery 1.9.1+
 * requires jQuery UI 1.10 widget factory
 *
 * work in progress...
 */
(function($, undefined) {

    "use strict";
    var calendarWidgetID = 0;

    /**
     * Hack for calendarsPicker: do not close upon select if we have a timepicker,
     * always also pick up the time before updating the real input during onSelect
     */
    $.calendarsPicker._base_selectDate = $.calendarsPicker.selectDate;
    $.calendarsPicker.selectDate = function(elem, target) {

        var inst = this._getInst(elem),
            timepicker = inst.timepicker,
            was_inline;

        if (timepicker) {
            // Pretend that this instance is inline to keep it open after selection
            was_inline = inst.inline;
            inst.inline = true;
            // FIXME: does not highlight the selected date! (base version does not either)
            this._base_selectDate(elem, target);
            inst.inline = was_inline;

            // Pick up the time
            inst.pickUpTime = true;
            $.datepicker._selectDate(timepicker);
            inst.pickUpTime = false;

            // _updateInput not called while inline, so do it now
            // (also triggers the onSelect-callback)
            this._updateInput(elem);
        } else {
            this._base_selectDate(elem, target);
        }
    };

    /**
     * calendarWidget
     */
    $.widget('s3.calendarWidget', {

        /**
         * Default options
         *
         * @prop {string} calendar - the calendar to use
         *
         * @prop {string} dateFormat - the date format (Python strftime)
         * @prop {string} timeFormat - the time format (Python strftime)
         * @prop {string} separator - the separator between date and time
         *
         * @prop {bool} monthSelector - show a drop-down to select the month
         * @prop {bool} yearSelector - show a drop-down to select the year
         * @prop {bool} showButtons - show the button panel
         *
         * @prop {bool} weekNumber - show the week number in the calendar
         * @prop {number} firstDOW - the first day of the week (0=Sunday, 1=Monday, ...)
         *
         * @prop {bool} timepicker - show a timepicker
         * @prop {number} minuteStep - the minute-step for the timepicker slider
         */
        options: {

            calendar: 'gregorian',

            dateFormat: '%Y-%m-%d',
            timeFormat: '%H:%M',
            separator: ' ',

            monthSelector: false,
            yearSelector: true,
            showButtons: true,

            weekNumber: false,
            firstDOW: 1,

            timepicker: false,
            minuteStep: 5
        },

        /**
         * Create the widget
         */
        _create: function() {

            // Instance ID and namespace
            this.id = calendarWidgetID;
            this.namespace = '.calendar-widget-' + calendarWidgetID;

            calendarWidgetID += 1;
        },

        /**
         * Update the widget options
         */
        _init: function() {

            var el = $(this.element);

            this.refresh();
        },

        /**
         * Remove generated elements & reset other changes
         */
        _destroy: function() {

            // Remove any existing hidden inputs
            this._removeHiddenInputs();

            // Call prototype method
            $.Widget.prototype.destroy.call(this);
        },

        /**
         * Redraw contents
         */
        refresh: function() {

            var el = $(this.element),
                opts = this.options;

            // Unbind all event handlers
            this._unbindEvents();

            // Remove any existing hidden inputs
            this._removeHiddenInputs();

            if (opts.calendar == 'gregorian') {
                this._datePicker();
            } else {
                this._calendarsPicker();
            }

            // Bind event handlers
            this._bindEvents();
        },

        /**
         * Attach a $.datepicker instance
         */
        _datePicker: function() {

            var el = $(this.element),
                opts = this.options,
                dateFormat = this._transformDateFormat();

            if (opts.timepicker) {
                // $.datetimepicker
                var timeFormat = this._transformTimeFormat()

                el.datetimepicker({
                    dateFormat: dateFormat,
                    timeFormat: timeFormat,
                    separator: opts.separator,
                    firstDay: opts.firstDOW,
                    showWeek: opts.weekNumber,

                    changeMonth: opts.monthSelector,
                    changeYear: opts.yearSelector,
                    stepMinute: opts.minuteStep,
                    showSecond: false
                });

            } else {
                // $.datepicker

                el.datepicker({
                    dateFormat: dateFormat,
                    firstDay: opts.firstDOW,
                    showWeek: opts.weekNumber,

                    changeMonth: opts.monthSelector,
                    changeYear: opts.yearSelector
                });
            }
            this._clickFocus(el);
        },

        /**
         * Attach a $.calendarsPicker instance
         */
        _calendarsPicker: function() {

            var el = $(this.element),
                opts = this.options,
                dateFormat = this._transformDateFormat('calendarsPicker');

            // Configure calendarsPicker
            // @todo: choose the right calendar
            // @todo: choose the right locale
            $.calendarsPicker.setDefaults($.calendarsPicker.regionalOptions['']);

            // Configure themeRoller
            var renderer;
            if (opts.weekNumber) {
                renderer = $.calendarsPicker.themeRollerWeekOfYearRenderer;
            } else {
                renderer = $.calendarsPicker.themeRollerRenderer;
            }
            $.calendarsPicker.setDefaults({renderer: renderer});

            if (opts.timepicker) {
                // $.calendarsPicker with injected $.timepicker and split inputs

                // Add hidden inputs
                var value = el.val(),
                    dt = this._split(value);
                this.dateInput = $('<input type="hidden">').insertAfter(el).val(dt.date);
                this.timeInput = $('<input type="hidden">').insertAfter(el).val(dt.time);

                // Instantiate calendarsPicker
                var self = this;
                this.dateInput.calendarsPicker({
                    dateFormat: dateFormat,
                    firstDay: opts.firstDOW,

                    changeMonth: opts.monthSelector || opts.yearSelector,

                    defaultDate: +0, // drawDate will automatically be min/max adjusted
                    showTrigger: '<div>',
                    onSelect: function(input) {
                        self._updateInput();
                    },
                    onShow: function(picker, calendar, inst) {
                        self._injectTimePicker(picker, calendar, inst);
                    },
                    onClose: function() {
                        var inst = this;
                        if (inst.name != 'calendarsPicker') {
                            inst = $.calendarsPicker._getInst(this);
                        }
                        if (inst.timepicker) {
                            inst.timepicker.remove();
                            inst.timepicker = null;
                        }
                    }
                });

            } else {
                // $.calendarsPicker

                el.calendarsPicker({
                    dateFormat: dateFormat,
                    firstDay: opts.firstDOW,

                    changeMonth: opts.monthSelector || opts.yearSelector
                });
            }
            this._clickFocus(el);
        },

        /**
         * @todo: docstring
         * @todo: move inline into calling function?
         */
        _injectTimePicker: function(picker, calendar, inst) {

            if (inst.timepicker) {
                return;
            }

            var self = this,
                opts = this.options,
                dateFormat = this._transformDateFormat('calendarsPicker'),
                timeFormat = this._transformTimeFormat();

            picker.find('.ui-datepicker-group').first().each(function() {
                var input = $('<div>').insertAfter($(this)),
                    lock = false;
                input.timepicker({
                    timeFormat: timeFormat,
                    stepMinute: opts.minuteStep,
                    showSecond: false,

                    showButtonPanel: false,
                    onSelect: function(input) {
                        self.timeInput.val(input);
                        // Pick up the date unless we're called from inside selectDate
                        if (!inst.pickUpTime) {
                            var dates = self.dateInput.calendarsPicker('getDate'),
                                datestr;
                            if (dates.length) {
                                datestr = dates[0].formatDate(dateFormat);
                            } else {
                                // Fall back to drawDate if no date has yet been selected
                                datestr = inst.drawDate.formatDate(dateFormat);
                            }
                            // Update the dateInput
                            self.dateInput.val(datestr);
                            // Update the real input
                            self._updateInput();
                        }
                    }
                });
                inst.timepicker = input;
                input.find('.ui-timepicker-div .ui-widget-header').remove();
            });
        },

        /**
         * Split a date/time string into its date and time parts
         *
         * @param {string} dtstr - the date/time string
         */
        _split: function (dtstr) {

            var opts = this.options,
                sep = opts.separator,
                timeFormat = opts.timeFormat,
                tlen = timeFormat.split(sep).length,
                parts = dtstr.split(sep),
                plen = parts.length;

            if (plen > 1) {
                return {
                    date: parts.splice(0, plen - tlen).join(sep),
                    time: parts.splice(0, tlen).join(sep)
                };
            }
            return {
                date: dtstr,
                time: ''
            };
        },

        /**
         * Join date and time strings into a combined date/time string
         */
        _join: function(datestr, timestr) {

            return [datestr, timestr].join(this.options.separator);
        },

        /**
         * Update the real input from the hidden date and time inputs
         *
         * @todo: always pick up both date and time even if one of them
         *        hasn't been selected yet
         */
        _updateInput: function() {

            var el = $(this.element),
                date = this.dateInput.val(),
                time = this.timeInput.val();

            el.val(this._join(date, time));
        },

        /**
         * Remove any existing hidden inputs
         */
        _removeHiddenInputs: function() {

            if (this.dateInput) {
                this.dateInput.remove();
                this.dateInput = null;
            }
            if (this.timeInput) {
                this.timeInput.remove();
                this.timeInput = null;
            }
        },

        /**
         * Transform the date format (Python strftime) into a datepicker
         * or calendarsPicker format string
         *
         * @param {string} variant - the picker variant
         */
        _transformDateFormat: function(variant) {

            var format = this.options.dateFormat;

            switch(variant) {
                case 'calendarsPicker':
                    format = format.replace("%Y", "yyyy")
                                   .replace("%y", "yy")
                                   .replace("%-m", "m")
                                   .replace("%m", "mm")
                                   .replace("%-d", "d")
                                   .replace("%d", "dd")
                                   .replace("%B", "MM")
                                   .replace("%b", "M");
                    break;
                default:
                    format = format.replace("%Y", "yy")
                                   .replace("%y", "y")
                                   .replace("%-m", "m")
                                   .replace("%m", "mm")
                                   .replace("%-d", "d")
                                   .replace("%d", "dd")
                                   .replace("%B", "MM")
                                   .replace("%b", "M");
                    break;
            }
            return format;
        },

        /**
         * Transform the time format (Python strftime) into a timepicker
         * format string
         */
        _transformTimeFormat: function() {

            var format = this.options.timeFormat;

            format = format.replace("%p", "TT")
                           .replace("%-I", "h")
                           .replace("%I", "hh")
                           .replace("%-H", "H")
                           .replace("%H", "HH")
                           .replace("%M", "mm")
                           .replace("%S", "ss");
            return format;
        },

        /**
         * Replace the focus event on the trigger by a click event
         * in case the trigger element already has the focus
         *
         * @param {jQuery|string} trigger - the trigger element
         */
        _clickFocus: function(trigger) {

            var node = $(trigger);
            if (node.is(":focus")) {
                node.one('click', function(){
                    $(this).focus();
                });
            }
            return node;
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var el = $(this.element),
                ns = this.namespace,
                self = this;

            // Trigger calendarsPicker.show when real input receives focus
            if (this.dateInput || this.timeInput) {
                el.bind('focus' + ns, function() {
                    self.dateInput.calendarsPicker('show');
                });
                // Change-event for date and time inputs
                this.dateInput.bind('change' + ns, function() {
                    self._updateInput();
                });
                this.timeInput.bind('change' + ns, function() {
                    self._updateInput();
                });
            }

            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var el = $(this.element),
                ns = this.namespace,
                self = this;

            el.unbind(ns);

            if (this.dateInput) {
                this.dateInput.unbind(ns);
            }
            if (this.timeInput) {
                this.timeInput.unbind(ns);
            }

            return true;
        }
    });
})(jQuery);
