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

        // Default options
        options: {
            showTotals: true,
            ajaxURL: null,
            defaultChart: {
                type: 'breakdown',
                axis: 'rows'
            },
            renderFilter: true,
            renderOptions: true,
            renderChart: true,
            renderTable: true,
            collapseFilter: false,
            collapseOptions: true,
            collapseChart: true,
            collapseTable: false,

            autoSubmit: 1000
        },

        _create: function() {
            // Create the widget
            
            this.id = pivottableID;
            pivottableID += 1;

            this.table = null;
            this.chart = null;
        },

        _init: function() {
            // Update widget options
            
            var el = this.element;

            this.data = null;
            this.table = null;

            this.chart_options = {
                currentChart: null,
                currentDataIndex: null,
                currentSeriesIndex: null
            };

            this.table_options = {
                hidden: false
            };

            var chart = $(el).find('.pt-chart');
            if (chart.length) {
                this.chart = chart.first();
            } else {
                this.chart = null;
            }

            // Hide the form or parts of it?
            if (!this.options.renderFilter && !this.options.renderOptions) {
                $(el).find('.pt-form-container').hide();
            } else {
                var widget_id = $(el).attr('id');
                if (this.options.renderOptions) {
                    $('#' + widget_id + '-options').show();
                    if (this.options.collapseOptions) {
                        $('#' + widget_id + '-options legend').siblings().toggle();
                        $('#' + widget_id + '-options legend').children().toggle();
                    }
                } else {
                    $('#' + widget_id + '-options').hide();
                }
                if (this.options.renderFilter) {
                    $('#' + widget_id + '-filters').show();
                    if (this.options.collapseFilter) {
                        $('#' + widget_id + '-filters legend').siblings().toggle();
                        $('#' + widget_id + '-filters legend').children().toggle();
                    }
                } else {
                    $('#' + widget_id + '-options').hide();
                }
            }

            // Hide the pivot table?
            if (this.options.collapseTable) {
                this.table_options.hidden = true;
                $(el).find('.pt-table').hide();
                $(el).find('.pt-show-table').show();
                $(el).find('.pt-hide-table').hide();
            }

            // Render all initial contents
            this.refresh();
        },

        _destroy: function() {
            // Remove generated elements & reset other changes
            if (this.table) {
                this.table.remove();
            }
            if (this.chart) {
                this.chart.empty();
            }
        },

        refresh: function() {
            // Rre-draw contents
            var el = this.element, data = null;

            this._unbindEvents();

            var pivotdata = $(el).find('input[type="hidden"][name="pivotdata"]');
            if (pivotdata.length) {
                data = JSON.parse($(pivotdata).first().val());
            }
            if (!data) {
                data = {empty: true};
                // Show the empty section
                $(el).find('.pt-hide-table').hide();
                $(el).find('.pt-show-table').hide();
            }
            this.data = data;

            if (data.nodata) {
                $(el).find('.pt-table')
                     .first()
                     .empty()
                     .append($('<div class="pt-no-data">' + data.nodata + '</div>'));
                $(el).find('.pt-hide-table').hide();
                $(el).find('.pt-show-table').hide();
                this._renderChart();

            } else {
                this._renderTable();
                this._renderChartOptions();
                this._renderChart();
            }
            if (data.empty) {
                $(el).find('.pt-empty').show();
            } else {
                $(el).find('.pt-empty').hide();
            }
            if (this.options.autoSubmit) {
                $(el).find('.pt-submit').hide();
            } else {
                $(el).find('.pt-submit').show();
            }
            this._bindEvents();

            $(el).find('.pt-throbber').hide();
        },

        _renderTable: function() {
            // Render the pivot table (according to current options)

            var el = this.element;
            var container = $(el).find('.pt-table').first().empty();

            this.table = null;

            var data = this.data;
            if (data.empty) {
                return;
            }

            if (this.options.renderTable) {
                var cells = data.cells,
                    cols = data.cols,
                    rows = data.rows,
                    total = data.total,
                    labels = data.labels,
                    nodata = data.nodata;

                // Render the table
                var thead = this._renderHeader(cols, labels);

                thead.append(this._renderColumns(cols, labels));

                var tbody = this._renderRows(rows, cols, labels, cells),
                    tfoot = this._renderFooter(rows, cols, labels, total);
                var table = $('<table class="dataTable display report"/>')
                            .append(thead)
                            .append(tbody);
                if (tfoot !== null) {
                    table.append(tfoot);
                }
                this.table = $(table);

                // Show the table
                $(container).append(this.table);

                if (this.table_options.hidden) {
                    $(el).find('.pt-show-table').show();
                    $(el).find('.pt-hide-table').hide();
                } else {
                    $(el).find('.pt-show-table').hide();
                    $(el).find('.pt-hide-table').show();
                }
            } else {
                $(el).find('.pt-show-table').hide();
                $(el).find('.pt-hide-table').hide();
            }
        },

        _renderHeader: function(cols, labels) {
            // Render the pivot table header

            var header = $('<tr>');

            if (cols[cols.length-1][0] == '__other__') {
                colspan = cols.length-1;
            } else {
                colspan = cols.length;
            }

            header.append($('<th scope="col">' + labels['layer'] + '</th>'));

            if (cols.length > 1 || cols[0][4]) {
                header.append($('<th scope="col" colspan="' + colspan + '">' + labels['cols'] + '</th>'));
            }

            if (this.options.showTotals) {
                header.append($('<th class="totals_header row_totals" scope="col" rowspan="2">' + labels.total + '</th>'));
            }
            return $('<thead>').append(header);
        },

        _renderColumns: function(cols, labels) {
            // Render the pivot table column headers

            var columns = $('<tr>'), clabel;

            columns.append($('<th scope="col">' + labels['rows'] + '</th>'));

            var single_col = cols.length == 1 && cols[0][4] === null ? true : false;

            for (var i=0; i < cols.length; i++) {
                if (cols[i][0] != '__other__' && !(single_col && this.options.showTotals)) {
                    clabel = single_col ? "": cols[i][4];
                    columns.append($('<th scope="col">' + clabel + '</th>'));
                }
            }

            return columns;
        },

        _renderRows: function(rows, cols, labels, cells) {
            // Render the pivot table rows

            var tbody = $('<tbody>'),
                show_totals = this.options.showTotals,
                single_row = rows.length == 1 && rows[0][4] === null ? true : false,
                row, tr, rlabel;
            
            for (var i=0; i<cells.length; i++) {
                row = rows[i];
                if (row[0] != '__other__' && !(single_row && this.options.showTotals)) {
                    rlabel = single_row ? "": rows[i][4];
                    tr = $('<tr class="' + (i % 2 ? 'odd': 'even') + '">' + '<td>' + rlabel + '</td></tr>')
                        .append(this._renderCells(cells[i], cols, labels));
                    if (show_totals) {
                        tr.append($('<td>' + row[2] + '</td>'));
                    }
                    tbody.append(tr);
                }
            }
            return tbody;
        },

        _renderCells: function(cells, cols, labels) {
            // Render the pivot table cells

            var cell, items, keys,
                none = labels.none,
                c = "pt-cell-value",
                single_col = cols.length == 1 && cols[0][4] === null ? true : false,
                row = [], column, value;

            
            for (var i = 0; i < cells.length; i++) {

                if (cols[i][0] == '__other__' || (single_col && this.options.showTotals)) {
                    continue;
                }
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
            // Render the pivot table footer

            var single_col = cols.length == 1 && cols[0][4] === null ? true : false;
            if (this.options.showTotals) {

                var i, n;
                for (i = 0, n = 0, len=rows.length; i<len; i++) {
                    if (rows[i][0] != '__other__') {
                        n++;
                    }
                }
                var c = n % 2 ? 'odd' : 'even';
                var footer = $('<tr class="' + c + ' totals_row">' +
                               '<th class="totals_header" scope="row">' +
                               labels.total +
                               '</th></tr>');
                for (i = 0; i < cols.length; i++) {
                    if (cols[i][0] != '__other__' && !single_col) {
                        footer.append($('<td>' + cols[i][2] + '</td>'));
                    }
                }
                footer.append($('<td>' + total + '</td>'));
                return $('<tfoot>').append(footer);

            } else {

                return null;
            }
        },

        _renderChartOptions: function() {
            // Render the chart options (according to current options)

            var el = this.element;
            var container = $(el).find('.pt-chart-controls').first().empty();
            
            var data = this.data;
            if (data.empty || !this.options.renderChart) {
                return;
            }
            var labels = data.labels;

            var widget_id = $(el).attr('id'),
                layer_label = labels.layer,
                rows_label = labels.rows,
                cols_label = labels.cols,
                per = labels.per,
                chart_opts = $('<div class="pt-chart-opts">');
                
            var pchart_rows = widget_id + '-pchart-rows',
                vchart_rows = widget_id + '-vchart-rows',
                hchart_rows = widget_id + '-hchart-rows',
                pchart_cols = widget_id + '-pchart-cols',
                vchart_cols = widget_id + '-vchart-cols',
                hchart_cols = widget_id + '-hchart-cols';

            if (layer_label) {
                $(chart_opts).append($(
                    '<span class="pt-chart-label">' + layer_label + '</span>'
                ));
            }
            if (rows_label) {
                $(chart_opts).append($(
                    '<div id="' + pchart_rows + '" class="pt-chart-icon pt-pchart"/>' +
                    '<div id="' + vchart_rows + '" class="pt-chart-icon pt-vchart"/>' +
                    '<span class="pt-chart-label">' + per + ' ' + rows_label + '</span>'
                ));
            }

            if (cols_label) {
                $(chart_opts).append($(
                    '<div id="' + pchart_cols + '" class="pt-chart-icon pt-pchart"/>' +
                    '<div id="' + vchart_cols + '" class="pt-chart-icon pt-vchart"/>' +
                    '<span class="pt-chart-label">' + per + ' '  + cols_label + '</span>'
                ));
            }

            if (rows_label && cols_label) {
                $(chart_opts).append($(
                    '<span class="pt-chart-label">| ' + labels.breakdown + '</span>' +
                    '<div id="' + hchart_rows + '" class="pt-chart-icon pt-hchart"/>' +
                    '<span class="pt-chart-label">' +
                        [per, rows_label, '&amp;', cols_label].join(' ') +
                    '</span>' +
                    '<div id="' + hchart_cols + '"  class="pt-chart-icon pt-hchart"/>' +
                    '<span class="pt-chart-label">' +
                        [per, cols_label, '&amp;', rows_label].join(' ') +
                    '</span>'
                ));
            }

            // Show the chart options
            $(container).append(chart_opts);
        },
        
        _renderChart: function(chart_options) {
            // Render the chart (according to current options)

            var el = this.element,
                data = this.data;

            // Hide the chart contents section initially
            $(el).find('.pt-chart-contents').hide();

            var chart = this.chart;
            if (chart) {
                $(chart).unbind('plothover').unbind('plotclick').empty();
            } else {
                return;
            }
            if (data.empty || !this.options.renderChart) {
                return;
            }
            if (chart_options === false) {
                this.options.collapseChart = true;
                return;
            }

            var collapseChart = this.options.collapseChart;
            if (typeof chart_options == 'undefined' || !chart_options) {
                if (collapseChart) {
                    return;
                }
                chart_options = this.chart_options.currentChart;
            }
            if (typeof chart_options == 'undefined' || !chart_options) {
                if (collapseChart) {
                    return;
                }
                chart_options = this.options.defaultChart;
            }
            if (typeof chart_options == 'undefined' || !chart_options) {
                return;
            }
            
            this.options.collapseChart = false;
            this.chart_options.currentChart = chart_options;

            var chart_type = chart_options.type,
                chart_axis = chart_options.axis,
                labels = data.labels;

            var per = labels.per,
                rows_title = labels.layer + ' ' + per + ' ' + labels.rows,
                cols_title = labels.layer + ' ' + per + ' ' + labels.cols;

            var filter = data.filter;
            var filter_url = filter[0],
                rows_selector = filter[1],
                cols_selector = filter[2];

            if (chart_type == 'piechart') {
                if (chart_axis == 'rows') {
                    this._renderPieChart(data.rows, rows_title, filter_url, rows_selector);
                } else {
                    this._renderPieChart(data.cols, cols_title, filter_url, cols_selector);
                }
            } else if (chart_type == 'barchart') {
                if (chart_axis == 'rows') {
                    this._renderBarChart(data.rows, rows_title, filter_url, rows_selector);
                } else {
                    this._renderBarChart(data.cols, cols_title, filter_url, cols_selector);
                }
            } else if (chart_type == 'breakdown') {
                if (chart_axis == 'rows') {
                    this._renderBreakDown(data, 0, rows_title, filter);
                } else {
                    this._renderBreakDown(data, 1, cols_title, filter);
                }
            }
        },

        _renderPieChart: function(data, title, filter_url, selector) {
            // Render a pie chart

            var chart = this.chart;
            if (!chart) {
                return;
            }
            $(chart).closest('.pt-chart-contents').show().css({width: '800px'});
            $(chart).css({height: '360px'});

            var items = [];
            for (var i=0; i<data.length; i++) {
                var item = data[i];
                if (!item[1]) {
                    items.push({
                        label: item[4],
                        data: item[2],
                        key: item[3]
                    });
                }
            }

            if (title) {
                $(chart).siblings('.pt-chart-title')
                        .html('<h4>' + title + '</h4>');
            } else {
                $(chart).siblings('.pt-chart-title')
                        .empty();
            }
            reportChart = jQuery.plot($(chart), items, {
                    series: {
                        pie: {
                            show: true,
                            radius: 125
                        }
                    },
                    legend: {
                        show: true,
                        position: 'ne'
                    },
                    grid: {
                        hoverable: true,
                        clickable: true
                    }
                }
            );

            var pt = this;

            // Hover-tooltip
            this.chart_options.currentDataIndex = null;
            $(chart).bind('plothover', function(event, pos, item) {
                if (item) {
                    if (pt.chart_options.currentDataIndex == item.seriesIndex) {
                        return;
                    }
                    pt._removeChartTooltip();
                    pt.chart_options.currentDataIndex = item.seriesIndex;
                    var value = item.series.data[0][1];
                    var percent = item.series.percent.toFixed(1);
                    var tooltip = '<div class="pt-tooltip-label">' + item.series.label + '</div>';
                    tooltip += '<div class="pt-tooltip-text">' + value + ' (' + percent + '%)</div>';
                    pt._renderChartTooltip(pos.pageX, pos.pageY, tooltip);
                    $('.pt-tooltip-label').css({color: item.series.color});
                } else {
                    pt._removeChartTooltip();
                }
            });

            // Click-link to filtered URL
            if (filter_url && selector) {
                $(chart).bind('plotclick', function(event, pos, item) {
                    if (item) {
                        var filter={};
                        try {
                            filter[selector] = items[item.seriesIndex]['key'];
                        }
                        catch(e) {
                            return;
                        }
                        var page = pt._updateURL(filter_url, filter);
                        window.open(page, '_blank');
                    }
                });
            }
        },

        _renderBarChart: function(data, title, filter_url, selector) {
            // Render a (vertical) bar chart

            var chart = this.chart;
            if (!chart) {
                return;
            }
            $(chart).closest('.pt-chart-contents').show().css({width: '96%'});
            $(chart).css({height: '360px'});

            var items = [], labels = [], idx=0;
            for (var i=0; i<data.length; i++) {
                var item = data[i];
                if (!item[1]) {
                    items.push({
                        label: item[4],
                        data: [[idx+1, item[2]]],
                        key: item[3]
                    });
                    labels.push([idx+1, item[4]]);
                    idx++;
                }
            }

            if (title) {
                $(chart).siblings('.pt-chart-title')
                        .html('<h4>' + title + '</h4>');
            } else {
                $(chart).siblings('.pt-chart-title')
                        .empty();
            }
            reportChart = jQuery.plot($(chart), items,
                {
                    series: {
                        bars: {
                            show: true,
                            barWidth: 0.6,
                            align: 'center'
                        }
                    },
                    legend: {
                        show: false,
                        position: 'ne'
                    },
                    grid: {
                        hoverable: true,
                        clickable: true
                    },
                    xaxis: {
                        ticks: labels,
                        min: 0,
                        max: items.length+1,
                        tickLength: 0
                    }
                }
            );

            var pt = this;

            // Hover-tooltip
            this.chart_options.currentDataIndex = null;
            $(chart).bind('plothover', function(event, pos, item) {
                if (item) {
                    if (pt.chart_options.currentDataIndex == item.seriesIndex) {
                        return;
                    }
                    pt._removeChartTooltip();
                    pt.chart_options.currentDataIndex = item.seriesIndex;

                    var value = item.series.data[0][1];
                    var tooltip = '<div class="pt-tooltip-label">' + item.series.label + '</div>';
                    tooltip += '<div class="pt-tooltip-text">' + value + '</div>';
                    pt._renderChartTooltip(pos.pageX, pos.pageY, tooltip);
                    $('.pt-tooltip-label').css({color: item.series.color});
                } else {
                    pt._removeChartTooltip();
                }
            });
            
            // Click-link to filtered URL
            if (filter_url && selector) {
                $(chart).bind('plotclick', function(event, pos, item) {
                    if (item) {
                        var filter={};
                        try {
                            filter[selector] = items[item.seriesIndex]['key'];
                        }
                        catch(e) {
                            return;
                        }
                        var page = pt._updateURL(filter_url, filter);
                        window.open(page, '_blank');
                    }
                });
            }
        },

        _renderBreakDown: function(data, dim, title, filter) {
            // Render a breakdown (2-dimensional horizontal bar chart)

            var chart = this.chart;
            if (!chart) {
                return;
            }
            $(chart).closest('.pt-chart-contents').show().css({width: '96%'});

            var filter_url = filter[0], rows_selector, cols_selector;

            var cells = data.cells, rdim, cdim, get_data, ridx = [], cidx = [];
            if (dim === 0) {
                rdim = data.rows;
                cdim = data.cols;
                get_data = function(i, j) {
                    var ri = ridx[i], ci = cidx[j];
                    return cells[ri][ci]['value'];
                };
                rows_selector = filter[1];
                cols_selector = filter[2];
            } else {
                rdim = data.cols;
                cdim = data.rows;
                get_data = function(i, j) {
                    var ri = ridx[i], ci = cidx[j];
                    return cells[ci][ri]['value'];
                };
                rows_selector = filter[2];
                cols_selector = filter[1];
            }

            var i, rows = [], cols = [];
            for (i=0, len=rdim.length; i < len; i++) {
                if (!rdim[i][1]) {
                    rows.push(rdim[i]);
                    ridx.push(i);
                }
            }
            for (i=0, len=cdim.length; i < len; i++) {
                if (!cdim[i][1]) {
                    cols.push(cdim[i]);
                    cidx.push(i);
                }
            }

            var height = Math.max(rows.length * Math.max((cols.length + 1) * 16, 50) + 70, 360);
            $(chart).css({height: height + 'px'});

            var odata = [], xmax = 0;
            for (var c=0; c < cols.length; c++) {
                // every col gives a series
                var series = {label: cols[c][4]}, values = [], index, value;
                for (var r=0; r < rows.length; r++) {
                    index = (rows.length - r) * (cols.length + 1) - c;
                    value = get_data(r, c);
                    if (value > xmax) {
                        xmax = value;
                    }
                    values.push([value, index]);
                }
                series['data'] = values;
                odata.push(series);
            }

            var yaxis_ticks = [], label;
            for (r=0; r < rows.length; r++) {
                label = rows[r][4];
                index = (rows.length - r) * (cols.length + 1) + 1;
                yaxis_ticks.push([index, label]);
            }

            if (title) {
                $(chart).siblings('.pt-chart-title')
                        .html('<h4>' + title + '</h4>');
            } else {
                $(chart).siblings('.pt-chart-title')
                        .empty();
            }
            reportChart = jQuery.plot($(chart), odata, {
                    series: {
                        bars: {
                            show: true,
                            barWidth: 0.8,
                            align: 'center',
                            horizontal: true
                        }
                    },
                    legend: {
                        show: true,
                        position: 'ne'
                    },
                    yaxis: {
                        ticks: yaxis_ticks,
                        labelWidth: 120,
                        max: (rows.length) * (cols.length + 1) + 1
                    },
                    xaxis: {
                        max: xmax * 1.1
                    },
                    grid: {
                        hoverable: true,
                        clickable: true
                    }
                }
            );
            $('.flot-y-axis .tickLabel').css({
                'padding-top': '20px',
                'left': '0px', // prevent left-overflow
                'width': '120px'
            });

            var pt = this;

            // Hover-tooltip
            this.chart_options.currentDataIndex = null;
            this.chart_options.currentSeriesIndex = null;
            $(chart).bind('plothover', function(event, pos, item) {

                if (item) {
                    if (pt.chart_options.currentDataIndex == item.dataIndex &&
                        pt.chart_options.currentSeriesIndex == item.seriesIndex) {
                        return;
                    }
                    pt._removeChartTooltip();
                    pt.chart_options.currentDataIndex = item.dataIndex;
                    pt.chart_options.currentSeriesIndex = item.seriesIndex;

                    var name = rows[item.dataIndex][4];
                    var value = item.datapoint[0];
                    var tooltip = '<div class="pt-tooltip-label">' + name + '</div>';
                    tooltip += '<div class="pt-tooltip-text">' + item.series.label + ' : <span class="pt-tooltip-value">' + value + '</span></div>';
                    pt._renderChartTooltip(pos.pageX, pos.pageY, tooltip);
                    $('.pt-tooltip-label').css({'padding-bottom': '8px'});
                    $('.pt-tooltip-text').css({color: item.series.color});
                    $('.pt-tooltip-value').css({'font-weight': 'bold'});
                } else {
                    pt._removeChartTooltip();
                }
            });

            // Click-link to filtered URL
            if (filter_url && rows_selector && cols_selector) {
                $(chart).bind('plotclick', function(event, pos, item) {
                    if (item) {
                        var filter = {};
                        try {
                            filter[rows_selector] = rows[item.dataIndex][3];
                            filter[cols_selector] = cols[item.seriesIndex][3];
                        }
                        catch(e) {
                            return;
                        }
                        var page = pt._updateURL(filter_url, filter);
                        window.open(page, '_blank');
                    }
                });
            }
        },

        _renderChartTooltip: function(x, y, contents) {
            // Render a hover-tooltip for a chart data point
            
            $('<div class="pt-chart-tooltip">' + contents + '</div>').css({
                position: 'absolute',
                display: 'none',
                top: y - 50,
                left: x + 10,
                border: '1px solid #999',
                'padding': '10px',
                'min-height': '50px',
                'max-width': '240px',
                'z-index': '501',
                'background-color': 'white',
                color: '#000',
                opacity: 0.95
            }).appendTo('body').fadeIn(200);
        },

        _removeChartTooltip: function() {
            // Remove all hover-tooltips for chart data points
            
            $('.pt-chart-tooltip').remove();
            this.chart_options.currentDataIndex = null;
            this.chart_options.currentSeriesIndex = null;
        },

        _getOptions: function() {
            // Get current report options form the report options form

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
            // Get current filters from the filter form

            var widget_id = '#' + $(this.element).attr('id');

            var filters = $(widget_id + '-filters'), filter_options = [];
            try {
                if (filters.length) {
                    return S3.search.getCurrentFilters(filters.first());
                } else {
                    return null;
                }
            } catch (e) {}

        },

        _updateURL: function(url, filters) {
            // Update a URL with new filters

            // Construct the URL
            var url_parts = url.split('?'), query = {};

            if (url_parts.length > 1) {
                var qstr = url_parts[1];

                var a = qstr.split('&'),
                b, v, i, len;
                for (i=0, len=a.length; i < len; i++) {
                    b = a[i].split('=');
                    if (b.length > 1) {
                        query[decodeURIComponent(b[0])] = decodeURIComponent(b[1]);
                    }
                }
            }

            if (filters) {
                for (option in filters) {
                    newopt = filters[option];
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
            return filtered_url;
        },
        
        _updateAjaxURL: function(options, filters) {
            // Update the Ajax URL with new options and filters

            var ajaxURL = this.options.ajaxURL;

            // Construct the URL
            var url_parts = ajaxURL.split('?'),
                url_query = null,
                query = [];
                needs_reload = false;

            var qstr, url_vars;
            
            if (url_parts.length > 1) {
                qstr = url_parts[1];
                url_vars = qstr.split('&');
            } else {
                qstr = '';
                url_vars = [];
            }

            var option, q;
            if (options) {
                for (option in options) {
                    newopt = options[option];
                    q = option + '=' + newopt;
                    if (option == 'totals') {
                        this.options.showTotals = newopt ? true : false;
                    } else if (!(needs_reload || $.inArray(q, url_vars) != -1 )) {
                        needs_reload = true;
                    }
                    query.push(q);
                }
            }
            
            var update = {},
                remove = {},
                i, len, q, k, v;

            // Check filters to update/remove (we're not using
            // S3.search.filterURL here, but an experimental
            // lazy-reload-pattern, i.e. we only reload data
            // if the filter or a pivot axis have actually changed.)
            if (filters) {
                for (i=0, len=filters.length; i < len; i++) {
                    q = filters[i];
                    k = q[0];
                    v = q[1];
                    if (v === null) {
                        if (!update[k]) {
                            remove[k] = true;
                        }
                    } else {
                        if (remove[k]) {
                            remove[k] = false;
                        }
                        if (update[k]) {
                            update[k].push(k + '=' + v);
                        } else {
                            update[k] = [k + '=' + v];
                        }
                    }
                }
            }

            // Check which existing URL query vars to retain/replace
            for (i=0, len=url_vars.length; i < len; i++) {
                q = url_vars[i].split('=');
                if (q.length > 1) {
                    k = decodeURIComponent(q[0]);
                    v = decodeURIComponent(q[1]);

                    if (remove[k]) {
                        needs_reload = true;
                        continue;
                    } else if (update[k]) {
                        if (!(needs_reload || $.inArray(k + '=' + v, update[k]) != -1)) {
                            needs_reload = true;
                        }
                        // Will be replaced
                        continue;
                    } else if (k == 'aggregate') {
                        // Remove
                        continue;
                    } else if (options && options.hasOwnProperty(k)) {
                        continue;
                    } else {
                        // Keep this
                        query.push(url_vars[i]);
                    }
                }
            }

            // Add new filters
            for (k in update) {
                for (i=0, len=update[k].length; i < len; i++) {
                    if (!(needs_reload || $.inArray(update[k][i], url_vars) != -1)) {
                        needs_reload = true;
                    }
                    query.push(update[k][i]);
                }
            }

            var url_query = query.join('&'),
                filtered_url = url_parts[0];
            if (url_query) {
                filtered_url = filtered_url + '?' + url_query;
            }
            this.options.ajaxURL = filtered_url;
            return needs_reload;
        },

        reload: function(options, filters, force) {
            // Ajax-reload the pivot data and refresh all widget elements

            force = typeof force != 'undefined' ? force : true;

            if (typeof filters == 'undefined') {
                // extract filters
                filters = this._getFilters();
            }

            var pt = this,
                el = this.element,
                needs_reload;
            
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
                $(el).find('.pt-empty').hide();
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
            // Bind events to generated elements (after refresh)

            var pt = this,
                el = this.element;
                data = this.data;
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

            // Show/hide pivot table
            $(el).find('.pt-hide-table').click(function() {
                pt.table_options.hidden = true;
                $(el).find('.pt-table').hide();
                $(this).siblings('.pt-show-table').show();
                $(this).hide();
            });
            $(el).find('.pt-show-table').click(function() {
                pt.table_options.hidden = false;
                $(el).find('.pt-table').show();
                $(this).siblings('.pt-hide-table').show();
                $(this).hide();
            });

            // Totals-option doesn't need Ajax-refresh
            $('#' + widget_id + '-totals').click(function() {
                var show_totals = $(this).is(':checked');
                if (pt.options.showTotals != show_totals) {
                    pt.reload({totals: show_totals}, null, false);
                }
            });
            
            // Axis selectors to fire optionChanged-event
            $('#' + widget_id + '-rows, #' +
                    widget_id + '-cols, #' +
                    widget_id + '-fact').on('change.autosubmit', function() {
                $(el).find('.pt-form').trigger('optionChanged');
            });

            // Form submission
            if (this.options.autoSubmit) {
                // Auto-submit
                var timeout = this.options.autoSubmit;
                $(el).find('.pt-form').on('optionChanged', function() {
                    var that = $(this);
                    if (that.data('noAutoSubmit')) {
                        // Event temporarily disabled
                        return;
                    }
                    var timer = that.data('autoSubmitTimeout');
                    if (timer) {
                        clearTimeout(timer);
                    }
                    timer = setTimeout(function () {
                        var options = pt._getOptions(),
                            filters = pt._getFilters();
                        pt.reload(options, filters, false);
                    }, timeout);
                    that.data('autoSubmitTimeout', timer);
                });
            } else {
                // Manual submit
                $(el).find('input.pt-submit').click(function() {
                    var options = pt._getOptions(),
                        filters = pt._getFilters();
                    pt.reload(options, filters, false);
                });
            }

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

            // Charts
            $('#' + widget_id + '-pchart-rows').click(function() {
                pt._renderChart({type: 'piechart', axis: 'rows'});
            });
            $('#' + widget_id + '-vchart-rows').click(function() {
                pt._renderChart({type: 'barchart', axis: 'rows'});
            });
            $('#' + widget_id + '-pchart-cols').click(function() {
                pt._renderChart({type: 'piechart', axis: 'cols'});
            });
            $('#' + widget_id + '-vchart-cols').click(function() {
                pt._renderChart({type: 'barchart', axis: 'cols'});
            });
            $('#' + widget_id + '-hchart-rows').click(function() {
                pt._renderChart({type: 'breakdown', axis: 'rows'});
            });
            $('#' + widget_id + '-hchart-cols').click(function() {
                pt._renderChart({type: 'breakdown', axis: 'cols'});
            });
            $(el).find('.pt-hide-chart').click(function () {
                pt._renderChart(false);
            });
        },

        _unbindEvents: function() {
            // Unbind events (before refresh)
            
            var el = this.element;
            var widget_id = $(el).attr('id');

            $('#' + widget_id + ' div.pt-table div.pt-cell-zoom').unbind('click');
            $('#' + widget_id + '-options legend').unbind('click');
            $('#' + widget_id + '-filters legend').unbind('click');
            
            $(widget_id + '-totals').unbind('click');

            $('#' + widget_id + '-rows, #' +
                    widget_id + '-cols, #' +
                    widget_id + '-fact').unbind('change.autosubmit');
                    
            $(el).find('.pt-form').unbind('optionChanged');
            $(el).find('input.pt-submit').unbind('click');

            $('#' + widget_id + '-pchart-rows').unbind('click');
            $('#' + widget_id + '-vchart-rows').unbind('click');
            $('#' + widget_id + '-pchart-cols').unbind('click');
            $('#' + widget_id + '-vchart-cols').unbind('click');
            
            $(el).find('.pt-hide-table').unbind('click');
            $(el).find('.pt-show-table').unbind('click');
            
            $(el).find('.pt-hide-chart').unbind('click');
            
        }
    });
})(jQuery);
