/**
 * Script to apply the jQuery DataTables plugin, implementing:
 *
 *   - server-side pagination including page caching (pipeline)
 *   - Ajax-reloading
 *   - filtering and sorting
 *   - configurable per-row actions
 *   - multi-selection of table rows for bulk-actions
 *   - simple grouping of rows with collapse/expand feature
 *
 * Server-side script in modules/s3/s3data.py.
 *
 * @copyright 2018-2019 (c) Sahana Software Foundation
 * @license MIT
 *
 * requires jQuery 1.9.1+
 * requires jQuery UI 1.10 widget factory
 *
 * Global variables/functions:
 *
 * - uses/applies:
 *
 *   - S3.datatables                   - global object for datatables configuration
 *   - S3.datatables.id                - global array of DOM-ids of data tables
 *   - S3.dataTables.initComplete      - global callback function (optional)
 *   - S3.dataTables.Actions           - global array of per-row actions
 *
 *   - $.searchDownloadS3              - provided by s3.filter.js, used for exports
 *   - S3.Utf8.decode                  - provided by S3.js
 *   - S3.addModals                    - provided by S3.js
 *
 * - provides:
 *
 *   - S3.dataTables.initDataTable     - not implemented, used by vulnerability TODO
 *   - S3.dataTables.accordionRow      - not implemented, used by vulnerability TODO
 */
(function($, undefined) {

    "use strict";

    var dataTableS3ID = 0;

    // ------------------------------------------------------------------------
    // HELPER FUNCTIONS

    /**
     * Array search function that allows implicit type coercion
     * (i.e. comparison with ==, unlike indexOf which uses ===)
     *
     * @param {mixed} item - the item to search for
     * @param {Array} arr - the array to search through
     *
     * @returns {integer} - the position of the item in the array,
     *                      or -1 if the item is not found
     */
    var inList = function(item, arr) {

        for (var i = 0, len = arr.length; i < len; i++) {
            if (item == arr[i]) {
                return i;
            }
        }
        return -1;
    };

    /**
     * Append a format extension and query string to a URL
     *
     * @param {string} url - the URL
     * @param {string} extension - the format extension (e.g. 'json')
     * @param {string} query - the query string (e.g. 'var=1&f=2')
     *
     * @returns {string} - a new URL
     */
    var appendUrlQuery = function(url, extension, query) {

        var parts = url.split('?');

        if (extension) {
            parts[0] += '.' + extension;
        }
        if (query) {
            if (parts.length > 1) {
                parts[1] += '&' + query;
            } else {
                parts.push(query);
            }
        }
        return parts.join('?');
    };

    /**
     * Update a URL with filter expressions from another URL, retaining
     * all non-filter query parts, used to update the permalink URL with
     * the latest Ajax-URL filters
     *
     * @param {string} target - the URL to update
     * @param {string} source - the URL containing the filter expressions
     *
     * @returns {string} - a new string with the updated URL
     */
    var updateUrlQuery = function(target, source) {

        var urlFilters = function(k) {
            return k.indexOf('.') != -1 || k[0] == '(';
        };
        var otherParams = function(k) {
            return !urlFilters(k) && k[0] != 'w';
        };

        var extractFrom = function(query, f) {
            return query && query.split('&').filter(function(item) {
                var q = item.split('=');
                return q.length > 1 && f(decodeURIComponent(q[0]));
            }) || [];
        };

        var tparts = target.split('?'),
            sparts = source.split('?'),
            urlVars = extractFrom(tparts[1], otherParams);

        tparts[1] = urlVars.concat(extractFrom(sparts[1], urlFilters)).join('&');

        return tparts.join('?');
    };

    // ------------------------------------------------------------------------
    // PIPELINE CACHE

    /**
     * Discontiguous Data Table Cache (DDTC)
     * - allows caching of discontiguous slices of a data set, thereby
     *   preventing server requests for a page outside of the last response
     */
    function DDTCache() {

        this.data = [];
        this.slices = [];

        this.availableRecords = -1;
    }

    /**
     * Store an array of records in the cache
     *
     * @param {integer} startIndex - the index of the first record
     * @param {Array} data - the array of records
     * @param {integer} availableRecords - total number of records in the set
     */
    DDTCache.prototype.store = function(startIndex, data, availableRecords) {

        if (availableRecords !== undefined) {
            this.availableRecords = availableRecords;
        }

        var dataLength = data.length;
        if (dataLength) {

            var cache = this.data,
                slices = this.slices;

            // Insert the records into the cache
            data.forEach(function(record, index) {
                cache[startIndex + index] = record;
            });

            // Remember the indices
            slices.push([startIndex, startIndex + dataLength]);

            // Sort and merge the index tuples
            slices.sort(function(x, y) {
                var diff = x[0] - y[0];
                if (diff !== 0) {
                    return diff;
                } else {
                    return x[1] - y[1];
                }
            });
            if (slices.length > 1) {
                var newSlices = [];
                var merged = slices.reduce(function(x, y) {
                    if (x[1] < y[0] || x[0] > y[1]) {
                        // Slices do not overlap
                        // => skip the first, continue with the second
                        newSlices.push(x);
                        return y;
                    } else {
                        // Slices overlap
                        // => merge them, continue with the merged slice
                        return [Math.min(x[0], y[0]), Math.max(x[1], y[1])];
                    }
                });
                newSlices.push(merged);
                this.slices = newSlices;
            }
        }

    };

    /**
     * Retrieve a slice of the cached data
     *
     * @param {integer} pageStart - the index of the first record to retrieve
     * @param {integer} pageLength - the number of records to retrieve
     *
     * @returns {Array|null} - the records as array, or null if any portion
     *                         of the slice is missing from the cache (and
     *                         must therefore be looked up from server)
     */
    DDTCache.prototype.retrieve = function(pageStart, pageLength) {

        var availableRecords = this.availableRecords;

        if (availableRecords < 0) {
            // We have not cached anything yet
            return null;
        }

        if (pageStart < 0) {
            pageStart = 0;
        }

        if (pageStart >= availableRecords) {
            // Attempt to read beyond last page
            return [];
        }

        var pageEnd = pageStart + pageLength;
        if (pageEnd > availableRecords) {
            pageEnd = availableRecords;
        }

        var slices = this.slices,
            slice,
            numSlices = slices.length;

        for (var i = 0; i < numSlices; i++) {
            slice = slices[i];
            if (pageStart >= slice[0] && pageEnd <= slice[1]) {
                return this.data.slice(pageStart, pageEnd);
            }
        }

        return null;
    };

    /**
     * Clear the cache
     */
    DDTCache.prototype.clear = function() {

        this.cache = [];
        this.slices = [];
        this.availableRecords = -1;
    };

    // ------------------------------------------------------------------------
    // UI WIDGET

    /**
     * dataTableS3
     */
    $.widget('s3.dataTableS3', {

        // --------------------------------------------------------------------
        // WIDGET METHODS

        /**
         * Default options
         *
         * @property {boolean} destroy - destroy any existing table matching
         *                               the selector and replace with the new
         *                               options
         * @property {boolean} deselectedIndicator - show the number of de-selected
         *                                           records in exclusion-mode (bulk-select)
         */
        options: {
            destroy: false,
            deselectedIndicator: false
        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = dataTableS3ID;
            dataTableS3ID += 1;

            this.eventNamespace = '.dataTableS3';
        },

        /**
         * Update the widget options
         */
        _init: function() {

            var el = $(this.element),
                tableID = el.attr('id');

            this.tableID = tableID;
            this.selector = '#' + tableID;

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

            // Parse the table config
            var tableConfig = this._parseConfig();
            if (tableConfig === undefined) {
                // No table config found => abort
                return;
            }

            // Initialize pagination
            var serverSide = true,
                processing = true,
                fnAjax = null;
            // FIXME Why is this a string and not a boolean? (It's JSON anyway)
            if (tableConfig.pagination == 'true') {
                // Server-side Pagination
                this.ajaxUrl = tableConfig.ajaxUrl;
                fnAjax = this._pipeline({cache: this._initCache()});
            } else {
                // Client-side Pagination
                serverSide = false;
                processing = false;
            }

            // Render bulk-actions
            this._renderBulkActions();

            // Initialize dataTable
            el.dataTable({
                'ajax': fnAjax,
                'autoWidth': false,
                'columns': this.columnConfigs,
                'deferRender': true,
                'destroy': opts.destroy,
                'dom': tableConfig.dom,
                'lengthMenu': tableConfig.lengthMenu,
                'order': tableConfig.order,
                'orderFixed': tableConfig.group,
                'ordering': true,
                'pageLength': tableConfig.pageLength,
                'pagingType': tableConfig.pagingType,
                'processing': processing,
                'searchDelay': 450,
                // FIXME Why is this a string and not a boolean:
                'searching': tableConfig.searching == 'true',
                'serverSide': serverSide,
                'search': {
                    // Workaround for dataTables bug:
                    // - smart search crashing with empty search string
                    'smart': serverSide
                },
                'language': {
                    'aria': {
                        'sortAscending': ': ' + i18n.sortAscending,
                        'sortDescending': ': ' + i18n.sortDescending
                    },
                    'paginate': {
                        'first': i18n.first,
                        'last': i18n.last,
                        'next': i18n.next,
                        'previous': i18n.previous
                    },
                    'emptyTable': i18n.emptyTable,
                    'info': i18n.info,
                    'infoEmpty': i18n.infoEmpty,
                    'infoFiltered': i18n.infoFiltered,
                    'infoThousands': i18n.infoThousands,
                    'lengthMenu': i18n.lengthMenu,
                    'loadingRecords': i18n.loadingRecords + '...',
                    'processing': i18n.processing + '...',
                    'search': i18n.search + ':',
                    'zeroRecords': i18n.zeroRecords
                },

                // Currently unused:
                //'headerCallback': this._headerCallback(),
                'rowCallback': this._rowCallback(),
                'drawCallback': this._drawCallback(),

                // Custom initComplete
                // - can e.g. be used to reposition elements like export_formats
                'initComplete': S3.dataTables.initComplete
            });

            this._bindEvents();
        },

        /**
         * Parse the table configuration JSON from hidden field (#*_configurations)
         *
         * @returns {object} - the table configuration
         */
        _parseConfig: function() {

            var el = $(this.element),
                config = $(this.selector + '_configurations');

            if (!config.length) {
                return;
            }

            // Parse and store the table config
            var tableConfig = $.parseJSON(config.val());
            this.tableConfig = tableConfig;

            // Apply actions fallback
            if (!tableConfig.rowActions.length) {
                tableConfig.rowActionsJSON = false;
                if (S3.dataTables.Actions) {
                    tableConfig.rowActions = S3.dataTables.Actions;
                } else {
                    tableConfig.rowActions = [];
                }
            } else {
                // This is the standard
                tableConfig.rowActionsJSON = true;
            }

            // Configure columns
            var columnConfig = [],
                numCols = $('thead tr', el).children().length;
            for (var i = 0; i < numCols; i++) {
                columnConfig[i] = null;
            }
            if (tableConfig.rowActions.length > 0) {
                columnConfig[tableConfig.actionCol] = {
                    'sTitle': ' ',
                    'bSortable': false
                };
            }
            if (tableConfig.bulkActions) {
                columnConfig[tableConfig.bulkCol] = {
                    'sTitle': '<div class="bulk-select-options"><input class="bulk-select-all" type="checkbox">' + i18n.selectAll + '</input></div>',
                    'bSortable': false
                };
            }
            if (tableConfig.colWidths) {
                var col,
                    _colWidths = tableConfig.colWidths;
                for (col in _colWidths) {
                    if (columnConfig[col] != null) {
                        columnConfig[col].sWidth = _colWidths[col];
                    } else {
                        columnConfig[col] = {
                            'sWidth': _colWidths[col]
                        };
                    }
                }
            }
            this.columnConfigs = columnConfig;

            return tableConfig;
        },

        // --------------------------------------------------------------------
        // PIPELINE

        /**
         * Get the pipelines function to Ajax-load data from server, called
         * during refresh to configure the "ajax" option of the dataTable
         * instance
         *
         * @param {object} opts - the pipeline options
         */
        _pipeline: function(opts) {

            // Configuration options
            var conf = $.extend( {
                cache: {},    // S3 Extension: Allow passing in initial cache
                pages: 2,     // number of pages to cache
                //url: '',    // script url
                data: null,   // function or object with parameters to send to the server
                              // matching how `ajax.data` works in DataTables
                method: 'GET' // Ajax HTTP method
            }, opts );

            // Private variables for handling the cache
            var cache = conf.cache,
                cacheLastRequest = cache.cacheLastRequest || null,
                cacheLastJson = cache.cacheLastJson || null,
                cacheUpper = cache.cacheUpper || null,
                cacheLower = cache.cacheLower;

            if (cacheLower === undefined) {
                cacheLower = -1;
            }

            // Initialize cache
            var cacheCombined = new DDTCache();
            if (cacheLastJson && cacheLower != -1) {
                var availableRecords = cacheLastJson.recordsFiltered ||
                                       cacheLastJson.recordsTotal;
                cacheCombined.store(cacheLower, cacheLastJson.data, availableRecords);
            }

            /**
             * Pipelining function for DataTables. To be used for the `ajax` option
             * of DataTables, original version from:
             * - http://datatables.net/examples/server_side/pipeline.html
             */
            var self = this;
            return function(request, drawCallback, settings) {

                if (this.hasOwnProperty('nTable')) {
                    // We have been called by reloadAjax()

                    var sAjaxSource = settings.sAjaxSource;
                    if (sAjaxSource) {
                        // Update Ajax URL, and clear sAjaxSource to not
                        // override the ajax-setting for the actual reload:
                        self.ajaxUrl = sAjaxSource;
                        settings.sAjaxSource = null;
                    }

                    // Clear cache to enforce reload
                    cacheLastJson = null;
                    cacheLastRequest = null;
                    cacheLower = -1;
                    cacheUpper = null;
                    cacheCombined.clear();

                    drawCallback({}); // calls the inner function of reloadAjax

                    // Can just return here, because draw() inside drawCallback
                    // has already triggered the regular pipeline refresh
                    return;
                }

                var ajax          = false,
                    requestStart  = request.start,
                    drawStart     = request.start,
                    requestLength = request.length,
                    cached;

                // Determine total and available records
                var totalRecords = request.recordsTotal,
                    availableRecords = totalRecords;
                if (cacheLastJson) {
                    if (cacheLastJson.recordsTotal !== undefined) {
                        totalRecords = cacheLastJson.recordsTotal;
                    }
                    if (cacheLastJson.recordsFiltered !== undefined) {
                        availableRecords = cacheLastJson.recordsFiltered;
                    } else {
                        availableRecords = totalRecords;
                    }
                }

                // Make the totalRecords visible to other functions
                self.totalRecords = totalRecords;

                if (requestLength == -1) {
                    // Showing all records
                    requestStart = 0;
                    if (availableRecords !== undefined) {
                        requestLength = availableRecords;
                    } else {
                        // Total number of records is unknown and hence not
                        // all records cached either => need server in any case
                        ajax = true;
                    }
                }

                if (!ajax) {
                    var requestEnd = requestStart + requestLength;

                    if (settings.clearCache) {
                        // API requested that the cache be cleared
                        cacheCombined.clear();
                        settings.clearCache = false;
                        ajax = true;

                    } else if (cacheLastRequest &&
                               (JSON.stringify(request.order)   !== JSON.stringify(cacheLastRequest.order) ||
                                JSON.stringify(request.columns) !== JSON.stringify(cacheLastRequest.columns) ||
                                JSON.stringify(request.search)  !== JSON.stringify(cacheLastRequest.search))) {
                        // Properties changed (ordering, columns, searching)
                        cacheCombined.clear();
                        ajax = true;

                    } else {
                        // Try retrieving from cache
                        cached = cacheCombined.retrieve(requestStart, requestEnd - requestStart);
                        if (cached === null) {
                            ajax = true;
                        }
                    }
                }

                // Store the request for checking next time around
                cacheLastRequest = $.extend(true, {}, request);

                if (ajax) {
                    // Need data from the server
                    if (requestStart < cacheLower) {
                        requestStart = requestStart - (requestLength * (conf.pages - 1));
                        if (requestStart < 0) {
                            requestStart = 0;
                        }
                    }
                    cacheLower = requestStart;
                    if (request.length != -1) {
                        cacheUpper = requestStart + (requestLength * conf.pages);
                    } else {
                        cacheUpper = requestLength;
                    }

                    request.start = requestStart;
                    request.length = requestLength * conf.pages;

                    // Provide the same `data` options as DataTables.
                    if ($.isFunction(conf.data)) {
                        // As a function it is executed with the data object as an arg
                        // for manipulation. If an object is returned, it is used as the
                        // data object to submit
                        var d = conf.data(request);
                        if (d) {
                            $.extend(request, d);
                        }
                    }
                    else if ($.isPlainObject(conf.data)) {
                        // As an object, the data given extends the default
                        $.extend(request, conf.data);
                    }

                    // Send a minimal URL query with old-style vars
                    var limit;
                    if (requestLength == -1) {
                        // Load all records
                        limit = 'none';
                    } else {
                        limit = request.length;
                    }
                    var sendData = [{'name': 'draw',
                                     'value': request.draw
                                     },
                                    {'name': 'limit',
                                     'value': limit
                                     }
                                    ];
                    if (requestStart != 0) {
                        sendData.push({'name': 'start',
                                       'value': requestStart
                                       });
                    }
                    if (request.search && request.search.value) {
                        sendData.push({'name': 'sSearch',
                                       'value': request.search.value
                                       });
                        sendData.push({'name': 'iColumns',
                                       'value': request.columns.length
                                       });
                    }
                    var order_len = request.order.length;
                    if (order_len) {
                        // Number of sorting columns
                        sendData.push({'name': 'iSortingCols',
                                       'value': order_len
                                       });
                        var columnConfigs = self.columnConfigs,
                            columnConfig,
                            ordering,
                            i;
                        // Declare non-sortable columns (required by server to interpret
                        // column indices correctly)
                        for (i = 0; i < columnConfigs.length; i++) {
                            columnConfig = columnConfigs[i];
                            if (columnConfig && !columnConfig.bSortable) {
                                sendData.push({'name': 'bSortable_' + i,
                                               'value': 'false'
                                               });
                            }
                        }
                        // Declare sort-column indices and sorting directions
                        for (i = 0; i < order_len; i++) {
                            ordering = request.order[i];
                            sendData.push({'name': 'iSortCol_' + i,
                                           'value': ordering.column
                                           });
                            sendData.push({'name': 'sSortDir_' + i,
                                           'value': ordering.dir
                                           });
                        }
                    }

                    // Use $.searchS3 if filter framework is available,
                    // otherwise (e.g. custom page without s3.filter.js)
                    // fall back to $.ajaxS3
                    var ajaxMethod = $.ajaxS3;
                    if ($.searchS3 !== undefined) {
                        ajaxMethod = $.searchS3;
                    }

                    settings.jqXHR = ajaxMethod({
                        'type':     conf.method,
                        'url':      self.ajaxUrl,
                        'data':     sendData,
                        'dataType': 'json',
                        'cache':    false,
                        'success':  function(json) {

                            // Store the data in the cache
                            var cacheEnd = self.totalRecords;
                            if (json.recordsFiltered !== undefined) {
                                // This could be smaller than totalRecords
                                cacheEnd = json.recordsFiltered;
                            }
                            cacheCombined.store(requestStart, json.data, cacheEnd);

                            // Keep the server response as basis for subsequent cache responses
                            cacheLastJson = $.extend(true, {}, json);

                            // Update cacheUpper with the actual number of records returned
                            cacheUpper = requestStart + json.data.length;

                            if (requestStart != drawStart) {
                                // Remove the records up to the start of the
                                // current page from JSON
                                json.data.splice(0, drawStart - requestStart);
                            }
                            if (requestLength != -1) {
                                // Not showing all records: remove all records behind
                                // the end of the current page
                                json.data.splice(requestLength, json.data.length);
                            }

                            drawCallback(json);
                        }
                    });

                } else {
                    // Re-use cacheLastJson with updated draw and data
                    var json = $.extend(true, {}, cacheLastJson, {draw: request.draw});
                    json.data = cached;
                    drawCallback(json);
                }
            };
        },

        /**
         * Read the initial cache contents (JSON) from hidden field (#*_dataTable_cache)
         *
         * @returns {object} - the initial cache to pass to the pipeline in refresh()
         */
        _initCache: function() {

            var initial = $(this.selector + '_dataTable_cache'),
                cache;

            if (initial.length > 0) {
                cache = JSON.parse(initial.val());
            } else {
                cache = {};
            }

            this.pipelineCache = cache;
            return cache;
        },

        // --------------------------------------------------------------------
        // DATATABLE CALLBACKS

        /**
         * Get the header callback function
         */
        _headerCallback: function() {

            // Currently unused
            //return function (/* nHead, aasData, iStart, iEnd, aiDisplay */) {
            //
            //};
        },

        /**
         * Get the row callback function
         */
        _rowCallback: function() {

            var self = this;

            /**
             * Callback function per row
             *
             * @param {jQuery} nRow - the row, jQuery-enhanced DOM node of the [tr] element
             * @param {Array} aData - the contents of the columns in this row
             */
            return function(nRow, aData /* , iDisplayIndex */) {

                var tableConfig = self.tableConfig,
                    actionCol = tableConfig.actionCol;

                // Determine the record ID of the row
                var result = />(.*)</i.exec(aData[actionCol]),
                    recordId;
                if (result === null) {
                    recordId = aData[actionCol];
                } else {
                    recordId = result[1];
                }

                // Render action buttons
                var rowActions = tableConfig.rowActions;
                if (rowActions.length || tableConfig.bulkActions) {

                    // Render the action buttons
                    var buttons = [];
                    for (var i=0; i < rowActions.length; i++) {
                        buttons.push(self._renderActionButton(recordId, rowActions[i]));
                    }
                    // Put the actions buttons in the actionCol
                    //if ((tableConfig.group.length) && (tableConfig.group[0][0] < actionCol)) {
                    //    actionCol -= 1;
                    //}
                    $('td:eq(' + actionCol + ')', nRow).addClass('actions').html(buttons.join(''));
                }

                // Mark selected rows
                if (tableConfig.bulkActions) {
                    self._bulkSelect(nRow, inList(recordId, self.selectedRows));
                }

                // Add per-row CSS classes
                var styles = tableConfig.rowStyles;
                if (styles.length) {
                    var row = $(nRow);
                    for (var style in styles) {
                        if (inList(recordId, styles[style]) != -1) {
                            row.addClass(style);
                        }
                    }
                }

                // Truncate cell contents exceeding configured limits
                self._truncateCellContents(nRow, aData);

                return nRow;
            };
        },

        /**
         * Get the draw callback function
         */
        _drawCallback: function() {

            var self = this;

            /**
             * Callback function per draw
             *
             * @param {object} oSettings - the dataTable table info object
             */
            return function(oSettings) {

                var el = $(self.element),
                    selector = self.selector,
                    wrapper = el.closest('.dt-wrapper');

                // Update permalink
                var ajaxSource = self.ajaxUrl;
                if (ajaxSource) {
                    wrapper.find('a.permalink').each(function() {
                        var $this = $(this);
                        $this.attr('href', updateUrlQuery($this.attr('href'), ajaxSource));
                    });
                }

                var numrows = oSettings.fnRecordsDisplay();

                // Hide/show pagination controls depending on number of pages
                if (Math.ceil(numrows / oSettings._iDisplayLength) > 1)  {
                    $(selector + '_paginate').show();
                } else {
                    // Single page, so hide them
                    $(selector + '_paginate').hide();
                }

                // Show/hide export options depending on whether there are data in the table
                if (numrows === 0) {
                    // Hide the export options (table is empty)
                    wrapper.find('.dt-export-options').hide();
                } else {
                    // Show the export options (table has data)
                    wrapper.find('.dt-export-options').show();
                }

                // Add modals if necessary
                // - in future maybe use S3.redraw() to catch all elements
                if ($(selector + ' .s3_modal').length) {
                    S3.addModals();
                }

                // Toggle empty section if present (e.g. S3Profile, homepages in certain templates)
                var container = el.closest('.dt-contents');
                if (container.length) {
                    if (numrows > 0) {
                        // Show table, hide empty section
                        container.find('.empty').hide().siblings('.dt-wrapper').show();
                    } else {
                        // Hide table, show empty section
                        container.find('.empty').show().siblings('.dt-wrapper').hide();
                    }
                }

                // Grouped Rows
                // - configured as array of [[groupingColumnIndex, 'asc'|'desc'], ...]
                var tableConfig = self.tableConfig,
                    groups = tableConfig.group;
                if (groups.length) {

                    // Array of preceding grouping column indices, used to
                    // construct a key for groupTotals
                    var prefixID = [];

                    // Insert the header rows for all groups
                    tableConfig.group.forEach(function(group, i) {
                        var groupTotals = tableConfig.groupTotals[i] || {},
                            groupTitles = tableConfig.groupTitles[i] || [];
                        self._renderGroups(oSettings, group[0], groupTitles, groupTotals, prefixID, i + 1);
                        prefixID.push(group[0]);
                    });

                    // Collapse all groups initially
                    if (tableConfig.shrinkGroupedRows) {
                        var levelID,
                            groupID;
                        $('tbody tr', el).each(function() {
                            var row = $(this);
                            if (row.hasClass('group')) {
                                levelID = row.data('level');
                                groupID = row.data('group');
                            } else if (levelID && groupID && !row.hasClass('spacer')) {
                                row.addClass('xgroup_' + levelID + '_' + groupID)
                                   .addClass('collapsable');
                            }
                        });
                        $('.collapsable').hide();
                   }
                }

                // Activate or refresh doubleScroll if required
                self.doubleScroll();

            };
        },

        // --------------------------------------------------------------------
        // CELL CONTENTS HELPERS

        /**
         * Render an action button (used by rowCallback)
         *
         * @param {integer|string} recordId - the record ID of the row, used to construct URLs
         * @param {object} action - the action configuration:
         * @property {Array} action.restrict - Render the button only for these record IDs
         * @property {Array} action.exclude - Do not render the action button for these record IDs
         * @property {string} action._class - the CSS class to use for the button
         * @property {string} action.label - the label for the button
         * @property {string} action.icon - the CSS class for the icon to be placed on the button
         * @property {string} action.url - alternative to icon, render this image on the button
         * @property {boolean} action._disabled - disable the button initially
         * @property {string} action.url - render the button as hyperlink to this URL
         * @property {string} action.onclick - alternatively, on-click script for the button
         * @property {string} action._ajaxURL - if neither url nor onclick, render this ajaxURL
         *                                      as data-url attribute for use by external scripts
         *                                      (mandatory for Ajax-delete with dt-ajax-delete class)
         *
         * @returns {string} - the action button HTML
         */
        _renderActionButton: function(recordId, action) {

            var button = '';

            // Check if action is restricted to a subset of records
            var restrict = action.restrict;
            if (restrict && restrict.constructor === Array && restrict.indexOf(recordId) == -1) {
                return button;
            }
            var exclude = action.exclude;
            if (exclude && exclude.constructor === Array && exclude.indexOf(recordId) != -1) {
                return button;
            }

            var c = action._class;

            // Construct button label and on-hover title
            var label = action.label;
            if (!this.tableConfig.rowActionsJSON && this.tableConfig.utf8) {
               label = S3.Utf8.decode(action.label);
            }
            var title = action._title || label;

            // Display the button as icon or image?
            if (action.icon) {
                label = '<i class="' + action.icon + '" alt="' + label + '"> </i>';
            } else if (action.img) {
                label = '<img src="' + action.icon + '" alt="' + label + '"></img>';
            }

            // Disabled button?
            var disabled;
            if (action._disabled) {
                disabled = ' disabled="disabled"';
            } else {
                disabled = '';
            }

            var re = /%5Bid%5D/g;
            if (action._onclick) {
                // Onclick-script
                var oc = action._onclick.replace(re, recordId);
                button = '<a class="' + c + '" onclick="' + oc + disabled + '">' + label + '</a>';

            } else if (action.url) {
                // Hyperlink
                var url = action.url.replace(re, recordId),
                    target = action._target || '';
                if (target) {
                    target = ' target="' + target + '"';
                }
                button = '<a db_id="'+ recordId + '" class="' + c + '" href="' + url + '" title="' + title + '"' + target + disabled + '>' + label + '</a>';

            } else {
                // External click-event handler
                var ajaxURL = action._ajaxurl || '';
                if (ajaxURL) {
                    ajaxURL = ' data-url="' + ajaxURL + '"';
                }
                button = '<a db_id="'+ recordId + '" class="' + c + '" title="' + title + '"' + ajaxURL + disabled + '>' + label + '</a>';
            }

            return button;
        },

        /**
         * Generic click-event handler for Ajax action buttons that need to interact
         * with the server:
         *
         *  - asks the user to confirm the intended action (optional)
         *  - sends a POST request to the configured Ajax-URL (replacing [id] placeholder)
         *  - reloads the table if the POST request succeeds
         *
         * @param {string} confirmation - the confirmation question to ask (optional)
         *
         * Used internally for Ajax-delete buttons (.dt-ajax-delete), but can
         * also be configured for other button classes by external scripts like:
         *
         *      var dt = $('#datatable-id');
         *      dt.on('click', '.button-class', dt.dataTableS3('ajaxAction', 'Are you sure?'));
         */
        ajaxAction: function(confirmation) {

            var el = $(this.element);

            return function(event) {

                event.stopPropagation();
                event.preventDefault();

                if (!confirmation || confirm(confirmation)) {
                    var $this = $(this),
                        recordID = $this.attr('db_id'),
                        ajaxURL = $this.data('url'),
                        data = {},
                        formKey = el.closest('.dt-wrapper').find('input[name="_formkey"]').first().val();

                    if (formKey !== undefined) {
                        data._formkey = formKey;
                    }

                    if (ajaxURL && recordID) {
                        $.ajaxS3({
                            'url': ajaxURL.replace(/%5Bid%5D/g, recordID),
                            'type': 'POST',
                            'dataType': 'json',
                            'data': data,
                            'success': function(/* data */) {
                                el.dataTable().fnReloadAjax();
                            }
                        });
                    }
                }
            };
        },

        /**
         * Render a truncated version of any cell contents that exceeds the
         * configured maximum text length, as well as controls to expand/collapse
         *
         * @param {jQuery} row - the table row
         * @param {Array} data - the row data
         */
        _truncateCellContents: function(row, data) {

            var tableConfig = this.tableConfig,
                maxLength = tableConfig.textMaxLength,
                shrinkLength = tableConfig.textShrinkLength,
                groups = tableConfig.group.map(function(group) { return group[0]; }),
                colIdx = 0;

            for (var i = 0; i < data.length; i++) {

                // Ignore any columns used for groups
                if ($.inArray(i, groups) != -1) {
                    continue;
                }

                // Truncate contents exceeding maxLength (unless it contains markup)
                var str = data[i];
                if (str.length > maxLength && !str.match(/<.*>/)) {
                    var disp = '<div class="dt-truncate"><span class="ui-icon ui-icon-zoomin" style="float:right"></span>'+ str.substr(0, shrinkLength) + "&hellip;</div>",
                        full = '<div  style="display:none" class="dt-truncate"><span class="ui-icon ui-icon-zoomout" style="float:right"></span>' + str + "</div>";
                    $('td:eq(' + colIdx + ')', row).html(disp + full);
                }
                colIdx++;
            }
        },

        /**
         * Activate or refresh doubleScroll for the table container
         *
         * NB this function must be called again whenever the actual width
         * property of the table changes, e.g.:
         *
         * - after reloading table contents (drawCallback)
         * - after un-hiding a hidden data table (e.g. summary tabs)
         * - ...
         *
         * It can therefore be called from the outside like:
         *
         *      $('#tableID').dataTableS3('doubleScroll');
         */
        doubleScroll: function() {

            var el = $(this.element);

            if (el.hasClass('doublescroll') && !el.hasClass('responsive')) {
                try {
                    el.closest('.dataTable_table').doubleScroll({
                        contentElement: el,
                        resetOnWindowResize: true
                    });
                } catch(e) {
                    console.log('dataTableS3: doubleScroll not available');
                }
            }

        },

        // --------------------------------------------------------------------
        // BULK ACTION METHODS

        /**
         * Render the bulk action controls (action buttons) and determine
         * previously selected rows and selection mode
         */
        _renderBulkActions: function() {

            var tableConfig = this.tableConfig,
                bulkActions = tableConfig.bulkActions;

            if (bulkActions) {

                // Generate submit-buttons for bulk-actions
                var bulkActionControls = $('<div class="dataTable-action">');
                bulkActions.forEach(function(bulkAction) {

                    var name,
                        value,
                        cls;

                    if (bulkAction.constructor === Array) {
                        value = bulkAction[0];
                        name = bulkAction[1];
                        if (bulkAction.length > 2) {
                            cls = bulkAction[2];
                        }
                    } else {
                        name = bulkAction;
                        value = bulkAction;
                    }

                    var bulkActionSubmit = $('<input type="submit" class="selected-action">').attr({
                        id: name + '-selected-action',
                        name: name,
                        value: value
                    }).appendTo(bulkActionControls);

                    if (cls) {
                        bulkActionSubmit.addClass(cls);
                    }
                });
                this.bulkActionControls = bulkActionControls;

                // Determine which rows had been selected previously
                var selected = JSON.parse($(this.selector + '_dataTable_bulkSelection').val());
                if (selected === null) {
                    selected = [];
                }
                this.selectedRows = selected;

                // Determine selection mode
                if ($(this.selector + '_dataTable_bulkSelectAll').val()) {
                    this.selectionMode = 'Exclusive';
                } else {
                    this.selectionMode = 'Inclusive';
                }
            }
        },

        /**
         * Manage selection/de-selection of a row for bulk-actions
         *
         * @param {jQuery} row - the row to select/deselect
         * @param {integer} index - the index of the clicked row in the
         *                          currently selected rows
         */
        _bulkSelect: function(row, index) {

            var el = $(this.element),
                tableConfig = this.tableConfig,
                numSelected = this.selectedRows.length,
                totalRecords = this.totalRecords;

            // Elements
            var bulkSelectOptions = $('.bulk-select-options', el),  // mandatory layout element
                selectAll = $('.bulk-select-all', el),              // mandatory layout element
                deselected = $('.bulk-deselected', el),             // dynamically added
                totalAvailable = $('.bulk-total-available', el),    // optional layout element
                totalSelected = $('.bulk-total-selected', el),      // optional layout element
                selectedIndicator = totalAvailable.length && totalAvailable.length;

            if (this.selectionMode == 'Inclusive') {

                if (selectedIndicator) {
                    totalSelected.text(numSelected);
                    totalAvailable.text(totalRecords);
                } else {
                    deselected.remove();
                }
                var bulkSingle = tableConfig.bulkSingle;
                if (index == -1) {
                    // Row is not currently selected
                    $(row).removeClass('row_selected');
                    $('.bulkcheckbox', row).prop('checked', false);
                } else {
                    // Row is currently selected
                    if (bulkSingle) {
                        // Deselect all other rows
                        $(row).closest('table').find('tr').removeClass('row_selected')
                                               .find('.bulkcheckbox').prop('checked', false);
                    }
                    $(row).addClass('row_selected');
                    $('.bulkcheckbox', row).prop('checked', true);

                }
                if (!bulkSingle && (numSelected == totalRecords)) {
                    // All rows have been selected => switch to exclusive mode
                    selectAll.prop('checked', true);
                    this.selectionMode = 'Exclusive';
                    this.selectedRows = [];
                }

            } else {

                if (selectedIndicator) {
                    totalSelected.text(parseInt(totalAvailable.text(), 10) - numSelected);
                    totalAvailable.text(totalRecords);
                } else {
                    if (!numSelected || numSelected == totalRecords) {
                        deselected.remove();
                    } else {
                        if (!deselected.length && this.options.deselectedIndicator) {
                            deselected = $('<span class="bulk-deselected">').appendTo(bulkSelectOptions);
                        }
                        deselected.html('[-' + numSelected + ']');
                    }
                }

                if (index == -1) {
                    // Row is currently selected
                    $(row).addClass('row_selected');
                    $('.bulkcheckbox', row).prop('checked', true);
                } else {
                    // Row is not currently selected
                    $(row).removeClass('row_selected');
                    $('.bulkcheckbox', row).prop('checked', false);
                }

                if (numSelected == totalRecords) {
                    // All rows have been de-selected => switch to inclusive mode
                    selectAll.prop('checked', false);
                    this.selectionMode = 'Inclusive';
                    this.selectedRows = [];
                }
            }

            if (tableConfig.bulkActions) {

                // Store select mode and (de-)selected rows in hidden form fields
                $(this.selector + '_dataTable_bulkMode').val(this.selectionMode);
                $(this.selector + '_dataTable_bulkSelection').val(this.selectedRows.join(','));

                // Add the bulk action controls
                this.bulkActionControls.insertBefore(bulkSelectOptions);

                // Activate bulk actions?
                var numActive = this.selectedRows.length;
                if (this.selectionMode == 'Exclusive') {
                    numActive = totalRecords - numActive;
                }
                $('.selected-action', el).prop('disabled', numActive == 0);
                $('.pair-action', el).prop('disabled', numActive != 2);
            }
        },

        /**
         * Click-event handler for the select-checkbox per row
         */
        _bulkSelectRow: function() {

            var self = this;

            return function(/* event */) {

                var $this = $(this),
                    id = $this.data('dbid'),
                    rows = self.selectedRows;

                var posn = inList(id, rows);
                if (posn == -1) {
                    if (self.tableConfig.bulkSingle){
                        self.selectedRows = [id];
                    } else {
                        rows.push(id);
                    }
                    posn = 0; // toggle selection class
                } else {
                    rows.splice(posn, 1);
                    posn = -1; // toggle selection class
                }
                self._bulkSelect($this.closest('tr'), posn);
            };
        },

        /**
         * Click-event handler for the Select-all checkbox
         */
        _bulkSelectAll: function() {

            var el = $(this.element),
                self = this;

            return function(/* event */) {

                self.selectedRows = [];
                if ($(this).prop('checked')) {
                    self.selectionMode = 'Exclusive';
                } else {
                    self.selectionMode = 'Inclusive';
                }
                // Trigger row-callback for all rows
                el.dataTable().api().draw(false);
            };
        },

        // --------------------------------------------------------------------
        // GROUPED ROWS

        /**
         * Group the rows in the current table (by inserting group headers)
         *
         * @param {object} oSettings - the dataTable settings
         * @param {integer} groupColumn - the index of the colum that will be grouped
         * @param {Array} groupTitles - the group titles
         * @param {Array} groupTotals - (optional) the totals to be used for each group
         * @param {Array} prefixID - indices of columns to use to construct
         *                           the group totals access key
         * @param {integer} level - the level of this group, starting at 1
         */
        _renderGroups: function(oSettings,
                                groupColumn,
                                groupTitles,
                                groupTotals,
                                prefixID,
                                level) {

            var iColspan = oSettings.aoColumns.length,
                parentGroup,
                el = $(this.element),
                tableRows = $('tbody tr', el),
                row,
                rowData,
                value,
                prevValue,
                title,
                group = 1,         // The number of group headers added
                dataCnt = 0,       // The number of data rows processed
                groupTitleCnt = 0, // The index of the next group title
                groupPrefix = '';  // the access key for the groupTotals

            for (var i = 0; i < tableRows.length; i++) {

                row = $(tableRows[i]);

                if (row.hasClass('spacer')) {
                    // A spacer row that has been inserted at a higher level => skip
                    continue;
                }

                rowData = oSettings.aoData[oSettings.aiDisplay[dataCnt]]._aData;

                if (row.hasClass('group')) {
                    // A group header row of a higher level
                    prevValue = undefined;
                    parentGroup = row.data('group');
                    groupPrefix = prefixID.map(function(idx) {
                        return this[idx];
                    }, rowData).join('_');
                    continue;
                }

                // A data row
                value = rowData[groupColumn];
                if (value !== prevValue) {

                    // With custom groupTitles, insert empty group headers for all preceding titles
                    while (groupTitles.length > groupTitleCnt && value != groupTitles[groupTitleCnt][0]) {
                        title = groupTitles[groupTitleCnt][1];
                        this._insertGroupHeader(row,
                                                title,
                                                level,
                                                group,
                                                parentGroup,
                                                iColspan,
                                                groupTotals,
                                                groupPrefix);
                        groupTitleCnt++;
                        group++;
                    }

                    // Start a new group
                    if (groupTitles.length > groupTitleCnt) {
                        // We shall use a custom group title
                        title = groupTitles[groupTitleCnt][1];
                        groupTitleCnt++;
                    } else {
                        // We use the value of the grouping column as group title
                        title = value;
                    }
                    this._insertGroupHeader(row,
                                            title,
                                            level,
                                            group,
                                            parentGroup,
                                            iColspan,
                                            groupTotals,
                                            groupPrefix,
                                            true);
                    group++;
                    prevValue = value;

                }
                dataCnt += 1;

                if (this.tableConfig.shrinkGroupedRows) {
                    // Hide the detail row
                    row.hide();
                }
            }

            // With custom groupTitles, insert empty group headers for all remaining titles
            row = tableRows[tableRows.length-1];
            while (groupTitles.length > groupTitleCnt) {
                title = groupTitles[groupTitleCnt][1];
                this._insertGroupHeader(row,
                                        title,
                                        level,
                                        group,
                                        parentGroup,
                                        iColspan,
                                        groupTotals,
                                        groupPrefix,
                                        false,
                                        true);
                groupTitleCnt++;
                group++;
            }
        },

        /**
         * Insert a group header before (or after) a data row; DRY utility function
         * used by _renderGroups()
         *
         * @param {jQuery} row - the data row
         * @param {string} groupTitle - the title to use for the group header
         * @param {integer} level - the grouping level (counting from 1)
         * @param {integer} group - index of the group within the level (counting from 1)
         * @param {integer} parentGroup - index of the parent group within the previous level
         * @param {integer} iColspan - number of columns in the table (=colspan of the header)
         * @param {object} groupTotals - dict of group totals
         * @param {string} groupPrefix - prefix for the access key for the group totals
         * @param {boolean} addIcons - add collapse/expand icons to the header
         * @param {boolean} append - insert the header after the row rather than before it;
         *                           used to add additional groups at the end for which there
         *                           are no data rows
         */
        _insertGroupHeader: function(row,
                                     groupTitle,
                                     level,
                                     group,
                                     parentGroup,
                                     iColspan,
                                     groupTotals,
                                     groupPrefix,
                                     addIcons,
                                     append) {

            var tableConfig = this.tableConfig;

            // Create the group header row
            var nGroup = $('<tr class="group">').data({level: '' + level, group: '' + group})
                                                .addClass('level_' + level);

            // Add parent level and group (if any)
            var collapsable = tableConfig.shrinkGroupedRows;

            if (parentGroup) {
                var parentLevel = '' + (level - 1);
                nGroup.addClass('xgroup_' + parentLevel + '_' + parentGroup)
                      .data({parentLevel: parentLevel, parentGroup: parentGroup});
                if (collapsable) {
                    nGroup.addClass('collapsable');
                }
            }

            // Create a full-width cell
            var nCell = $('<td>').attr('colspan', iColspan).appendTo(nGroup);

            // Add an indentation of the grouping depth
            for (var lvl=1; lvl < level; lvl++) {
                $('<span class="group-indent">').appendTo(nCell);
            }

            // Add open/closed indicators
            if (level > 1) {
                $('<span class="ui-icon ui-icon-triangle-1-e group-closed">').appendTo(nCell);
                $('<span class="ui-icon ui-icon-triangle-1-s group-opened">').hide().appendTo(nCell);
            }

            // Add the subtotal counts (if provided)
            var groupCount = '';
            // Not !== as we want to catch undefined as well as null
            if (groupTotals[groupTitle] != null) {
                groupCount = ' (' + groupTotals[groupTitle] + ')';
            } else {
                var index = groupPrefix + groupTitle;
                if (groupTotals[index] != null) {
                    groupCount = ' (' + groupTotals[index] + ')';
                }
            }

            // Construct the group header text
            nCell.append(groupTitle + groupCount);

            // Add open/close-icons (arrows on the right)
            if (collapsable && addIcons) {

                var expandIcons = tableConfig.groupIcon,
                    expandIconType;
                if (expandIcons.length >= level) {
                    expandIconType = expandIcons[level - 1];
                } else {
                    expandIconType = 'icon';
                }

                var expandIcon = $('<span class="group-expand">').appendTo(nCell),
                    collapseIcon = $('<span class="group-collapse">').hide().appendTo(nCell);

                if (expandIconType == 'text') {
                    expandIcon.text('→');
                    collapseIcon.text('↓');
                } else if (expandIconType == 'icon') {
                    expandIcon.addClass('ui-icon ui-icon-arrowthick-1-e');
                    collapseIcon.addClass('ui-icon ui-icon-arrowthick-1-s');
                }
            }

            // Insert the group header row before/after the passed-in row
            if (append) {
                nGroup.insertAfter(row);
            } else {
                nGroup.insertBefore(row);
            }

            // Insert a spacer if this header follows a group of the same level
            if (tableConfig.groupSpacing) {
                var prevHeader = nGroup.prevAll('tr.group').first();
                if (prevHeader.length) {
                    var prevLevel = prevHeader.data('level');
                    if (prevLevel == level) {
                        var prevGroup = prevHeader.data('group'),
                            emptyCell = $('<td>').attr('colspan', iColspan),
                            spacerRow = $('<tr class="spacer">').append(emptyCell);
                        if (collapsable) {
                            spacerRow.addClass('collapsable');
                        }
                        spacerRow.addClass('xgroup_' + level + '_' + prevGroup)
                                 .insertBefore(nGroup);
                    }
                }
            }
        },

        /**
         * Expand/collapse a group
         *
         * @param {jQuery} row - the header row of the group
         * @param {boolean} visibility - true to expand, false to collapse the group
         */
        _toggleGroup: function(row, visibility) {

            switch(this.tableConfig.shrinkGroupedRows) {

                case 'individual':
                    if (visibility) {
                        this._expandGroup(row);
                    } else {
                        this._collapseGroup(row);
                    }
                    break;

                case 'accordion':
                    if (visibility) {

                        // Expand this group
                        this._expandGroup(row);

                        // Collapse all sibling groups at the same level
                        var level = row.data('level'),
                            siblingClass = '.level_' + level,
                            parentGroup = row.data('parentGroup');
                        if (parentGroup) {
                            siblingClass += '.xgroup_' + row.data('parentLevel') + '_' + parentGroup;
                        }
                        var self = this;
                        row.siblings('tr.group' + siblingClass).each(function() {
                            self._collapseGroup($(this));
                        });

                    } else {
                        this._collapseGroup(row);
                    }
                    break;
                default:
                    // do nothing
                    break;
            }
        },

        /**
         * Expand a group
         *
         * @param {jQuery} row - the header row of the group
         */
        _expandGroup: function(row) {

            // Get group and level from this row
            var level = row.data('level'),
                group = row.data('group');

            // Show all immediate child rows
            row.siblings('tr.xgroup_' + level + '_' + group).show();

            // Switch icons
            $('.group-expand, .group-closed', row).hide();
            $('.group-collapse, .group-opened', row).show();
        },

        /**
         * Collapse a group
         *
         * @param {jQuery} row - the header row of the group
         */
        _collapseGroup: function(row) {

            // Get group and level from this row
            var level = row.data('level'),
                group = row.data('group'),
                self = this;

            // Collapse sub-groups and hide all immediate child rows
            row.siblings('tr.xgroup_' + level + '_' + group).each(function() {
                var $this = $(this);
                if ($this.hasClass('group')) {
                    self._collapseGroup($this);
                }
                $this.hide();
            });

            // Switch icons
            $('.group-expand, .group-closed', row).show();
            $('.group-collapse, .group-opened', row).hide();
        },

        // --------------------------------------------------------------------
        // Export

        /**
         * Click-event handler for export format options
         */
        _exportFormat: function() {

            var el = $(this.element),
                self = this;

            return function(/* event */) {

                var oSetting = el.dataTable().fnSettings(),
                    url = $(this).data('url'),
                    extension = $(this).data('extension');

                // NB url already has filters (s3.filter.js/updateFormatURLs)

                if (oSetting) {

                    var args = 'id=' + self.tableid,
                        sSearch = oSetting.oPreviousSearch.sSearch,
                        aaSort = oSetting.aaSorting,
                        aaSortFixed = oSetting.aaSortingFixed,
                        aoColumns = oSetting.aoColumns;

                    if (sSearch) {
                        args += '&sSearch=' + sSearch + '&iColumns=' + aoColumns.length;
                    }
                    if (aaSortFixed !== null) {
                        aaSort = aaSortFixed.concat(aaSort);
                    }
                    aoColumns.forEach(function(column, i) {
                        if (!column.bSortable) {
                            args += '&bSortable_' + i + '=false';
                        }
                    });
                    args += '&iSortingCols=' + aaSort.length;
                    aaSort.forEach(function(sorting, i) {
                        args += '&iSortCol_' + i + '=' + aaSort[i][0] +
                                '&sSortDir_' + i + '=' + aaSort[i][1];
                    });

                    url = appendUrlQuery(url, extension, args);

                } else {

                    url = appendUrlQuery(url, extension);
                }

                // Use $.searchS3Download if available, otherwise (e.g. custom
                // page without s3.filter.js) fall back to window.open:
                if ($.searchDownloadS3 !== undefined) {
                    $.searchDownloadS3(url, '_blank');
                } else {
                    window.open(url);
                }
            };
        },

        /**
         * Update export URLs with initial filters:
         * - Export URLs are initially unfiltered until the filter
         *   form updates them for the first time; however, there
         *   may be filter defaults which also must be respected
         *   by exports => copy initial filters from the Ajax URL
         */
        _initExportFormats: function() {

            var tableConfig = this._parseConfig();
            if (tableConfig === undefined) {
                // No table config found => abort
                return;
            }

            var ajaxURL = tableConfig.ajaxUrl;
            if (ajaxURL && S3.search !== undefined) {
                var link = document.createElement('a');
                link.href = ajaxURL;
                if (link.search) {
                    var items = link.search.slice(1).split('&'),
                        queries = items.map(function(item) {
                            return item.split('=');
                        }).filter(function(item) {
                            return item[0].indexOf('.') != -1;
                        });
                    $(this.element).closest('.dt-wrapper')
                                   .find('.dt-export')
                                   .each(function() {
                        var $this = $(this);
                        var url = $this.data('url');
                        if (url) {
                            $this.data('url', S3.search.filterURL(url, queries));
                        }
                    });
                }
            }
        },

        // --------------------------------------------------------------------
        // EVENT HANDLING

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var el = $(this.element),
                ns = this.eventNamespace,
                self = this;

            // Expand/collapse truncated cell contents
            el.on('click' + ns, '.dt-truncate .ui-icon-zoomin, .dt-truncate .ui-icon-zoomout', function() {
                $(this).parent().toggle().siblings('.dt-truncate').toggle();
                return false;
            });

            // Export formats
            this._initExportFormats();
            el.closest('.dt-wrapper').find('.dt-export')
                                     .on('click' + ns, this._exportFormat());

            // Ajax-delete
            el.on('click' + ns, '.dt-ajax-delete', this.ajaxAction(i18n.delete_confirmation));

            // Group Expand/Collapse
            el.on('click' + ns, '.group-collapse, .group-expand', function() {

                var $this = $(this),
                    trow = $this.closest('tr.group'),
                    visibility = true;

                if ($this.hasClass('group-collapse')) {
                    visibility = false;
                }
                self._toggleGroup(trow, visibility);
            });

            // Bulk selection
            if (this.tableConfig.bulkActions) {

                if (this.tableConfig.bulkSingle) {
                    // Hide Select All if only 1 can be selected
                    $('.bulk-select-options', el).hide();
                } else {
                    // Bulk action select-all handler
                    el.on('click' + ns, '.bulk-select-all', this._bulkSelectAll());
                }

                // Bulk action checkbox handler
                el.on('click' + ns, '.bulkcheckbox', this._bulkSelectRow());
            }

            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var el = $(this.element),
                ns = this.eventNamespace;

            el.off(ns);
            el.closest('.dt-wrapper').find('.dt-export').off(ns);

            return true;
        }
    });

    // ------------------------------------------------------------------------
    // DATATABLE API EXTENSIONS

    /**
     * Register an API method that will empty the pipelined data, forcing an Ajax
     * fetch on the next draw (i.e. `table.clearPipeline().draw()`)
     */
    $.fn.dataTable.Api.register('clearPipeline()', function() {

        return this.iterator('table', function (settings) {
            settings.clearCache = true;
        });
    });

    /**
     * Simple plugin to Ajax-refresh a datatable. This also allows to
     * change the sAjaxSource URL for that table (e.g. in order to
     * update URL filters). Use e.g. in a onclick-handler like:
     * dt = $('#<list_id>').dataTable();
     * dt.fnReloadAjax(<new URL>);
     */
    $.fn.dataTableExt.oApi.fnReloadAjax = function(oSettings, sNewSource) {

        if ( sNewSource != 'undefined' && sNewSource != null ) {
            // sNewSource is a string containing the new Ajax-URL for
            // this instance, so override the previous setting
            oSettings.sAjaxSource = sNewSource;
        }

        // Show the "Processing..." box
        this.oApi._fnProcessingDisplay( oSettings, true );

        // Call ajax with empty request to trigger the pipeline
        // script, clear the table cache and run the following
        // callback:
        var self = this;
        oSettings.ajax({}, function(/* json */) {

            // Clear the table
            self.oApi._fnClearTable(oSettings);

            // Trigger the pipeline script again (this time without callback),
            // in  order to re-load the table data from the server:
            self.fnDraw();

        }, oSettings );
    };

    // ------------------------------------------------------------------------
    // GLOBAL FUNCTIONS

    // TODO Make methods available for vulnerability/s3.report.js
//     S3.dataTables.initDataTable = initDataTable;
//     S3.dataTables.accordionRow = accordionRow;

    // ------------------------------------------------------------------------
    // DOCUMENT-READY

    // Actions when document ready
    $(document).ready(function() {

        if (S3.dataTables) {
            // Initialize all data tables
            var dataTableIds = S3.dataTables.id;
            if (dataTableIds) {
                dataTableIds.forEach(function(tableId) {
                    $('#' + tableId).dataTableS3({destroy: false});
                });
            }
        }
    });

    // END --------------------------------------------------------------------

})(jQuery);
