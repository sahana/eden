/**
 * Static JS for DVR Disaster Victim Registration
 */

// Module pattern to hide internal vars
(function() {

    "use strict";

    // Namespace for events
    var ns = '.dvr';

    /**
     * Helper function to hide any alert messages that are currently shown
     */
    var clearAlert = function() {

        $('.alert-error, .alert-warning, .alert-info, .alert-success').fadeOut('fast');
        $('.error_wrapper').fadeOut('fast').remove();
    };

    /**
     * Helper function to toggle the submit mode of the form
     *
     * @param {jQuery} form - the form node
     * @param {bool} submit - true to enable event registration while disabling
     *                        the ID check button, false vice versa
     */
    var toggleSubmit = function(form, submit) {

        var buttons = ['.check-btn', '.submit-btn'];
        if (submit) {
            buttons.reverse();
        }

        var $form = $(form),
            active = $form.find(buttons[0]),
            disabled = $form.find(buttons[1]);

        disabled.prop('disabled', true).hide().insertAfter(active);
        active.prop('disabled', false).hide().removeClass('hide').show();
    };

    /**
     * Helper function to remove the person data and empty the label input,
     * also re-enabling the ID check button while hiding the registration button
     *
     * @param {jQuery} form - the form node
     * @param {bool} keepAlerts - do not clear the alert space
     */
    var clearForm = function(form, keepAlerts) {

        if (!keepAlerts) {
            clearAlert();
        }
        $('#case_event_label').val('');
        $('#case_event_person__row .controls').hide().empty();
        toggleSubmit(form, false);
    };

    /**
     * Actions on jQuery-ready, configure event handlers for page elements
     */
    $(document).ready(function() {

        // Disable Zxing-button if not Android
        if (navigator.userAgent.toLowerCase().indexOf("android") == -1) {
            $('.zxing-button').addClass('disabled').unbind('click').click(function(e) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            });
        } else {
            // Clear alert space when launching Zxing
            $('.zxing-button').unbind(ns).bind('click' + ns, function() {
                clearAlert();
            });
        }

        // Toggle event type selector
        $('.event-type-toggle').unbind(ns).bind('click' + ns, function() {
            var selector = $('ul.event-type-selector');
            if (selector.hasClass('hide')) {
                selector.hide().removeClass('hide').slideDown();
            } else {
                selector.slideToggle();
            }
        });

        // Select event type
        $('a.event-type-selector').unbind(ns).bind('click' + ns, function() {
            var self = $(this),
                code = self.data('code'),
                name = self.data('name');
            // Store new event type in form
            $('input[type="hidden"][name="event"]').val(code);
            // Update event type in header
            $('.event-type-name').text(name);
            // Enable submit if we have a person
            if ($('#case_event_person__row .controls').text()) {
                toggleSubmit($('form'), true);
            }
            // Update Zxing URL
            $('.zxing-button').each(function() {
                var $this = $(this),
                    urlTemplate = $this.data('tmp');
                if (urlTemplate) {
                    $this.attr('href', urlTemplate.replace('%7BEVENT%7D', code));
                }
            });
            // Hide event type selector
            self.closest('ul.event-type-selector').slideUp();
        });

        var labelInput = $('#case_event_label').unbind(ns);

        // Focus on ID input at start
        labelInput.focus().val(labelInput.val());

        // Changing the label resets form
        labelInput.bind('input' + ns, function(e) {
            clearAlert();
            $('#case_event_person__row .controls').hide().empty();
            toggleSubmit($(this).closest('form'), false);
        });

        // Key events for label field
        labelInput.bind('keyup' + ns, function(e) {
            switch (e.which) {
                case 27:
                    // Pressing ESC resets the form
                    clearForm($(this).closest('form'));
                    break;
                default:
                    break;
            }
        });

        // Cancel-button to clear the form
        $('a.cancel-action').unbind(ns).bind('click' + ns, function(e) {
            e.preventDefault();
            clearForm($(this).closest('form'));
        });

        var personInfo = $('#case_event_person__row .controls');

        // Click-Handler for Check-ID button
        $('.check-btn').unbind(ns).bind('click' + ns, function(e) {

            e.preventDefault();
            clearAlert();

            var label = $('#case_event_label').val();
            if (!label) {
                return;
            }

            var input = {'l': label, 'c': true},
                ajaxURL = S3.Ap.concat('/dvr/case_event/register.json');

            // Clear person info, show throbber
            personInfo.empty();
            var throbber = $('<div class="inline-throbber">').insertAfter(personInfo);

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
                        msg.insertAfter($('#case_event_label')).slideDown();

                    } else {
                        // Show the person details
                        personInfo.html(data.p).removeClass('hide').show();
                        // Enable submit if we have a valid event type
                        if ($('input[type="hidden"][name="event"]').val()) {
                            toggleSubmit($('form'), true);
                        }
                    }

                    // Show alerts
                    if (data.a) {
                        S3.showAlert(data.a, 'error');
                    } else if (data.m) {
                        S3.showAlert(data.m, 'success');
                    }

                },
                'error': function () {

                    // Clear the form, but keep the alert
                    throbber.remove();
                    clearForm($('form'), true);
                }
            });
        });

        $('.submit-btn').unbind(ns).bind('click' + ns, function(e) {

            e.preventDefault();
            clearAlert();

            var label = $('#case_event_label').val(),
                event = $('input[type="hidden"][name="event"]').val();
            if (!label || !event) {
                return;
            }
            var input = {'l': label, 't': event},
                ajaxURL = S3.Ap.concat('/dvr/case_event/register.json');

            // Show throbber (don't clear person info just yet)
            var throbber = $('<div class="inline-throbber">').insertAfter(personInfo);

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
                        msg.insertAfter($('#case_event_label')).slideDown();

                    } else {
                        // Done - clear the form
                        clearForm($('form'));
                    }

                    if (data.a) {
                        S3.showAlert(data.a, 'error', false);
                    } else if (data.m) {
                        S3.showAlert(data.m, 'success', false);
                    }

                },
                'error': function () {

                    // Clear the form, but keep the alert
                    throbber.remove();
                    clearForm($('form'), true);
                }
            });
        });
    });

}(jQuery));
