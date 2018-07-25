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
         * @todo document options
         */
        options: {

            height: '280px',
            colors: null,
            transition: 50

        },

        /**
         * Create the widget
         */
        _create: function() {

            var el = $(this.element);

            this.id = uiChartID;
            uiChartID += 1;

            this.eventNamespace = '.uiChart';
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

            $.Widget.prototype.destroy.call(this);
        },

        /**
         * Redraw contents
         */
        refresh: function() {

            var el = $(this.element),
                opts = this.options;

            this._unbindEvents();

            el.empty().css({height: opts.height});

            var container = d3.select(el.get(0)).append('svg').attr('class', 'nv'),
                chart;

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

            if (chart) {
                this._getData(function(data) {
                    container.datum(data).call(chart);
                    chart.update();
                });
            }

            this._bindEvents();
        },

        _getData: function(callback) {

            var el = $(this.element),
                dataSource = el.data('source');

            // TODO suppress alert for 4xx
            if (dataSource) {
                $.ajaxS3({
                    'url': dataSource,
                    'dataType': 'json',
                    'type': 'GET',
                    'success': function(data) {
                        callback(data);
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
            }
        },

        _barChart: function(container) {

            var el = $(this.element),
                opts = this.options;

            var chart = nv.models.discreteBarChart()
                          .duration(opts.transition)
                          .x(function(d) { return d.label })
                          .y(function(d) { return d.value })
                          .staggerLabels(true)
                          .showValues(true);

            if (opts.colors) {
                chart.color(opts.colors);
            }

            // Render a bar chart
            nv.addGraph(function() {
                container.call(chart);
                nv.utils.windowResize(chart.update);
            });

            return chart;
        },

        _multiBarChart: function(container) {

            var el = $(this.element),
                opts = this.options;

            var chart = nv.models.multiBarChart()
                          .duration(opts.transition)
                          .x(function(d) { return d.label; })
                          .y(function(d) { return d.value; })
                          .reduceXTicks(false)
                          .rotateLabels(0)
                          .showControls(false)
                          .stacked(true)
                          .groupSpacing(0.1);

//             chart.xAxis.tickFormat(d3.format(',f'));
//             chart.yAxis.tickFormat(d3.format(',.1f'));

            if (opts.colors) {
                chart.color(opts.colors);
            }

            // Render a multi-bar chart
            nv.addGraph(function() {
                container.call(chart);
                nv.utils.windowResize(chart.update);
            });

            return chart;

        },

        _pieChart: function(container) {

            var el = $(this.element),
                opts = this.options;

            var chart = nv.models.pieChart()
                                 .duration(opts.transition)
                                 .x(function(d) { return d.label })
                                 .y(function(d) { return d.value })
                                 .showLabels(true);
            if (opts.colors) {
                chart.color(opts.colors);
            }
            // Render a pie chart
            nv.addGraph(function() {
                container.datum([]).call(chart);
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
