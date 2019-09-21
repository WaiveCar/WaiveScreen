function renderCampaigns(campaigns) {
  moment.locale('en');
  document.querySelectorAll('.campaign-list').forEach(node => node.innerHTML = campaigns
    .map(
      campaign =>
        `<div class="card mt-1 ml-2">
           <a class="prevent-underline" href="/campaigns/show?id=${campaign.id}">
             <div id="asset-container-1"> 
               <div>
                 <img src="http://waivecar-prod.s3.amazonaws.com/311a1ccb-c3d0-4c42-995d-5d3d38af0bf2.jpeg" class="campaign-image-preview">
               </div>
             </div>
             <div class="campaign-title mt-1">${campaign.project}</div>
             <div class="campaign-dates">
               ${`${moment(campaign.start_time).format('MMM D')}   `}<i class="fas fa-play arrow"></i> ${`   ${moment(campaign.end_time).format('MMM D')}`}
             </div>
             <div class="user-icon-holder">
               <img src="../svg/user-icon.svg" class="user-icon">
               <img src="../svg/user-icon.svg" class="user-icon">
               <img src="../svg/user-icon.svg" class="user-icon">
               <img src="../svg/user-icon.svg" class="user-icon">
             </div>
           </a>
         </div>`,
    )
    .join(''));
}

(() => {
  fetch('http://waivescreen.com/api/campaigns')
    .then(response => response.json())
    .then(json => {
      renderCampaigns(json);
    })
    .catch(e => console.log('error fetching screens', e));
})();
