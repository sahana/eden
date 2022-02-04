/**
 * Used by the inv/recv controller
 * - show/Hide fields according to Shipment Type
 * - set Sites based on selected Requests
 * - set Labels based on Transport Type
 */

$(document).ready(function() {
    
    var recvTypeField = $('#inv_recv_type'),
        reqField = $('#link_defaultreq'),
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
        recvTypeField.on('change', recvTypeChange);
    }

    if (reqField.length) {

        // Set Sites based on selected Requests
        var ajaxURL,
            fromSites,
            toSites,
            req_id = reqField.val(),
            fromField = $('#inv_recv_from_site_id'),
            toField = $('#inv_recv_site_id');

        var lookupSites = function(req_id) {
            ajaxURL = S3.Ap.concat('/inv/req/recv_sites.json?req_id=' + req_id);
            $.getJSONS3(ajaxURL, function(data) {
                fromSites = data[0];
                fromSitesLength = fromSites.length;
                if (fromSitesLength) {
                    if (fromSitesLength == 1) {
                        // Only a single Site matches, so set to this Site
                        fromField.val(fromSites[0]);
                    }
                    // Set to 'Internal Shipment'
                    $('#inv_recv_type').val(11)
                                       .trigger('change');
                }
                toSites = data[1];
                if (toSites.length == 1) {
                    // Only a single Site matches, so set to this Site
                    toField.val(toSites[0]);
                }
            });
        };

        if (req_id) {
            // Update form
            lookupSites(req_id);
        }

        reqField.on('change', function() {
            req_id = reqField.val();
            lookupSites(req_id);
        });
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
        transportTypeField.on('change', transportTypeChange);
    }
});