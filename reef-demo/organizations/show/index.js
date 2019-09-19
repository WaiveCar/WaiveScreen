function renderOrganization(organization) {
  const organizationTitle = document.getElementById('organization-title');
  organizationTitle.textContent = `Organization ${organization.id} Info`;
}

(() => {
  const id = new URL(location.href).searchParams.get('id');
  fetch(`http://waivescreen.com/api/organizations?id=${id}`)
    .then(response => response.json())
    .then(json => renderOrganization(json[0]))
    .catch(e => console.log('error fetching organizations', e));
})();
