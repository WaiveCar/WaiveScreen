function renderCampaigns(campaigns, inputStatus) {
  let status = inputStatus;
  moment.locale('en');
  let campaignList = document.querySelectorAll('.campaign-list');
  campaignList.forEach(
    (node, listIdx) =>
      (node.innerHTML = campaigns
        .map(
          (campaign, campaignIdx) => `<div class="card mt-1 ml-2">
           <a class="prevent-underline" href="/campaigns/show?id=${
             campaign.id
           }">
             <div id="asset-container-${listIdx}-${campaignIdx}" style="height: 113px"> 
             </div>
             <div class="campaign-title mt-1">${campaign.project}</div>
             <div class="campaign-dates">
               ${`${moment(campaign.start_time).format(
                 'MMM D',
               )}   `}<i class="fas fa-play arrow"></i> ${`   ${moment(
            campaign.end_time,
          ).format('MMM D')}`}
             </div>
           </a>
           <div class="user-icon-holder">
              ${
                listIdx === 0
                  ? `<a href="" class="campaign-dates"><i class="fas fa-plus"></i> <span style="font-size: 14px"> approve</span></a>`
                  : ''
              }
              ${
                listIdx === 1
                  ? `<a href="" class="campaign-dates"><i class="fas fa-pause"></i> <span style="font-size: 14px"> pause</span></a>`
                  : ''
              }
              ${
                listIdx === 2
                  ? `<a href="" class="campaign-dates"><i class="fas fa-play"></i> <span style="font-size: 14px"> resume</span></a>`
                  : ''
              }
           </div>
         </div>`,
        )
        .join('')),
  );
  campaignList.forEach((node, listIdx) =>
    campaigns.forEach((campaign, campaignIdx) => {
      let e = Engine({
        container: document.querySelector(
          `#asset-container-${listIdx}-${campaignIdx}`,
        ),
      });
      e.AddJob({url: campaign.asset});
      e.Start();
    }),
  );
}

(() => {
  fetch('http://waivescreen.com/api/campaigns')
    .then(response => response.json())
    .then(json => {
      renderCampaigns(json);
    })
    .catch(e => console.log('error fetching screens', e));
})();
