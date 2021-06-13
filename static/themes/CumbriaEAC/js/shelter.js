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
        $('form:not(.filter-form,.pt-form)').submit(function(event){
            if (['1', '6'].includes(status_field.val())) {
                // Shelter is now Closed, so Warn
                return confirm('Closing the Shelter will check-out all clients, are you sure?');
            }
            // Normal Submit
            return true;
        });
    }

});