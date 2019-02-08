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
      lat float default null,
      lng float default null,
      text default null, 
      port integer, 
      first_seen datetime, 
      last_seen datetime
    )',

    'create table if not exists campaign(
      id integer primary key autoincrement,
      asset text not null,
      duration integer,
      lat float default null,
      lng float default null,
      radius float default null,
      start_time datetime,
      end_time datetime
    )',

    'create table if not exists job(
      id integer primary key autoincrement,
      campaign_id integer,
      screen_id integer,
      goal_seconds integer,
      completion_seconds integer default 0,
      job_start datetime,
      job_end datetime
    )'
  ];
  foreach($schema as $table) {
    $res = $db->exec($table);
  }
}

function get_campaign_remaining($id) {
  return (getDb())->querySingle("
    select 
      sum(completion_seconds) - duration_seconds        as remaining
      from campaign join job on campaign_id = campaign.id
      where campaign.id = $id 
    ");
}

function get_campaign_completion($id) {
  return (getDb())->querySingle("
    select 
      sum(completion_seconds) / duration_seconds        as shown, 
      end_time - date('now') / (end_time - start_time)  as lapsed
      from campaign join job on campaign_id = campaign.id
      where campaign.id = $id 
    ");
}

function get_job($id) {
  return (getDb())->querySingle("select * from job where id=$id");
}

function get_campaign($id) {
  return (getDb())->querySingle("select * from campaign where id=$id");
}

function db_update($table, $id, $kv) {
  $fields = [];

  $db = getDb();

  foreach($kv as $k => $v) {
    $fields[] = "$k=".$db->escapeString($v);
  } 

  $fields = implode(',', $fields);

  return $db->exec("update $table set $fields where id = $id");
}

function db_insert($table, $kv) {
  $fields = [];
  $values = [];

  $db = getDb();

  foreach($kv as $k => $v) {
    $fields[] = $k;
    $values[] = $db->escapeString($v);
  } 

  $values = implode(',', $values);
  $fields = implode(',', $fields);

  if($db->exec("insert into $table($fields) values($values)")) {
    return $db->lastInsertRowID();
  }
}

/*
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
 */
