<ul class="navbar-nav bg-gradient-primary sidebar sidebar-dark accordion collapsed toggled" id="accordionSidebar">

  <a class="sidebar-brand d-flex align-items-center justify-content-center">
    <div class="sidebar-brand-text mx-3">waive</div>
  </a>
  <hr class="sidebar-divider d-none d-md-block">

  <? foreach(['screens','campaigns','commands'] as $cmd) { ?>
  <li class="nav-item active">
    <a class="nav-link" href="<?= $cmd ?>">
    <span><?= $cmd ?></span></a>
  </li>
  <? } ?>

  <hr class="sidebar-divider d-none d-md-block">

  <div class="text-center d-none d-md-inline">
    <button class="rounded-circle border-0" id="sidebarToggle"></button>
  </div>

</ul>
