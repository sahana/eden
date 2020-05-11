/**
 * jQuery UI Widget for RLP Inline Notifications
 *
 * @copyright 2020-2020 (c) Sahana Software Foundation
 * @license MIT
 *
 * requires jQuery 1.9.1+
 * requires jQuery UI 1.10 widget factory
 */
(function($, undefined) {

    "use strict";
    var rlpNotificationsID = 0;

    /**
     * rlpNotifications
     */
    $.widget('s3.rlpNotifications', {

        /**
         * Default options
         *
         * TODO document options
         */
        options: {

        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = rlpNotificationsID;
            rlpNotificationsID += 1;

            this.eventNamespace = '.rlpNotifications';
        },

        /**
         * Update the widget options
         */
        _init: function() {

            var el = $(this.element);

            this.trigger = $('#hrm_delegation_status');
            this.input = $('.notification-data', el).first();

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

            // Clear the form, reset loaded
            this._clearSubForm();
            this.loaded = false;

            // Populate form from hidden input
            this._deserialize();

            // Show subform if trigger is APPR, otherwise hide it
            if (this.trigger.val() == 'APPR') {
                this._showSubForm();
            } else {
                this._hideSubForm();
            }

            this._bindEvents();
        },

        /**
         * Write data from current inputs to hidden JSON input
         */
        _serialize: function() {

            var $el = $(this.element),
                formName = this.options.formName,
                fieldSets = ["organisation", "volunteer", "office"],
                formFields = ['email', 'subject', 'message'];

            var messages = {},
                send = {};
            fieldSets.forEach(function(recipient) {
                var message = {},
                    include = false,
                    prefix = '#sub_' + formName + '_' + recipient + '_';

                send[recipient] = $('#' + formName + '_notify_' + recipient).prop('checked');
                formFields.forEach(function(key) {
                    var input = $(prefix + key, $el);
                    if (!input.length) {
                        return;
                    }
                    message[key] = input.val();
                    include = true;
                });
                if (include) {
                    messages[recipient] = message;
                }
            });

            var data = {
                messages: messages,
                send: send
            };

            var delegationID = this.data.delegationID;
            if (delegationID !== undefined) {
                data.delegationID = delegationID;
            }
            this.input.val(JSON.stringify(data));
        },

        /**
         * Read data from hidden JSON input and populate form
         */
        _deserialize: function() {

            var jsonData = this.input.val();
            if (jsonData) {
                this.data = JSON.parse(jsonData);
            } else {
                this.data = {};
            }
            var messages = this.data.messages;
            if (messages) {
                this._populateSubForm(messages);
                this.loaded = true; // do not load again
            }
            var send = this.data.send;
            if (send) {
                var formName = this.options.formName;
                for (var recipient in send) {
                    var doSend = send[recipient],
                        toggle = $('#' + formName + '_notify_' + recipient);
                    if (doSend) {
                        toggle.prop('checked', true);
                        $('.form-row', toggle.closest('fieldset')).show();
                    } else {
                        toggle.prop('checked', false);
                        $('.form-row', toggle.closest('fieldset')).hide();
                    }
                }
            }
        },

        /**
         * Ajax-load the notification messages and populate the form
         */
        _load: function() {

            var self = this,
                opts = this.options,
                $el = $(this.element),
                ajaxURL = opts.ajaxURL;

            if (this.loaded || !ajaxURL) {
                return;
            }

            // Show a throbber (in each fieldset)
            var fieldSets = $('fieldset', $el),
                throbber = $('<div class="inline-throbber">').prependTo(fieldSets);

            // Load messages Ajax
            $.ajaxS3({
                'url': ajaxURL,
                'type': 'GET',
                'dataType': 'json',
                'contentType': 'application/json; charset=utf-8',
                'success': function(data) {

                    // Remove the throbber
                    throbber.remove();

                    // Parse the data and fill input fields in subform
                    self._populateSubForm(data);
                    self._serialize();
                    self.loaded = true;
                },
                'error': function () {

                    // Remove throbber
                    throbber.remove();

                    // Clear the subform
                    self._clearSubForm();
                    self._serialize();
                }
            });

        },

        /**
         * Show the subform, and load the messages if not loaded yet
         */
        _showSubForm: function() {

            $(this.element).closest('.form-row').show();

            if (!this.loaded) {
                this._load();
            }
        },

        /**
         * Hide the subform
         */
        _hideSubForm: function() {

            $(this.element).closest('.form-row').hide();
        },

        /**
         * Populate the subform with data loaded from server
         *
         * @param {object} data: the data with the messages and form status
         */
        _populateSubForm: function(data) {

            if (!data) {
                return;
            }

            var $el = $(this.element),
                opts = this.options,
                formName = opts.formName,
                fieldSets = ["organisation", "volunteer", "office"],
                formFields = ['email', 'subject', 'message'];

            fieldSets.forEach(function(recipient) {
                var message = data[recipient];
                if (message === undefined) {
                    $('#' + formName + '_notify_' + recipient).prop('checked', false).change();
                    return;
                }
                var prefix = '#sub_' + formName + '_' + recipient + '_';
                formFields.forEach(function(key) {
                    var input = $(prefix + key, $el);
                    if (!input.length) {
                        return;
                    }
                    var value = message[key];
                    if (value !== undefined) {
                        input.val(value);
                    } else {
                        input.val('');
                    }
                });
            });
        },

        /**
         * Clear the subform
         */
        _clearSubForm: function() {

            var $el = $(this.element),
                opts = this.options,
                formName = opts.formName,
                fieldSets = ["organisation", "volunteer", "office"],
                formFields = ['email', 'subject', 'message'];

            fieldSets.forEach(function(recipient) {
                var prefix = '#sub_' + formName + '_' + recipient + '_';
                formFields.forEach(function(key) {
                    var input = $(prefix + key, $el);
                    if (input.length) {
                        input.val('');
                    }
                });
            });
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var $el = $(this.element),
                ns = this.eventNamespace,
                self = this;

            this.trigger.on('change' + ns, function() {
                if ($(this).val() == 'APPR') {
                    self._showSubForm();
                } else {
                    self._hideSubForm();
                }
            });

            $('.notify-toggle', $el).on('change' + ns, function() {
                if ($(this).prop('checked')) {
                    $('.form-row', $(this).closest('fieldset')).show();
                } else {
                    $('.form-row', $(this).closest('fieldset')).hide();
                }
                self._serialize();
            });

            $('input[type="text"], textarea', $el).on('keyup' + ns, function() {
                self._serialize();
            });

            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var $el = $(this.element),
                ns = this.eventNamespace;

            this.trigger.off(ns);
            $('.notify-toggle', $el).off(ns);
            $('input[type="text"], textarea', $el).off(ns);

            return true;
        }
    });
})(jQuery);
