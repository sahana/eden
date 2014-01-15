// Static code to support GIS Feature CRUD

(function() {
    var s3_gis_feature_crud = function(feature_type) {
        if (feature_type === '') {
            // Pass
        } else if (feature_type == 1) {
            // Point
            // Hide the WKT input
            $('#gis_location_wkt__row').hide();
            $('#gis_location_wkt__row1').hide();
            // Show the Lat/Lon inputs
            $('#gis_location_lat__row').show();
            $('#gis_location_lon__row').show();
            $('#gis_location_lat__row1').show();
            $('#gis_location_lon__row1').show();
        } else {
            // Hide the Lat/Lon inputs
            $('#gis_location_lat__row').hide();
            $('#gis_location_lon__row').hide();
            $('#gis_location_lat__row1').hide();
            $('#gis_location_lon__row1').hide();
            // Show the WKT input
            $('#gis_location_wkt__row').show();
            $('#gis_location_wkt__row1').show();
            if (feature_type == 2) {
                // Line
                if ($('#gis_location_wkt').val() === ''){
                    // Pre-populate the WKT field
                    $('#gis_location_wkt').val('LINESTRING( , , )');
                }
            } else if (feature_type == 3) {
                // Polygon
                if ($('#gis_location_wkt').val() === ''){
                    // Pre-populate the WKT field
                    $('#gis_location_wkt').val('POLYGON(( , , ))');
                }
            } else if (feature_type == 6) {
                // Polygon
                if ($('#gis_location_wkt').val() === ''){
                    // Pre-populate the WKT field
                    $('#gis_location_wkt').val('MULTIPOLYGON(( , , ))');
                }
            }
        }
    };

    /**
     * Check that Map JS is Loaded
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

    $(document).ready(function() {
        var feature_type = $('#gis_location_gis_feature_type').val();
        s3_gis_feature_crud(feature_type);
        // When the Type changes:
        $('#gis_location_gis_feature_type').change(function() {
            // What is the new type?
            feature_type = $(this).val();
            s3_gis_feature_crud(feature_type);
        });

        var level = $('#gis_location_level').val();
        if (level) {
            //If the Location is a Admin Boundary then Street Address makes no sense
            $('#gis_location_addr_street__row').hide();
            $('#gis_location_addr_street__row1').hide();
            $('#gis_location_addr_postcode__row').hide();
            $('#gis_location_addr_postcode__row1').hide();
            // If the Location is a Country then Parent makes no sense
            if (level == 'L0') {
                $('#gis_location_parent__row').hide();
            }
        }
        // When the Level changes:
        $('#gis_location_level').change(function() {
            // What is the new type?
            var level = $(this).val();
            if (level) {
                // If the Location is a Admin Boundary then Street Address makes no sense
                $('#gis_location_addr_street__row').hide();
                $('#gis_location_addr_street__row1').hide();
                $('#gis_location_addr_postcode__row').hide();
                $('#gis_location_addr_postcode__row1').hide();
                if (level == 'L0') {
                // If the Location is a Country then Parent makes no sense
                    $('#gis_location_parent__row').hide();
                    $('#gis_location_parent__row1').hide();
                    $('#gis_location_parent').val('');
                } else {
                    $('#gis_location_parent__row').show();
                    $('#gis_location_parent__row1').show();
                }
            } else {
                $('#gis_location_addr_street__row').show();
                $('#gis_location_addr_street__row1').show();
                $('#gis_location_addr_postcode__row').show();
                $('#gis_location_addr_postcode__row1').show();
                $('#gis_location_parent__row').show();
                $('#gis_location_parent__row1').show();
            }
        });

        // Check if Maps JS is Loaded
        $.when(jsLoaded()).then(
            function(status) {
                // Success
                var map = S3.gis.maps['default_map'];

                // Point Placed callback
                map.s3.pointPlaced = function(feature) {
                    var centerPoint = feature.geometry.getBounds().getCenterLonLat();
                    centerPoint.transform(map.getProjectionObject(), S3.gis.proj4326);
                    $('#gis_location_lon').val(centerPoint.lon);
                    $('#gis_location_lat').val(centerPoint.lat);
                    $('#gis_location_wkt').val('');
                };
            }
        );
    });
}());