/**
 * jQuery UI Widget for S3Organizer
 *
 * @copyright 2018-2019 (c) Sahana Software Foundation
 * @license MIT
 *
 * requires jQuery 1.9.1+
 * requires jQuery UI 1.10 widget factory
 * requires moment.js
 * requires jQuery fullCalendar plugin
 * requires qTip2
 * requires jQuery UI datepicker
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
     * Update an item in the cache after it has been dragged&dropped
     * to another date, or resized.
     *
     * NB moving the item to another slice is unnecessary because
     *    items can only ever be moved between or resized within
     *    dates that are visible at the same time, and hence belong
     *    to the same slice (due to slice-merging in store())
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
     * Remove an item from the cache
     *
     * @param {integer} itemID - the item record ID
     */
    EventCache.prototype.deleteItem = function(itemID) {

        this.slices.forEach(function(slice) {
            delete slice[2][itemID];
        });
        delete this.items[itemID];
    };

    /**
     * Clear the cache
     */
    EventCache.prototype.clear = function() {

        this.slices = [];
        this.items = {};
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
         * @prop {string} locale - the locale to use
         *                         (one of those in fullcalendar/locale)
         * @prop {integer} timeout - the Ajax timeout (in milliseconds)
         * @prop {Array} resources - the resources, array of resource objects:
         *
         *   @prop {string} resource.start - start date column name
         *   @prop {string} resource.end - end date column name
         *   @prop {string} resource.ajaxURL - URL for Ajax-lookups
         *   @prop {string} resource.baseURL - base URL for modals (create/update)
         *   @prop {boolean} resource.useTime - use time (and hence, agenda views)
         *   @prop {boolean} resource.insertable - new items can be created
         *   @prop {string} resource.labelCreate - CRUD label for create
         *   @prop {boolean} resource.editable - items can be edited
         *   @prop {boolean} resource.startEditable - item start can be changed
         *   @prop {boolean} resource.durationEditable - item duration can be changed
         *   @prop {boolean} resource.deletable - items can be deleted
         *   @prop {boolean} resource.reloadOnUpdate - reload all items after
         *                                             updating start/duration
         *   @prop {string} resource.color - column name to determine item color
         *   @prop {object} resource.colors - mapping of color-column value to color:
         *                                    {value: '#rrggbb'}
         *
         * @prop {float} aspectRatio: the aspect ratio of the calendar
         * @prop {boolean} nowIndicator: show the now-indicator in agenda views
         * @prop {string} slotDuration: the slot size in agenda views
         * @prop {string} defaultTimedEventDuration: the default event duration for
         *                                           timed events without explicit end
         * @prop {object|Array} businessHours: business hours, an object or array of
         *                                     objects of the format:
         *                                     {dow:[0,1,2,3,4,5,6], start: "HH:MM", end: "HH:MM"},
         *                                     - false to disable
         * @prop {string} timeFormat: time format for events, to override the locale default
         * @prop {integer} firstDay: first day of the week (0=Sunday, 1=Monday etc.)
         * @prop {string} labelEdit: label for Edit-button
         * @prop {string} labelDelete: label for the Delete-button
         * @prop {string} deleteConfirmation: the question for the delete-confirmation
         *
         */
        options: {

            locale: 'en',
            timeout: 10000,
            resources: null,

            aspectRatio: 1.8,
            nowIndicator: true,
            slotDuration: '00:30:00',
            snapDuration: '00:15:00',
            defaultTimedEventDuration: '00:30:00',
            businessHours: false,
            timeFormat: null,

            labelEdit: 'Edit',
            labelDelete: 'Delete',
            deleteConfirmation: 'Do you want to delete this entry?',
            firstDay: 1
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
                resourceConfigs = opts.resources,
                el = $(this.element),
                widgetID = el.attr('id');

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
                leftHeader = 'month,agendaWeek,agendaDay reload';
                defaultView = 'agendaWeek';
            } else {
                leftHeader = 'month,basicWeek reload';
                defaultView = 'month';
            }

            var self = this,
                datePicker = $('#' + widgetID + '-date-picker');
            $(this.element).fullCalendar({

                // General options
                aspectRatio: opts.aspectRatio,
                nowIndicator: opts.nowIndicator,
                slotDuration: opts.slotDuration,
                snapDuration: opts.snapDuration,
                displayEventEnd: false,
                defaultTimedEventDuration: opts.defaultTimedEventDuration,
                allDaySlot: allDaySlot,
                firstDay: opts.firstDay,
                timeFormat: opts.timeFormat,
                slotLabelFormat: opts.timeFormat,
                businessHours: opts.businessHours,

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
                    reload: {
                        text: '',
                        click: function() {
                            self.reload();
                        }
                    },
                    calendar: {
                        text: '',
                        click: function() {
                            datePicker.datepicker('show');
                        }
                    }
                },
                header: {
                    left: leftHeader,
                    center: 'title',
                    right: 'calendar today prev,next'
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
            this.reloadButton = $('.fc-reload-button').html('<i class="fa fa-refresh">');

            // Move datepicker into header, use icon for calendar button
            var calendarButton = $('.fc-calendar-button').html('<i class="fa fa-calendar">');
            datePicker.datepicker('option', {showOn: 'focus', showButtonPanel: true, firstDay: opts.firstDay})
                      .insertBefore(calendarButton)
                      .on('change', function() {
                          var date = datePicker.datepicker('getDate');
                          if (date) {
                              el.fullCalendar('gotoDate', date);
                          }
                      });

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
                timeFormat = 'LT',
                dates = [item.start.format(dateFormat)];

            if (item.end) {
                var end = moment(item.end).endOf('minute');
                dates.push(end.format(timeFormat));
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
            $('<h6>').html(item.popupTitle).appendTo(contents);

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
                self = this,
                buttons = [],
                btn,
                baseURL = resource.baseURL;
            if (baseURL) {
                // Edit button
                if (resource.editable && item.editable !== false) {
                    var link = document.createElement('a');
                    link.href = baseURL;
                    link.pathname += '/' + item.id + '/update.popup';
                    if (link.search) {
                        link.search += '&refresh=' + widgetID;
                    } else {
                        link.search = '?refresh=' + widgetID;
                    }
                    btn = $('<a class="action-btn s3_modal">').text(opts.labelEdit)
                                                              .attr('href', link.href);
                    btn.on('click' + ns, function() {
                        api.hide();
                    });
                    buttons.push(btn);
                }
                // Delete button
                if (resource.deletable && item.deletable !== false) {
                    btn = $('<a class="action-btn delete-btn-ajax">').text(opts.labelDelete);
                    btn.on('click' + ns, function() {
                        if (confirm(opts.deleteConfirmation)) {
                            api.hide();
                            self._deleteItem(item, function() {
                                api.destroy();
                            });
                        }
                        return false;
                    });
                    buttons.push(btn);
                }
            }
            if (buttons.length) {
                $('<div>').append(buttons).appendTo(contents);
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

                    var link = createButton.get(0),
                        query = [];

                    // Set path to create-dialog
                    link.href = url;
                    link.pathname += '/create.popup';

                    // Add refresh-target
                    if (widgetID) {
                        query.push('refresh=' + encodeURIComponent(widgetID));
                    }

                    // Add selected date range
                    var dates = start.toISOString() + '--' + moment(end).subtract(1, 'seconds').toISOString();
                    query.push('organizer=' + encodeURIComponent(dates));

                    // Update query part of link URL
                    if (link.search) {
                        link.search += '&' + query.join('&');
                    } else {
                        link.search = '?' + query.join('&');
                    }

                    // Complete the button and append it to popup
                    createButton.text(label)
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

            // Remove filters for start/end
            var filters = currentFilters.filter(function(query) {
                var selector = query[0].split('__')[0];
                return selector !== resource.start && selector !== resource.end;
            });

            // Update ajax URL
            var ajaxURL = resource.ajaxURL;
            if (!ajaxURL) {
                return;
            } else {
                ajaxURL = S3.search.filterURL(ajaxURL, filters);
            }

            // Add interval
            var interval = encodeURIComponent(start.toISOString() + '--' + end.toISOString());
            if (ajaxURL.indexOf('?') != -1) {
                ajaxURL += '&$interval=' + interval;
            } else {
                ajaxURL += '?$interval=' + interval;
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
                translateCols = 0,
                colors = resource.colors;

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

                var title = record.t,
                    item = {
                    'id': record.id,
                    title: $('<div>').html(title).text(),
                    popupTitle: title,
                    start: record.s,
                    end: end,
                    description: description,
                };

                // Permission overrides (skip if true to let resource-default apply)
                if (!record.pe) {
                    item.editable = false;
                }
                if (!record.pd) {
                    item.deletable = false;
                }

                // Item color
                if (colors && record.c) {
                    var itemColor = colors[record.c];
                    if (itemColor !== undefined) {
                        item.color = itemColor;
                    }
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
         * Delete a calendar item
         *
         * @param {object} item - the item (fullCalendar event object)
         * @param {function} callback - the callback to invoke upon success
         */
        _deleteItem: function(item, callback) {

            var resource = this.resources[item.source.id],
                data = {'id': item.id},
                el = $(this.element);

            this._sendItems(resource, {d: [data]}, function() {
                // Remove the item from the calendar
                el.fullCalendar('removeEvents', function(eventObj) {
                    return eventObj.source.id == item.source.id && eventObj.id == item.id;
                });
                // Remove the item from the cache
                resource._cache.deleteItem(item.id);
                if (typeof callback === 'function') {
                    callback();
                }
            });
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
