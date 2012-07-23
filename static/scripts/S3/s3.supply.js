/**
    Supply Static JS Code

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2011-01-27
*/
// ============================================================================

// Filter Item Packs based on Inv Items and Items
function fncPrepItem(data){
	for (var i = 0; i < data.length; i++) {
		if (data[i].quantity == 1) {
			return data[i].name;
		}
	}
};
// ============================================================================
function fncRepresentItem(record, PrepResult) {
	if (record.quantity == 1) {
		return record.name 
	} else {
		return record.name + ' (' + record.quantity + ' x ' + PrepResult + ')'
	}
}
// ============================================================================
// Displays the number of items available in an inventory
function InvItemPackIDChange() {     
	// Cancel previous request
  	try {S3.JSONRequest[$(this).attr('id')].abort()} catch(err) {};

    $('#TotalQuantity').remove();   
    if ($('[name = "inv_item_id"]').length > 0) {
        id = $('[name = "inv_item_id"]').val()
    }
    else if  ($('[name = "send_inv_item_id"]').length > 0) {
        id = $('[name = "send_inv_item_id"]').val()
    }
//Following condition removed since it doesn't appear to be correct
//the ajax call is looking for the number of items in stock, but
//this is the supply catalogue id - not an id related to an inventory
//    else if  ($('[name = "item_id"]').length > 0) {
//        id = $('[name = "item_id"]').val()
//    }
    else
        return;

    var url = S3.Ap.concat('/inv/inv_item_quantity/' + id);
    if ($('#inv_quantity_ajax_throbber').length == 0 ) {
    	$('[name = "quantity"]').after('<div id="inv_quantity_ajax_throbber" class="ajax_throbber" style="float:right"/>'); 
    }
    
    // Save JSON Request by element id
    S3.JSONRequest[$(this).attr('id')] = $.getJSON(url, function(data) {
        // @ToDo: Error Checking
        var InvQuantity = data.inv_inv_item.quantity; 
        var InvPackQuantity = data.supply_item_pack.quantity; 
        
        var PackName = $('[name = "item_pack_id"] option:selected').text();
        var re = /\(([0-9]*)\sx/;
        var RegExpResult = re.exec(PackName);
        if (RegExpResult == null) {
        	var PackQuantity = 1
        } else {
        	var PackQuantity = RegExpResult[1]
        }
        
        var Quantity = (InvQuantity * InvPackQuantity) / PackQuantity;
                        
        TotalQuantity = '<span id = "TotalQuantity"> / ' + Quantity.toFixed(2) + ' ' + PackName + ' (' + S3.i18n.in_inv + ')</span>';
        $('#inv_quantity_ajax_throbber').remove();
        $('[name = "quantity"]').after(TotalQuantity);
    });
};
//============================================================================
//Displays the number of items available in an inventory
function InvRecvTypeChange() {
	var RecvType = $("#inv_recv_type").val()
	if (RecvType != undefined) {
		if ( RecvType == 11) { // @ToDo: pass this value instead of hardcoding it base on s3cfg.py 
			// Internal Shipment 
			$('[id^="inv_recv_from_site_id__row"]').show();
			$('[id^="inv_recv_organisation_id__row"]').hide();
		} else if ( RecvType >= 32) { // @ToDo: pass this value instead of hardcoding it base on s3cfg.py 
			// External Shipment 
			$('[id^="inv_recv_from_site_id__row"]').hide();
			$('[id^="inv_recv_organisation_id__row"]').show();
		} else { // @ToDo: pass this value instead of hardcoding it base on s3cfg.py 
			// External Shipment 
			$('[id^="inv_recv_from_site_id__row"]').hide();
			$('[id^="inv_recv_organisation_id__row"]').hide();
		}
		
	}
};
//=============================================================================
$(document).ready(function() {
    // ========================================================================
    $('#inv_track_item_item_pack_id').change(InvItemPackIDChange);
    InvRecvTypeChange();
    $('#inv_recv_type').change(InvRecvTypeChange);
    // ========================================================================
/**
    // Item ID Field
    // Assets don't use Packs, so skip
    if ($("#asset_asset_item_id").val() == undefined &
    	  "#supply_catalog_item_item_id").val() == undefined) {
        S3FilterFieldChange({
            'FilterField':	'item_id',
            'Field':		'item_pack_id',
            'FieldResource':'item_pack',
            'FieldPrefix':	'supply',
            'msgNoRecords':	S3.i18n.no_packs,
            'fncPrep':		fncPrepItem,
            'fncRepresent':	fncRepresentItem
        });
    }

    // Inv Item Field
    S3FilterFieldChange({
		'FilterField':	'inv_item_id',
		'Field':		'item_pack_id',
		'FieldResource':'item_pack',
		'FieldPrefix':	'supply',
	    'url':		 	S3.Ap.concat('/inv/inv_item_packs/'),
		'msgNoRecords':	S3.i18n.no_packs,
		'fncPrep':		fncPrepItem,
		'fncRepresent':	fncRepresentItem
	});
    
    // Req Item Field
    S3FilterFieldChange({
		'FilterField':	'req_item_id',
		'Field':		'item_pack_id',
		'FieldResource':'item_pack',
		'FieldPrefix':	'supply',
	    'url':		 	S3.Ap.concat('/req/req_item_packs/'),
		'msgNoRecords':	S3.i18n.no_packs,
		'fncPrep':		fncPrepItem,
		'fncRepresent':	fncRepresentItem
	});
*/
    // ========================================================================
    /**
     * Function to show the transactions related to request commit, transit &
     * fulfil quantities
     */
	$('.quantity.ajax_more').live( 'click', function (e) {		
		e.preventDefault();
		var DIV = $(this)
        var ShipmentType;
		var App;
		if (DIV.hasClass('collapsed')) {
			if (DIV.hasClass('fulfil')) {
				App = 'inv';
				ShipmentType = 'recv';
			} else if (DIV.hasClass('transit')) {
				ShipmentType = 'send';
				App = 'inv';
			} else if (DIV.hasClass('commit')) {
				ShipmentType = 'commit';
				App = 'req';
			}	
			DIV.after('<div class="ajax_throbber quantity_req_ajax_throbber"/>')
			   .removeClass('collapsed')
			   .addClass('expanded');
			
			// Get the req_item_id
			var UpdateURL = $('.action-btn', DIV.parent().parent().parent()).attr('href');
			var re = /req_item\/(\d*).*/i;
			var req_item_id = re.exec(UpdateURL)[1];
			var url = S3.Ap.concat('/', App, '/', ShipmentType, '_item_json/', req_item_id);	
			//var url = S3.Ap.concat('/', App, '/', ShipmentType, '_item.s3json?/', 
			//		   ShipmentType, '_item.req_item_id=', req_item_id);	
			$.ajax( { 
				url: url,
				dataType: 'json',
				context: DIV,
				success: function(data) {
					RecvTable = '<table class="recv_table">'	
					for (i=0; i<data.length; i++) {
						RecvTable += '<tr><td>';
						if (i==0) {
							//Header Row
							RecvTable += data[0].id
							
						} else {
							RecvURL = S3.Ap.concat('/', App, '/', ShipmentType, '/',  data[i].id, '/track_item');
							RecvTable += "<a href = '" + RecvURL + "'>"; 
							if (data[i].date != null) {
								RecvTable += data[i].date.substring(0, 10) + ' - '
								RecvTable += data[i].name + '</a>';
							} else {
								RecvTable +=  ' - </a>';
							}
							
						}
						RecvTable += '</td><td>' + data[i].quantity + '</td></tr>';
					}
					RecvTable += '</table>';
					$('.quantity_req_ajax_throbber', this.parent()).remove();
					this.parent().after(RecvTable);
				}
			});
		} else {			
			DIV.removeClass('expanded')
			   .addClass('collapsed');
			$('.recv_table', DIV.parent().parent() ).remove()
		}
			
	});
	// ========================================================================
	/**
     * ASSET APPLICATION JS
	 * @ToDo: - Populate Location based on site(?)
	 */
	// ------------------------------------------------------------------------
	/**
     * Code to switch between location & site widgets
	 * @ToDo: Find a better way to show/hide location widget
	 */
    /*
	$('[name="site_or_location"]').change(function() {
		if ($('#asset_log_site_or_location').length == 1) {
			$('[id^="asset_log_site_id__row"]').hide();
			// $('[id^="asset_log_location_id__row"]').hide();
			$('tr[id^="gis_location"]').hide();
			$('span[id^="gis_loc"]').hide();
			$('#gis_location_map-btn').hide();
			$('td.subheading').hide()
		}
		if ($('[name="site_or_location"]:checked').val() == '1') {
			// Enable Site Input
			$('[id^="asset_log_site_id__row"]').show();
			$('[id^="asset_log_room_id__row"]').show();
			$('tr[id^="gis_location"]').hide();
			$('span[id^="gis_loc"]').hide();
			$('#gis_location_map-btn').hide();
			$('td.subheading').hide();
		} else if ($('[name="site_or_location"]:checked').val() == '2'){
			// Enable Location Input
			$('[id^="asset_log_site_id__row"]').hide();
			$('[id^="asset_log_room_id__row"]').hide();
			// $('[id^="asset_log_location_id__row"]').hide();
			$('tr[id^="gis_location"]').show();
			$('span[id^="gis_loc"]').show();
			$('#gis_location_map-btn').show();
			$('td.subheading').show();
		}
	});
	$('[name="site_or_location"]').change();
	*/
	/* Populate Organisation based on Site  */
	/*
	$('#asset_log_site_id').change( function() {
		// Cancel previous request
		
		if ($('#asset_log_person_id').val() != '' || $('#asset_log_organisation_id').val() != '') {
			// Don't populate if the person & org are already set
		
			try {S3.JSONRequest[$(this).attr('id')].abort()} catch(err) {};
			
			var site_id = $('#asset_log_site_id').val()
			if (site_id != "") {
				$('#dummy_asset_log_organisation_id').after('<div id="organisation_ajax_throbber" class="ajax_throbber"/>')
													 .hide()
				var url = S3.Ap.concat('/org/site_org_json/', site_id);	
				
				// Save JSON Request by element id
				S3.JSONRequest[$(this).attr('id')] = $.ajax( { 
					url: url,
					dataType: 'json',
					success: function(data) {
						$('#organisation_ajax_throbber').remove();
						if (data.length > 0) {
							$('#dummy_asset_log_organisation_id').show()
																 .val(data[0].name)
																 .attr('disabled', 'disabled');
							$('#asset_log_organisation_id').val(data[0].id);
						} else {
							$('#dummy_asset_log_organisation_id').show()
																 .val('')
																 .removeAttr('disabled');
							$('#asset_log_organisation_id').val('');
						}
						
					}
				});
			} else {
				$('#dummy_asset_log_organisation_id').val('')
													 .removeAttr('disabled');
				$('#asset_log_organisation_id').val('');
			}
		}
	});
	*/
	/** Populate Site & Org Based on Person
	/* @ToDo: have this only select the correct site - and not disable the field
     */
	/*$('#asset_log_person_id').change( function() {
		// Cancel previous request
		try {S3.JSONRequest[$(this).attr('id')].abort()} catch(err) {};
		
		// Do NOT Populate Organisation based on Site
		$('#asset_log_site_id').change( function() {}); 
		
		var person_id = $('#asset_log_person_id').val()
		if (person_id != '') {
			$('#asset_log_site_id').after('<div id="site_ajax_throbber" class="ajax_throbber"/>')
								   .hide()
			$('#dummy_asset_log_organisation_id').after('<div id="organisation_ajax_throbber" class="ajax_throbber"/>')
												 .hide()
			var url = S3.Ap.concat('/hrm/staff_org_site_json/', person_id);	
			
			// Save JSON Request by element id
			S3.JSONRequest[$(this).attr('id')] = $.ajax( { 
				url: url,
				dataType: 'json',
				success: function(data) {
					$('#site_ajax_throbber').remove();
					$('#organisation_ajax_throbber').remove();
					if (data.length > 0) {
						$('#dummy_asset_log_organisation_id').show()
						 .val(data[0].name)
						 .attr('disabled', 'disabled');
						$('#asset_log_organisation_id').val(data[0].id);
						$('#asset_log_site_id').show()
											   .val(data[0].site_id)
											   .attr('disabled', 'disabled')
											   .change();
					} else {
						$('#dummy_asset_log_organisation_id').show()
						 .val('')
						 .removeAttr('disabled');
						$('#asset_log_organisation_id').val('');
						$('#asset_log_site_id').show()
											   .val('')
											   .removeAttr('disabled')
											   .change();
					}
					
				}
			});
		} else {
			$('#asset_log_site_id').show()
								   .val('')
								   .removeAttr('disabled')
								   .change();
			$('#asset_log_organisation_id').val('');
			$('#dummy_asset_log_organisation_id').val('')
												 .removeAttr('disabled');
		}
	});*/
});
// ============================================================================

