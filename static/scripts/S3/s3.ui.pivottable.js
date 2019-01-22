/**
 * jQuery UI pivottable Widget for S3Report
 *
 * @copyright 2013-2018 (c) Sahana Software Foundation
 * @license MIT
 *
 * requires jQuery 1.9.1+
 * requires jQuery UI 1.10 widget factory
 * requires D3.js 3.4.9+
 * requires NVD3.js
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

            autoSubmit: 1000, // 1s but controlled by get_ui_report_auto_submit()
            timeout: 10000, // 10s but controlled by get_ui_report_timeout()

            thousandSeparator: ' ',
            thousandGrouping: '3',
            minTickSize: null,
            precision: null,
            textAll: 'All',
            labelRecords: 'Records',
        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = pivottableID;
            pivottableID += 1;

            this.table = null;
            this.chart = null;
            this.openRequest = null;

            // Namespace for events
            this.eventNamespace = '.pt';
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
                $el.find('.pt-export-opt').hide();
            } else if (data.method == 'count') {
                // Charts should show integers if method is 'count'
                this.options.precision = 0;
                this.options.minTickSize = 1;
            }
            this.data = data;

            // Cache for cell record representations
            this.lookups = {};

            if (data.nodata) {
                $el.find('.pt-table')
                   .first()
                   .empty()
                   .append($('<div class="pt-no-data">' + data.nodata + '</div>'));
                $el.find('.pt-hide-table').hide();
                $el.find('.pt-show-table').hide();
                $el.find('.pt-export-opt').hide();
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

            var $el = $(this.element),
                container = $el.find('.pt-table').first().empty();

            this.table = null;

            var data = this.data;
            if (data.empty) {
                return;
            }

            if (this.options.renderTable) {
                var cells = data.cells.slice(0),
                    cols = data.cols,
                    rows = data.rows,
                    total = data.total,
                    labels = data.labels;

                var singleRow = false,
                    singleCol = false,
                    facts = data.facts;
                if (facts.length == 1 && facts[0][1] != "list") {
                    if (rows.length == 1 && rows[0][4] === null) {
                        singleRow = true;
                    }
                    if (cols.length == 1 && cols[0][4] === null) {
                        singleCol = true;
                    }
                }

                var opts = this.options,
                    showTotals = opts.showTotals,
                    i;

                if (singleCol && showTotals) {
                    // Render no columns (totals column only)
                    cols = [];
                    for (i=0; i<rows.length; i++) {
                        cells[i] = [];
                    }
                } else {
                    // Filter out the "others" column
                    var notOther = function(cell, cidx) {
                        return cols[cidx][0] != '__other__';
                    };
                    for (i=0; i<rows.length; i++) {
                        cells[i] = cells[i].filter(notOther);
                    }
                    cols = cols.filter(function(col) {
                        return col[0] != '__other__';
                    });
                }

                if (singleRow && showTotals) {
                    // Render no rows (totals row only)
                    rows = [];
                    cells = [];
                } else {
                    // Filter out the "others" row
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
                     .call(this._renderColumns, cols, labels, singleCol);

                // Table rows and cells
                if (!singleRow || !showTotals) {
                    var pt = this;
                    table.append('tbody')
                         .call(this._renderRows, pt, rows, cols, labels, cells, opts);
                }

                // Table footer with totals
                if (showTotals) {
                    table.append('tfoot')
                         .call(this._renderFooter, rows, cols, labels, total);
                }

                // Map table to a jQuery-enhanced node
                this.table = $(table.node());

                if (this.table_options.hidden) {
                    $el.find('.pt-show-table').show();
                    $el.find('.pt-hide-table').hide();
                    $el.find('.pt-export-opt').hide();
                } else {
                    $el.find('.pt-show-table').hide();
                    $el.find('.pt-hide-table').show();
                    $el.find('.pt-export-opt').show();
                }
            } else {
                $el.find('.pt-show-table').hide();
                $el.find('.pt-hide-table').hide();
                $el.find('.pt-export-opt').hide();
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
         *
         * @todo: optimize parameter list (pass in data? use "this"?)
         * @todo: get cols, labels and opts from this or pass in pt?
         * @todo: use dashes in CSS classes instead of underscores
         */
        _renderColumns: function(thead, cols, labels, singleCol) {

            var columns = thead.append('tr');

            // Append the rows header
            columns.append('th')
                   .attr({'scope': 'col',
                          'class': 'pt-rows-header'
                          })
                   .text(labels.rows);

            columns.selectAll('th.pt-data')
                   .data(cols)
                   .enter()
                   .append('th')
                   .attr({'scope': 'col',
                          'class': 'pt-col-label'
                          })
                   .text(function(d) {
                       if (singleCol) {
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

            rows = tbody.selectAll('tr.pt-row')
                        .data(rows)
                        .enter()
                        .append('tr')
                        .attr('class', function(d, i) { return i % 2 ? 'odd': 'even'; });

            // Render the row header
            rows.append('td').text(function(d) { return d[4]; });

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
                        return d[2][0];
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
                items = data.i,
                layer;

            for (var i=0, len=items.length; i<len; i++) {
                layer = items[i];

                var value = column.append('div')
                                  .attr('class', 'pt-cell-value');
                if (layer === null) {
                    value.text(labels.none);
                } else if ($.isArray(layer)) {
                    value.append('ul')
                         .selectAll('li')
                         .data(layer)
                         .enter()
                         .append('li')
                         .html(function(d) { return d; });
                } else {
                    value.text(layer);
                }
                if (len - i > 1) {
                    value.append('span').text(' / ');
                }
            }

            var recordIDs = data.k;
            if (recordIDs && recordIDs.length) {
                $(column.node()).data('recordIDs', recordIDs);
                // TODO CSS to place cell-zoom icon at the top right of the cell
                column.append('div').attr('class', 'pt-cell-zoom');
            }
        },

        /**
         * Render a list of contributing records inside a pivot table cell,
         * normally called from _cellExplore
         *
         * @param {jQuery} cell - the picot table cell (td.pt-cell)
         * @param {Array} recordIDs - the record IDs to look up their
         *                            representations from this.lookups,
         *                            or a falsy value to just remove the list
         */
        _renderCellRecords: function(cell, recordIDs) {

            var zoom = $('.pt-cell-zoom', cell).removeClass('opened'),
                records = $('.pt-cell-records', cell).remove();

            if (recordIDs) {

                var lookups = this.lookups,
                    recordList = [],
                    recordRepr,
                    keys = [];

                recordIDs.forEach(function(recordID) {
                    recordRepr = lookups[recordID];
                    if (!recordRepr) {
                        return;
                    }
                    if (recordRepr.constructor === Array) {
                        var key = recordRepr[1];
                        if (keys.indexOf(key) != -1) {
                            return;
                        } else {
                            keys.push(key);
                        }
                        recordRepr = recordRepr[0];
                    }
                    if (recordRepr) {
                        recordList.push(recordRepr);
                    }
                });

                records = $('<div class="pt-cell-records">');

                var list = $('<ul>').appendTo(records);
                if (recordList.length) {
                    recordList.sort(function(a, b) {
                        return a.localeCompare(b);
                    });
                    recordList.forEach(function(recordRepr) {
                        $('<li>').html(recordRepr).appendTo(list);
                    });
                } else {
                    // Fallback if no representations are available
                    $('<li>').text(recordIDs.length + ' ' + this.options.textRecords).appendTo(list);
                }
                zoom.addClass('opened').after(records);
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
                  .text(function(col) { return col[2][0]; });

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
            $('.pt-chart-contents', $el).hide();

            var chart = this.chart;
            if (chart) {
                $(chart).off('plothover').off('plotclick').empty();
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
            var rows_selector = filter[0],
                cols_selector = filter[1];

            if (chartType == 'piechart') {
                if (chartAxis == 'rows') {
                    this._renderPieChart(data.rows, rowsTitle, rows_selector);
                } else {
                    this._renderPieChart(data.cols, colsTitle, cols_selector);
                }
            } else if (chartType == 'barchart') {
                if (chartAxis == 'rows') {
                    this._renderBarChart(data.rows, data.facts, rowsTitle, rows_selector);
                } else {
                    this._renderBarChart(data.cols, data.facts, colsTitle, cols_selector);
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
            var height = 360;
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
            for (var i=0; i < data.length; i++) {
                var item = data[i];
                if (!item[1] && item[2][0] >= 0) {
                    items.push({
                        index: item[0],
                        label: item[4],
                        value: item[2][0],
                        key: item[3]
                    });
                    total += item[2][0];
                }
            }

            // On-hover data point tooltip
            var pt = this;
            pt.chartOptions.currentDataIndex = null;
            var onhoverTooltip = function(e) {

                var index = e.index;

                if (pt.chartOptions.currentDataIndex == index) {
                    // Already open
                    return;
                }
                // Close any open tooltip
                pt._removeChartTooltip();
                pt.chartOptions.currentDataIndex = index;

                // Get the data point data
                var data = e.data;
                var value = data.value;
                var percent = Math.round((value / total) * 100);

                // Create the tooltip
                var tooltip = '<div class="pt-tooltip-label">' + data.label + '</div>';
                tooltip += '<div class="pt-tooltip-text">' + value + ' (' + percent + '%)</div>';
                var d3_event = d3.event,
                    x = d3_event.pageX,
                    y = d3_event.pageY;
                pt._renderChartTooltip(x, y, tooltip);

                $('.pt-tooltip-label').css({
                    color: nv.utils.defaultColor()({}, index)
                });
            };

            nv.addGraph(function() {

                var reportChart = nv.models.pieChart()
                                           .x(function(d) { return d.label; })
                                           .y(function(d) { return d.value; })
                                           .labelsOutside(false)
                                           .labelType('percent')
                                           .labelThreshold(0.03)
                                           .showLegend(true);

                // Disbale tooltip as using onhoverTooltip instead
                reportChart.tooltip.enabled(false);
                reportChart.legend.align(true)
                                  .rightAlign(false);

                reportChart.pie.dispatch.on('elementMouseover', onhoverTooltip)
                                        .on('elementMouseout', function() {
                    $('.pt-tooltip').remove();
                    pt.chartOptions.currentDataIndex = null;
                    pt.chartOptions.currentSeriesIndex = null;
                });

                if (pt.options.exploreChart && selector) {
                    reportChart.pie.dispatch.on('elementClick', function(e) {
                        var data = e.data,
                            index = data.index,
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
        _renderBarChart: function(data, facts, title, selector) {

            var chart = this.chart;
            if (!chart) {
                return;
            }

            // Show the container
            $(chart).closest('.pt-chart-contents').show().css({width: '96%'});

            // Prepare the data items
            var items = [],
                truncateLabel = this._truncateLabel,
                series,
                set,
                item;

            for (var i=0; i < facts.length; i++) {
                series = {key: facts[i][2]};
                set = [];
                for (var j=0; j < data.length; j++) {
                    item = data[j];
                    set.push({
                        label: item[4],
                        value: item[2][i],
                        filterIndex: item[0],
                        filterKey: item[3]
                    });
                }
                series.values = set;
                items.push(series);
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
            var tooltipContent = function(data) {

                data = data.data;

                var color = nv.utils.defaultColor()({}, data.index);

                var tooltip = '<div class="pt-tooltip">' +
                              '<div class="pt-tooltip-label" style="color:' + color + '">' + data.label + '</div>' +
                              '<div class="pt-tooltip-text">' + data.value + '</div>' +
                              '</div>';
                return tooltip;
            };
            var pt = this,
                valueFormat = this.options.numberFormatter;
            nv.addGraph(function() {

                // Define the chart
                var reportChart, dispatch;
                if (items.length > 1) {
                    reportChart = nv.models.multiBarChart()
                                           .x(function(d) { return d.label; })
                                           .y(function(d) { return d.value; })
                                           .staggerLabels(true)
                                           .showControls(false);
                    dispatch = reportChart.multibar;
                } else {
                    reportChart = nv.models.discreteBarChart()
                                           .x(function(d) { return d.label; })
                                           .y(function(d) { return d.value; })
                                           .staggerLabels(true)
                                           .showValues(true);
                    reportChart.valueFormat(valueFormat);
                    dispatch = reportChart.discretebar;
                }
                reportChart.tooltip.contentGenerator(tooltipContent);

                // Set value and tick formatters
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
                  .datum(items)
                  .transition().duration(500)
                  .call(reportChart);

                // Event handlers
                if (pt.options.exploreChart && selector) {
                    // Click on a bar forwards to a filtered view
                    dispatch.dispatch.on('elementClick', function(e) {
                        var filterKey = e.data.filterKey;
                        if (filterKey === null) {
                            filterKey = 'None';
                        }
                        var filterVar = selector;
                        if (e.data.filterIndex == '__other__') {
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
                    return cells[ri][ci].v[0];
                };
                rowsSelector = selectors[0];
                colsSelector = selectors[1];
            } else {
                rdim = data.cols;
                cdim = data.rows;
                getData = function(i, j) {
                    var ri = ridx[i], ci = cidx[j];
                    return cells[ci][ri].v[0];
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
                    values = [];
                for (var r=0; r < rows.length; r++) {
                    // Every row gives a value
                    values.push({label: rows[r][4],
                                 filterIndex: rows[r][0],
                                 filterKey: rows[r][3],
                                 value: getData(r, c)
                                 });
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
            var tooltipContent = function(data) {

                var series = data.series[0],
                    item = data.data,
                    seriesLabel = item.series;
                if (series) {
                    seriesLabel = series.key;
                }

                var color = nv.utils.defaultColor()({}, item.index),
                    tooltip = '<div class="pt-tooltip">' +
                              '<div class="pt-tooltip-label" style="color:' + color + '">' + series.key + '</div>' +
                              '<div class="pt-tooltip-text">' + item.label + ': <span class="pt-tooltip-value">' + item.value + '</span></div>' +
                              '</div>';
                return tooltip;
            };

            // Chart
            var pt = this,
                valueFormat = this.options.numberFormatter,
                truncateLabel = this._truncateLabel;

            nv.addGraph(function() {

                // Define the chart
                var reportChart = nv.models.multiBarHorizontalChart()
                                           .x(function(d) { return d.label; })
                                           .y(function(d) { return d.value; })
                                           .margin({top: 20, right: 20, bottom: 20, left: 175})
                                           .showValues(true)
                                           .duration(350)
                                           .showControls(true);

                reportChart.tooltip.contentGenerator(tooltipContent);
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
                        var data = e.data,
                            series = d3.event.currentTarget.parentElement.__data__,
                            columnKey = series.filterKey,
                            columnFilter;
                        if (columnKey === null) {
                            columnKey = 'None';
                        }
                        if (series.filterIndex == '__other__') {
                            columnFilter = colsSelector + '__belongs';
                        } else {
                            columnFilter = colsSelector;
                        }
                        var rowKey = data.filterKey,
                            rowFilter;
                        if (rowKey === null) {
                            rowKey = 'None';
                        }
                        if (data.filterIndex == '__other__') {
                            rowFilter = rowsSelector + '__belongs';
                        } else {
                            rowFilter = rowsSelector;
                        }
                        var filterVars = [[rowFilter, rowKey], [columnFilter, columnKey]];
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
            var cells = data.cells,
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
                        value = item[2][0];
                    } else {
                        value = getData(xIndex, i).v[0];
                    }
                    if (!item[1] && item[2][0] >= 0) {
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
            var xHeaders = [],
                total = 0;
            for (var i=0; i<xAxis.length; i++) {
                var item = getData(i, null);
                if (!item[1] && item[2][0] >= 0) {
                    xHeaders.push({
                        position: i,
                        filterIndex: item[0],
                        filterKey: item[3],
                        label: item[4],
                        value: item[2][0]
                    });
                    total += item[2][0];
                }
            }

            // On-hover data point tooltip
            pt.chartOptions.currentDataIndex = null;
            var onhoverTooltip = function(e) {

                var index = e.index;

                if (pt.chartOptions.currentDataIndex == index) {
                    // Already open
                    return;
                }
                // Close any open tooltip
                pt._removeChartTooltip();
                pt.chartOptions.currentDataIndex = index;

                // Get the data point data
                var data = e.data;
                var value = data.value;
                var percent = Math.round((value / total) * 100);

                // Create the tooltip
                var tooltip = '<div class="pt-tooltip-label">' + data.label + '</div>';
                tooltip += '<div class="pt-tooltip-text">' + value + ' (' + percent + '%)</div>';
                var d3_event = d3.event,
                    x = d3_event.pageX,
                    y = d3_event.pageY;
                pt._renderChartTooltip(x, y, tooltip);

                $('.pt-tooltip-label').css({
                    color: nv.utils.defaultColor()({}, index)
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
            var barChartTooltip = function(data) {

                data = data.data;

                var color = data.color || [defaultColor];

                var tooltip = '<div class="pt-tooltip">' +
                              '<div class="pt-tooltip-label" style="color:' + color + '">' + data.label + '</div>' +
                              '<div class="pt-tooltip-text">' + valueFormat(data.value) + '</div>' +
                              '</div>';
                return tooltip;
            };
            var barChart = nv.models.discreteBarChart()
                                    .x(function(d) { return d.label; })
                                    .y(function(d) { return d.value; })
                                    .color([defaultColor])
                                    .staggerLabels(true)
                                    .showValues(true);

            barChart.tooltip.contentGenerator(barChartTooltip);
            // Set value and tick formatters
            barChart.valueFormat(valueFormat);
            barChart.yAxis
                    .tickFormat(valueFormat);
            barChart.xAxis
                    .tickFormat(function(d) { return truncateLabel(d, 18); });

            var barChartContainer = d3.select($(barArea).get(0))
                                      .append('svg')
                                      .attr('class', 'nv');

            // Define the pie chart
            var pieWidth = Math.floor(pieArea.width() / 2) - 30;
            var pieChart = nv.models.pieChart()
                                    .x(function(d) { return d.label; })
                                    .y(function(d) { return d.value; })
                                    .height(280)
                                    .width(pieWidth)
                                    .margin({top: -20, left: 20})
                                    .labelType('percent')
                                    .labelThreshold(0.10)
                                    .showLegend(false)
                                    .donut(true)
                                    .donutRatio(0.35);

            // Disbale tooltip as using onhoverTooltip instead
            pieChart.tooltip.enabled(false);

            pieChart.legend.align(true)
                           .rightAlign(false);

            pieChart.pie.startAngle(function(d) { return d.startAngle/2 -Math.PI/2; })
                        .endAngle(function(d) { return d.endAngle/2 -Math.PI/2; });

            pieChart.pie.dispatch.on('elementMouseover', onhoverTooltip)
                                 .on('elementMouseout', function() {
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
                    };
                    pieChartContainer.selectAll('.nv-slice')
                                     .style('fill', sliceColor)
                                     .style('stroke', sliceColor);
                    items = getSeries(null);
                    barChartContainer.datum([{key: null,
                                              filterIndex: null,
                                              filterKey: null,
                                              values: items
                                              }]);
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
                    };
                    pieChartContainer.selectAll('.nv-slice')
                                     .style('fill', sliceColor)
                                     .style('stroke', sliceColor);
                    items = getSeries(seriesHeader.position, color);
                    barChartContainer.datum([{key: seriesHeader.position,
                                              filterIndex: seriesHeader.filterIndex,
                                              filterKey: seriesHeader.filterKey,
                                              values: items
                                              }]);
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
            seriesSelector.on('change.pt', function() {
                var xIndex = d3.select(this).property('value');
                if (xIndex == 'null') {
                    selectSeries(null);
                } else {
                    selectSeries(xIndex);
                }
            });

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
                        var data = e.data,
                            series = d3.event.currentTarget.parentElement.__data__,
                            xIndex = series.filterIndex,
                            xKey = series.filterKey,
                            yIndex = data.filterIndex,
                            yKey = data.filterKey,
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
                        };
                        if (xIndex !== null) {
                            var xFilter = filterExpression(xSelector, xIndex, xKey);
                            filters.push([xFilter, xKey || 'None']);
                        }
                        if (yIndex !== null) {
                            var yFilter = filterExpression(ySelector, yIndex, yKey);
                            filters.push([yFilter, yKey || 'None']);
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
         * Show a list of records contributing to a pivot table cell,
         * expects the recordIDs to be stored in the cell data dict
         *
         * @param {jQuery} cell: the pivot table cell (td.pt-cell)
         */
        _cellExplore: function(cell) {

            var records = $('.pt-cell-records', cell);
            if (records.length) {
                this._renderCellRecords(cell, false);
                return;
            }

            var recordIDs = cell.data('recordIDs');
            if (recordIDs.length){

                var dfd = $.Deferred(),
                    self = this;

                dfd.promise().then(function() {
                    self._renderCellRecords(cell, recordIDs);
                });

                var ajaxURL = this._updateAjaxURL({'explore': '1'}, null, true),
                    lookups = this.lookups;

                // Only request the record IDs that are not cached yet
                var unknowns = recordIDs.filter(function(recordID) {
                    return !lookups.hasOwnProperty(recordID);
                });
                if (!unknowns.length) {

                    // No need for server call, we have all items cached
                    dfd.resolve();

                } else {

                    var zoom = $('.pt-cell-zoom', cell).hide(),
                        throbber = $('<div class="inline-throbber">');

                    throbber.css({'display': 'inline-block'})
                            .insertAfter(zoom);

                    $.ajaxS3({
                        type: 'POST',
                        url: ajaxURL,
                        data: JSON.stringify(unknowns),
                        dataType: 'json',
                        contentType: 'application/json; charset=utf-8',
                        success: function(data) {
                            $.extend(self.lookups, data);
                            dfd.resolve();
                            throbber.remove();
                            zoom.show();
                        },
                        error: function() {
                            dfd.reject();
                            throbber.remove();
                            zoom.show();
                        }
                    });
                }
            }
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

            var widgetID = '#' + $(this.element).attr('id');

            return {
                rows: $(widgetID + '-rows').val(),
                cols: $(widgetID + '-cols').val(),
                fact: $(widgetID + '-fact').val(),
                totals: $(widgetID + '-totals').is(':checked') ? 1 : 0
            };
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
            var urlParts,
                urlVars,
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
            urlParts = ajaxURL.split('?');
            if (urlParts.length > 1) {
                urlVars = urlParts[1].split('&');
                seen = {};
                for (i=0, len=urlVars.length; i < len; i++) {
                    q = urlVars[i].split('=');
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
            urlParts = url.split('?');
            if (urlParts.length > 1) {
                urlVars = urlParts[1].split('&');
                seen = {};
                for (i=0, len=urlVars.length; i < len; i++) {
                    q = urlVars[i].split('=');
                    if (q.length > 1) {
                        k = decodeURIComponent(q[0]);
                        if (!update[k]) {
                            queries.push(k + '=' + decodeURIComponent(q[1]));
                        }
                    }
                }
            }

            // Update URL
            var urlQuery = queries.join('&');
            var filteredURL = urlParts[0];
            if (urlQuery) {
                filteredURL = filteredURL + '?' + urlQuery;
            }
            return filteredURL;
        },

        /**
         * Update the Ajax URL with new options and filters
         *
         * @param {object} options: the pivot table URL options
         * @param {object} filters: the URL filters
         * @param {bool} noupdate: return the updated URL rather than setting it
         */
        _updateAjaxURL: function(options, filters, noupdate) {

            var ajaxURL = this.options.ajaxURL;

            // Construct the URL
            var urlParts = ajaxURL.split('?'),
                query = [],
                needsReload = false;

            var qstr, urlVars;

            if (urlParts.length > 1) {
                qstr = urlParts[1];
                urlVars = qstr.split('&');
            } else {
                qstr = '';
                urlVars = [];
            }

            var option, q, newopt;
            if (options) {
                for (option in options) {
                    newopt = options[option];
                    q = option + '=' + newopt;
                    if (option == 'totals') {
                        this.options.showTotals = newopt ? true : false;
                    } else if (!(needsReload || $.inArray(q, urlVars) != -1 )) {
                        needsReload = true;
                    }
                    query.push(q);
                }
            }

            var update = {},
                remove = {},
                subquery,
                i, len, k, v;

            // Check filters to update/remove (we're not using
            // S3.search.filterURL here, but an experimental
            // lazy-reload-pattern, i.e. we only reload data
            // if the filter or a pivot axis have actually changed.)
            if (filters) {

                // Operators excluding other filters for the same field
                var removeIncompatible = function(k) {

                    var exclusive = ['contains', 'anyof', 'belongs', 'eq'],
                        pattern,
                        match,
                        incompatible = [];

                    exclusive.forEach(function(op) {
                        pattern = new RegExp('__' + op + '$', 'g');
                        if (k.match(pattern)) {
                            match = pattern;
                        } else {
                            incompatible.push(op);
                        }
                    });

                    if (match) {
                        incompatible.forEach(function(op) {
                            remove[k.replace(match, '__' + op)] = true;
                        });
                    }
                };

                for (i=0, len=filters.length; i < len; i++) {
                    q = filters[i];
                    k = q[0];
                    v = q[1];

                    removeIncompatible(k);

                    if (v === null) {
                        if (!update[k]) {
                            remove[k] = true;
                        }
                    } else {
                        if (remove[k]) {
                            remove[k] = false;
                        }
                        subquery = k + '=' + encodeURIComponent(v);
                        if (update[k]) {
                            update[k].push(subquery);
                        } else {
                            update[k] = [subquery];
                        }
                    }
                }
            }

            // Check which existing URL query vars to retain/replace
            for (i=0, len=urlVars.length; i < len; i++) {
                q = urlVars[i].split('=');
                if (q.length > 1) {
                    k = decodeURIComponent(q[0]);
                    v = decodeURIComponent(q[1]);

                    if (remove[k]) {
                        needsReload = true;
                        continue;
                    } else if (update[k]) {
                        if (!(needsReload || $.inArray(k + '=' + v, update[k]) != -1)) {
                            needsReload = true;
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
                        query.push(urlVars[i]);
                    }
                }
            }

            // Add new filters
            for (k in update) {
                for (i=0, len=update[k].length; i < len; i++) {
                    if (!(needsReload || $.inArray(update[k][i], urlVars) != -1)) {
                        needsReload = true;
                    }
                    query.push(update[k][i]);
                }
            }

            var urlQuery = query.join('&'),
                filteredURL = urlParts[0];
            if (urlQuery) {
                filteredURL = filteredURL + '?' + urlQuery;
            }

            if (noupdate) {
                return filteredURL;
            } else {
                this.options.ajaxURL = filteredURL;
                return needsReload;
            }
        },

        /**
         * Utility function to replace the format extension in a REST URL
         *
         * @param {string} url - the URL
         * @param {string} extension - the new format extension
         *
         * @returns {string} - the new URL
         */
        _setExtension: function(url, extension) {

            var parser = document.createElement('a');

            parser.href = url;

            var path = parser.pathname.split('/'),
                items = [];
            if (path.length) {
                // Remove any file extensions from path
                path.forEach(function(item) {
                    var idx = item.lastIndexOf('.');
                    if (idx != -1) {
                        items.push(item.slice(0, idx));
                    } else {
                        items.push(item);
                    }
                });
                // Add file extension to last path element
                items[items.length - 1] += '.' + extension;
                // Reconstruct path
                parser.pathname = items.join('/');
            }

            // Drop (or replace) 'format' parameter from query
            var search = parser.search;
            if (search) {
                items = search.slice(1).split().filter(function(query) {
                    return query.split('=')[0] != 'format';
                });
                if (!path.length) {
                    items.push('format=' + extension);
                }
                parser.search = '?' + items.join('&');
            }

            return parser.href;
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
                needsReload,
                pivotdata = $el.find('input[type="hidden"][name="pivotdata"]');
            if (!pivotdata.length) {
                return;
            }

            // Show throbber
            $el.find('.pt-throbber').show();

            // Update ajaxURL with current options and filters
            if (options || filters) {
                needsReload = this._updateAjaxURL(options, filters);
            }

            if (needsReload || force) {
                // Reload data from server

                // Use $.searchS3 if available, otherwise (e.g. custom
                // page without s3.filter.js) fall back to $.ajaxS3:
                var ajaxURL = this.options.ajaxURL,
                    timeout = this.options.timeout,
                    ajaxMethod = $.ajaxS3;
                if ($.searchS3 !== undefined) {
                    ajaxMethod = $.searchS3;
                }

                // Hide empty section while loading
                $el.find('.pt-empty').hide();

                if (pt.openRequest) {
                    // Abort previously open request
                    pt.openRequest.onreadystatechange = null;
                    pt.openRequest.abort();
                }

                pt.openRequest = ajaxMethod({
                    'timeout': timeout,
                    'url': ajaxURL,
                    'dataType': 'json',
                    'type': 'GET',
                    'success': function(data) {
                        pt.openRequest = null;
                        pivotdata.first().val(JSON.stringify(data));
                        pt.refresh();
                    },
                    'error': function(jqXHR, textStatus, errorThrown) {
                        var msg;
                        if (errorThrown == 'UNAUTHORIZED') {
                            msg = i18n.gis_requires_login;
                        } else {
                            msg = jqXHR.responseText;
                        }
                        console.log(msg);
                    }
                });
            } else {
                // Refresh without reloading
                pt.refresh();
            }
        },

        /**
         * Download the pivot table as XLS spreadsheet
         */
        _downloadXLS: function() {

            // Make sure we actually have data in the pivot table
            var pivotdata = this.element.find('input[type="hidden"][name="pivotdata"]');
            if (!pivotdata.length) {
                return;
            }

            // Update options and filters
            var options = this._getOptions(),
                filters = this._getFilters();

            // Get updated ajaxURL (but do not set it so we do not
            // forestall autoSubmit)
            var ajaxURL = this._updateAjaxURL(options, filters, true);

            // Construct download URL
            var downloadURL = this._setExtension(ajaxURL, 'xls');

            // Use searchDownloadS3 if present, or fallback to window.open
            if ($.searchDownloadS3 !== undefined) {
                $.searchDownloadS3(downloadURL, '_blank');
            } else {
                window.open(downloadURL);
            }
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var pt = this,
                el = $(this.element),
                ns = this.eventNamespace,
                widgetID = '#' + el.attr('id');

            // Show/hide report options
            $(widgetID + '-options legend').on('click' + ns, function() {
                $(this).siblings().toggle();
                $(this).children().toggle();
            });
            $(widgetID + '-filters legend').on('click' + ns, function() {
                $(this).siblings().toggle();
                $(this).children().toggle();
            });

            // Show/hide pivot table
            $('.pt-hide-table', el).on('click' + ns, function() {
                pt.table_options.hidden = true;
                $('.pt-table', el).hide();
                $('.pt-export-opt', el).hide();
                $(this).hide().siblings('.pt-show-table').show();
            });
            $('.pt-show-table', el).on('click' + ns, function() {
                pt.table_options.hidden = false;
                $('.pt-table', el).show();
                $('.pt-export-opt', el).show();
                $(this).hide().siblings('.pt-hide-table').show();
            });

            // Exports
            $('.pt-export-xls', el).on('click' + ns, function() {
                pt._downloadXLS();
            });

            // Totals-option doesn't need Ajax-refresh
            $(widgetID + '-totals').on('click' + ns, function() {
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
                $(widgetID + '-pt-form input.pt-submit').on('click' + ns, function() {
                    var options = pt._getOptions(),
                        filters = pt._getFilters();
                    pt.reload(options, filters, false);
                });
            }

            // Zoom in
            $(widgetID + ' .pt-table .pt-cell-zoom').on('click' + ns, function(event) {
                var zoom = $(event.currentTarget),
                    cell = zoom.closest('.pt-cell');
                if (cell.length) {
                    pt._cellExplore(cell);
                }
            });

            // Charts
            $(widgetID + '-pchart-rows').on('click' + ns, function() {
                pt._renderChart({type: 'piechart', axis: 'rows'});
            });
            $(widgetID + '-vchart-rows').on('click' + ns, function() {
                pt._renderChart({type: 'barchart', axis: 'rows'});
            });
            $(widgetID + '-schart-rows').on('click' + ns, function() {
                pt._renderChart({type: 'spectrum', axis: 'rows'});
            });
            $(widgetID + '-hchart-rows').on('click' + ns, function() {
                pt._renderChart({type: 'breakdown', axis: 'rows'});
            });
            $(widgetID + '-pchart-cols').on('click' + ns, function() {
                pt._renderChart({type: 'piechart', axis: 'cols'});
            });
            $(widgetID + '-vchart-cols').on('click' + ns, function() {
                pt._renderChart({type: 'barchart', axis: 'cols'});
            });
            $(widgetID + '-schart-cols').on('click' + ns, function() {
                pt._renderChart({type: 'spectrum', axis: 'cols'});
            });
            $(widgetID + '-hchart-cols').on('click' + ns, function() {
                pt._renderChart({type: 'breakdown', axis: 'cols'});
            });
            $('.pt-hide-chart', el).on('click' + ns, function () {
                pt._renderChart(false);
            });
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var el = $(this.element),
                widgetID = '#' + el.attr('id'),
                ns = this.eventNamespace;

            $(widgetID + ' .pt-table .pt-cell-zoom').off(ns);
            $(widgetID + '-options legend').off(ns);
            $(widgetID + '-filters legend').off(ns);

            $(widgetID + '-totals').off(ns);

            $(widgetID + '-rows,' +
              widgetID + '-cols,' +
              widgetID + '-fact').off('change.autosubmit');

            $(widgetID + '-pt-form').off('optionChanged');

            $('input.pt-submit, .pt-export-xls', el).off(ns);

            $(widgetID + '-pchart-rows,' +
              widgetID + '-vchart-rows,' +
              widgetID + '-schart-rows,' +
              widgetID + '-hchart-rows,' +
              widgetID + '-pchart-cols,' +
              widgetID + '-vchart-cols,' +
              widgetID + '-schart-cols,' +
              widgetID + '-hchart-cols').off(ns);

            $('.pt-hide-table, .pt-show-table, .pt-hide-chart', el).off(ns);
        }
    });
})(jQuery);
