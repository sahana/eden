/**
 * Used by the Compose function in Messaging (modules/s3msg.py)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

/* Global vars */
//S3.msg = Object();

function s3_msg_ac_pe_input() {
    // Hide the real Input Field
    $('#msg_outbox_pe_id').hide();
    // Autocomplete-enable the Dummy Input
    $('#dummy').autocomplete({
        source: S3.msg_search_url,
        minLength: 2,
        focus: function( event, ui ) {
            $( '#dummy' ).val( ui.item.name );
            return false;
        },
        select: function( event, ui ) {
            $( '#dummy_input' ).val( ui.item.name );
            $( '#msg_outbox_pe_id' ).val( ui.item.id );
            return false;
        }
    })
    .data( 'autocomplete' )._renderItem = function( ul, item ) {
        return $( '<li></li>' )
            .data( 'item.autocomplete', item )
            .append( '<a>' + item.name + '</a>' )
            .appendTo( ul );
    };
}
 
$(document).ready(function() {
    if ($('#msg_outbox_pr_message_method').val() != 'EMAIL') {
        // SMS/Tweets don't have subjects
        $('#msg_log_subject__row').hide();
    }
    $('#msg_outbox_pr_message_method').change(function() {
        if ($(this).val() == 'EMAIL') {
            // Emails have a Subject
            $('#msg_log_subject__row').show();
        } else {
            $('#msg_log_subject__row').hide();
        }
    });
});