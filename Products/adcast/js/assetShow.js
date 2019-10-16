function render(type, asset) {
  console.log('type: ', type);
  console.log('asset: ', asset);
  // Here something will eventually need to be done with the asset
}

(() => {
  const id = new URL(location.href).searchParams.get('id');
  const type = document.currentScript.getAttribute('asset')
  fetch(`http://waivescreen.com/api/${type}?id=${id}`)
    .then(response => response.json())
    .then(json => render(type, json[0]))
    .catch(e => console.log('error fetching user', e));
})();
