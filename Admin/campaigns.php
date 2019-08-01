<?
include('../MadisonAve/lib/lib.php');
include('../AdDaemon/lib/lib.php');
include('lib.php');

$campaignList = get('campaigns');
$addrList = get_addressList(array_map(function($row) { 
  return [$row['lat'],$row['lng']]; 
}, $campaignList));

for($ix = 0; $ix < count($campaignList); $ix++){
  $campaignList[$ix]['addr'] = $addrList[$ix];
}

$width = 450;
$height = $width * 675 / 1920;
?>
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link href="/css/all.min.css" rel="stylesheet">
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
    </style>
  </head>
  <body id="page-top">
    <div id="wrapper">
      <? include ('partials/sidebar.php'); ?>
      <div id="content-wrapper" class="d-flex flex-column">
        <? include ('partials/topbar.php'); ?>
          <div class="alert alert-primary" id="notice" role="alert"></div>
          <div class='row'>
          <? foreach($campaignList as $campaign) { 
            $done = min($campaign['completed_seconds'] / $campaign['duration_seconds'], 1) * 100;
            $isDefault = $campaign['is_default'];
            ?>
              <div class="card" style="width: <?=$width?>px">
              <div class='asset-container' id='asset-container-<?=$campaign['id']?>'/> </div>
              <div class="card-body">
                <? if (!$isDefault) { ?>
                  <div class="progress">
                    <div class="progress-bar" role="progressbar" style="width: <?= $done ?>%" aria-valuenow="<?= $done ?>" aria-valuemin="0" aria-valuemax="100"></div>
                  </div>
                  <p><?= $campaign['completed_seconds'] ?>/<?= $campaign['duration_seconds'] ?>s complete<br/>
                  <a href="https://maps.google.com/?q=<?= $campaign['lat'] ?>,<?= $campaign['lng'] ?>"><?= $campaign['addr']; ?></a><br/>
                  Radius: <?= $campaign['radius'] ?>m</p>
                  Start: <?= $campaign['start_time'] ?><br>
                  End: <?= $campaign['end_time'] ?>
                <? } else { ?>
                  <h4>Default advertisement
                  <? foreach( $DEFAULT_CAMPAIGN_MAP as $key => $value) { 
                    if ($value == $campaign['id']) { 
                      echo "<span class='badge badge-pill badge-dark'>$key</span> ";
                    }
                  } ?>
                  </h4>
                <? } ?>

                <p class="card-text"></p>

                <div class="btn-group" role="group" aria-label="Basic example">
                  <div class="dropdown">
                    <button class="btn btn-secondary dropdown-toggle" type="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                      Actions
                    </button>
                    <div class="dropdown-menu" aria-labelledby="dropdownMenuButton">
<?                   if ($campaign['active']) {?>
                      <a onclick="update_campaign({id:<?=$campaign['id']?>,active:false})" class="dropdown-item">Disable</a>
<?} else { ?>
                      <a onclick="update_campaign({id:<?=$campaign['id']?>,active:true})" class="dropdown-item">Enable</a>
<? } ?>
                      <label class="dropdown-item upload-button" for="image-upload-<?=$campaign['id']?>">Replace</label>
                      <label onclick="append()" class="dropdown-item upload-button" for="image-upload-<?=$campaign['id']?>">Append</label>
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

                  <h3><span class="badge badge-<?=$style?>" style=margin-left:1rem><?= $word ?></span></h3>
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
    <script>
      var Data=<?=json_encode($campaignList);?>,width=<?=$width?>,height=<?=$height?>;
    </script>
    <script src="https://unpkg.com/axios/dist/axios.min.js"></script>
    <script src="/engine.js"></script>
    <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
    <script src="/js/sb-admin-2.min.js"></script>
    <script src="/Admin/script.js?1"></script>
  </body>
</html>
