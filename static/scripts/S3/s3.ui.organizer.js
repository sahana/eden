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

                // General options
                aspectRatio: 1.8,               // TODO make configurable (default 1.8)
                nowIndicator: true,             // TODO make configurable (default on)
                slotDuration: '00:30:00',       // TODO make configurable (default 30min)
                snapDuration: '00:15:00',       // TODO make configurable (default 15min)

                // Permitted actions
                selectable: true,               // TODO make sure we have insertable resources
                editable: true,                 // TODO implement edit

                // View options
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
                defaultView: defaultView,

                eventRender: function(item, element) {
                    self._eventRender(item, element);
                },
                eventDestroy: function(item, element) {
                    self._eventDestroy(item, element);
                },
                select: function(start, end, jsEvent /*, view */) {
                    self._selectDate(start, end, jsEvent);
                },
                unselect: function(/* jsEvent, view */) {
                    $(self.element).qtip('destroy', true);
                },
                unselectCancel: '.s3-organizer-create',

                // L10n
                locale: opts.locale,
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
                resourceConfigs.forEach(function(resourceConfig, index) {
                    this._addResource(resourceConfig, index);
                }, this);
            }

            this._bindEvents();
        },

        /**
         * Add a resource
         *
         * @param {object} resourceConfig - the resource config from options
         */
        _addResource: function(resourceConfig, index) {

            var resource = $.extend({}, resourceConfig, {_cache: new EventCache()});

            this.resources.push(resource);
            var timeout = resource.timeout;
            if (timeout === undefined) {
                timeout = this.options.timeout;
            }

            var self = this;
            $(this.element).fullCalendar('addEventSource', {
                id: '' + index, // must pass a string here
                allDayDefault: !resource.useTime,
                events: function(start, end, timezone, callback) {
                    self._fetchItems(resource, start, end, timezone, callback);
                }
            });
        },

        /**
         * Actions after a calendar item has been rendered
         *
         * @param {object} item - the calendar item
         * @param {jQuery} element - the DOM node of the item
         */
        _eventRender: function(item, element) {

            var self = this;

            // Attach the item popup
            // TODO add modals on visible-event
            $(element).qtip({
                content: {
                    title: function(jsEvent, api) {
                        return self._itemTitle(item, api);
                    },
                    text: function(jsEvent, api) {
                        return self._itemDisplay(item, api);
                    },
                    button: true
                },
                position: {
                    at: 'center right',
                    my: 'left center',
                    effect: false,
                    viewport: $(window),
                    adjust: {
                        // horizontal vertical
                        method: 'flip shift'
                    }
                },
                show: {
                    event: 'click',
                    solo: true
                },
                hide: {
                    event: 'click mouseleave',
                    delay: 800,
                    fixed: true
                }
            });
        },

        /**
         * Actions before a calendar item is removed from the DOM
         *
         * @param {object} item - the calendar item
         * @param {jQuery} element - the DOM node of the item
         */
        _eventDestroy: function(item, element) {

            // Remove the item popup
            $(element).qtip('destroy', true);
        },

        /**
         * Render the popup title for a calendar item
         *
         * @param {object} item - the calendar item
         *
         * @returns {string} - the popup title
         */
        _itemTitle: function(item) {

            var dateFormat = item.allDay && 'L' || 'L LT',
                dates = [item.start.format(dateFormat)];

            if (item.end) {
                dates.push(item.end.format(dateFormat));
            }

            return dates.join(' - ');
        },

        /**
         * Render the popup contents for a calendar item
         *
         * @param {object} item - the calendar item
         *
         * @returns {jQuery} - a DOM node with the contents
         */
        _itemDisplay: function(item) {

            var contents = $('<div class="s3-organizer-popup">'),
                opts = this.options,
                resource = opts.resources[item.source.id];

            // Item title
            $('<h6>').text(item.title).appendTo(contents);

            // Item description
            var columns = resource.columns,
                description = item.description;
            if (columns && description) {
                columns.forEach(function(column) {
                    var colName = column[0],
                        label = column[1];
                    if (description[colName] !== undefined) {
                        if (label) {
                            $('<label>').text(label).appendTo(contents);
                        }
                        $('<p>').html(description[colName]).appendTo(contents);
                    }
                });
            }

            // Buttons
            // TODO make these work
            // TODO convert edit-button into action-button with popup
//             $('<button class="tiny button s3-organizer-edit" type="button">').text('Edit').appendTo(contents);
//             $('<button class="tiny alert button s3-organizer-delete" type="button">').text('Delete').appendTo(contents);

            return contents;
        },

        /**
         * Actions when a date interval has been selected
         *
         * @param {moment} start - the start date
         * @param {moment} end - the end date
         * @param {event} jsEvent - the JS event that triggered the selection
         */
        _selectDate: function(start, end, jsEvent) {

            var self = this;

            $(this.element).qtip({
                content: {
                    text: function(jsEvent, api) {
                        return self._selectResource(start, end, jsEvent, api);
                    }
                },
                position: {
                    target: 'mouse',
                    at: 'center right',
                    my: 'left center',
                    effect: false,
                    viewport: $(window),
                    adjust: {
                        mouse: false,
                        method: 'flip shift'
                    }
                },
                show: {
                    event: 'click',
                    solo: true
                },
                hide: {
                    event: 'mouseleave',
                    delay: 800,
                    fixed: true
                },
                events: {
                    visible: function(/* jsEvent, api */) {
                        S3.addModals();
                    }
                }
            });

            $(this.element).qtip('show', jsEvent);
        },

        /**
         * Render the contents of the resource-selector (create-popup)
         *
         * @param {moment} start - the start of the selected interval
         * @param {moment} end - the end of the selected interval
         * @param {event} jsEvent - the event that opened the popup
         * @param {object} api - the qtip-API for the popup
         */
        _selectResource: function(start, end, jsEvent, api) {

            // Add class to attach styles and cancel auto-unselect
            api.set('style.classes', 's3-organizer-create');

            var opts = this.options,
                resources = opts.resources,
                el = $(this.element),
                ns = this.eventNamespace,
                widgetID = el.attr('id'),
                contents = $('<div>');

            resources.forEach(function(resource) {

                // Make sure resource is insertable
                if (!resource.insertable) {
                    return;
                }
                var createButton = $('<a class="action-btn s3_modal">'),
                    label = resource.labelCreate,
                    url = resource.baseURL;

                if (url && label) {
                    url += '/create.popup';
                    var query = [];

                    // Add refresh-target
                    if (widgetID) {
                        query.push('refresh=' + encodeURIComponent(widgetID));
                    }

                    // Add selected date range
                    var dates = start.toISOString() + '--' + moment(end).subtract(1, 'seconds').toISOString();
                    query.push('organizer=' + encodeURIComponent(dates));

                    url += '?' + query.join('&');
                    createButton.attr('href', url)
                                .text(label)
                                .appendTo(contents)
                                .off(ns).on('click' + ns, function() {
                                    // TODO bind per button-class rather than individual button?
                                    el.qtip('hide');
                                });
                }
            });

            return contents;
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

                    data = self._decodeServerData(data);

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
         * TODO docstring
         */
        _decodeServerData: function(data) {

            var columns = data.columns,
                items = data.items,
                translateCols = 0;

            if (columns && columns.constructor === Array) {
                translateCols = columns.length;
            }

            items.forEach(function(item) {
                var description = {},
                    values = item.description;
                if (translateCols && values && values.constructor === Array) {
                    var len = values.length;
                    if (len <= translateCols) {
                        for (var i = 0; i < len; i++) {
                            description[columns[i]] = values[i];
                        }
                    }
                }
                item.description = description;
            });

            return items;
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
