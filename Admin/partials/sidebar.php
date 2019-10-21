<ul class="navbar-nav bg-gradient-primary sidebar sidebar-dark accordion collapsed toggled" id="accordionSidebar">

  <a class="sidebar-brand d-flex align-items-center justify-content-center">
    <div class="sidebar-brand-text mx-3" style=color:white>waive</div>
  </a>
  <hr class="sidebar-divider d-none d-md-block">

  <li class="nav-item active">
    <a class="nav-link" href="screens">
    <span>screens</span></a>
  </li>
  <li class="nav-item active">
    <a class="nav-link" href="#" data-toggle="collapse" data-target="#campaignPages" aria-expanded="true" aria-controls="collapsePages">
      <span>campaigns</span></a>
    </a>
    <div id="campaignPages" class="collapse" aria-labelledby="headingPages" data-parent="#accordionSidebar">
      <div class="bg-white py-2 collapse-inner rounded">
        <? foreach(['pending','active','rejected','completed'] as $term) { ?>
        <a class="collapse-item" href="/campaigns?which=<?=$term?>"><?=ucfirst($term)?></a>
        <? } ?>
      </div>
    </div>
  </li>

  <li class="nav-item active">
    <a class="nav-link" href="commands">
    <span>commands</span></a>
  </li>

  <hr class="sidebar-divider d-none d-md-block">

  <div class="text-center d-none d-md-inline">
    <button class="rounded-circle border-0" id="sidebarToggle"></button>
  </div>

</ul>
