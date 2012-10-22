/**
 * Used by the S3LocationSelectorWidget (modules/s3/s3widgets.py)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

// Main jQuery function
$(function() {
    // Moved to sub-function to be able to fire on inserted form
    s3_gis_locationselector_jQuery_onReady();
});

function s3_gis_locationselector_jQuery_onReady() {
    if (typeof(S3.gis.location_id) == 'undefined') {
        // This page doesn't include the Location Selector Widget
    } else {
        // Hide the Label row
        // (we add the label inside the widget boundary)
        $('#' + S3.gis.location_id + '__row1').hide();

        // Set the URL to download locations from
        S3.gis.url = S3.Ap.concat('/gis/location');

        // Should we open a different tab to the default 'Create'?
        // @ToDo: Start off this way server-side
        if ( S3.gis.tab ) {
            if ( S3.gis.tab == 'search' ) {
                // Open the Search tab by default
                s3_gis_search_tab();
            }
        }

        // Load Google API for Geocoder
        try {
            if (google && S3.gis.geocoder) {
                // Google already loaded, so don't load again
                s3_gis_initGeocoder();
            } else if (S3.gis.geocoder) {
                s3_gis_loadGoogle();
            }
        } catch(err) {};

        // Set initial Autocompletes
        s3_gis_autocompletes();

        // Setup converter for latitude and longitude fields
        s3_gis_lat_lon_converter();

        // Listen for Events & take appropriate Actions

        // Name
        if (S3.gis.site) {
            // For Sites, we default the Building Name to the same as the Site
            $('#' + S3.gis.site + '_name').blur( function() {
                if (!$('#gis_location_name').val()) {
                    // Copy from the Site Name
                    var name = $('#' + S3.gis.site + '_name').val();
                    $('#gis_location_name').val(name);
                }
            });
        }

        // L0
        $('#gis_location_L0').change( function() {
            s3_gis_l0_select();
        });

        // Tabs
        $('#gis_location_search-btn').click( function(evt) {
            s3_gis_search_tab();
            evt.preventDefault();
        });

        $('#gis_location_add-btn').click( function(evt) {
            s3_gis_add_tab();
            evt.preventDefault();
        });

        $('#gis_location_edit-btn').click( function(evt) {
            s3_gis_edit_tab();
            evt.preventDefault();
        });

        $('#gis_location_view-btn').click( function(evt) {
            s3_gis_view_tab();
            evt.preventDefault();
        });

        // Buttons
        $('#gis_location_expand').click( function(evt) {
            if ($('#gis_location_expand').hasClass('expand')) {
                s3_gis_hide_selector();
                $('#gis_location_expand').addClass('expanded');
                $('#gis_location_expand').removeClass('expand');
                evt.preventDefault();
            } else {
                s3_gis_show_tab('add');
                $('#gis_location_expand').addClass('expand');
                $('#gis_location_expand').removeClass('expanded');
                evt.preventDefault();
            }
        });

        $('#gis_location_search_select-btn').click( function(evt) {
            s3_gis_select_search_result();
            evt.preventDefault();
        });

        $('form').submit( function() {
            // The form is being submitted

            // Do the normal form-submission tasks
            // @ToDo: Look to have this happen automatically
            // http://forum.jquery.com/topic/multiple-event-handlers-on-form-submit
            // http://api.jquery.com/bind/
            S3ClearNavigateAwayConfirm();

            // Prepare the location(s) ready to be validated/saved server-side
            if (s3_gis_save_locations()) {
                // Allow the Form's save to continue
                return true;
            } else {
                // If not valid then don't allow save to continue
                return false;
            }
        });
    }
}

// Main Ext function
Ext.onReady(function(){
    // Moved to sub-function to be able to fire on inserted form
    s3_gis_locationselector_Ext_onReady();
});

function s3_gis_locationselector_Ext_onReady() {
    // Map Popup
    var mapButton = Ext.get('gis_location_map-btn');
    if (mapButton) {
        mapButton.on('click', function() {
            S3.gis.mapWin.show();
            if (S3.gis.polygonButton) {
                var wkt = $('#gis_location_wkt').val();
                if (!wkt) {
                    // Enable the crosshair on the Map Selector
                    $('.olMapViewport').addClass('crosshair');
                    // Enable the Control
                    S3.gis.polygonButton.control.activate()
                }
            } else {
                var lat = $('#gis_location_lat').val();
                var lon = $('#gis_location_lon').val();
                if (!lat || !lon) {
                    // Enable the crosshair on the Map Selector
                    $('.olMapViewport').addClass('crosshair');
                    // Enable the Control
                    S3.gis.pointButton.control.activate()
                }
            }
        });
    }
}

function s3_gis_locationselector_activate() {
    // Called after form is inserted into page to activate
    s3_gis_locationselector_jQuery_onReady();
    s3_gis_locationselector_Ext_onReady();
}

function s3_gis_autocompletes() {
    s3_gis_autocomplete(1);
    s3_gis_autocomplete(2);
    s3_gis_autocomplete(3);
    s3_gis_autocomplete(4);
    s3_gis_autocomplete(5);
    s3_gis_autocomplete_search();
}

function s3_gis_autocomplete(level) {
    if (undefined != $('#gis_location_L' + level + '_ac').val()) {
        $('#gis_location_L' + level + '_ac').autocomplete({
            source: s3_gis_ac_set_source(level),
            delay: 500,
            minLength: 2,
            search: function(event, ui) {
                $('#gis_location_L' + level + '_throbber').removeClass('hide').show();
                // Wipe the existing ID so that update forms can change the values to new ones
                $('#gis_location_L' + level).val('');
                return true;
            },
            response: function(event, ui, content) {
                $('#gis_location_L' + level + '_throbber').hide();
                return content;
            },
            focus: function( event, ui ) {
                $('#gis_location_L' + level + '_ac').val( ui.item.name );
                return false;
            },
            select: function( event, ui ) {
                $('#gis_location_L' + level + '_ac').val( ui.item.name );
                $('#gis_location_L' + level).val( ui.item.id );
                if ((ui.item.level == 'L1') && (ui.item.parent) && ($('#gis_location_L0').val() == '')) {
                    // If no L0 set & we've just added an L1 with a parent then set the country accordingly
                    $('#gis_location_L0').val(ui.item.parent);
                }
                // Hide the search results
                $('ul.ui-autocomplete').hide();
                // Update autocompletes
                s3_gis_autocomplete(parseInt(ui.item.level.replace('L', '')) + 1);
                return false;
            }
        }).data('autocomplete')._renderItem = function(ul, item) {
            return $('<li></li>')
                .data('item.autocomplete', item)
                .append('<a>' + item.name + '</a>')
                .appendTo(ul);
        };
    }
}

function s3_gis_autocomplete_search() {
    if (undefined != $('#gis_location_search_ac').val()) {
        $('#gis_location_search_ac').autocomplete({
            source: s3_gis_ac_set_search_source(),
            delay: 500,
            minLength: 2,
            search: function(event, ui) {
                $('#gis_location_search_throbber').removeClass('hide').show();
                // Hide the Select Button
                $('#gis_location_search_select-btn').hide();
                return true;
            },
            response: function(event, ui, content) {
                $('#gis_location_search_throbber').hide();
                return content;
            },
            focus: function( event, ui ) {
                $('#gis_location_search_ac').val( ui.item.name );
                return false;
            },
            select: function( event, ui ) {
                $('#gis_location_search_ac').val( ui.item.name );
                // Hide the search results
                $('ul.ui-autocomplete').hide();
                // Show details
                s3_gis_ac_search_selected(ui.item);
                return false;
            }
        }).data( 'autocomplete' )._renderItem = function( ul, item ) {
            if (item.name && item.addr_street) {
                var represent = '<a>' + item.name + ',  ' + item.addr_street.split(',')[0].split('\n')[0] + '</a>';
            } else if (item.name) {
                var represent = '<a>' + item.name + '</a>';
            } else {
                var represent = '<a>' + item.addr_street.split(',')[0].split('\n')[0] + '</a>';
            }
            return $('<li></li>')
                .data('item.autocomplete', item)
                .append(represent)
                .appendTo(ul);
        };
    }
}

function s3_gis_ac_set_source(level) {
    // Set the source for an Lx Autocomplete

    // Lookup the immediate parent
    var parent = $('#gis_location_L' + (level - 1)).val();

    var grandparent;
    if (('' == parent) && (level > 1)) {
        // Lookup a grandparent
        grandparent = $('#gis_location_L' + (level - 2)).val();
        if (('' == grandparent) && (level > 2)) {
            grandparent = $('#gis_location_L' + (level - 2)).val();
            if (('' == grandparent) && (level > 3)) {
                grandparent = $('#gis_location_L' + (level - 3)).val();
                if (('' == grandparent) && (level > 4)) {
                    grandparent = $('#gis_location_L' + (level - 4)).val();
                    if (('' == grandparent) && (level > 5)) {
                        grandparent = $('#gis_location_L' + (level - 5)).val();
                    }
                }
            }
        }
    }

    if (parent) {
        // Filter on parent
        var source = S3.gis.url + '/search.json?filter=~&field=name&level=L' + level + '&parent=' + parent;
    } else if (grandparent) {
        // Filter on children (slower)
        var source = S3.gis.url + '/search.json?filter=~&field=name&level=L' + level + '&children=' + grandparent;
    } else {
        // No Filter possible beyond Level
        var source = S3.gis.url + '/search.json?filter=~&field=name&level=L' + level;
    }
    return source;
}

function s3_gis_ac_set_search_source() {
    // Set the source for a Search Autocomplete

    // @ToDo: Read Hierarchical Filters

    // Search all specific locations
    var source = S3.gis.url + '/search.json?filter=~&field=name&field2=addr_street&level=nullnone';

    return source;
}

function s3_gis_ac_search_selected(location) {
    // Autocomplete Search Results has been selected

    // Empty the old hierarchy
    var i;
    for (i = 0; i <= 5; i++) {
        $('#gis_location_L' + i + '_search').val('');
        $('#gis_location_L' + i + '_label__row').hide();
        $('#gis_location_L' + i + '_search__row').hide();
    }

    // Display the details
    var path = location.path;
    var parent = location.parent;
    if (path) {
        // Lookup the hierarchies
        var suffix = path.toString().length + 1;
        var ancestors = path.slice(0, suffix).split('/');
        var queries = ancestors.length - 1
        if (queries == 0) {
            $('#gis_location_search_throbber').hide();
            // Display the Select Button
            $( '#gis_location_search_select-btn' ).removeClass('hide').show();
        } else {
            for (i = 0; i <= queries; i++) {
                if (i == (queries - 1)) {
                    s3_gis_search_hierarchy(ancestors[i], false, true);
                } else {
                    s3_gis_search_hierarchy(ancestors[i], false, false);
                }
            }
        }
    } else if (parent) {
        // Lookup the parent
        s3_gis_search_hierarchy(parent, true, true);
    }
    if (location.name) {
        $('#gis_location_name_label__row').removeClass('hide').show();
        $('#gis_location_name_search').val(location.name);
        $('#gis_location_name_search__row').removeClass('hide').show();
    } else {
        $('#gis_location_name_label__row').hide();
        $('#gis_location_name_search').val('');
        $('#gis_location_name_search__row').hide();
    }
    if (location.addr_street) {
        $('#gis_location_street_label__row').removeClass('hide').show();
        $('#gis_location_street_search').val(location.addr_street);
        $('#gis_location_street_search__row').removeClass('hide').show();
    } else {
        $('#gis_location_street_label__row').hide();
        $('#gis_location_street_search').val('');
        $('#gis_location_street_search__row').hide();
    }
    if (location.addr_postcode) {
        $('#gis_location_postcode_label__row').removeClass('hide').show();
        $('#gis_location_postcode_search').val(location.addr_postcode);
        $('#gis_location_postcode_search__row').removeClass('hide').show();
    } else {
        $('#gis_location_postcode_label__row').hide();
        $('#gis_location_postcode_search').val('');
        $('#gis_location_postcode_search__row').hide();
    }
    if ( !S3.gis.no_latlon ) {
        if (location.lat) {
            $('#gis_location_lat_label__row').removeClass('hide').show();
            $('#gis_location_lat_search').val(location.lat);
            $('#gis_location_lat_search__row').removeClass('hide').show();
        } else {
            $('#gis_location_lat_label__row').hide();
            $('#gis_location_lat_search').val('');
            $('#gis_location_lat_search__row').hide();
        }
        if (location.lon) {
            $('#gis_location_lon_label__row').removeClass('hide').show();
            $('#gis_location_lon_search').val(location.lon);
            $('#gis_location_lon_search__row').removeClass('hide').show();
        } else {
            $('#gis_location_lon_label__row').hide();
            $('#gis_location_lon_search').val('');
            $('#gis_location_lon_search__row').hide();
        }
    }

    // Store the ID & UUID
    $('body').data('id', location.id);
    //$('body').data('uuid', location.uuid);

    if (!path && !parent) {
        // Display the Select Button
        $('#gis_location_search_select-btn').removeClass('hide').show();
    }
}

function s3_gis_lat_lon_converter() {
    // Set up the lat_lon converter
    var nanError = S3.i18n.gis_only_numbers,
        rangeError = S3.i18n.gis_range_error;

    function isNum(n) {
      return !isNaN(parseFloat(n)) && isFinite(n);
    }

    function get_wrap(e) {
        return e.parents('.gis_coord_wrap').eq(0);
    }

    function set($e) {
        return function (v) {
            // clear and focus or set a field
            $e.val(v||'')
            if (typeof(v) == 'undefined') $e.focus();
        }
    }

    function get_dms(dec) {
        var d = Math.abs(dec),
            m = (d - parseInt(d)) * 60;

        // Stop integer values of m from being approximated
        if (Math.abs(m - Math.round(m)) < 1e-10) {
            m = Math.round(m);
            s = 0;
        } else {
            var s = (m - parseInt(m)) * 60;

            // Stop integer values of s from being approximated
            if (Math.abs(s - Math.round(s)) < 1e-10)
                s = Math.round(s)
        }

        return { d: parseInt(dec),
                 m: parseInt(m),
                 s: s
               }
    }

    function get_float(d, m, s) {
        return (d < 0 ? -1 : 1) * 
                (Math.abs(d) +
                 m / 60 +
                 s / 3600);
    }

    function to_decimal(wrap) {

        var d = $('.degrees', wrap).val() || 0,
            m = $('.minutes', wrap).val() || 0,
            s = $('.seconds', wrap).val() || 0,

            set_d = set($('.degrees', wrap)),
            set_m = set($('.minutes', wrap)),
            set_s = set($('.seconds', wrap)),
            set_dec = set($('.decimal', wrap)),

            isLat = $('.decimal', wrap).attr('id') == 'gis_location_lat';

        // validate degrees
        if (!isNum(d)) {
            alert(nanError.degrees);
            set_d();
            return;
        }

        d = Number(d);
        if (Math.abs(d) > (isLat ? 90 : 180)) {
            alert(rangeError.degrees[isLat? 'lat' : 'lon']);
            set_d();
            return;
        }

        // validate minutes
        if (!isNum(m)) {
            alert(nanError.minutes);
            set_m();
            return;
        }

        m = Math.abs(m);
        if (m > 60) {
            alert(rangeError.minutes);
            set_m();
            return;
        }

        // validate seconds
        if (!isNum(s)) {
            alert(nanError.seconds);
            set_s();
            return;
        }

        s = Math.abs(s);
        if (s >= 60) {
            alert(rangeError.seconds);
            set_s();
            return;
        }

        // Normalize all the values
        // Degrees and Minutes as integers
        var decimal = get_float(d, m, s);

        if (Math.abs(decimal) > (isLat ? 90 : 180)) {
            alert(rangeError.decimal[isLat? 'lat' : 'lon']);
            return;
        }

        var dms = get_dms(decimal);

        set_dec('' + decimal);
        set_d(dms.d || '0');
        set_m(dms.m || '0');
        set_s(dms.s || '0');
    }

    $('.gis_coord_dms input').blur(function () {
        to_decimal(get_wrap($(this)));
    }).keypress(function(e) {
        if (e.which == 13) e.preventDefault();
    });

    function to_dms(wrap) {
        var field = $('.decimal', wrap),
            dec = field.val(),
            isLat = $('.decimal', wrap).attr('id') == 'gis_location_lat';
        if (dec == '') return;
        if (!isNum(dec)) {
            alert(nanError.decimal);
            field.val('').focus();
            return;
        }
        dec = Number(dec);
        if (Math.abs(dec) > (isLat ? 90 : 180)) {
            alert(rangeError.decimal[isLat? 'lat' : 'lon']);
            field.focus();
            return;
        }
        var dms = get_dms(dec);
        $('.degrees', wrap).val(dms.d || '0');
        $('.minutes', wrap).val(dms.m || '0');
        $('.seconds', wrap).val(dms.s || '0');
    }

    $('.gis_coord_decimal input').blur(function () {
        to_dms(get_wrap($(this)));
    }).keypress(function(e) {
        if (e.which == 13) e.preventDefault();
    });

    $('.gis_coord_switch_dms').click(function (evt) {
        $('.gis_coord_dms').show();
        $('.gis_coord_decimal').hide();
        $('.gis_coord_wrap').each(function () {
            to_dms($(this));
        });
        evt.preventDefault();
    });

    $('.gis_coord_switch_decimal').click(function (evt) {
        $('.gis_coord_decimal').show();
        $('.gis_coord_dms').hide();
        $('.gis_coord_wrap').each(function () {
            to_decimal($(this));
        });
        evt.preventDefault();
    });

    // Initially fill up the dms boxes
    $('.gis_coord_wrap').each(function () {
        to_dms($(this));
    });
}

function s3_gis_search_hierarchy(location_id, recursive, last) {
    // Do an async lookup of Hierarchy when a specific value is found
    // Recursive needed when we just have Parent.
    // Path doesn't need this

    $('#gis_location_search_throbber').removeClass('hide').show();

    var url = S3.gis.url + '/' + location_id + '.json';
    $.ajax({
        async: true,
        url: url,
        dataType: 'json',
        success: function(data) {
            if (data[0].id == location_id) {
                // Parse the new location
                var name = data[0].name;
                var level = data[0].level;
                var parent = data[0].parent;

                // Store the ID for later retrieval (in case we 'Select' this Location)
                $('body').data(level, location_id);

                // Display the details for this level
                $('#gis_location_' + level + '_search').val(name);
                $('#gis_location_' + level + '_label__row').removeClass('hide').show();
                $('#gis_location_' + level + '_search__row').removeClass('hide').show();
                if (recursive && parent) {
                    s3_gis_search_hierarchy(parent, true, true);
                } else if (last) {
                    $('#gis_location_search_throbber').hide();
                    // Display the Select Button
                    $('#gis_location_search_select-btn').removeClass('hide').show();
                }
            }
        }
    });
}

function s3_gis_show_level(level) {
    // Unhide field & label
    $('#gis_location_L' + level + '_label__row').removeClass('hide').show();
    $('#gis_location_L' + level + '__row').removeClass('hide').show();
}

function s3_gis_hide_level(level) {
    // Hide field & label
    $('#gis_location_L' + level + '_label__row').hide();
    $('#gis_location_L' + level + '__row').hide();
}

function s3_gis_l0_select() {
    // L0 dropdown has been selected

    var L0 = $('#gis_location_L0').val();
    var url = S3.gis.url.replace('gis/location', 'gis/l0') + '/' + L0;
    $.ajax({
        async: true,
        url: url,
        dataType: 'json',
        success: function(data) {
            if (data.id == L0) {
                // Store the code (for the Geocoder)
                S3.gis.country = data.code
                // Read which hierarchy levels we have & their labels
                for (level = 1; level < 6; level++) {
                    var _level = 'L' + level;
                    if (data[_level]) {
                        // Replace the label
                        $('#gis_location_' + _level + '_label__row label').text(data[_level] + ':');
                        s3_gis_show_level(level);
                        // Replace the Help Tip
                        var tooltip = $('#gis_location_' + _level + '__row div.tooltip');
                        var old_title = tooltip.attr('title');
                        var parts = old_title.split('|');
                        var newtitle = data[_level] + '|' + parts[1]+ '|' + parts[2];
                        tooltip.attr('title', newtitle);
                        // Re-apply Cluetip so that it sees the new value
                        tooltip.cluetip({activation: 'hover', sticky: false, splitTitle: '|'});
                    } else {
                        s3_gis_hide_level(level);
                    }
                }
                if ( !S3.gis.no_map ) {
                    // Zoom the Map?
                    var lat = $('#gis_location_lat').val();
                    var lon = $('#gis_location_lon').val();
                    if (!lat && !lon) {
                        // If no LatLon already set then Zoom the map to the appropriate location
                        var left = data.lon_min;
                        var bottom = data.lat_min;
                        var right = data.lon_max;
                        var top = data.lat_max;
                        if (left && bottom && right && top) {
                            // If we have Bounds then Zoom to the Bounds
                            s3_gis_zoomMap(left, bottom, right, top);
                        } else {
                            lat = data.lat;
                            lon = data.lon;
                            if (lat && lon) {
                                // Otherwise, simply Center the map
                                var newPoint = new OpenLayers.LonLat(lon, lat);
                                newPoint.transform(S3.gis.proj4326, S3.gis.projection_current);
                                if (S3.gis.mapWin.rendered) {
                                    // Map has been opened, so center directly
                                    map.setCenter(newPoint);
                                } else {
                                    // Map hasn't yet been opened, so change the mapPanel ready for when it is
                                    S3.gis.mapPanel.center = newPoint;
                                }
                            }
                        }
                    }
                }
                // @ToDo: Are we operating in mode strict?
                //        - these will need adding to the output if we need them
                // Store in global var?
                //data.strict_hierarchy;
                //data.location_parent_required;
            }
        }
    });

    // Set the Autocompletes' filters
    $('#gis_location_L1_ac').autocomplete('option', 'source', s3_gis_ac_set_source(1));
    $('#gis_location_L2_ac').autocomplete('option', 'source', s3_gis_ac_set_source(2));
    $('#gis_location_L3_ac').autocomplete('option', 'source', s3_gis_ac_set_source(3));
    $('#gis_location_L4_ac').autocomplete('option', 'source', s3_gis_ac_set_source(4));
    $('#gis_location_L5_ac').autocomplete('option', 'source', s3_gis_ac_set_source(5));
}


function s3_gis_zoomMap(left, bottom, right, top) {
    // Zoom the Map to the specified bounds
    if (S3.gis.mapWin.rendered) {
        // For some reason the reprojection shouldn't be done if the Map hasn't been opened yet
        var southWest = new OpenLayers.LonLat(left, bottom);
        var northEast = new OpenLayers.LonLat(right, top);
        southWest.transform(S3.gis.proj4326, S3.gis.projection_current);
        northEast.transform(S3.gis.proj4326, S3.gis.projection_current);
        left = southWest.lon;
        bottom = southWest.lat;
        right = northEast.lon;
        top = northEast.lat;
    }
    var bounds = OpenLayers.Bounds.fromArray([left, bottom, right, top]);
    var newPoint = bounds.getCenterLonLat();
    var zoom = map.getZoomForExtent(bounds, true);
    if (zoom > 16) {
        // Stop us being too zoomed in
        zoom = 16;
    }
    if (S3.gis.mapWin.rendered) {
        // Map has been opened, so zoom directly
        map.setCenter(newPoint);
        map.zoomTo(zoom);
    } else {
        // Map hasn't yet been opened, so change the mapPanel ready for when it is
        newPoint.transform(S3.gis.proj4326, S3.gis.projection_current);
        S3.gis.mapPanel.center = newPoint;
        S3.gis.mapPanel.zoom = zoom;
    }
}

// Hide selector
function s3_gis_hide_selector() {
    // Hide all rows with the locselect class
    $('.locselect').hide();
}
function s3_gis_hide_selector_all() {
    // Hide the label row
    $('#gis_location_label_row').hide();
    // Hide the subheadings
    // @ToDo: We may need to identify these ones separately
    $('.subheading').hide();
    // Hide the fields
    s3_gis_hide_selector();
}
function s3_gis_show_selector() {
    // Show the label row
    $('#gis_location_label_row').show();
    // Show the subheadings
    // @ToDo: We may need to identify these ones separately
    $('.subheading').show();
    // Open the Create Tab
    s3_gis_show_tab('add');
}

// Tabs
function s3_gis_show_tab(tab) {
    // Show the Tabs
    $('#gis_location_tabs_row').removeClass('hide').show();
    // Open the relevant Tab contents
    if (tab == 'search') {
        s3_gis_search_tab();
    } else if (tab == 'add') {
        s3_gis_add_tab();
    } else if (tab == 'edit') {
        s3_gis_edit_tab();
    } else if (tab == 'view') {
        s3_gis_view_tab();
    } else {
        // Unknown Tab
        return false;
    }
}

function s3_gis_search_tab() {
    // 'Select Existing Location' tab has been selected

    // Hide the Add rows
    $('#gis_location_L0_label__row').hide();
    $('#gis_location_L0__row').hide();
    $('#gis_location_name_label__row').hide();
    $('#gis_location_name__row').hide();
    $('#gis_location_street_label__row').hide();
    $('#gis_location_street__row').hide();
    $('#gis_location_postcode_label__row').hide();
    $('#gis_location_postcode__row').hide();
    $('#gis_location_L1_label__row').hide();
    $('#gis_location_L1__row').hide();
    $('#gis_location_L2_label__row').hide();
    $('#gis_location_L2__row').hide();
    $('#gis_location_L3_label__row').hide();
    $('#gis_location_L3__row').hide();
    $('#gis_location_L4_label__row').hide();
    $('#gis_location_L4__row').hide();
    $('#gis_location_L5_label__row').hide();
    $('#gis_location_L5__row').hide();
    $('#gis_location_lat_label__row').hide();
    $('#gis_location_lat__row').hide();
    $('#gis_location_lon_label__row').hide();
    $('#gis_location_lon__row').hide();

    // Show the Search rows
    $('#gis_location_search_label__row').removeClass('hide').show();
    $('#gis_location_search__row').removeClass('hide').show();

    // Change the label of the Map button
    $('#gis_location_map-btn').html(S3.i18n.gis_view_on_map);
    // Hide it
    $('#gis_location_map_button_row').hide();

    // Set the Classes on the tabs
    $('#gis_loc_add_tab').removeClass('tab_here').addClass('tab_other');
    $('#gis_loc_search_tab').removeClass('tab_last').addClass('tab_here');

    // Focus in the Search box
    $('#gis_location_search_ac').focus();
}

function s3_gis_add_tab() {
    // 'Create New Location' tab has been selected

    // Hide the Search rows
    s3_gis_hide_search_fields();

    // Show the Add rows
    $('#gis_location_L0_label__row').show();
    $('#gis_location_L0__row').show();
    $('#gis_location_name_label__row').show();
    $('#gis_location_name__row').show();
    $('#gis_location_street_label__row').show();
    $('#gis_location_street__row').show();
    $('#gis_location_postcode_label__row').show();
    $('#gis_location_postcode__row').show();
    // Show Lx rows which are appropriate to this Region
    if ( !$('#gis_location_L1_ac').hasClass('hide') ) {
        $('#gis_location_L1_label__row').show();
        $('#gis_location_L1__row').show();
    } else {
        $('#gis_location_L1_label__row').hide();
        $('#gis_location_L1__row').hide();
    }
    if ( !$('#gis_location_L2_ac').hasClass('hide') ) {
        $('#gis_location_L2_label__row').show();
        $('#gis_location_L2__row').show();
    } else {
        $('#gis_location_L2_label__row').hide();
        $('#gis_location_L2__row').hide();
    }
    if ( !$('#gis_location_L3_ac').hasClass('hide') ) {
        $('#gis_location_L3_label__row').show();
        $('#gis_location_L3__row').show();
    } else {
        $('#gis_location_L3_label__row').hide();
        $('#gis_location_L3__row').hide();
    }
    if ( !$('#gis_location_L4_ac').hasClass('hide') ) {
        $('#gis_location_L4_label__row').show();
        $('#gis_location_L4__row').show();
    } else {
        $('#gis_location_L4_label__row').hide();
        $('#gis_location_L4__row').hide();
    }
     if ( !$('#gis_location_L5_ac').hasClass('hide') ) {
        $('#gis_location_L5_label__row').show();
        $('#gis_location_L5__row').show();
    } else {
        $('#gis_location_L5_label__row').hide();
        $('#gis_location_L5__row').hide();
    }
    if ( !S3.gis.no_latlon ) {
        $('#gis_location_lat_label__row').show();
        $('#gis_location_lat__row').show();
        $('#gis_location_lon_label__row').show();
        $('#gis_location_lon__row').show();
    }

    // Change the label of the Map button
    $('#gis_location_map-btn').html( S3.i18n.gis_place_on_map );
    // Display it
    $('#gis_location_map_button_row').show();

    // Set the Classes on the tabs
    $('#gis_loc_add_tab').removeClass('tab_other').addClass('tab_here');
    $('#gis_loc_search_tab').removeClass('tab_here').addClass('tab_last');

    // Hide the Select Button (in case we return to the Search page)
    $( '#gis_location_search_select-btn' ).hide();
}

function s3_gis_edit_tab() {
    // 'Edit Location Details' tab has been selected

    // @ToDo: Display warning about this location possibly being a shared location

    // Remove the Disabled Status from the fields
    $('#gis_location_L0').removeAttr('disabled');
    $('#gis_location_name').removeAttr('disabled');
    $('#gis_location_street').removeAttr('disabled');
    $('#gis_location_postcode').removeAttr('disabled');
    $('#gis_location_lat').removeAttr('disabled');
    $('#gis_location_lon').removeAttr('disabled');
    $('#gis_location_L5_ac').removeAttr('disabled');
    $('#gis_location_L4_ac').removeAttr('disabled');
    $('#gis_location_L3_ac').removeAttr('disabled');
    $('#gis_location_L2_ac').removeAttr('disabled');
    $('#gis_location_L1_ac').removeAttr('disabled');

    // Unhide all fields
    $('#gis_location_L0_label__row').removeClass('hide').show();
    $('#gis_location_L0__row').removeClass('hide').show();
    $('#gis_location_name_label__row').removeClass('hide').show();
    $('#gis_location_name__row').removeClass('hide').show();
    $('#gis_location_street_label__row').removeClass('hide').show();
    $('#gis_location_street__row').removeClass('hide').show();
    $('#gis_location_postcode_label__row').removeClass('hide').show();
    $('#gis_location_postcode__row').removeClass('hide').show();
    if ( !$('#gis_location_L5_ac').hasClass('hide') ) {
        $('#gis_location_L5_label__row').removeClass('hide').show();
        $('#gis_location_L5__row').removeClass('hide').show();
    } else {
        $('#gis_location_L5_label__row').hide();
        $('#gis_location_L5__row').hide();
    }
    if ( !$('#gis_location_L4_ac').hasClass('hide') ) {
        $('#gis_location_L4_label__row').removeClass('hide').show();
        $('#gis_location_L4__row').removeClass('hide').show();
    } else {
        $('#gis_location_L4_label__row').hide();
        $('#gis_location_L4__row').hide();
    }
    if ( !$('#gis_location_L3_ac').hasClass('hide') ) {
        $('#gis_location_L3_label__row').removeClass('hide').show();
        $('#gis_location_L3__row').removeClass('hide').show();
    } else {
        $('#gis_location_L3_label__row').hide();
        $('#gis_location_L3__row').hide();
    }
    if ( !$('#gis_location_L2_ac').hasClass('hide') ) {
        $('#gis_location_L2_label__row').removeClass('hide').show();
        $('#gis_location_L2__row').removeClass('hide').show();
    } else {
        $('#gis_location_L2_label__row').hide();
        $('#gis_location_L2__row').hide();
    }
    if ( !$('#gis_location_L1_ac').hasClass('hide') ) {
        $('#gis_location_L1_label__row').removeClass('hide').show();
        $('#gis_location_L1__row').removeClass('hide').show();
    } else {
        $('#gis_location_L1_label__row').hide();
        $('#gis_location_L1__row').hide();
    }
    if ( !S3.gis.no_latlon ) {
        $('#gis_location_lat_label__row').removeClass('hide').show();
        $('#gis_location_lat__row').removeClass('hide').show();
        $('#gis_location_lon_label__row').removeClass('hide').show();
        $('#gis_location_lon__row').removeClass('hide').show();
    }
    $('#gis_location_wkt_label__row').removeClass('hide').show();
    $('#gis_location_wkt__row').removeClass('hide').show();

    // Change the label of the Map button
    $('#gis_location_map-btn').html( S3.i18n.gis_place_on_map );
    // Display it
    $('#gis_location_map_button_row').show();

    // Set the Classes on the tabs
    $('#gis_loc_edit_tab').removeClass('tab_other').addClass('tab_here');
    $('#gis_loc_view_tab').removeClass('tab_here').addClass('tab_last');
}

function s3_gis_view_tab() {
    // 'View Location Details' tab has been selected
    // or we have Selected a Search result

    // Does this act like a Cancel to the Edit Location?
    // i.e. should we restore previous values.
    // No?

    // Hide the fields without data
    // Add the Disabled Status to the fields with data
    var L0 = $('#gis_location_L0').val();
    if (L0 == '') {
        $('#gis_location_L0_label__row').hide();
        $('#gis_location_L0__row').hide();
    } else {
        $('#gis_location_L0').attr('disabled', true);
        $('#gis_location_L0__row').show();
    }
    var name = $('#gis_location_name').val();
    if (name == '') {
        $('#gis_location_name_label__row').hide();
        $('#gis_location_name__row').hide();
    } else {
        $('#gis_location_name').attr('disabled', true);
        $('#gis_location_name__row').show();
    }
    var street = $('#gis_location_street').val();
    if (street == '') {
        $('#gis_location_street_label__row').hide();
        $('#gis_location_street__row').hide();
    } else {
        $('#gis_location_street').attr('disabled', true);
        $('#gis_location_street__row').show();
    }
    var postcode = $('#gis_location_postcode').val();
    if (postcode == '') {
        $('#gis_location_postcode_label__row').hide();
        $('#gis_location_postcode__row').hide();
    } else {
        $('#gis_location_postcode').attr('disabled', true);
        $('#gis_location_postcode__row').show();
    }
    if ( !S3.gis.no_latlon ) {
        var lat = $('#gis_location_lat').val();
        if (lat == '') {
            $('#gis_location_lat_label__row').hide();
            $('#gis_location_lat__row').hide();
        } else {
            $('#gis_location_lat').attr('disabled', true);
            $('#gis_location_lat__row').show();
        }
        var lon = $('#gis_location_lon').val();
        if (lon == '') {
            $('#gis_location_lon_label__row').hide();
            $('#gis_location_lon__row').hide();
        } else {
            $('#gis_location_lon').attr('disabled', true);
            $('#gis_location_lon__row').show();
        }
    }
    var wkt = $('#gis_location_wkt').val();
    if (wkt == '') {
        $('#gis_location_wkt_label__row').hide();
        $('#gis_location_wkt__row').hide();
    } else {
        $('#gis_location_wkt_label__row').show();
        $('#gis_location_wkt').attr('disabled', true);
        $('#gis_location_wkt__row').show();
    }
    var L5 = $('#gis_location_L5_ac').val();
    if (L5 == '') {
        $('#gis_location_L5_label__row').hide();
        $('#gis_location_L5__row').hide();
    } else if ( !$('#gis_location_L5_ac').hasClass('hide') ) {
        $('#gis_location_L5_ac').attr('disabled', true);
        $('#gis_location_L5__row').show();
    }
    var L4 = $('#gis_location_L4_ac').val();
    if (L4 == '') {
        $('#gis_location_L4_label__row').hide();
        $('#gis_location_L4__row').hide();
    } else if ( !$('#gis_location_L4_ac').hasClass('hide') ) {
        $('#gis_location_L4_ac').attr('disabled', true);
        $('#gis_location_L4__row').show();
    }
    var L3 = $('#gis_location_L3_ac').val();
    if (L3 == '') {
        $('#gis_location_L3_label__row').hide();
        $('#gis_location_L3__row').hide();
    } else if ( !$('#gis_location_L3_ac').hasClass('hide') ) {
        $('#gis_location_L3_ac').attr('disabled', true);
        $('#gis_location_L3__row').show();
    }
    var L2 = $('#gis_location_L2_ac').val();
    if (L2 == '') {
        $('#gis_location_L2_label__row').hide();
        $('#gis_location_L2__row').hide();
    } else if ( !$('#gis_location_L2_ac').hasClass('hide') ) {
        $('#gis_location_L2_ac').attr('disabled', true);
        $('#gis_location_L2__row').show();
    }
    var L1 = $('#gis_location_L1_ac').val();
    if (L1 == '') {
        $('#gis_location_L1_label__row').hide();
        $('#gis_location_L1__row').hide();
    } else if ( !$('#gis_location_L1_ac').hasClass('hide') ) {
        $('#gis_location_L1_ac').attr('disabled', true);
        $('#gis_location_L1__row').show();
    }

    // Change the label of the Map button
    $('#gis_location_map-btn').html( S3.i18n.gis_view_on_map );
    // Display it
    $('#gis_location_map_button_row').show();

    // Set the Classes on the tabs
    $('#gis_loc_view_tab').removeClass('tab_other').addClass('tab_here');
    $('#gis_loc_edit_tab').removeClass('tab_here').addClass('tab_last');
}

function s3_gis_select_search_result(id, uuid) {
    // 'Select This Location' button has been pressed

    // Set the real location_id
    var id = $('body').data('id');
    $('#' + S3.gis.location_id).val(id);

    // Set the global var
    //S3.gis.uuid = $('body').data('uuid');

    // Convert to an Update-style form
    // Hide the create tabs
    $('#gis_loc_add_tab').hide();
    $('#gis_loc_search_tab').hide();
    // Show the update tabs
    $('#gis_loc_view_tab').removeClass('hide').show();
    $('#gis_loc_edit_tab').removeClass('hide').show();

    // Hide the Search rows
    s3_gis_hide_search_fields();

    // Copy the results from the Search fields to the View fields
    var name = $('#gis_location_name_search').val();
    $('#gis_location_name').val(name);
    var street = $('#gis_location_street_search').val();
    $('#gis_location_street').val(street);
    var postcode = $('#gis_location_postcode_search').val();
    $('#gis_location_postcode').val(postcode);
    var lat = $('#gis_location_lat_search').val();
    $('#gis_location_lat').val(lat);
    var lon = $('#gis_location_lon_search').val();
    $('#gis_location_lon').val(lon);
    var L0 = $('body').data('L0');
    $('#gis_location_L0').val(L0);
    var L1 = $('body').data('L1');
    $('#gis_location_L1').val(L1);
    var L2 = $('body').data('L2');
    $('#gis_location_L2').val(L2);
    var L3 = $('body').data('L3');
    $('#gis_location_L3').val(L3);
    var L4 = $('body').data('L4');
    $('#gis_location_L4').val(L4);
    var L5 = $('body').data('L5');
    $('#gis_location_L5' ).val(L5);
    var L1_text = $('#gis_location_L1_search').val();
    $('#gis_location_L1_ac' ).val(L1_text);
    var L2_text = $('#gis_location_L2_search').val();
    $('#gis_location_L2_ac').val(L2_text);
    var L3_text = $('#gis_location_L3_search').val();
    $('#gis_location_L3_ac').val(L3_text);
    var L4_text = $('#gis_location_L4_search').val();
    $('#gis_location_L4_ac').val(L4_text);
    var L5_text = $('#gis_location_L5_search').val();
    $('#gis_location_L5_ac').val(L5_text);

    // Open the View tab
    s3_gis_view_tab();
}

function s3_gis_hide_search_fields() {
    // Hide the Search rows
    $('#gis_location_search_label__row').hide();
    $('#gis_location_search__row').hide();
    $('#gis_location_name_search__row').hide();
    $('#gis_location_street_search__row').hide();
    $('#gis_location_postcode_search__row').hide();
    $('#gis_location_lat_search__row').hide();
    $('#gis_location_lon_search__row').hide();
    $('#gis_location_L0_search__row').hide();
    $('#gis_location_L1_search__row').hide();
    $('#gis_location_L2_search__row').hide();
    $('#gis_location_L3_search__row').hide();
    $('#gis_location_L4_search__row').hide();
    $('#gis_location_L5_search__row').hide();
}

// Geocoder
function s3_gis_loadGoogle() {
    var script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = 'http://maps.google.com/maps/api/js?v=3.6&sensor=false&callback=s3_gis_initGeocoder';
    document.body.appendChild(script);
}
function s3_gis_initGeocoder() {
    // Do Geocoder lookups if changes made to Street Address, Postcode & L3
    $('#gis_location_street').blur( function() {
        s3_gis_geocode();
    });
    $('#gis_location_postcode').blur( function() {
        s3_gis_geocode();
    });
    $('#gis_location_L3_ac').blur( function() {
        s3_gis_geocode();
    });
}
function s3_gis_geocode() {
    // Address has been changed - do a Geocoder lookup
    var lat = $('#gis_location_lat').val();
    var lon = $('#gis_location_lon').val();
    // Only do the Geocoder lookup if we don't already have LatLon
    if (!lat && !lon) {
        // Read the Street Address
        var address = $('#gis_location_street').val();
        if (address) {
            // Strip the leading digits as they cause NO_RESULTS
            var start = address.search(/[A-z]/);
            address = address.substr(start);
        }
        // Read Postcode to be able to fine-tune the results
        var postcode = $('#gis_location_postcode').val();
        if (postcode) {
            address += ' ' + postcode
        }
        // Read any Lx set to be able to fine-tune the results
        var L5 = $('#gis_location_L5_ac').val();
        if (L5) {
            address += ' ' + L5
        }
        var L4 = $('#gis_location_L4_ac').val();
        if (L4) {
            address += ' ' + L4
        }
        var L3 = $('#gis_location_L3_ac').val();
        if (L3) {
            address += ' ' + L3
        }
        var L2 = $('#gis_location_L2_ac').val();
        if (L2) {
            address += ' ' + L2
        }
        var L1 = $('#gis_location_L1_ac').val();
        if (L1) {
            address += ' ' + L1
        }
        // Build the Query
        var query = { 'address': address }
        // Restrict results to the country if we have it available.
        if (S3.gis.country) {
            query['region'] = S3.gis.country;
        }
        // @ToDo: Restrict results to the bounds if we have them available.
        //if () {
        //    // Convert to LatLngBounds
        //    var myLatLngBounds;
        //    query['bounds'] = myLatLngBounds;
        //}
        // Query the Geocoder service
        var geocoder = new google.maps.Geocoder();
        geocoder.geocode( query, function(results, status) {
            if (status == google.maps.GeocoderStatus.OK) {

                // Parse the returned Location
                var myLatLng = results[0].geometry.location;
                // Convert to OpenLayers format
                var lat = myLatLng.lat();
                var lon = myLatLng.lng();
                var newPoint = new OpenLayers.LonLat(lon, lat);

                var myLatLngBounds = results[0].geometry.viewport;
                if (myLatLngBounds) {
                    // Zoom to the Viewport (Bounds)
                    var northEast = myLatLngBounds.getNorthEast();
                    var southWest = myLatLngBounds.getSouthWest();
                    var left = southWest.lng();
                    var bottom = southWest.lat();
                    var right = northEast.lng();
                    var top = northEast.lat();
                    s3_gis_zoomMap(left, bottom, right, top);
                } else if (S3.gis.mapWin.rendered) {
                    // Map has been opened, so center directly
                    newPoint.transform(S3.gis.proj4326, S3.gis.projection_current);
                    map.setCenter(newPoint);
                } else {
                    // Map hasn't yet been opened, so change the mapPanel ready for when it is
                    S3.gis.mapPanel.center = newPoint;
                }

                // @ToDo: Set the Marker to the center of this viewport?
                // Better to let the user do this manually?
                //var marker = new google.maps.Marker({
                //    map: map,
                //    position: results[0].geometry.location
                //});

                // @ToDo: Populate the Lx Hierarchy
                //var L1 = $('#gis_location_L1_ac').val();
                //if (!L1) {
                    //results[0].address_components administrative_area_level_1
                //}
                // results[0].address_components postal_code

            } else {
                // @ToDo: Visible notification?
                s3_debug('Geocode was not successful for the following reason', status);
            }
        });
    }
}

// Save
function s3_gis_save_locations() {
    // This is done server-side via the IS_LOCATION_SELECTOR validator
    // What we need to do here is prepare for this

    // Specific Location
    var id = $( '#' + S3.gis.location_id ).val();
    if (!id) {
        // Create form: we need to populate the location_id field in order to trigger validation
        $( '#' + S3.gis.location_id ).val('dummy')
    }
    if (S3.gis.site) {
        // For Sites, we default the Building Name to the same as the Site
        var namefield = '#' + S3.gis.site + '_name';
        var name = $( namefield ).val();
        if (!name) {
            // Site Name is required
            if (undefined == $('#name__error').val()) {
                // Prompt the user for a name
                $(namefield).after('<div id="name__error" class="error" style="display: block;">' + S3.i18n.gis_name_required + '</div>');
            }
            // Move focus to this field
            $(namefield).focus();
            if (S3.navigate_away_confirm) {
                // Reset the Navigation protection
                S3SetNavigateAwayConfirm()
            }
            // Prevent the Form's save from continuing
            return false;
        } else if (!$( '#gis_location_name' ).val()) {
            // Copy from the Site Name
            $( '#gis_location_name' ).val(name);
        }
    }

    // L0: Mandatory field if there is any other data
    var L1 = $('#gis_location_L1').val();
    var L2 = $('#gis_location_L2').val();
    var L3 = $('#gis_location_L3').val();
    var L4 = $('#gis_location_L4').val();
    var L5 = $('#gis_location_L5').val();
    if ($('#gis_location_L0').val()) {
        // pass
    } else {
        // Check if there is other data to save
        if (S3.gis.site) {
            // Don't include the name in the check for sites, since these have the name auto-populated
            var name = '';
        } else {
            var name = $('#gis_location_name').val();
        }
        var street = $('#gis_location_street').val();
        var postcode = $('#gis_location_postcode').val();
        var lat = $('#gis_location_lat').val();
        var lon = $('#gis_location_lon').val();
        if (L1 || L2 || L3 || L4 || L5 || name || street || postcode || lat || lon) {
            if (undefined == $('#country__error').val()) {
                // Prompt the user for a country
                $('#gis_location_L0').after('<div id="country__error" class="error" style="display: block;">' + S3.i18n.gis_country_required + '</div>');
            }
            // Move focus to this field
            $('#gis_location_L0').focus();
            if (S3.navigate_away_confirm) {
                // Reset the Navigation protection
                S3SetNavigateAwayConfirm()
            }
            // Prevent the Form's save from continuing
            return false;
        }
    }

    // Lx hierarchy
    // If there is no value in the ID field but there is text in the AC then
    // copy the text to the ID field to have it visible to the Validator
    // L1
    if (L1) {
        // pass
    } else {
         L1 = $('#gis_location_L1_ac').val();
         if (L1) {
            $('#gis_location_L1').val(L1)
         }
    }
    // L2
    if (L2) {
        // pass
    } else {
         L2 = $('#gis_location_L2_ac').val();
         if (L2) {
            $('#gis_location_L2').val(L2)
         }
    }
    // L3
    if (L3) {
        // pass
    } else {
         L3 = $('#gis_location_L3_ac').val();
         if (L3) {
            $('#gis_location_L3').val(L3)
         }
    }
    // L4
    if (L4) {
        // pass
    } else {
         L4 = $('#gis_location_L4_ac').val();
         if (L4) {
            $('#gis_location_L4').val(L4)
         }
    }
    // L5
    if (L5) {
        // pass
    } else {
         L5 = $('#gis_location_L5_ac').val();
         if (L5) {
            $('#gis_location_L5').val(L5)
         }
    }

    // Ensure that all fields aren't disabled (to avoid wiping their contents)
    $('#gis_location_L0').removeAttr('disabled');
    $('#gis_location_name').removeAttr('disabled');
    $('#gis_location_street').removeAttr('disabled');
    $('#gis_location_postcode').removeAttr('disabled');
    $('#gis_location_lat').removeAttr('disabled');
    $('#gis_location_lon').removeAttr('disabled');

    // Allow the Form's Save to continue
    return true;
}
