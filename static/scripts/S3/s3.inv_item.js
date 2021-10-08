/**
 * Used by the inv/inv_item controller when direct_stock_edits are allowed and bin_site_layout is configured
 */

$(document).ready(function() {
    var ajaxURL,
        createButton = $('#inv_inv_item_layout_id-create-btn'),
        re = /%5Bid%5D/g,
        siteField = $('#inv_inv_item_site_id'),
        oldSiteID,
        siteID,
        tree = $('#inv_inv_item_layout_id-hierarchy');

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