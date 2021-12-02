/**
 * Used by the inv/send controller
 * - replace filterOptionsS3 to show item packs for Inv Item
 * - show available Stock
 * - set/filter Bins
 * - set req_item_id
 */

$(document).ready(function() {

   var invItemField = $('#inv_track_item_send_inv_item_id');

    if (invItemField.length) {

        // Use data provided from inv_send_controller
        // - Pack Options
        // - Available Stock Quantity
        // - REQ Quantity
        // - req_item_id
        var availableQuantity, // Quantity available of current Pack
            bin,
            binQuantity,
            binnedQuantity = S3.supply.binnedQuantity || 0, // Needs to be multiplied by InvPackQuantity for comparisons. Unused when binsLength == 0-1
            binnedQuantityPacked, // Quantity binned of current Pack
            binRow = $('#inv_track_item_sub_defaultsend_bin__row'),
            binStockQuantity, // Available Stock in this bin. Needs to be multiplied by InvPackQuantity for comparisons
            binStockQuantityPacked, // Available Stock in this bin of current Pack
            bins,
            binsByID,
            binsLength,
            error,
            errorField = $('#quantity__error'),
            i,
            inlineComponent = $('#sub-defaultsend_bin'),
            inlineComponentInput = $('#inv_track_item_sub_defaultsend_bin'),
            invItemID,
            invItems = S3.supply.inv_items,
            InvQuantity, // Available Stock. Needs to be multiplied by InvPackQuantity for comparisons
            InvPackQuantity,
            ItemPackField = $('#inv_track_item_item_pack_id'),
            itemPackID,
            newBinField = $('#sub_defaultsend_bin_defaultsend_bin_i_layout_id_edit_none'),
            newBinQuantityField = $('#sub_defaultsend_bin_defaultsend_bin_i_quantity_edit_none'),
            newTree = $('#sub_defaultsend_bin_defaultsend_bin_i_layout_id_edit_none-hierarchy'),
            // Represent numbers with thousand separator
            // @ToDo: Respect settings
            numberFormat = /(\d)(?=(\d{3})+(?!\d))/g,
            oldBinField = $('#sub_defaultsend_bin_defaultsend_bin_i_layout_id_edit_0'),
            oldBinQuantityField = $('#sub_defaultsend_bin_defaultsend_bin_i_quantity_edit_0'),
            oldPackQuantity,
            oldTree = $('#sub_defaultsend_bin_defaultsend_bin_i_layout_id_edit_0-hierarchy'),
            opt,
            pack,
            PackQuantity,
            PackName,
            packs,
            packsLength,
            piece,
            QuantityField = $('#inv_track_item_quantity'),
            ReqItemRow = $('#inv_track_item_req_item_id__row'),
            reqItems,
            selected,
            siteID = S3.supply.site_id,
            startingInvItemID = invItemField.val(),
            startingQuantity, // Needs to be multiplied by startingPackQuantity for comparisons
            startingPackID = S3.supply.itemPackID,
            startingPackQuantity = 1,
            stockQuantity, // Available Stock of current Pack
            totalQuantity, // Value in QuantityField
            trees = $('div[id^="sub_defaultsend_bin_defaultsend_bin_i_layout_id"].s3-hierarchy-widget'), // There will be 3
            update,
            updateBinQuantity,
            updateQuantity,
            updateSendQuantity;

        if (ReqItemRow.length) {
            // Hide it by Default
            ReqItemRow.hide();
        }

        updateBinQuantity = function() {
            // Runs when binsLength == 1
            if (update) {
                // Update the Bin Quantity field
                updateQuantity = function(row) {
                    row.quantity.value = totalQuantity;
                    row.quantity.text = totalQuantity.toString().replace(numberFormat, '$1,');
                };
                inlineComponent.inlinecomponent('updateRows', updateQuantity);
                // Hide the buttons again
                $('#edt-defaultsend_bin-0').hide();
                $('#rmv-defaultsend_bin-0').hide();
            } else {
                // Show the Bins
                binRow.show();
                // Populate the Bin Quantity field
                binStockQuantity = binsByID[bins[0]]; // Inv qty in Bin
                if ((binStockQuantity * InvPackQuantity) > (totalQuantity * PackQuantity)) {
                    newBinQuantityField.val(totalQuantity);
                } else {
                    newBinQuantityField.val(binStockQuantity * InvPackQuantity / PackQuantity);
                }
            }
        };

        var InvItemChange = function(event, first) {
            // Update the available packs for this item
            // Display the number of these items available in this site's inventory

            invItemID = invItemField.val();

            // Remove old Elements
            ItemPackField.html('');
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
            $('#TotalQuantity').remove();

            if (!invItemID) {
                return;
            }

            // @ToDo: When sites have a very large number of items:
            //if (!invItems || !invItems[invItemID]) {read data for this item via AJAX call to inv/inv_item_quantity & cache}

            var data = invItems[invItemID],
                defaultPack;

            InvQuantity = data.q;
            packs = data.p;
            packsLength = packs.length;
            reqItems = data.r;

            for (i = 0; i < packsLength; i++) {
                pack = packs[i];
                if (pack.q == 1) {
                    piece = pack.n;
                    break;
                }
            }

            // Update available Packs
            for (i = 0; i < packsLength; i++) {
                pack = packs[i];
                if (pack.d != undefined) {
                    defaultPack = true;
                    InvPackQuantity = pack.q;
                } else {
                    defaultPack = false;
                }
                if (startingPackID && (startingInvItemID == invItemID) && (startingPackID == pack.i)) {
                    itemPackID = pack.i;
                    oldPackQuantity = startingPackQuantity = PackQuantity = pack.q;
                    PackName = pack.n;
                    selected = ' selected';
                } else if (defaultPack) {
                    itemPackID = pack.i;
                    oldPackQuantity = PackQuantity = pack.q;
                    PackName = pack.n;
                    selected = ' selected';
                } else {
                    selected = '';
                }
                if (pack.q !== 1) {
                    opt = '<option value="' + pack.i + '"' + selected + '>' + pack.n + ' (' + pack.q + ' x ' + piece + ')</option>';
                } else {
                    opt = '<option value="' + pack.i + '"' + selected + '>' + pack.n + '</option>';
                }
                ItemPackField.append(opt);
            }
            if (first) {
                // Adjust the quantities now that the vars are defined
                binnedQuantity = binnedQuantity * InvPackQuantity / PackQuantity;
            }

            binsByID = data.b;
            bins = [];
            for (layoutID in binsByID) {
                bins.push(layoutID);
            }
            binsLength = bins.length;
            if (binsLength == 0) {
                // Not Binned
                // Hide the Bins
                binRow.hide();
            } else if (binsLength == 1) {
                if (update) {
                    // Hide the Add Row
                    $('#add-row-defaultsend_bin').hide();
                    // Hide the Buttons on the readRow
                    $('#read-row-defaultsend_bin-0 > .subform-action').hide();
                    // Prevent Editing
                    inlineComponent.off('click.inlinecomponent', '.read-row');
                } else {
                    // Populate the Bin fields
                    updateBinQuantity();
                    var onTreeReady = function() {
                        newTree.hierarchicalopts('set', [bins[0]]);
                        // Make read-only
                        newBinQuantityField.attr('disabled', true);
                        $('#add-row-defaultsend_bin > .subform-action').hide();
                        newTree.next('.s3_inline_add_resource_link').hide();
                        $('.s3-hierarchy-button').attr('disabled', true);
                    };
                    if (newTree.is(":data('s3-hierarchicalopts')")) {
                        // Tree is already ready
                        onTreeReady();
                    } else {
                        // We run before the hierarchicalopts so need to wait for tree to be ready
                        newTree.find('.s3-hierarchy-tree').first().on('ready.jstree', function() {
                            onTreeReady();
                        });
                    }
                }
            } else {
                // Split across multiple Bins
                // Show the Bins
                binRow.show();
                var onTreeReady = function() {
                    // Make read-write
                    newBinQuantityField.removeAttr('disabled');
                    $('#add-row-defaultsend_bin > .subform-action').show();
                    newTree.next('.s3_inline_add_resource_link').show();
                    $('.s3-hierarchy-button').removeAttr('disabled');
                    // Filter to the available bins
                    // - can be done client-side without any AJAX, as we have all the layout_ids
                    newTree.hierarchicalopts('show', bins, true);
                    oldTree.hierarchicalopts('show', bins, true);
                };
                if (newTree.is(":data('s3-hierarchicalopts')")) {
                    // Tree is already ready
                    onTreeReady();
                } else {
                    // We run before the hierarchicalopts so need to wait for tree to be ready
                    newTree.find('.s3-hierarchy-tree').first().on('ready.jstree', function() {
                        onTreeReady();
                    });
                }
            }

            if (errorField.length) {
                // Read the value from the error
                var words = errorField.html().split(' ');
                for (i = 0; i < words.length; i++) {
                    stockQuantity = parseFloat(words[i]);
                    if (stockQuantity) {
                        break;
                    }
                }
            } else {
                // Calculate Available Stock Quantity for this Pack
                stockQuantity = InvQuantity * InvPackQuantity / PackQuantity;
                if (startingQuantity && (startingInvItemID == invItemID)) {
                    stockQuantity += (startingQuantity * startingPackQuantity / PackQuantity);
                }
            }

            // Display Available Stock Quantity
            var TotalQuantity = '<span id="TotalQuantity"> / ' + stockQuantity.toFixed(2) + ' ' + PackName + ' (' + i18n.in_inv + ')</span>';
            QuantityField.after(TotalQuantity);

            if (reqItems) {
                var req_item = reqItems[0];

                // Update Send Quantity
                updateSendQuantity = function() {
                    if (reqItems.length == 1) {
                        if (startingQuantity && (startingInvItemID == invItemID)) {
                            // Keep what we have
                        } else {
                            // Default to REQ Quantity
                            var ReqQuantity = req_item.q / PackQuantity;
                            if (ReqQuantity <= stockQuantity) {
                                // We can send the full quantity requested
                                totalQuantity = ReqQuantity;
                            } else {
                                // We can only send what we have in stock!
                                totalQuantity = stockQuantity;
                            }
                            QuantityField.val(totalQuantity);
                            if (binsLength == 1) {
                                updateBinQuantity();
                            }
                        }

                        // Set req_item_id, so that we can track request fulfilment
                        $('#inv_track_item_req_item_id').val(req_item.i);

                    } else {
                        // Multiple Req Items for the same Inv Item
                        // Display ReqItemRow
                        ReqItemRow.show();
                        // Populate with Options
                        var ReqItemField = $('#inv_track_item_req_item_id'),
                            req_item_id = ReqItemField.val(),
                            ReqQuantity;
                        if (req_item_id) {
                            req_item_id = parseInt(req_item_id);
                        }
                        ReqItemField.html('');
                        for (i = 0; i < reqItems.length; i++) {
                            req_item = reqItems[i];
                            ReqItemField.append(new Option(req_item.r, req_item.i));
                            if (req_item_id) {
                                if (req_item.i == req_item_id) {
                                    if (startingQuantity && (startingInvItemID == invItemID)) {
                                        // Keep what we have
                                    } else {
                                        // Default to REQ Quantity
                                        ReqQuantity = req_item.q / PackQuantity;
                                        if (ReqQuantity <= stockQuantity) {
                                            // We can send the full quantity requested
                                            QuantityField.val(ReqQuantity);
                                        } else {
                                            // We can only send what we have in stock!
                                            QuantityField.val(stockQuantity);
                                        }
                                    }
                                }
                            } else if (first) {
                                ReqQuantity = req_item.q / PackQuantity;
                                if (ReqQuantity <= stockQuantity) {
                                    // We can send the full quantity requested
                                    QuantityField.val(ReqQuantity);
                                } else {
                                    // We can only send what we have in stock!
                                    QuantityField.val(stockQuantity);
                                }
                            }
                            first = false;
                        }
                        ReqItemField.on('change', function() {
                            // Update the Quantity accordingly
                            req_item_id = parseInt(ReqItemField.val());
                            for (i = 0; i < reqItems.length; i++) {
                                req_item = reqItems[i];
                                if (req_item.i == req_item_id) {
                                    ReqQuantity = req_item.q / PackQuantity;
                                    if (ReqQuantity <= stockQuantity) {
                                        // We can send the full quantity requested
                                        QuantityField.val(ReqQuantity);
                                    } else {
                                        // We can only send what we have in stock!
                                        QuantityField.val(stockQuantity);
                                    }
                                    break;
                                }
                            }
                        });
                    }
                }

                updateSendQuantity();
            }
        };

        invItemField.on('change.s3', InvItemChange);

        ItemPackField.on('change.s3', function() {
            itemPackID = parseInt(ItemPackField.val());
            for (i = 0; i < packsLength; i++) {
                pack = packs[i]
                if (pack.i == itemPackID) {
                    PackQuantity = pack.q;
                    PackName = pack.n;
                    // Calculate Available Stock Quantity for this Pack
                    stockQuantity = InvQuantity * InvPackQuantity / PackQuantity;
                    if (startingQuantity && (startingInvItemID == invItemID)) {
                        stockQuantity += (startingQuantity * startingPackQuantity / PackQuantity);
                    }

                    // Display Available Stock Quantity
                    $('#TotalQuantity').html(stockQuantity.toFixed(2) + ' ' + PackName + ' (' + i18n.in_inv + ')');

                    // Adjust Total Quantity
                    totalQuantity = QuantityField.val();
                    totalQuantity = totalQuantity * oldPackQuantity / PackQuantity;
                    QuantityField.val(totalQuantity);
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

                    if (reqItems) {
                        // Update Send Quantity
                        updateSendQuantity();
                    }

                    break;
                }
            }
        });

        if (startingInvItemID) {
            // Update form
            update = true
            if (binnedQuantity == 0) {
                binnedQuantity = oldBinQuantityField.val();
                if (binnedQuantity) {
                    // InvPackQuantity & PackQuantity not yet defined so do this in InvItemChange
                    //binnedQuantity = parseFloat(binnedQuantity) * InvPackQuantity / PackQuantity;
                    binnedQuantity = parseFloat(binnedQuantity);
                } else {
                    binnedQuantity = 0;
                }
            }
            startingQuantity = QuantityField.val();
            if (startingQuantity) {
                startingQuantity = parseFloat(startingQuantity);
                totalQuantity = startingQuantity;
            } else {
                totalQuantity = 0;
            }
            invItemField.trigger('change.s3', true);
        }

        QuantityField.change(function() {
            totalQuantity = QuantityField.val();
            if (totalQuantity) {
                totalQuantity = parseFloat(totalQuantity);
                // Cleanup any old error message
                $('#inv_track_item_quantity-warning').remove();
            } else {
                totalQuantity = 0;
            }
            message = null;
            if (totalQuantity > stockQuantity) {
                // @ToDo: i18n
                totalQuantity = stockQuantity;
                message = 'Total Quantity reduced to Quantity in Stock';
            } else if (totalQuantity < 0) {
                // @ToDo: i18n
                totalQuantity = 0;
                message = 'Total Quantity cannot be negative';
            }
            if (binsLength == 1) {
                // Update the Bin Quantity field
                updateBinQuantity();
            } else if (binsLength > 1) {
                binnedQuantityPacked = binnedQuantity * InvPackQuantity / PackQuantity;
                if (totalQuantity < binnedQuantityPacked) {
                    // @ToDo: i18n
                    totalQuantity = binnedQuantityPacked;
                    message = 'Total Quantity increased to Quantity in Bins';
                }
                // Validate the new bin again
                newBinQuantityField.change();
            }
            if (message) {
                error = $('<div id="inv_track_item_quantity-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                QuantityField.val(totalQuantity)
                             .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                    $(this).fadeOut('slow').remove();
                    return false;
                });
            }
        });

        newBinQuantityField.change(function() {
            if (binsLength > 1) {
                binQuantity = newBinQuantityField.val();
                if (binQuantity) {
                    binQuantity = parseFloat(binQuantity);
                    bin = newBinField.val();
                    if (bin) {
                        binStockQuantity = binsByID[bin]; // Inv qty in Bin
                        binStockQuantityPacked = binStockQuantity * InvPackQuantity / PackQuantity;
                        if (binQuantity > binStockQuantityPacked) {
                            // @ToDo: i18n
                            binQuantity = binStockQuantityPacked;
                            message = 'Bin Quantity reduced to Quantity of Stock in Bin';
                            error = $('<div id="sub_defaultsend_bin_defaultsend_bin_i_quantity_edit_none-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                            newBinQuantityField.val(binQuantity)
                                               .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                                $(this).fadeOut('slow').remove();
                                return false;
                            });
                        }
                    }
                    binnedQuantityPacked = binnedQuantity * InvPackQuantity / PackQuantity;
                    availableQuantity = totalQuantity - binnedQuantityPacked;
                    if (binQuantity > availableQuantity) {
                        // @ToDo: i18n
                        message = 'Bin Quantity reduced to Quantity remaining to be Sent';
                        error = $('<div id="sub_defaultsend_bin_defaultsend_bin_i_quantity_edit_none-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                        newBinQuantityField.val(availableQuantity)
                                           .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                            $(this).fadeOut('slow').remove();
                            return false;
                        });
                    }
                }
            }
        });

        oldBinQuantityField.change(function() {
            if (binsLength > 1) {
                binQuantity = oldBinQuantityField.val();
                if (binQuantity) {
                    binQuantity = parseFloat(binQuantity);
                    bin = oldBinField.val();
                    if (bin) {
                        binStockQuantity = binsByID[bin]; // Inv qty in Bin
                        binStockQuantityPacked = binStockQuantity * InvPackQuantity / PackQuantity;
                        if (binQuantity > binStockQuantityPacked) {
                            // @ToDo: i18n
                            binQuantity = binStockQuantityPacked;
                            message = 'Bin Quantity reduced to Quantity of Stock in Bin';
                            error = $('<div id="sub_defaultsend_bin_defaultsend_bin_i_quantity_edit_0-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                            oldBinQuantityField.val(binQuantity)
                                               .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                                $(this).fadeOut('slow').remove();
                                return false;
                            });
                        }
                    }
                    binnedQuantityPacked = binnedQuantity * InvPackQuantity / PackQuantity;
                    availableQuantity = totalQuantity - binnedQuantityPacked;
                    if (binQuantity > availableQuantity) {
                        // @ToDo: i18n
                        message = 'Bin Quantity reduced to Quantity remaining to be Sent';
                        error = $('<div id="sub_defaultsend_bin_defaultsend_bin_i_quantity_edit_0-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                        oldBinQuantityField.val(availableQuantity)
                                           .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                            $(this).fadeOut('slow').remove();
                            return false;
                        });
                    }
                }
            }
        });

        // Attach to the top-level element to catch newly-created readRows
        inlineComponent.on('click.s3', '.inline-edt', function() {
            if (binsLength > 1) {
                binQuantity = oldBinQuantityField.val();
                if (binQuantity) {
                    binQuantity = parseFloat(binQuantity);
                    // Make this Bin's Quantity available
                    binnedQuantity -= (binQuantity * PackQuantity / InvPackQuantity);
                }
            }
        });

        $('#rdy-defaultbin-0').click(function() {
            // read-only row has been opened for editing
            // - Tick clicked to save changes
            if (binsLength > 1) {
                binQuantity = oldBinQuantityField.val();
                if (binQuantity) {
                    binQuantity = parseFloat(binQuantity);
                    // Make this Bin's Quantity unavailable
                    binnedQuantity = binnedQuantity + (binQuantity * PackQuantity / InvPackQuantity);
                }
                // Validate the new bin again
                newBinQuantityField.change();
            }
        });

        inlineComponent.on('editCancelled', function(event, rowindex) {
            // read-only row has been opened for editing
            // - X clicked to cancel changes
            // Make Quantity unavailable
            binQuantity = parseFloat(inlineComponentInput.data('data').data[rowindex].quantity.value);
            binnedQuantity = binnedQuantity + binQuantity;
        });

        inlineComponent.on('rowAdded', function(event, row) {
            if (binsLength > 1) {
                // Make Quantity unavailable
                binQuantity = row.quantity.value;
                if (binQuantity) {
                    binQuantity = parseFloat(binQuantity);
                    binnedQuantity += (binQuantity * PackQuantity / InvPackQuantity);
                }
                // Cleanup any old warning message
                $('#sub_defaultsend_bin_defaultsend_bin_i_quantity_edit_none-warning').remove();
            }
        });

        inlineComponent.on('rowRemoved', function(event, row) {
            if (binsLength > 1) {
                // Make Quantity available
                binQuantity = row.quantity.value;
                if (binQuantity) {
                    binQuantity = parseFloat(binQuantity);
                    binnedQuantity -= (binQuantity * PackQuantity / InvPackQuantity);
                }
            }
        });
    }

});