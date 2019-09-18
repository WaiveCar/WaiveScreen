<?
include('../AdDaemon/lib/lib.php');
include('lib.php');

$campaignList = get('campaigns');
$addrList = get_addressList(array_map(function($row) { 
  return [$row['lat'],$row['lng']]; 
}, $campaignList));

for($ix = 0; $ix < count($campaignList); $ix++){
  $campaignList[$ix]['addr'] = $addrList[$ix];
}

$screenList = get('screens', ['removed' => 0, 'active' => 1]);
$width = 450;
$height = $width * 675 / 1920;
?>
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link href="/css/all.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://openlayers.org/en/v5.3.0/css/ol.css" type="text/css">
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
    <link rel='stylesheet' href='/engine.css'>
    <link href="/css/sb-admin-2.min.css" rel="stylesheet">
    <title>Campaign admin</title>
    <style>
    form { float: right }
    #content-wrapper h4 { color: #000 }
    .form-control-file { display: none }
    .asset-container { width: <?= $width; ?>px; position: relative; height: <?= $height; ?>px; }
    .upload-button { margin-bottom: 0 }
    #notice { position: fixed; top:0; left:0; width: 100%; z-index: 100;display:none}
    .dropdown-menu > a.dark { color: #000;cursor: default }
    </style>
  </head>
  <body id="page-top">
    <div id="wrapper">
      <? include ('partials/sidebar.php'); ?>
      <div id="content-wrapper" class="d-flex flex-column">
        <div id="content">

        <? include ('partials/topbar.php'); ?>
        <div class="container-fluid">
          <div class="alert alert-primary" id="notice" role="alert"></div>
            <div class="d-sm-flex align-items-center justify-content-between mb-4">
            <h1 class="h3 mb-0 text-gray-800">Campaigns</h1>
            <a onclick="create_campaign()" href="#" class="d-none d-sm-inline-block btn btn-sm btn-primary shadow-sm"><i class="fas fa-plus fa-sm text-white-50"></i> New</a>
          </div>
          <div class='row'>
          <? foreach($campaignList as $campaign) { 
            if( $campaign['duration_seconds'] ) {
              $done = min($campaign['completed_seconds'] / $campaign['duration_seconds'], 1) * 100;
            } else {
              $done = 0;
            }
            $isDefault = $campaign['is_default'];
            ?>
              <div class="card" style="width: <?=$width?>px">
              <div title=<?=$campaign['id']?> class='asset-container' id='asset-container-<?=$campaign['id']?>'/> </div>
              <div class="card-body">
                <? if (!$isDefault) { ?>
                  <div class="progress">
                    <div class="progress-bar" role="progressbar" style="width: <?= $done ?>%" aria-valuenow="<?= $done ?>" aria-valuemin="0" aria-valuemax="100"></div>
                  </div>
                  <p><?= $campaign['completed_seconds'] ?>/<a href=# onclick="change_time(<?=$campaign['id']?>,<?= $campaign['duration_seconds'] ?>)"><?= $campaign['duration_seconds'] ?></a><br/>
                  Start: <?= $campaign['start_time'] ?><br>
                  End: <?= $campaign['end_time'] ?>
                <? } else { ?>
                  <h4>Default advertisement
                  </h4>
                <? } ?>

                <p class="card-text"></p>

                <div class="btn-group" role="group" aria-label="Actions">
                  <div class="dropdown">
                    <button class="btn btn-secondary dropdown-toggle" type="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                      Actions
                    </button>
                    <div class="dropdown-menu" aria-labelledby="dropdownMenuButton">
                      <a onclick="geofence(<?=$campaign['id']?>)" class="dropdown-item dark">Geofence</a>
                    <? if ($campaign['active']) {?>
                      <a onclick="update_campaign({id:<?=$campaign['id']?>,active:false})" class="dropdown-item dark">Disable</a>
                    <? } else { ?>
                      <a onclick="update_campaign({id:<?=$campaign['id']?>,active:true})" class="dropdown-item dark">Enable</a>
                    <? } ?>
                      <div class="dropdown-divider"></div>
                      <label class="dropdown-item upload-button" for="image-upload-<?=$campaign['id']?>">Replace</label>
                      <label onclick="append()" class="dropdown-item upload-button" for="image-upload-<?=$campaign['id']?>">Append</label>
                      <div class="dropdown-divider"></div>
                      <a class="dropdown-item" href="#">Make Default</a>
                    </div>
                  </div>
                  <? 
                    if ($campaign['active']) {
                      $word = 'active';
                      $style = 'info'; 
                    } else {
                      $word = 'inactive';
                      $style = 'light';
                    }
                  ?>
                  <h3><span class="badge badge-<?=$style?>" style=margin-left:1rem><?= $word ?></span>
                  <? 
                    $matched = false;
                    foreach( $DEFAULT_CAMPAIGN_MAP as $key => $value) { 
                      if ($value == $campaign['id']) { 
                        echo "<span class='badge badge-pill badge-dark'>$key</span> ";
                        $matched = true;
                      }
                    } 
                    if(!$matched) {
                      echo "<span class='badge badge-pill badge-dark'>${campaign['project']}</span>";
                    }
                  ?>
                  </h3>
                </div>

                <form id='form-<?=$campaign['id']?>'>
                  <input id="image-upload-<?=$campaign['id']?>" data-campaign=<?=$campaign['id']?> multiple class="form-control-file" type="file" name="ad-asset" accept="image/*,video/*">
                </form>
              </div>
            </div>
          <? } ?>
          </div>
        </div>
      </div>
    </div>
    <div class="modal fade" id="editModal" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="ModalLabel">Edit Geofence</h5>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>

          <div class="modal-body">
            <select id="type" class="custom-select custom-select-lg">
              <option value="Circle">Circle</option>
              <option value="Polygon">Geofence</option>
            </select>
            <div style='width:100%;height:40vw' id='map'></div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-danger btn-sm mr-auto" data-dismiss="modal">Cancel</button>
            <button type="button" class="btn btn-outline-secondary btn-sm mr-auto" onclick=clearmap()>Clear</button>
            <button type="button" class="btn btn-outline-secondary btn-sm mr-auto" onclick=removeShape()>Remove Most Recent Shape</button>
            <button type="button" class="btn btn-secondary" onclick=geosave()>Update</button>
          </div>
        </div>
      </div>
    </div>
    <script>
      var Data=<?=json_encode($campaignList);?>,width=<?=$width?>,height=<?=$height?>;
      var Screens=<?=json_encode($screenList);?>;
    </script>
    <script src="https://unpkg.com/axios/dist/axios.min.js"></script>
    <script src="/engine.js"></script>
    <script src="/Admin/dist/map.js?1"></script>
    <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
    <script src="/js/sb-admin-2.min.js"></script>
    <script src="/Admin/script.js?1"></script>
    <script src="/Admin/campaigns.js?2"></script>
  </body>
</html>
