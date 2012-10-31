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

function reportRenderPieChart(src, title, layer) {

    var data = [];
    for (var i=0; i<src.length; i++) {
        var item = src[i];
        data.push({
            label: item[0],
            data: item[1]
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
                clickable: false
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
            reportShowTooltip(pos.pageX, pos.pageY, tooltip)
            $('.reportTooltipLabel').css({color: item.series.color});
        } else {
            reportRemoveTooltip();
        }
    });
}

function reportRenderBarChart(src, title, layer) {

    var data = [];
    var labels = [];
    for (var i=0; i<src.length; i++) {
        var item = src[i];
        data.push({label: item[0], data: [[i+1, item[1]]]});
        labels.push([i+1, item[0]]);
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
                clickable: false
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
            reportShowTooltip(pos.pageX, pos.pageY, tooltip)
            $('.reportTooltipLabel').css({color: item.series.color});
        } else {
            reportRemoveTooltip();
        }
    });
}

$(function() {
    $('#pie_chart_rows').click(function() {
        $('#chart-container').removeClass('hide');
        $('#chart').unbind('plothover');
        $('#chart').empty();
        reportRenderPieChart(json_data['rows'],
                             json_data['row_label'],
                             json_data['layer_label']);
    });
    $('#pie_chart_cols').click(function() {
        $('#chart-container').removeClass('hide');
        $('#chart').unbind('plothover');
        $('#chart').empty();
        reportRenderPieChart(json_data['cols'],
                             json_data['col_label'],
                             json_data['layer_label']);
    });
    $('#vbar_chart_rows').click(function() {
        $('#chart-container').removeClass('hide');
        $('#chart').unbind('plothover');
        $('#chart').empty();
        reportRenderBarChart(json_data['rows'],
                             json_data['row_label'],
                             json_data['layer_label']);
    });
    $('#vbar_chart_cols').click(function() {
        $('#chart-container').removeClass('hide');
        $('#chart').unbind('plothover');
        $('#chart').empty();
        reportRenderBarChart(json_data['cols'],
                             json_data['col_label'],
                             json_data['layer_label']);
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
                    lists.append(list)
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
