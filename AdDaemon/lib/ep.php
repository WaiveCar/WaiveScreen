<?
include('lib.php');

$func = $_REQUEST['func'];
$verb = $_SERVER['REQUEST_METHOD'];

if($func == 'campaign') {
  if($verb == 'GET') {
    jemit(campaigns());
  } else {
    jemit(create_campaign($_POST));
  }
}
if($func == 'sow') {
  jemit(sow($_POST));
}
if($func == 'setup') {
  jemit(setup($_POST));
}
if($func == 'reset') {
  jemit(truncate());
}
jemit(doError("$func not found"));
