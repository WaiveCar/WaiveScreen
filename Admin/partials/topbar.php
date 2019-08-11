<nav class="navbar navbar-expand navbar-light bg-white topbar mb-4 static-top shadow">

  <!-- Sidebar Toggle (Topbar) -->
  <button id="sidebarToggleTop" class="btn btn-link d-md-none rounded-circle mr-3">
    <i class="fa fa-bars"></i>
  </button>

  <?
    $color = [
      'ads.waivecar.com' => 'secondary',
      'staging.waivescreen.com' => 'warning',
      'waivecsreen.com' => 'danger'
    ][$_SERVER['HTTP_HOST']];
  ?>
  <div class="alert alert-<?=$color?>" role="alert"><?= $_SERVER['HTTP_HOST']; ?></div>
  <!-- Topbar Search 
  <form class="d-none d-sm-inline-block form-inline mr-auto ml-md-3 my-2 my-md-0 mw-100 navbar-search">
    <div class="input-group">
      <input type="text" class="form-control bg-light border-0 small" placeholder="Search for..." aria-label="Search" aria-describedby="basic-addon2">
      <div class="input-group-append">
        <button class="btn btn-primary" type="button">
          <i class="fas fa-search fa-sm"></i>
        </button>
      </div>
    </div>
  </form>-->


</nav>
