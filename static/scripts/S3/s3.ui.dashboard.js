/**
 * jQuery UI Widget Classes for S3Dashboard
 *
 * @copyright 2016 (c) Sahana Software Foundation
 * @license MIT
 *
 * requires jQuery 1.9.1+
 * requires jQuery UI 1.10 widget factory
 *
 */

(function($, undefined) {

    "use strict";
    var dashboardID = 0;

    /**
     * Dashboard Controller
     */
    $.widget('s3.dashboardController', {

        /**
         * Default options
         *
         * @prop {string} ajaxURL - URL for dashboard agent Ajax requests
         */
        options: {

            ajaxURL: null

        },

        /**
         * Create the widget
         */
        _create: function() {

            var el = $(this.element);

            this.id = dashboardID;
            dashboardID += 1;
        },

        /**
         * Update the widget options
         */
        _init: function() {

            var el = $(this.element);

            this.refresh();

            // @todo: remove
            s3_debug("dashboard initialized");
            s3_debug("dashboard ajaxURL=" + this.options.ajaxURL);
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

            this._bindEvents();
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

(function($, undefined) {

    "use strict";
    var dashboardWidgetID = 0;

    /**
     * Dashboard Controller
     */
    $.widget('s3.dashboardWidget', {

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

            this.id = dashboardWidgetID;
            dashboardWidgetID += 1;
        },

        /**
         * Update the widget options
         */
        _init: function() {

            var el = $(this.element);

            this.refresh();

            // @todo: remove
            s3_debug("dashboard widget initialized");
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

            this._bindEvents();
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
