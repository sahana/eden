/**
 * jQuery UI Widget for Shelter Inspection (used by CRShelterInspection)
 *
 * @copyright 2017-2020 (c) Sahana Software Foundation
 * @license MIT
 */
(function($, undefined) {

    "use strict";
    var shelterInspectionID = 0;

    /**
     * shelterInspection
     */
    $.widget('s3.shelterInspection', {

        /**
         * Default options
         *
         * @prop {string} ajaxURL - the URL to send Ajax requests to
         */
        options: {
            ajaxURL: ''
        },

        /**
         * Create the widget
         */
        _create: function() {

            var el = $(this.element);

            this.id = shelterInspectionID;
            shelterInspectionID += 1;

            this.eventNamespace = '.shelterInspection';
        },

        /**
         * Update the widget options
         */
        _init: function() {

            var el = $(this.element);

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

            var opts = this.options;

            this._unbindEvents();

            // Disable submit until housing unit selected
            this._toggleSubmit(false);

            this._bindEvents();
        },

        /**
         * Ajax method to register the inspection results
         */
        _registerInspection: function() {

            var opts = this.options,
                ajaxURL = opts.ajaxURL;

            // Clear any previous alert
            this._clearAlert();

            // Show throbber
            var throbber = $('<div class="inline-throbber">').insertBefore('#submit_record__row');

            // Collect the input
            var input = {
                u: $('#shelter_inspection_shelter_unit_id').val(),
                f: $('#shelter_flags-options').val(),
                c: $('#shelter_inspection_comments').val()
            };

            // Send Ajax
            var self = this;
            $.ajaxS3({
                'url': ajaxURL,
                'type': 'POST',
                'dataType': 'json',
                'contentType': 'application/json; charset=utf-8',
                'data': JSON.stringify(input),
                'success': function(data) {

                    // Remove the throbber
                    throbber.remove();

                    if (data.e) {
                        // Show error message?

                    } else {
                        // Done - clear the form
                        self._clearForm();
                    }

                    // Show alert/confirmation message
                    if (data.a) {
                        S3.showAlert(data.a, 'error', false);
                    } else if (data.m) {
                        S3.showAlert(data.m, 'success', false);
                    }
                },
                'error': function () {

                    // Remove the throbber
                    throbber.remove();

                    // Clear the form, but keep the alert
                    this._clearForm(true);
                }
            });
        },

        /**
         * Helper function to toggle the submit mode of the form
         *
         * @param {bool} submit - true to enable submit
         */
        _toggleSubmit: function(submit) {

            if (submit) {
                $('.submit-btn').removeClass('disabled')
                                .prop('disabled', false);
            } else {
                $('.submit-btn').addClass('disabled')
                                .prop('disabled', true);
            }
        },

        /**
         * Helper function to hide any alert messages that are currently shown
         */
        _clearAlert: function() {

            $('.alert-error, .alert-warning, .alert-info, .alert-success').fadeOut('fast');
            $('.error_wrapper').fadeOut('fast').remove();
        },

        /**
         * Helper function to reset the form
         *
         * @param {bool} keepAlert - do not clear the alert space
         */
        _clearForm: function(keepAlert) {

            // Remove all throbbers
            $('.inline-throbber').remove();

            // Clear alerts
            if (!keepAlert) {
                this._clearAlert();
            }

            // Reset shelter unit selector
            var unitSelector = $('#shelter_inspection_shelter_unit_id');
            unitSelector.val('');
            if (unitSelector.hasClass('multiselect-widget')) {
                unitSelector.multiselect('refresh');
            }

            // Reset shelter flags
            var flags = $('#shelter_flags-options');
            flags.val('');
            if (flags.hasClass('groupedopts-widget')) {
                flags.groupedopts('refresh');
            }

            // Clear comments field
            $('#shelter_inspection_comments').val('');

            // Disable submit until housing unit selected
            this._toggleSubmit(false);
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var form = $(this.element),
                ns = this.eventNamespace,
                self = this;

            // Toggle submit dependent on housing unit selection
            $('#shelter_inspection_shelter_unit_id').bind('change' + ns, function() {
                if ($(this).val()) {
                    self._toggleSubmit(true);
                } else {
                    self._toggleSubmit(false);
                }
            });

            // Click-Handler for Submit-button
            form.find('.submit-btn').bind('click' + ns, function(e) {
                e.preventDefault();
                self._registerInspection();
            });

            // Cancel-button to clear the form
            form.find('a.cancel-action').bind('click' + ns, function(e) {
                e.preventDefault();
                self._clearForm();
            });

            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var form = $(this.element),
                ns = this.eventNamespace;

            $('#shelter_inspection_shelter_unit_id').unbind(ns);

            form.find('.submit-btn').unbind(ns);

            form.find('a.cancel-action').unbind(ns);

            return true;
        }
    });
})(jQuery);
