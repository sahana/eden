/**
 * Used by the inv/send controller
 * - replace filterOptionsS3 to show item packs for Inv Item
 * - show available Stock
 * - set req_item_id
 */

$(document).ready(function() {

   var invItemField = $('#inv_track_item_send_inv_item_id');

    if (invItemField.length) {

        var ItemPackField = $('#inv_track_item_item_pack_id'),
            QuantityField = $('#inv_track_item_quantity'),
            ReqItemRow = $('#inv_track_item_req_item_id__row'),
            startingInvItemID = invItemField.val(),
            startingQuantity,
            startingPackID;

        if (ReqItemRow.length) {
            // Hide it by Default
            ReqItemRow.hide();
        }

        var InvItemChange = function(event, update) {
            // Update the available packs for this item
            // Display the number of these items available in this site's inventory

            var inv_item_id = invItemField.val(),
                startingPackQuantity;

            // Remove old Items
            ItemPackField.html('');
            if (update) {
                 // Don't clear for update forms
            } else {
                QuantityField.val('');
            }
            $('#TotalQuantity').remove();

            if (inv_item_id === '') {
                // No Inv Item available yet
                return
            }

            var elementID = $(this).attr('id');

            // Cancel previous AJAX request
            try {S3.JSONRequest[elementID].abort();} catch(err) {}

            var inv_items = S3.supply.inv_items;
            if (undefined === inv_items) {
                // Lookup data via AJAX
                if ($('#item_pack_throbber').length === 0) {
                    ItemPackField.after('<div id="item_pack-throbber" class="throbber"/>');
                }
                var url = S3.Ap.concat('/inv/inv_item_quantity.json/' + inv_item_id);

                // Save JSON Request by element id
                S3.JSONRequest[elementID] = $.getJSON(url, function(data) {

                    var errorField = $('#quantity__error'),
                        first = true,
                        i,
                        InvQuantity = data.quantity,
                        opt,
                        PackQuantity,
                        PackName,
                        pack,
                        packs = data.packs,
                        packsLength = packs.length,
                        piece,
                        Quantity,
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
                        if (startingPackID && (startingInvItemID == inv_item_id) && (startingPackID == pack.id)) {
                            startingPackQuantity = pack.quantity;
                            PackQuantity = pack.quantity;
                            PackName = pack.name;
                            selected = ' selected';
                        } else if (first) {
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

                    $('#item_pack-throbber').remove();

                    if (errorField.length) {
                        // Read the value from the error
                        var words = errorField.html().split(' ');
                        for (i = 0; i < words.length; i++) {
                            Quantity = parseFloat(words[i]);
                            if (Quantity) {
                                break;
                            }
                        }
                    } else {
                        // Calculate Available Stock Quantity for this Pack
                        Quantity = InvQuantity / PackQuantity; // inv_quantity includes inv_pack_quantity
                        if (startingQuantity && (startingInvItemID == inv_item_id)) {
                            Quantity += (startingQuantity * startingPackQuantity / PackQuantity);
                        }
                    }

                    // Display Available Stock Quantity
                    var TotalQuantity = '<span id="TotalQuantity"> / ' + Quantity.toFixed(2) + ' ' + PackName + ' (' + i18n.in_inv + ')</span>';
                    QuantityField.after(TotalQuantity);

                    if (packsLength > 1) {
                        var item_pack_id;
                        ItemPackField.on('change', function() {
                            item_pack_id = parseInt(ItemPackField.val());
                            for (i = 0; i < packsLength; i++) {
                                pack = packs[i]
                                if (pack.id == item_pack_id) {
                                    PackQuantity = pack.quantity;
                                    PackName = pack.name;
                                    // Calculate Available Stock Quantity for this Pack
                                    Quantity = InvQuantity / PackQuantity;
                                    if (startingQuantity && (startingInvItemID == inv_item_id)) {
                                        Quantity += (startingQuantity * startingPackQuantity / PackQuantity);
                                    }

                                    // Display Available Stock Quantity
                                    $('#TotalQuantity').html(Quantity.toFixed(2) + ' ' + PackName + ' (' + i18n.in_inv + ')');
                                    break;
                                }
                            }
                        });
                    }
                });
            } else {
                // Use data provided from inv_send_controller
                // - Pack Options
                // - Available Stock Quantity
                // - REQ Quantity
                // - req_item_id

                var data = inv_items[inv_item_id],
                    errorField = $('#quantity__error'),
                    first = true,
                    i,
                    opt,
                    pack,
                    packs = data.packs,
                    packsLength = packs.length,
                    PackQuantity,
                    PackName,
                    piece,
                    req_items = data.req_items,
                    req_item = req_items[0],
                    selected,
                    InvQuantity = req_item.inv_quantity;

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
                    if (startingPackID && (startingInvItemID == inv_item_id) && (startingPackID == pack.id)) {
                        startingPackQuantity = pack.quantity;
                        PackQuantity = pack.quantity;
                        PackName = pack.name;
                        selected = ' selected';
                    } else if (first) {
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

                if (errorField.length) {
                    // Read the value from the error
                    var words = errorField.html().split(' ');
                    for (i = 0; i < words.length; i++) {
                        Quantity = parseFloat(words[i]);
                        if (Quantity) {
                            break;
                        }
                    }
                } else {
                    // Calculate Available Stock Quantity for this Pack
                    // - inv_quantity will be the same in every row
                    var Quantity = InvQuantity / PackQuantity; // inv_quantity includes inv_pack_quantity
                    if (startingQuantity && (startingInvItemID == inv_item_id)) {
                        Quantity += (startingQuantity * startingPackQuantity / PackQuantity);
                    }
                }

                // Display Available Stock Quantity
                var TotalQuantity = '<span id="TotalQuantity"> / ' + Quantity.toFixed(2) + ' ' + PackName + ' (' + i18n.in_inv + ')</span>';
                QuantityField.after(TotalQuantity);

                // Update Send Quantity
                var updateSendQuantity = function() {
                    if (req_items.length == 1) {
                        if (startingQuantity && (startingInvItemID == inv_item_id)) {
                            // Keep what we have
                        } else {
                            // Default to REQ Quantity
                            var ReqQuantity = req_item.req_quantity / PackQuantity;
                            if (ReqQuantity <= Quantity) {
                                // We can send the full quantity requested
                                QuantityField.val(ReqQuantity);
                            } else {
                                // We can only send what we have in stock!
                                QuantityField.val(Quantity);
                            }
                        }

                        // Set req_item_id, so that we can track request fulfilment
                        $('#inv_track_item_req_item_id').val(req_item.req_item_id);

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
                            ReqItemField.append(new Option(req_item.req_ref, req_item.req_item_id));
                            if (req_item_id) {
                                if (req_item.req_item_id == req_item_id) {
                                    if (startingQuantity && (startingInvItemID == inv_item_id)) {
                                        // Keep what we have
                                    } else {
                                        // Default to REQ Quantity
                                        ReqQuantity = req_item.req_quantity / PackQuantity;
                                        if (ReqQuantity <= Quantity) {
                                            // We can send the full quantity requested
                                            QuantityField.val(ReqQuantity);
                                        } else {
                                            // We can only send what we have in stock!
                                            QuantityField.val(Quantity);
                                        }
                                    }
                                }
                            } else if (first) {
                                ReqQuantity = req_item.req_quantity / PackQuantity;
                                if (ReqQuantity <= Quantity) {
                                    // We can send the full quantity requested
                                    QuantityField.val(ReqQuantity);
                                } else {
                                    // We can only send what we have in stock!
                                    QuantityField.val(Quantity);
                                }
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
                                    if (ReqQuantity <= Quantity) {
                                        // We can send the full quantity requested
                                        QuantityField.val(ReqQuantity);
                                    } else {
                                        // We can only send what we have in stock!
                                        QuantityField.val(Quantity);
                                    }
                                    break;
                                }
                            }
                        });
                    }
                }

                updateSendQuantity();

                if (packsLength > 1) {
                    var item_pack_id;
                    ItemPackField.on('change', function() {
                        item_pack_id = parseInt(ItemPackField.val());
                        for (i = 0; i < packsLength; i++) {
                            pack = packs[i]
                            if (pack.id == item_pack_id) {
                                PackQuantity = pack.quantity;
                                PackName = pack.name;
                                // Calculate Available Stock Quantity for this Pack
                                Quantity = InvQuantity / PackQuantity;
                                    if (startingQuantity && (startingInvItemID == inv_item_id)) {
                                        Quantity += (startingQuantity * startingPackQuantity / PackQuantity);
                                    }

                                // Display Available Stock Quantity
                                $('#TotalQuantity').html(Quantity.toFixed(2) + ' ' + PackName + ' (' + i18n.in_inv + ')');

                                // Update Send Quantity
                                updateSendQuantity();
                                break;
                            }
                        }
                    });
                }
            }
        };

        invItemField.on('change.s3', InvItemChange);

        if (startingInvItemID) {
            // Update form
            startingQuantity = QuantityField.val();
            if (startingQuantity) {
                startingQuantity = parseFloat(startingQuantity);
            }
            startingPackID = parseInt(ItemPackField.val());
            invItemField.trigger('change.s3', true);
        }
    }

});