// Tags for Incident
var incident_tags = function(incident_id) {
    if (incident_id) {
        // Read-Write
        $('#incident-tags').tagit({
            // @ToDo: i18n
            placeholderText: 'Add tags here…',
            afterTagAdded: function(event, ui) {
                if (ui.duringInitialization) {
                    return;
                }
                var url = S3.Ap.concat('/event/incident/' + incident_id + '/add_tag/', ui.tagLabel);
                $.getS3(url);
            },
            afterTagRemoved: function(event, ui) {
                var url = S3.Ap.concat('/event/incident/' + incident_id + '/remove_tag/', ui.tagLabel);
                $.getS3(url);
            }
        });
    } else {
        // Read-only
         $('#incident-tags').tagit({
            readOnly: true
        });
    }
};

// Resize Map
S3.wacop_resizeMap = function(map_id) {

    // Set Map Height to the minimum of Viewport height or Filter Form height
    var resizeMap = function(map_id) {
        var height = Math.min($('#sizeTo').height(), $(window).height());
        height = Math.max(height, 400);
        S3.gis.maps[map_id].s3.mapWin.setSize(undefined, height);
    }

    // Check that Map JS is Loaded
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

    // Wait till the map has loaded
    $.when(jsLoaded()).then(
        function(status) {
            // Success:
            // Resize the Map Now
            resizeMap(map_id);

            // Zoom to current Bounds
            var bounds = new OpenLayers.Bounds(incident_bounds['lon_min'], incident_bounds['lat_min'], incident_bounds['lon_max'], incident_bounds['lat_max']);
            S3.gis.zoomBounds(S3.gis.maps[map_id], bounds);

            // Resize the map whenever the Viewport is resized
            $(window).resize(function() {
                resizeMap(map_id);
            });
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
};

$(document).ready(function() {
    //$('main.main').attr('id', 'incident-profile');

    $('.filter-clear, .show-filter-manager').addClass('button tiny secondary');
});