/**
 * jQuery UI Widget for RLP Inline Notifications
 *
 * @copyright 2020-2021 (c) Sahana Software Foundation
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
         * @prop {string} ajaxURL - the URL to load the data from
         * @prop {string} formName - the formName prefix for element selectors
         */
        options: {
            ajaxURL: null,
            formName: null,
            recipients: ["organisation", "volunteer", "office"],
            organisations: null
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

            this.watch = '#hrm_delegation_date, #hrm_delegation_end_date, #hrm_delegation_comments, #hrm_delegation_organisation_id';
            this.watchFields = {
                'start': $('#hrm_delegation_date'),
                'end': $('#hrm_delegation_end_date'),
                'comments': $('#hrm_delegation_comments'),
                'organisation': $('#hrm_delegation_organisation_id')
            };

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
                opts = this.options,
                formName = opts.formName,
                fieldSets = opts.recipients,
                formFields = ['subject', 'message'],
                emailAddresses = {},
                templates = {},
                send = {};

            fieldSets.forEach(function(recipient) {
                var prefix = '#sub_' + formName + '_' + recipient + '_',
                    emailField = $(prefix + 'email', $el);

                if (emailField.length) {
                    emailAddresses[recipient] = emailField.val();
                }
                send[recipient] = $('#' + formName + '_notify_' + recipient).prop('checked');

                var template = {},
                    include = false;
                formFields.forEach(function(key) {
                    var input = $(prefix + key, $el);
                    if (!input.length) {
                        return;
                    }
                    template[key] = input.val();
                    include = true;
                });
                if (include) {
                    templates[recipient] = template;
                }
            });

            this.data = $.extend({}, this.data, {
                email: emailAddresses,
                templates: templates,
                send: send
            });
            this.input.val(JSON.stringify(this.data));
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
            var data = this.data;
            if (data.email) {
                this._populateSubForm(this.data);
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
                'success': function(response) {

                    // Remove the throbber
                    throbber.remove();

                    if (!response.data) {
                        response.data = {};
                    }
                    self.data = $.extend({}, self.data, response);

                    // Parse the data and fill input fields in subform
                    self._populateSubForm(response);
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

            var emailAdresses = data.email || {},
                templates = data.templates || {};

            var $el = $(this.element),
                opts = this.options,
                formName = opts.formName,
                fieldSets = opts.recipients,
                formFields = ['subject', 'message'];

            fieldSets.forEach(function(recipient) {

                var prefix = '#sub_' + formName + '_' + recipient + '_',
                    email = emailAdresses[recipient],
                    deactivate = false;

                // Set the email address
                if (!email) {
                    $(prefix + 'email', $el).val('');
                    deactivate = true;
                } else {
                    $(prefix + 'email', $el).val(email);
                }

                // Load templates into inputs
                var recipientTemplates = templates[recipient];
                formFields.forEach(function(key) {
                    var input = $(prefix + key, $el);
                    if (!input.length) {
                        return;
                    }
                    var value;
                    if (recipientTemplates) {
                        value = recipientTemplates[key];
                    }
                    if (value !== undefined) {
                        input.val(value);
                    } else {
                        input.val('');
                        deactivate = true;
                    }
                });
                if (deactivate) {
                    // Email, subject template or message template missing
                    // => deactivate sending
                    $('#' + formName + '_notify_' + recipient).prop('checked', false).change();
                }
            });

            this._renderPreviews();
        },

        /**
         * Update data with current form values
         */
        _updateData: function() {

            var watchFields = this.watchFields,
                update = {};

            for (var key in watchFields) {
                var field = watchFields[key];
                if (field.length) {
                    var value = field.val();
                    if (key == 'organisation') {
                        var labels = this.options.organisations;
                        if (labels.hasOwnProperty(value)) {
                            update[key] = labels[value];
                            continue;
                        }
                    }
                    if (field.prop('tagName') == 'SELECT') {
                        value = $('option[value=' + value + ']', field).text();
                    }
                    update[key] = value;
                }
            }
            this.data.data = $.extend({}, this.data.data, update);
        },

        /**
         * Render a preview from a template, using current data
         *
         * @param {string} template - the string template
         */
        _renderPreview: function(template) {

            this._updateData();

            var data = this.data.data;
            return template.replace(/{([^{}]+)}/g, function(placeholder, name) {
                var value = data[name];
                if (value === undefined || name != 'comments' && value === '') {
                    return '<span class="highlight-miss">' + placeholder + '</span>';
                } else {
                    return '<span class="highlight-sub" title="' + placeholder + '">' + value + '</span>';
                }
            });
        },

        /**
         * Render all previews
         */
        _renderPreviews: function() {

            var $el = $(this.element),
                opts = this.options,
                formName = opts.formName,
                fieldSets = opts.recipients,
                formFields = ['subject', 'message'],
                self = this;

            fieldSets.forEach(function(recipient) {

                var prefix = '#sub_' + formName + '_' + recipient + '_';

                if (!$(prefix + 'email__row', $el).length) {
                    return;
                }

                formFields.forEach(function(key) {
                    var input = $(prefix + key, $el);
                    if (!input.length) {
                        return;
                    }

                    // Read the template from input
                    var template = input.val(),
                        previewContent = '';
                    if (template) {
                        previewContent = self._renderPreview(template);
                    }
                    var preview = input.siblings('.preview');
                    if (preview.length) {
                        preview.html(previewContent);
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
                fieldSets = opts.recipients,
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

            // Re-render previews when main form data change
            $(this.watch).on('change' + ns + ', keyup' + ns, function() {
                self._renderPreviews();
            });

            // Show/hide field sets when notification is selected/deselected
            $('.notify-toggle', $el).on('change' + ns, function() {
                if ($(this).prop('checked')) {
                    $('.form-row, .preview-toggles', $(this).closest('fieldset')).show();
                } else {
                    $('.form-row, .preview-toggles', $(this).closest('fieldset')).hide();
                }
                self._serialize();
            });

            // Switch between edit/preview
            $('.preview-toggle', $el).on('click' + ns, function() {
                var $this = $(this);
                $('.preview-widget', $this.closest('fieldset')).children().toggle();
                $this.toggle().siblings().toggle();
            });

            // Serialize and re-render previews when templates are changed
            $('input[type="text"], textarea', $el).on('keyup' + ns, function() {
                self._serialize();
                self._renderPreviews();
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
            $(this.watch).off(ns);

            $('.notify-toggle', $el).off(ns);
            $('input[type="text"], textarea', $el).off(ns);
            $('.preview-toggle .toggle-view').off(ns);
            $('.preview-toggle .toggle-edit').off(ns);

            return true;
        }
    });
})(jQuery);
