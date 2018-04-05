/* Static JavaScript code for dc_TargetReport */

S3.dc_results = function(selector, data) {
    // https://bl.ocks.org/mbostock/3310560
    var margin = {top: 10, right: 15, bottom: 20, left: 25},
        width = 480 - margin.left - margin.right,
        height = 250 - margin.top - margin.bottom;

    var x = d3.scale.ordinal().rangeRoundBands([0, width], 0.1, 0.2)
        y = d3.scale.linear().rangeRound([height, 0]);

    var svg = d3.select(selector)
                .attr('width', width + margin.left + margin.right)
                .attr('height', height + margin.top + margin.bottom);

    var g = svg.append('g')
               .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

    data = JSON.parse(data);

    x.domain(data.map(function(d) { return d.o; }));
    y.domain([0, d3.max(data, function(d) { return d.v; })]);

    g.append('g')
      .attr('class', 'x axis')
      .attr('transform', 'translate(0,' + height + ')')
      .call(d3.svg.axis().scale(x).orient('bottom'));

    g.append('g')
      .attr('class', 'y axis')
      .call(d3.svg.axis().scale(y).orient('left')) // .ticks(10, '%')
      .append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 6)
      .attr('dy', '0.71em')
      .attr('text-anchor', 'end')
      .text('Responses'); // @ToDo: i18n

    g.selectAll('.bar')
      .data(data)
      .enter().append('rect')
      .attr('class', 'bar')
      .attr('x', function(d) { return x(d.o); })
      .attr('y', function(d) { return y(d.v); })
      .attr('width', x.rangeBand())
      .attr('height', function(d) { return height - y(d.v); });
}
