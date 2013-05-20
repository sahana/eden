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
    if (S3.password_position == 1) {
        var password_position = 'first';
    } else {
        var password_position = 'last';
    }

    if (S3.auth_registration_mobile_phone_mandatory) {
        var auth_registration_mobile_phone_mandatory = true;
    } else {
        var auth_registration_mobile_phone_mandatory = false;
    }

    if (S3.get_auth_registration_organisation_required) {
        var get_auth_registration_organisation_required = true;
    } else {
        var get_auth_registration_organisation_required = false;
    }

    if (S3.auth_registration_hide_organisation) {
        // Hide the Organisation row initially
        $('#auth_user_organisation_id__row').hide();
    }

    if (undefined != S3.whitelists) {
        // Check for Whitelists
        $('#regform #auth_user_email').blur(function() {
            var email = $('#regform #auth_user_email').val();
            var domain = email.split('@')[1];
            if (undefined != S3.whitelists[domain]) {
                $('#auth_user_organisation_id').val(S3.whitelists[domain]);
            } else {
                $('#auth_user_organisation_id__row').show();
            }
        })
    }

    // Validate signup form on keyup and submit
    $('#regform').validate({
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
                required: auth_registration_mobile_phone_mandatory
            },
            organisation_id: {
                required: get_auth_registration_organisation_required
            },
            password: {
                required: true
            },
            password_two: {
                required: true,
                equalTo: '.password:' + password_position
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
            organisation_id: i18n.enter_your_organisation
        },
        errorPlacement: function(error, element) {
            // Standard/DRRPP Formstyles: Place in Comment
            error.appendTo(element.parent().next())
            // Bootstrap Formstyle
            error.appendTo(element.parent().next())
        },
        submitHandler: function(form) {
            form.submit()
        }
    });

    // Password Strength indicator
    $('.password:' + password_position).pstrength({
        'minChar': S3.password_min_length
    });

};