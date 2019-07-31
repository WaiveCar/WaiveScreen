<?
include('../MadisonAve/lib/lib.php');
include('../AdDaemon/lib/const.php');
include('lib.php');

$screenList = get('screens');
$addrList = get_addressList(array_map(function($row) { 
  if($row['lat'] && $row['lng']) {
    return [$row['lat'],$row['lng']]; 
  } else  {
    return [];
  }
}, $screenList));

for($ix = 0; $ix < count($screenList); $ix++){
  if($addrList[$ix]) {
    $screenList[$ix]['addr'] = "<a target=_blank href=//maps.google.com/?q={$screenList[$ix]['lat']},{$screenList[$ix]['lng']}>{$addrList[$ix]}</a>";
  } else {
    $screenList[$ix]['addr'] = '<em>unknown</em>';
  }
  foreach(['first','last'] as $key) {
    $screenList[$ix]["{$key}_local"] = strtotime(str_replace(' ', 'T', $screenList[$ix]["{$key}_seen"] . 'Z'));
  }

  $sec =  time() - $screenList[$ix]['last_local'];
  $screenList[$ix]['last_sec'] = $sec;

  if($sec > 300) {
    $screenList[$ix]['uptime'] = 'off';
  } 

  $screenList[$ix]['last_local'] = sprintf("%dd %d:%02d:%02d", floor($sec / 60 / 60 / 24), floor($sec / 60 / 60) % 24, floor($sec/60) % 60, $sec %60);
  $screenList[$ix]['first_local'] = date("Y-m-d H:i:s", $screenList[$ix]['first_local']);

  if (isset( $screenList[$ix]['last_loc']) ) {
    $tmp = strtotime(str_replace(' ', 'T', $screenList[$ix]["last_loc"] . 'Z'));
    $sec =  time() - $tmp;
    $screenList[$ix]['diff_loc'] = sprintf("%dd %d:%02d:%02d", floor($sec / 60 / 60 / 24), floor($sec / 60 / 60) % 24, floor($sec/60) % 60, $sec %60);
    $screenList[$ix]['loc_sec'] = $sec;
  } else {
    $screenList[$ix]['loc_sec'] = 99999999999;
    $screenList[$ix]['diff_loc'] = '<em>never</em>';
  }
}

//$tagList = db_all("select name from tag");

$PROJECT_LIST = [
  '' => 'none',
  'LA' => 'LA', 
  'NY' => 'NY',
  'dev' => 'dev'
];
$MODEL_LIST = [
  '' => 'none',
  'ioniq_ev' => 'Ioniq EV', 
  'ioniq_hybrid' => 'Ioniq Hybrid', 
  'camry' => 'Camry'
];

$fieldList = [
  //'id'  => 'uid',
  'car' => 'car',
  'serial' => 'serial',
  'location' => 'addr',
  'updated' => 'diff_loc',
  'phone' => 'phone',
  'port' => 'port',
  'version' => 'version',
  'uptime' => 'uptime',
  'last' => 'last_local',
  'first' => 'first_local'
];
$editable = ['car', 'serial'];

$props = [
  'version' => [ 
    'order' => function($value, $row) {
      $base = substr($value, 3);
      $parts = explode('-', $base);
      return intval($parts[0]) * 10000 + intval($parts[2]);
    }
  ],
  'last' => [ 
    'order' => function($value, $row) {
      return $row['last_sec'];
    }
  ],
  'updated' => [ 
    'order' => function($value, $row) {
      return $row['loc_sec'];
    }
  ],
  'uptime' => [ 
    'order' => function($value, $row) {
      return $value === 'off' ? PHP_INT_MAX : $value;
    }
  ]
];

function split($str) {
  return $str;
}

?>
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link href="/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css?family=Nunito:200,200i,300,300i,400,400i,600,600i,700,700i,800,800i,900,900i" rel="stylesheet">
    <link href="/css/sb-admin-2.min.css" rel="stylesheet">
		<link rel=stylesheet href=https://stackpath.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css>
    <link href="/css/dataTables.bootstrap4.min.css" rel="stylesheet">
    <title>Screen Admin</title>
  </head>
  <style>
    #content-wrapper span { color: #000 }
    .id,.version { font-family: monospace }
    .edit { color: #999; cursor: pointer }
    .last { text-align: right }
    em { color: #555 }
    .table td {padding: .75rem .2rem; }
    td.edit { white-space: nowrap; }
    .modal-body span {
      min-width: 5rem; 
      display: inline-block;
      vertical-align: top;
    }
    .edit:hover { color: #000 }
    #notice { position: absolute; top:0; left:0; width: 100%; z-index: 100;display:none}
  </style>
  <body id="page-top">
  <div id="wrapper">
  <? include ('partials/sidebar.php'); ?>
  <div id="content-wrapper" class="d-flex flex-column">
    <? include ('partials/topbar.php'); ?>

    <h3>
    <div class="alert alert-primary" id="notice" role="alert"></div>
    </h3>

    <div class="table-responsive">
      <table class="table table-bordered" id="dataTable" width="100%" cellspacing="0">

        <thead>
          <tr>
          <th scope="col">id</th>
          <th scope="col">project</th>
          <th scope="col">model</th>
          <? foreach($fieldList as $key => $value) { ?>
            <th scope="col"><?= $key ?></th>
          <? } ?>
          <th scope="col">cmd</th>
          </tr>
        </thead>
        <tbody>
        <? foreach($screenList as $screen) { ?>
          <tr>
            <td>
              <a href="#<?=$screen['id']?>" onclick='edit("<?=$screen['id']?>")' class=id><?= split($screen['uid']) ?></a>
            </td>
            <td>
              <select onchange=change(<?=$screen['id']?>,'project',this)>
                <?foreach($PROJECT_LIST as $value => $project) { 
                  $selected = ($value === $screen['project']) ? 'selected' : '';
                 ?>
                  <option value="<?=$value?>" <?=$selected?>><?=$project?></option>
                <? } ?>
              </select>
            </td>
            <td>
              <select onchange=change(<?=$screen['id']?>,'model',this)>
                <?foreach($MODEL_LIST as $value => $project) { 
                  $selected = ($value === $screen['model']) ? 'selected' : '';
                ?>
                  <option value="<?=$value?>" <?=$selected?>><?=$project?></option>
                <? } ?>
              </select>
            </td>
            <? foreach($fieldList as $name => $key) { 
              
                 $dataVals = [];
                 if(array_key_exists($name, $props)) {
                   foreach($props[$name] as $propKey => $propValue) {
                     $dataVals[] = "data-$propKey='" . $propValue($screen[$key], $screen) . "'";
                   }
                 }
                 $dataVals = implode(' ', $dataVals);
                 $canedit = array_search($key, $editable) !== false ? 'edit' : '';
            ?>
              <td class="<?= $name?> <?=$canedit?>" <?=$dataVals?>>
                <span><?= $screen[$key] ?></span>
                <? if ($canedit) { ?>
                  <a onclick="promptchange(<?=$screen['id']?>,'<?=$key?>',this)"><i class="edit fa fa-pencil"></i></a>
                <? } ?>
              </td>
            <? } ?>
            <td>
              <button onclick='command("<?=$screen['id']?>","<?=$screen['car']?>")' class="btn btn-secondary">cmd</button>
            </td>
          </tr>
        <? } ?>
      </tbody>
    </table>
    <input size=4 id=field placeholder=field></input>
    <input id=value placeholder=value></input>
    <input id=command placeholder=command></input>
    <input id=args placeholder=args></input>
    <button onclick=scope_command()>do it</button>
   </div>

    <div class="modal fade" id="editModal" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true">
      <div class="modal-dialog" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="ModalLabel">screen naem</h5>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>

          <div class="modal-body">
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
            <!--<button type="button" class="btn btn-primary">Update</button>-->
          </div>
        </div>
      </div>
    </div>

  </div>
    <script>
    var Data=<?=json_encode($screenList);?>
    </script>
  <script
    src="https://code.jquery.com/jquery-3.4.1.min.js"
    integrity="sha256-CSXorXvZcTkaix6Yvo6HppcZGetbYMGWSFlBw8HfCJo="
    crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
    <script src="/js/jquery.easing.min.js"></script>
    <script src="/js/sb-admin-2.min.js"></script>
    <script src="/js/jquery.dataTables.min.js"></script>
    <script src="/js/dataTables.bootstrap4.min.js"></script>
    <script src="/Admin/script.js?1"></script>
  </body>
</html>
