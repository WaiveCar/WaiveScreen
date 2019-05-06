<?php
date_default_timezone_set('UTC');

$SCHEMA = [
  'user' => [
    'id'          => 'integer primary key autoincrement', 
    'email'       => 'text not null',
    'phone'       => 'text', 
    'stripe_id'   => 'text not null',
    'created_at'  => 'datetime default current_timestamp', 
    'last_seen'   => 'datetime default current_timestamp'
  ],

  'orders' => [
    'id'          => 'integer primary key autoincrement', 
    'user_id'     => 'integer',
    'campaign_id' => 'integer',
    'amount'      => 'integer', 
    'charge_id'   => 'text',
    'status'      => 'text',
    'created_at'  => 'datetime default current_timestamp'
  ],

  'subscription' => [
    'id'          => 'integer primary key autoincrement', 
    'user_id'     => 'integer',
    'campaign_id' => 'integer',
    'amount'      => 'integer', 
    'created_at'  => 'datetime default current_timestamp'
  ],

  'screen' => [
    'id'          => 'integer primary key autoincrement', 
    'uid'         => 'text not null', 
    'lat'         => 'float default null',
    'lng'         => 'float default null',
    'version'     => 'text',
    'port'        => 'integer', 
    'first_seen'  => 'datetime', 
    'last_seen'   => 'datetime'
  ],

  'place' => [
    'id'     => 'integer primary key autoincrement',
    'name'   => 'text not null',
    'lat'    => 'float default null',
    'lng'    => 'float default null',
    'radius' => 'float default null'
  ],

  //
  // consider: potentially create a second table for "staging" campaigns
  // that aren't active as opposed to relying on a boolean
  // in this table below
  //
  // The start_minute and end_minute are for campaigns that 
  // don't run 24 hours a day.
  //
  // The start_time and end_time are the bounds to do the 
  // campaign. It doesn't need to be exactly timebound by
  // these and can bleed over in either direction if it 
  // gets to that.
  // 
  // If they are empty', then it means that it's 24 hours a day
  //
  'campaign' => [
    'id'          => 'integer primary key autoincrement',
    'order_id'    => 'integer',
    'asset'       => 'text not null',
    'duration_seconds' => 'integer',
    'completed_seconds' => 'integer default 0',
    'place_id'    => 'integer default null',
    'lat'         => 'float default null',
    'lng'         => 'float default null',
    'radius'      => 'float default null',
    'start_minute'=> 'integer default null',
    'end_minute'  => 'integer default null',
    'active'      => 'boolean default false',
    'start_time'  => 'datetime default current_timestamp',
    'end_time'    => 'datetime'
  ],

  'job' => [
    'id'          => 'integer primary key autoincrement',
    'campaign_id' => 'integer',
    'screen_id'   => 'integer',
    'goal'        => 'integer',
    'completed_seconds' => 'integer default 0',
    'last_update' => 'datetime',
    'job_start'   => 'datetime',
    'job_end'     => 'datetime'
  ]

];
$_db = false;
function db_connect() {
  global $_db;
  if(!$_db) {
    $dbPath = __DIR__ . "/../../db/main.db";
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
function db_date($what) {
 return "datetime($what,'unixepoch')";
}
function get_column_list($table_name) {
  $db = db_connect();
  $res = $db->query("pragma table_info( $table_name )");

  return array_map(function($row) { 
    return $row['name'];
  }, db_all($res));
}

function setup() {
  $db = db_connect();
  global $SCHEMA;
  $res = [];
  foreach(array_values($SCHEMA) as $table) {
    $table = preg_replace('/\s+/', ' ', $table);
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
  $res = (db_connect())->querySingle("
    select 
      duration_seconds - sum(campaign.completed_seconds) as remaining
      from campaign left join job on campaign_id = campaign.id
      where campaign.id = $id 
    ");

  if($res === null) {
    return (db_connect())->querySingle("select duration_seconds from campaign where id=$id");
  }
  return $res;
}

function get_campaign_completion($id) {
  return (db_connect())->querySingle("
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
      // this means a raw string was passed
      if(is_integer($key)) {
        $kvargs[] = $value;
      } else {
        if(is_string($value)) {
          $value = db_string($value);
        }
        $kvargs[] = "$key=$value";
      }
    }
    $kvstr = implode(' and ', $kvargs);

    return (db_connect())->querySingle("select * from $name where $kvstr", true);
  }
};


function db_update($table, $id, $kv) {
  $fields = [];

  $db = db_connect();

  foreach($kv as $k => $v) {
    $fields[] = "$k=".$db->escapeString($v);
  } 

  $fields = implode(',', $fields);

  return $db->exec("update $table set $fields where id = $id");
}

function db_clean($kv) {
  $res = [];
  $db = db_connect();
  foreach($kv as $k => $v) {
    $res[$db->escapeString($k)] = $db->escapeString($v);
  } 
  return $res;
}

function sql_kv($hash, $operator = '=', $quotes = "'", $intList = []) {
  $ret = [];
  foreach($hash as $key => $value) {
    if ( is_string($value) ) {
      if(in_array($key, $intList)) {
        $ret[] = "$key $operator $value";
      } else {
        $ret[] = "$key $operator $quotes$value$quotes";
      }
    }
  } 
  return $ret;
}

function db_all($qstr) {
  $rowList = [];
  if(!is_string($qstr)) {
    $res = $qstr;
  } else {
    $res = (db_connect())->query($qstr);
  }
  while( $row = $res->fetchArray(SQLITE3_ASSOC) ) {
    $rowList[] = $row;
  } 
  return $rowList;
}

function db_insert($table, $kv) {
  $fields = [];
  $values = [];

  $db = db_connect();

  foreach($kv as $k => $v) {
    $fields[] = $k;
    if($v === false) {
      $values[] = 'false';
    } else {
      $values[] = $v;//db->escapeString($v);
    }
  } 

  $values = implode(',', $values);
  $fields = implode(',', $fields);

  $qstr = "insert into $table($fields) values($values)";

  try {
    if($db->exec($qstr)) {
      return $db->lastInsertRowID();
    } 
  } catch(Exception $ex) { 
    error_log($qstr);
    error_log($ex);
  }
  return $qstr;
}
