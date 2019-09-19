function toggleMenu() {
  document.querySelector('.navbar-nav').classList.toggle('menu-shown');
}

(() => {
  document.getElementById('menu').innerHTML = `
      <div class="menu-btn ml-3 mt-1">
        <i class="fas fa-bars" onclick="toggleMenu()"></i>
      </div>
      <ul class="navbar-nav bg-gradient-white sidebar sidebar-light">
        <a class="d-flex align-items-center justify-content-center">
          <div class="sidebar-brand-text mx-3" style=color:black>adcast</div>
        </a>
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
