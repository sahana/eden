$(document).ready(function(){
    var label_state = function(el) {
        var question_id = el.attr('name').split('-')[1],
            label_row = $('#label-row-' + question_id);
        if (el.prop('checked')) {
            // Show the Label row
            label_row.show();
        } else {
            // Hide the Label row
            label_row.hide();
        }
    };
    $('#report_filters').find(':checkbox').each(function() {
        var $this = $(this);
        // Show/Hide Label Row based on initial state
        label_state($this);
        // Show/Hide Label Row based on changed state
        $this.on('change.ucce', function() {
            label_state($this);
        });
    });
});
