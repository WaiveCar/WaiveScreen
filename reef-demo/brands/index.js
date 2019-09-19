function renderBrands(brands) {
  document.getElementById('brands-table-body').innerHTML = brands
    .map(
      brand =>
        `
        <tr>
          <th><a href="show/index.html?id=${brand.id}">${brand.id}</a></th>
          <th>${brand.project}</th>
          <th>${brand.lat}, ${brand.lng}</th>
          <th>${brand.phone}</th>
        </tr>
      `,
    )
    .join('');
}
(() => {
  const brands = [];
  fetch('http://waivescreen.com/api/brands')
    .then(response => response.json())
    .then(json => brands.push(...json))
    .then(() => {
      renderBrands(brands);
    })
    .catch(e => console.log('error fetching brands', e));
})();
