<?
include('lib.php');
if(empty($_GET['uid'])) {
  echo "Not OK Computer!";
  exit(0);
}

$PORT_OFFSET = 7000;
$db = getDb();

$uid = $db->escapeString($_GET['uid']);

$row = $db->querySingle("select * from screen where uid='$uid'", true);

if(!$row) {
  return create_screen($uid);
}

$db->query('update screen set last_seen=current_timestamp where id=' . $row['id']);
echo $row['port'] + $PORT_OFFSET;
exit(0);
