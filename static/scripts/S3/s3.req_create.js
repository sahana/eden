/* JS code to modify req/create forms
   - inserted into page in req_create_form_mods()
*/

$(document).ready(function() {
    
    // onChange
    $('#req_req_site_id').change(function() {
        var site_id = $('#req_req_site_id').val();
        var url = $('#staff_add').attr('href');
        if (url.indexOf('&site_id=') == -1) {
            // Add to URL
            url = url + '&site_id=' + site_id;
        } else {
            // Update URL
            url = url.replace(/&site_id=.*/, '&site_id=' + site_id);
        }
        $('#staff_add').attr('href', url);
    });

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
});