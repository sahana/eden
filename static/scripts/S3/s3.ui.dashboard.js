/**
 * jQuery UI Widget Classes for S3Dashboard
 *
 * @copyright 2016-2019 (c) Sahana Software Foundation
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
         * @prop {string} version - the current config version key
         */
        options: {

            ajaxURL: null,
            version: null

        },

        /**
         * Create the widget
         */
        _create: function() {

            var el = $(this.element);

            this.id = dashboardID;
            dashboardID += 1;

            // Namespace for events
            this.eventNamespace = '.dashboard';
        },

        /**
         * Update the widget options
         */
        _init: function() {

            var el = $(this.element);

            this.refresh();

            // @todo: remove?
            s3_debug("dashboard initialized");
            s3_debug("dashboard ajaxURL=" + this.options.ajaxURL);
            s3_debug("dashboard version=" + this.options.version);
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
         * @param {boolean} mode - true|false to turn config mode on/off,
         *                         undefined to return the current status
         */
        configMode: function(mode) {

            var el = this.element,
                ns = this.eventNamespace,
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

                // Turn on config mode for all widgets
                el.find('.db-widget').each(function() {
                    $(this).dashboardWidget('configMode', true);
                });

                // Trigger openConfig event
                el.trigger('openConfig' + ns);

            } else {

                // Trigger closeConfig event
                el.trigger('closeConfig' + ns);

                // Turn off config mode for all widgets
                el.find('.db-widget').each(function() {
                    $(this).dashboardWidget('configMode', false);
                });

                // Turn config mode off
                modeSwitch.data('mode', 'off');
                modeSwitch.find('.db-config-off').hide();
                modeSwitch.find('.db-config-on').show().removeClass('hide');

            }
            return mode;
        },

        /**
         * Helper method to update the version key for the dashboard
         * and all its active widgets
         *
         * @param {string} version: the version key
         */
        updateVersion: function(version) {

            var el = this.element;

            // Update version key
            this._setOption('version', version);

            // @todo: remove?
            s3_debug("dashboard new version=" + version);

            // Also update version key in all widgets
            el.find('.db-widget').each(function() {
                $(this).dashboardWidget('option', 'version', version);
            });
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var el = this.element,
                ns = this.eventNamespace,
                self = this;

            // Config mode switches
            // @ToDo: Replace bind() with on() as bind deprecated: http://api.jquery.com/bind/
            $('.db-config-on').bind('click' + ns, function() {
                self.configMode(true);
            });
            $('.db-config-off').bind('click' + ns, function() {
                self.configMode(false);
            });

            // Config saved => update version key
            el.bind('configSaved' + ns, function(e, data) {

                // Prevent configSaved event from bubbling further up
                e.stopPropagation();

                var version = null;
                if (data && data.hasOwnProperty('v')) {
                    version = data.v;
                }
                if (version) {
                    self.updateVersion(version);
                }
            });

            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var ns = this.eventNamespace;

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
         * @prop {string} dashboardURL - the URL for dashboard agent requests
         * @prop {string} version - the config version key
         * @prop {string} title - the widget title (used in config dialog,
         *                        configured in back-end widget class)
         */
        options: {

            dashboardURL: null,
            version: null,
            title: 'Dashboard Widget'

        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = dashboardWidgetID;
            dashboardWidgetID += 1;

            // Namespace for events
            this.eventNamespace = '.dashboardWidget';
        },

        /**
         * Update the widget options
         */
        _init: function() {

            var el = $(this.element);

            // Get the agent ID
            this.agentID = el.attr('id');

            // Identify the config-bar
            this.configBar = el.find('.db-configbar');

            // Refresh the widget contents
            this.refresh();

            // @todo: remove?
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

            var el = $(this.element),
                opts = this.options;

            this._unbindEvents();

            this._bindEvents();
        },

        /**
         * Actions after widget config settings have changed
         *
         * @param {object} newConfig - the new widget config
         */
        _onConfigUpdate: function(newConfig) {

            var el = $(this.element);

            // Generic widget can update directly from newConfig,
            // no need to Ajax-reload anything (other widget
            // classes may have to, though - and then this is the
            // right place to do it)
            if (newConfig && newConfig.hasOwnProperty('xml')) {

                // Remove everything except config bars
                el.children(':not(.db-configbar)').remove();

                // Insert the new XML after the top-most config bar
                var xmlStr = newConfig.xml;
                if (xmlStr) {
                    this.configBar.first().after(xmlStr);
                }
            }

            // Refresh widget (this should always be done after
            // updating elements or DOM tree of the widget)
            this.refresh();
        },

        /**
         * Get or set the current config-mode status
         *
         * @param {bool} mode - true|false to turn config mode on/off,
         *                      undefined to return the current status
         */
        configMode: function(mode) {

            var el = $(this.element);

            if (typeof mode === 'undefined') {
                mode = this.configBar.is(':visible');
            } else if (mode) {
                this.configBar.show();
                el.addClass('db-config-active');
            } else {
                this.configBar.hide();
                el.removeClass('db-config-active');
            }
            return mode;
        },

        /**
         * Render the config dialog
         */
        _configDialog: function() {

            var el = $(this.element),
                ns = this.eventNamespace,
                opts = this.options,
                self = this;

            if (!$('.db-config-dialog').length) {

                // Construct the popup URL
                var configURL = 'config.popup?agent=' + this.agentID + '&version=' + opts.version,
                    dashboardURL = opts.dashboardURL;
                if (dashboardURL) {
                    configURL = dashboardURL + '/' + configURL;
                }

                // Construct the iframe
                var iframeID = this.agentID + '-dialog',
                    dialog = $('<iframe>', {
                    'id': iframeID,
                    'src': '',
                    'class': 'loading',
                    'load': function() {
                        $(this).removeClass('loading');
                        var width = $('.ui-dialog').width();
                        $('#' + iframeID).width(width).contents().find('#popup form').show();
                    },
                    'marginWidth': '0',
                    'marginHeight': '0',
                    'frameBorder': '0'
                }).appendTo('body');

                this.configDialog = dialog;

                // Instantiate the dialog
                dialog.dialog({
                    autoOpen: false,
                    modal: true,
                    minWidth: 320,
                    minHeight: 480,
                    title: opts.title,
                    open: function() {
                        // Clicking outside of the dialog closes it
                        $('.ui-widget-overlay').one('click' + ns, function() {
                            dialog.dialog('close');
                        });
                        // Highlight the widget this dialog belongs to
                        el.addClass('db-has-dialog');
                    },
                    close: function() {
                        dialog.attr('src', '');
                        el.removeClass('db-has-dialog');
                        self.configDialog.remove();
                        self.configDialog = null;
                    }
                });

                // Set iframe source and open the dialog
                dialog.attr('src', configURL).dialog('open');
            }
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var el = $(this.element),
                ns = this.eventNamespace,
                self = this;

            // ConfigBar actions
            this.configBar.find('.db-task-config').on('click' + ns, function() {
                self._configDialog();
            });

            // Actions after successful config update
            el.bind('configSaved' + ns, function(e, data) {

                // New config returned from form processing?
                var newConfig = null;
                if (data && data.hasOwnProperty('c')) {
                    newConfig = data.c;
                }

                // Reload/refresh widget as necessary
                self._onConfigUpdate(newConfig);

                // Close the dialog (will remove the iframe itself)
                var dialog = self.configDialog;
                if (dialog) {
                    dialog.dialog('close');
                }
            });

            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var el = $(this.element),
                ns = this.eventNamespace;

            el.unbind(ns);

            this.configBar.find('.db-task-config').off('click' + ns);

            return true;
        }
    });
})(jQuery);
