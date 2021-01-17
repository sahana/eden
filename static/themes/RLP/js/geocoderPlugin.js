/*
 * Plugin for the S3LocationSelector to Geocode the Lx from the Postcode
 */

$(document).ready(function(){

    S3.gis.geocodeDecisionPlugin = function(selector, data, self) {
        // Postcode or Address is mandatory for geocoding
        if (!data.postcode && !data.address) {
            return;
        }

        // Hide previous success/failure messages
        $(selector + '_geocode .geocode_success,' +
          selector + '_geocode .geocode_fail').hide();

        var ns = self.eventNamespace;
        if (self.input.data('manually_geocoded')) {
            // Show a button to allow the user to do a new automatic Geocode
            $(selector + '_geocode button').removeClass('hide')
                                           .show()
                                           .unbind(ns)
                                           .bind('click' + ns, function() {
                $(this).hide();
                rlpGeocode(self);
            });
        } else {
            // Do an automatic Geocode
            rlpGeocode(self);
        }
    };

    rlpGeocode= function(self) {

        var fieldname = self.fieldname,
            data = self.data
        var selector = '#' + fieldname;

        // Hide old messages, show throbber
        var failure = $(selector + '_geocode .geocode_fail').hide(),
            success = $(selector + '_geocode .geocode_success').hide(),
            throbber = $(selector + '_geocode .throbber').removeClass('hide').show();

        // Submit to Geocoder
        $.ajaxS3({
            //async: false,
            url: S3.Ap.concat('/default/index/geocode'),
            type: 'POST',
            data: {address: data.address,
                   postcode: data.postcode,
                   },
            dataType: 'json',
            success: function(result) {

                var lat = result.lat,
                    lon = result.lon;

                if (lat || lon) {
                    // Update data dict + serialize
                    data.lat = parseFloat(lat);
                    data.lon = parseFloat(lon);
                    self._collectData();

                    // If Map Showing then add/move Point
                    var gis = S3.gis;
                    if (gis.maps) {
                        var map = gis.maps['location_selector_' + fieldname];
                        if (map) {
                            var draftLayer = map.s3.draftLayer;
                            draftLayer.removeAllFeatures();
                            var geometry = new OpenLayers.Geometry.Point(data.lon, data.lat);
                            geometry.transform(gis.proj4326, map.getProjectionObject());
                            var feature = new OpenLayers.Feature.Vector(geometry);
                            draftLayer.addFeatures([feature]);
                            // Move viewport to this feature
                            self._zoomMap();
                        }
                    }
                    
                    var L1 = result.L1,
                        L2 = result.L2,
                        L3 = result.L3,
                        L4 = result.L4;

                    if (L1) {
                        // Prevent forward geocoding
                        self.useGeocoder = false;

                        var pending;
                        [L1, L2 || L3, L3 || L4, L4].forEach(function(level, index) {
                            if (level) {
                                if (pending) {
                                    pending = pending.then(function() {
                                        return self.lxSelect(index + 1, level);
                                    });
                                } else {
                                    pending = self.lxSelect(index + 1, level);
                                }
                            }
                        });

                        // Reset Geocoder-option
                        self.useGeocoder = true;
                    }

                    // Notify results
                    throbber.hide();
                    success.html(i18n.address_mapped).removeClass('hide').show();
                } else {

                    // Notify results
                    throbber.hide();
                    failure.html(i18n.address_not_mapped).removeClass('hide').show();
                    s3_debug(result);
                }
            },
            error: function(request, status, error) {
                var msg;
                if (error == 'UNAUTHORIZED') {
                    msg = i18n.gis_requires_login;
                } else {
                    msg = request.responseText;
                }
                // Notify results
                throbber.hide();
                failure.html(i18n.address_not_mapped).removeClass('hide').show();
                s3_debug(msg);
            }
        });
    };
});
