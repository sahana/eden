/**
 * Used by dataTables (views/dataTables.html)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

var oDataTable = new Array();
var fnInitDataTable;

var tableCnt = 1;
var tableId = new Array();
var myList = new Array();

function toggleDiv(divId) {
   $('#display' + divId).toggle();
   $('#full' + divId).toggle();
}

function hideSubRows(groupid){
    var sublevel = '.sublevel' + groupid.substr(6);
    $(sublevel).each(function (){
        obj = $(this);
        if (obj.hasClass('group') && obj.is(':visible')){
            // Get the group_xxx class
            var classList = obj.attr('class').split(/\s+/);
            var objGroupid = '';
            $.each( classList, function(index, item){
                if (item.substr(0, 6) == 'group_'){
                    objGroupid = item;
                }
            });
            hideSubRows(objGroupid);
        }
    });
    $(sublevel).hide();
    // Close all the arrows
    $('.arrow_e' + groupid).show();
    $('.arrow_s' + groupid).hide();
    // Remove any active row class
    $('.' + groupid).removeClass('activeRow');
}

function showSubRows(groupid){
    var sublevel = '.sublevel' + groupid.substr(6);
    $(sublevel).show();
    // Open the arrow
    $('.arrow_e' + groupid).hide();
    $('.arrow_s' + groupid).show();
    // Add the active row class
    $('.' + groupid).addClass('activeRow');
    // If this has opened groups then open the first row in the group
    var firstObj = $(sublevel + ':first')
    if (firstObj.hasClass('collapsable')){
        var classList = firstObj.attr('class').split(/\s+/);
        $.each( classList, function(index, groupLevel){
            if (groupLevel.substr(0, 6) == 'group_'){
                showSubRows(groupLevel);
            }
        });
    }
}

function toggleRow(groupid){
    var sublevel = '.sublevel' + groupid.substr(6);
    if ($(sublevel).is(':visible')){
        // Close all sublevels and change the icon to collapsed
        hideSubRows(groupid);
        $(sublevel).hide();
        $('#' + groupid + '_in').show();
        $('#' + groupid + '_out').hide();
    } else {
        // Open the immediate sublevel and change the icon to expanded
        $(sublevel).show();
        $('#' + groupid + '_in').hide();
        $('#' + groupid + '_out').show();
    }
}

/********************************************************************/
/* This function can be called by other scripts to attach the
/* accordion functionality to the row, not just the icon, as follows:
/*
/* $('.collapsable').click(function(){thisAccordionRow(0,this);});
/*
/********************************************************************/
function thisAccordionRow(t, obj){
    var level = '';
    var groupid = '';
    var classList = $(obj).attr('class').split(/\s+/);
    $.each( classList, function(index, rootClass){
        if (rootClass.substr(0, 6) == 'level_'){
            level = rootClass;
        }
        if (rootClass.substr(0, 6) == 'group_'){
            groupid = rootClass;
        }
    });
    accordionRow(t, level, groupid);
}

function accordionRow(t, level, groupid){
    /******************************************************************/
    /* Close all rows with a level higher than then level passed in   */
    /******************************************************************/
    // Get the level being opened
    var lvlOpened = level.substr(6);
    // Get a list of levels from the table
    var classList = $(tableId[t]).attr('class').split(/\s+/);
    $.each( classList, function(index, groupLevel){
        if (groupLevel.substr(0, 6) == 'level_'){
            var lvlNo = groupLevel.substr(6);
            if (lvlNo >= lvlOpened){
                // find all groups at this level which are active
                // and then close all opened rows
                var activeRow = $('.activeRow.' + groupLevel);
                $.each(activeRow , function(index, itemClass){
                    var classList2 = $(itemClass).attr('class').split(/\s+/);
                    $.each( classList2, function(index, rowClass){
                        if (rowClass.substr(0, 6) == 'group_'){
                            //var sublevel = 'sublevel' + item.substr(6);
                            hideSubRows(rowClass);
                        }
                    });
                }); // looping through each active row at the given level
            }
        }
    }); // close looping through the tables levels
    /******************************************************************/
    /* Open the items that are members of the clicked group           */
    /******************************************************************/
    showSubRows(groupid);
}

function tableIdReverse(id) {
    for (var t=0; t < tableCnt; t++) {
        if (tableId[t] == id) {
            return t;
        }
    }
    return -1;
}
$(document).ready(function() {
    /* dataTables handling */
    // Create an array for the column settings (this is required, otherwise the column widths don't autosize)
    var ColumnSettings = new Array();
    if (S3.dataTables.id) {
        tableCnt = S3.dataTables.id.length;
        for (var t=0; t < tableCnt; t++) {
            id = '#' + S3.dataTables.id[t];
            tableId[t] = id;
            myList[t] = $(id);
        }
    } else {
        id = '#list';
        tableId[0] = id;
        myList[0] = $(id);
    }

    // The configuration details for each table
    var aoTableConfig = new Array(); // Passed in from the server
    var sDom = new Array();
    var sPagination = new Array();
    var sPaginationType = new Array();
    var fnAjaxCallback = new Array();
    var fnActionCallBacks = new Array();
    var oGroupColumns = new Array();
    var aHiddenFieldsID = new Array();
    var selectedRows = new Array();
    var selectionMode = new Array();
    var cache = new Array();
    var textDisplay = new Array();

    for (var t=0; t < tableCnt; t++) {
        // First get the config details for each table
        var config_id = tableId[t] + '_configurations'
        if ($(config_id).length > 0) {
            aoTableConfig[t] = jQuery.parseJSON($(config_id).val());
        } else {
            // This table is not in the page (maybe empty)
            aoTableConfig[t] = null;
            continue;
        }
        sDom[t] = aoTableConfig[t]['sDom'];
        sPaginationType[t] = aoTableConfig[t]['paginationType'];

        fnActionCallBacks[t] = new Array();
        var ColumnCount = myList[t].find('thead tr').first().children().length;

        ColumnSettings[t] = new Array();
        // Buffer the array so that the default settings are preserved for the rest of the columns
        for (var c=0; c < ColumnCount; c++) {
            ColumnSettings[t][c] = null;
        }
        if (aoTableConfig[t]['rowActions'].length < 1) {
            if (S3.dataTables.Actions) {
                aoTableConfig[t]['rowActions'] = S3.dataTables.Actions;
            }
        }
        if (aoTableConfig[t]['rowActions'].length > 0) {
            ColumnSettings[t][aoTableConfig[t]['actionCol']] = {
                'sTitle': ' ',
                'bSortable': false
            }
        }
        if (aoTableConfig[t]['bulkActions']) {
            ColumnSettings[t][aoTableConfig[t]['bulkCol']] = {
                'sTitle': '<select id="bulk_select_options"><option></option><option id="modeSelectionAll">Select All</option><option id="modeSelectionNone">Deselect All</option></select>',
                'bSortable': false
            }
        }
        textDisplay[t] = [aoTableConfig[t]['textMaxLength'],
                          aoTableConfig[t]['textShrinkLength']
                          ];


        if ($(tableId[t] + '_dataTable_cache').length > 0) {
            cache[t] = jQuery.parseJSON($(tableId[t] + '_dataTable_cache').val());
        } else {
            cache[t] = { iCacheLower: -1 };
        }

        if (aoTableConfig[t]['group'].length > 0) {
            groupList = aoTableConfig[t]['group'];
            var gList = [];
            for (var gCnt=0; gCnt<groupList.length; gCnt++) {
                gList.push(groupList[gCnt][0]);
            }
            oGroupColumns[t] = {
                'bVisible': false,
                'aTargets': gList
            };
        } else {
            oGroupColumns[t] = {
                'bVisible': false,
                'aTargets': [ ]
            };
        }

        /* Code to calculate the bulk action buttons

           They will actually be placed on the dataTable inside the fnHeaderCallback
           It is necessary to do this inside of the callback because the dataTable().fnDraw
           that these buttons trigger will remove the on click binding. */
        if (aoTableConfig[t]['bulkActions']) {
            var bulk_submit = '';
            for (var i=0, iLen=aoTableConfig[t]['bulkActions'].length; i < iLen; i++) {
                bulk_submit += '<input type="submit" id="submitSelection"  name="' + aoTableConfig[t]['bulkActions'][i] + '" value="' + aoTableConfig[t]['bulkActions'][i] + '">&nbsp;';
            }
            var bulk_action_controls = '<span class="dataTable-action">' + bulk_submit + '<span>';
            // Add hidden fields to the form to record what has been selected
            bulkSelectionID = tableId[t] + '_dataTable_bulkSelection';
            selected =  jQuery.parseJSON($(bulkSelectionID).val())
            if (selected == null)
                selected = [];
            selectedRows[t] = selected;
            selectionMode[t] = 'Inclusive';
            if ($(tableId[t] + '_dataTable_bulkSelectAll').val()) {
                selectionMode[t] = 'Exclusive';
            }
            aHiddenFieldsID[t] = [tableId[t] + '_dataTable_bulkMode',
                                  tableId[t] + '_dataTable_bulkSelection'
                                  ];
        }

        // The call back used to manage the paganation
        if (aoTableConfig[t]['pagination'] == 'true') {
            // Cache the pages to reduce server-side calls
            var bServerSide = true;
            var bProcessing = true;
            var iDisplayLength = aoTableConfig[t]['displayLength'];
            var aoData = [{name: 'iDisplayLength', value: iDisplayLength},
                          {name: 'iDisplayStart', value: 0},
                          {name: 'sEcho', value: 1}]

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
                var table = '#' + this[0].id;
                var t = tableIdReverse(table);
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
                var oCache = cache[t];
                oCache.iDisplayStart = iRequestStart;
                // Prevent the Ajax lookup of the last page if we already know
                // that there are no more records than we have in the cache.
                if (oCache.hasOwnProperty('lastJson') &&
                    oCache.lastJson.hasOwnProperty('iTotalDisplayRecords')) {
                    if (oCache.lastJson.iTotalDisplayRecords < iRequestEnd) {
                        iRequestEnd = oCache.lastJson.iTotalDisplayRecords;
                    }
                }
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
            fnAjaxCallback[t] = fnDataTablesPipeline
            // end of pagination code
        } else {
            var bServerSide = false;
            var bProcessing = false;
            aoTableConfig[t]['ajaxUrl'] = null;
            function fnDataTablesPipeline ( url, data, callback ) {
                $.ajax( {
                    'url': url,
                    'data': data,
                    'success': callback,

                    'dataType': 'json',
                    'cache': false,
                    'error': function (xhr, error, thrown) {
                        if (error == 'parsererror') {
                            alert('DataTables warning: JSON data from server could not be parsed. ' +
                                  'This is caused by a JSON formatting error.');
                        }
                    }
                } );
            }
            fnAjaxCallback[t] = fnDataTablesPipeline;

        } // end of no pagination code
    } // end of loop for each dataTable

    /*********************************************************************/
    /* Helper functions                                                  */
    /*********************************************************************/
    function createSubmitBtn(t) {
        if (aoTableConfig[t]['bulkActions']) {
            // Make sure that the details of the selected records are stored in the hidden fields
            $(aHiddenFieldsID[t][0]).val(selectionMode[t]);
            $(aHiddenFieldsID[t][1]).val(selectedRows[t].join(','));
            // Add the bulk action controls to the dataTable
            $('.dataTable-action').remove();
            $(bulk_action_controls).insertBefore('#bulk_select_options');
        }
    }

    function inList(id, list) {
    /* The selected items for bulk actions is held in the list parameter
       This function finds if the given id is in the list. */
        for (var cnt=0, lLen=list.length; cnt < lLen; cnt++) {
            if (id == list[cnt]) {
                return cnt;
            }
        }
        return -1;
    }

    function bindButtons(t) {
    /* This will bind the row action and the bulk action buttons to their callback function */
        if (aoTableConfig[t]['rowActions'].length > 0) {
            for (var i=0; i < fnActionCallBacks[t].length; i++){
                var currentID = '#' + fnActionCallBacks[t][i][0];
                $(currentID).unbind('click');
                $(currentID).bind('click', fnActionCallBacks[t][i][1]);
            }
        }
        if (aoTableConfig[t]['bulkActions']) {
            $('.bulkcheckbox').unbind('change');
            $('.bulkcheckbox').change( function(event){
                id = this.id.substr(6)
                var posn = inList(id, selectedRows[t])
                if (posn == -1) {
                    selectedRows[t].push(id);
                    posn = 0 // force the row to be selected
                } else {
                    selectedRows[t].splice(posn, 1);
                    posn = -1 // force the row to be deselected
                }
                row = $(this).parent().parent()
                setSelectionClass(t, row, posn);
            });
        }

    }

    function setSelectionClass(t, row, index){
    /* This function is used to show which rows have been selected for a bulk select action */
        if (selectionMode[t] == 'Inclusive') {
            $('#totalSelected').text(selected.length);
            if (index == -1) {
                $(row).removeClass('row_selected');
                $(".bulkcheckbox", row).attr('checked', false);
            } else {
                $(row).addClass('row_selected');
                $(".bulkcheckbox", row).attr('checked', true);
            }
        }
        if (selectionMode[t] == 'Exclusive') {
            $('#totalSelected').text(parseInt($('#totalAvaliable').text()) - selected.length);
            if (index == -1) {
                $(row).addClass('row_selected');
                $('.bulkcheckbox', row).attr('checked', true);
            } else {
                $(row).removeClass('row_selected');
                $('.bulkcheckbox', row).attr('checked', false);
            }
        }
        createSubmitBtn(t);
    }

    function setModeSelectionAll(event) {
        wrapper = $(this).parents('.dataTables_wrapper')[0].id
        selector = '#' + wrapper.substr(0, wrapper.length - 8);
        t = tableIdReverse(selector);
        selectionMode[t] = 'Exclusive';
        selectedRows[t] = [];
        oDataTable[t].fnDraw(false);
    }

    function setModeSelectionNone(event) {
        wrapper = $(this).parents('.dataTables_wrapper')[0].id;
        selector = '#' + wrapper.substr(0, wrapper.length - 8);
        t = tableIdReverse(selector);
        selectionMode[t] = 'Inclusive';
        selectedRows[t] = [];
        oDataTable[t].fnDraw(false);
    }


    function buildGroups(oSettings, t, group, groupTotals, level) {
        var shrink = aoTableConfig[t]['shrinkGroupedRows'] == 'individual';
        var accordion = aoTableConfig[t]['shrinkGroupedRows'] == 'accordion';
        var nTrs = $(tableId[t] + ' tbody tr');
        var iColspan = $(tableId[t] + ' thead tr')[0].getElementsByTagName('th').length;
        var sLastGroup = '';
        var groupCnt = 0;
        var dataCnt = 0;
        var levelClass = 'level_' + level;
        var sublevel = '';
        $(tableId[t]).addClass(levelClass);
        for (var i=0; i<nTrs.length; i++) {
            if ($(nTrs[i]).hasClass('group')) {
                // Calculate the sublevel which can be used for the next new group
                var classList = $(nTrs[i]).attr('class').split(/\s+/);
                $.each( classList, function(index, item){
                    if (item.substr(0, 6) == 'group_'){
                        sublevel = 'sublevel' + item.substr(6);
                    }
                });
                sLastGroup = '';
                continue;
            }
            var sGroup = oSettings.aoData[ oSettings.aiDisplay[dataCnt] ]._aData[group];
            if ( sGroup != sLastGroup ) {  // New group
                // Add an indentation of the grouping depth
                var levelDisplay = '';
                for (var lvl=1; lvl<level; lvl++) {
                    levelDisplay += "<div style='float:left; width:10px;'>&nbsp;</div>";
                }
                if (level > 1) { levelDisplay += "<div class='ui-icon ui-icon-play' style='float:left;'></div>"; }
                // Add the subtotal counts (if provided)
                var groupCount = '';
                if (groupTotals[sGroup]) {
                    groupCount = ' (' + groupTotals[sGroup] + ')';
                }
                // Create the new HTML elements
                var nGroup = document.createElement( 'tr' );
                nGroup.className = 'group';
                var nCell = document.createElement( 'td' );
                if (shrink || accordion) {
                    groupCnt++;
                    var groupClass = 'group_' + t + level + groupCnt;
                    $(nGroup).addClass('headerRow');
                    $(nGroup).addClass(groupClass);
                    $(nGroup).addClass(levelClass);
                    if (sublevel){
                        $(nGroup).addClass(sublevel);
                        $(nGroup).addClass('collapsable');
                    }
                    if (shrink) {
                        var iconin = '<a id="' + groupClass + '_in" href="javascript:toggleRow(\'' + groupClass + '\');" class="ui-icon ui-icon-arrowthick-1-e" style="float:right"></a>';
                        var iconout = '<a id="' + groupClass + '_out" href="javascript:toggleRow(\'' + groupClass + '\');" class="ui-icon ui-icon-arrowthick-1-s" style="float:right; display:none"></a>';
                    } else {
                        var iconin = '<a href="javascript:accordionRow(\'' + t + '\', \'' + levelClass + '\', \'' + groupClass + '\');" class="ui-icon ui-icon-arrowthick-1-e arrow_e'+groupClass+'" style="float:right"></a>';
                        var iconout = '<a href="javascript:accordionRow(\'' + t + '\', \'' + levelClass + '\', \'' + groupClass + '\');" class="ui-icon ui-icon-arrowthick-1-s arrow_s'+groupClass+'" style="float:right; display:none"></a>';
                    }
                    htmlText = sGroup + groupCount+ iconin + iconout;
                } else {
                    htmlText = sGroup + groupCount;
                }
                nCell.colSpan = iColspan;
                nCell.innerHTML = levelDisplay + htmlText;
                nGroup.appendChild( nCell );
                nTrs[i].parentNode.insertBefore( nGroup, nTrs[i] );
                sLastGroup = sGroup;
            } // end of processing for a new group
            dataCnt += 1;
            if (shrink || accordion) {
                // Hide the detail row
                $(nTrs[i]).hide();
            }
        } // end of loop for each row
    }

    for (var tcnt=0; tcnt < tableCnt; tcnt++) {
      initDataTable(myList[tcnt], tcnt, false);
      // Delay in milliseconds to prevent too many AJAX calls
      if (null !== oDataTable[tcnt]) {
        oDataTable[tcnt].fnSetFilteringDelay(450);
      }
    } // end of loop through for each table

    function initDataTable(oTable, t, bReplace) {
        var config_id = tableId[t] + '_configurations'
        if ($(config_id).length > 0) {
            config = jQuery.parseJSON($(config_id).val());
        } else {
            oDataTable[t] = null;
            return;
        }
      aoTableConfig[t]["groupTotals"] = config["groupTotals"];
      oDataTable[t] = $(oTable).dataTable({
        'bDestroy': bReplace,
        'sDom': sDom[t],
        'sPaginationType': sPaginationType[t],
        'bServerSide': bServerSide,
        'bAutoWidth' : false,
        'bFilter': aoTableConfig[t]['bFilter'] == 'true',
        'bSort': true,
        'bDeferRender': true,
        'aaSorting': aoTableConfig[t]['aaSort'],
        "aaSortingFixed": aoTableConfig[t]['group'],
        "aoColumnDefs": [ oGroupColumns[t] ],
        'aoColumns': ColumnSettings[t],
        'iDisplayLength': aoTableConfig[t]['displayLength'],
        'aLengthMenu': [[ 25, 50, -1], [ 25, 50, S3.i18n.all]],
        'bProcessing': bProcessing,
        'sAjaxSource': aoTableConfig[t]['ajaxUrl'],
        'fnServerData': fnAjaxCallback[t],
        'fnHeaderCallback' : function (nHead, aasData, iStart, iEnd, aiDisplay) {
            $('#modeSelectionAll').on('click', setModeSelectionAll);
            $('#modeSelectionNone').on('click', setModeSelectionNone);
        },
        'fnRowCallback': function( nRow, aData, iDisplayIndex ) {
            // Extract the id # from the link
            t = tableIdReverse(this.selector);
            var actionCol = aoTableConfig[t]['actionCol'];
            var re = />(.*)</i;
            var result = re.exec(aData[actionCol]);
            if (result == null) {
                var id = aData[actionCol];
            } else {
                var id = result[1];
            }
            // Set the action buttons in the id column for each row
            if (aoTableConfig[t]['rowActions'].length > 0 || aoTableConfig[t]['bulkActions']) {
                var Buttons = '';
                if (aoTableConfig[t]['rowActions'].length > 0) {
                    var Actions = aoTableConfig[t]['rowActions'];
                    // Loop through each action to build the button
                    for (var i=0; i < Actions.length; i++) {

                        $('th:eq(0)').css( { 'width': 'auto' } );

                        // Check if action is restricted to a subset of records
                        if ('restrict' in Actions[i]) {
                            if (inList(id, Actions[i].restrict) == -1) {
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
                            fnActionCallBacks[t].push([id, S3ActionCallBack]);
                        }else {
                            if (Actions[i].icon) {
                                label = '<img src="'+Actions[i].icon+'" alt="'+label+'" title="'+label+'">';
                            }
                            var url = Actions[i].url.replace(re, id);
                            Buttons = Buttons + '<a class="'+ c + '" href="' + url + '">' + label + '</a>' + '&nbsp;';
                        }
                    }
                    // Put the actions buttons in the actionCol
                    if ((aoTableConfig[t]['group'].length > 0) && (aoTableConfig[t]['group'][0][0] < actionCol)){
                        actionCol -= 1;
                    }
                    $('td:eq(' + actionCol + ')', nRow).html( Buttons );
                }
                // Code to toggle the selection of the row
                if (aoTableConfig[t]['bulkActions']) {
                    setSelectionClass(t, nRow, inList(id, selectedRows[t]));
                }
                styles = aoTableConfig[t]['rowStyles'];
                for (style in styles) {
                    if (inList(id, styles[style]) > -1) {
                        $(nRow).addClass( style );
                    }
                }
                // Code to condense any text that is longer than the display limits
                tdposn = 0;
                gList = [];
                if (aoTableConfig[t]['group'].length > 0) {
                    groupList = aoTableConfig[t]['group'];
                    var gList = [];
                    for (var gCnt=0; gCnt < groupList.length; gCnt++) {
                        gList.push(groupList[gCnt][0]);
                    }
                }
                tdposn++; // increment the count of the td tags (don't do this for groups)
            }
            return nRow;
        }, // end of fnRowCallback
        'fnDrawCallback': function(oSettings) {
            table = '#' + oSettings.nTable.id;
            t = tableIdReverse(table);
            bindButtons(t);
            if ( oSettings.aiDisplay.length == 0 ) {
                return;
            }
            if (aoTableConfig[t]['group'].length > 0) {
                groupList = aoTableConfig[t]['group'];
                for (var gCnt=0; gCnt<groupList.length; gCnt++) {
                    group = groupList[gCnt];
                    groupTotals = [];
                    if (aoTableConfig[t]['groupTotals'].length > gCnt) {
                        groupTotals = aoTableConfig[t]['groupTotals'][gCnt];
                    }
                    buildGroups(oSettings, t, group[0], groupTotals, gCnt + 1);
                }
                return nRow;
            }}, // end of fnRowCallback
            'fnDrawCallback': function(oSettings) {
                table = '#' + oSettings.nTable.id;
                t = tableIdReverse(table);
                bindButtons(t);
                if ( oSettings.aiDisplay.length == 0 ) {
                    return;
                }
                if (aoTableConfig[t]['group'].length > 0) {
                    groupList = aoTableConfig[t]['group'];
                    for (var gCnt=0; gCnt < groupList.length; gCnt++) {
                        group = groupList[gCnt];
                        groupTotals = [];
                        if (aoTableConfig[t]['groupTotals'].length > gCnt) {
                            groupTotals = aoTableConfig[t]['groupTotals'][gCnt];
                        }
                        buildGroups(oSettings, t, group[0], groupTotals, gCnt + 1);
                    }
                    // Now loop through each row and add the subLevel controls for row collapsing
                    var shrink = aoTableConfig[t]['shrinkGroupedRows'] == 'individual';
                    var accordion = aoTableConfig[t]['shrinkGroupedRows'] == 'accordion';
                    if (shrink || accordion) {
                        var nTrs = $(tableId[t] + ' tbody tr');
                        var sublevel = '';
                        for (var i=0; i < nTrs.length; i++) {
                            obj = $(nTrs[i]);
                            // If the row is a headerRow get the level
                            if (obj.hasClass('headerRow')) {
                                var classList = obj.attr('class').split(/\s+/);
                                $.each( classList, function(index, item){
                                    if (item.substr(0, 6) == 'group_'){
                                        sublevel = 'sublevel' + item.substr(6);
                                    }
                                });
                            } else {
                                $(nTrs[i]).addClass(sublevel);
                                $(nTrs[i]).addClass('collapsable');
                            }
                        }
                        $('.collapsable').hide();
                        if (accordion) {
                            accordionRow(t, 'level_1', 'group_' + t + '11');
                        }
                   } // end of collapsable rows
                }
                if (Math.ceil((oSettings.fnRecordsDisplay()) / oSettings._iDisplayLength) > 1)  {
                    $(tableId[t] + '_paginate').css('display', 'block');
                } else {
                    $(tableId[t] + '_paginate').css('display', 'none');
                }
            }
        });
    } // end of initDataTable function

    // Allow dataTables to be initialised outside of this function.
    fnInitDataTable = initDataTable;

    if (S3.dataTables.Resize) {
        // Resize the Columns after hiding extra data
        $('.dataTable').dataTable().fnAdjustColumnSizing();
    }

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

function s3FormatRequest(representation, tableid, url) {
    t = tableIdReverse('#' + tableid);
    dt = oDataTable[t];
    oSetting = dt.dataTableSettings[t];
    if (oSetting) {
        argData = 'id=' + tableid;
        serverFilterArgs = $('#' + tableid + '_dataTable_filter');
        if (serverFilterArgs.val() != '') {
            argData += '&sFilter=' + serverFilterArgs.val();
        }
        argData += '&sSearch=' + oSetting.oPreviousSearch['sSearch'];
        sSort = Array();
        aaSort = ( oSetting.aaSortingFixed !== null ) ?
                 oSetting.aaSortingFixed.concat( oSetting.aaSorting ) :
                 oSetting.aaSorting.slice();
        argData += '&iSortingCols=' + aaSort.length;
        for ( i=0 ; i<aaSort.length ; i++ ){
                argData += '&iSortCol_' + i + '=' + aaSort[i][0];
                argData += '&sSortDir_' + i + '=' +aaSort[i][1];
        }
        url = url + '.' + representation + '?' + argData;
    } else {
        url =  url + '.' + representation;
    }
    window.location = url;
}

function s3_gis_search_layer_loadend(event) {
    // Search results have Loaded
    var layer = event.object;
    // Zoom to Bounds
    var bounds = layer.getDataExtent();
    if (bounds) {
        map.zoomToExtent(bounds);
    }
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
