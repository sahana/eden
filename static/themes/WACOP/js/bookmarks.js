// Bookmarks for Events/Incidents/Posts (Alerts/Updates)
S3.wacop_bookmarks = function() {
    $('.bookmark').click(function() {
        var $this = $(this);
        var c = $this.data('c');
        var f = $this.data('f');
        var record_id = $this.data('i');
        var icon = $this.find('i');
        if (icon.hasClass('fa-bookmark')) {
            // Bookmark exists already
            var url = S3.Ap.concat('/' + c + '/' + f + '/' + record_id + '/remove_bookmark');
            $.getS3(url, function() {
                // Update Icon
                icon.removeClass('fa-bookmark').addClass('fa-bookmark-o');
                // Update Title - @ToDo: i18n
                $this.attr('title', 'Add Bookmark');
            });
        } else {
            // Bookmark doesn't exist yet
            var url = S3.Ap.concat('/' + c + '/' + f + '/' + record_id + '/add_bookmark');
            $.getS3(url, function() {
                // Update Icon
                icon.removeClass('fa-bookmark-o').addClass('fa-bookmark');
                // Update Title - @ToDo: i18n
                $this.attr('title', 'Remove Bookmark');
            });
        }
    });
};
