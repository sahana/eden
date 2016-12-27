$(document).ready(function() {
  // based on prepared DOM, initialize echarts instance
  var myChart = echarts.init(document.getElementById('timeline-embed'));

  // specify chart configuration item and data
  var option = {
    title: {
      text: ''
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data:['Amount of Incidents']
    },
    grid: {
      top: '12px',
      right: '12px',
      bottom: '24px',
      left: '24px'
    },
    backgroundColor: '#d6d7d9',
    textStyle: {
        color: '#323a45'
    },
    labelLine: {
      normal: {
        lineStyle: {
          color: 'rgba(0, 0, 0, 0)'
        }
      }
    },
    lineStyle: {
      normal: {
        width: 4
      }
    },
    markLine: {
      normal: {
        lineStyle: {
          color: 'rgba(0, 0, 0, 0)'
        }
      }
    },
    itemStyle: {
      normal: {
        color: '#cd2026'
      }
    },
    xAxis: {
      type: 'category',
      data: [
        "5 Incidents",
        "3 Incidents",
        "4 Incidents",
        "13 Incidents",
        "2 Incidents",
        "14 Incidents"
      ]
    },
    yAxis: {
      type: 'value'
    },
    series: [{
      name: 'Incidents',
      type: 'line',
      data: [5, 3, 4, 13, 2, 14]
    }]
  };

  // use configuration item and data specified to show chart
  myChart.setOption(option);
});