/* JS code to modify req/create forms
   - Inserted into page in req_customize_req_fields()
   - Defaults the requester / contact to the site contact when the site is
     selected.
*/

$(document).ready(function() {
	// When the site is selected, fetch the site's contact and put that person
	// in as the requester.
	// @ToDo: Switch to using .ajaxS3.
	// @ToDo: For preference, change .ajaxS3 use the same callback mechanism as
	// .ajax, so that the same functions can be supplied to both. This would
	// allow library functions normally called with .ajax to also be called
	// with .ajaxS3.
	// @ToDo: Pull out the anonymous function passed to done into a named
	// function that conditionally updates all the person fields, and then
	// share it with s3.add_person.js.
	$('#req_req_site_id').change(function() {
	    var site_id = $('#req_req_site_id').val();
	    if (site_id) {
	        var url = S3.Ap.concat('/req/site_contact.json/' + site_id);
		    $.ajax({
			    url: url,
			    dataType: 'json'
		    }).done(function(data) {
                if (data) {
                	// Fill in any supplied items, and clear any we don't find.
                	// That's because the user may have selected a contact with
                	// other items set, then selected someone else with
                	// different items set, and we don't want the now-unset ones
                	// to be left in the form. Nothing happens if we try to
                	// select a non-existent item -- the selector will just
                	// yield an empty set. This will also empty the fields if
                	// no contact person was found.
                	if (data.hasOwnProperty('id')) {
                		$('#req_req_requester_id').val(data['id']);
                	} else {
                        $('#req_req_requester_id').val('');
                	}
                	if (data.hasOwnProperty('full_name')) {
                		$('#req_req_requester_id_full_name').val(data['full_name']);
                	} else {
                        $('#req_req_requester_id_full_name').val('');
                	}
                	if (data.hasOwnProperty('mobile_phone')) {
                		$('#req_req_requester_id_mobile_phone').val(data['mobile_phone']);
                	} else {
                        $('#req_req_requester_id_mobile_phone').val('');
                	}
                	if (data.hasOwnProperty('email')) {
                		$('#req_req_requester_id_email').val(data['email']);
                	} else {
                        $('#req_req_requester_id_email').val('');
                	}
                }
		    }).fail(function(jqXHR, textStatus, errorThrown) {
	            console.log(jqXHR.responseText);
		    });
	    }
	});
});