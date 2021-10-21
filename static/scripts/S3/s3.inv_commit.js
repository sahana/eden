/**
 * Used by inv/commit() for action buttons
 * - send POST requests not GET
 */

$(document).ready(function() {

    // Need to wait for Action buttons to be rendered before we can add the event
    S3.dataTables.initComplete = function() {
        $('.send-btn').on('click.s3', function(event) {
            event.preventDefault();
            // Send request as a POST
            var ajaxURL = $(this).attr('href') + '.json';
            $.ajaxS3({
                url: ajaxURL,
                dataType: 'json',
                method : 'POST',
                success: function(data) {
                    // Load the page requested by the call
                    location = data.tree;
                }
            });
        });
    };
});