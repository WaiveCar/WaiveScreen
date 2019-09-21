function toggleMenu() {
  document.querySelector('.navbar-nav').classList.toggle('menu-shown');
}

(() => {
  document.getElementById('menu').innerHTML = `
      <ul class="navbar-nav bg-gradient-white sidebar sidebar-light">
        ${['screens', 'campaigns', 'organizations', 'brands', 'users']
          .map(
            item => `
          <li class="ml-2 nav-item menu-item sidebar-link active" data-item="${item}">
            <a class="nav-link" href="/${item}/">
            <span>${item}</span></a>
          </li>
        `,
          )
          .join('')}
      </ul>
    `;
  let items = document.querySelectorAll('.navbar-nav li');
  items.forEach(one => {
    if (window.location.href.includes(one.dataset.item)) {
      one.classList.add('current-link');
      one.querySelector('span').classList.add('current-link-text');
    }
  });
})();
