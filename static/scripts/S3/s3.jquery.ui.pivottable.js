/**
 * jQuery UI pivottable Widget for S3Report
 *
 * @copyright: 2013-14 (c) Sahana Software Foundation
 * @license: MIT
 *
 * requires: jQuery 1.9.1+
 * requires: jQuery UI 1.10 widget factory
 * requires: D3.js 3.4.9+
 *
 */

(function($, undefined) {

    "use strict";
    var pivottableID = 0;

    /**
     * Pivottable Report
     */
    $.widget('s3.pivottable', {

        /**
         * Default options
         *
         * @prop {bool} showTotals - show totals in pivot table
         * @prop {string} ajaxURL - the URL to Ajax-load data from
         * @prop {object} defaultChart - the chart to show at start
         * @prop {bool} renderFilter - render a filter form
         * @prop {bool} renderOptions - render a report options form
         * @prop {bool} renderChart - render charts
         * @prop {bool} renderTable - render the pivot table
         * @prop {bool} collapseFilter - start with filter form collapsed
         * @prop {bool} collapseOptions - start with report options form collapsed
         * @prop {bool} collapseChart - start with chart collapsed (hidden)
         * @prop {bool} collapseTable - start with pivot table collapsed (hidden)
         * @prop {bool} exploreChart - activate chart-explore function
         * @prop {string} filterURL - URL to forward to upon plot-click (chart-explore)
         * @prop {string} filterForm - ID of the filter form to update upon plot-click (chart-explore),
         *                             default: '#filterform'
         * @prop {string} filterTab - ID of the summary-tab to activate upon plot-click (chart-explore),
         *                            default: first tab
         * @prop {number|bool} autoSubmit - auto-submit timeout, false to
         *                                  deactivate auto-submit
         * @prop {string} thousandSeparator - character to use as thousand-separator
         * @prop {string|number} thousandGrouping - number of digits to group with thousand-separator
         * @prop {number} minTickSize - the minimum interval between two y-axis ticks
         * @prop {number} precision - the number of decimals to show on y-axis ticks
         */
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

            exploreChart: false,        // Activate/deactivate chart-explore function
            filterURL: null,            // URL to forward to upon plot-click
            filterForm: null,           // ID of the filter form to update
                                        // (default: #filter-form)
            filterTab: null,            // ID of the summary tab to activate upon
                                        // plot-click (default: first tab)

            autoSubmit: 1000,
            thousandSeparator: ' ',
            thousandGrouping: '3',
            minTickSize: null,
            precision: null,
            textAll: 'All'
        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = pivottableID;
            pivottableID += 1;

            this.table = null;
            this.chart = null;
        },

        /**
         * Update widget options
         */
        _init: function() {

            var $el = $(this.element),
                opts = this.options;

            this.data = null;
            this.table = null;

            this.chartOptions = {
                currentChart: null,
                currentDataIndex: null,
                currentSeriesIndex: null,
                currentSpectrumIndex: null
            };

            this.table_options = {
                hidden: false
            };

            var chart = $el.find('.pt-chart');
            if (chart.length) {
                this.chart = chart.first();
            } else {
                this.chart = null;
            }

            // Hide the form or parts of it?
            if (!opts.renderFilter && !opts.renderOptions) {
                $el.find('.pt-form-container').hide();
            } else {
                var widgetID = '#' + $el.attr('id');
                if (opts.renderOptions) {
                    $(widgetID + '-options').show();
                    if (opts.collapseOptions) {
                        $(widgetID + '-options legend').siblings().toggle();
                        $(widgetID + '-options legend').children().toggle();
                    }
                } else {
                    $(widgetID + '-options').hide();
                }
                if (opts.renderFilter) {
                    $(widgetID + '-filters').show();
                    if (opts.collapseFilter) {
                        $(widgetID + '-filters legend').siblings().toggle();
                        $(widgetID + '-filters legend').children().toggle();
                    }
                } else {
                    $(widgetID + '-options').hide();
                }
            }

            // Hide the pivot table?
            if (opts.collapseTable) {
                this.table_options.hidden = true;
                $el.find('.pt-table').hide();
                $el.find('.pt-show-table').show();
                $el.find('.pt-hide-table').hide();
            }

            // Define number formatter
            opts.numberFormatter = function(number) {

                var decimals = opts.precision;
                if (number === null || typeof number == 'undefined') {
                    return '-';
                }
                var n = decimals || decimals == 0 ? number.toFixed(decimals) : number.toString();

                n = n.split('.');
                var n1 = n[0],
                    n2 = n.length > 1 ? '.' + n[1] : '';
                var re = new RegExp('\\B(?=(\\d{' + opts.thousandGrouping + '})+(?!\\d))', 'g');
                n1 = n1.replace(re, opts.thousandSeparator);
                return n1 + n2;
            };

            // Render all initial contents
            this.refresh();
        },

        /**
         * Remove generated elements & reset other changes
         */
        _destroy: function() {

            if (this.table) {
                this.table.remove();
            }
            if (this.chart) {
                this.chart.empty();
            }
        },

        /**
         * Re-draw contents
         */
        refresh: function() {

            var $el = $(this.element),
                data = null;

            this._unbindEvents();

            var pivotdata = $el.find('input[type="hidden"][name="pivotdata"]');
            if (pivotdata.length) {
                data = JSON.parse($(pivotdata).first().val());
            }

            if (!data) {
                data = {empty: true};
                // Show the empty section
                $el.find('.pt-hide-table').hide();
                $el.find('.pt-show-table').hide();
            } else if (data.method == 'count') {
                // Charts should show integers if method is 'count'
                this.options.precision = 0;
                this.options.minTickSize = 1;
            }
            this.data = data;

            if (data.nodata) {
                $el.find('.pt-table')
                   .first()
                   .empty()
                   .append($('<div class="pt-no-data">' + data.nodata + '</div>'));
                $el.find('.pt-hide-table').hide();
                $el.find('.pt-show-table').hide();
                this._renderChart();
            } else {
                this._renderTable();
                this._renderChartOptions();
                this._renderChart();
            }
            if (data.empty) {
                $el.find('.pt-empty').show();
            } else {
                $el.find('.pt-empty').hide();
            }
            if (this.options.autoSubmit) {
                $el.find('.pt-submit').hide();
            } else {
                $el.find('.pt-submit').show();
            }
            this._bindEvents();

            $el.find('.pt-throbber').hide();
        },

        /**
         * Render the pivot table (according to current options)
         */
        _renderTable: function() {

            var $el = $(this.element);
            var container = $el.find('.pt-table').first().empty();

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

                var opts = this.options;
                var showTotals = opts.showTotals;

                // @todo: explain
                var singleColumn = false;
                if (cols.length == 1 && cols[0][4] === null) {
                    singleColumn = true;
                }
                cells = data.cells.slice(0);
                var i;
                if (singleColumn && showTotals) {
                    cols = [];
                    for (i=0; i<rows.length; i++) {
                        cells[i] = [];
                    }
                } else {
                    for (i=0; i<rows.length; i++) {
                        cells[i] = cells[i].filter(function(cell, cidx) {
                            return cols[cidx][0] != '__other__';
                        });
                    }
                    cols = cols.filter(function(col) {
                        return col[0] != '__other__';
                    });
                }

                // @todo: explain
                var singleRow = false;
                if (cols.length == 1 && cols[0][4] === null) {
                    singleRow = true;
                }
                if (singleRow && showTotals) {
                    rows = [];
                    cells = [];
                } else {
                    cells = cells.filter(function(row, ridx) {
                        return rows[ridx][0] != '__other__';
                    });
                    rows = rows.filter(function(row) {
                        return row[0] != '__other__';
                    });
                }

                // The table
                var table = d3.select(container.get(0))
                              .append('table')
                              .attr('class', 'dataTable display report');

                // Table header and column labels
                table.append('thead')
                     .call(this._renderHeader, cols, labels, opts)
                     .call(this._renderColumns, cols, labels, opts);

                // Table rows and cells
                var pt = this;
                table.append('tbody')
                     .call(this._renderRows, pt, rows, cols, labels, cells, opts);

                // Table footer with totals
                if (opts.showTotals) {
                    table.append('tfoot')
                         .call(this._renderFooter, rows, cols, labels, total);
                }

                // Map table to a jQuery-enhanced node
                this.table = $(table.node());

                if (this.table_options.hidden) {
                    $el.find('.pt-show-table').show();
                    $el.find('.pt-hide-table').hide();
                } else {
                    $el.find('.pt-show-table').hide();
                    $el.find('.pt-hide-table').show();
                }
            } else {
                $el.find('.pt-show-table').hide();
                $el.find('.pt-hide-table').hide();
            }
        },

        /**
         * Render the pivot table header
         *
         * @param {node} thead - the table header D3 node
         * @param {array} cols - the pivot table columns
         * @param {object} labels - the labels
         * @param {object} opts - the configuration options
         *
         * @todo: optimize parameter list (pass in data? use "this"?)
         * @todo: get cols, labels and opts from this or pass in pt?
         * @todo: use dashes in CSS classes instead of underscores
         */
        _renderHeader: function(thead, cols, labels, opts) {

            var header = thead.append('tr');
            header.append('th')
                  .attr('scope', 'col')
                  .text(labels.layer);

            if (cols.length) {
                header.append('th')
                      .attr({'scope': 'col',
                             'colspan': cols.length
                             })
                      .text(labels.cols);
            }
            if (opts.showTotals) {
                header.append('th')
                      .attr({'scope': 'col',
                             'class': 'pt-totals-header pt-row-total',
                             'rowspan': 2
                             })
                      .text(labels.total);
            }
            return header;
        },

        /**
         * Render the pivot table column headers
         *
         * @param {node} thead - the table header D3 node
         * @param {array} cols - the pivot table columns
         * @param {object} labels - the labels
         * @param {object} opts - the configuration options
         *
         * @todo: optimize parameter list (pass in data? use "this"?)
         * @todo: get cols, labels and opts from this or pass in pt?
         * @todo: use dashes in CSS classes instead of underscores
         */
        _renderColumns: function(thead, cols, labels, opts) {

            var columns = thead.append('tr');

            // Append the rows header
            columns.append('th')
                   .attr({'scope': 'col',
                          'class': 'pt-rows-header'
                          })
                   .text(labels.rows);

            // Append the column labels
            var showTotals = opts.showTotals,
                singleColumn = false;
            if (cols.length == 1 && cols[0][4] === null) {
                singleColumn = true;
            }
            columns.selectAll('th.pt-data')
                   .data(cols)
                   .enter()
                   .append('th')
                   .attr({'scope': 'col',
                          'class': 'pt-col-label'
                          })
                   .text(function(d) {
                       if (singleColumn) {
                           return '';
                       } else {
                           return d[4];
                       }
                    });
            return columns;
        },

        /**
         * Render the pivot table rows
         *
         * @param {node} tbody - the table body D3 node
         * @param {object} pt - the reference to the pivot table (to access functions)
         * @param {array} rows - the pivot table rows
         * @param {array} cols - the pivot table columns
         * @param {object} labels - the labels
         * @param {array} cells - the pivot table cells
         * @param {object} opts - the configuration options
         *
         * @todo: optimize parameter list (pass in data? use "this"?)
         * @todo: get rows, cols and cells from data
         * @todo: get data from pt
         * @todo: get opts from pt
         * @todo: get labels from pt
         */
        _renderRows: function(tbody, pt, rows, cols, labels, cells, opts) {

            var rows = tbody.selectAll('tr.pt-row')
                            .data(rows)
                            .enter()
                            .append('tr')
                            .attr('class', function(d, i) { return i % 2 ? 'odd': 'even'; });

            // Render the row header
            var singleRow = false;
            if (rows.length == 1 && rows[0][4] === null) {
                singleRow = true;
            }
            rows.append('td')
                .text(function(d) {
                    if (singleRow) {
                        return '';
                    } else {
                        return d[4];
                    }
                });

            // Render the cells in this row
            rows.selectAll('td.pt-cell')
                .data(function(d, i) { return cells[i]; })
                .enter()
                .append('td')
                .attr('class', 'pt-cell')
                .each(pt._renderCell, labels);

            // Render the row total
            if (opts.showTotals) {
                rows.append('td')
                    .attr('class', 'pt-row-total')
                    .text(function(d) {
                        return d[2];
                    });
            }
            return rows;
        },

        /**
         * Render a pivot table cell
         *
         * @param {object} data - the pivot table cell data
         * @param {number} index - column index, unused
         * @param {object} labels - the labels
         */
        _renderCell: function(data, index, labels) {

            var column = d3.select(this),
                items = data.items;

            var value = column.append('div')
                              .attr('class', 'pt-cell-value');
            if (items === null) {
                value.text(labels.none);
            } else if ($.isArray(items)) {
                value.append('ul')
                     .selectAll('li')
                     .data(items)
                     .enter()
                     .append('li')
                     .html(function(d) { return d; });
            } else {
                value.text(items);
            }

            var keys = data.keys;
            if (items && keys && keys.length) {
                $(column.node()).data('records', keys);
                column.append('div')
                      .attr('class', 'pt-cell-zoom');
            }
        },

        /**
         * Render the pivot table footer (totals row)
         *
         * @param {node} tfoot - the table footer D3 node
         * @param {array} rows - the rows data
         * @param {array} cols - the columns data
         * @param {object} labels - the labels
         */
        _renderFooter: function(tfoot, rows, cols, labels, total) {

            // Totals row
            var rowClass;
            if (rows.length % 2) {
                rowClass = 'odd';
            } else {
                rowClass = 'even';
            }
            var footer = tfoot.append('tr')
                              .attr('class', rowClass + ' pt-totals-row');

            // Totals header
            footer.append('th')
                  .attr({'class': 'pt-totals-header',
                         'scope': 'row'
                         })
                  .text(labels.total);

            // Column totals
            footer.selectAll('td.pt-col-total')
                  .data(cols)
                  .enter()
                  .append('td')
                  .attr('class', 'pt-col-total')
                  .text(function(col) { return col[2]; });

            // Grand total
            footer.append('td')
                  .attr('class', 'pt-total')
                  .text(total);

            return footer;
        },

        /**
         * Render the chart options (according to current options)
         */
        _renderChartOptions: function() {

            var $el = $(this.element);
            var container = $el.find('.pt-chart-controls').first().empty();

            var data = this.data;
            if (data.empty || !this.options.renderChart) {
                return;
            }
            var labels = data.labels;

            var widgetID = $el.attr('id'),
                layerLabel = labels.layer,
                rowsLabel = labels.rows,
                colsLabel = labels.cols,
                per = labels.per,
                chartOpts = $('<div class="pt-chart-opts">');

            var pchartRows = widgetID + '-pchart-rows',
                vchartRows = widgetID + '-vchart-rows',
                hchartRows = widgetID + '-hchart-rows',
                schartRows = widgetID + '-schart-rows',
                pchartCols = widgetID + '-pchart-cols',
                vchartCols = widgetID + '-vchart-cols',
                hchartCols = widgetID + '-hchart-cols',
                schartCols = widgetID + '-schart-cols';

            if (layerLabel) {
                $(chartOpts).append($(
                    '<span class="pt-chart-label">' + layerLabel + ': </span>'
                ));
            }
            if (rowsLabel) {
                $(chartOpts).append($(
                    '<div id="' + pchartRows + '" class="pt-chart-icon pt-pchart"/>' +
                    '<div id="' + vchartRows + '" class="pt-chart-icon pt-vchart"/>' +
                    '<span class="pt-chart-label">' + per + ' ' + rowsLabel + '</span>'
                ));
            }

            if (colsLabel) {
                $(chartOpts).append($(
                    '<div id="' + pchartCols + '" class="pt-chart-icon pt-pchart"/>' +
                    '<div id="' + vchartCols + '" class="pt-chart-icon pt-vchart"/>' +
                    '<span class="pt-chart-label">' + per + ' '  + colsLabel + '</span>'
                ));
            }

            if (rowsLabel && colsLabel) {
                $(chartOpts).append($(
                    '<span class="pt-chart-label">| ' + labels.breakdown + ': </span>' +
                    '<div id="' + schartRows + '" class="pt-chart-icon pt-schart"/>' +
                    '<div id="' + hchartRows + '" class="pt-chart-icon pt-hchart"/>' +
                    '<span class="pt-chart-label">' + per + ' ' + rowsLabel + '</span>' +
                    '<div id="' + schartCols + '"  class="pt-chart-icon pt-schart"/>' +
                    '<div id="' + hchartCols + '"  class="pt-chart-icon pt-hchart"/>' +
                    '<span class="pt-chart-label">' + per + ' ' + colsLabel + '</span>'
                ));
            }

            // Show the chart options
            $(container).append(chartOpts);
        },

        /**
         * Truncate a label
         *
         * @param {string} label - the label
         * @param {number} len - the desired maximum length
         */
        _truncateLabel: function(label, len) {

            if (label && label.length > len) {
                return label.substring(0, len-3).replace(/\s+$/g,'') + '...';
            } else {
                return label;
            }

        },

        /**
         * Render the chart (according to current options)
         *
         * @param {object} chartOptions - the chart options
         */
        _renderChart: function(chartOptions) {

            var $el = $(this.element),
                data = this.data;

            // Hide the chart contents section initially
            $el.find('.pt-chart-contents').hide();

            var chart = this.chart;
            if (chart) {
                $(chart).unbind('plothover').unbind('plotclick').empty();
            } else {
                return;
            }
            if (data.empty || !this.options.renderChart) {
                return;
            }
            if (chartOptions === false) {
                this.options.collapseChart = true;
                return;
            }

            var collapseChart = this.options.collapseChart;
            if (typeof chartOptions == 'undefined' || !chartOptions) {
                if (collapseChart) {
                    return;
                }
                chartOptions = this.chartOptions.currentChart;
            }
            if (typeof chartOptions == 'undefined' || !chartOptions) {
                if (collapseChart) {
                    return;
                }
                chartOptions = this.options.defaultChart;
            }
            if (typeof chartOptions == 'undefined' || !chartOptions) {
                return;
            }

            this.options.collapseChart = false;
            this.chartOptions.currentChart = chartOptions;

            var chartType = chartOptions.type,
                chartAxis = chartOptions.axis,
                labels = data.labels;

            var per = labels.per,
                rowsTitle = labels.layer + ' ' + per + ' ' + labels.rows,
                colsTitle = labels.layer + ' ' + per + ' ' + labels.cols;

            var filter = data.filter;
            var filter_url = this.options.filterURL,
                rows_selector = filter[0],
                cols_selector = filter[1];

            if (chartType == 'piechart') {
                if (chartAxis == 'rows') {
                    this._renderPieChart(data.rows, rowsTitle, rows_selector);
                } else {
                    this._renderPieChart(data.cols, colsTitle, cols_selector);
                }
            } else if (chartType == 'barchart') {
                if (chartAxis == 'rows') {
                    this._renderBarChart(data.rows, rowsTitle, rows_selector);
                } else {
                    this._renderBarChart(data.cols, colsTitle, cols_selector);
                }
            } else if (chartType == 'breakdown') {
                if (chartAxis == 'rows') {
                    this._renderBreakDown(data, 0, rowsTitle, filter);
                } else {
                    this._renderBreakDown(data, 1, colsTitle, filter);
                }
            } else if (chartType == 'spectrum') {
                this._renderSpectrum(data, chartAxis, filter);
            }
        },

        /**
         * Render a pie chart
         *
         * @param {array} data - the axis data
         * @param {string} title - the chart title
         * @param {string} selector - the field selector for the axis (for filtering)
         */
        _renderPieChart: function(data, title, selector) {

            // Get the chart container
            var chart = this.chart;
            if (!chart) {
                return;
            }

            // Container width + height
            // @todo: adapt dynamically?
            var width = 800,
                height = 360;
            $(chart).css({height: height + 'px'})
                    .closest('.pt-chart-contents')
                    .show()
                    .css({width: '98%'});

            // Add title
            if (title) {
                $(chart).siblings('.pt-chart-title')
                        .html('<h4>' + title + '</h4>');
            } else {
                $(chart).siblings('.pt-chart-title')
                        .empty();
            }

            // Generate the items
            var items = [], total = 0;
            for (var i=0; i<data.length; i++) {
                var item = data[i];
                if (!item[1] && item[2] >= 0) {
                    items.push({
                        index: item[0],
                        label: item[4],
                        value: item[2],
                        key: item[3]
                    });
                    total += item[2];
                }
            }

            // On-hover data point tooltip
            var pt = this;
            pt.chartOptions.currentDataIndex = null;
            var onhoverTooltip = function(e) {

                if (pt.chartOptions.currentDataIndex == e.pointIndex) {
                    // Already open
                    return;
                }
                // Close any open tooltip
                pt._removeChartTooltip();
                pt.chartOptions.currentDataIndex = e.pointIndex;

                // Get the data point data
                var value = e.value;
                var percent = Math.round((value / total) * 100);

                // Create the tooltip
                var tooltip = '<div class="pt-tooltip-label">' + e.label + '</div>';
                tooltip += '<div class="pt-tooltip-text">' + value + ' (' + percent + '%)</div>';
                pt._renderChartTooltip(e.pos[0], e.pos[1], tooltip);

                $('.pt-tooltip-label').css({
                    color: nv.utils.defaultColor()({}, e.pointIndex)
                });
            };

            nv.addGraph(function() {

                var reportChart = nv.models.pieChart()
                                           .x(function(d) { return d.label; })
                                           .y(function(d) { return d.value; })
                                           .pieLabelsOutside(false)
                                           .labelType('percent')
                                           .labelThreshold(0.03)
                                           .showLegend(true)
                                           .tooltips(false);

                reportChart.legend.align(true)
                                  .rightAlign(false);

                reportChart.pie.dispatch.on('elementMouseover', onhoverTooltip)
                                        .on('elementMouseout', function(e) {
                    $('.pt-tooltip').remove();
                    pt.chartOptions.currentDataIndex = null;
                    pt.chartOptions.currentSeriesIndex = null;
                });

                if (pt.options.exploreChart && selector) {
                    reportChart.pie.dispatch.on('elementClick', function(e) {
                        var data = e.point;
                        var index = data.index,
                            key = data.key,
                            fvar;
                        if (index == '__other__') {
                            fvar = selector + '__belongs';
                        } else {
                            fvar = selector;
                        }
                        pt._chartExplore([[fvar, key]]);
                    });
                }

                d3.select($(chart).get(0))
                  .append('svg')
                  .attr('class', 'nv')
                  .datum(items)
                  .transition().duration(1200)
                  .call(reportChart);

                nv.utils.windowResize(reportChart.update);
                return reportChart;
            });
        },

        /**
         * Render a (vertical) bar chart
         *
         * @param {array} data - the axis data
         * @param {string} title - the chart title
         * @param {string} selector - the field selector for the axis (for filtering)
         */
        _renderBarChart: function(data, title, selector) {

            var chart = this.chart;
            if (!chart) {
                return;
            }

            // Show the container
            $(chart).closest('.pt-chart-contents').show().css({width: '96%'});

            // Prepare the data items
            var items = [],
                truncateLabel = this._truncateLabel;
            for (var i=0; i<data.length; i++) {
                var item = data[i];
                if (!item[1]) {
                    items.push({
                        label: item[4],
                        value: item[2],
                        filterIndex: item[0],
                        filterKey: item[3]
                    });
                }
            }

            // Set the height of the chart container
            $(chart).css({height: '360px'});

            // Chart title
            if (title) {
                $(chart).siblings('.pt-chart-title')
                        .html('<h4>' + title + '</h4>');
            } else {
                $(chart).siblings('.pt-chart-title')
                        .empty();
            }

            // On-hover data point tooltip
            var tooltipContent = function(series, label, value, dataPoint) {

                var data = dataPoint.point,
                    color = nv.utils.defaultColor()({}, dataPoint.pointIndex);

                var tooltip = '<div class="pt-tooltip">' +
                              '<div class="pt-tooltip-label" style="color:' + color + '">' + data.label + '</div>' +
                              '<div class="pt-tooltip-text">' + data.value + '</div>' +
                              '</div>';
                return tooltip;
            }
            var pt = this,
                valueFormat = this.options.numberFormatter;
            nv.addGraph(function() {

                // Define the chart
                var reportChart = nv.models.discreteBarChart()
                                           .x(function(d) { return d.label })
                                           .y(function(d) { return d.value })
                                           .staggerLabels(true)
                                           .tooltips(true)
                                           .tooltipContent(tooltipContent)
                                           .showValues(true);

                // Set value and tick formatters
                reportChart.valueFormat(valueFormat);
                reportChart.yAxis
                           .tickFormat(valueFormat);
                reportChart.xAxis
                           .tickFormat(function(d) {
                               return truncateLabel(d, 18);
                            });

                // Render the chart
                d3.select($(chart).get(0))
                  .append('svg')
                  .attr('class', 'nv')
                  .datum([{key: "reportChart", values: items}])
                  .transition().duration(500)
                  .call(reportChart);

                // Event handlers
                if (pt.options.exploreChart && selector) {
                    // Click on a bar forwards to a filtered view
                    reportChart.discretebar.dispatch.on('elementClick', function(e) {
                        var filterKey = e.point.filterKey;
                        if (filterKey === null) {
                            filterKey = 'None';
                        }
                        var filterVar = selector;
                        if (e.point.filterIndex == '__other__') {
                            filterVar += '__belongs';
                        }
                        pt._chartExplore([[filterVar, filterKey]]);
                    });
                }

                // Re-draw when window gets resized
                nv.utils.windowResize(reportChart.update);

                return reportChart;
            });
        },

        /**
         * Render a breakdown (2-dimensional horizontal bar chart)
         *
         * @param {object} data - the pivot table data
         * @param {number} dim - the primary dimension (0=rows, 1=columns)
         * @param {string} title - the chart title
         * @param {array} selectors - the field selectors for filtering [row, col]
         */
        _renderBreakDown: function(data, dim, title, selectors) {

            var chart = this.chart;
            if (!chart) {
                return;
            }

            // Show the container
            $(chart).closest('.pt-chart-contents').show().css({width: '96%'});

            // Determine x and y dimension and value accessor
            var cells = data.cells,
                rdim,
                cdim,
                getData,
                ridx = [],
                cidx = [],
                rowsSelector,
                colsSelector;
            if (dim === 0) {
                rdim = data.rows;
                cdim = data.cols;
                getData = function(i, j) {
                    var ri = ridx[i], ci = cidx[j];
                    return cells[ri][ci]['value'];
                };
                rowsSelector = selectors[0];
                colsSelector = selectors[1];
            } else {
                rdim = data.cols;
                cdim = data.rows;
                getData = function(i, j) {
                    var ri = ridx[i], ci = cidx[j];
                    return cells[ci][ri]['value'];
                };
                rowsSelector = selectors[1];
                colsSelector = selectors[0];
            }

            // Prepare rows and cols for the data matrix
            var i, len, rows = [], cols = [];
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

            // Generate the data matrix for the chart
            var matrix = [];
            for (var c=0; c < cols.length; c++) {
                // Every column gives a series
                var series = {key: cols[c][4],
                              filterIndex: cols[c][0],
                              filterKey: cols[c][3]
                              },
                    values = [],
                    index, value;
                for (var r=0; r < rows.length; r++) {
                    // Every row gives a value
                    values.push({label: rows[r][4],
                                 filterIndex: rows[r][0],
                                 filterKey: rows[r][3],
                                 value: getData(r, c)
                                 })
                }
                series.values = values;
                matrix.push(series);
            }

            // Set the height of the chart container
            var height = Math.max(rows.length * Math.max((cols.length + 1) * 16, 50) + 70, 360);
            $(chart).css({height: height + 'px'});

            // Chart title
            if (title) {
                $(chart).siblings('.pt-chart-title')
                        .html('<h4>' + title + '</h4>');
            } else {
                $(chart).siblings('.pt-chart-title')
                        .empty();
            }

            // Callback function to render the chart tooltip
            var tooltipContent = function(series, label, value, dataPoint) {
                var data = dataPoint.point,
                    color = nv.utils.defaultColor()({}, dataPoint.seriesIndex);

                var tooltip = '<div class="pt-tooltip">' +
                              '<div class="pt-tooltip-label" style="color:' + color + '">' + series + '</div>' +
                              '<div class="pt-tooltip-text">' + data.label + ': <span class="pt-tooltip-value">' + data.value + '</span></div>' +
                              '</div>';
                return tooltip;
            }

            // Chart
            var pt = this,
                valueFormat = this.options.numberFormatter,
                truncateLabel = this._truncateLabel;

            nv.addGraph(function() {

                // Define the chart
                var reportChart = nv.models.multiBarHorizontalChart()
                                           .x(function(d) { return d.label })
                                           .y(function(d) { return d.value })
                                           .margin({top: 20, right: 20, bottom: 20, left: 175})
                                           .showValues(true)
                                           .tooltips(true)
                                           .tooltipContent(tooltipContent)
                                           .transitionDuration(350)
                                           .showControls(true);

                // Set value and tick formatters
                reportChart.valueFormat(valueFormat);
                reportChart.yAxis
                           .tickFormat(valueFormat);
                reportChart.xAxis
                           .tickFormat(function(d) {
                               return truncateLabel(d, 24);
                            });

                // Render the chart
                d3.select($(chart).get(0))
                  .append('svg')
                  .attr('class', 'nv')
                  .datum(matrix)
                  .call(reportChart);

                // Event handlers
                if (pt.options.exploreChart && rowsSelector && colsSelector) {
                    // Click on a bar forwards to a filtered view
                    reportChart.multibar.dispatch.on('elementClick', function(e) {
                        var columnKey = e.series.filterKey,
                            columnFilter;
                        if (columnKey === null) {
                            columnKey = 'None';
                        }
                        if (e.series.filterIndex == '__other__') {
                            columnFilter = colsSelector + '__belongs';
                        } else {
                            columnFilter = colsSelector;
                        }
                        var rowKey = e.point.filterKey,
                            rowFilter;
                        if (rowKey === null) {
                            rowKey = 'None';
                        }
                        if (e.point.filterIndex == '__other__') {
                            rowFilter = rowsSelector + '__belongs';
                        } else {
                            rowFilter = rowsSelector;
                        }
                        var filterVars = [[rowFilter, rowKey], [columnFilter, columnKey]]
                        pt._chartExplore(filterVars);
                    });
                }

                // Resize dynamically when the window gets resized
                nv.utils.windowResize(reportChart.update);

                return reportChart;
            });
        },

        /**
         * Render spectrum chart
         *
         * @param {object} data - the pivot table data
         * @param {string} axis - the axis to break down by
         * @param {array} selectors - the field selectors for filtering [row, col]
         */
        _renderSpectrum: function(data, axis, selectors) {

            var chart = this.chart;
            if (!chart) {
                return;
            }
            var pt = this,
                defaultColor = 'silver';

            // Determine the x and y axes of the pivot table
            var chartOptions = pt.chartOptions,
                cells = data.cells,
                labels = data.labels,
                xAxis,
                yAxis,
                xLabel,
                yLabel,
                xSelector,
                ySelector,
                getCell;
            if (axis == 'rows') {
                xAxis = data.rows;
                yAxis = data.cols;
                xLabel = labels.rows;
                yLabel = labels.cols;
                xSelector = selectors[0];
                ySelector = selectors[1];
                // Cell accessor
                getCell = function(xIndex, yIndex) {
                    return cells[xIndex][yIndex];
                };
            } else {
                xAxis = data.cols;
                yAxis = data.rows;
                xLabel = labels.cols;
                yLabel = labels.rows;
                xSelector = selectors[1];
                ySelector = selectors[0];
                // Cell accessor
                getCell = function(xIndex, yIndex) {
                    return cells[yIndex][xIndex];
                };
            }

            // Data accessor, read either cells or axis headers
            var getData = function(xIndex, yIndex) {
                if (xIndex === null) {
                    // Read y header
                    return yAxis[yIndex];
                } else if (yIndex === null) {
                    // Read x header
                    return xAxis[xIndex];
                } else {
                    return getCell(xIndex, yIndex);
                }
            };

            // Series accessor (returns all Y data points for a particular X)
            var getSeries = function(xIndex, color) {
                if (color === undefined) {
                    color = defaultColor;
                }
                var items = [], item, value;
                for (var i=0; i<yAxis.length; i++) {
                    item = getData(null, i);
                    if (xIndex === null) {
                        value = item[2];
                    } else {
                        value = getData(xIndex, i).value;
                    }
                    if (!item[1] && item[2] >= 0) {
                        items.push({
                            filterIndex: item[0],
                            filterKey: item[3],
                            label: item[4],
                            value: value,
                            color: color
                        });
                    }
                }
                return items;
            };

            // Read the xAxis headers
            var xHeaders = [], total = 0;
            for (var i=0; i<xAxis.length; i++) {
                var item = getData(i, null);
                if (!item[1] && item[2] >= 0) {
                    xHeaders.push({
                        position: i,
                        filterIndex: item[0],
                        filterKey: item[3],
                        label: item[4],
                        value: item[2]
                    });
                    total += item[2];
                }
            }

            // On-hover data point tooltip
            pt.chartOptions.currentDataIndex = null;
            var onhoverTooltip = function(e) {

                if (pt.chartOptions.currentDataIndex == e.pointIndex) {
                    // Already open
                    return;
                }
                // Close any open tooltip
                pt._removeChartTooltip();
                pt.chartOptions.currentDataIndex = e.pointIndex;

                // Get the data point data
                var value = e.value;
                var percent = Math.round((value / total) * 100);

                // Create the tooltip
                var tooltip = '<div class="pt-tooltip-label">' + e.label + '</div>';
                tooltip += '<div class="pt-tooltip-text">' + value + ' (' + percent + '%)</div>';
                pt._renderChartTooltip(e.pos[0], e.pos[1], tooltip);

                $('.pt-tooltip-label').css({
                    color: nv.utils.defaultColor()({}, e.pointIndex)
                });
            };

            // Show the container
            $(chart).removeAttr('style')
                    .closest('.pt-chart-contents')
                    .css({'width': '98%', 'height': 'auto'})
                    .show();

            // Remove previous title
            $(chart).siblings('.pt-chart-title').empty();

            // Chart areas
            var pieArea = $('<div class="pt-spectrum-pie">').appendTo(chart),
                barArea = $('<div class="pt-spectrum-bar">').appendTo(chart);

            // Define the bar chart
            var valueFormat = this.options.numberFormatter,
                truncateLabel = this._truncateLabel;

            // On-hover data point tooltip
            var barChartTooltip = function(series, label, value, dataPoint) {
                var data = dataPoint.point,
                    color = data.color || [defaultColor];

                var tooltip = '<div class="pt-tooltip">' +
                              '<div class="pt-tooltip-label" style="color:' + color + '">' + data.label + '</div>' +
                              '<div class="pt-tooltip-text">' + valueFormat(data.value) + '</div>' +
                              '</div>';
                return tooltip;
            }
            var barChart = nv.models.discreteBarChart()
                                    .x(function(d) { return d.label })
                                    .y(function(d) { return d.value })
                                    .color([defaultColor])
                                    .staggerLabels(true)
                                    .tooltips(true)
                                    .tooltipContent(barChartTooltip)
                                    .showValues(true);

            // Set value and tick formatters
            barChart.valueFormat(valueFormat);
            barChart.yAxis
                    .tickFormat(valueFormat);
            barChart.xAxis
                    .tickFormat(function(d) { return truncateLabel(d, 18); });

            var barChartContainer = d3.select($(barArea).get(0))
                                      .append('svg')
                                      .attr('class', 'nv')

            // Define the pie chart
            var pieWidth = Math.floor(pieArea.width()/2) - 30;
            var pieChart = nv.models.pieChart()
                                    .x(function(d) { return d.label })
                                    .y(function(d) { return d.value })
                                    .height(280)
                                    .width(pieWidth)
                                    .margin({top: -20, left: 20})
                                    .labelType('percent')
                                    .labelThreshold(0.10)
                                    .showLegend(false)
                                    .donut(true)
                                    .donutRatio(0.35)
                                    .tooltips(false);

            pieChart.legend.align(true)
                           .rightAlign(false);

            pieChart.pie.startAngle(function(d) { return d.startAngle/2 -Math.PI/2 })
                        .endAngle(function(d) { return d.endAngle/2 -Math.PI/2 });

            pieChart.pie.dispatch.on('elementMouseover', onhoverTooltip)
                                 .on('elementMouseout', function(e) {
                $('.pt-tooltip').remove();
                pt.chartOptions.currentDataIndex = null;
                pt.chartOptions.currentSeriesIndex = null;
            });

            // Pie chart container
            var pieChartContainer = d3.select($(pieArea).get(0))
                                      .append('svg')
                                      .attr('class', 'nv')
                                      .style({'min-width': (pieWidth-30) + 'px' });

            var formArea = d3.select($(pieArea).get(0))
                             .append('div')
                             .attr('class', 'pt-spectrum-form');

            // Chart title
            formArea.append('h4')
                    .html(labels.layer + ' ' + labels.per + ' ' + yLabel);

            // Series selector
            formArea.append('label')
                    .html(xLabel + ':');
            var seriesSelector = formArea.append('select');
            seriesSelector.append('option')
                          .attr('value', 'null')
                          .style('font-weight', 'bold')
                          .html(pt.options.textAll);
            seriesSelector.selectAll('.pt-series-item')
                          .data(xHeaders)
                          .enter()
                          .append('option')
                          .attr('class', 'pt-series-item')
                          .attr('value', function(d, i) { return i; })
                          .html(function(d) { return d.label; });

            // Series total
            formArea.append('label')
                    .html(labels.total + ':');
            var totalValue = formArea.append('span')
                                     .text(data.total);

            // Helper method to render a series
            var selectSeries = function(xIndex) {

                var sliceColor, items;
                if (xIndex === null || pt.chartOptions.currentSpectrumIndex == xIndex) {
                    sliceColor = function(d, i) {
                        return nv.utils.defaultColor()({}, i);
                    }
                    pieChartContainer.selectAll('.nv-slice')
                                     .style('fill', sliceColor)
                                     .style('stroke', sliceColor);
                    items = getSeries(null);
                    barChartContainer.datum([{key: null,
                                              filterIndex: null,
                                              filterKey: null,
                                              values: items
                                              }])
                    barChart.update();
                    pt.chartOptions.currentSpectrumIndex = null;
                    seriesSelector.property('value', 'null');
                    totalValue.text(data.total);
                } else {
                    var seriesHeader = xHeaders[xIndex],
                        color = nv.utils.defaultColor()({}, xIndex);
                    sliceColor = function(d, i) {
                        if (i == xIndex) {
                            return color;
                        } else {
                            return defaultColor;
                        }
                    }
                    pieChartContainer.selectAll('.nv-slice')
                                     .style('fill', sliceColor)
                                     .style('stroke', sliceColor);
                    items = getSeries(seriesHeader.position, color);
                    barChartContainer.datum([{key: seriesHeader.position,
                                              filterIndex: seriesHeader.filterIndex,
                                              filterKey: seriesHeader.filterKey,
                                              values: items
                                              }])
                    barChart.update();
                    pt.chartOptions.currentSpectrumIndex = xIndex;
                    seriesSelector.property('value', xIndex);
                    totalValue.text(xHeaders[xIndex].value);
                }
            };

            // Pie chart click event
            pieChart.pie.dispatch.on('elementClick', function(e) {
                selectSeries(e.index);
            });

            // Series selector change event
            seriesSelector.on('change.pt', function(e) {
                var xIndex = d3.select(this).property('value');
                if (xIndex == 'null') {
                    selectSeries(null);
                } else {
                    selectSeries(xIndex);
                }
            })

            // Render the pie chart
            nv.addGraph(function() {
                pieChartContainer.datum(xHeaders)
                                 .transition().duration(1200)
                                 .call(pieChart);

                nv.utils.windowResize(pieChart.update);
                return pieChart;
            });

            // Render the bar chart
            nv.addGraph(function() {
                barChartContainer.datum([{key: null,
                                          filterIndex: null,
                                          filterKey: null,
                                          values: getSeries(null)
                                          }])
                                 .transition().duration(500)
                                 .call(barChart);
                // Event handlers
                if (pt.options.exploreChart && xSelector && ySelector) {
                    // Click on a bar forwards to a filtered view
                    barChart.discretebar.dispatch.on('elementClick', function(e) {
                        var xIndex = e.series.filterIndex,
                            xKey = e.series.filterKey,
                            yIndex = e.point.filterIndex,
                            yKey = e.point.filterKey,
                            filters = [];

                        var filterExpression = function(selector, index, key) {
                            if (key === null && index !== null) {
                                key = 'None';
                            }
                            if (index == '__other__') {
                                return selector + '__belongs';
                            } else {
                                return selector;
                            }
                        }
                        if (xIndex !== null) {
                            var xFilter = filterExpression(xSelector, xIndex, xKey);
                            filters.push([xFilter, xKey]);
                        }
                        if (yIndex !== null) {
                            var yFilter = filterExpression(ySelector, yIndex, yKey);
                            filters.push([yFilter, yKey]);
                        }
                        pt._chartExplore(filters);
                    });
                }
                // Re-draw when window gets resized
                nv.utils.windowResize(barChart.update);
                return barChart;
            });
        },

        /**
         * Forward to a filtered view upon click on a chart data point
         *
         * @param {object} filter - the URL filter corresponding to the data point
         */
        _chartExplore: function(filter) {

            var opts = this.options,
                summaryTabs = $(this.element).closest('.ui-tabs');

            var tab = opts.filterTab;
            if (summaryTabs.length && tab !== false) {
                // We're inside a summary
                var filterForm = opts.filterForm;

                // Update the filter form (default: first filter form)
                var $filterForm = filterForm ? $('#' + filterForm) : undefined;
                S3.search.setCurrentFilters($filterForm, filter);

                // Switch to the specified tab (default: first tab)
                var index = tab ? $('#' + tab).index() : 0;
                summaryTabs.tabs('option', 'active', index);

            } else {

                // Forward to a filtered page
                var filterURL = opts.filterURL;
                if (filterURL) {
                    var page = this._updateURL(filterURL, filter);
                    window.open(page, '_blank');
                }
            }
            return;
        },

        /**
         * Render an onhover-tooltip for a chart data point
         *
         * @param {number} x - screen position of the data point (x)
         * @param {number} y - screen position of the data point (y)
         * @param {string|HTML} contents - contents for the tooltip popup
         */
        _renderChartTooltip: function(x, y, contents) {

            $('<div class="pt-tooltip">' + contents + '</div>').css({
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

        /**
         * Remove all onhover-tooltips for chart data points
         */
        _removeChartTooltip: function() {
            $('.pt-tooltip').remove();
            this.chartOptions.currentDataIndex = null;
            this.chartOptions.currentSeriesIndex = null;
        },

        /**
         * Get current report options form the report options form
         *
         * @returns {object} the pivot table URL options
         */
        _getOptions: function() {

            var $el = $(this.element);
            var widgetID = '#' + $el.attr('id');

            var options = {
                rows: $(widgetID + '-rows').val(),
                cols: $(widgetID + '-cols').val(),
                fact: $(widgetID + '-fact').val(),
                totals: $(widgetID + '-totals').is(':checked') ? 1 : 0
            };
            return options;
        },

        /**
         * Get current filters from the filter form
         *
         * @returns {object} the URL filters
         */
        _getFilters: function() {

            var widgetID = '#' + $(this.element).attr('id'),
                filters = null;

            var filterForm = $(widgetID + '-filters');
            if (filterForm.length) {
                try {
                    filters = S3.search.getCurrentFilters(filterForm.first());
                } catch (e) {}
            }
            return filters;
        },

        /**
         * Update a URL with both Ajax- and axis-filters
         *
         * @param {string} url - the URL
         * @param {object} filters - the URL filters
         */
        _updateURL: function(url, filters) {

            // Construct the URL
            var url_parts,
                url_vars,
                queries = [],
                update = {},
                seen = {},
                i, len, f, q, k;

            // Add axis filters
            if (filters) {
                for (i=0, len=filters.length; i<len; i++) {
                    f = filters[i];
                    k = f[0];
                    update[k] = true;
                    queries.push(k + '=' + f[1]);
                }
            }

            // Add filters from ajaxURL
            var ajaxURL = this.options.ajaxURL;
            url_parts = ajaxURL.split('?');
            if (url_parts.length > 1) {
                url_vars = url_parts[1].split('&');
                seen = {};
                for (i=0, len=url_vars.length; i < len; i++) {
                    q = url_vars[i].split('=');
                    if (q.length > 1) {
                        k = decodeURIComponent(q[0]);
                        if (!update[k]) {
                            queries.push(k + '=' + decodeURIComponent(q[1]));
                            seen[k] = true;
                        }
                    }
                }
                for (k in seen) {
                    update[k] = true;
                }
            }

            // Extract all original filters
            url_parts = url.split('?');
            if (url_parts.length > 1) {
                url_vars = url_parts[1].split('&');
                seen = {};
                for (i=0, len=url_vars.length; i < len; i++) {
                    q = url_vars[i].split('=');
                    if (q.length > 1) {
                        k = decodeURIComponent(q[0]);
                        if (!update[k]) {
                            queries.push(k + '=' + decodeURIComponent(q[1]));
                        }
                    }
                }
            }

            // Update URL
            var url_query = queries.join('&');
            var filtered_url = url_parts[0];
            if (url_query) {
                filtered_url = filtered_url + '?' + url_query;
            }
            return filtered_url;
        },

        /**
         * Update the Ajax URL with new options and filters
         *
         * @param {object} options: the pivot table URL options
         * @param {object} filters: the URL filters
         */
        _updateAjaxURL: function(options, filters) {

            var ajaxURL = this.options.ajaxURL;

            // Construct the URL
            var url_parts = ajaxURL.split('?'),
                query = [],
                needs_reload = false;

            var qstr, url_vars;

            if (url_parts.length > 1) {
                qstr = url_parts[1];
                url_vars = qstr.split('&');
            } else {
                qstr = '';
                url_vars = [];
            }

            var option, q, newopt;
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
                i, len, k, v;

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

        /**
         * Ajax-reload the pivot data and refresh all widget elements
         *
         * @param {object} options - the pivot table URL options
         * @param {object} filters - the URL filters
         * @param {boolean} force - false to reload only when URL parameters have
         *                          changed, true to reload in any case
         */
        reload: function(options, filters, force) {

            force = typeof force != 'undefined' ? force : true;

            if (typeof filters == 'undefined') {
                // extract filters
                filters = this._getFilters();
            }

            var pt = this,
                $el = (this.element),
                needs_reload;

            var pivotdata = $el.find('input[type="hidden"][name="pivotdata"]');
            if (!pivotdata.length) {
                return;
            }
            $el.find('.pt-throbber').show();
            if (options || filters) {
                needs_reload = this._updateAjaxURL(options, filters);
            }
            if (needs_reload || force) {
                var ajaxURL = this.options.ajaxURL;
                $el.find('.pt-empty').hide();
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
                pt.refresh();
            }
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var pt = this,
                $el = $(this.element),
                data = this.data;
            var widgetID = '#' + $el.attr('id');

            // Show/hide report options
            $(widgetID + '-options legend').click(function() {
                $(this).siblings().toggle();
                $(this).children().toggle();
            });
            $(widgetID + '-filters legend').click(function() {
                $(this).siblings().toggle();
                $(this).children().toggle();
            });

            // Show/hide pivot table
            $el.find('.pt-hide-table').click(function() {
                pt.table_options.hidden = true;
                $el.find('.pt-table').hide();
                $(this).siblings('.pt-show-table').show();
                $(this).hide();
            });
            $el.find('.pt-show-table').click(function() {
                pt.table_options.hidden = false;
                $el.find('.pt-table').show();
                $(this).siblings('.pt-hide-table').show();
                $(this).hide();
            });

            // Totals-option doesn't need Ajax-refresh
            $(widgetID + '-totals').click(function() {
                var show_totals = $(this).is(':checked');
                if (pt.options.showTotals != show_totals) {
                    pt.reload({totals: show_totals}, null, false);
                }
            });

            // Axis selectors to fire optionChanged-event
            $(widgetID + '-rows,' +
              widgetID + '-cols,' +
              widgetID + '-fact').on('change.autosubmit', function() {
                $(widgetID + '-pt-form').trigger('optionChanged');
            });

            // Form submission
            if (this.options.autoSubmit) {
                // Auto-submit
                var timeout = this.options.autoSubmit;
                $(widgetID + '-pt-form').on('optionChanged', function() {
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
                $(widgetID + '-pt-form input.pt-submit').click(function() {
                    var options = pt._getOptions(),
                        filters = pt._getFilters();
                    pt.reload(options, filters, false);
                });
            }

            // Zoom in
            $(widgetID + ' div.pt-table div.pt-cell-zoom').click(function(event) {

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
            $(widgetID + '-pchart-rows').click(function() {
                pt._renderChart({type: 'piechart', axis: 'rows'});
            });
            $(widgetID + '-vchart-rows').click(function() {
                pt._renderChart({type: 'barchart', axis: 'rows'});
            });
            $(widgetID + '-schart-rows').click(function() {
                pt._renderChart({type: 'spectrum', axis: 'rows'});
            });
            $(widgetID + '-hchart-rows').click(function() {
                pt._renderChart({type: 'breakdown', axis: 'rows'});
            });
            $(widgetID + '-pchart-cols').click(function() {
                pt._renderChart({type: 'piechart', axis: 'cols'});
            });
            $(widgetID + '-vchart-cols').click(function() {
                pt._renderChart({type: 'barchart', axis: 'cols'});
            });
            $(widgetID + '-schart-cols').click(function() {
                pt._renderChart({type: 'spectrum', axis: 'cols'});
            });
            $(widgetID + '-hchart-cols').click(function() {
                pt._renderChart({type: 'breakdown', axis: 'cols'});
            });
            $el.find('.pt-hide-chart').click(function () {
                pt._renderChart(false);
            });
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var $el = $(this.element);
            var widgetID = '#' + $el.attr('id');

            $(widgetID + ' div.pt-table div.pt-cell-zoom').unbind('click');
            $(widgetID + '-options legend').unbind('click');
            $(widgetID + '-filters legend').unbind('click');

            $(widgetID + '-totals').unbind('click');

            $(widgetID + '-rows,' +
              widgetID + '-cols,' +
              widgetID + '-fact').unbind('change.autosubmit');

            $(widgetID + '-pt-form').unbind('optionChanged');
            $el.find('input.pt-submit').unbind('click');

            $(widgetID + '-pchart-rows,' +
              widgetID + '-vchart-rows,' +
              widgetID + '-schart-rows,' +
              widgetID + '-hchart-rows,' +
              widgetID + '-pchart-cols,' +
              widgetID + '-vchart-cols,' +
              widgetID + '-schart-cols,' +
              widgetID + '-hchart-cols').unbind('click');

            $el.find('.pt-hide-table').unbind('click');
            $el.find('.pt-show-table').unbind('click');
            $el.find('.pt-hide-chart').unbind('click');
        }
    });
})(jQuery);
