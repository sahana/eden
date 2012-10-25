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
        buttonImage: S3.Ap.concat('/static/img/jquery-ui/calendar.gif'),
        buttonImageOnly: true,
        dateFormat: 'yy-mm-dd',
        isRTL: S3.rtl
    });

    // Time fields - use jquery.ui.timepicker
    $('input.time').timepicker({
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
