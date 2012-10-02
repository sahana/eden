/**
 * Used by Project Tasks (modules/eden/project.py)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

/* Global vars */
S3.project_task_update_fields = function () {
    // Common options
    var value_high = 1;
    var represent_high = '';

    // Milestone Filter
    var url = S3.Ap.concat('/project/task/options.s3json?field=milestone_id');
    $.getJSONS3(url, function (data) {
        var selector = $('#project_task_milestone_id');
        var initial_value = selector.val();
        var options = $('#project_task_milestone_id' + ' >option')
        var append = [];
        var value, represent;
        $.each(data['option'], function() {
            value = this['@value'];
            represent = this['$'];
            if (typeof represent === 'undefined') {
                represent = '';
            }
            append.push(["<option value='", value, "'>", represent, "</option>"].join(''));
            // Type conversion: http://www.jibbering.com/faq/faq_notes/type_convert.html#tcNumber
            //numeric_value = (+value)
            //if (numeric_value > value_high) {
            //    value_high = numeric_value;
            //    represent_high = represent;
            //}
        });
        // Clean up the caller
        options.remove();
        selector.append(append.join('')).change();

        // IE6 needs time for DOM to settle: http://csharperimage.jeremylikness.com/2009/05/jquery-ie6-and-could-not-set-selected.html
        setTimeout( function() {
            // Set the newly-created value (one with highest value)
            //selector.val(value_high).change();
            if (initial_value) {
                selector.val(initial_value).change();
            }
        }, 1);

        // Don't hassle users about unsaved data just for these dropdown settings
        S3ClearNavigateAwayConfirm();
    });
}

$(document).ready(function() {
    S3.project_task_update_fields();
    $('#project_task_project_project_id').change(function() {
        S3.project_task_update_fields();
    });
});