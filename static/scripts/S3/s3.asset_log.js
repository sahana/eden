/**
 * Used by the Asset Log Form (modules/s3db/asset.py)
 */

$(document).ready(function() {
    var ajaxURL,
        siteField = $('#asset_log_site_id'),
        tree = $('#asset_log_layout_id-hierarchy');

    siteField.change(function() {
        ajaxURL = S3.Ap.concat('/org/site/' + siteField.val() + '/layout/hierarchy.tree');
        tree.hierarchicalopts('reload', ajaxURL);
    });
});
// END ========================================================================
