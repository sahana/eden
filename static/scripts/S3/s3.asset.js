/**
 * Used by the Asset Form (modules/s3db/asset.py)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

// Module pattern to hide internal vars
(function () {

    var hide_components = function() {
        // Hide the component items
        $('#asset_asset_sub_defaultitem__row1').hide();
        $('#asset_asset_sub_defaultitem__row').hide();

        // Submit appropriate data
        $('#asset_asset_sn').attr('disabled', false);
        $('#asset_asset_supply_org_id').attr('disabled', false);
        $('#asset_asset_purchase_date').attr('disabled', false);
        $('#asset_asset_purchase_price').attr('disabled', false);
        $('#asset_asset_purchase_currency').attr('disabled', false);

        // Show the top-level fields
        $('#asset_asset_sn__row1').show();
        $('#asset_asset_sn__row').show();
        $('#asset_asset_supply_org_id__row1').show();
        $('#asset_asset_supply_org_id__row').show();
        $('#asset_asset_purchase_date__row1').show();
        $('#asset_asset_purchase_date__row').show();
        $('#asset_asset_purchase_price__row1').show();
        $('#asset_asset_purchase_price__row').show();
        $('#asset_asset_purchase_currency__row1').show();
        $('#asset_asset_purchase_currency__row').show();
    }

    var show_components = function() {
        // Hide the top-level fields
        $('#asset_asset_sn__row1').hide();
        $('#asset_asset_sn__row').hide();
        $('#asset_asset_supply_org_id__row1').hide();
        $('#asset_asset_supply_org_id__row').hide();
        $('#asset_asset_purchase_date__row1').hide();
        $('#asset_asset_purchase_date__row').hide();
        $('#asset_asset_purchase_price__row1').hide();
        $('#asset_asset_purchase_price__row').hide();
        $('#asset_asset_purchase_currency__row1').hide();
        $('#asset_asset_purchase_currency__row').hide();

        // Show the component items
        $('#asset_asset_sub_defaultitem__row1').show();
        $('#asset_asset_sub_defaultitem__row').show();

        // Don't submit inappropriate data
        $('#asset_asset_sn').attr('disabled', true);
        $('#asset_asset_supply_org_id').attr('disabled', true);
        $('#asset_asset_purchase_date').attr('disabled', true);
        $('#asset_asset_purchase_price').attr('disabled', true);
        $('#asset_asset_purchase_currency').attr('disabled', true);
    }

    $(document).ready(function() {
        var checkbox = $('#asset_asset_kit');

        // Read current state
        if (checkbox.attr('checked')) {
            show_components();
        } else {
            hide_components();
        }

        // Listen for changes
        checkbox.change(function() {
            if (checkbox.attr('checked')) {
                show_components();
            } else {
                hide_components();
            }
        })

    });

}());
// END ========================================================================
