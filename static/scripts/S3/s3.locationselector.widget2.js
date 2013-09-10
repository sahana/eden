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
(function () {

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

        // Move the user-visible rows underneath the real (hidden) one
        var error_row = real_input.next('.error_wrapper');
        var L0_row = $(selector + '_L0__row');
        var L1_row = $(selector + '_L1__row');
        var L2_row = $(selector + '_L2__row');
        var L3_row = $(selector + '_L3__row');
        var L4_row = $(selector + '_L4__row');
        var L5_row = $(selector + '_L5__row');
        var address_row = $(selector + '_address__row');
        var postcode_row = $(selector + '_postcode__row');
        var map_icon_row = $(selector + '_map_icon__row');
        var map_div = $(selector + '__row .map_wrapper').attr('id', fieldname + '_map_wrapper');
        if (reverse_lx) {
            $(selector + '__row').hide()
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
            $(selector + '__row').hide()
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

        if (specific) {
            // Store this to retrieve later
            real_input.data('specific', specific);
        }

        // Store whether we hide_lx
        real_input.data('hide_lx', hide_lx);

        // Initial population of dropdown(s)
        if (L0) {
            lx_select(fieldname, 0, L0);
        } else {
            // Show the Country row
            L0_row.show();
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
            var select = $(selector + '_L0');
            for (var i=0, len=values.length; i < len; i++) {
                location = values[i];
                _id = location['i'];
                option = '<option value="' + _id + '">' + location['n'] + '</option>';
                select.append(option);
            }
        }
        if (L1) {
            lx_select(fieldname, 1, L1);
        }
        if (L2) {
            lx_select(fieldname, 2, L2);
        }
        if (L3) {
            lx_select(fieldname, 3, L3);
        }
        if (L4) {
            lx_select(fieldname, 4, L4);
        }
        if (L5) {
            lx_select(fieldname, 5, L5);
        }
        // Show Address/Postcode Rows
        showAddress(fieldname);
        // Show Map icon
        map_icon_row.show();

        var lat = $(selector + '_lat').val();
        var lon = $(selector + '_lon').val();
        var wkt = $(selector + '_wkt').val();
        if (lat || lon || wkt) {
            showMap(fieldname);
        } else {
            $(selector + '_map_icon').click(function() {
                showMap(fieldname);
                return false;
            });
        }

        // Listen events
        $(selector + '_L0').change(function() {
            lx_select(fieldname, 0);
        });
        $(selector + '_L1').change(function() {
            lx_select(fieldname, 1);
        });
        $(selector + '_L2').change(function() {
            lx_select(fieldname, 2);
        });
        $(selector + '_L3').change(function() {
            lx_select(fieldname, 3);
        });
        $(selector + '_L4').change(function() {
            lx_select(fieldname, 4);
        });
        $(selector + '_L5').change(function() {
            lx_select(fieldname, 5);
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
            $(selector + '_L' + level).val(id);
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
                $.ajax({
                    async: false,
                    url: url,
                    dataType: 'script'
                }).done(function(data) {
                    // Copy the elements across
                    hi = {};
                    for (var prop in n) {
                        hi[prop] = n[prop];
                    }
                    h[id] =  hi;
                    // Clear the memory
                    n = null;
                }).fail(function(request, status, error) {
                    if (error == 'UNAUTHORIZED') {
                        msg = i18n.gis_requires_login;
                    } else {
                        msg = request.responseText;
                    }
                });
            }
            // Use default values as fallback if no value specified
            var d = h['d'];
            var label = hi['1'] || d['1'];
            $(selector + '_L1__row label').html(label + ':');
            label = hi['2'] || d['2'];
            $(selector + '_L2__row label').html(label + ':');
            label = hi['3'] || d['3'];
            $(selector + '_L3__row label').html(label + ':');
            label = hi['4'] || d['4'];
            $(selector + '_L4__row label').html(label + ':');
            label = hi['5'] || d['5'];
            $(selector + '_L5__row label').html(label + ':');
        }
        if (id) {
            // Hide all lower levels
            // & remove their values
            for (var lev=level + 1; lev < 6; lev++) {
                var s = selector + '_L' + lev;
                if (hide_lx) {
                    $(s + '__row').hide();
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
            var dropdown = $(selector + '_L' + level + '__row');
            if (dropdown.length) {
                dropdown.show();
                // Do we need to read hierarchy?
                var read = true; 
                for (var i in l) {
                    if (l[i].f == id) {
                        read = false;
                        continue;
                    }
                }
                if (read) {
                    // AJAX Read extra hierarchy options
                    readHierarchy(fieldname, level, id);
                }
                var values = [];
                for (var i in l) {
                    v = l[i];
                    if ((v['l'] == level) && (v['f'] == id)) {
                        v['i'] = i;
                        values.push(v);
                    }
                }
                values.sort(nameSort);
                var _id, location, option, selected;
                var select = $(selector + '_L' + level);
                // Remove old entries
                $(selector + '_L' + level + ' option').remove('[value != ""]');
                for (var i=0, len=values.length; i < len; i++) {
                    location = values[i];
                    _id = location['i'];
                    if (id == _id) {
                        selected = ' selected="selected"';
                    } else {
                        selected = '';
                    }
                    option = '<option value="' + _id + '"' + selected + '>' + location['n'] + '</option>';
                    select.append(option);
                }
            //} else {
                // We're at the top of the hierarchy
                // - nothing to do
            }
        } else {
            // Dropdown has been de-selected
            if (level === 0) {
                // Have the Map Zoom use the default bounds
                id = 'd';
            } else {
                // Set the ID for the Map Zoom
                id = $(selector + '_L' + (level - 1)).val();
                if (!id) {
                    // Have the Map Zoom use the default bounds
                    id = 'd';
                }
            }
            // Set the real/parent inputs appropriately
            resetHidden(fieldname);
            // Hide all lower levels
            // & remove their values
            for (var lev=level + 1; lev < 6; lev++) {
                var s = selector + '_L' + lev;
                if (hide_lx) {
                    $(s + '__row').hide();
                } else {
                    // Hide the limited options
                    $(s + ' option').remove('[value != ""]');
                    // @ToDo: Read the full set of options via a new call
                }
                $(s).val('');
            }
        }
        // Zoom the map to the appropriate bounds
        zoomMap(fieldname, id);
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

        // Show Throbber
        var throbber = $(selector + '_L' + level + '__throbber');
        throbber.show();

        // Download Location Data
        var url = S3.Ap.concat('/gis/ldata/' + id);
        $.ajax({
            async: false,
            url: url,
            dataType: 'script'
        }).done(function(data) {
            // Copy the elements across
            for (var prop in n) {
                l[prop] = n[prop];
            }
            // Clear the memory
            n = null;
            // Hide Throbber
            throbber.hide();
            // Show dropdown
            dropdown.show();
        }).fail(function(request, status, error) {
            if (error == 'UNAUTHORIZED') {
                msg = i18n.gis_requires_login;
            } else {
                msg = request.responseText;
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
        // No Lx set at all, so return the default country if-any
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
        var specific = real_input.data('specific');
        if (specific) {
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
                var id = lookupParent(fieldname);
                // Update the real_input
                real_input.val(id);
                // Clear the parent field
                parent_input.val('');
            } else {
                // Dummify the real_input to trigger a create in IS_LOCATION_SELECTOR2
                real_input.val('dummy');
                // Set the Parent field
                var parent = lookupParent(fieldname);
                parent_input.val(parent);
            }
        }
    }

    /**
     * Show the Address & Postcode fields
     */
    var showAddress = function(fieldname) {
        var selector = '#' + fieldname;

        // Display the rows
        $(selector + '_address__row').show();
        $(selector + '_postcode__row').show();

        var geocode_button = $(selector + '_geocode button');
        if (geocode_button.length) {
            // Listen for changes
            $(selector + '_address').change(function() {
                var real_input = $(selector);
                var manually_geocoded = real_input.data('manually_geocoded');
                if (manually_geocoded) {
                    // Show a button to allow the user to do a new automatic Geocode
                    $(selector + '_geocode .geocode_success').hide();
                    $(selector + '_geocode .geocode_fail').hide();
                    geocode_button.removeClass('hide')
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
            });
        }
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
        $.ajax({
            async: false,
            url: url,
            type: 'POST',
            data: post_data,
            dataType: 'json'
        }).done(function(data) {
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
                    }
                }
                // Notify results
                throbber.hide();
                success.removeClass('hide').show();
            } else {
                // Notify results
                throbber.hide();
                fail.removeClass('hide').show();
                s3_debug(data);
            }
        }).fail(function(request, status, error) {
            if (error == 'UNAUTHORIZED') {
                msg = i18n.gis_requires_login;
            } else {
                msg = request.responseText;
            }
            // Notify results
            throbber.hide();
            fail.removeClass('hide').show();
            s3_debug(msg);
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
        $.ajax({
            async: false,
            url: url,
            type: 'POST',
            data: post_data,
            dataType: 'json'
        }).done(function(data) {
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
                success.removeClass('hide').show();
            } else {
                // Notify results
                throbber.hide();
                fail.removeClass('hide').show();
                //s3_debug(data);
            }
        }).fail(function(request, status, error) {
            if (error == 'UNAUTHORIZED') {
                msg = i18n.gis_requires_login;
            } else {
                msg = request.responseText;
            }
            // Notify results
            throbber.hide();
            fail.removeClass('hide').show();
            s3_debug(msg);
        });
    }

    /**
     * Hide the Map
     * - this also acts as a 'Cancel' for the addition of Lat/Lon fields
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

        // Remove the Feature (if-any)
        var map_id = 'location_selector_' + fieldname;
        var map = S3.gis.maps[map_id];
        map.s3.draftLayer.removeAllFeatures();

        // Clear the Lat/Lon fields
        $(selector + '_lat').val('');
        $(selector + '_lon').val('');

        // Reset the real_input
        resetHidden(fieldname);
    }

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

        // Show the Map
        $(selector + '_map_wrapper').show();

        var map_id = 'location_selector_' + fieldname;
        var gis = S3.gis;
        if (!gis.maps || !gis.maps[map_id]) {
            // Instantiate the Map as we couldn't do it when DIV is hidden
            var map = gis.show_map(map_id);

            var real_input = $(selector);
            var parent_input = $(selector + '_parent');
            // Zoom to the appropriate bounds
            var id = lookupParent(fieldname);
            if (!id) {
                // Use default bounds
                id = 'd';
            }
            zoomMap(fieldname, id);

            var latfield = $(selector + '_lat');
            var lonfield = $(selector + '_lon');
            var wktfield = $(selector + '_wkt');
            var lat = latfield.val();
            var lon = lonfield.val();
            var wkt = wktfield.val();
            if (lat || lon || wkt) {
                // Display feature
                if (wkt != undefined) {
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
                var pointPlaced = function(event) {
                    // Hide any Geocoder messages
                    $(selector + '_geocode .geocode_fail').hide();
                    $(selector + '_geocode .geocode_success').hide();
                    // Update the Form fields
                    var geometry = event.feature.geometry;
                    if (geometry.CLASS_NAME == 'OpenLayers.Geometry.Point') {
                        var centerPoint = geometry.getBounds().getCenterLonLat();
                        centerPoint.transform(map.getProjectionObject(), gis.proj4326);
                        latfield.val(centerPoint.lat);
                        lonfield.val(centerPoint.lon);
                        // Store the fact that we've now added Marker manually
                        real_input.data('manually_geocoded', true);
                        // Reverse Geocode the Point
                        geocode_r(fieldname);
                    } else {
                        // Polygon
                        var WKT = geometry.transform(map.getProjectionObject(), gis.proj4326).toString();
                        wktfield.val(WKT);
                    }
                    // Update the Hidden Fields
                    resetHidden(fieldname);
                }
                control.events.register('featureadded', null, pointPlaced);
            }
        } else {
            // Map already instantiated
            //var map = gis.maps[map_id];
        }
    }

    /**
     * Zoom the Map
     * - to the appropriate bounds
     */
    var zoomMap = function(fieldname, id) {
        if (S3.gis.maps) {
            var map_id = 'location_selector_' + fieldname;
            var map = S3.gis.maps[map_id];
            if (map) {
                // Zoom to extent of the Lx, if we have it
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
                if (bounds) {
                    bounds = OpenLayers.Bounds.fromArray(bounds)
                                              .transform(S3.gis.proj4326,
                                                         map.getProjectionObject());
                    map.zoomToExtent(bounds);
                }
            }
        }
    }

}());

// END ========================================================================