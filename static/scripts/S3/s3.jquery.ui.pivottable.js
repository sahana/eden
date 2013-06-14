/**
 * jQuery UI pivottable Widget for S3Report2
 * 
 * @copyright: 2013 (c) Sahana Software Foundation
 * @license: MIT
 *
 * requires: jQuery 1.9.1+
 * requires: jQuery UI 1.10 widget factory
 *
 */

(function($, undefined) {
    
    var pivottableID = 0;

    $.widget('s3.pivottable', {

        // default options
        options: {
            showTotals: true,
            collapseForm: true,
            ajaxURL: null
        },

        _create: function() {
            // create the widget
            
            this.id = pivottableID;
            pivottableID += 1;

            this.table = null;
        },

        _init: function() {
            // update widget options
            this.refresh();

            var el = this.element;

            // Hide report options initially?
            if (this.options.collapseForm) {
                var widget_id = $(el).attr('id');
                $('#' + widget_id + '-options legend').siblings().toggle();
                $('#' + widget_id + '-options legend').children().toggle();
            }
        },

        _destroy: function() {
            // remove generated elements & reset other changes
            this.table.remove();
        },

        refresh: function() {
            // re-draw contents
            var el = this.element, data;

            this._unbindEvents();

            var pivotdata = $(el).find('input[type="hidden"][name="pivotdata"]');
            if (pivotdata.length) {
                data = JSON.parse($(pivotdata).first().val());
            }

            if (data) {
                var cells = data['cells'],
                    cols = data['cols'],
                    rows = data['rows'],
                    total = data['total'],
                    labels = data['labels'];

                var thead = this._renderHeader(cols, labels);

                thead.append(this._renderColumns(cols, labels));

                var tbody = this._renderRows(rows, labels, cells),
                    tfoot = this._renderFooter(rows, cols, labels, total);

                var table = $('<table class="dataTable display report"/>')
                            .append(thead)
                            .append(tbody);
                if (tfoot !== null) {
                    table.append(tfoot);
                }

                this.table = $(table);
                $(el).find('.pt-table').first()
                                       .empty()
                                       .append(this.table);
                $(el).find('.pt-empty').hide();
            } else {
                data = {};
            }

            this._bindEvents(data);
            $(el).find('.pt-throbber').hide();
        },

        _renderHeader: function(cols, labels) {

            var header = $('<tr>');

            header.append($('<th scope="col">' + labels['layer'] + '</th>'))
                  .append($('<th scope="col" colspan="' + cols.length + '">' + labels['cols'] + '</th>'));

            if (this.options.showTotals) {
                header.append($('<th class="totals_header row_totals" scope="col" rowspan="2">' + labels.total + '</th>'));
            }
            return $('<thead>').append(header);
        },

        _renderColumns: function(cols, labels) {

            var columns = $('<tr>');
            
            columns.append($('<th scope="col">' + labels['rows'] + '</th>'));
            
            for (var i=0; i < cols.length; i++) {
                columns.append($('<th scope="col">' + cols[i][2] + '</th>'));
            }

            return columns;
        },

        _renderRows: function(rows, labels, cells) {

            var tbody = $('<tbody>'),
                show_totals = this.options.showTotals,
                row, tr;
            for (var i=0; i<cells.length; i++) {
                row = rows[i];
                tr = $('<tr class="' + (i % 2 ? 'odd': 'even') + '">' + '<td>' + row[2] + '</td></tr>')
                     .append(this._renderCells(cells[i], labels));
                if (show_totals) {
                    tr.append($('<td>' + row[3] + '</td>'));
                }
                tbody.append(tr);
            }
            return tbody;
        },

        _renderCells: function(cells, labels) {

            var cell, items, keys,
                none = labels.none,
                c = "pt-cell-value",
                row = [], column, value;
            
            for (var i = 0; i < cells.length; i++) {
                
                cell = cells[i];
                items = cell.items;
                
                column = $('<td>');
                
                if (items === null) {
                    value = $('<div class="' + c + '">' + none + '</div>');
                } else if ($.isArray(items)) {
                    value = $('<div class="' + c + '">');
                    list = $('<ul>');
                    for (var j=0; j < items.length; j++) {
                        list.append($('<li>' + items[j] + '</li>'));
                    }
                    value.append(list);
                } else {
                    value = $('<div class="' + c + '">' + items + '</div>');
                }
                column.append(value);

                keys = cell.keys;
                if (items && keys && keys.length) {
                    column.data('records', keys)
                          .append($('<div class="pt-cell-zoom"></div>'));
                }
                row.push(column);
            }
            return row;
        },

        _renderFooter: function(rows, cols, labels, total) {

            if (this.options.showTotals) {
                
                var c = rows.length % 2 ? 'odd' : 'even';
                var footer = $('<tr class="' + c + ' totals_row">' +
                               '<th class="totals_header" scope="row">' +
                               labels.total +
                               '</th></tr>');
                for (var i = 0; i < cols.length; i++) {
                    footer.append($('<td>' + cols[i][3] + '</td>'));
                }
                footer.append($('<td>' + total + '</td>'));
                return $('<tfoot>').append(footer);
                
            } else {
                
                return null;
            }
        },

        _getOptions: function() {

            var el = this.element;
            var widget_id = '#' + $(el).attr('id');

            var options = {
                rows: $(widget_id + '-rows').val(),
                cols: $(widget_id + '-cols').val(),
                fact: $(widget_id + '-fact').val(),
                totals: $(widget_id + '-totals').is(':checked') ? 1 : 0
            };
            return options;
        },

        _getFilters: function() {

            var widget_id = '#' + $(this.element).attr('id');

            var filters = $(widget_id + '-filters'), filter_options = [];
            try {
                if (filters.length) {
                    filter_options = S3.search.getCurrentFilters(filters.first());
                } else {
                    return null;
                }
            } catch (e) {}

            var options = {};
            for (var i=0, len=filter_options.length, opt; i < len; i++) {
                opt = filter_options[i].split('=');
                if (opt.length > 1) {
                    options[opt[0]] = opt[1];
                }
            }
            return options;
        },

        _updateAjaxURL: function(options, filters) {

            var ajaxURL = this.options.ajaxURL;

            // Construct the URL
            var url_parts = ajaxURL.split('?'), query = {};
            
            if (url_parts.length > 1) {
                var qstr = url_parts[1];
                    
                var a = qstr.split('&'),
                b, v, i, len;
                for (i=0, len=a.length; i < len; i++) {
                    b = a[i].split('=');
                    if (b.length > 1 && b[0] != 'aggregate') {
                        query[decodeURIComponent(b[0])] = decodeURIComponent(b[1]);
                    }
                }
            }

            var newopt, needs_reload = false;

            if (options) {
                for (option in options) {
                    newopt = options[option];
                    if (option == 'totals') {
                        this.options.showTotals = newopt ? true : false;
                    } else if (query[option] != newopt) {
                        needs_reload = true;
                    }
                    query[option] = newopt ? newopt : null;
                }
            }
            
            if (filters) {
                for (option in filters) {
                    newopt = filters[option];
                    if (query[option] != newopt) {
                        needs_reload = true;
                    }
                    query[option] = newopt ? newopt : null;
                }
                for (option in query) {
                    if (options.hasOwnProperty(option)) {
                        continue;
                    }
                    newopt = filters[option];
                    if (query[option] != newopt) {
                        needs_reload = true;
                    }
                    query[option] = newopt ? newopt : null;
                }
            }
            
            var url_queries = [], url_query;
            for (option in query) {
                if (query[option] !== null) {
                    url_queries.push(option + '=' + query[option]);
                }
            }
            url_query = url_queries.join('&');

            var filtered_url = url_parts[0];
            if (url_query) {
                filtered_url = filtered_url + '?' + url_query;
            }
            this.options.ajaxURL = filtered_url;
            return needs_reload;
        },

        reload: function(options, filters, force) {

            force = typeof force != 'undefined' ? force : true;

            if (typeof filters == 'undefined') {
                // extract filters
                filters = this._getFilters();
            }

            var pt = this, el = this.element, needs_reload;
            
            var pivotdata = $(el).find('input[type="hidden"][name="pivotdata"]');
            if (!pivotdata.length) {
                return;
            }

            if (options || filters) {
                needs_reload = this._updateAjaxURL(options, filters);
            }

            if (needs_reload || force) {
                var ajaxURL = this.options.ajaxURL;
                $(el).find('.pt-throbber').show();
                $.ajax({
                    'url': ajaxURL,
                    'dataType': 'json'
                }).done(function(data) {
                    pivotdata.first().val(JSON.stringify(data));
                    pt.refresh();
                }).fail(function(jqXHR, textStatus, errorThrown) {
                    if (errorThrown == 'UNAUTHORIZED') {
                        msg = i18n.gis_requires_login;
                    } else {
                        msg = jqXHR.responseText;
                    }
                    console.log(msg);
                });
            } else {
                $(el).find('.pt-throbber').show();
                pt.refresh();
            }
        },

        _bindEvents: function(data) {
            // bind events to generated elements (after refresh)

            var pt = this,
                el = this.element;
            var widget_id = $(el).attr('id');

            // Show/hide report options
            $('#' + widget_id + '-options legend').click(function() {
                $(this).siblings().toggle();
                $(this).children().toggle();
            });
            $('#' + widget_id + '-filters legend').click(function() {
                $(this).siblings().toggle();
                $(this).children().toggle();
            });
            
            $('#' + widget_id + '-totals').click(function() {
                var show_totals = $(this).is(':checked');
                if (pt.options.showTotals != show_totals) {
                    pt.reload({totals: show_totals}, null, false);
                }
            });
            
            // Submit
            $(el).find('input.pt-submit').click(function() {
                var options = pt._getOptions(),
                    filters = pt._getFilters();
                pt.reload(options, filters, false);
            });

            // Zoom in
            $('#' + widget_id + ' div.pt-table div.pt-cell-zoom').click(function(event) {
                
                var zoom = $(event.currentTarget);
                var cell = zoom.closest('td'); //parent();
            
                var values = cell.find('.pt-cell-records');
                if (values.length > 0) {
                    values.remove();
                    zoom.removeClass('opened');
                } else {
                    var keys = cell.data('records');

                    values = $('<div/>').addClass('pt-cell-records');
                    
                    var list = $('<ul/>');
                    for (var i=0; i < keys.length; i++) {
                        list.append('<li>' + data.lookup[keys[i]] + '</li>');
                    }
                    values.append(list);
                    cell.append(values);
                    zoom.addClass('opened');
                }
            });
        },

        _unbindEvents: function() {
            // unbind events (before refresh)
            
            var el = this.element;
            var widget_id = $(el).attr('id');

            $(el).find('input.pt-submit').unbind('click');
            $('#' + widget_id + ' div.pt-table div.pt-cell-zoom').unbind('click');
            $('#' + widget_id + '-options legend').unbind('click');
            $('#' + widget_id + '-filters legend').unbind('click');
            $(widget_id + '-totals').unbind('click');
        }
    });
})(jQuery);
