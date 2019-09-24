(() => {
  console.log('here');
  window.chartColors = {
    red: 'rgb(255, 99, 132)',
    orange: 'rgb(255, 159, 64)',
    yellow: '#fedc47',
    green: 'rgb(75, 192, 192)',
    blue: 'rgb(54, 162, 235)',
    purple: 'rgb(153, 102, 255)',
    grey: 'rgb(201, 203, 207)',
  };
  chart1();
})();

function chart1() {
  function nextVal(date, lastCount, i) {
    var impressionCounts = [
      0,
      4084,
      33074,
      106723,
      83706,
      84957,
      75615,
      109611,
      168552,
      117820,
      87177,
      122732,
      89352,
      49303,
      155203,
      111235,
      65087,
      103426,
      102824,
      101306,
      105517,
      129283,
      96884,
      130025,
      102495,
      60772,
      112026,
      168445,
      150818,
      90633,
      95544,
      15382,
      140500,
      57950,
      123479,
      140891,
      39569,
      75645,
      90429,
      147522,
      105722,
      186988,
      110638,
      50873,
      84417,
      156382,
      68850,
      200902,
      131360,
      115607,
      76344,
      140875,
      100465,
      68137,
      91241,
      131633,
      135400,
      70507,
      187823,
      32466,
    ];
    var count = lastCount + impressionCounts[i];
    return {
      t: date.valueOf(),
      y: count,
    };
  }

  var dateFormat = 'MMMM DD YYYY';
  var date = moment('July 29 2019', dateFormat);
  var data = [nextVal(date, 0, 0)];
  for (var i = 1; i < 60; i++) {
    date = date.clone().add(1, 'd');
    data.push(nextVal(date, data[data.length - 1].y, i));
  }

  var ctx = document.getElementById('screen-chart-1').getContext('2d');
  ctx.canvas.width = 1000;
  ctx.canvas.height = 300;

  var color = Chart.helpers.color;
  var cfg = {
    type: 'bar',
    data: {
      datasets: [
        {
          label: 'Impressions Per Screen',
          backgroundColor: color(window.chartColors.yellow)
            .alpha(0.5)
            .rgbString(),
          borderColor: window.chartColors.yellow,
          data: data,
          type: 'line',
          pointRadius: 0,
          fill: true,
          lineTension: 0,
          borderWidth: 2,
        },
      ],
    },
    options: {
      scales: {
        xAxes: [
          {
            type: 'time',
            distribution: 'series',
            ticks: {
              source: 'auto',
              autoSkip: true,
            },
          },
        ],
        yAxes: [
          {
            scaleLabel: {
              display: true,
              labelString: 'Impressions',
            },
          },
        ],
      },
      tooltips: {
        intersect: false,
        mode: 'index',
        callbacks: {
          label: function(tooltipItem, myData) {
            var label = myData.datasets[tooltipItem.datasetIndex].label || '';
            if (label) {
              label += ': ';
            }
            label += parseFloat(tooltipItem.value).toFixed(0);
            return label;
          },
        },
      },
    },
  };
  var chart = new Chart(ctx, cfg);
}

