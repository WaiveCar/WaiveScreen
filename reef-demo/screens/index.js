function renderScreens(screens, locations) {
  const screenTableBody = document.getElementById('screen-table-body');
  screenTableBody.innerHTML = screens
    .map(
      screen =>
        `
        <tr>
          <th><a href="show?id=${screen.id}">${screen.id}</a></th>
          <th>${screen.project}</th>
          <th>${screen.lat}, ${screen.lng}</th>
          <th>${screen.phone}</th>
        </tr>
      `,
    )
    .join('');
}
(() => {
  const screens = [];
  const locations = [];
  fetch('http://waivescreen.com/api/screens')
    .then(response => response.json())
    .then(json => screens.push(...json))
    .then(() => {
      renderScreens(screens);
      // The fetching of locations currently doesn't work due to cors issues. Return to this later if time
      /*
      return fetch(
        `https://basic.waivecar.com/location.php?multi=[${screens.map(
          screen => `[${[screen.lat, screen.lng]}]`,
        )}]`,
      );*/
    })
    /*
    .then(streets => {
      return streets.json();
    })
    .then(json => {
      locations.push(...json);
      renderScreens(screens, locations);
    })
    */
    .catch(e => console.log('error fetching screens', e));
})();
