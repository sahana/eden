/**
 * Used by dataTables (views/dataTables.html)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 *
 * Global vars
 * - usage minimised
 *
 * Consumes:
 *
 * S3.dataTables                    Global object with dataTables details
 * S3.dataTables.id                 Array of CSS selectors
 * S3.dataTables.Actions            Array of row action button configurations
 *                                  (fallback-only for tables that have no rowActions in their JSON-config)
 *
 * S3.dataTables.initComplete       optional, custom callback for initComplete-event (applies for all tables)
 * S3.dataTables.Resize             optional, boolean to enforce column width adjustment (applies for all tables)
 *                                  (Resize not really working since called synchronously)
 *
 * S3.Utf8.decode                   Function provided by S3.js
 * S3.addModals                     Function provided by S3.js
 *
 * Provides:
 *
 * S3.dataTables.ajax_urls          Object with the current Ajax-URLs by table CSS selector
 * S3.dataTables.toggleRow          Function for grouped Rows
 * S3.dataTables.accordionRow       Function for grouped Rows
 * S3.dataTables.initDataTable      Function to initialize a datatable
 *
 * TODO: clean up multiple consecutive var-declarations, improve variable names
 * TODO: move to on/off instead of bind/unbind/delegate/undelegate
 */

// Done in views/dataTables.html & s3.vulnerability.js
//S3.dataTables = {};

// Module pattern to hide internal vars
(function($, undefined) {

    "use strict";

    // The configuration details for each table are currently stored as
    // common indexes of a number of global variables
    // TODO: Move to being properties of the table instances instead
    //       - similar to S3.gis.maps

    var bulk_action_controls,           // TODO what's this?

        aHiddenFieldsID = [],           // TODO what's this?
        ajax_urls = {},                 // TODO what's this? Lookup by id not index as easier for reloadAjax()

        aoTableConfig = [],             // Array of table configs from parsed JSON, per table index

        columns = [],                   // TODO what's this?

        fnAjax = [],                    // the pipeline function to Ajax-load table data (array per table),
                                        // passed to dataTable

        oDataTable = [],                // Array of data table instances,
                                        // not read by anything TODO remove?

        oGroupColumns = [],             // TODO what's this?
        selectedRows = [],              // TODO what's this?
        selectionMode = [],             // TODO what's this?
        table_ids = [],                 // TODO what's this?
        textDisplay = [],               // TODO what's this?
        totalRecords = [];              // TODO what's this?

    // Global scope for reloadAjax()
    // TODO no longer needed?
    S3.dataTables.ajax_urls = ajax_urls;

    /**
     * HELPER FUNCTION
     *
     * Array search function that allows implicit type coercion
     * (comparison with ==, unlike indexOf which uses ===)
     *
     * @param {mixed} item - the item to search for
     * @param {Array} arr - the array to search through
     *
     * @returns {integer} - the position of the item in the array,
     *                      or -1 if the item is not found
     */
    var inList = function(item, arr) {

        for (var i = 0, len = arr.length; i < len; i++) {
            if (item == arr[i]) {
                return i;
            }
        }
        return -1;
    };

    /**
     * HELPER FUNCTION
     *
     * TODO docstring, improve
     */
    var appendUrlQuery = function(url, extension, query) {

        var parts = url.split('?'),
            q = '';
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
    };

    /**
     * HELPER FUNCTION
     *
     * TODO docstring, improve
     */
    var updateURLQuery = function(target, source) {

        var tquery = target.split('?'),
            squery = source.split('?');

        var turlvars = tquery.length > 1 ? tquery[1].split('&') : [],
            surlvars = squery.length > 1 ? squery[1].split('&') : [],
            rurlvars = [],
            i, k, len, q;

        for (i=0, len=turlvars.length; i<len; i++) {
            q = turlvars[i].split('=');
            if (q.length > 1) {
                k = decodeURIComponent(q[0]);
                if (k.indexOf('.') == -1 && k[0] != '(' && k[0] != 'w') {
                    rurlvars.push(turlvars[i]);
                }
            }
        }
        for (i=0, len=surlvars.length; i<len; i++) {
            q = surlvars[i].split('=');
            if (q.length > 1) {
                k = decodeURIComponent(q[0]);
                if (k.indexOf('.') != -1 || k[0] == '(') {
                    rurlvars.push(surlvars[i]);
                }
            }
        }
        return rurlvars.length ? tquery[0] + '?' + rurlvars.join('&') : tquery[0];
    };

    /**
     * HELPER FUNCTION
     *
     * Lookup a table index from it's selector
     *
     * TODO docstring
     */
    var lookupTableIndex = function(selector) {

        var tableCnt = S3.dataTables.id.length;
        for (var tableIdx = 0; tableIdx < tableCnt; tableIdx++) {
            if (table_ids[tableIdx] == selector) {
                return tableIdx;
            }
        }
        return -1;
    };

    /**
     * GROUPED ROWS FUNCTION
     *
     * Return the class name of the tag from the class name prefix that is passed in
     * TODO docstring
     */
    var getElementClass = function(tagObj, prefix) {

        // Calculate the sublevel which can be used for the next new group
        var pLen = prefix.length,
            classList = tagObj.attr('class').split(/\s+/),
            className = '';
        $.each(classList, function(index, item) {
            if (item.substr(0, pLen) == prefix) {
                className = item;
                return; // TODO pointless return, should use for() + break here
            }
        });
        return className;
    };

    /**
     * GROUPED ROWS FUNCTION
     *
     * TODO docstring
     */
    var hideSubRows = function(groupid) {

        var sublevel = $('.sublevel' + groupid.substr(6));
        sublevel.each(function() {
            var obj = $(this);
            if (obj.hasClass('group') && obj.is(':visible')) {
                // Get the group_xxx class
                var objGroupid = getElementClass(obj, 'group_');
                hideSubRows(objGroupid);
            }
        });
        sublevel.hide();
        // Close all the arrows
        $('.arrow_e' + groupid).show();
        $('.arrow_s' + groupid).hide();
        $('.ui-icon-triangle-1-e').show();
        $('.ui-icon-triangle-1-s').hide();
        // Remove any active row class
        $('.' + groupid).removeClass('activeRow');
    };

    /**
     * GROUPED ROWS FUNCTION
     *
     * TODO docstring
     */
    var showSubRows = function(groupid) {

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
    };

    /**
     * GROUPED ROWS FUNCTION
     *
     * TODO docstring
     */
    var toggleRow = function(groupid) {

        var _sublevel = '.sublevel' + groupid.substr(6),
            sublevel = $(_sublevel),
            selector = '#' + groupid;

        if (sublevel.is(':visible')) {

            // Close all sublevels and change the icon to collapsed
            hideSubRows(groupid);
            sublevel.hide();
            $(selector + '_closed').show();
            $(selector + '_open').hide();
            $(selector + '_in').show();
            $(selector + '_out').hide();
            // Display the spacer of open groups
            $(_sublevel + '.spacer').show();

        } else {

            // Open the immediate sublevel and change the icon to expanded
            sublevel.show();
            $(selector + '_closed').hide();
            $(selector + '_open').show();
            $(selector + '_in').hide();
            $(selector + '_out').show();
        }
    };
    // Pass to global scope to be accessible as an href in HTML
    S3.dataTables.toggleRow = toggleRow;

    /**
     * GROUPED ROWS FUNCTION
     *
     * TODO docstring
     * This function can be called by other scripts to attach the
     * accordion functionality to the row, not just the icon, as follows:
     *
     * $('.collapsable').click(function(){thisAccordionRow(0,this);});
     **/
    var thisAccordionRow = function(tableIdx, obj) {

        var level = '',
            groupid = '',
            classList = $(obj).attr('class').split(/\s+/);

        $.each(classList, function(index, rootClass) {
            if (rootClass.substr(0, 6) == 'level_') {
                level = rootClass;
            }
            if (rootClass.substr(0, 6) == 'group_') {
                groupid = rootClass;
            }
        });

        accordionRow(tableIdx, level, groupid);
    };

    /**
     * GROUPED ROWS FUNCTION
     *
     * TODO docstring
     */
    var accordionRow = function(tableIdx, level, groupid) {

        // Close all rows with a level higher than then level passed in

        // Get the level being opened
        var lvlOpened = level.substr(6);

        // Get a list of levels from the table
        var theTableObj = $(table_ids[tableIdx]);

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

        // Open the items that are members of the clicked group
        showSubRows(groupid);

        // Display the spacer of open groups
        $('.spacer.alwaysOpen').show();

        var sublevel;
        $.each($('.activeRow'), function(index, itemClass) {
            rowClass = getElementClass($(itemClass), 'group_');
            sublevel = '.sublevel' + rowClass.substr(6);
            // Display the spacer of open groups
            $(sublevel + '.spacer').show();
        });
    };
    // Pass to global scope to be accessible as an href in HTML & for s3.vulnerability.js
    S3.dataTables.accordionRow = accordionRow;

    /**
     * GROUPED ROWS FUNCTION
     *
     * TODO docstring
     * Helper function to add the new group row
     */
    var insertGroupHeaderRow = function(tableIdx,
                                        groupTitle,
                                        level,
                                        sublevel,
                                        iColspan,
                                        groupTotals,
                                        groupPrefix,
                                        addIcons,
                                        iconGroupType,
                                        insertSpace,
                                        expandMode, // null, 'accordion', 'individual'
                                        groupCnt,
                                        row,
                                        before) {

        var nGroup = $('<tr class="group">'),
            levelClass = 'level_' + level,
            groupClass = 'group_' + tableIdx + level + groupCnt;

        // Create a TR
        var shrink = expandMode == 'individual',
            accordion = expandMode == 'accordion';

        if (shrink || accordion) {
            nGroup.addClass('headerRow')
                  .addClass(groupClass)
                  .addClass(levelClass);
            if (sublevel) {
                nGroup.addClass(sublevel)
                      .addClass('collapsable');
            }
        }

        // Create a TD and append it to the group
        var nCell = $('<td>').attr('colspan', iColspan).appendTo(nGroup);

        // Add an indentation of the grouping depth
        for (var lvl=1; lvl < level; lvl++) {
            // TODO: Move style to CSS
            $('<div>').css({float: 'left', width: '10px'}).html('&nbsp;').appendTo(nCell);
        }

        // Add open/closed icons
        if (level > 1) {
            // TODO Move style to CSS
            $('<div class="ui-icon ui-icon-triangle-1-e">').attr('id', groupClass + '_closed')
                                                           .css({float: 'left'})
                                                           .appendTo(nCell);

            $('<div class="ui-icon ui-icon-triangle-1-s">').attr('id', groupClass + '_open')
                                                           .css({float: 'left'})
                                                           .hide()
                                                           .appendTo(nCell);
        }

        // Add the subtotal counts (if provided)
        var groupCount = '';
        // Not !== as we want to catch undefined as well as null
        if (groupTotals[groupTitle] != null) {
            groupCount = ' (' + groupTotals[groupTitle] + ')';
        } else {
            var index = groupPrefix + groupTitle;
            if (groupTotals[index] != null) {
                groupCount = ' (' + groupTotals[index] + ')';
            }
        }

        // Construct the group header text
        nCell.append(groupTitle + groupCount);

        // Add open/close-icons (arrows on the right)
        if (addIcons) {
            nGroup.addClass('expandable');

            var iconClassOpen = '',
                iconClassClose = '';

            var iconTextOpen = '',
                iconTextClose = '';

            if (iconGroupType == 'text') {
                iconTextOpen = '→';
                iconTextClose = '↓';
            } else {
                iconTextOpen = '';
                iconTextClose = '';
            }

            if (shrink) {

                // TODO simplify
                if (iconGroupType == 'icon') {
                    iconClassOpen = 'ui-icon ui-icon-arrowthick-1-e';
                    iconClassClose = 'ui-icon ui-icon-arrowthick-1-s';
                }

                // TODO: Move style to CSS
                // TODO: Move script into event handler
                $('<a>').attr('id', groupClass + '_in')
                        .attr('href', "javascript:S3.dataTables.toggleRow(\'' + groupClass + '\');")
                        .addClass(iconClassOpen)
                        .css({float: 'right'})
                        .text(iconTextOpen)
                        .appendTo(nCell);

                $('<a>').attr('id', groupClass + '_out')
                        .attr('href', "javascript:S3.dataTables.toggleRow(\'' + groupClass + '\');")
                        .addClass(iconClassClose)
                        .css({float: 'right'})
                        .text(iconTextClose)
                        .hide()
                        .appendTo(nCell);

            } else if (accordion) {

                // TODO: simplify
                if (iconGroupType == 'icon') {
                    iconClassOpen = 'ui-icon ui-icon-arrowthick-1-e arrow_e' + groupClass;
                    iconClassClose = 'ui-icon ui-icon-arrowthick-1-s arrow_s' + groupClass;
                } else {
                    iconClassOpen = 'arrow_e' + groupClass;
                    iconClassClose = 'arrow_s' + groupClass;
                }

                // TODO: Move style to CSS
                // TODO: Move script into event handler
                $('<a>').addClass(iconClassOpen)
                        .attr('href', 'javascript:S3.dataTables.accordionRow(\'' + tableIdx + '\', \'' + levelClass + '\', \'' + groupClass + '\');')
                        .css({float: 'right'})
                        .text(iconTextOpen)
                        .appendTo(nCell);

                $('<a>').addClass(iconClassClose)
                        .attr('href', 'javascript:S3.dataTables.accordionRow(\'' + tableIdx + '\', \'' + levelClass + '\', \'' + groupClass + '\');')
                        .css({float: 'right'})
                        .text(iconTextClose)
                        .hide()
                        .appendTo(nCell);
            }
        }


        // Insert the entire TR before or after the passed-in row
        if (before) {
            nGroup.insertBefore(row);
        } else {
            nGroup.insertAfter(row);
        }

        // Insert spacer row before group header (except for first group)
        if (insertSpace && (level != 1 || groupCnt != 1 )) {

            var emptyCell = $('<td>').attr('colspan', iColspan),
                spacerRow = $('<tr class="spacer">').append(emptyCell);

            if (sublevel){
                spacerRow.addClass(sublevel).addClass('collapsable');
            } else {
                spacerRow.addClass('alwaysOpen');
            }
            spacerRow.insertBefore(nGroup);
        }
    }; // end of function insertGroupHeaderRow

    /**
     * GROUPED ROWS FUNCTION
     *
     * Group the rows in the current table (by inserting group headers)
     *
     * @param {object} oSettings - the dataTable settings
     * @param {string} selector - the selector of the table
     * @param {integer} tableIdx - the index of the table
     *
     * @param {integer} grpColIdx - the index of the colum that will be grouped
     * @param {Array} groupTotals - (optional) the totals to be used for each group
     *
     * @param {integer} level - the level of this group, starting at 1
     */
    var groupRows = function(oSettings,
                             selector,
                             tableIdx,

                             grpColIdx,               // index of the grouping column within all columns

                             groupTotals,
                             prefixID,            // array of grouping column indices including the current one TODO move down,
                                                  // used to generate a key for the groupTotals dict
                             groupTitles,         // Array of strings to use as titles for the group header
                             level                // the grouping depth
                             ) {

        // @ToDo: Pass table instance not index
        var tableConfig = aoTableConfig[tableIdx],

            insertSpace = tableConfig.groupSpacing,

            expandMode = tableConfig.shrinkGroupedRows,
            expandIcons = tableConfig.groupIcon;


        var expandIconType;
        if (expandIcons.length >= level) {
            expandIconType = expandIcons[level - 1];
        } else {
            expandIconType = 'icon';
        }

        var iColspan = oSettings.aoColumns.length;

        var prevGrpColVal = '';          // The value of the grouping column last used for a group

        var groupPrefix = '';         // TODO what's this? the access key for the groupTotals object
        var groupCnt = 1;             // The number of group headers added
        var groupTitleCnt = 0;        // The index of the next group title
        var dataCnt = 0;              // The current data row index (skipping spacers/headers)
        var sublevel = '';
        var title;

        // Add the level class to the <table> (TODO why?)
        $(selector).addClass('level_' + level);

        var tableRows = $(selector + ' tbody tr'); // rows (tr) in the tbody
        var rowData;
        var i, j;

        for (i=0; i < tableRows.length; i++) {

            var row = $(tableRows[i]);

            if (row.hasClass('spacer')) {
                // A spacer row that has been inserted at a higher level => skip
                continue;

            }

            // The column values in the next data row
            rowData = oSettings.aoData[oSettings.aiDisplay[dataCnt]]._aData;

            if (row.hasClass('group')) {
                // A group header row of a higher level

                // There is no previous row in this group, so there is no prevGrpColVal
                prevGrpColVal = '';

                // Determine the sublevel which can be used for the next new group
                var groupClass = getElementClass($(tableRows[i]), 'group_');
                sublevel = 'sublevel' + groupClass.substr(6);

                groupPrefix = '';
                // prefixID = list of grouping columns including the current one
                for (var j = 0; j < prefixID.length; j++) {
                    try {
                        groupPrefix += rowData[prefixID[j]] + '_';
                    } catch(err) {}
                }
                continue;
            }

            // A data row

            // grpColVal = the value in the grouping column of the current table row
            var grpColVal = rowData[grpColIdx];

            if (grpColVal != prevGrpColVal) {

                // Insert empty group header rows for all preceding empty groups
                // TODO DRY with the empty group renderer at the end
                while (groupTitles.length > groupTitleCnt && grpColVal != groupTitles[groupTitleCnt][0]) {
                    title = groupTitles[groupTitleCnt][1];
                    insertGroupHeaderRow(tableIdx,
                                         title,
                                         level,
                                         sublevel,
                                         iColspan,
                                         groupTotals,
                                         groupPrefix,
                                         false,
                                         expandIconType,
                                         insertSpace,
                                         expandMode,
                                         groupCnt,
                                         tableRows[i],
                                         true
                                         );
                    groupTitleCnt++;
                    groupCnt++;
                }

                // Start a new group
                if (groupTitles.length > groupTitleCnt){

                    // We shall use a custom group title
                    title = groupTitles[groupTitleCnt][1];
                    insertGroupHeaderRow(tableIdx,
                                         title,
                                         level,
                                         sublevel,
                                         iColspan,
                                         groupTotals,
                                         groupPrefix,
                                         true,
                                         expandIconType,
                                         insertSpace,
                                         expandMode,
                                         groupCnt,
                                         tableRows[i],
                                         true
                                         );
                    groupTitleCnt++;

                } else {

                    // We use the value of the grouping column as group title
                    insertGroupHeaderRow(tableIdx,
                                         grpColVal,
                                         level,
                                         sublevel,
                                         iColspan,
                                         groupTotals,
                                         groupPrefix,
                                         true,
                                         expandIconType,
                                         insertSpace,
                                         expandMode,
                                         groupCnt,
                                         tableRows[i],
                                         true
                                         );
                }
                groupCnt++;
                prevGrpColVal = grpColVal;

                // end of processing for a new group

            } else {

                // This row still belongs to the same group
            }

            dataCnt += 1; // increase data row index for next row

//             if (shrink || accordion) {
            if (expandMode) {
                // Hide the detail row
                row.hide();
            }

        } // end of loop for each row

        // Append empty group header rows for all remaining empty groups
        while (groupTitles.length > groupTitleCnt) {
            title = groupTitles[groupTitleCnt][1];
            insertGroupHeaderRow(tableIdx,                             // table index
                                 title,                         // grouping column value
                                 level,                         // grouping level
                                 sublevel,                      // sublevel TODO?
                                 iColspan,                      // Width of the table (columns)
                                 groupTotals,                   // Group totals
                                 groupPrefix,                   // Group prefix
                                 false,                         // addIcons
                                 expandIconType,                // expandIconType
                                 insertSpace,                   // insertSpace
                                 expandMode,                    // expandMode
                                 groupCnt,                      // groupCount
                                 tableRows[tableRows.length-1], // the next data row
                                 false                          // insert before
                                 );

            groupTitleCnt++;
            groupCnt++;
        }
    };

    /**
     * GROUPED ROWS FUNCTION
     *
     * TODO docstring
     */
    var setSpecialSortRules = function(tableIdx, tableConfig, tableColumns) {

        var titles = tableConfig.groupTitles;
        var order = [];
        var fname = 'group-title-' + tableIdx;
        var limit = titles[0].length;
        for (var cnt=0; cnt < limit; cnt++) {
            var title = titles[0][cnt][0];
            order[title] = cnt;
        }
        $.fn.dataTableExt.oSort[fname + '-asc']  = function(x, y) {
            return ((order[x] < order[y]) ? -1 : ((order[x] > order[y]) ?  1 : 0));
        };
        $.fn.dataTableExt.oSort[fname + '-desc']  = function(x, y) {
            return ((order[x] < order[y]) ? 1 : ((order[x] > order[y]) ?  -1 : 0));
        };
        tableColumns[tableConfig.group[0][0]] = {'sType': fname};
    };

    /**
     * BULK ACTIONS FUNCTION
     *
     * TODO docstring
     */
    var togglePairActions = function(tableIdx) {

        var s = selectedRows[tableIdx].length;

        if (selectionMode[tableIdx] == 'Exclusive') {
            s = totalRecords[tableIdx] - s;
        }
        if (s == 2) {
            $(table_ids[tableIdx] + ' .pair-action').removeClass('hide');
        } else {
            $(table_ids[tableIdx] + ' .pair-action').addClass('hide');
        }
    };

    /**
     * BULK ACTIONS FUNCTION
     *
     * TODO docstring
     * Show which rows have been selected for a bulk select action
     */
    var setSelectionClass = function(tableIdx, row, index) {

        var $totalAvailable = $('#totalAvailable'),
            $totalSelected = $('#totalSelected'),
            numSelected = selectedRows[tableIdx].length;

        if (selectionMode[tableIdx] == 'Inclusive') {

            // @ToDo: can 'selected' be pulled in from a parameter rather than module-scope?
            if ($totalSelected.length && $totalAvailable.length) {
                $('#totalSelected').text(numSelected);
            }
            if (index == -1) {
                // Row is not currently selected
                $(row).removeClass('row_selected');
                $('.bulkcheckbox', row).prop('checked', false);
            } else {
                // Row is currently selected
                $(row).addClass('row_selected');
                $('.bulkcheckbox', row).prop('checked', true);
            }
            if (numSelected == totalRecords[tableIdx]) {
                $('#modeSelectionAll').prop('checked', true);
                selectionMode[tableIdx] = 'Exclusive';
                selectedRows[tableIdx] = [];
            }

        } else {

            if ($totalSelected.length && $totalAvailable.length) {
                $('#totalSelected').text(parseInt($('#totalAvailable').text(), 10) - numSelected);
            }
            if (index == -1) {
                // Row is currently selected
                $(row).addClass('row_selected');
                $('.bulkcheckbox', row).prop('checked', true);
            } else {
                // Row is not currently selected
                $(row).removeClass('row_selected');
                $('.bulkcheckbox', row).prop('checked', false);
            }
            if (numSelected == totalRecords[tableIdx]) {
                $('#modeSelectionAll').prop('checked', false);
                selectionMode[tableIdx] = 'Inclusive';
                selectedRows[tableIdx] = [];
            }
        }

        if (aoTableConfig[tableIdx].bulkActions) {

            // Make sure that the details of the selected records
            // are stored in the hidden fields
            $(aHiddenFieldsID[tableIdx][0]).val(selectionMode[tableIdx]);
            $(aHiddenFieldsID[tableIdx][1]).val(selectedRows[tableIdx].join(','));

            // Add the bulk action controls to the dataTable
            $('.dataTable-action').remove();
            $(bulk_action_controls).insertBefore('#bulk_select_options');

            // Activate bulk actions?
            numSelected = selectedRows[tableIdx].length;
            var off = selectionMode[tableIdx] == 'Inclusive' ? 0 : totalRecords[tableIdx];
            $('.selected-action').prop('disabled', (numSelected == off));
            togglePairActions(tableIdx);
        }
    };

    /**
     * BULK ACTIONS FUNCTION
     *
     * TODO docstring
     * Bind the row action and the bulk action buttons to their callback function
     */
    var bindButtons = function(tableIdx, tableConfig, fnActionCallBacks) {

        if (tableConfig.rowActions.length > 0) {
            for (var i=0; i < fnActionCallBacks.length; i++){
                var currentID = '#' + fnActionCallBacks[i][0];
                $(currentID).unbind('click')
                            .bind('click', fnActionCallBacks[i][1]);
            }
        }

        if (tableConfig.bulkActions) {
            $('.bulkcheckbox').unbind('click.bulkSelect')
                              .on('click.bulkSelect', function() {

                var id = this.id.substr(6),
                    rows = selectedRows[tableIdx];

                var posn = inList(id, rows);
                if (posn == -1) {
                    rows.push(id);
                    posn = 0; // toggle selection class
                } else {
                    rows.splice(posn, 1);
                    posn = -1; // toggle selection class
                }

                var row = $(this).closest('tr');
                togglePairActions(tableIdx);
                setSelectionClass(tableIdx, row, posn);
            });
        }
    };

    /**
     * PIPELINE FUNCTION
     *
     * Pipelining function for DataTables. To be used for the `ajax` option of DataTables
     * original version from http://datatables.net/examples/server_side/pipeline.html
     * TODO docstring
     */
    var pipeline = function(opts) {
//     $.fn.dataTable.pipeline = function(opts) {

        // Configuration options
        var conf = $.extend( {
            cache: {},    // S3 Extension: Allow passing in initial cache
            pages: 2,     // number of pages to cache
            //url: '',    // script url
            data: null,   // function or object with parameters to send to the server
                          // matching how `ajax.data` works in DataTables
            method: 'GET' // Ajax HTTP method
        }, opts );

        // Private variables for storing the cache
        var cache = conf.cache,
            cacheLower;
        if (undefined !== cache.cacheLower) {
            cacheLower = cache.cacheLower;
        } else {
            cacheLower = -1;
        }
        var cacheUpper = cache.cacheUpper || null,
            cacheLastRequest = cache.cacheLastRequest || null,
            cacheLastJson = cache.cacheLastJson || null;

        return function(request, drawCallback, settings) {

            // S3 Extension
            if (this.hasOwnProperty('nTable')) {
                // We have been called by reloadAjax()

                var sAjaxSource = settings.sAjaxSource;
                if (sAjaxSource) {
                    // Update Ajax URL, and clear sAjaxSource to not
                    // override the ajax-setting for the actual reload:
                    ajax_urls[settings.nTable.id] = sAjaxSource;
                    settings.sAjaxSource = null;
                }

                // Clear cache to enforce reload
                cacheLastJson = null;
                cacheLastRequest = null;
                cacheLower = -1;
                cacheUpper = null;

                drawCallback({}); // calls the inner function of reloadAjax

                // Can just return here, because draw() inside drawCallback
                // has already triggered the regular pipeline refresh
                return;
            }

            var ajax          = false,
                requestStart  = request.start,
                drawStart     = request.start,
                requestLength = request.length;

            // S3 Extensions
            // Make the totalRecords visible to other functions
            var id = settings.nTable.id,
                selector = '#' + id,
                tableIdx = lookupTableIndex(selector);
            if (cacheLastJson && cacheLastJson.hasOwnProperty('recordsTotal')) {
                totalRecords[tableIdx] = cacheLastJson.recordsTotal;
            } else {
                totalRecords[tableIdx] = request.recordsTotal;
            }
            if (requestLength == -1) {
                // Showing all records
                var total = totalRecords[tableIdx];
                if (total !== undefined) {
                    requestLength = total;
                } else {
                    // Total number of records is unknown and hence not
                    // all records cached either => need server in any case
                    ajax = true;
                }
            }

            if (!ajax) {
                var requestEnd = requestStart + requestLength;

                // Prevent the Ajax lookup of the last page if we already know
                // that there are no more records than we have in the cache.
                if (cacheLastJson && cacheLastJson.hasOwnProperty('recordsFiltered')) {
                    if (cacheLastJson.recordsFiltered < requestEnd) {
                        requestEnd = cacheLastJson.recordsFiltered;
                    }
                }

                if (settings.clearCache) {
                    // API requested that the cache be cleared
                    ajax = true;
                    settings.clearCache = false;
                } else if (cacheLower < 0 || requestStart < cacheLower || requestEnd > cacheUpper) {
                    // outside cached data - need to make a request
                    ajax = true;
                } else if (cacheLastRequest &&
                        (JSON.stringify(request.order)   !== JSON.stringify(cacheLastRequest.order) ||
                         JSON.stringify(request.columns) !== JSON.stringify(cacheLastRequest.columns) ||
                         JSON.stringify(request.search)  !== JSON.stringify(cacheLastRequest.search))) {
                    // properties changed (ordering, columns, searching)
                    ajax = true;
                }
            }

            // Store the request for checking next time around
            cacheLastRequest = $.extend(true, {}, request);

            if (ajax) {
                // Need data from the server
                if (requestStart < cacheLower) {
                    requestStart = requestStart - (requestLength * (conf.pages - 1));

                    if (requestStart < 0) {
                        requestStart = 0;
                    }
                }

                cacheLower = requestStart;
                if (request.length != -1) {
                    cacheUpper = requestStart + (requestLength * conf.pages);
                } else {
                    cacheUpper = requestLength;
                }

                request.start = requestStart;
                request.length = requestLength * conf.pages;

                // Provide the same `data` options as DataTables.
                if ($.isFunction(conf.data)) {
                    // As a function it is executed with the data object as an arg
                    // for manipulation. If an object is returned, it is used as the
                    // data object to submit
                    var d = conf.data(request);
                    if (d) {
                        $.extend(request, d);
                    }
                }
                else if ($.isPlainObject(conf.data)) {
                    // As an object, the data given extends the default
                    $.extend(request, conf.data);
                }

                // Send a minimal URL query with old-style vars
                var limit;
                if (requestLength == -1) {
                    // Load all records
                    limit = 'none';
                } else {
                    limit = request.length;
                }
                var sendData = [{'name': 'draw',
                                 'value': request.draw
                                 },
                                {'name': 'limit',
                                 'value': limit
                                 }
                                ];
                if (requestStart != 0) {
                    sendData.push({'name': 'start',
                                   'value': requestStart
                                   });
                }
                if (request.search && request.search.value) {
                    sendData.push({'name': 'sSearch',
                                   'value': request.search.value
                                   });
                    sendData.push({'name': 'iColumns',
                                   'value': request.columns.length
                                   });
                }
                var order_len = request.order.length;
                if (order_len) {
                    // Number of sorting columns
                    sendData.push({'name': 'iSortingCols',
                                   'value': order_len
                                   });
                    var columnConfigs = columns[tableIdx],
                        columnConfig,
                        ordering,
                        i;
                    // Declare non-sortable columns (required by server to interpret
                    // column indices correctly)
                    for (i = 0; i < columnConfigs.length; i++) {
                        columnConfig = columnConfigs[i];
                        if (columnConfig && !columnConfig.bSortable) {
                            sendData.push({'name': 'bSortable_' + i,
                                           'value': 'false'
                                           });
                        }
                    }
                    // Declare sort-column indices and sorting directions
                    for (i = 0; i < order_len; i++) {
                        ordering = request.order[i];
                        sendData.push({'name': 'iSortCol_' + i,
                                       'value': ordering.column
                                       });
                        sendData.push({'name': 'sSortDir_' + i,
                                       'value': ordering.dir
                                       });
                    }
                }

                // Use $.searchS3 if filter framework is available,
                // otherwise (e.g. custom page without s3.filter.js)
                // fall back to $.ajaxS3
                var ajaxMethod = $.ajaxS3;
                if ($.searchS3 !== undefined) {
                    ajaxMethod = $.searchS3;
                }

                settings.jqXHR = ajaxMethod({
                    'type':     conf.method,
                    //'url':      conf.url,
                    'url':      ajax_urls[id], // Needs to be dynamic to be able to be altered by reloadAjax()
                    'data':     sendData,
                    'dataType': 'json',
                    'cache':    false,
                    'success':  function(json) {
                        cacheLastJson = $.extend(true, {}, json);

                        // Update cacheUpper with the actual number of records returned
                        cacheUpper = cacheLower + json.data.length;

                        if (cacheLower != drawStart) {
                            // Remove the records up to the start of the
                            // current page from JSON
                            json.data.splice(0, drawStart - cacheLower);
                        }
                        if (requestLength != -1) {
                            // Not showing all records: remove all records behind
                            // the end of the current page
                            json.data.splice(requestLength, json.data.length);
                        }

                        drawCallback(json);
                    }
                });
            } else {
                // Copy the JSON from cache
                var json = $.extend(true, {}, cacheLastJson);

                // Update the echo for each response
                json.draw = request.draw;

                // Remove the records up to the start of the current page
                json.data.splice(0, requestStart - cacheLower);

                if (requestLength != -1) {
                    // Not showing all records: remove all records behind
                    // the end of the current page
                    json.data.splice(requestLength, json.data.length);
                }
                drawCallback(json);
            }
        };
    };

    /**
     * PIPELINE FUNCTION
     *
     * Register an API method that will empty the pipelined data, forcing an Ajax
     * fetch on the next draw (i.e. `table.clearPipeline().draw()`)
     * TODO docstring
     */
    $.fn.dataTable.Api.register('clearPipeline()', function() {

        return this.iterator('table', function (settings) {
            settings.clearCache = true;
        });
    });

    /**
     * DATATABLE FUNCTION
     *
     * Initialise a dataTable
     * TODO docstring, cleanup, break up
     *
     * Parameters:
     * id - {String} Selector to locate this dataTable (e.g. '#dataTable')
     * tableIdx - {Integer} The index within all the global vars
     * destroy - {Boolean} Whether to remove any existing dataTable with the same selector before creating this one
     */
    var initDataTable = function(selector, tableIdx, destroy) {

        // Read the configuration details
        var config_id = $(selector + '_configurations'),
            tableConfig;
        if (config_id.length > 0) {
            tableConfig = $.parseJSON(config_id.val());
        } else {
            // No config can be read: abort
            oDataTable[tableIdx] = null;
            return;
        }

        var tableColumns = [];
        // Pass to global scope
        aoTableConfig[tableIdx] = tableConfig;
        columns[tableIdx] = tableColumns;

        if (tableConfig.groupTitles.length > 0) {
            setSpecialSortRules(tableIdx, tableConfig, tableColumns);
        }

        var fnActionCallBacks = [];

        // Buffer the array so that the default settings are preserved for the rest of the columns
        var columnCount = $(selector).find('thead tr').first().children().length;
        for (var c=0; c < columnCount; c++) {
            tableColumns[c] = null;
        }

        // Action Buttons
        var rowActionsJSON = false;
        if (tableConfig.rowActions.length < 1) {
            if (S3.dataTables.Actions) {
                tableConfig.rowActions = S3.dataTables.Actions;
            } else {
                tableConfig.rowActions = [];
            }
        } else {
            rowActionsJSON = true;
        }
        if (tableConfig.rowActions.length > 0) {
            tableColumns[tableConfig.actionCol] = {
                'sTitle': ' ',
                'bSortable': false
            };
        }
        if (tableConfig.bulkActions) {
            tableColumns[tableConfig.bulkCol] = {
                'sTitle': '<div id="bulk_select_options"><input id="modeSelectionAll" type="checkbox">' + i18n.selectAll + '</input></div>',
                'bSortable': false
            };
        }
        textDisplay[tableIdx] = [tableConfig.textMaxLength,
                                 tableConfig.textShrinkLength
                                 ];

        if (tableConfig.group.length > 0) {
            var groupList = tableConfig.group;
            var gList = [];
            for (var gCnt=0; gCnt < groupList.length; gCnt++) {
                gList.push(groupList[gCnt][0]);
            }
            oGroupColumns[tableIdx] = {
                'bVisible': false,
                'aTargets': gList
            };
        } else {
            oGroupColumns[tableIdx] = {
                'bVisible': false,
                'aTargets': [ ]
            };
        }

        /*
           Code to calculate the bulk action buttons

           They will actually be placed on the dataTable inside the headerCallback
           It is necessary to do this inside of the callback because the dataTable().fnDraw
           that these buttons trigger will remove the onClick binding.
        */
        if (tableConfig.bulkActions) {
            var bulk_submit = '';
            for (var i=0, iLen=tableConfig.bulkActions.length; i < iLen; i++) {
                var bulk_action = tableConfig.bulkActions[i],
                    name,
                    value,
                    cls = '';
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
                bulk_submit += '<input type="submit" id="' + name + '-selected-action" class="' + cls + ' selected-action" name="' + name + '" value="' + value + '">&nbsp;';
            }
            // Module-scope currently as read by setSelectionClass()
            bulk_action_controls = '<div class="dataTable-action">' + bulk_submit + '</div>';

            // Add hidden fields to the form to record what has been selected
            // Module-scope currently as read by setSelectionClass()
            var selected = $.parseJSON($(selector + '_dataTable_bulkSelection').val());
            if (selected === null) {
                selected = [];
            }
            selectedRows[tableIdx] = selected;
            selectionMode[tableIdx] = 'Inclusive';

            if ($(selector + '_dataTable_bulkSelectAll').val()) {
                selectionMode[tableIdx] = 'Exclusive';
            }
            aHiddenFieldsID[tableIdx] = [selector + '_dataTable_bulkMode',
                                         selector + '_dataTable_bulkSelection'
                                         ];
        }

        var serverSide = true,
            processing = true,
            pageLength = tableConfig.pageLength;
        if (tableConfig.pagination == 'true') {
            // TODO Why is this a string and not a boolean? (It's JSON anyway)
            // Server-side Pagination
            // Cache the pages to reduce server-side calls
            var cache;
            if ($(selector + '_dataTable_cache').length > 0) {
                cache = $.parseJSON($(selector + '_dataTable_cache').val());
            } else {
                cache = {};
            }
            // Store Ajax-URL and enable pipeline
            ajax_urls[selector.slice(1)] = tableConfig.ajaxUrl;
//             fnAjax[tableIdx] = $.fn.dataTable.pipeline({
            fnAjax[tableIdx] = pipeline({
                cache: cache
            });
        } else {
            // Client-side Pagination
            serverSide = false;
            processing = false;
            fnAjax[tableIdx] = null;
        }

        var dt;
        dt = $(selector).dataTable({
            'ajax': fnAjax[tableIdx], // formerly fnServerData
            'autoWidth': false, // formerly bAutoWidth
            'columnDefs': [oGroupColumns[tableIdx]], // formerly aoColumnDefs
            'columns': tableColumns, // formerly aoColumns
            'deferRender': true, // formerly bDeferRender
            'destroy': destroy, // formerly bDestroy
            'dom': tableConfig.dom, // formerly sDom
            'lengthMenu': tableConfig.lengthMenu, // formerly aLengthMenu
            'order': tableConfig.order, // formerly aaSorting
            'orderFixed': tableConfig.group, // formerly aaSortingFixed
            'ordering': true, // formerly bSort
            'pageLength': pageLength, // formerly iDisplayLength
            'pagingType': tableConfig.pagingType, // formerly sPaginationType
            'processing': processing, // formerly bProcessing
            //'responsive': $(selector).hasClass('responsive'), // redundant, responsive-class alone should be enough
            'searchDelay': 450,
            'searching': tableConfig.searching == 'true', // formerly bFilter TODO why is this a string and not a boolean?
            'serverSide': serverSide, // formerly bServerSide
            'search': {
                'smart': serverSide // workaround for dataTables bug: smart search crashing with empty search string
            },
            'language': { // formerly oLanguage
                'aria': { // formerly oAria
                    'sortAscending': ': ' + i18n.sortAscending,  // formerly sSortAscending
                    'sortDescending': ': ' + i18n.sortDescending // formerly sSortDescending
                },
                'paginate': { // formerly oPaginate
                    'first': i18n.first, // formerly sFirst
                    'last': i18n.last,   // formerly sLast
                    'next': i18n.next,   // formerly sNext
                    'previous': i18n.previous // formerly sPrevious
                },
                'emptyTable': i18n.emptyTable, // formerly sEmptyTable
                'info': i18n.info, // formerly sInfo
                'infoEmpty': i18n.infoEmpty, // formerly sInfoEmpty
                'infoFiltered': i18n.infoFiltered, // formerly sInfoFiltered
                'infoThousands': i18n.infoThousands, // formerly sInfoThousands
                'lengthMenu': i18n.lengthMenu, // formerly sLengthMenu
                'loadingRecords': i18n.loadingRecords + '...', // formerly sLoadingRecords
                'processing': i18n.processing + '...', // formerly sProcessing
                'search': i18n.search + ':', // formerly sSearch
                'zeroRecords': i18n.zeroRecords // formerly sZeroRecords
            },

            'headerCallback': function (/* nHead, aasData, iStart, iEnd, aiDisplay */) {

                $('#modeSelectionAll').unbind('click.selectAll')
                                      .on('click.selectAll', function() {

                    selectedRows[tableIdx] = [];
                    if ($(this).prop('checked')) {
                        selectionMode[tableIdx] = 'Exclusive';
                        dt.api().draw(false);
                    } else {
                        selectionMode[tableIdx] = 'Inclusive';
                        dt.api().draw(false);
                    }
                });
                $('.ui-icon-zoomin, .ui-icon-zoomout').unbind('click.dtToggleCell');
            },

            'rowCallback': function(nRow, aData /* , iDisplayIndex */) { // formerly fnRowCallback

                // Determine the record ID of the row
                var actionCol = tableConfig.actionCol,
                    re = />(.*)</i,
                    result = re.exec(aData[actionCol]),
                    action_id;

                if (result === null) {
                    action_id = aData[actionCol];
                } else {
                    action_id = result[1];
                }

                // Render the action buttons in the id column for each row
                if (tableConfig.rowActions.length || tableConfig.bulkActions) {

                    var Buttons = '';
                    if (tableConfig.rowActions.length) {
                        var Actions = tableConfig.rowActions,
                            action,
                            restrict,
                            exclude;

                        // Loop through each action to build the button
                        re = /%5Bid%5D/g;
                        for (var i=0; i < Actions.length; i++) {

                            action = Actions[i];
                            var c = action._class;

                            //$('th:eq(0)').css( { 'width': 'auto' } );

                            // Check if action is restricted to a subset of records
                            restrict = action.restrict;
                            if (restrict && restrict.constructor === Array && restrict.indexOf(action_id) == -1) {
                                continue;
                            }
                            exclude = action.exclude;
                            if (exclude && exclude.constructor === Array && exclude.indexOf(action_id) != -1) {
                                continue;
                            }

                            // Construct button label and on-hover title
                            var label = action.label;
                            if (!rowActionsJSON) {
                                label = S3.Utf8.decode(action.label);
                            }
                            var title = action._title || label;

                            // Display the button as icon or image?
                            if (action.icon) {
                                label = '<i class="' + action.icon + '" alt="' + label + '"> </i>';
                            } else if (action.img) {
                                label = '<img src="' + action.icon + '" alt="' + label + '"></img>';
                            }

                            // Disabled button?
                            var disabled;
                            if (action._disabled) {
                                disabled = ' disabled="disabled"';
                            } else {
                                disabled = '';
                            }

                            if (action._onclick) {
                                var oc = Actions[i]._onclick.replace(re, action_id);
                                Buttons = Buttons + '<a class="' + c + '" onclick="' + oc + disabled + '">' + label + '</a>' + '&nbsp;';
                            } else if (action._jqclick) {
                                Buttons = Buttons + '<span class="' + c + '" id="' + action_id + '">' + label + '</span>' + '&nbsp;';
                                if (S3ActionCallBack !== undefined) {
                                    fnActionCallBacks.push([action_id, S3ActionCallBack]);
                                }
                            } else if (action.url) {
                                var url = action.url.replace(re, action_id);
                                var target = action._target;
                                if (target) {
                                    target = ' target="' + target + '"';
                                } else {
                                    target = '';
                                }
                                Buttons = Buttons + '<a db_id="'+ action_id + '" class="' + c + '" href="' + url + '" title="' + title + '"' + target + disabled + '>' + label + '</a>' + '&nbsp;';
                            } else {
                                var ajaxURL = action._ajaxurl;
                                if (ajaxURL) {
                                    ajaxURL = ' data-url="' + ajaxURL + '"';
                                } else {
                                    ajaxURL = '';
                                }
                                Buttons = Buttons + '<a db_id="'+ action_id + '" class="' + c + '" title="' + title + '"' + ajaxURL + disabled + '>' + label + '</a>' + '&nbsp;';
                            }
                        } // end of loop through for each row Action for this table
                    } // end of if there are to be Row Actions for this table
                    // Put the actions buttons in the actionCol
                    if ((tableConfig.group.length > 0) && (tableConfig.group[0][0] < actionCol)) {
                        actionCol -= 1;
                    }
                    $('td:eq(' + actionCol + ')', nRow).addClass('actions').html(Buttons);
                } // end of processing for the action and bulk buttons

                // Code to toggle the selection of the row
                if (tableConfig.bulkActions) {
                    setSelectionClass(tableIdx, nRow, inList(action_id, selectedRows[tableIdx]));
                }

                // Code to add special CSS styles to a row
                var styles = tableConfig.rowStyles;
                if (styles.length) {
                    var row = $(nRow);
                    var style;
                    for (style in styles) {
                        if (inList(action_id, styles[style]) > -1) {
                            row.addClass(style);
                        }
                    }
                }

                // Code to condense any text that is longer than the display limits
                var tdposn = 0,
                    gList = [];

                if (tableConfig.group.length) {
                    var groupList = tableConfig.group;
                    for (var gCnt=0; gCnt < groupList.length; gCnt++) {
                        gList.push(groupList[gCnt][0]);
                    }
                }

                for (var j=0; j < aData.length; j++) {
                    // Ignore any columns used for groups
                    if ($.inArray(j, gList) != -1) {
                        continue;
                    }
                    // Ignore if the data contains HTML tags
                    if (aData[j].match(/<.*>/)) {
                        tdposn++;
                        continue;
                    }
                    if (aData[j].length > textDisplay[tableIdx][0]) {
                        var disp = '<div class="dt-truncate"><span class="ui-icon ui-icon-zoomin" style="float:right"></span>' + aData[j].substr(0, textDisplay[tableIdx][1]) + "&hellip;</div>";
                        var full = '<div  style="display:none" class="dt-truncate"><span class="ui-icon ui-icon-zoomout" style="float:right"></span>' + aData[j] + "</div>";
                        $('td:eq(' + tdposn + ')', nRow).html(disp+full);
                    }
                    // increment the count of the td tags (don't do this for groups)
                    tdposn++;
                } // end of code to condense 'long text' in a cell

                return nRow;

            }, // end of rowCallback

            'drawCallback': function(oSettings) { // formerly fnDrawCallback

                // Update permalink
                var ajaxSource = ajax_urls[selector.slice(1)];
                if (ajaxSource) {
                    $(selector).closest('.dt-wrapper').find('a.permalink').each(function() {
                        var $this = $(this);
                        var url = updateURLQuery($this.attr('href'), ajaxSource);
                        $this.attr('href', url);
                    });
                }

                // Bind click-handler for truncated cell contents
                $('.dt-truncate .ui-icon-zoomin, .dt-truncate .ui-icon-zoomout').bind('click.dtToggleCell', function() {
                    $(this).parent()
                           .toggle()
                           .siblings('.dt-truncate')
                           .toggle();
                    return false;
                });

                // BULK ACTIONS FUNCTION
                bindButtons(tableIdx, tableConfig, fnActionCallBacks);

                // Show/hide export options depending on whether there are data in the table
                if (oSettings.aiDisplay.length === 0) {
                    // Hide the export options (table is empty)
                    $(selector).closest('.dt-wrapper').find('.dt-export-options').hide();
                    return;
                } else {
                    // Show the export options (table has data)
                    $(selector).closest('.dt-wrapper').find('.dt-export-options').show();
                }

                // GROUPED ROWS FUNCTION
                if (tableConfig.group.length) {

                    var groupList = tableConfig.group; // an array [[groupingColumnIndex, 'asc'|'desc'], ...]

                    for (var gCnt=0; gCnt < groupList.length; gCnt++) {

                        // gCnt = the index of the current grouping

                        // The prefixID is used to identify what will be added to the key for the
                        // groupTotals, a comma separated list of grouping column indices
                        var prefixID = [];
                        for (var pixidCnt = 0; pixidCnt < gCnt; pixidCnt++) {
                            prefixID.push(groupList[pixidCnt][0]);
                        }
                        var group = groupList[gCnt],
                            groupTotals;
                        if (tableConfig.groupTotals.length > gCnt) {
                            groupTotals = tableConfig.groupTotals[gCnt];
                        } else {
                            groupTotals = []; // TODO wrong, must be {}
                        }

                        var groupTitles;
                        if (tableConfig.groupTitles.length > gCnt) {
                            groupTitles = tableConfig.groupTitles[gCnt];
                        } else {
                            groupTitles = [];
                        }

                        groupRows(oSettings,    // the dataTable settings
                                    selector,     // the selector if the table
                                    tableIdx,     // the index of the table
                                    group[0],     // the index of the grouping column
                                    groupTotals,  // the array of group totals
                                    prefixID,     // TODO undocumented
                                    groupTitles,  // TODO undocumented
                                    gCnt + 1      // level
                                    );
                    }
                    // Now loop through each row and add the subLevel controls for row collapsing
                    var shrink = tableConfig.shrinkGroupedRows == 'individual';
                    var accordion = tableConfig.shrinkGroupedRows == 'accordion';
                    if (shrink || accordion) {
                        var nTrs = $(selector + ' tbody tr');
                        var sublevel = '',
                            obj,
                            item;
                        for (var i=0; i < nTrs.length; i++) {
                            obj = $(nTrs[i]);
                            // If the row is a headerRow get the level
                            if (obj.hasClass('headerRow')) {
                                item = getElementClass(obj, 'group_');
                                sublevel = 'sublevel' + item.substr(6);
                            } else {
                                $(nTrs[i]).addClass(sublevel)
                                          .addClass('collapsable');
                            }
                        } // end of loop through each row adding controls to collapse & expand the grouped table
                        $('.collapsable').hide();
                        if (accordion) {
                            accordionRow(tableIdx, 'level_1', 'group_' + tableIdx + '11');
                        }
                        $('.expandable').click(function() {
                            thisAccordionRow(tableIdx, this);
                        });
                   } // end of collapsable rows
                }

                // Hide/show pagination controls depending on number of pages
                if (Math.ceil((oSettings.fnRecordsDisplay()) / oSettings._iDisplayLength) > 1)  {
                    $(selector + '_paginate').css('display', 'block');
                } else {
                    // Single page, so hide them
                    $(selector + '_paginate').css('display', 'none');
                }

                // Add modals if necessary
                // - in future maybe use S3.redraw() to catach all elements
                if ($(selector).find('.s3_modal').length) {
                    S3.addModals();
                }

                // Do we have any records? => toggle empty section
                // TODO: this may be outdated => remove?
                var numrows = oSettings.fnRecordsDisplay();
                if (numrows > 0) {
                    $(selector).closest('.dt-contents')
                               .find('.empty')
                               .hide()
                               .siblings('.dt-wrapper')
                               .show();
                } else {
                    $(selector).closest('.dt-contents')
                               .find('.empty')
                               .show()
                               .siblings('.dtwrapper')
                               .hide();
                }

            }, // end of drawCallback

            // Custom initComplete can be used to reposition elements like export_formats
            'initComplete': S3.dataTables.initComplete

        }); // end of call to $(selector).datatable()

        // Ajax-delete handler
        dt.delegate('.dt-ajax-delete', 'click.datatable', function(e) {

            e.stopPropagation();
            if (confirm(i18n.delete_confirmation)) {
                var $this = $(this),
                    db_id = $this.attr('db_id'),
                    ajaxURL = $this.data('url'),
                    data = {},
                    formKey = dt.closest('.dt-wrapper').find('input[name="_formkey"]').first().val();
                if (formKey !== undefined) {
                    data._formkey = formKey;
                }
                if (ajaxURL && db_id) {
                    ajaxURL = ajaxURL.replace(/%5Bid%5D/g, db_id);
                }
                $.ajaxS3({
                    'url': ajaxURL,
                    'type': 'POST',
                    'dataType': 'json',
                    'data': data,
                    'success': function(/* data */) {
                        dt.fnReloadAjax();
                    }
                });
            } else {
                event.preventDefault();
                return false;
            }
        });

        // Export formats click-handler
        dt.closest('.dt-wrapper').find('.dt-export')
                                 .off('click.datatable')
                                 .on('click.datatable', function() {

            var tableid = dt.attr('id');

            var oSetting = dt.dataTableSettings[tableIdx],
                url = $(this).data('url'),
                extension = $(this).data('extension');

            if (oSetting) {
                var args = 'id=' + tableid,
                    serverFilterArgs = $('#' + tableid + '_dataTable_filter'),
                    sFilter = serverFilterArgs.val();
                if (sFilter !== undefined && sFilter !== '') {
                    args += '&sFilter=' + sFilter;
                }
                args += '&sSearch=' + oSetting.oPreviousSearch.sSearch;
                columns = oSetting.aoColumns;
                var i, len;
                for (i=0, len=columns.length; i < len; i++) {
                    if (!columns[i].bSortable) {
                        args += '&bSortable_' + i + '=false';
                    }
                }
                var aaSort = oSetting.aaSortingFixed !== null ?
                             oSetting.aaSortingFixed.concat(oSetting.aaSorting) :
                             oSetting.aaSorting.slice();
                args += '&iSortingCols=' + aaSort.length;
                for (i=0, len=aaSort.length; i < len; i++) {
                    args += '&iSortCol_' + i + '=' + aaSort[i][0];
                    args += '&sSortDir_' + i + '=' + aaSort[i][1];
                }
                url = appendUrlQuery(url, extension, args);
            } else {
                url = appendUrlQuery(url, extension, '');
            }
            // Use $.searchS3Download if available, otherwise (e.g. custom
            // page without s3.filter.js) fall back to window.open:
            if ($.searchDownloadS3 !== undefined) {
                $.searchDownloadS3(url, '_blank');
            } else {
                window.open(url);
            }
        });

        if (S3.dataTables.Resize) {
            // Resize the Columns after hiding extra data
            //dt.fnAdjustColumnSizing();
            dt.columns.adjust();
        }

        // Pass back to global scope
        oDataTable[tableIdx] = dt;

    }; // end of initDataTable function

    // Pass to global scope to allow dataTables to be initialised some time after the page is loaded.
    // - used by Vulnerability
    S3.dataTables.initDataTable = initDataTable;

    // Actions when document ready
    $(document).ready(function() {

        // Register all data tables (table_ids), and initialize them
        var dataTableIds = S3.dataTables.id;
        if (dataTableIds) {
            dataTableIds.forEach(function(tableId, idx) {

                var selector = '#' + tableId;

                table_ids[idx] = selector;
                initDataTable(selector, idx, false);
            });
        }
    });

}(jQuery));

// END ========================================================================
