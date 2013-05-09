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

var s3_gis_locationselector2 = function(fieldname, L0, L1, L2, L3, L4, L5) {
    // Function to be called by S3LocationSelectorWidget2

    // Move the visible rows underneath the real (hidden) one
    var map_div = $('#' + fieldname + '__row .map_wrapper').attr('id', fieldname + '_map_wrapper');
    var L0_row = $('#' + fieldname + '_L0__row');
    var L1_row = $('#' + fieldname + '_L1__row');
    var L2_row = $('#' + fieldname + '_L2__row');
    var L3_row = $('#' + fieldname + '_L3__row');
    var L4_row = $('#' + fieldname + '_L4__row');
    var L5_row = $('#' + fieldname + '_L5__row');
    $('#' + fieldname + '__row').hide()
                                .after(map_div)
                                .after(L5_row)
                                .after(L4_row)
                                .after(L3_row)
                                .after(L2_row)
                                .after(L1_row)
                                .after(L0_row);

    // Initial population of dropdown(s)
    if (L0) {
        lx_select(fieldname, 0, L0);
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

    // Listen events
    $('#' + fieldname + '_L0').change(function() {
        lx_select(fieldname, 0);
    });
    $('#' + fieldname + '_L1').change(function() {
        lx_select(fieldname, 1);
    });
    $('#' + fieldname + '_L2').change(function() {
        lx_select(fieldname, 2);
    });
    $('#' + fieldname + '_L3').change(function() {
        lx_select(fieldname, 3);
    });
    $('#' + fieldname + '_L4').change(function() {
        lx_select(fieldname, 4);
    });
    $('#' + fieldname + '_L5').change(function() {
        lx_select(fieldname, 5);
    });
}

function lx_select(fieldname, level, id) {
    // Hierarchical dropdown has been selected
    // Clear the Lat/Lon fields after storing the current value
    // - need to clear for IS_LOCATION_SELECTOR2
    var latfield = $('#' + fieldname + '_lat');
    var lonfield = $('#' + fieldname + '_lon');
    var lat = latfield.val();
    var lon = lonfield.val();
    if (lat) {
        latfield.data('lat', lat);
    }
    if (lon) {
        lonfield.data('lon', lon);
    }
    latfield.val('');
    lonfield.val('');
    // Hide Map
    $('#' + fieldname + '_map_wrapper').hide();
    if (id) {
        // Set this dropdown to this value
        // - this is being set from outside the dropdown, e.g. an update form or using a visible default location
        $('#' + fieldname + '_L' + level).val(id);
    } else {
        // Read the selected value from the dropdown
        id = $('#' + fieldname + '_L' + level).val();
    }
    //if (level === 0) {
        // @ToDo: This data structure doesn't exist yet (not required for TLDRMP)
        // Set Labels
        //var h = hdata[id];
        //$('#' + fieldname + '_L1__row label').html(h.l1 + ':');
        //$('#' + fieldname + '_L2__row label').html(h.l2 + ':');
        //$('#' + fieldname + '_L3__row label').html(h.l3 + ':');
        //$('#' + fieldname + '_L4__row label').html(h.l4 + ':');
        //$('#' + fieldname + '_L5__row label').html(h.l5 + ':');
    //}
    if (id) {
        // Set the real input to this value
        $('#' + fieldname).val(id);
        // Hide all lower levels
        for (var lev=level + 1; lev < 6; lev++) {
            $('#' + fieldname + '_L' + lev + '__row').hide();
        }
        // Show next dropdown
        level += 1;
        var selector = $('#' + fieldname + '_L' + level + '__row');
        if (selector.length) {
            selector.show();
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
            var select = $('#' + fieldname + '_L' + level);
            // Remove old entries
            $('#' + fieldname + '_L' + level + ' option').remove('[value != ""]');
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
        } else {
            // We're at the top of the hierarchy so show the map so we can select a specific point
            $('#' + fieldname + '_map_wrapper').show();
            if (!S3.gis.mapPanel) {
                // Instantiate the Map as we couldn't do it when DIV is hidden
                var map = S3.gis.show_map();
                // @ToDo: Display any existing stored point
                var lat = latfield.data('lat');
                if (lat) {
                    latfield.val(lat);
                }
                var lon = lonfield.data('lon');
                if (lon) {
                    lonfield.val(lon);
                }
                var geometry = new OpenLayers.Geometry.Point(parseFloat(lon), parseFloat(lat));
                geometry.transform(S3.gis.proj4326, map.getProjectionObject());
                var feature = new OpenLayers.Feature.Vector(geometry);
                S3.gis.draftLayer.addFeatures([feature]);
                // Watch for new points being selected, so that we can store the Lat/Lon
                var control;
                var controls = map.controls;
                for (var i=0, len=controls.length; i < len; i++) {
                    if (controls[i].CLASS_NAME == 'OpenLayers.Control.DrawFeature') {
                        control = controls[i];
                    }
                }
                if (control) {
                    var updateForm = function(event) {
                        var centerPoint = event.feature.geometry.getBounds().getCenterLonLat();
                        centerPoint.transform(map.getProjectionObject(), S3.gis.proj4326);
                        latfield.val(centerPoint.lat);
                        lonfield.val(centerPoint.lon);
                        // Store the parent
                        $('#' + fieldname + '_parent').val(id);
                        // Dummify the real input (need this to enter IS_LOCATION_SELECTOR2)
                        $('#' + fieldname).val('dummy');
                    }
                    control.events.register('featureadded', null, updateForm);
                }
            }
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
                bounds = OpenLayers.Bounds.fromArray(bounds).transform(S3.gis.proj4326, S3.gis.projection_current);
                map.zoomToExtent(bounds);
            }
        }
    } else {
        if (level === 0) {
            // Clear the real input
            $('#' + fieldname).val('');
        } else {
            // Set the real input to the next higher-level
            id = $('#' + fieldname + '_L' + (level - 1)).val();
            $('#' + fieldname).val(id);
        }
        // Hide all lower levels
        for (var lev=level + 1; lev < 6; lev++) {
            $('#' + fieldname + '_L' + lev + '__row').hide();
        }
    }
}

function nameSort(a, b) {
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

function readHierarchy(fieldname, level, id) {
    // Show Throbber
    $('#' + fieldname + '_L' + level + '__throbber').show();
    var url = S3.Ap.concat('/gis/ldata/' + id);
    if (!$('#' + fieldname + '_L' + (level + 1) + '__row').length) {
        // This is the lowest-level of the hierarchy, so
        // Download the bounds to zoom the map to
        url += '/b';
    }
    // Download Location Data
    $.ajax({
        'async': false,
        'url': url,
        'success': function(data) {
            // Copy the elements across
            for (var prop in n) {
                l[prop] = n[prop];
            }
            // Clear the memory
            n = null;
            // Hide Throbber
            $('#' + fieldname + '_L' + level + '__throbber').hide();
        },
        'error': function(request, status, error) {
            if (error == 'UNAUTHORIZED') {
                msg = i18n.gis_requires_login;
            } else {
                msg = request.responseText;
            }
        },
        'dataType': 'script'
    });
}
