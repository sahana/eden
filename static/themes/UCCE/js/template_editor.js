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

    // Drag'n'Drop
    $('.draggable').draggable({
        revert: true,
        revertDuration: 200
    });
    $('#survey-layout').droppable({
        drop: function(event, ui) {
            // @ToDo: Open QuestionEditorWidget with correct options for type
            var qtype = ui.draggable[0].id;
        }
    });

    var instructions = function(){
        
    }
});
