/**
 * jQuery UI Widget for Charts
 *
 * @copyright 2018 (c) Sahana Software Foundation
 * @license MIT
 *
 * requires jQuery 1.9.1+
 * requires jQuery UI 1.10 widget factory
 */
(function($, undefined) {

    "use strict";
    var uiChartID = 0;

    /**
     * uiChart
     */
    $.widget('s3.uiChart', {

        /**
         * Default options
         *
         * @prop {CSS} height - the container height
         * @prop {Array} colors - array of custom colors
         * @prop {integer} transition - duration of transition animation in ms
         * @prop {bool} staggerLabels - stagger X-axis labels (useful if they tend to overlap)
         */
        options: {

            height: '280px',
            colors: null,
            transition: 50,
            staggerLabels: true,
            valueFormat: ',.0f'

        },

        /**
         * Create the widget
         */
        _create: function() {

            //var el = $(this.element);

            this.id = uiChartID;
            uiChartID += 1;

            this.eventNamespace = '.uiChart';
        },

        /**
         * Update the widget options
         */
        _init: function() {

            //var el = $(this.element);

            this.refresh();
        },

        /**
         * Remove generated elements & reset other changes
         */
        _destroy: function() {

            $.Widget.prototype.destroy.call(this);
        },

        /**
         * Redraw contents
         */
        refresh: function() {

            var el = $(this.element),
                opts = this.options;

            this._unbindEvents();

            // Adjust the height of the container
            el.empty().css({height: opts.height});

            // Initialize the container
            var container = d3.select(el.get(0)).append('svg').attr('class', 'nv'),
                chart;

            // Instatiate the diagram
            switch(el.data('type')) {
                case 'piechart':
                    chart = this._pieChart(container);
                    break;
                case 'barchart':
                    chart = this._barChart(container);
                    break;
                case 'multibarchart':
                    chart = this._multiBarChart(container);
                    break;
                default:
                    break;
            }

            this._bindEvents();
        },

        /**
         * Fetch the diagram data (JSON) from the source
         *
         * @param {function} callback - the callback to invoke with the data
         */
        _getData: function(callback) {

            var el = $(this.element),
                dataSource = el.data('source');

            if (dataSource) {
                $.ajaxS3({
                    'url': dataSource,
                    'dataType': 'json',
                    'type': 'GET',
                    'ignoreStatus': [404],
                    'success': function(data) {
                        callback(data);
                    },
                    'error': function(jqXHR, textStatus, errorThrown) {
                        callback([]);
                        var msg;
                        if (errorThrown == 'UNAUTHORIZED') {
                            msg = i18n.gis_requires_login;
                        } else {
                            msg = jqXHR.responseText;
                        }
                        console.log(msg);
                    }
                });
            }
        },

        /**
         * Render data as bar chart
         *
         * @param {object} container - the D3-enhanced DOM node of the chart container
         */
        _barChart: function(container) {

            var //el = $(this.element),
                opts = this.options;

            var chart = nv.models.discreteBarChart()
                          .duration(opts.transition)
                          .x(function(d) { return d.label; })
                          .y(function(d) { return d.value; })
                          .staggerLabels(opts.staggerLabels)
                          .showValues(true);

            if (opts.colors) {
                chart.color(opts.colors);
            }

            var valueFormat = d3.format(opts.valueFormat);
            chart.yAxis.tickFormat(valueFormat);
            chart.valueFormat(valueFormat);

            // Render a bar chart
            var self = this;
            nv.addGraph(function() {
                self._getData(function(data) {
                    container.datum(data).call(chart);
                    chart.update();
                });
                nv.utils.windowResize(chart.update);
            });

            return chart;
        },

        /**
         * Render data as multi-bar chart
         *
         * @param {object} container - the D3-enhanced DOM node of the chart container
         */
        _multiBarChart: function(container) {

            var el = $(this.element),
                opts = this.options;

            var chart = nv.models.multiBarChart()
                          .duration(opts.transition)
                          .x(function(d) { return d.label; })
                          .y(function(d) { return d.value; })
                          .reduceXTicks(false)
                          .staggerLabels(opts.staggerLabels)
                          .stacked(true)
                          .groupSpacing(0.1);

            // Hide grouped/stacked switch?
            if (el.data('controls') == 'off') {
                chart.showControls(false);
            }

            // Hide legend?
            if (el.data('legend') == 'off') {
                chart.showLegend(false);
            }

            var valueFormat = d3.format(opts.valueFormat);
            chart.yAxis.tickFormat(valueFormat);

            if (opts.colors) {
                chart.color(opts.colors);
            }

            // Render a multi-bar chart
            var self = this;
            nv.addGraph(function() {
                self._getData(function(data) {
                    container.datum(data).call(chart);
                    chart.update();
                });
                nv.utils.windowResize(chart.update);
            });

            return chart;

        },

        /**
         * Render data as pie chart
         *
         * @param {object} container - the D3-enhanced DOM node of the chart container
         */
        _pieChart: function(container) {

            var el = $(this.element),
                opts = this.options;

            var chart = nv.models.pieChart()
                                 .duration(opts.transition)
                                 .x(function(d) { return d.label; })
                                 .y(function(d) { return d.value; })
                                 .showLabels(true)
                                 //.labelsOutside(true)
                                 .showTooltipPercent(true);

            var valueFormat = d3.format(opts.valueFormat);
            chart.valueFormat(valueFormat);

            // Hide legend?
            if (el.data('legend') == 'off') {
                chart.showLegend(false);
            }

            if (opts.colors) {
                chart.color(opts.colors);
            }
            // Render a pie chart
            var self = this;
            nv.addGraph(function() {
                self._getData(function(data) {
                    container.datum(data).call(chart);
                    chart.update();
                });
                nv.utils.windowResize(chart.update);
            });

            return chart;
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {
            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {
            return true;
        }
    });
})(jQuery);
