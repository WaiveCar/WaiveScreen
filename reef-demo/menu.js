(() => {
  document.getElementById('menu').innerHTML = `
      <ul class="navbar-nav bg-gradient-white sidebar sidebar-light accordion" id="accordionSidebar">
        <a class="d-flex align-items-center justify-content-center">
          <div class="sidebar-brand-text mx-3" style=color:black>adcast</div>
        </a>
        <hr class="sidebar-divider d-none d-md-block">
        ${['screens', 'campaigns', 'organizations', 'brands', 'users']
          .map(
            item => `
          <li class="ml-2 nav-item menu-item sidebar-link active" data-item="${item}">
            <a class="nav-link" href="/${item}/index.html">
            <span>${item}</span></a>
          </li>
        `,
          )
          .join('')}
        <hr class="sidebar-divider d-none d-md-block">
      </ul>
    `;
  let items = document.querySelectorAll('.navbar-nav li');
  items.forEach(one => {
    if (window.location.href.includes(one.dataset.item)) {
      one.querySelector('span').classList.add('current-link');
    }
  });
})();
