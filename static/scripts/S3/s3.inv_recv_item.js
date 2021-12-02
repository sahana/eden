/**
 * Used by the inv/recv controller for SHIP_STATUS_IN_PROCESS
 * - replace filterOptionsS3 to show item packs for Item
 * - set req_item_id based on selected Item
 * - manage Bin allocations
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
            error,
            first,
            inlineComponent = $('#sub-defaultrecv_bin'),
            inlineComponentInput = $('#inv_track_item_sub_defaultrecv_bin'),
            itemID = ItemField.val(),
            ItemPackField = $('#inv_track_item_item_pack_id'),
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
            RecvQuantityField = $('#inv_track_item_recv_quantity'),
            recvQuantity, // Value in RecvQuantityField (or QuantityField, if that isn't set). Needs to be multiplied by PackQuantity for comparisons
            reqData = S3.supply.req_data || {},
            reqItems,
            ReqItemField = $('#inv_track_item_req_item_id'),
            ReqItemRow = $('#inv_track_item_req_item_id__row'),
            sendQuantity, // Value in QuantityField. Needs to be multiplied by PackQuantity for comparisons
            startingQuantity, // Needs to be multiplied by startingPackQuantity for comparisons
            startingPackID,
            startingPackQuantity = 1,
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

            if (first) {
                // Don't clear for first run of update forms
                // Set sendQuantity and recvQuantity
                sendQuantity = QuantityField.val();
                if (sendQuantity) {
                    sendQuantity = parseFloat(sendQuantity);
                }
                recvQuantity = RecvQuantityField.val();
                if (recvQuantity) {
                    recvQuantity = parseFloat(recvQuantity);
                } else {
                    recvQuantity = sendQuantity;
                }
            } else {
                update = false;
                QuantityField.val('');
                RecvQuantityField.val('');
                reqItems = reqData[itemID];
                if (reqItems) {
                    if (reqItems.length == 1) {
                        // Default to REQ Quantity
                        var reqItem = reqItems[0];
                        sendQuantity = reqItem.q / PackQuantity;
                        QuantityField.val(sendQuantity);

                        // Set req_item_id, so that we can track request fulfilment
                        ReqItemField.val(reqItem.i);

                    } else {
                        // Multiple Req Items for the same Item
                        // Display ReqItemRow
                        ReqItemRow.show();
                        // Populate with Options
                        var reqItem,
                            reqItemID,
                            ReqQuantity;
                        ReqItemField.html('');
                        first = true;
                        for (i = 0; i < reqItems.length; i++) {
                            reqItem = reqItems[i];
                            ReqItemField.append(new Option(reqItem.r, reqItem.u));
                            if (first) {
                                sendQuantity = reqItem.q / PackQuantity;
                                QuantityField.val(ReqQuantity);
                            }
                            first = false;
                        }
                        ReqItemField.on('change', function() {
                            // Update the Quantity accordingly
                            reqItemID = parseInt(ReqItemField.val());
                            for (i = 0; i < reqItems.length; i++) {
                                reqItem = reqItems[i];
                                if (reqItem.i == reqItemID) {
                                    sendQuantity = reqItem.q / PackQuantity;
                                    QuantityField.val(sendQuantity);
                                    break;
                                }
                            }
                        });
                    }
                } else {
                    // Not linked to a Request
                    ReqItemField.val('');
                    // => we have no useful default
                    sendQuantity = 0;
                }
                recvQuantity = 0;
                // Empty the Bins field
                inlineComponent.inlinecomponent('removeRows');
                binnedQuantity = 0;
            }

        });

        if (itemID) {
            // Update form
            update = true;
            startingItemPackID = itemPackID = ItemPackField.val();
            ItemField.trigger('change.s3', true);
        }

        ItemPackField.on('change.s3', function() {
            itemPackID = ItemPackField.val();
            PackQuantity = packsByID[itemPackID];
            // Adjust Total Quantities
            sendQuantity = QuantityField.val();
            if (sendQuantity) {
                sendQuantity = parseFloat(sendQuantity);
                sendQuantity = sendQuantity * oldPackQuantity / PackQuantity;
                QuantityField.val(totalQuantity);
                recvQuantity = RecvQuantityField.val();
                if (recvQuantity) {
                    recvQuantity = parseFloat(recvQuantity);
                    recvQuantity = recvQuantity * oldPackQuantity / PackQuantity;
                    RecvQuantityField.val(recvQuantity);
                } else {
                    recvQuantity = sendQuantity;
                }
            }
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

        QuantityField.change(function() {
            sendQuantity = QuantityField.val();
            if (sendQuantity) {
                sendQuantity = parseFloat(sendQuantity);
                recvQuantity = RecvQuantityField.val();
                if (recvQuantity) {
                    recvQuantity = parseFloat(recvQuantity);
                    if (recvQuantity > sendQuantity) {
                        // @ToDo: i18n
                        message = 'Quantity Sent increased to Quantity Received';
                        error = $('<div class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                        sendQuantity = recvQuantity;
                        QuantityField.val(recvQuantity)
                                     .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                            $(this).fadeOut('slow').remove();
                            return false;
                        });
                    }
                } else {
                    recvQuantity = sendQuantity;
                }
            } else {
                sendQuantity = recvQuantity = 0;
            }
        });

        RecvQuantityField.change(function() {
            recvQuantity = RecvQuantityField.val();
            if (recvQuantity) {
                recvQuantity = parseFloat(recvQuantity);
                if (recvQuantity > sendQuantity) {
                    // @ToDo: i18n
                    message = 'Quantity Received reduced to Quantity Sent';
                    error = $('<div class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                    recvQuantity = sendQuantity;
                    RecvQuantityField.val(sendQuantity)
                                     .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                        $(this).fadeOut('slow').remove();
                        return false;
                    });
                }
            } else {
                recvQuantity = sendQuantity;
            }
        });

        newBinQuantityField.change(function() {
            binQuantity = newBinQuantityField.val();
            if (binQuantity) {
                binQuantity = parseFloat(binQuantity);
                binnedQuantityPacked = binnedQuantity * startingPackQuantity / PackQuantity;
                availableQuantity = recvQuantity - binnedQuantityPacked;
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
                availableQuantity = recvQuantity - binnedQuantityPacked;
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

        // Attach to the top-level element to catch newly-created readRows
        inlineComponent.on('click.s3', '.inline-edt', function() {
            binQuantity = oldBinQuantityField.val();
            if (binQuantity) {
                binQuantity = parseFloat(binQuantity);
                // Make this Bin's Quantity available
                binnedQuantity -= (binQuantity * PackQuantity / startingPackQuantity);
            }
        });

        $('#rdy-defaultbin-0').click(function() {
            // read-only row has been opened for editing
            // - Tick clicked to save changes
            binQuantity = oldBinQuantityField.val();
            if (binQuantity) {
                binQuantity = parseFloat(binQuantity);
                // Make this Bin's Quantity unavailable
                binnedQuantity += (binQuantity * PackQuantity / startingPackQuantity);
            }
            // Validate the new bin again
            //newBinQuantityField.change();
        });

        inlineComponent.on('editCancelled', function(event, rowindex) {
            // read-only row has been opened for editing
            // - X clicked to cancel changes
            // Make Quantity unavailable
            binQuantity = parseFloat(inlineComponentInput.data('data').data[rowindex].quantity.value);
            binnedQuantity = binnedQuantity + binQuantity;
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