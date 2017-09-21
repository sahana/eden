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
    S3.addPersonWidget = function(fieldname, lookup_duplicates) {
        // Function to be called by S3AddPersonWidget2

        var selector = '#' + fieldname;
        var real_input = $(selector);
        var real_row = $(selector + '__row');

        var title_row = $(selector + '_title__row');
        var error_row = real_input.next('.error_wrapper');

        var div_style = real_row.hasClass('control-group') // Bootstrap
                        || real_row.hasClass('form-row'); // Foundation
        if (div_style) {
            // Move the user-visible rows underneath the real (hidden) one
            var org_row = $(selector + '_organisation_id__row');
            var name_row = $(selector + '_full_name__row');
            var first_name_row = $(selector + '_first_name__row');
            var middle_name_row = $(selector + '_middle_name__row');
            var last_name_row = $(selector + '_last_name__row');
            var father_name_row = $(selector + '_father_name__row');
            var grandfather_name_row = $(selector + '_grandfather_name__row');
            var date_of_birth_row = $(selector + '_date_of_birth__row');
            var year_of_birth_row = $(selector + '_year_of_birth__row');
            var gender_row = $(selector + '_gender__row');
            var occupation_row = $(selector + '_occupation__row');
            var mobile_phone_row = $(selector + '_mobile_phone__row');
            var home_phone_row = $(selector + '_home_phone__row');
            var email_row = $(selector + '_email__row');
            var box_bottom = $(selector + '_box_bottom');
            if (first_name_row.length) {
                // separate_name_fields
                if ($(selector + '_first_name').attr('data-c') == undefined) {
                    // Last Name field must be the activator & should be showed first
                    real_row.hide()
                            .after(box_bottom)
                            .after(email_row)
                            .after(home_phone_row)
                            .after(mobile_phone_row)
                            .after(occupation_row)
                            .after(gender_row)
                            .after(date_of_birth_row)
                            .after(year_of_birth_row)
                            .after(grandfather_name_row)
                            .after(father_name_row)
                            .after(first_name_row)
                            .after(middle_name_row)
                            .after(last_name_row)
                            .after(org_row)
                            .after(error_row)
                            .after(title_row);
                } else {
                    real_row.hide()
                            .after(box_bottom)
                            .after(email_row)
                            .after(home_phone_row)
                            .after(mobile_phone_row)
                            .after(occupation_row)
                            .after(gender_row)
                            .after(date_of_birth_row)
                            .after(year_of_birth_row)
                            .after(grandfather_name_row)
                            .after(father_name_row)
                            .after(last_name_row)
                            .after(middle_name_row)
                            .after(first_name_row)
                            .after(org_row)
                            .after(error_row)
                            .after(title_row);
                }
            } else {
                // Unified name field
                real_row.hide()
                        .after(box_bottom)
                        .after(email_row)
                        .after(home_phone_row)
                        .after(mobile_phone_row)
                        .after(occupation_row)
                        .after(gender_row)
                        .after(date_of_birth_row)
                        .after(year_of_birth_row)
                        .after(grandfather_name_row)
                        .after(father_name_row)
                        .after(last_name_row)
                        .after(middle_name_row)
                        .after(first_name_row)
                        .after(name_row)
                        .after(org_row)
                        .after(error_row)
                        .after(title_row);
            }

            title_row.removeClass('hide').show();
            org_row.removeClass('hide').show();
            name_row.removeClass('hide').show();
            first_name_row.removeClass('hide').show();
            middle_name_row.removeClass('hide').show();
            last_name_row.removeClass('hide').show();
            father_name_row.removeClass('hide').show();
            grandfather_name_row.removeClass('hide').show();
            date_of_birth_row.removeClass('hide').show();
            year_of_birth_row.removeClass('hide').show();
            gender_row.removeClass('hide').show();
            occupation_row.removeClass('hide').show();
            mobile_phone_row.removeClass('hide').show();
            home_phone_row.removeClass('hide').show();
            email_row.removeClass('hide').show();
            box_bottom.removeClass('hide').show();
        } else {
            // Hide the main row & move out the Error underneath the top of the widget
            $(selector + '__row1').hide();
            real_row.hide()
                    .after(error_row)
                    .after(title_row);
        }

        var value = real_input.val();
        if (value) {
            // Update form
            // Disable the fields by default
            disable_person_fields(fieldname);
            // Hide the cancel button
            $(selector + '_edit_bar .icon-remove').hide();
        } else {
            // Create form
            // Enable the Autocomplete
            enable_autocomplete(fieldname);
            // Hide the edit button
            $(selector + '_edit_bar .icon-edit').hide();
        }

        // Attach the hook to be able to lookup site contact
        real_input.data('lookup_contact', lookup_contact);

        // Show the edit bar
        $(selector + '_edit_bar').removeClass('hide').show();

        // Events
        $(selector + '_edit_bar .icon-edit').click(function() {
            edit(fieldname);
        });
        $(selector + '_edit_bar .icon-remove').click(function() {
            cancel(fieldname);
        });

        if (lookup_duplicates) {
            // Add place to store results
            var results = '<div id="' + fieldname + '_duplicates" class="req"></div>';
            if (div_style) {
                // Bootstrap / Foundation
                $(selector + '_box_bottom').before(results);
            } else {
                // Default formstyle
                $(selector + '_box_bottom1').before(results);
            }
            var dupes_count = $(selector + '_duplicates');
            dupes_count.data('results', [])
                       .click(function() {
                // Open up the full list of results
                display_duplicates(fieldname);
            });
            // Check for Duplicates whenever any of the person fields are changed
            $(selector + '_full_name' + ',' +
              selector + '_first_name' + ',' +
              selector + '_middle_name' + ',' +
              selector + '_last_name' + ',' +
              selector + '_date_of_birth' + ',' +
              selector + '_gender' + ',' +
              selector + '_father_name' + ',' +
              selector + '_grandfather_name' + ',' +
              selector + '_year_of_birth' + ',' +
              selector + '_occupation' + ',' +
              selector + '_mobile_phone' + ',' +
              selector + '_home_phone' + ',' +
              selector + '_email').change(function() {
                check_duplicates(fieldname);
            });
            real_input.change(function() {
                if (real_input.val()) {
                    // Clear the duplicate results
                    clear_duplicates(fieldname);
                }
            });
        }

        $(selector + '_organisation_id').change(function() {
            // HR: If there is an organisation selected then use this as a filter for the Autocomplete
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

        real_input.closest('form').submit(function() {
            // The form is being submitted

            // Do we have any duplicates found which we should force the user to review?
            if (lookup_duplicates) {
                if (dupes_count.data('results').length) {
                    // Mark that we're coming from a form submission
                    dupes_count.data('submit', true);
                    // Open up the list of results
                    display_duplicates(fieldname);
                    // Prevent form submission
                    return false;
                }
            }

            // Do the normal form-submission tasks
            // @ToDo: Look to have this happen automatically
            // http://forum.jquery.com/topic/multiple-event-handlers-on-form-submit
            // http://api.jquery.com/bind/
            S3ClearNavigateAwayConfirm();

            if (!real_input.val()) {
                // Ensure that all fields aren't disabled (to avoid wiping their contents)
                enable_person_fields(fieldname);
            }

            // Allow the Form's Save to continue
            return true;
        });
    };

    /**
     * Check that Widget is ready
     * - used to fire functions from outside
     */
    S3.addPersonWidgetReady = function(fieldname) {
        var dfd = new jQuery.Deferred();

        var selector = '#' + fieldname;
        var real_input = $(selector);

        // Test every half-second
        setTimeout(function working() {
            if (real_input.data('lookup_contact') != undefined) {
                dfd.resolve('loaded');
            } else if (dfd.state() === 'pending') {
                // Notify progress
                dfd.notify('waiting for Widget to setup...');
                // Loop
                setTimeout(working, 500);
            } else {
                // Failed!?
            }
        }, 1);

        // Return the Promise so caller can't change the Deferred
        return dfd.promise();
    };

    var enable_person_fields = function(fieldname) {
        var selector = '#' + fieldname;
        $(selector + '_organisation_id').prop('disabled', false);
        $(selector + '_full_name').prop('disabled', false);
        $(selector + '_first_name').prop('disabled', false);
        $(selector + '_middle_name').prop('disabled', false);
        $(selector + '_last_name').prop('disabled', false);
        $(selector + '_gender').prop('disabled', false);
        $(selector + '_date_of_birth').prop('disabled', false);
        $(selector + '_year_of_birth').prop('disabled', false);
        $(selector + '_father_name').prop('disabled', false);
        $(selector + '_grandfather_name').prop('disabled', false);
        $(selector + '_occupation').prop('disabled', false);
        $(selector + '_mobile_phone').prop('disabled', false);
        $(selector + '_home_phone').prop('disabled', false);
        $(selector + '_email').prop('disabled', false);
    };

    var disable_person_fields = function(fieldname) {
        var selector = '#' + fieldname;
        $(selector + '_organisation_id').prop('disabled', true);
        $(selector + '_full_name').prop('disabled', true);
        $(selector + '_first_name').prop('disabled', true);
        $(selector + '_middle_name').prop('disabled', true);
        $(selector + '_last_name').prop('disabled', true);
        $(selector + '_gender').prop('disabled', true);
        $(selector + '_date_of_birth').prop('disabled', true);
        $(selector + '_date_of_birth__row .ui-datepicker-trigger').hide();
        $(selector + '_year_of_birth').prop('disabled', true);
        $(selector + '_father_name').prop('disabled', true);
        $(selector + '_grandfather_name').prop('disabled', true);
        $(selector + '_occupation').prop('disabled', true);
        $(selector + '_mobile_phone').prop('disabled', true);
        $(selector + '_home_phone').prop('disabled', true);
        $(selector + '_email').prop('disabled', true);
        // Show the edit button
        $(selector + '_edit_bar .icon-edit').removeClass('hide').show();
        // Hide the cancel button
        $(selector + '_edit_bar .icon-remove').hide();
    };

    var edit = function(fieldname) {
        var selector = '#' + fieldname;
        // Enable the Autocomplete
        enable_autocomplete(fieldname);
        // Enable all the fields & clear their values
        $(selector + '_full_name').prop('disabled', false).val('');
        $(selector + '_first_name').prop('disabled', false).val('');
        $(selector + '_middle_name').prop('disabled', false).val('');
        $(selector + '_last_name').prop('disabled', false).val('');
        clear_person_fields(fieldname);
        // Hide the edit button
        $(selector + '_edit_bar .icon-edit').hide();
        // Show the cancel button
        $(selector + '_edit_bar .icon-remove').removeClass('hide').show();
    };

    var cancel = function(fieldname) {
        var selector = '#' + fieldname;
        var real_input = $(selector);
        var existing = real_input.data('existing');
        if (existing) {
            // Revert to existing
            $(selector).val(existing.value);
            $(selector + '_organisation_id').prop('disabled', true).val(existing.organisation_id);
            $(selector + '_full_name').prop('disabled', true).val(existing.full_name);
            $(selector + '_first_name').prop('disabled', true).val(existing.first_name);
            $(selector + '_middle_name').prop('disabled', true).val(existing.middle_name);
            $(selector + '_last_name').prop('disabled', true).val(existing.last_name);
            $(selector + '_gender').prop('disabled', true).val(existing.gender);
            $(selector + '_date_of_birth').prop('disabled', true).val(existing.date_of_birth);
            $(selector + '_date_of_birth__row .ui-datepicker-trigger').show();
            $(selector + '_year_of_birth').prop('disabled', true).val(existing.year_of_birth);
            $(selector + '_father_name').prop('disabled', true).val(existing.father_name);
            $(selector + '_grandfather_name').prop('disabled', true).val(existing.grandfather_name);
            $(selector + '_occupation').prop('disabled', true).val(existing.occupation);
            $(selector + '_mobile_phone').prop('disabled', true).val(existing.mobile_phone);
            $(selector + '_home_phone').prop('disabled', true).val(existing.home_phone);
            $(selector + '_email').prop('disabled', true).val(existing.email);
            // Show the edit button
            $(selector + '_edit_bar .icon-edit').removeClass('hide').show();
            // Hide the cancel button
            $(selector + '_edit_bar .icon-remove').hide();
        } else {
            // Nothing should come here?
            // Clear all values
            $(selector + '_full_name').prop('disabled', false).val('');
            $(selector + '_first_name').prop('disabled', false).val('');
            $(selector + '_middle_name').prop('disabled', false).val('');
            $(selector + '_last_name').prop('disabled', false).val('');
            clear_person_fields(fieldname);
        }
    };

    var clear_person_fields = function(fieldname) {
        var selector = '#' + fieldname;
        // Clear values & Enable Fields except for name, as select_person
        // should retain the name that the user selected via autocomplete.
        $(selector).val('');
        $(selector + '_organisation_id').prop('disabled', false).val('');
        $(selector + '_gender').prop('disabled', false).val('');
        $(selector + '_date_of_birth').prop('disabled', false).val('');
        $(selector + '_date_of_birth__row .ui-datepicker-trigger').show();
        $(selector + '_year_of_birth').prop('disabled', false).val('');
        $(selector + '_father_name').prop('disabled', false).val('');
        $(selector + '_grandfather_name').prop('disabled', false).val('');
        $(selector + '_occupation').prop('disabled', false).val('');
        $(selector + '_mobile_phone').prop('disabled', false).val('');
        $(selector + '_home_phone').prop('disabled', false).val('');
        $(selector + '_email').prop('disabled', false).val('');
        // Hide the edit bar
        //$(selector + '_edit_bar').hide();
    };

    var represent_person = function(item) {
        if (item.label != undefined) {
            // No Match
            return item.label;
        }
        if (fullname) {
            var name = item.name;
        } else {
        }
        return name;
    };

    var represent_hr = function(item) {
        if (item.label != undefined) {
            // No Match
            return item.label;
        }
        var name = item.name;
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
    };

    var enable_autocomplete = function(fieldname) {
        var selector = '#' + fieldname;
        var dummy_input = $(selector + '_full_name');
        if (dummy_input.length == 0) {
            // separate_name_fields
            fullname = false;
            dummy_input = $(selector + '_first_name');
            var controller = dummy_input.attr('data-c');
            if (controller == undefined) {
                // Last Name field must be the activator
                firstname = false;
                dummy_input = $(selector + '_last_name');
                var controller = dummy_input.attr('data-c');
            } else {
                firstname = true;
            }
        } else {
            fullname = true;
            var controller = dummy_input.attr('data-c');
        }
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
                organisation_id: $(selector + '_organisation_id').val(),
                gender: $(selector + '_gender').val(),
                date_of_birth: $(selector + '_date_of_birth').val(),
                year_of_birth: $(selector + '_year_of_birth').val(),
                father_name: $(selector + '_father_name').val(),
                grandfather_name: $(selector + '_grandfather_name').val(),
                occupation: $(selector + '_occupation').val(),
                mobile_phone: $(selector + '_mobile_phone').val(),
                home_phone: $(selector + '_home_phone').val(),
                email: $(selector + '_email').val()
            };
            if (fullname) {
                existing['full_name'] = dummy_input.val();
            } else {
                existing['first_name'] = $(selector + '_first_name').val();
                existing['middle_name'] = $(selector + '_middle_name').val();
                existing['last_name'] = $(selector + '_last_name').val();
            }
        } else {
            var existing = {};
        }
        real_input.data('existing', existing);

        // Add a Throbber
        dummy_input.after('<div id="' + fieldname + '_throbber" class="throbber input_throbber hide"></div>');
        var throbber = $(selector + '_throbber');

        var fn = dummy_input.attr('data-f');
        var url = S3.Ap.concat('/' + controller + '/' + fn + '/search_ac');
        // Have this URL editable after setup (e.g. to Filter by Organisation)
        real_input.data('url', url);

        dummy_input.autocomplete({
            delay: $(this).data('delay') || 800,
            minLength: $(this).data('chars') || 2,
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
                        data.push({
                            id: 0,
                            value: '',
                            label: i18n.none_of_the_above
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
                return false;
            },
            select: function(event, ui) {
                var item = ui.item;
                if (item.id) {
                    var name = represent_person(item);
                    dummy_input.val(name);
                    real_input.val(item.id).change();
                    // Update the Form Fields
                    select_person(fieldname, item.id);
                } else {
                    // 'None of the above' => New Entry
                    real_input.val('').change();
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
            if (fullname) {
                if (existing.hasOwnProperty('full_name') && existing.full_name != dummy_input.val()) {
                    // New Entry - without letting AC complete (e.g. tab out)
                    real_input.val('').change();
                }
            } else if (firstname) {
                if (existing.hasOwnProperty('first_name') && existing.first_name != dummy_input.val()) {
                    // New Entry - without letting AC complete (e.g. tab out)
                    real_input.val('').change();
                }
            } else {
                // lastname
                if (existing.hasOwnProperty('last_name') && existing.last_name != dummy_input.val()) {
                    // New Entry - without letting AC complete (e.g. tab out)
                    real_input.val('').change();
                }
            }
        });
    };

    // Called on post-process by the Autocomplete Widget
    var select_person = function(fieldname, id) {
        var selector = '#' + fieldname;
        var name_input = $(selector + '_full_name');
        if (name_input.length == 0) {
            // separate_name_fields
            fullname = false;
            name_input = $(selector + '_first_name');
            name_input.prop('disabled', false);
            var controller = name_input.attr('data-c');
            if (controller == undefined) {
                // Last Name field must be the activator
                name_input = $(selector + '_last_name');
                name_input.prop('disabled', false);
                var controller = name_input.attr('data-c');
            } else {
                $(selector + '_last_name').prop('disabled', false).val('');
            }
            $(selector + '_middle_name').prop('disabled', false);
        } else {
            fullname = true;
            var controller = name_input.attr('data-c');
            name_input.prop('disabled', false);
        }
        clear_person_fields(fieldname);
        var real_input = $(selector);
        var fn = name_input.attr('data-f');
        var url = S3.Ap.concat('/' + controller + '/' + fn + '/' + id + '/lookup.json');
        $.getJSONS3(url, function(data) {
            try {
                // Already done by ac, yet gets lost due to {} returning True
                real_input.val(id);

                var existing = {value: id}
                if (fullname) {
                    var full_name = name_input.val();
                    existing['full_name'] = full_name;
                }
                real_input.data('existing', existing);
                process_reponse(data, fieldname);

            } catch(e) {
                real_input.val('');
                clear_person_fields(fieldname);
            }
        });
    };

    // Lookup the Site Contact Person for a Site
    // Up to the calling function (external) as to whether this is only done
    // when fieldname is currently empty or not
    var lookup_contact = function(fieldname, site_id) {
        var selector = '#' + fieldname;
        var name_input = $(selector + '_full_name');
        if (name_input.length == 0) {
            // separate_name_fields
            fullname = false;
            name_input = $(selector + '_first_name');
            name_input.prop('disabled', false).val('');
            if (name_input.attr('data-c') == undefined) {
                // Last Name field must be the activator
                name_input = $(selector + '_last_name');
                name_input.prop('disabled', false).val('');
            } else {
                $(selector + '_last_name').prop('disabled', false).val('');
            }
            $(selector + '_middle_name').prop('disabled', false).val('');
        } else {
            fullname = true;
            name_input.prop('disabled', false).val('');
        }
        clear_person_fields(fieldname);
        var real_input = $(selector);
        var url = S3.Ap.concat('/org/site/' + site_id + '/site_contact_person');
        $.getJSONS3(url, function(data) {
            try {
                var id = data['id'];
                real_input.val(id);

                var existing = {value: id}

                if (fullname) {
                    var full_name = data['name'];
                    name_input.val(full_name);
                    existing['full_name'] = full_name;
                } else {
                    var first_name = data['first_name'];
                    $(selector + '_first_name').val(first_name);
                    existing['first_name'] = first_name;
                    var last_name = data['last_name'];
                    $(selector + '_last_name').val(last_name);
                    existing['last_name'] = last_name;
                    var middle_name_field = $(selector + '_middle_name');
                    if (middle_name_field.length) {
                        var middle_name = data['middle_name'];
                        middle_name_field.val(middle_name);
                        existing['middle_name'] = middle_name;
                    }
                }

                real_input.data('existing', existing);
                process_reponse(data, fieldname, id);
            } catch(e) {
                real_input.val('');
                if (fullname) {
                    name_input.prop('disabled', false).val('');
                } else {
                    $(selector + '_first_name').prop('disabled', false).val('');
                    $(selector + '_middle_name').prop('disabled', false).val('');
                    $(selector + '_last_name').prop('disabled', false).val('');
                }
                clear_person_fields(fieldname);
            }
        });
    };

    // Process the response from pr_person_lookup, hrm_lookup or site_contact_person
    var process_reponse = function(data, fieldname) {

        var selector = '#' + fieldname;
        var real_input = $(selector);
        var existing = real_input.data('existing');

        if (data.hasOwnProperty('email')) {
            var email = data['email'];
            $(selector + '_email').val(email);
            existing['email'] = email;
        }
        if (data.hasOwnProperty('mphone')) {
            var mobile_phone = data['mphone'];
            $(selector + '_mobile_phone').val(mobile_phone);
            existing['mobile_phone'] = mobile_phone;
        }
        if (data.hasOwnProperty('hphone')) {
            var home_phone = data['hphone'];
            $(selector + '_home_phone').val(home_phone);
            existing['home_phone'] = home_phone;
        }
        if (data.hasOwnProperty('sex')) {
            var gender = data['sex'];
            $(selector + '_gender').val(gender);
            existing['gender'] = gender;
        }
        if (data.hasOwnProperty('dob')) {
            var date_of_birth = data['dob'];
            $(selector + '_date_of_birth').val(date_of_birth);
            existing['date_of_birth'] = date_of_birth;
        }
        if (data.hasOwnProperty('year_of_birth')) {
            var year_of_birth = data['year_of_birth'];
            $(selector + '_year_of_birth').val(year_of_birth);
            existing['year_of_birth'] = year_of_birth;
        }
        if (data.hasOwnProperty('father_name')) {
            var father_name = data['father_name'];
            $(selector + '_father_name').val(father_name);
            existing['father_name'] = father_name;
        }
        if (data.hasOwnProperty('grandfather_name')) {
            var grandfather_name = data['grandfather_name'];
            $(selector + '_grandfather_name').val(grandfather_name);
            existing['grandfather_name'] = grandfather_name;
        }
        if (data.hasOwnProperty('occupation')) {
            var occupation = data['occupation'];
            $(selector + '_occupation').val(occupation);
            existing['occupation'] = occupation;
        }
        if (data.hasOwnProperty('org_id')) {
            var organisation_id = data['org_id'];
            $(selector + '_organisation_id').val(organisation_id);
            existing['organisation_id'] = organisation_id;
        }
        if (data.hasOwnProperty('first_name')) {
            var first_name = data['first_name'];
            $(selector + '_first_name').val(first_name);
            existing['first_name'] = first_name;
            var last_name = data['last_name'];
            $(selector + '_last_name').val(last_name);
            existing['last_name'] = last_name;
            if (data.hasOwnProperty('middle_name')) {
                var middle_name = data['middle_name'];
                $(selector + '_middle_name').val(middle_name);
                existing['middle_name'] = middle_name;
            }
        }

        disable_person_fields(fieldname);
    };

    /**
     * Check for duplicates
     */
    var check_duplicates = function(fieldname) {

        var selector = '#' + fieldname;
        var real_input = $(selector);
        if (real_input.val()) {
            // User has selected an entry, so no need for additional deduplication checks
            return;
        }
        var name_field = $(selector + '_full_name');
        if (name_field.length == 0) {
            // separate_name_fields
            var first_name = $(selector + '_first_name').val();
            if (!first_name) {
                // Nothing we can lookup yet
                return;
            }
            var data = {first_name: first_name};
            var last_name = $(selector + '_last_name').val();
            if (last_name) {
                data['last_name'] = last_name;
            }
            var middle_name_field = $(selector + '_middle_name');
            if (middle_name_field.length) {
                var middle_name = $(selector + '_middle_name').val();
                if (middle_name) {
                    data['middle_name'] = middle_name;
                }
            }
        } else {
            var name = name_field.val();
            if (!name) {
                // Nothing we can lookup yet
                return;
            }
            var data = {name: name};
        }
        var dob = $(selector + '_date_of_birth').val();
        if (dob) {
            data['dob'] = dob;
        }
        var gender = $(selector + '_gender').val();
        if (gender) {
            data['sex'] = gender;
        }
        var father_name = $(selector + '_father_name').val();
        if (father_name) {
            data['father_name'] = father_name;
        }
        var grandfather_name = $(selector + '_grandfather_name').val();
        if (grandfather_name) {
            data['grandfather_name'] = grandfather_name;
        }
        var occupation = $(selector + '_occupation').val();
        if (occupation) {
            data['occupation'] = occupation;
        }
        var mobile_phone = $(selector + '_mobile_phone').val();
        if (mobile_phone) {
            data['mphone'] = mobile_phone;
        }
        var home_phone = $(selector + '_home_phone').val();
        if (home_phone) {
            data['hphone'] = home_phone;
        }
        var email = $(selector + '_email').val();
        if (email) {
            data['email'] = email;
        }
        // @ToDo: Allow controller to be configurable
        var url = S3.Ap.concat('/pr/person/check_duplicates');
        $.ajaxS3({
            url: url,
            data: data,
            type: 'POST',
            dataType: 'json',
            success: function(data) {
                // Remove old results
                $(selector + '_results').remove();
                if (data.length) {
                    // Display new count
                    var count = i18n.dupes_found.replace('_NUM_', data.length);
                    $(selector + '_duplicates').html(count + ' <i class="icon-caret-down"> </i>')
                                               .show()
                                               .data('results', data);
                } else {
                    // Clear old count
                    $(selector + '_duplicates').data('results', [])
                                               .hide();
                }
            }
        });
    };

    /**
     * Display duplicates
     */
    var display_duplicates = function(fieldname) {

        var selector = '#' + fieldname;

        if ($(selector + '_results').length) {
            // Already showing
            return;
        }

        var dupes_count = $(selector + '_duplicates');
        var items = dupes_count.data('results');
        var card,
            item,
            name,
            options = '<div id="' + fieldname + '_results">',
            len_items = items.length;
        for (var i=0; i < len_items; i++) {
            item = items[i];
            name = item.name;
            card = '<div class="dl-item" data-id=' + item.id + ' data-name="' + name + '">';
            card += '<a class="fleft"><img width=50 height=50 src="';
            if (item.image) {
                S3.Ap.concat('/default/download/' + item.image)
            } else {
                // Default placeholder
                card += S3.Ap.concat('/static/img/blank-user.gif');
            }
            card += '" class="media-object"></a><div>';
            if (item.org) {
                card += '<div class="card_1_line">' + item.org + '</div>';
            }
            card += '<div class="card_1_line">' + name + '</div>';
            if (item.father_name && i18n.father_name_label) {
                card += '<div class="card_1_line"><label>' + i18n.father_name_label + '</label>' + item.father_name + '</div>';
            }
            if (item.grandfather_name && i18n.grandfather_name_label) {
                card += '<div class="card_1_line"><label>' + i18n.grandfather_name_label + '</label>' + item.grandfather_name + '</div>';
            }
            if (item.year_of_birth) {
                card += '<div class="card_1_line">' + item.year_of_birth + '</div>';
            }
            if (item.dob) {
                card += '<div class="card_1_line">' + item.dob + '</div>';
            }
            if (item.email) {
                card += '<div class="card_1_line">' + item.email + '</div>';
            }
            if (item.phone) {
                card += '<div class="card_1_line">' + item.phone + '</div>';
            }
            // Buttons default to type=submit if not set explicitly
            card += '<button type="button" class="fright"><i class="icon icon-ok"> </i> ' + i18n.Yes + '</button></div></div>';
            options += card;
        }
        // Buttons default to type=submit if not set explicitly
        options += '<div class="dl-item"><button type="button" class="fright"><i class="icon icon-remove"> </i> ' + i18n.No + '</button></div></div>';
        dupes_count.after(options);

        // Scroll to this section
        $('html,body').animate({scrollTop: dupes_count.offset().top}, 250);

        // Add Event Handler to handle clicks
        $(selector + '_results .dl-item').click(function() {
            $this = $(this);
            name = $this.attr('data-name');
            if (name) {
                // Yes: Select this person
                $(selector + '_full_name').val(name);
                var person_id = $this.attr('data-id');
                // Remove results
                clear_duplicates(fieldname);
                if (dupes_count.data('submit')) {
                    // Set to this value
                    $(selector).val(person_id);
                    // Complete form submission
                    dupes_count.closest('form').submit();
                } else {
                    select_person(fieldname, person_id);
                }
            } else {
                // No: Remove results
                clear_duplicates(fieldname);
                if (dupes_count.data('submit')) {
                    // Complete form submission
                    dupes_count.closest('form').submit();
                }
            }
        });
    };

    /**
     * Clear duplicates
     */
    var clear_duplicates = function(fieldname) {
        var selector = '#' + fieldname;
        $(selector + '_duplicates').data('results', [])
                                   .empty();
        $(selector + '_results').remove();
    };

}());
