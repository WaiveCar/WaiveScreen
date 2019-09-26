<?php
date_default_timezone_set('UTC');

$JSON = [
  'pre' => function($v) { 
    if ($v === null) { return $v; } 
    if (!is_string($v)) { $v = json_encode($v); }
    return db_string($v); 
  },
  'post' => function($v) { 
    if (!$v) { return $v; } 
    return json_decode($v, true); 
  }
];

$RULES = [
  'campaign' => [ 
    'shape_list' => $JSON,
    'asset' => [
      'pre' => $JSON['pre'],
      'post' => function($v) {
         $v = json_decode($v, true);
         if(!is_array($v)) {
           $v = [ $v ];
         }

         return array_map(function($m) {
           if(strpos($m, 'http') === false) {
             return 'http://waivecar-prod.s3.amazonaws.com/' . $m;
           } 
           return $m;
         }, $v);
      }
    ]
  ],
  'screen' => [
    'features' => $JSON,
    'panels' => $JSON,
    'location' => $JSON
  ],
  'sensor_history' => [
    'created_at' => [
      'pre' => function($v) { return db_string($v); },
     ]
   ]
];

// 
// Screens 
//  have 0 or 1 preset
//
// presets 
//  have 0 or 1 layout
//  have 0 or 1 exclusive sets 
//  belong to many screens
//
// exclusive sets
//  have 0 or more campaigns to include
//  have 0 or more campaigns to exclude
//
// layouts
//  have 0 or 1 template
//  have 0 or more widgets
//
// organizations
//  have 1 or more users
//  have 0 or more brands
//
// brands
//  have 0 or more campaigns
//
 
$SCHEMA = [
  'screen' => [
    'id'          => 'integer primary key autoincrement', 

    # A uid self-reported by the screen (as of the writing
    # of this comment, using dmidecode to get the CPU ID)
    'uid'         => 'text not null', 

    # A human readable name
    'serial'      => 'text',

    # If the device goes offline this will tell us
    # what it is that dissappeared so we can check
    'last_campaign_id' => 'integer',
    'imei'        => 'text',
    'phone'       => 'text',
    'car'         => 'text',
    'project'     => 'text',
    'has_time'    => 'boolean default false',
    'widget_id'   => 'integer',
    'ticker_id'   => 'integer',
    'model'       => 'text',
    'panels'      => 'text',
    'photo'       => 'text',
    'revenue'     => 'integer',
    'impact'      => 'integer',
    'lat'         => 'float default null',
    'lng'         => 'float default null',
    'location'    => 'text',
    'version'     => 'text',
    'version_time'=> 'integer',
    'uptime'      => 'integer',
    'pings'       => 'integer default 0',
    'port'        => 'integer', 
    'active'      => 'boolean default true',
    'removed'     => 'boolean default false',
    'is_fake'     => 'boolean default false',
    'features'    => 'text',
    'first_seen'  => 'datetime', 
    'last_task'   => 'integer default 0',
    'last_loc'    => 'datetime',
    'last_seen'   => 'datetime'
  ],

  'place' => [
    'id'     => 'integer primary key autoincrement',
    'name'   => 'text not null',
    'lat'    => 'float default null',
    'lng'    => 'float default null',
    'radius' => 'float default null'
  ],

  'attribution' => [
    'id'         => 'integer primary key autoincrement',
    'screen_id'  => 'integer',
    'type'       => 'text',    // such as wifi/plate, etc
    'signal'     => 'integer', // optional, could be distance, RSSI
    'mark'       => 'text',    // such as the 48-bit MAC address
    'created_at' => 'datetime default current_timestamp',
  ],

  'exclusive' => [
    'id'          => 'integer primary key autoincrement',
    'set_id'      => 'integer',
    'whitelist'   => 'boolean', // if true then this is inclusive, if false 
    'campaign_id' => 'integer'  // then we should leave it out.
  ],
    
  // revenue historicals
  'revenue_history' => [
    'id'            => 'integer primary key autoincrement',
    'screen_id'     => 'integer',
    'revenue_total' => 'integer', // deltas can be manually computed for now
    'created_at'    => 'datetime default current_timestamp',
  ],

  'organization' => [
    'id'         => 'integer primary key autoincrement',
    'name'       => 'text',
    'image'      => 'text',
  ],

  'brand' => [
    'id'         => 'integer primary key autoincrement',
    'organization_id'     => 'integer',
    'name'       => 'text',
    'image'      => 'text',
    'balance'    => 'integer',
    'created_at' => 'datetime default current_timestamp',
  ],

  'social' => [
    'id'         => 'integer primary key autoincrement',
    'brand_id'   => 'integer',
    'service'    => 'text',
    'name'       => 'text',
    'token'      => 'text',
    'created_at' => 'datetime default current_timestamp',
  ],

  'user' => [
    'id'         => 'integer primary key autoincrement',
    'name'       => 'text',
    'password'   => 'text',
    'image'      => 'text',
    'email'      => 'text',
    'title'      => 'text',
    'organization_id'     => 'integer',
    'brand_id'   => 'integer',
    'role'       => 'text', // either admin/manager/viewer
    'phone'      => 'text',
    'created_at' => 'datetime default current_timestamp',
  ],

  'addon' => [
    'id'     => 'integer primary key autoincrement',
    'name'   => 'text', // what to call it
    'image'  => 'text', // url of logo or screenshot
    'type'   => 'text', // ticker or app
    'topic'  => 'text', // optional, such as "weather"
    'source' => 'text', // The url where to get things
    'created_at' => 'datetime default current_timestamp',
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
  // If they are empty, then it means that it's 24 hours a day
  //
  'campaign' => [
    'id'          => 'integer primary key autoincrement',
    'name'        => 'text',
    'ref_id'      => 'text',
    'brand_id'    => 'integer',
    'organization_id'    => 'integer',
    'order_id'    => 'integer',
    'asset'       => 'text not null',
    'duration_seconds' => 'integer',
    'completed_seconds' => 'integer default 0',
    'project'     => 'text default "dev"',

    //
    // For now, until we get a geo db system
    // this makes things easily queriable
    //
    // Stuff will be duplicated into shapelists
    //
    'lat'         => 'float default null',
    'lng'         => 'float default null',
    'radius'      => 'float default null',

    //
    // shape_list := [ polygon | circle ]* 
    //  polygon   := [ "Polygon", [ coord, ... ] ]
    //  circle    := [ "Circle", coord, radius ]
    //  coord     := [ lon, lat ]
    //  radius    := integer (meters)
    //
    'shape_list'  => 'text',

    'start_minute'=> 'integer default null',
    'end_minute'  => 'integer default null',
    'approved'    => 'boolean default false',
    'active'      => 'boolean default false',
    'is_default'  => 'boolean default false',
    'priority'    => 'integer default 0',
    'impression_count' => 'integer',

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

  // In the future we can have different tag classes or namespaces
  // But for the time being we just need 1 separation: LA and NY
  // and that's literally it. Generalizability can come later.
  //
  // This is a list of tags, it's notable that we aren't really
  // doing some kind of "normalization" like all the proper kids
  // do because we don't want to be doing stupid table joins 
  // everywhere to save a couple bytes.
  'tag' => [
    'id'        => 'integer primary key autoincrement',
    'name'      => 'text',
    'created_at' => 'datetime default current_timestamp',
  ],

  // #47 - the screen_id/tag is the unique constraint. There's
  // probably a nice way to do it. Also if you really are doing
  // things well then you use the whitelist from the tag table
  // before inserting since we are keeping it daringly free-form
  'screen_tag' => [
    'id'        => 'integer primary key autoincrement',
    'screen_id' => 'integer',
    'tag'       => 'text',
    'created_at' => 'datetime default current_timestamp',
  ],

  // #95 If different tags need different default campaign ids 
  // or split kingdoms we do that here. It's basically a
  // key/value with a name-space. Right now we don't have 
  // a list of tags, probably should so that the screen_tag
  // and tag_info table references a tag_list but this is
  // fine for now.
  'tag_info' => [
    'id'         => 'integer primary key autoincrement',
    'tag'        => 'text not null',
    'key'        => 'text',
    'value'      => 'text',
    'created_at' => 'datetime default current_timestamp',
  ],

  // #107 - scoped tasks
  // The id here is the referential id so that we 
  // can group the responses
  'task' => [
    'id'           => 'integer primary key autoincrement',
    'created_at'   => 'datetime default current_timestamp',
    'expiry_sec'   => 'integer default 172800',
    'scope'        => 'text',
    'command'      => 'text',
    'args'         => 'text'
  ],
   
  // #39
  'task_screen' => [
    'id'           => 'integer primary key autoincrement',
    'task_id'      => 'integer',
    'screen_id'    => 'integer',
  ],

  'task_response' => [
    'id'          => 'integer primary key autoincrement',
    'task_id'     => 'integer',
    'screen_id'   => 'integer',
    'response'    => 'text',
    'created_at'  => 'datetime default current_timestamp',
  ],
    
  # 143
  'screen_history' => [
    'id'          => 'integer primary key autoincrement',
    'screen_id'   => 'integer',
    'action'      => 'text',
    'value'       => 'text',
    'old'         => 'text',
    'created_at'  => 'datetime default current_timestamp'
  ],

  // #65
  'job_history' => [
    'id'        => 'integer primary key autoincrement',
    'job_id'    => 'integer',
    'start'     => 'datetime',
    'end'       => 'datetime'
  ],

  'ping_history' => [
    'id'        => 'integer primary key autoincrement',
    'screen_id' => 'integer',
    'created_at'=> 'datetime default current_timestamp',
  ],

  // This is going to be a monstrosity really and will
  // be the majority of the storage.
  'sensor_history' => [
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
    $dbPath = "/var/db/waivescreen/main.db";
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

function db_int($what) {
  return intval($what);
}

function db_string($what) {
  $where = strpos($what, "'");
  if ($where === false) {
    return "'$what'";
  } else if ($where != 0) {
    return "'" . SQLite3::escapeString($what) . "'";
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

function get_campaign_remaining($id) {
  $res = (db_connect())->querySingle("select duration_seconds - completed_seconds as remaining from campaign where campaign.id = $id");

  if($res === null) {
    return (db_connect())->querySingle("select duration_seconds from campaign where id=$id");
  }
  return $res;
}

class Get {
  public static function doquery($qstr, $table) {
    $res = _query($qstr, 'querySingle');
    return process($table, $res, 'post');
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

function process($table, $obj, $what) {
  global $RULES;
  if($obj && $table && isset($RULES[$table])) {
    foreach($RULES[$table] as $key => $processor) {
      if(isset($obj[$key]) && isset($processor[$what])) {
        $obj[$key] = $processor[$what]($obj[$key], $obj);
      }
    }
  }
  return $obj;
}

function db_update($table, $id, $kv) {
  $fields = [];

  $kv = process($table, $kv, 'pre');
  
  if(is_array($id)) {
    $parts = array_keys($id);
    $key = $parts[0];
    $value = $id[$key];
  } else {
    $key = 'id';
    $value = $id;
  }

  foreach($kv as $k => $v) {
    $fields[] = "$k=$v";
  } 

  $fields = implode(',', $fields);

  $qstr = "update $table set $fields where $key = $value";
  // error_log($qstr);
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
    if ( is_numeric($value) ) {
      $ret[] = "$key $operator $value";
    }
    else if ( is_string($value) ) {
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
        $row = process($table, $row, 'post');
      }
      $rowList[] = $row;
    } 
  }
  return $rowList;
}

function db_insert_many($table, $kvList) {
  if(count($kvList) === 0) {
    return null;
  }
  $fields = [];
  $valueList = [];
  $isFirst = true;
  $db = db_connect();

  foreach($kvList as $kv) {
    $kv = process($table, $kv, 'pre');
    $row = [];
    foreach($kv as $k => $v) {
      if($isFirst) {
        $fields[] = $k;
      }
      if($v === false) {
        $row[] = 'false';
      } else {
        $row[] = $v;
      }
    } 
    $valueList[] = "(" . implode(',', $row) . ")";
    $isFirst = false;
  }
  $fields = implode(',', $fields);
  $values = implode(',', $valueList);
  $qstr = "insert into $table($fields) values $values";
  //error_log($qstr);

  if(_query($qstr)) {
    return $db->lastInsertRowID();
  }
  return null;
}

function db_insert($table, $kv) {
  $fields = [];
  $values = [];

  $db = db_connect();
  $kv = process($table, $kv, 'pre');

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
