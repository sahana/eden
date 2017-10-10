/**
 * Used by the pr_contacts method (modules/s3db/pr.py)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 *
 * Deprecated: replaced by s3.ui.contacts.js
 * (retained only as historic reference)
 */

// Module pattern to hide internal vars
//(function () {

$(document).ready(function() {
    var person_id = S3.pr_contacts_person_id,
        controller = S3.pr_contacts_controller,
        access = S3.pr_contacts_access;

    $('#contact-add').click(function() {
        // Show a Spinner
        $('#contact-add_throbber').removeClass('hide').show();
        var button = $(this);
        // Remove any existing form
        $('#popup').remove();
        // Download the form
        var url = S3.Ap.concat('/pr/contact/create.iframe?person=' + person_id);
        if (access) {
            url += '&access=' + access;
        }
        $.get(url, function(data) {
            // Hide the Add button
            button.hide();
            // Add a DIV to show the iframe in
            button.after('<div></div>');
            // Load the Form into the iframe
            button.next().html(data);
            // Modify the submission URL
            var url2 = S3.Ap.concat('/pr/contact/create?person=' + person_id + '&controller=' + controller);
            if (access) {
                url2 += '&access=' + access;
            }
            $('#popup').find('form').attr('action', url2);
            // Hide the spinner
            $('#contact-add_throbber').hide();
            // Show the form
            $('#popup form').show();
        });
    });

    $('.contact').each(function() {
        var contact = $(this);
        var id = contact.attr('id').match(/\d+/);

        contact.find('a.delete-btn-ajax').click(function (e) {
            if (confirm(i18n.delete_confirmation)) {
                $.post(S3.Ap.concat('/pr/contact/' + id[0] + '/delete'));
                contact.addClass('hide');
            }
        });

        contact.find('a.editBtn').click(function(e) {
            var span = contact.find('span');
            var current = span.html();

            var formHolder = $('<div>').addClass('form-container');

            var form = $('<form>');
            formHolder.append(form);

            var input = $('<input id="pr_contact_value" size=62>');
            input.val(current);
            form.append(input);

            var save = $('<input type="submit" class="fright">');
            save.val('Save');
            form.append(save);

            span.replaceWith(formHolder);
            contact.addClass('edit');

            form.submit(function(e) {
                e.preventDefault();
                $('#pr_contact_value_error').remove();
                contact.removeClass('edit').addClass('saving');
                form.append($('<img class="pr_contact_throbber inline-throbber fright">'));
                form.find('input[type=submit]').addClass('hide');
                $.post(S3.Ap.concat('/pr/contact/' + id[0] + '.s3json'),
                    '{"$_pr_contact":' + JSON.stringify({'value': input.val()}) + '}',
                    function(data) {
                        if (data.status == 'failed') {
                            try {
                                error_message = data.tree.$_pr_contact[0].value['@error'];
                            } catch (e) {
                                error_message = data.message;
                            }
                            $('#pr_contact_value').after(
                                $('<div id="pr_contact_value_error" class="error">' + error_message + '</div>')
                                    .css({display: 'none'})
                                    .slideDown('slow')
                                    .click(function() { $(this).fadeOut('slow'); return false; })
                            );
                            contact.removeClass('saving').addClass('edit');
                            form.find('input[type=submit]').removeClass('hide');
                            $('.pr_contact_throbber').remove();
                        } else {
                            contact.removeClass('saving');
                            // @ToDo: Use returned value instead of submitted one
                            var value = input.val();
                            formHolder.replaceWith($('<span>').html(value));
                        }
                    },
                    'json'
                );
            });
        });
    });

    $('#emergency-add').click(function() {
        // Show a Spinner
        $('#emergency-add_throbber').removeClass('hide').show();
        var button = $(this);
        // Remove any existing form
        $('.iframe-container').remove();
        // Display all contacts
        $('.emergency').show();
        // Download the form
        var url = S3.Ap.concat('/pr/contact_emergency/create.iframe');
        if (access) {
            url += '&access=' + access;
        }
        $.get(url, function(data) {
            // Hide the Add button
            button.hide();
            // Add a DIV to show the iframe in
            button.after('<div class="iframe-container"></div>');
            // Load the Form into the iframe
            button.next().html(data);
            // Modify the submission URL
            var url2 = S3.Ap.concat('/pr/contact_emergency/create?person=' + person_id + '&controller=' + controller);
            if (access) {
                url2 += '&access=' + access;
            }
            // Hide the spinner
            $('#emergency-add_throbber').hide();
            // Modify the submission URL, Display form
            var $form = $('.iframe-container form');
            $form.attr('action', url2).show();
        });
    });

    $('.emergency').each(function() {
        var emergency = $(this);
        var id = emergency.attr('id').match(/\d+/);

        emergency.find('a.delete-btn-ajax').click(function (e) {
            if (confirm(i18n.delete_confirmation)) {
                $.post(S3.Ap.concat('/pr/contact_emergency/' + id + '/delete'));
                emergency.addClass('hide');
            }
        });

        emergency.find('a.editBtn').click(function() {
            // Show a Spinner
            $('#emergency-add_throbber').removeClass('hide').show();
            // Download the form
            var url = S3.Ap.concat('/pr/contact_emergency/' + id + '.iframe/update');
            $.get(url, function(data) {
                // Remove any existing form
                $('.iframe-container').remove();
                // Display all contacts
                $('.emergency').show();
                // Show Add button
                $('#emergency-add').show();
                // Hide the Read row
                emergency.hide();
                // Add a DIV to show the iframe in
                emergency.after('<div class="iframe-container"></div>');
                // Load the Form into the iframe
                emergency.next().html(data);
                // Hide the spinner
                $('#emergency-add_throbber').hide();
                // Modify the submission URL, Display form
                var url2 = S3.Ap.concat('/pr/contact_emergency/' + id + '/update?person=' + person_id + '&controller=' + controller);
                var $form = $('.iframe-container form');
                $form.attr('action', url2).show();
            });
        });
    });

    /* Addresses not done in this controller for now as can't load Google Maps properly
    $('#address-add').click(function () {
        // Show a Spinner
        $('#address-add_throbber').removeClass('hide').show();
        var button = $(this);
        // Remove any existing form
        $('#popup').remove()
        // Download the form
        var url = S3.Ap.concat('/pr/address/create.iframe?person=' + person_id)
        if (access) {
            url += '&access=' + access;
        }
        $.get(url, function(data) {
            // Hide the Add button
            button.hide();
            // Add a DIV to show the iframe in
            button.after('<div></div>');
            // Load the Form into the iframe
            button.next().html(data);
            // Activate the Location Selector
            s3_gis_locationselector_activate();
            // Modify the submission URL
            var url2 = S3.Ap.concat('/pr/address/create?person=' + person_id + '&controller=' + controller);
            if (access) {
                url2 += '&access=' + access;
            }
            $('#popup').find('form').attr('action', url2);
            // Hide the spinner
            $('#address-add_throbber').hide();
        });
    });

    $('.address').each(function () {
        var address = $(this);
        var id = address.attr('id').match(/\d+/);
        address.find('a.editBtn').click(function () {
            // Show a Spinner
            $('#address-add_throbber').removeClass('hide').show();
            // Download the form
            var url = S3.Ap.concat('/pr/address/' + id + '.iframe/update')
            $.get(url, function(data) {
                // Remove any existing form
                $('#popup').remove()
                // Hide the Read row
                address.hide();
                // Add a DIV to show the iframe in
                address.after('<div></div>');
                // Load the Form into the iframe
                address.next().html(data);
                // Activate the Location Selector
                s3_gis_locationselector_activate();
                // Modify the submission URL
                var url2 = S3.Ap.concat('/pr/address/' + id + '/update?person=' + person_id + '&controller=' + controller);
                $('#popup').find('form').attr('action', url2);
                // Hide the spinner
                $('#address-add_throbber').hide();
            });
        });
    });
    */
});

//}());
// END ========================================================================
