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
      jemit(campaigns_list($_GET));
    } elseif ($verb == 'POST') {
      $assetList = array_values($_FILES);
      jemit(campaign_create($_POST, $assetList));
    } elseif ($verb == 'PUT') {
      jemit(campaign_activate($_POST['campaignId'], $_POST));
    }
  }
  else if($func == 'screens') {
    if($verb == 'GET') {
      jemit(screens($all));
    } elseif ($verb == 'POST' || $verb == 'PUT') {
      jemit(screen_edit($all));
    }
  } 
  else if($func == 'sow') {
    jemit(sow($all));
  }
  else if(array_search($func, ['jobs', 'campaigns', 'screens']) !== false) {
    jemit(show(rtrim($func, 's')));
  }
  else if($func == 'tag') {
    jemit(tag($all));
  }
  else if($func == 'ping') {
    jemit(ping($all));
  }
  else if($func == 'setup') {
    jemit(setup($_POST));
  }
  else if($func == 'reset') {
    jemit(truncate());
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
