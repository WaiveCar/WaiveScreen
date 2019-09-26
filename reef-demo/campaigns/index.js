function renderCampaigns(campaigns, brand, brandIdx) {
  moment.locale('en');
  let campaignList = document.querySelector('.campaign-list');
  let newEl = document.createElement('div');
  newEl.innerHTML = `
    <div class="mt-2 mb-3">
      <span class="brand-name">${brand}</span>
    </div>
    <div class="row card-group ml-1" id="brand-${brandIdx}">
      ${campaigns
        .map(
          (campaign, campaignIdx) =>
            `<div class="card mt-1 ml-2">
             <a class="prevent-underline" href="/campaigns/show?id=${
               campaign.id
             }">
               <div id="asset-container-${brandIdx}-${campaignIdx}" style="height: 145px;"> 
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
  campaignList.appendChild(newEl);
  campaigns.forEach((campaign, campaignIdx) => {
    let e = Engine({
      container: document.querySelector(
        `#asset-container-${brandIdx}-${campaignIdx}`,
      ),
    });
    e.AddJob({url: campaign.asset});
    e.Start();
  });
}

function groupByBrand(response, brands) {
  let brandTable = {};
  for (let brand of brands) {
    brandTable[brand.id] = brand.name;
  }
  let output = {};
  for (let c of response) {
    if (!output[brandTable[c.brand_id]]) {
      output[brandTable[c.brand_id]] = [];
    }
    output[brandTable[c.brand_id]].push(c);
  }
  return output;
}

(() => {
  const brandId = new URL(location.href).searchParams.get('brand_id');
  fetch('http://192.168.86.58/api/brands')
    .then(response => response.json())
    .then(brands => {
      fetch(
        `http://192.168.86.58/api/campaigns${
          brandId ? `?brand_id=${brandId}` : ''
        }`,
      )
        .then(response => response.json())
        .then(json => {
          let byBrand = groupByBrand(json, brands);
          Object.keys(byBrand).forEach((brand, brandIdx) => {
            renderCampaigns(byBrand[brand], brand, brandIdx);
          });
        });
    })
    .catch(e => console.log('error fetching screens', e));
})();
