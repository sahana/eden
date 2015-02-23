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
    var aHiddenFieldsID = [],
        ajax_urls = {}, // Lookup by id not index as easier for reloadAjax()
        aoTableConfig = [],
        columns = [],
        fnAjax = [],
        oDataTable = [],
        oGroupColumns = [],
        selectedRows = [],
        selectionMode = [],
        table_ids = [],
        textDisplay = [],
        totalRecords = [];

    // Global scope for reloadAjax()
    S3.dataTables.ajax_urls = ajax_urls;

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

    var updateURLQuery = function(target, source) {

        var tquery = target.split('?'),
            squery = source.split('?');

        var turlvars = tquery.length > 1 ? tquery[1].split('&') : [],
            surlvars = squery.length > 1 ? squery[1].split('&') : [],
            rurlvars = [],
            i, len, q;

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
    };

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
    };

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

    // Lookup a table index from it's selector
    var lookupTableIndex = function(selector) {
        var tableCnt = S3.dataTables.id.length;
        for (var t=0; t < tableCnt; t++) {
            if (table_ids[t] == selector) {
                return t;
            }
        }
        return -1;
    };

    var toggleCell = function() {
        $(this).parent()
               .toggle()
               .siblings('.dt-truncate')
               .toggle();
        return false;
    };

    var toggleRow = function(groupid) {
        var _sublevel = '.sublevel' + groupid.substr(6);
        var sublevel = $(_sublevel);
        var selector = '#' + groupid;
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
    };

    var accordionRow = function(t, level, groupid) {
        /* Close all rows with a level higher than then level passed in */
        // Get the level being opened
        var lvlOpened = level.substr(6);
        // Get a list of levels from the table
        var theTableObj = $(table_ids[t]);
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
    };
    // Pass to global scope to be accessible as an href in HTML & for s3.vulnerability.js
    S3.dataTables.accordionRow = accordionRow;

    /* Helper functions */
    var togglePairActions = function(t) {
        var s = selectedRows[t].length;
        if (selectionMode[t] == 'Exclusive') {
            s = totalRecords[t] - s;
        }
        if (s == 2) {
            $(table_ids[t] + ' .pair-action').removeClass('hide');
        } else {
            $(table_ids[t] + ' .pair-action').addClass('hide');
        }
    };

    var inList = function(id, list) {
    /* The selected items for bulk actions is held in the list parameter
       This function finds if the given id is in the list. */
        for (var cnt=0, lLen=list.length; cnt < lLen; cnt++) {
            if (id == list[cnt]) {
                return cnt;
            }
        }
        return -1;
    };

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
            $('.bulkcheckbox').unbind('click.bulkSelect')
                              .on('click.bulkSelect', function(event) {
                                  
                var id = this.id.substr(6),
                    rows = selectedRows[t];
                    
                var posn = inList(id, rows);
                if (posn == -1) {
                    rows.push(id);
                    posn = 0; // toggle selection class
                } else {
                    rows.splice(posn, 1);
                    posn = -1; // toggle selection class
                }
                var row = $(this).closest('tr');
                togglePairActions(t);
                setSelectionClass(t, row, posn);
            });
        }
    };

    // Show which rows have been selected for a bulk select action
    var setSelectionClass = function(t, row, index) {
        var $totalAvailable = $('#totalAvailable'),
            $totalSelected = $('#totalSelected'),
            numSelected = selectedRows[t].length;
        if (selectionMode[t] == 'Inclusive') {
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
            if (numSelected == totalRecords[t]) {
                $('#modeSelectionAll').prop('checked', true);
                selectionMode[t] = 'Exclusive';
                selectedRows[t] = [];
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
            if (numSelected == totalRecords[t]) {
                $('#modeSelectionAll').prop('checked', false);
                selectionMode[t] = 'Inclusive';
                selectedRows[t] = [];
            }
        }

        if (aoTableConfig[t]['bulkActions']) {

            // Make sure that the details of the selected records
            // are stored in the hidden fields
            $(aHiddenFieldsID[t][0]).val(selectionMode[t]);
            $(aHiddenFieldsID[t][1]).val(selectedRows[t].join(','));
            
            // Add the bulk action controls to the dataTable
            $('.dataTable-action').remove();
            $(bulk_action_controls).insertBefore('#bulk_select_options');

            // Activate bulk actions?
            numSelected = selectedRows[t].length;
            var off = selectionMode[t] == 'Inclusive' ? 0 : totalRecords[t];
            $('.selected-action').prop('disabled', (numSelected == off));
            togglePairActions(t);
        };
    };

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
            // @ToDo: Move to CSS
            levelDisplay += "<div style='float:left;width:10px;'>&nbsp;</div>";
        }
        if (level > 1) {
            // @ToDo: Move style to CSS
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
                // @ToDo: Move style to CSS
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
    }; // end of function addNewGroup

    /*********************************************************************
     * Function to group the data
     *
     * @param oSettings the dataTable settings
     * @param selector the selector of the table
     * @param t the index of the table
     * @param group The index of the colum that will be grouped
     * @param groupTotals (optional) the totals to be used for each group
     * @param level the level of this group, starting at 1
     *********************************************************************/
    var buildGroups = function(oSettings, selector, t, group, groupTotals, prefixID, groupTitles, level) {
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
        var nTrs = $(selector + ' tbody tr');
        var iColspan = $(selector + ' thead tr')[0].getElementsByTagName('th').length;
        var sLastGroup = '';
        var groupPrefix = '';
        var groupCnt = 1;
        var groupTitleCnt = 0;
        var dataCnt = 0;
        var sublevel = '';
        var levelClass = 'level_' + level;
        var title;
        $(selector).addClass(levelClass);
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
                        groupPrefix += oSettings.data[oSettings.aiDisplay[dataCnt]]._aData[prefixID[gpCnt]] + '_';
                    } catch(err) {}
                }
                continue;
            }
            var sGroup = oSettings.data[oSettings.aiDisplay[dataCnt]]._aData[group];
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
    };

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
    };

    //
    // Pipelining function for DataTables. To be used for the `ajax` option of DataTables
    // original version from http://datatables.net/examples/server_side/pipeline.html
    //
    $.fn.dataTable.pipeline = function(opts) {
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
        var cache = conf.cache;
        if (undefined != cache.cacheLower) {
            var cacheLower = cache.cacheLower;
        } else {
            var cacheLower = -1;
        }
        var cacheUpper = cache.cacheUpper || null,
            cacheLastRequest = cache.cacheLastRequest || null,
            cacheLastJson = cache.cacheLastJson || null;

        return function(request, drawCallback, settings) {
            // S3 Extension
            if (this.hasOwnProperty('nTable')) {
                // We have been called by reloadAjax()

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
            var id = settings.nTable.id;
            var selector = '#' + id;
            var t = lookupTableIndex(selector);
            if (cacheLastJson && cacheLastJson.hasOwnProperty('recordsTotal')) {
                totalRecords[t] = cacheLastJson.recordsTotal;
            } else {
                totalRecords[t] = request.recordsTotal;
            }
            if (requestLength == -1) {
                // Showing all records
                var total = totalRecords[t];
                if (typeof total != 'undefined') {
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
                    sendData.push({'name': 'iSortingCols',
                                   'value': order_len
                                   });
                    for (var i=0; i < order_len; i++) {
                        var _order = request.order[i];
                        sendData.push({'name': 'iSortCol_' + i,
                                       'value': _order.column
                                       });
                        sendData.push({'name': 'sSortDir_' + i,
                                       'value': _order.dir
                                       });
                    }
                }

                settings.jqXHR = $.ajaxS3({
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
        }
    };

    // Register an API method that will empty the pipelined data, forcing an Ajax
    // fetch on the next draw (i.e. `table.clearPipeline().draw()`)
    $.fn.dataTable.Api.register('clearPipeline()', function() {
        return this.iterator('table', function (settings) {
            settings.clearCache = true;
        });
    });

    /**
     * Initialise a dataTable
     *
     * Parameters:
     * id - {String} Selector to locate this dataTable (e.g. '#dataTable')
     * t - {Integer} The index within all the global vars
     * destroy - {Boolean} Whether to remove any existing dataTable with the same selector before creating this one
     */
    var initDataTable = function(selector, t, destroy) {
        // Read the configuration details
        var config_id = $(selector + '_configurations');
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
        columns[t] = tableColumns;

        if (tableConfig['groupTitles'].length > 0) {
            setSpecialSortRules(t, tableConfig, tableColumns);
        }

        fnActionCallBacks = [];

        // Buffer the array so that the default settings are preserved for the rest of the columns
        var columnCount = $(selector).find('thead tr').first().children().length;
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
                'sTitle': '<div id="bulk_select_options"><input id="modeSelectionAll" type="checkbox">' + i18n.selectAll + '</input></div>',
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

        /*
           Code to calculate the bulk action buttons

           They will actually be placed on the dataTable inside the headerCallback
           It is necessary to do this inside of the callback because the dataTable().fnDraw
           that these buttons trigger will remove the onClick binding.
        */
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
                bulk_submit += '<input type="submit" id="' + name + '-selected-action" class="' + cls + ' selected-action" name="' + name + '" value="' + value + '">&nbsp;';
            }
            // Module-scope currently as read by setSelectionClass()
            bulk_action_controls = '<div class="dataTable-action">' + bulk_submit + '</div>';
            // Add hidden fields to the form to record what has been selected
            // Module-scope currently as read by setSelectionClass()
            selected = $.parseJSON($(selector + '_dataTable_bulkSelection').val());
            if (selected === null) {
                selected = [];
            }
            selectedRows[t] = selected;
            selectionMode[t] = 'Inclusive';
            if ($(selector + '_dataTable_bulkSelectAll').val()) {
                selectionMode[t] = 'Exclusive';
            }
            aHiddenFieldsID[t] = [selector + '_dataTable_bulkMode',
                                  selector + '_dataTable_bulkSelection'
                                  ];
        }

        if (tableConfig['pagination'] == 'true') {
            // Server-side Pagination is True
            // Cache the pages to reduce server-side calls
            var serverSide = true;
            var processing = true;
            ajax_urls[selector.slice(1)] = tableConfig['ajaxUrl'];
            var pageLength = tableConfig['pageLength'];
            //var data = {'length': pageLength,
            //            'start': 0,
            //            'draw': 1
            //            };

            if ($(selector + '_dataTable_cache').length > 0) {
                var cache = $.parseJSON($(selector + '_dataTable_cache').val());
            } else {
                var cache = {};
            }

            fnAjax[t] = $.fn.dataTable.pipeline({
                cache: cache
                //data: data
            });
            // end of pagination code
        } else {
            // No Pagination
            var serverSide = false;
            var processing = false;
            var pageLength = tableConfig['pageLength'];
            fnAjax[t] = null;
        } // end of no pagination code

        var dt;
        dt = $(selector).dataTable({
            'ajax': fnAjax[t], // formerly fnServerData
            'autoWidth': false, // formerly bAutoWidth
            'columnDefs': [oGroupColumns[t]], // formerly aoColumnDefs
            'columns': tableColumns, // formerly aoColumns
            'deferRender': true, // formerly bDeferRender
            'destroy': destroy, // formerly bDestroy
            'dom': tableConfig['dom'], // formerly sDom
            'lengthMenu': tableConfig['lengthMenu'], // formerly aLengthMenu
            'order': tableConfig['order'], // formerly aaSorting
            'orderFixed': tableConfig['group'], // formerly aaSortingFixed
            'ordering': true, // formerly bSort
            'pageLength': pageLength, // formerly iDisplayLength
            'pagingType': tableConfig['pagingType'], // formerly sPaginationType
            'processing': processing, // formerly bProcessing
            'responsive': true,
            'searchDelay': 450,
            'searching': tableConfig['searching'] == 'true', // formerly bFilter
            'serverSide': serverSide, // formerly bServerSide
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

            'headerCallback': function (nHead, aasData, iStart, iEnd, aiDisplay) {
                $('#modeSelectionAll').unbind('click.selectAll')
                                      .on('click.selectAll', function(event) {
                    selectedRows[t] = [];
                    if ($(this).prop('checked')) {
                        selectionMode[t] = 'Exclusive';
                        dt.api().draw(false);
                    } else {
                        selectionMode[t] = 'Inclusive';
                        dt.api().draw(false);
                    }
                });
                $('.ui-icon-zoomin, .ui-icon-zoomout').unbind('click.dtToggleCell');
            },

            'rowCallback': function(nRow, aData, iDisplayIndex) { // formerly fnRowCallback
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
                    var Buttons = '', add_modals = false;
                    if (tableConfig['rowActions'].length) {
                        var Actions = tableConfig['rowActions'], action;
                        // Loop through each action to build the button
                        for (var i=0; i < Actions.length; i++) {
                            action = Actions[i];

                            //$('th:eq(0)').css( { 'width': 'auto' } );

                            // Check if action is restricted to a subset of records
                            if ('restrict' in action) {
                                if (inList(action_id, action.restrict) == -1) {
                                    continue;
                                }
                            }
                            var c = action._class;
                            var label = S3.Utf8.decode(action.label);
                            var title = label;
                            re = /%5Bid%5D/g;
                            if (action.icon) {
                                label = '<i class="' + action.icon + '" alt="' + label + '"> </i>';
                            } else if (action.img) {
                                label = '<img src="' + action.icon + '" alt="' + label + '"></img>';
                            }
                            if (action._onclick) {
                                var oc = Actions[i]._onclick.replace(re, action_id);
                                Buttons = Buttons + '<a class="' + c + '" onclick="' + oc + '">' + label + '</a>' + '&nbsp;';
                            } else if (action._jqclick) {
                                Buttons = Buttons + '<span class="' + c + '" id="' + action_id + '">' + label + '</span>' + '&nbsp;';
                                if (typeof S3ActionCallBack != 'undefined') {
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
                                Buttons = Buttons + '<a db_id="'+ action_id + '" class="' + c + '" href="' + url + '" title="' + title + '"' + target + '>' + label + '</a>' + '&nbsp;';
                            } else {
                                var ajaxURL = action._ajaxurl;
                                if (ajaxURL) {
                                    ajaxURL = ' data-url="' + ajaxURL + '"';
                                } else {
                                    ajaxURL = '';
                                }
                                Buttons = Buttons + '<a db_id="'+ action_id + '" class="' + c + '" title="' + title + '"' + ajaxURL + '>' + label + '</a>' + '&nbsp;';
                            }
                        } // end of loop through for each row Action for this table
                    } // end of if there are to be Row Actions for this table
                    // Put the actions buttons in the actionCol
                    if ((tableConfig['group'].length > 0) && (tableConfig['group'][0][0] < actionCol)) {
                        actionCol -= 1;
                    }
                    $('td:eq(' + actionCol + ')', nRow).addClass('actions').html(Buttons);
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
                    // Ignore if the data contains HTML tags
                    if (aData[j].match(/<.*>/)) {
                        tdposn++;
                        continue;
                    }
                    if (aData[j].length > textDisplay[t][0]) {
                        var disp = '<div class="dt-truncate"><span class="ui-icon ui-icon-zoomin" style="float:right"></span>' + aData[j].substr(0, textDisplay[t][1]) + "&hellip;</div>";
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

                $('.dt-truncate .ui-icon-zoomin, .dt-truncate .ui-icon-zoomout').bind('click.dtToggleCell', toggleCell);
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
                                    selector,
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
                        var nTrs = $(selector + ' tbody tr');
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
                    $(selector + '_paginate').css('display', 'block');
                } else {
                    $(selector + '_paginate').css('display', 'none');
                }
                // Add modals if necessary
                // - in future maybe use S3.redraw() to catach all elements
                if ($(selector).find('.s3_modal').length) {
                    S3.addModals();
                }
                // Do we have any records? => toggle empty section
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
                var $this = $(this);
                var db_id = $this.attr('db_id'),
                    ajaxURL = $this.data('url');
                if (ajaxURL && db_id) {
                    ajaxURL = ajaxURL.replace(/%5Bid%5D/g, db_id);
                }
                $.ajaxS3({
                    'url': ajaxURL,
                    'type': 'POST',
                    'dataType': 'json',
                    'data': '',
                    'success': function(data) {
                        dt.dataTable().reloadAjax();
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
              
            var oSetting = dt.dataTableSettings[t],
                url = $(this).data('url'),
                extension = $(this).data('extension');
                
            if (oSetting) {
                var arguments = 'id=' + tableid,
                    serverFilterArgs = $('#' + tableid + '_dataTable_filter');
                if (serverFilterArgs.val() !== '') {
                    arguments += '&sFilter=' + serverFilterArgs.val();
                }
                arguments += '&sSearch=' + oSetting.oPreviousSearch['sSearch'];
                columns = oSetting.aoColumns;
                var i, len;
                for (i=0, len=columns.length; i < len; i++) {
                    if (!columns[i].bSortable) {
                        arguments += '&bSortable_' + i + '=false';
                    }
                }
                var aaSort = oSetting.aaSortingFixed !== null ?
                             oSetting.aaSortingFixed.concat(oSetting.aaSorting) :
                             oSetting.aaSorting.slice();
                arguments += '&iSortingCols=' + aaSort.length;
                for (i=0, len=aaSort.length; i < len; i++) {
                    arguments += '&iSortCol_' + i + '=' + aaSort[i][0];
                    arguments += '&sSortDir_' + i + '=' + aaSort[i][1];
                }
                url = appendUrlQuery(url, extension, arguments);
            } else {
                url = appendUrlQuery(url, extension, '');
            }
            window.open(url);
        });

        if (S3.dataTables.Resize) {
            // Resize the Columns after hiding extra data
            //dt.fnAdjustColumnSizing();
            dt.columns.adjust();
        }

        // Pass back to global scope
        oDataTable[t] = dt;

    }; // end of initDataTable function

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
                var selector = '#' + S3.dataTables.id[t];
                table_ids[t] = selector;
                initDataTable(selector, t, false);
            }
        }
    };
    // Export to global scope so that $(document).ready can call it
    S3.dataTables.initAll = initAll;

}());

$(document).ready(function() {
    // Initialise all dataTables on the page
    S3.dataTables.initAll();
});

// END ========================================================================
