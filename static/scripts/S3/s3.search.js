/**
    S3Search Static JS Code
*/

S3.search = Object();

/*
 * Save the current search to the users' profile
 * so it can be subscribed to
 */
S3.search.saveCurrentSearch = function(event) {
	// The Save this Search button
	var btn = $(event.currentTarget);

	// Show the progress indicator in the button
	$('<img/>').attr('src', S3.Ap.concat('/static/img/indicator.gif'))
               .insertAfter(btn);

	// Disable the button to prevent clicking while loading
	btn.attr('disabled', 'disabled');

	// POST the s3json to the saved_search REST controller
	$.ajax({
		type: 'POST',
		url: S3.search.saveOptions.url,
		data: S3.search.saveOptions.data,
		success: function(data) {
			// If successful this will be the new record ID
			var recordId = data.created[0];

			// Set the id of the new hyperlink to the id the button had
			id = (btn.attr('id') != undefined) ? btn.attr('id') : '';

			// Create a new hyperlink pointing to the new record
			// under the current users' profile
			var link = $('<a/>')
				.attr('id', id)
				.attr('href', S3.search.saveOptions.url_detail.replace('%3Cid%3E', recordId))
				.text(i18n.edit_saved_search);

			// replace the Save button with the hyperlink
			btn.replaceWith(link);

			// change indicator to 'success' icon
			link.next().attr('src', S3.Ap.concat('/static/img/tick.png'));
		},
		error: function(data) {
			// If the request fails, change the indicator icon
			btn.next().attr('src', S3.Ap.concat('/static/img/cross2.png'));

			// show the response text
			$('<span/>').text(data.statusText)
                        .insertAfter(btn);
		}
	});
	//event.preventDefault();
	return false;
}

// ============================================================================

S3.search.AutocompleteTimer = function() {
	// Cancel previous timer
	try {
		clearTimeout(S3.TimeoutVar[$(this).attr('id')]);
	} catch(err) {};
	var selSearchDiv = $(this);
	var fncSearchAutocompleteAjaxArg = function() {
        S3.search.AutocompleteAjax(selSearchDiv);
    };
	S3.TimeoutVar[$(this).attr('id')] = setTimeout(fncSearchAutocompleteAjaxArg, 400);
};

S3.search.AutocompleteAjax = function(selSearchDiv) {

    // Cancel previous request
    try {
        S3.JSONRequest[selSearchDiv.attr('id')].abort();
    } catch(err) {};

    var selSearchForm = selSearchDiv.parent();
    var selHiddenInput = selSearchForm.parent().find('.hidden_input');
    var get_fieldname = selSearchForm.attr('get_fieldname');

    var resourcename = selSearchForm.attr('resourcename');
    var Fieldname = selSearchForm.attr('fieldname');

    var selInput = $('[name ^= "' + Fieldname + '_search_simple"]');

    // Clear the current input
    selHiddenInput.val('');
	selHiddenInput.change(); // Trigger other events

    var selResultList = $('#' + Fieldname + '_result_list');
    var selThrobber = $('#' + Fieldname + '_ajax_throbber');

    // Check if there is enough input to filter
    var FormValues = selSearchDiv.find(':input[value]').serialize()
    if (!FormValues) {
    	// Do nothing
    	selThrobber.remove();
    	$('#' + Fieldname + '_result_list').remove();
    	return
    }

    // @ToDo: Add a time delay before making an AJAX call

    /* Show Throbber */
    selResultList.remove();
    if (selThrobber.length == 0 ) {
        selSearchForm.append('<div id="' + Fieldname + '_ajax_throbber" class="ajax_throbber"/>');
        selThrobber = $('#' + Fieldname + '_ajax_throbber'); // Refresh selector
    }

    var prefix = selSearchForm.attr('prefix');
    var formname = selSearchDiv.attr('class').replace('-', '_');
    var url = S3.Ap.concat('/', prefix, '/', resourcename, '/search.acjson?',
                            formname, '=True&', FormValues);

    // AJAX uses search method, where input name uses resourcename not Fieldname
    url = url.replace(Fieldname, resourcename);

    if (get_fieldname != undefined) {
        url += '&get_fieldname=' + get_fieldname;
    }

    var data;

    // Save JSON Request by element id
    S3.JSONRequest[selSearchDiv.attr('id')] = $.ajax( {
        url: url,
        dataType: 'json',
        success: function(data) {
        	if (data.length == 1) {
	        	/* Populate Field with Result */
        		var represent =  $(data[0].represent).text();
        		selInput.val(represent);
        		//selInput.attr('_value', represent);
        		selHiddenInput.val(data[0].id);
        		selHiddenInput.change(); // Trigger other events
        	} else {
	            /* Create Table Element */
	            var table = '<UL id = "' + Fieldname + '_result_list"' +
	                        'class = "search_autocomplete_result_list" ' +
	                        'style = "display:inline;">';

	            if (data.length == 0) {
	                table += '<LI class = "search_autocomplete_result_item" ' +
                             'style = "border:1px solid;list-style-type:none;">' +
                             i18n.no_match + '</LI>';
	            } else {
	                for (var i = 0; i < data.length; i++) {
	                    table += '<LI id="' +  data[i].id + '"' +
	                            'class = "search_autocomplete_result_item" ' +
	                            'style = "border:1px solid;list-style-type:none;">';
	                    var selRepresent = $(data[i].represent)
	                    table += '<SPAN style = "cursor:pointer;">' + selRepresent.text() + '</SPAN>' +
	                    		 '<A href="' + selRepresent.attr("href") + '" ' +
	                    		 'target = "blank" ' +
	                    		 'style = "font-size:0.8em;margin-right:10px;float:right;">' +
	                    		 'Details</A>' +
	                    		'</LI>';
	                }
	                if (data.length > 10 ) {
	                	table += '<LI ' +
                        		 'class = "search_autocomplete_result_item" ' +
                        		 'style = "border:1px solid;list-style-type:none;"><I>' +
                        		 i18n.ac_widget_more_results +
	                			 '</I></LI>';
	                }
	            }
	            table += '</UL>';
	            selSearchForm.append(table);
        	}
        	selThrobber.remove();
            // Prevents the search being re-triggered
            $('[name ^= "' + Fieldname + '_search_simple"]').blur();
        }
    });
};

S3.search.CancelEnterPress = function(e){
    if(e.which === 13){
        return false;
    }
};

// wait for the DOM to be loaded
$(document).ready(function() {
    /* Search Form handling */
    if ( undefined == $('.advanced-form').val() ) {
        // No Action Required
    } else if ( undefined == $('.simple-form').val() ) {
        // Only an Advanced Form
        $('.simple-form').slideUp();
        $('.advanced-form').slideDown();
    } else {
        $('.advanced-lnk').click(function(e) {
        	e.preventDefault();
            var selSearchForm = $('.search_form[fieldname="' + $(this).attr('fieldname') + '"]')
            if (selSearchForm.length == 0) {
                // Not an Search Form embedded into a Big form, but a normal search page with a single form.
                selSearchForm = $('.search_form');
            }
            selSearchForm.find('.simple-form').slideUp();
            selSearchForm.find('.advanced-form').slideDown();
            return false;
        });
        $('.simple-lnk').click(function(e) {
        	e.preventDefault();
        	var selSearchForm = $('.search_form[fieldname="' + $(this).attr('fieldname') + '"]')
            if (selSearchForm.length == 0) {
                // Not an Search Form embedded into a Big form, but a normal search page with a single form.
                selSearchForm = $('.search_form');
            }
            selSearchForm.find('.advanced-form').slideUp();
            selSearchForm.find('.simple-form').slideDown();
            return false;
        });
    }


    /*
        Hide all the expanding/collapsing letter widgets that don't have
        any options selected
    */
    $('.search_select_letter_label,.s3-grouped-checkboxes-widget-label').live('click', function(event) {
        /*
            Listen for click events on the expanding/collapsing letter widgets
        */
        var div = $(this)
        div.next('table').toggleClass('hide');
        div.toggleClass('expanded');
    })
    .each(function() {
        widget = $(this).next();
        if ($(':checked', widget).length < 1) {
        	$(this).click();
        }
    });

    /* Search AutoComplete */

    // Events to capture autocomplete input
    $('div.simple-form').keyup(S3.search.AutocompleteTimer)
    					.click(S3.search.AutocompleteTimer)
    					.keypress(S3.search.CancelEnterPress);

    $('div.advanced-form').keyup(S3.search.AutocompleteTimer)
    					  .click(S3.search.AutocompleteTimer)
    					  .keypress(S3.search.ancelEnterPress);

    // Select Item for Autocomplete
    $('.search_autocomplete_result_list li span').live('click', function() {
        var selResultLI = $(this).parent();
        var selResultList = selResultLI.parent();
        var selSearchForm = selResultList.parent();
        var selHiddenInput = selSearchForm.parent().find('.hidden_input');

        var Fieldname = selSearchForm.attr('fieldname')

        var id = selResultLI.attr('id');
        if (id != undefined) {
            selHiddenInput.val(id);
            selHiddenInput.change(); // Trigger other events
            var selInput = $('[name ^= "' + Fieldname + '_search_simple"]');
            var represent = $(this).text();
            selInput.val(represent);
            //selInput.attr('_value', represent);
            selResultList.remove();
        }
    });

    // Activate the Save Search buttons
   $('button#save-search').on('click', S3.search.saveCurrentSearch);

    // S3SearchLocationWidget
    // Allow clearing of map polygons in search forms
    $('button#gis_search_polygon_input_clear').on('click', function(event) {
        S3.search.clearMapPolygon();
        // prevent form submission
        event.preventDefault();
    });
    $('input#gis_search_polygon_input').on('change', S3.search.toggleMapClearButton)
                                       .trigger('change');
});

/*
 * S3SearchLocationWidget
 *
 * Clears the map widget in a search form and also removes the
 * polygon from the map itself
 */
S3.search.clearMapPolygon = function() {
    if (S3.gis.lastDraftFeature) {
        S3.gis.lastDraftFeature.destroy();
    }
    $('input#gis_search_polygon_input').val('').trigger('change');
}

/*
 * S3SearchLocationWidget
 *
 * If the map widget has a value, a clear button will be shown
 * otherwise it is hidden
 */
S3.search.toggleMapClearButton = function(event) {
    var inputElement = $(event.currentTarget);
    var clearButton = inputElement.siblings('button#gis_search_polygon_input_clear');
    if (inputElement.val()) {
        clearButton.show();
    } else {
        clearButton.hide();
    }
}

// ============================================================================
// New search framework

/*
 * filterURL: add all current filters to a URL
 */
S3.search.filterURL = function(url) {

    var queries = [];

    // Text widgets
    $('.text-filter:visible').each(function() {

        var id = $(this).attr('id');

        var url_var = $('#' + id + '-data').val(),
            value = $(this).val();
        if (value) {
            var values = value.split(' ');
            for (var i=0; i<values.length; i++) {
                queries.push(url_var + '=*' + values[i] + '*');
            }
        }
    });

    // Other widgets go here...

    // Construct the URL
    var url_parts = url.split('?'), url_query = queries.join('&');
    if (url_parts.length > 1) {
        if (url_query) {
            url_query = url_query + '&' + url_parts[1];
        } else {
            url_query = url_parts[1];
        }
    }
    var filtered_url = url_parts[0];
    if (url_query) {
        filtered_url = filtered_url + '?' + url_query;
    }
    return filtered_url;
}

// Test code: to be removed after implementation is complete
// $(document).ready(function() {
// 
//     $('#filter-submit-button').click(function() {
//         var url = $(this).next('input[type="hidden"]').val();
//         url = S3.search.filterURL(url);
//         window.location.href = url;
//     });
// 
// });
