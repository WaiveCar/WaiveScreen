<?php
date_default_timezone_set('UTC');

$SCHEMA = [
  'user' => 'create table if not exists user(
    id integer primary key autoincrement, 
    email text not null,
    stripe_id text not null,
    created_at datetime, 
    last_seen datetime
  )',

  'charge' => 'create table if not exists charge(
    id integer primary key autoincrement, 
    user_id integer,
    campaign_id integer,
    amount integer, 
    charge_id text,
    created_at datetime, 
  )',

  'subscription' => 'create table if not exists subscription(
    id integer primary key autoincrement, 
    user_id integer,
    campaign_id integer,
    amount integer, 
    created_at datetime, 
  )',

  'screen' => 'create table if not exists screen(
    id integer primary key autoincrement, 
    uid text not null, 
    lat float default null,
    lng float default null,
    text default null, 
    port integer, 
    first_seen datetime, 
    last_seen datetime
  )',

  'campaign' => 'create table if not exists campaign(
    id integer primary key autoincrement,
    asset text not null,
    duration_seconds integer,
    lat float default null,
    lng float default null,
    radius float default null,
    start_time datetime,
    end_time datetime
  )',

  'job' => 'create table if not exists job(
    id integer primary key autoincrement,
    campaign_id integer,
    screen_id integer,
    goal integer,
    completion_seconds integer default 0,
    last_update datetime,
    job_start datetime,
    job_end datetime
  )'
];
$_db = false;
function getDb() {
  global $_db;
  if(!$_db) {
    $dbPath = "${_SERVER['DOCUMENT_ROOT']}/db/main.db";
    if(!file_exists($dbPath)) {
      touch($dbPath);
    }
    $_db = new SQLite3($dbPath);
  }
  return $_db;
}

function db_string($what) {
  return "'$what'";
}

function setup() {
  $db = getDb();
  global $SCHEMA;
  $res = [];
  foreach(array_values($SCHEMA) as $table) {
    $res[] = [$db->exec($table), $table];
  }
  return $res;
}

function truncate() {
  $dbPath = "${_SERVER['DOCUMENT_ROOT']}/db/main.db";
  if (!unlink($dbPath)) {
    return [
      'res' => false,
      'data' => "Couldn't delete file $dbPath"
    ];
  }

  return [
    'res' => true,
    'data' => setup()
  ];
}

function get_campaign_remaining($id) {
  $res = (getDb())->querySingle("
    select 
      duration_seconds - sum(completion_seconds) as remaining
      from campaign left join job on campaign_id = campaign.id
      where campaign.id = $id 
    ");

  if($res === null) {
    return (getDb())->querySingle("select duration_seconds from campaign where id=$id");
  }
  return $res;
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
  return (getDb())->querySingle("select * from job where id=$id", true);
}

function get_campaign($id) {
  return (getDb())->querySingle("select * from campaign where id=$id", true);
}

function get_screen($id) {
  if(is_string($id)) {
    $key = 'uid';
    $id = db_string($id);
  } else {
    $key = 'id';
  }
  return (getDb())->querySingle("select * from screen where $key=$id", true);
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

function db_clean($kv) {
  $res = [];
  $db = getDb();
  foreach($kv as $k => $v) {
    $res[$db->escapeString($k)] = $db->escapeString($v);
  } 
  return $res;
}

function db_all($qstr) {
  $rowList = [];
  $res = (getDb())->query($qstr);
  while( $row = $res->fetchArray() ) {
    $rowList[] = $row;
  } 
  return $rowList;
}

function db_insert($table, $kv) {
  $fields = [];
  $values = [];

  $db = getDb();

  foreach($kv as $k => $v) {
    $fields[] = $k;
    $values[] = $v;//db->escapeString($v);
  } 

  $values = implode(',', $values);
  $fields = implode(',', $fields);

  $qstr = "insert into $table($fields) values($values)";
  if($db->exec($qstr)) {
    return $db->lastInsertRowID();
  } 
  return $qstr;
}
