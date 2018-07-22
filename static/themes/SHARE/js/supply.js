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
  'trigger': {'alias': 'need_line', 'name': 'item_category_id'},
  'target': {'alias': 'need_line', 'name': 'item_id'},
  'scope': 'row',
  'lookupPrefix': 'supply',
  'lookupResource': 'item',
  //'fncPrep': S3.supply.fncPrepItem,
  'fncRepresent': S3.supply.fncRepresentItemT
})
$.filterOptionsS3({
  'trigger': {'alias':'need_line','name':'item_id'},
  'target': {'alias':'need_line','name':'item_pack_id'},
  'scope': 'row',
  'lookupPrefix': 'supply',
  'lookupResource' :'item_pack',
  'msgNoRecords': i18n.no_packs
})
$.filterOptionsS3({
  'trigger': 'location_id_L2',
  'target': {'name': 'coarse_location_id'},
  'lookupPrefix': 'gis',
  'lookupResource': 'location',
  // Level hardcoded for SHARE/LK
  'lookupURL': S3.Ap.concat('/gis/location.json?location.level=L3&location.parent=')
})
$.filterOptionsS3({
  'trigger': {'alias': 'need_line', 'name': 'coarse_location_id'},
  'target': {'alias': 'need_line', 'name': 'location_id'},
  'scope': 'row',
  'lookupPrefix': 'gis',
  'lookupResource': 'location',
  // Level hardcoded for SHARE/LK
  'lookupURL': S3.Ap.concat('/gis/location.json?location.level=L4&location.parent=')
})
