// Comments for Posts (Alerts/Updates) in dataLists
S3.wacop_comments = function() {
    var url = S3.Ap.concat('/cms/comment.s3json');
    $('.add-comment').click(function(e) {
        $this = $(this);
        var list_id = $this.data('l');
        var record_id = $this.data('i');
        // Show the new comment form & force focus to it
        $('#' + list_id + '-' + record_id + ' .comment-form').removeClass('hide')
                                                             .show();
        var formField = $('#' + list_id + '-' + record_id + ' .comment-form textarea');
        formField.focus();
        // Bind Submit handler
        $('#' + list_id + '-' + record_id + ' .comment-form .submit').click(function(e) {
            var data = {
                '$_cms_comment': [{
                    'post_id': record_id,
                    'body': formField.val()
                    }]
            };
            var options = {
                data: JSON.stringify(data),
                type: 'PUT',
                url: url,
                success: function(e) {
                    // Refresh the whole Post, including the comments
                    $('#' + list_id).datalist('ajaxReloadItem', record_id);
                }
            };
            $.ajaxS3(options);
        });
    });
}
