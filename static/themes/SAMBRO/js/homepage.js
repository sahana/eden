$(document).ready(function(){

    // Zoom the map to the relevant alert when clicking on an Alert in the dataList
    $('#cap_alert_datalist .dl-item').click(function() {
        var alert_id = parseInt($(this).attr('id').split('-')[1]);
        S3.gis.refreshLayer('search_results', [['~.id', alert_id]]);
    });

    // Show/Hide Filter options
    $('#alert-filter-form-show').click(function() {
        $('#alert-filter-form-show').hide();
        $('#alert-filter-form, #alert-filter-form-hide').show();
    });
    $('#alert-filter-form-hide').click(function() {
        $('#alert-filter-form, #alert-filter-form-hide').hide();
        $('#alert-filter-form-show').show();
    });

});