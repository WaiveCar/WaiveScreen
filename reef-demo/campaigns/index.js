function renderCampaigns(campaigns) {
  document.getElementById('campaign-list').innerHTML = campaigns.map(campaign => 
    `<div class="card" style="width: 450px">
       <h4>${campaign.project}</h4>
       <div title=1 class='asset-container' id='asset-container-1'/> </div>
       <div title="1" class="asset-container engine-xA8tAY4YSBmn2RTQqnnXXw" id="asset-container-1"> 
         <div>
           <img src="http://waivecar-prod.s3.amazonaws.com/311a1ccb-c3d0-4c42-995d-5d3d38af0bf2.jpeg" class="campaign-image-preview">
         </div>
       </div>
       <div class="card-body">
         <p class="card-text"></p>
         <div class="btn-group" role="group" aria-label="Actions">
           <h3>
             <span class="badge badge-info" style=margin-left:1rem><a href="">Client Name</a></span>
             <span class='badge badge-pill badge-dark'>Priority: ${campaign.priority}</span>                   
           </h3>
         </div>
         <div class="btn-group" role="group" aria-label="Actions">
           <h3>
             <span class="badge badge-info" style=margin-left:1rem><a href="">Start: ${campaign.start_time}</a></span>
             <span class='badge badge-pill badge-dark'>End: ${campaign.end_time}</span>                   
           </h3>
         </div>
         <a class="btn btn-primary" href="/campaigns/show/index.html?id=${campaign.id}">Edit/Modify</a>
       </div>
    </div>
  `
  ).join('');
};

(() => {
  fetch('http://waivescreen.com/api/campaigns')
    .then(response => response.json())
    .then(json => {
      renderCampaigns(json);
    })
    .catch(e => console.log('error fetching screens', e));
})();
