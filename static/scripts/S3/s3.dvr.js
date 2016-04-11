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
     */
    var clearForm = function(form) {

        clearAlert();
        $('#case_event_label').val('');
        $('#case_event_person__row').remove();
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
        }

        // Cancel-button to clear the form
        $('a.cancel-action').unbind(ns).bind('click' + ns, function(e) {
            e.preventDefault();
            clearForm($(this).closest('form'));
        });


        var labelInput = $('#case_event_label').unbind(ns);

        labelInput.focus().val(labelInput.val());

        // Changing the label resets form
        labelInput.bind('input' + ns, function(e) {
            $('#case_event_person__row').remove();
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
            if ($('#case_event_person__row').length) {
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

        // Clear alert space when launching Zxing
        $('.zxing-button').unbind(ns).bind('click' + ns, function() {
            clearAlert();
        });

    });

}(jQuery));
