/**
    S3Filter Static JS Code
*/

S3.search = {};

// Module pattern to hide internal vars
(function() {

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

    /**
     * Default options for $.searchS3
     */
    var searchS3Defaults = {
        timeout : 10000,
        retryLimit: 5,
        dataType: 'json',
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
     * @prop {Array} s.data - GET variables as array of dicts {name: k, value: v},
     *                        will be appended to the POST URL
     * @prop {function} s.done - the done-callback (alternatively s.success)
     * @prop {function} s.fail - the fail-callback (alternatively s.error)
     *
     * @note: only GET requests will be converted, while POST requests
     *        will be sent unmodified (=equivalent to $.AjaxS3)
     */
    $.searchS3 = function(s) {

        var message,
            options = $.extend({}, searchS3Defaults, s),
            doneCallback = null,
            failCallback = null;

        if (s.done) {
            doneCallback = s.done;
        } else if (s.success) {
            doneCallback = s.success;
        }
        if (s.fail) {
            failCallback = s.fail;
        } else if (s.error) {
            failCallback = s.error;
        }

        // Prevent callbacks from being executed twice
        options.done = null;
        options.success = null;
        options.fail = null;
        options.error = null;

        // Retry-counter
        options.tryCount = 0;

        // Rewrite the Ajax options
        searchRewriteAjaxOptions(options, 'ajax');

        if (s.message) {
            message = i18n.ajax_get + ' ' + (s.message ? s.message : i18n.ajax_fmd) + '...';
            S3.showAlert(message, 'info');
        }
        $.ajax(
            options
        ).done(function(data, status) {
            S3.hideAlerts();
            this.tryCount = 0;
            if (data && data.message) {
                S3.showAlert(data.message, 'success');
            }
            // Call done/success callback:
            if (doneCallback) {
                doneCallback(data, status);
            }
        }).fail(function(jqXHR, textStatus, errorThrown) {
            if (textStatus == 'timeout') {
                this.tryCount++;
                if (this.tryCount <= this.retryLimit) {
                    // Try again
                    message = i18n.ajax_get + ' ' + (s.message ? s.message : i18n.ajax_fmd) + '... ' + i18n.ajax_rtr + ' ' + this.tryCount;
                    S3.showAlert(message, 'warning');
                    $.ajax(this);
                    return;
                }
                message = i18n.ajax_wht + ' ' + (this.retryLimit + 1) + ' ' + i18n.ajax_gvn;
                S3.showAlert(message, 'error');
            } else if (jqXHR.status == 500) {
                S3.showAlert(i18n.ajax_500, 'error');
            } else {
                S3.showAlert(i18n.ajax_dwn, 'error');
            }
            // Call fail/error callback:
            if (failCallback) {
                failCallback(jqXHR, textStatus, errorThrown);
            }
        });
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
            form = document.createElement("form");

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
                if (typeof data[key] === 'object') {
                    input.value = JSON.stringify(data[key]);
                } else {
                    input.value = data[key];
                }
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
        var values = [];
        var quote = false;
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
        form = typeof form !== 'undefined' ? form : $('body').find('form.filter-form').first();

        // Temporarily disable auto-submit
        form.data('noAutoSubmit', 1);

        form.find('.text-filter').each(function() {
            $(this).val('');
        });
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
        form.find('.range-filter-input').each(function() {
            $(this).val('');
        });
        form.find('.date-filter-input').each(function() {
            $(this).calendarWidget('clear');
        });
        // Hierarchy filter widget (experimental)
        form.find('.hierarchy-filter').each(function() {
            $(this).hierarchicalopts('reset');
        });

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
            operator;

        // Text widgets
        form.find('.text-filter:visible').each(function() {
            $this = $(this);
            id = $this.attr('id');
            urlVar = $('#' + id + '-data').val();
            value = $this.val();
            if (value) {
                values = value.split(' ');
                var match = $this.data('match'),
                    quoted,
                    anyValue = [];
                for (i=0; i < values.length; i++) {
                    quoted = quoteValue('*' + values[i] + '*');
                    if (match == "any") {
                        anyValue.push(quoted);
                    } else {
                        queries.push([urlVar, quoted]);
                    }
                }
                if (match == "any") {
                    queries.push([urlVar, anyValue.join(',')])
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
            operator = $("input:radio[name='" + id + "_filter']:checked").val();

            var contains = /__contains$/;
            var anyof = /__anyof$/;
            if (operator == 'any' && urlVar.match(contains)) {
                urlVar = urlVar.replace(contains, '__anyof');
            } else if (operator == 'all' && urlVar.match(anyof)) {
                urlVar = urlVar.replace(anyof, '__contains');
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

        // Numerical range widgets -- each widget has two inputs.
        form.find('.range-filter-input:visible').each(function() {

            $this = $(this),
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

            $this = $(this),
            id = $this.attr('id'),
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
                queries.push([urlVar, urlValue]);
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

            operator = $("input:radio[name='" + id + "_filter']:checked").val();

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

            values = $this.hierarchicalopts('get');
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

        form = typeof form !== 'undefined' ? form : $('body').find('form.filter-form').first();

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
                var refresh = false;
                var selector = expression.split('__')[0];
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
                selector = expression.split('__')[0],
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
                    var selector = expression.split('__')[0];
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
                $this.hierarchicalopts('set', values);
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
                for (i=0; i<a.length; i++) {
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
                query.push(k + '=' + v);
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

        for (filter_id in options) {
            var widget = $('#' + filter_id);

            if (widget.length) {
                var newopts = options[filter_id];

                // OptionsFilter
                if ($(widget).hasClass('options-filter')) {
                    if ($(widget)[0].tagName.toLowerCase() == 'select') {
                        // Standard SELECT
                        var selected = $(widget).val(),
                            s=[], opts='', group, item, value, label, tooltip;

                        // Update HTML
                        if (newopts.hasOwnProperty('empty')) {

                            // @todo: implement

                        } else

                        if (newopts.hasOwnProperty('groups')) {
                            for (var i=0, len=newopts.groups.length; i < len; i++) {
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
                            for (var i=0, len=newopts.length; i < len; i++) {
                                item = newopts[i];
                                value = item[0].toString();
                                label = item[1];
                                if (selected && $.inArray(value, selected) >= 0) {
                                    s.push(value);
                                }
                                opts += '<option value="' + value + '">' + label + '</option>';
                            }
                        }
                        $(widget).html(opts);

                        // Update SELECTed value
                        if (s) {
                            $(widget).val(s);
                        }

                        // Refresh UI widgets
                        if (widget.hasClass('groupedopts-filter-widget') &&
                            widget.groupedopts('instance')) {
                            widget.groupedopts('refresh');
                        } else
                        if (widget.hasClass('multiselect-filter-widget') &&
                            widget.multiselect('instance')) {
                            widget.multiselect('refresh');
                        }

                    } else {
                        // other widget types of options filter
                    }

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
     */
    S3.search.ajaxUpdateOptions = function(form) {

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
        }).fail(function(jqXHR, textStatus, errorThrown) {
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

            needs_reload = target_data['needs_reload'];
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
            if (t.hasClass('dl')) {
                t.datalist('ajaxReload', target_data['queries']);
            } else if (t.hasClass('dataTable')) {
                // Refresh Data
                var dt = t.dataTable(),
                    dtAjaxURL = target_data['ajaxurl'];
                dt.fnReloadAjax(dtAjaxURL);
                updateFormatURLs(dt, queries);
                $('#' + dt[0].id + '_dataTable_filterURL').each(function() {
                    $(this).val(dtAjaxURL);
                });
            } else if (t.hasClass('map_wrapper')) {
                S3.gis.refreshLayer('search_results');
            } else if (t.hasClass('gi-container')) {
                t.groupedItems('reload', null, target_data['queries']);
            } else if (t.hasClass('pt-container')) {
                t.pivottable('reload', null, target_data['queries']);
            } else if (t.hasClass('tp-container')) {
                t.timeplot('reload', null, target_data['queries']);
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
     * Set up the Tabs for an S3Summary page
     * - in global scope as called from outside
     *
     * Parameters:
     * form - {String} ID of the filter form
     * active_tab - {Integer} Which Section is active to start with
     */
    S3.search.summary_tabs = function(form, active_tab, pending) {

        // Schedule initially hidden widgets to Ajax-load their data
        // layers, required here because otherwise this happens only
        // during filter-submit, but the user could also simply switch
        // tabs without prior filter-submit; list of initially hidden
        // widgets with ajax-init option is provided by the page
        // renderer (S3Summary.summary()).
        if (pending) {
            var ajaxurl,
                config,
                q = getCurrentFilters($('#' + form)),
                t,
                target_id,
                targets = pending.split(',');
            for (var i=0, len=targets.length; i < len; i++) {
                target_id = targets[i];
                if (!pendingTargets.hasOwnProperty(form)) {
                    pendingTargets[form] = {};
                }
                if (pendingTargets[form].hasOwnProperty(target_id)) {
                    // already scheduled
                    continue;
                }
                t = $('#' + target_id);
                if (t.hasClass('dl') ||
                    t.hasClass('gi-container') ||
                    t.hasClass('pt-container') ||
                    t.hasClass('tp-container') ||
                    t.hasClass('map_wrapper')) {
                    // These targets handle their AjaxURL themselves
                    ajaxurl = null;
                } else if (t.hasClass('dataTable')) {
                    // Lookup and filter the AjaxURL
                    config = $('input#' + targets[i] + '_configurations');
                    if (config.length) {
                        settings = JSON.parse($(config).val());
                        ajaxurl = settings['ajaxUrl'];
                        if (typeof ajaxurl != 'undefined') {
                            ajaxurl = filterURL(ajaxurl, q);
                        } else {
                            continue;
                        }
                    }
                } else {
                    continue;
                }
                pendingTargets[form][target_id] = {
                    needs_reload: false,
                    ajaxurl: ajaxurl,
                    queries: q
                };
            }
        }

        /**
         * Helper method to trigger re-calculation of column width in
         * responsive data tables after unhiding them
         *
         * @param {jQuery} datatable - the datatable
         */
        var recalcResponsive = function(datatable) {
            var dt = $(datatable).DataTable();
            if (dt && dt.responsive) {
                dt.responsive.recalc();
            }
        };

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
                // Find any Map widgets in this section
                var maps = newPanel.find('.map_wrapper');
                var maps_len = maps.length;
                if (maps_len) {
                    // Check that Maps JS is Loaded
                    $.when(jsLoaded()).then(
                        function(status) {
                            // Success: Instantiate Maps
                            var gis = S3.gis;
                            for (var i=0; i < maps_len; i++) {
                                var map_id = maps[i].attributes['id'].value;
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
                newPanel.find('table.dataTable.display.responsive')
                        .each(function() {
                    recalcResponsive(this);
                });
            }
        }).css({visibility: 'visible'});

        // Activate not called? Unhide initial section anyway:
        $('.ui-tabs-panel[aria-hidden="false"]').first()
                                                .removeClass('hide')
                                                .find('table.dataTable.display.responsive')
                                                .each(function() {
                                                    recalcResponsive(this);
                                                });
    };

    /**
     * Check that Map JS is Loaded
     * - used if a tab containing a Map is unhidden
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
                var map_id = map.attributes['id'].value;
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
    S3.search.s3map = function() {
        var gis = S3.gis;
        // Instantiate the map
        var map_id = 'default_map';
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
        var name = widget.name;
        var base = name.slice(0, -1);
        var level = parseInt(name.slice(-1));
        var $widget = $('#' + name);
        var values = $widget.val();
        if (values) {
            // Show the next widget down
            var fn = base.replace(/-/g, '_') + (level + 1);
            S3[fn]();
            $('#' + base + (level + 1)).next('.ui-multiselect').show();
        } else {
            // Hide the next widget down
            var next_widget = $widget.next('.ui-multiselect').next('.location-filter').next('.ui-multiselect');
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
        }
        var hierarchy = S3.location_filter_hierarchy;
        if (S3.location_name_l10n != undefined) {
            var translate = true;
            var location_name_l10n = S3.location_name_l10n;
        } else {
            var translate = false;
        }
        // Initialise vars in a way in which we can access them via dynamic names
        widget.options1 = [];
        widget.options2 = [];
        widget.options3 = [];
        widget.options4 = [];
        widget.options5 = [];
        var new_level, opt, _opt, i, option;
        if (hierarchy.hasOwnProperty('L' + level)) {
            // Top-level
            var _hierarchy = hierarchy['L' + level];
            for (opt in _hierarchy) {
                if (_hierarchy.hasOwnProperty(opt)) {
                    if (values === null) {
                        // Show all Options
                        for (option in _hierarchy[opt]) {
                            if (_hierarchy[opt].hasOwnProperty(option)) {
                                new_level = level + 1;
                                if (option && option != 'null') {
                                    widget['options' + new_level].push(option);
                                }
                                if (typeof(_hierarchy[opt][option]) === 'object') {
                                    var __hierarchy = _hierarchy[opt][option];
                                    for (_opt in __hierarchy) {
                                        if (__hierarchy.hasOwnProperty(_opt)) {
                                            new_level = level + 2;
                                            if (_opt && _opt != 'null') {
                                                widget['options' + new_level].push(_opt);
                                            }
                                            // @ToDo: Greater recursion
                                            //if (typeof(__hierarchy[_opt]) === 'object') {
                                            //}
                                        }
                                    }
                                }
                            }
                        }
                    } else {
                        for (i in values) {
                            if (values[i] === opt) {
                                for (option in _hierarchy[opt]) {
                                    if (_hierarchy[opt].hasOwnProperty(option)) {
                                        new_level = level + 1;
                                        if (option && option != 'null') {
                                            widget['options' + new_level].push(option);
                                        }
                                        if (typeof(_hierarchy[opt][option]) === 'object') {
                                            var __hierarchy = _hierarchy[opt][option];
                                            for (_opt in __hierarchy) {
                                                if (__hierarchy.hasOwnProperty(_opt)) {
                                                    new_level = level + 2;
                                                    if (_opt && _opt != 'null') {
                                                        widget['options' + new_level].push(_opt);
                                                    }
                                                    // @ToDo: Greater recursion
                                                    //if (typeof(__hierarchy[_opt]) === 'object') {
                                                    //}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        } else if (hierarchy.hasOwnProperty('L' + (level - 1))) {
            // Nested 1 in
            var _hierarchy = hierarchy['L' + (level - 1)];
            // Read higher level
            var _values = $('#' + base + (level - 1)).val();
            for (opt in _hierarchy) {
                if (_hierarchy.hasOwnProperty(opt)) {
                    if (_values === null) {
                        // We can't be hiding
                        // Read this level
                        _values = $('#' + base + level).val();
                        for (option in _hierarchy[opt]) {
                            for (i in _values) {
                                if (_values[i] === option) {
                                    new_level = level + 1;
                                    // Read the options for this level
                                    var __hierarchy = _hierarchy[opt][option];
                                    for (_opt in __hierarchy) {
                                        if (__hierarchy.hasOwnProperty(_opt)) {
                                            if (_opt && _opt != 'null') {
                                                widget['options' + new_level].push(_opt);
                                            }
                                        }
                                    }
                                    // @ToDo: Read the options for subsequent levels
                                }
                            }
                        }
                    } else {
                        for (i in _values) {
                            if (_values[i] === opt) {
                                for (option in _hierarchy[opt]) {
                                    if (_hierarchy[opt].hasOwnProperty(option)) {
                                        if (values === null) {
                                            // Show all subsequent Options
                                            for (option in _hierarchy[opt]) {
                                                if (_hierarchy[opt].hasOwnProperty(option)) {
                                                    new_level = level + 1;
                                                    var __hierarchy = _hierarchy[opt][option];
                                                    for (_opt in __hierarchy) {
                                                        if (__hierarchy.hasOwnProperty(_opt)) {
                                                            if (_opt && _opt != 'null') {
                                                                widget['options' + new_level].push(_opt);
                                                            }
                                                            // @ToDo: Greater recursion
                                                            //if (typeof(__hierarchy[_opt]) === 'object') {
                                                            //}
                                                        }
                                                    }
                                                }
                                            }
                                        } else {
                                            for (i in values) {
                                                if (values[i] === option) {
                                                    new_level = level + 1;
                                                    var __hierarchy = _hierarchy[opt][option];
                                                    for (_opt in __hierarchy) {
                                                        if (__hierarchy.hasOwnProperty(_opt)) {
                                                            if (_opt && _opt != 'null') {
                                                                widget['options' + new_level].push(_opt);
                                                            }
                                                            // @ToDo: Greater recursion
                                                            //if (typeof(__hierarchy[_opt]) === 'object') {
                                                            //}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        } else if (hierarchy.hasOwnProperty('L' + (level - 2))) {
            // @ToDo
        }
        var name, name_l10n, options, _options;
        for (var l = level + 1; l <= 5; l++) {
            var select = $('#' + base + l);
            if (typeof(select) != 'undefined') {
                options = widget['options' + l];
                // @ToDo: Sort by name_l10n not by name
                options.sort();
                _options = '';
                for (i in options) {
                    if (options.hasOwnProperty(i)) {
                        name = options[i];
                        if (translate) {
                            name_l10n = location_name_l10n[name] || name;
                        } else {
                            name_l10n = name;
                        }
                        _options += '<option value="' + name + '">' + name_l10n + '</option>';
                    }
                }
                select.html(_options);
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
                if (l === (level + 1)) {
                    if (values) {
                        // Show next level down (if hidden)
                        select.next('button').removeClass('hidden').show();
                        // @ToDo: Hide subsequent levels (if configured to do so)
                    } else {
                        // @ToDo: Hide next levels down (if configured to do so)
                        //select.next('button').hide();
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

                if (t.hasClass('dl')) {
                    // data lists do not need page reload
                    needs_reload = false;
                } else if (t.hasClass('dataTable')) {
                    // data tables need page reload if no AjaxURL configured
                    config = $('input#' + targets[i] + '_configurations');
                    if (config.length) {
                        settings = JSON.parse($(config).val());
                        ajaxurl = settings['ajaxUrl'];
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
                } else if (t.hasClass('map_wrapper')) {
                    // maps do not need page reload
                    needs_reload = false;
                } else if (t.hasClass('cms_content')) {
                    // CMS widgets do not need page reload
                    needs_reload = false;
                } else if (t.hasClass('gi-container')) {
                    // GroupedItems do not need page reload
                    needs_reload = false;
                } else if (t.hasClass('pt-container')) {
                    // PivotTables do not need page reload
                    needs_reload = false;
                } else if (t.hasClass('tp-container')) {
                    // TimePlots do not need page reload
                    needs_reload = false;
                } else {
                    // all other targets need page reload
                    if (visible) {
                        // reload immediately
                        url = filterURL(url, queries);
                        window.location.href = url;
                    } else {
                        // mark the need for a reload later
                        needs_reload = true;
                    }
                }

                if (!visible) {
                    // schedule for later
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
                } else if (t.hasClass('dl')) {
                    t.datalist('ajaxReload', queries);
                } else if (t.hasClass('dataTable')) {
                    var dt = t.dataTable(),
                        dtAjaxURL = dt_ajaxurl[target_id];
                    dt.fnReloadAjax(dtAjaxURL);
                    updateFormatURLs(dt, queries);
                    $('#' + dt[0].id + '_dataTable_filterURL').each(function() {
                        $(this).val(dtAjaxURL);
                    });
                } else if (t.hasClass('map_wrapper')) {
                    S3.gis.refreshLayer('search_results', queries);
                } else if (t.hasClass('gi-container')) {
                    t.groupedItems('reload', null, queries);
                } else if (t.hasClass('pt-container')) {
                    t.pivottable('reload', null, queries);
                } else if (t.hasClass('tp-container')) {
                    t.timeplot('reload', null, queries);
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
                            selector = $(this);
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

        // Filter-form submission
        $('.filter-submit').click(function() {
            filterSubmit($(this).closest('.filter-form'));
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
        $('.options-filter, .location-filter, .date-filter-input').on('change.autosubmit', function () {
            $(this).closest('form').trigger('optionChanged');
        });
        $('.hierarchy-filter').on('select.s3hierarchy', function() {
            $(this).closest('form').trigger('optionChanged');
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
                                $this = $(this);
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

            var url = new String(this.options.ajaxURL);
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