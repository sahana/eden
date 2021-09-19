/**
 * Used by the inv/inv_item controller when direct_stock_edits are allowed and bin_site_layout is configured
 */

$(document).ready(function() {
    var ajaxURL,
        siteField = $('#inv_inv_item_site_id'),
        tree = $('#inv_inv_item_layout_id-hierarchy');
    siteField.change(function() {
        ajaxURL = S3.Ap.concat('/org/site/' + siteField.val() + '/layout/hierarchy.tree');
        tree.hierarchicalopts('reload', ajaxURL);
    });
});