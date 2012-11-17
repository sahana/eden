/* JS code to modify req/create forms
   - inserted into page in req_create_form_mods()
*/
function idescape(input) {
    // Create a valid ID
    var output = input.replace(/ /g, 'SPACE')
                      .replace(/&/g, 'AMP');
    return output;
}

$(document).ready(function() {
    
    var span = '<span class="req"> *</span>';

    function type_9() {
        // Other
        $('.summary_item').remove();
        req_req_sub_defaultreq_item__row1
        $('#req_req_sub_defaultreq_item__row1').hide();
        $('#req_req_sub_defaultreq_item__row').hide();
        $('#req_req_sub_defaultreq_skill__row1').hide();
        $('#req_req_sub_defaultreq_skill__row').hide();
        $('#req_req_date_required_until__row1').hide();
        $('#req_req_date_required_until__row').hide();
        $('#req_req_purpose__row1 label').html(i18n.req_purpose + ':');
        $('#req_req_site_id__row1 label').html(i18n.req_site_id + ':' + span);
        $('#req_req_request_for_id__row1 label').html(i18n.req_request_for_id + ':');
        $('#req_req_recv_by_id__row1 label').html(i18n.req_recv_by_id + ':');
        $('#req_req_purpose__row1').show();
        $('#req_req_purpose__row').show();
    }

    function type_8() {
        // Summary
        $('#req_req_sub_defaultreq_item__row1').hide();
        $('#req_req_sub_defaultreq_item__row').hide();
        $('#req_req_sub_defaultreq_skill__row1').hide();
        $('#req_req_sub_defaultreq_skill__row').hide();
        $('#req_req_date_required_until__row1').hide();
        $('#req_req_date_required_until__row').hide();
        $('#req_req_site_id__row1 label').html(i18n.req_site_id + ':' + span);
        $('#req_req_request_for_id__row1 label').html(i18n.req_request_for_id + ':');
        $('#req_req_recv_by_id__row1 label').html(i18n.req_recv_by_id + ':');
        // Replace the Purpose field with a list of checkboxes
        $('#req_req_purpose__row1').hide();
        $('#req_req_purpose__row').hide();
        $('.summary_item').remove(); // If populated by server
        for (var i=0; i < req_summary_items.length; i++) {
            var item = req_summary_items[i];
            var row = '<tr class="summary_item"><td>' + item + '</td><td><input type="checkbox" id="req_summary_' + idescape(item) + '"></td></tr>';
            $('#req_req_purpose__row').after(row);
        }
    }

    function type_next(type) {
        // Items or People/Skills
        if (type == 1) {
            // Items
            $('#req_req_date_required_until__row1').hide();
            $('#req_req_date_required_until__row').hide();
            $('#req_req_sub_defaultreq_item__row1').show();
            $('#req_req_sub_defaultreq_item__row').show();
            $('#req_req_sub_defaultreq_skill__row1').hide();
            $('#req_req_sub_defaultreq_skill__row').hide();
            $('#req_req_purpose__row1 label').html(i18n.req_items_purpose + ':');
            $('#req_req_site_id__row1 label').html(i18n.req_items_site_id + ':' + span);
            $('#req_req_request_for_id__row1 label').html(i18n.req_items_recv_by_id + ':');
            $('#req_req_recv_by_id__row1 label').html(i18n.req_items_recv_by_id + ':');
        } else if (type == 3) {
            // People/Skills
            $('#req_req_sub_defaultreq_item__row1').hide();
            $('#req_req_sub_defaultreq_item__row').hide();
            $('#req_req_sub_defaultreq_skill__row1').show();
            $('#req_req_sub_defaultreq_skill__row').show();
            if ($('#req_req_is_template').is(':checked')) {
                // pass
            } else {
                $('#req_req_date_required_until__row1').show();
                $('#req_req_date_required_until__row').show();
            }
            $('#req_req_purpose__row1 label').html(i18n.req_people_purpose + ':');
            $('#req_req_site_id__row1 label').html(i18n.req_people_site_id + ':' + span);
            $('#req_req_request_for_id__row1 label').html(i18n.req_people_recv_by_id + ':');
            $('#req_req_recv_by_id__row1 label').html(i18n.req_people_recv_by_id + ':');
        }
        $('.summary_item').remove();
        $('#req_req_purpose__row1').show();
        $('#req_req_purpose__row').show();
    }

    // Initial settings
    var type = $('#req_req_type').val();
    if (type == undefined) {
        type = getUrlVars().type
    }
    if (type == 9) {
        type_9();
    } else if (type == 8) {
        type_8();
    } else {
        type_next(type);
    }

    // onChange
    $('#req_req_type').change(function() {
        var type = $('#req_req_type').val();
        if (type == 9) {
            type_9();
        } else if (type == 8) {
            type_8();
        } else {
            type_next(type);
        }
    });
    $('#req_req_is_template').change(function() {
        if ($('#req_req_is_template').is(':checked')) {
            $('#req_req_date__row1').hide();
            $('#req_req_date__row').hide();
            $('#req_req_date_required__row1').hide();
            $('#req_req_date_required__row').hide();
            $('#req_req_date_required_until__row1').hide();
            $('#req_req_date_required_until__row').hide();
            $('#req_req_recv_by_id__row1').hide();
            $('#req_req_recv_by_id__row').hide();
        } else {
            $('#req_req_date__row1').show();
            $('#req_req_date__row').show();
            $('#req_req_date_required__row1').show();
            $('#req_req_date_required__row').show();
            $('#req_req_recv_by_id__row1').show();
            $('#req_req_recv_by_id__row').show();
            var type = $('#req_req_type').val();
            if (type == 3) {
                $('#req_req_date_required_until__row1').show();
                $('#req_req_date_required_until__row').show();
            }
        }
    });

    // onSubmit
    $('form').submit(function() {
        // Do the normal form-submission tasks
        // @ToDo: Look to have this happen automatically
        // http://forum.jquery.com/topic/multiple-event-handlers-on-form-submit
        // http://api.jquery.com/bind/
        S3ClearNavigateAwayConfirm();

        var type = $('#req_req_type').val();
        if (type == 9) {
            // Other
            if ($('#req_req_comments').val() == i18n.req_other_msg) {
                // Default help still showing
                // Requests of type 'Other' need this field to be mandatory
                $('#req_req_comments').after('<div id="type__error" class="error" style="display: block;">i18n.req_details_mandatory</div>');
                // Reset the Navigation protection
                S3SetNavigateAwayConfirm();
                // Move focus to this field
                $('#req_req_comments').focus();
                // Prevent the Form's save from continuing
                return false;
            }
        } else if (type == 8) {
            // Summary
            // Read the checkboxes & JSON-Encode them
            var items = [];
            for (var i=0; i < req_summary_items.length; i++) {
                var item = req_summary_items[i];
                if ($('#req_summary_' + idescape(item)).is(':checked')) {
                    items.push(item);
                }
            }
            $('#req_req_purpose').val(JSON.stringify(items));
        }
        // Allow the Form's save to continue
        return true;
    });
});