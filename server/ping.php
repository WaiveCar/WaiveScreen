<?php
if(empty($_GET['uid'])) {
  echo "Not OK Computer!";
  exit(0);
}

$PORT_OFFSET = 7000;
date_default_timezone_set('UTC');
$db = new SQLite3("main.db", SQLITE3_OPEN_READWRITE);

$uid = $db->escapeString($_GET['uid']);

$row = $db->querySingle("select * from lookup where uid='$uid'", true);

if(!$row) {
  // we need to get the next available port number
  $nextport = intval($db->querySingle('select max(port) from lookup')) + 1;

  $db->query("insert into lookup(uid, port, first_seen, last_seen) values('$uid', $nextport, current_timestamp, current_timestamp)");
  echo $nextport + $PORT_OFFSET;
  exit(0);
}

$db->query('update lookup set last_seen=current_timestamp where id=' . $row['id']);
echo $row['port'] + $PORT_OFFSET;
exit(0);
