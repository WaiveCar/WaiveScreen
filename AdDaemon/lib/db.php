<?php
date_default_timezone_set('UTC');

$RULES = [
  'campaign' => [ 
    'asset' => function($v) {
      return array_map(function($m) {
        return 'http://waivecar-prod.s3.amazonaws.com/' . $m;
      }, json_decode($v, true));
     }
   ]
];

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

    # A uid self-reported by the screen (as of the writing
    # of this comment, using dmidecode to get the CPU ID)
    'uid'         => 'text not null', 

    # A human readable name
    'name'        => 'text',

    # If the device goes offline this will tell us
    # what it is that dissappeared so we can check
    'imei'        => 'text',
    'phone'       => 'text',

    'lat'         => 'float default null',
    'lng'         => 'float default null',
    'version'     => 'text',
    'pings'       => 'integer default 0',
    'port'        => 'integer', 
    'active'      => 'boolean default true',
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
    'priority'    => 'integer default 0',
    'start_time'  => 'datetime default current_timestamp',
    'end_time'    => 'datetime'
  ],

  'kv' => [
    'id'         => 'integer primary key autoincrement',
    'key'        => 'text',
    'value'      => 'text',
    'created_at' => 'datetime default current_timestamp',
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
  ],

  // see #65
  'job_history' => [
    'id'        => 'integer primary key autoincrement',
    'job_id'    => 'integer',
    'start'     => 'datetime',
    'end'       => 'datetime'
  ],

  // This is going to be a monstrosity really and will
  // be the majority of the storage.
  'history' => [
    'id'        => 'integer primary key autoincrement',
    'job_id'    => 'integer',
    // this is duplicate but honestly I'm thinking this
    // will be a common request - let's not make it expensive
    'screen_id' => 'integer',
    'lat' => 'float default null',
    'lng' => 'float default null',
    'created_at' => 'datetime',

    // The rest here is kind of a copy and paste for now.
    // We probably don't *truly* care about this but we'll see
    'Light' => 'float default null',
    'Fan' => 'float default null',
    'Current' => 'float default null',
    'Voltage' => 'float default null',
    'Temp' => 'float default null',
    'Tread' => 'float default null',
    'Tres' => 'float default null',
    'Pitch' => 'float default null',
    'Roll' => 'float default null',
    'Yaw' => 'float default null',
    'Accel_x' => 'float default null',
    'Accel_y' => 'float default null',
    'Accel_z' => 'float default null',
    'Gyro_x' => 'float default null',
    'Gyro_y' => 'float default null',
    'Gyro_z' => 'float default null'
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
    $_db->busyTimeout(5000);
    // WAL mode has better control over concurrency.
    // Source: https://www.sqlite.org/wal.html
    $_db->exec('PRAGMA journal_mode = wal;');
  }
  return $_db;
}

function db_string($what) {
  if (strpos($what, "'") === false) {
    return "'$what'";
  }
  return $what;
}
function db_date($what) {
 return "datetime($what,'unixepoch')";
}
function _query($qstr, $func='exec') {
  $db = db_connect();
  try {
    if($func === 'querySingle') {
      $res = $db->$func($qstr, true);
    } else {
      $res = $db->$func($qstr);
    }
    if($res) {
      return $res;
    } else {
      error_log("Failed Query:" . $qstr);
    }
  } catch(Exception $ex) { 
    error_log("$qstr $ex " . json_encode($ex->getTrace()));
  }
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
  public static function doquery($qstr, $table) {
    global $RULES;
    $res = _query($qstr, 'querySingle');
    if($res) {
      if($table && isset($RULES[$table])) {
        $ruleTable = $RULES[$table];
        foreach($ruleTable as $key => $processor) {
          $res[$key] = $processor($res[$key]);
        }
      }
    }
    return $res;
  }

  public static function __callStatic($name, $argList) {
    $arg = $argList[0];
    $key = 'id';
    if(!is_array($arg)) {
      if((is_string($arg) || is_numeric($arg)) && !empty($arg)) {
        $arg = ['id' => $arg];
      } else {
        return null;
      }
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

    $qstr = "select * from $name where $kvstr";
    return static::doquery($qstr, $name);
  }
};

class Many extends Get {
  public static function doquery($qstr, $table) {
    return db_all($qstr, $table);
  }
};


function db_update($table, $id, $kv) {
  $fields = [];

  foreach($kv as $k => $v) {
    $fields[] = "$k=$v";
  } 

  $fields = implode(',', $fields);
  /*
  if(!is_integer($id)) {
    $id = db_string($id);
  }
   */

  $qstr = "update $table set $fields where id = $id";
  return _query($qstr);
}

function db_clean($kv) {
  $res = [];
  $db = db_connect();
  foreach($kv as $k => $v) {
    if(is_array($v)) {
      error_log(json_encode([$k, $v]));
    } else {
      $res[$db->escapeString($k)] = $db->escapeString($v);
    }
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

function db_all($qstr, $table = false) {
  global $RULES;
  $ruleTable = false;
  if($table && isset($RULES[$table])) {
    $ruleTable = $RULES[$table];
  }

  $rowList = [];
  if(!is_string($qstr)) {
    $res = $qstr;
  } else {
    $res = _query($qstr, 'query');
    if(is_bool($res)) {
      return [];
    }
  }
  if($res) {
    while( $row = $res->fetchArray(SQLITE3_ASSOC) ) {
      if($ruleTable) {
        foreach($ruleTable as $key => $processor) {
          $row[$key] = $processor($row[$key]);
        }
      }
      $rowList[] = $row;
    } 
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

  if(_query($qstr)) {
    return $db->lastInsertRowID();
  }
  return null;
}
