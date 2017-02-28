/* Static JavaScript code for the Data Collection Questions tab */

$(document).ready(function() {
    var qtype = $('#dc_question_field_type');
    if (qtype.val() == 6) {
        // Options Field
        // Convert the TEXTAREA field to an INPUT
        $textarea = $('#dc_question_options');
        $input = $('<input></input>').attr({
            id: $textarea.prop('id'),
            name: $textarea.prop('name'),
            value: $textarea.val()
        });
        $textarea.after($input).remove();
        // Convert the JSON values into comma-separated
        var json_opts = JSON.parse($input.val()),
            opt,
            comma_opts = '';
        for (opt in json_opts) {
            if (json_opts.hasOwnProperty(opt)) {
                if (comma_opts != '') {
                    comma_opts += ',';
                };
                comma_opts += json_opts[opt];
            }
        };
        $('#dc_question_options').val(comma_opts);
        // Use Tags widget to input Options
        $('#dc_question_options').tagit();
    } else {
        // Hide the Options field & label
        $('#dc_question_options, #dc_question_options__label').hide();
    }
    qtype.change(function() {
        if ($(this).val() == 6) {
            // Options Field
            // Show the Options field & label
            $('#dc_question_options, #dc_question_options__label').show();
            // Convert the TEXTAREA field to an INPUT
            $textarea = $('#dc_question_options');
            $input = $('<input></input>').attr({
                id: $textarea.prop('id'),
                name: $textarea.prop('name'),
                value: $textarea.val()
            });
            $textarea.after($input).remove();
            // Use Tags widget to input Options
            $input.tagit();
        } else {
            // Hide the Options field & label
            $('#dc_question_options, #dc_question_options__label').hide();
        }
    });
    $('form').submit(function() {
        // Do the normal form-submission tasks
        // @ToDo: Look to have this happen automatically
        // http://forum.jquery.com/topic/multiple-event-handlers-on-form-submit
        // http://api.jquery.com/bind/
        S3ClearNavigateAwayConfirm();

        if (qtype.val() == 6) {
            // Options Field
            // Convert the comma-separated values into JSON
            var $input = $('#dc_question_options'),
                json_opts = Object(),
                comma_opts = $input.val(),
                pieces = comma_opts.split(',');
            $(pieces).each(function(index) {
                json_opts[index + 1] = pieces[index];
            });
            $input.val(JSON.stringify(json_opts));
        }
        // Allow the Form's save to continue
        return true;
    });
});