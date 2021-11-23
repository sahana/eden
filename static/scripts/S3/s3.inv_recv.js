/**
 * Used by the inv/recv controller
 * - show/Hide fields according to Shipment Type
 * - set Labels based on Transport Type
 */

$(document).ready(function() {
    
    var recvTypeField = $('#inv_recv_type'),
        transportTypeField = $('#inv_recv_transport_type');

    if (recvTypeField.length) {
        // Show/Hide fields according to Shipment Type
        var recvTypeChange = function() {
            var recvType = recvTypeField.val();
            if (recvType != undefined) {
                if (recvType == 11) { // @ToDo: pass this value instead of hardcoding it - base on s3cfg.py 
                    // Internal Shipment 
                    $('[id^="inv_recv_from_site_id__row"]').show();
                    $('[id^="inv_recv_organisation_id__row"]').hide();
                } else if (recvType >= 32) { // @ToDo: pass this value instead of hardcoding it - base on s3cfg.py 
                    // External Shipment: Donation, Purchase, Loan, In-Transit
                    $('[id^="inv_recv_from_site_id__row"]').hide();
                    $('[id^="inv_recv_organisation_id__row"]').show();
                } else {
                    // Unknown Type
                    $('[id^="inv_recv_from_site_id__row"]').hide();
                    $('[id^="inv_recv_organisation_id__row"]').hide();
                }
            }
        };

        recvTypeChange();
        recvTypeField.change(recvTypeChange);
    }

    if (transportTypeField.length) {
        // Show/Hide fields according to Shipment Type
        var transportTypeChange = function() {
            var transportType = transportTypeField.val();
            switch (transportType) {
                case 'Air':
                    $('#inv_recv_transport_ref__row').show();
                    $('#inv_recv_transport_ref__label').html(i18n.AWB + ':');
                    $('#inv_recv_registration_no__row').show();
                    $('#inv_recv_registration_no__label').html(i18n.flight + ':');
                    break;
                case 'Sea':
                    $('#inv_recv_transport_ref__row').show();
                    $('#inv_recv_transport_ref__label').html(i18n.BL + ':');
                    $('#inv_recv_registration_no__row').show();
                    $('#inv_recv_registration_no__label').html(i18n.vessel + ':');
                    break;
                case 'Road':
                    $('#inv_recv_transport_ref__row').show();
                    $('#inv_recv_transport_ref__label').html(i18n.CMR + ':');
                    $('#inv_recv_registration_no__row').show();
                    $('#inv_recv_registration_no__label').html(i18n.vehicle + ':');
                    break;
                case 'Hand':
                    $('#inv_recv_transport_ref__row').hide();
                    $('#inv_recv_registration_no__row').hide();
                    break;
                default:
                    // Not selected or Rail
                    $('#inv_recv_transport_ref__row').show();
                    $('#inv_recv_transport_ref__label').html(i18n.ref + ':');
                    $('#inv_recv_registration_no__row').show();
                    $('#inv_recv_registration_no__label').html(i18n.reg + ':');
            }
        };

        transportTypeChange();
        transportTypeField.change(transportTypeChange);
    }
});