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
	btn.prop('disabled', true);

	// POST the s3json to the saved_search REST controller
	$.ajax({
		type: 'POST',
		url: S3.search.saveOptions.url,
		data: S3.search.saveOptions.data,
		success: function(data) {
			// If successful this will be the new record ID
			var recordId = data.created[0];

			// Set the id of the new hyperlink to the id the button had
			var id = (btn.attr('id') != undefined) ? btn.attr('id') : '';

			// Create a new hyperlink pointing to the new record
			// under the current users' profile
			var link = $('<a/>').attr('id', id)
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
};

// ============================================================================

S3.search.AutocompleteTimer = function() {
	// Cancel previous timer
	try {
		clearTimeout(S3.TimeoutVar[$(this).attr('id')]);
	} catch(err) {}
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
    } catch(err) {}

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
    var FormValues = selSearchDiv.find(':input[value]').serialize();
    if (!FormValues) {
    	// Do nothing
    	selThrobber.remove();
    	$('#' + Fieldname + '_result_list').remove();
    	return;
    }

    // @ToDo: Add a time delay before making an AJAX call

    /* Show Throbber */
    selResultList.remove();
    if (selThrobber.length === 0 ) {
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

	            if (data.length === 0) {
	                table += '<LI class = "search_autocomplete_result_item" ' +
                             'style = "border:1px solid;list-style-type:none;">' +
                             i18n.no_match + '</LI>';
	            } else {
	                for (var i = 0; i < data.length; i++) {
	                    table += '<LI id="' +  data[i].id + '"' +
	                            'class = "search_autocomplete_result_item" ' +
	                            'style = "border:1px solid;list-style-type:none;">';
	                    var selRepresent = $(data[i].represent);
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
            var selSearchForm = $('.search_form[fieldname="' + $(this).attr('fieldname') + '"]');
            if (selSearchForm.length === 0) {
                // Not an Search Form embedded into a Big form, but a normal search page with a single form.
                selSearchForm = $('.search_form');
            }
            selSearchForm.find('.simple-form').slideUp();
            selSearchForm.find('.advanced-form').slideDown();
            return false;
        });
        $('.simple-lnk').click(function(e) {
        	e.preventDefault();
        	var selSearchForm = $('.search_form[fieldname="' + $(this).attr('fieldname') + '"]');
            if (selSearchForm.length === 0) {
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
    $(document).on('click', '.search_select_letter_label, .s3-grouped-checkboxes-widget-label', function(event) {
        /*
            Listen for click events on the expanding/collapsing letter widgets
        */
        var div = $(this);
        div.next('table').toggleClass('hide');
        div.toggleClass('expanded');
    });
    $('.search_select_letter_label, .s3-grouped-checkboxes-widget-label').each(function() {
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
    					  .keypress(S3.search.CancelEnterPress);

    // Select Item for Autocomplete
    $(document).on('click', '.search_autocomplete_result_list li span', function() {
        var selResultLI = $(this).parent();
        var selResultList = selResultLI.parent();
        var selSearchForm = selResultList.parent();
        var selHiddenInput = selSearchForm.parent().find('.hidden_input');

        var Fieldname = selSearchForm.attr('fieldname');

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
};

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
};

// ============================================================================
// New search framework (S3FilterForm aka "filtered GETs")

/*
 * quoteValue: add quotes to values which contain commas, escape quotes
 */
S3.search.quoteValue = function(value) {
    if (value) {
        var result = value.replace(/\"/, '\\"');
        if (result.search(/\,/) != -1) {
            result = '"' + result + '"';
        }
        return result
    } else {
        return (value);
    }
}

/*
 * getCurrentFilters: retrieve all current filters
 */
S3.search.getCurrentFilters = function() {

    // @todo: allow form selection (=support multiple filter forms per page)
    
    var queries = [];

    // Text widgets
    $('.text-filter:visible').each(function() {

        var id = $(this).attr('id');

        var url_var = $('#' + id + '-data').val(),
            value = $(this).val();
        if (value) {
            var values = value.split(' '), v;
            for (var i=0; i < values.length; i++) {
                v = '*' + values[i] + '*';
                queries.push(url_var + '=' + S3.search.quoteValue(v));
            }
        }
    });

    // Options widgets
    $('.options-filter:visible,' +
      '.options-filter.multiselect-filter-widget.active,' +
      '.options-filter.multiselect-filter-bootstrap.active').each(function() {
        var id = $(this).attr('id');
        var url_var = $('#' + id + '-data').val();
        var operator = $("input:radio[name='" + id + "_filter']:checked").val();
        var contains = /__contains$/;
        var anyof = /__anyof$/;
        if (operator == 'any' && url_var.match(contains)) {
            url_var = url_var.replace(contains, '__anyof');
        } else if (operator == 'all' && url_var.match(anyof)) {
            url_var = url_var.replace(anyof, '__contains');
        }
        if (this.tagName.toLowerCase() == 'select') {
            // Standard SELECT
            value = '';
            values = $(this).val();
            if (values) {
                for (i=0; i < values.length; i++) {
                    v = S3.search.quoteValue(values[i]);
                    if (value === '') {
                        value = v;
                    } else {
                        value = value + ',' + v;
                    }
                }
            }
        } else {
            // Checkboxes widget
            var value = '';
            $("input[name='" + id + "']:checked").each(function() {
                if (value === '') {
                    value = S3.search.quoteValue($(this).val());
                } else {
                    value = value + ',' + S3.search.quoteValue($(this).val());
                }
            });
        }
        if (value !== '') {
            queries.push(url_var + '=' + value);
        }
    });

    // Numerical range widgets -- each widget has two inputs.
    $('.range-filter-input:visible').each(function() {
        var id = $(this).attr('id');
        var url_var = $('#' + id + '-data').val();
        var value = $(this).val();
        if (value) {
            queries.push(url_var + '=' + value);
        }
    });

    // Date(time) range widgets -- each widget has two inputs.
    $('.date-filter-input:visible').each(function() {
        var id = $(this).attr('id'), value = $(this).val();
        var url_var = $('#' + id + '-data').val(), dt, dtstr;
        var pad = function (val, len) {
            val = String(val);
            len = len || 2;
            while (val.length < len) val = "0" + val;
            return val;
        };
        var iso = function(dt) {
            return dt.getFullYear() + '-' +
                   pad(dt.getMonth()+1, 2) + '-' +
                   pad(dt.getDate(), 2) + 'T' +
                   pad(dt.getHours(), 2) + ':' +
                   pad(dt.getMinutes(), 2) + ':' +
                   pad(dt.getSeconds(), 2);
        };
        if (value) {
            if ($(this).hasClass('datetimepicker')) {
                if ($(this).hasClass('hide-time')) {
                    dt = $(this).datepicker('getDate');
                    op = id.split('-').pop();
                    if (op == 'le' || op == 'gt') {
                        dt.setHours(23, 59, 59, 0);
                    } else {
                        dt.setHours(0, 0, 0, 0);
                    }
                } else {
                    dt = $(this).datetimepicker('getDate');
                }
                dt_str = iso(dt);
                queries.push(url_var + '=' + dt_str);
            } else {
                dt = Date.parse(value);
                if (isNaN(dt)) {
                    // Unsupported format (e.g. US MM-DD-YYYY), pass
                    // as string, and hope the server can parse this
                    dt_str = '"'+ value + '"';
                } else {
                    dt_str = iso(new Date(dt));
                }
                queries.push(url_var + '=' + dt_str);
            }
        }
    });

    // Location widgets
    $('.location-filter:visible,' +
      '.location-filter.multiselect-filter-widget.active,' +
      '.location-filter.multiselect-filter-bootstrap.active').each(function() {
        var id = $(this).attr('id');
        var url_var = $('#' + id + '-data').val();
        var operator = $("input:radio[name='" + id + "_filter']:checked").val();
        if (this.tagName.toLowerCase() == 'select') {
            // Standard SELECT
            value = '';
            values = $(this).val();
            if (values) {
                for (i=0; i < values.length; i++) {
                    v = S3.search.quoteValue(values[i]);
                    if (value === '') {
                        value = v;
                    } else {
                        value = value + ',' + v;
                    }
                }
            }
        } else {
            // Checkboxes widget
            var value = '';
            $("input[name='" + id + "']:checked").each(function() {
                if (value === '') {
                    value = S3.search.quoteValue($(this).val());
                } else {
                    value = value + ',' + S3.search.quoteValue($(this).val());
                }
            });
        }
        if (value !== '') {
            queries.push(url_var + '=' + value);
        }
    });

    // Other widgets go here...

    // return queries to caller
    return queries;
};

/*
 * filterURL: add filters to a URL
 * @note: this removes+replaces all existing filters in the URL query
 */
S3.search.filterURL = function(url, queries) {

    // Construct the URL
    var url_parts = url.split('?'), url_query = queries.join('&');
    if (url_parts.length > 1) {
        var qstr = url_parts[1], query = {};
        var a = qstr.split('&'), v, i;
        for (i=0; i<a.length; i++) {
            var b = a[i].split('=');
            if (b.length > 1 && b[0].search(/\./) == -1) {
                query[decodeURIComponent(b[0])] = decodeURIComponent(b[1]);
            }
        }
        for (i=0; i<queries.length; i++) {
            v = queries[i].split('=');
            if (v.length > 1) {
                query[v[0]] = v[1];
            }
        }
        var url_queries = [], url_query;
        for (v in query) {
            url_queries.push(v + '=' + query[v]);
        }
        url_query = url_queries.join('&');
    }
    var filtered_url = url_parts[0];
    if (url_query) {
        filtered_url = filtered_url + '?' + url_query;
    }
    return filtered_url;
};

/*
 * updateOptions: Update the options of all filter widgets
 */
S3.search.updateOptions = function(options) {

    for (filter_id in options) {
        var widget = $('#' + filter_id);
        if (widget.length) {
            var newopts = options[filter_id], i;

            // OptionsFilter
            if ($(widget).hasClass('options-filter')) {
                if ($(widget)[0].tagName.toLowerCase() == 'select') {
                    // Standard SELECT
                    var selected = $(widget).val(), k, v, s=[], opts='';
                    for (i=0; i<newopts.length; i++) {
                        k = newopts[i][0].toString();
                        v = newopts[i][1];
                        if (selected && $.inArray(k, selected) >= 0) {
                            s.push(k);
                        }
                        opts += '<option value="' + k + '">' + v + '</option>';
                    }
                    $(widget).html(opts);
                    if (s) {
                        $(widget).val(s);
                    }
                    if (typeof(widget.multiselect) !== undefined) {
                        widget.multiselect('refresh');
                    }
                } else {
                    // other widget types of options filter (e.g. grouped_checkboxes)
                }

            } else {
                // @todo: other filter types (e.g. S3LocationFilter)
            }
        }
    }
};

/*
 * ajaxUpdateOptions: Ajax-update the options in a filter form
 */
S3.search.ajaxUpdateOptions = function(form) {

    // Ajax-load the item
    var ajaxurl = $(form).find('input.filter-ajax-url');
    if (ajaxurl.length) {
        ajaxurl = $(ajaxurl[0]).val();
    }
    $.ajax({
        'url': ajaxurl,
        'success': function(data) {
            S3.search.updateOptions(data);
        },
        'error': function(request, status, error) {
            if (error == 'UNAUTHORIZED') {
                msg = i18n.gis_requires_login;
            } else {
                msg = request.responseText;
            }
            console.log(msg);
        },
        'dataType': 'json'
    });
};

/*
 * S3FilterForm: document-ready script
 */
$(document).ready(function() {

    // Activate drop-down checklist widgets:
    
    // Mark active, otherwise submit can't find them
    $('.multiselect-filter-widget:visible').addClass('active');
    $('.multiselect-filter-widget').each(function() {
        if ($(this).find('option').length > 5) {
            $(this).multiselect({
                selectedList: 5
            }).multiselectfilter();
        } else {
            $(this).multiselect({
                selectedList: 5
            });
        }
    });

    if (typeof($.fn.multiselect_bs) != 'undefined') {
        // Alternative with bootstrap-multiselect (note the hack for the fn-name):
        $('.multiselect-filter-bootstrap:visible').addClass('active');
        $('.multiselect-filter-bootstrap').multiselect_bs();
    }

    // Hierarchical Location Filter
    $('.location-filter').on('change', function() {
        var name = this.name;
        var values = $('#' + name).val();
        var base = name.slice(0, -1);
        var level = parseInt(name.slice(-1));
        var hierarchy = S3.location_filter_hierarchy;
        // Initialise vars in a way in which we can access them via dynamic names
        this.options1 = [];
        this.options2 = [];
        this.options3 = [];
        this.options4 = [];
        this.options5 = [];
        var new_level;
        if (hierarchy.hasOwnProperty('L' + level)) {
            // Top-level
            var _hierarchy = hierarchy['L' + level];
            for (opt in _hierarchy) {
                if (_hierarchy.hasOwnProperty(opt)) {
                    if (values === null) {
                        // Show all Options
                        for (option in _hierarchy[opt]) {
                            if (_hierarchy[opt].hasOwnProperty(option)) {
                                new_level = level + 1;
                                this['options' + new_level].push(option);
                                if (typeof(_hierarchy[opt][option]) === 'object') {
                                    var __hierarchy = _hierarchy[opt][option];
                                    for (_opt in __hierarchy) {
                                        if (__hierarchy.hasOwnProperty(_opt)) {
                                            new_level = level + 2;
                                            this['options' + new_level].push(_opt);
                                            // @ToDo: Greater recursion
                                            //if (typeof(__hierarchy[_opt]) === 'object') {
                                            //}
                                        }
                                    }
                                }
                            }
                        }
                    } else {
                        for (i in values) {
                            if (values[i] === opt) {
                                for (option in _hierarchy[opt]) {
                                    if (_hierarchy[opt].hasOwnProperty(option)) {
                                        new_level = level + 1;
                                        this['options' + new_level].push(option);
                                        if (typeof(_hierarchy[opt][option]) === 'object') {
                                            var __hierarchy = _hierarchy[opt][option];
                                            for (_opt in __hierarchy) {
                                                if (__hierarchy.hasOwnProperty(_opt)) {
                                                    new_level = level + 2;
                                                    this['options' + new_level].push(_opt);
                                                    // @ToDo: Greater recursion
                                                    //if (typeof(__hierarchy[_opt]) === 'object') {
                                                    //}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        } else if (hierarchy.hasOwnProperty('L' + (level - 1))) {
            // Nested 1 in
            var _hierarchy = hierarchy['L' + (level - 1)];
            // Read higher level
            var _values = $('#' + base + (level - 1)).val();
            for (opt in _hierarchy) {
                if (_hierarchy.hasOwnProperty(opt)) {
                    /* Only needed if not hiding
                    if (_values === null) {
                    } else { */
                    for (i in _values) {
                        if (_values[i] === opt) {
                            for (option in _hierarchy[opt]) {
                                if (_hierarchy[opt].hasOwnProperty(option)) {
                                    if (values === null) {
                                        // Show all subsequent Options
                                        for (option in _hierarchy[opt]) {
                                            if (_hierarchy[opt].hasOwnProperty(option)) {
                                                var __hierarchy = _hierarchy[opt][option];
                                                for (_opt in __hierarchy) {
                                                    if (__hierarchy.hasOwnProperty(_opt)) {
                                                        new_level = level + 1;
                                                        this['options' + new_level].push(_opt);
                                                        // @ToDo: Greater recursion
                                                        //if (typeof(__hierarchy[_opt]) === 'object') {
                                                        //}
                                                    }
                                                }
                                            }
                                        }
                                    } else {
                                        for (i in values) {
                                            if (values[i] === option) {
                                                var __hierarchy = _hierarchy[opt][option];
                                                for (_opt in __hierarchy) {
                                                    if (__hierarchy.hasOwnProperty(_opt)) {
                                                        new_level = level + 1;
                                                        this['options' + new_level].push(_opt);
                                                        // @ToDo: Greater recursion
                                                        //if (typeof(__hierarchy[_opt]) === 'object') {
                                                        //}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        } else if (hierarchy.hasOwnProperty('L' + (level - 2))) {
            // @ToDo
        }
        for (l = level + 1; l <= 5; l++) {
            var select = $('#' + base + l);
            if (typeof(select) != 'undefined') {
                var options = this['options' + l];
                options.sort();
                _options = '';
                for (i in options) {
                    if (options.hasOwnProperty(i)) {
                        _options += '<option value="' + options[i] + '">' + options[i] + '</option>';
                    }
                }
                select.html(_options);
                select.multiselect('refresh');
                if (l === (level + 1)) {
                    if (values) {
                        // Show next level down (if hidden)
                        select.next('button').removeClass('hidden').show();
                        // @ToDo: Hide subsequent levels (if configured to do so)
                    } else {
                        // @ToDo: Hide next levels down (if configured to do so)
                        //select.next('button').hide();
                    }
                }
            }
        }
    });
    
    // Filter-form submission
    $('.filter-submit').click(function() {
        try {
            // Update Map results URL
            Ext.iterate(map.layers, function(key, val, obj) {
                if (key.s3_layer_id == 'search_results') {
                    var layer = map.layers[val];
                    var url = layer.protocol.url;
                    url = S3.search.filterURL(url);
                    layer.protocol.url = url;
                    // If map is showing then refresh the layer
                    if (S3.gis.mapWin.isVisible()) {
                        // Set a new event when the layer is loaded (defined in s3.dataTable.js)
                        layer.events.on({
                            'loadend': s3_gis_search_layer_loadend
                        });
                        // Disable Clustering to get correct bounds
                        Ext.iterate(layer.strategies, function(key, val, obj) {
                            if (key.CLASS_NAME == 'OpenLayers.Strategy.AttributeCluster') {
                                layer.strategies[val].deactivate();
                            }
                        });
                        Ext.iterate(layer.strategies, function(key, val, obj) {
                            if (key.CLASS_NAME == 'OpenLayers.Strategy.Refresh') {
                                layer.strategies[val].refresh();
                            }
                        });
                    }
                }
            });
        } catch(err) {}
        
        var url = $(this).nextAll('input.filter-submit-url[type="hidden"]').val();
        var queries = S3.search.getCurrentFilters();
        
        if ($(this).hasClass('filter-ajax')) {
            // Ajax-refresh the target object (@todo: support multiple)
            var target = $(this).nextAll('input.filter-submit-target[type="hidden"]').val();
            if ($('#' + target).hasClass('dl')) {

                // Ajax-reload the datalist
                dlAjaxReload(target, queries);
                
            } else if ($('#' + target).hasClass('dataTable')) {
                
                // Experimental: Ajax-reloading of the datatable
                var ajaxurl = null;
                var config = $('input#' + target + '_configurations');
                if (config.length) {
                    var settings = JSON.parse($(config).val());
                    var ajaxurl = settings['ajaxUrl'];
                    if (typeof ajaxurl != 'undefined') {
                        ajaxurl = S3.search.filterURL(ajaxurl, queries);
                    } else {
                        ajaxurl = null;
                    }
                }
                if (ajaxurl) {
                    $('#' + target).dataTable().fnReloadAjax(ajaxurl);
                } else {
                    url = S3.search.filterURL(url, queries);
                    window.location.href = url;
                }
                
            } else {

                // All other targets
                url = S3.search.filterURL(url, queries);
                window.location.href = url;
                
            }
        } else {
            
            // Page reload
            url = S3.search.filterURL(url, queries);
            window.location.href = url;
        }
    });
});
