function calcItems() {
  setTimeout(() => {
    let schedule = JSON.parse($('#schedule').jqs('export'));
    let minutesPerWeek = schedule.reduce((acc, item) => {
      return (
        acc +
        item.periods.reduce((acc, period) => {
          return (
            acc +
            moment(period.end, 'hh:mm').diff(
              moment(period.start, 'hh:mm'),
              'minutes',
            )
          );
        }, 0)
      );
    }, 0);
    let budget = document.querySelector('#budget').value;
    let fakeNumImpressionsPerWeek = budget * 14.32;
    let fakeCPM = (fakeNumImpressionsPerWeek / budget / 100).toFixed(2);
    document.querySelector('#budget').textContent = `$${budget}`;
    document.querySelector('#cpm').textContent = `$${fakeCPM}`;
    document.querySelector(
      '#impressions',
    ).textContent = `${fakeNumImpressionsPerWeek}`;
  });
}

(() => {
  $('#schedule').jqs();
  document
    .getElementById('campaign-budget')
    .addEventListener('change', calcItems);
  document
    .getElementById('campaign-budget')
    .addEventListener('keyup', calcItems);
  document
    .querySelector('.jqs-table tbody')
    .addEventListener('mouseup', calcItems);
})();
