// Map Filter button
S3.wacop_mapFilter = function(map_id) {
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

    var clickHandler = function() {

        // Disable Button
        $('#map_filter_button').addClass('disabled')
                               .unbind('click');

        $.when(jsLoaded()).then(
            function(status) {
                // Success
                var s3 = S3.gis.maps[map_id].s3;

                // Show Panel
                var control = S3.gis.addPolygonPanel(map_id);

                // Activate Control
                control.activate();
                $('#' + map_id + '_panel .olMapViewport').addClass('crosshair');

                // Hooks

                // Point Placed
                // Save original callback
                var pointPlaced = s3.pointPlaced
                s3.pointPlaced = function(feature) {
                    // Update Panel
                    // Hide the original Panel
                    $('.map_polygon_panel').remove();
                    // Add New Panel
                    // @ToDo: i18n
                    var msg = 'Please wait while we update your results. Remove this filter any time by clicking the Clear button below.';
                    var div = '<div class="map_polygon_panel">' + msg + '<div class="map_polygon_buttons"><a class="button small map_polygon_clear">' + 'Clear' + '</a></div></div>';
                    $('#' + map_id).append(div);
                    // Deactivate control
                    control.deactivate();
                    $('#' + map_id + '_panel .olMapViewport').removeClass('crosshair');
                    // Click Handler
                    $('#' + map_id + ' .map_polygon_clear').click(function() {
                        if (s3.lastDraftFeature) {
                            s3.lastDraftFeature.destroy();
                        } else if (s3.draftLayer.features.length > 1) {
                            // Clear the one from the Current Location in S3LocationSelector
                            s3.draftLayer.features[0].destroy();
                        }
                        if (undefined != s3.polygonPanelClear) {
                            // Call Custom Call-back (used by S3MapFilter in WACOP)
                            s3.polygonPanelClear();
                        }
                    });

                    // Call original callback
                    pointPlaced(feature);
                }

                // Layer Refreshed
                s3.layerRefreshed = function(layer) {
                    // Do Nothing - except override the default handler
                };

                // Clear button
                s3.polygonPanelClear = function() {
                    var widget_name = $('.map-filter').attr('id'),
                        widget = $('#' + widget_name);
                    // Clear the data & trigger the autosubmit
                    widget.val('').trigger('change');
                    // Hide the Panel
                    $('.map_polygon_panel').remove();
                    // Enable Filter button
                    $('#map_filter_button').removeClass('disabled')
                                           .click(clickHandler);
                };

                // Finish button
                s3.polygonPanelFinish = function() {
                    // Do Nothing - except override the default handler
                };
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

    $('#map_filter_button').click(clickHandler);
};
