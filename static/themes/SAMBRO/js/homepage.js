$(document).ready(function(){

    // Zoom the map to the relevant alert when clicking on an Alert in the dataList
    $('#cap_alert_datalist .dl-item').click(function() {
        var alert_id = parseInt($(this).attr('id').split('-')[1]);
        S3.gis.refreshLayer('search_results', [['~.id', alert_id]]);
    });

});