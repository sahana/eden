/**
 * JS to handle Date & Time form fields
 */

$(document).ready(function() {
    // Date fields - use jquery.ui.datepicker
    $('input.date').datepicker({
        changeMonth: true,
        changeYear: true,
        //showOtherMonths: true, selectOtherMonths: true,
        showOn: 'both',
        // We want to be able to select image in CSS
        //buttonImage: S3.Ap.concat('/static/img/jquery-ui/calendar.gif'),
        //buttonImageOnly: true,
        buttonText: '',
        dateFormat: 'yy-mm-dd',
        isRTL: S3.rtl
    });

    // Time fields - use jquery.ui.fgtimepicker
    // (could also be migrated to jquery.ui.timepicker.addon.js,
    //  just use .timepicker instead - but this one seems easier
    //  to use than a slider)
    $('input.time').fgtimepicker({
        hourText: i18n.hour,
        minuteText: i18n.minute,
        defaultTime: ''
    });
});

// Automation of end date if start date is present and automation is allowed
// Widget Used: S3DateWidget
// Will be activated only if end_date_selector and start_date_selector are both used
(function($) {

    "use strict";

    /**
     * Start Date - End Date Interval widget
     */
    $.widget('s3.end_date_interval', {

        /**
         * Default options
         *
         * @prop {bool} show_clear_button - Display the clear button next to the selector
         */
        options: {
            show_clear_button: true
        },
        /**
         * Create the widget
         */
        _create: function() {

            var options;
            options = this.options;

            this.namespace = ".enddateinterval"

            this.start_element = $(options.start_date_selector);

            this.default_interval = options.interval;
            this.start_date_prev = this.start_element.datepicker('getDate');

        },

        /**
         * Update the widget options
         *
         */
        _init: function() {

            var select_start_date,
                default_interval,
                select_end_date,
                start_element,
                start_month,
                start_year,
                start_date,
                interval,
                options,
                element,
                self;

            // Set local variables
            options = this.options;
            self = this;
            start_element = this.start_element;
            element = $(this.element);
            interval = this.interval;
            default_interval = this.default_interval;

            element.datepicker('option',{
                yearRange: 'c-100:c+100',
                showButtonPanel: true
            }).one('click', function() {
                $(this).trigger('focus')
            });

            // Insert a clear button next to the end_date which clears the field
            // Only insert if needed (options)
            if (options.show_clear_button) {
                var clear_button = $('<button id="end_date_clear" class="btn date-clear-btn" type="button">'+ i18n.btn_clear +'</button>').on('click', function() {
                    element.val('');
                });
                element.next().after(clear_button);
            }

            element.off(self.namespace).on('click' + self.namespace, function() {
                select_start_date = start_element.datepicker('getDate');
                if (select_start_date != null) {
                    self._inputclick();
                }
            });

            select_end_date = element.datepicker('getDate');

            if (select_end_date == null) {
                // Explicit Default if allowed
                if (options.default_explicit) {
                    self.interval = default_interval;
                    self._end_date_automate(self.interval);
                }
                start_element.change(function() {
                    interval = self.interval;

                    // Set end date only if its not set explicitly by the user.
                    select_end_date = element.datepicker('getDate');
                    if (select_end_date != null) {
                        var start_date_prev = self.start_date_prev;

                        // Confirm that the end date was set by the script before updating
                        start_month = start_date_prev.getMonth() + 1;
                        start_year = start_date_prev.getFullYear();
                        start_date = start_date_prev.getDate();
                        start_date_prev = new Date(start_year, start_month, start_date);
                        self._add_months(start_date_prev, interval - 1);
                        select_end_date = element.datepicker('getDate');
                        if (self._equal_date(select_end_date, start_date_prev)) {
                            self._end_date_automate(interval);
                        }
                    }
                });
            }

        },

        /**
         * Sets the end date based on the start date and months given
         *
         * @param {integer} month - months to be added to the start date
         */
        _end_date_automate: function(months) {

            var select_start_date,
                start_element,
                start_month,
                start_year,
                start_date,
                element,
                self;

            // Set Local Variables
            start_element = this.start_element;
            element = $(this.element);
            self = this;

            // Get the value of start date
            select_start_date = start_element.datepicker('getDate');

            // Add Months to the start date
            start_month = select_start_date.getMonth() + 1;
            start_year = select_start_date.getFullYear();
            start_date = select_start_date.getDate();
            select_start_date = new Date(start_year, start_month, start_date);
            self._add_months(select_start_date, months - 1);

            // Set the end date
            element.datepicker('setDate', select_start_date);

            self.start_date_prev = start_element.datepicker('getDate');
        },

        /**
         * Function to link the buttons on the widget
         *
         */
        _inputclick: function() {

            var select_end_date,
                default_interval,
                element,
                ns,
                self;

            // Set local variables
            ns = this.namespace;
            element = $(this.element);
            default_interval = this.default_interval;
            self = this;

            // Default to default interval if end field is selected while its empty (i.e explicit default)
            select_end_date = element.datepicker('getDate');
            if (select_end_date == null) {
                self.interval = default_interval;
                self._end_date_automate(default_interval);
            }

            var buttonPane = $('.ui-datepicker-buttonpane');
            $('.ui-datepicker-current').hide();
            $('.ui-datepicker-close').hide();

            var pane_heading = $('<h5>'+ i18n.interval +'</h5>');
            pane_heading.appendTo(buttonPane);

            // @ToDo: DRY (make an array instead of repeating the code and numbering the buttons)
            var btn_1 = $('<a class="ui-datepicker-current ui-state-default ui-priority-primary" type="button">'+ i18n.btn_1_label +'</a>');
            btn_1.off(ns).on('click' + ns, function() {
                self.interval = 6;
                self._end_date_automate(self.interval);
            });
            btn_1.appendTo(buttonPane);

            var btn_2 = $('<a class="ui-datepicker-current ui-state-default ui-priority-primary" type="button">'+ i18n.btn_2_label +'</a>');
            btn_2.off(ns).on('click' + ns, function() {
                self.interval = 12;
                self._end_date_automate(self.interval);
            });
            btn_2.appendTo(buttonPane);

            var btn_3 = $('<a class="ui-datepicker-current ui-state-default ui-priority-primary" type="button">'+ i18n.btn_3_label +'</a>');
            btn_3.off(ns).on('click' + ns, function() {
                self.interval = 24;
                self._end_date_automate(self.interval);
            });
            btn_3.appendTo(buttonPane);

            var btn_4 = $('<a class="ui-datepicker-current ui-state-default ui-priority-primary" type="button">'+ i18n.btn_4_label +'</a>');
            btn_4.off(ns).on('click' + ns, function() {
                self.interval = 60;
                self._end_date_automate(self.interval);
            });
            btn_4.appendTo(buttonPane);

            // Style the interval buttons
            // @ToDo: Move to CSS
            // @ToDo: Improve Styling (use Jquery UI style)
            $('.ui-datepicker-buttonpane a').css('margin', '.3em');
            $('.ui-datepicker-buttonpane a').css('font-size', '1rem');
            $('.ui-datepicker-buttonpane').css('text-align', 'center');
        },

        /**
         * Checks whether two dates are equal or not
         *
         * @param {date} mdate - 1st Date
         * @param {date} pdate - 2nd Date
         * @return {bool}
         */
        _equal_date: function(mDate,pDate) {
            return (
                mDate.getFullYear() === pDate.getFullYear() &&
                mDate.getMonth() === pDate.getMonth() &&
                mDate.getDate() === pDate.getDate()
            );
        },

        /**
         * Checks whether a given year is leap year or not
         *
         * @param {year} year - Year to be checked
         * @return {bool}
         */
        _is_leap_year: function (year) {
            return (((year % 4 === 0) && (year % 100 !== 0)) || (year % 400 === 0));
        },

        /**
         * Returna a array of days of every month of a given year
         *
         * @param {year} year
         * @param {month} month
         * @return {array} - Number of days of every month in a year
         */
        _get_days_in_month: function (year, month) {
            var element = $(this.element);
            var self = this;
            return [31, (self._is_leap_year(year) ? 29 : 28), 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month];
        },

        /**
         * Calls for an array of days of every month in the year of a date
         *
         * @param {date} mdate
         * @return {array} - Number of days of every month in a year
         */
        _get_days_in_month_big: function (mdate) {
            var element = $(this.element);
            var self = this;
            return self._get_days_in_month(mdate.getFullYear(), mdate.getMonth());
        },

        /**
         * Adds Months to a given Date
         *
         * @param {date} mdate - Date to which the month is added
         * @param {integer} value - No of months to be added
         * @return {date} - New Date with the added month (mdate + value)
         */
        _add_months: function (mdate,value) {
            var self = this;
            var element = $(this.element);
            var n = mdate.getDate();
            mdate.setDate(1);
            mdate.setMonth(mdate.getMonth() + value);
            mdate.setDate(Math.min(n, self._get_days_in_month_big(mdate)));
            return mdate;
        }
    });
})(jQuery);

// END ========================================================================
