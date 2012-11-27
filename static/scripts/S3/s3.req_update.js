/* JS code to modify req/update forms
   - inserted into page in controller
*/

function add_site_to_staff_add_url() {
    var site_id = $('#req_req_site_id').val();
    if (site_id) {
        var url = $('#staff_add').attr('href');
        if (url.indexOf('&site_id=') == -1) {
            // Add to URL
            url = url + '&site_id=' + site_id;
        } else {
            // Update URL
            url = url.replace(/&site_id=.*/, '&site_id=' + site_id);
        }
        $('#staff_add').attr('href', url);
    }
}

$(document).ready(function() {
    // Read current value
    add_site_to_staff_add_url();
    // onChange
    $('#req_req_site_id').change(function() {
        add_site_to_staff_add_url();
    });
});