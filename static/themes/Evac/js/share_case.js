/**
 * Used by br_reader
 * - Trigger AJAX call to Share Case with another Org
 */

$(document).ready(function() {
    var field = $('#share-case');

    field.on('change', function() {
        if (confirm('Are you sure you want to share this case?')) {
            // Send request as a POST
            var orgID = field.val(),
                ajaxURL = S3.Ap.concat('/br/person/' + field.data('person_id') + '/share.json/' + orgID);
            $.ajaxS3({
                url: ajaxURL,
                dataType: 'json',
                method : 'POST',
                success: function(data) {
                    // Notify...happens within ajaxS3 anyway
                    //S3.showAlert(data.message, 'success');
                }
            });
        } else {
            // Revert
            field.val('');
        }
    });
});