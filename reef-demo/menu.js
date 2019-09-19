(() => {
  document.getElementById('menu')
    .innerHTML = `
      <ul class="navbar-nav bg-gradient-primary sidebar sidebar-dark accordion collapsed toggled" id="accordionSidebar">
        <a class="sidebar-brand d-flex align-items-center justify-content-center">
          <div class="sidebar-brand-text mx-3" style=color:white>waive</div>
        </a>
        <hr class="sidebar-divider d-none d-md-block">
        <li class="nav-item active">
          <a class="nav-link" href="/screens/index.html">
          <span>Screens</span></a>
        </li>
        <li class="nav-item active">
          <a class="nav-link" href="/campaigns/index.html">
          <span>Campaigns</span></a>
        </li>
        <li class="nav-item active">
          <a class="nav-link" href="/organizations/index.html">
          <span>Organizations</span></a>
        </li>
        <li class="nav-item active">
          <a class="nav-link" href="/brands/index.html">
          <span>Brands</span></a>
        </li>
        <li class="nav-item active">
          <a class="nav-link" href="/users/index.html">
          <span>Users</span></a>
        </li>
        <hr class="sidebar-divider d-none d-md-block">
        <div class="text-center d-none d-md-inline">
          <button class="rounded-circle border-0" id="sidebarToggle"></button>
        </div>
      </ul>
    `
})();
