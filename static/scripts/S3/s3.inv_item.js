/**
 * Used by the inv/inv_item controller when direct_stock_edits are allowed
 * - Limit to Bins from the relevant Site
 * - Validate the Bin Quantity
 */

$(document).ready(function() {
    var ajaxURL,
        createButton = $('#inv_inv_item_bin_layout_id-create-btn'),
        newBinQuantityField = $('#sub_defaultbin_defaultbin_i_quantity_edit_none'),
        re = /%5Bid%5D/g,
        siteField = $('#inv_inv_item_site_id'),
        oldSiteID,
        siteID,
        tree = $('#inv_inv_item_bin_layout_id-hierarchy');

    siteField.change(function() {
        siteID = siteField.val();
        ajaxURL = S3.Ap.concat('/org/site/' + siteID + '/layout/hierarchy.tree');
        tree.hierarchicalopts('reload', ajaxURL);
        if (createButton.length) {
            if (oldSiteID) {
                ajaxURL = createButton.attr('href').replace(oldSiteID, siteID);
            } else {
                ajaxURL = createButton.attr('href').replace(re, siteID);
            }
            createButton.attr('href', ajaxURL);
            oldSiteID = siteID;
        }
    });

    if (newBinQuantityField.length) {
        var alert,
            availableQuantity,
            binQuantity,
            binnedQuantity = S3.supply.binnedQuantity || 0,
            editBinBtnOK = $('#rdy-defaultbin-0');
            inlineComponent = $('#sub-defaultbin'),
            oldBinQuantityField = $('#sub_defaultbin_defaultbin_i_quantity_edit_0'),
            totalQuantityField = $('#inv_inv_item_quantity'),
            totalQuantity = totalQuantityField.val();

        if (totalQuantity) {
            totalQuantity = parseFloat(totalQuantity);
        } else {
            totalQuantity = 0;
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
                totalQuantity = 0;
            }
            if (totalQuantity < binnedQuantity) {
                // @ToDo: i18n
                message = 'Total Quantity reduced to Quantity in Bins';
                alert = $('<div class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                totalQuantityField.val(binnedQuantity)
                                  .parent().append(alert).undelegate('.s3').delegate('.alert', 'click.s3', function() {
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
                alert = $('<div class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                newBinQuantityField.val(availableQuantity)
                                   .parent().append(alert).undelegate('.s3').delegate('.alert', 'click.s3', function() {
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
                alert = $('<div class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                oldBinQuantityField.val(availableQuantity)
                                   .parent().append(alert).undelegate('.s3').delegate('.alert', 'click.s3', function() {
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
    }

});