(function() {
    S3.supply.fncRepresentItemT = function(record) {
        length = 32;
        name = record.name;
        if (name.length > length) {
            return name.substring(0, length) + '...';
        } else {
            return name;
        }
    }
    $.filterOptionsS3({
      'trigger': {'alias': 'response_line', 'name': 'item_category_id'},
      'target': {'alias': 'response_line', 'name': 'item_id'},
      'scope': 'row',
      'lookupPrefix': 'supply',
      'lookupResource': 'item',
      //'fncPrep': S3.supply.fncPrepItem,
      'fncRepresent': S3.supply.fncRepresentItemT
    })
    $.filterOptionsS3({
      'trigger': {'alias':'response_line','name':'item_id'},
      'target': {'alias':'response_line','name':'item_pack_id'},
      'scope': 'row',
      'lookupPrefix': 'supply',
      'lookupResource' :'item_pack',
      'msgNoRecords': i18n.no_packs
    })

    var fncRepresentLocation = function(level) {
        // Represent location as Lx name rather than name
        return function(record) {
            return record[level] || record.name;
        };
    };
    $.filterOptionsS3({
      'trigger': 'location_id_L2',
      'target': {'name': 'coarse_location_id'},
      'lookupPrefix': 'gis',
      'lookupResource': 'location',
      // Level hardcoded for SHARE/LK
      'lookupURL': S3.Ap.concat('/gis/location.json?l=L3&adm='),
      'fncRepresent': fncRepresentLocation('L3')
    })
    $.filterOptionsS3({
      'trigger': {'alias': 'response_line', 'name': 'coarse_location_id'},
      'target': {'alias': 'response_line', 'name': 'location_id'},
      'scope': 'row',
      'lookupPrefix': 'gis',
      'lookupResource': 'location',
      // Level hardcoded for SHARE/LK
      'lookupURL': S3.Ap.concat('/gis/location.json?l=L4&adm='),
      'fncRepresent': fncRepresentLocation('L4')
    })
})(jQuery);
