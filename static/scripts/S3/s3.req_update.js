/* JS code to modify req/update forms
   - inserted into page in controller
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
});