$(document).ready(function(){

    // Zoom the map to the relevant alert when clicking on an Alert in the dataList
    $('#cap_alert_datalist .dl-item').on('click', function() {
        var alert_id = parseInt($(this).attr('id').split('-')[1]);
        S3.gis.refreshLayer('search_results', [['~.id', alert_id]]);
    });

    // Set the maximum height of the datalist to the size of screen
    $('#cap_alert_datalist').css('max-height', $(window).height());

    // Show/Hide Filter options
    $('#alert-filter-form-show').on('click', function() {
        $('#alert-filter-form-show').hide();
        $('#alert-filter-form, #alert-filter-form-hide').show();
    });
    $('#alert-filter-form-hide').on('click', function() {
        $('#alert-filter-form, #alert-filter-form-hide').hide();
        $('#alert-filter-form-show').show();
    });

});