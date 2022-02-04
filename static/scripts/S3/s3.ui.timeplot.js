/**
 * jQuery UI timeplot Widget for S3TimePlot
 *
 * @copyright 2013-2021 (c) Sahana Software Foundation
 * @license MIT
 *
 * requires jQuery 1.9.1+
 * requires jQuery UI 1.10 widget factory
 * requires D3.js 3.4.9+
 * requires NVD3.js
 *
 */

(function($, undefined) {

    "use strict";

    /**
     * Helper function to convert multi-fact time series into chart data series
     *
     * @param Array facts: the facts
     * @param Array data: the time series
     */
    var multiSeries = function(facts, data) {

        // Prepare the data items
        var items = [],
            keys = {},
            key,
            index = 0,
            area = facts.length == 1,
            i,
            j;
        for (i=0; i < facts.length; i++) {
            key = facts[i][0];
            if (keys.hasOwnProperty(key)) {
                index = keys[key] + 1;
            }
            keys[key] = index;
            if (index) {
                key += ' [' + (index + 1) +']';
            }
            var series = {key: key, label: facts[i][0], area: area},
                period,
                values = [];
            for (j=0; j < data.length; j++) {
                period = data[j];
                values.push({
                    start: new Date(period.t[0]).getTime(),
                    value: period.v[i]
                });
            }
            series.values = values;
            items.push(series);
        }

        return items;
    };

    var timeplotID = 0;

    /**
     * Timeplot Report
     */
    $.widget('s3.timeplot', {

        /**
         * Default options
         *
         * @prop {string} ajaxURL - the URL to Ajax-load data from
         * @prop {number|bool} autoSubmit - auto-submit timeout, false to
         *                                  deactivate auto-submit
         * @prop {bool} burnDown - render as burnDown from baseline
         *                         rather than as burnUp from zero
         * @prop {string} emptyMessage - message to show when no data are
         *                               available for the time interval
         *
         * @prop {string} thousandSeparator: the thousands-separator
         * @prop {string} thousandGrouping: number of digits per thousands-group
         * @prop {integer} precision: number of decimal places for numbers,
         *                            null for any, 0 for none
         *
         * @prop {string} defaultChartType - the default chart type,
         *                                   'linechart'|'barchart'
         * @prop {string} defaultChartAxis - the default Y-axis aspect
         */
        options: {
            ajaxURL: null,
            autoSubmit: 1000,
            burnDown: false,
            emptyMessage: 'No data available',

            thousandSeparator: ' ',
            thousandGrouping: '3',
            precision: null,

            defaultChartType: 'barchart',
            defaultChartAxis: 'totals'
        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = timeplotID;
            timeplotID += 1;
        },

        /**
         * Update widget options
         */
        _init: function() {

            var $el = $(this.element),
                opts = this.options;

            // Initialize instance data
            this.widget_id = $el.attr('id');
            this.input = $el.find('input[type="hidden"][name="tp-data"]').first();
            this.data = null;
            this.svg = null;

            // Chart
            var chart = $el.find('.tp-chart');
            if (chart.length) {
                this.chart = chart.first();
            } else {
                this.chart = null;
            }

            this.currentChart = {
                type: null,
                chart: null,
                container: null
            };

            // Define number formatter
            opts.numberFormatter = function(number) {

                var decimals = opts.precision;
                if (number === null || typeof number == 'undefined') {
                    return '-';
                }
                var n = decimals || decimals == 0 ? number.toFixed(decimals) : number.toString();

                n = n.split('.');
                var n1 = n[0],
                    n2 = n.length > 1 ? '.' + n[1] : '';
                var re = new RegExp('\\B(?=(\\d{' + opts.thousandGrouping + '})+(?!\\d))', 'g');
                n1 = n1.replace(re, opts.thousandSeparator);
                return n1 + n2;
            };

            // Refresh
            this.refresh();
        },

        /**
         * Remove generated elements & reset other changes
         */
        _destroy: function() {

            var el = this.element;

            // Unbind events
            this._unbindEvents();

            // Remove the chart
            if (this.svg) {
                this.svg.remove();
                this.svg = null;
                el.find('.tp-chart').empty();
            }

            // Forget the data
            this.data = null;

            $.Widget.prototype.destroy.call(this);
        },

        /**
         * Re-draw contents
         */
        refresh: function() {

            var el = this.element;

            this._unbindEvents();

            this._renderChart();
            this._renderChartOptions();

            // Hide submit-button if autoSubmit
            if (this.options.autoSubmit) {
                el.find('.tp-submit').hide();
            } else {
                el.find('.tp-submit').show();
            }
            this._bindEvents();

            el.find('.tp-throbber').hide();
        },

        /**
         * Render the chart options (according to current options)
         *
         * @todo: better chart picker widget
         */
        _renderChartOptions: function() {

            var $el = $(this.element);
            var container = $el.find('.tp-chart-controls').first().empty();

            if (this.data.e) {
                return;
            }

            var widgetID = $el.attr('id'),
                chartOpts = $('<div class="pt-chart-opts">');

            var bchartTotals = widgetID + '-bchart-totals',
                lchartTotals = widgetID + '-lchart-totals';

            $(chartOpts).append($(
                '<span id="' + lchartTotals + '" class="tp-chart-icon tp-lchart"></span>' +
                '<span class="tp-chart-label">Line Chart</span>'
            ));

            $(chartOpts).append($(
                '<span id="' + bchartTotals + '" class="tp-chart-icon tp-bchart"></span>' +
                '<span class="tp-chart-label">Bar Chart</span>'
            ));

            // Show the chart options
            $(container).append(chartOpts);
        },

        /**
         * Render the chart
         *
         * @param {object} [chartOptions] - the chart options
         * @prop {string} chartOptions.type - the chart type ('linechart'|'barchart')
         * @prop {string} chartOptions.axis - the chart axis
         */
        _renderChart: function(chartOptions) {

            // Get the chart container
            var chart = this.chart;
            if (!chart) {
                return;
            }

            // Determine chart type and axis
            var opts = this.options,
                currentChart = this.currentChart,
                chartType = null,
                chartAxis = null;
            if (chartOptions) {
                // Follow the specified options
                chartType = chartOptions.type;
                chartAxis = chartOptions.axis;
            } else {
                // Use previous options, if any
                if (currentChart) {
                    chartType = currentChart.type;
                    chartAxis = currentChart.axis;
                }
                // Fallback to defaults
                if (!chartType || !chartAxis) {
                    chartType = opts.defaultChartType;
                    chartAxis = opts.defaultChartAxis;
                }
            }

            // Remove current chart if type or axis changed
            if (currentChart.type != chartType ||
                currentChart.axis != chartAxis) {
                this._removeChart();
            }

            // Empty section
            var el = this.element;
            var emptySection = el.find('.tp-empty');

            // Lazy parse the JSON data
            var data = this.data;
            if (data === null) {
                data = JSON.parse(this.input.val());
            }
            if (!data) {
                data = {e: true};
            }
            this.data = data;

            if (!data.e) {
                // Hide empty section and render/update the chart
                emptySection.hide();
                chart.show();
                switch(chartAxis) {
                    case "totals":
                        switch(chartType) {
                            case "barchart":
                                this._renderMultiBarChart(chart, data.f, data.p);
                                break;
                            default:
                                this._renderLineChart(chart, data.f, data.p);
                                break;
                        }
                        break;
                    default:
                        break;
                }
            } else {
                // Remove the chart and show the empty section
                this._removeChart();
                el.find('.tp-empty').show();
            }
        },

        /**
         * Remove the current chart and turn off events
         */
        _removeChart: function() {

            var chart = this.chart;
            if (!chart) {
                return;
            }
            chart.empty().hide();

            var currentChart = this.currentChart;
            currentChart.container = null;
            currentChart.chart = null;
            currentChart.type = null;
            currentChart.axis = null;

            $(window).off('resize.tp');
        },

        /**
         * Multi Bar Chart
         *
         * @param {jQuery} chart - the chart container
         * @param {Array} facts - array of facts to render (tuples, see
         *                        S3TimeSeries.as_dict() for details)
         * @param {Array} data - the aggregated period data
         */
        _renderMultiBarChart: function(chart, facts, data) {

            var items = multiSeries(facts, data),
                currentChart = this.currentChart,
                barChart,
                barChartContainer;

            if (currentChart.chart) {
                barChartContainer = currentChart.container;
                barChart = currentChart.chart;

                // Update the data
                barChartContainer.datum(items)
                                 .transition()
                                 .duration(50)
                                 .call(barChart);
            } else {
                // Set the height of the chart container
                $(chart).closest('.tp-chart-contents').show();
                $(chart).css({height: '360px'});

                // Create SVG
                barChartContainer = d3.select($(chart).get(0))
                                      .append('svg')
                                      .attr('class', 'nv');

                // @todo: show tooltips instead of values (needs contentGenerator)
                barChart = nv.models.multiBarChart()
                                    .x(function(d) { return d.start; })
                                    .y(function(d) { return d.value; })
                                    .staggerLabels(true)
                                    .showControls(facts.length > 1)
                                    .forceY([0, 1]);

                barChart.tooltip.enabled(false);
                //barChart.tooltip.contentGenerator(barChartTooltip);
                var valueFormat = this.options.numberFormatter;

                // Set value and tick formatters
                barChart.yAxis
                        .tickFormat(valueFormat);
                barChart.xAxis
                        .tickFormat(function(d) {
                            return new Date(d).toLocaleDateString();
                        });

                nv.addGraph(function() {
                    // Render the chart
                    barChartContainer.datum(items)
                                     .transition()
                                     .duration(50)
                                     .call(barChart);

                    // Re-draw when window gets resized (using jQuery's method
                    // here since NVD3 does not allow selective removal of handler)
                    $(window).off('resize.tp').on('resize.tp', function(e) {
                        barChart.update(e);
                    });

                    return barChart;
                });
                currentChart.container = barChartContainer;
                currentChart.chart = barChart;
                currentChart.type = "barchart";
                currentChart.axis = "totals";
            }
        },

        /**
         * Simple Line Chart
         *
         * @param {jQuery} chart - the chart container
         * @param {Array} facts - array of facts to render (tuples, see
         *                        TimeSeries.as_dict() for details), will
         *                        render multiple series
         * @param {Array} data - the aggregated period data
         */
        _renderLineChart: function(chart, facts, data) {

            var items = multiSeries(facts, data),
                currentChart = this.currentChart,
                lineChart,
                lineChartContainer;

            if (currentChart.chart) {

                lineChartContainer = currentChart.container;
                lineChart = currentChart.chart;

                // Update the data
                lineChartContainer.datum(items)
                                  .transition()
                                  .duration(50)
                                  .call(lineChart);
            } else {

                // Set the height of the chart container
                $(chart).closest('.tp-chart-contents').show();
                $(chart).css({height: '360px'});

                // Create SVG
                lineChartContainer = d3.select($(chart).get(0))
                                       .append('svg')
                                       .attr('class', 'nv');

                // @todo: make legend use label
                // @todo: tooltip.contentGenerator to use fact label
                lineChart = nv.models.lineChart()
                                     .x(function(d) { return d.start; })
                                     .y(function(d) { return d.value; })
                                     .margin({right: 50})
                                     .duration(50)
                                     .showLegend(true)
                                     .useInteractiveGuideline(true)
                                     .forceY([0, 1]);

                var valueFormat = this.options.numberFormatter;

                // Set value and tick formatters
                lineChart.yAxis.tickFormat(valueFormat);
                lineChart.xAxis.tickFormat(function(d) {
                    return new Date(d).toLocaleDateString();
                });

                nv.addGraph(function() {

                    // Render the chart
                    lineChartContainer.datum(items)
                                      .transition()
                                      .duration(50)
                                      .call(lineChart);

                    // Re-draw when window gets resized (using jQuery's method
                    // here since NVD3 does not allow selective removal of handler)
                    $(window).off('resize.tp').on('resize.tp', function(e) {
                        lineChart.update(e);
                    });

                    return lineChart;
                });
                currentChart.container = lineChartContainer;
                currentChart.chart = lineChart;
                currentChart.type = "linechart";
                currentChart.axis = "totals";
            }
        },

        /**
         * Ajax-reload the data and refresh all widget elements
         *
         * @param {object} options - the report options as object
         * @param {object} filters - the filter options as object
         * @param {bool} force - reload regardless whether options or
         *                       filters have changed (e.g. after db
         *                       update in popup), default = true
         */
        reload: function(options, filters, force) {

            force = typeof force != 'undefined' ? force : true;

            if (typeof filters == 'undefined') {
                // Reload not triggered by the filter form
                // itself => get the current filters
                filters = this._getFilters();
            }

            var self = this,
                needs_reload = false;

            $(this.element).find('.tp-throbber').show();

            if (options || filters) {
                needs_reload = this._updateAjaxURL(options, filters);
            }

            if (needs_reload || force) {

                // Reload data and refresh

                // Ajax URL and method
                var ajaxURL = this.options.ajaxURL,
                    ajaxMethod = $.ajaxS3;

                // Use $.searchS3 if available
                if ($.searchS3 !== undefined) {
                    ajaxMethod = $.searchS3;
                }

                ajaxMethod({
                    'url': ajaxURL,
                    'type': 'GET',
                    'dataType': 'json',
                    'success': function(data) {
                        self.input.val(JSON.stringify(data));
                        self.data = data;
                        self.refresh();
                    },
                    'error': function(jqXHR, textStatus, errorThrown) {
                        var msg;
                        if (errorThrown == 'UNAUTHORIZED') {
                            msg = i18n.gis_requires_login;
                        } else {
                            msg = jqXHR.responseText;
                        }
                        console.log(msg);
                    }
                });

            } else {
                // Refresh without reloading the data
                self.refresh();
            }
        },

        /**
         * Get current report options form the report options form
         */
        _getOptions: function() {

            var $el = $(this.element),
                widget_id = '#' + $el.attr('id'),
                time = $(widget_id + '-time').val(),
                time_options = null,
                start = null,
                end = null,
                slots = $(widget_id + '-slots').val();

            if (time != 'custom') {
                time_options = time.split('|');
                if (time_options.length == 3) {
                    start = time_options[0];
                    end = time_options[1];
                    if (!slots || slots == "auto") {
                        slots = time_options[2];
                    }
                }
            } //else {
                // @todo
            //}

            var options = {
                fact: $(widget_id + '-fact').val(),
                timestamp: $(widget_id + '-timestamp').val(),
                start: start,
                end: end,
                slots: slots
            };
            return options;
        },

        /**
         * Get current filters from the associated filter form
         *
         * This is needed when the reload is not triggered /by/ the filter form
         */
        _getFilters: function() {

            var filters = $('#' + this.widget_id + '-filters');
            try {
                if (filters.length) {
                    return S3.search.getCurrentFilters(filters.first());
                } else {
                    return null;
                }
            } catch (e) {
                return null;
            }
        },

        /**
         * Update the Ajax URL with new options and filters
         *
         * @param {object} options - the report options as object
         * @param {object} filters - the filter options as object
         */
        _updateAjaxURL: function(options, filters) {

            var ajaxURL = this.options.ajaxURL;

            if (!ajaxURL) {
                return false;
            }

            // Construct the URL
            var qstr,
                url_parts = ajaxURL.split('?'),
                url_vars;

            if (url_parts.length > 1) {
                qstr = url_parts[1];
                url_vars = qstr.split('&');
            } else {
                qstr = '';
                url_vars = [];
            }

            var query = [],
                needs_reload = false;

            // Check options to update/remove
            if (options) {
                var option, newopt;
                for (option in options) {
                    newopt = options[option];
                    qstr = option + '=' + newopt;
                    if (!(needs_reload || $.inArray(qstr, url_vars) != -1 )) {
                        needs_reload = true;
                    }
                    query.push(qstr);
                }
            }

            var update = {},
                remove = {},
                subquery,
                i, len, k, v, q;

            // Check filters to update/remove
            if (filters) {

                // Operators excluding other filters for the same field
                var removeIncompatible = function(k) {

                    var exclusive = ['contains', 'anyof', 'belongs', 'eq'],
                        pattern,
                        match,
                        incompatible = [];

                    exclusive.forEach(function(op) {
                        pattern = new RegExp('__' + op + '$', 'g');
                        if (k.match(pattern)) {
                            match = pattern;
                        } else {
                            incompatible.push(op);
                        }
                    });

                    if (match) {
                        incompatible.forEach(function(op) {
                            remove[k.replace(match, '__' + op)] = true;
                        });
                    }
                };

                for (i=0, len=filters.length; i < len; i++) {
                    q = filters[i];
                    k = q[0];
                    v = q[1];

                    removeIncompatible(k);

                    if (v === null) {
                        if (!update[k]) {
                            remove[k] = true;
                        }
                    } else {
                        if (remove[k]) {
                            remove[k] = false;
                        }
                        subquery = k + '=' + encodeURIComponent(v);
                        if (update[k]) {
                            update[k].push(subquery);
                        } else {
                            update[k] = [subquery];
                        }
                    }
                }
            }

            // Replace/retain existing URL variables
            for (i=0, len=url_vars.length; i < len; i++) {
                q = url_vars[i].split('=');
                if (q.length > 1) {
                    k = decodeURIComponent(q[0]);
                    v = decodeURIComponent(q[1]);

                    if (remove[k]) {
                        needs_reload = true;
                        continue;
                    } else if (update[k]) {
                        if (!(needs_reload || $.inArray(k + '=' + v, update[k]) != -1)) {
                            needs_reload = true;
                        }
                        continue;
                    } else if (options && options.hasOwnProperty(k)) {
                        continue;
                    } else {
                        query.push(url_vars[i]);
                    }
                }
            }

            // Add new filters
            for (k in update) {
                for (i=0, len=update[k].length; i < len; i++) {
                    if (!(needs_reload || $.inArray(update[k][i], url_vars) != -1)) {
                        needs_reload = true;
                    }
                    query.push(update[k][i]);
                }
            }

            var url_query = query.join('&'),
                filtered_url = url_parts[0];
            if (url_query) {
                filtered_url = filtered_url + '?' + url_query;
            }
            this.options.ajaxURL = filtered_url;
            return needs_reload;
        },

        /**
         * Convert an ISO datetime string into a JS Date
         *
         * @param {string} string - the datetime string
         *
         * @todo: unused?
         */
        _parseDate: function(string) {

            var dt = d3.time.format('%Y-%m-%dT%H:%M:%S+00:00').parse(string);
            return dt;
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var self = this,
                widgetID = '#' + this.widget_id;

            // Show/hide report options
            $(widgetID + '-options legend').on('click', function() {
                $(this).siblings().toggle();
                $(this).children().toggle();
            });
            $(widgetID + '-filters legend').on('click', function() {
                $(this).siblings().toggle();
                $(this).children().toggle();
            });

            // Axis selectors to fire optionChanged-event
            var axes = ["fact", "timestamp", "time", "slots"].map(function(suffix) {
                return widgetID + '-' + suffix;
            }).join(",");
            $(axes).on('change.autosubmit', function() {
                $(widgetID + '-tp-form').trigger('optionChanged');
            });

            // Form submission
            if (this.options.autoSubmit) {
                // Auto-submit
                var timeout = this.options.autoSubmit;
                $(widgetID + '-tp-form').on('optionChanged', function() {
                    var $this = $(this);
                    if ($this.data('noAutoSubmit')) {
                        // Event temporarily disabled
                        return;
                    }
                    var timer = $this.data('autoSubmitTimeout');
                    if (timer) {
                        clearTimeout(timer);
                    }
                    timer = setTimeout(function () {
                        var options = self._getOptions(),
                            filters = self._getFilters();
                        self.reload(options, filters, false);
                    }, timeout);
                    $this.data('autoSubmitTimeout', timer);
                });
            } else {
                // Manual submit
                $(widgetID + '-tp-form input.tp-submit').on('click.timeplot', function() {
                    // @todo: implement _getOptions
                    var options = self._getOptions(),
                        filters = self._getFilters();
                    self.reload(options, filters, false);
                });
            }

            // Charts
            $(widgetID + '-lchart-totals').on('click', function() {
                self._renderChart({type: 'linechart', axis: 'totals'});
            });
            $(widgetID + '-bchart-totals').on('click', function() {
                self._renderChart({type: 'barchart', axis: 'totals'});
            });
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var widgetID = '#' + this.widget_id;

            $(window).off("resize.timeplot");
            $(widgetID + '-tp-form').off('optionChanged');
            $(widgetID + '-tp-form input.tp-submit').off('click.timeplot');
            $(widgetID + '-time').off('change.autosubmit');

            $(widgetID + '-options legend').off('click');
            $(widgetID + '-filters legend').off('click');

            $(widgetID + '-lchart-totals,' +
              widgetID + '-bchart-totals').off('click');

        }
    });
})(jQuery);
