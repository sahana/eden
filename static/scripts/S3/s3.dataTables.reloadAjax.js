// Simple plugin to Ajax-refresh a datatable. This also allows to
// change the sAjaxSource URL for that table (e.g. in order to
// update URL filters). Use e.g. in a onclick-handler like:
//    dt = $('#<list_id>').dataTable();
//    dt.fnReloadAjax(<new URL>);
//
$.fn.dataTableExt.oApi.fnReloadAjax = function(oSettings, sNewSource) {

    if ( sNewSource != 'undefined' && sNewSource != null ) {
        // sNewSource is a string containing the new Ajax-URL for
        // this instance, so override the previous setting
        oSettings.sAjaxSource = sNewSource;
    }

    // Show the "Processing..." box
    this.oApi._fnProcessingDisplay( oSettings, true );

    // Call ajax with empty request to trigger the pipeline
    // script, clear the table cache and run the following
    // callback:
    var that = this;
    oSettings.ajax({}, function(json) {

        // Clear the table
        that.oApi._fnClearTable(oSettings);

        // Trigger the pipeline script again (this time without callback),
        // in  order to re-load the table data from the server:
        that.fnDraw();

    }, oSettings );
};
