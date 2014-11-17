/**
 * Used by the S3LocationSelectorWidget2 (modules/s3/s3widgets.py)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 *
 * Globals
 *  Location Hierachy
 *  l = {id : {'n' : name,
 *             'l' : level,
 *             'f' : parent
 *             }}
 *  n = same but temporary for new content retrieved from /gis/ldata
 *  hdata = Labels Hierarchy (@ToDo)
 */

// Module pattern to hide internal vars
(function() {

    /**
     * Instantiate a LocationSelector
     * - in global scope as called from outside
     *
     * Parameters:
     * fieldname - {String} A unique fieldname for a location_id field
     * hide_lx - {Boolean} Whether to hide lower Lx fields until higher level selected
     * reverse_lx - {Boolean} Whether to show Lx fields in the order usually used by Street Addresses
     * L0 - {Integer} gis_location.id of the L0
     * L1 - {Integer} gis_location.id of the L1
     * L2 - {Integer} gis_location.id of the L2
     * L3 - {Integer} gis_location.id of the L3
     * L4 - {Integer} gis_location.id of the L4
     * L5 - {Integer} gis_location.id of the L5
     * specific - {Integer} gis_location.id of the specific location
     */
    S3.gis.locationselector = function(fieldname, hide_lx, reverse_lx, L0, L1, L2, L3, L4, L5, specific) {
        // Function to be called by S3LocationSelectorWidget2

        var selector = '#' + fieldname;
        var real_input = $(selector);
        var real_row = $(selector + '__row');

        var error_row = real_input.next('.error_wrapper');
        var L0_row = $(selector + '_L0__row');
        var map_icon_row = $(selector + '_map_icon__row');
        var map_div = $(selector + '_map_icon__row .map_wrapper').attr('id', fieldname + '_map_wrapper');
        var div_style = real_row.hasClass('control-group') // Bootstrap
                        || real_row.hasClass('form-row'); // Foundation
        if (div_style) {
            // Move the user-visible rows underneath the real (hidden) one
            var L1_row = $(selector + '_L1__row');
            var L2_row = $(selector + '_L2__row');
            var L3_row = $(selector + '_L3__row');
            var L4_row = $(selector + '_L4__row');
            var L5_row = $(selector + '_L5__row');
            var address_row = $(selector + '_address__row');
            var postcode_row = $(selector + '_postcode__row');
            if (reverse_lx) {
                real_row.hide()
                        .after(map_div)
                        .after(map_icon_row)
                        .after(L0_row)
                        .after(L1_row)
                        .after(L2_row)
                        .after(L3_row)
                        .after(L4_row)
                        .after(L5_row)
                        .after(postcode_row)
                        .after(address_row)
                        .after(error_row);
            } else {
                real_row.hide()
                        .after(map_div)
                        .after(map_icon_row)
                        .after(postcode_row)
                        .after(address_row)
                        .after(L5_row)
                        .after(L4_row)
                        .after(L3_row)
                        .after(L2_row)
                        .after(L1_row)
                        .after(L0_row)
                        .after(error_row);
            }
        } else {
            // Hide the main row & move out the Error
            $(selector + '__row1').hide(); // Tuple themes
            real_row.hide()
                    .after(error_row);
            if (reverse_lx) {
                L0_row.after(map_div)
                      .after(map_icon_row);
            } else {
                $(selector + '_postcode__row').after(map_div)
                                              .after(map_icon_row);
            }
        }

        if (specific) {
            // Store this to retrieve later
            real_input.data('specific', specific);
        }

        // Store whether we hide_lx
        real_input.data('hide_lx', hide_lx);

        var lat = $(selector + '_lat').val();
        var lon = $(selector + '_lon').val();
        var wkt = $(selector + '_wkt').val();
        if (lat || lon || wkt) {
            // Don't do a Geocode when reading the data
            real_input.data('manually_geocoded', true);
        }

        // Initial population of dropdown(s)
        var L0_select = $(selector + '_L0');
        if (L0_row.length) {
            // Populate with values
            var values = [];
            for (var i in l) {
                v = l[i];
                if (v['l'] == 0) {
                    v['i'] = i;
                    values.push(v);
                }
            }
            values.sort(nameSort);
            var _id, location, option, selected;
            for (var i=0, len=values.length; i < len; i++) {
                location = values[i];
                _id = location['i'];
                option = '<option value="' + _id + '">' + location['n'] + '</option>';
                L0_select.append(option);
            }
            // Show the Country row
            L0_row.removeClass('hide').show();
            if (!div_style) {
                $(selector + '_L0__row1').removeClass('hide').show(); // Tuple themes
            }
        }
        if (L0) {
            lx_select(fieldname, 0, L0);
        }
        if (L1 || L2) { // || is to support Missing levels
            lx_select(fieldname, 1, L1 || L2);
        }
        if (L2 || L3) {
            lx_select(fieldname, 2, L2 || L3);
        }
        if (L3 || L4) {
            lx_select(fieldname, 3, L3 || L4);
        }
        if (L4 || L5) {
            lx_select(fieldname, 4, L4 || L5);
        }
        if (L5) {
            lx_select(fieldname, 5, L5);
        }

        // Show Address/Postcode Rows
        showAddress(fieldname);

        // Show Map icon
        map_icon_row.removeClass('hide').show();

        if (lat || lon || wkt) {
            showMap(fieldname);
        } else {
            $(selector + '_map_icon').click(function() {
                showMap(fieldname);
                return false;
            });
        }

        // Listen events
        L0_select.change(function() {
            lx_select(fieldname, 0);
        });
        var L1_select = $(selector + '_L1');
        L1_select.change(function() {
            lx_select(fieldname, 1);
        });
        var L2_select = $(selector + '_L2');
        L2_select.change(function() {
            lx_select(fieldname, 2);
        });
        var L3_select = $(selector + '_L3');
        L3_select.change(function() {
            lx_select(fieldname, 3);
        });
        var L4_select = $(selector + '_L4');
        L4_select.change(function() {
            lx_select(fieldname, 4);
        });
        var L5_select = $(selector + '_L5');
        L5_select.change(function() {
            lx_select(fieldname, 5);
        });
        var addressFields = $(selector + '_address' + ',' + selector + '_postcode');
        addressFields.change(function() {
            resetHidden(fieldname);
        });

        // Form submission
        real_input.closest('form').submit(function() {
            // Client-side validation
            if ((fieldname.slice(0, 4) == 'sub_') && (real_input.parent().parent().is(':hidden'))) {
                // This is an Inline version which is hidden
                // Disable the form fields to avoid conflicts
                $(selector + '_L0,' + selector + '_L1,' + selector + '_L2,' + selector + '_L3,' + selector + '_L4,' + selector + '_L5,' + selector + '_address,' + selector + '_lat,' + selector + '_lon,' + selector + '_parent,' + selector + '_postcode,' + selector + '_wkt').prop('disabled', true);
                // Ignore validation errors
                return true;
            }
            // Do we have a value to submit?
            var current_value = real_input.val();
            if (current_value) {
                if (!l[current_value]) {
                    // Must be a specific location => OK
                    // Normal Submit
                    return true;
                }
                var current_level = l[current_value].l;
                // Is a higher-level required? If so, then prevent submission
                // Is the value for a hidden, optional field? If so, then blank it, as it must be an optional default
                switch(current_level) {
                    case 0:
                        if ($(selector + '_address').hasClass('required')) {
                            S3.fieldError(selector + '_address', i18n.enter_value);
                            // Prevent Submit
                            return false;
                        } else if (L5_select.hasClass('required')) {
                            S3.fieldError(selector + '_L5', i18n.enter_value);
                            // Prevent Submit
                            return false;
                        } else if (L4_select.hasClass('required')) {
                            S3.fieldError(selector + '_L4', i18n.enter_value);
                            // Prevent Submit
                            return false;
                        } else if (L3_select.hasClass('required')) {
                            S3.fieldError(selector + '_L3', i18n.enter_value);
                            // Prevent Submit
                            return false;
                        } else if (L2_select.hasClass('required')) {
                            S3.fieldError(selector + '_L2', i18n.enter_value);
                            // Prevent Submit
                            return false;
                        } else if (L1_select.hasClass('required')) {
                            S3.fieldError(selector + '_L1', i18n.enter_value);
                            // Prevent Submit
                            return false;
                        } else {
                            var hidden_L0 = $('input#' + fieldname + '_L0');
                            if (hidden_L0.length && !hidden_L0.hasClass('required')) {
                                // Return NULL
                                real_input.val('');
                            }
                            // Normal Submit
                            return true;
                        }
                    case 1:
                        if ($(selector + '_address').hasClass('required')) {
                            S3.fieldError(selector + '_address', i18n.enter_value);
                            // Prevent Submit
                            return false;
                        } else if (L5_select.hasClass('required')) {
                            S3.fieldError(selector + '_L5', i18n.enter_value);
                            // Prevent Submit
                            return false;
                        } else if (L4_select.hasClass('required')) {
                            S3.fieldError(selector + '_L4', i18n.enter_value);
                            // Prevent Submit
                            return false;
                        } else if (L3_select.hasClass('required')) {
                            S3.fieldError(selector + '_L3', i18n.enter_value);
                            // Prevent Submit
                            return false;
                        } else if (L2_select.hasClass('required')) {
                            S3.fieldError(selector + '_L2', i18n.enter_value);
                            // Prevent Submit
                            return false;
                        } else {
                            var hidden_L1 = $('input#' + fieldname + '_L1');
                            if (hidden_L1.length && !hidden_L1.hasClass('required')) {
                                // Return NULL
                                real_input.val('');
                            }
                            // Normal Submit
                            return true;
                        }
                    case 2:
                        if ($(selector + '_address').hasClass('required')) {
                            S3.fieldError(selector + '_address', i18n.enter_value);
                            // Prevent Submit
                            return false;
                        } else if (L5_select.hasClass('required')) {
                            S3.fieldError(selector + '_L5', i18n.enter_value);
                            // Prevent Submit
                            return false;
                        } else if (L4_select.hasClass('required')) {
                            S3.fieldError(selector + '_L4', i18n.enter_value);
                            // Prevent Submit
                            return false;
                        } else if (L3_select.hasClass('required')) {
                            S3.fieldError(selector + '_L3', i18n.enter_value);
                            // Prevent Submit
                            return false;
                        } else {
                            var hidden_L2 = $('input#' + fieldname + '_L2');
                            if (hidden_L2.length && !hidden_L2.hasClass('required')) {
                                // Return NULL
                                real_input.val('');
                            }
                            // Normal Submit
                            return true;
                        }
                    case 3:
                        if ($(selector + '_address').hasClass('required')) {
                            S3.fieldError(selector + '_address', i18n.enter_value);
                            // Prevent Submit
                            return false;
                        } else if (L5_select.hasClass('required')) {
                            S3.fieldError(selector + '_L5', i18n.enter_value);
                            // Prevent Submit
                            return false;
                        } else if (L4_select.hasClass('required')) {
                            S3.fieldError(selector + '_L4', i18n.enter_value);
                            // Prevent Submit
                            return false;
                        } else {
                            var hidden_L3 = $('input#' + fieldname + '_L3');
                            if (hidden_L3.length && !hidden_L3.hasClass('required')) {
                                // Return NULL
                                real_input.val('');
                            }
                            // Normal Submit
                            return true;
                        }
                    case 4:
                        if ($(selector + '_address').hasClass('required')) {
                            S3.fieldError(selector + '_address', i18n.enter_value);
                            // Prevent Submit
                            return false;
                        } else if (L5_select.hasClass('required')) {
                            S3.fieldError(selector + '_L5', i18n.enter_value);
                            // Prevent Submit
                            return false;
                        } else {
                            var hidden_L4 = $('input#' + fieldname + '_L4');
                            if (hidden_L4.length && !hidden_L4.hasClass('required')) {
                                // Return NULL
                                real_input.val('');
                            }
                            // Normal Submit
                            return true;
                        }
                    case 5:
                        if ($(selector + '_address').hasClass('required')) {
                            S3.fieldError(selector + '_address', i18n.enter_value);
                            // Prevent Submit
                            return false;
                        } else {
                            var hidden_L5 = $('input#' + fieldname + '_L5');
                            if (hidden_L5.length && !hidden_L5.hasClass('required')) {
                                // Return NULL
                                real_input.val('');
                            }
                            // Normal Submit
                            return true;
                        }
                    default:
                        // Something has gone wrong! (e.g. str not int)
                        S3.showAlert('LocationSelector cannot validate!', 'error');
                        return false;
                }
            } else {
                // Do we have any required levels?
                // Report error at lowest-level
                if ($(selector + '_address').hasClass('required')) {
                    S3.fieldError(selector + '_address', i18n.enter_value);
                    // Prevent Submit
                    return false;
                } else if (L5_select.hasClass('required')) {
                    S3.fieldError(selector + '_L5', i18n.enter_value);
                    // Prevent Submit
                    return false;
                } else if (L4_select.hasClass('required')) {
                    S3.fieldError(selector + '_L4', i18n.enter_value);
                    // Prevent Submit
                    return false;
                } else if (L3_select.hasClass('required')) {
                    S3.fieldError(selector + '_L3', i18n.enter_value);
                    // Prevent Submit
                    return false;
                } else if (L2_select.hasClass('required')) {
                    S3.fieldError(selector + '_L2', i18n.enter_value);
                    // Prevent Submit
                    return false;
                } else if (L1_select.hasClass('required')) {
                    S3.fieldError(selector + '_L1', i18n.enter_value);
                    // Prevent Submit
                    return false;
                } else if (L0_select.hasClass('required')) {
                    S3.fieldError(selector + '_L0', i18n.enter_value);
                    // Prevent Submit
                    return false;
                } else {
                    // Normal Submit
                    return true;
                }
            }
        });
    }

    /**
     * A dropdown has been selected
     * - either manually or through an initial value
     */
    var lx_select = function(fieldname, level, id) {
        // Hierarchical dropdown has been selected

        var selector = '#' + fieldname;

        // Read options
        var real_input = $(selector);
        var hide_lx = real_input.data('hide_lx');

        if (id) {
            // Set this dropdown to this value
            // - this is being set from outside the dropdown, e.g. an update form or using a visible default location
            var dropdown = $(selector + '_L' + level);
            dropdown.val(id);
            if (dropdown.hasClass('multiselect')) {
                dropdown.multiselect('refresh');
            }
        } else {
            // Read the selected value from the dropdown
            id = parseInt($(selector + '_L' + level).val());
        }
        if (level === 0) {
            // Set Labels
            var hi = h[id];
            if (hi == undefined) {
                // Read the values from server
                var url = S3.Ap.concat('/gis/hdata/' + id);
                $.ajaxS3({
                    async: false,
                    url: url,
                    dataType: 'script',
                    success: function(data) {
                        // Copy the elements across
                        hi = {};
                        try {
                            for (var prop in n) {
                                hi[prop] = n[prop];
                            }
                            h[id] =  hi;
                            // Clear the memory
                            n = null;
                        } catch(e) {}
                    },
                    error: function(request, status, error) {
                        if (error == 'UNAUTHORIZED') {
                            msg = i18n.gis_requires_login;
                        } else {
                            msg = request.responseText;
                        }
                        s3_debug(msg);
                        // Revert state of widget to allow user to retry without reloading page
                        // - not necessary since this is just labels & we already have fallback
                        //S3.showAlert(msg, 'error');
                    }
                });
            }
            // Use default values as fallback if no value specified
            var d = h['d'];
            var i,
                lev,
                label,
                levels = ['1', '2', '3', '4', '5'],
                s;
            for (i=0; i < 5; i++) {
                lev = levels[i];
                label = hi[lev] || d[lev];
                s = selector + '_L' + lev;
                if ($(s).hasClass('required')) {
                    // @ToDo: Client-side s3_mark_required function
                    $(s + '__row label').html('<div>' + label + ':<span class="req"> *</span></div>');
                    $(s + '__row1 label').html('<div>' + label + ':<span class="req"> *</span></div>'); // Tuple themes
                } else {
                    $(s + '__row label').html(label + ':');
                    $(s + '__row1 label').html(label + ':'); // Tuple themes
                }
                $(s + ' option[value=""]').html(i18n.select + ' ' + label);
            }
        }
        if (id) {
            // Hide all lower levels
            // & remove their values
            var s;
            for (var lev=level + 1; lev < 6; lev++) {
                s = selector + '_L' + lev;
                if (hide_lx) {
                    $(s + '__row').hide();
                    $(s + '__row1').hide(); // Tuple themes
                } else {
                    // Hide the limited options
                    $(s + ' option').remove('[value != ""]');
                    // @ToDo: Read the full set of options via a new call
                }
                $(s).val('');
            }

            // Set the real or parent input to this value
            resetHidden(fieldname);

            // Show next dropdown
            level += 1;
            var dropdown_row = $(selector + '_L' + level + '__row');
            if (dropdown_row.length) {
                // Do we need to read hierarchy?
                if ($(selector + '_L' + (level - 1) + ' option[value="' + id + '"]').hasClass('missing')) {
                    // Missing level: we already have the data
                    var v = l[id];
                    // Add the ID inside
                    v['i'] = id;
                    var values = [v];
                } else {
                    var read = true;
                    for (var i in l) {
                        if (l[i].f == id) {
                            // We have a child, so assume we have all
                            read = false;
                            break;
                        }
                    }
                    if (read) {
                        // AJAX Read extra hierarchy options
                        readHierarchy(fieldname, level, id);
                    }
                    var v,
                        values = [];
                    for (var i in l) {
                        v = l[i];
                        //if ((v['l'] == level) && (v['f'] == id)) {
                        if (v['f'] == id) {
                            // Add the ID inside
                            v['i'] = i;
                            values.push(v);
                        }
                    }
                }
                var len_values = values.length;
                if (len_values) {
                    // Show dropdown
                    dropdown_row.removeClass('hide').show();
                    $(selector + '_L' + level + '__row1').removeClass('hide').show(); // Tuple themes
                    values.sort(nameSort);
                    var _id,
                        location,
                        missing,
                        option,
                        selected;
                    var select = $(selector + '_L' + level);
                    // Remove old entries
                    $(selector + '_L' + level + ' option').remove('[value != ""]');
                    for (var i=0; i < len_values; i++) {
                        location = values[i];
                        _id = location['i'];
                        if (id == _id) {
                            selected = ' selected="selected"';
                        } else {
                            selected = '';
                        }
                        if (l[_id]['l'] == level) {
                            // A normal level
                            missing = '';
                        } else {
                            // A link for a missing level
                            missing = ' class="missing"';
                        }
                        option = '<option value="' + _id + '"' + selected + missing + '>' + location['n'] + '</option>';
                        select.append(option);
                    }
                    if (select.hasClass('multiselect')) {
                        if (select.hasClass('search')) {
                            select.multiselect({header: '',
                                                height: 300,
                                                minWidth: 0,
                                                selectedList: 1,
                                                noneSelectedText: $(selector + '_L' + level + ' option[value=""]').html(),
                                                multiple: false
                                                }).multiselectfilter({label: '',
                                                                      placeholder: i18n.search
                                                                      });
                            // Show headers
                            $('.ui-multiselect-header').show();
                        } else {
                            select.multiselect({header: false,
                                                height: 300,
                                                minWidth: 0,
                                                selectedList: 1,
                                                noneSelectedText: $(selector + '_L' + level + ' option[value=""]').html(),
                                                multiple: false
                                                });
                        }
                    }
                    if (len_values == 1) {
                        // Only 1 option so select this one
                        lx_select(fieldname, level, _id);
                        // Nothing more for this old level
                        return;
                    }
                }
            } else {
                // We're at the top of the hierarchy
                var geocode_button = $(selector + '_geocode button');
                if (geocode_button.length) {
                    geocodeDecision(fieldname);
                }
            }
        } else {
            // Dropdown has been de-selected
            // Set the real/parent inputs appropriately
            resetHidden(fieldname);
            // Hide all lower levels
            // & remove their values
            for (var lev = level + 1; lev < 6; lev++) {
                var s = selector + '_L' + lev;
                if (hide_lx) {
                    $(s + '__row').hide();
                    $(s + '__row1').hide(); // Tuple themes
                } else {
                    // Hide the limited options
                    $(s + ' option').remove('[value != ""]');
                    // @ToDo: Read the full set of options via a new call
                }
                $(s).val('');
            }
        }
        // Zoom the map to the appropriate bounds
        zoomMap(fieldname);
    }

    /**
     * Sort Names alphabetically
     * - helper function for new dropdowns in lx_select()
     */
    var nameSort = function(a, b) {
        // Sort Hierarchical Dropdown data by Name
        a = a['n'];
        var names = [a, b['n']];
        names.sort();
        if (names[0] == a) {
            return -1;
        } else {
            return 1;
        }
    }

    /**
     * Read the Hierarchy
     * - lookup a set of locations to use to populate a dropdown
     */
    var readHierarchy = function(fieldname, level, id) {
        var selector = '#' + fieldname;

        // Hide dropdown
        var dropdown = $(selector + '_L' + level);
        dropdown.hide();
        if (dropdown.hasClass('multiselect')) {
            // Hide Multiselect button
            var button = $(selector + '_L' + level + '__row button');
            button.hide();
        }

        // Show Throbber
        var throbber = $(selector + '_L' + level + '__throbber');
        throbber.removeClass('hide').show();

        // Download Location Data
        var url = S3.Ap.concat('/gis/ldata/' + id);
        $.ajaxS3({
            async: false,
            url: url,
            dataType: 'script',
            success: function(data) {
                // Copy the elements across
                for (var prop in n) {
                    l[prop] = n[prop];
                }
                // Clear the memory
                n = null;
                // Hide Throbber
                throbber.hide();
                if (dropdown.hasClass('multiselect')) {
                    // Show button
                    button.removeClass('hide').show();
                } else {
                    // Show dropdown
                    dropdown.removeClass('hide').show();
                }
            },
            error: function(request, status, error) {
                if (error == 'UNAUTHORIZED') {
                    msg = i18n.gis_requires_login;
                } else {
                    msg = request.responseText;
                }
                s3_debug(msg);
                S3.showAlert(msg, 'error');
                // Revert state of widget to allow user to retry without reloading page
                // Hide Throbber
                throbber.hide();
                if (dropdown.hasClass('multiselect')) {
                    // Show button
                    button.removeClass('hide').show();
                } else {
                    // Show dropdown
                    dropdown.removeClass('hide').show();
                }
            }
        });
    }

    /**
     * Lookup the value of the lowest-set Lx
     */
    var lookupParent = function(fieldname) {
        var selector = '#' + fieldname + '_L';

        var id;
        for (var level=5; level > -1; level--) {
            id = $(selector + level).val();
            if (id) {
                return id;
            }
        }
        // No Lx set at all, so return the lowest-level un-selectable Lx if-any
        var d = l['d'];
        return d.id;
    }

    /**
     * Reset the Real & Parent Inputs
     */
    var resetHidden = function(fieldname) {
        var selector = '#' + fieldname;

        var parent_input = $(selector + '_parent');
        var real_input = $(selector);
        if (real_input.data('specific')) {
            // Set the Parent field
            var parent = lookupParent(fieldname);
            parent_input.val(parent);
        } else {
            var address = $(selector + '_address').val();
            var postcode = $(selector + '_postcode').val();
            var lat = $(selector + '_lat').val();
            var lon = $(selector + '_lon').val();
            var wkt = $(selector + '_wkt').val();
            if (!address && !postcode && !lat && !lon && !wkt) {
                // No specific data, so point directly to the Lowest-set Lx
                var id = lookupParent(fieldname);
                // Update the real_input
                real_input.val(id);
                // Clear the parent field
                parent_input.val('');
            } else {
                // We have specific data
                // Dummify the real_input to trigger a create in IS_LOCATION_SELECTOR2
                real_input.val('dummy');
                // Set the Parent field
                var parent = lookupParent(fieldname);
                parent_input.val(parent);
            }
            if (fieldname.slice(0, 4) == 'sub_') {
                // This is an S3SQLInlineComponent
                // Trigger a change
                real_input.change();
            }
        }
    }

    /**
     * Show the Address & Postcode fields
     */
    var showAddress = function(fieldname) {
        var selector = '#' + fieldname;

        // Display the rows
        $(selector + '_address__row').removeClass('hide').show();
        $(selector + '_address__row1').removeClass('hide').show(); // Tuple themes
        $(selector + '_postcode__row').removeClass('hide').show();
        $(selector + '_postcode__row1').removeClass('hide').show(); // Tuple themes

        var geocode_button = $(selector + '_geocode button');
        if (geocode_button.length) {
            // Geocoder enabled: Listen for changes
            $(selector + '_address,' + selector + '_postcode').change(function() {
                geocodeDecision(fieldname);
            });
        }
    }

    /**
     * Event handler to decide whether to Geocode
     * Address: Mandatory
     * Postcode: optional
     * Lx: Mandatory to lowest-level if it has options
     */
    var geocodeDecision = function(fieldname) {
        var selector = '#' + fieldname;

        if (!$(selector + '_address').val()) {
            return;
        }
        var i,
            lev,
            levels = ['1', '2', '3', '4', '5'],
            s;
        for (i=0; i < 5; i++) {
            lev = levels[i];
            s = $(selector + '_L' + lev);
            if ((s.length) && (!s.val())) {
                if (s[0].options.length > 1) {
                    // User hasn't yet selected an option, but can do so
                    return;
                }
            }
        }

        if ($(selector).data('manually_geocoded')) {
            // Show a button to allow the user to do a new automatic Geocode
            $(selector + '_geocode .geocode_success').hide();
            $(selector + '_geocode .geocode_fail').hide();
            $(selector + '_geocode button').removeClass('hide')
                                           .show()
                                           .click(function() {
                $(this).hide();
                geocode(fieldname);
                resetHidden(fieldname);
            });
        } else {
            // Do an Automatic Geocode
            geocode(fieldname);
        }
        resetHidden(fieldname);
    }

    /**
     * Lookup the Lat/Lon for a Street Address
     */
    var geocode = function(fieldname) {
        var selector = '#' + fieldname;

        // Hide old messages
        var fail = $(selector + '_geocode .geocode_fail');
        var success = $(selector + '_geocode .geocode_success');
        fail.hide();
        success.hide();

        // Show Throbber
        var throbber = $(selector + '_geocode .throbber');
        throbber.removeClass('hide').show();

        // Collect the Address Components
        var address = $(selector + '_address').val();
        var post_data = {address: address};
        var postcode = $(selector + '_postcode').val();
        if (postcode) {
            post_data.postcode = postcode;
        }
        var L0 = $(selector + '_L0').val();
        if (L0) {
            post_data.L0 = L0;
        }
        var L1 = $(selector + '_L1').val();
        if (L1) {
            post_data.L1 = L1;
        }
        var L2 = $(selector + '_L2').val();
        if (L2) {
            post_data.L2 = L2;
        }
        var L3 = $(selector + '_L3').val();
        if (L3) {
            post_data.L3 = L3;
        }
        var L4 = $(selector + '_L4').val();
        if (L4) {
            post_data.L4 = L4;
        }
        var L5 = $(selector + '_L5').val();
        if (L5) {
            post_data.L5 = L5;
        }

        // Submit to Geocoder
        var url = S3.Ap.concat('/gis/geocode');
        $.ajaxS3({
            //async: false,
            url: url,
            type: 'POST',
            data: post_data,
            dataType: 'json',
            success: function(data) {
                var lat = data.lat;
                var lon = data.lon;
                if (lat || lon) {
                    // Update fields
                    $(selector + '_lat').val(lat);
                    $(selector + '_lon').val(lon);
                    // If Map Showing then add/move Point
                    gis = S3.gis
                    if (gis.maps) {
                        var map_id = 'location_selector_' + fieldname;
                        var map = gis.maps[map_id];
                        if (map) {
                            var draftLayer = map.s3.draftLayer
                            draftLayer.removeAllFeatures();
                            var geometry = new OpenLayers.Geometry.Point(parseFloat(lon), parseFloat(lat));
                            geometry.transform(gis.proj4326, map.getProjectionObject());
                            var feature = new OpenLayers.Feature.Vector(geometry);
                            draftLayer.addFeatures([feature]);
                            // Move viewport to this feature
                            zoomMap(fieldname);
                        }
                    }
                    // Notify results
                    throbber.hide();
                    success.html(i18n.address_mapped).removeClass('hide').show();
                } else {
                    // Notify results
                    throbber.hide();
                    fail.html(i18n.address_not_mapped).removeClass('hide').show();
                    s3_debug(data);
                }
            },
            error: function(request, status, error) {
                if (error == 'UNAUTHORIZED') {
                    msg = i18n.gis_requires_login;
                } else {
                    msg = request.responseText;
                }
                // Notify results
                throbber.hide();
                fail.html(i18n.address_not_mapped).removeClass('hide').show();
                s3_debug(msg);
            }
        });
    }

    /**
     * Lookup the Location of a Lat/Lon
     */
    var geocode_r = function(fieldname) {
        var selector = '#' + fieldname;

        // Hide old messages
        var fail = $(selector + '_geocode .geocode_fail');
        var success = $(selector + '_geocode .geocode_success');
        fail.hide();
        success.hide();

        // Show Throbber
        var throbber = $(selector + '_geocode .throbber');
        throbber.removeClass('hide').show();

        // Collect the Lat/Lon
        post_data = {lat: $(selector + '_lat').val(),
                     lon: $(selector + '_lon').val()
                     }

        // Submit to Geocoder
        var url = S3.Ap.concat('/gis/geocode_r');
        $.ajaxS3({
            async: false,
            url: url,
            type: 'POST',
            data: post_data,
            dataType: 'json',
            success: function(data) {
                if (data.L0) {
                    // Update fields
                    $(selector + '_L0_input').val(data.L0);
                    $(selector + '_L0').val(data.L0);
                    if (data.L1) {
                        $(selector + '_L1_input').val(data.L1);
                        $(selector + '_L1').val(data.L1);
                    }
                    if (data.L2) {
                        $(selector + '_L2_input').val(data.L2);
                        $(selector + '_L2').val(data.L2);
                    }
                    if (data.L3) {
                        $(selector + '_L3_input').val(data.L3);
                        $(selector + '_L3').val(data.L3);
                    }
                    if (data.L4) {
                        $(selector + '_L4_input').val(data.L4);
                        $(selector + '_L4').val(data.L4);
                    }
                    if (data.L5) {
                        $(selector + '_L5_input').val(data.L5);
                        $(selector + '_L5').val(data.L5);
                    }
                    // Notify results
                    throbber.hide();
                    success.html(i18n.location_found).removeClass('hide').show();
                } else {
                    // Notify results
                    throbber.hide();
                    fail.html(i18n.location_not_found).removeClass('hide').show();
                    //s3_debug(data);
                }
            },
            error: function(request, status, error) {
                if (error == 'UNAUTHORIZED') {
                    msg = i18n.gis_requires_login;
                } else {
                    msg = request.responseText;
                }
                // Notify results
                throbber.hide();
                fail.html(i18n.location_not_found).removeClass('hide').show();
                s3_debug(msg);
            }
        });
    }

    /**
     * Hide the Map
     * - this also acts as a 'Cancel' for the addition of Lat/Lon/WKT fields
     */
    var hideMap = function(fieldname) {
        var selector = '#' + fieldname;

        // Reset the Click event
        $(selector + '_map_icon').unbind('click')
                                 .click(function() {
            showMap(fieldname);
        });

        // Hide the Map
        $(selector + '_map_wrapper').hide();

        if ($(selector).data('specific')) {
            // Change the Label
            $(selector + '_map_icon span').html(i18n.show_map_view);
        } else {
            // Remove the Feature (if-any)
            var map_id = 'location_selector_' + fieldname;
            var map = S3.gis.maps[map_id];
            map.s3.draftLayer.removeAllFeatures();

            // Clear the Lat/Lon/WKT fields
            $(selector + '_lat').val('');
            $(selector + '_lon').val('');
            $(selector + '_wkt').val('');

            // Change the Label
            $(selector + '_map_icon span').html(i18n.show_map_add);

            // Reset the real_input
            resetHidden(fieldname);
        }
    }

    /**
     * Check that Map JS is Loaded
     * - used if a tab containing a Map is unhidden
     */
    var jsLoaded = function() {
        var dfd = new jQuery.Deferred();

        // Test every half-second
        setTimeout(function working() {
            if (S3.gis.maps != undefined) {
                dfd.resolve('loaded');
            } else if (dfd.state() === 'pending') {
                // Notify progress
                dfd.notify('waiting for JS to load...');
                // Loop
                setTimeout(working, 500);
            } else {
                // Failed!?
            }
        }, 1);

        // Return the Promise so caller can't change the Deferred
        return dfd.promise();
    };

    /**
     * Show the Map
     * - this doesn't imply that a specific location is to be created
     * - that only happens if a Point is created on the Map
     */
    var showMap = function(fieldname, options) {
        var selector = '#' + fieldname;

        // Reset the Click event
        $(selector + '_map_icon').unbind('click')
                                 .click(function() {
            hideMap(fieldname);
        });

        // Change the Label
        var label = $(selector + '_map_icon span')
        label.html(i18n.hide_map);

        // Show the Map
        var map_wrapper = $(selector + '_map_wrapper')
        map_wrapper.removeClass('hide').show();
        // Scroll to this section
        $('html,body').animate({scrollTop: map_wrapper.offset().top}, 250);

        // Check if Maps JS is Loaded
        $.when(jsLoaded()).then(
            function(status) {
                // Success: Instantiate Maps
                var map_id = 'location_selector_' + fieldname;
                var gis = S3.gis;
                if (!gis.maps[map_id]) {
                    // Instantiate the Map as we couldn't do it when DIV is hidden
                    var map = gis.show_map(map_id);

                    var real_input = $(selector);
                    var parent_input = $(selector + '_parent');
                    // Zoom to the appropriate bounds
                    zoomMap(fieldname);

                    var latfield = $(selector + '_lat');
                    var lonfield = $(selector + '_lon');
                    var wktfield = $(selector + '_wkt');
                    var lat = latfield.val();
                    var lon = lonfield.val();
                    var wkt = wktfield.val();
                    if (lat || lon || wkt) {
                        // Display feature
                        if ((wkt != undefined) && wkt) {
                            var in_options = {
                                'internalProjection': map.getProjectionObject(),
                                'externalProjection': gis.proj4326
                                };
                            var feature = new OpenLayers.Format.WKT(in_options).read(wkt);
                        } else {
                            var geometry = new OpenLayers.Geometry.Point(parseFloat(lon), parseFloat(lat));
                            geometry.transform(gis.proj4326, map.getProjectionObject());
                            var feature = new OpenLayers.Feature.Vector(geometry);
                        }
                        map.s3.draftLayer.addFeatures([feature]);
                        // Update the Hidden Fields
                        resetHidden(fieldname);
                    }
                    // Watch for new features being selected, so that we can store the Lat/Lon/WKT
                    var control;
                    var controls = map.controls;
                    for (var i=0, len=controls.length; i < len; i++) {
                        if (controls[i].CLASS_NAME == 'OpenLayers.Control.DrawFeature') {
                            control = controls[i];
                            break;
                        }
                    }
                    if (control) {
                        // Callback function for when a feature is added
                        map.s3.pointPlaced = function(feature) {
                            // Hide any Geocoder messages
                            $(selector + '_geocode .geocode_fail').hide();
                            $(selector + '_geocode .geocode_success').hide();
                            // Update the Form fields
                            var geometry = feature.geometry;
                            if (geometry.CLASS_NAME == 'OpenLayers.Geometry.Point') {
                                var centerPoint = geometry.getBounds().getCenterLonLat();
                                centerPoint.transform(map.getProjectionObject(), gis.proj4326);
                                wktfield.val('');
                                latfield.val(centerPoint.lat);
                                lonfield.val(centerPoint.lon);
                                // Store the fact that we've now added Marker manually
                                real_input.data('manually_geocoded', true);
                                //if (!$(selector + '_address').val()) {
                                // Reverse Geocode the Point
                                geocode_r(fieldname);
                                //}
                            } else {
                                // Polygon
                                var out_options = {
                                    'internalProjection': map.getProjectionObject(),
                                    'externalProjection': gis.proj4326
                                    };
                                wkt = new OpenLayers.Format.WKT(out_options).write(feature);
                                wktfield.val(wkt);
                                latfield.val('');
                                lonfield.val('');
                                // Store the fact that we've now added Marker manually
                                real_input.data('manually_geocoded', true);
                            }
                            // Update the Hidden Fields
                            resetHidden(fieldname);
                        }
                        //control.events.register('featureadded', null, pointPlaced);
                    }
                } else {
                    // Map already instantiated
                    //var map = gis.maps[map_id];
                }
            },
            function(status) {
                // Failed
                s3_debug(status);
            },
            function(status) {
                // Progress
                s3_debug(status);
            }
        );
    }

    /**
     * Zoom the Map
     * - to the appropriate bounds
     */
    var zoomMap = function(fieldname, id) {
        var gis = S3.gis;
        if (gis.maps) {
            var map_id = 'location_selector_' + fieldname;
            var map = gis.maps[map_id];
            if (map) {
                // Zoom to point, if we have it
                var selector = '#' + fieldname;
                var lat = $(selector + '_lat').val();
                var lon = $(selector + '_lon').val();
                if (lat && lon) {
                    // Ensure a minimal BBOX in case we just have a single data point
                    var min_size = 0.05;
                    // Add an Inset in order to not have points right at the edges of the map
                    var inset = 0.007;
                    var delta = (min_size / 2) + inset;
                    var lon_min = lon - delta,
                        lat_min = lat - delta,
                        lon_max = lon + delta,
                        lat_max = lat + delta;
                    var bounds = [lon_min, lat_min, lon_max, lat_max];
                } else {
                    // Zoom to extent of the Lx, if we have it
                    if (!id) {
                        // Use default bounds if lookupParent fails
                        id = lookupParent(fieldname) || 'd';
                    }
                    var bounds = l[id].b;
                    if (!bounds) {
                        // Try the parent
                        var parent = l[id].f;
                        parent = l[parent];
                        if (parent) {
                            bounds = parent.b;
                            if (!bounds) {
                                // Try the grandparent
                                var grandparent = parent.f;
                                grandparent = l[grandparent];
                                if (grandparent) {
                                    bounds = grandparent.b;
                                    if (!bounds) {
                                        // Try the greatgrandparent
                                        var greatgrandparent = grandparent.f;
                                        greatgrandparent = l[greatgrandparent];
                                        if (greatgrandparent) {
                                            bounds = greatgrandparent.b;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                if (bounds) {
                    bounds = OpenLayers.Bounds.fromArray(bounds);
                    S3.gis.zoomBounds(map, bounds);
                }
            }
        }
    }

}());

// END ========================================================================