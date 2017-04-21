// Tags for Incident
var incident_tags = function(incident_id) {
    if (incident_id) {
        // Read-Write
        $('#incident-tags').tagit({
            // @ToDo: i18n
            placeholderText: 'Add tags here…',
            afterTagAdded: function(event, ui) {
                if (ui.duringInitialization) {
                    return;
                }
                var url = S3.Ap.concat('/event/incident/' + incident_id + '/add_tag/', ui.tagLabel);
                $.getS3(url);
            },
            afterTagRemoved: function(event, ui) {
                var url = S3.Ap.concat('/event/incident/' + incident_id + '/remove_tag/', ui.tagLabel);
                $.getS3(url);
            }
        });
    } else {
        // Read-only
         $('#incident-tags').tagit({
            readOnly: true
        });
    }
};

$(document).ready(function() {
    $('main.main').attr('id', 'incident-profile');

    $('.filter-clear, .show-filter-manager').addClass('button tiny secondary');
});