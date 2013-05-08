/**
 * Used by S3AddPersonWidget (modules/s3widgets.py)
 * Currently hardcoded for the hrm_human_resource/create context
 */

// Global, so can only have 1 per page
var addPerson_real_input;
 
function addPersonWidget() {
    var fieldname = $('#select_from_registry_row').attr('field');
    var dummyname = 'dummy_' + fieldname;
    var dummy_input = '#' + dummyname;
    $(dummy_input).addClass('hide');
    addPerson_real_input = '#' + fieldname;
    var person_id = $(addPerson_real_input).val();
    if (person_id > 0) {
        // If an ID present then disable input fields
        $('#clear_form_link').removeClass('hide');
        $('#edit_selected_person_link').removeClass('hide');
        disable_person_fields();
    }
    // Set up Listeners
    $('#select_from_registry').click(function() {
        $('#select_from_registry_row').addClass('hide');
        $('#person_autocomplete_row').removeClass('hide');
        $(dummy_input).removeClass('hide');
        $('#person_autocomplete_label').removeClass('hide');
        $(dummy_input).focus();
    });
    $(dummy_input).focusout(function() {
        var person_id = $(addPerson_real_input).val();
        $(dummy_input).addClass('hide');
        $('#person_autocomplete_label').addClass('hide');
        $('#select_from_registry_row').removeClass('hide');
        if (person_id > 0) {
             $('#clear_form_link').removeClass('hide');
        }
    });
    var value = $('#select_from_registry_row').attr('value');
    if (value != 'None') {
        $(addPerson_real_input).val(value);
        select_person(value);
    }
    $('form').submit(function() {
        // The form is being submitted

        // Do the normal form-submission tasks
        // @ToDo: Look to have this happen automatically
        // http://forum.jquery.com/topic/multiple-event-handlers-on-form-submit
        // http://api.jquery.com/bind/
        S3ClearNavigateAwayConfirm();

        // Ensure that all fields aren't disabled (to avoid wiping their contents)
        enable_person_fields();

        // Allow the Form's Save to continue
        return true;
    });
}

function clear_person_form() {
    enable_person_fields();
    $(addPerson_real_input).val('');
    $('#pr_person_first_name').val('');
    $('#pr_person_middle_name').val('');
    $('#pr_person_last_name').val('');
    $('#pr_person_gender').val('');
    $('#pr_person_date_of_birth').val('');
    $('#pr_person_occupation').val('');
    $('#pr_person_email').val('');
    $('#pr_person_mobile_phone').val('');
    $('#clear_form_link').addClass('hide');
    $('#edit_selected_person_link').addClass('hide');
}

function edit_selected_person_form() {
    enable_person_fields();
    $('#edit_selected_person_link').addClass('hide');
}

// Called on post-process by the Autocomplete Widget
function select_person(person_id) {
    if (person_id) {
        var controller = $('#select_from_registry_row').attr('controller');
        if (controller) {
            $('#select_from_registry').addClass('hide');
            $('#clear_form_link').addClass('hide');
            $('#person_load_throbber').removeClass('hide');
            clear_person_form();
            var url = S3.Ap.concat('/' + controller + '/person/' + person_id + '.s3json?show_ids=True');
            $.getJSONS3(url, function(data) {
                try {
                    var person = data['$_pr_person'][0];
                    disable_person_fields();
                    $(addPerson_real_input).val(person['@id']);
                    if (person.hasOwnProperty('first_name')) {
                        $('#pr_person_first_name').val(person['first_name']);
                    }
                    if (person.hasOwnProperty('middle_name')) {
                        $('#pr_person_middle_name').val(person['middle_name']);
                    }
                    if (person.hasOwnProperty('last_name')) {
                        $('#pr_person_last_name').val(person['last_name']);
                    }
                    if (person.hasOwnProperty('gender')) {
                        $('#pr_person_gender').val(person['gender']['@value']);
                    }
                    if (person.hasOwnProperty('date_of_birth')) {
                        $('#pr_person_date_of_birth').val(person['date_of_birth']['@value']);
                    }
                    if (person.hasOwnProperty('occupation')) {
                        $('#pr_person_occupation').val(person['occupation']);
                    }
                    var contacts, contact, method, value;
                    try {
                        contacts = person['$_pr_email_contact'];
                        if (contacts !== undefined) {
                            value = contacts[0]['value'];
                            if (value.hasOwnProperty('@value')) {
                                value = value['@value'];
                            }
                            if (value !== undefined) {
                                $('#pr_person_email').val(value);
                            }
                        }
                    }
                    catch(e) {
                        // continue
                    }
                    try {
                        contacts = person['$_pr_phone_contact'];
                        if (contacts !== undefined) {
                            value = contacts[0]['value'];
                            if (value.hasOwnProperty('@value')) {
                                value = value['@value'];
                            }
                            if (value !== undefined) {
                                $('#pr_person_mobile_phone').val(value);
                            }
                        }
                    }
                    catch(e) {
                        // continue
                    }
                }
                catch(e) {
                    $(addPerson_real_input).val('');
                }
                $('#person_load_throbber').addClass('hide');
                $('#select_from_registry').removeClass('hide');
                $('#clear_form_link').removeClass('hide');
                $('#edit_selected_person_link').removeClass('hide');
            });
            $('#person_autocomplete_row').addClass('hide');
            $('#select_from_registry_row').removeClass('hide');
        }
    }
}

function enable_person_fields() {
    $('#pr_person_first_name').prop('disabled', false);
    $('#pr_person_middle_name').prop('disabled', false);
    $('#pr_person_last_name').prop('disabled', false);
    $('#pr_person_gender').prop('disabled', false);
    $('#pr_person_date_of_birth').prop('disabled', false);
    $('#pr_person_occupation').prop('disabled', false);
    $('#pr_person_email').prop('disabled', false);
    $('#pr_person_mobile_phone').prop('disabled', false);
}

function disable_person_fields() {
    $('#pr_person_first_name').prop('disabled', true);
    $('#pr_person_middle_name').prop('disabled', true);
    $('#pr_person_last_name').prop('disabled', true);
    $('#pr_person_gender').prop('disabled', true);
    $('#pr_person_date_of_birth').prop('disabled', true);
    $('#pr_person_occupation').prop('disabled', true);
    $('#pr_person_email').prop('disabled', true);
    $('#pr_person_mobile_phone').prop('disabled', true);
}
