/**
 * Used by S3AddPersonWidget2 (modules/s3widgets.py)
 */

// Module pattern to hide internal vars
(function () {
    
    /**
     * Instantiate an AddPersonWidget
     * - in global scope as called from outside
     *
     * Parameters:
     * fieldname - {String} A unique fieldname for a person_id or human_resource_id field
     */
    S3.addPersonWidget = function(fieldname) {
        // Function to be called by S3AddPersonWidget2

        var selector = '#' + fieldname;
        var real_input = $(selector);

        // Move the user-visible rows underneath the real (hidden) one
        var error_row = real_input.next('.error_wrapper');
        var title_row = $(selector + '_title__row');
        var org_row = $(selector + '_organisation_id__row');
        var name_row = $(selector + '_full_name__row');
        var date_of_birth_row = $(selector + '_date_of_birth__row');
        var gender_row = $(selector + '_gender__row');
        var occupation_row = $(selector + '_occupation__row');
        var email_row = $(selector + '_email__row');
        var mobile_phone_row = $(selector + '_mobile_phone__row');
        var box_bottom = $(selector + '_box_bottom');
        $(selector + '__row').hide()
                             .after(box_bottom)
                             .after(mobile_phone_row)
                             .after(email_row)
                             .after(occupation_row)
                             .after(gender_row)
                             .after(date_of_birth_row)
                             .after(name_row)
                             .after(org_row)
                             .after(title_row)
                             .after(error_row);

        title_row.show();
        org_row.show();
        name_row.show();
        date_of_birth_row.show();
        gender_row.show();
        occupation_row.show();
        email_row.show();
        mobile_phone_row.show();
        box_bottom.show();

        var value = real_input.val();
        if (value) {
            // Update form: disable the fields by default
            disable_person_fields(fieldname);
            // Hide the cancel button
            $(selector + '_edit_bar .icon-remove').hide();
        } else {
            // Create form: Enable the Autocomplete
            enable_autocomplete(fieldname);
            // Hide the edit button
            $(selector + '_edit_bar .icon-edit').hide();
        }
        // Show the edit bar
        $(selector + '_edit_bar').removeClass('hide').show();

        // Events
        $(selector + '_edit_bar .icon-edit').click(function() {
            edit(fieldname);
        });
        $(selector + '_edit_bar .icon-remove').click(function() {
            cancel(fieldname);
        });

        $(selector + '_organisation_id').change(function() {
            // If there is an organisation selected then use this as a filter for the Autocomplete
            var organisation_id = $(this).val();
            var url = real_input.data('url');
            if (organisation_id) {
                // Remove any old filter
                url = url.split('?')[0];
                // Add a filter
                url += '?~.organisation_id=' + organisation_id;
            } else {
                // Strip off the filter
                url = url.split('?')[0];
            }
            real_input.data('url', url);
        });

        $('form').submit(function() {
            // The form is being submitted

            // Do the normal form-submission tasks
            // @ToDo: Look to have this happen automatically
            // http://forum.jquery.com/topic/multiple-event-handlers-on-form-submit
            // http://api.jquery.com/bind/
            S3ClearNavigateAwayConfirm();

            // Ensure that all fields aren't disabled (to avoid wiping their contents)
            enable_person_fields(fieldname);

            // Allow the Form's Save to continue
            return true;
        });
    }

    var enable_person_fields = function(fieldname) {
        var selector = '#' + fieldname;
        $(selector + '_organisation_id').prop('disabled', false);
        $(selector + '_full_name').prop('disabled', false);
        $(selector + '_gender').prop('disabled', false);
        $(selector + '_date_of_birth').prop('disabled', false);
        $(selector + '_occupation').prop('disabled', false);
        $(selector + '_email').prop('disabled', false);
        $(selector + '_mobile_phone').prop('disabled', false);
    }

    var disable_person_fields = function(fieldname) {
        var selector = '#' + fieldname;
        $(selector + '_organisation_id').prop('disabled', true);
        $(selector + '_full_name').prop('disabled', true);
        $(selector + '_gender').prop('disabled', true);
        $(selector + '_date_of_birth').prop('disabled', true);
        $(selector + '_occupation').prop('disabled', true);
        $(selector + '_email').prop('disabled', true);
        $(selector + '_mobile_phone').prop('disabled', true);
        // Show the edit button
        $(selector + '_edit_bar .icon-edit').show();
        // Hide the cancel button
        $(selector + '_edit_bar .icon-remove').hide();
    }

    var edit = function(fieldname) {
        var selector = '#' + fieldname;
        // Enable the Autocomplete
        enable_autocomplete(fieldname);
        // Enable all the fields & clear their values
        $(selector).val('');
        $(selector + '_organisation_id').prop('disabled', false).val('').change();
        $(selector + '_full_name').prop('disabled', false).val('');
        $(selector + '_gender').prop('disabled', false).val('');
        $(selector + '_date_of_birth').prop('disabled', false).val('');
        $(selector + '_occupation').prop('disabled', false).val('');
        $(selector + '_email').prop('disabled', false).val('');
        $(selector + '_mobile_phone').prop('disabled', false).val('');
        // Hide the edit button
        $(selector + '_edit_bar .icon-edit').hide();
        // Show the cancel button
        $(selector + '_edit_bar .icon-remove').show();
    }

    var cancel = function(fieldname) {
        var selector = '#' + fieldname;
        var real_input = $(selector);
        var existing = real_input.data('existing');
        if (existing) {
            // Revert to existing
            $(selector).val(existing.value);
            $(selector + '_organisation_id').prop('disabled', true).val(existing.organisation_id);
            $(selector + '_full_name').prop('disabled', true).val(existing.full_name);
            $(selector + '_gender').prop('disabled', true).val(existing.gender);
            $(selector + '_date_of_birth').prop('disabled', true).val(existing.date_of_birth);
            $(selector + '_occupation').prop('disabled', true).val(existing.occupation);
            $(selector + '_email').prop('disabled', true).val(existing.email);
            $(selector + '_mobile_phone').prop('disabled', true).val(existing.mobile_phone);
            // Show the edit button
            $(selector + '_edit_bar .icon-edit').show();
            // Hide the cancel button
            $(selector + '_edit_bar .icon-remove').hide();
        } else {
            // Nothing should come here?
            // Clear all values
            $(selector + '_full_name').prop('disabled', false).val('');
            clear_person_fields(fieldname);
        }
    }

    var clear_person_fields = function(fieldname) {
        var selector = '#' + fieldname;
        // Clear all values & Enable Fields
        $(selector).val('');
        $(selector + '_organisation_id').prop('disabled', false).val('');
        $(selector + '_gender').prop('disabled', false).val('');
        $(selector + '_date_of_birth').prop('disabled', false).val('');
        $(selector + '_occupation').prop('disabled', false).val('');
        $(selector + '_email').prop('disabled', false).val('');
        $(selector + '_mobile_phone').prop('disabled', false).val('');
        // Hide the edit bar
        //$(selector + '_edit_bar').hide();
    }

    var represent_person = function(item) {
        var name = item.first;
        if (item.middle) {
            name += ' ' + item.middle;
        }
        if (item.last) {
            name += ' ' + item.last;
        }
        return name;
    }

    var represent_hr = function(item) {
        var name = item.first;
        if (item.middle) {
            name += ' ' + item.middle;
        }
        if (item.last) {
            name += ' ' + item.last;
        }
        var org = item.org;
        var job = item.job;
        if (org || job) {
            if (job) {
                name += ' (' + job;
                if (org) {
                    name += ', ' + org;
                }
                name += ')';
            } else {
                name += ' (' + org + ')';
            }
        }
        return name;
    }

    var enable_autocomplete = function(fieldname) {
        var selector = '#' + fieldname;
        var dummy_input = $(selector + '_full_name');
        if (dummy_input.attr('autocomplete')) {
            // Already setup
            return;
        }

        var real_input = $(selector);
        var value = real_input.val();
        if (value) {
            // Store existing data in case of cancel
            var existing = {
                value: value,
                full_name: dummy_input.val(),
                organisation_id: $(selector + '_organisation_id').val(),
                gender: $(selector + '_gender').val(),
                date_of_birth: $(selector + '_date_of_birth').val(),
                occupation: $(selector + '_occupation').val(),
                email: $(selector + '_email').val(),
                mobile_phone: $(selector + '_mobile_phone').val()
            };
        } else {
            var existing = {};
        }
        real_input.data('existing', existing);

        // Add a Throbber
        $(selector + '_full_name').after('<div id="' + fieldname + '_throbber" class="throbber input_throbber hide"></div>');
        var throbber = $(selector + '_throbber');

        var controller = dummy_input.attr('data-c');
        var fn = dummy_input.attr('data-f');
        var url = S3.Ap.concat('/' + controller + '/' + fn + '/search_ac');
        // Have this URL editable after setup (e.g. to Filter by Organisation)
        real_input.data('url', url);

        dummy_input.autocomplete({
            // @ToDo: Configurable options
            delay: 450,
            minLength: 2,
            source: function(request, response) {
                // Patch the source so that we can handle No Matches
                $.ajax({
                    url: real_input.data('url'),
                    data: {
                        term: request.term
                    }
                }).done(function (data) {
                    if (data.length == 0) {
                        // New Entry
                        real_input.val('');
                    } else {
                        var none_of_the_above = i18n.none_of_the_above;
                        data.push({
                            id: 0,
                            value: '',
                            label: none_of_the_above,
                            // First Name
                            first: none_of_the_above
                        });
                    }
                    response(data);
                });
            },
            search: function(event, ui) {
                throbber.removeClass('hide').show();
                return true;
            },
            response: function(event, ui, content) {
                throbber.hide();
                return content;
            },
            focus: function(event, ui) {
                var name = represent_person(ui.item);
                return false;
            },
            select: function(event, ui) {
                var item = ui.item;
                if (item.id) {
                    var name = represent_person(item);
                    dummy_input.val(name);
                    real_input.val(item.id);
                    // Update the Form Fields
                    select_person(fieldname, item.id);
                } else {
                    // 'None of the above' => New Entry
                    real_input.val('');
                }
                return false;
            }
        })
        .data('ui-autocomplete')._renderItem = function(ul, item) {
            var name = represent_hr(item);
            return $('<li>').data('item.autocomplete', item)
                            .append('<a>' + name + '</a>')
                            .appendTo(ul);
        };
        dummy_input.blur(function() {
            if (existing && existing.full_name != dummy_input.val()) {
                // New Entry - without letting AC complete (e.g. tab out)
                real_input.val('');
            }
        });
    }

    // Called on post-process by the Autocomplete Widget
    var select_person = function(fieldname, id) {
        var selector = '#' + fieldname;
        var name_input = $(selector + '_full_name');
        name_input.prop('disabled', false);
        clear_person_fields(fieldname);
        var real_input = $(selector);
        var controller = name_input.attr('data-c');
        var fn = name_input.attr('data-f');
        var url = S3.Ap.concat('/' + controller + '/' + fn + '/' + id + '/lookup');
        $.getJSONS3(url, function(data) {
            try {
                /* We have these already from the search_ac
                var names = [];
                if (data.hasOwnProperty('first_name')) {
                    names.push(data['first_name']);
                }
                if (data.hasOwnProperty('middle_name')) {
                    names.push(data['middle_name']);
                }
                if (data.hasOwnProperty('last_name')) {
                    names.push(data['last_name']);
                }
                var full_name = names.join(' ');
                name_input.val(full_name); */
                var full_name = name_input.val();
                var existing = {
                    value: id,
                    full_name: full_name
                }
                // Already done by ac, yet gets lost for some reason
                real_input.val(id);
                real_input.data('existing', existing);
                if (data.hasOwnProperty('email')) {
                    var email = data['email'];
                    $(selector + '_email').val(email);
                    existing['email'] = email;
                }
                if (data.hasOwnProperty('phone')) {
                    var phone = data['phone'];
                    $(selector + '_mobile_phone').val(phone);
                    existing['mobile_phone'] = phone;
                }
                if (data.hasOwnProperty('gender')) {
                    var gender = data['gender'];
                    $(selector + '_gender').val(gender);
                    existing['gender'] = gender;
                }
                if (data.hasOwnProperty('date_of_birth')) {
                    var date_of_birth = data['date_of_birth'];
                    $(selector + '_date_of_birth').val(date_of_birth);
                    existing['date_of_birth'] = date_of_birth;
                }
                if (data.hasOwnProperty('occupation')) {
                    var occupation = data['occupation'];
                    $(selector + '_occupation').val(occupation);
                    existing['occupation'] = occupation;
                }
                if (data.hasOwnProperty('organisation_id')) {
                    var organisation_id = data['organisation_id'];
                    $(selector + '_organisation_id').val(organisation_id);
                    existing['organisation_id'] = organisation_id;
                }

                disable_person_fields(fieldname);

            } catch(e) {
                real_input.val('');
                clear_person_fields(fieldname);
            }
        });
    }

}());