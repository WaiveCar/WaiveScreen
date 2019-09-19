function renderUser(user) {
  const userTitle = document.getElementById('user-title');
  userTitle.textContent = `Organization ${user.id} Info`;
}

(() => {
  const id = new URL(location.href).searchParams.get('id');
  fetch(`http://waivescreen.com/api/users?id=${id}`)
    .then(response => response.json())
    .then(json => renderUser(json[0]))
    .catch(e => console.log('error fetching user', e));
})();
