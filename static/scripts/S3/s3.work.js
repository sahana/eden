/**
 * Used by work/job/datalist
 */

(function($, undefined) {

    "use strict";

    /**
     * Bind button event handlers for sign-up and cancellation
     */
    var bindSignUpActions = function() {
        $('.job-signup').off('.work').on('click.work', function() {
            signup(this, true);
        });
        $('.job-cancel').off('.work').on('click.work', function() {
            signup(this, false);
        });
    };

    /**
     * Sign-up / Cancel Assignment (Ajax)
     *
     * @param {jQuery} button - the action button
     * @param {bool} assign - whether to assign (true) or cancel (false)
     */
    var signup = function(button, assign) {

        var $button = $(button),
            item = $button.closest('.dl-item'),
            dl = $button.closest('.dl'),
            action = assign ? 'signup' : 'cancel',
            throbber = $('<div class="inline-throbber">').css({'display': 'inline-block'});

        if (!item.length || !dl.length) {
            return;
        }

        var recordID = $(item).attr('id').split('-').pop();
        if (recordID) {
            $button.after(throbber);
            $.ajax({
                'url': S3.Ap.concat('/work/job/') + recordID + '/' + action + '.json',
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

    /**
     * Document-ready functions for work/job datalist
     */
    $(document).ready(function() {
        // Re-bind signup-actions after every datalist update
        $('.job-signup, .job-cancel').closest('.dl').off('.work').on('listUpdate.work', function() {
            bindSignUpActions();
        });
        // ...and bind once at document-ready
        bindSignUpActions();
    });

})(jQuery);

// END ========================================================================
