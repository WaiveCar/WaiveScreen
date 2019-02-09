<?
include('lib.php');

$func = $_POST['func'];

if($func == 'campaign') {
  jemit(create_campaign($_POST));
}
if($func == 'sow') {
  jemit(sow($_POST));
}

jemit(doError("$func not found"));
