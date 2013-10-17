/**
 * JS to handle Date & Time form fields
 */

$(document).ready(function() {
    // Date fields - use jquery.ui.datepicker
    $('input.date').datepicker({
        changeMonth: true,
        changeYear: true,
        //showOtherMonths: true, selectOtherMonths: true,
        showOn: 'both',
        // We want to be able to select image in CSS
        //buttonImage: S3.Ap.concat('/static/img/jquery-ui/calendar.gif'),
        //buttonImageOnly: true,
        buttonText: '',
        dateFormat: 'yy-mm-dd',
        isRTL: S3.rtl
    });

    // Time fields - use jquery.ui.fgtimepicker
    // (could also be migrated to jquery.ui.timepicker.addon.js,
    //  just use .timepicker instead - but this one seems easier
    //  to use than a slider)
    $('input.time').fgtimepicker({
        hourText: i18n.hour,
        minuteText: i18n.minute,
        defaultTime: ''
    });
});

/* Function to ensure that end_date is always start-date or later */
S3.start_end_date = function(start_field, end_field) {
    // This gets overridden by the widget when done from prep
    // - need to instantiate from postp if we need this
    var min = $('#' + start_field).datepicker('getDate');
    if (min) {
        $('#' + end_field).datepicker('option', 'minDate', min);
    }
    $('#' + start_field).change(function() {
        var min = $('#' + start_field).datepicker('getDate');
        $('#' + end_field).datepicker('option', 'minDate', min);
        var curr = $('#' + end_field).datepicker('getDate');
        if (curr && curr < min) {
            $('#' + end_field).datepicker('setDate', min);
        }
    });
};
