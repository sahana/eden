$(document).ready(function(){
    /**
     * ajaxMethod: use $.searchS3 if available, fall back to $.ajaxS3
     */
    var ajaxMethod = $.ajaxS3;
    if ($.searchS3 !== undefined) {
        ajaxMethod = $.searchS3;
    }

    // Edit Survey Name
    $('#survey-name').on('change.ucce', function(/* event */) {
        var $this = $(this),
            name = $this.val(),
            recordID = $this.data('id');
        ajaxMethod({
            'url': S3.Ap.concat('/dc/target/') + recordID + '/name.json',
            'type': 'POST',
            // $.searchS3 defaults to processData: false
            'data': JSON.stringify({name: name}),
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

    // Drag ('n'Drop handled in surveyLayout())
    $('.draggable').draggable({
        revert: true,
        revertDuration: 250
    });

    // Initialise the Template Editor Widget
    $('#survey-layout').surveyLayout();
});
