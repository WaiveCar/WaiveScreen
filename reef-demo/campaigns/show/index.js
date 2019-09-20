function renderCampaign(campaign) {
  document.querySelector('.campaign-show-title').textContent =
    campaign.project[0].toUpperCase() + campaign.project.slice(1);
  document.querySelector('#start-date').value = campaign.start_time.split(
    ' ',
  )[0];
  document.querySelector('#end-date').value = campaign.end_time.split(' ')[0];
}

function calcItems() {
  requestAnimationFrame(() => {
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
    if (budget) {
      document.querySelector('#budget').textContent = `$${budget}`;
      document.querySelector('#cpm').textContent = `$${fakeCPM}`;
      document.querySelector(
        '#impressions',
      ).textContent = `${fakeNumImpressionsPerWeek}`;
    }
  });
}

let campaign = null;

let selectedLinkIdx = 0;
let topBarRight = document.querySelector('.top-bar-right');

function changeSelected(newIdx) {
  topBarRight.children[selectedLinkIdx].classList.remove('top-bar-selected');
  selectedLinkIdx = newIdx;
  topBarRight.children[selectedLinkIdx].classList.add('top-bar-selected');
}

(() => {
  topBarRight.innerHTML = [
    'Overview',
    'Budget',
    'Performance',
    'Controls',
    'Creatives',
    'Billing',
    'Summary',
    'Location',
  ]
    .map(
      (item, i) => `
    <a href="#${item}">
      <div class="top-bar-link" onclick="changeSelected(${i})">
        ${item}
      </div>
    </a>
  `,
    )
    .concat(['<div class="top-bar-link update-campaign-btn">Update</div>'])
    .join('');
  topBarRight.children[selectedLinkIdx].classList.add('top-bar-selected');

  window.addEventListener('hashchange', function() {
    window.scrollTo(window.scrollX, window.scrollY - 50);
  });

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
