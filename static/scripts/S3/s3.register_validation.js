/**
 * Used by s3_register_validation() (modules/s3/s3utils.py)
 */

var s3_register_validation = function() {
    // Hide password verification field until password changed
    $('input[name="password"]').keyup(function() {
        $('#auth_user_password_two__row, #auth_user_password_two__row1').removeClass('hide').show();
        $('#password_two').prop('disabled', false);
    });

    // Read options
    var mobile_phone_mandatory = false,
        organisation_required = false,
        terms_of_service_required = false;
    if (S3.auth_registration_mobile_phone_mandatory) {
        mobile_phone_mandatory = true;
    }
    if (S3.auth_registration_organisation_required) {
        organisation_required = true;
    }
    if (S3.auth_terms_of_service) {
        terms_of_service_required = true;
    }

    if (S3.auth_registration_hide_organisation) {
        // Hide the Organisation row initially
        $('#auth_user_organisation_id__row').hide();
    }

    if (undefined != S3.whitelists) {
        // Check for Whitelists
        $('.auth_register #auth_user_email').blur(function() {
            var field = $('#auth_user_organisation_id');
            if (!field.val()) {
                // If no value yet exists then set from whitelist
                var email = $('.auth_register #auth_user_email').val();
                var domain = email.split('@')[1];
                if (undefined != S3.whitelists[domain]) {
                    field.val(S3.whitelists[domain]);
                } else {
                    $('#auth_user_organisation_id__row').show();
                }
            }
        });
    }

    var email_row = $('#auth_user_email__row');
    // Detect formstyle using DIVs as form rows: Foundation=form-row, Bootstrap=control-group
    var div_style = email_row.hasClass('form-row') || email_row.hasClass('control-group');

    // Validate signup form on keyup and submit
    $('.auth_register').validate({
        errorClass: 'req',
        rules: {
            first_name: {
                required: true
            },
            email: {
                required: true,
                // @ToDo
                //remote:'emailsurl',
                email: true
            },
            mobile: {
                required: mobile_phone_mandatory
            },
            organisation_id: {
                required: organisation_required
            },
            password: {
                required: true
            },
            password_two: {
                required: true,
                equalTo: '.auth_register .password:first'
            },
            tos: {
                required: terms_of_service_required
            }
        },
        messages: {
            first_name: i18n.enter_first_name,
            password: {
                required: i18n.provide_password
            },
            password_two: {
                required: i18n.repeat_your_password,
                equalTo: i18n.enter_same_password
            },
            email: {
                required: i18n.please_enter_valid_email,
                email: i18n.please_enter_valid_email
            },
            organisation_id: i18n.enter_your_organisation,
            tos: i18n.tos_required
        },
        errorPlacement: function(error, element) {
            if (div_style) {
                // Bootstrap/Foundation
                // Place immediately after widget
                error.appendTo(element.parent());
            } else {
                // Default/DRRPP
                // Place in comment
                error.appendTo(element.parent().next());
            }
        },
        submitHandler: function(form) {
            form.submit();
        }
    });

    // Password Strength indicator
    $('.auth_register .password:first').pstrength({
        'minChar': S3.password_min_length,
        'minCharText': i18n.password_min_chars,
		'verdicts':	[i18n.weak, i18n.normal, i18n.medium, i18n.strong, i18n.very_strong]
    });

};
