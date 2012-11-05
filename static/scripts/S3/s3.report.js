/**
 * S3 Reporting Framework, Static JavaScript
 *
 * copyright: 2012 (c) Sahana Software Foundation
 * license: MIT
 *
 * requires: jQuery
 * requires: jqplot
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use,
 * copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following
 * conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 * OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 * OTHER DEALINGS IN THE SOFTWARE.
 */

var reportDataIndex = null;
var reportSeriesIndex = null;
var reportChart = null;

function reportShowTooltip(x, y, contents) {
    $('<div id="reportTooltip">' + contents + '</div>').css({
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
}

function reportRemoveTooltip() {
    $('#reportTooltip').remove();
    reportDataIndex = null;
}

function reportRenderPieChart(json, dim) {

    $('#chart-container').css({width: '800px'});
    $('#chart').css({height: '360px'});

    var d = json['d'], src, xdim, title;
    if (dim === 0) {
        src = d['rows'];
        xdim = json['r'];
        title = json['y'];
    } else {
        src = d['cols'];
        xdim = json['c'];
        title = json['x'];
    }
    var layer = json['t'];

    var url = json['u'], concat = '?';
    for (var f in json['f']) {
        url += concat + f + '=' + json['f'][f];
        concat = '&';
    }

    var data = [];
    for (var i=0; i<src.length; i++) {
        var item = src[i];
        data.push({
            label: item[2],
            data: item[3]
        });
    }
    $('#chart-header').html('<h4>'+layer + ' ' + title+'</h4>');

    reportChart = jQuery.plot($('#chart'), data,
        {
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

    $('#chart').bind('plothover', function(event, pos, item) {
        if (item) {
            if (reportDataIndex == item.seriesIndex) {
                return;
            }
            reportRemoveTooltip();
            reportDataIndex = item.seriesIndex;
            var value = item.series.data[0][1];
            var percent = item.series.percent.toFixed(1);
            var tooltip = '<div class="reportTooltipLabel">' + item.series.label + '</div>';
            tooltip += '<div class="reportTooltipValue">' + value + ' (' + percent + '%)</div>';
            reportShowTooltip(pos.pageX, pos.pageY, tooltip);
            $('.reportTooltipLabel').css({color: item.series.color});
        } else {
            reportRemoveTooltip();
        }
    });
    $('#chart').bind('plotclick', function(event, pos, item) {
        if (item) {
            var page = new String(url), val;
            if (xdim) {
                try {
                    val = src[item.seriesIndex][1];
                }
                catch(e) {
                    val = null;
                }
                if (val) {
                    page += concat + xdim + '=' + val;
                }
            }
            window.open(page, '_blank');
        }
    });
}

function reportRenderBarChart(json, dim) {

    $('#chart-container').css({width: '100%'});
    $('#chart').css({height: '360px'});

    var d = json['d'], src, xdim, title;
    if (dim === 0) {
        src = d['rows'];
        xdim = json['r'];
        title = json['y'];
    } else {
        src = d['cols'];
        xdim = json['c'];
        title = json['x'];
    }
    var layer = json['t'];

    var url = json['u'], concat = '?';
    for (var f in json['f']) {
        url += concat + f + '=' + json['f'][f];
        concat = '&';
    }

    var data = [];
    var labels = [];
    for (var i=0; i<src.length; i++) {
        var item = src[i];
        data.push({label: item[2], data: [[i+1, item[3]]]});
        labels.push([i+1, item[2]]);
    }
    $('#chart-header').html('<h4>'+layer + ' ' + title+'</h4>');

    reportChart = jQuery.plot($('#chart'), data,
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
                max: src.length+1,
                tickLength: 0
            }
        }
    );
    $('#chart').bind('plothover', function(event, pos, item) {
        if (item) {
            if (reportDataIndex == item.seriesIndex) {
                return;
            }
            reportRemoveTooltip();
            reportDataIndex = item.seriesIndex;
            var value = item.series.data[0][1];
            var tooltip = '<div class="reportTooltipLabel">' + item.series.label + '</div>';
            tooltip += '<div class="reportTooltipValue">' + value + '</div>';
            reportShowTooltip(pos.pageX, pos.pageY, tooltip);
            $('.reportTooltipLabel').css({color: item.series.color});
        } else {
            reportRemoveTooltip();
        }
    });
    $('#chart').bind('plotclick', function(event, pos, item) {
        if (item) {
            var page = new String(url), val;
            if (xdim) {
                try {
                    val = src[item.seriesIndex][1];
                }
                catch(e) {
                    val = null;
                }
                if (val) {
                    page += concat + xdim + '=' + val;
                }
            }
            window.open(page, '_blank');
        }
    });
}

function reportRenderBreakdown(json, dim) {

    var src = json['d'];

    $('#chart-container').css({width: '100%'});

    var idata = src.cells, rdim, cdim, rows, cols, title, get_data;
    if (dim === 0) {
        // breakdown cols by rows
        title = json['y'];
        rdim = json['r'];
        cdim = json['c'];
        rows = src.rows;
        cols = src.cols;
        get_data = function(i, j) { return idata[i][j]; };
    } else {
        // breakdown rows by cols
        title = json['x'];
        rdim = json['c'];
        cdim = json['r'];
        rows = src.cols;
        cols = src.rows;
        get_data = function(i, j) { return idata[j][i]; };
    }

    var height = Math.max(rows.length * Math.max((cols.length + 1) * 16, 50) + 70, 360);
    $('#chart').css({height: height + 'px'});

    var layer = json['t'];

    var url = json['u'], concat = '?';
    for (var f in json['f']) {
        url += concat + f + '=' + json['f'][f];
        concat = '&';
    }

    var odata = [];
    var xmax = 0;
    for (var c=0; c<cols.length; c++) {
        // every col gives a series
        var series = {label: cols[c][2]};
        var values = [];
        for (var r=0; r<rows.length; r++) {
            var index = (r + 1) * (cols.length + 1) - c;
            var value = get_data(r, c);
            if (value > xmax) {
                xmax = value;
            }
            values.push([value, index]);
        }
        series['data'] = values;
        odata.push(series);
    }

    var yaxis_ticks = [];
    for (r=0; r<rows.length; r++) {
        var label = rows[r][2];
        index = (r + 1) * (cols.length + 1) + 1;
        yaxis_ticks.push([index, label]);
    }

    $('#chart-header').html('<h4>'+layer + ' ' + title+'</h4>');
    reportChart = jQuery.plot($('#chart'), odata,
        {
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
    $('.yAxis .tickLabel').css({'padding-top': '20px'});
    $('#chart').bind('plothover', function(event, pos, item) {
        if (item) {
            if (reportDataIndex == item.dataIndex && reportSeriesIndex == item.seriesIndex) {
                return;
            }
            reportRemoveTooltip();
            reportDataIndex = item.dataIndex;
            reportSeriesIndex = item.seriesIndex;
            var name = rows[reportDataIndex][2];
            var value = item.datapoint[0];
            var tooltip = '<div class="reportTooltipLabel">' + name + '</div>';
            tooltip += '<div class="reportTooltipValue">' + item.series.label + ' : <span class="reportItemValue">' + value + '</span></div>';
            reportShowTooltip(pos.pageX, pos.pageY, tooltip);
            $('.reportTooltipLabel').css({'padding-bottom': '8px'});
            $('.reportTooltipValue').css({color: item.series.color});
            $('.reportItemValue').css({'font-weight': 'bold'});
        } else {
            reportRemoveTooltip();
        }
    });
    $('#chart').bind('plotclick', function(event, pos, item) {
        var s = concat;
        if (item) {
            var page = new String(url), rval, cval;
            if (rdim) {
                try {
                    rval = rows[item.dataIndex][1];
                }
                catch(e) {
                    rval = null;
                }
                if (rval) {
                    page += s + rdim + '=' + rval;
                    s = '&';
                }
            }
            if (cdim) {
                try {
                    cval = cols[item.seriesIndex][1];
                }
                catch(e) {
                    cval = null;
                }
                if (cval) {
                    page += s + cdim + '=' + cval;
                }
            }
            window.open(page, '_blank');
        }
    });
}

$(function() {

    // json_data comes with the page, and contains these attributes:
    //
    // t - Title of the layer
    // x - Label for the cols-dimension
    // y - Label for the rows-dimension
    // r - Field selector for the rows-dimension (to construct URLs)
    // c - Field selector for the cols-dimension (to construct URLs)
    // d - Compact report data (see S3PivotTable.compact())
    // u - URL of the resource
    // f - URL query variables of the report filter widgets

    $('#pie_chart_rows').click(function() {
        $('#chart-container').removeClass('hide');
        $('#chart').unbind('plothover');
        $('#chart').unbind('plotclick');
        $('#chart').empty();
        reportRenderPieChart(json_data, 0);
    });
    $('#pie_chart_cols').click(function() {
        $('#chart-container').removeClass('hide');
        $('#chart').unbind('plothover');
        $('#chart').unbind('plotclick');
        $('#chart').empty();
        reportRenderPieChart(json_data, 1);
    });
    $('#vbar_chart_rows').click(function() {
        $('#chart-container').removeClass('hide');
        $('#chart').unbind('plothover');
        $('#chart').unbind('plotclick');
        $('#chart').empty();
        reportRenderBarChart(json_data, 0);
    });
    $('#vbar_chart_cols').click(function() {
        $('#chart-container').removeClass('hide');
        $('#chart').unbind('plothover');
        $('#chart').unbind('plotclick');
        $('#chart').empty();
        reportRenderBarChart(json_data, 1);
    });
    $('#bd_chart_rows').click(function() {
        $('#chart-container').removeClass('hide');
        $('#chart').unbind('plothover');
        $('#chart').unbind('plotclick');
        $('#chart').empty();
        reportRenderBreakdown(json_data, 0);
    });
    $('#bd_chart_cols').click(function() {
        $('#chart-container').removeClass('hide');
        $('#chart').unbind('plothover');
        $('#chart').unbind('plotclick');
        $('#chart').empty();
        reportRenderBreakdown(json_data, 1);
    });
    $('#hide-chart').click(function(){
        $('#chart-container').addClass('hide');
    });

    // Toggle the report options
    $('#reportform legend').click(function(){
        $(this).siblings().toggle();
        $(this).children().toggle();
    });

    /*
     * User can click on a magnifying glass in the cell to show
     * the list of values for each cell layer
     */
    $('table#list tbody').on('click', 'a.report-cell-zoom', function(event) {
        zoom = $(event.currentTarget);
        cell = zoom.parent();

        lists = cell.find('.report-cell-records');

        if (lists.length > 0) {
            lists.remove();
            zoom.removeClass('opened');
        }
        else {
            layers = cell.data('records');

            if (layers) {
                lists = $('<div/>').addClass('report-cell-records');

                for (var layer=0, ln=layers.length; layer<ln; layer++) {
                    var list = $('<ul/>');
                    var records = layers[layer];

                    for (var record=0, rn=records.length; record<rn; record++) {
                        list.append('<li>' + json_data.cell_lookup_table[layer][records[record]] + '</li>');
                    }
                    lists.append(list);
                }

                cell.append(lists);
                zoom.addClass('opened');
            }
        }
    });
});

$(document).ready(function() {
    // Hide the report options when the page loads
    $('#report_options legend').siblings().toggle();
});
