/**
 * JS to handle Popup Modal forms to create new resources
 */

function s3_popup_refresh_main_form() {
    // The GET parameters
    var $_GET = getQueryParams(document.location.search);

    // Is this a modal that is to refresh a datatable/datalist/map?
    // => must specify ?refresh=list_id in the popup-URL, and for
    //    datalists (optionally) &record_id=record_id in order to just
    //    refresh this one record
    var refresh = $_GET['refresh'];
    if (typeof refresh != 'undefined') {
        // Update DataList/DataTable (if appropriate)
        var selector = self.parent.$('#' + refresh);
        if (selector.hasClass('dl')) {
            // Refresh dataList
            var record = $_GET['record'];
            if (record !== undefined) {
                // reload a single item
                selector.datalist('ajaxReloadItem', record)
            } else {
                // reload the whole list
                selector.datalist('ajaxReload');
            }
        } else {
            // Refresh dataTable
            try {
                selector.dataTable().reloadAjax();
            } catch(e) {}
        }
        // Update the layer on the Maps (if appropriate)
        var maps = self.parent.S3.gis.maps
        if (typeof maps != 'undefined') {
            var map_id, map, layer_id, layers, i, len, layer, strategies, j, jlen, strategy;
            for (map_id in maps) {
                map = maps[map_id];
                layer_id = refresh.replace(/-/g, '_');
                layers = map.layers;
                for (i=0, len=layers.length; i < len; i++) {
                    layer = layers[i];
                    if (layer.s3_layer_id == layer_id) {
                        strategies = layer.strategies;
                        for (j=0, jlen=strategies.length; j < jlen; j++) {
                            strategy = strategies[j];
                            if (strategy.CLASS_NAME == 'OpenLayers.Strategy.Refresh') {
                                // Reload the layer
                                strategy.refresh();
                                break;
                            }
                        }
                        break;
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
        self.parent.S3.popup_remove();
        return;
    }

    // Is this a Map popup? (e.g. PoI entry)
    var layer_id = $_GET['refresh_layer'];
    if (typeof layer_id != 'undefined') {
        var maps = self.parent.S3.gis.maps
        if (typeof maps != 'undefined') {
            var map_id, map, layers, i, len, layer, found, strategies, j, jlen, strategy;
            if (layer_id != 'undefined') {
                layer_id = parseInt(layer_id);
            }
            var gis_draft_layer = self.parent.i18n.gis_draft_layer;
            for (map_id in maps) {
                map = maps[map_id];
                layers = map.layers;
                for (i=0, len=layers.length; i < len; i++) {
                    layer = layers[i];
                    if (layer.s3_layer_id == layer_id) {
                        // Refresh this layer
                        strategies = layer.strategies;
                        for (j=0, jlen=strategies.length; j < jlen; j++) {
                            strategy = strategies[j];
                            if (strategy.CLASS_NAME == 'OpenLayers.Strategy.Refresh') {
                                // Reload the layer
                                strategy.refresh();
                                break;
                            }
                        }
                    } else if (layer.name == gis_draft_layer) {
                        /* Close ALL popups */
                        while (map.popups.length) {
                            map.removePopup(map.popups[0]);
                        }
                        // Remove the Feature
                        var features = layer.features;
                        for (j=features.length - 1; j >= 0; j--) {
                            features[j].destroy();
                        }
                    }
                }
            }
        }
        return;
    }

    var node_id = $_GET['node'];
    if (node_id) {
        var hierarchy = self.parent.$('#' + $_GET['hierarchy']),
            node = self.parent.$('#' + node_id);
        if (hierarchy && node) {
            hierarchy.hierarchicalcrud('refreshNode', node);
        }
        self.parent.S3.popup_remove();
        return;
    }

    // Modal opened from a form (e.g. S3AddResourceLink)?
    // => update the respective form field (=the caller)

    var level = $_GET['level'];
    if (typeof level != 'undefined') {
        // Location Selector
        self.parent.S3.popup_remove();
        return;
    }

    var caller = $_GET['caller'];
    if (caller === undefined) {
        // All code after this is there to update the caller, so pointless
        // to continue beyond this point without it.
        s3_debug('Neither calling element nor refresh-target specified in popup URL!');
        self.parent.S3.popup_remove();
        return;
    } else {
        s3_debug('Caller: ', caller);
    }

    var person_id = $_GET['person_id'];
    if (typeof person_id != 'undefined') {
        // Person Selector
        var field = self.parent.$('#' + caller);
        field.val(person_id).change();
        self.parent.S3.popup_remove();
        return;
    }

    var re = new RegExp('.*\\' + S3.Ap + '\\/'),
        child = $_GET['child'],
        rel_url,
        args,
        child_resource;

    if (typeof child === 'undefined') {
        // Use default
        var url = new String(self.location);
        rel_url = url.replace(re, '');
        args = rel_url.split('?')[0].split('/');
        var request_function = args[1].split(".")[0];
        child_resource = request_function + '_id';
    } else {
        // Use manual override
        child_resource = child;
    }
    s3_debug('child_resource', child_resource);

    var parent = $_GET['parent'],
        parent_url = new String(self.parent.location),
        parent_resource,
        lookup_prefix = $_GET['prefix'];

    rel_url = parent_url.replace(re, '');

    if (typeof parent === 'undefined') {
        // @ToDo: Make this less fragile by passing these fields as separate vars?
        var parent_field = caller.replace('_' + child_resource, '');
        s3_debug('parent_field', parent_field);

        var parent_module = parent_field.replace(/_.*/, '');

        // Find the parent resource (fixed for components)
        parent_resource = parent_field.replace(parent_module + '_', '');

        args = rel_url.split('?')[0].split('/');
        var parent_component = null;
        if (!lookup_prefix) {
            lookup_prefix = args[0];
        }
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
        if (!lookup_prefix) {
            rel_url = parent_url.replace(re, '');
            args = rel_url.split('?')[0].split('/');
            lookup_prefix = args[0];
        }
    }
    s3_debug('parent_resource', parent_resource);
    s3_debug('lookup_prefix', lookup_prefix);

    // URL to retrieve the Options list for the field of the master resource
    var opt_url = S3.Ap.concat('/' + lookup_prefix + '/' + parent_resource + '/options.s3json?field=' + child_resource);

    // Identify the widget type (Dropdown, Checkboxes, Hierarchy or Autocomplete)
    var selector = self.parent.$('#' + caller);
    s3_debug('selector', selector);
    var inline = (caller.substring(0, 4) == 'sub_');
    var dummy = self.parent.$('#dummy_' + caller);
    var has_dummy = (dummy.val() != undefined);
    s3_debug('has_dummy', has_dummy);
    var checkboxes = selector.hasClass('checkboxes-widget-s3');
    var hierarchy_widget = selector.hasClass('s3-hierarchy-input');

    var append;
    if (checkboxes) {
        // The number of columns
        var cols = self.parent.$('#' + caller + ' tbody tr:first').children().length;
        append = [];
    } else {
        var options = self.parent.$('#' + caller + ' >option');
        var dropdown = selector.prop('tagName').toLowerCase() == 'select';
        /* S3SearchAutocompleteWidget should do something like this instead */
        //var dummy = self.parent.$('input[name="item_id_search_simple_simple"]');
        //var has_dummy = (dummy.val() != undefined);
        if (dropdown) {
            append = [];
        } else if (hierarchy_widget) {
            // Request hierarchy information for widget
            opt_url += '&hierarchy=1&only_last=1';
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
                // Add new option
                append.push(["<option value='", value, "'>", represent, "</option>"].join(''));
            } else if (checkboxes) {
                id = 'id_' + child_resource + '-' + count;
                append.push(["<td><input id='", id, "' name='", child_resource, "' value='", value, "' type='checkbox'><label for='", id, "'>", represent, "</label></td>"].join(''));
                count++;
            } else if (hierarchy_widget) {
                // Add new node
                parent = this['@parent'];
                selector.parent().hierarchicalopts('addNode', parent, value, represent, true);
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
            // Ensure Input not disabled
            selector.prop('disabled', false);
            // Refresh MultiSelect if present
            if (selector.hasClass('multiselect-widget') &&
                selector.multiselect('instance')) {
                try {
                    selector.multiselect('refresh');
                } catch(e) {
                    // MultiSelect not present
                }
            }
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
            for (i = 0; i < append.length; i++) {
                if (count === 0) {
                    // Start the row
                    output.push('<tr>');
                    // Add a cell
                    output.push(append[i]);
                    count++;
                } else if (count == (cols - 1)) {
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
            for (i = 0; i < values.length; i++) {
                self.parent.$('#' + caller + ' input[value="' + values[i] + '"]').prop('checked', true);
            }
        }

        // IE6 needs time for DOM to settle: http://csharperimage.jeremylikness.com/2009/05/jquery-ie6-and-could-not-set-selected.html
        //setTimeout( function() {
                // Set the newly-created value (one with highest value)
        //        selector.val(value_high).change();
        //    }, 1);

        // Clean-up
        self.parent.S3.popup_remove();
    });
}

// Function to get the URL parameters
function getQueryParams(qs) {
    // We want all the vars, i.e. after the ?
    var params = {};
    qs = qs.substring(1);
    if (qs) {
        var pairs = qs.split('&');
        var check = [];
        for (var i=0; i < pairs.length; i++) {
            check = pairs[i].split('=');
            params[decodeURIComponent(check[0])] = decodeURIComponent(check[1]);
        }
    }
    return params;
}
