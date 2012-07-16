/* Addresses not done in this controller for now as can't load Google Maps properly
$('#address-add').click(function () {
    // Show a Spinner
    $('#address-add_throbber').removeClass('hide').show();
    var button = $(this);
    // Remove any existing form
    $('#popup').remove()
    // Download the form
    var url = S3.Ap.concat('/pr/address/create.iframe')
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
        var url2 = S3.Ap.concat('/pr/address/create?person=' + personId + '&controller=' + controller);
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
            var url2 = S3.Ap.concat('/pr/address/' + id + '/update?person=' + personId + '&controller=' + controller);
            $('#popup').find('form').attr('action', url2);
            // Hide the spinner
            $('#address-add_throbber').hide();
        });
    });
});
*/

$('#contact-add').click(function () {
    // Show a Spinner
    $('#contact-add_throbber').removeClass('hide').show();
    var button = $(this);
    // Remove any existing form
    $('#popup').remove()
    // Download the form
    var url = S3.Ap.concat('/pr/contact/create.iframe')
    $.get(url, function(data) {
        // Hide the Add button
        button.hide();
        // Add a DIV to show the iframe in
        button.after('<div></div>');
        // Load the Form into the iframe
        button.next().html(data);
        // Modify the submission URL
        var url2 = S3.Ap.concat('/pr/contact/create?person=' + personId + '&controller=' + controller);
        $('#popup').find('form').attr('action', url2);
        // Hide the spinner
        $('#contact-add_throbber').hide();
    });
});

$('.contact').each(function () {
    var contact = $(this);
    var id = contact.attr('id').match(/\d+/);

    contact.find('a.deleteBtn').click(function (e) {
        if (confirm(S3.i18n.delete_confirmation)) {
            $.post(S3.Ap.concat('/pr/contact/' + id[0] + '/delete'));
            contact.addClass('hide');
        }
    });

    contact.find('a.editBtn').click(function (e) {
        var span = contact.find('span');
        var current = span.html();

        var formHolder = $('<div>').addClass('form-container');

        var form = $('<form>');
        formHolder.append(form);

        var input = $('<input size=62>');
        input.val(current);
        form.append(input);

        var save = $('<input type="submit" class="fright">');
        save.val('Save');
        form.append(save);

        span.replaceWith(formHolder);
        contact.addClass('edit');

        form.submit(function (e) {
            e.preventDefault();
            contact.removeClass('edit').addClass('saving');
            form.append($('<img src="' + S3.Ap.concat('/static/img/jquery-ui/ui-anim_basic_16x16.gif') + '">').addClass('fright'));
            form.find('input[type=submit]').addClass('hide');
            $.post(S3.Ap.concat('/pr/contact/' + id[0] + '.s3json'),
                   '{"$_pr_contact":' + JSON.stringify({'value': input.val()}) + '}',
                   function () {
                      contact.removeClass('saving');
                      // @ToDo: Use returned value instead of submitted one
                      var value = input.val();
                      formHolder.replaceWith($('<span>').html(value));
                   }, 'json');
        });
    });
});

$('#emergency-add').click(function () {
    // Show a Spinner
    $('#emergency-add_throbber').removeClass('hide').show();
    var button = $(this);
    // Remove any existing form
    $('#popup').remove()
    // Download the form
    var url = S3.Ap.concat('/pr/contact_emergency/create.iframe')
    $.get(url, function(data) {
        // Hide the Add button
        button.hide();
        // Add a DIV to show the iframe in
        button.after('<div></div>');
        // Load the Form into the iframe
        button.next().html(data);
        // Modify the submission URL
        var url2 = S3.Ap.concat('/pr/contact_emergency/create?person=' + personId + '&controller=' + controller);
        $('#popup').find('form').attr('action', url2);
        // Hide the spinner
        $('#emergency-add_throbber').hide();
    });
});

$('.emergency').each(function () {
    var emergency = $(this);
    var id = emergency.attr('id').match(/\d+/);

    emergency.find('a.deleteBtn').click(function (e) {
        if (confirm(S3.i18n.delete_confirmation)) {
            $.post(S3.Ap.concat('/pr/contact_emergency/' + id + '/delete'));
            emergency.addClass('hide');
        }
    });

    emergency.find('a.editBtn').click(function () {
        // Show a Spinner
        $('#emergency-add_throbber').removeClass('hide').show();
        // Download the form
        var url = S3.Ap.concat('/pr/contact_emergency/' + id + '.iframe/update')
        $.get(url, function(data) {
            // Remove any existing form
            $('#popup').remove()
            // Hide the Read row
            emergency.hide();
            // Add a DIV to show the iframe in
            emergency.after('<div></div>');
            // Load the Form into the iframe
            emergency.next().html(data);
            // Modify the submission URL
            var url2 = S3.Ap.concat('/pr/contact_emergency/' + id + '/update?person=' + personId);
            $('#popup').find('form').attr('action', url2);
            // Hide the spinner
            $('#emergency-add_throbber').hide();
        });
    });
});