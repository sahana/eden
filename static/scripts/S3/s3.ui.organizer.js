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

        this.items = {};  // {id: item}
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
            this.items[item.id] = events[item.id] = item;
        }, this);

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
     * Update an item in the cache
     *
     * @param {integer} itemID - the item record ID
     * @param {object} data - the data to update the item with
     */
    EventCache.prototype.updateItem = function(itemID, data) {

        var item = this.items[itemID];

        if (item && data) {
            $.extend(item, data);
        }
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

            var opts = this.options,
                resourceConfigs = opts.resources;

            this._unbindEvents();

            // Can records be created for any resource?
            var insertable = false,
                allDaySlot = false;
            resourceConfigs.forEach(function(resourceConfig) {
                if (resourceConfig.insertable) {
                    insertable = true;
                }
                if (!resourceConfig.useTime) {
                    allDaySlot = true;
                }
            });

            // Determine available views and default view
            // TODO make configurable (override options)
            var leftHeader,
                defaultView;
            if (opts.useTime) {
                leftHeader = 'month,agendaWeek,agendaDay reloadButton';
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
                defaultTimedEventDuration: '00:30:00',
                allDaySlot: allDaySlot,

                // Permitted actions
                selectable: insertable,
                editable: true,
                eventDrop: function(event, delta, revertFunc /* , jsEvent, ui, view */) {
                    self._updateItem(event, revertFunc);
                },
                eventResize: function(event, delta, revertFunc /* , jsEvent, ui, view */) {
                    self._updateItem(event, revertFunc);
                },

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
                id: '' + index, // must be string, falsy gets dropped
                allDayDefault: !resource.useTime,
                editable: !!resource.editable, // can be overridden per-record
                startEditable: !!resource.startEditable,
                durationEditable: !!resource.end && !!resource.durationEditable,
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
                },
                events: {
                    visible: function(/* jsEvent, api */) {
                        S3.addModals();
                    }
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
         * @param {object} api - the qtip-API of the popup
         *
         * @returns {jQuery} - a DOM node with the contents
         */
        _itemDisplay: function(item, api) {

            var contents = $('<div class="s3-organizer-popup">'),
                opts = this.options,
                resource = opts.resources[item.source.id];

            // Item Title
            $('<h6>').text(item.title).appendTo(contents);

            // Item Description
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

            // Edit/Delete Buttons
            var widgetID = $(this.element).attr('id'),
                ns = this.eventNamespace,
                buttons = [],
                btn,
                baseURL = resource.baseURL,
                url;
            if (baseURL) {
                if (resource.editable && item.editable !== false) {
                    url = baseURL + '/' + item.id + '/update.popup?refresh=' + widgetID;
                    // TODO i18n
                    btn = $('<a class="action-btn s3_modal">').text('Edit')
                                                              .attr('href', url)
                                                              .on('click' + ns, function() {
                                                                api.hide();
                                                              });
                    buttons.push(btn);
                }
                if (resource.deletable && item.deletable !== false) {
                    // TODO i18n
                    // TODO bind Ajax-deletion method
                    btn = $('<a class="action-btn delete-btn-ajax">').text('Delete');
                    buttons.push(btn);
                }
            }
            if (buttons.length) {
                var buttonArea = $('<div>').appendTo(contents);
                buttons.forEach(function(btn) {
                    btn.appendTo(buttonArea);
                });
            }

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
                    'text': function(jsEvent, api) {
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
                    'visible': function(/* jsEvent, api */) {
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
                ns = this.eventNamespace,
                widgetID = $(this.element).attr('id'),
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
                                .on('click' + ns, function() {
                                    api.hide();
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

            // Remove other filters for start/end
            var filters = currentFilters.filter(function(query) {
                var selector = query[0].split('__')[0];
                return selector !== resource.start && selector !== resource.end;
            });

            // Add date filters for start/end
            // (record start date or end date must be within the interval)
            var selectors = [];
            if (resource.start) {
                selectors.push(resource.start);
            }
            if (resource.end) {
                selectors.push(resource.end);
            }
            if (selectors.length) {
                selectors = selectors.join('|');
                filters.push([selectors + '__ge', start.toISOString()]);
                filters.push([selectors + '__lt', end.toISOString()]);
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

                    data = self._decodeServerData(resource, data);

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
         * Decode server data into fullCalendar events
         *
         * @param {object} resource - the resource from which items are loaded
         * @param {object} data - the data returned from the server
         *
         * @returns {Array} - Array of fullCalendar event objects
         */
        _decodeServerData: function(resource, data) {

            var columns = data.c,
                records = data.r,
                items = [],
                translateCols = 0;

            if (columns && columns.constructor === Array) {
                translateCols = columns.length;
            }

            records.forEach(function(record) {

                var description = {},
                    values = record.d;

                if (translateCols && values && values.constructor === Array) {
                    var len = values.length;
                    if (len <= translateCols) {
                        for (var i = 0; i < len; i++) {
                            description[columns[i]] = values[i];
                        }
                    }
                }

                var end = record.e;
                if (end) {
                    // End date in item is exclusive
                    if (resource.useTime) {
                        // Item end date is record end date plus one second
                        end = moment(end).add(1, 'seconds').toISOString();
                    } else {
                        // Item end date is start of next day after record end
                        end = moment(end).add(1, 'days').startOf('day').toISOString();
                    }
                }

                var item = {
                    'id': record.id,
                    title: record.t,
                    start: record.s,
                    end: end,
                    description: description
                };

                // Permission overrides (skip if true to let resource-default apply)
                if (!record.pe) {
                    item.editable = false;
                }
                if (!record.pd) {
                    item.deletable = false;
                }

                items.push(item);
            });

            return items;
        },

        /**
         * Update start/end of a calendar item
         *
         * @param {object} item - the calendar item
         * @param {function} revertFunc - function to revert the action
         *                                (in case the Ajax request fails)
         */
        _updateItem: function(item, revertFunc) {

            var resource = this.resources[item.source.id],
                self = this;

            var data = {"id": item.id, "s": item.start.toISOString()};
            if (resource.end) {
                // End date in item is exclusive
                if (resource.useTime) {
                    // Record end is one second before item end
                    data.e = moment(item.end).subtract(1, 'seconds').toISOString();
                } else {
                    // Record end is end of previous day before item end
                    data.e = moment(item.end).subtract(1, 'days').endOf('day').toISOString();
                }
            }

            this._sendItems(resource, {u: [data]}, function() {
                if (resource.reloadOnUpdate) {
                    self.reload();
                } else {
                    resource._cache.updateItem(item.id, {
                        start: item.start,
                        end: item.end
                    });
                }
            }, revertFunc);
        },

        /**
         * Send item updates to the server
         *
         * @param {object} resource - the resource to send updates to
         * @param {object} data - the data to send
         * @param {function} callback - the callback to invoke upon success
         * @param {function} revertFunc - the callback to invoke upon failure
         */
        _sendItems: function(resource, data, callback, revertFunc) {

            var formKey = $('input[name="_formkey"]', this.element).val(),
                jsonData = JSON.stringify($.extend({k: formKey}, data));

            this._showThrobber();

            var self = this;
            $.ajaxS3({
                type: 'POST',
                url: resource.ajaxURL,
                data: jsonData,
                dataType: 'json',
                retryLimit: 0,
                contentType: 'application/json; charset=utf-8',
                success: function() {
                    if (typeof callback === 'function') {
                        callback();
                    }
                    self._hideThrobber();
                },
                error: function() {
                    if (typeof revertFunc === 'function') {
                        revertFunc();
                    }
                    self._hideThrobber();
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
