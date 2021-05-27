$(document).ready(function(){

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