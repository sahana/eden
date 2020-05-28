/**
 * jQuery UI Widget for S3Anonymize
 *
 * @copyright 2018-2020 (c) Sahana Software Foundation
 * @license MIT
 *
 * requires jQuery 1.9.1+
 * requires jQuery UI 1.10 widget factory
 */
(function($, undefined) {

    "use strict";
    var anonymizeID = 0;

    /**
     * s3.anonymize
     */
    $.widget('s3.anonymize', {

        /**
         * Default options
         *
         * @prop {string} ajaxURL - the URL to send the anonymize-request to
         * @prop {string} nextURL - the URL to redirect to on success
         */
        options: {

            ajaxURL: null,
            nextURL: null
        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = anonymizeID;
            anonymizeID += 1;

            this.eventNamespace = '.anonymize';
        },

        /**
         * Update the widget options
         */
        _init: function() {

            var el = $(this.element);

            this.container = el.find('.anonymize-dialog');
            this.submitButton = el.find('.anonymize-submit');
            this.cancelButton = el.find('.anonymize-cancel');
            this.confirmCB = el.find('input[name="anonymize_confirm"]').first();

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

            this._bindEvents();
        },

        /**
         * Show the UI dialog to select rules and submit the request
         */
        _showDialog: function() {

            var opts = this.options,
                ns = this.eventNamespace,
                container = this.container,
                cancelButton = this.cancelButton,
                submitButton = this.submitButton,
                confirmCB = this.confirmCB,
                self = this;

            var dialog = container.removeClass('hide').show().dialog({
                autoOpen: false,
                //height: 400,
                //width: 350,
                modal: true,
                closeText: '',
                open: function( /* event, ui */ ) {
                    // Clicking outside of the popup closes it
                    $('.ui-widget-overlay').off(ns).on('click' + ns, function() {
                        dialog.dialog('close');
                    });

                    // Cancel button closes it too, of course
                    cancelButton.off(ns).on('click' + ns, function() {
                        dialog.dialog('close');
                    });

                    // Confirmation checkbox toggles submit button
                    confirmCB.off(ns).on('click' + ns, function() {
                        if ($(this).prop('checked')) {
                            submitButton.prop('disabled', false);
                        } else {
                            submitButton.prop('disabled', true);
                        }
                    });

                    submitButton.off(ns).on('click' + ns, function() {
                        self._anonymize(container).then(
                            function(reload) {
                                // Success
                                container.find('.anonymize-form').hide();
                                container.find('.anonymize-success')
                                         .removeClass('hide')
                                         .show();
                                if (reload) {
                                    try {
                                        S3ClearNavigateAwayConfirm();
                                    } finally {
                                        if (opts.nextURL) {
                                            window.location = opts.nextURL;
                                        } else {
                                            window.location.reload(true);
                                        }
                                    }
                                } else {
                                    dialog.dialog('close');
                                }
                            },
                            function() {
                                // Error
                                dialog.dialog('close');
                            });
                    });

                },
                close: function() {
                    // Reset confirmation checkbox + submit
                    confirmCB.prop('checked', false);
                    submitButton.prop('disabled', true);

                    // Hide the container
                    container.hide();
                }
            });

            dialog.dialog('open');
        },

        /**
         * Send anonymize-request (Ajax)
         *
         * @param {jQuery} container - the container node
         *
         * @returns {promise} - a promise that is resolved when
         *                      the anonymize-request was successful
         */
        _anonymize: function(container) {

            var dfd = $.Deferred();

            // Disable submit + hide cancel
            var cancelButton = this.cancelButton.hide(),
                submitButton = this.submitButton.prop('disabled', true);

            // Show throbber
            var throbber = $('<div class="inline-throbber">').css({
                'display': 'inline-block',
                'margin-left': '1rem'
            }).insertAfter(cancelButton);

            var removeThrobber = function() {
                throbber.remove();
                cancelButton.show();
                submitButton.prop('disabled', false);
            };

            // Get selected options
            var selected = [];
            container.find('.anonymize-rule').each(function() {
                if ($(this).prop('checked')) {
                    selected.push($(this).attr('name'));
                }
            });
            if (!selected.length) {
                return dfd.resolve(false);
            }

            // Request data including action-key
            var key = container.find('input[name="action-key"]').first().val(),
                data = JSON.stringify({
                    'apply': selected,
                    'key': key,
                }),
                url = this.options.ajaxURL;

            $.ajaxS3({
                type: 'POST',
                url: url,
                data: data,
                dataType: 'json',
                contentType: 'application/json; charset=utf-8',
                success: function() {
                    removeThrobber();
                    dfd.resolve(true);
                },
                error: function() {
                    removeThrobber();
                    dfd.reject();
                }
            });

            return dfd.promise();
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var self = this,
                ns = this.eventNamespace;

            $(this.element).find('.anonymize-btn').off(ns).on('click' + ns, function() {
                self._showDialog();
            });

            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var ns = this.eventNamespace;

            $(this.element).off(ns);

            return true;
        }
    });
})(jQuery);
