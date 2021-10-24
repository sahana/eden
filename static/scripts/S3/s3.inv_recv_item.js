/**
 * Used by the inv/recv controller
 * - replace filterOptionsS3 to show item packs for Item
 * - set req_item_id based on selected Item
 */

$(document).ready(function() {

    var ItemField = $('#inv_track_item_item_id');

    if (ItemField.length) {

        var ajaxURL,
            allPacks = S3.supply.packs || {},
            availableQuantity, // Quantity available of current Pack
            bin,
            binQuantity,
            binnedQuantity = S3.supply.binnedQuantity || 0, // Needs to be multiplied by InvPackQuantity for comparisons
            binnedQuantityPacked, // Quantity binned of current Pack
            editBinBtnOK = $('#rdy-defaultbin-0'),
            error,
            first,
            inlineComponent = $('#sub-defaultrecv_bin'),
            itemID = ItemField.val(),
            ItemPackField = $('#inv_inv_item_item_pack_id'),
            itemPackID,
            message,
            newBinQuantityField = $('#sub_defaultrecv_bin_defaultrecv_bin_i_quantity_edit_none'),
            // Represent numbers with thousand separator
            // @ToDo: Respect settings
            numberFormat = /(\d)(?=(\d{3})+(?!\d))/g,
            oldBinQuantityField = $('#sub_defaultrecv_bin_defaultrecv_bin_i_quantity_edit_0'),
            oldPackQuantity,
            opt,
            pack,
            packs,
            packsByID,
            packsLength,
            PackQuantity,
            QuantityField = $('#inv_track_item_quantity'),
            ReqItemRow = $('#inv_track_item_req_item_id__row'),
            startingQuantity, // Needs to be multiplied by startingPackQuantity for comparisons
            startingPackID,
            startingPackQuantity = 1,
            totalQuantity, // Value in QuantityField. Needs to be multiplied by PackQuantity for comparisons
            update,
            updatePacks,
            updateQuantity;

        if (ReqItemRow.length) {
            // Hide it by Default
            ReqItemRow.hide();
        }

        updatePacks = function() {
            first = true;
            packs = allPacks[itemID];
            packsByID = {};
            packsLength = packs.length;
            ItemPackField.html('');
            for (i = 0; i < packsLength; i++) {
                pack = packs[i];
                packsByID[pack.i] = pack.q;
                if (startingPackID && (startingPackID == pack.i)) {
                    itemPackID = startingPackID;
                    oldPackQuantity = startingPackQuantity = PackQuantity = pack.q;
                    selected = ' selected';
                } else if (first) {
                    itemPackID = pack.i;
                    oldPackQuantity = PackQuantity = pack.q;
                    selected = ' selected';
                } else {
                    selected = '';
                }
                first = false;
                opt = '<option value="' + pack.i + '"' + selected + '>' + pack.n + '</option>';
                ItemPackField.append(opt);
            }
        };

        ItemField.on('change.s3', function(event, first) {
            itemID = ItemField.val();

            if (first) {
                 // Don't clear for first run of update forms
            } else {
                update = false;
                QuantityField.val('');
                totalQuantity = 0;
                // Empty the Bins field
                inlineComponent.inlinecomponent('removeRows');
                binnedQuantity = 0;
            }

            // Update available Packs
            packs = allPacks[itemID];
            if (packs) {
                // We have cached data
                updatePacks();
            } else {
                // We need to look the data up
                ajaxURL = S3.Ap.concat('/supply/item_packs.json/' + itemID);
                $.ajaxS3({
                    url: ajaxURL,
                    dataType: 'json',
                    success: function(data) {
                        allPacks[itemID] = data;
                        updatePacks();
                    }
                });
            }

        });

        if (itemID) {
            // Update form
            update = true;
            startingItemPackID = itemPackID = ItemPackField.val();
            if (totalQuantity) {
                totalQuantity = parseFloat(totalQuantity);
            } else {
                totalQuantity = 0;
            }
            ItemField.trigger('change.s3', true);
        }

        ItemPackField.on('change.s3', function() {
            itemPackID = ItemPackField.val();
            PackQuantity = packsByID[itemPackID];
            // Adjust Total Quantity
            totalQuantity = totalQuantityField.val();
            totalQuantity = totalQuantity * oldPackQuantity / PackQuantity;
            totalQuantityField.val(totalQuantity);
            // Adjust Bins
            binQuantity = newBinQuantityField.val();
            binQuantity = binQuantity * oldPackQuantity / PackQuantity;
            newBinQuantityField.val(binQuantity);
            binQuantity = oldBinQuantityField.val();
            binQuantity = binQuantity * oldPackQuantity / PackQuantity;
            oldBinQuantityField.val(binQuantity);
            updateQuantity = function(row) {
                binQuantity = row.quantity.value;
                binQuantity = binQuantity * oldPackQuantity / PackQuantity;
                row.quantity.value = binQuantity;
                row.quantity.text = binQuantity.toString().replace(numberFormat, '$1,');
            };
            inlineComponent.inlinecomponent('updateRows', updateQuantity);
            // New oldPackQuantity
            oldPackQuantity = PackQuantity;
        });

        // Attach to the top-level element to catch newly-created readRows
        inlineComponent.on('click.s3', '.inline-edt', function() {
            binQuantity = oldBinQuantityField.val();
            if (binQuantity) {
                binQuantity = parseFloat(binQuantity);
                // Make this Bin's Quantity available
                binnedQuantity -= (binQuantity * PackQuantity / startingPackQuantity);
            }
        });

        editBinBtnOK.click(function() {
            binQuantity = oldBinQuantityField.val();
            if (binQuantity) {
                binQuantity = parseFloat(binQuantity);
                // Make this Bin's Quantity unavailable
                binnedQuantity += (binQuantity * PackQuantity / startingPackQuantity);
            }
            // Validate the new bin again
            //newBinQuantityField.change();
        });

        QuantityField.change(function() {
            totalQuantity = QuantityField.val();
            if (totalQuantity) {
                totalQuantity = parseFloat(totalQuantity);
            } else {
                totalQuantity = 0;
            }
        });

        newBinQuantityField.change(function() {
            binQuantity = newBinQuantityField.val();
            if (binQuantity) {
                binQuantity = parseFloat(binQuantity);
                binnedQuantityPacked = binnedQuantity * startingPackQuantity / PackQuantity;
                availableQuantity = totalQuantity - binnedQuantityPacked;
                if (binQuantity > availableQuantity) {
                    // @ToDo: i18n
                    message = 'Bin Quantity reduced to Quantity remaining to be Received';
                    error = $('<div class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                    newBinQuantityField.val(availableQuantity)
                                       .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                        $(this).fadeOut('slow').remove();
                        return false;
                    });
                }
            }
        });

        oldBinQuantityField.change(function() {
            binQuantity = oldBinQuantityField.val();
            if (binQuantity) {
                binQuantity = parseFloat(binQuantity);
                binnedQuantityPacked = binnedQuantity * startingPackQuantity / PackQuantity;
                availableQuantity = totalQuantity - binnedQuantityPacked;
                if (binQuantity > availableQuantity) {
                    // @ToDo: i18n
                    message = 'Bin Quantity reduced to Quantity remaining to be Received';
                    error = $('<div id="sub_defaultrecv_bin_defaultrecv_bin_i_quantity_edit_0-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                    oldBinQuantityField.val(availableQuantity)
                                       .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                        $(this).fadeOut('slow').remove();
                        return false;
                    });
                }
            }
        });

        inlineComponent.on('rowAdded', function(event, row) {
            // Make Quantity unavailable
            binQuantity = row.quantity.value;
            if (binQuantity) {
                binQuantity = parseFloat(binQuantity);
                binnedQuantity += (binQuantity * PackQuantity / startingPackQuantity);
            }
        });

        inlineComponent.on('rowRemoved', function(event, row) {
            // Make Quantity available
            binQuantity = row.quantity.value;
            if (binQuantity) {
                binQuantity = parseFloat(binQuantity);
                binnedQuantity -= (binQuantity * PackQuantity / startingPackQuantity);
            }
        });
    }
});