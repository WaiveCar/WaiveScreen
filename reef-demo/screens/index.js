function renderScreens(screens, locations) {
  screens.sort((a, b) => {
    if (a.lat && !b.lat) {
      return -1;
    }
    if (b.lat && !a.lat) {
      return 1;
    }
    return;
  });
  screens = screens.slice(0, 20);
  let latLngs = '';
  screens.forEach(screen => (latLngs += `[${screen.lat}, ${screen.lng}],`));
  latLngs = latLngs.slice(0, latLngs.length - 1);
  fetch(`http://192.168.86.58/api/location?multi=[${latLngs}]`)
    .then(response => response.json())
    .then(json => {
      const screenTableBody = document.getElementById('screen-table-body');
      screenTableBody.innerHTML = screens
        .map(
          (screen, i) =>
            `
        <tr>
          <th><a href="show?id=${screen.id}">${screen.uid.slice(
              screen.uid.length - 4,
            )}</a></th>
          <th>${screen.project}</th>
          <th>${json[i]}</th>
          <th>${screen.phone}</th>
        </tr>
      `,
        )
        .join('');
    });
}
(() => {
  const screens = [];
  const locations = [];

  fetch('http://192.168.86.58/api/screens')
    .then(response => response.json())
    .then(json => screens.push(...json))
    .then(() => {
      renderScreens(screens);
      self._map = map({points: screens});
      let success = false;
      if (success) {
        _map.load(_campaign.shape_list);
      } else {
        _map.center([-118.34, 34.06], 11);
      }
    })
    .catch(e => console.log('error fetching screens', e));
})();
