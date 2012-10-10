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

$(function() {
    var plot;
    render_pie_chart = function(src, title, layer) {
        plot = jQuery.jqplot('chart', [src],
            {
                seriesDefaults: {
                    renderer: $.jqplot.PieRenderer,
                    rendererOptions: {
                        showDataLabels: true,
                        diameter:250
                    }
                },
                highlighter: {
                    show: true,
                    formatString:'%s: %s',
//                     tooltipPosition: 'e',
                    tooltipOffset: -200,
                    tooltipAxes: 'xy',
                    useAxesFormatters:false
                },
                title: layer + ' ' + title,
                legend: { show:true, location: 'e', escapeHtml:true }
            }
        );
    };
    render_vbar_chart = function(src, title, layer) {
        var s = new Array(src.length);
        var t = new Array(src.length);
        minzero = 0;
        rotate = 0;
        for (var i=0; i<src.length; i++) {
            t[i] = src[i][0];
            s[i] = src[i][1];
            if (s[i] < 0) {
                minzero = null;
            }
            if (t[i].length > 15) {
                rotate = -60;

            }
        }
        plot = $.jqplot('chart', [s], {
            seriesDefaults:{
                renderer:$.jqplot.BarRenderer,
                rendererOptions: {
                    barPadding: 8,
                    barMargin: 20,
                    varyBarColor: true
                }
            },
            highlighter: {
                show: true,
                formatString:'%s',
                tooltipAxes: 'y',
                useAxesFormatters: false
            },
            axes: {
                xaxis: {
                    renderer: $.jqplot.CategoryAxisRenderer,
                    ticks: t,
                    tickRenderer: $.jqplot.CanvasAxisTickRenderer ,
                    tickOptions: {
                        angle: rotate
                    }
                },
                yaxis: {
                    rendererOptions: {
                        forceTickAt0: true
                    },
//                     min: minzero,
//                     autoscale: autoscale
                    padMax: 1.2
                }
            },
            title: layer + ' ' + title
        });
    };
    $('#pie_chart_rows').click(function() {
        $('#chart-container').removeClass('hide');
        $('#chart').empty();
        render_pie_chart(json_data['rows'], json_data['row_label'], json_data['layer_label']);
    });
    $('#pie_chart_cols').click(function() {
        $('#chart-container').removeClass('hide');
        $('#chart').empty();
        render_pie_chart(json_data['cols'], json_data['col_label'], json_data['layer_label']);
    });
    $('#vbar_chart_rows').click(function() {
        $('#chart-container').removeClass('hide');
        $('#chart').empty();
        render_vbar_chart(json_data['rows'], json_data['row_label'], json_data['layer_label']);
    });
    $('#vbar_chart_cols').click(function() {
        $('#chart-container').removeClass('hide');
        $('#chart').empty();
        render_vbar_chart(json_data['cols'], json_data['col_label'], json_data['layer_label']);
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
