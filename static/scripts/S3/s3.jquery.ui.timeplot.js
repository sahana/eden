/**
 * jQuery UI timeplot Widget for S3TimePlot
 *
 * @copyright: 2013-14 (c) Sahana Software Foundation
 * @license: MIT
 *
 * requires: jQuery 1.9.1+
 * requires: jQuery UI 1.10 widget factory
 * requires: D3.js 3.4.9+
 *
 */

(function($, undefined) {

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
         * @prop {string} emptyMessage - message to show when no data are
         *                               available for the time interval
         * @prop {bool} burnDown - render as burnDown from baseline
         *                         rather than as burnUp from zero
         */
        options: {
            ajaxURL: null,
            autoSubmit: 1000,
            burnDown: false,
            emptyMessage: 'No data available'
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

            // Initialize instance data
            this.widget_id = $(this.element).attr('id');
            this.input = $(this.element).find('input[type="hidden"][name="tp-data"]').first();
            this.data = null;
            this.svg = null;

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
        },
        
        /**
         * Re-draw contents
         */
        refresh: function() {

            var el = this.element

            this._unbindEvents();
            
            this._renderChart();

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
         * Render the Chart
         */
        _renderChart: function() {

            var el = this.element;

            // Lazy parse the JSON data
            var data = this.data;
            if (data === null) {
                data = JSON.parse(this.input.val());
                this.data = data;
            }
            
            // data = [[start, end, value], ...]

            // Remove previous plot
            if (this.svg) {
                this.svg.remove();
                this.svg = null;
                el.find('.tp-chart').empty();
            }

            // Compute width and height
            var available_width = el.width();
            var available_height = available_width / 16 * 5;

            var values = this._computeValues(data);
            var marginLeft = this.options.burnDown ? 10 : values.maxValue.toString().length * 6 + 18;
            var marginRight = this.options.burnDown ? values.maxValue.toString().length * 6 + 18 : 10;
            
            var margin = {top: 40, right: marginRight, bottom: 70, left: marginLeft},
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

            this._renderBarChart(values, width, height);
        },

        /**
         * Compute the chart values
         *
         * @param {object} data - the data (from the server)
         * @return chart data object including min/max values
         */
        _computeValues: function(data) {
            
            var values = data.items,
                baseline = data.baseline,
                burnDown = this.options.burnDown;

            var results = [],
                minValue,
                maxValue;
            if (!data.empty) {
                var items = data.items, v;
                for (var i=0, len=items.length; i<len; i++) {
                    item = items[i];
                    if (burnDown && (baseline || baseline == 0)) {
                        v = baseline - item[2];
                    } else {
                        v = item[2];
                    }
                    results.push([item[0], item[1], v]);
                }
                var minValue = d3.min(results, function(d) {
                    return burnDown ? d[2] : Math.min(d[2], baseline);
                });
                var maxValue = d3.max(results, function(d) {
                    return burnDown ? d[2] : Math.max(d[2], baseline);
                });
            } else {
                results = [];
                minValue = d3.min([baseline, 0]);
                maxValue = d3.max([baseline, 0]);
            }
            return {
                baseline: baseline,
                items: results,
                empty: data.empty,
                minValue: minValue,
                maxValue: maxValue
            }
        },

        /**
         * Render Bar Chart
         *
         * @param {object} data - the computed data (from _computeValues)
         * @param {number} width - the chart width
         * @param {number} height - the chart height
         */

        _renderBarChart: function(data, width, height) {

            var svg = this.svg,
                burnDown = this.options.burnDown;

            // Create the x axis
            var x = d3.scale.ordinal()
                            .rangeRoundBands([0, width], .05);

            // @todo: dynamic tick formatter
            var xAxis = d3.svg.axis()
                              .scale(x)
                              .orient("bottom")
                              .tickFormat(d3.time.format("%Y-%m-%d"));

            // Create the y axis
            var y = d3.scale.linear()
                            .range([height, 0]);

            var yAxis = d3.svg.axis()
                              .scale(y)
                              .orient(burnDown? "right" : "left");

            // Compute the scales
            var self = this;
            x.domain(data.items.map(function(d) {
                return self._parseDate(d[0]);
            }));
            y.domain([Math.min(0, data.minValue), data.maxValue]);

            // Add x axis
            svg.append("g")
               .attr("class", "x axis")
               .attr("transform", "translate(0," + height + ")")
               .call(xAxis)
               .selectAll("text")
               .style("text-anchor", "end")
               .style("font", "10px sans-serif")
               .attr("dx", "-.8em")
               .attr("dy", "-.55em")
               .attr("transform", "rotate(-90)" );

            // Add y axis
            var yAxisPosition = burnDown ? width : 0;
            svg.append("g")
               .attr("class", "y axis")
               .attr("transform", "translate(" + yAxisPosition + ",0)")
               .call(yAxis);

            if (data.empty) {
                // Display empty message
                svg.selectAll("message")
                   .data([this.options.emptyMessage])
                   .enter()
                   .append("text")
                   .attr("class", "empty")
                   .attr("x", 20)
                   .attr("y", 30)
                   .text(function(d) { return d; });
            } else {
                // Add horizontal grid lines
                svg.append("g")
                   .attr("class", "grid")
                   .call(yAxis.tickSize(burnDown ? width : -width).tickFormat(""));

                // Render baseline?
                var baseline = data.baseline;
                if (baseline && !burnDown) {
                    
                    svg.selectAll("basearea")
                       .data([baseline])
                       .enter()
                       .append("rect")
                       .attr("class", baseline > 0 ? "basearea positive" : "basearea negative")
                       .attr("x", 0 )
                       .attr("width", width )
                       .attr("y", function(d) { return d < 0 ? y(0) : y(d); })
                       .attr("height", function(d) { return Math.abs(y(d) - y(0)); });
                       
                    svg.selectAll("baseline")
                       .data([baseline])
                       .enter()
                       .append("line")
                       .attr("class",  baseline > 0 ? "baseline positive" : "baseline negative")
                       .attr("x1", 0)
                       .attr("x2", width)
                       .attr("y1", function(d) { return y(d);} )
                       .attr("y2", function(d) { return y(d);} );
                }

                // Add the bars
                bar = svg.selectAll("bar")
                         .data(data.items);

                bar.enter()
                   .append("rect")
                   .attr("class", function(d, i) { return d[2] < 0 ? "bar negative" : "bar positive"; })
                   .attr("x", function(d) { return x(self._parseDate(d[0])); })
                   .attr("width", x.rangeBand())
                   .attr("y", function(d) { return d[2] < 0 ? y(0) : y(d[2]); })
                   .attr("height", function(d) { return Math.abs(y(d[2]) - y(0)); });
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
                var ajaxURL = this.options.ajaxURL;
                $.ajax({
                    'url': ajaxURL,
                    'dataType': 'json'
                }).done(function(data) {
                    self.input.val(JSON.stringify(data));
                    self.data = data;
                    self.refresh();
                }).fail(function(jqXHR, textStatus, errorThrown) {
                    if (errorThrown == 'UNAUTHORIZED') {
                        msg = i18n.gis_requires_login;
                    } else {
                        msg = jqXHR.responseText;
                    }
                    console.log(msg);
                });
            } else {
                // Refresh without reloading the data
                // @todo: this may be too fast to see the throbber, so user
                //        doesn't get a visual feedback for clicking 'Submit'
                //        => consider a micro-delay here
                self.refresh();
            }
        },

        /**
         * Get current report options form the report options form
         */
        _getOptions: function() {

            var $el = $(this.element);
            var widget_id = '#' + $el.attr('id');

            var time = $(widget_id + '-time').val(),
                time_options = null,
                start = null,
                end = null,
                slots = null;
                
            if (time != 'custom') {
                time_options = time.split('|');
                if (time_options.length == 3) {
                    start = time_options[0];
                    end = time_options[1];
                    slots = time_options[2];
                }
            } else {
                // @todo
            }

            var options = {
//                 fact: $(widget_id + '-fact').val(),
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
            } catch (e) {}
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
                var option;
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
                i, len, k, v, q;

            // Check filters to update/remove
            if (filters) {
                for (i=0, len=filters.length; i < len; i++) {
                    q = filters[i];
                    k = q[0];
                    v = q[1];
                    if (v === null) {
                        if (!update[k]) {
                            remove[k] = true;
                        }
                    } else {
                        if (remove[k]) {
                            remove[k] = false;
                        }
                        if (update[k]) {
                            update[k].push(k + '=' + v);
                        } else {
                            update[k] = [k + '=' + v];
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
                widget_id = this.widget_id;

            // Refresh on resize in order to adapt to page width
            // @todo: make configurable
            $(window).on("resize.timeplot", function() {
                self.refresh();
            });
            
            // Show/hide report options
            $('#' + widget_id + '-options legend').click(function() {
                $(this).siblings().toggle();
                $(this).children().toggle();
            });
            $('#' + widget_id + '-filters legend').click(function() {
                $(this).siblings().toggle();
                $(this).children().toggle();
            });

            // Axis selectors to fire optionChanged-event
            $('#' + widget_id + '-time').on('change.autosubmit', function() {
                $('#' + widget_id + '-tp-form').trigger('optionChanged');
            });

            // Form submission
            if (this.options.autoSubmit) {
                // Auto-submit
                var timeout = this.options.autoSubmit;
                $('#' + this.widget_id + '-tp-form').on('optionChanged', function() {
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
                        // @todo: implement _getOptions
                        var options = self._getOptions(),
                            filters = self._getFilters();
                        self.reload(options, filters, false);
                    }, timeout);
                    $this.data('autoSubmitTimeout', timer);
                });
            } else {
                // Manual submit
                $('#' + this.widget_id + '-tp-form input.tp-submit').on('click.timeplot', function() {
                    // @todo: implement _getOptions
                    var options = self._getOptions(),
                        filters = self._getFilters();
                    self.reload(options, filters, false);
                });
            }
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var widget_id = this.widget_id;

            $(window).off("resize.timeplot");
            $('#' + widget_id + '-tp-form').off('optionChanged');
            $('#' + widget_id + '-tp-form input.tp-submit').off('click.timeplot');
            $('#' + widget_id + '-time').unbind('change.autosubmit');

            $('#' + widget_id + '-options legend').unbind('click');
            $('#' + widget_id + '-filters legend').unbind('click');
        }
    });
})(jQuery);
