<?
include('../MadisonAve/lib/lib.php');
include('lib.php');

$campaignList = get('campaigns');
$addrList = get_addressList(array_map(function($row) { 
  return [$row['lat'],$row['lng']]; 
}, $campaignList));

for($ix = 0; $ix < count($campaignList); $ix++){
  $campaignList[$ix]['addr'] = $addrList[$ix];
}

?>
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
    <link rel='stylesheet' href='/engine.css'>
    <title>Campaign admin</title>
    <style>
    .form-control-file { display: none }
    .asset-container { width: 500px; position: relative; height: 215px; }
    .upload-button { margin-bottom: 0 }
    #notice { position: fixed; top:0; left:0; width: 100%; z-index: 100;display:none}
    </style>
  </head>
  <body>
    <div class="alert alert-primary" id="notice" role="alert"></div>
    <div class='row'>
    <? foreach($campaignList as $campaign) { 
      $done = min($campaign['completed_seconds'] / $campaign['duration_seconds'], 1) * 100;
      ?>
      <div class="card" style="width: 500px">
        <div class='asset-container' id='asset-container-<?=$campaign['id']?>'/> </div>
        <!-- <img src="<?= $campaign['asset'][0] ?>" class="card-img-top"> -->
        <div class="card-body">
          <div class="progress">
            <div class="progress-bar" role="progressbar" style="width: <?= $done ?>%" aria-valuenow="<?= $done ?>" aria-valuemin="0" aria-valuemax="100"></div>
          </div>
          <p><?= $campaign['completed_seconds'] ?>/<?= $campaign['duration_seconds'] ?>s complete<br/>
          <a href="https://maps.google.com/?q=<?= $campaign['lat'] ?>,<?= $campaign['lng'] ?>"><?= $campaign['addr']; ?></a><br/>
          Radius: <?= $campaign['radius'] ?>m</p>

          Start: <?= $campaign['start_time'] ?><br>
          End: <?= $campaign['end_time'] ?>
  
          <p class="card-text"></p>
          <a href="#<?=$campaign['id']?>" class="btn btn-secondary">Disable</a>
          <form id='form-<?=$campaign['id']?>'>
            <label class="btn btn-info upload-button" for="image-upload-<?=$campaign['id']?>">
              Edit
            </label>
            <input id="image-upload-<?=$campaign['id']?>" data-campaign=<?=$campaign['id']?> multiple class="form-control-file" type="file" name="ad-asset" accept="image/*,video/*">
          </form>
        </div>
      </div>
    <? } ?>
    </div>
    <script>
    var Data=<?=json_encode($campaignList);?>
    </script>
    <script src="https://unpkg.com/axios/dist/axios.min.js"></script>
    <script src="/engine.js"></script>
    <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
    <script src="/Admin/script.js?1"></script>
  </body>
</html>
