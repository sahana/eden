/**
 *   PoIs Static JS Code
 */

// Module pattern to hide internal vars
(function() {

    /**
     * Check that Map JS is Loaded
     */
    var jsLoaded = function() {
        var dfd = new jQuery.Deferred();
        var gis = S3.gis;

        // Test every half-second
        setTimeout(function working() {
            // @ToDo: Configurable map_id
            if ((gis.maps != undefined) && (gis.maps['default_map'] != undefined)) {
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
    var pointPlaced = function(feature) {
        var gis = S3.gis;
        var proj4326 = gis.proj4326;
        // Read lat & lon
        var current_projection = feature.layer.map.getProjectionObject();
        var centerPoint = feature.geometry.getBounds().getCenterLonLat();
        centerPoint.transform(current_projection, proj4326);
        // Build URL for create form
        var url = S3.Ap.concat('/gis/poi/create.popup?refresh_layer=' + gis.pois_layer + '&lat=' + centerPoint.lat + '&lon=' + centerPoint.lon);
        // Convert geometry back for the marker
        centerPoint.transform(proj4326, current_projection);
        // Collapse the LayerTree to give more space for the Popup
        gis.maps['default_map'].s3.westPanelContainer.collapse();
        // Create a popup with an iframe inside
        gis.addPopup(feature, url, undefined, true);
    };

    /**
     * document-ready script
     */
    $(document).ready(function() {
        $.when(jsLoaded()).then(
            function(status) {
                // Success: Add Callback to handle PoIs
                // @ToDo: Configurable map_id
                S3.gis.maps['default_map'].s3.pointPlaced = pointPlaced;
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