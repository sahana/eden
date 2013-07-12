/*
    Static JS for guided tours
*/
function pre_step_callback(tip_index, tip_html){
    $.each(pre_step_data,function(indx, list){
    /* list will have three entires, and is set up in 00_utils.py s3_guided_tour()
       list[0]: The tip count
       list[1]: The dataTable id to get a record id
       list[2]: The dataTable row from which to extract the data

       This function will replace placeholders with data from the dataTable
       This cannot be done in Python because the data for the dataTable will arrive
       after this has been sent.
       */
        var cnt = list[0];
        var dt_id = list[1];
        var dt_row = list[2];

        if (tip_index== cnt){
            var columns = $('#'+dt_id+' thead th').map(function() {
            return $(this).text().toLowerCase();
            });
            columns[0]="id";
            var tableObject = $('#'+dt_id+' tbody tr').map(function(i) {
            var row = {};
            if (i == dt_row) {
            $(this).find('td').each(function(i) {
              var rowName = columns[i];
              if (rowName == 'id'){row[rowName] = $(this).find('a').attr('db_id');}
              else {row[rowName] = $(this).text();}
            });
            return row;
            }
            }).get();
            var html = $(tip_html)[0].innerHTML;
            if (tableObject.length > 0) {
              var replacementData = tableObject[0];
              $.each(replacementData, function (key, value){
                var re = new RegExp("dt_"+key,"g");
                html = html.replace(re, value);
            });
            }
            $($(tip_html)[0]).html(html);
        }
    });
}

function post_step_callback(tip_index, tip_html){
    $.each(post_step_data,function(indx, list){
    /* list will have two or four entires, and is set up in 00_utils.py s3_guided_tour()
       list[0]: The tip count
       list[1]: The URL to relocate to
       list[2]: The dataTable id to get a record id
       list[3]: The dataTable row from which to extract the id

       This function is used to jump to a new URL extra data can be obtained from the dataTable
       */
        var cnt = list[0];
        var url = list[1];

        if (tip_index== cnt){
            if (list.length >2){
                var dt_id = list[2]
                var dt_row = list[3];
                var row_id = $($('td:first a:first', '#'+dt_id+' tbody tr')[dt_row]).attr('db_id')
                url = url.replace(/dt_id/g, row_id);
            }
            window.location.href=url;
        }
    });
}

function post_ride_callback(tip_index, tip_html){
    /* post_ride_data will have two entires, and is set up in 00_utils.py s3_guided_tour()
       post_ride_data[0]: The number of the last tip
       post_ride_data[1]: The tour_id

       This function will send an AJAX call to update the database
       to record that the tour has been completed
       */
    var data = new Object();
    data['completed'] = post_ride_data[0];
    data['tour_id'] = post_ride_data[1];
    $.ajax({type: 'POST', url: S3.Ap.concat('/tour/guided_tour_finished'), data: data});
}

$(document).ready(function() {
    var pre_step_html = $('#prestep_data');
    if (pre_step_html.length > 0) {
        // Pass to global scope
        pre_step_data = $.parseJSON(pre_step_html.val());
        prestep_callback = pre_step_callback;
    } else {prestep_callback=$.noop;}

    var post_step_html = $('#poststep_data');
    if (post_step_html.length > 0) {
        // Pass to global scope
        post_step_data = $.parseJSON(post_step_html.val());
        poststep_callback = post_step_callback;
    } else {poststep_callback=$.noop;}

    var post_ride_html = $('#postride_data');
    if (post_ride_html.length > 0) {
        // Pass to global scope
        post_ride_data = $.parseJSON(post_ride_html.val());
        postride_callback = post_ride_callback;
    } else {postride_callback=$.noop;}

    $("#joyrideID_1").joyride({
        autoStart : true,
        preStepCallback : prestep_callback,
        postStepCallback : poststep_callback,
        postRideCallback : post_ride_callback
    });
});

