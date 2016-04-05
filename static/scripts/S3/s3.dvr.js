/**
 * Static JS for DVR Disaster Victim Registration
 */

// Module pattern to hide internal vars
(function() {

    // Namespace for events
    var ns = '.dvr';

    var clearAlert = function() {
        $('.alert-error, .alert-warning, .alert-info, .alert-success').fadeOut('fast');
    }

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
            clearAlert();
            $('#case_event_label').val('');
            $('#case_event_person__row').remove();
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

        // Clear alert space when scanning
        $('.zxing-button').unbind(ns).bind('click' + ns, function() {
            clearAlert();
        });

    });

}(jQuery));
