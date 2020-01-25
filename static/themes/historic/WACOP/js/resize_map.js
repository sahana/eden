// Resize the Map on Browse pages

S3.wacop_resizeMap = function(map_id) {

    // Set Map Height to the minimum of Viewport height or Filter Form height
    var resizeMap = function(map_id) {
        var height = Math.min($('#ff').height(), $(window).height());
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
