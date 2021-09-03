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
     */
	var ReqItemRow = $('#inv_track_item_req_item_id__row');
    if (ReqItemRow.length) {
        // Hide it by Default
        ReqItemRow.hide();
    }

    // Display the number of items available in an inventory
    var InvItemPackIDChange = function() {

        var elementID = $(this).attr('id'),
            inv_item_id;

        // Cancel previous request
        try {S3.JSONRequest[elementID].abort();} catch(err) {}

        // Remove old Available Stock
        $('#TotalQuantity').remove();   

        var invItemField = $('#inv_track_item_send_inv_item_id');
        if (invItemField.length > 0) {
            // Preparing an Outgoing Shipment
            inv_item_id = invItemField.val();
        } else {
            invItemField = $('#inv_track_item_inv_item_id');
            if (invItemField.length > 0) {
                // Receiving a Shipment...but not sure where exactly!?
                inv_item_id = invItemField.val();
            } else {
                // No invItemField to operate on
                return;
            }
        }
        if (inv_item_id === '') {
            // No Inv Item available yet
            return
        }

        var inv_items = S3.supply.inv_items;
        if (undefined === inv_items) {
            // Lookup data via AJAX
            // - Available Stock Quantity
            if ($('#inv_quantity_throbber').length === 0) {
                $('[name="quantity"]').after('<div id="inv_quantity_throbber" class="throbber"/>'); 
            }
            var url = S3.Ap.concat('/inv/inv_item_quantity.json/' + inv_item_id);

            // Save JSON Request by element id
            S3.JSONRequest[elementID] = $.getJSON(url, function(data) {
                // @ToDo: Error Checking
                
                // Calculate Pack Quantity
                // @ToDo: Something more robust than this!
                // - Better to replace the previous filterOptionsS3 AJAX call with a single call here
                var PackName = $('#inv_track_item_item_pack_id option:selected').text(),
                    re = /\(([0-9]*)\sx/,
                    RegExpResult = re.exec(PackName),
                    PackQuantity;
                if (RegExpResult === null) {
                    PackQuantity = 1;
                } else {
                    PackQuantity = RegExpResult[1];
                }

                // Calculate Available Stock Quantity for this Pack
                var Quantity = (data.iquantity * data.pquantity) / PackQuantity;

                // Display Available Stock Quantity
                var TotalQuantity = '<span id="TotalQuantity"> / ' + Quantity.toFixed(2) + ' ' + PackName + ' (' + i18n.in_inv + ')</span>';
                $('#inv_track_item_quantity').after(TotalQuantity);

                $('#inv_quantity_throbber').remove();
            });
        } else {
            // Use data provided (currently just RMS template)
            // - Available Stock Quantity
            // - REQ Quantity
            // - req_item_id

            var data = inv_items[inv_item_id];

            // Calculate Pack Quantity
            // @ToDo: Something more robust than this!
            var PackName = $('#inv_track_item_item_pack_id option:selected').text(),
                re = /\(([0-9]*)\sx/, // @ToDo: Something more robust than this!
                RegExpResult = re.exec(PackName),
                PackQuantity;
            if (RegExpResult === null) {
                PackQuantity = 1;
            } else {
                PackQuantity = RegExpResult[1];
            }

            var req_item = data[0];

            // Calculate Available Stock Quantity for this Pack
            // - inv_quantity will be the same in every row
            var Quantity = req_item.inv_quantity / PackQuantity; // inv_quantity includes inv_pack_quantity

            // Display Available Stock Quantity
            var TotalQuantity = '<span id="TotalQuantity"> / ' + Quantity.toFixed(2) + ' ' + PackName + ' (' + i18n.in_inv + ')</span>';
            $('#inv_track_item_quantity').after(TotalQuantity);

            if (data.length == 1) {
                // Default to REQ Quantity
                var ReqQuantity = req_item.req_quantity / PackQuantity;
                if (ReqQuantity <= Quantity) {
                    // We can send the full quantity requested
                    $('#inv_track_item_quantity').val(ReqQuantity);
                } else {
                    // We can only send what we have in stock!
                    $('#inv_track_item_quantity').val(Quantity);
                }

                // Set req_item_id, so that we can track request fulfilment
                $('#inv_track_item_req_item_id').val(req_item.req_item_id);

            } else {
                // Multiple Req Items for the same Inv Item
                // Display ReqItemRow
                ReqItemRow.show();
                // Populate with Options
                var i,
                    first = true,
                    req_item_id,
                    ReqItemField = $('#inv_track_item_req_item_id');
                ReqItemField.html('');
                for (i = 0; i < data.length; i++) {
                    req_item = data[i];
                    ReqItemField.append(new Option(req_item.req_ref, req_item.req_item_id));
                    if (first) {
                        var ReqQuantity = req_item.req_quantity / PackQuantity;
                        if (ReqQuantity <= Quantity) {
                            // We can send the full quantity requested
                            $('#inv_track_item_quantity').val(ReqQuantity);
                        } else {
                            // We can only send what we have in stock!
                            $('#inv_track_item_quantity').val(Quantity);
                        }
                    }
                    first = false;
                }
                ReqItemField.on('change', function() {
                    // Update the Quantity accordingly
                    req_item_id = ReqItemField.val();
                    for (i = 0; i < data.length; i++) {
                        req_item = data[i];
                        if (req_item.req_item_id == req_item_id) {
                            ReqQuantity = req_item.req_quantity / PackQuantity;
                            if (ReqQuantity <= Quantity) {
                                // We can send the full quantity requested
                                $('#inv_track_item_quantity').val(ReqQuantity);
                            } else {
                                // We can only send what we have in stock!
                                $('#inv_track_item_quantity').val(Quantity);
                            }
                            break;
                        }
                    }
                });
            }
        }
    };

    $('#inv_track_item_item_pack_id').change(InvItemPackIDChange);

    // ========================================================================
    /**
     * req_item_quantity_represent
     */
	$(document).on('click', '.quantity.ajax_more', function(e) {

		e.preventDefault();

		var DIV = $(this);

		if (DIV.hasClass('collapsed')) {

            var App,
                ShipmentType;

			if (DIV.hasClass('fulfil')) {
				App = 'inv';
				ShipmentType = 'recv';
			} else if (DIV.hasClass('transit')) {
				App = 'inv';
				ShipmentType = 'send';
			} else if (DIV.hasClass('commit')) {
				App = 'req';
				ShipmentType = 'commit';
			}
			DIV.after('<div class="ajax_throbber quantity_req_ajax_throbber"/>')
			   .removeClass('collapsed')
			   .addClass('expanded');

			// Get the req_item_id
			var i,
                re = /req_item\/(\d*).*/i,
                RecvTable,
                RecvURL,
                UpdateURL = $('.action-btn', DIV.parent().parent().parent()).attr('href'),
                req_item_id = re.exec(UpdateURL)[1],
                url = S3.Ap.concat('/req/', ShipmentType, '_item_json.json/', req_item_id);
			$.ajax( {
				url: url,
				dataType: 'json',
				context: DIV
			}).done(function(data) {
                RecvTable = '<table class="recv_table">';
                for (i = 0; i < data.length; i++) {
                    RecvTable += '<tr><td>';
                    if (i === 0) {
                        // Header Row
                        RecvTable += data[0].id;
                    } else {
                        RecvURL = S3.Ap.concat('/', App, '/', ShipmentType, '/',  data[i].id, '/track_item');
                        RecvTable += "<a href='" + RecvURL + "'>";
                        if (data[i].date !== null) {
                            RecvTable += data[i].date;
                            RecvTable += data[i].name + '</a>';
                        } else {
                            RecvTable +=  ' - </a>';
                        }
                    }
                    RecvTable += '</td><td>' + data[i].quantity + '</td></tr>';
                }
                RecvTable += '</table>';
                $('.quantity_req_ajax_throbber', this.parent()).remove();
                this.parent().after(RecvTable);
            });
		} else {
			DIV.removeClass('expanded')
			   .addClass('collapsed');
			$('.recv_table', DIV.parent().parent() ).remove();
		}
	});
});

// END ========================================================================