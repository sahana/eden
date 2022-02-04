/**
 * Used by the dissemination field
 * - Confirm changes
 */

$(document).ready(function() {
    var field = $('select[name="sub_dissemination_dissemination"]'),
        level = field.val();

    field.on('change', function() {
        if (confirm('Are you sure you want to change the dissemination level?')) {
            // OK
            level = field.val();
        } else {
            // Revert
            field.val(level);
        }
    });

});