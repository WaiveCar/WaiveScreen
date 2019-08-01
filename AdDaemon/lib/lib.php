<?
require $_SERVER['DOCUMENT_ROOT'] .  'AdDaemon/vendor/autoload.php';

use Aws\S3\S3Client;
use Ramsey\Uuid\Uuid;
use Ramsey\Uuid\Exception\UnsatisfiedDependencyException;

$mypath = $_SERVER['DOCUMENT_ROOT'] . 'AdDaemon/lib/';
include_once($mypath . 'db.php');

$PORT_OFFSET = 7000;
$DAY = 24 * 60 * 60;
$PROJECT_LIST = ['LA', 'NY'];
$DEFAULT_CAMPAIGN_MAP = [
  'none' => 1,
  'LA' => 1,
  'NY' => 2,
  'dev' => 3
];

// Play time in seconds of one ad.
$PLAYTIME = 7.5;

function mapBy($obj, $key) {
  $res = [];
  foreach($obj as $row) {
    $res[$key] = $row;
  }
  return $res;
}

function aget($source, $keyList, $default = null) {
  if(!is_array($keyList)) {
    $keyStr = $keyList;
    $keyList = explode('.', $keyStr);

    $orList = explode('|', $keyStr);
    if(count($orList) > 1) {

      $res = null;
      foreach($orList as $key) {
        // this resolves to the FIRST valid value
        if($res === null) {
          $res = aget($source, $key);
        }
      }
      return ($res === null) ? $default : $res;
    }   
  }
  $key = array_shift($keyList);

  if($source && isset($source[$key])) {
    if(count($keyList) > 0) {
      return aget($source[$key], $keyList);
    } 
    return $source[$key];
  }

  return $default;
}

function jemit($what) {
  echo json_encode($what);
  exit;
}

function doSuccess($what) {
  return [
    'res' => true,
    'data' => $what
  ];
}

function doError($what) {
  return [
    'res' => false,
    'data' => $what
  ];
}

function missing($what, $list) {
  $res = [];
  foreach($list as $field) {
    if(!isset($what[$field])) {
      $res[] = $field;
    }
  }
  if(count($res)) {
    return $res;
  }
}

function distance($lat1, $lon1, $lat2 = false, $lon2 = false) {
  if(!$lat2) {
    if(empty($lon1['lng']) && empty($lat1['lng'])) {
      return false;
    }
    $lon2 = $lon1['lng'];
    $lat2 = $lon1['lat'];
    $lon1 = $lat1['lng'];
    $lat1 = $lat1['lat'];
  }

  $theta = $lon1 - $lon2;
  $dist = sin(deg2rad($lat1)) * sin(deg2rad($lat2)) +  cos(deg2rad($lat1)) * cos(deg2rad($lat2)) * cos(deg2rad($theta));
  $dist = acos($dist);
  $dist = rad2deg($dist);
  // meters
  return $dist * 60 * 1397.60312636;
}

function create_screen($uid, $data = []) {
  global $PORT_OFFSET;
  // we need to get the next available port number
  $nextport = intval((db_connect())->querySingle('select max(port) from screen')) + 1;
  if($nextport < $PORT_OFFSET) {
    // gotta start from somewhere.
    $nextport = $PORT_OFFSET;
  }

  $data = array_merge($data, [
    'uid' => db_string($uid),
    'port' => $nextport,
    'first_seen' => 'current_timestamp',
    'last_seen' => 'current_timestamp'
  ]);

  $screen_id = db_insert('screen', $data);

  return Get::screen($screen_id);
}

function find_unfinished_job($campaignId, $screenId) {
  return Many::job([
    'campaign_id' => $campaignId,
    'screen_id' => $screenId,
    'completed_seconds < goal'
  ]);
}


function find_missing($obj, $fieldList) {
  return array_diff($fieldList, array_keys($obj));
}

function log_screen_changes($old, $new) {
  // When certain values change we should log that
  // they change.
  $deltaList = ['phone', 'car', 'project', 'model', 'version', 'active', 'features'];
  foreach($deltaList as $delta) {
    if(!isset($new[$delta])) {
      continue;
    }
    $compare_before = $old[$delta];
    $compare_after = $new[$delta];

    if(is_array($old[$delta])) {
      $compare_before = json_encode($compare_before);
      $old[$delta] = $compare_before;
    }
    if(is_array($new[$delta])) {
      $compare_after = json_encode($compare_after);
      $new[$delta] = $compare_after;
    }

    $compare_before = trim($compare_before, "'");
    $compare_after = trim($compare_after, "'");
    if($compare_before !== $compare_after) {
      error_log("'$compare_before' != '$compare_after'");
      db_insert('screen_history', [
        'screen_id' => $old['id'],
        'action' => db_string($delta),
        'old' => db_string($old[$delta]),
        'value' => db_string($new[$delta])
      ]);
    }
  }
}

// Whenever we get some communication we know
// the screen is on and we may have things like
// lat/lng if we're lucky so let's try to gleam
// that.
function upsert_screen($screen_uid, $payload) {
  $screen = Get::screen(['uid' => $screen_uid]);

  if(!$screen) {
    $screen = create_screen($screen_uid);
  }

  $data = ['last_seen' => 'current_timestamp'];
  if(!empty($payload['lat']) && floatval($payload['lat'])) {
    $data['lat'] = floatval($payload['lat']);
    $data['lng'] = floatval($payload['lng']);
    $data['last_loc'] = 'current_timestamp';
  }

  db_update('screen', ['uid' => db_string($screen_uid)], $data);

  return array_merge($screen, $data);
}

// After a screen runs a task it's able to respond... kind of 
// have a dialog if you will.
function response($payload) {
  $missing = find_missing($payload, ['task_id', 'uid', 'response']);
  if($missing) {
    return doError("Missing fields: " . implode(', ', $missing));
  }
  $task_id = intval($payload['task_id']);

  $screen = Get::screen(['uid' => $payload['uid']]);

  if ($screen['last_task'] < $task_id) {
    db_update('screen', $screen['id'], ['last_task' => $task_id]);
  }

  return db_insert('task_response', [
    'task_id' => db_int($payload['task_id']),
    'screen_id' => db_int($screen['id']),
    'response' => db_string($payload['response'])
  ]);
}

// This is called from the admin UX
function command($payload) {
  $scope_whitelist = ['id', 'project', 'model', 'version'];
  $idList = [];
  
  $field_raw = aget($payload, 'field');
  $value_raw = aget($payload, 'value');
  $command = aget($payload, 'command');

  if (in_array($field_raw, $scope_whitelist)) {
    $value = db_string($value_raw);
    $idList = array_map(
      function($row) { return $row['id']; }, 
      db_all("select id from screen where $field_raw = $value and active = true")
    );
  } else {
    return doError("Scope is wrong. Try: " . implode(', ', $scope_whitelist));
  }

  if(count($idList) == 0) {
    return doError("No screens match query");
  }

  if(empty($command)) {
    return doError("Command cannot be blank");
  }

  $taskId = db_insert('task', [
    'scope' => db_string("$field_raw:$value_raw"),
    'command' => db_string($command),
    'args' => db_string($payload['args'])
  ]);

  if(!$taskId) {
    return doError("Unable to create task");
  }

  $toInsert = [];
  foreach($idList as $id) {
    $toInsert[] = [
      'task_id' => $taskId,
      'screen_id' => $id 
    ];
  }

  db_insert_many('task_screen', $toInsert);

  return doSuccess( $taskId );
}

function default_campaign($screen) {
  global $DEFAULT_CAMPAIGN_MAP;
  $id = $DEFAULT_CAMPAIGN_MAP['none'];
  if($screen['project']) {
    $id =  $DEFAULT_CAMPAIGN_MAP[$screen['project']];
  }
  return Get::campaign($id);
}

function ping($payload) {
  global $VERSION, $LASTCOMMIT;

  error_log(json_encode($payload));

  // features/modem/gps
  foreach([
    'version', // consistent
    'imei', 'phone', 'Lat', 'Lng',                     // <v0.2-Bakeneko-347-g277611a
    'modem.imei', 'modem.phone', 'gps.lat', 'gps.lng', // >v0.2-Bakeneko-347-g277611a
    'version_time',                                    // >v0.2-Bakeneko-378-gf6697e1
    'uptime', 'features',                              // >v0.2-Bakeneko-384-g4e32e37
    'last_task'                                        // >v0.2-Bakeneko-623-g8989622
  ] as $key) {
    $val = aget($payload, $key);

    if($val) {
      $parts = explode('.', $key);
      $base = strtolower(array_pop($parts));
      if(is_array($val)) {
        $obj[$base] = $val;
      } else {
        $obj[$base] = db_string($val);
      }
    }
  }

  if(isset($payload['uid'])) {
    $screen = upsert_screen($payload['uid'], $obj);
  } else {
    return doError("UID needs to be set before continuing");
  }

  $obj['pings'] = intval($screen['pings']) + 1;

  log_screen_changes($screen, $obj);

  db_update('screen', $screen['id'], $obj);
  db_insert('ping_history', ['screen_id' => $screen['id']]);

  // We return the definition for the default campaign
  // The latest version of the software
  // and the definition of the screen.
  $res = [
    'version' => $VERSION,
    'version_date' => $LASTCOMMIT,
    'screen' => $screen,
    'default' => default_campaign($screen)
  ];
  return task_inject($screen, $res);
}

function create_job($campaignId, $screenId) {
  $job_id = false;
  $ttl = get_campaign_remaining($campaignId);
  if($ttl < 0) {
    return false;
  }
  $campaign = Get::campaign($campaignId);

  if($campaign) {
    $goal = min($ttl, 60 * 4);

    $job_id = db_insert(
      'job', [
        'campaign_id' => db_int($campaignId),
        'screen_id' => $screenId,
        'job_start' => 'current_timestamp',
        'job_end' => db_string($campaign['end_time']),
        'last_update' => 'current_timestamp',
        'goal' => $goal
      ]
    );
  }
  if($job_id) {
    return Get::job($job_id);
  }
}

function update_job($jobId, $completed_seconds) {
  if($jobId) {
    return db_update('job', $jobId, [
      'completed_seconds' => $completed_seconds,
      'job_end' => 'current_timestamp'
    ]);
  } 
}

function task_master($screen) {
  // The crazy date math there is the simplest way I can get 
  // this thing to work, I know I know, it looks excessive.
  //
  // If you think you can do better crack open an sqlite3 shell
  // and start hacking.
  //
  return db_all("
    select * from task_screen 
      join task on task_screen.task_id = task.id
      where 
            task_screen.screen_id = {$screen['id']}
        and task.id > {$screen['last_task']} 
        and strftime('%s', task.created_at) + task.expiry_sec - strftime('%s', current_timestamp) > 0 
  ");
}

// ----
//
// end points
//
// ----

function screens() {
  return show('screen');
}

function tasks() {
  return show('task');
}

function task_dump() {
  return [
    'task' => show('task', 'order by id desc'),
    'task_screen' => show('task_screen'),
    'response' => show('task_response'),
    'screen' => show('screen')
  ];
}

function screen_edit($data) {
  $whitelist = ['car', 'phone', 'serial', 'project', 'model'];
  $update = [];
  foreach(array_intersect($whitelist, array_keys($data)) as $key) {
    $update[$key] = db_string($data[$key]);
  }
  $old = Get::screen($data['id']);
  log_screen_changes($old, $data);
  db_update('screen', $data['id'], $update);
  return Get::screen($data['id']);
}

// we need to find out if the screen has tasks we need
// to inject and then do so
//
// Why are we calling by reference like a weirdo? 
// We want the key to be empty if there's nothing
// that satisfies it.
function task_inject($screen, $res) {
  $taskList = task_master($screen);
  if(count($taskList) > 0) {
    if(empty($res['task'])) {
      // Vintage task
      $res['task'] = [];
      // modern tasklist
      $res['taskList'] = [];
    }
    foreach($taskList as $task) {
      $res['task'][] = [$task['command'],$task['args']];
      $res['taskList'][] = $task;
    }
  }
  $tasks = aget($res,'taskList');
  if ($tasks) {
    error_log($screen['uid'] . ' ' . json_encode($tasks));
  }
  return $res;
}


function update_campaign_completed($id) {
  if(!$id) {
    error_log("Not updating an invalid campaign: $id");
  } else {
    // only update campaign totals that aren't our defaults
    _query("update campaign 
      set completed_seconds=(
        select sum(completed_seconds) from job where campaign_id=$id
      ) where id=$id and is_default=0");
  }
}
  
function inject_priority($job, $screen, $campaign) {
  $job['priority'] = aget($campaign, 'priority');
  return $job;
}

function sow($payload) {
  error_log(json_encode($payload));
  if(isset($payload['uid'])) {
    $screen = upsert_screen($payload['uid'], $payload);
  } else {
    return doError("UID needs to be set before continuing");
  }

  $jobList = aget($payload, 'jobs', []);
  $campaignsToUpdateList = [];

  foreach($jobList as $job) {

    // this is the old system ... these machines
    // should just upgrade.
    $job_id = aget($job, 'job_id');
    if(aget($job, 'id')) {
      error_log("need to upgrade: {$payload['uid']}");
    } else if($job_id) {
      if (! update_job($job_id, $job['completed_seconds']) ) {
        error_log("could not process job: " . json_encode($job));
      }

      if(!isset($job['campaign_id'])) {
        $job = Get::job($job_id);
      }
      if(isset( $job['campaign_id'] )) {
        $campaignsToUpdateList[] = $job['campaign_id'];
      }
    }
  }

  // Make sure we update our grand totals on a per campaign basis when it comes in.
  $uniqueCampaignList = array_unique($campaignsToUpdateList);
  foreach($uniqueCampaignList as $campaign_id) {
    if($campaign_id) {
      update_campaign_completed($campaign_id);
    } else {
      error_log("Couldn't update campaign");
    }
  }
  // error_log(json_encode($uniqueCampaignList));
	
  $active = active_campaigns($screen);
  // If we didn't get lat/lng from the sensor then we just any ad
  if(empty($payload['lat'])) {
    $nearby_campaigns = $active;
  } else {
    // right now we are being realllly stupid.
    $nearby_campaigns = array_filter($active, function($campaign) use ($payload) {
      /*
      if(isset($payload['lat'])) {
        // under 1.5km
        return distance($campaign, $payload) < ($campaign['radius'] * 100);
      } 
       */
      // essentially this is for debugging
      return true;
    });
  }

  // so if we have existing outstanding jobs with the
  // screen id and campaign then we can just re-use them.
  error_log("nearby: " . json_encode($nearby_campaigns));
  $server_response = task_inject($screen, ['res' => true]);
  $server_response['data'] = array_map(function($campaign) use ($screen) {
    $jobList = find_unfinished_job($campaign['id'], $screen['id']);
    if(!$jobList) {
      $jobList = [ create_job($campaign['id'], $screen['id']) ];
    }
    foreach($jobList as $job) {
      if(isset($job['id'])) {
        $job_res = array_merge([
          'job_id' => $job['id'],
          'campaign_id' => $campaign['id'],
          'asset' => $campaign['asset']
        ], $job);
        return inject_priority($job_res, $screen, $campaign);
      }
    }
  }, $nearby_campaigns);
  
  error_log("jobs: " . json_encode($server_response));
  return $server_response; 
}

function get_available_slots($start_query, $duration) {
  if(!$start_query) {
    $start_query = date();
  }
  if($duration) {
    $duration = 7 * $DAY;
  }
  $end_query = $start_query + $duration;
  //
  // This is more or less a functional ceiling on our commitment for a time period if we are to assume that we can get everything
  // done by the end of the duration, not the end of the campaign.
  //
  $committed_seconds = run("select sum(completed_seconds - duration_seconds) from campaigns where $start_time > $start_query or $end_time < $end_query");
  $available_seconds = $duration - $committed_seconds;

  // This is really rudimentary
  return $committed_seconds;
}


function upload_s3($file) {
  // lol we deploy this line of code with every screen. what awesome.
	$credentials = new Aws\Credentials\Credentials('AKIAIL6YHEU5IWFSHELQ', 'q7Opcl3BSveH8TU9MR1W27pWuczhy16DqRg3asAd');

  // this means there was an error uploading the file
  // currently we'll let this routine fail and then hit
  // the error log
  if(empty($file['tmp_name'])) {}

  $parts = explode('/',$file['type']);
  $ext = array_pop($parts);
  $name = implode('.', [Uuid::uuid4()->toString(), $ext]);

	$s3 = new Aws\S3\S3Client([
		'version'     => 'latest',
		'region'	    => 'us-east-1',
		'credentials' => $credentials
	]);
  try {
    $res = $s3->putObject([
      'Bucket' => 'waivecar-prod',
      'Key'    => $name,
      'Body'   => fopen($file['tmp_name'], 'r'),
      'ACL'    => 'public-read',
    ]);
  } catch (Aws\S3\Exception\S3Exception $e) {
    throw new Exception("$file failed to upload");
  }
  // see https://docs.aws.amazon.com/aws-sdk-php/v3/api/api-s3-2006-03-01.html#putobject
  return $name;
}

function show($what, $clause = '') {
  return db_all("select * from $what $clause", $what);
}

function active_campaigns($screen) {
  return show('campaign', "where 
    active = 1                       and 
    is_default = 0                   and
    project = '{$screen["project"]}' and
    end_time > current_timestamp     and 
    start_time < current_timestamp   and 
    completed_seconds < duration_seconds 
    order by active desc, start_time desc");
}

function campaigns_list($opts = []) {
  $filter = [];

  if(isset($opts['id'])) {
    // ah, with this slight increase in bullshit we 
    // can do comma separated mulit-request support.
    // What a life.
    $idList = array_map(
      function($row) { 
        return intval($row); 
      }, 
      explode(',', $opts['id'])
    );
    $filter[] = 'id in (' . implode(',', $idList) . ')';
  }
  $append = '';

  if($filter) {
    $append = 'where ' . implode(' and ', $filter);
  }

  return show('campaign', $append);
}

function campaign_new($opts) {
  //
  // Currently we don't care about radius ... eventually we'll be using
  // spatial systems anyway so let's be simple.
  //
  // Also we eventually need a user system here.
  //
  $missing = missing($opts, ['duration', 'asset', 'lat', 'lng', 'start_time', 'end_time']);
  if($missing) {
    return doError('Missing parameters: ' . implode(', ', $missing));
  }
  if(is_array($opts['asset'])) {
    $opts['asset'] = json_encode($opts['asset']);
  }
  // make sure things aren't arrays when they are passed in here.
  $opts = db_clean($opts);

  // by default active gets set to false
  // which means that we don't consider this 
  foreach(["start_time", "end_time"] as $key) {
    if(is_numeric($opts[$key])) {
      $opts[$key] = db_date($opts[$key]);
    }
  }
  //error_log(json_encode($opts));
  $campaign_id = db_insert(
    'campaign', [
      'active' => 1,//false,
      'asset' => db_string($opts['asset']),
      'duration_seconds' => $opts['duration'],
      'lat' => $opts['lat'],
      'lng' => $opts['lng'],
      'radius' => $opts['radius'],
      'start_time' => $opts['start_time'],
      'end_time' => $opts['end_time']
    ]
  );

  return $campaign_id;
}


function campaign_history($data) {
  $campaign = Get::campaign($data);

  if($campaign) {
    $campaignId = $campaign['id'];
  } else if(isset($data['id'])) {
    $campaign = [];
    $campaignId = $data['id'];
  } else {
    return doError("Campaign not found");
  }  

  $jobList = Many::job([ 'campaign_id' => $campaignId ]);
  $jobMap = mapBy($jobList, 'id');
  $jobHistory = Many::job_history(['job_id in (' . implode(',', array_keys($jobMap)) .')']);

  foreach($jobHistory as $row) {
    $job = $jobMap[$row['job_id']];
    if(!array_key_exists('log', $job)) {
      $job['log'] = [];
    }
    $job['log'][] = $row;
  }

  $campaign['jobs'] = $jobList;
  return $campaign;
}

// This is the first entry point ... I know naming and caching
// are the hardest things.
//
// According to our current flow we may not know the user at the time
// of creating this
function campaign_create($data, $fileList, $user = false) {
  global $DAY, $PLAYTIME;

  error_log("campaign new: " . json_encode($data));
  # This means we do #141
  if(aget($data,'secret') === 'b3nYlMMWTJGNz40K7jR5Hw') {
    $ref_id = db_string(aget($data,'ref_id'));
    $campaign = Get::campaign(['ref_id' => $ref_id]);
    $asset = db_string(json_encode([aget($data, 'asset')]));
    if(!$campaign) {
      $campaign_id = db_insert(
        'campaign', [
          'active' => 1,
          'ref_id' => $ref_id,
          'asset' => $asset,
          'duration_seconds' => 240,
          'lat' => 33.999819, 'lng' => -118.390412, 'radius' => 35000,
          'start_time' => time(),
          'end_time' => time() + $DAY * 7
        ]
      );
    } else {
      db_update('campaign', ['asset' => $asset]);
    }
    return doSuccess(Get::campaign($campaign_id));
  }

  // get the lat/lng radius of the location into the data.
  $data = array_merge(
    ['lat' => 33.999819, 'lng' => -118.390412, 'radius' => 35000],
    ['total' => 999, 'duration' => $PLAYTIME * 300 ],
    ['start_time' => time(), 'end_time' => time() + $DAY * 7, 'asset' => []],
    $data
  );

  foreach($fileList as $file) {
    $data['asset'][] = upload_s3($file);
  }

  $campaign_id = campaign_new($data);
  if($campaign_id) {
    $order = [
      'campaign_id' => $campaign_id,
      'amount' => $data['total'], 
      'status' => db_string('open')
    ];

    if(!empty($data['charge_id'])) {
      $order['charge_id'] = $data['charge_id'];
    }

    if($user) {
      $row['user_id'] = $user['id'];
    }
    $order_id = db_insert('orders', $order);

    db_update('campaign', $campaign_id, ['order_id' => $order_id]);
  }
  return $campaign_id;
}

function campaign_update($data, $fileList, $user = false) {
  $assetList = [];
  $campaign_id = aget($data,'campaign_id|id');
  if(empty($campaign_id)) {
    return doError("Need to set the campaign id");
  }

  if(!$fileList) {
    $obj = [];
    foreach($data as $k => $v) {
      if (in_array($k, ['active','lat','lng','radius'])) {
        $obj[$k] = db_string($v);
      }
    }
    db_update('campaign', $campaign_id, $obj);
  } else {
    if(aget($data, 'append')) {
      $campaign = Get::campaign($campaign_id);
      $assetList = $campaign['asset'];
    }

    foreach($fileList as $file) {
      $assetList[] = upload_s3($file);
    }

    db_update('campaign', $campaign_id, ['asset' => db_string(json_encode($assetList))]);
  }
  return $campaign_id;
}

