/**
 * Used by the Asset Log Form (modules/s3db/asset.py)
 */

$(document).ready(function() {
    var ajaxURL,
        createButton = $('#asset_log_layout_id-create-btn'),
        re = /%5Bid%5D/g,
        siteField = $('#asset_log_site_id'),
        oldSiteID,
        siteID,
        tree = $('#asset_log_layout_id-hierarchy');

    siteField.change(function() {
        siteID = siteField.val(),
        ajaxURL = S3.Ap.concat('/org/site/' + siteID + '/layout/hierarchy.tree');
        tree.hierarchicalopts('reload', ajaxURL);
        if (oldSiteID) {
            ajaxURL = createButton.attr('href').replace(oldSiteID, siteID);
        } else {
            ajaxURL = createButton.attr('href').replace(re, siteID);
        }
        createButton.attr('href', ajaxURL);
        oldSiteID = siteID;
    });
});
// END ========================================================================
