/**
 * Used by the inv/inv_item controller when direct_stock_edits are allowed
 * - Limit to Bins from the relevant Site
 * - Validate the Bin Quantity
 */

$(document).ready(function() {
    var ajaxURL,
        availableQuantity,
        binQuantity,
        binnedQuantity = S3.supply.binnedQuantity || 0,
        error,
        inlineComponent = $('#sub-defaultbin'),
        createButtons = $('a[id^="inv"].s3_add_resource_link'), // There will be 3 if we have permission to create new Bins
        editBinBtnOK = $('#rdy-defaultbin-0'),
        newBinQuantityField = $('#sub_defaultbin_defaultbin_i_quantity_edit_none'),
        re = /%5Bid%5D/g,
        oldBinQuantityField = $('#sub_defaultbin_defaultbin_i_quantity_edit_0'),
        siteField = $('#inv_inv_item_site_id'),
        oldSiteID = siteField.val(),
        totalQuantityField = $('#inv_inv_item_quantity'),
        totalQuantity = totalQuantityField.val(),
        siteID,
        $this,
        trees = $('div[id^="sub_defaultbin_defaultbin_i_layout_id"].s3-hierarchy-widget'); // There will be 3

    siteField.change(function() {
        // Remove all Bin allocations
        inlineComponent.inlinecomponent('removeRows');
        siteID = siteField.val();
        ajaxURL = S3.Ap.concat('/org/site/' + siteID + '/layout/hierarchy.tree');
        trees.hierarchicalopts('reload', ajaxURL);
        createButtons.each(function() {
            $this = $(this);
            if (oldSiteID) {
                ajaxURL = $this.attr('href').replace(oldSiteID, siteID);
            } else {
                ajaxURL = $this.attr('href').replace(re, siteID);
            }
            $this.attr('href', ajaxURL);
        });
        oldSiteID = siteID;
    });

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