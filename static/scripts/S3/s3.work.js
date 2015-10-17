/**
 * Used by work/job/datalist
 */

(function($, undefined) {

    var bindSignUpActions = function() {
        $('.job-signup').unbind('.work').bind('click.work', function() {
            signup(this, true);
        });
        $('.job-cancel').unbind('.work').bind('click.work', function() {
            signup(this, false);
        });
    };
    
    var signup = function(button, assign) {

        var $button = $(button),
            action = assign ? '/signup.json' : '/cancel.json',
            throbber = $('<div class="inline-throbber">').css({'display': 'inline-block'});
            
        var item = $button.closest('.dl-item'),
            dl = $button.closest('.dl');
        if (!item.length || !dl.length) {
            return;
        }
        var recordID = $(item).attr('id').split('-').pop();
        
        if (recordID) {
            $button.after(throbber);
            $.ajax({
                'url': S3.Ap.concat('/work/job/') + recordID + action,
                'success': function(data) {
                    throbber.remove();
                    dl.datalist('ajaxReloadItem', recordID);
                },
                'error': function(request, status, error) {
                    throbber.remove();
                    var msg;
                    if (error == 'UNAUTHORIZED') {
                        msg = i18n.gis_requires_login;
                    } else {
                        msg = request.responseText;
                    }
                    console.log(msg);
                },
                'type': 'POST',
                'dataType': 'json'
            });
        }
    };
    
    $(document).ready(function() {
        // Re-bind signup-actions after every datalist update
        $('.job-signup, .job-cancel').closest('.dl').unbind('.work').bind('listUpdate.work', function() {
            bindSignUpActions();
        });
        // ...and bind once at document-ready
        bindSignUpActions();
    });

})(jQuery);

// END ========================================================================
