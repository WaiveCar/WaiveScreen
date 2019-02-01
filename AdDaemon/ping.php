<?php
include('db.php');
if(empty($_GET['uid'])) {
  echo "Not OK Computer!";
  exit(0);
}

$PORT_OFFSET = 7000;
$db = getDb();

$uid = $db->escapeString($_GET['uid']);

$row = $db->querySingle("select * from screen where uid='$uid'", true);

if(!$row) {
  // we need to get the next available port number
  $nextport = intval($db->querySingle('select max(port) from screen')) + 1;

  $bb = $db->query("insert into screen(uid, port, first_seen, last_seen) values('$uid', $nextport, current_timestamp, current_timestamp)");
  var_dump($bb);
  echo $nextport + $PORT_OFFSET;
  exit(0);
}

$db->query('update screen set last_seen=current_timestamp where id=' . $row['id']);
echo $row['port'] + $PORT_OFFSET;
exit(0);
