/**
 * Used by the inv/send controller when using inv_send_req
 */

$(document).ready(function() {
    var ajaxURL,
        reqField = $('#link_defaultreq'),
        req_id = reqField.val(),
        siteField = $('#inv_send_site_id');

    var lookupSites = function(req_id) {
        ajaxURL = S3.Ap.concat('/req/req/sites.json?req_id=' + req_id);
        $.getJSONS3(ajaxURL, function(data) {
            // Clear all options
            siteField.html('');
            var site,
                optsNum = data.length;
            if (optsNum == 0) {
                // No Options!
                return;
            }
            // Add options
            for (var i=0; i < optsNum; i++) {
                site = data[i];
                siteField.append(new Option(site[1], site[0]))
            }
            if (optsNum == 1) {
                // Only a single Site matches, so set to this Site
                siteField.val(site[0]);
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