/**
 * Used by dataTables (views/dataTables.html)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

$(document).ready(function() {
    /* dataTables handling */
    // Create an array for the column settings (this is required, otherwise the column widths don't autosize)
    if (S3.dataTables.id) {
        var myList = document.getElementById(S3.dataTables.id);
    } else {
        var myList = document.getElementById('list');
    }
    if (myList != null) {
        var ColumnCount = myList.getElementsByTagName('th').length;
    } else {
        var ColumnCount = 0;
    }
    var ColumnSettings = new Array();
    if (S3.dataTables.Actions) {
        var actionCallBacks = new Array();
        var currentID;
        ColumnSettings[0] = { 'sTitle': ' ', 'bSortable': false  }
    } else {
        ColumnSettings[0] = null;
    }

    // Buffer the array so that the default settings are preserved for the rest of the columns
    for (var i=1; i < ColumnCount; i++) {
        ColumnSettings[i] = null;
    }

    if (S3.dataTables.iDisplayLength) {
        iDisplayLength = S3.dataTables.iDisplayLength;
    } else {
        iDisplayLength = 25;
    }

    if (S3.dataTables.no_pagination) {
        var bServerSide = false;
        var bProcessing = false;
        var sAjaxSource = null;
        function fnDataTablesPipeline ( url, data, callback ) {
            $.ajax( {
                "url": url,
                "data": data,
                "success": callback,
                "dataType": "json",
                "cache": false,
                "error": function (xhr, error, thrown) {
                    if ( error == "parsererror" ) {
                        alert( "DataTables warning: JSON data from server could not be parsed. "+
                            "This is caused by a JSON formatting error." );
                    }
                }
            } );
        }
    } else {
        // Cache the pages to reduce server-side calls
        var bServerSide = true;
        var bProcessing = true;
        var sAjaxSource = S3.dataTables.sAjaxSource;

        if (S3.dataTables.oCache) {
            var oCache = S3.dataTables.oCache;
        } else {
            var oCache = { iCacheLower: -1 };
        }
        var aoData = [{name: "iDisplayLength", value: iDisplayLength},
                      {name: "iDisplayStart", value: 0},
                      {name: "sEcho", value: 1}]

        function fnSetKey( aoData, sKey, mValue ) {
            for (var i=0, iLen=aoData.length; i < iLen; i++) {
                if ( aoData[i].name == sKey ) {
                    aoData[i].value = mValue;
                }
            }
        }
        function fnGetKey( aoData, sKey ) {
            for (var i=0, iLen=aoData.length; i < iLen; i++) {
                if ( aoData[i].name == sKey ) {
                    return aoData[i].value;
                }
            }
            return null;
        }
        function fnDataTablesPipeline ( sSource, aoData, fnCallback ) {
            var iRequestLength = fnGetKey(aoData, 'iDisplayLength');
            // Adjust the pipe size depending on the page size
            if (iRequestLength == iDisplayLength) {
                var iPipe = 6;
            } else if (iRequestLength > 49 || iRequestLength == -1) {
                var iPipe = 2;
            } else {
                // iRequestLength == 25
                var iPipe = 4;
            }
            var bNeedServer = false;
            var sEcho = fnGetKey(aoData, 'sEcho');
            var iRequestStart = fnGetKey(aoData, 'iDisplayStart');
            var iRequestEnd = iRequestStart + iRequestLength;
            oCache.iDisplayStart = iRequestStart;
            // outside pipeline?
            if ( oCache.iCacheUpper !== -1 && /* If Display All oCache.iCacheUpper == -1 */
                 ( iRequestLength == -1 || oCache.iCacheLower < 0 || iRequestStart < oCache.iCacheLower || iRequestEnd > oCache.iCacheUpper )
                ) {
                bNeedServer = true;
            }

            // sorting etc changed?
            if ( oCache.lastRequest && !bNeedServer ) {
                for (var i=0, iLen=aoData.length; i < iLen; i++) {
                    if ( aoData[i].name != 'iDisplayStart' && aoData[i].name != 'iDisplayLength' && aoData[i].name != 'sEcho' ) {
                        if ( aoData[i].value != oCache.lastRequest[i].value ) {
                            bNeedServer = true;
                            break;
                        }
                    }
                }
            }
            // Store the request for checking next time around
            oCache.lastRequest = aoData.slice();
            if ( bNeedServer ) {
                if (iRequestStart < oCache.iCacheLower) {
                    iRequestStart = iRequestStart - (iRequestLength * (iPipe - 1));
                    if ( iRequestStart < 0 ) {
                        iRequestStart = 0;
                    }
                }
                oCache.iCacheLower = iRequestStart;
                oCache.iDisplayLength = fnGetKey( aoData, 'iDisplayLength' );
                if (iRequestLength == -1) {
                    oCache.iCacheUpper = -1; // flag for all records are in Cache
                    fnSetKey( aoData, 'iDisplayStart', "None" ); // No Filter
                    fnSetKey( aoData, 'iDisplayLength', "None" );  // No Filter
                } else {
                    oCache.iCacheUpper = iRequestStart + (iRequestLength * iPipe);
                    fnSetKey( aoData, 'iDisplayStart', iRequestStart );
                    fnSetKey( aoData, 'iDisplayLength', iRequestLength * iPipe );
                }
                $.getJSON(sSource, aoData, function (json) {
                    // Callback processing
                    oCache.lastJson = jQuery.extend(true, {}, json);
                    if ( oCache.iCacheLower != oCache.iDisplayStart ) {
                        json.aaData.splice( 0, oCache.iDisplayStart - oCache.iCacheLower );
                    }
                    if (oCache.iDisplayLength !== -1) {
                        json.aaData.splice( oCache.iDisplayLength, json.aaData.length );
                    }
                    fnCallback(json)
                } );
            } else {
                json = jQuery.extend(true, {}, oCache.lastJson);
                json.sEcho = sEcho; // Update the echo for each response
                if (iRequestLength !== -1) {
                    json.aaData.splice( 0, iRequestStart - oCache.iCacheLower );
                    json.aaData.splice( iRequestLength, json.aaData.length );
                }
                fnCallback(json);
            }
        }
    }

    if (undefined == S3.dataTables.bFilter) {
        var bFilter = true;
    } else {
        var bFilter = S3.dataTables.bFilter;
    }

    if (S3.dataTables.aaSorting) {
        var aaSorting = S3.dataTables.aaSorting;
    } else {
        var aaSorting = [ [1, 'asc'] ];
    }

    if (S3.dataTables.group) {
        var sortFixed = [[ S3.dataTables.group, 'asc' ]];
    } else {
        var sortFixed = null;
    }

    if (S3.dataTables.sDom) {
        var sDom = S3.dataTables.sDom;
    } else {
        var sDom = 'fril<"dataTable_table"t>pi';
    }

    if (S3.dataTables.sPaginationType) {
        var sPaginationType = S3.dataTables.sPaginationType;
    } else {
        var sPaginationType = 'full_numbers';
    }

    if (S3.dataTables.Selectable) {
        var selected = jQuery.parseJSON($('#importSelected').val())
        if (selected == null) {
        	selected = []
        }
        var selectionMode = 'Inclusive';
        if (S3.dataTables.SelectAll) {
        	var selectionMode = 'Exclusive';
        }
    }

    function fnGetSelected(oTableLocal) {
	    var aReturn = new Array();
	    var aTrs = oTableLocal.fnGetNodes();

	    for (var i=0; i<aTrs.length; i++) {
		    if ( $(aTrs[i]).hasClass('row_selected') ) {
			    aReturn.push( aTrs[i] );
		    }
	    }
	    return aReturn;
    }

    function posn_in_List(id, list) {
        for (var cnt=0, lLen=list.length; cnt < lLen; cnt++) {
            if (id == list[cnt]) {
                return cnt;
            }
        }
        return -1;
    }

    function setModeSelectionAll(event) {
        selectionMode = 'Exclusive';
        selected = [];
        $('.dataTable').dataTable().fnDraw(false);
    }

    function setModeSelectionNone(event) {
        selectionMode = 'Inclusive';
        selected = [];
        $('.dataTable').dataTable().fnDraw(false);
    }

    function setModeSelectionValid(event) {
        selectionMode = 'Exclusive';
        selected = [];
        if (S3.dataTables.Warning)
            $.each(S3.dataTables.Warning, function(index, value){selected.push(value);});
        $('.dataTable').dataTable().fnDraw(false);
    }

    function setSelectionClass(nRow, index){
        if (selectionMode == 'Inclusive') {
            $('#totalSelected').text(selected.length);
            if (index == -1) {
                $(nRow).removeClass('row_selected');
            } else {
                $(nRow).addClass('row_selected');
            }
        }
        if (selectionMode == 'Exclusive') {
            $('#totalSelected').text(parseInt($('#totalAvaliable').text()) - selected.length);
            if (index == -1) {
                $(nRow).addClass('row_selected');
            } else {
                $(nRow).removeClass('row_selected');
            }
        }
        createSubmitBtn();
    }

    function createSubmitBtn() {
        if (S3.dataTables.Selectable)
            $('.actionButton').remove();
        	if (S3.dataTables.id)
        		paginateBtns = '#' + S3.dataTables.id + '_paginate';
        	else
        		paginateBtns = '#list_paginate';
    		if (S3.dataTables.PostSubmitPosn == 'top')
    			place = "#series_summary_filter";
    		else
    			place = paginateBtns;
        	if (S3.dataTables.UsePostMethod){
        		$('#importMode').val(selectionMode)
        		$('#importSelected').val(selected.join(','))
        		$('<div class="actionButton"><input type="submit" class="action-btn" id="submitSelection" value="'+S3.dataTables.PostSubmitLabel+'"></div>').insertBefore(place);
        	} else {
	            URL = S3.dataTables.SelectURL
	            	+ 'mode='
	            	+ selectionMode
	            	+ '&selected='
	            	+ selected.join(',')
	            	+ '&post';
	            $('<div class="actionButton"><a class="action-btn" id="submitSelection" href='+URL+'>Submit</a></div>').insertBefore(place);
        }
    }

    function bindActionButton() {
        if (S3.dataTables.Actions) {
            for (var i=0; i < actionCallBacks.length; i++){
                var currentID = '#'+actionCallBacks[i][0];
                $(currentID).unbind('click');
                $(currentID).bind('click', actionCallBacks[i][1]);
            }
        }
    }

    $('.dataTable').dataTable({
        // @ToDo: Remember the pagination size without remembering the page number across tables as otherwise we can be misled to thinking we have no search results!
        //'bStateSave': true,
        'sDom': sDom,
        'sPaginationType': sPaginationType,
        // @ToDo: Skip this part outside of CRUD
        'bServerSide': bServerSide,
        'bFilter': bFilter,
        'bSort': true,
        'bDeferRender': true,
        'aaSorting': aaSorting,
        'aoColumns': ColumnSettings,
        'iDisplayLength': iDisplayLength,
        'aLengthMenu': [[ 25, 50, -1], [ 25, 50, S3.i18n.all]],
        'bProcessing': bProcessing,
        'sAjaxSource': sAjaxSource,
	    'fnServerData': fnDataTablesPipeline,
	    'fnHeaderCallback': function( nHead, aasData, iStart, iEnd, aiDisplay ) {
	    	var selectButtons = '<span class="dataTable-btn" id="modeSelectionNone">Deselect&nbsp;All</span>';
	    	selectButtons += '&nbsp;<span class="dataTable-btn" id="modeSelectionAll">Select&nbsp;All</span>';
	    	if (S3.dataTables.ShowAllValidButton){
	    		var selectButtons = '<span class="dataTable-btn" id="modeSelectionValid">Select&nbsp;Valid</span>&nbsp;' + selectButtons;
	    	}
            if (S3.dataTables.Selectable) {
                nHead.getElementsByTagName('th')[0].innerHTML = selectButtons;
            }
            $('#modeSelectionAll').bind('click', setModeSelectionAll);
            $('#modeSelectionNone').bind('click', setModeSelectionNone);
            $('#modeSelectionValid').bind('click', setModeSelectionValid);
            },
        'fnRowCallback': function( nRow, aData, iDisplayIndex ) {
            // Extract the id # from the link
            var re = />(.*)</i;
            var result = re.exec(aData[0]);
            if (result == null) {
                var id = aData[0];
            } else {
                var id = result[1];
            }
            // Code to toggle the selection of the row
            if (S3.dataTables.Selectable) {
            	$(nRow).unbind('click');
                $(nRow).click( function() {
		            if (posn_in_List(id, selected) == -1) {
		                selected.push(id);
		            } else {
		                selected.splice(posn_in_List(id, selected), 1);
		            }
		            setSelectionClass(nRow, posn_in_List(id, selected));
                });
                // Set the row_selected based on selected and selectionMode
                setSelectionClass(nRow, posn_in_List(id, selected));
            }
            // Set the action buttons in the id (first) column for each row
            if (S3.dataTables.Actions) {
                var Actions = S3.dataTables.Actions;
                var Buttons = '';
                // Loop through each action to build the button
                for (var i=0; i < Actions.length; i++) {
                    $('th:eq(0)').css( { 'width': 'auto' } );
                    // Check if action is restricted to a subset of records
                    if ('restrict' in Actions[i]) {
                        if (posn_in_List(id, Actions[i].restrict) == -1) {
                            continue;
                        }
                    }
                    var c = Actions[i]._class;
                    var label = S3.Utf8.decode(Actions[i].label);
                    re = /%5Bid%5D/g;
                    if (Actions[i]._onclick) {
                        var oc = Actions[i]._onclick.replace(re, id);
                        Buttons = Buttons + '<a class="' + c + '" onclick="' + oc + '">' + label + '</a>' + '&nbsp;';
                    } else if (Actions[i]._jqclick) {
                        Buttons = Buttons + '<span class="' + c + '" id="' + id + '">' + label + '</span>' + '&nbsp;';
                        actionCallBacks.push([id, S3ActionCallBack]);
                    }else {
                        var url = Actions[i].url.replace(re, id);
                        Buttons = Buttons + '<a class="'+ c + '" href="' + url + '">' + label + '</a>' + '&nbsp;';
                    }
                }
                // Set the first column to the action buttons
                $('td:eq(0)', nRow).html( Buttons );
            }
            if (S3.dataTables.Disabled) {
                if (posn_in_List(id, S3.dataTables.Disabled) > -1) {
                    $(nRow).addClass( 'dtdisable' );
                }
            }
            if (S3.dataTables.Warning) {
                if (posn_in_List(id, S3.dataTables.Warning) > -1) {
                    $(nRow).addClass( 'dtwarning' );
                }
            }
            if (S3.dataTables.Alert) {
                if (posn_in_List(id, S3.dataTables.Alert) > -1) {
                    $(nRow).addClass( 'dtalert' );
                }
            }
            if (S3.dataTables.Display) {
                var Display = S3.dataTables.Display;
                // Loop through each display to see which fields need to be checked
                for (var i=0; i < Display.length; i++) {
                    col = Display[i].col;
                    key = Display[i].key;
                    value = Display[i].display;
                    if ( aData[col] == key ) {
                        $('td:eq(' + col + ')', nRow).html( value );
                    }
                }
            }
            return nRow;
        }, // end of fnRowCallback
        "fnDrawCallback": function(oSettings) {
            bindActionButton()
            if ( oSettings.aiDisplay.length == 0 )
            {
                return;
            }
            if (S3.dataTables.group)
            {
	            var nTrs = $('.dataTable tbody tr');
	            var iColspan = nTrs[0].getElementsByTagName('td').length;
	            var sLastGroup = "";
	            for (var i=0; i<nTrs.length; i++)
	            {
	                var sGroup = oSettings.aoData[ oSettings.aiDisplay[i] ]._aData[S3.dataTables.group];
	                if ( sGroup != sLastGroup )
	                {
	                    var nGroup = document.createElement( 'tr' );
	                    var nCell = document.createElement( 'td' );
	                    nCell.colSpan = iColspan;
	                    nCell.className = "group";
	                    nCell.innerHTML = sGroup;
	                    nGroup.appendChild( nCell );
	                    nTrs[i].parentNode.insertBefore( nGroup, nTrs[i] );
	                    sLastGroup = sGroup;
	                }
	            }
            }
            if (Math.ceil((this.fnSettings().fnRecordsDisplay()) / this.fnSettings()._iDisplayLength) > 1)  {
                $('.dataTables_paginate').css("display", "block");
            } else {
                $('.dataTables_paginate').css("display", "none");
            }
        },
        "aaSortingFixed": sortFixed,
        "aoColumnDefs": [
                         { "bVisible": false, "aTargets": [ S3.dataTables.group ] }
                     ]
    });

	if (S3.dataTables.hideList) {
		for (var i=0; i<S3.dataTables.hideList.length; i++){
			$('.dataTable').dataTable().fnSetColumnVis(S3.dataTables.hideList[i], false);
		}
	}

    if (S3.dataTables.Resize) {
        // Resize the Columns after hiding extra data
        $('.dataTable').dataTable().fnAdjustColumnSizing();
    }

    // Delay in milliseconds to prevent too many AJAX calls
    $('.dataTable').dataTable().fnSetFilteringDelay(450);

    /* Messaging */
    /* Taken a different route for now, although this might come back to open form dynamically
       - change views/_search.html if-so
    $('#msg_datatables-btn').click( function(evt) {
        // @ToDo: Display the Compose form

        // @ToDo: Focus on form
        //$('#msg_log_message').focus();

        evt.preventDefault();
    }); */
});

function s3_gis_search_layer_loadend(event) {
    // Search results have Loaded
    var layer = event.object;
    // Zoom to Bounds
    var bounds = layer.getDataExtent();
    map.zoomToExtent(bounds);
    // Re-enable Clustering
    Ext.iterate(layer.strategies, function(key, val, obj) {
        if (key.CLASS_NAME == 'OpenLayers.Strategy.AttributeCluster') {
            layer.strategies[val].activate();
        }
    });
    // Disable this event
    layer.events.un({
        'loadend': s3_gis_search_layer_loadend
    });
}

Ext.onReady(function(){
    // Are there any map Buttons?
    var s3_dataTables_mapButton = Ext.get('gis_datatables_map-btn');
    if (s3_dataTables_mapButton) {
        s3_dataTables_mapButton.on('click', function() {
            // Load the search results layer
            Ext.iterate(map.layers, function(key, val, obj) {
                if (key.s3_layer_id == 'search_results') {
                    var layer = map.layers[val];
                    // Set a new event when the layer is loaded
                    layer.events.on({
                        'loadend': s3_gis_search_layer_loadend
                    });
                    // Disable Clustering to get correct bounds
                    Ext.iterate(layer.strategies, function(key, val, obj) {
                        if (key.CLASS_NAME == 'OpenLayers.Strategy.AttributeCluster') {
                            layer.strategies[val].deactivate();
                        }
                    });
                    layer.setVisibility(true);
                }
            });
            if (S3.gis.polygonButton) {
                // Disable the polygon control
                S3.gis.polygonButton.disable();
            }
            S3.gis.mapWin.show();
            // Disable the crosshair on the Map Selector
            $('.olMapViewport').removeClass('crosshair');
            // Set the Tab to show as active
            $('#gis_datatables_map-btn').parent().addClass('tab_here');
            // Deactivate the list Tab
            $('#gis_datatables_list_tab').parent().removeClass('tab_here').addClass('tab_other');
            // Set to revert if Map closed
            $('div.x-tool-close').click( function(evt) {
                // Set the Tab to show as inactive
                $('#gis_datatables_map-btn').parent().removeClass('tab_here').addClass('tab_other');
                // Activate the list Tab
                $('#gis_datatables_list_tab').parent().removeClass('tab_other').addClass('tab_here');
            });
            // @ToDo: Close Map Window & revert if Tab clicked
        });
    }
    var s3_search_mapButton = Ext.get('gis_search_map-btn');
    if (s3_search_mapButton) {
        s3_search_mapButton.on('click', function() {
            // Enable the polygon control
            S3.gis.polygonButton.enable();
            // @ToDo: Set appropriate Bounds
            // Default to current gis_config
            // If there is an Options widget for Lx, then see if that is set & use this
            S3.gis.mapWin.show();
            // Enable the crosshair on the Map Selector
            $('.olMapViewport').addClass('crosshair');
        });
    }
});
// =========================================================================
