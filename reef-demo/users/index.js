function renderUsers(users) {
  document.getElementById('users-table-body').innerHTML = users
    .map(
      user =>
        `
        <tr>
          <th><a href="show/index.html?id=${user.id}">${user.id}</a></th>
          <th>${user.project}</th>
          <th>${user.lat}, ${user.lng}</th>
          <th>${user.phone}</th>
        </tr>
      `,
    )
    .join('');
}
(() => {
  const users = [];
  fetch('http://waivescreen.com/api/users')
    .then(response => response.json())
    .then(json => users.push(...json))
    .then(() => {
      renderUsers(users);
    })
    .catch(e => console.log('error fetching users', e));
})();
