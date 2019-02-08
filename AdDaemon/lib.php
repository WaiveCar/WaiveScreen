<?
include_once('db.php');

function create_campaign($opts) {
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
  if(!db_update('screen', $payload['id'], [
    'lat' => $payload['lat'],
    'lng' => $payload['lng']
  ])) {
  };

  foreach($payload['work'] as $job) {
    update_job($job['id'], $job['done']);
  }

  
}
