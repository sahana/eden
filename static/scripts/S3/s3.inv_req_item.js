/**
 * Used by the inv/req controller
 * - supports settings.get_inv_req_reserve_items()
 * - supports req_item_quantity_represent
 */

$(document).ready(function() {

    var totalQuantityField = $('#inv_req_item_quantity_reserved');

    if (totalQuantityField.length) {

        var availableQuantity,
            binQuantity,
            binnedQuantity,
            error,
            inlineComponent = $('#sub-defaultreq_item_inv'),
            editBinBtnOK = $('#rdy-defaultreq_item_inv-0'),
            message,
            newBinQuantityField = $('#sub_defaultreq_item_inv_defaultreq_item_inv_i_quantity_edit_none'),
            oldBinQuantityField = $('#sub_defaultreq_item_inv_defaultreq_item_inv_i_quantity_edit_0'),
            reqData = S3.supply.reqData || {},
            reqQuantity,
            totalQuantity = totalQuantityField.val();

        if (totalQuantity) {
            totalQuantity = parseFloat(totalQuantity);
        } else {
            totalQuantity = 0;
        }

        // Parse reqData
        binnedQuantity = reqData.bq || 0;
        reqQuantity = reqData.rq;
        stockQuantity = reqData.sq;

        // Display Available Stock Quantity
        var TotalQuantity = '<span id="TotalQuantity"> / ' + stockQuantity.toFixed(2) + ' ' + reqData.pn + ' (' + i18n.in_inv + ')</span>';
        totalQuantityField.after(TotalQuantity);

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
                // Cleanup any old error message
                $('#inv_req_item_quantity_reserved-error').remove();
            } else {
                totalQuantity = 0;
            }
            if (totalQuantity > reqQuantity) {
                totalQuantity = reqQuantity;
                message = 'Quantity Reserved decreased to Quantity Requested';
                error = $('<div id="inv_req_item_quantity_reserved-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                totalQuantityField.val(reqQuantity)
                                  .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                    $(this).fadeOut('slow').remove();
                    return false;
                });
            } else if (totalQuantity < binnedQuantity) {
                // @ToDo: i18n
                totalQuantity = binnedQuantity;
                message = 'Quantity Reserved increased to Quantity in Bins';
                error = $('<div id="inv_req_item_quantity_reserved-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
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
                message = 'Bin Quantity reduced to Quantity Reserved';
                error = $('<div id="sub_defaultreq_item_inv_defaultreq_item_inv_i_quantity_edit_none-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
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
                message = 'Bin Quantity reduced to Quantity Reserved';
                error = $('<div id="sub_defaultreq_item_inv_defaultreq_item_inv_i_quantity_edit_0-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
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
            // Cleanup any old warning message
            $('#sub_defaultreq_item_inv_defaultreq_item_inv_i_quantity_edit_none-warning').remove();
        });

        inlineComponent.on('rowRemoved', function(event, row) {
            // Make Quantity available
            binnedQuantity = binnedQuantity - parseFloat(row.quantity.value);
        });
    }

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