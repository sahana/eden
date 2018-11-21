/**
 * jQuery UI Widget for S3Organizer
 *
 * @copyright 2018 (c) Sahana Software Foundation
 * @license MIT
 *
 * requires jQuery 1.9.1+
 * requires jQuery UI 1.10 widget factory
 */
(function($, undefined) {

    "use strict";
    var organizerID = 0;

    // ------------------------------------------------------------------------
    // EVENT CACHE

    /**
     * Discontinuous Event Cache to reduce Ajax-calls when browsing dates
     */
    function EventCache() {

        this.slices = []; // [[startMoment, endMoment, {id: item, ...}], ...]
    }

    /**
     * Store events within a certain time interval
     *
     * @param {moment} start - the (inclusive) start date/time of the interval
     * @param {moment} end - the (exclusive) end date/time of the interval
     * @param {Array} items - the event items in this interval
     */
    EventCache.prototype.store = function(start, end, items) {

        // Convert items array into object with item IDs as keys
        var events = {};
        items.forEach(function(item) {
            events[item.id] = item;
        });

        // Add the new slice
        var slices = this.slices,
            slice = [moment(start), moment(end), events];
        slices.push(slice);

        // Sort slices
        slices.sort(function(x, y) {
            if (x[0].isBefore(y[0])) {
                return -1;
            } else if (y[0].isBefore(x[0])) {
                return 1;
            } else {
                if (x[1].isBefore(y[1])) {
                    return -1;
                } else if (y[1].isBefore(x[1])) {
                    return 1;
                }
            }
            return 0;
        });

        // Merge overlapping/adjacent slices
        if (slices.length > 1) {
            var newSlices = [];
            var merged = slices.reduce(function(x, y) {
                if (x[1].isBefore(y[0]) || x[0].isAfter(y[1])) {
                    // Slices do not overlap
                    newSlices.push(x);
                    return y;
                } else {
                    // Slices overlap
                    return [
                        moment.min(x[0], y[0]),
                        moment.max(x[1], y[1]),
                        $.extend({}, x[2], y[2])
                    ];
                }
            });
            newSlices.push(merged);
            this.slices = newSlices;
        }
    };

    /**
     * Retrieve events within a certain time interval
     *
     * @param {moment|Date|string} start - the start of the interval
     * @param {moment|Date|string} end - the end of the interval
     *
     * @returns {Array} - the events within the interval,
     *                    or null if the interval is not completely cached
     */
    EventCache.prototype.retrieve = function(start, end) {

        start = moment(start);
        end = moment(end);

        var slices = this.slices,
            numSlices = slices.length,
            slice,
            events,
            eventID,
            event,
            eventStart,
            items = [];

        for (var i = 0; i < numSlices; i++) {
            slice = slices[i];
            if (slice[0].isSameOrBefore(start) && slice[1].isSameOrAfter(end)) {
                events = slice[2];
                for (eventID in events) {
                    event = events[eventID];
                    eventStart = moment(event.start);
                    if (eventStart.isAfter(end)) {
                        continue;
                    }
                    if (event.end) {
                        if (moment(event.end).isBefore(start)) {
                            continue;
                        }
                    } else {
                        if (eventStart.isSameOrBefore(moment(start).subtract(1, 'days'))) {
                            continue;
                        }
                    }
                    items.push(event);
                }
                return items;
            }
        }
        return null;
    };

    /**
     * Clear the cache
     */
    EventCache.prototype.clear = function() {

        this.slices = [];
    };

    // ------------------------------------------------------------------------
    // UI WIDGET

    /**
     * Organizer
     */
    $.widget('s3.organizer', {

        /**
         * Default options
         *
         * TODO document options
         */
        options: {

            locale: 'en',
            timeout: 10000,
            resources: null
        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = organizerID;
            organizerID += 1;

            this.eventNamespace = '.organizer';
        },

        /**
         * Update the widget options
         */
        _init: function() {

            this.openRequest = null;
            this.loadCount = -1;

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

            var opts = this.options;

            this._unbindEvents();

            // Determine available views and default view
            // TODO make configurable (override options)
            var leftHeader,
                defaultView;
            if (opts.useTime) {
                leftHeader = 'month,agendaWeek reloadButton';
                defaultView = 'agendaWeek';
            } else {
                leftHeader = 'month,basicWeek reloadButton';
                defaultView = 'month';
            }

            var self = this;
            $(this.element).fullCalendar({
                customButtons: {
                    reloadButton: {
                        text: '',
                        click: function() {
                            self.reload();
                        }
                    }
                },
                header: {
                    left: leftHeader,
                    center: 'title',
                    right: 'today prev,next'
                },
                locale: opts.locale,
                defaultView: defaultView,
                aspectRatio: 1.8,               // TODO make configurable (default 1.8)
                nowIndicator: true,             // TODO make configurable (default on)
                slotDuration: '00:30:00',       // TODO make configurable (default 30min)
                snapDuration: '00:15:00',       // TODO make configurable (default 15min)
                selectable: false,              // TODO implement create
                editable: false,                // TODO implement edit

                // Show all events in local time zone
                timezone: 'local'
            });

            // Remember reloadButton, use icon
            this.reloadButton = $('.fc-reloadButton-button').html('<i class="fa fa-refresh">');

            // Add throbber
            var throbber = $('<div class="inline-throbber">').css({visibility: 'hidden'});
            $('.fc-header-toolbar .fc-left', this.element).append(throbber);
            this.throbber = throbber;

            // Configure resources
            var resourceConfigs = opts.resources;
            this.resources = [];
            if (resourceConfigs) {
                resourceConfigs.forEach(function(resourceConfig) {
                    this._addResource(resourceConfig);
                }, this);
            }

            this._bindEvents();
        },

        /**
         * Add a resource
         *
         * @param {object} resourceConfig - the resource config from options
         */
        _addResource: function(resourceConfig) {

            var resource = $.extend({}, resourceConfig, {_cache: new EventCache()});

            this.resources.push(resource);
            var timeout = resource.timeout;
            if (timeout === undefined) {
                timeout = this.options.timeout;
            }

            var self = this;
            $(this.element).fullCalendar('addEventSource', {
                allDayDefault: !resource.useTime,
                events: function(start, end, timezone, callback) {
                    self._fetchItems(resource, start, end, timezone, callback);
                }
            });
        },

        /**
         * Fetch items from server (async)
         *
         * @param {object} resource - the resource configuration
         * @param {moment} start - start date (inclusive) of the interval
         * @param {moment} end - end date (exclusive) of the interval
         * @param {boolean|string} timezone - the timezone setting
         * @param {function} callback - the callback to invoke when the
         *                              data are available, function(items)
         */
        _fetchItems: function(resource, start, end, timezone, callback) {

            // Try to lookup from cache
            var items = resource._cache.retrieve(start, end);
            if (items) {
                callback(items);
                return;
            }

            var opts = this.options;

            // Show throbber
            this._showThrobber();

            // Get current filters
            var filterForm;
            if (resource.filterForm) {
                filterForm = $('#' + resource.filterForm);
            } else if (opts.filterForm) {
                filterForm = $('#' + opts.filterForm);
            }
            var currentFilters = S3.search.getCurrentFilters(filterForm);

            // Add date filters for start/end
            var startQuery,
                endQuery,
                filters = [];
            if (resource.start) {
                startQuery = [resource.start + '__ge', start.toISOString()];
            }
            if (resource.end) {
                endQuery = [resource.end + '__lt', end.toISOString()];
            } else {
                endQuery = [resource.start + '__lt', end.toISOString()];
            }
            currentFilters.forEach(function(query) {
                var selector = query[0].split('__')[0];
                if (selector === resource.start) {
                    if (startQuery) {
                        filters.push(startQuery);
                        startQuery = null;
                        if (!resource.end) {
                            filters.push(endQuery);
                            endQuery = null;
                        }
                    }
                } else if (selector === resource.end) {
                    if (endQuery) {
                        filters.push(endQuery);
                        endQuery = null;
                    }
                } else {
                    filters.push(query);
                }
            });
            if (startQuery) {
                filters.push(startQuery);
            }
            if (endQuery) {
                filters.push(endQuery);
            }

            // Update ajax URL
            var ajaxURL = resource.ajaxURL;
            if (!ajaxURL) {
                return;
            } else {
                ajaxURL = S3.search.filterURL(ajaxURL, filters);
            }

            // SearchS3 or AjaxS3?
            var timeout = resource.timeout,
                ajaxMethod = $.ajaxS3;
            if (timeout === undefined) {
                timeout = opts.timeout;
            }
            if ($.searchS3 !== undefined) {
                ajaxMethod = $.searchS3;
            }

            var openRequest = resource.openRequest;
            if (openRequest) {
                // Abort previously open request
                openRequest.onreadystatechange = null;
                openRequest.abort();
            }

            // Request updates for resource from server
            var self = this;
            resource.openRequest = ajaxMethod({
                'timeout': timeout,
                'url': ajaxURL,
                'dataType': 'json',
                'type': 'GET',
                'success': function(data) {

                    self._hideThrobber();
                    resource._cache.store(start, end, data);
                    callback(data);
                },
                'error': function(jqXHR, textStatus, errorThrown) {

                    self._hideThrobber();
                    var msg;
                    if (errorThrown == 'UNAUTHORIZED') {
                        msg = i18n.gis_requires_login;
                    } else {
                        msg = jqXHR.responseText;
                    }
                    console.log(msg);
                }
            });
        },

        /**
         * Clear the cache and re-fetch data (e.g. after filter change)
         */
        reload: function() {

            this.resources.forEach(function(resource) {
                resource._cache.clear();
            });

            $(this.element).fullCalendar('refetchEvents');
        },

        /**
         * Show the throbber
         */
        _showThrobber: function() {
            this.reloadButton.prop('disabled', true);
            this.throbber.css({visibility: 'visible'});
        },

        /**
         * Hide the throbber
         */
        _hideThrobber: function() {
            this.throbber.css({visibility: 'hidden'});
            this.reloadButton.prop('disabled', false);
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
