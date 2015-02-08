/**
 * Used by the Compose function in Messaging (modules/s3msg.py)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

/* Global vars */
//S3.msg = Object();

$(document).ready(function() {
    var contact_method = $('#msg_outbox_pr_message_method');
    if (contact_method.val() != 'EMAIL') {
        // SMS/Tweets don't have subjects
        $('#msg_log_subject__row').hide();
    }
    contact_method.change(function() {
        if ($(this).val() == 'EMAIL') {
            // Emails have a Subject
            $('#msg_log_subject__row').show();
        } else {
            $('#msg_log_subject__row').hide();
        }
    });
});