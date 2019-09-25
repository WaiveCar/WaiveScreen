function renderCampaigns(campaigns, brand) {
  moment.locale('en');
  let campaignList = document.querySelector('.campaign-list');
  campaignList.innerHTML = campaignList.innerHTML + `
    <div class="mt-2 mb-3">
      <span class="brand-name">${brand}</span>
    </div>
    <div class="row card-group ml-1" id="brand-${brand}">
      ${campaigns
        .map(
          (campaign, campaignIdx) =>
            `<div class="card mt-1 ml-2">
             <a class="prevent-underline" href="/campaigns/show?id=${
               campaign.id
             }">
               <div id="asset-container-${brand}-${campaignIdx}" style="height: 113px"> 
               </div>
               <div class="campaign-title mt-1">${campaign.project}</div>
               <div class="campaign-dates">
                 ${`${moment(campaign.start_time).format(
                   'MMM D',
                 )}   `}<i class="fas fa-play arrow"></i> ${`   ${moment(
              campaign.end_time,
            ).format('MMM D')}`}
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
        .join('')}
    </div>`;
  campaigns.forEach((campaign, campaignIdx) => {
    let e = Engine({
      container: document.querySelector(
        `#asset-container-${brand}-${campaignIdx}`,
      ),
    });
    e.AddJob({url: campaign.asset});
    e.Start();
  });
}

function groupByBrand(response) {
  let output = {};
  for (let c of response) {
    if (!output[c.brand_id]) {
      output[c.brand_id] = [];
    }
    output[c.brand_id].push(c);
  }
  return output;
}

(() => {
  const brandId = new URL(location.href).searchParams.get('brand_id');
  fetch(
    `http://192.168.86.58/api/campaigns${
      brandId ? `?brand_id=${brandId}` : ''
    }`,
  )
    .then(response => response.json())
    .then(json => {
      let byBrand = groupByBrand(json);
      Object.keys(byBrand).forEach(brand =>
        renderCampaigns(byBrand[brand], brand),
      );
    })
    .catch(e => console.log('error fetching screens', e));
})();
