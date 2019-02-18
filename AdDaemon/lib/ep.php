<?
include('lib.php');

$func = $_REQUEST['func'];

if($func == 'campaign') {
  jemit(create_campaign($_POST));
}
if($func == 'sow') {
  jemit(sow($_POST));
}
if($func == 'setup') {
  jemit(setup($_POST));
}
jemit(doError("$func not found"));
