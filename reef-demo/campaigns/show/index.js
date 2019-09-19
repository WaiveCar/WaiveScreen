
function renderCampaign(campaign) {
  console.log(campaign);
  document.getElementById('campaign-title').textContent = campaign.project;
  document.querySelector('#start-date').value = campaign.start_time.split(' ')[0];
  document.querySelector('#end-date').value = campaign.end_time.split(' ')[0];
}

function toggleEditor() {
  document.getElementsByClassName('editor')[0].classList.toggle('show');
}

function calcItems() {
  setTimeout(() => {
    let schedule = JSON.parse($('#schedule').jqs('export'));
    let minutesPerWeek = schedule.reduce((acc, item) => {
      return (
        acc +
        item.periods.reduce((acc, period) => {
          console.log('period', period);
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

let campaign = null;

(() => {
  $('#schedule').jqs();
  const id = new URL(location.href).searchParams.get('id');
  fetch(`http://waivescreen.com/api/campaigns?id=${id}`)
    .then(response => response.json())
    .then(json => {
      campaign = json[0];
      renderCampaign(json[0]);
    })
    .catch(e => console.log('error fetching screens', e));
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
