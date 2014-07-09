/**
 * jQuery UI timeplot Widget for S3Timeline
 *
 * @copyright: 2013-14 (c) Sahana Software Foundation
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
            this.svg = null;
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
                
            this._renderChart(data);

            this._bindEvents();
        },

        _parseDate: function(string) {

            var dt = d3.time.format('%Y-%m-%dT%H:%M:%S+00:00').parse(string);
            return dt;
        },

        _renderChart: function(data) {

            // data = [[start, end, value], ...]

            var el = this.element;

            // Remove previous plot
            if (this.svg) {
                this.svg.remove();
                el.find('.tp-chart').empty();
            }

            // Compute width and height
            var available_width = el.width();
            var available_height = available_width / 16 * 5;
            
            var margin = {top: 40, right: 10, bottom: 70, left: 40},
                width = available_width - margin.left - margin.right,
                height = available_height - margin.top - margin.bottom;

            // Generate new plot
            var svg = d3.select("#timeplot .tp-chart")
                        .append("svg")
                        .attr("width", width + margin.left + margin.right)
                        .attr("height", height + margin.top + margin.bottom)
                        .append("g")
                        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
            this.svg = svg;

            var x = d3.scale.ordinal()
                            .rangeRoundBands([0, width], .05);

            // @todo: dynamic tick formatter
            var xAxis = d3.svg.axis()
                              .scale(x)
                              .orient("bottom")
                              .tickFormat(d3.time.format("%Y-%m-%d"));

            var y = d3.scale.linear()
                            .range([height, 0]);

            var yAxis = d3.svg.axis()
                              .scale(y)
                              .orient("left");

            var self = this;
            x.domain(data.map(function(d) {
                return self._parseDate(d[0]);
            }));
            y.domain([0, d3.max(data, function(d) { return d[2]; })]);
            
            svg.append("g")
               .attr("class", "x axis")
               .attr("transform", "translate(0," + height + ")")
               .call(xAxis)
               .selectAll("text")
               .style("text-anchor", "end")
               .style({"font": "10px sans-serif"})
               .attr("dx", "-.8em")
               .attr("dy", "-.55em")
               .attr("transform", "rotate(-90)" );
      
            svg.append("g")
               .attr("class", "y axis")
               .call(yAxis);
               
            svg.selectAll("bar")
               .data(data)
               .enter()
               .append("rect")
               .style("fill", "steelblue")
               .attr("x", function(d) { return x(self._parseDate(d[0])); })
               .attr("width", x.rangeBand())
               .attr("y", function(d) { return y(d[2]); })
               .attr("height", function(d) { return height - y(d[2]); });
              
        },

        _bindEvents: function() {

            var self = this;
            
            // Bind events to generated elements (after refresh)
            $(window).on("resize.timeplot", function() {
                data = JSON.parse($(self.element).find('.tp-data').first().val())
                self._renderChart(data);
            });
        },

        _unbindEvents: function() {
            // Unbind events (before refresh)
            $(window).off("resize.timeplot");
        }
    });
})(jQuery);
