function renderBrand(brand) {
  const brandTitle = document.getElementById('brand-title');
  brandTitle.textContent = `Organization ${brand.id} Info`;
}

(() => {
  const id = new URL(location.href).searchParams.get('id');
  fetch(`http://waivescreen.com/api/brands?id=${id}`)
    .then(response => response.json())
    .then(json => renderBrand(json[0]))
    .catch(e => console.log('error fetching brand', e));
})();
