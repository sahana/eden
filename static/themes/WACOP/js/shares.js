// Shares for Events/Incidents/Tasks/Posts (Alerts/Updates)
S3.wacop_shares = function() {
    $('.share').each(function() {
        var $this = $(this);
        var c = $this.data('c');
        var f = $this.data('f');
        var record_id = $this.data('i');
        $this.find('input').each(function() {
            var checkbox = $(this);
            checkbox.change(function() {
                var forum_id = checkbox.val();
                if (checkbox.prop('checked')) {
                    // Share the record
                    var url = S3.Ap.concat('/' + c + '/' + f + '/' + record_id + '/share/' + forum_id);
                    $.getS3(url, function() {
                    });
                } else {
                    // Unshare the record
                    var url = S3.Ap.concat('/' + c + '/' + f + '/' + record_id + '/unshare/' + forum_id);
                    $.getS3(url, function() {
                    });
                }
            });
        });
    });
};
