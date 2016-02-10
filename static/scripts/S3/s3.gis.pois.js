/**
 *   PoIs Static JS Code
 */

// Module pattern to hide internal vars
(function() {

    /**
     * Check that Map JS is Loaded
     */
    var jsLoaded = function(map_id) {
        var dfd = new jQuery.Deferred();
        var gis = S3.gis;

        // Test every half-second
        setTimeout(function working() {
            if ((gis.maps != undefined) && (gis.maps[map_id] != undefined)) {
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
     * Callback for placing a new PoI
     */
    var pointPlaced = function(feature, resource) {
        var gis = S3.gis;
        var proj4326 = gis.proj4326;
        // Read lat & lon
        var current_projection = feature.layer.map.getProjectionObject();
        var geometry = feature.geometry;
        if (geometry.CLASS_NAME != 'OpenLayers.Geometry.Point') {
            // Line or Polygon or Circle: pass WKT
            geometry.transform(current_projection, proj4326);
            var wkt = geometry.toString();
            // Build URL for create form
            var url = S3.Ap.concat('/' + resource['c'] + '/' + resource['f'] + '/create.popup?refresh_layer=' + resource['i'] + '&wkt=' + wkt);
            // Convert geometry back for the vector
            geometry.transform(proj4326, current_projection);
        } else {
            var centerPoint = geometry.getBounds().getCenterLonLat();
            centerPoint.transform(current_projection, proj4326);
            // Build URL for create form
            var url = S3.Ap.concat('/' + resource['c'] + '/' + resource['f'] + '/create.popup?refresh_layer=' + resource['i'] + '&lat=' + centerPoint.lat + '&lon=' + centerPoint.lon);
            // Convert geometry back for the marker
            centerPoint.transform(proj4326, current_projection);
        }
        // Collapse the LayerTree to give more space for the Popup
        gis.maps['default_map'].s3.westPanelContainer.collapse();
        // Create a popup with an iframe inside
        gis.addPopup(feature, url, undefined, true);
    };

    /* @ToDo: Support for PoIs to be added using a Popup to select which type
    var urlForPopup = function(feature, resource) { 
        var gis = S3.gis;
        var proj4326 = gis.proj4326;
        // Read lat & lon
        var current_projection = feature.layer.map.getProjectionObject();
        var centerPoint = feature.geometry.getBounds().getCenterLonLat();
        centerPoint.transform(current_projection, proj4326);
        // Build URL for create form
        var url = S3.Ap.concat('/' + resource['c'] + '/' + resource['f'] + '/create.popup?refresh_layer=' + resource['i'] + '&lat=' + centerPoint.lat + '&lon=' + centerPoint.lon);
		// Convert geometry back for the marker
        centerPoint.transform(proj4326, current_projection);
        return url;
    }; */

    /**
     * document-ready script
     */
    $(document).ready(function() {
        // @ToDo: Configurable map_id
        var map_id = 'default_map';
        $.when(jsLoaded(map_id)).then(
            function(status) {
                // Success: Add Callback to handle PoIs
                S3.gis.maps[map_id].s3.pointPlaced = pointPlaced;
                //S3.gis.maps[map_id].s3.urlForPopup = urlForPopup;
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
    });

})(jQuery);

// END ========================================================================