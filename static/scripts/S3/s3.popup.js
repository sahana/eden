/**
 * JS to handle Popup Modal forms to create new resources
 */

function s3_popup_refresh_main_form() {
    // The Get parameters
    var $_GET = getQueryParams(document.location.search);

    // Update Form?
    var refresh = $_GET['refresh'];
    if (typeof refresh != 'undefined') {
        // Update DataList/DataTable
        var selector = self.parent.$('#' + refresh);
        if (typeof selector.dataTable !== 'undefined') {
            // refresh dataTable
            selector.dataTable().fnReloadAjax();
        } else {
            var record = $_GET['record'];
            if (record !== undefined) {
                // reload a single item
                self.parent.dlAjaxReloadItem(refresh, record);
            } else {
                // reload the whole list
                self.parent.dlAjaxReload(refresh);
            }
        }
        // Also update the layer on the Maps (if any)
        var maps = self.parent.S3.gis.maps
        if (typeof maps != 'undefined') {
            var map_id, map, needle, layers, i, len, layer, strategies, j, jlen, strategy;
            for (map_id in maps) {
                map = maps[map_id];
                needle = refresh.replace(/-/g, '_');
                layers = map.layers;
                for (i=0, len=layers.length; i < len; i++) {
                    layer = layers[i];
                    if (layer.s3_layer_id == needle) {
                        strategies = layer.strategies;
                        for (j=0, jlen=strategies.length; j < jlen; j++) {
                            strategy = strategies[j];
                            if (strategy.CLASS_NAME == 'OpenLayers.Strategy.Refresh') {
                                // Reload the layer
                                strategy.refresh();
                            }
                        }
                    }
                }
            }
        }
        // Also update the options in the filter-form for this target (if any)
        var filterform = self.parent.$('#' + refresh + '-filter-form');
        if (filterform.length) {
            self.parent.S3.search.ajaxUpdateOptions(filterform);
        }
        // Remove popup
        self.parent.s3_popup_remove();
        return;
    }

    // Create form (e.g. S3AddResourceLink)
    var level = $_GET['level'];
    if (typeof level != 'undefined') {
        // Location Selector
        self.parent.s3_popup_remove();
        return;
    }

    var caller = $_GET['caller'];
    s3_debug('caller', caller);

    var person_id = $_GET['person_id'];
    if (typeof person_id != 'undefined') {
        // Person Selector
        if (typeof caller != 'undefined') {
            var field = self.parent.$('#' + caller);
            field.val(person_id).change();
        }
        self.parent.s3_popup_remove();
        return;
    }

    var re = new RegExp('.*\\' + S3.Ap + '\\/');

    var child = $_GET['child'];
    var rel_url;
    var args;
    var child_resource;
    if (typeof child === 'undefined') {
        // Use default
        var url = new String(self.location);
        rel_url = url.replace(re, '');
        args = rel_url.split('?')[0].split('/');
        var request_function = args[1];
        child_resource = request_function + '_id';
    } else {
        // Use manual override
        child_resource = child;
    }
    s3_debug('child_resource', child_resource);

    var parent = $_GET['parent'];
    var parent_resource;
    var parent_url;
    var caller_prefix;
    if (typeof parent === 'undefined') {
        // @ToDo: Make this less fragile by passing these fields as separate vars?
        var parent_field = caller.replace('_' + child_resource, '');
        s3_debug('parent_field', parent_field);
        var parent_module = parent_field.replace(/_.*/, '');

        // Find the parent resource (fixed for components)
        parent_resource = parent_field.replace(parent_module + '_', '');
        parent_url = new String(self.parent.location);
        rel_url = parent_url.replace(re, '');
        args = rel_url.split('?')[0].split('/');
        var parent_component = null;
        caller_prefix = args[0];
        var parent_function = args[1];
        if (args.length > 2) {
            if (args[2].match(/\d*/) !== null) {
                if (args.length > 3) {
                    parent_component = args[3];
                }
            } else {
                parent_component = args[2];
            }
        }
        if ((parent_component !== null) && (parent_resource != parent_function) && (parent_resource == parent_component)) {
            parent_resource = parent_function + '/' + parent_component;
        }
    } else {
        // Use manual override
        parent_resource = parent;
        parent_url = new String(self.parent.location);
        rel_url = parent_url.replace(re, '');
        args = rel_url.split('?')[0].split('/');
        caller_prefix = args[0];
    }
    s3_debug('parent_resource', parent_resource);
    s3_debug('caller_prefix', caller_prefix);

    // URL to retrieve the Options list for the field of the master resource
    var opt_url = S3.Ap.concat('/' + caller_prefix + '/' + parent_resource + '/options.s3json?field=' + child_resource);

    // Dropdown or Autocomplete
    var selector = self.parent.$('#' + caller);
    s3_debug('selector', selector);
    var inline = (caller.substring(0, 4) == 'sub_');
    var dummy = self.parent.$('#dummy_' + caller);
    var has_dummy = (dummy.val() != undefined);
    s3_debug('has_dummy', has_dummy);
    var checkboxes = selector.hasClass('checkboxes-widget-s3');
    var append;
    if (checkboxes) {
        // The number of columns
        var cols = self.parent.$('#' + caller + ' tbody tr:first').children().length;
        append = [];
    } else {
        var options = self.parent.$('#' + caller + ' >option');
        var dropdown = options.length;
        /* S3SearchAutocompleteWidget should do something like this instead */
        //var dummy = self.parent.$('input[name="item_id_search_simple_simple"]');
        //var has_dummy = (dummy.val() != undefined);
        if (dropdown) {
            append = [];
        } else {
            // Return only current record if field is autocomplete
            opt_url += '&only_last=1';
        }
    }
    var value_high = 1;
    var represent_high = '';
    $.getJSONS3(opt_url, function (data) {
        var value, represent, id;
        var count = 0;

        $.each(data['option'], function() {
            value = this['@value'];
            represent = this['$'];
            if (typeof represent === 'undefined') {
                represent = '';
            }
            if (dropdown) {
                append.push(["<option value='", value, "'>", represent, "</option>"].join(''));
            } else if (checkboxes) {
                id = 'id_' + child_resource + '-' + count;
                append.push(["<td><input id='", id, "' name='", child_resource, "' value='", value, "' type='checkbox'><label for='", id, "'>", represent, "</label></td>"].join(''));
                count++;
            }
            // Type conversion: http://www.jibbering.com/faq/faq_notes/type_convert.html#tcNumber
            numeric_value = (+value);
            if (numeric_value > value_high) {
                value_high = numeric_value;
                represent_high = represent;
            }
        });

        if (has_dummy) {
            dummy.val(represent_high);
            selector.val(value_high).change();
        }
        var i;
        if (dropdown) {
            // We have been called next to a drop-down
            if (inline) {
                // Update all related selectors with new options list
                var all_selects = ['_0', '_none', '_default'], suffix;
                var selector_prefix = caller.split('_').slice(0, -1).join('_');
                for (i=0; i < all_selects.length; i++) {
                    suffix = all_selects[i];
                    var s = self.parent.$('#' + selector_prefix + suffix);
                    s.empty().append(append.join(''));
                }
            } else {
                // @ToDo: Read existing values for a multi-select
                // Clean up the caller
                options.remove();
                selector.append(append.join('')).val(value_high).change();
            }
            // Select the value we just added
            selector.val(value_high).change();
        } else if (checkboxes) {
            // We have been called next to a CheckboxesWidgetS3
            // Read the current value(s)
            var values = [];
            self.parent.$('#' + caller + ' input').each(function(index) {
                if ( $(this).prop('checked') ) {
                    values.push($(this).val());
                }
            });
            var output = [];
            count = 0;
            for ( i = 0; i < append.length; i++ ) {
                if (count === 0) {
                    // Start the row
                    output.push('<tr>');
                    // Add a cell
                    output.push(append[i]);
                    count++;
                } else if ( count == (cols - 1) ) {
                    // Add a cell
                    output.push(append[i]);
                    // End the row
                    output.push('</tr>');
                    // Restart next time
                    count = 0;
                } else {
                    // Add a cell
                    output.push(append[i]);
                    count++;
                }
            }
            selector.html(output.join(''));
            // Select the value we just added
            values.push(value_high);
            //selector.val(values).change();
            for ( i = 0; i < values.length; i++ ) {
                self.parent.$('#' + caller + ' input[value="' + values[i] + '"]').prop('checked', true);
            }
        }

        // IE6 needs time for DOM to settle: http://csharperimage.jeremylikness.com/2009/05/jquery-ie6-and-could-not-set-selected.html
        //setTimeout( function() {
                // Set the newly-created value (one with highest value)
        //        selector.val(value_high).change();
        //    }, 1);

        // Clean-up
        self.parent.s3_popup_remove();
    });
}

// Function to get the URL parameters
function getQueryParams(qs) {
    // We want all the vars, i.e. after the ?
    qs = qs.split('?')[1];
    var pairs = qs.split('&');
    var params = {};
    var check = [];
    for (var i=0; i < pairs.length; i++) {
        check = pairs[i].split('=');
        params[decodeURIComponent(check[0])] = decodeURIComponent(check[1]);
    }
    return params;
}