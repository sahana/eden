/**
 * Used by the inv/package controller
 * - show/hide fields based on Type
 */

$(document).ready(function() {

    var typeField = $('#inv_package_type');
    if (typeField.length) {

        var type,
            maxHeightField = $('#inv_package_max_height');

        var typeChange = function(/*event*/) {
            type = typeField.val();
            if (type == 'PALLET') {
                // Enable field
                maxHeightField.removeAttr('disabled');
            } else {
                // Disable field
                maxHeightField.attr('disabled', 'disabled');
            }
        };

        typeField.change(typeChange);

        if (typeField.val()) {
            // Update form
            typeChange
        }
    }

});