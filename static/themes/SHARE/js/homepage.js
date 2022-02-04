$(document).ready(function(){

    // Zoom the map to the relevant request when clicking on a request summary in the dataList
    $('#req_datalist .dl-item').on('click', function() {
        var req_id = parseInt($(this).attr('id').split('-')[1]);
        S3.gis.refreshLayer('search_results', [['~.id', req_id]]);
    });

    // Set the maximum height of the datalist to the size of screen
    $('#req_datalist').css('max-height', $(window).height());

    // Show/Hide Filter options
    $('#req-filter-form-show').on('click', function() {
        $('#req-filter-form-show').hide();
        $('#req-filter-form, #req-filter-form-hide').show();
    });
    $('#req-filter-form-hide').on('click', function() {
        $('#req-filter-form, #req-filter-form-hide').hide();
        $('#req-filter-form-show').show();
    });

});
