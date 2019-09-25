function toggleMenu() {
  document.querySelector('.navbar-nav').classList.toggle('menu-shown');
}

(() => {
  let menu=`
      <ul class="navbar-nav bg-gradient-white sidebar sidebar-light">
        ${[
            ['approval', 'admin'], 
            ['screens', 'admin'], 
            ['campaigns', 'viewer'], 
            ['organizations', 'admin'],
            ['brands', 'viewer'],
            ['users', 'manager']
          ].map(
            item => `
          <li class="ml-2 nav-item menu-item sidebar-link active p-${item[1]}" data-item="${item[0]}">
            <a class="nav-link" href="/${item[0]}/">
            <span>${item[0]}</span></a>
          </li>
        `,
          )
          .join('')}
      </ul>
    `;
  var profile = '<div class="row mb-2"> <div class="offset-md-1 col">Sign In</div></div>';
  document.getElementById('menu').innerHTML = profile + menu;
  let items = document.querySelectorAll('.navbar-nav li');
  items.forEach(one => {
    if (window.location.href.includes(one.dataset.item)) {
      one.classList.add('current-link');
      one.querySelector('span').classList.add('current-link-text');
    }
  });
})();
