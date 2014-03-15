/**
 * jQuery UI timeplot Widget for S3Timeline
 *
 * @copyright: 2013 (c) Sahana Software Foundation
 * @license: MIT
 *
 * requires: jQuery 1.9.1+
 * requires: jQuery UI 1.10 widget factory
 *
 */

(function($, undefined) {

    var timeplotID = 0;

    $.widget('s3.timeplot', {

        // Default options
        options: {
            method: 'count'
        },

        _create: function() {
            // Create the widget

            this.id = timeplotID;
            timeplotID += 1;
        },

        _init: function() {
            // Update widget options

            var el = this.element;

            // Render all initial contents
            this.refresh();
        },

        _destroy: function() {
            // Remove generated elements & reset other changes
        },
        
        refresh: function() {
            // Rre-draw contents

            this._unbindEvents();

            var opts = this.options,
                data = JSON.parse($(this.element).find('.tp-data').first().val());

            this._renderChart(data, opts.method);
            this._bindEvents();
        },

        _renderChart: function(data, method) {

            var el = this.element,
                d = this._aggregateSeries(data, method);

            var placeholder = $(el).find('.tp-chart').first()
            var chart = jQuery.plot(placeholder, [d], {
                series: {
                    bars: {
                        show: true,
                        align: "center",
                        barWidth: 120*24*60*60*300,
                        align: "left"
                    },
//                     lines: {
//                         show: true,
//                         lineWidth: 0.5,
//                         fill: true,
// //                         steps: true,
//                         fillColor: {
//                             colors: [ "rgba(255, 255, 255, 0.6)",
//                                       "rgba(204, 128, 128, 0.6)" ]
//                         }
//                     },
//                     points: { show: true }
                },
                xaxis: { mode: "time" },
                colors: ["#ff0000"],
                grid: {
//                     show: boolean
//                     aboveData: boolean
//                     color: color
                    backgroundColor: {colors: ['#ffffff', '#cccccc']}
//                     margin: number or margin object
//                     labelMargin: number
//                     axisMargin: number
//                     markings: array of markings or (fn: axes -> array of markings)
//                     borderWidth: number or object with "top", "right", "bottom" and "left" properties with different widths
//                     borderColor: color or null or object with "top", "right", "bottom" and "left" properties with different colors
//                     minBorderMargin: number or null
//                     clickable: boolean
//                     hoverable: boolean
//                     autoHighlight: boolean
//                     mouseActiveRadius: number
                }
            });

        },

        _aggregateSeries: function(data, method) {

            // data is an array of tuples [[id, start, end, value], ...]
            // method is:
            //     count = count the number of records
            //     sum = cumulate the value
            // id is the record ID
            // start/end are timestamps
            // value is a numeric value

            var series = [], item, start, dt;

            var start, end;
            for (i=0; i<data.length; i++) {

                item = data[i];
                start = item[0];
                if (!start) {
                    continue;
                } else {
                    dt = new Date(start).getTime();
                    series.push([dt, item[2]]);
                }
            }
            return series
        },

        _bindEvents: function() {
            // Bind events to generated elements (after refresh)
        },

        _unbindEvents: function() {
            // Unbind events (before refresh)
        }
    });
})(jQuery);
