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

                // @todo: render the table

                // Show the table container
                table.show();

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
         * @todo: docstring
         */
        _serialize: function() {

            var items = this.items;
            if (items) {
                var value = '';
                if (this.data) {
                    value = JSON.stringify(this.data);
                }
                items.val(value)
            }
            return value;
        },

        /**
         * @todo: docstring
         */
        _deserialize: function() {

            this.data = {}

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
