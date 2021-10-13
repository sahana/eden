/**
 * Function to refresh the caller of a popup (e.g. the parent form),
 * usually called via layout_popup.html, which itself is rendered by
 * layout.html if r.representation=="popup" and response.confirmation
 * (i.e. successful form submission from a popup).
 *
 * @param {object} popupData - data passed back from form submission
 *                             via response.s3.popup_data, this can
 *                             help to avoid having to Ajax-load them ;)
 */
function s3_popup_refresh_caller(popupData) {

    'use strict';

    // The GET vars (=URL query parameters)
    var $_GET = getQueryParams(document.location.search),
        parentWindow = window.parent,
        callerWidget,
        i,
        j,
        jlen,
        layer,
        layerID,
        layers,
        len,
        map,
        mapID,
        maps,
        strategies,
        strategy;

    // Is this a modal that is to refresh a Widget?
    // => must specify ?refresh=widget_id in the popup-URL, and for
    //    datalists (optionally) &record_id=record_id in order to just
    //    refresh a single record
    var refresh = $_GET.refresh;

    if (undefined !== refresh) {
        if (! isNaN(parseInt(refresh))) {
            parentWindow.location.reload(true);
        }
        // Update Widget
        callerWidget = parentWindow.$('#' + refresh);
        if (callerWidget.hasClass('dl')) {
            // Refresh dataList
            var record = $_GET.record;
            if (record !== undefined) {
                // reload a single item
                callerWidget.datalist('ajaxReloadItem', record);
            } else {
                // reload the whole list
                callerWidget.datalist('ajaxReload');
            }
        } else if (callerWidget.hasClass('s3-organizer')) {
            try {
                callerWidget.organizer('reload');
            } catch(e) {}
        } else if (callerWidget.children('div').hasClass('s3-hierarchy-tree')) {
            try {
                callerWidget.hierarchicalcrud('reload');
            } catch(e) {}
        } else {
            // Refresh dataTable
            try {
                callerWidget.dataTable().fnReloadAjax();
            } catch(e) {}
        }
        // Update the layer on the Maps (if appropriate)
        maps = parentWindow.S3.gis.maps;
        if (typeof maps != 'undefined') {
            for (mapID in maps) {
                map = maps[mapID];
                layerID = refresh.replace(/-/g, '_');
                layers = map.layers;
                for (i = 0, len = layers.length; i < len; i++) {
                    layer = layers[i];
                    if (layer.s3_layer_id == layerID) {
                        strategies = layer.strategies;
                        for (j = 0, jlen = strategies.length; j < jlen; j++) {
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

        // Notify all filter forms that target data have changed
        // and filter options may need to be updated accordingly
        parentWindow.$('.filter-form').trigger('dataChanged', refresh);

        // Remove popup
        parentWindow.S3.popup_remove();
        return;
    }

    // Is this a Map popup? (e.g. PoI entry)
    layerID = $_GET.refresh_layer;
    if (typeof layerID != 'undefined') {
        maps = parentWindow.S3.gis.maps;
        if (typeof maps != 'undefined') {
            if (layerID != 'undefined') {
                layerID = parseInt(layerID);
            }
            var draftLayerName = parentWindow.i18n.gis_draft_layer;
            for (mapID in maps) {
                map = maps[mapID];
                layers = map.layers;
                for (i = 0, len = layers.length; i < len; i++) {
                    layer = layers[i];
                    if (layer.s3_layer_id == layerID) {
                        // Refresh this layer
                        strategies = layer.strategies;
                        for (j = 0, jlen = strategies.length; j < jlen; j++) {
                            strategy = strategies[j];
                            if (strategy.CLASS_NAME == 'OpenLayers.Strategy.Refresh') {
                                // Reload the layer
                                strategy.refresh();
                                break;
                            }
                        }
                    } else if (layer.name == draftLayerName) {
                        /* Close ALL popups */
                        while (map.popups.length) {
                            map.removePopup(map.popups[0]);
                        }
                        // Remove the Feature
                        var features = layer.features;
                        for (j = features.length - 1; j >= 0; j--) {
                            features[j].destroy();
                        }
                    }
                }
            }
        }
        return;
    }

    // Is this a popup to edit a node in hierarchical CRUD?
    var nodeID = $_GET.node;
    if (nodeID) {
        // Refresh the node in the hierarchy
        var hierarchy = parentWindow.$('#' + $_GET.hierarchy),
            node = parentWindow.$('#' + nodeID);
        if (hierarchy && node) {
            hierarchy.hierarchicalcrud('refreshNode', node);
        }
        // Remove the dialog
        parentWindow.S3.popup_remove();
        return;
    }

    // Is this a dashboard widget configuration dialog?
    var agent = $_GET.agent;
    if (typeof agent != 'undefined') {

        var data;
        if (typeof popupData != 'undefined') {
            data = [popupData];
        } else {
            data = [];
        }

        // Inform the agent that it's done (agent will remove the dialog)
        parentWindow.$('#' + agent).trigger('configSaved', data);
        return;
    }

    // Location selector?
    var level = $_GET.level;
    if (typeof level != 'undefined') {
        parentWindow.S3.popup_remove();
        return;
    }

    // Modal opened from a form (e.g. S3PopupLink, PersonSelector)?
    // => update the respective form field (=the caller)

    var caller = $_GET.caller;
    if (caller === undefined) {
        // All code after this is there to update the caller, so pointless
        // to continue beyond this point without it.
        s3_debug('Neither calling element nor refresh-target specified in popup URL!');
        parentWindow.S3.popup_remove();
        return;
    } else {
        s3_debug('Caller', caller);
    }

    var personID = $_GET.person_id;
    if (typeof personID != 'undefined') {
        // Person Selector
        var field = parentWindow.$('#' + caller);
        field.val(personID).change();
        parentWindow.S3.popup_remove();
        return;
    }

    var args,
        child = $_GET.child,
        childResource,
        lookupPrefix = $_GET.prefix,
        optionsVar = $_GET.optionsVar,
        optionsValue = $_GET.optionsValue,
        parent = $_GET.parent,
        parentURL = '' + parentWindow.location,
        parentResource,
        re = new RegExp('.*\\' + S3.Ap + '\\/'),
        relativeURL;

    if (typeof child === 'undefined') {
        // Use default
        var url = '' + window.location;
        relativeURL = url.replace(re, '');
        args = relativeURL.split('?')[0].split('/');
        var requestFunction = args[1].split(".")[0];
        childResource = requestFunction + '_id';
    } else {
        // Use manual override
        childResource = child;
    }
    s3_debug('childResource', childResource);

    relativeURL = parentURL.replace(re, '');

    if (typeof parent === 'undefined') {
        // @ToDo: Make this less fragile by passing these fields as separate vars?
        var parentField = caller.replace('_' + childResource, '');
        s3_debug('parentField', parentField);

        var parentModule = parentField.replace(/_.*/, '');

        // Find the parent resource (fixed for components)
        parentResource = parentField.replace(parentModule + '_', '');

        args = relativeURL.split('?')[0].split('/');
        var parentComponent = null;
        if (!lookupPrefix) {
            lookupPrefix = args[0];
        }
        var parentFunction = args[1];
        if (args.length > 2) {
            if (args[2].match(/\d*/) !== null) {
                if (args.length > 3) {
                    parentComponent = args[3];
                }
            } else {
                parentComponent = args[2];
            }
        }
        if ((parentComponent !== null) && (parentResource != parentFunction) && (parentResource == parentComponent)) {
            parentResource = parentFunction + '/' + parentComponent;
        }
    } else {
        // Use manual override
        parentResource = parent;
        if (!lookupPrefix) {
            relativeURL = parentURL.replace(re, '');
            args = relativeURL.split('?')[0].split('/');
            lookupPrefix = args[0];
        }
    }
    s3_debug('parentResource', parentResource);
    s3_debug('lookupPrefix', lookupPrefix);
    s3_debug('optionsVar', optionsVar);
    s3_debug('optionsValue', optionsValue);

    // URL to retrieve the Options list for the field of the master resource
    var optionsURL = S3.Ap.concat('/' + lookupPrefix + '/' + parentResource + '/options.s3json?field=' + childResource)
    if (typeof optionsVar !== 'undefined' && typeof optionsValue !== 'undefined') {
        optionsURL += '&' + optionsVar + '=' + optionsValue;
    }

    // Identify the widget type (Dropdown, Checkboxes, Hierarchy or Autocomplete)
    callerWidget = parentWindow.$('#' + caller);
    s3_debug('callerWidget', callerWidget);

    var inline = (caller.substring(0, 4) == 'sub_'),
        dummy = parentWindow.$('#dummy_' + caller),
        hasDummy = (undefined !== dummy.val());
    s3_debug('hasDummy', hasDummy);

    var checkboxes = callerWidget.hasClass('checkboxes-widget-s3'),
        isHierarchyWidget = callerWidget.hasClass('s3-hierarchy-input'),
        append,
        cols,
        options,
        isDropdown;

    if (checkboxes) {
        // The number of columns
        cols = parentWindow.$('#' + caller + ' tbody tr:first').children().length;
        append = [];
    } else {
        options = parentWindow.$('#' + caller + ' >option');
        isDropdown = callerWidget.prop('tagName').toLowerCase() == 'select';
        /* S3SearchAutocompleteWidget should do something like this instead */
        //var dummy = parentWindow.$('input[name="item_id_search_simple_simple"]');
        //var hasDummy = (dummy.val() != undefined);
        if (isDropdown) {
            append = [];
        } else if (isHierarchyWidget) {
            // Request hierarchy information for widget
            // @ToDo: This is a potential race condition
            optionsURL += '&hierarchy=1&only_last=1';
        } else {
            // Return only latest record for autocomplete field
            // @ToDo: This is a potential race condition
            optionsURL += '&only_last=1';
        }
    }

    var lastOptionValue = 1,
        lastOptionRepr = '';

    $.getJSONS3(optionsURL, function (data) {

        var count = 0,
            newOptions = data.option;

        if (!newOptions || !newOptions.length) {
            s3_debug('No options available to refresh parent field');
            parentWindow.S3.popup_remove();
            return;
        }

        newOptions.forEach(function(option) {

            var value = option['@value'],
                represent = option.$;

            if (undefined === represent) {
                represent = '';
            }
            if (isDropdown) {
                // Add new option
                append.push(["<option value='", value, "'>", represent, "</option>"].join(''));
            } else if (checkboxes) {
                var id = 'id_' + childResource + '-' + count;
                append.push(["<td><input id='", id, "' name='", childResource, "' value='", value, "' type='checkbox'><label for='", id, "'>", represent, "</label></td>"].join(''));
                count++;
            } else if (isHierarchyWidget) {
                // Add new node
                parent = option['@parent'];
                callerWidget.parent().hierarchicalopts('addNode', parent, value, represent, true);
            }
            // Type conversion: http://www.jibbering.com/faq/faq_notes/type_convert.html#tcNumber
            var numericValue = (+value);
            if (!isNaN(numericValue) && numericValue > lastOptionValue) {
                lastOptionValue = numericValue;
                lastOptionRepr = represent;
            }
        });

        if (hasDummy) {
            dummy.val(lastOptionRepr);
            callerWidget.val(lastOptionValue).change();
        }

        var i;
        if (isDropdown) {
            // We have been called next to a drop-down
            if (inline) {
                // Update all related selectors with new options list
                var allSelects = ['_0', '_none', '_default'], suffix,
                    callerPrefix = caller.split('_').slice(0, -1).join('_');
                for (i = 0; i < allSelects.length; i++) {
                    suffix = allSelects[i];
                    var s = parentWindow.$('#' + callerPrefix + suffix);
                    s.empty().append(append.join(''));
                }
            } else {
                // @ToDo: Read existing values for a multi-select
                // Clean up the caller
                options.remove();
                callerWidget.append(append.join('')).val(lastOptionValue).change();
            }
            // Select the value we just added
            callerWidget.val(lastOptionValue).change();
            // Ensure Input not disabled
            callerWidget.prop('disabled', false);
            // Refresh MultiSelect if present
            if (callerWidget.hasClass('multiselect-widget') &&
                callerWidget.multiselect('instance')) {
                try {
                    callerWidget.multiselect('refresh');
                } catch(e) {
                    // MultiSelect not present
                }
            }
        } else if (checkboxes) {
            // We have been called next to a CheckboxesWidgetS3
            // Read the current value(s)
            var values = [];
            parentWindow.$('#' + caller + ' input').each(function() {
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
            callerWidget.html(output.join(''));
            // Select the value we just added
            values.push(lastOptionValue);
            //callerWidget.val(values).change();
            for (i = 0; i < values.length; i++) {
                parentWindow.$('#' + caller + ' input[value="' + values[i] + '"]').prop('checked', true);
            }
        }

        // Clean-up
        parentWindow.S3.popup_remove();
    });
}

/**
 * Function to get the URL query parameters
 *
 * @param {string} qs - the query string (e.g. document.location.search)
 */
function getQueryParams(qs) {

    // Remove the leading '?'
    qs = qs.substring(1);

    var params = {};
    if (qs) {
        var pairs = qs.split('&'),
            pair = [];
        for (var i = 0, len = pairs.length; i < len; i++) {
            pair = pairs[i].split('=');
            params[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1]);
        }
    }
    return params;
}
