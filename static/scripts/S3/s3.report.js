/**
    S3 Reporting Framework, Static JavaScript

    @author: Dominic König <dominic[AT]aidiq[DOT]com>

    @copyright: 2012 (c) Sahana Software Foundation
    @license: MIT

    @requires: jQuery
    @requires: jqplot

    @status: work in progress

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
*/

$(function() {
    var plot;
    render_pie_chart = function(src) {
        plot = jQuery.jqplot ('chart', [src],
            {
                seriesDefaults: {
                    renderer: $.jqplot.PieRenderer,
                    rendererOptions: {
                        showDataLabels: true,
                        diameter:200
                    }
                },
                legend: { show:true, location: 'e', escapeHtml:true }
            }
        );
    };
    $('#pie_chart_rows').click(function() {
        $('#chart-container').show();
        $('#chart').empty();
        render_pie_chart(json_data['rows']);
    });
    $('#pie_chart_cols').click(function() {
        $('#chart-container').show();
        $('#chart').empty();
        render_pie_chart(json_data['cols']);
    });
//     $('#chart-container').hide();
    $('#hide-chart').click(function(){
        $('#chart-container').hide();
    });
});
