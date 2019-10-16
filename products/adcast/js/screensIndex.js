function renderScreens(screens, locations) {
  screens.sort((a, b) => {
    if (a.uid.match(/fake/gi) && !b.uid.match(/fake/gi)) {
      return 1;
    }
    if (b.uid.match(/fake/gi) && !a.uid.match(/fake/gi)) {
      return -1;
    }
    return;
  });
  screens = screens.filter(s => s.lat && !isNaN(Number(s.lat))).filter(s => s.phone);
  screens = screens.slice(0, 30);
  let latLngs = '';
  screens.forEach(screen => (latLngs += `[${screen.lat}, ${screen.lng}],`));
  latLngs = latLngs.slice(0, latLngs.length - 1);
  fetch(`http://adcast/api/location?multi=[${latLngs}]`)
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
          <th>${screen.uptime}</th>
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

  fetch('http://adcast/api/screens')
    .then(response => response.json())
    .then(json => screens.push(...json))
    .then(() => {
      document.querySelector('#screen-count').textContent = `${screens.length} Screens`
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
