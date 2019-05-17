<?
include('../lib/lib.php');

function get($ep) {
  return json_decode(file_get_contents("http://waivescreen.com/api/$ep"), true);
}
function get_addressList($list) {
  $url="http://basic.waivecar.com/location.php?multi=" . urlencode(json_encode($list));
  return curldo($url);
}

function get_address($obj) {
  $url="http://basic.waivecar.com/location.php?latitude=${obj['lat']}&longitude=${obj['lng']}";
  return curldo($url, ['raw' => true]);
}

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
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

    <!-- Bootstrap CSS -->
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">

    <title>Admin panel</title>
  </head>
  <body>
   <h2> Campaigns</h2>
    <div class='row'>
    <? foreach($campaignList as $campaign) { 
      $done = min($campaign['completed_seconds'] / $campaign['duration_seconds'], 1) * 100;
?>
      <div class="card" style="width: 18rem;">
        <img src="http://waivecar-prod.s3.amazonaws.com/<?= $campaign['asset'] ?>" class="card-img-top">
        <div class="card-body">
          <div class="progress">
            <div class="progress-bar" role="progressbar" style="width: <?= $done ?>%" aria-valuenow="<?= $done ?>" aria-valuemin="0" aria-valuemax="100"></div>
          </div>
          <p><?= $campaign['completed_seconds'] ?>/<?= $campaign['duration_seconds'] ?>s complete<br/>
          <a href="https://maps.google.com/?q=<?= $campaign['lat'] ?>,<?= $campaign['lng'] ?>"><?= $campaign['addr']; ?></a><br/>
          Radius: <?= $campaign['radius'] ?>m</p>


  
          <h5 class="card-title">Card title</h5>
          <p class="card-text">Some quick example text to build on the card title and make up the bulk of the card's content.</p>
          <a href="#" class="btn btn-primary">Go somewhere</a>
        </div>
      </div>
    <? } ?>
    </div>
    Users
    <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
  </body>
</html>
