/**
 * jQuery UI Widget for DataSeriesTable
 *
 * @copyright 2026 (c) Sahana Software Foundation
 * @license MIT
 */

/* jshint esversion: 6 */

(function($, undefined) {

    "use strict";
    var dsTableID = 0;

    /**
     * dsTable
     */
    $.widget('s3.dsTable', {

        /**
         * Default options
         *
         * @todo document options
         */
        options: {

        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = dsTableID;
            dsTableID += 1;

            this.eventNamespace = '.dsTable';
        },

        /**
         * Update the widget options
         */
        _init: function() {

            const $el = $(this.element),
                  widgetID = $el.attr('id'),
                  dataInput = $('#' + widgetID + '-data');

            // Read+parse initial data
            self.data = {};
            if (dataInput.length) {
                try {
                    self.data = JSON.parse(dataInput.val());
                } catch(e) {
                    // pass
                }
            }

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

            this._unbindEvents();

            this._renderTable(self.data);

            this._bindEvents();
        },

        _renderTable: function(data) {

            const $el = $(this.element);

            const head = this._renderHeader(data),
                  body = this._renderBody(data),
                  foot = this._renderFooter(data);

            $el.empty()
               .append(head)
               .append(body)
               .append(foot);

            head.show();
            foot.show();
            body.show();
        },

        _renderHeader: function(data) {

            const head = $('<thead>').hide();

            return this._renderSlots(head, data);
        },

        _renderBody: function(data) {

            const body = $('<tbody>').hide();

            const groups = data.g || [],
                  series = data.s || [],
                  slots = data.d || [],
                  self = this;

            if (groups) {
                groups.forEach(group => {
                    var groupID = group[0],
                        groupRow = $('<tr>').append($('<td colspan=' + (1 + slots.length) + '>')
                                            .text(group[1]))
                                            .appendTo(body);
                    series.forEach(parameter => {
                        if (parameter[1] != groupID) {
                            return;
                        }
                        self._renderSeries(data, parameter).appendTo(body);
                    });
                });
            } else {
                series.forEach(parameter => {
                    self._renderSeries(data, parameter).appendTo(body);
                });
            }

            return body;
        },

        _renderSeries: function(data, series) {

            const slots = data.d || [],
                  values = data.v;

            var row = $('<tr>'),
                label = $('<div class="dstable-param">').text(series[2] || '??'),
                range = $('<div class="dstable-range">').text((series[4] || '??') + ' ' + (series[5] || '??'));

            $('<th class="fixed">').append(label).append(range).appendTo(row);

            slots.forEach(slot => {

                var slotID = slot[0],
                    slotValues = values[slotID],
                    result = slotValues ? slotValues[series[0]] : null,
                    cell = $("<td>");

                if (result !== null) {
                    cell.text(result[0]);
                }
                cell.appendTo(row);
            });

            return row;
        },

        _renderFooter: function(data) {

            const foot = $('<tfoot>').hide();

            return this._renderSlots(foot, data);
        },

        _renderSlots: function(container, data) {

            const row = $('<tr>').appendTo(container),
                  label = data.l || '',
                  slots = data.d || [];

            $('<th scope="col">').addClass('fixed').text(label).appendTo(row);
            slots.forEach(function(slot) {
                var slotLabel = slot[2] || '??';
                $('<th scope="col">').text(slotLabel).appendTo(row);
            });

            return container;
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            let $el = $(this.element),
                ns = this.eventNamespace,
                self = this;

            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            let $el = $(this.element),
                ns = this.eventNamespace;

            return true;
        }
    });
})(jQuery);
