function renderCampaigns(campaigns, status) {
  moment.locale('en');
  document.querySelectorAll(`#${status}-campaigns`).forEach(
    node =>
      (node.innerHTML = campaigns
        .map(
          campaign =>
            `<div class="card mt-1 ml-2">
           <a class="prevent-underline" href="/campaigns/show?id=${
             campaign.id
           }">
             <div id="asset-container-1"> 
               <div>
                 <img src="http://waivecar-prod.s3.amazonaws.com/311a1ccb-c3d0-4c42-995d-5d3d38af0bf2.jpeg" class="campaign-image-preview">
               </div>
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
              ${status === 'pending' ? `<a href="" class="campaign-dates"><i class="fas fa-plus"></i> <span style="font-size: 14px"> approve</span></a>` : ''}
              ${status === 'active' ? `<a href="" class="campaign-dates"><i class="fas fa-pause"></i> <span style="font-size: 14px"> pause</span></a>` : ''}
              ${status === 'paused' ? `<a href="" class="campaign-dates"><i class="fas fa-play"></i> <span style="font-size: 14px"> resume</span></a>` : ''}
           </div>
         </div>`,
        )
        .join('')),
  );
}

(() => {
  fetch('http://waivescreen.com/api/campaigns')
    .then(response => response.json())
    .then(json => {
      ['pending', 'active', 'paused'].forEach(
        status => renderCampaigns(json, status),
      );
    })
    .catch(e => console.log('error fetching screens', e));
})();