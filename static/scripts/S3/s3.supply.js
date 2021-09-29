/**
    Static JS Code related to Supply, Inv & Req
*/

S3.supply = Object();

/**
 * Globals called by filterOptionsS3 when Item Packs filtered based on Items
 */
S3.supply.fncPrepItem = function(data) {
    for (var i = 0; i < data.length; i++) {
        if (data[i].quantity == 1) {
            return data[i].name;
        }
    }
    return '';
}

S3.supply.fncRepresentItem = function(record, PrepResult) {
    if (record.quantity == 1) {
        return record.name;
    } else {
        return record.name + ' (' + record.quantity + ' x ' + PrepResult + ')';
    }
}

// END ========================================================================