<?php
date_default_timezone_set('UTC');

$SCHEMA = [
  'user' => 'create table if not exists user(
    id integer primary key autoincrement, 
    email text not null,
    phone text, 
    stripe_id text not null,
    created_at datetime default current_timestamp, 
    last_seen datetime default current_timestamp
  )',

  'order' => 'create table if not exists order(
    id integer primary key autoincrement, 
    user_id integer,
    campaign_id integer,
    amount integer, 
    charge_id text,
    status text,
    created_at datetime default current_timestamp, 
  )',

  'subscription' => 'create table if not exists subscription(
    id integer primary key autoincrement, 
    user_id integer,
    campaign_id integer,
    amount integer, 
    created_at datetime default current_timestamp, 
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

  'place' => 'create table if not exists place(
    id integer primary key autoincrement,
    name text not null,
    lat float default null,
    lng float default null,
    radius float default null
  )',

  //
  // consider: potentially create a second table for "staging" campaigns
  // that aren't active as opposed to relying on a boolean
  // in this table below
  //
  'campaign' => 'create table if not exists campaign(
    id integer primary key autoincrement,
    order_id integer,
    asset text not null,
    duration_seconds integer,
    completed_seconds integer default 0,
    place_id integer default null,
    lat float default null,
    lng float default null,
    radius float default null,
    start_minute integer default null,
    end_minute integer default null,
    active boolean default false,
    start_time datetime default current_timestamp,
    end_time datetime
  )',

  'job' => 'create table if not exists job(
    id integer primary key autoincrement,
    campaign_id integer,
    screen_id integer,
    goal integer,
    completed_seconds integer default 0,
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

class Get {
  public static function __callStatic($name, $argList) {
    $arg = $argList[0];
    $key = 'id';
    if(!is_array($arg)) {
      $arg = ['id' => $arg];
    }

    $kvargs = [];
    foreach($arg as $key => $value) {
      if(is_string($value)) {
        $value = db_string($value);
      }
      $kvargs[] = "$key=$value";
    }
    $kvstr = implode(' and ', $kvargs);

    return (getDb())->querySingle("select * from $name where $kvstr", true);
  }
};


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
