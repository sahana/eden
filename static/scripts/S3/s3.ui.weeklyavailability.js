/**
 * jQuery UI Widget for Weekly Availability
 *
 * @copyright 2020 (c) Sahana Software Foundation
 * @license MIT
 */
(function($, undefined) {

    "use strict";

    function WeeklyHours(rules) {

        this.initMatrix();

        if (rules !== undefined) {
            this.applyRules(rules);
        }
    }

    WeeklyHours.prototype.initMatrix = function() {

        var matrix = [[], [], [], [], [], [], []];

        matrix.forEach(function(day) {
            for (var hour = 0; hour < 24; hour++) {
                day.push(false);
            }
        });

        this.matrix = matrix;
    };

    WeeklyHours.prototype.applyRules = function(rules) {

        var matrix = this.matrix;

        rules.forEach(function(rule) {
            if (rule.f == 'WEEKLY' && rule.i == 1) {
                var end = rule.e[0];
                if (end === 0) {
                    end = 24;
                }
                for (var hour = rule.s[0]; hour < end; hour++) {
                    rule.d.forEach(function(day) {
                        matrix[day][hour] = true;
                    });
                }
            }
        });
    };

    WeeklyHours.prototype.setSelected = function(day, hour, selected) {

        this.matrix[day][hour] = !!selected;
    };

    WeeklyHours.prototype.isSelected = function(day, hour) {

        return !!this.matrix[day][hour];
    };

    WeeklyHours.prototype.getRules = function() {

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

    WeeklyHours.prototype.getIntervals = function(hours) {

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

    var weeklyAvailabilityID = 0;

    /**
     * weeklyAvailability
     */
    $.widget('s3.weeklyAvailability', {

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
            firstDoW: 1

        },

        /**
         * Create the widget
         */
        _create: function() {

//             var el = $(this.element);

            this.id = weeklyAvailabilityID;
            weeklyAvailabilityID += 1;

            this.eventNamespace = '.weeklyAvailability';
        },

        /**
         * Update the widget options
         */
        _init: function() {

//             var el = $(this.element);

            this.refresh();
        },

        /**
         * Remove generated elements & reset other changes
         */
        _destroy: function() {

            this._unbindEvents();

            var $matrix = $(this.matrix);
            if ($matrix) {
                $matrix.remove();
            }
            $(this.element).show();

            $.Widget.prototype.destroy.call(this);
        },

        /**
         * Redraw contents
         */
        refresh: function() {

            var $el = this.element;

            this._unbindEvents();

            // Set initial selection
            this._deserialize(false);

            // Render matrix and hide real input
            var matrix = this._renderMatrix();
            $el.hide().after(matrix);

            this._bindEvents();
        },

        /**
         * Update hidden input from weekly hours matrix
         */
        _serialize: function() {
            // Format: [{f:'WEEKLY', i:1, d:[days], s:[h,m,s], e:[h,m,s]}]

            var $el = $(this.element),
                rules = this.weeklyHours.getRules();

            if (rules.length) {
                $el.val(JSON.stringify(rules));
            } else {
                $el.val('');
            }
        },

        /**
         * Update weekly hours matrix from hidden input
         */
        _deserialize: function(updateWidget) {

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

            this.weeklyHours = new WeeklyHours(rules);

            // Update matrix
            if (updateWidget) {
                this._updateWidget();
            }
        },

        _updateMatrix: function() {

            var weeklyHours = this.weeklyHours,
                self = this;

            $('td.wa-hour', this.matrix).each(function() {
                var $this = $(this),
                    day = $this.data('day'),
                    hour = $this.data('hour');

                self._selectHour($this, weeklyHours.isSelected(day, hour));
            });
        },

        /**
         * Render the widget
         */
        _renderMatrix: function() {

            var opts = this.options,
                weekdays = opts.weekdays,
                firstDoW = opts.firstDoW;

            var matrix = $('<table>').addClass('wa-matrix')
                                     .append(this._renderHeader());

            for (var i = firstDoW; i < firstDoW + 7; i++) {

                var dow = i % 7;
                if (weekdays.hasOwnProperty(dow)) {
                    matrix.append(this._renderRow(dow));
                }
            }

            this.matrix = matrix;
            return matrix;
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
                headerRow.append($('<td>').addClass('wa-hour-header').text(hour));
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

            var status = this.weeklyHours.isSelected(day, hour),
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

            return cell;
        },

        _selectHour: function(col, newStatus) {

            var $col = $(col),
                status = $col.data('selected');

            if (status === newStatus) {
                return;
            }

            $col.data('selected', newStatus);
            this.weeklyHours.setSelected($col.data('day'), $col.data('hour'), newStatus);

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

            var $matrix = $(this.matrix),
                ns = this.eventNamespace,
                self = this;

            $(document).on('mouseup' + ns + ' touchend' + ns, function() {
                $matrix.off('mouseenter' + ns);
                self._serialize();
            });

            $matrix.on('mousedown' + ns + ' touchstart' + ns, '.wa-hour', function(e) {

                e.preventDefault();

                var col = $(this).focus(),
                    newStatus = col.hasClass('wa-off'),
                    selector = '.wa-off';

                if (!newStatus) {
                    selector = '.wa-on';
                }

                self._selectHour(col, newStatus);
                $matrix
                    .off('mouseenter' + ns)
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

            var $matrix = $(this.matrix),
                ns = this.eventNamespace;

            $(document).off(ns);
            $matrix.off(ns);

            return true;
        }
    });
})(jQuery);
