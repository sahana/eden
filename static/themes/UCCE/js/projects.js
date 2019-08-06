$(document).ready(function(){
    /**
     * ajaxMethod: use $.searchS3 if available, fall back to $.ajaxS3
     */
    var ajaxMethod = $.ajaxS3;
    if ($.searchS3 !== undefined) {
        ajaxMethod = $.searchS3;
    }

    var dl = $('#datalist');

    var ajaxDeleteItem = function(item){
        // Ajax-delete the item
        var $this = $(item),
            recordID = $this.attr('id').split('-').pop(),
            projectID = $this.closest('.dl-item').attr('id').split('-').pop();

        ajaxMethod({
            'url': S3.Ap.concat('/dc/target/') + recordID + '/delete.json',
            'type': 'POST',
            'dataType': 'json',
            'success': function(/* data */) {
                // Refresh the outer Project
                dl.datalist('ajaxReloadItem', projectID);
                dl.on('listUpdate', function(/* event */) {
                    // Subsequent Page Load
                    bindItemEvents();
                });
            },
            'error': function(request, status, error) {
                var msg;
                if (error == 'UNAUTHORIZED') {
                    msg = i18n.gis_requires_login;
                } else {
                    msg = request.responseText;
                }
                console.log(msg);
            }
        });
    };

    var bindItemEvents = function(){
        // Click-event for dl-survey-delete
        dl.find('.dl-survey-delete')
          .css({cursor: 'pointer'})
          .off('click.ucce')
          .on('click.ucce', function(event) {
            if (confirm(i18n.delete_confirmation)) {
                // Ajax-delete the item
                ajaxDeleteItem(this);
                return true;
            } else {
                event.preventDefault();
                return false;
            }
        });
        // Change-event for switches
        dl.find('.switch input')
          .off('change.ucce')
          .on('change.ucce', function(/* event */) {
            var $this = $(this),
                method,
                recordID = $this.attr('id').split('-').pop();
            if ($this.prop('checked')) {
                method = 'activate';
            } else{
                method = 'deactivate';
            }
            ajaxMethod({
                'url': S3.Ap.concat('/dc/target/') + recordID + '/' + method + '.json',
                'type': 'POST',
                'dataType': 'json',
                'success': function(/* data */) {
                    // Nothing needed here
                },
                'error': function(request, status, error) {
                    var msg;
                    if (error == 'UNAUTHORIZED') {
                        msg = i18n.gis_requires_login;
                    } else {
                        msg = request.responseText;
                    }
                    console.log(msg);
                }
            });
        });
    };

    // Initial Page Load
    bindItemEvents();
});
