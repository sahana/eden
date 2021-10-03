/**
 * Used by the Event Asset Form (incident() in controllers/event.py)
 */

$(document).ready(function() {
    // Filter Assets by Item Type
    var itemField = $('#event_asset_item_id'),
        popupLink = $('#asset_add'),
        url,
        fncRepresentAsset = function(record) {
        return record.number;
    };
    $.filterOptionsS3({
        'trigger': 'item_id',
        'target': 'asset_id',
        'lookupPrefix': 'asset',
        'lookupResource': 'asset',
        'fncRepresent': fncRepresentAsset
    });
    // Update Create Asset S3PopupLink URL to filter options returned by Item Type
    itemField.on('change.event_asset', function() {
        url = popupLink.attr('href');
        url += '&optionsVar=item_id&optionsValue=' + itemField.val();
        popupLink.attr('href', url);
    });
});
// END ========================================================================
