/**
 * JS to handle Colorbox popups
 * moved from views/layout_popup.html
 */

function s3_tb_call_cleanup(caller) {
    if (self.parent.s3_tb_cleanup) {
        // Cleanup the parent
        self.parent.s3_tb_cleanup(caller);
    }
    self.parent.s3_tb_remove();
}

function s3_tb_refresh() {
    // The Get parameters
    var $_GET = getQueryParams(document.location.search);

    var level = $_GET['level'];
    if (typeof level === 'undefined') {
        // pass
    } else {
        // Location Selector
        s3_tb_call_cleanup(level);
        return;
    }

    var caller = $_GET['caller'];
    s3_debug('caller', caller);

    var person_id = $_GET['person_id'];
    if (typeof person_id === 'undefined') {
        // pass
    } else {
        // Person Selector
        if (typeof caller === 'undefined') {
            // pass
        } else {
            var field = self.parent.$('#' + caller);
            field.val(person_id).change();
        }
        s3_tb_call_cleanup(person_id);
        return;
    }

    var re = new RegExp('.*\\' + S3.Ap + '\\/');

    var child = $_GET['child'];
    if (typeof child === 'undefined') {
        // Use default
        var url = new String(self.location);
        var rel_url = url.replace(re, '');
        var args = rel_url.split('?')[0].split('/');
        var request_function = args[1]
        var child_resource = request_function + '_id';
    } else {
        // Use manual override
        var child_resource = child;
    }
    s3_debug('child_resource', child_resource);
    var selector;
    if ( child_resource == 'item_id' ) {
        selector = self.parent.$('#supply_catalog_item_item_id');
        if ( selector != undefined) {
            // S3SearchAutocompleteWidget
            //caller = 'supply_catalog_item_item_id';
        }
    }

    // @ToDo: Make this less fragile by passing these fields as separate vars?
    var parent_field = caller.replace('_' + child_resource, '');
    s3_debug('parent_field', parent_field);
    var parent_module = parent_field.replace(/_.*/, '');

    // Find the parent resource (fixed for components)
    var parent_resource = parent_field.replace(parent_module + '_', '');
    var parent_url = new String(self.parent.location);
    var rel_url = parent_url.replace(re, '');
    var args = rel_url.split('?')[0].split('/');
    var parent_component = null;
    var caller_prefix = args[0]
    var parent_function = args[1]
    if (args.length > 2) {
        if (args[2].match(/\d*/) != null) {
            if (args.length > 3) {
                parent_component = args[3];
            }
        } else {
            parent_component = args[2];
        }
    }
    if ((parent_component != null) && (parent_resource != parent_function) && (parent_resource == parent_component)) {
        parent_resource = parent_function + '/' + parent_component;
    }

    // URL to retrieve the Options list for the field of the master resource
    var url = S3.Ap.concat('/' + caller_prefix + '/' + parent_resource + '/options.s3json?field=' + child_resource);
    if ( selector === undefined ) {
        var selector = self.parent.$('#' + caller);
        var dummy = self.parent.$('#dummy_' + caller);
        var has_dummy = (dummy.val() != undefined);
        var options = self.parent.$('#' + caller + ' >option')
        var dropdown = options.length
    } else {
        // S3SearchAutocompleteWidget
        var dummy = self.parent.$('input[name="item_id_search_simple_simple"]');
        var has_dummy = (dummy.val() != undefined);
        s3_debug('has_dummy', has_dummy);
        var dropdown;
    }
    if (dropdown) {
        var append = [];
    } else {
        // Return only current record if field is autocomplete
        url += '&only_last=1';
    }
    var value_high = 1;
    var represent_high = '';
    $.getJSONS3(url, function (data) {
        var value, represent;
        $.each(data['option'], function() {
            value = this['@value'];
            represent = this['$'];
            if (typeof represent === 'undefined') {
                represent = '';
            }
            if (dropdown) {
                append.push(["<option value='", value, "'>", represent, "</option>"].join(''));
            }
            // Type conversion: http://www.jibbering.com/faq/faq_notes/type_convert.html#tcNumber
            numeric_value = (+value)
            if (numeric_value > value_high) {
                value_high = numeric_value;
                represent_high = represent;
            }
        });
        if (has_dummy) {
            dummy.val(represent_high);
            selector.val(value_high).change();
        }
        if (dropdown) {
            // We have been called next to a drop-down
            // Clean up the caller
            options.remove();
            selector.append(append.join('')).change();
        }

        // IE6 needs time for DOM to settle: http://csharperimage.jeremylikness.com/2009/05/jquery-ie6-and-could-not-set-selected.html
        //setTimeout( function() {
                // Set the newly-created value (one with highest value)
        //        selector.val(value_high).change();
        //    }, 1);

        // Clean-up
        s3_tb_call_cleanup(caller);
    });
}

// Function to get the URL parameters
function getQueryParams(qs) {
    // We want all the vars, i.e. after the ?
    qs = qs.split('?')[1]
    var pairs = qs.split('&');
    var params = {};
    var check = [];
    for( var i = 0; i < pairs.length; i++ ) {
            check = pairs[i].split('=');
            params[decodeURIComponent(check[0])] = decodeURIComponent(check[1]);
        }
    return params;
}