/**
 * jQuery UI Widget for S3GroupedItemsReport
 *
 * @copyright 2015-2020 (c) Sahana Software Foundation
 * @license MIT
 *
 * requires jQuery 1.9.1+
 * requires jQuery UI 1.10 widget factory
 */
(function($, undefined) {

    "use strict";
    var groupedItemsID = 0;

    /**
     * groupedItems
     */
    $.widget('s3.groupedItems', {

        /**
         * Default options
         *
         * @prop {string} ajaxURL - the URL to retrieve updated data from
         * @prop {bool} renderGroupHeaders - whether to render group headers
         * @prop {string} totalsLabel - the label for group totals
         */
        options: {

            ajaxURL: null,

            renderGroupHeaders: false,
            totalsLabel: 'TOTAL'

        },

        /**
         * Create the widget
         */
        _create: function() {

            var el = $(this.element);

            this.id = groupedItemsID;
            groupedItemsID += 1;

            // Namespace for events
            this.eventNamespace = '.groupeditems';
        },

        /**
         * Update the widget options
         */
        _init: function() {

            var el = $(this.element);

            this.widget_id = el.attr('id');

            this.items = el.find('.gi-data').first();

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

            // Show throbber
            el.find('.gi-throbber').show();

            this._unbindEvents();

            // Read data from hidden input
            if (!this.data) {
                this._deserialize();
            }
            var data = this.data;

            var table = el.find('.gi-table');
            if (!data.e) {
                // Hide empty section
                el.find('.gi-empty').hide();

                // Remove the table
                table.empty();

                // Render the table contents
                var tableContents = this._renderTable(data);

                // Show the table container
                table.append(tableContents).show();

            } else {
                // Hide the table container
                table.hide();

                // Remove the table
                table.empty();

                // Show the empty section
                el.find('.gi-empty').show();
            }

            this._bindEvents();

            // Hide throbber
            el.find('.gi-throbber').css('visibility', 'hidden');;
        },

        /**
         * Render the grouped table
         *
         * @param {object} data - the data object
         * @return {jQuery} - the table (table)
         */
        _renderTable: function(data) {

            var table = $('<table class="groupeditems">');

            this._renderTableHeader(data).appendTo(table);
            this._renderGroup(table, data);
            this._renderTableFooter(data).appendTo(table);

            return table;
        },

        /**
         * Render the header for the grouped table (column labels)
         *
         * @param {object} data - the data object
         * @return {jQuery} - the table header (thead)
         */
        _renderTableHeader: function(data) {

            var thead = $('<thead>'),
                headerRow = $('<tr class="gi-column-headers">').appendTo(thead);

            var columns = data.c,
                labels = data.l,
                label;
            for (var i = 0, len = columns.length; i < len; i++) {
                label = labels[columns[i]];
                $('<th>').html(label).appendTo(headerRow);
            }
            return thead;
        },

        /**
         * Render the footer for the grouped table (overall totals)
         *
         * @param {object} data - the data object
         * @return {jQuery} - the table footer (tfoot)
         */
        _renderTableFooter: function(data) {

            var opts = this.options,
                tfoot = $('<tfoot>'),
                footerRow = $('<tr class="gi-column-totals">');

            var totals = data.t,
                hasTotals = false;
            for (var key in totals) {
                hasTotals = true;
                break;
            }
            if (hasTotals) {

                var columns = data.c,
                    value,
                    cell,
                    footerLabel = null,
                    titleSpan = 0;
                for (var i = 0, len = columns.length; i < len; i++) {
                    if (!footerLabel) {
                        if (!totals.hasOwnProperty(columns[i])) {
                            titleSpan++;
                            continue;
                        }
                        if (titleSpan > 1) {
                            footerLabel = $('<td class="gi-column-totals-label" colspan="' + titleSpan + '">');
                            $('<span> ' + opts.totalsLabel + '</span>').appendTo(footerLabel);
                            footerLabel.appendTo(footerRow);
                        }
                    }
                    cell = $('<td>').appendTo(footerRow);
                    value = totals[columns[i]];
                    if (value) {
                        cell.html(value);
                    }
                }
                footerRow.appendTo(tfoot);
            }
            return tfoot;
        },

        /**
         * Render a group of rows in the grouped table
         *
         * @param {jQuery} table - the table
         * @param {object} data - the data object
         * @param {object} group - the group object
         * @param {integer} level - the grouping level
         */
        _renderGroup: function(table, data, group, level) {

            if (typeof group == 'undefined') {
                group = data;
            }
            if (typeof level == 'undefined') {
                level = 0;
            }

            if (this.options.renderGroupHeaders && level > 0) {
                this._renderGroupHeader(table, data, group, level);
            }

            var subGroups = group.d,
                items = group.i,
                i,
                len;
            if (subGroups) {
                for (i = 0, len = subGroups.length; i < len; i++) {
                    this._renderGroup(table, data, subGroups[i], level + 1);
                }
            } else if (items) {
                for (i = 0, len = items.length; i < len; i++) {
                    this._renderItem(table, data, items[i], level);
                }
            }

            if (level > 0) {
                this._renderGroupFooter(table, data, group, level);
            }
        },

        /**
         * Render the header for a group (group title)
         *
         * @param {jQuery} table - the table
         * @param {object} data - the data object
         * @param {object} group - the group object
         * @param {integer} level - the grouping level
         */
        _renderGroupHeader: function(table, data, group, level) {

            var columns = data.c,
                value = group.v,
                groupHeader = $('<tr class="gi-group-header gi-level-' + level + '">');

            $('<td colspan="' + columns.length + '">').html(value).appendTo(groupHeader);

            groupHeader.appendTo(table);
        },

        /**
         * Render the footer for a group (group totals)
         *
         * @param {jQuery} table - the table
         * @param {object} data - the data object
         * @param {object} group - the group object
         * @param {integer} level - the grouping level
         */
        _renderGroupFooter: function(table, data, group, level) {

            var opts = this.options,
                groupTotals = group.t,
                hasTotals = false;
            for (var key in groupTotals) {
                hasTotals = true;
                break;
            }

            var columns = data.c,
                value = group.v,
                footerRow = $('<tr class="gi-group-footer gi-level-' + level + '">');

            if (!hasTotals && !opts.renderGroupHeaders) {

                $('<td colspan="' + columns.length + '">').html(value).appendTo(footerRow);
                footerRow.appendTo(table);

            } else if (hasTotals) {

                // render the group totals
                var titleSpan = 0,
                    footerLabel = null,
                    total,
                    cell;

                for (var i = 0, len = columns.length; i < len; i++) {

                    if (!footerLabel) {
                        if (!groupTotals.hasOwnProperty(columns[i])) {
                            titleSpan++;
                            continue;
                        }
                        if (titleSpan > 1) {
                            footerLabel = $('<td class="gi-group-footer-label" colspan="' + titleSpan + '">');
                            if (!opts.renderGroupHeaders) {
                                footerLabel.html(value);
                            }
                            $('<span class="gi-group-footer-inline-label"> ' + opts.totalsLabel + '</span>').appendTo(footerLabel);
                            footerLabel.appendTo(footerRow);
                        }
                    }
                    cell = $('<td>').appendTo(footerRow);
                    total = groupTotals[columns[i]];
                    if (total) {
                        cell.html(total);
                    }
                }
                footerRow.appendTo(table);
            }
        },

        /**
         * Render an item row in the grouped table
         *
         * @param {jQuery} table - the table
         * @param {object} data - the data object
         * @param {object} item - the item object
         * @param {integer} level - the grouping level
         */
        _renderItem: function(table, data, item, level) {

            var itemRow = $('<tr class="gi-item gi-level-' + level + '">');

            var columns = data.c,
                value,
                cell;
            for (var i = 0, len = columns.length; i < len; i++) {
                cell = $('<td>');
                value = item[columns[i]];
                if (value) {
                    cell.html(value);
                }
                cell.appendTo(itemRow);
            }
            itemRow.appendTo(table);
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

            $(this.element).find('.gi-throbber').css('visibility', 'visible');

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
                    self.items.val(JSON.stringify(data));
                    self.data = null; // enforce deserialize
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
                self.refresh();
            }
        },

        /**
         * Get current filters from the associated filter form
         *
         * This is needed when the reload is not triggered /by/ the filter form
         */
        _getFilters: function() {

            var filters = $('#' + this.widget_id + '-filter-form');
            try {
                if (filters.length) {
                    return S3.search.getCurrentFilters(filters.first());
                } else {
                    return null;
                }
            } catch (e) {
                return null;
            }
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
                var option, newopt;
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
                subquery,
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
                        subquery = k + '=' + encodeURIComponent(v);
                        if (update[k]) {
                            update[k].push(subquery);
                        } else {
                            update[k] = [subquery];
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
         * Serialize this.data as JSON and set it as value for the
         * hidden data element
         */
        _serialize: function() {

            var items = this.items;
            if (items) {
                var value = '';
                if (this.data) {
                    value = JSON.stringify(this.data);
                }
                items.val(value);
            }
            return value;
        },

        /**
         * Read the value of the hidden data element, parse the JSON
         * and store the data in this.data
         */
        _deserialize: function() {

            this.data = {};

            var items = this.items;
            if (items) {
                var value = items.val();
                if (value) {
                    this.data = JSON.parse(value);
                }
            }
            return this.data;
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var el = $(this.element),
                ns = this.eventNamespace,
                self = this;

            el.delegate('.gi-export', 'click' + ns, function() {

                var url = $(this).data('url'),
                    queries = self._getFilters();

                if (queries) {
                    url = S3.search.filterURL(url, queries);
                }
                window.open(url);
            });
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var el = $(this.element),
                ns = this.eventNamespace;

            el.undelegate(ns);
        }
    });
})(jQuery);
