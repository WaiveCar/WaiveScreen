create table screen(
  id integer primary key autoincrement, 
  uid text not null, 
  lat integer,
  lng integer,
  license text default null, 
  port integer, 
  first_seen datetime, 
  last_seen datetime
);

create table campaign(
  id integer primary key autoincrement,
  asset text not null,
  duration_seconds integer,
  start_time datetime,
  end_time datetime
)

create table job(
  job_id integer primary key autoincrement,
  campaign_id integer,
  screen_id integer,
  start_time datetime,
  end_time datetime,
  duration_seconds integer,
  completion_seconds integer,
  last_update datetime
)

  asset: string
  duration: seconds (float)
  startTime: utc
  endTime: utc
  now: utc
  completion: 0-1 (float)
