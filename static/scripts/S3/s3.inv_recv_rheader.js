/**
 * Used by inv_recv_rheader for action buttons
 * - handle confirmation
 * - send POST requests not GET
 */

$(document).ready(function() {

    var ajaxURL,
        $button,
        buttonID,
        buttons = ['recv-process',
                   'recv-cancel'
                   ],
        buttonsLength = buttons.length,
        message;

    for (var i = 0; i < buttonsLength; i++) {
        buttonID = buttons[i];
        $button = $('#' + buttonID);
        if ($button.length) {
            $button.on('click.s3', function(event) {
                message = i18n[$(this).attr('id').replace('-', '_') + '_confirm'];
                event.preventDefault();
                if (confirm(message)) {
                    // Send request as a POST
                    ajaxURL = $(this).attr('href') + '.json';
                    $.ajaxS3({
                        url: ajaxURL,
                        dataType: 'json',
                        method : 'POST',
                        success: function(data) {
                            // Load the page requested by the call
                            location = data.tree;
                        }
                    });
                } else {
                    return false;
                }
            });
        }
    }
});