$(document).ready(function(){

    // Make the Streetview URL clickable
    
    var streetview_field = $('#cr_shelter_sub_streetview_value'),
        streetview_url = streetview_field.val();

    if (streetview_url) {
        streetview_field.hide()
                        .after('<button class="btn tiny button streetview_edit">Edit</button>')
                        .after('<a href="' + streetview_url + '" target="_blank" id="cr_shelter_streetview_btn">' + streetview_url + '</a>');
        $('#cr_shelter_sub_streetview_value').next().next().click(function(e) {
            e.preventDefault(); // Stop form submission
            streetview_field.show()
                            .next().hide()
                            .next().hide();
        });
    }


    // Prompt for confirmation when closing a Shelter
    // - this will check-out all clients

    var status_field = $('#cr_shelter_status');

    if (['3', '4', '5'].includes(status_field.val())) {
        // Shelter is Open, so set watch on form submission
        $('form:not(.filter-form,.pt-form)').on('submit.eac', function(event){
            // Shelter is now Closed, so Warn
            var result = confirm('Closing the Shelter will check-out all clients, are you sure?');
            if (result) {
                // Unbind handler so it doesn't get called a 2nd time
                $('form').off('submit.eac');
                // Normal Submit
                return true;
            } else {
                // Stop Event Propagation
                event.stopImmediatePropagation();
                // Prevent Submission
                return false;
            }
        });
    }

});