function renderOrganizations(organizations) {
  document.getElementById('org-table-body').innerHTML = organizations
    .map(
      org =>
        `
        <tr>
          <th><a href="show/index.html?id=${org.id}">${org.id}</a></th>
          <th>${org.project}</th>
          <th>${org.lat}, ${org.lng}</th>
          <th>${org.phone}</th>
        </tr>
      `,
    )
    .join('');
}
(() => {
  const organizations = [];
  fetch('http://waivescreen.com/api/organizations')
    .then(response => response.json())
    .then(json => organizations.push(...json))
    .then(() => {
      renderOrganizations(organizations);
    })
    .catch(e => console.log('error fetching organizations', e));
})();
