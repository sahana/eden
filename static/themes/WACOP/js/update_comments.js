// Comments for Posts (Alerts/Updates) in dataLists
S3.wacop_comments = function() {
    var url = S3.Ap.concat('/cms/comment.s3json');
    $('.add-comment').click(function(e) {
        var $this = $(this);
        var list_id = $this.data('l'),
            record_id = $this.data('i'),
            card_selector = '#' + list_id + '-' + record_id
            form_selector = card_selector + ' .comment-form',
            form = $(form_selector);
        // Hide the 'Add Comment' button
        $(card_selector + ' .add-comment').hide();
        // Show the new comment form & force focus to it
        form.removeClass('hide')
            .show();
        var formField = $(form_selector + ' textarea');
        formField.focus();
        // Bind Submit handler
        $(form_selector + ' .submit').click(function(e) {
            // Hide the Edit box & Submit Button
            form.hide();
            // Show Spinner
            form.after('<div class="throbber"></div>');
            // Submit Data
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
