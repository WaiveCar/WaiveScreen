function toggleMenu() {
  document.querySelector('.navbar-nav').classList.toggle('menu-shown');
}

(() => {
  let menu=`
      <ul class="navbar-nav bg-gradient-white sidebar sidebar-light p-manager">
        ${[
            ['approval', 'admin'], 
            ['screens', 'admin'], 
            ['campaigns', 'viewer'], 
            ['organizations', 'admin'],
            ['brands', 'viewer'],
            ['users', 'manager'],
            ['widgets', 'admin']
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
  var profile =  `
    <div class="row mb-2 user-area offset-md-1"> 
      <div class="signin"><a href=/signin/>Signin / Signup</a></div>
      <div class="signed-in"><img><span></span></div>
    </div>`;
  document.getElementById('menu').innerHTML = profile + menu;
  let items = document.querySelectorAll('.navbar-nav li');
  items.forEach(one => {
    if (window.location.href.includes(one.dataset.item)) {
      one.classList.add('current-link');
      one.querySelector('span').classList.add('current-link-text');
    }
  });
  function when(lib) {
    var _cb, _ival = setInterval(function(){
      if(self[lib]) {
        _cb();
        clearInterval(_ival);
      }
    }, 20);
    return {
      run: function(cb) { _cb = cb; }
    }
  }
  when('_me').run(() => {
    if(_me && _me.id) {
      $('.signed-in').html(_me.name).show();
    } else {
      $('.signin').show();
    }
  });
})();
