/**
 * Used by S3AddPersonWidget (modules/s3widgets.py)
 * Currently hardcoded for the hrm_human_resource/create context
 */

// Module pattern to hide internal vars
(function () {
    // Can only have 1 per page currently
    var addPerson_real_input;

    // Needs to be in global scope as called from jquery_ready
    S3.addPersonWidget = function() {
        var fieldname = $('#select_from_registry_row').attr('field');
        var dummy_input = $('#dummy_' + fieldname);
        dummy_input.addClass('hide');
        addPerson_real_input = $('#' + fieldname);
        var person_id = addPerson_real_input.val();
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
            $('#person_autocomplete_label').removeClass('hide');
            dummy_input.removeClass('hide')
                       .focus();
        });
        dummy_input.focusout(function() {
            var person_id = addPerson_real_input.val();
            dummy_input.addClass('hide');
            $('#person_autocomplete_label').addClass('hide');
            $('#select_from_registry_row').removeClass('hide');
            if (person_id > 0) {
                 $('#clear_form_link').removeClass('hide');
            }
        });
        var value = $('#select_from_registry_row').attr('value');
        if (value != 'None') {
            addPerson_real_input.val(value);
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

    var select_person_clear_form = function() {
        enable_person_fields();
        addPerson_real_input.val('');
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
    // Pass to global scope to be activated onClick
    S3.select_person_clear_form = select_person_clear_form;

    // Needs to be in global scope as activated onClick
    S3.select_person_edit_form = function() {
        enable_person_fields();
        $('#edit_selected_person_link').addClass('hide');
    }

    // Called on post-process by the Autocomplete Widget
    var select_person = function(person_id) {
        select_person_clear_form();
        if (person_id) {
            var controller = $('#select_from_registry_row').attr('controller');
            if (controller) {
                $('#select_from_registry').addClass('hide');
                $('#clear_form_link').addClass('hide');
                $('#person_load_throbber').removeClass('hide');
                var url = S3.Ap.concat('/' + controller + '/person/' + person_id + '.s3json?show_ids=True');
                $.getJSONS3(url, function(data) {
                    try {
                        var email = undefined, phone = undefined;
                        var person = data['$_pr_person'][0];
                        disable_person_fields();
                        addPerson_real_input.val(person['@id']);
                        if (person.hasOwnProperty('first_name')) {
                            $('#pr_person_first_name').val(person['first_name']);
                        }
                        if (person.hasOwnProperty('middle_name')) {
                            $('#pr_person_middle_name').val(person['middle_name']['@value']);
                        }
                        if (person.hasOwnProperty('last_name')) {
                            $('#pr_person_last_name').val(person['last_name']['@value']);
                        }
                        if (person.hasOwnProperty('gender')) {
                            $('#pr_person_gender').val(person['gender']['@value']);
                        }
                        if (person.hasOwnProperty('date_of_birth')) {
                            $('#pr_person_date_of_birth').val(person['date_of_birth']['@value']);
                        }
                        if (person.hasOwnProperty('occupation')) {
                            $('#pr_person_occupation').val(person['occupation']['@value']);
                        }
                        if (person.hasOwnProperty('$_pr_email_contact')) {
                            var contact = person['$_pr_email_contact'][0];
                            email = contact['value']['@value'];                            
                        }
                        if (person.hasOwnProperty('$_pr_phone_contact')) {
                            var contact = person['$_pr_phone_contact'][0];
                            phone = contact['value']['@value'];                            
                        }                       
                        if (person.hasOwnProperty('$_pr_contact')) {
                            var contacts = person['$_pr_contact'];
                            var contact;
                            for (var i=0; i < contacts.length; i++) {
                                contact = contacts[i];
                                if (email == undefined){
                                    if (contact['contact_method']['@value'] == 'EMAIL') {
                                        email = contact['value']['@value'];
                                    }
                                }
                                if (phone == undefined){
                                    if (contact['contact_method']['@value'] == 'SMS') {
                                        phone = contact['value']['@value'];
                                    }
                                }
                            }
                        }
                        if (email !== undefined){
                            $('#pr_person_email').val(email);
                        }
                        if (phone !== undefined){
                            $('#pr_person_mobile_phone').val(phone);
                        }

                    } catch(e) {
                        addPerson_real_input.val('');
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
    // Pass to global scope
    S3.select_person = select_person;

    var enable_person_fields = function() {
        $('#pr_person_first_name').prop('disabled', false);
        $('#pr_person_middle_name').prop('disabled', false);
        $('#pr_person_last_name').prop('disabled', false);
        $('#pr_person_gender').prop('disabled', false);
        $('#pr_person_date_of_birth').prop('disabled', false);
        $('#pr_person_occupation').prop('disabled', false);
        $('#pr_person_email').prop('disabled', false);
        $('#pr_person_mobile_phone').prop('disabled', false);
    }

    var disable_person_fields = function() {
        $('#pr_person_first_name').prop('disabled', true);
        $('#pr_person_middle_name').prop('disabled', true);
        $('#pr_person_last_name').prop('disabled', true);
        $('#pr_person_gender').prop('disabled', true);
        $('#pr_person_date_of_birth').prop('disabled', true);
        $('#pr_person_occupation').prop('disabled', true);
        $('#pr_person_email').prop('disabled', true);
        $('#pr_person_mobile_phone').prop('disabled', true);
    }
}());