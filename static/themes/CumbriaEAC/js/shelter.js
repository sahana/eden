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

    var status_field = $('#cr_shelter_sub_shelter_details_status');

    if (['3', '4', '5'].includes(status_field.val())) {
        // Shelter is Open, so set watch on form submission
        $('form:not(.filter-form,.pt-form)').on('submit.eac', function(event){
            if (['1', '6'].includes(status_field.val())) {
                // Shelter is now Closed
                // Lookup the number of clients who remain checked-in
                var result;
                $.ajaxS3({
                    'url': S3.Ap.concat('/cr/shelter/' + S3.r_id + '/clients'),
                    'async': false,
                    'success': function (response) {
                        if (response) {
                            // There are still clients checked-in, so warn:
                            var nclients = response + ' client';
                            if (response > 1) {
                                nclients += 's';
                            }
                            var confirmation = confirm('Closing the Shelter will check-out ' + nclients + ', are you sure?');
                            if (confirmation) {
                                // Unbind handler so it doesn't get called a 2nd time
                                $('form').off('submit.eac');
                                // Normal Submit
                                result = true;
                                //return true;
                            } else {
                                // Stop Event Propagation
                                event.stopImmediatePropagation();
                                // Prevent Submission
                                result = false;
                                //return false;
                            }
                        } else {
                            // Unbind handler so it doesn't get called a 2nd time
                            $('form').off('submit.eac');
                            // Normal Submit
                            result = true;
                            //return true;
                        }
                    },
                    'error': function () {
                        // Stop Event Propagation
                        event.stopImmediatePropagation();
                        // Prevent Submission
                        result = false;
                        //return false;
                    }
                });
                return result;
            }
        });
    }

});