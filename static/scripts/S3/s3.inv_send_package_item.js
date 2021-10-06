/**
 * Used by the inv/send controller
 * - set default quantity & show as max
 */

$(document).ready(function() {

    var trackItemField = $('#sub_defaultsend_package_item_defaultsend_package_item_i_track_item_id_edit_none');
    if (trackItemField.length) {

        var track_items = S3.supply.track_items;
        if (undefined !== track_items) {

            var trackItemID,
                quantity,
                QuantityField = $('#sub_defaultsend_package_item_defaultsend_package_item_i_quantity_edit_none');

            var TrackItemChange = function(/*event*/) {
                trackItemID = trackItemField.val();
                if (trackItemID) {
                    quantity = track_items[trackItemID];
                    QuantityField.val(quantity);
                } else {
                    // Clear Values
                    QuantityField.val(1);
                }
            };

            trackItemField.change(TrackItemChange);
        }
    }

});