/**
 * Used by the inv/send controller
 * - set default quantity & show as max
 */

$(document).ready(function() {

    var trackItemAddFieldSelector = '#sub_defaultsend_package_item_defaultsend_package_item_i_track_item_id_edit_none',
        trackItemAddField = $(trackItemAddFieldSelector);
    if (trackItemAddField.length) {

        var track_items = S3.supply.track_items;
        if (undefined !== track_items) {

            var inlineComponent = $('#sub-defaultsend_package_item'),
                quantity,
                QuantityField = $('#sub_defaultsend_package_item_defaultsend_package_item_i_quantity_edit_none'),
                trackItemID;

            // Prevent editing the Item for existing rows
            $('#sub_defaultsend_package_item_defaultsend_package_item_i_track_item_id_edit_0').attr('disabled', 'disabled');

            // Don't allow new rows to have the same track item as ones which are already in this Package
            var packageItems = JSON.parse($('#inv_send_package_sub_defaultsend_package_item').val()).data;
            for (var i = 0; i < packageItems.length; i++) {
                trackItemID = packageItems[i].track_item_id.value;
                $(trackItemAddFieldSelector + ' option[value="' + trackItemID + '"]').remove();
            }

            var TrackItemChange = function(/*event*/) {
                trackItemID = trackItemAddField.val();
                if (trackItemID) {
                    // Set the default Quantity to be the Quantity left to Package
                    quantity = track_items[trackItemID];
                    QuantityField.val(quantity);
                } else {
                    // Clear Values
                    QuantityField.val(1);
                }
            };

            trackItemAddField.change(TrackItemChange);

            inlineComponent.on('rowAdded', function(event, row) {
                trackItemID = row.track_item_id.value;
                // Remove Item from selection options
                $(trackItemAddFieldSelector + ' option[value="' + trackItemID + '"]').remove();
                // Remove Quantity available (in case we then delete again)
                track_items[trackItemID] = track_items[trackItemID] - parseFloat(row.quantity.value);
            });

            inlineComponent.on('rowRemoved', function(event, row) {
                trackItemID = row.track_item_id.value;
                // Add Item to selection options
                trackItemAddField.append('<option value="' + trackItemID + '">' + row.track_item_id.text + '</option>');
                // Make Quantity available
                track_items[trackItemID] = track_items[trackItemID] + parseFloat(row.quantity.value);
            });
        }
    }

});