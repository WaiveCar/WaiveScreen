<?
include_once('db.php');
include_once('email.php');
include_once('user.php');

$PORT_OFFSET = 7000;
$DAY = 24 * 60 * 60;

function jemit($what) {
  echo json_encode($what);
  exit;
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

function campaigns($clause = '') {
  return db_all("select * from campaign $clause");
}
function active_campaigns() {
  return campaigns('where end_time > current_timestamp and start_time < current_timestamp');
}

function create_screen($uid) {
  global $PORT_OFFSET;
  // we need to get the next available port number
  $nextport = intval((getDb())->querySingle('select max(port) from screen')) + 1;

  $screen_id = db_insert(
    'screen', [
      'uid' => db_string($uid),
      'port' => $nextport,
      'first_seen' => 'current_timestamp',
      'last_seen' => 'current_timestamp',
    ]
  );

  return Get::screen($screen_id);
}

function create_job($campaignId, $screenId) {
  $ttl = get_campaign_remaining($campaignId);

  $goal = min($ttl, 60 * 4);

  $job_id = db_insert(
    'job', [
      'campaign_id' => $campaignId,
      'screen_id' => $screenId,
      'job_start' => 'current_timestamp',
      'last_update' => 'current_timestamp',
      'goal' => $goal
    ]
  );

  return Get::job($job_id);
}

function update_job($jobId, $completion_seconds) {
  return db_update('job', $jobId, [
    'completion_seconds' => $completion_seconds,
    'job_end' => 'current_timestamp'
  ]);
}

// ----
//
// end points
//
// ----

function sow($payload) {
  if(isset($payload['uid'])) {
    $uid = $payload['uid'];
  } else {
    return doError("UID needs to be set before continuing");
  }

  $screen = Get::screen(['uid' => $uid]);

  if(!$screen) {
    $screen = create_screen($uid);
  }

  db_update('screen', db_string($uid), [
    'lat' => $payload['lat'],
    'lng' => $payload['lng'],
    'last_seen' => 'current_timestamp'
  ]);

  if(array_key_exists('jobs', $payload) && is_array($payload['jobs'])) {
    foreach($payload['jobs'] as $job) {
      update_job($job['id'], $job['done']);
    }
  }

  // right now we are being realllly stupid.
  $nearby_campaigns = array_filter(active_campaigns(), function($campaign) use ($payload) {
    // under 1.5km
    return distance($campaign, $payload) < 1500;
  });

  $job_list = array_map(function($row) use ($screen) {
    $job = create_job($row['id'], $screen['id']);
    if($job) {

      $res = array_merge([
        'jobid' => $job['id'],
        'campaignid' => $row['id'],
        'asset' => $row['asset']
      ], $job);
      return $res;
    }
  }, $nearby_campaigns);
  
  return [
    'res' => true,
    'data' => $job_list
  ];
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


function create_campaign($opts) {
  //
  // Currently we don't care about radius ... eventually we'll be using
  // spatial systems anyway so let's be simple.
  //
  // Also we eventually need a user system here.
  //
  $missing = missing($opts, ['duration', 'asset', 'lat', 'lng', 'start_time', 'end_time']);
  if($missing) {
    return doError("Missing parameters: " . implode(', ', $missing));
  }
  $opts = db_clean($opts);

  $campaign_id = db_insert(
    'campaign', [
      'asset' => db_string($opts['asset']),
      'duration_seconds' => $opts['duration'],
      'lat' => $opts['lat'],
      'lng' => $opts['lng'],
      'start_time' => db_string($opts['start_time']),
      'end_time' => db_string($opts['end_time'])
    ]
  );
  return [
    'res' => true, 
    'data' => $campaign_id
  ];
}

