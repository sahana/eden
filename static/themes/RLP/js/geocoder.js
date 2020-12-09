/*
 * Shim for the S3LocationSelector to Geocode the Lx from the Postcode
 */

$(document).ready(function(){

    S3.rlp_GeoCoder = function(fieldname) {

        var addressField = $('#' + fieldname + '_address'),
            postcodeField = $('#' + fieldname + '_postcode');

        // Add elements not present as Geocoder not active server-side as no map!
        $('#' + fieldname + '_postcode__row').after('<div id="' + fieldname + '_geocode" class="controls geocode"><div class="throbber hide"></div><div class="geocode_success hide"></div><div class="geocode_fail hide"></div></div>');

        postcodeField.on('blur', function() {

            // Hide old messages, show throbber
            var selector = '#' + fieldname,
                failure = $(selector + '_geocode .geocode_fail').hide(),
                success = $(selector + '_geocode .geocode_success').hide(),
                throbber = $(selector + '_geocode .throbber').removeClass('hide').show();

            // Connect to the LocationSelector Widget
            var field = $('#' + fieldname);

            // Submit to Geocoder
            $.ajaxS3({
                //async: false,
                url: S3.Ap.concat('/default/index/geocode'),
                type: 'POST',
                data: {address: addressField.val(),
                       postcode: postcodeField.val(),
                       },
                dataType: 'json',
                success: function(result) {

                    if (result.L1) {
                            field.locationselector('lxSelect', 1, result.L1);
                            if (result.L2) {
                                // @ToDo: Rewrite with callbacks for better speed/reliability
                                var selectL2 = function() {
                                    field.locationselector('lxSelect', 2, result.L2);
                                };
                                setTimeout(selectL2, 500);
                                if (result.L3) {
                                    var selectL3 = function() {
                                        field.locationselector('lxSelect', 3, result.L3);
                                    };
                                    setTimeout(selectL3, 250);
                                }
                            }
                            // Notify results
                            throbber.hide();
                            success.html(i18n.location_found).removeClass('hide').show();
                        } else {
                            // Notify results
                            throbber.hide();
                            failure.html(i18n.location_not_found).removeClass('hide').show();
                            //s3_debug(result);
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
                    failure.html(i18n.location_not_found).removeClass('hide').show();
                    s3_debug(msg);
                }
            });
        });
    };
});
