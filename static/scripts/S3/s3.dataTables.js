/**
 * Used by dataTables (views/dataTables.html)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

/**
 * Global vars
 * - usage minimised
 * - documentation useful on what these are for
 */
// Done in views/dataTables.html & s3.vulnerability.js
//S3.dataTables = {};

// Module pattern to hide internal vars
(function() {
    // Module scope
    var bulk_action_controls;
    var selected;

    // The configuration details for each table are currently stored as common indexes of a number of global variables
    // @ToDo: Move to being properties of the table instances instead
    //        - similar to S3.gis.maps
    var aHiddenFieldsID = [];
    var aoColumns = [];
    var aoTableConfig = [];
    var cache = [];
    var fnAjaxCallback = [];
    var oDataTable = [];
    var oGroupColumns = [];
    var selectedRows = [];
    var selectionMode = [];
    var tableId = [];
    var textDisplay = [];
    var totalRecords = [];

    var appendUrlQuery = function(url, extension, query) {
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

    /* Function used by Export buttons */
    var formatRequest = function(representation, tableid, url) {
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
            aoColumns = oSetting.aoColumns;
            var i, len;
            for (i=0, len=aoColumns.length; i < len; i++) {
                if (!aoColumns[i].bSortable) {
                    argData += '&bSortable_' + i + '=false';
                }
            }
            var aaSort = (oSetting.aaSortingFixed !== null) ?
                         oSetting.aaSortingFixed.concat(oSetting.aaSorting) :
                         oSetting.aaSorting.slice();
            argData += '&iSortingCols=' + aaSort.length;
            for (i=0, len=aaSort.length; i < len; i++) {
                argData += '&iSortCol_' + i + '=' + aaSort[i][0];
                argData += '&sSortDir_' + i + '=' + aaSort[i][1];
            }
            url = appendUrlQuery(url, representation, argData);
        } else {
            url = appendUrlQuery(url, representation, '');
        }
        window.open(url);
    }
    // Pass to global scope to be accessible onclick HTML
    S3.dataTables.formatRequest = formatRequest;

    /* Function to return the class name of the tag from the class name prefix that is passed in. */
    var getElementClass = function(tagObj, prefix) {
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

    var hideSubRows = function(groupid) {
        var sublevel = $('.sublevel' + groupid.substr(6));
        sublevel.each(function() {
            obj = $(this);
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
    }

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
    }

    // Lookup a table index from it's id
    var tableIdReverse = function(id) {
        var tableCnt = S3.dataTables.id.length;
        for (var t=0; t < tableCnt; t++) {
            if (tableId[t] == id) {
                return t;
            }
        }
        return -1;
    }

    var toggleDiv = function(divId) {
       $('#display' + divId).toggle();
       $('#full' + divId).toggle();
    }
    // Pass to global scope to be accessible as an href in HTML
    S3.dataTables.toggleDiv = toggleDiv;

    var toggleRow = function(groupid) {
        var _sublevel = '.sublevel' + groupid.substr(6);
        var sublevel = $(_sublevel);
        if (sublevel.is(':visible')) {
            // Close all sublevels and change the icon to collapsed
            hideSubRows(groupid);
            sublevel.hide();
            $('#' + groupid + '_closed').show();
            $('#' + groupid + '_open').hide();
            $('#' + groupid + '_in').show();
            $('#' + groupid + '_out').hide();
            // Display the spacer of open groups
            $(_sublevel + '.spacer').show();
        } else {
            // Open the immediate sublevel and change the icon to expanded
            sublevel.show();
            $('#' + groupid + '_closed').hide();
            $('#' + groupid + '_open').show();
            $('#' + groupid + '_in').hide();
            $('#' + groupid + '_out').show();
        }
    }
    // Pass to global scope to be accessible as an href in HTML
    S3.dataTables.toggleRow = toggleRow;

    /**
     * This function can be called by other scripts to attach the
     * accordion functionality to the row, not just the icon, as follows:
     *
     * $('.collapsable').click(function(){thisAccordionRow(0,this);});
     **/
    var thisAccordionRow = function(t, obj) {
        var level = '';
        var groupid = '';
        var classList = $(obj).attr('class').split(/\s+/);
        $.each(classList, function(index, rootClass){
            if (rootClass.substr(0, 6) == 'level_'){
                level = rootClass;
            }
            if (rootClass.substr(0, 6) == 'group_'){
                groupid = rootClass;
            }
        });
        accordionRow(t, level, groupid);
    }

    var accordionRow = function(t, level, groupid) {
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
    // Pass to global scope to be accessible as an href in HTML & for s3.vulnerability.js
    S3.dataTables.accordionRow = accordionRow;

    /**
     * Determine if this data element's value is the default for its key, and
     * return false if so. Used to remove data elements that have default values,
     * to reduce size of the URL in Ajax calls. We'll call this from filter() so
     * want it to return true for non-default elements.
     * @param element is an object with fields name and value.
     * @param index, @param array are unused, but allow calling this from filter().
     **/
    var isNonDefaultData = function(element, index, array) {
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

    /* Helper functions */
    var togglePairActions = function(t) {
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

    var inList = function(id, list) {
    /* The selected items for bulk actions is held in the list parameter
       This function finds if the given id is in the list. */
        for (var cnt=0, lLen=list.length; cnt < lLen; cnt++) {
            if (id == list[cnt]) {
                return cnt;
            }
        }
        return -1;
    }

    // Bind the row action and the bulk action buttons to their callback function
    var bindButtons = function(t, tableConfig, fnActionCallBacks) {
        if (tableConfig['rowActions'].length > 0) {
            for (var i=0; i < fnActionCallBacks.length; i++){
                var currentID = '#' + fnActionCallBacks[i][0];
                $(currentID).unbind('click')
                            .bind('click', fnActionCallBacks[i][1]);
            }
        }
        if (tableConfig['bulkActions']) {
            $('.bulkcheckbox').unbind('change')
                              .change(function(event) {
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

    // Show which rows have been selected for a bulk select action
    var setSelectionClass = function(t, row, index) {
        if (selectionMode[t] == 'Inclusive') {
            // @ToDo: can 'selected' be pulled in from a parameter rather than module-scope?
            $('#totalSelected').text(selected.length);
            if (index == -1) {
                $(row).removeClass('row_selected');
                $('.bulkcheckbox', row).prop('checked', false);
            } else {
                $(row).addClass('row_selected');
                $('.bulkcheckbox', row).prop('checked', true);
            }
        }
        if (selectionMode[t] == 'Exclusive') {
            $('#totalSelected').text(parseInt($('#totalAvailable').text(), 10) - selected.length);
            if (index == -1) {
                $(row).addClass('row_selected');
                $('.bulkcheckbox', row).prop('checked', true);
            } else {
                $(row).removeClass('row_selected');
                $('.bulkcheckbox', row).prop('checked', false);
            }
        }
        if (aoTableConfig[t]['bulkActions']) {
            // Make sure that the details of the selected records are stored in the hidden fields
            $(aHiddenFieldsID[t][0]).val(selectionMode[t]);
            $(aHiddenFieldsID[t][1]).val(selectedRows[t].join(','));
            // Add the bulk action controls to the dataTable
            $('.dataTable-action').remove();
            $(bulk_action_controls).insertBefore('#bulk_select_options');
            togglePairActions(t);
        };
    }

    /* Helper function to add the new group row */
    var addNewGroup = function(t,
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
            levelDisplay += "<div style='float:left;width:10px;'>&nbsp;</div>";
        }
        if (level > 1) {
            levelDisplay += '<div id="' + groupClass + '_closed" class="ui-icon ui-icon-triangle-1-e" style="float:left;"></div>';
            levelDisplay += '<div id="' + groupClass + '_open" class="ui-icon ui-icon-triangle-1-s" style="float:left;display:none;"></div>';
        }
        // Add the subtotal counts (if provided)
        var groupCount = '';
        // Not !== as we want to catch undefined as well as null
        if (groupTotals[sGroup] != null) {
            groupCount = ' (' + groupTotals[sGroup] + ')';
        } else {
            var index = groupPrefix + sGroup;
            if (groupTotals[index] != null) {
                groupCount = ' (' + groupTotals[index] + ')';
            }
        }
        // Create the new HTML elements
        var nGroup = document.createElement('tr');
        nGroup.className = 'group';
        if (shrink || accordion) {
            $(nGroup).addClass('headerRow')
                     .addClass(groupClass)
                     .addClass(levelClass);
            if (sublevel) {
                $(nGroup).addClass(sublevel)
                         .addClass('collapsable');
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
                iconin = '<a id="' + groupClass + '_in" href="javascript:S3.dataTables.toggleRow(\'' + groupClass + '\');" ' + iconClassOpen + ' style="float:right">' + iconTextOpen + '</a>';
                iconout = '<a id="' + groupClass + '_out" href="javascript:S3.dataTables.toggleRow(\'' + groupClass + '\');" ' + iconClassClose + ' style="float:right; display:none">' + iconTextClose + '</a>';
            } else {
                if (iconGroupType == 'icon') {
                    iconClassOpen = 'class="ui-icon ui-icon-arrowthick-1-e arrow_e' + groupClass + '" ';
                    iconClassClose = 'class="ui-icon ui-icon-arrowthick-1-s arrow_s' + groupClass + '" ';
                } else {
                    iconClassOpen = 'class="arrow_e' + groupClass + '" ';
                    iconClassClose = 'class="arrow_s' + groupClass + '" ';
                }
                iconin = '<a href="javascript:S3.dataTables.accordionRow(\'' + t + '\', \'' + levelClass + '\', \'' + groupClass + '\');" ' + iconClassOpen + ' style="float:right">' + iconTextOpen + '</a>';
                iconout = '<a href="javascript:S3.dataTables.accordionRow(\'' + t + '\', \'' + levelClass + '\', \'' + groupClass + '\');" ' + iconClassClose + ' style="float:right; display:none">' + iconTextClose + '</a>';
            }
            var htmlText = groupTitle + groupCount + iconin + iconout;
        } else {
            var htmlText = groupTitle + groupCount;
        }
        var nCell = document.createElement('td');
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
            var _nSpace = $(nSpace);
            _nSpace.addClass('spacer');
            if (sublevel){
                _nSpace.addClass(sublevel)
                       .addClass('collapsable');
            } else {
                _nSpace.addClass('alwaysOpen');
            }
            nCell = document.createElement('td');
            nCell.colSpan = iColspan;
            nSpace.appendChild(nCell);
            _nSpace.insertAfter(nGroup);
        }
    } // end of function addNewGroup

    /*********************************************************************
     * Function to group the data
     *
     * @param oSettings the dataTable settings
     * @param id the selector of the table
     * @param t the index of the table
     * @param group The index of the colum that will be grouped
     * @param groupTotals (optional) the totals to be used for each group
     * @param level the level of this group, starting at 1
     *********************************************************************/
    var buildGroups = function(oSettings, id, t, group, groupTotals, prefixID, groupTitles, level) {
        // @ToDo: Pass table instance not index
        var tableConfig = aoTableConfig[t];
        if (tableConfig['shrinkGroupedRows'] == 'individual') {
            var shrink = true;
            var accordion = false;
        } else if (tableConfig['shrinkGroupedRows'] == 'accordion') {
            var shrink = false;
            var accordion = true;
        } else {
            var shrink = false;
            var accordion = false;
        }
        var insertSpace = tableConfig['groupSpacing'];
        var iconGroupTypeList = tableConfig['groupIcon'];
        if (iconGroupTypeList.length >= level) {
            var iconGroupType = iconGroupTypeList[level - 1];
        } else {
            var iconGroupType = 'icon';
        }
        var nTrs = $(id + ' tbody tr');
        var iColspan = $(id + ' thead tr')[0].getElementsByTagName('th').length;
        var sLastGroup = '';
        var groupPrefix = '';
        var groupCnt = 1;
        var groupTitleCnt = 0;
        var dataCnt = 0;
        var sublevel = '';
        var levelClass = 'level_' + level;
        var title;
        $(id).addClass(levelClass);
        for (var i=0; i < nTrs.length; i++) {
            var row = $(nTrs[i]);
            if (row.hasClass('spacer')) {
                continue;
            }
            if (row.hasClass('group')) {
                // Calculate the sublevel which can be used for the next new group
                var item = getElementClass($(nTrs[i]), 'group_');
                sublevel = 'sublevel' + item.substr(6);
                sLastGroup = '';
                groupPrefix = '';
                for (var gpCnt = 0; gpCnt < prefixID.length; gpCnt++) {
                    try {
                        groupPrefix += oSettings.aoData[oSettings.aiDisplay[dataCnt]]._aData[prefixID[gpCnt]] + '_';
                    } catch(err) {}
                }
                continue;
            }
            var sGroup = oSettings.aoData[oSettings.aiDisplay[dataCnt]]._aData[group];
            if (sGroup != sLastGroup) {
                // New group
                while (groupTitles.length > groupTitleCnt && sGroup != groupTitles[groupTitleCnt][0]) {
                    title = groupTitles[groupTitleCnt][1];
                    addNewGroup(t, title, level, sublevel, iColspan, groupTotals, groupPrefix, title, false, iconGroupType, insertSpace, shrink, accordion, groupCnt, nTrs[i], true);
                    groupTitleCnt++;
                    groupCnt++;
                }
                if (groupTitles.length > groupTitleCnt){
                    title = groupTitles[groupTitleCnt][1];
                    addNewGroup(t, title, level, sublevel, iColspan, groupTotals, groupPrefix, title, true, iconGroupType, insertSpace, shrink, accordion, groupCnt, nTrs[i], true);
                    groupTitleCnt++;
                } else {
                    addNewGroup(t, sGroup, level, sublevel, iColspan, groupTotals, groupPrefix, sGroup, true, iconGroupType, insertSpace, shrink, accordion, groupCnt, nTrs[i], true);
                }
                groupCnt++;
                sLastGroup = sGroup;
            } // end of processing for a new group
            dataCnt += 1;
            if (shrink || accordion) {
                // Hide the detail row
                row.hide();
            }
        } // end of loop for each row
        // add any empty groups not yet added to at the end of the table
        while (groupTitles.length > groupTitleCnt) {
            title = groupTitles[groupTitleCnt][1];
            addNewGroup(t, title, level, sublevel, iColspan, groupTotals, groupPrefix, title, false, iconGroupType, insertSpace, shrink, accordion, groupCnt, nTrs[nTrs.length-1], false);
            groupTitleCnt++;
            groupCnt++;
        }
    }

    var setSpecialSortRules = function(t, tableConfig, tableColumns) {
        var titles = tableConfig['groupTitles'];
        var order = [];
        var fname = 'group-title-' + t;
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
        tableColumns[tableConfig['group'][0][0]] = {'sType': fname};
    }

    /**
     * Initialise a dataTable
     *
     * Parameters:
     * id - {String} Selector to locate this dataTable (e.g. '#dataTable')
     * t - {Integer} The index within all the global vars
     * bDestroy - {Boolean} Whether to remove any existing dataTable with the same selector before creating this one
     */
    var initDataTable = function(id, t, bDestroy) {
        // Read the configuration details
        var config_id = $(id + '_configurations');
        if (config_id.length > 0) {
            var tableConfig = $.parseJSON(config_id.val());
        } else {
            // No config can be read: abort
            oDataTable[t] = null;
            return;
        }

        var tableColumns = [];
        // Pass to global scope
        aoTableConfig[t] = tableConfig;
        aoColumns[t] = tableColumns;

        if (tableConfig['groupTitles'].length > 0) {
            setSpecialSortRules(t, tableConfig, tableColumns);
        }

        fnActionCallBacks = [];

        // Buffer the array so that the default settings are preserved for the rest of the columns
        var columnCount = $(id).find('thead tr').first().children().length;
        for (var c=0; c < columnCount; c++) {
            tableColumns[c] = null;
        }

        // Action Buttons
        if (tableConfig['rowActions'].length < 1) {
            if (S3.dataTables.Actions) {
                tableConfig['rowActions'] = S3.dataTables.Actions;
            } else {
                tableConfig['rowActions'] = [];
            }
        }
        if (tableConfig['rowActions'].length > 0) {
            tableColumns[tableConfig['actionCol']] = {
                'sTitle': ' ',
                'bSortable': false
            };
        }
        if (tableConfig['bulkActions']) {
            tableColumns[tableConfig['bulkCol']] = {
                // @ToDo: i18n
                'sTitle': '<select id="bulk_select_options"><option></option><option id="modeSelectionAll">Select All</option><option id="modeSelectionNone">Deselect All</option></select>',
                'bSortable': false
            };
        }
        textDisplay[t] = [tableConfig['textMaxLength'],
                          tableConfig['textShrinkLength']
                          ];

        if (tableConfig['group'].length > 0) {
            var groupList = tableConfig['group'];
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
           that these buttons trigger will remove the onClick binding. */
        if (tableConfig['bulkActions']) {
            var bulk_submit = '';
            for (var i=0, iLen=tableConfig['bulkActions'].length; i < iLen; i++) {
                var bulk_action = tableConfig['bulkActions'][i],
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
                bulk_submit += '<input type="submit" id="submitSelection" class="' + cls + '" name="' + name + '" value="' + value + '">&nbsp;';
            }
            // Module-scope currently as read by setSelectionClass()
            bulk_action_controls = '<div class="dataTable-action">' + bulk_submit + '</div>';
            // Add hidden fields to the form to record what has been selected
            // Module-scope currently as read by setSelectionClass()
            selected = $.parseJSON($(tableId[t] + '_dataTable_bulkSelection').val());
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

        if (tableConfig['pagination'] == 'true') {
            // Server-side Pagination is True
            // Cache the pages to reduce server-side calls
            var bServerSide = true;
            var bProcessing = true;
            var iDisplayLength = tableConfig['displayLength'];
            var aoData = [{name: 'iDisplayLength', value: iDisplayLength},
                          {name: 'iDisplayStart', value: 0},
                          {name: 'sEcho', value: 1}
                          ];

            if ($(tableId[t] + '_dataTable_cache').length > 0) {
                cache[t] = $.parseJSON($(tableId[t] + '_dataTable_cache').val());
            } else {
                cache[t] = { iCacheLower: -1 };
            }

            function fnSetKey(aoData, sKey, mValue) {
                for (var i=0, iLen=aoData.length; i < iLen; i++) {
                    if (aoData[i].name == sKey) {
                        aoData[i].value = mValue;
                    }
                }
            }
            function fnGetKey(aoData, sKey) {
                for (var i=0, iLen=aoData.length; i < iLen; i++) {
                    if (aoData[i].name == sKey) {
                        return aoData[i].value;
                    }
                }
                return null;
            }
            var fnDataTablesPipeline = function(sSource, aoData, fnCallback) {
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
                oCache.iDisplayStart = iRequestStart;
                if (oCache.hasOwnProperty('lastJson') && oCache.lastJson.hasOwnProperty('iTotalRecords')) {
                    totalRecords[t] = oCache.lastJson.iTotalRecords;
                } else {
                    // This key never seems to be present?
                    totalRecords[t] = fnGetKey(aoData, 'iTotalRecords');
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
                if (oCache.iCacheUpper !== -1 && /* If Display All oCache.iCacheUpper == -1 */
                    (iRequestLength == -1 || oCache.iCacheLower < 0 || iRequestStart < oCache.iCacheLower || iRequestEnd > oCache.iCacheUpper)
                    ) {
                    bNeedServer = true;
                }
                // sorting etc changed?
                if (oCache.lastRequest && !bNeedServer) {
                    if (!oCache.lastRequest.length) {
                        // no previous request => need server in any case
                        bNeedServer = true;
                    } else {
                        for (var i=0, iLen=aoData.length; i < iLen; i++) {
                            if (aoData[i].name != 'iDisplayStart' && aoData[i].name != 'iDisplayLength' && aoData[i].name != 'sEcho') {
                                if (aoData[i].value != oCache.lastRequest[i].value) {
                                    bNeedServer = true;
                                    break;

                                }
                            }
                        }
                    }
                }

                // Store the request for checking next time around
                oCache.lastRequest = aoData.slice();
                if (bNeedServer) {
                    if (iRequestStart < oCache.iCacheLower) {
                        iRequestStart = iRequestStart - (iRequestLength * (iPipe - 1));
                        if (iRequestStart < 0) {
                            iRequestStart = 0;
                        }
                    }
                    oCache.iCacheLower = iRequestStart;
                    oCache.iDisplayLength = fnGetKey(aoData, 'iDisplayLength');
                    if (iRequestLength == -1) {
                        oCache.iCacheUpper = -1; // flag for all records are in Cache
                        fnSetKey(aoData, 'iDisplayStart', 'None'); // No Filter
                        fnSetKey(aoData, 'iDisplayLength', 'None');  // No Filter
                    } else {
                        oCache.iCacheUpper = iRequestStart + (iRequestLength * iPipe);
                        fnSetKey(aoData, 'iDisplayStart', iRequestStart);
                        fnSetKey(aoData, 'iDisplayLength', iRequestLength * iPipe);
                    }
                    var nonDefaultData = aoData.filter(isNonDefaultData);
                    $.getJSON(sSource, nonDefaultData, function(json) {
                        // Callback processing
                        oCache.lastJson = $.extend(true, {}, json);
                        if (oCache.iCacheLower != oCache.iDisplayStart) {
                            json.aaData.splice(0, oCache.iDisplayStart - oCache.iCacheLower);
                        }
                        if (oCache.iDisplayLength !== -1) {
                            json.aaData.splice(oCache.iDisplayLength, json.aaData.length);
                        }
                        fnCallback(json);
                    } );
                } else {
                    json = $.extend(true, {}, oCache.lastJson);
                    json.sEcho = sEcho; // Update the echo for each response
                    if (iRequestLength !== -1) {
                        json.aaData.splice(0, iRequestStart - oCache.iCacheLower);
                        json.aaData.splice(iRequestLength, json.aaData.length);
                    }
                    fnCallback(json);
                }
            };
            fnAjaxCallback[t] = fnDataTablesPipeline;
            // end of pagination code
        } else {
            // No Pagination
            var bServerSide = false;
            var bProcessing = false;
            tableConfig['ajaxUrl'] = null;
            var fnDataTablesPipeline = function(url, data, callback) {
                var nonDefaultData = data.filter(isNonDefaultData);
                $.ajax({
                    'url': url,
                    'data': nonDefaultData,
                    'dataType': 'json',
                    'cache': false
                }).done(function(data, status) {
                    if (callback) {
                        callback(data, status);
                    }
                }).fail(function(jqXHR, textStatus, errorThrown) {
                    if (textStatus == 'parsererror') {
                        alert('DataTables warning: JSON data from server could not be parsed. ' +
                              'This is caused by a JSON formatting error.');
                    }
                });
            };
            fnAjaxCallback[t] = fnDataTablesPipeline;
        } // end of no pagination code

        var dt;
        dt = $(id).dataTable({
            'aaSorting': tableConfig['aaSort'],
            'aaSortingFixed': tableConfig['group'],
            'aLengthMenu': tableConfig['lengthMenu'],
            'aoColumnDefs': [oGroupColumns[t]],
            'aoColumns': tableColumns,
            'bAutoWidth' : false,
            'bDeferRender': true,
            'bDestroy': bDestroy,
            'bFilter': tableConfig['bFilter'] == 'true',
            'bProcessing': bProcessing,
            'bServerSide': bServerSide,
            'bSort': true,
            'sDom': tableConfig['sDom'],
            'iDisplayLength': tableConfig['displayLength'],
            'sPaginationType': tableConfig['paginationType'],
            'sAjaxSource': tableConfig['ajaxUrl'],
            'fnHeaderCallback' : function (nHead, aasData, iStart, iEnd, aiDisplay) {
                $('#modeSelectionAll').on('click', function(event) {
                    //var wrapper = $(this).parents('.dataTables_wrapper')[0].id;
                    //var selector = '#' + wrapper.substr(0, wrapper.length - 8);
                    //var t = tableIdReverse(selector);
                    selectionMode[t] = 'Exclusive';
                    selectedRows[t] = [];
                    //oDataTable[t].fnDraw(false);
                    dt.fnDraw(false);
                });
                $('#modeSelectionNone').on('click', function(event) {
                    //var wrapper = $(this).parents('.dataTables_wrapper')[0].id;
                    //var selector = '#' + wrapper.substr(0, wrapper.length - 8);
                    //var t = tableIdReverse(selector);
                    selectionMode[t] = 'Inclusive';
                    selectedRows[t] = [];
                    //oDataTable[t].fnDraw(false);
                    dt.fnDraw(false);
                });
            },
            'fnServerData': fnAjaxCallback[t],
            'fnRowCallback': function(nRow, aData, iDisplayIndex) {
                // Extract the index # from the link (should be in-scope still)
                //var t = tableIdReverse(this.selector);
                var actionCol = tableConfig['actionCol'];
                var re = />(.*)</i;
                var result = re.exec(aData[actionCol]);
                var action_id;
                if (result === null) {
                    action_id = aData[actionCol];
                } else {
                    action_id = result[1];
                }
                // Set the action buttons in the id column for each row
                if (tableConfig['rowActions'].length || tableConfig['bulkActions']) {
                    var Buttons = '';
                    if (tableConfig['rowActions'].length) {
                        var Actions = tableConfig['rowActions'];
                        // Loop through each action to build the button
                        for (var i=0; i < Actions.length; i++) {

                            $('th:eq(0)').css( { 'width': 'auto' } );

                            // Check if action is restricted to a subset of records
                            if ('restrict' in Actions[i]) {
                                if (inList(action_id, Actions[i].restrict) == -1) {
                                    continue;
                                }
                            }
                            var c = Actions[i]._class;
                            var label = S3.Utf8.decode(Actions[i].label);
                            re = /%5Bid%5D/g;
                            if (Actions[i]._onclick) {
                                var oc = Actions[i]._onclick.replace(re, action_id);
                                Buttons = Buttons + '<a class="' + c + '" onclick="' + oc + '">' + label + '</a>' + '&nbsp;';
                            } else if (Actions[i]._jqclick) {
                                Buttons = Buttons + '<span class="' + c + '" id="' + action_id + '">' + label + '</span>' + '&nbsp;';
                                if (typeof S3ActionCallBack != 'undefined') {
                                    fnActionCallBacks.push([action_id, S3ActionCallBack]);
                                }
                            } else {
                                if (Actions[i].icon) {
                                    label = '<img src="' + Actions[i].icon + '" alt="' + label + '" title="' + label + '">';
                                }
                                var url = Actions[i].url.replace(re, action_id);
                                Buttons = Buttons + '<a db_id="'+ action_id +'" class="'+ c + '" href="' + url + '">' + label + '</a>' + '&nbsp;';
                            }
                        } // end of loop through for each row Action for this table
                    } // end of if there are to be Row Actions for this table
                    // Put the actions buttons in the actionCol
                    if ((tableConfig['group'].length > 0) && (tableConfig['group'][0][0] < actionCol)) {
                        actionCol -= 1;
                    }
                    $('td:eq(' + actionCol + ')', nRow).html( Buttons );
                } // end of processing for the action and bulk buttons

                // Code to toggle the selection of the row
                if (tableConfig['bulkActions']) {
                    setSelectionClass(t, nRow, inList(action_id, selectedRows[t]));
                }
                // Code to add special CSS styles to a row
                var styles = tableConfig['rowStyles'];
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
                var tdposn = 0;
                var gList = [];
                if (tableConfig['group'].length) {
                    var groupList = tableConfig['group'];
                    for (var gCnt=0; gCnt < groupList.length; gCnt++) {
                        gList.push(groupList[gCnt][0]);
                    }
                }
                for (var j=0; j < aData.length; j++) {
                    // Ignore any columns used for groups
                    if ($.inArray(j, gList) != -1) {
                        continue;
                    }
                    // Ignore if the data starts with an html open tag
                    if (aData[j][0] == '<') {
                        tdposn++;
                        continue;
                    }
                    if (aData[j].length > textDisplay[t][0]) {
                        var uniqueid = '_' + t + iDisplayIndex + j;
                        var icon = '<a href="javascript:S3.dataTables.toggleDiv(\'' + uniqueid + '\');" class="ui-icon ui-icon-zoomin" style="float:right"></a>';
                        var display = '<div id="display' + uniqueid + '">' + icon + aData[j].substr(0, textDisplay[t][1]) + "&hellip;</div>";
                        icon = '<a href="javascript:S3.dataTables.toggleDiv(\'' + uniqueid + '\');" class="ui-icon ui-icon-zoomout" style="float:right"></a>';
                        display += '<div  style="display:none" id="full' + uniqueid + '">' + icon + aData[j] + "</div>";
                        $('td:eq(' + tdposn + ')', nRow).html( display );
                    }
                    // increment the count of the td tags (don't do this for groups)
                    tdposn++;
                } // end of code to condense 'long text' in a cell
                return nRow;
            }, // end of fnRowCallback
            'fnDrawCallback': function(oSettings) {
                //var table = '#' + oSettings.nTable.id;
                //var t = tableIdReverse(table);
                // If using Modals for Update forms:
                //S3.addModals();
                bindButtons(t, tableConfig, fnActionCallBacks);
                if (oSettings.aiDisplay.length === 0) {
                    return;
                }
                if (tableConfig['group'].length) {
                    var groupList = tableConfig['group'];
                    for (var gCnt=0; gCnt < groupList.length; gCnt++) {
                        // The prefixID is used to identify what will be added to the key for the
                        // groupTotals, typically it will be a comma separated list of the groups
                        var prefixID = [];
                        for (var pixidCnt = 0; pixidCnt < gCnt; pixidCnt++) {
                            prefixID.push(groupList[pixidCnt][0]);
                        }
                        var group = groupList[gCnt];
                        if (tableConfig['groupTotals'].length > gCnt) {
                            var groupTotals = tableConfig['groupTotals'][gCnt];
                        } else {
                            var groupTotals = [];
                        }
                        if (tableConfig['groupTitles'].length > gCnt) {
                            var groupTitles = tableConfig['groupTitles'][gCnt];
                        } else {
                            var groupTitles = [];
                        }
                        buildGroups(oSettings,
                                    id,
                                    t,
                                    group[0],
                                    groupTotals,
                                    prefixID,
                                    groupTitles,
                                    gCnt + 1
                                    );
                    }
                    // Now loop through each row and add the subLevel controls for row collapsing
                    var shrink = tableConfig['shrinkGroupedRows'] == 'individual';
                    var accordion = tableConfig['shrinkGroupedRows'] == 'accordion';
                    if (shrink || accordion) {
                        var nTrs = $(id + ' tbody tr');
                        var sublevel = '';
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
                            accordionRow(t, 'level_1', 'group_' + t + '11');
                        }
                        $('.expandable').click(function() {
                            thisAccordionRow(t, this);
                        });
                   } // end of collapsable rows
                }
                if (Math.ceil((oSettings.fnRecordsDisplay()) / oSettings._iDisplayLength) > 1)  {
                    $(id + '_paginate').css('display', 'block');
                } else {
                    $(id + '_paginate').css('display', 'none');
                }
            } // end of fnDrawCallback
        }); // end of call to $(id).datatable()

        // Delay in milliseconds to prevent too many AJAX calls
        dt.fnSetFilteringDelay(450);

        // Does not handle horizontal overflow properly:
        //new FixedHeader(dt);

        if (S3.dataTables.Resize) {
            // Resize the Columns after hiding extra data
            dt.fnAdjustColumnSizing();
        }

        // Pass back to global scope
        oDataTable[t] = dt;

    } // end of initDataTable function

    // Pass to global scope to allow dataTables to be initialised some time after the page is loaded.
    // - used by Vulnerability
    S3.dataTables.initDataTable = initDataTable;

    // Function to Initialise all dataTables in the page
    // Designed to be called from $(document).ready()
    var initAll = function() {
        if (S3.dataTables.id) {
            // Iterate through each dataTable, store ID in list & Init it
            var tableCnt = S3.dataTables.id.length;
            for (var t=0; t < tableCnt; t++) {
                var id = '#' + S3.dataTables.id[t];
                tableId[t] = id;
                initDataTable(id, t, false);
            }
        }
    }
    // Export to global scope so that $(document).ready can call it
    S3.dataTables.initAll = initAll;

}());

$(document).ready(function() {
    // Initialise all dataTables on the page
    S3.dataTables.initAll();

    // Add Events to any Map Buttons present
    // S3Search Results
    var dt_mapButton = $('#gis_datatables_map-btn');
    if (dt_mapButton) {
        dt_mapButton.on('click', function() {
            // Find the map
            var map_id = dt_mapButton.attr('map');
            if (undefined == map_id) {
                map_id = 'default_map';
            }
            var map = S3.gis.maps[map_id];
            // Load the search results layer
            var layers = map.layers;
            var layer, j, jlen, strategies, strategy;
            for (var i=0, len=layers.length; i < len; i++) {
                layer = layers[i];
                if (layer.s3_layer_id == 'search_results') {
                    // Set a new event to restore clustering when the layer is loaded
                    layer.events.on({
                        'loadend': S3.gis.search_layer_loadend
                    });
                    // Disable Clustering to get correct bounds
                    strategies = layer.strategies;
                    for (j=0, jlen=strategies.length; j < jlen; j++) {
                        strategy = strategies[j];
                        if (strategy.CLASS_NAME == 'OpenLayers.Strategy.AttributeCluster') {
                            strategy.deactivate();
                        }
                    }
                    layer.setVisibility(true);
                }
            };
            if (map.s3.polygonButton) {
                // Disable the polygon control
                map.s3.polygonButton.disable();
            }
            map.s3.mapWin.show();
            // Disable the crosshair on the Map Selector
            $('.olMapViewport').removeClass('crosshair');
            // Set the Tab to show as active
            dt_mapButton.parent()
                        .addClass('tab_here');
            // Deactivate the list Tab
            $('#gis_datatables_list_tab').parent()
                                         .removeClass('tab_here')
                                         .addClass('tab_other');
            // Set to revert if Map closed
            $('div.x-tool-close').click(function(evt) {
                // Set the Tab to show as inactive
                dt_mapButton.parent()
                            .removeClass('tab_here')
                            .addClass('tab_other');
                // Activate the list Tab
                $('#gis_datatables_list_tab').parent()
                                             .removeClass('tab_other')
                                             .addClass('tab_here');
            });
            // @ToDo: Close Map Window & revert if Tab clicked
        });
    }

    // S3Search Widget
    var search_mapButton = $('#gis_search_map-btn');
    if (search_mapButton) {
        search_mapButton.on('click', function(evt) {
            // Prevent button submitting the form
            evt.preventDefault();
            // Find the map
            var map_id = search_mapButton.attr('map');
            if (undefined == map_id) {
                map_id = 'default_map';
            }
            var map = S3.gis.maps[map_id];
            // Enable the polygon control
            map.s3.polygonButton.enable();
            // @ToDo: Set appropriate Bounds
            // Default to current gis_config
            // If there is an Options widget for Lx, then see if that is set & use this
            map.s3.mapWin.show();
            // Enable the crosshair on the Map Selector
            $('.olMapViewport').addClass('crosshair');
        });
    }
});

// END ========================================================================
