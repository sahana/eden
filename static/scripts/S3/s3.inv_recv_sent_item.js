/**
 * Used by the inv/recv controller for SHIP_STATUS_SENT
 * - manage Bin allocations (NB Pack is fixed, so can be ignored)
 */

$(document).ready(function() {

    var RecvQuantityField = $('#inv_track_item_recv_quantity');

    if (RecvQuantityField.length) {

        var availableQuantity, // Quantity available
            binQuantity,
            binnedQuantity = S3.supply.binnedQuantity || 0,
            editBinBtnOK = $('#rdy-defaultbin-0'),
            error,
            inlineComponent = $('#sub-defaultrecv_bin'),
            message,
            newBinQuantityField = $('#sub_defaultrecv_bin_defaultrecv_bin_i_quantity_edit_none'),
            oldBinQuantityField = $('#sub_defaultrecv_bin_defaultrecv_bin_i_quantity_edit_0'),
            recvQuantity, // Value in RecvQuantityField (or sendQuantity, if that isn't set)
            sendQuantity = S3.supply.sendQuantity; // Value in QuantityField

        // Attach to the top-level element to catch newly-created readRows
        inlineComponent.on('click.s3', '.inline-edt', function() {
            binQuantity = oldBinQuantityField.val();
            if (binQuantity) {
                binQuantity = parseFloat(binQuantity);
                // Make this Bin's Quantity available
                binnedQuantity -= binQuantity;
            }
        });

        editBinBtnOK.click(function() {
            binQuantity = oldBinQuantityField.val();
            if (binQuantity) {
                binQuantity = parseFloat(binQuantity);
                // Make this Bin's Quantity unavailable
                binnedQuantity += binQuantity;
            }
            // Validate the new bin again
            //newBinQuantityField.change();
        });

        RecvQuantityField.on('change.s3', function(event, first) {
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

        RecvQuantityField.trigger('change.s3', true);

        newBinQuantityField.change(function() {
            binQuantity = newBinQuantityField.val();
            if (binQuantity) {
                binQuantity = parseFloat(binQuantity);
                availableQuantity = recvQuantity - binnedQuantity;
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
                availableQuantity = recvQuantity - binnedQuantity;
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
                binnedQuantity += binQuantity;
            }
        });

        inlineComponent.on('rowRemoved', function(event, row) {
            // Make Quantity available
            binQuantity = row.quantity.value;
            if (binQuantity) {
                binQuantity = parseFloat(binQuantity);
                binnedQuantity -= binQuantity;
            }
        });
    }
});