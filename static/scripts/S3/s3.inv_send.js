/**
 * Used by inv_send_controller
 * - set Sites based on selected Requests
 * - set Labels based on Transport Type
 */

$(document).ready(function() {

    var reqField = $('#link_defaultreq'),
        transportTypeField = $('#inv_send_transport_type');

   if (reqField.length) {

        var ajaxURL,
            site,
            fromSites,
            toSites,
            req_id = reqField.val(),
            fromField = $('#inv_send_site_id'),
            toField = $('#inv_send_to_site_id');
       
       var lookupSites = function(req_id) {
            ajaxURL = S3.Ap.concat('/inv/req/send_sites.json?req_id=' + req_id);
            $.getJSONS3(ajaxURL, function(data) {
                // Clear all options
                fromField.html('');
                toField.html('');
                fromSites = data[0];
                fromSitesLength = fromSites.length;
                if (fromSitesLength == 0) {
                    // No Options => No Shipment can be made (either due to permissions, no items requested or all items already fulfilled)
                    return;
                }
                // Add options
                for (var i = 0; i < fromSitesLength; i++) {
                    site = fromSites[i];
                    fromField.append(new Option(site[1], site[0]))
                }
                if (fromSitesLength == 1) {
                    // Only a single Site matches, so set to this Site
                    fromField.val(site[0]);
                }
                toSites = data[1];
                toSitesLength = toSites.length;
                if (toSitesLength == 0) {
                    // No Options => No Shipment can be made (e.g. Permissions)
                    return;
                }
                // Add options
                for (var i = 0; i < toSitesLength; i++) {
                    site = toSites[i];
                    toField.append(new Option(site[1], site[0]))
                }
                if (toSitesLength == 1) {
                    // Only a single Site matches, so set to this Site
                    toField.val(site[0]);
                }
                // Set to 'Internal Shipment'
                $('#inv_send_type').val(11);
            });
        };

        if (req_id) {
            // Initial setting - coming from 'Fulfil Request' button
            lookupSites(req_id);
        }

        reqField.change(function() {
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
                    $('#inv_send_transport_ref__row').show();
                    $('#inv_send_transport_ref__label').html(i18n.AWB);
                    $('#inv_send_registration_no__row').show();
                    $('#inv_send_registration_no__label').html(i18n.flight);
                    break;
                case 'Sea':
                    $('#inv_send_transport_ref__row').show();
                    $('#inv_send_transport_ref__label').html(i18n.BL);
                    $('#inv_send_registration_no__row').show();
                    $('#inv_send_registration_no__label').html(i18n.vessel);
                    break;
                case 'Road':
                    $('#inv_send_transport_ref__row').show();
                    $('#inv_send_transport_ref__label').html(i18n.ref);
                    $('#inv_send_registration_no__row').show();
                    $('#inv_send_registration_no__label').html(i18n.vehicle);
                    break;
                case 'Hand':
                    $('#inv_send_transport_ref__row').hide();
                    $('#inv_send_registration_no__row').hide();
                    break;
                default:
                    // Not selected
                    $('#inv_send_transport_ref__row').show();
                    $('#inv_send_transport_ref__label').html(i18n.ref);
                    $('#inv_send_registration_no__row').show();
                    $('#inv_send_registration_no__label').html(i18n.reg);
            }
        };

        transportTypeChange();
        transportTypeField.change(transportTypeChange);
    }
});