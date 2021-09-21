/**
    Static JS Code related to Supply, Inv & Req
*/

S3.supply = Object();

/**
 * Globals called by filterOptionsS3 when Item Packs filtered based on Items
 */
S3.supply.fncPrepItem = function(data) {
    for (var i = 0; i < data.length; i++) {
        if (data[i].quantity == 1) {
            return data[i].name;
        }
    }
    return '';
}

S3.supply.fncRepresentItem = function(record, PrepResult) {
    if (record.quantity == 1) {
        return record.name;
    } else {
        return record.name + ' (' + record.quantity + ' x ' + PrepResult + ')';
    }
}

// ============================================================================
$(document).ready(function() {

    /**
     * Incoming Shipments
     * - Show/Hide fields according to Shipment Type
     */
    var InvRecvTypeChange = function() {
        var RecvType = $("#inv_recv_type").val();
        if (RecvType != undefined) {
            if ( RecvType == 11) { // @ToDo: pass this value instead of hardcoding it - base on s3cfg.py 
                // Internal Shipment 
                $('[id^="inv_recv_from_site_id__row"]').show();
                $('[id^="inv_recv_organisation_id__row"]').hide();
            } else if ( RecvType >= 32) { // @ToDo: pass this value instead of hardcoding it - base on s3cfg.py 
                // External Shipment: Donation, Purchase, Consignment, In-Transit
                $('[id^="inv_recv_from_site_id__row"]').hide();
                $('[id^="inv_recv_organisation_id__row"]').show();
            } else {
                // Unknown Type
                $('[id^="inv_recv_from_site_id__row"]').hide();
                $('[id^="inv_recv_organisation_id__row"]').hide();
            }
        }
    };

    InvRecvTypeChange();
    $('#inv_recv_type').change(InvRecvTypeChange);

    // ========================================================================
    /**
     * Outgoing Shipments
     * - replace filterOptionsS3 to show item packs for Inv Item
     * - show available Stock
     * - if data provided from global (currently just RMS) then also set req_item_id
     */

    var invItemField = $('#inv_track_item_send_inv_item_id'),
        ReqItemRow = $('#inv_track_item_req_item_id__row');

    if (ReqItemRow.length) {
        // Hide it by Default
        ReqItemRow.hide();
    }

    var InvItemIDChange = function() {
        // Update the available packs for this item
        // Display the number of these items available in this site's inventory

        var inv_item_id = invItemField.val(),
            ItemPackField = $('#inv_track_item_item_pack_id'),
            QuantityField = $('#inv_track_item_quantity');

        // Remove old Items
        ItemPackField.html('');
        QuantityField.val('');
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

                var i,
                    InvQuantity = data.quantity,
                    opt,
                    PackQuantity,
                    PackName,
                    pack,
                    packs = data.packs,
                    packsLength = packs.length,
                    piece,
                    selected,
                    first = true;

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
                    if (first) {
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

                // Calculate Available Stock Quantity for this Pack
                var Quantity = InvQuantity / PackQuantity;

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

                                // Display Available Stock Quantity
                                $('#TotalQuantity').html(Quantity.toFixed(2) + ' ' + PackName + ' (' + i18n.in_inv + ')');
                                break;
                            }
                        }
                    });
                }
            });
        } else {
            // Use data provided (currently just RMS template)
            // - Pack Options
            // - Available Stock Quantity
            // - REQ Quantity
            // - req_item_id

            var i,
                first = true,
                data = inv_items[inv_item_id],
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
                if (first) {
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

            // Calculate Available Stock Quantity for this Pack
            // - inv_quantity will be the same in every row
            var Quantity = InvQuantity / PackQuantity; // inv_quantity includes inv_pack_quantity

            // Display Available Stock Quantity
            var TotalQuantity = '<span id="TotalQuantity"> / ' + Quantity.toFixed(2) + ' ' + PackName + ' (' + i18n.in_inv + ')</span>';
            QuantityField.after(TotalQuantity);

            // Update Send Quantity
            var updateSendQuantity = function() {
                if (req_items.length == 1) {
                    // Default to REQ Quantity
                    var ReqQuantity = req_item.req_quantity / PackQuantity;
                    if (ReqQuantity <= Quantity) {
                        // We can send the full quantity requested
                        QuantityField.val(ReqQuantity);
                    } else {
                        // We can only send what we have in stock!
                        QuantityField.val(Quantity);
                    }

                    // Set req_item_id, so that we can track request fulfilment
                    $('#inv_track_item_req_item_id').val(req_item.req_item_id);

                } else {
                    // Multiple Req Items for the same Inv Item
                    // Display ReqItemRow
                    ReqItemRow.show();
                    // Populate with Options
                    var req_item_id,
                        ReqItemField = $('#inv_track_item_req_item_id'),
                        ReqQuantity;
                    ReqItemField.html('');
                    for (i = 0; i < req_items.length; i++) {
                        req_item = req_items[i];
                        ReqItemField.append(new Option(req_item.req_ref, req_item.req_item_id));
                        if (first) {
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

    invItemField.change(InvItemIDChange);

    // ========================================================================
    /**
     * req_item_quantity_represent
     */
	$(document).on('click', '.quantity.ajax_more', function(e) {

		e.preventDefault();

		var DIV = $(this);

		if (DIV.hasClass('collapsed')) {

            var ShipmentType,
                Component;

			if (DIV.hasClass('fulfil')) {
				ShipmentType = 'recv';
                Component = 'track_item';
			} else if (DIV.hasClass('transit')) {
				ShipmentType = 'send';
                Component = 'track_item';
			} else if (DIV.hasClass('commit')) {
				ShipmentType = 'commit';
                Component = 'commit_item';
			}
			DIV.after('<div class="ajax_throbber quantity_req_ajax_throbber"/>')
			   .removeClass('collapsed')
			   .addClass('expanded');

			// Get the req_item_id
			var i,
                re = /req_item\/(\d*).*/i,
                ResultTable,
                LineURL,
                UpdateURL = $('.action-btn', DIV.parent().parent().parent()).attr('href'),
                req_item_id = re.exec(UpdateURL)[1],
                url = S3.Ap.concat('/inv/', ShipmentType, '_item_json.json/', req_item_id);
			$.ajax( {
				url: url,
				dataType: 'json',
				context: DIV
			}).done(function(data) {
                ResultTable = '<table class="recv_table">';
                for (i = 0; i < data.length; i++) {
                    ResultTable += '<tr><td>';
                    if (i === 0) {
                        // Header Row
                        ResultTable += data[0].id;
                    } else {
                        LineURL = S3.Ap.concat('/inv/', ShipmentType, '/',  data[i].id, '/' + Component);
                        ResultTable += "<a href='" + LineURL + "'>" + data[i].name + ' - ' + data[i].date + '</a>';
                    }
                    ResultTable += '</td><td>' + data[i].quantity + '</td></tr>';
                }
                ResultTable += '</table>';
                $('.quantity_req_ajax_throbber', this.parent()).remove();
                this.parent().after(ResultTable);
            });
		} else {
			DIV.removeClass('expanded')
			   .addClass('collapsed');
			$('.recv_table', DIV.parent().parent() ).remove();
		}
	});
});

// END ========================================================================