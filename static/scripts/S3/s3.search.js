/**
    S3Search Static JS Code
*/
// ============================================================================
function fncSearchAutocompleteTimer() {
	// Cancel previous timer
	try {
		clearTimeout(S3.TimeoutVar[$(this).attr('id')]);
	} catch(err) {};
	var selSearchDiv = $(this);
	var fncSearchAutocompleteAjaxArg = function() { fncSearchAutocompleteAjax(selSearchDiv); };
	S3.TimeoutVar[$(this).attr('id')] = setTimeout( fncSearchAutocompleteAjaxArg, 400);
};

function fncSearchAutocompleteAjax(selSearchDiv) {

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
    selHiddenInput.val("");
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
                             S3.i18n.no_match + '</LI>';
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
                        		 S3.i18n.ac_widget_more_results +
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

function CancelEnterPress(e){
    if(e.which === 13){
        return false;
    }
};

//wait for the DOM to be loaded
$(document).ready(function() {
    /* Search Form handling */
    if ( undefined == $('.advanced-form').val() ) {
        // No Action Required
    } else if ( undefined == $('.simple-form').val() ) {
        // Only an Advanced Form
        $('.simple-form').hide();
        $('.advanced-form').show();
    } else {
        // Simple & Advanced Search Forms
        if ($('#search-mode').attr('mode')=='advanced') {
            $('.simple-form').hide();
            $('.advanced-form').show();
        } else {
            $('.advanced-form').hide();
        }
        $('.advanced-lnk').click(function(e) {
        	e.preventDefault();
            var selSearchForm = $('.search_form[fieldname="' + $(this).attr('fieldname') + '"]')
            if (selSearchForm.length == 0) {
                // Not an Search Form embedded into a Big form, but a normal search page with a single form.
                selSearchForm = $('.search_form');
            }
            selSearchForm.find('.simple-form').hide();
            selSearchForm.find('.advanced-form').show();
            return false;
        });
        $('.simple-lnk').click(function(e) {
        	e.preventDefault();
        	var selSearchForm = $('.search_form[fieldname="' + $(this).attr('fieldname') + '"]')
            if (selSearchForm.length == 0) {
                // Not an Search Form embedded into a Big form, but a normal search page with a single form.
                selSearchForm = $('.search_form');
            }
            selSearchForm.find('.advanced-form').hide();
            selSearchForm.find('.simple-form').show();
            return false;
        });
    }

    /* Expanding & Collapsing Letters */
    $('.search_select_letter_label').click( function () {
        $('#' + $(this).attr('id').replace('label', 'widget')).slideToggle();
        $(this).toggleClass('expanded');
    });

    /* Search AutoComplete */

    // Events to capture autocomplete input
    $('div.simple-form').keyup( fncSearchAutocompleteTimer )
    					.click( fncSearchAutocompleteTimer )
    					.keypress(CancelEnterPress);

    $('div.advanced-form').keyup( fncSearchAutocompleteTimer )
    					  .click( fncSearchAutocompleteTimer )
    					  .keypress(CancelEnterPress);

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
});
