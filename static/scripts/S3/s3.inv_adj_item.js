/**
 * Used by the inv/adj/adj_item controller
 * - Validate the Bin Quantity
 */

$(document).ready(function() {
    var availableQuantity,
        binQuantity,
        binnedQuantity = S3.supply.binnedQuantity || 0,
        error,
        inlineComponent = $('#sub-defaultbin'),
        editBinBtnOK = $('#rdy-defaultbin-0'),
        newBinQuantityField = $('#sub_defaultbin_defaultbin_i_quantity_edit_none'),
        oldBinQuantityField = $('#sub_defaultbin_defaultbin_i_quantity_edit_0'),
        totalQuantityField = $('#inv_adj_item_new_quantity'),
        totalQuantity = totalQuantityField.val(),
        $this;

    if (totalQuantity) {
        totalQuantity = parseFloat(totalQuantity);
    } else {
        totalQuantity = S3.supply.oldQuantity || 0;
    }

    // Attach to the top-level element to catch newly-created readRows
    inlineComponent.on('click.s3', '.inline-edt', function() {
        binQuantity = oldBinQuantityField.val();
        if (binQuantity) {
            binQuantity = parseFloat(binQuantity);
        } else {
            binQuantity = 0;
        }
        // Make this Bin's Quantity available
        binnedQuantity = binnedQuantity - binQuantity;
    });

    editBinBtnOK.click(function() {
        binQuantity = oldBinQuantityField.val();
        if (binQuantity) {
            binQuantity = parseFloat(binQuantity);
        } else {
            binQuantity = 0;
        }
        // Make this Bin's Quantity unavailable
        binnedQuantity = binnedQuantity + binQuantity;
        // Validate the new bin again
        newBinQuantityField.change();
    });

    totalQuantityField.change(function() {
        totalQuantity = totalQuantityField.val();
        if (totalQuantity) {
            totalQuantity = parseFloat(totalQuantity);
        } else {
            totalQuantity = S3.supply.oldQuantity || 0;
        }
        if (totalQuantity < binnedQuantity) {
            // @ToDo: i18n
            message = 'Total Quantity reduced to Quantity in Bins';
            error = $('<div class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
            totalQuantityField.val(binnedQuantity)
                              .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                $(this).fadeOut('slow').remove();
                return false;
            });
        }
        // Validate the new bin again
        newBinQuantityField.change();
    });

    newBinQuantityField.change(function() {
        binQuantity = newBinQuantityField.val();
        if (binQuantity) {
            binQuantity = parseFloat(binQuantity);
        } else {
            binQuantity = 0;
        }
        availableQuantity = totalQuantity - binnedQuantity;
        if (binQuantity > availableQuantity) {
            // @ToDo: i18n
            message = 'Bin Quantity reduced to Available Quantity';
            error = $('<div class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
            newBinQuantityField.val(availableQuantity)
                               .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                $(this).fadeOut('slow').remove();
                return false;
            });
        }
    });

    oldBinQuantityField.change(function() {
        binQuantity = oldBinQuantityField.val();
        if (binQuantity) {
            binQuantity = parseFloat(binQuantity);
        } else {
            binQuantity = 0;
        }
        availableQuantity = totalQuantity - binnedQuantity;
        if (binQuantity > availableQuantity) {
            // @ToDo: i18n
            message = 'Bin Quantity reduced to Available Quantity';
            error = $('<div class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
            oldBinQuantityField.val(availableQuantity)
                               .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                $(this).fadeOut('slow').remove();
                return false;
            });
        }
    });

    inlineComponent.on('rowAdded', function(event, row) {
        // Make Quantity unavailable
        binnedQuantity = binnedQuantity + parseFloat(row.quantity.value);
    });

    inlineComponent.on('rowRemoved', function(event, row) {
        // Make Quantity available
        binnedQuantity = binnedQuantity - parseFloat(row.quantity.value);
    });

});