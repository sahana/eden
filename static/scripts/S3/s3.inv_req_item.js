/**
 * Used by the inv/req controller
 * - supports settings.get_inv_req_reserve_items()
 * - supports req_item_quantity_represent
 */

$(document).ready(function() {

    var totalQuantityField = $('#inv_req_item_quantity_reserved');

    if (totalQuantityField.length) {

        var availableQuantity, // Total unallocated from Stock
            binAvailableQuantity, // Quantity of this Stock (& Bin if-binned)
            binQuantity,
            bins,
            binsByID,
            binsLength,
            editBinBtnOK = $('#rdy-defaultreq_item_inv-0'),
            error,
            inlineComponent = $('#sub-defaultreq_item_inv'),
            invItemID,
            layoutID,
            message,
            newRowInvField = $('#sub_defaultreq_item_inv_defaultreq_item_inv_i_inv_item_id_edit_none'),
            newRowBinField = $('#sub_defaultreq_item_inv_defaultreq_item_inv_i_layout_id_edit_none'),
            newRowQuantityField = $('#sub_defaultreq_item_inv_defaultreq_item_inv_i_quantity_edit_none'),
            newTree = $('#sub_defaultreq_item_inv_defaultreq_item_inv_i_layout_id_edit_none-hierarchy'),
            // Represent numbers with thousand separator
            // @ToDo: Respect settings
            numberFormat = /(\d)(?=(\d{3})+(?!\d))/g,
            oldRowInvField = $('#sub_defaultreq_item_inv_defaultreq_item_inv_i_inv_item_id_edit_0'),
            oldRowBinField = $('#sub_defaultreq_item_inv_defaultreq_item_inv_i_layout_id_edit_0'),
            oldRowQuantityField = $('#sub_defaultreq_item_inv_defaultreq_item_inv_i_quantity_edit_0'),
            oldTree = $('#sub_defaultreq_item_inv_defaultreq_item_inv_i_layout_id_edit_0-hierarchy'),
            onTreeReady,
            update,
            reqData = S3.supply.reqData || {},
            binnedQuantity = reqData.b || 0, // Total Quantity Reserved allocated from Stock
            invItems = reqData.i || {},
            reqQuantity = reqData.r,
            singleRow = 0,
            siteID = reqData.s,
            totalQuantity = totalQuantityField.val();  // Total Quantity Reserved

        if (totalQuantity) {
            totalQuantity = parseFloat(totalQuantity);
        } else {
            totalQuantity = 0;
        }

        // Display Total Available Stock Quantity
        var stockInfo = '<span> / ' + reqData.q.toFixed(2) + ' ' + reqData.p + ' (' + i18n.in_inv + ')</span>';
        totalQuantityField.after(stockInfo);

        // Attach to the top-level element to catch newly-created readRows
        inlineComponent.on('click.s3', '.inline-edt', function() {
            binQuantity = oldRowQuantityField.val();
            if (binQuantity) {
                binQuantity = parseFloat(binQuantity);
            } else {
                binQuantity = 0;
            }
            // Make this Bin's Quantity available
            binnedQuantity = binnedQuantity - binQuantity;
        });

        editBinBtnOK.click(function() {
            binQuantity = oldRowQuantityField.val();
            if (binQuantity) {
                binQuantity = parseFloat(binQuantity);
            } else {
                binQuantity = 0;
            }
            // Make this Bin's Quantity unavailable
            binnedQuantity = binnedQuantity + binQuantity;
            // Validate the new bin again
            newRowQuantityField.change();
        });

        totalQuantityField.change(function() {
            totalQuantity = totalQuantityField.val();
            if (totalQuantity) {
                totalQuantity = parseFloat(totalQuantity);
                // Cleanup any old error message
                $('#inv_req_item_quantity_reserved-warning').remove();
            } else {
                totalQuantity = 0;
            }
            if (totalQuantity > reqQuantity) {
                totalQuantity = reqQuantity;
                message = 'Quantity Reserved decreased to Quantity Requested';
                error = $('<div id="inv_req_item_quantity_reserved-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                totalQuantityField.val(totalQuantity)
                                  .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                    $(this).fadeOut('slow').remove();
                    return false;
                });
            } else if (totalQuantity < 0) {
                totalQuantity = 0;
                message = 'Quantity Reserved cannot be negative';
                error = $('<div id="inv_req_item_quantity_reserved-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                totalQuantityField.val(totalQuantity)
                                  .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                    $(this).fadeOut('slow').remove();
                    return false;
                });
            }
            if (singleRow) {
                // Keep the BinQuantity in sync
                if (update) {
                    // Create form => In read-only row
                    binAvailableQuantity = invItems[invItemID].b[layoutID] + binnedQuantity;
                    binQuantity = Math.min(totalQuantity, binAvailableQuantity);
                    updateQuantity = function(row) {
                        row.quantity.value = binQuantity;
                        row.quantity.text = binQuantity.toString().replace(numberFormat, '$1,');
                    };
                    inlineComponent.inlinecomponent('updateRows', updateQuantity);
                    // Hide the buttons again
                    $('#edt-defaultreq_item_inv-0').hide();
                    $('#rmv-defaultreq_item_inv-0').hide();
                } else {
                    // Create form => In newRow
                    availableQuantity = totalQuantity - binnedQuantity;
                    binAvailableQuantity = invItems[invItemID].b[layoutID];
                    binQuantity = Math.min(availableQuantity, binAvailableQuantity);
                    newRowQuantityField.val(binQuantity);
                }
            } else if (totalQuantity < binnedQuantity) {
                // @ToDo: i18n
                totalQuantity = binnedQuantity;
                message = 'Quantity Reserved increased to Quantity in Bins';
                error = $('<div id="inv_req_item_quantity_reserved-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                totalQuantityField.val(totalQuantity)
                                  .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                    $(this).fadeOut('slow').remove();
                    return false;
                });
            }
            // Validate the new bin again
            //newRowQuantityField.change();
        });

        newRowQuantityField.change(function() {
            binQuantity = newRowQuantityField.val();
            if (!binQuantity) {
                return;
            }
            availableQuantity = totalQuantity - binnedQuantity;
            binQuantity = parseFloat(binQuantity);
            message = null;
            invItemID = newRowInvField.val();
            if (invItemID) {
                layoutID = newRowBinField.val();
                if (layoutID) {
                    binAvailableQuantity = invItems[invItemID].b[layoutID];
                    // Validate against lower of availableQuantity and binAvailableQuantity
                    if (availableQuantity >= binAvailableQuantity) {
                        if (binQuantity > binAvailableQuantity) {
                            // @ToDo: i18n
                            message = 'Bin Quantity reduced to Quantity in Bin';
                        }
                    } else {
                        if (binQuantity > availableQuantity) {
                            // @ToDo: i18n
                            message = 'Bin Quantity reduced to Quantity Reserved';
                        }
                    }
                } else {
                    // No Bins
                    binAvailableQuantity = invItems[invItemID].q;
                    // Validate against lower of availableQuantity and binAvailableQuantity
                    if (availableQuantity >= binAvailableQuantity) {
                        if (binQuantity > binAvailableQuantity) {
                            // @ToDo: i18n
                            message = 'Bin Quantity reduced to Quantity of Stock Item';
                        }
                    } else {
                        if (binQuantity > availableQuantity) {
                            // @ToDo: i18n
                            message = 'Bin Quantity reduced to Quantity Reserved';
                        }
                    }
                }
            } else {
                // Can only validate against Total Quantity at this stage
                if (binQuantity > availableQuantity) {
                    // @ToDo: i18n
                    message = 'Bin Quantity reduced to Quantity Reserved';
                }
            }
            if (message) {
                error = $('<div id="sub_defaultreq_item_inv_defaultreq_item_inv_i_quantity_edit_none-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                newRowQuantityField.val(availableQuantity)
                                   .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                    $(this).fadeOut('slow').remove();
                    return false;
                });
            }
        });
        newRowInvField.change(function() {
            invItemID = newRowInvField.val();
            if (!invItemID) {
                return;
            }
            // Filter the Bins
            binsByID = invItems[invItemID].b;
            bins = [];
            for (layoutID in binsByID) {
                bins.push(layoutID);
            }
            binsLength = bins.length;
            if (binsLength == 1) {
                if (update) {
                    // Hide the Add Row
                    $('#add-row-defaultreq_item_inv').hide();
                    // Hide the Buttons on the readRow
                    $('#read-row-defaultreq_item_inv-0 > .subform-action').hide();
                    // Prevent Editing
                    inlineComponent.off('click.inlinecomponent', '.read-row');
                    onTreeReady = function() {}; // Nothing needed as not editable
                } else {
                    // Default the Bin & make field read-only
                    layoutID = bins[0];
                    onTreeReady = function() {
                        newTree.hierarchicalopts('set', [layoutID]);
                        $('.s3-hierarchy-button').attr('disabled','disabled');
                        if (singleRow) {
                            // Default the Quantity & make read-only
                            availableQuantity = totalQuantity - binnedQuantity;
                            binAvailableQuantity = invItems[invItemID].b[layoutID];
                            newRowQuantityField.val(Math.min(availableQuantity, binAvailableQuantity))
                                               .attr('disabled', true);
                            $('#add-row-defaultreq_item_inv > .subform-action').hide();
                        } else {
                            binQuantity = newRowQuantityField.val();
                            if (binQuantity) {
                                // Validate the Quantity
                                newRowQuantityField.change();
                            } else {
                                // Default the Quantity
                                availableQuantity = totalQuantity - binnedQuantity;
                                binAvailableQuantity = invItems[invItemID].b[layoutID];
                                newRowQuantityField.val(Math.min(availableQuantity, binAvailableQuantity));
                            }
                        }
                    }
                };
            } else {
                // Enable the Bins
                singleRow = false;
                onTreeReady = function() {
                    $('.s3-hierarchy-button').removeAttr('disabled');
                    // Filter the Bins
                    // - can be done client-side without any AJAX, as we have all the layout_ids
                    newTree.hierarchicalopts('show', bins, true);
                    // Validate the Quantity
                    newRowQuantityField.change();
                };
            }
            if (newTree.is(":data('s3-hierarchicalopts')")) {
                // Tree is already ready
                onTreeReady();
            } else {
                // We run before the hierarchicalopts so need to wait for tree to be ready
                newTree.find('.s3-hierarchy-tree').first().on('ready.jstree', function() {
                    onTreeReady();
                });
            }
        });
        newRowBinField.change(function() {
            // Validate the Quantity
            newRowQuantityField.change();
        });

        for (invItemID in invItems) {
            singleRow++;
        }
        if (singleRow == 1) {
            if (binnedQuantity) {
                update = true;
            }
            // Set the InvItem to this value & make read-only
            newRowInvField.val(invItemID)
                          .attr('disabled', true)
                          .change();
        } else {
            singleRow = false;
        }

        oldRowQuantityField.change(function() {
            binQuantity = oldRowQuantityField.val();
            if (!binQuantity) {
                return;
            }
            availableQuantity = totalQuantity - binnedQuantity;
            binQuantity = parseFloat(binQuantity);
            message = null;
            invItemID = oldRowInvField.val();
            if (invItemID) {
                layoutID = oldRowBinField.val();
                if (layoutID) {
                    binAvailableQuantity = invItems[invItemID].b[layoutID];
                    // Validate against lower of availableQuantity and binAvailableQuantity
                    if (availableQuantity >= binAvailableQuantity) {
                        if (binQuantity > binAvailableQuantity) {
                            // @ToDo: i18n
                            message = 'Bin Quantity reduced to Quantity in Bin';
                        }
                    } else {
                        if (binQuantity > availableQuantity) {
                            // @ToDo: i18n
                            message = 'Bin Quantity reduced to Quantity Reserved';
                        }
                    }
                } else {
                    // No Bins
                    binAvailableQuantity = invItems[invItemID].q;
                    // Validate against lower of availableQuantity and binAvailableQuantity
                    if (availableQuantity >= binAvailableQuantity) {
                        if (binQuantity > binAvailableQuantity) {
                            // @ToDo: i18n
                            message = 'Bin Quantity reduced to Quantity of Stock Item';
                        }
                    } else {
                        if (binQuantity > availableQuantity) {
                            // @ToDo: i18n
                            message = 'Bin Quantity reduced to Quantity Reserved';
                        }
                    }
                }
            } else {
                // Can only validate against Total Quantity at this stage
                availableQuantity = totalQuantity - binnedQuantity;
                if (binQuantity > availableQuantity) {
                    // @ToDo: i18n
                    message = 'Bin Quantity reduced to Quantity Reserved';
                }
            }
            if (message) {
                error = $('<div id="sub_defaultreq_item_inv_defaultreq_item_inv_i_quantity_edit_0-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                oldRowQuantityField.val(availableQuantity)
                                   .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                    $(this).fadeOut('slow').remove();
                    return false;
                });
            }
        });
        oldRowInvField.change(function() {
            invItemID = oldRowInvField.val();
            if (!invItemID) {
                return;
            }
            // Filter the Bins
            binsByID = invItems[invItemID].b;
            bins = [];
            for (layoutID in binsByID) {
                bins.push(layoutID);
            }
            binsLength = bins.length;
            if (binsLength == 1) {
                // Default the Bin & make field read-only
                layoutID = bins[0];
                oldTree.hierarchicalopts('set', [layoutID]);
                $('.s3-hierarchy-button').attr('disabled','disabled');
                binQuantity = oldRowQuantityField.val();
                if (binQuantity) {
                    // Validate the Quantity
                    oldRowQuantityField.change();
                } else {
                    // Default the Quantity
                    availableQuantity = totalQuantity - binnedQuantity;
                    binAvailableQuantity = invItems[invItemID].b[layoutID];
                    oldRowQuantityField.val(Math.min(availableQuantity, binAvailableQuantity));
                }
            } else {
                // Enable the Bins
                $('.s3-hierarchy-button').removeAttr('disabled');
                // Filter the Bins
                // - can be done client-side without any AJAX, as we have all the layout_ids
                oldTree.hierarchicalopts('show', bins);
                // Validate the Quantity
                oldRowQuantityField.change();
            }
        });
        oldRowBinField.change(function() {
            // Validate the Quantity
            oldRowQuantityField.change();
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

   /* Support req_item_quantity_represent */
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