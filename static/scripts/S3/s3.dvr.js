/**
 * jQuery UI Widget for DVR Case Event Registration / Payment Registration
 *
 * @copyright 2016 (c) Sahana Software Foundation
 * @license MIT
 *
 * requires jQuery 1.9.1+
 * requires jQuery UI 1.10 widget factory
 */
(function($, undefined) {

    "use strict";

    var eventRegistrationID = 0;

    /**
     * eventRegistration, instantiate on event registration form
     */
    $.widget('dvr.eventRegistration', {

        /**
         * Default options
         *
         * @prop {string} tablename - the tablename used for the form
         * @prop {boolean} ajax - data submission using Ajax
         * @prop {string} ajaxURL - the URL to send Ajax requests to
         *
         * @prop {boolean} showPicture - true=always show profile picture
         *                               false=show profile picture on demand
         * @prop {string} showPictureText - button label for "Show Picture"
         * @prop {string} hidePictureText - button label for "Hide Picture"
         */
        options: {

            tablename: 'case_event',
            ajax: null,
            ajaxURL: '',

            showPicture: true,
            showPictureText: 'Show Picture',
            hidePictureText: 'Hide Picture'
        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = eventRegistrationID;
            eventRegistrationID += 1;

            // Namespace for events
            this.eventNamespace = '.eventRegistration';
        },

        /**
         * Update the widget options
         */
        _init: function() {

            // ID prefix for form rows
            this.idPrefix = '#' + this.options.tablename;

            // Hidden input fields
            var form = $(this.element);

            this.flagInfo = form.find('input[type=hidden][name=flags]');
            this.permissionInfo = form.find('input[type=hidden][name=permitted]');
            this.actionableInfo = form.find('input[type=hidden][name=actionable]');
            this.eventType = form.find('input[type="hidden"][name="event"]');
            this.blockingInfo = form.find('input[type="hidden"][name="intervals"]');
            this.actionDetails = form.find('input[type="hidden"][name="actions"]');
            this.imageURL = form.find('input[type="hidden"][name="image"]');

            // Get blocked events from hidden input
            var intervals = this.blockingInfo.val();
            if (intervals) {
                this.blockedEvents = JSON.parse(intervals);
            } else {
                this.blockedEvents = {};
            }
            this.blockingMessage = null;

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

            var opts = this.options,
                prefix = this.idPrefix;

            this._unbindEvents();

            // Enable Ajax if we have an AjaxURL
            if (opts.ajaxURL && opts.ajax === null) {
                opts.ajax = true;
            }

            // Show flag info at start
            this._showFlagInfo();

            // Show profile picture at start
            this._showProfilePicture();

            // Enable styles on details row
            $(this.element).find(prefix + '_details__row .controls').addClass('has-details');

            // Show action details, if any
            if (this.actionDetails.length) {
                var actionData = JSON.parse(this.actionDetails.val());
                if (actionData.length) {
                    this._showDetails(true);
                } else {
                    this._hideDetails();
                }
            } else {
                this._hideDetails();
            }

            // Check blocked events at start
            if (!this._checkBlockedEvents()) {
                this._toggleSubmit(false);
            }

            // Focus on label input at start
            var labelInput = $(prefix + '_label');
            labelInput.focus().val(labelInput.val());

            this._bindEvents();
        },

        /**
         * Ajax method to identify the person from the label
         */
        _checkID: function() {

            this._clearAlert();

            var form = $(this.element),
                prefix = this.idPrefix,
                labelInput = $(prefix + '_label'),
                label = labelInput.val().trim();

            // Update label input with trimmed value
            labelInput.val(label);

            if (!label) {
                return;
            }

            var input = {'l': label, 'c': true},
                ajaxURL = this.options.ajaxURL,
                // Clear the person info
                personInfo = $(prefix + '_person__row .controls').empty(),
                // Show a throbber
                throbber = $('<div class="inline-throbber">').insertAfter(personInfo),
                self = this;

            // Remove profile picture
            this._removeProfilePicture();

            // Clear action details
            this._clearDetails();

            // Send the ajax request
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
                        // Show error message on ID field
                        var msg = $('<div class="error_wrapper"><div id="label__error" class="error" style="display: block;">' + data.e + '</div></div>').hide();
                        msg.insertAfter($(prefix + '_label')).slideDown();

                    } else {

                        // Show the person details
                        personInfo.html(data.p).removeClass('hide').show();

                        // Update flag info
                        var flagInfo = self.flagInfo;
                        if (data.f) {
                            flagInfo.val(JSON.stringify(data.f));
                        } else {
                            flagInfo.val('[]');
                        }

                        // Update permission info
                        var permissionInfo = self.permissionInfo;
                        if (data.s !== undefined) {
                            permissionInfo.val(JSON.stringify(data.s));
                        } else {
                            permissionInfo.val('false');
                        }

                        // Update actionable info
                        var actionableInfo = self.actionableInfo,
                            actionable = data.u;
                        if (actionableInfo.length) {
                            if (actionable !== undefined) {
                                actionableInfo.val(JSON.stringify(data.u));
                            } else {
                                actionable = true;
                                actionableInfo.val('true');
                            }
                        }

                        // Render details
                        if (data.d) {
                            self._updateDetails(data.d, actionable);
                        }

                        if (data.b) {
                            self.imageURL.val(data.b);
                            self._showProfilePicture();
                        }

                        // Update blocked events
                        self.blockedEvents = data.i || {};
                        self.blockingInfo.val(JSON.stringify(self.blockedEvents));

                        // Attempt to enable submit if we have a valid event type
                        // - this will automatically check whether the registration is
                        //   permitted, actionable and not blocked due to minimum intervals
                        if (self.eventType.val()) {
                            self._toggleSubmit(true);
                        }

                        // Show the flag info
                        self._showFlagInfo();
                    }

                    // Show alerts
                    if (data.a) {
                        S3.showAlert(data.a, 'error');
                    } else if (data.m) {
                        S3.showAlert(data.m, 'success');
                    }

                },
                'error': function () {

                    // Remove throbber
                    throbber.remove();

                    // Clear the form, but keep the alert
                    self._clearForm(true);
                }
            });
        },

        /**
         * Ajax method to register the event
         */
        _registerEvent: function() {

            this._clearAlert();

            var prefix = this.idPrefix,
                label = $(prefix + '_label').val(),
                event = this.eventType.val();

            if (!label || !event) {
                return;
            }

            var input = {'l': label, 't': event},
                ajaxURL = this.options.ajaxURL,
                // Don't clear the person info just yet
                personInfo = $(prefix + '_person__row .controls'),
                // Show a throbber
                throbber = $('<div class="inline-throbber">').insertAfter(personInfo),
                self = this;

            // Add action data (if any) to request JSON
            var actionDetails = this.actionDetails;
            if (actionDetails.length) {
                actionDetails = actionDetails.val();
                if (actionDetails) {
                    input.d = JSON.parse(actionDetails);
                } else {
                    input.d = [];
                }
            }

            // Add comments to request JSON
            input.c = $(prefix + 'comments').val();

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
                        // Show error message on ID field
                        var msg = $('<div class="error_wrapper"><div id="label__error" class="error" style="display: block;">' + data.e + '</div></div>').hide();
                        msg.insertAfter($(prefix + '_label')).slideDown();

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
         * Helper method to check for blocked events and show message
         */
        _checkBlockedEvents: function() {

            // Get current event type and blocked events
            var event = this.eventType.val(),
                blocked = this.blockedEvents,
                info = blocked[event];

            // Remove existing message, if any
            if (this.blockingMessage) {
                this.blockingMessage.remove();
            }
            if (info) {
                // Check the date
                var message = $('<h6>').addClass('event-registration-blocked')
                                       .html(info[0]),
                    date = new Date(info[1]),
                    now = new Date();
                if (date > now) {
                    // Event registration is blocked, show message and return
                    this.blockingMessage = $('<div>').addClass('small-12-columns')
                                                     .append(message)
                                                     .prependTo($('#submit_record__row'));
                    return false;
                }
            }
            return true;
        },

        /**
         * Helper function to show flag infos
         */
        _showFlagInfo: function() {

            var flagInfo = this.flagInfo,
                prefix = this.idPrefix,
                flagInfoContainer = $(prefix + '_flaginfo__row .controls').empty();

            if (flagInfo.length) {
                flagInfo = JSON.parse(flagInfo.val());
            } else {
                flagInfo = [];
            }

            var numFlags = flagInfo.length;
            if (numFlags) {

                flagInfoContainer.addClass('has-flaginfo');

                var advise = $('<div class="checkpoint-advise">').hide().appendTo(flagInfoContainer),
                    flag,
                    instructions;

                for (var i=0; i < numFlags; i++) {

                    flag = flagInfo[i];
                    instructions = $('<div class="checkpoint-instructions">').appendTo(advise);

                    $('<h4>' + flag.n + '</h4>').appendTo(instructions);
                    if (flag.i) {
                        $('<p>' + flag.i + '</p>').appendTo(instructions);
                    }
                }
                advise.slideDown();
            }
        },

        /**
         * Render a panel to show the profile picture (automatically loads
         * the picture if options.showPicture is true)
         */
        _showProfilePicture: function() {

            var el = $(this.element),
                opts = this.options,
                imageURL = this.imageURL.val();

            this._removeProfilePicture();

            if (!imageURL) {
                return;
            }

            var button = $('<button class="tiny secondary button toggle-picture" type="button">'),
                buttonRow = $('<div class="button-row">').append(button);
            button.text(opts.showPictureText);

            var panel = $('<div class="panel profile-picture">');
            panel.append(buttonRow)
                 .data('url', imageURL)
                 .appendTo(el);

            if (opts.showPicture) {
                this._togglePicture();
            }
        },

        /**
         * Remove the profile picture panel
         */
        _removeProfilePicture: function() {

            this.imageURL.val('');
            $(this.element).find('.panel.profile-picture').remove();
        },

        /**
         * Show or hide the profile picture (click handler for toggle button)
         */
        _togglePicture: function() {

            var el = $(this.element),
                opts = this.options,
                container = el.find('.panel.profile-picture');

            if (container.length) {
                var imageRow = container.find('.image-row'),
                    imageURL = container.data('url'),
                    toggle = container.find('button.toggle-picture');

                if (imageRow.length) {
                    imageRow.remove();
                    toggle.text(opts.showPictureText);
                } else {
                    if (imageURL) {
                        var image = $('<img>').attr('src', imageURL);
                        imageRow = $('<div class="image-row">').append(image);
                        container.prepend(imageRow);
                        toggle.text(opts.hidePictureText);
                    }
                }
            }
        },

        /**
         * Helper function to hide the details form fields
         */
        _hideDetails: function() {

            var prefix = this.idPrefix,
                hasPersonInfo = $(prefix + '_person__row .controls').text();

            if (hasPersonInfo) {
                // Retain the details (showing empty-message)
                $(prefix + '_details__row').show();
            } else {
                // Hide the details if there are no person data
                $(prefix + '_details__row').hide();
            }

            // Hide all other details
            $(prefix + '_date__row').hide();
            $(prefix + '_comments__row').hide();
        },

        /**
         * Helper function to show the details form fields
         *
         * @param {bool} actionable - whether there are any actionable details
         */
        _showDetails: function(actionable) {

            var prefix = this.idPrefix;

            $(prefix + '_details__row').show();
            if (actionable) {
                $(prefix + '_date__row').show();
                $(prefix + '_comments__row').show();
            }
        },

        /**
         * Helper function to update the action details in the form
         *
         * @param {object} data - the action details as dict
         * @param {bool} actionable - whether there are any actionable details
         */
        _updateDetails: function(data, actionable) {

            var prefix = this.idPrefix,
                detailsContainer = $(prefix + '_details__row .controls'),
                dateContainer = $(prefix + '_date__row .controls');

            // Update the hidden input
            var actionDetails = this.actionDetails;
            if (actionDetails.length) {
                if (data.h !== '') {
                    actionDetails.val(JSON.stringify(data.h));
                } else {
                    actionDetails.val('[]');
                }
            }

            // Update the visible form fields
            $(prefix + '_details__row .controls').html(data.d);
            $(prefix + '_date__row .controls').html(data.t);

            // Show the form fields
            this._showDetails(actionable);
        },

        /**
         * Helper function to clear the details form fields
         */
        _clearDetails: function() {

            var prefix = this.idPrefix;

            this._hideDetails();

            // Reset flag info and permission info
            this.flagInfo.val('[]');
            this.permissionInfo.val('false');
            $(prefix + '_flaginfo__row .controls').empty();

            // Remove action details, date and comments
            $(prefix + '_details__row .controls').empty();
            $(prefix + '_date__row .controls').empty();
            $(prefix + '_comments').val('');

            // Remove blocked events and message
            this.blockedEvents = {};
            if (this.blockingMessage) {
                this.blockingMessage.remove();
            }
            this.blockingInfo.val(JSON.stringify(this.blockedEvents));
        },

        /**
         * Helper function to toggle the submit mode of the form
         *
         * @param {bool} submit - true to enable event registration while disabling
         *                        the ID check button, false vice versa
         */
        _toggleSubmit: function(submit) {

            var form = $(this.element),
                buttons = ['.check-btn', '.submit-btn'],
                permissionInfo = this.permissionInfo,
                actionableInfo = this.actionableInfo;

            if (submit) {

                var permitted = false,
                    actionable = false;

                // Check whether form action is permitted
                if (permissionInfo.length) {
                    permissionInfo = permissionInfo.val();
                    if (permissionInfo) {
                        permitted = JSON.parse(permissionInfo);
                    }
                }

                // Check whether the form is actionable
                if (permitted) {
                    actionable = true;
                    if (actionableInfo.length) {
                        actionableInfo = actionableInfo.val();
                        if (actionableInfo) {
                            actionable = JSON.parse(actionableInfo);
                        }
                    }
                }

                // Check blocked events
                if (permitted && actionable) {
                    actionable = this._checkBlockedEvents();
                }

                // Only enable submit if permitted and actionable
                if (permitted && actionable) {
                    buttons.reverse();
                }
            }

            var active = form.find(buttons[0]),
                disabled = form.find(buttons[1]);

            disabled.prop('disabled', true).hide().insertAfter(active);
            active.prop('disabled', false).hide().removeClass('hide').show();
        },

        /**
         * Helper function to hide any alert messages that are currently shown
         */
        _clearAlert: function() {

            $('.alert-error, .alert-warning, .alert-info, .alert-success').fadeOut('fast');
            $('.error_wrapper').fadeOut('fast').remove();
        },

        /**
         * Helper function to remove the person data and empty the label input,
         * also re-enabling the ID check button while hiding the registration button
         *
         * @param {bool} keepAlerts - do not clear the alert space
         * @param {bool} keepLabel - do not clear the label input field
         */
        _clearForm: function(keepAlerts, keepLabel) {

            var prefix = this.idPrefix;

            // Remove all throbbers
            $('.inline-throbber').remove();

            // Clear alerts
            if (!keepAlerts) {
                this._clearAlert();
            }

            // Clear ID label
            if (!keepLabel) {
                $(prefix + '_label').val('');
            }

            // Hide person info
            $(prefix + '_person__row .controls').hide().empty();

            // Remove profile picture
            this._removeProfilePicture();

            // Clear details
            this._clearDetails();

            // Disable submit
            this._toggleSubmit(false);
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var form = $(this.element),
                prefix = this.idPrefix,
                ns = this.eventNamespace,
                self = this;

            // Events for outside elements
            var zxingButton = $('.zxing-button'),
                eventTypeToggle = $('#event-type-toggle'),
                eventTypeSelector = $('#event-type-selector');

            if (navigator.userAgent.toLowerCase().indexOf("android") == -1) {
                // Disable Zxing-button if not Android
                zxingButton.addClass('disabled').click(function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                });
            } else {
                // Clear alert space when launching Zxing
                zxingButton.bind('click' + ns, function() {
                    self._clearAlert();
                });
            }

            // Toggle event type selector
            eventTypeToggle.bind('click' + ns, function() {
                self._clearAlert();
                if (eventTypeSelector.hasClass('hide')) {
                    eventTypeSelector.hide().removeClass('hide').slideDown();
                } else {
                    eventTypeSelector.slideToggle();
                }
            });

            // Select event type
            eventTypeSelector.find('a.event-type-selector').bind('click' + ns, function() {

                var $this = $(this),
                    code = $this.data('code'),
                    name = $this.data('name');

                // Store new event type in form
                $('input[type="hidden"][name="event"]').val(code);

                // Update event type in header
                $('.event-type-name').text(name);

                // Enable submit if we have a person
                if ($(prefix + '_person__row .controls').text()) {
                    self._toggleSubmit(true);
                }

                // Update Zxing URL
                zxingButton.each(function() {
                    var $zxing = $(this),
                        urlTemplate = $zxing.data('tmp');
                    if (urlTemplate) {
                        $zxing.attr('href', urlTemplate.replace('%7BEVENT%7D', code));
                    }
                });

                // Hide event type selector
                eventTypeSelector.slideUp();
            });

            form.delegate('.toggle-picture', 'click' + ns, function(e) {
                e.preventDefault();
                self._togglePicture();
            });

            // Cancel-button to clear the form
            form.find('a.cancel-action').bind('click' + ns, function(e) {
                e.preventDefault();
                self._clearForm();
            });

            if (this.options.ajax) {
                // Click-Handler for Check-ID button
                form.find('.check-btn').bind('click' + ns, function(e) {
                    e.preventDefault();
                    self._checkID();
                });
                // Click-Handler for Register button
                form.find('.submit-btn').unbind(ns).bind('click' + ns, function(e) {
                    e.preventDefault();
                    self._registerEvent();
                });
            }

            // Events for the label input
            var labelInput = $(prefix + '_label');

            // Changing the label resets form
            labelInput.bind('input' + ns, function(e) {
                self._clearForm(false, true);
            });

            // Key events for label field
            labelInput.bind('keyup' + ns, function(e) {
                switch (e.which) {
                    case 27:
                        // Pressing ESC resets the form
                        self._clearForm();
                        break;
                    default:
                        break;
                }
            });

            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var form = $(this.element),
                ns = this.eventNamespace,
                prefix = this.idPrefix;

            $('.zxing-button').unbind(ns).unbind('click');
            $('#event-type-toggle').unbind(ns);
            $('#event-type-selector').find('a.event-type-selector').unbind(ns);

            $(prefix + '_label').unbind(ns);

            form.find('a.cancel-action').unbind(ns);

            form.find('.check-btn').unbind(ns);

            form.find('.submit-btn').unbind(ns);

            form.undelegate(ns);

            return true;
        }
    });
})(jQuery);
