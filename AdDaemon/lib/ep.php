<?
session_start();
include('lib.php');

$func = $_REQUEST['func'];
$verb = $_SERVER['REQUEST_METHOD'];
$input_raw = file_get_contents('php://input');
$json_payload = @json_decode($input_raw, true);

$all = $_REQUEST;
if($json_payload) {
  $all = array_merge($all, $json_payload);
} 

try {
  if($func == 'campaign') {
    if($verb == 'GET') {
      jemit(campaigns());
    } elseif ($verb == 'POST') {
      $assetList = array_values($_FILES);
      jemit(campaign_create($_POST, $assetList[0]));
    } elseif ($verb == 'PUT') {
      jemit(campaign_activate($_POST['campaignId'], $_POST));
    }
  }
  else if($func == 'sow') {
    jemit(sow($all));
  }
  else if($func == 'ping') {
    jemit(ping($all));
  }
  else if($func == 'setup') {
    jemit(setup($_POST));
  }
  else if($func == 'reset') {
    jemit(truncate());
  }
} catch(Exception $ex) {
  jemit([
    'res' => false,
    'data' => $ex
  ]);
}

jemit(doError("$func not found"));
