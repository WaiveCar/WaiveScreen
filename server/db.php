<?php
date_default_timezone_set('UTC');
$dbPath = "${_SERVER['DOCUMENT_ROOT']}/../db/main.db";
if(!file_exists($dbPath)) {
  touch($dbPath);
}
$db = new SQLite3($dbPath);
$db->exec('
create table if not exists screen(
  id integer primary key autoincrement, 
  uid text not null, 
  lat integer,
  lng integer,
  text default null, 
  port integer, 
  first_seen datetime, 
  last_seen datetime
);

create table if not exists campaign(
  id integer primary key autoincrement,
  asset text not null,
  duration_seconds integer,
  start_time datetime,
  end_time datetime
);

create table if not exists job(
  job_id integer primary key autoincrement,
  campaign_id integer,
  screen_id integer,
  start_time datetime,
  end_time datetime,
  duration_seconds integer,
  completion_seconds integer,
  last_update datetime
)');

function db_incrstats($what) {
  global $db;
  $me = me();
  $id = $me['id'];

  @$db->exec("insert into users(user_id) values($id)");
  $db->exec("update users set $what = $what + 1, last = current_timestamp where user_id = $id");
}

function db_get($key) {
  global $db;
  $key = $db->escapeString($key);
  return $db->querySingle("select name from location_cache where latlng='$key'");
}

function db_set($key, $val) {
  global $db;
  $key = $db->escapeString($key);
  $val = $db->escapeString($val);

  $db->exec("insert into location_cache(latlng, name, created) values('$key', '$val', date('now'))");
}
