<?
require '../vendor/autoload.php';
use Aws\S3\S3Client;
use Ramsey\Uuid\Uuid;
use Ramsey\Uuid\Exception\UnsatisfiedDependencyException;


include_once('const.php');
include_once('db.php');
include_once('email.php');
include_once('user.php');

$PORT_OFFSET = 7000;
$DAY = 24 * 60 * 60;
$DEFAULT_CAMPAIGN_ID = 30;

// Play time in seconds of one ad.
$PLAYTIME = 7.5;

$DEALMAP = [
  'testdrive' => [ 
    "total" => 100,
    "duration" => $PLAYTIME * 25
  ],
  'shoestring' => [ 
    "total" => 999,
    "duration" => $PLAYTIME * 300
  ],
  'standard' => [ 
    "total" => 2999,
    "duration" => $PLAYTIME * 1050
  ]
]; 

$PLACEMAP = [
  'la' => ['lat' => 33.999819, 'lng' => -118.390412, 'radius' => 35000],
  'hollywood' => ['lat' => 34.093053, 'lng' => -118.343259, 'radius' => 4500],
  'santamonica' => ['lat' => 34.024353, 'lng' => -118.478620, 'radius' => 3000]
];

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
  $res = Many::job([
    'campaign_id' => $campaignId,
    'screen_id' => $screenId,
    'completed_seconds < goal'
  ]);
  //error_log(json_encode([$campaignId,$screenId, $res]));
  return $res;
}

function ping($data) {
  global 
    $VERSION, 
    $DEFAULT_CAMPAIGN_ID,
    $LASTCOMMIT;

  //error_log(json_encode($data));

  if(!isset($data['uid'])) {
    return doError("You need to pass in a UID");
  }

  $uid = $data['uid'];

  $screen = Get::screen(['uid' => $uid]);
  $obj = [ 'last_seen' => 'current_timestamp' ];
  foreach(['imei','version','phone'] as $key) {
    if(isset($data[$key])) {
      $obj[$key] = db_string(aget($data, $key));
    }
  }

  if(!$screen) {
    $screen = create_screen($uid, $obj);
  } else {
    $obj['pings'] = intval($screen['pings']) + 1;
    db_update('screen', $screen['id'], $obj);
  }

  // We return the definition for the default campaign
  // The latest version of the software
  // and the definition of the screen.
  return [
    'version' => $VERSION,
    'version_date' => $LASTCOMMIT,
    'screen' => $screen,
    'default' => Get::campaign($DEFAULT_CAMPAIGN_ID)
  ];
}

function create_job($campaignId, $screenId) {
  $ttl = get_campaign_remaining($campaignId);
  if($ttl < 0) {
    return false;
  }
  $campaign = Get::campaign($campaignId);

  if($campaign) {
    $goal = min($ttl, 60 * 4);

    $job_id = db_insert(
      'job', [
        'campaign_id' => $campaignId,
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
  } else {
    error_log("update job failed: $jobId");
  }

}

// ----
//
// end points
//
// ----

function screens() {
  return show('screen');
}

function update_campaign_completed($id) {
  if(!$id) {
    error_log("Not updating an invalid campaign: $id");
  } else {
    _query("update campaign set completed_seconds=(select sum(completed_seconds) from job where campaign_id=$id) where id=$id");
  }
}
  
function sow($payload) {
  global $LASTCOMMIT, $VERSION;
  $server_response = [ 'res' => true ];

  error_log(json_encode($payload));
  if(isset($payload['uid'])) {
    $uid = $payload['uid'];
  } else {
    return doError("UID needs to be set before continuing");
  }

  $screen = Get::screen(['uid' => $uid]);

  if(!$screen) {
    $screen = create_screen($uid);
  }

  $data = ['last_seen' => 'current_timestamp'];
  if(!empty($payload['lat'])) {
    $data['lat'] = floatval($payload['lat']);
    $data['lng'] = floatval($payload['lng']);
  }

  db_update('screen', db_string($uid), $data);

  $jobList = aget($payload, 'jobs');
  $campaignsToUpdateList = [];

  if($jobList) {
    foreach($jobList as $job) {
      if(!empty($job['id'])) {
        update_job($job['id'], $job['completed_seconds']);
        if(!isset($job['campaign_id'])) {
          error_log(json_encode([]));
          $job = Get::job($job['id']);
          error_log(json_encode($job));
        }
        $campaignsToUpdateList[] = $job['campaign_id'];
      }
    }
  }

  // Make sure we update our grand totals on a per campaign basis when it comes in.
  $uniqueCampaignList = array_unique($campaignsToUpdateList);
  foreach($uniqueCampaignList as $campaign) {
    if($campaign) {
      update_campaign_completed($campaign);
    } else {
      error_log("Couldn't update campaign");
    }
  }
  // error_log(json_encode($uniqueCampaignList));
	
  // Before we assign new jobs we want to make sure that the server
  // is up to date.  We need to make sure we continue to give it 
  // tasks in case the server is failing to upgrade.
  if($screen['version'] != $VERSION) {
    $server_response['task'] = [['upgrade',false]];
  }

  $active = active_campaigns();
  // If we didn't get lat/lng from the sensor then we just any ad
  if(empty($payload['lat'])) {
    $nearby_campaigns = $active;
  } else {
    // right now we are being realllly stupid.
    $nearby_campaigns = array_filter($active, function($campaign) use ($payload) {
      if(isset($payload['lat'])) {
        // under 1.5km
        return distance($campaign, $payload) < ($campaign['radius'] * 100);
      } 
      // essentially this is for debugging
      return true;
    });
  }

  // so if we have existing outstanding jobs with the
  // screen id and campaign then we can just re-use them.
  $job_list = array_map(function($campaign) use ($screen) {
    $jobList = find_unfinished_job($campaign['id'], $screen['id']);
    if(!$jobList) {
      $jobList = [ create_job($campaign['id'], $screen['id']) ];
    }
    foreach($jobList as $job) {
      if(isset($job['id'])) {
        $res = array_merge([
          'job_id' => $job['id'],
          'campaign_id' => $campaign['id'],
          'asset' => $campaign['asset']
        ], $job);
        return $res;
      }
    }
  }, $nearby_campaigns);
  
  $server_response['data'] = $job_list;
  // error_log(json_encode($job_list));
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

function active_campaigns() {
  return show('campaign', 'where active=1 and end_time > current_timestamp and start_time < current_timestamp and completed_seconds < duration_seconds order by active desc, start_time desc');
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


// This is the first entry point ... I know naming and caching
// are the hardest things.
//
// According to our current flow we may not know the user at the time
// of creating this
function campaign_create($data, $fileList, $user = false) {
  global $DEALMAP, $PLACEMAP, $DAY;

  // get the lat/lng radius of the location into the data.
  $data = array_merge($PLACEMAP[$data['location']], $data);
  // and the deal/contract
  $data = array_merge($DEALMAP[$data['option']], $data);

  // currently (2019,10,29) all durations are 1 week.
  $data['start_time'] =  time();
  $data['end_time'] = time() + $DAY * 7;
  $data['asset'] = [];

  foreach($fileList as $file) {
    //$asset = 'fakename.png';
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

// By the time we get here we should already have the asset
// and we should have our monies
function campaign_activate($campaign_id, $data) {
  $payer = $data['payer']['payer_info'];
  $info = $data['paymentInfo'];
  $campaign = Get::campaign($campaign_id);

  $user = Get::user(['email' => $payer['email']]);
  if(!$user) {
    $user_id = User::create([
      'name' => "${payer['first_name']} ${payer['last_name']}",
      'email' => $payer['email'],
      'phone' => $payer['phone']
    ]);
    $user = Get::user($user_id);
  }

  $campaign = Get::campaign($campaign_id);
  db_update('orders', $campaign['order_id'], [
    'status' => 'completed',
    // is this different?
    'charge_id' => $info['orderID']
  ]);

  db_update('campaign', $campaign_id, [
    'active' => true,
    'user_id' => $user['id']
  ]);
}
