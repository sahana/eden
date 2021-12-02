/**
 * Used by the inv/inv_item or <site_instance>/inv_item controller when direct_stock_edits are allowed
 * - Limit to Bins from the relevant Site (inv/inv_item)
 * - Validate the Bin Quantity
 */

$(document).ready(function() {

    var ItemField = $('#inv_inv_item_item_id');

    if (ItemField.length) {
        var ajaxURL,
            allPacks = S3.supply.packs || {},
            availableQuantity,
            binQuantity,
            binnedQuantity = S3.supply.binnedQuantity || 0, // Needs to be multiplied by startingPackQuantity for comparisons.
            binnedQuantityPacked, // Quantity binned of current Pack
            error,
            first,
            inlineComponent = $('#sub-defaultbin'),
            inlineComponentInput = $('#inv_inv_item_sub_defaultbin'),
            itemID = ItemField.val(),
            ItemPackField = $('#inv_inv_item_item_pack_id'),
            itemPackID,
            newBinQuantityField = $('#sub_defaultbin_defaultbin_i_quantity_edit_none'),
            // Represent numbers with thousand separator
            // @ToDo: Respect settings
            numberFormat = /(\d)(?=(\d{3})+(?!\d))/g,
            oldBinQuantityField = $('#sub_defaultbin_defaultbin_i_quantity_edit_0'),
            oldPackQuantity,
            pack,
            packs,
            packsByID,
            packsLength,
            PackQuantity,
            siteField = $('#inv_inv_item_site_id'),
            startingQuantity, // Needs to be multiplied by startingPackQuantity for comparisons
            startingPackID = S3.supply.itemPackID,
            startingPackQuantity = 1,
            totalQuantityField = $('#inv_inv_item_quantity'),
            totalQuantity = totalQuantityField.val(), // Needs to be multiplied by PackQuantity for comparisons
            $this,
            updatePacks,
            updateQuantity;

        if (siteField.length) {
            // inv/inv_item
            var createButtons = $('a[id^="inv"].s3_add_resource_link'), // There will be 3 if we have permission to create new Bins
                re = /%5Bid%5D/g,
                oldSiteID = siteField.val(),
                siteID,
                trees = $('div[id^="sub_defaultbin_defaultbin_i_layout_id"].s3-hierarchy-widget'); // There will be 3

            if (trees.length) {
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
            }
        }

        updatePacks = function(update) {
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

        ItemField.on('change.s3', function(event, update) {
            itemID = ItemField.val();
            // Replace filterOptionsS3
            packs = allPacks[itemID];
            if (packs) {
                // We have cached data
                updatePacks(update);
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

        totalQuantityField.change(function() {
            totalQuantity = totalQuantityField.val();
            if (totalQuantity) {
                totalQuantity = parseFloat(totalQuantity);
            } else {
                totalQuantity = 0;
            }
            binnedQuantityPacked = binnedQuantity * startingPackQuantity / PackQuantity;
            if (totalQuantity < binnedQuantityPacked) {
                // @ToDo: i18n
                message = 'Total Quantity reduced to Quantity in Bins';
                error = $('<div class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                totalQuantityField.val(binnedQuantityPacked)
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
                binnedQuantityPacked = binnedQuantity * startingPackQuantity / PackQuantity;
                availableQuantity = totalQuantity - binnedQuantityPacked;
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
                    message = 'Bin Quantity reduced to Available Quantity';
                    error = $('<div class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
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
            newBinQuantityField.change();
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