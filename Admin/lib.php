<?

function curldo($url, $params = false, $verb = false, $opts = []) {
  if($verb === false) {
    $verb = 'GET';
    // this is a problem
  }
  $verb = strtoupper($verb);

  $ch = curl_init();

  $header = [];
  if(isset($_SESSION['token']) && strlen($_SESSION['token']) > 2) {
    $header[] = "Authorization: ${_SESSION['token']}";
  }
    
  if($verb !== 'GET') {
    if(!isset($opts['isFile'])) {
      if(!$params) {
        $params = [];
      }
      $params = json_encode($params);
      $header[] = 'Content-Type: application/json';
    } else {
      $header[] = 'Content-Type: multipart/form-data';
    }
    curl_setopt($ch, CURLOPT_POSTFIELDS, $params);  
    // $header[] = 'Content-Length: ' . strlen($data_string);
  }

  if($verb === 'POST') {
    curl_setopt($ch, CURLOPT_POST,1);
  }

  curl_setopt($ch, CURLOPT_HTTPHEADER, $header);
  curl_setopt($ch, CURLOPT_URL, $url);
  curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $verb);  
  curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
  curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

  $res = curl_exec($ch);
  
  /*
  $tolog = json_encode([
      'verb' => $verb,
      'header' => $header,
      'url' => $url,
      'params' => $params,
      'res' => $res
  ]);
  var_dump(['>>>', curl_getinfo ($ch), json_decode($tolog, true)]);
  

  file_put_contents('/tmp/log.txt', $tolog, FILE_APPEND);
   */

  if(isset($opts['raw'])) {
    return $res;
  }
  $resJSON = @json_decode($res, true);
  if($resJSON) {
    return $resJSON;
  }
  return $res;
}

function get($ep, $kv=false) {
  if($kv) {
    $kv = '?' . http_build_query($kv);
  } else {
    $kv = '';
  }
  return json_decode(file_get_contents("http://{$_SERVER['HTTP_HOST']}/api/$ep$kv"), true);
}
function get_addressList($list) {
  $url="http://basic.waivecar.com/location.php?multi=" . urlencode(json_encode($list));
  return curldo($url);
}

function get_address($obj) {
  $url="http://basic.waivecar.com/location.php?latitude=${obj['lat']}&longitude=${obj['lng']}";
  return curldo($url, ['raw' => true]);
}

