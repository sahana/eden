/* JS code to modify req/update forms if type==8 (Summary)
   - inserted into page in controller
*/
function idescape(input) {
    // Create a valid ID
    var output = input.replace(/ /g, 'SPACE')
                      .replace(/&/g, 'AMP');
    return output;
}

$(document).ready(function() {
    if ($('#req_req_purpose').length > 0) {
        // Update form
        // Replace the Purpose field with a list of checkboxes
        $('#req_req_purpose__row1').hide();
        $('#req_req_purpose__row').hide();
        var current = $('#req_req_purpose').val();
        if (current) {
            current = JSON.parse(current);
        }
        var item, checked, row;
        for (var i=0; i < req_summary_items.length; i++) {
            item = req_summary_items[i];
            if ((current) && ($.inArray(item, current) != -1)) {
                checked = ' checked';
            } else {
                checked = '';
            }
            row = '<tr class="summary_item"><td>' + item + '</td><td><input type="checkbox"' + checked + ' id="req_summary_' + idescape(item) + '"></td></tr>';
            $('#req_req_purpose__row').after(row);
        }
        $('form').submit(function() {
            // Read the checkboxes & JSON-Encode them
            var items = [];
            for (var i=0; i < req_summary_items.length; i++) {
                var item = req_summary_items[i];
                if ($('#req_summary_' + idescape(item)).is(':checked')) {
                    items.push(item);
                }
            }
            $('#req_req_purpose').val(JSON.stringify(items));
            // Allow the Form's save to continue
            return true;
        });
     }
});