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
  'trigger': {'name': 'item_category_id'},
  'target': {'name': 'item_id'},
   'lookupPrefix': 'supply',
   'lookupResource': 'item',
   //'fncPrep': S3.supply.fncPrepItem,
   'fncRepresent': S3.supply.fncRepresentItemT
})
$.filterOptionsS3({
   'trigger': {'name': 'item_id'},
   'target': {'name': 'item_pack_id'},
   'lookupPrefix': 'supply',
   'lookupResource': 'item_pack',
   'msgNoRecords': i18n.no_packs
})