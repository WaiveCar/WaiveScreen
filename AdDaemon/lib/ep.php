<?
session_start();
include('lib.php');

$func = $_REQUEST['_VxiXw3BaQ4WAQClBoAsNTg_func'];
unset($_REQUEST['_VxiXw3BaQ4WAQClBoAsNTg_func']);
$verb = $_SERVER['REQUEST_METHOD'];
$input_raw = file_get_contents('php://input');
$json_payload = @json_decode($input_raw, true);

$all = $_REQUEST;
if($json_payload) {
  $all = array_merge($all, $json_payload);
} 

try {
  if($func == 'state') {
    $list = array_values($_FILES);
    move_uploaded_file(aget($list, '0.tmp_name'), "/var/states/" . aget($list, '0.name'));
    jemit(doSuccess('uploaded'));
  } else if($func == 'campaign') {
    if($verb == 'GET') {
      jemit(campaigns_list($_GET));
    } elseif ($verb == 'POST') {
      $assetList = array_values($_FILES);
      jemit(campaign_create($_POST, $assetList));
    } elseif ($verb == 'PUT') {
      jemit(campaign_activate($_POST['campaignId'], $_POST));
    }
  }
  else if($func == 'campaign_update') {
    $assetList = array_values($_FILES);
    jemit(campaign_update($all, $assetList));
  }
  else if($func == 'screens' && ($verb == 'POST' || $verb == 'PUT')) {
    jemit(screen_edit($all));
  } 
  else if(array_search($func, ['jobs', 'sensor_history', 'campaigns', 'screens', 'tasks']) !== false) {
    jemit(show(rtrim($func, 's'), $all));
  }
  else if(array_search($func, ['active_campaigns', 'campaign_history', 'sow', 'task_dump', 'screen_tag', 'tag', 'ping', 'command', 'response']) !== false) { 
    jemit($func($all, $verb));
  } else {
    jemit([
      'res' => false,
      'data' => "$func not found"
    ]);
  }
} catch(Exception $ex) {
  jemit([
    'res' => false,
    'data' => $ex
  ]);
}

jemit(doError("$func not found"));
