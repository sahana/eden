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
     * calendarWidget
     */
    $.widget('s3.calendarWidget', {

        /**
         * Default options
         *
         * @todo document options
         */
        options: {

            calendar: 'gregorian',
            timepicker: false,

            dateFormat: 'yy-mm-dd',
            timeFormat: 'HH:mm',
            separator: ' ',

            weekNumber: false,
            showButtonPanel: true,
            monthSelector: false,
            yearSelector: true,
            firstDOW: 1
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

            // Remove the hidden inputs
            this.dateInput.remove();
            this.timeInput.remove();

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
            if (this.dateInput) {
                this.dateInput.remove();
                this.dateInput = null;
            }
            if (this.timeInput) {
                this.timeInput.remove();
                this.timeInput = null;
            }

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
                    // @todo: complete options
                    changeMonth: opts.monthSelector,
                    changeYear: opts.yearSelector,
                    dateFormat: dateFormat,
                    timeFormat: timeFormat,
                    separator: opts.separator
                });

            } else {
                // $.datepicker

                el.datepicker({
                    // @todo: complete options
                    changeMonth: opts.monthSelector,
                    changeYear: opts.yearSelector,
                    dateFormat: dateFormat
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
            $.calendarsPicker.setDefaults({renderer: $.calendarsPicker.themeRollerRenderer});

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
                    // @todo: complete options
                    changeMonth: opts.monthSelector || opts.yearSelector,
                    dateFormat: dateFormat,

                    showTrigger: '<div>',
                    onSelect: function(input) {
                        self._updateInput();
                    },
                    onShow: function(picker, calendar, inst) {
                        self._injectTimePicker(picker, calendar, inst);
                    }
                });

            } else {
                // $.calendarsPicker

                el.calendarsPicker({
                    // @todo: complete options
                    changeMonth: opts.monthSelector || opts.yearSelector,
                    dateFormat: dateFormat
                });
            }
            this._clickFocus(el);
        },

        /**
         * @todo: docstring
         * @todo: move inline into calling function?
         */
        _injectTimePicker: function(picker, calendar, inst) {

            var self = this,
                timeFormat = this._transformTimeFormat();

            picker.find('.ui-datepicker-group').each(function() {
                var input = $('<div>').insertAfter($(this));
                input.timepicker({
                    timeFormat: timeFormat,
                    showButtonPanel: false,
                    onSelect: function(input) {
                        self.timeInput.val(input);
                        self._updateInput();
                    }
                });
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
         */
        _updateInput: function() {

            var el = $(this.element),
                date = this.dateInput.val(),
                time = this.timeInput.val();

            el.val(this._join(date, time));
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
