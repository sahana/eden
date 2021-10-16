/**
 * Used by the inv/recv controller when settings.inv_recv_req = True
 * - replace filterOptionsS3 to show item packs for Item
 * - set req_item_id based on selected Item
 */

$(document).ready(function() {

    var ItemField = $('#inv_track_item_item_id'),
        ReqItemRow = $('#inv_track_item_req_item_id__row');

    if (ReqItemRow.length) {
        // Hide it by Default
        ReqItemRow.hide();
    }

    var ItemIDChange = function() {
        // Update the available packs for this item
        // Default to the number of these items requested

        var item_id = ItemField.val(),
            ItemPackField = $('#inv_track_item_item_pack_id'),
            QuantityField = $('#inv_track_item_quantity');

        // Remove old Items
        ItemPackField.html('');
        QuantityField.val('');

        if (item_id === '') {
            // No Item available yet
            return
        }

        // Use data provided from inv_recv_controller
        // - Pack Options
        // - REQ Quantity
        // - req_item_id
        var item_data = S3.supply.item_data;

        var i,
            first = true,
            data = item_data[item_id],
            opt,
            pack,
            packs = data.packs,
            packsLength = packs.length,
            PackQuantity,
            PackName,
            piece,
            req_items = data.req_items,
            req_item = req_items[0],
            selected;

        for (i = 0; i < packsLength; i++) {
            pack = packs[i];
            if (pack.quantity == 1) {
                piece = pack.name;
                break;
            }
        }

        // Update available Packs
        for (i = 0; i < packsLength; i++) {
            pack = packs[i];
            if (first) {
                PackQuantity = pack.quantity;
                PackName = pack.name;
                selected = ' selected';
            } else {
                selected = '';
            }
            if (pack.quantity !== 1) {
                opt = '<option value="' + pack.id + '"' + selected + '>' + pack.name + ' (' + pack.quantity + ' x ' + piece + ')</option>';
            } else {
                opt = '<option value="' + pack.id + '"' + selected + '>' + pack.name + '</option>';
            }
            ItemPackField.append(opt);
            first = false;
        }

        // Update Quantity
        var updateQuantity = function() {
            if (req_items.length == 1) {
                // Default to REQ Quantity
                var ReqQuantity = req_item.req_quantity / PackQuantity;
                QuantityField.val(ReqQuantity);

                // Set req_item_id, so that we can track request fulfilment
                $('#inv_track_item_req_item_id').val(req_item.req_item_id);

            } else {
                // Multiple Req Items for the same Item
                // Display ReqItemRow
                ReqItemRow.show();
                // Populate with Options
                var req_item_id,
                    ReqItemField = $('#inv_track_item_req_item_id'),
                    ReqQuantity;
                ReqItemField.html('');
                for (i = 0; i < req_items.length; i++) {
                    req_item = req_items[i];
                    ReqItemField.append(new Option(req_item.req_ref, req_item.req_item_id));
                    if (first) {
                        ReqQuantity = req_item.req_quantity / PackQuantity;
                        QuantityField.val(ReqQuantity);
                    }
                    first = false;
                }
                ReqItemField.on('change', function() {
                    // Update the Quantity accordingly
                    req_item_id = parseInt(ReqItemField.val());
                    for (i = 0; i < req_items.length; i++) {
                        req_item = req_items[i];
                        if (req_item.req_item_id == req_item_id) {
                            ReqQuantity = req_item.req_quantity / PackQuantity;
                            QuantityField.val(ReqQuantity);
                            break;
                        }
                    }
                });
            }
        }

        updateQuantity();

        if (packsLength > 1) {
            var item_pack_id;
            ItemPackField.on('change', function() {
                item_pack_id = parseInt(ItemPackField.val());
                for (i = 0; i < packsLength; i++) {
                    pack = packs[i]
                    if (pack.id == item_pack_id) {
                        // Update Quantity
                        updateQuantity();
                        break;
                    }
                }
            });
        }
    };

    ItemField.change(ItemIDChange);

});