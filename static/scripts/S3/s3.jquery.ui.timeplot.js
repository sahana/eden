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

            var data = JSON.parse($(this.element).find('.tp-data').first().val());

            this._renderChart(data, 'count');

            this._bindEvents();
        },

        _renderChart: function(data, method) {

            var el = this.element,
                d = this._aggregateSeries(data, method);

            var placeholder = $(el).find('.tp-chart').first()
            var chart = jQuery.plot(placeholder, [d], {
                series: {
                    lines: {
                        show: true,
                        lineWidth: 0.5,
                        fill: true,
//                         steps: true,
                        fillColor: {
                            colors: [ "rgba(255, 255, 255, 0.6)",
                                      "rgba(204, 128, 128, 0.6)" ]
                        }
                    },
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

            var series = [];
            for (i=0; i<data.length; i++) {
                item = data[i];

                value = method == 'count'? 1: item[3];

                start = item[1];
                if (!start) {
                    series.push([0, value]);
                } else {
                    start = start.split(' ').join('T');
                    d = new Date(start).getTime();
                    series.push([d, value]);
                }
                end = item[2];
                if (end) {
                    end = end.split(' ').join('T');
                    d = new Date(end).getTime();
                    series.push([d, -value]);
                }
            }
            var order = function(x, y) {
                return x[0] - y[0];
            };
            series.sort(order);
            var current = 0,
                timestamp = 0,
                result = [];
            for (i=0; i<series.length; i++) {
                item = series[i];

                current += item[1];

                if (result.length) {
                    last = result.slice(-1)[0];
                    if (item[0] > last[0]) {
                        result.push([item[0], current]);
                    } else {
                        result.pop();
                        result.push([item[0], current]);
                    }
                } else {
                    result.push([item[0], current]);
                }
            }
            if (result[0][0] == 0 && result.length > 1) {
                result = result.slice(1);
            }
            return result;
        },

        _bindEvents: function() {
            // Bind events to generated elements (after refresh)
        },

        _unbindEvents: function() {
            // Unbind events (before refresh)
        }
    });
})(jQuery);
