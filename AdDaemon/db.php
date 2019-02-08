<?php
date_default_timezone_set('UTC');

$_db = false;
function getDb() {
  global $_db;
  if(!$_db) {
    $dbPath = "${_SERVER['DOCUMENT_ROOT']}/../db/main.db";
    if(!file_exists($dbPath)) {
      touch($dbPath);
    }
    $_db = new SQLite3($dbPath);
  }
  return $_db;
}

function setup() {
  $db = getDb();
  $schema = [
    'create table if not exists screen(
      id integer primary key autoincrement, 
      uid text not null, 
      location point default null,
      text default null, 
      port integer, 
      first_seen datetime, 
      last_seen datetime
    )',

    'create table if not exists campaign(
      id integer primary key autoincrement,
      asset text not null,
      duration_seconds integer,
      center point default null,
      radius float default null,
      start_time datetime,
      end_time datetime
    )',

    'create table if not exists job(
      job_id integer primary key autoincrement,
      campaign_id integer,
      screen_id integer,
      job_start datetime,
      job_end datetime,
      goal_seconds integer,
      completion_seconds integer,
      last_update datetime
    )'
  ];
  foreach($schema as $table) {
    $res = $db->exec($table);
  }
}

function db_incrstats($what) {
  $db = getDb();
  $me = me();
  $id = $me['id'];

  @$db->exec("insert into users(user_id) values($id)");
  $db->exec("update users set $what = $what + 1, last = current_timestamp where user_id = $id");
}

function db_get($key) {
  $db = getDb();
  $key = $db->escapeString($key);
  return $db->querySingle("select name from location_cache where latlng='$key'");
}

function db_set($key, $val) {
  $db = getDb();
  $key = $db->escapeString($key);
  $val = $db->escapeString($val);

  $db->exec("insert into location_cache(latlng, name, created) values('$key', '$val', date('now'))");
}
