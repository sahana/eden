// Simple plugin to Ajax-refresh a datatable. This also allows to
// change the Ajax Source URL for that table (e.g. in order to
// update URL filters). Use e.g. in a onclick-handler like:
//    dt = $('#<list_id>').dataTable();
//    dt.reloadAjax(<new URL>);
//

var tableIdReverse = function(id) {
    
    return -1;
};

$.fn.dataTableExt.oApi.reloadAjax = function(settings, newSource) {

    if ( typeof newSource != 'undefined' && newSource != null ) {
        // newSource is a string containing the new Ajax-URL for
        // this instance, so override the previous setting
        S3.dataTables.ajax_urls[settings.nTable.id] = newSource;
    }
    // Show the "Processing..." box
    this.oApi._fnProcessingDisplay( settings, true );

    var that = this;
    // Call ajax with empty data to trigger the pipeline
    // script, clear the table cache and run the following callback
    settings.ajax( [], function(json) {

        // Clear the table
        that.oApi._fnClearTable( settings );

        // Trigger the pipeline script again (this time without callback),
        // in  order to re-load the table data from the server:
        that.fnDraw();

        // Remove the "Processing..." box
        that.oApi._fnProcessingDisplay( settings, false );

    }, settings );
}