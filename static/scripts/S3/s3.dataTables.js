/**
 * Used by dataTables (views/dataTables.html)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

/**
 * The startsWith string function is introduced in JS 1.8.6 -- it's not even
 * accepted in ECMAScript yet, so don't expect all browsers to have it.
 * Thx to http://www.moreofless.co.uk/javascript-string-startswith-endswith/
 * for showing how to add it to string if not present.
 */
if (typeof String.prototype.startsWith != 'function') {
    String.prototype.startsWith = function(str) {
        return this.substring(0, str.length) === str;
    };
}

var oDataTable = new Array();
var fnInitDataTable;

var tableCnt = 1;
var tableId = new Array();
var myList = new Array();

// Simple plugin to Ajax-refresh a datatable. This also allows to
// change the sAjaxSource URL for that table (e.g. in order to
// update URL filters). Use e.g. in a onclick-handler like:
//    dt = $('#<list_id>').dataTable();
//    dt.fnReloadAjax(<new URL>);
//
$.fn.dataTableExt.oApi.fnReloadAjax = function(oSettings, sNewSource) {
    if ( typeof sNewSource != 'undefined' && sNewSource != null ) {
        // sNewSource is a string containing the new Ajax-URL for
        // this instance, so override the previous setting
        oSettings.sAjaxSource = sNewSource;
    }
    // Show the "Processing..." box
    this.oApi._fnProcessingDisplay( oSettings, true );

    var that = this;
    // Call fnServerData with empty aoData to trigger the pipeline
    // script, clear the table cache and run the following callback
    oSettings.fnServerData( oSettings.sAjaxSource, [], function(json) {

        // Clear the table
        that.oApi._fnClearTable( oSettings );

        // Trigger the pipeline script again (this time without callback),
        // in  order to re-load the table data from the server:
        that.fnDraw();

        // Remove the "Processing..." box
        that.oApi._fnProcessingDisplay( oSettings, false );

    }, oSettings );
}

function toggleDiv(divId) {
   $('#display' + divId).toggle();
   $('#full' + divId).toggle();
}

function hideSubRows(groupid) {
    var sublevel = '.sublevel' + groupid.substr(6);
    $(sublevel).each(function (){
        obj = $(this);
        if (obj.hasClass('group') && obj.is(':visible')) {
            // Get the group_xxx class
            var objGroupid = getElementClass(obj, 'group_');
            hideSubRows(objGroupid);
        }
    });
    $(sublevel).hide();
    // Close all the arrows
    $('.arrow_e' + groupid).show();
    $('.arrow_s' + groupid).hide();
    $('.ui-icon-triangle-1-e').show();
    $('.ui-icon-triangle-1-s').hide();
    // Remove any active row class
    $('.' + groupid).removeClass('activeRow');
}

/* Function to return the class name of the tag from the class name prefix that is passed in. */
function getElementClass(tagObj, prefix) {
    // Calculate the sublevel which can be used for the next new group
    var pLen = prefix.length;
    var classList = tagObj.attr('class').split(/\s+/);
    var className = '';
    $.each(classList, function(index, item) {
        if (item.substr(0, pLen) == prefix) {
            className = item;
            return;
        }
    });
    return className;
}

function showSubRows(groupid) {
    var sublevel = '.sublevel' + groupid.substr(6);
    $(sublevel).show();
    // Open the arrow
    $('.arrow_e' + groupid).hide();
    $('.arrow_s' + groupid).show();
    $('#' + groupid + '_closed').hide();
    $('#' + groupid + '_open').show();
    // Add the active row class
    $('.' + groupid).addClass('activeRow');
    // Display the spacer of open groups
    $(sublevel + '.spacer').show();
    // If this has opened groups then open the first row in the group
    var firstObj = $(sublevel + ':first');
    if (firstObj.hasClass('spacer')) {
        firstObj = firstObj.next();
    }
    if (firstObj.hasClass('collapsable')) {
        var groupLevel = getElementClass(firstObj, 'group_');
        if (groupLevel) {
            showSubRows(groupLevel);
        }
    }
}

function toggleRow(groupid) {
    var sublevel = '.sublevel' + groupid.substr(6);
    if ($(sublevel).is(':visible')) {
        // Close all sublevels and change the icon to collapsed
        hideSubRows(groupid);
        $(sublevel).hide();
        $('#' + groupid + '_closed').show();
        $('#' + groupid + '_open').hide();
        $('#' + groupid + '_in').show();
        $('#' + groupid + '_out').hide();
    // Display the spacer of open groups
    $(sublevel + '.spacer').show();
    } else {
        // Open the immediate sublevel and change the icon to expanded
        $(sublevel).show();
        $('#' + groupid + '_closed').hide();
        $('#' + groupid + '_open').show();
        $('#' + groupid + '_in').hide();
        $('#' + groupid + '_out').show();
    }
}

/**
 * This function can be called by other scripts to attach the
 * accordion functionality to the row, not just the icon, as follows:
 *
 * $('.collapsable').click(function(){thisAccordionRow(0,this);});
 **/
function thisAccordionRow(t, obj) {
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

function accordionRow(t, level, groupid) {
    /* Close all rows with a level higher than then level passed in */
    // Get the level being opened
    var lvlOpened = level.substr(6);
    // Get a list of levels from the table
    var theTableObj = $(tableId[t]);
    var groupLevel = getElementClass(theTableObj, 'level_');
    // The table should have a list of all the level_# that it supports
    var classList = theTableObj.attr('class').split(/\s+/);
    var activeRow, rowClass;
    $.each(classList, function(index, groupLevel) {
        if (groupLevel.substr(0, 6) == 'level_') {
            var lvlNo = groupLevel.substr(6);
            if (lvlNo >= lvlOpened) {
                // find all groups at this level which are active
                // and then close all opened rows
                activeRow = $('.activeRow.' + groupLevel);
                $.each(activeRow, function(index, itemClass) {
                    rowClass = getElementClass($(itemClass), 'group_');
                    hideSubRows(rowClass);
                }); // looping through each active row at the given level
            }
        }
    }); // close looping through the tables levels
    /* Open the items that are members of the clicked group */
    showSubRows(groupid);
    // Display the spacer of open groups
    $('.spacer.alwaysOpen').show();
    var sublevel;
    $.each($('.activeRow') , function(index, itemClass) {
        rowClass = getElementClass($(itemClass), 'group_');
        sublevel = '.sublevel' + rowClass.substr(6);
        // Display the spacer of open groups
        $(sublevel + '.spacer').show();
    });

}

function tableIdReverse(id) {
    for (var t=0; t < tableCnt; t++) {
        if (tableId[t] == id) {
            return t;
        }
    }
    return -1;
}

/**
 * Determine if this data element's value is the default for its key, and
 * return false if so. Used to remove data elements that have default values,
 * to reduce size of the URL in Ajax calls. We'll call this from filter() so
 * want it to return true for non-default elements.
 * @param element is an object with fields name and value.
 * @param index, @param array are unused, but allow calling this from filter().
 **/
function isNonDefaultData(element, index, array) {
    var name = element.name;
    var value = element.value;
    if ((name == 'sSearch' && value === '') ||
        (name.startsWith('sSearch_') && value === '') ||
        (name.startsWith('bRegex_') && !value) ||
        (name.startsWith('bSearchable_') && value) ||
        (name.startsWith('bSortable_') && value)) {
        return false;
    }
    if (name.startsWith('mDataProp_')) {
        // Here, we're looking for elements of the form:
        // name: 'mDataProp_N', value: N
        // where N is an integer, and is the same in both places.
        var n = parseInt(name.substr('mDataProp_'.length), 10);
        if (!isNaN(n) && typeof value == 'number' && n == value) {
            return false;
        }
    }
    return true;
}

$(document).ready(function() {
	var t;  // scratch
    /* dataTables handling */
    // Create an array for the column settings (this is required, otherwise the column widths don't autosize)
    var ColumnSettings = new Array();
    if (S3.dataTables.id) {
        tableCnt = S3.dataTables.id.length;
        for (t=0; t < tableCnt; t++) {
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
    var totalRecords = new Array();

    var bServerSide;
    var bProcessing;

    for (t=0; t < tableCnt; t++) {
        // First get the config details for each table
        var config_id = tableId[t] + '_configurations';
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
            };
        }
        if (aoTableConfig[t]['bulkActions']) {
            ColumnSettings[t][aoTableConfig[t]['bulkCol']] = {
                // @ToDo: i18n
                'sTitle': '<select id="bulk_select_options"><option></option><option id="modeSelectionAll">Select All</option><option id="modeSelectionNone">Deselect All</option></select>',
                'bSortable': false
            };
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
            var groupList = aoTableConfig[t]['group'];
            var gList = [];
            for (var gCnt=0; gCnt < groupList.length; gCnt++) {
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
                var bulk_action = aoTableConfig[t]['bulkActions'][i], name, value, cls='';
                if (bulk_action instanceof Array) {
                    value = bulk_action[0];
                    name = bulk_action[1];
                    if (bulk_action.length == 3) {
                        cls = bulk_action[2];
                    }
                } else {
                    value = bulk_action;
                    name = value;
                }
                bulk_submit += '<input type="submit" id="submitSelection" class="' + cls + '" name="' + name + '" value="' + value + '">&nbsp;';
            }
            var bulk_action_controls = '<div class="dataTable-action">' + bulk_submit + '</div>';
            // Add hidden fields to the form to record what has been selected
            var bulkSelectionID = tableId[t] + '_dataTable_bulkSelection';
            // global
            selected = jQuery.parseJSON($(bulkSelectionID).val());
            if (selected === null)
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
        var fnDataTablesPipeline;
        if (aoTableConfig[t]['pagination'] == 'true') {
            // Cache the pages to reduce server-side calls
            bServerSide = true;
            bProcessing = true;
            var iDisplayLength = aoTableConfig[t]['displayLength'];
            var aoData = [{name: 'iDisplayLength', value: iDisplayLength},
                          {name: 'iDisplayStart', value: 0},
                          {name: 'sEcho', value: 1}];

            function fnSetKey( aoData, sKey, mValue ) {
                for (var i=0, iLen=aoData.length; i < iLen; i++) {
                    if ( aoData[i].name == sKey ) {
                        aoData[i].value = mValue;
                    }
                }
            }
            function fnGetKey(aoData, sKey) {
                for (var i=0, iLen=aoData.length; i < iLen; i++) {
                    if ( aoData[i].name == sKey ) {
                        return aoData[i].value;
                    }
                }
                return null;
            }
            fnDataTablesPipeline = function(sSource, aoData, fnCallback) {

                var bNeedServer = false;
                var table;
                if (this.hasOwnProperty('nTable')) {
                    // Called from fnReloadAjax
                    table = '#' + this.nTable.id;

                    // Clear cache to enforce reload
                    var t = tableIdReverse(table);
                    cache[t] = {
                            lastRequest: [],
                            iCacheLower: -1,
                            iCacheUpper: -1
                    };
                    fnCallback({}); // calls the inner function of fnReloadAjax

                    // Can just return here, because fnDraw inside fnCallback
                    // has already triggered the regular pipeline refresh
                    return;

                } else {
                    table = '#' + this[0].id;
                }

                var t = tableIdReverse(table);
                var iRequestLength = fnGetKey(aoData, 'iDisplayLength');
                var iPipe;
                // Adjust the pipe size depending on the page size
                if (iRequestLength == iDisplayLength) {
                    iPipe = 6;
                } else if (iRequestLength > 49 || iRequestLength == -1) {
                    iPipe = 2;
                } else {
                    // iRequestLength == 25;
                    iPipe = 4;
                }
                var sEcho = fnGetKey(aoData, 'sEcho');
                var iRequestStart = fnGetKey(aoData, 'iDisplayStart');
                var iRequestEnd = iRequestStart + iRequestLength;
                var oCache = cache[t];
                totalRecords[t] = fnGetKey(aoData, 'iTotalRecords');
                oCache.iDisplayStart = iRequestStart;
                if (oCache.hasOwnProperty('lastJson') &&
                    oCache.lastJson.hasOwnProperty('iTotalRecords')) {
                    totalRecords[t] = oCache.lastJson.iTotalRecords;
                }
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
                    if (!oCache.lastRequest.length) {
                        // no previous request => need server in any case
                        bNeedServer = true;
                    } else {
                        for (var i=0, iLen=aoData.length; i < iLen; i++) {
                            if ( aoData[i].name != 'iDisplayStart' && aoData[i].name != 'iDisplayLength' && aoData[i].name != 'sEcho' ) {
                                if ( aoData[i].value != oCache.lastRequest[i].value ) {
                                    bNeedServer = true;
                                    break;

                                }
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
                    var nonDefaultData = aoData.filter(isNonDefaultData);
                    $.getJSON(sSource, nonDefaultData, function (json) {
                        // Callback processing
                        oCache.lastJson = jQuery.extend(true, {}, json);
                        if ( oCache.iCacheLower != oCache.iDisplayStart ) {
                            json.aaData.splice( 0, oCache.iDisplayStart - oCache.iCacheLower );
                        }
                        if (oCache.iDisplayLength !== -1) {
                            json.aaData.splice( oCache.iDisplayLength, json.aaData.length );
                        }
                        fnCallback(json);
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
            };
            fnAjaxCallback[t] = fnDataTablesPipeline;
            // end of pagination code
        } else {
            bServerSide = false;
            bProcessing = false;
            aoTableConfig[t]['ajaxUrl'] = null;
            fnDataTablesPipeline = function( url, data, callback ) {
                var nonDefaultData = data.filter(isNonDefaultData);
                $.ajax( {
                    'url': url,
                    'data': nonDefaultData,
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
            };
            fnAjaxCallback[t] = fnDataTablesPipeline;

        } // end of no pagination code
    } // end of loop for each dataTable

    /* Helper functions */
    function createSubmitBtn(t) {
        if (aoTableConfig[t]['bulkActions']) {
            // Make sure that the details of the selected records are stored in the hidden fields
            $(aHiddenFieldsID[t][0]).val(selectionMode[t]);
            $(aHiddenFieldsID[t][1]).val(selectedRows[t].join(','));
            // Add the bulk action controls to the dataTable
            $('.dataTable-action').remove();
            $(bulk_action_controls).insertBefore('#bulk_select_options');
            togglePairActions(t);
        }
    }

    function togglePairActions(t) {
        var s = selectedRows[t].length;
        if (selectionMode[t] == 'Exclusive') {
            s = totalRecords[t] - s;
        }
        if (s == 2) {
            $(tableId[t] + ' .pair-action').removeClass('hide');
        } else {
            $(tableId[t] + ' .pair-action').addClass('hide');
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
                var id = this.id.substr(6);
                var posn = inList(id, selectedRows[t]);
                if (posn == -1) {
                    selectedRows[t].push(id);
                    posn = 0; // force the row to be selected
                } else {
                    selectedRows[t].splice(posn, 1);
                    posn = -1; // force the row to be deselected
                }
                var row = $(this).parent().parent();
                togglePairActions(t);
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
                $('.bulkcheckbox', row).attr('checked', false);
            } else {
                $(row).addClass('row_selected');
                $('.bulkcheckbox', row).attr('checked', true);
            }
        }
        if (selectionMode[t] == 'Exclusive') {
            $('#totalSelected').text(parseInt($('#totalAvailable').text(), 10) - selected.length);
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
        var wrapper = $(this).parents('.dataTables_wrapper')[0].id;
        var selector = '#' + wrapper.substr(0, wrapper.length - 8);
        var t = tableIdReverse(selector);
        selectionMode[t] = 'Exclusive';
        selectedRows[t] = [];
        oDataTable[t].fnDraw(false);
    }

    function setModeSelectionNone(event) {
        var wrapper = $(this).parents('.dataTables_wrapper')[0].id;
        var selector = '#' + wrapper.substr(0, wrapper.length - 8);
        var t = tableIdReverse(selector);
        selectionMode[t] = 'Inclusive';
        selectedRows[t] = [];
        oDataTable[t].fnDraw(false);
    }

    /* Helper function to add the new group row */
    function addNewGroup(t,
                         sGroup,
                         level,
                         sublevel,
                         iColspan,
                         groupTotals,
                         groupPrefix,
                         groupTitle,
                         addIcons,
                         iconGroupType,
                         insertSpace,
                         shrink,
                         accordion,
                         groupCnt,
                         row,
                         before
                         ) {
        var levelClass = 'level_' + level;
        var groupClass = 'group_' + t + level + groupCnt;
        // Add an indentation of the grouping depth
        var levelDisplay = '';
        for (var lvl=1; lvl < level; lvl++) {
            levelDisplay += "<div style='float:left; width:10px;'>&nbsp;</div>";
        }
        if (level > 1) {
            levelDisplay += '<div id="' + groupClass + '_closed" class="ui-icon ui-icon-triangle-1-e" style="float:left;"></div>';
            levelDisplay += '<div id="' + groupClass + '_open" class="ui-icon ui-icon-triangle-1-s" style="float:left; display:none;"></div>';
        }
        // Add the subtotal counts (if provided)
        var groupCount = '';
        if (groupTotals[sGroup] !== null) {
            groupCount = ' (' + groupTotals[sGroup] + ')';
        } else {
            var index = groupPrefix + sGroup;
            if (groupTotals[index] !== null) {
                groupCount = ' (' + groupTotals[index] + ')';
            }
        }
        // Create the new HTML elements
        var nGroup = document.createElement('tr');
        nGroup.className = 'group';
        var nCell = document.createElement('td');
        var htmlText;
        if (shrink || accordion) {
            $(nGroup).addClass('headerRow');
            $(nGroup).addClass(groupClass);
            $(nGroup).addClass(levelClass);
            if (sublevel) {
                $(nGroup).addClass(sublevel);
                $(nGroup).addClass('collapsable');
            }
        }
        if (addIcons) {
            $(nGroup).addClass('expandable');
            var iconClassOpen = '';
            var iconClassClose = '';
            var iconTextOpen = '';
            var iconTextClose = '';
            var iconin;
            var iconout;
            if (iconGroupType == 'text') {
                iconTextOpen = '→';
                iconTextClose = '↓';
            }
            if (shrink) {
                if (iconGroupType == 'icon') {
                    iconClassOpen = 'class="ui-icon ui-icon-arrowthick-1-e" ';
                    iconClassClose = 'class="ui-icon ui-icon-arrowthick-1-s" ';
                }
                iconin = '<a id="' + groupClass + '_in" href="javascript:toggleRow(\'' + groupClass + '\');" ' + iconClassOpen + ' style="float:right">' + iconTextOpen + '</a>';
                iconout = '<a id="' + groupClass + '_out" href="javascript:toggleRow(\'' + groupClass + '\');" ' + iconClassClose + ' style="float:right; display:none">' + iconTextClose + '</a>';
            } else {
                if (iconGroupType == 'icon') {
                    iconClassOpen = 'class="ui-icon ui-icon-arrowthick-1-e arrow_e' + groupClass + '" ';
                    iconClassClose = 'class="ui-icon ui-icon-arrowthick-1-s arrow_s' + groupClass + '" ';
                } else {
                    iconClassOpen = 'class="arrow_e' + groupClass + '" ';
                    iconClassClose = 'class="arrow_s' + groupClass + '" ';
                }
                iconin = '<a href="javascript:accordionRow(\'' + t + '\', \'' + levelClass + '\', \'' + groupClass + '\');" ' + iconClassOpen + ' style="float:right">' + iconTextOpen + '</a>';
                iconout = '<a href="javascript:accordionRow(\'' + t + '\', \'' + levelClass + '\', \'' + groupClass + '\');" ' + iconClassClose + ' style="float:right; display:none">' + iconTextClose + '</a>';
            }
            htmlText = groupTitle + groupCount+ iconin + iconout;
        } else {
            htmlText = groupTitle + groupCount;
        }
        nCell.colSpan = iColspan;
        nCell.innerHTML = levelDisplay + htmlText;
        nGroup.appendChild(nCell);
        if (before) {
            $(nGroup).insertBefore(row);
        } else {
            $(nGroup).insertAfter(row);
        }
        if (insertSpace) {
            var nSpace = document.createElement('tr');
            $(nSpace).addClass('spacer');
            if (sublevel){
                $(nSpace).addClass(sublevel);
                $(nSpace).addClass('collapsable');
            } else {
                $(nSpace).addClass('alwaysOpen');
            }
            nCell = document.createElement('td');
            nCell.colSpan = iColspan;
            nSpace.appendChild( nCell );
            $(nSpace).insertAfter(nGroup);
        }
    } // end of function addNewGroup

    /*********************************************************************
     * Function to group the data
     *
     * @param oSettings the dataTable settings
     * @param t the index of the table
     * @param group The index of the colum that will be grouped
     * @param groupTotals (optional) the totals to be used for each group
     * @param level the level of this group, starting at 1
     *********************************************************************/
    function buildGroups(oSettings, t, group, groupTotals, prefixID, groupTitles, level) {
        var shrink = aoTableConfig[t]['shrinkGroupedRows'] == 'individual';
        var accordion = aoTableConfig[t]['shrinkGroupedRows'] == 'accordion';
        var insertSpace = aoTableConfig[t]['groupSpacing'];
        var iconGroupTypeList = aoTableConfig[t]['groupIcon'];
        var iconGroupType;
        if (iconGroupTypeList.length >= level) {
            iconGroupType = iconGroupTypeList[level-1];
        } else {
            iconGroupType = 'icon';
        }
        var nTrs = $(tableId[t] + ' tbody tr');
        var iColspan = $(tableId[t] + ' thead tr')[0].getElementsByTagName('th').length;
        var sLastGroup = '';
        var groupPrefix = '';
        var groupCnt = 1;
        var groupTitleCnt = 0;
        var dataCnt = 0;
        var sublevel = '';
        var levelClass = 'level_' + level;
        var title;
        $(tableId[t]).addClass(levelClass);
        for (var i=0; i < nTrs.length; i++) {
            if ($(nTrs[i]).hasClass('spacer')) {
                continue;
            }
            if ($(nTrs[i]).hasClass('group')) {
                // Calculate the sublevel which can be used for the next new group
                var item = getElementClass($(nTrs[i]), 'group_');
                sublevel = 'sublevel' + item.substr(6);
                sLastGroup = '';
                groupPrefix = '';
                for (var gpCnt = 0; gpCnt < prefixID.length; gpCnt++) {
                    try {
                        groupPrefix += oSettings.aoData[ oSettings.aiDisplay[dataCnt] ]._aData[prefixID[gpCnt]] + "_";
                    } catch(err) {}
                }
                continue;
            }
            var sGroup = oSettings.aoData[ oSettings.aiDisplay[dataCnt] ]._aData[group];
            if (sGroup != sLastGroup) {  // New group
                while (groupTitles.length > groupTitleCnt && sGroup != groupTitles[groupTitleCnt][0]) {
                    title = groupTitles[groupTitleCnt][1];
                    addNewGroup(t, title, level, sublevel, iColspan, groupTotals, groupPrefix, title, false, iconGroupType, insertSpace, shrink, accordion, groupCnt, nTrs[i],true);
                    groupTitleCnt++;
                    groupCnt++;
                }
                if (groupTitles.length > groupTitleCnt){
                    title = groupTitles[groupTitleCnt][1];
                    addNewGroup(t, title, level, sublevel, iColspan, groupTotals, groupPrefix, title, true, iconGroupType, insertSpace, shrink, accordion, groupCnt, nTrs[i],true);
                    groupTitleCnt++;
                } else {
                    addNewGroup(t, sGroup, level, sublevel, iColspan, groupTotals, groupPrefix, sGroup, true, iconGroupType, insertSpace, shrink, accordion, groupCnt, nTrs[i],true);
                }
                groupCnt++;
                sLastGroup = sGroup;
            } // end of processing for a new group
            dataCnt += 1;
            if (shrink || accordion) {
                // Hide the detail row
                $(nTrs[i]).hide();
            }
        } // end of loop for each row
        // add any empty groups not yet added to at the end of the table
        while (groupTitles.length > groupTitleCnt) {
            title = groupTitles[groupTitleCnt][1];
            addNewGroup(t, title, level, sublevel, iColspan, groupTotals, groupPrefix, title, false, iconGroupType, insertSpace, shrink, accordion, groupCnt, nTrs[nTrs.length-1],false);
            groupTitleCnt++;
            groupCnt++;
        }
    }

    for (var tcnt=0; tcnt < tableCnt; tcnt++) {
      initDataTable(myList[tcnt], tcnt, false);
      // Delay in milliseconds to prevent too many AJAX calls
      if (null !== oDataTable[tcnt]) {
        oDataTable[tcnt].fnSetFilteringDelay(450);
      }
    } // end of loop through for each table

    function setSpecialSortRules(t) {
        var titles = aoTableConfig[t]['groupTitles'];
        var order = Array();
        var fname = 'group-title-' + t;
        var limit = titles[0].length;
        for (var cnt=0; cnt < limit; cnt++) {
            var title = titles[0][cnt][0];
            order[title] = cnt;
        }
        jQuery.fn.dataTableExt.oSort[fname + '-asc']  = function(x, y) {
            return ((order[x] < order[y]) ? -1 : ((order[x] > order[y]) ?  1 : 0));
        };
        jQuery.fn.dataTableExt.oSort[fname + '-desc']  = function(x, y) {
            return ((order[x] < order[y]) ? 1 : ((order[x] > order[y]) ?  -1 : 0));
        };
        ColumnSettings[t][aoTableConfig[t]['group'][0][0]] = {'sType': fname};
    }

    function initDataTable(oTable, t, bReplace) {
        var config_id = tableId[t] + '_configurations';
        if ($(config_id).length > 0) {
            var config = jQuery.parseJSON($(config_id).val());
        } else {
            oDataTable[t] = null;
            return;
        }
        aoTableConfig[t]['groupTitles'] = config['groupTitles'];
        if (config['groupTitles'].length > 0) {
            setSpecialSortRules(t);
        }
        aoTableConfig[t]['groupTotals'] = config['groupTotals'];
        aoTableConfig[t]['displayLength'] = config['displayLength'];
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
            'aLengthMenu': [[ 25, 50, -1], [ 25, 50, i18n.all]],
            'bProcessing': bProcessing,
            'sAjaxSource': aoTableConfig[t]['ajaxUrl'],
            'fnServerData': fnAjaxCallback[t],
            'fnHeaderCallback' : function (nHead, aasData, iStart, iEnd, aiDisplay) {
                $('#modeSelectionAll').on('click', setModeSelectionAll);
                $('#modeSelectionNone').on('click', setModeSelectionNone);
            },
            'fnRowCallback': function(nRow, aData, iDisplayIndex) {
                // Extract the id # from the link
                var t = tableIdReverse(this.selector);
                var actionCol = aoTableConfig[t]['actionCol'];
                var re = />(.*)</i;
                var result = re.exec(aData[actionCol]);
                var id;
                if (result === null) {
                    id = aData[actionCol];
                } else {
                    id = result[1];
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
                                if (typeof S3ActionCallBack != 'undefined') {
                                    fnActionCallBacks[t].push([id, S3ActionCallBack]);
                                }
                            } else {
                                if (Actions[i].icon) {
                                    label = '<img src="' + Actions[i].icon + '" alt="' + label + '" title="' + label + '">';
                                }
                                var url = Actions[i].url.replace(re, id);
                                Buttons = Buttons + '<a class="'+ c + '" href="' + url + '">' + label + '</a>' + '&nbsp;';
                            }
                        } // end of loop through for each row Action for this table
                    } // end of if there are to be Row Actions for this table
                    // Put the actions buttons in the actionCol
                    if ((aoTableConfig[t]['group'].length > 0) && (aoTableConfig[t]['group'][0][0] < actionCol)) {
                        actionCol -= 1;
                    }
                    $('td:eq(' + actionCol + ')', nRow).html( Buttons );
                } // end of processing for the action and bulk buttons

                // Code to toggle the selection of the row
                if (aoTableConfig[t]['bulkActions']) {
                    setSelectionClass(t, nRow, inList(id, selectedRows[t]));
                }
                // Code to add special CSS styles to a row
                var styles = aoTableConfig[t]['rowStyles'];
                for (style in styles) {
                    if (inList(id, styles[style]) > -1) {
                        $(nRow).addClass( style );
                    }
                }
                // Code to condense any text that is longer than the display limits
                var tdposn = 0;
                var gList = [];
                if (aoTableConfig[t]['group'].length > 0) {
                    var groupList = aoTableConfig[t]['group'];
                    for (var gCnt=0; gCnt < groupList.length; gCnt++) {
                        gList.push(groupList[gCnt][0]);
                    }
                }
                for (var j=0; j < aData.length; j++) {
                    // Ignore any columns used for groups
                    if ($.inArray(j, gList) != -1) { continue; }
                    // Ignore if the data starts with an html open tag
                    if (aData[j][0] == '<') {
                        tdposn++;
                        continue;
                    }
                    if (aData[j].length > textDisplay[t][0]) {
                        var uniqueid = '_' + t + iDisplayIndex + j;
                        var icon = '<a href="javascript:toggleDiv(\'' + uniqueid + '\');" class="ui-icon ui-icon-zoomin" style="float:right"></a>';
                        var display = '<div id="display' + uniqueid + '">' + icon + aData[j].substr(0,textDisplay[t][1]) + "&hellip;</div>";
                        icon = '<a href="javascript:toggleDiv(\'' + uniqueid + '\');" class="ui-icon ui-icon-zoomout" style="float:right"></a>';
                        display += '<div  style="display:none" id="full' + uniqueid + '">' + icon + aData[j] + "</div>";
                        $('td:eq(' + tdposn + ')', nRow).html( display );
                    }
                    tdposn++; // increment the count of the td tags (don't do this for groups)
                } // end of code to condense 'long text' in a cell
                return nRow;
            }, // end of fnRowCallback
            'fnDrawCallback': function(oSettings) {
                var table = '#' + oSettings.nTable.id;
                var t = tableIdReverse(table);
                bindButtons(t);
                if (oSettings.aiDisplay.length === 0) {
                    return;
                }
                if (aoTableConfig[t]['group'].length > 0) {
                    var groupList = aoTableConfig[t]['group'];
                    for (var gCnt=0; gCnt < groupList.length; gCnt++) {
                        // The prefixID is used to identify what will be added to the key for the
                        // groupTotals, typically it will be a comma separated list of the groups
                        prefixID = [];
                        for (var pixidCnt = 0; pixidCnt < gCnt; pixidCnt++) {
                            prefixID.push(groupList[pixidCnt][0]);
                        }
                        var group = groupList[gCnt];
                        var groupTotals = [];
                        if (aoTableConfig[t]['groupTotals'].length > gCnt) {
                            groupTotals = aoTableConfig[t]['groupTotals'][gCnt];
                        }
                        var groupTitles = [];
                        if (aoTableConfig[t]['groupTitles'].length > gCnt) {
                            groupTitles = aoTableConfig[t]['groupTitles'][gCnt];
                        }
                        buildGroups(oSettings,
                                    t,
                                    group[0],
                                    groupTotals,
                                    prefixID,
                                    groupTitles,
                                    gCnt + 1
                                    );
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
                                item = getElementClass(obj, 'group_');
                                sublevel = 'sublevel' + item.substr(6);
                            } else {
                                $(nTrs[i]).addClass(sublevel);
                                $(nTrs[i]).addClass('collapsable');
                            }
                        } // end of loop through each row adding controls to collapse & expand the grouped table
                        $('.collapsable').hide();
                        if (accordion) {
                            accordionRow(t, 'level_1', 'group_' + t + '11');
                        }
                        $('.expandable').click(function() {
                            thisAccordionRow(t, this);
                        });
                   } // end of collapsable rows
                }
                if (Math.ceil((oSettings.fnRecordsDisplay()) / oSettings._iDisplayLength) > 1)  {
                    $(tableId[t] + '_paginate').css('display', 'block');
                } else {
                    $(tableId[t] + '_paginate').css('display', 'none');
                }
            } // end of fnDrawCallback
        }); // end of call to $(oTable).datatable()
        // Does not handle horizontal overflow properly:
        //new FixedHeader(oDataTable[t]);
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

function s3AppendUrlQuery(url, extension, query) {
    var parts = url.split('?'), q = '';
    var newurl = parts[0] + '.' + extension;
    if (parts.length > 1) {
        if (query) {
            q = '&' + query;
        }
        return (newurl + '?' + parts[1] + q);
    } else {
        if (query) {
            q = '?' + query;
        }
        return (newurl + q);
    }
}

function s3FormatRequest(representation, tableid, url) {
    var t = tableIdReverse('#' + tableid);
    var dt = oDataTable[t];
    var oSetting = dt.dataTableSettings[t];
    if (oSetting) {
        var argData = 'id=' + tableid;
        var serverFilterArgs = $('#' + tableid + '_dataTable_filter');
        if (serverFilterArgs.val() !== '') {
            argData += '&sFilter=' + serverFilterArgs.val();
        }
        argData += '&sSearch=' + oSetting.oPreviousSearch['sSearch'];
        var aaSort = (oSetting.aaSortingFixed !== null) ?
                     oSetting.aaSortingFixed.concat(oSetting.aaSorting) :
                     oSetting.aaSorting.slice();
        argData += '&iSortingCols=' + aaSort.length;
        for (i=0 ; i < aaSort.length ; i++) {
            argData += '&iSortCol_' + i + '=' + aaSort[i][0];
            argData += '&sSortDir_' + i + '=' + aaSort[i][1];
        }
        url = s3AppendUrlQuery(url, representation, argData);
    } else {
        url = s3AppendUrlQuery(url, representation, '');
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
            $('div.x-tool-close').click(function(evt) {
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
        s3_search_mapButton.on('click', function(evt) {
            // prevent button submitting the form
            evt.preventDefault();
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

// END ========================================================================
