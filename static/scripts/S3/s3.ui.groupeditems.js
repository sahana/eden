/**
 * jQuery UI Widget for S3GroupedItemsReport
 *
 * @copyright 2015 (c) Sahana Software Foundation
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
         * @todo document options
         */
        options: {

            renderGroupHeaders: false

        },

        /**
         * Create the widget
         */
        _create: function() {

            var el = $(this.element);

            this.id = groupedItemsID;
            groupedItemsID += 1;
        },

        /**
         * Update the widget options
         */
        _init: function() {

            var el = $(this.element);

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
            el.find('.gi-throbber').hide();

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
            el.find('.gi-throbber').hide();
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
         *
         * @todo: render 'Total' label
         */
        _renderTableFooter: function(data) {

            var tfoot = $('<tfoot>'),
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
                    cell;
                for (var i = 0, len = columns.length; i < len; i++) {
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

            var groupTotals = group.t,
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
                            footerLabel = $('<td class="gi-group-footer-label" colspan="' + titleSpan + '">').html(value);
                            $('<span> TOTAL</span>').appendTo(footerLabel);
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
