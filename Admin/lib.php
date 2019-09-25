<?


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

