/* Static JavaScript code for the Questions tab on Data Collection Templates */

S3.dc_question_types = function(value, init) {
    if (value == '2') {
        // Integer Field
        // Hide the Options field & label
        options_field = $('#dc_question_options');
        if (options_field.hasClass('tagit-hidden-field')) {
            options_field.tagit('destroy');
        }
        $('#dc_question_options__row').hide();
        if (init) {
            var $input = $('#dc_question_totals'),
                value = $input.val();
            if (value) {
                // Convert the JSON values into comma-separated
                var json_opts = JSON.parse(value),
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
                $input.val(comma_opts);
            }
        }
        // Show the Totals field, label & comment
        $('#dc_question_totals__row').show();
    } else if (value == '6') {
        // Options Field
        // Hide the Totals field, label & comment
        $('#dc_question_totals__row').hide();
        if (init) {
            var value = $input.val();
            if (value) {
                // Convert the JSON values into comma-separated
                var json_opts = JSON.parse(value),
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
            }
        }
        // Convert the TEXTAREA field to an INPUT
        $textarea = $('#dc_question_options');
        $input = $('<input></input>').attr({
            id: $textarea.prop('id'),
            name: $textarea.prop('name'),
            value: $textarea.val()
        });
        $textarea.after($input).remove();
        // Show the Options field & label
        $('#dc_question_options__row').show();
        // Use Tags widget to input Options
        $('#dc_question_options').tagit();
    } else if (value == '9') {
        // Grid Pseudo-Field
        // Hide the Totals field, label & comment
        $('#dc_question_totals__row').hide();
        // Hide the Options field & label
        options_field = $('#dc_question_options');
        if (options_field.hasClass('tagit-hidden-field')) {
            options_field.tagit('destroy');
        }
        $('#dc_question_options__row').hide();
        /*
        if (init) {
            // @ToDo: Convert the JSON values into simpler format: rlabel1,rlabel2;clabel1,clabel2
            var $input = $('#dc_question_grid'),
                value = $input.val();
            if (value) {
                var json_opts = JSON.parse(value),
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
                $input.val(comma_opts);
            }
        } */
        // Show the Grid field & label
        //$('#dc_question_grid__row').show();
    } else {
        // Hide the Totals field, label & comment
        $('#dc_question_totals__row').hide();
        // Hide the Options field & label
        options_field = $('#dc_question_options');
        if (options_field.hasClass('tagit-hidden-field')) {
            options_field.tagit('destroy');
        }
        $('#dc_question_options__row').hide();
    }
    if (init && (value != '9')) {
        // Potential Grid Child
        // Convert the JSON values into simpler format: grid,row,col
        var $input = $('#dc_question_grid'),
            value = $input.val();
        if (value) {
            var json_opts = JSON.parse(value),
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
            $input.val(comma_opts);
        }
    }
}

$(document).ready(function() {
    var qtype = $('#dc_question_field_type');
    // Set initial state
    S3.dc_question_types(qtype.val(), true);

    qtype.change(function() {
        // Update state
        S3.dc_question_types($(this).val(), false);
    });

    $('form').submit(function() {
        // Do the normal form-submission tasks
        // @ToDo: Look to have this happen automatically
        // http://forum.jquery.com/topic/multiple-event-handlers-on-form-submit
        S3ClearNavigateAwayConfirm();

        var value = qtype.val()
        if (value == '2') {
            // Integer Field
            // Convert the comma-separated values into JSON
            var $input = $('#dc_question_totals'),
                json_opts = [],
                comma_opts = $input.val(),
                pieces = comma_opts.split(',');
            $(pieces).each(function(index) {
                json_opts.push(pieces[index]);
            });
            $input.val(JSON.stringify(json_opts));
        } else if (value == '6') {
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
        if (value == '9') {
            // Grid Pseudo-Field
            // @ToDo: Convert the comma-separated values into JSON
        
        } else {
            // Potential Grid Child
            // Convert the comma-separated values into JSON
            var $input = $('#dc_question_grid'),
                json_opts = [],
                comma_opts = $input.val(),
                pieces = comma_opts.split(',');
            $(pieces).each(function(index) {
                json_opts.push(pieces[index]);
            });
            $input.val(JSON.stringify(json_opts));
        }
        // Allow the Form's save to continue
        return true;
    });
});