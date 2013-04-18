/* JS code to modify req/create forms
   - inserted into page in req_create_form_mods()
*/

$(document).ready(function() {
    // Read current value
    var site_id = $('#req_req_site_id').val();
    if (site_id) {
        var url = $('#staff_add').attr('href');
        // Add to URL
        url = url + '&site_id=' + site_id;
        $('#staff_add').attr('href', url);
    }
    // onChange happens in S3.js S3OptionsFilter

    $('#req_req_is_template').change(function() {
        if ($('#req_req_is_template').is(':checked')) {
            $('#req_req_date__row1').hide();
            $('#req_req_date__row').hide();
            $('#req_req_date_required__row1').hide();
            $('#req_req_date_required__row').hide();
            $('#req_req_date_required_until__row1').hide();
            $('#req_req_date_required_until__row').hide();
            $('#req_req_recv_by_id__row1').hide();
            $('#req_req_recv_by_id__row').hide();
        } else {
            $('#req_req_date__row1').show();
            $('#req_req_date__row').show();
            $('#req_req_date_required__row1').show();
            $('#req_req_date_required__row').show();
            $('#req_req_recv_by_id__row1').show();
            $('#req_req_recv_by_id__row').show();
            $('#req_req_date_required_until__row1').show();
            $('#req_req_date_required_until__row').show();
        }
    });

    var startDateTextBox = $('#req_req_date_required');
    var endDateTextBox = $('#req_req_date_required_until');

    startDateTextBox.datetimepicker({
	    onClose: function (dateText, inst) {
            if (endDateTextBox.val() != '') {
                var testStartDate = startDateTextBox.datetimepicker('getDate');
                var testEndDate = endDateTextBox.datetimepicker('getDate');
                if (testStartDate > testEndDate){
                    endDateTextBox.datetimepicker('setDate', testStartDate);
                }
            } else {
                endDateTextBox.val(dateText);
            }
        },
        onSelect: function (selectedDateTime) {
            endDateTextBox.datetimepicker('option', 'minDate', startDateTextBox.datetimepicker('getDate'));
        }
    });

    endDateTextBox.datetimepicker({
        onClose: function (dateText, inst) {
            if (startDateTextBox.val() != '') {
                var testStartDate = startDateTextBox.datetimepicker('getDate');
                var testEndDate = endDateTextBox.datetimepicker('getDate');
                if (testStartDate > testEndDate){
                    startDateTextBox.datetimepicker('setDate', testEndDate);
                }
            } else {
                startDateTextBox.val(dateText);
            }
        },
        onSelect: function (selectedDateTime) {
            startDateTextBox.datetimepicker('option', 'maxDate', endDateTextBox.datetimepicker('getDate'));
        }
    });
    $("#req_req_site_id").focus();
});
