/**
    S3Filter Static JS Code
*/

S3.search = {};

// Module pattern to hide internal vars
(function() {

    "use strict";

    /**
     * Rewrite the Ajax options for a filtered GET, converting into a POST
     *
     * @param {object} s - the Ajax options dict
     */
    var searchRewriteAjaxOptions = function(s, method) {

        // Rewrite only GET
        if (s.type != 'GET') {
            return;
        } else {
            s.type = 'POST';
        }

        // Helper function to check whether a URL variable is a filter expression
        var isFilterKey = function(k) {
            var k0 = k[0];
            return (k == '$filter' || k0 != '_' && (k.search(/\./) != -1 || k0 == '(' && k.search(/\)/) != -1));
        };

        var parts = s.url.split('#'),
            path = parts[0],
            fragment = null,
            query = null;

        // Split the URL into path, query and fragment
        if (parts.length > 1) {
            fragment = parts[1];
        }
        parts = path.split('?');
        path = parts[0];
        if (parts.length > 1) {
            query = parts[1];
        }

        var ajaxData = s.data,
            postData = {},
            queryDict = {},
            queryItem,
            valueCount,
            itemCount,
            i,
            j,
            k,
            v;

        // Helper function to add a query item to a query item dict
        var addQueryItem = function(items, key, val) {
            if (Array.isArray(val)) {
                for (j = 0, valueCount = val.length; j < valueCount; j++) {
                    addQueryItem(items, key, val[j]);
                }
                return;
            }
            if (!items.hasOwnProperty(key)) {
                items[key] = val;
            } else if (Array.isArray(items[key])) {
                items[key].push(val);
            } else {
                items[key] = [items[key], val];
            }
        };

        // Add the original ajaxData to the queryDict
        if (ajaxData) {
            for (i = 0, itemCount = ajaxData.length; i < itemCount; i++) {
                queryItem = ajaxData[i];
                addQueryItem(queryDict, queryItem.name, queryItem.value);
            }
        }

        // Parse the query string, add filter expressions to the
        // postData, and other query items to the queryDict
        if (query) {
            var items = S3.queryString.parse(query);
            for (k in items) {
                v = items[k];
                if (isFilterKey(k)) {
                    addQueryItem(postData, k, v);
                } else {
                    addQueryItem(queryDict, k, v);
                }
            }
        }
        if (method == "ajax") {
            s.data = JSON.stringify(postData);
        } else {
            s.data = postData;
        }
        s.processData = false;

        // Construct new Ajax URL
        var ajaxURL = path + '?$search=' + method;

        // Stringify and append queryDict
        var queryString = S3.queryString.stringify(queryDict);
        if (queryString) {
            ajaxURL += '&' + queryString;
        }

        // Append fragment
        if (fragment !== null) {
            ajaxURL += '#' + fragment;
        }
        s.url = ajaxURL;
    };

    // Pass to global scope to be called by s3.gis.js
    S3.search.searchRewriteAjaxOptions = searchRewriteAjaxOptions;

    /**
     * Default options for $.searchS3
     */
    var searchS3Defaults = {
        timeout : 10000, // 10s
        retryLimit: 5,
        dataType: 'json',
        contentType: 'application/json; charset=utf-8',
        processData: false,
        async: true,
        type: 'POST'
    };

    /**
     * Ajax search request method, converts GET into POST, encoding
     * URL filters as JSON request body, thus allowing arbitrary
     * length of filter options as well as TLS encryption of filters
     *
     * @param {object} s - the Ajax options
     * @prop {string} s.url - the Ajax URL
     * @prop {Array} s.data - Filters as array of dicts {name: k, value: v},
     *                        will be encoded as JSON body of the POST request
     * @prop {function} s.success - the success-callback
     * @prop {function} s.error - the error-callback
     *
     * @note: only GET requests will be converted, while POST requests
     *        will be sent unmodified (=equivalent to $.ajaxS3)
     */
    $.searchS3 = function(ajaxOptions) {

        // Apply searchS3-specific defaults
        var options = $.extend({}, searchS3Defaults, ajaxOptions);

        // Rewrite the GET as POST
        searchRewriteAjaxOptions(options, 'ajax');

        // Forward to $.ajaxS3
        return $.ajaxS3(options);
    };

    /**
     * Non-Ajax search request method, converts GET into POST, encoding
     * URL filters as form data, thus allowing arbitrary length of filter
     * options as well as TLS encryption of filters. Opens the filtered URL
     * in the window specified by target (default: _self)
     *
     * @param {string} url: the request URL
     * @param {string} target: the target window
     */
    $.searchDownloadS3 = function(url, target) {

        var options = $.extend({}, searchS3Defaults, {url: url}),
            form = document.createElement('form');

        options.type = 'GET';
        searchRewriteAjaxOptions(options, 'form');

        form.action = options.url;
        form.method = 'POST';
        form.target = target || '_self';
        form.enctype = 'multipart/form-data';

        var data = options.data;
        if (data) {
            var key,
                input;
            for (key in data) {
                input = document.createElement('textarea');
                input.name = key;
                input.value = JSON.stringify(data[key]);
                form.appendChild(input);
            }
        }
        form.style.display = 'none';
        document.body.appendChild(form);
        form.submit();
    };

    /**
     * pendingTargets: targets which were invisible during last filter-submit
     */
    var pendingTargets = {};

    /**
     * quoteValue: add quotes to values which contain commas, escape quotes
     */
    var quoteValue = function(value) {
        if (value) {
            var result = value.replace(/\"/, '\\"');
            if (result.search(/\,/) != -1) {
                result = '"' + result + '"';
            }
            return result;
        } else {
            return (value);
        }
    };

    /**
     * parseValue: parse a URL filter value into an array of individual values
     */
    var parseValue = function(value) {
        if (!value) {
            return value;
        }
        var values = [],
            quote = false;
        for (var idx=0, i=0; i < value.length; i++) {
            var c = value[i];
            values[idx] = values[idx] || '';
            if (c == '"') {
                quote = !quote;
                continue;
            }
            if (c == ',' && !quote) {
                if (values[idx] == 'NONE') {
                    values[idx] = null;
                }
                ++idx;
                continue;
            }
            values[idx] += c;
        }
        return values;
    };

    /**
     * clearFilters: remove all selected filter options
     */
    var clearFilters = function(form) {

        // If no form has been specified, find the first one
        if (undefined === form) {
            form = $('body').find('form.filter-form').first();
        }

        // Temporarily disable auto-submit
        form.data('noAutoSubmit', 1);

        // Clear text filters
        form.find('.text-filter').val('');

        // Clear option/location filters
        form.find('.options-filter, .location-filter').each(function() {
            var $this = $(this);
            if (this.tagName.toLowerCase() == 'select') {
                $this.val('');
                if ($this.hasClass('groupedopts-filter-widget') &&
                    $this.groupedopts('instance')) {
                    $this.groupedopts('refresh');
                } else
                if ($this.hasClass('multiselect-filter-widget') &&
                    $this.multiselect('instance')) {
                    $this.multiselect('refresh');
                }
            } else {
                var id = $this.attr('id');
                $("input[name='" + id + "']:checked").each(function() {
                    $(this).click();
                });
            }
            if ($this.hasClass('location-filter')) {
                hierarchical_location_change(this);
            }
        });

        // Clear map filters
        form.find('.map-filter').each(function() {
            var $this = $(this);
            $this.val('');
            // Ensure that the button is off (so polygon removed)
            var widget_name = $this.attr('id'),
                map_id = widget_name + '-map',
                s3 = S3.gis.maps[map_id].s3,
                polygonButton = s3.polygonButton;
            if (polygonButton.getIconClass() == 'drawpolygonclear-off') {
                polygonButton.items[0].btnEl.dom.click();
            }
        });

        // Clear range filters
        form.find('.range-filter-input').val('');

        // Clear date filters
        form.find('.date-filter-input').each(function() {
            var $this = $(this);
            $this.calendarWidget('clear');
            var widget_name = $this.attr('id');
            var widget = $('#' + widget_name.slice(0, -3));
            widget.find('.range-picker').each(function() {
                $(this).trigger('clear');
            });
        });

        // Clear hierarchy filters
        form.find('.hierarchy-filter').each(function() {
            var $this = $(this);
            if ($this.hasClass('s3-cascade-select')) {
                $this.cascadeSelect('reset');
            } else {
                $this.hierarchicalopts('reset');
            }
        });

        // Clear age filters
        form.find('.age-filter-input').val('');

        // Other widgets go here

        // Clear filter manager
        form.find('.filter-manager-widget').each(function() {
            var that = $(this);
            if (that.filtermanager !== undefined) {
                that.filtermanager('clear');
            }
        });

        // Re-enable auto-submit
        form.data('noAutoSubmit', 0);

        // Fire optionChanged event
        form.trigger('optionChanged');
    };

    /**
     * Regex for the operator in a filter expression
     */
    var FILTEROP = /__(?!link\.)([a-z_]+)$/;

    /**
     * getCurrentFilters: retrieve all current filters
     *
     * - returns: [[key, value], [key, value], ...]
     *            to update a URL query like &key=value,
     *            a value of null means to remove that key from the URL query.
     *
     * Note: empty widgets must push [key, null] anyway, so
     *       that existing queries for 'key' get removed!
     */
    var getCurrentFilters = function(form) {

        // Fall back to first filter form in page
        if (typeof form == 'undefined') {
            form = $('body').find('form.filter-form').first();
        }

        var i,
            id,
            queries = [],
            $this,
            urlVar,
            value,
            values,
            subString,
            operator;

        // Text widgets
        form.find('.text-filter:visible').each(function() {
            $this = $(this);
            id = $this.attr('id');
            urlVar = $('#' + id + '-data').val();
            value = $this.val().trim();
            if (value) {
                values = value.split(' ');
                var match = $this.data('match'),
                    quoted,
                    anyValue = [];
                for (i=0; i < values.length; i++) {
                    subString = $.trim(values[i]);
                    if (subString === "") {
                        continue;
                    }
                    quoted = quoteValue('*' + subString + '*');
                    if (match == "any") {
                        anyValue.push(quoted);
                    } else {
                        queries.push([urlVar, quoted]);
                    }
                }
                if (match == "any") {
                    queries.push([urlVar, anyValue.join(',')]);
                }
            } else {
                queries.push([urlVar, null]);
            }
        });

        // Options widgets
        form.find('.s3-groupedopts-widget:visible').prev(
                  '.options-filter.groupedopts-filter-widget')
        .add(
        form.find('.ui-multiselect:visible').prev(
                  '.options-filter.multiselect-filter-widget'))
        .add(
        form.find('.options-filter:visible,' +
                  '.options-filter.multiselect-filter-widget.active' /*+
                  ',.options-filter.multiselect-filter-bootstrap.active'*/))
        .each(function() {
            $this = $(this);
            id = $this.attr('id');
            urlVar = $('#' + id + '-data').val();

            // Adjust urlVar for user-selected operator
            operator = $("input:radio[name='" + id + "_filter']:checked").val();
            switch(operator) {
                case 'any':
                    urlVar = urlVar.replace(/__contains$|__belongs$/, '__anyof');
                    break;
                case 'all':
                    urlVar = urlVar.replace(/__anyof$|__belongs$/, '__contains');
                    break;
                default:
                    break;
            }

            if (this.tagName.toLowerCase() == 'select') {
                // Standard SELECT
                value = '';
                values = $this.val();
                if (values) {
                    if (!(values instanceof Array)) {
                        // multiple=False, but a single option may contain multiple
                        values = values.split(',');
                    }
                    var v;
                    for (i=0; i < values.length; i++) {
                        v = quoteValue(values[i]);
                        if (value === '') {
                            value = v;
                        } else {
                            value = value + ',' + v;
                        }
                    }
                }
            } else {
                // Checkboxes widget
                value = '';
                $("input[name='" + id + "']:checked").each(function() {
                    if (value === '') {
                        value = quoteValue($(this).val());
                    } else {
                        value = value + ',' + quoteValue($(this).val());
                    }
                });
            }
            if ((value === '') || (value == '*')) {
                queries.push([urlVar, null]);
            } else {
                queries.push([urlVar, value]);
            }
        });

        // Map widgets
        form.find('.map-filter').each(function() {

            $this = $(this);
            id = $this.attr('id');
            urlVar = $('#' + id + '-data').val();
            value = $this.val();

            if (value) {
                queries.push([urlVar, value]);
            } else {
                queries.push([urlVar, null]);
            }
        });

        // Numerical range widgets -- each widget has two inputs.
        form.find('.range-filter-input:visible').each(function() {

            $this = $(this);
            id = $this.attr('id');
            urlVar = $('#' + id + '-data').val();
            value = $this.val();

            if (value) {
                queries.push([urlVar, value]);
            } else {
                queries.push([urlVar, null]);
            }
        });

        // Date(time) range widgets -- each widget has two inputs.
        form.find('.date-filter-input:visible').each(function() {

            $this = $(this);
            id = $this.attr('id');
            urlVar = $('#' + id + '-data').val();
            value = $this.val();

            operator = id.split('-').pop();

            // Helper to convert a JS Date into an ISO format string
            var isoFormat;
            if ($this.hasClass('datetimepicker')) {
                isoFormat = function(dt) {
                    return dt.getFullYear() + '-' +
                           ('0' + (dt.getMonth() + 1)).slice(-2) + '-' +
                           ('0' + dt.getDate()).slice(-2) + 'T' +
                           ('0' + dt.getHours()).slice(-2) + ':' +
                           ('0' + dt.getMinutes()).slice(-2) + ':' +
                           ('0' + dt.getSeconds()).slice(-2);
                };
            } else {
                isoFormat = function(dt) {
                    return dt.getFullYear() + '-' +
                           ('0' + (dt.getMonth() + 1)).slice(-2) + '-' +
                           ('0' + dt.getDate()).slice(-2);
                };
            }

            if (value) {
                var end = false;
                if (operator == 'le') {
                    end = true;
                }
                var jsDate = $this.calendarWidget('getJSDate', end),
                    urlValue = isoFormat(jsDate);
                if (end && $this.hasClass('end_date')) {
                    // end_date
                    var selector = urlVar.replace(FILTEROP, '');
                    // @ToDo: filterURL should AND multiple $filter into 1 (will be required when we have multiple $filter in a single page)
                    queries.push(['$filter', '(' + selector + ' ' + operator + ' "' + urlValue + '") or (' + selector + ' eq None)']);
                } else {
                    // Single field or start_date
                    queries.push([urlVar, urlValue]);
                }
            } else {
                // Remove the filter (explicit null)
                queries.push([urlVar, null]);
            }
        });

        // Location widgets
        form.find('.s3-groupedopts-widget:visible').prev(
                  '.location-filter.groupedopts-filter-widget')
        .add(
        form.find('.ui-multiselect:visible').prev(
                  '.location-filter.multiselect-filter-widget')
        .add(
        form.find('.location-filter:visible,' +
                  '.location-filter.multiselect-filter-widget.active' /*+
          ',.location-filter.multiselect-filter-bootstrap.active'*/)))
        .each(function() {

            $this = $(this);
            id = $this.attr('id');
            urlVar = $('#' + id + '-data').val();
            value = '';

            //operator = $("input:radio[name='" + id + "_filter']:checked").val();

            if (this.tagName.toLowerCase() == 'select') {
                // Standard SELECT
                values = $(this).val();
                var v;
                if (values) {
                    for (i=0; i < values.length; i++) {
                        v = quoteValue(values[i]);
                        if (value === '') {
                            value = v;
                        } else {
                            value = value + ',' + v;
                        }
                    }
                }
            } else {
                // Checkboxes widget
                $("input[name='" + id + "']:checked").each(function() {
                    if (value === '') {
                        value = quoteValue($(this).val());
                    } else {
                        value = value + ',' + quoteValue($(this).val());
                    }
                });
            }
            if (value === '') {
                queries.push([urlVar, null]);
            } else {
                queries.push([urlVar, value]);
            }
        });

        // Hierarchy filter (experimental)
        form.find('.hierarchy-filter:visible').each(function() {

            $this = $(this);
            id = $this.attr('id');
            urlVar = $('#' + id + '-data').val();
            value = '';

            if ($this.hasClass('s3-cascade-select')) {
                values = $this.cascadeSelect('get');
            } else {
                values = $this.hierarchicalopts('get');
            }
            if (values) {
                for (i=0; i < values.length; i++) {
                    if (value === '') {
                        value += values[i];
                    } else {
                        value = value + ',' + values[i];
                    }
                }
            }
            if (value === '') {
                queries.push([urlVar, null]);
            } else {
                queries.push([urlVar, value]);
            }
        });

        // Age filter widgets -- each widget has two inputs.
        form.find('.age-filter-input:visible').each(function() {

            $this = $(this);
            id = $this.attr('id');
            urlVar = $('#' + id + '-data').val();
            value = $this.val();

            var years = value - 0;
            if (value && !isNaN(years)) {
                var m = urlVar.match(FILTEROP);
                if (m && m[1] == 'gt') {
                    // Age in years is the same until one day before
                    // the next birthday, so must add one year here:
                    years += 1;
                }
                // Convert years (ago) into a date
                var dt = new Date();
                dt.setYear(dt.getFullYear() - years);
                // Convert to ISO format
                dt = dt.getFullYear() + '-' +
                       ('0' + (dt.getMonth() + 1)).slice(-2) + '-' +
                       ('0' + dt.getDate()).slice(-2);
                queries.push([urlVar, dt]);
            } else {
                queries.push([urlVar, null]);
            }
        });

        // Value filter widgets
        $('.value-filter:visible', form).each(function() {

            $this = $(this);
            id = $this.attr('id');
            urlVar = $('#' + id + '-data').val();

            if ($this.prop('checked')) {
                queries.push([urlVar, 'None']);
            } else {
                queries.push([urlVar, null]);
            }
        });

        // Other widgets go here...

        // return queries to caller
        return queries;
    };

    // Pass to global scope to be called by s3.ui.pivottable.js
    S3.search.getCurrentFilters = getCurrentFilters;

    /**
     * setCurrentFilters: populate filter form widgets from an array of URL queries
     */
    var setCurrentFilters = function(form, queries) {

        if (undefined === form) {
            form = $('body').find('form.filter-form').first();
        }

        // Temporarily disable auto-submit
        form.data('noAutoSubmit', 1);

        var expression,
            i,
            id,
            q = {},
            len,
            $this,
            value,
            values;

        for (i=0, len=queries.length; i < len; i++) {
            var query = queries[i];
            expression = query[0];
            if (typeof query[1] == 'string') {
                values = parseValue(query[1]);
            } else {
                values = query[1];
            }
            if (q.hasOwnProperty(expression)) {
                q[expression] = q[expression].concat(values);
            } else {
                q[expression] = values;
            }
        }

        // Text widgets
        form.find('.text-filter').each(function() {
            $this = $(this);
            id = $this.attr('id');
            expression = $('#' + id + '-data').val();
            if (q.hasOwnProperty(expression)) {
                if (!$this.is(':visible') && !$this.hasClass('active')) {
                    toggleAdvanced(form);
                }
                values = q[expression];
                value = '';
                if (values) {
                    var v;
                    for (i=0, len=values.length; i < len; i++) {
                        v = values[i];
                        if (!v) {
                            continue;
                        }
                        if (i > 0) {
                            value += ' ';
                        }
                        if (v[0] == '*') {
                            v = v.slice(1);
                        }
                        if (v.slice(-1) == '*') {
                            v = v.slice(0, -1);
                        }
                        value += v;
                    }
                }
                $this.val(value);
            }
        });

        // Options widgets
        form.find('.options-filter').each(function() {
            $this = $(this);
            id = $this.attr('id');
            expression = $('#' + id + '-data').val();
            var operator = $('input:radio[name="' + id + '_filter"]:checked').val();
            if (this.tagName && this.tagName.toLowerCase() == 'select') {
                var refresh = false,
                    selector = expression.replace(FILTEROP, '');
                if (q.hasOwnProperty(selector + '__eq')) {
                    values = q[selector + '__eq'];
                    refresh = true;
                } else if (q.hasOwnProperty(selector)) {
                    values = q[selector];
                    refresh = true;
                } else if (q.hasOwnProperty(expression)) {
                    values = q[expression];
                    refresh = true;
                } else if (operator == 'any' || operator == 'all') {
                    if (q.hasOwnProperty(selector + '__anyof')) {
                        values = q[selector + '__anyof'];
                        refresh = true;
                        $('input:radio[name="' + id + '_filter"][value="any"]')
                         .prop('checked', true);
                    } else if (q.hasOwnProperty(selector + '__contains')) {
                        values = q[selector + '__contains'];
                        refresh = true;
                        $('input:radio[name="' + id + '_filter"][value="all"]')
                         .prop('checked', true);
                    }
                }
                if (refresh) {
                    if (!$this.is(':visible') && !$this.hasClass('active')) {
                        toggleAdvanced(form);
                    }
                    $this.val(values);
                    if ($this.hasClass('groupedopts-filter-widget') &&
                        $this.groupedopts('instance')) {
                        $this.groupedopts('refresh');
                    } else
                    if ($this.hasClass('multiselect-filter-widget') &&
                        $this.multiselect('instance')) {
                        $this.multiselect('refresh');
                    }
                }
            }
        });

        // Map widgets
        form.find('.map-filter').each(function() {
            $this = $(this);
            id = $this.attr('id');
            expression = $('#' + id + '-data').val();
            if (q.hasOwnProperty(expression)) {
                if (!$this.is(':visible') && !$this.hasClass('active')) {
                    toggleAdvanced(form);
                }
                values = q[expression];
                var map_id;
                if (values) {
                    $this.val(values[0]);
                    map_id = id + '-map';
                    // Display the Polygon
                    S3.gis.maps[map_id].s3.polygonButtonLoaded();
                } else {
                    $this.val('');
                    map_id = id + '-map';
                    // Hide the Polygon
                    S3.gis.maps[map_id].s3.layerRefreshed();
                }
            }
        });

        // Numerical range widgets
        form.find('.range-filter-input').each(function() {
            $this = $(this);
            id = $this.attr('id');
            expression = $('#' + id + '-data').val();
            if (q.hasOwnProperty(expression)) {
                if (!$this.is(':visible') && !$this.hasClass('active')) {
                    toggleAdvanced(form);
                }
                values = q[expression];
                if (values) {
                    $this.val(values[0]);
                } else {
                    $this.val('');
                }
            }
        });

        // Date(time) range widgets
        form.find('.date-filter-input').each(function() {

            var $this = $(this),
                expression = $('#' + $this.attr('id') + '-data').val(),
                selector = expression.replace(FILTEROP, ''),
                values = false;

            if (q.hasOwnProperty(expression)) {
                values = q[expression];
            } else if (q.hasOwnProperty(selector)) {
                // Match isolated selector if no operator-specific expression present
                values = q[selector];
            }
            if (values !== false) {
                if (!$this.is(':visible') && !$this.hasClass('active')) {
                    toggleAdvanced(form);
                }
                if (values) {
                    // Add the 'T' separator to the date string so it
                    // can be parsed by the Date constructor:
                    var dtString = values[0].replace(' ', 'T');
                    $this.calendarWidget('setJSDate', new Date(dtString));
                } else {
                    $this.calendarWidget('clear');
                }
                // Ensure any range-picker is updated with new value
                $this.trigger('change');
            }
        });

        // Location filter widget
        form.find('.location-filter').each(function() {
            $this = $(this);
            id = $this.attr('id');
            expression = $('#' + id + '-data').val();
            var operator = $('input:radio[name="' + id + '_filter"]:checked').val();
            if (this.tagName && this.tagName.toLowerCase() == 'select') {
                var refresh = false;
                if (q.hasOwnProperty(expression)) {
                    values = q[expression];
                    refresh = true;
                } else
                if (operator == 'any' || operator == 'all') {
                    var selector = expression.replace(FILTEROP, '');
                    if (q.hasOwnProperty(selector + '__anyof')) {
                        values = q[selector + '__anyof'];
                        refresh = true;
                        $('input:radio[name="' + id + '_filter"][value="any"]')
                         .prop('checked', true);
                    } else if (q.hasOwnProperty(selector + '__contains')) {
                        values = q[selector + '__contains'];
                        refresh = true;
                        $('input:radio[name="' + id + '_filter"][value="all"]')
                         .prop('checked', true);
                    }
                }
                if (refresh) {
                    if (!$this.is(':visible') && !$this.hasClass('active')) {
                        toggleAdvanced(form);
                    }
                    $this.val(values);
                    if ($this.hasClass('groupedopts-filter-widget') &&
                        $this.groupedopts('instance')) {
                        $this.groupedopts('refresh');
                    } else
                    if ($this.hasClass('multiselect-filter-widget') &&
                        $this.multiselect('instance')) {
                        $this.multiselect('refresh');
                    }
                    hierarchical_location_change(this);
                }
            }
        });

        // Hierarchy filter widget (experimental)
        form.find('.hierarchy-filter:visible').each(function() {
            $this = $(this);
            id = $this.attr('id');
            expression = $('#' + id + '-data').val();
            if (q.hasOwnProperty(expression)) {
                if (!$this.is(':visible') && !$this.hasClass('active')) {
                    toggleAdvanced(form);
                }
                values = q[expression];
                if ($this.hasClass('s3-cascade-select')) {
                    $this.cascadeSelect('set', values);
                } else {
                    $this.hierarchicalopts('set', values);
                }
            }
        });

        // Re-enable auto-submit
        form.data('noAutoSubmit', 0);

        // Fire optionChanged event
        form.trigger('optionChanged');
    };
    // Pass to gloabl scope to be called from Filter Manager
    S3.search.setCurrentFilters = setCurrentFilters;

    /**
     * Update a variable in the query part of the filter-submit URL
     */
    var updateFilterSubmitURL = function(form, name, value) {

        var submit_url = $('#' + form).find('input.filter-submit-url[type="hidden"]');

        if (submit_url.length) {

            submit_url = submit_url.first();

            var url = $(submit_url).val();

            var url_parts = url.split('?'),
                update_url,
                query,
                vars = [];

            if (url_parts.length > 1) {

                var qstr = url_parts[1];
                var a = qstr.split('&'), b, c;
                for (var i=0; i<a.length; i++) {
                    b = a[i].split('=');
                    if (b.length > 1) {
                        c = decodeURIComponent(b[0]);
                        if (c != name) {
                            vars.push(b[0] + '=' + b[1]);
                        }
                    }
                }
                vars.push(name + '=' + value);

                query = vars.join('&');
                update_url = url_parts[0];
                if (query) {
                    update_url = update_url + '?' + query;
                }
            } else {
                update_url = url + '?' + name + '=' + value;
            }
            $(submit_url).val(update_url);
        }
    };

    /**
     * filterURL: update filters in a URL
     *
     * - url: URL as string
     * - queries: [[key, value], [key, value], ...]
     *
     * Note: a value of null means to remove that key from the URL
     *       query
     * Note: Each key can appear multiple times - remove/update will
     *       affect all occurences of that key in the URL, and update
     *       overrides remove.
     */
    var filterURL = function(url, queries) {

        if (undefined === queries) {
            queries = getCurrentFilters();
        }

        var url_parts = url.split('?'),
            update = {},
            reset = {},
            i, len, q, k, v;

        for (i=0, len=queries.length; i < len; i++) {
            q = queries[i];
            k = q[0];
            v = q[1];
            if (v === null) {
                if (!update.hasOwnProperty(k)) {
                    reset[k] = true;
                }
            } else {
                if (reset.hasOwnProperty(k)) {
                    reset[k] = false;
                }
                update[k] = true;
            }
        }

        var query = [];

        if (S3.search.stripFilters == 1) {
            // Strip existing URL filters
        } else if (url_parts.length > 1) {
            // Keep existing URL filters
            var qstr = url_parts[1];
            var url_vars = qstr.split('&');

            for (i=0, len=url_vars.length; i < len; i++) {
                q = url_vars[i].split('=');
                if (q.length > 1) {
                    k = decodeURIComponent(q[0]);
                    if (reset[k] || update[k]) {
                        continue;
                    } else {
                        query.push(url_vars[i]);
                    }
                }
            }
        }

        for (i=0, len=queries.length; i < len; i++) {
            q = queries[i];
            k = q[0];
            v = q[1];
            if (update[k]) {
                query.push(k + '=' + encodeURIComponent(v));
            }
        }

        var url_query = query.join('&'),
            filtered_url = url_parts[0];
        if (url_query) {
            filtered_url = filtered_url + '?' + url_query;
        }
        return filtered_url;
    };

    // Pass to global scope to be called by S3.gis.refreshLayer()
    S3.search.filterURL = filterURL;

    /**
     * updateOptions: Update the options of all filter widgets
     */
    var updateOptions = function(options) {

        var filter_id;
        for (filter_id in options) {
            var widget = $('#' + filter_id);

            if (widget.length) {
                var newopts = options[filter_id];

                // OptionsFilter
                if (widget.hasClass('options-filter')) {
                    if (widget[0].tagName.toLowerCase() == 'select') {
                        // Standard SELECT
                        // (which could be the hidden one in an s3.ui.groupedopts.widget.js)

                        var noopt = widget.siblings('.no-options-available');

                        // Update HTML
                        if (newopts.hasOwnProperty('empty')) {

                            // Remove options
                            widget.html('');

                            // Ensure the widget is hidden
                            if (widget.hasClass('multiselect-filter-widget') &&
                                widget.multiselect('instance')) {
                                widget.multiselect('refresh');
                                widget.multiselect('instance').button.hide();
                            } else if (widget.hasClass('groupedopts-filter-widget') &&
                                widget.groupedopts('instance')) {
                                widget.groupedopts('refresh');
                            } else {
                                widget.hide();
                            }

                            // Show the no-opts
                            if (noopt.length) {
                                noopt.html(newopts.empty);
                                noopt.removeClass('hide').show();
                            }

                        } else {

                            var selected = widget.val(),
                                s=[], opts='', group, item, value, label, tooltip, i, len;

                            if (newopts.hasOwnProperty('groups')) {
                                for (i=0, len=newopts.groups.length; i < len; i++) {
                                    group = newopts.groups[i];
                                    if (group.label) {
                                        opts += '<optgroup label="' + group.label + '">';
                                    }
                                    for (var j=0, lenj=group.items.length; j < lenj; j++) {
                                        item = group.items[j];
                                        value = item[0].toString();
                                        if (selected && $.inArray(value, selected) >= 0) {
                                            s.push(value);
                                        }
                                        opts += '<option value="' + value + '"';
                                        tooltip = item[3];
                                        if (tooltip) {
                                            opts += ' title="' + tooltip + '"';
                                        }
                                        label = item[1];
                                        opts += '>' + label + '</option>';
                                    }
                                    if (group.label) {
                                        opts += '</optgroup>';
                                    }
                                }

                            } else {
                                for (i=0, len=newopts.length; i < len; i++) {
                                    item = newopts[i];
                                    value = item[0];
                                    if (null === value) {
                                        value = 'None';
                                    } else {
                                        value = value.toString();
                                    }
                                    label = item[1];
                                    if (selected && $.inArray(value, selected) >= 0) {
                                        s.push(value);
                                    }
                                    opts += '<option value="' + value + '">' + label + '</option>';
                                }
                            }
                            widget.html(opts);

                            // Update SELECTed value
                            if (s) {
                                widget.val(s);
                            }

                            // Hide the no-opts
                            if (noopt.length) {
                                noopt.hide();
                            }
                            // Refresh UI widgets
                            if (widget.hasClass('groupedopts-filter-widget') &&
                                widget.groupedopts('instance')) {
                                widget.groupedopts('refresh');
                            } else if (widget.hasClass('multiselect-filter-widget') &&
                                widget.multiselect('instance')) {
                                widget.multiselect('refresh');
                                widget.multiselect('instance').button.show();
                            } else {
                                widget.removeClass('hide').show();
                            }
                        }

                    } else {
                        // other widget types of options filter
                    }

                } else if (widget.hasClass('date-filter')) {
                    var min = newopts.min,
                        max = newopts.max;
                    $('#' + filter_id + '-ge').calendarWidget('instance')
                                              .option('minDateTime', min)
                                              .option('maxDateTime', max)
                                              .refresh();
                    $('#' + filter_id + '-le').calendarWidget('instance')
                                              .option('minDateTime', min)
                                              .option('maxDateTime', max)
                                              .refresh();
                    widget.find('.range-picker')
                          .trigger('resize', [min, max, newopts.ts]);
                } else {
                    // @todo: other filter types (e.g. S3LocationFilter)
                }
            }
        }
    };

    /**
     * ajaxUpdateOptions: Ajax-update the options in a filter form
     *
     * In global scope as called from s3.popup.js
     * - indirectly now, as goes via $('.filter-form').trigger('dataChanged', refresh);
     */
    S3.search.ajaxUpdateOptions = function(form, callback) {

        // Ajax-load the item
        var $form = $(form);
        var ajaxurl = $form.find('input.filter-ajax-url');
        if (ajaxurl.length) {
            ajaxurl = $(ajaxurl[0]).val();
        }
        $.ajax({
            'url': ajaxurl,
            'dataType': 'json'
        }).done(function(data) {
            // Temporarily disable auto-submit
            $form.data('noAutoSubmit', 1);
            updateOptions(data);
            // Re-enable
            $form.data('noAutoSubmit', 0);
            if (callback) {
                callback.apply();
            }
        }).fail(function(jqXHR, textStatus, errorThrown) {
            var msg;
            if (errorThrown == 'UNAUTHORIZED') {
                msg = i18n.gis_requires_login;
            } else {
                msg = jqXHR.responseText;
            }
            console.log(msg);
        });
    };

    /**
     * Update export format URLs in a datatable
     *
     * @param {jQuery} dt - the datatable
     * @param {object} queries - the filter queries
     */
    var updateFormatURLs = function(dt, queries) {

        $('#' + dt[0].id).closest('.dt-wrapper')
                         .find('.dt-export')
                         .each(function() {
            var $this = $(this);
            var url = $this.data('url');
            if (url) {
                $this.data('url', filterURL(url, queries));
            }
        });
    };

    /**
     * updatePendingTargets: update all targets which were hidden during
     *                       last filter-submit, reload page if required
     */
    var updatePendingTargets = function(form) {

        var url = $('#' + form).find('input.filter-submit-url[type="hidden"]')
                               .first().val(),
            targets = pendingTargets[form],
            target_id,
            target_data,
            needs_reload,
            queries,
            t,
            visible;

        // Clear the list
        pendingTargets[form] = {};

        // Inspect the targets
        for (target_id in targets) {

            t = $('#' + target_id);

            if (!t.is(':visible')) {
                visible = false;
            } else {
                visible = true;
            }

            target_data = targets[target_id];

            needs_reload = target_data.needs_reload;
            if (visible) {
                if (needs_reload) {
                    // reload immediately
                    queries = getCurrentFilters($('#' + form));
                    url = filterURL(url, queries);
                    window.location.href = url;
                }
            } else {
                // re-schedule for later
                pendingTargets[form][target_id] = target_data;
            }
        }

        // Ajax-update all visible targets
        for (target_id in targets) {
            t = $('#' + target_id);
            if (!t.is(':visible')) {
                continue;
            }
            target_data = targets[target_id];
            t = $('#' + target_id);
            if (t.hasClass('dataTable')) {
                // Refresh Data
                var dt = t.dataTable(),
                    dtAjaxURL = target_data.ajaxurl;
                dt.fnReloadAjax(dtAjaxURL);
                updateFormatURLs(dt, queries);
                $('#' + dt[0].id + '_dataTable_filterURL').val(dtAjaxURL);
            } else if (t.hasClass('dl')) {
                t.datalist('ajaxReload', target_data.queries);
            } else if (t.hasClass('map_wrapper')) {
                S3.gis.refreshLayer('search_results');
            } else if (t.hasClass('gi-container')) {
                t.groupedItems('reload', null, target_data.queries);
            } else if (t.hasClass('pt-container')) {
                t.pivottable('reload', null, target_data.queries);
            } else if (t.hasClass('tp-container')) {
                t.timeplot('reload', null, target_data.queries);
            } else if (t.hasClass('s3-organizer')) {
                t.organizer('reload');
            }
        }
    };

    /**
     * filterFormAutoSubmit: configure a filter form for automatic
     *                       submission after option change
     * Parameters:
     * form_id: the form element ID
     * timeout: timeout in milliseconds
     */
    S3.search.filterFormAutoSubmit = function(form_id, timeout) {

        var filter_form = $('#' + form_id);
        if (!filter_form.length || !timeout) {
            return;
        }
        filter_form.on('optionChanged', function() {
            var $this = $(this);
            if ($this.data('noAutoSubmit')) {
                // Event temporarily disabled
                return;
            }
            var timer = $this.data('autoSubmitTimeout');
            if (timer) {
                clearTimeout(timer);
            }
            timer = setTimeout(function() {
                filterSubmit($this);
            }, timeout);
            $this.data('autoSubmitTimeout', timer);
        });
    };

    /**
     * Check that Map JS is Loaded
     * - e.g. used if a tab containing a Map is unhidden
     */
    var jsLoaded = function() {
        var dfd = new jQuery.Deferred();

        // Test every half-second
        setTimeout(function working() {
            if (S3.gis.maps != undefined) {
                dfd.resolve('loaded');
            } else if (dfd.state() === 'pending') {
                // Notify progress
                dfd.notify('waiting for JS to load...');
                // Loop
                setTimeout(working, 500);
            } else {
                // Failed!?
            }
        }, 1);

        // Return the Promise so caller can't change the Deferred
        return dfd.promise();
    };

    /**
     * Set up an initially hidden widget
     * - e.g. for S3Summary page, or similar
     *
     * Parameters:
     * form - {String} ID of the filter form
     * widget - {String} ID of the widget
     * queries - key, value tuples
     */
    var setup_hidden_widget = function(form, widget, queries) {
        var ajaxurl;
        if (undefined === queries) {
            queries = getCurrentFilters($('#' + form));
        }
        if (!pendingTargets.hasOwnProperty(form)) {
            pendingTargets[form] = {};
        }
        if (pendingTargets[form].hasOwnProperty(widget)) {
            // already scheduled
            return;
        }
        var t = $('#' + widget);
        if (t.hasClass('dl') ||
            t.hasClass('gi-container') ||
            t.hasClass('pt-container') ||
            t.hasClass('tp-container') ||
            t.hasClass('map_wrapper') ||
            t.hasClass('s3-organizer')) {
            // These targets handle their AjaxURL themselves
            ajaxurl = null;
        } else if (t.hasClass('dataTable')) {
            // Lookup and filter the AjaxURL
            var config = $('input#' + widget + '_configurations');
            if (config.length) {
                var settings = JSON.parse($(config).val());
                ajaxurl = settings.ajaxUrl;
                if (typeof ajaxurl != 'undefined') {
                    ajaxurl = filterURL(ajaxurl, queries);
                } else {
                    return;
                }
            }
        } else {
            return;
        }
        pendingTargets[form][widget] = {
            needs_reload: false,
            ajaxurl: ajaxurl,
            queries: queries
        };
    };

    // Pass to global scope to be called by external scripts (e.g. WACOP)
    S3.search.setup_hidden_widget = setup_hidden_widget;

    /**
     * Helper method to
     *
     * - re-calculate the column width in responsive data tables, or
     * - adjust the top scrollbar width in non-responsive data tables
     *
     * ...after unhiding them on a summary tab
     *
     * @param {jQuery} datatable - the datatable
     */
    var recalcResponsive = function(datatable) {

        var dt = $(datatable);

        if (dt.hasClass('responsive')) {
            var instance = dt.DataTable();
            if (instance && instance.responsive) {
                instance.responsive.recalc();
            }
        } else if (dt.hasClass('doublescroll')) {
            try {
                dt.dataTableS3('doubleScroll');
            } catch(e) {
                // pass
            }
        }
    };

    /**
     * Unhide an initially hidden section
     * - e.g. for S3Summary page, or similar
     *
     * Parameters:
     * form - {String} ID of the filter form
     * section - {jQuery} the object just unhidden
     */
    var unhide_section = function(form, section) {
        // Find any Map widgets in this section
        var maps = section.find('.map_wrapper');
        var maps_len = maps.length;
        if (maps_len) {
            // Check that Maps JS is Loaded
            $.when(jsLoaded()).then(
                function() {
                    // Success: Instantiate Maps
                    var gis = S3.gis;
                    for (var i=0; i < maps_len; i++) {
                        var map_id = maps[i].attributes.id.value;
                        if (undefined === gis.maps[map_id]) {
                            // Instantiate the map (can't be done when the DIV is hidden)
                            var options = gis.options[map_id];
                            gis.show_map(map_id, options);
                        }
                    }
                    // Update all just-unhidden widgets which have pending updates
                    updatePendingTargets(form);
                },
                function(status) {
                    // Failed
                    s3_debug(status);
                },
                function(status) {
                    // Progress
                    s3_debug(status);
                }
            );
        } else {
            // Update all just-unhidden widgets which have pending updates
            updatePendingTargets(form);
        }
        // Setup any Responsive dataTables
        section.find('table.dataTable.display')
               .each(function() {
            recalcResponsive(this);
        });
    };

    // Pass to global scope to be called by external scripts (e.g. WACOP)
    S3.search.unhide_section = unhide_section;

    /**
     * Set up the (jQueryUI) Tabs for an S3Summary page
     * - in global scope as called from outside
     *
     * Parameters:
     * form - {String} ID of the filter form
     * active_tab - {Integer} Which Section is active to start with
     * pending - {String} comma-separated list of widget IDs which are initially hidden
     */
    S3.search.summary_tabs = function(form, active_tab, pending) {

        // Schedule initially hidden widgets to Ajax-load their data
        // layers, required here because otherwise this happens only
        // during filter-submit, but the user could also simply switch
        // tabs without prior filter-submit; list of initially hidden
        // widgets with ajax-init option is provided by the page
        // renderer (S3Summary.summary()).
        if (pending) {
            var queries = getCurrentFilters($('#' + form)),
                widget,
                targets = pending.split(',');
            for (var i=0, len=targets.length; i < len; i++) {
                widget = targets[i];
                setup_hidden_widget(form, widget, queries);
            }
        }

        if (active_tab != undefined) {
            // Initialise jQueryUI Tabs
            $('#summary-tabs').tabs({
                active: active_tab,
                activate: function(event, ui) {
                    var newPanel = $(ui.newPanel);
                    // Unhide the section (.ui-tab's display: block overrides anyway but hey ;)
                    newPanel.removeClass('hide');
                    // A New Tab has been selected
                    if (ui.newTab.length) {
                        // Update the Filter Query URL to show which tab is active
                        updateFilterSubmitURL(form, 't', $(ui.newTab).index());
                    }
                    unhide_section(form, newPanel);
                }
            }).css({visibility: 'visible'});
            // Activate not called? Unhide initial section anyway:
            $('.ui-tabs-panel[aria-hidden="false"]').first()
                                                    .removeClass('hide')
                                                    .find('table.dataTable.display')
                                                    .each(function() {
                                                        recalcResponsive(this);
                                                    });
        } else {
            // Unhide initial section anyway:
            $('#summary-tabs').css({visibility: 'visible'})
                              .find('table.dataTable.display')
                              .each(function() {
                                recalcResponsive(this);
                              });
        }
    };

    /**
     * Initialise Maps for an S3Summary page
     * - in global scope as called from callback to Map Loader
     */
    S3.search.summary_maps = function(form) {
        // Find any Map widgets in the common section or initially active tab
        var maps = $('#summary-common, #summary-sections').find('.map_wrapper');
        for (var i=0; i < maps.length; i++) {
            var map = maps[i];
            if (!map.hidden) {
                var gis = S3.gis;
                var map_id = map.attributes.id.value;
                if (undefined === gis.maps[map_id]) {
                    // Instantiate the map (can't be done when the DIV is hidden)
                    var options = gis.options[map_id];
                    if (undefined != options) {
                        gis.show_map(map_id, options);
                        // Get the current Filters
                        var queries = getCurrentFilters($('#' + form));
                        // Load the layer
                        gis.refreshLayer('search_results', queries);
                    }
                }
            }
        }
    };

    /**
     * Initialise Map for an S3Map page
     * - in global scope as called from callback to Map Loader
     */
    S3.search.s3map = function(map_id) {
        // Instantiate the map
        var gis = S3.gis;
        if (map_id === undefined) {
            map_id = 'default_map';
        }
        var options = gis.options[map_id];
        gis.show_map(map_id, options);
        // Get the current Filters
        // @todo: select a filter form
        var queries = getCurrentFilters();
        // Load the layer
        gis.refreshLayer('search_results', queries);
    };

    /**
     * A Hierarchical Location Filter has changed
     */
    var hierarchical_location_change = function(widget) {
        var name = widget.name,
            base = name.slice(0, -1),
            level = parseInt(name.slice(-1)),
            $widget = $('#' + name),
            values = $widget.val(),
            next_widget,
            select,
            l;
        if (!values) {
            // Clear the values from all subsequent widgets
            for (l = level + 1; l <= 5; l++) {
                select = $('#' + base + l);
                if (select.length) {
                    select.html('');
                    if (select.hasClass('groupedopts-filter-widget') &&
                        select.groupedopts('instance')) {
                        try {
                            select.groupedopts('refresh');
                        } catch(e) { }
                    } else
                    if (select.hasClass('multiselect-filter-widget') &&
                        select.multiselect('instance')) {
                        select.multiselect('refresh');
                    }
                }
            }
            // Hide all subsequent widgets
            // Hide the next widget down
            next_widget = $widget.next('.ui-multiselect').next('.location-filter').next('.ui-multiselect');
            if (next_widget.length) {
                next_widget.hide();
                // Hide the next widget down
                next_widget = next_widget.next('.location-filter').next('.ui-multiselect');
                if (next_widget.length) {
                    next_widget.hide();
                    // Hide the next widget down
                    next_widget = next_widget.next('.location-filter').next('.ui-multiselect');
                    if (next_widget.length) {
                        next_widget.hide();
                        // Hide the next widget down
                        next_widget = next_widget.next('.location-filter').next('.ui-multiselect');
                        if (next_widget.length) {
                            next_widget.hide();
                            // Hide the next widget down
                            next_widget = next_widget.next('.location-filter').next('.ui-multiselect');
                            if (next_widget.length) {
                                next_widget.hide();
                            }
                        }
                    }
                }
            }
        } else {
            var new_level = level + 1,
                next = base + new_level,
                $next = $('#' + next);
            if (!$next.length) {
                // Missing level or the end of the widgets
                new_level = level + 2;
                next = base + new_level;
                $next = $('#' + next);
            }
            if (!$next.length) {
                // End of the widgets
                return;
            }
            // Show the next widget down
            var fn = next.replace(/-/g, '_');
            S3[fn]();
            $next.next('.ui-multiselect').show();

            var hierarchy = S3.location_filter_hierarchy,
                location_name_l10n,
                translate;
            if (S3.location_name_l10n != undefined) {
                translate = true;
                location_name_l10n = S3.location_name_l10n;
            } else {
                translate = false;
            }
            // Initialise vars in a way in which we can access them via dynamic names
            widget.options1 = [];
            widget.options2 = [];
            widget.options3 = [];
            widget.options4 = [];
            widget.options5 = [];
            // Find the level at which the hierarchy is defined
            var hierarchy_level;
            for (hierarchy_level = level; hierarchy_level >= 0; hierarchy_level--) {
                if (hierarchy.hasOwnProperty('L' + hierarchy_level)) {
                    break;
                }
            }
            // Support Function to populate the lists which will populate the widget options
            var showSubOptions = function(thisHierarchy) {
                var thisOpt,
                    thatOpt,
                    thatHierarchy;
                for (thisOpt in thisHierarchy) {
                    if (thisHierarchy.hasOwnProperty(thisOpt)) {
                        if (thisOpt && thisOpt != 'null') {
                            widget['options' + new_level].push(thisOpt);
                        }
                        thatHierarchy = thisHierarchy[thisOpt];
                        if (typeof(thatHierarchy) === 'object') {
                            next = new_level + 1;
                            if (!$('#' + base + next).length) {
                                // Missing level
                                next = new_level + 2;
                            }
                            if ($('#' + base + next).length) {
                                for (thatOpt in thatHierarchy) {
                                    if (thatHierarchy.hasOwnProperty(thatOpt)) {
                                        if (thatOpt && thatOpt != 'null') {
                                            widget['options' + next].push(thatOpt);
                                        }
                                        // @ToDo: Greater recursion?
                                        //if (typeof(thatHierarchy[thatOpt]) === 'object') {
                                        //}
                                    }
                                }
                            }
                        }
                    }
                }
            };
            // Recursive Function to populate the lists which will populate the widget options
            var showOptions = function(thisHierarchy, thisLevel) {
                var i,
                    nextLevel,
                    thisOpt,
                    theseValues = $('#' + base + thisLevel).val();
                for (thisOpt in thisHierarchy) {
                    if (thisHierarchy.hasOwnProperty(thisOpt)) {
                        if (theseValues === null) {
                            if (thisLevel === level) {
                                // Show all Options
                                showSubOptions(thisHierarchy[thisOpt]);
                            } else {
                                // Recurse
                                nextLevel = thisLevel + 1;
                                if (!$('#' + base + nextLevel).length) {
                                    // Missing level
                                    nextLevel++;
                                }
                                showOptions(thisHierarchy[thisOpt], nextLevel);
                            }
                        } else {
                            // Show only selected options
                            for (i in theseValues) {
                                if (theseValues[i] === thisOpt) {
                                    if (thisLevel === level) {
                                        showSubOptions(thisHierarchy[thisOpt]);
                                    } else {
                                        // Recurse
                                        nextLevel = thisLevel + 1;
                                        if (!$('#' + base + nextLevel).length) {
                                            // Missing level
                                            nextLevel++;
                                        }
                                        showOptions(thisHierarchy[thisOpt], nextLevel);
                                    }
                                }
                            }
                        }
                    }
                }
            };
            // Start with the base Hierarchy level
            var _hierarchy = hierarchy['L' + hierarchy_level];
            showOptions(_hierarchy, hierarchy_level);

            // Populate the widget options from the lists
            var name_l10n,
                options,
                htmlOptions;
            for (l = new_level; l <= 5; l++) {
                select = $('#' + base + l);
                if (select.length) {
                    options = widget['options' + l];
                    // @ToDo: Sort by name_l10n not by name
                    options.sort();
                    htmlOptions = '';
                    for (var i in options) {
                        if (options.hasOwnProperty(i)) {
                            name = options[i];
                            if (translate) {
                                name_l10n = location_name_l10n[name] || name;
                            } else {
                                name_l10n = name;
                            }
                            htmlOptions += '<option value="' + name + '">' + name_l10n + '</option>';
                        }
                    }
                    select.html(htmlOptions);
                    if (select.hasClass('groupedopts-filter-widget') &&
                        select.groupedopts('instance')) {
                        try {
                            select.groupedopts('refresh');
                        } catch(e) { }
                    } else
                    if (select.hasClass('multiselect-filter-widget') &&
                        select.multiselect('instance')) {
                        select.multiselect('refresh');
                    }
                    if (l === (new_level)) {
                        //if (values) {
                            // Show next level down (if hidden)
                            select.next('button').removeClass('hidden').show();
                            // Hide all subsequent widgets
                            // Select the next widget down
                            next_widget = $widget.next('.ui-multiselect').next('.location-filter').next('.ui-multiselect');
                            if (next_widget.length) {
                                // Don't hide the immediate next one
                                //next_widget.hide();
                                // Hide the next widget down
                                next_widget = next_widget.next('.location-filter').next('.ui-multiselect');
                                if (next_widget.length) {
                                    next_widget.hide();
                                    // Hide the next widget down
                                    next_widget = next_widget.next('.location-filter').next('.ui-multiselect');
                                    if (next_widget.length) {
                                        next_widget.hide();
                                        // Hide the next widget down
                                        next_widget = next_widget.next('.location-filter').next('.ui-multiselect');
                                        if (next_widget.length) {
                                            next_widget.hide();
                                            // Hide the next widget down
                                            next_widget = next_widget.next('.location-filter').next('.ui-multiselect');
                                            if (next_widget.length) {
                                                next_widget.hide();
                                            }
                                        }
                                    }
                                }
                            }
                        /*
                        } else {
                            // @ToDo: Hide next levels down (if configured to do so)
                            //select.next('button').hide();
                        }*/
                    }
                }
            }
        }
    };

    var filterSubmit = function(filter_form) {

        // Hide any warnings (e.g. 'Too Many Features')
        S3.hideAlerts('warning');

        var form_id = filter_form.attr('id'),
            url = filter_form.find('input.filter-submit-url[type="hidden"]').val(),
            queries = getCurrentFilters(filter_form);

        if (filter_form.hasClass('filter-ajax')) {
            // Ajax-refresh the target objects

            // Get the target IDs
            var target = filter_form.find('input.filter-submit-target[type="hidden"]')
                                    .val();

            // Clear the list
            pendingTargets[form_id] = {};

            var targets = target.split(' '),
                needs_reload,
                dt_ajaxurl = {},
                ajaxurl,
                settings,
                config,
                i,
                t,
                target_id,
                visible;

            // Inspect the targets
            for (i=0; i < targets.length; i++) {
                target_id = targets[i];
                t = $('#' + target_id);

                if (!t.is(':visible')) {
                    visible = false;
                } else {
                    visible = true;
                }

                needs_reload = false;
                ajaxurl = null;

                if (t.hasClass('dataTable')) {
                    // Data tables need page reload if no AjaxURL configured
                    config = $('input#' + targets[i] + '_configurations');
                    if (config.length) {
                        settings = JSON.parse($(config).val());
                        ajaxurl = settings.ajaxUrl;
                        if (typeof ajaxurl != 'undefined') {
                            ajaxurl = filterURL(ajaxurl, queries);
                        } else {
                            ajaxurl = null;
                        }
                    }
                    if (ajaxurl) {
                        dt_ajaxurl[targets[i]] = ajaxurl;
                        needs_reload = false;
                    } else {
                        needs_reload = true;
                    }
                } else if (t.hasClass('dl') ||
                           t.hasClass('map_wrapper') ||
                           t.hasClass('cms_content') ||
                           t.hasClass('gi-container') ||
                           t.hasClass('pt-container') ||
                           t.hasClass('tp-container') ||
                           t.hasClass('s3-organizer')) {
                    // These targets can be Ajax-reloaded
                    needs_reload = false;
                } else {
                    // All other targets need page reload
                    if (visible) {
                        // Reload immediately
                        url = filterURL(url, queries);
                        window.location.href = url;
                    } else {
                        // Mark the need for a reload later
                        needs_reload = true;
                    }
                }

                if (!visible) {
                    // Schedule for later
                    pendingTargets[form_id][target_id] = {
                        needs_reload: needs_reload,
                        ajaxurl: ajaxurl,
                        queries: queries
                    };
                }
            }

            // Ajax-update all visible targets
            for (i=0; i < targets.length; i++) {
                target_id = targets[i];
                t = $('#' + target_id);
                if (!t.is(':visible')) {
                    continue;
                } else if (t.hasClass('dataTable')) {
                    var dt = t.dataTable(),
                        dtAjaxURL = dt_ajaxurl[target_id];
                    dt.fnReloadAjax(dtAjaxURL);
                    updateFormatURLs(dt, queries);
                    $('#' + dt[0].id + '_dataTable_filterURL').val(dtAjaxURL);
                } else if (t.hasClass('dl')) {
                    t.datalist('ajaxReload', queries);
                } else if (t.hasClass('map_wrapper')) {
                    S3.gis.refreshLayer('search_results', queries);
                } else if (t.hasClass('gi-container')) {
                    t.groupedItems('reload', null, queries);
                } else if (t.hasClass('pt-container')) {
                    t.pivottable('reload', null, queries);
                } else if (t.hasClass('tp-container')) {
                    t.timeplot('reload', null, queries);
                } else if (t.hasClass('s3-organizer')) {
                    t.organizer('reload');
                }
            }
        } else {
            // Reload the page
            url = filterURL(url, queries);
            window.location.href = url;
        }
    };

    var toggleAdvanced = function(form) {

        var $form = $(form), hidden;

        $form.find('.advanced').each(function() {
            var widget = $(this);
            // Ignoring .multiselect-filter-bootstrap as not used & to be deprecated
            var selectors = '.multiselect-filter-widget,.groupedopts-filter-widget';
            if (widget.hasClass('hide')) {
                // Show the Widgets
                widget.removeClass('hide')
                        .show()
                        .find(selectors).each( function() {
                            var selector = $(this);
                            // Mark them as Active
                            selector.addClass('active');
                            // Refresh the contents
                            if (selector.hasClass('groupedopts-filter-widget') &&
                                selector.groupedopts('instance')) {
                                selector.groupedopts('refresh');
                            } else
                            if (selector.hasClass('multiselect-filter-widget') &&
                                selector.multiselect('instance')) {
                                selector.multiselect('refresh');
                            }
                        });
                hidden = true;
            } else {
                // Hide the Widgets
                widget.addClass('hide')
                        .hide()
                        // Mark them as Inactive
                        .find(selectors)
                        .removeClass('active');
                hidden = false;
            }
        });

        var $btn = $($form.find('.filter-advanced-label'));
        if (hidden) {
            // Change label to label_off
            $btn.text($btn.data('off')).siblings().toggle();
        } else {
            // Change label to label_on
            $btn.text($btn.data('on')).siblings().toggle();
        }

    };

    /**
     * Event handler for the dataChanged event: data of a filter
     * target have changed => update filter options accordingly
     *
     * @param {string} targetID - the filter target ID
     * @param {function} callback - optional callback function
     */
    var dataChanged = function(targetID, callback) {

        if (targetID) {

            var target = $(this).find('input.filter-submit-target').val();
            if (target) {
                var targets = target.split(' ');
                if (targets.length && $.inArray(targetID + '', targets) != -1) {
                    S3.search.ajaxUpdateOptions(this, callback);
                }
            }
        }
    };

    /**
     * document-ready script
     */
    $(document).ready(function() {

        // Activate MultiSelect Widgets
        /*
        $('.multiselect-filter-widget').each(function() {
            if ($(this).find('option').length > 5) {
                $(this).multiselect({
                    selectedList: 5
                }).multiselectfilter();
            } else {
                $(this).multiselect({
                    selectedList: 5
                });
            }
        });
        if (typeof($.fn.multiselect_bs) != 'undefined') {
            // Alternative with bootstrap-multiselect (note the hack for the fn-name):
            $('.multiselect-filter-bootstrap:visible').addClass('active');
            $('.multiselect-filter-bootstrap').multiselect_bs();
        }*/

        // Mark visible widgets as active, otherwise submit won't use them
        $('.groupedopts-filter-widget:visible,.multiselect-filter-widget:visible').addClass('active');

        // Clear all filters
        $('.filter-clear').click(function() {
            var form = $(this).closest('.filter-form');
            clearFilters(form);
        });

        // Show Filter Manager
        $('.show-filter-manager').click(function() {
            $('.filter-manager-row').removeClass('hide').show();
            $('.show-filter-manager').hide();
        });

        // Manual form submission
        $('.filter-submit').click(function() {
            filterSubmit($(this).closest('.filter-form'));
        });

        // Handle external target data updates
        // (e.g. add/update popups, or jeditable-Ajax)
        $('.filter-form').on('dataChanged', function(e, targetID, callback) {
            dataChanged.call(this, targetID, callback);
            // No need (currently) to let this bubble up:
            return false;
        });

        // Advanced button
        $('.filter-advanced').on('click', function() {
            toggleAdvanced($(this).closest('form'));
        });

        // Hierarchical Location Filter
        $('.location-filter').on('change', function() {
            hierarchical_location_change(this);
        });

        // Set filter widgets to fire optionChanged event
        $('.text-filter, .range-filter-input').on('input.autosubmit', function () {
            $(this).closest('form').trigger('optionChanged');
        });
        $('.options-filter, .location-filter, .date-filter-input, .age-filter-input, .map-filter, .value-filter').on('change.autosubmit', function () {
            $(this).closest('form').trigger('optionChanged');
        });
        $('.s3-options-filter-anyall input[type="radio"]').on('change.autosubmit', function() {
            $(this).closest('form').trigger('optionChanged');
        });
        $('.hierarchy-filter').on('select.s3hierarchy', function() {
            $(this).closest('form').trigger('optionChanged');
        });
        $('.map-filter').each(function() {
            var $this = $(this);
            $.when(jsLoaded()).then(
                function() {
                    // Success: Add Callbacks
                    var widget_name = $this.attr('id'),
                        widget = $('#' + widget_name),
                        map_id = widget_name + '-map',
                        wkt,
                        gis = S3.gis,
                        map = gis.maps[map_id],
                        s3 = map.s3;
                    s3.pointPlaced = function(feature) {
                        var out_options = {
                            'internalProjection': map.getProjectionObject(),
                            'externalProjection': gis.proj4326
                            };
                        wkt = new OpenLayers.Format.WKT(out_options).write(feature);
                        // Store the data & trigger the autosubmit
                        widget.val('"' + wkt + '"').trigger('change');
                    };
                    s3.polygonButtonOff = function() {
                        // Clear the data & trigger the autosubmit
                        widget.val('').trigger('change');
                    };
                    s3.layerRefreshed = function() {
                        var polygonButton = s3.polygonButton;
                        if (polygonButton && polygonButton.getIconClass() == 'drawpolygonclear-off') {
                            // Hide the Polygon
                            if (s3.lastDraftFeature) {
                                s3.lastDraftFeature.destroy();
                            } else if (s3.draftLayer.features.length > 1) {
                                // Clear the one from the Current Location in S3LocationSelector
                                s3.draftLayer.features[0].destroy();
                            }
                            // Deactivate Control
                            polygonButton.control.deactivate();
                            polygonButton.items[0].pressed = true;
                        }
                    };
                    s3.polygonButtonLoaded = function() {
                        wkt = widget.val();
                        if (wkt) {
                            // Press Toolbar button
                            s3.polygonButton.items[0].btnEl.dom.click();
                            // Draw Polygon
                            var geometry = OpenLayers.Geometry.fromWKT(wkt);
                            geometry.transform(gis.proj4326, map.getProjectionObject());
                            var feature = new OpenLayers.Feature.Vector(
                                geometry,
                                {}, // attributes
                                null // Style
                            );
                            var draftLayer = s3.draftLayer;
                            draftLayer.addFeatures([feature]);
                            s3.lastDraftFeature = feature;
                            map.zoomToExtent(draftLayer.getDataExtent());
                        }
                    };
                    s3.polygonButtonLoaded();
                },
                function(status) {
                    // Failed
                    s3_debug(status);
                },
                function(status) {
                    // Progress
                    s3_debug(status);
                }
            );
        });

        // Range-Picker
        // https://github.com/zhangtasdq/range-picker
        // @ToDo: Copy (ideally Move DRY) non-Date aspects to range-filter
        $('.date-filter').find('.range-picker').each(function() {
            var $this = $(this);
            var fmt = $this.data('fmt');
            var minValue = $this.data('min');
            var minDate;
            if (minValue) {
                minDate = moment(minValue);
            } else {
                minDate = moment().subtract(5, 'minutes');
                $this.data('min', minDate.format());
            }
            var maxValue = $this.data('max'),
                maxDate;
            if (maxValue) {
                maxDate = moment(maxValue);
            } else {
                maxDate = moment().subtract(5, 'minutes');
                $this.data('max', maxDate.format());
            }
            var widget_name = $this.parent().attr('id');

            // Coarse Filters
            // @ToDo: widget & deployment settings
            // Options: All months between minDate & maxDate
            var cfmt = 'MMM YYYY',
                year = minDate.format('YYYY'),
                optDate = moment(minDate), // Clone
                optgroups = '', // Concat faster than join in modern browsers
                years = [{'year': year,
                          'months': []
                          }],
                i = 0,
                j,
                months,
                new_year;
            while (maxDate > optDate || optDate.format('M') === maxDate.format('M')) {
                new_year = optDate.format('YYYY');
                if (new_year != year) {
                    years.push({'year': new_year,
                                'months': []
                                });
                    year = new_year;
                    i++;
                }
                years[i].months.push(optDate.format(cfmt));
                optDate.add(1, 'month');
            }
            for (i = 0; i < years.length; i++) {
                year = years[i];
                months = year.months;
                year = year.year;
                optgroups += '<optgroup label="' + year + '">';
                for (j = 0; j < months.length; j++) {
                    optgroups += '<option value="' + months[j] + '">' + months[j] + '</option>';
                }
                optgroups += '</optgroup>';
            }
            // @ToDo: i18n
            $this.before('<div class="range-coarse"><div class="range-coarse-start"><label for="' + widget_name + '-cs">From:</label><select id="' + widget_name + '-cs">' + optgroups + '</select></div><div class="range-coarse-end"><label for="' + widget_name + '-ce">to:</label><select id="' + widget_name + '-ce">' + optgroups + '</select></div></div>');
            var coarseStart = $('#' + widget_name + '-cs');
            var coarseEnd = $('#' + widget_name + '-ce');
            coarseStart.val(minDate.format(cfmt));
            coarseEnd.val(maxDate.format(cfmt));

            // Function used by both LineGraph & Play button
            function slotsData() {
                var v,
                    label,
                    values = [],
                    ts = $this.data('ts');

                // Data is represented as an array of {x,y} pairs.
                for (var i = 0; i < ts.length; i++) {
                    v = ts[i];
                    // Axes cannot be Text strings
                    // so we hook into tooltip to add fmt there
                    //label = moment(v[0]).format(fmt) + ' - ' + moment(v[1]).format(fmt);
                    label = moment(v[0]);
                    //values.push({x: label, y: v[2]}); // If pulling back start & end of slot
                    values.push({x: label, y: v[1]});
                }

                // Store the Values as used in multiple places
                $this.data('slots', values);

                // Line chart data should be sent as an array of series objects.
                return [{values: values,   // values - represents the array of {x,y} data points
                         key: '',          // key  - the name of the series.
                         // @ToDo: deployment_setting: use same as the one that enables...or copy from another CSS element?
                         color: '#3b6596', // color - optional: choose your own line color.
                         area: true        // area - set to true if you want this line to turn into a filled area chart.
                         },
                        ];
            }
            // Store the initial values for Play button
            slotsData();

            // Play Button
            // @ToDo: widget & deployment settings
            // @ToDo: Make this sensitive to changing of Icon sets
            // @ToDo: i18n
            $this.before('<a class="button secondary tiny play"><i class="fa fa-play"></i> Play</a><a class="button secondary tiny hide pause"><i class="fa fa-pause"></i> Pause</a><a class="button secondary tiny hide stop"><i class="fa fa-stop"></i> Stop</a>');
            var play = $('#' + widget_name + ' .play'),
                pause = $('#' + widget_name + ' .pause'),
                stop = $('#' + widget_name + ' .stop'),
                slots = $this.data('slots');
            if (slots.length < 3) {
                // Hide the Play button as it doesn't work for such a small number of values
                play.hide();
            }

            // Range-Picker
            var offset,
                timeOffset,
                currentDate;
            var rangePicker = $this.rangepicker({
                type: 'double',
                startValue: minDate.format(fmt),
                endValue: maxDate.format(fmt),
                translateSelectLabel: function(currentPosition, totalPosition) {
                    minDate = new Date($this.data('min'));
                    maxDate = new Date($this.data('max'));
                    offset = maxDate - minDate;
                    timeOffset = offset * (currentPosition / totalPosition);
                    currentDate = new Date(+minDate + parseInt(timeOffset));
                    return moment(currentDate).format(fmt);
                }
            });

            // Line Graph
            // @ToDo: widget & deployment settings
            $this.before('<div id="' + widget_name + '-chart"><svg></svg></div>');
            // On-hover data point tooltip
            var tooltipContent = function(data) {
                var point = data.point;

                var tooltip = '<div class="pt-tooltip">' +
                              '<div class="pt-tooltip-label" style="color:' + point.color + '">' + point.x.format(fmt) + '</div>' +
                              '<div class="pt-tooltip-text">' + point.y + '</div>' +
                              '</div>';
                return tooltip;
            };
            rangePicker.graph = function() {
                nv.addGraph(function() {
                    var chart = nv.models.lineChart()
                                  .margin({left: 0, right: 0})      // Adjust chart margins to give the x-axis some breathing room.
                                  //.useInteractiveGuideline(true)  // We want nice looking tooltips and a guideline!
                                  //.transitionDuration(350)        // how fast do you want the lines to transition?
                                  .showLegend(false)       // Hide the legend (would allow users to turn on/off line series)
                                  .showYAxis(false)        // Hide the y-axis
                                  .showXAxis(false);       // Show the x-axis

                     chart.tooltip.contentGenerator(tooltipContent);

                    //chart.xAxis     // Chart x-axis settings
                    //     .axisLabel('Time (ms)')
                    //     .tickFormat(d3.format(',r'));

                    //chart.yAxis     // Chart y-axis settings
                    //     .axisLabel('Voltage (v)')
                    //     .tickFormat(d3.format('.02f'));

                    // Done setting the chart up? Time to render it!
                    var myData = slotsData();   // You need data...

                    d3.select('#' + widget_name + '-chart svg')  // Select the <svg> element you want to render the chart in.
                      .datum(myData)         // Populate the <svg> element with chart data...
                      .call(chart);          // Finally, render the chart!

                    // Update the chart when window resizes.
                    nv.utils.windowResize(function() { chart.update(); });
                    return chart;
                });
            };
            rangePicker.graph();

            // Events
            // minuteStep handled server-side by extending widget ranges in _options
            //var startStep = startField.calendarWidget('option', 'minuteStep');
            var startField = $('#' + widget_name + '-ge'),
                endField = $('#' + widget_name + '-le'),
                values,
                totalPosition,
                startValue,
                endValue,
                startDate,
                endDate;

            // If the slider is updated then update the INPUTs & trigger a form refresh
            $this.on('update', function() {
                values = rangePicker.getSelectValue();
                totalPosition = values.totalWidth;
                startValue = values.start;
                endValue = values.end;
                minDate = new Date($this.data('min'));
                maxDate = new Date($this.data('max'));
                offset = maxDate - minDate;
                timeOffset = offset * (startValue / totalPosition);
                startDate = new Date(+minDate + parseInt(timeOffset));
                startField.val(moment(startDate).format(fmt));
                timeOffset = offset * (endValue / totalPosition);
                endDate = new Date(+minDate + parseInt(timeOffset));
                endField.val(moment(endDate).format(fmt));
                $this.closest('form').trigger('optionChanged');
            });

            // If the Coarse Filters are updated then update the slider min/max & the INPUTs & trigger a form refresh
            coarseStart.on('change', function() {
                minDate = moment($(this).val(), cfmt);
                $this.data('min', minDate.format());
                startDate = minDate.format(fmt);
                rangePicker.refresh({'startValue': startDate
                                     });
                startField.val(startDate);
                $this.closest('form').trigger('optionChanged');
            });
            coarseEnd.on('change', function() {
                maxDate = moment($(this).val(), cfmt).endOf('month');
                $this.data('max', maxDate.format());
                endDate = maxDate.format(fmt);
                rangePicker.refresh({'endValue': endDate
                                     });
                endField.val(endDate);
                $this.closest('form').trigger('optionChanged');
            });

            // If the INPUTs are updated then update the slider
            function updatePosition() {
                startValue = startField.val();
                endValue = endField.val();
                minDate = new Date($this.data('min'));
                maxDate = new Date($this.data('max'));
                offset = maxDate - minDate;
                if (startValue) {
                    startDate = moment(startValue, fmt);
                    timeOffset = startDate - minDate;
                    startValue = ((timeOffset / offset) * 100) + '%';
                } else {
                    startValue = '0%';
                }
                if (endValue) {
                    endDate = moment(endValue, fmt);
                    timeOffset = endDate - minDate;
                    endValue = ((timeOffset / offset) * 100) + '%';
                } else {
                    endValue = '100%';
                }
                rangePicker.updatePosition(endValue, startValue);
            }
            startField.on('change', function() {
                updatePosition();
            });
            endField.on('change', function() {
                updatePosition();
            });

            // Handle clear
            $this.on('clear', function() {
                rangePicker.updatePosition('100%', '0%');
            });

            // Allow resizing by updateOptions
            $this.on('resize', function(e, min, max, ts) {
                $this.data('min', min);
                $this.data('max', max);
                rangePicker.refresh({'startValue': moment(min).format(fmt),
                                     'endValue': moment(max).format(fmt)//,
                                     });
                $this.data('ts', ts);
                rangePicker.graph();
                // Store the new values for Play button
                //slotsData(); // If the .graph() is hidden by settings but Play is present then need to do this
                slots = $this.data('slots');
                if (slots.length > 2) {
                    // Ensure Play button is visible in case it was previously hidden
                    play.show();
                 } else {
                    // Hide the Play button as it doesn't work for such a small number of values
                    play.hide();
                }
            });

            // Play button
            // @ToDo: Make slot_speed configurable (use same setting as on/off)
            var slot_speed = 4000,
                slot_wait = 0,    // 1st will happen immediately
                timers = [];
            function playSlot(slot) {
                var start = slots[slot].x,
                    end;
                try {
                    end = slots[slot + 1].x;
                } catch(e) {
                    // Final slot
                    end =  moment($this.data('max'));
                }
                var timeout = slot_wait;
                slot_wait = slot_wait + slot_speed;
                var timer = setTimeout(function() {
                    setSlot(slot, start, end);
                }, timeout);
                timers.push(timer);
            }
            function setSlot(slot, start, end) {
                $this.data('slot', slot);
                startField.val(start.format(fmt));
                endField.val(end.format(fmt));
                startField.trigger('change');
            }
            // First Play should start at the beginning
            $this.data('slot', 0);
            play.on('click', function() {
                // Start Play from the correct slot
                var slot = $this.data('slot');
                // Hide Play
                play.hide();
                // Unhide Pause & Stop
                pause.removeClass('hide').show();
                stop.removeClass('hide').show();
                // Move the slider through each of the slots at the defined interval
                slots = $this.data('slots');
                for (slot; slot < slots.length; slot++) {
                    playSlot(slot);
                }
            });
            pause.on('click', function() {
                // Stop Playback
                for (var i = 0; i < timers.length; i++) {
                    clearTimeout(timers.pop());
                }
                // Reset Wait (so we don't have long pause for initial resume)
                slot_wait = 0;
                // Hide Pause
                pause.hide();
                // Show Play
                play.show();
            });
            stop.on('click', function() {
                // Stop Playback
                for (var i = 0; i < timers.length; i++) {
                    clearTimeout(timers.pop());
                }
                // Future Plays should start at the beginning
                $this.data('slot', 0);
                slot_wait = 0;
                // Hide Pause & Stop
                pause.hide();
                stop.hide();
                // Show Play
                play.show();
            });
        });

        // Don't submit if pressing Enter
        $('.text-filter').keypress(function(e) {
            if (e.which == 13) {
                e.preventDefault();
                return false;
            }
            return true;
        });
    });

}());

/**
 * Filter Manager Widget:
 *  - Filter form widget to save/load/apply saved filters
 */

(function($, undefined) {

    var filterManagerID = 0;

    $.widget('s3.filtermanager', {

        /**
         * options: default options
         */
        options: {
            // Basic configuration (required)
            filters: {},                    // the available filters
            ajaxURL: null,                  // URL to save filters

            // Workflow options
            readOnly: false,                // do not allow to create/update/delete filters
            explicitLoad: false,            // load filters via load-button
            allowCreate: true,              // allow Create
            allowUpdate: true,              // allow Update
            allowDelete: true,              // allow Delete

            // Tooltips for actions
            createTooltip: null,            // tooltip for create-button
            loadTooltip: null,              // tooltip for load-button
            saveTooltip: null,              // tooltip for save-button
            deleteTooltip: null,            // tooltip for delete-button

            // Hints (these should be localized by the back-end)
            selectHint: 'Saved filters...', // hint in the selector
            emptyHint: 'No saved filters',  // hint in the selector if no filters available
            titleHint: 'Enter a title',     // hint (watermark) in the title input field

            // Ask the user for confirmation when updating a saved filter?
            confirmUpdate: null,            // user must confirm update of existing filters
            confirmDelete: null,            // user must confirm deletion of existing filters

            // If text is provided for actions, we render them as <a>nchors
            // with the buttonClass - otherwise as empty DIVs for CSS-icons
            createText: null,               // Text for create-action button
            loadText: null,                 // Text for load-action button
            saveText: null,                 // Text for save-action button
            deleteText: null,               // Text for delete-action button
            buttonClass: 'action-btn'       // Class for action buttons
        },

        /**
         * _create: create the widget
         */
        _create: function() {

            this.id = filterManagerID++;
        },

        /**
         * _init: update widget options
         */
        _init: function() {

            this.refresh();

        },

        /**
         * _destroy: remove generated elements & reset other changes
         */
        _destroy: function() {
            // @todo: implement
        },

        /**
         * refresh: re-draw contents
         */
        refresh: function() {

            var id = this.id,
                el = this.element.val(''),
                options = this.options;

            this._unbindEvents();

            var buttonClass = options.buttonClass;

            // CREATE-button
            if (this.create_btn) {
                this.create_btn.remove();
            }
            if (options.createText) {
                this.create_btn = $('<a class="fm-create ' + buttonClass + '" id="fm-create-' + id + '">' + options.createText + '</a>');
            } else {
                this.create_btn = $('<div class="fm-create" id="fm-create-' + id + '">');
            }
            if (options.createTooltip) {
                this.create_btn.attr('title', options.createTooltip);
            }

            // LOAD-button
            if (this.load_btn) {
                this.load_btn.remove();
            }
            if (options.loadText) {
                this.load_btn = $('<a class="fm-load ' + buttonClass + '" id="fm-load-' + id + '">' + options.loadText + '</a>');
            } else {
                this.load_btn = $('<div class="fm-load" id="fm-load-' + id + '">');
            }
            if (options.loadTooltip) {
                this.load_btn.attr('title', options.loadTooltip);
            }

            // SAVE-button
            if (this.save_btn) {
                this.save_btn.remove();
            }
            if (options.saveText) {
                this.save_btn = $('<a class="fm-save ' + buttonClass + '" id="fm-save-' + id + '">' + options.saveText + '</a>');
            } else {
                this.save_btn = $('<div class="fm-save" id="fm-save-' + id + '">');
            }
            if (options.saveTooltip) {
                this.save_btn.attr('title', options.saveTooltip);
            }

            // DELETE-button
            if (this.delete_btn) {
                this.delete_btn.remove();
            }
            if (options.deleteText) {
                this.delete_btn = $('<a class="fm-delete ' + buttonClass + '" id="fm-delete-' + id + '">' + options.deleteText + '</a>');
            } else {
                this.delete_btn = $('<div class="fm-delete" id="fm-delete-' + id + '">');
            }
            if (options.deleteTooltip) {
                this.delete_btn.attr('title', options.deleteTooltip);
            }

            // Throbber
            if (this.throbber) {
                this.throbber.remove();
            }
            this.throbber = $('<div class="inline-throbber" id="fm-throbber-' + id + '">')
                            .css({'float': 'left'});

            // ACCEPT button for create-dialog
            if (this.accept_btn) {
                this.accept_btn.remove();
            }
            this.accept_btn = $('<div class="fm-accept" id="fm-accept-' + id + '">');

            // CANCEL button for create-dialog
            if (this.cancel_btn) {
                this.cancel_btn.remove();
            }
            this.cancel_btn = $('<div class="fm-cancel" id="fm-cancel-' + id + '">');

            // Insert buttons into widget
            $(el).after(this.load_btn.hide(),
                        this.create_btn.hide(),
                        this.save_btn.hide(),
                        this.delete_btn.hide(),
                        this.throbber.hide(),
                        this.accept_btn.hide(),
                        this.cancel_btn.hide());

            // Reset status
            this._cancel();

            // Bind events
            this._bindEvents();
        },

        /**
         * _newFilter: dialog to create a new filter from current options
         */
        _newFilter: function() {

            // @todo: ignore if readOnly

            // Hide selector and buttons
            var el = this.element.hide(),
                fm = this;

            this._hideCRUDButtons();

            // Show accept/cancel
            this.accept_btn.show();
            this.cancel_btn.show();

            // Input field
            var hint = this.options.titleHint;
            var input = $('<input type="text" id="fm-title-input-' + this.id + '">')
                        .val(hint)
                        .css({color: 'grey', 'float': 'left'})
                        .focusin(function() {
                            if (!$(this).hasClass('changed')) {
                                $(this).css({color: 'black'}).val('');
                            }
                        })
                        .change(function() {
                            $(this).addClass('changed');
                        })
                        .focusout(function() {
                            if ($(this).val() === '') {
                                $(this).removeClass('changed')
                                       .css({color: 'grey'})
                                       .val(hint);
                            }
                        }).keypress(function(e) {
                            if(e.which == 13) {
                                e.preventDefault();
                                var $this = $(this);
                                if ($this.val()) {
                                    $this.addClass('changed');
                                }
                                fm._accept();
                            }
                        });
            this.input = input;
            $(el).after(input);
        },

        /**
         * _accept: accept create-dialog and store current options as new filter
         */
        _accept: function () {

            // @todo: ignore if readOnly

            var el = this.element,
                fm = this,
                title = this.input.val();

            if (!$(this.input).hasClass('changed') || !title) {
                return;
            } else {
                $(this.input).removeClass('changed');
            }

            // Hide accept/cancel
            this.accept_btn.hide();
            this.cancel_btn.hide();

            // Show throbber
            this.throbber.show();

            // Collect data
            var filter = {
                title: title,
                query: S3.search.getCurrentFilters($(el).closest('form')),
                url: this._getFilterURL()
            };

            // Ajax-save
            $.ajaxS3({
                'url': this.options.ajaxURL,
                'type': 'POST',
                'dataType': 'json',
                'contentType': 'application/json; charset=utf-8',
                'data': JSON.stringify(filter),
                'success': function(data) {
                    var new_id = data.created;
                    if (new_id) {
                        // Store filter
                        fm.options.filters[new_id] = filter.query;
                        // Append filter to SELECT + select it
                        var new_opt = $('<option value="' + new_id + '">' + filter.title + '</option>');
                        $(el).append(new_opt).val(new_id).change().prop('disabled', false);
                    }
                    // Close save-dialog
                    fm._cancel();
                },
                'error': function () {
                    fm._cancel();
                }
            });
        },

        /**
         * _save: update the currently selected filter with current options
         */
        _save: function() {

            var el = this.element,
                fm = this,
                opts = this.options;

            var id = $(el).val();

            if (!id || opts.confirmUpdate && !confirm(opts.confirmUpdate)) {
                return;
            }

            // Hide buttons
            this._hideCRUDButtons();

            // Show throbber
            this.throbber.show();

            // Collect data
            var filter = {
                id: id,
                query: S3.search.getCurrentFilters($(el).closest('form')),
                url: this._getFilterURL()
            };

            // Ajax-update current filter
            $.ajaxS3({
                'url': this.options.ajaxURL,
                'type': 'POST',
                'dataType': 'json',
                'contentType': 'application/json; charset=utf-8',
                'data': JSON.stringify(filter),
                'success': function() {
                    fm.options.filters[id] = filter.query;
                    fm._cancel();
                },
                'error': function () {
                    fm._cancel();
                }
            });
        },

        /**
         * _delete: delete the currently selected filter
         */
        _delete: function() {

            var $el = $(this.element),
                opts = this.options;

            var id = $el.val();

            if (!id || opts.confirmDelete && !confirm(opts.confirmDelete)) {
                return;
            }

            // Hide buttons
            this._hideCRUDButtons();

            // Show throbber
            this.throbber.show();

            // Collect data
            var filter = {
                id: id
            };

            var url = '' + this.options.ajaxURL;
            if (url.search(/.*\?.*/) != -1) {
                url += '&delete=1';
            } else {
                url += '?delete=1';
            }

            // Ajax-delete current filter
            var fm = this;
            $.ajaxS3({
                'url': url,
                'type': 'POST',
                'dataType': 'json',
                'contentType': 'application/json; charset=utf-8',
                'data': JSON.stringify(filter),
                'success': function() {
                    // Remove options from element
                    $el.val('').find('option[value=' + id + ']').remove();
                    // Remove filter from fm.options
                    delete fm.options.filters[id];
                    // Reset
                    fm._cancel();
                },
                'error': function () {
                    fm._cancel();
                }
            });
        },

        /**
         * _cancel: cancel create-dialog and return to filter selection
         */
        _cancel: function() {

            // Hide throbber
            this.throbber.hide();

            // Remove input and hide accept/cancel
            if (this.input) {
                this.input.remove();
                this.input = null;
            }
            this.accept_btn.hide();
            this.cancel_btn.hide();

            // Show selector and buttons
            var el = this.element.show(),
                opts = this.options;

            // Disable selector if no filters
            var options = $(el).find('option');
            if (options.length == 1 && options.first().hasClass('filter-manager-prompt')) {
                $(el).prop('disabled', true);
                $(el).find('option.filter-manager-prompt').text(opts.emptyHint);
            } else {
                $(el).prop('disabled', false);
                $(el).find('option.filter-manager-prompt').text(opts.selectHint);
            }

            this._showCRUDButtons();
        },

        /**
         * _load: load the selected filter
         */
        _load: function() {

            var el = this.element,
                filters = this.options.filters;

            var filter_id = $(el).val();
            if (filter_id && filters.hasOwnProperty(filter_id)) {
                S3.search.setCurrentFilters($(el).closest('form'), filters[filter_id]);
            } else {
                // @todo: clear filters? => not in global scope
                // S3.search.clearFilters($(this).closest('form'));
            }
        },

        /**
         * clear: clear current selection
         */
        clear: function() {

            var el = this.element;

            $(el).val('');
            this._cancel();
        },

        /**
         * _showCRUDButtons: show (unhide) load/save/delete buttons
         */
        _showCRUDButtons: function() {

            var opts = this.options;

            this._hideCRUDButtons();

            if (!opts.readOnly && opts.allowCreate) {
                this.create_btn.show();
            }
            if ($(this.element).val()) {
                if (opts.explicitLoad) {
                    this.load_btn.show();
                }
                if (!opts.readOnly) {
                    if (opts.allowUpdate) {
                        this.save_btn.show();
                    }
                    if (opts.allowDelete) {
                        this.delete_btn.show();
                    }
                }
            }
        },

        /**
         * _hideCRUDButtons: hide load/save/delete buttons
         */
        _hideCRUDButtons: function() {

            this.create_btn.hide();
            this.load_btn.hide();
            this.delete_btn.hide();
            this.save_btn.hide();
        },

        /**
         * _getFilterURL: get the page URL of the filter form
         */
        _getFilterURL: function() {

            var url = $(this.element).closest('form')
                                     .find('input.filter-submit-url[type="hidden"]');
            if (url.length) {
                return url.first().val();
            } else {
                return document.URL;
            }
        },

        /**
         * _bindEvents: bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var fm = this;

            // @todo: don't bind create if readOnly
            this.create_btn.click(function() {
                fm._newFilter();
            });
            this.accept_btn.click(function() {
                fm._accept();
            });
            this.cancel_btn.click(function() {
                fm._cancel();
            });
            this.element.change(function() {
                fm._showCRUDButtons();
                if (!fm.options.explicitLoad) {
                    fm._load();
                }
            });
            if (this.options.explicitLoad) {
                this.load_btn.click(function() {
                    fm._load();
                });
            }
            // @todo: don't bind save if readOnly
            this.save_btn.click(function() {
                fm._save();
            });
            // @todo: don't bind delete if readOnly
            this.delete_btn.click(function() {
                fm._delete();
            });
        },

        /**
         * _unbindEvents: remove events from generated elements (before refresh)
         */
        _unbindEvents: function() {

            if (this.create_btn) {
                this.create_btn.unbind('click');
            }
            if (this.accept_btn) {
                this.accept_btn.unbind('click');
            }
            if (this.cancel_btn) {
                this.cancel_btn.unbind('click');
            }
            if (this.load_btn && this.options.explicitLoad) {
                this.load_btn.unbind('click');
            }
            if (this.save_btn) {
                this.save_btn.unbind('click');
            }
            if (this.delete_btn) {
                this.delete_btn.unbind('click');
            }
            this.element.unbind('change');
        }
    });
})(jQuery);

// END ========================================================================
