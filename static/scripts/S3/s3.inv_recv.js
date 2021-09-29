/**
 * Used by the inv/recv controller
 * - show/Hide fields according to Shipment Type
 */

$(document).ready(function() {

    // Show/Hide fields according to Shipment Type
    var InvRecvTypeChange = function() {
        var RecvType = $("#inv_recv_type").val();
        if (RecvType != undefined) {
            if ( RecvType == 11) { // @ToDo: pass this value instead of hardcoding it - base on s3cfg.py 
                // Internal Shipment 
                $('[id^="inv_recv_from_site_id__row"]').show();
                $('[id^="inv_recv_organisation_id__row"]').hide();
            } else if ( RecvType >= 32) { // @ToDo: pass this value instead of hardcoding it - base on s3cfg.py 
                // External Shipment: Donation, Purchase, Consignment, In-Transit
                $('[id^="inv_recv_from_site_id__row"]').hide();
                $('[id^="inv_recv_organisation_id__row"]').show();
            } else {
                // Unknown Type
                $('[id^="inv_recv_from_site_id__row"]').hide();
                $('[id^="inv_recv_organisation_id__row"]').hide();
            }
        }
    };

    InvRecvTypeChange();
    $('#inv_recv_type').change(InvRecvTypeChange);

});