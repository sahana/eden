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

    /**
     * Timeplot Report
     */
    $.widget('s3.timeplot', {

        /**
         * Default options
         *
         * @todo document options
         */
        options: {
            ajaxURL: null,
            autoSubmit: 1000
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

            this.widget_id = $(this.element).attr('id');
            
            this.input = $(this.element).find('input[type="hidden"][name="tp-data"]').first();
            this.data = null;

            // Render all initial contents
            this.svg = null;

            // Refresh
            this.refresh();
        },

        /**
         * Remove generated elements & reset other changes
         *
         * @todo: implement
         */
        _destroy: function() {
            
        },
        
        /**
         * Re-draw contents
         */
        refresh: function() {

            var $el = this.element

            this._unbindEvents();
            
            this._renderChart();

            // Hide submit-button if autoSubmit
            if (this.options.autoSubmit) {
                $el.find('.tp-submit').hide();
            } else {
                $el.find('.tp-submit').show();
            }
            this._bindEvents();
            
            $el.find('.tp-throbber').hide();
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

            // @todo: move into subfunction per chart type
            // @todo: split groups, stack or group bars

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
                              .orient("left");

            // Compute the scales
            var self = this;
            x.domain(data.map(function(d) {
                return self._parseDate(d[0]);
            }));
            y.domain([0, d3.max(data, function(d) { return d[2]; })]);

            // Add x axis
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

            // Add y axis
            svg.append("g")
               .attr("class", "y axis")
               .call(yAxis);

            // Add horizontal grid lines
            svg.append("g")
               .attr("class", "grid")
               .call(yAxis.tickSize(-width).tickFormat(""));

            // Add the bars
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

        /**
         * Ajax-reload the data and refresh all widget elements
         *
         * @todo: document parameters
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

            var options = {
                fact: $(widget_id + '-fact').val(),
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
         * */
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

        _parseDate: function(string) {

            var dt = d3.time.format('%Y-%m-%dT%H:%M:%S+00:00').parse(string);
            return dt;
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var self = this;

            // Refresh on resize in order to adapt to page width
            // @todo: make configurable
            $(window).on("resize.timeplot", function() {
                self.refresh();
            });
            
            // Form submission
            // @todo: implement _getOptions
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
                        var options = null, //self._getOptions(),
                            filters = self._getFilters();
                        self.reload(options, filters, false);
                    }, timeout);
                    $this.data('autoSubmitTimeout', timer);
                });
            } else {
                // Manual submit
                $('#' + this.widget_id + '-tp-form input.tp-submit').on('click.timeplot', function() {
                    var options = null, // self._getOptions(),
                        filters = self._getFilters();
                    self.reload(options, filters, false);
                });
            }
        },

        _unbindEvents: function() {
            // Unbind events (before refresh)
            $(window).off("resize.timeplot");
            $('#' + this.widget_id + '-tp-form').off('optionChanged');
            $('#' + this.widget_id + '-tp-form input.tp-submit').off('click.timeplot');
        }
    });
})(jQuery);
