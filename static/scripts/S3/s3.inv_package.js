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
                maxHeightField.prop('disabled', false);
            } else {
                // Disable field
                maxHeightField.prop('disabled', true);
            }
        };

        typeField.change(typeChange);

        if (typeField.val()) {
            // Update form
            typeChange();
        }
    }

});