<?
include_once('db.php');

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

function create_campaign($opts) {
}

function active_campaigns() {
  return (getDb())->query('select * from campaigns where end_time < date("now") and start_time > date("now")');
}


function create_job($campaignId, $screenId) {
  $ttl = get_campaign_remaining($campaignId);
  $goal_seconds = min($ttl, 60 * 4);

  $job_id = db_insert(
    'job', [
      'campaign_id' => $campaignId,
      'screen_id' => $screenId,
      'job_start' => 'date("now")',
      'last_update' => 'date("now")',
      'goal_seconds' => $goal_seconds
    ]
  );

  return get_job($job_id);
}

function update_job($jobId, $completion_seconds) {
  return db_update('job', $jobId, [
    'completion_seconds' => $completion_seconds,
    'job_end' => 'date("now")'
  ]);
}

function sow($payload) {
  db_update('screen', $payload['id'], [
    'lat' => $payload['lat'],
    'lng' => $payload['lng']
  ]);

  foreach($payload['work'] as $job) {
    update_job($job['id'], $job['done']);
  }

  // right now we are being realllly stupid.
  $nearby_campaigns = array_filter(active_campaigns(), function($campaign) uses ($payload) {
    // under 1.5km
    return distance($campaign, $payload) < 1500;
  });

  $job_list = array_map(function($row) uses ($payload) {
    $job = create_job($row['id'], $payload['id']);

    return array_merge([
      'jobid' => $job['id'],
      'campaignid' => $row['id'],
      'asset' => $row['asset']
    ], $job);
  }, $nearby_campaigns);
  
  return [
    'res' => true,
    'jobs' => $job_list
  ];
}
