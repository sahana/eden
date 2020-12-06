/**
 * jQuery UI Widget to enter weekly time rules using a 24/7 hours matrix
 *
 * @copyright 2020 (c) Sahana Software Foundation
 * @license MIT
 */
(function($, undefined) {

    "use strict";

    /**
     * Helper object to manage the weekly 24/7 hours matrix
     */
    function HoursMatrix(rules) {

        // Initialize the matrix
        this.initMatrix();

        // Apply any existing rules
        if (rules !== undefined) {
            this.applyRules(rules);
        }
    }

    /**
     * Initialize (reset) the 24/7 matrix
     */
    HoursMatrix.prototype.initMatrix = function() {

        // Initialize the matrix
        var matrix = [[], [], [], [], [], [], []];

        matrix.forEach(function(day) {
            for (var hour = 0; hour < 24; hour++) {
                day.push(false);
            }
        });

        this.matrix = matrix;
    };

    /**
     * Apply a set of time rules to update the 24/7 matrix
     *
     * @param {Array} rules - an array of rules of the format:
     *                        [{f:'WEEKLY', i:1, d:[days], s:[h,m,s], e:[h,m,s]}],
     *                        f = frequency, always 'WEEKLY'
     *                        i = interval, always 1
     *                        d = array of day numbers, 0=Sun, 1=Mon, etc.
     *                        s = start time
     *                        e = end time (exclusive)
     */
    HoursMatrix.prototype.applyRules = function(rules) {

        var matrix = this.matrix;

        rules.forEach(function(rule) {
            if (rule.f == 'WEEKLY' && rule.i == 1) {
                var end = rule.e[0];
                if (end === 0) {
                    end = 24;
                }
                rule.d.forEach(function(day) {
                    for (var hour = rule.s[0]; hour < end; hour++) {
                        matrix[day][hour] = true;
                    }
                });
            }
        });
    };

    /**
     * Convert the 24/7 matrix into a set of time rules
     *
     * @returns {Array} - an array of rules, format see applyRules
     */
    HoursMatrix.prototype.getRules = function() {

        var matrix = this.matrix,
            slots = {},
            self = this;

        matrix.forEach(function(hours, day) {

            var intervals = self.getIntervals(hours);

            intervals.forEach(function(interval) {
                var key = interval[0] + ':' + interval[1];
                if (slots.hasOwnProperty(key)) {
                    slots[key].push(day);
                } else {
                    slots[key] = [day];
                }
            });
        });

        var rules = [];

        for (var key in slots) {
            var days = slots[key],
                hours = key.split(':');

            var rule = {
                f: 'WEEKLY',
                i: 1,
                d: days,
                s: [parseInt(hours[0]), 0, 0],
                e: [parseInt(hours[1]), 0, 0]
            };
            rules.push(rule);
        }

        return rules;
    };

    /**
     * Mark an hour as selected/deselected
     *
     * @param {integer} day - the day number (0=Sunday, 1=Monday, etc.)
     * @param {integer} hour - the hour (0..23)
     * @param {boolean} selected - the new status (true=selected)
     */
    HoursMatrix.prototype.setSelected = function(day, hour, selected) {

        this.matrix[day][hour] = !!selected;
    };

    /**
     * Check whether an hour is currently selected
     *
     * @param {integer} day - the day number (0=Sunday, 1=Monday, etc.)
     * @param {integer} hour - the hour (0..23)
     *
     * @returns {boolean} - the current status of this hour (true=selected)
     */
    HoursMatrix.prototype.isSelected = function(day, hour) {

        return !!this.matrix[day][hour];
    };

    /**
     * Identify intervals of consecutive hours within a day, used
     * internally to generate time rules from the matrix
     *
     * @param {Array} hours - the hours array of the day
     *
     * @returns {Array} - an array of intervals [start, end], where
     *                    start is the first hour of the selected
     *                    interval, and end the first hour after the
     *                    selected interval (=exclusive)
     */
    HoursMatrix.prototype.getIntervals = function(hours) {

        var intervals = [],
            start = null,
            end = null;

        hours.forEach(function(selected, index) {
            if (selected) {
                if (start === null) {
                    start = end = index;
                } else {
                    end = index;
                }
                if (index == 23) {
                    intervals.push([start, 0]);
                    start = end = null;
                }
            } else {
                if (start !== null) {
                    end += 1;
                    if (end == 24) {
                        end = 0;
                    }
                    intervals.push([start, end]);
                    start = end = null;
                }
            }
        });

        return intervals;
    };

    var weeklyHoursID = 0;

    /**
     * weeklyHours UI widget
     */
    $.widget('s3.weeklyHours', {

        /**
         * Default options
         *
         * @todo document options
         */
        options: {

            weekdays: {
                0: 'Sunday',
                1: 'Monday',
                2: 'Tuesday',
                3: 'Wednesday',
                4: 'Thursday',
                5: 'Friday',
                6: 'Saturday'
            },
            firstDoW: 1,
        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = weeklyHoursID;
            weeklyHoursID += 1;

            this.eventNamespace = '.weeklyHours';
        },

        /**
         * Update the widget options
         */
        _init: function() {

            this.refresh();
        },

        /**
         * Remove generated elements & reset other changes
         */
        _destroy: function() {

            // Drop all event handlers
            this._unbindEvents();

            // Remove the raster
            var $raster = $(this.raster);
            if ($raster) {
                $raster.remove();
            }

            // Show the real input
            $(this.element).show();

            $.Widget.prototype.destroy.call(this);
        },

        /**
         * Redraw contents
         */
        refresh: function() {

            var $el = this.element;

            this._unbindEvents();

            // Parse rules from real input and set initial selection
            this._deserialize(false);

            // Render input raster and hide real input
            var raster = this._renderRaster();
            $el.hide().after(raster);

            this._bindEvents();
        },

        /**
         * Update hidden input from weekly hours matrix
         */
        _serialize: function() {

            var $el = $(this.element),
                rules = this.hoursMatrix.getRules();

            if (rules.length) {
                $el.val(JSON.stringify(rules));
            } else {
                $el.val('');
            }
        },

        /**
         * Update weekly hours matrix from hidden input
         *
         * @param {boolean} updateRaster - also update the widget
         */
        _deserialize: function(updateRaster) {

            // Parse real input JSON
            var $el = $(this.element),
                value = $el.val(),
                rules = [];

            if (value) {
                try {
                    rules = JSON.parse(value);
                } catch(e) {
                    // ignore
                }
            }

            // Reset (reinstantiate) the weekly hours matrix
            this.hoursMatrix = new HoursMatrix(rules);

            // Update the widget, if requested
            if (updateRaster) {
                this._updateRaster();
            }
        },

        /**
         * TODO docstring
         */
        _updateRaster: function() {

            var hoursMatrix = this.hoursMatrix,
                self = this;

            $('td.wa-hour', this.raster).each(function() {
                var $this = $(this),
                    day = $this.data('day'),
                    hour = $this.data('hour');

                self._selectHour($this, hoursMatrix.isSelected(day, hour));
            });
        },

        /**
         * Render the widget
         */
        _renderRaster: function() {

            var opts = this.options,
                weekdays = opts.weekdays,
                firstDoW = opts.firstDoW;

            var raster = $('<table>').addClass('wa-raster')
                                     .append(this._renderHeader());

            for (var i = firstDoW; i < firstDoW + 7; i++) {

                var dow = i % 7;
                if (weekdays.hasOwnProperty(dow)) {
                    raster.append(this._renderRow(dow));
                }
            }

            this.raster = raster;
            return raster;
        },

        /**
         * Render the table header with hours-columns
         */
        _renderHeader: function() {

            var headerRow = $('<tr>').append($('<td>'));

            // TODO make first/last hour configurable
            for (var i=0; i < 24; i++) {
                var hour = i.toString();
                if (i < 10) {
                    hour = '0' + hour;
                }
                var cell = $('<td>').addClass('wa-hour-header').text(hour);
                if (i > 0 && i % 6 === 0) {
                    cell.addClass('wa-tick');
                }
                headerRow.append(cell);
            }

            return $('<thead>').append(headerRow);
        },

        /**
         * Render a table row with hour selectors
         */
        _renderRow: function(day) {

            var weekdays = this.options.weekdays,
                dayCol = $('<td>').addClass('wa-day').text(weekdays[day]),
                row = $('<tr>').append(dayCol);

            // TODO make first/last hour configurable
            for (var hour = 0; hour < 24; hour++) {
                row.append(this._renderHour(day, hour));
            }
            return row;
        },

        /**
         * Render a hour selector (=table cell)
         */
        _renderHour: function(day, hour) {

            var status = this.hoursMatrix.isSelected(day, hour),
                icon = $('<i>'),
                cell = $('<td>').data({day: day, hour: hour, selected: status})
                                .addClass('wa-hour')
                                .append(icon);

            // TODO make icon classes configurable
            if (status) {
                cell.addClass('wa-on');
                icon.addClass('fa fa-check-square-o');
            } else {
                cell.addClass('wa-off');
                icon.addClass('fa fa-square-o');
            }

            if (hour > 0 && hour % 6 === 0) {
                cell.addClass('wa-tick');
            }
            return cell;
        },

        /**
         * TODO docstring
         */
        _selectHour: function(col, newStatus) {

            var $col = $(col),
                status = $col.data('selected');

            if (status === newStatus) {
                return;
            }

            $col.data('selected', newStatus);
            this.hoursMatrix.setSelected($col.data('day'), $col.data('hour'), newStatus);

            // TODO make icon classes configurable
            if (newStatus) {
                $col.removeClass('wa-off').addClass('wa-on');
                $('i.fa', $col).removeClass('fa-square-o')
                               .addClass('fa-check-square-o');
            } else {
                $col.removeClass('wa-on').addClass('wa-off');
                $('i.fa', $col).removeClass('fa-check-square-o')
                               .addClass('fa-square-o');
            }
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var $raster = $(this.raster),
                ns = this.eventNamespace,
                self = this;

            $(document).on('mouseup' + ns + ' touchend' + ns, function() {
                $raster.off('mouseenter' + ns);
                self._serialize();
            });

            $raster.on('mousedown' + ns + ' touchstart' + ns, '.wa-hour', function(e) {

                e.preventDefault();

                var col = $(this).focus(),
                    newStatus = col.hasClass('wa-off'),
                    selector = '.wa-off';

                if (!newStatus) {
                    selector = '.wa-on';
                }

                self._selectHour(col, newStatus);
                $raster.off('mouseenter' + ns)
                     .on('mouseenter' + ns, '.wa-hour' + selector, function() {
                    self._selectHour($(this), newStatus);
                });
            });

            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var $raster = $(this.raster),
                ns = this.eventNamespace;

            $(document).off(ns);
            $raster.off(ns);

            return true;
        }
    });
})(jQuery);
