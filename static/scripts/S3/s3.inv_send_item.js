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
        var inv_items = S3.supply.inv_items,
            ajaxURL,
            availableQuantity, // Quantity available of current Pack
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
            editBinBtnOK = $('#rdy-defaultbin-0'),
            error,
            errorField = $('#quantity__error'),
            i,
            inlineComponent = $('#sub-defaultsend_bin'),
            InvQuantity, // Available Stock. Needs to be multiplied by InvPackQuantity for comparisons
            InvPackQuantity,
            ItemPackField = $('#inv_track_item_item_pack_id'),
            newBinField = $('#sub_defaultsend_bin_defaultsend_bin_i_layout_id_edit_none'),
            newBinQuantityField = $('#sub_defaultsend_bin_defaultsend_bin_i_quantity_edit_none'),
            newTree = $('#sub_defaultsend_bin_defaultsend_bin_i_layout_id_edit_none-hierarchy'),
            oldBinField = $('#sub_defaultsend_bin_defaultsend_bin_i_layout_id_edit_0'),
            oldBinQuantityField = $('#sub_defaultsend_bin_defaultsend_bin_i_quantity_edit_0'),
            opt,
            pack,
            PackQuantity,
            PackName,
            piece,
            QuantityField = $('#inv_track_item_quantity'),
            ReqItemRow = $('#inv_track_item_req_item_id__row'),
            selected,
            siteID = S3.supply.site_id,
            startingInvItemID = invItemField.val(),
            startingQuantity, // Needs to be multiplied by startingPackQuantity for comparisons
            startingPackID,
            startingPackQuantity,
            stockQuantity, // Available Stock of current Pack
            totalQuantity, // Value in QuantityField
            trees = $('div[id^="sub_defaultsend_bin_defaultsend_bin_i_layout_id"].s3-hierarchy-widget'); // There will be 3

        if (ReqItemRow.length) {
            // Hide it by Default
            ReqItemRow.hide();
        }

        var updateBinQuantity = function() {
            // Runs when binsLength == 1
            // Show the Bins
            binRow.show();
            // Populate the Bin Quantity field
            binStockQuantity = bins[0].q; // Inv qty in Bin
            if ((binStockQuantity * InvPackQuantity) > (totalQuantity * PackQuantity)) {
                newBinQuantityField.val(totalQuantity);
            } else {
                newBinQuantityField.val(binStockQuantity * InvPackQuantity / PackQuantity);
            }
        };

        var InvItemChange = function(event, update) {
            // Update the available packs for this item
            // Display the number of these items available in this site's inventory

            var inv_item_id = invItemField.val();

            // Remove old Elements
            ItemPackField.html('');
            if (update) {
                 // Don't clear for update forms
            } else {
                QuantityField.val('');
                totalQuantity = 0;
                // Empty the Bins field
                inlineComponent.inlinecomponent('removeRows');
                binnedQuantity = 0;
            }
            $('#TotalQuantity').remove();

            // @ToDo: When sites have a very large number of items:
            //if (!inv_items || !inv_items[inv_item_id]) {read data for this item via AJAX call & cache}

            var data = inv_items[inv_item_id],
                defaultPack,
                packs = data.p,
                packsLength = packs.length,
                req_items = data.r,
                updateSendQuantity;

            InvQuantity = data.q;

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
                if (startingPackID && (startingInvItemID == inv_item_id) && (startingPackID == pack.i)) {
                    startingPackQuantity = pack.q;
                    PackQuantity = pack.q;
                    PackName = pack.n;
                    selected = ' selected';
                } else if (defaultPack) {
                    PackQuantity = pack.q;
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

            bins = data.b;
            binsLength = bins.length;
            if (binsLength == 0) {
                // Not Binned
                // Hide the Bins
                binRow.hide();
            } else if (binsLength == 1) {
                // Show the Bins
                binRow.show();
                // Populate the Bin fields
                updateBinQuantity();
                var onTreeReady = function() {
                    newTree.hierarchicalopts('set', [bins[0].l]);
                    // Make read-only
                    newBinQuantityField.attr('disabled', 'disabled');
                    $('#add-row-defaultsend_bin > .subform-action').hide();
                    newTree.next('.s3_inline_add_resource_link').hide();
                    $('.s3-hierarchy-button').attr('disabled','disabled');
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
            } else {
                // Split across multiple Bins
                binsByID = {};
                for (i = 0; i < binsLength; i++) {
                    bin = bins[i];
                    binsByID[bin.l] = bin.q;
                }
                // Show the Bins
                binRow.show();
                var onTreeReady = function() {
                    // Make read-write
                    newBinQuantityField.removeAttr('disabled');
                    $('#add-row-defaultsend_bin > .subform-action').show();
                    newTree.next('.s3_inline_add_resource_link').show();
                    $('.s3-hierarchy-button').removeAttr('disabled');
                    // Filter to the available bins
                    // @ToDo: Make 1 server-side call & apply results to all 3 trees
                    ajaxURL = S3.Ap.concat('/org/site/' + siteID + '/layout/hierarchy.tree?inv_item_id=' + inv_item_id);
                    trees.hierarchicalopts('reload', ajaxURL);
                    // Manage the allocations from where the items are pulled
                    // - see s3.inv_adj_item.js
                    // have this be optional & allow automation in form postprocess? Visible via both screen & picklist.xls
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
                if (startingQuantity && (startingInvItemID == inv_item_id)) {
                    stockQuantity += (startingQuantity * startingPackQuantity / PackQuantity);
                }
            }

            // Display Available Stock Quantity
            var TotalQuantity = '<span id="TotalQuantity"> / ' + stockQuantity.toFixed(2) + ' ' + PackName + ' (' + i18n.in_inv + ')</span>';
            QuantityField.after(TotalQuantity);

            if (req_items) {
                var req_item = req_items[0];

                // Update Send Quantity
                updateSendQuantity = function() {
                    if (req_items.length == 1) {
                        if (startingQuantity && (startingInvItemID == inv_item_id)) {
                            // Keep what we have
                        } else {
                            // Default to REQ Quantity
                            var ReqQuantity = req_item.q / PackQuantity;
                            if (ReqQuantity <= stockQuantity) {
                                // We can send the full quantity requested
                                QuantityField.val(ReqQuantity);
                            } else {
                                // We can only send what we have in stock!
                                QuantityField.val(stockQuantity);
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
                        for (i = 0; i < req_items.length; i++) {
                            req_item = req_items[i];
                            ReqItemField.append(new Option(req_item.r, req_item.i));
                            if (req_item_id) {
                                if (req_item.i == req_item_id) {
                                    if (startingQuantity && (startingInvItemID == inv_item_id)) {
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
                            for (i = 0; i < req_items.length; i++) {
                                req_item = req_items[i];
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

            if (packsLength > 1) {
                var item_pack_id;
                ItemPackField.on('change', function() {
                    item_pack_id = parseInt(ItemPackField.val());
                    for (i = 0; i < packsLength; i++) {
                        pack = packs[i]
                        if (pack.i == item_pack_id) {
                            PackQuantity = pack.q;
                            PackName = pack.n;
                            // Calculate Available Stock Quantity for this Pack
                            stockQuantity = InvQuantity * InvPackQuantity / PackQuantity;
                            if (startingQuantity && (startingInvItemID == inv_item_id)) {
                                stockQuantity += (startingQuantity * startingPackQuantity / PackQuantity);
                            }

                            // Display Available Stock Quantity
                            $('#TotalQuantity').html(stockQuantity.toFixed(2) + ' ' + PackName + ' (' + i18n.in_inv + ')');

                            if (req_items) {
                                // Update Send Quantity
                                updateSendQuantity();
                            }

                            break;
                        }
                    }
                });
            }
        };

        invItemField.on('change.s3', InvItemChange);

        if (startingInvItemID) {
            // Update form
            if (binnedQuantity == 0) {
                binnedQuantity = oldBinQuantityField.val();
                if (binnedQuantity) {
                    binnedQuantity = parseFloat(binnedQuantity) * InvPackQuantity / PackQuantity;
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
            startingPackID = parseInt(ItemPackField.val());
            invItemField.trigger('change.s3', true);
        }

        QuantityField.change(function() {
            totalQuantity = QuantityField.val();
            if (totalQuantity) {
                totalQuantity = parseFloat(totalQuantity);
                // Cleanup any old error message
                $('#inv_track_item_quantity-error').remove();
            } else {
                totalQuantity = 0;
            }
            if (totalQuantity > stockQuantity) {
                // @ToDo: i18n
                message = 'Total Quantity reduced to Quantity in Stock';
                error = $('<div id="inv_track_item_quantity-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                QuantityField.val(stockQuantity)
                             .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                    $(this).fadeOut('slow').remove();
                    return false;
                });
                totalQuantity = stockQuantity;
            }
            if (binsLength == 1) {
                // Update the Bin Quantity field
                updateBinQuantity();
            } else if (binsLength > 1) {
                binnedQuantityPacked = binnedQuantity * InvPackQuantity / PackQuantity;
                if (totalQuantity < binnedQuantityPacked) {
                    // @ToDo: i18n
                    message = 'Total Quantity increased to Quantity in Bins';
                    error = $('<div id="inv_track_item_quantity-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                    QuantityField.val(binnedQuantityPacked)
                                 .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                        $(this).fadeOut('slow').remove();
                        return false;
                    });
                }
                // Validate the new bin again
                newBinQuantityField.change();
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
                            message = 'Bin Quantity reduced to Quantity of Stock in Bin';
                            error = $('<div id="sub_defaultsend_bin_defaultsend_bin_i_quantity_edit_none-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                            newBinQuantityField.val(binStockQuantityPacked)
                                               .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                                $(this).fadeOut('slow').remove();
                                return false;
                            });
                            binQuantity = binStockQuantityPacked;
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
                            message = 'Bin Quantity reduced to Quantity of Stock in Bin';
                            error = $('<div id="sub_defaultsend_bin_defaultsend_bin_i_quantity_edit_0-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                            oldBinQuantityField.val(binStockQuantityPacked)
                                               .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                                $(this).fadeOut('slow').remove();
                                return false;
                            });
                            binQuantity = binStockQuantityPacked;
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
                } else {
                    binQuantity = 0;
                }
                // Make this Bin's Quantity available
                binnedQuantity -= (binQuantity * PackQuantity / InvPackQuantity);
            }
        });

        editBinBtnOK.click(function() {
            if (binsLength > 1) {
                binQuantity = oldBinQuantityField.val();
                if (binQuantity) {
                    binQuantity = parseFloat(binQuantity);
                } else {
                    binQuantity = 0;
                }
                // Make this Bin's Quantity unavailable
                binnedQuantity = binnedQuantity + (binQuantity * PackQuantity / InvPackQuantity);
                // Validate the new bin again
                newBinQuantityField.change();
            }
        });

        inlineComponent.on('rowAdded', function(event, row) {
            if (binsLength > 1) {
                // Make Quantity unavailable
                binQuantity = row.quantity.value;
                if (binQuantity) {
                    binQuantity = parseFloat(binQuantity);
                    binnedQuantity = binnedQuantity + (binQuantity * PackQuantity / InvPackQuantity);
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
                    binnedQuantity = binnedQuantity - (binQuantity * PackQuantity / InvPackQuantity);
                }
            }
        });
    }

});