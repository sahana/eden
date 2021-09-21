/**
 * Used by the inv/send controller when using inv_send_req
 * - set Sites based on selected Requests
 */

$(document).ready(function() {
    var ajaxURL,
        site,
        fromSites,
        toSites,
        reqField = $('#link_defaultreq'),
        req_id = reqField.val(),
        fromField = $('#inv_send_site_id'),
        toField = $('#inv_send_to_site_id');

    var lookupSites = function(req_id) {
        // Custom Method in RMS/config.py
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
            for (var i=0; i < fromSitesLength; i++) {
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
            for (var i=0; i < toSitesLength; i++) {
                site = toSites[i];
                toField.append(new Option(site[1], site[0]))
            }
            if (toSitesLength == 1) {
                // Only a single Site matches, so set to this Site
                toField.val(site[0]);
            }
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
});