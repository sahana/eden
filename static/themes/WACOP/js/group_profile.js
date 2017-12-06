$(document).ready(function() {
    $('#notify_email, #notify_immediately, #notify_daily').change(function() {
        // Submit Data
        var notify = $('#notify_email').is(':checked') ? 1 : 0,
            url = S3.Ap.concat('/pr/forum/' + $('#notify_settings').data('forum_id') + '/notify_settings');
        var options = {
            data: {'email': notify,
                   'frequency': $('input[name=frequency]:checked', '#notify_settings').val()
                   },
            type: 'POST',
            url: url,
            success: function(e) {
                // Nothing we need to do here
            }
        };
        $.ajaxS3(options);
    });
});