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

            // Namespace for events
            this.namespace = '.dashboard';
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
         * Get or set the current config-mode status
         *
         * @param {boolean} mode - true to turn config mode on,
         *                         false to turn config mode off,
         *                         undefined to return the current status
         */
        configMode: function(mode) {

            var el = this.element,
                ns = this.namespace,
                modeSwitch = $('.db-config');

            if (typeof mode === 'undefined') {

                // Return the current status
                var status = modeSwitch.data('mode');
                if (status == 'on') {
                    mode = true;
                } else {
                    mode = false;
                }

            } else if (mode) {

                // Turn config mode on
                modeSwitch.data('mode', 'on');
                modeSwitch.find('.db-config-on').hide();
                modeSwitch.find('.db-config-off').show().removeClass('hide');

                // Trigger openConfig event
                el.trigger('openConfig' + ns);

            } else {

                // Turn config mode off
                modeSwitch.data('mode', 'off');
                modeSwitch.find('.db-config-off').hide();
                modeSwitch.find('.db-config-on').show().removeClass('hide');

                // Trigger closeConfig event
                el.trigger('closeConfig' + ns);
            }
            return mode;
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var ns = this.namespace,
                self = this;

            // Config mode switches
            $('.db-config-on').bind('click' + ns, function() {
                self.configMode(true);
            });
            $('.db-config-off').bind('click' + ns, function() {
                self.configMode(false);
            });

            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var ns = this.namespace;

            $('.dashboard-config').unbind(ns);

            return true;
        }
    });
})(jQuery);

// ----------------------------------------------------------------------------

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
