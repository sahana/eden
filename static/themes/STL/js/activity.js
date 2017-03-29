/**
 * Used in STL template, dvr/activity controller
 */

(function($, undefined) {

    "use strict";

    var modality = '#dvr_activity_modality',
        wrapperID = 'dvr_activity_location_id__wrapper',
        certificate = '#dvr_activity_certificate',
        certificateDetailsRow = '#dvr_activity_certificate_details__row';


    /**
     * Toggle fields for Site/Room and Target Area by Modality
     */
    var toggleActivityLocationFields = function() {

        var siteRoom = '#dvr_activity_site_id__row,#dvr_activity_room_id__row',
            targetArea = '#' + wrapperID,
            hide,
            show;

        if ($(modality).val() == 'O') {
            hide = siteRoom;
            show = targetArea;
        } else {
            hide = targetArea;
            show = siteRoom;
        }

        $(hide).hide();
        $(show).removeClass('hide').show();
    };

    /**
     * Toggle certificate details input
     */
    var toggleCertificateDetails = function() {

        if ($(certificate).is(':checked')) {
            $(certificateDetailsRow).removeClass('hide').show();
        } else {
            $(certificateDetailsRow).hide();
            // Remove details when certificate-flag is unchecked
            $('#dvr_activity_certificate_details').val('');
        }
    };

    $(document).ready(function() {

        // If we have an active modality input...
        if ($(modality).length) {

            // Wrap the target area location selector, so that we
            // can toggle its overall visibility without disturbing
            // the visibility of individual rows of the widget
            $('<div id="' + wrapperID + '">').insertBefore($('#dvr_activity_location_id__row'))
                                             .append($('.form-row[id^="dvr_activity_location_id"]'));

            // Toggle fields whenever the modality field changes
            $(modality).unbind('.dvr').bind('change.dvr', function() {
                toggleActivityLocationFields();
            });

            // Set initial visibility
            toggleActivityLocationFields();
        }

        // If we have an active certificate checkbox...
        if ($(certificate).length) {

            // Toggle visibility of certificate details row
            $(certificate).unbind('.dvr').bind('change.dvr', function() {
                toggleCertificateDetails();
            });

            // Set initial visibility
            toggleCertificateDetails();
        }
    });

})(jQuery);

// END ========================================================================
