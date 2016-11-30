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

// Bookmarks for Incident
var incident_bookmarks = function(incident_id) {
    $('#incident-bookmark').click(function() {
        if ($('#incident-bookmark i').hasClass('fa-bookmark')) {
            // Bookmark exists already
            var url = S3.Ap.concat('/event/incident/' + incident_id + '/remove_bookmark');
            $.getS3(url, function() {
                // Update Icon
                $('#incident-bookmark i').removeClass('fa-bookmark').addClass('fa-bookmark-o');
                // Update Title - @ToDo: i18n
                $(this).attr('title', 'Add Bookmark');
            });
        } else {
            // Bookmark doesn't exist yet
            var url = S3.Ap.concat('/event/incident/' + incident_id + '/add_bookmark');
            $.getS3(url, function() {
                // Update Icon
                $('#incident-bookmark i').removeClass('fa-bookmark-o').addClass('fa-bookmark');
                // Update Title - @ToDo: i18n
                $(this).attr('title', 'Remove Bookmark');
            });
        }
    });
};

$(document).ready(function() {
    $('main.main').attr('id', 'incident-profile');

    $('.filter-clear, .show-filter-manager').addClass('button tiny secondary');

    // Tags for Updates Create form
    $('#cms_post_create_tags_ul').tagit({
        // @ToDo: i18n
        placeholderText: 'Add tags here…',
        singleField: true,
        singleFieldNode: $('#cms_post_create_tags_input')//,
        // @ToDo: make options visible
        //autocomplete: {
        //    source: S3.Ap.concat('/cms/tag/search_ac.json')
        //}
    });
});