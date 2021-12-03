/**
 * Used by the inv/adj/adj_item controller
 * - Validate the Bin Quantities
 * - @ToDo: Show/Hide fields based on Reason
 */

$(document).ready(function() {
    var availableQuantity,
        binnedQuantity = S3.supply.binnedQuantity || 0,
        error,
        inlineComponent = $('#sub-defaultbin'),
        inlineComponentInput = $('#inv_adj_item_sub_defaultbin'),
        message,
        newBinQuantityField = $('#sub_defaultbin_defaultbin_i_quantity_edit_none'),
        newBinQuantity,
        // Represent numbers with thousand separator
        // @ToDo: Respect settings
        numberFormat = /(\d)(?=(\d{3})+(?!\d))/g,
        oldBinQuantityField = $('#sub_defaultbin_defaultbin_i_quantity_edit_0'),
        oldBinQuantity,
        totalQuantityField = $('#inv_adj_item_new_quantity'),
        totalQuantity = totalQuantityField.val(),
        form = totalQuantityField.closest('form');

    if (totalQuantity) {
        totalQuantity = parseFloat(totalQuantity);
    } else {
        totalQuantity = S3.supply.oldQuantity || 0;
    }

    form.on('submit.s3', function(event) {
        if (!totalQuantityField.val()) {
            // Empty 'Revised Quantity' will give a server-side validation error
            // - this means we lose any revised bin allocations
            // => Catch this client-side instead
            event.preventDefault();
            // @ToDo: i18n
            message = 'Enter a number greater than or equal to 0';
            error = $('<div id="inv_adj_item_new_quantity-error" class="alert alert-error" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
            totalQuantityField.parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                $(this).fadeOut('slow').remove();
                return false;
            });
        }
    });

    totalQuantityField.change(function() {
        totalQuantity = totalQuantityField.val();
        if (totalQuantity) {
            totalQuantity = parseFloat(totalQuantity);
            // Cleanup any old error message
            $('#inv_adj_item_new_quantity-error').remove();
            $('#inv_adj_item_new_quantity-warning').remove();
        } else {
            totalQuantity = S3.supply.oldQuantity || 0;
        }
        if (totalQuantity < 0) {
            // @ToDo: i18n
            totalQuantity = 0;
            message = 'Quantity cannot be Negative';
            error = $('<div id="inv_adj_item_new_quantity-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
            totalQuantityField.val(totalQuantity)
                              .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                $(this).fadeOut('slow').remove();
                return false;
            });
        }
        newBinQuantity = newBinQuantityField.val();
        if (newBinQuantity) {
            newBinQuantity = parseFloat(newBinQuantity);
        } else {
            newBinQuantity = 0;
        }
        if (oldBinQuantityField.is(":visible")) {
            oldBinQuantity = oldBinQuantityField.val();
            if (oldBinQuantity) {
                oldBinQuantity = parseFloat(oldBinQuantity);
            } else {
                oldBinQuantity = 0;
            }
        } else {
            oldBinQuantity = 0;
        }
        availableQuantity = binnedQuantity + newBinQuantity + oldBinQuantity;
        if (totalQuantity < availableQuantity) {
            if (newBinQuantity >= (availableQuantity - totalQuantity)) {
                // Can just reduce the Quantity in the newRow
                // @ToDo: i18n
                message = 'Quantity in Bins reduced to Total Quantity';
                error = $('<div id="sub_defaultbin_defaultbin_i_quantity_edit_none-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                newBinQuantityField.val(newBinQuantity - (availableQuantity - totalQuantity))
                                   .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                    $(this).fadeOut('slow').remove();
                    return false;
                });
            } else if (oldBinQuantity >= (availableQuantity - totalQuantity)) {
                // Can just reduce the Quantity in the oldRow
                // @ToDo: i18n
                message = 'Quantity in Bins reduced to Total Quantity';
                error = $('<div id="sub_defaultbin_defaultbin_i_quantity_edit_none-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                oldBinQuantityField.val(oldBinQuantity - (availableQuantity - totalQuantity))
                                   .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                    $(this).fadeOut('slow').remove();
                    return false;
                });
            } else {
                var rows = inlineComponentInput.data('data');
                if (!rows) {
                    // Data hasn't been read yet, so read it now
                    rows = JSON.parse(inlineComponentInput.val());
                    inlineComponentInput.data('data', rows);
                }
                rows = rows.data;
                var bins = [];
                for (var row in rows) {
                    bins.push(row);
                }
                if (bins.length == 1) {
                    if (newBinQuantity) {
                        // 1st reduce the newRow to 0
                        newBinQuantityField.val(0);
                        availableQuantity -= newBinQuantity;
                    }
                    if (oldBinQuantity) {
                        // Take the rest from the oldRow
                        oldBinQuantity -= (availableQuantity - totalQuantity);
                        oldBinQuantityField.val(oldBinQuantity);
                        
                    } else {
                        // Take the rest from the readRow
                        var updateQuantity = function(row) {
                            row.quantity.value = totalQuantity;
                            row.quantity.text = totalQuantity.toString().replace(numberFormat, '$1,');
                        };
                        inlineComponent.inlinecomponent('updateRows', updateQuantity);
                    }
                    message = 'Quantity in Bins reduced to Total Quantity';
                    error = $('<div id="sub_defaultbin_defaultbin_i_quantity_edit_none-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                    newBinQuantityField.parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                        $(this).fadeOut('slow').remove();
                        return false;
                    });
                } else {
                    // Ugly: need to revert the change & inform user
                    // @ToDo: Provide a lightbox of just the bins section & have that actionable with the previous step in an isolated container
                    // @ToDo: i18n
                    totalQuantity = binnedQuantity;
                    message = 'You need to reduce the Quantity in the Bins before you can reduce the Total Quantity';
                    error = $('<div id="inv_adj_item_new_quantity-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
                    totalQuantityField.val(totalQuantity)
                                      .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                        $(this).fadeOut('slow').remove();
                        return false;
                    });
                }
            }
        }
        // Validate the new bin again
        //newBinQuantityField.change();
    });

    newBinQuantityField.change(function() {
        newBinQuantity = newBinQuantityField.val();
        if (newBinQuantity) {
            newBinQuantity = parseFloat(newBinQuantity);
        } else {
            newBinQuantity = 0;
        }
        availableQuantity = totalQuantity - binnedQuantity;
        if (newBinQuantity > availableQuantity) {
            // @ToDo: i18n
            message = 'Quantity in Bins cannot be higher than Total Quantity';
            error = $('<div id="sub_defaultbin_defaultbin_i_quantity_edit_none-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
            newBinQuantityField.val(availableQuantity)
                               .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                $(this).fadeOut('slow').remove();
                return false;
            });
        }
    });

    oldBinQuantityField.change(function() {
        oldBinQuantity = oldBinQuantityField.val();
        if (oldBinQuantity) {
            oldBinQuantity = parseFloat(oldBinQuantity);
        } else {
            oldBinQuantity = 0;
        }
        availableQuantity = totalQuantity - binnedQuantity;
        if (oldBinQuantity > availableQuantity) {
            // @ToDo: i18n
            message = 'Quantity in Bins cannot be higher than Total Quantity';
            error = $('<div id="sub_defaultbin_defaultbin_i_quantity_edit_0-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
            oldBinQuantityField.val(availableQuantity)
                               .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                $(this).fadeOut('slow').remove();
                return false;
            });
        }
    });

    // Attach to the top-level element to catch newly-created readRows
    inlineComponent.on('click.s3', '.inline-edt', function() {
        // read-only row has been opened for editing
        oldBinQuantity = oldBinQuantityField.val();
        if (oldBinQuantity) {
            oldBinQuantity = parseFloat(oldBinQuantity);
        } else {
            oldBinQuantity = 0;
        }
        // Make this Bin's Quantity available
        binnedQuantity -= oldBinQuantity;
    });

    $('#rdy-defaultbin-0').click(function() {
        // read-only row has been opened for editing
        // - Tick clicked to save changes
        oldBinQuantity = oldBinQuantityField.val();
        if (oldBinQuantity) {
            oldBinQuantity = parseFloat(oldBinQuantity);
        } else {
            oldBinQuantity = 0;
        }
        // Make this Bin's Quantity unavailable
        binnedQuantity += oldBinQuantity;
        // Validate the new bin again
        newBinQuantityField.change();
    });

    inlineComponent.on('editCancelled', function(event, rowindex) {
        // read-only row has been opened for editing
        // - X clicked to cancel changes
        // Make Quantity unavailable
        oldBinQuantity = parseFloat(inlineComponentInput.data('data').data[rowindex].quantity.value);
        binnedQuantity += oldBinQuantity;
    });

    inlineComponent.on('rowAdded', function(event, row) {
        // Make Quantity unavailable
        binnedQuantity += parseFloat(row.quantity.value);
        // Cleanup any old warning message
        $('#sub_defaultbin_defaultbin_i_quantity_edit_none-warning').remove();
    });

    inlineComponent.on('rowRemoved', function(event, row) {
        // Make Quantity available
        binnedQuantity -= parseFloat(row.quantity.value);
    });

});