CREATE TABLE IF NOT EXISTS assets(
  id integer primary key asc, 
  path text
);

CREATE TABLE IF NOT EXISTS purchases(
  id integer primary key, 
  quote_id text, 
  service text, 
  asset_id text, 
  order_id text, 
  extra_days integer, 
  extra_minutes_per_day integer, 
  total_price float, 
  days integer, 
  price_per_day float, 
  per_minute_per_day float, 
  start_date text, 
  end_date text, 
  paid bool, 
  email text, 
  phone text, 
  first_name text, 
  last_name text
);

create table if not exists screen(
 id integer primary key autoincrement,
 uid text not null,
 lat integer,
 lng integer,
 car text default null,
 port integer,
 first_seen datetime,
 last_seen datetime
);

create table if not exists campaign(
 id integer primary key autoincrement,
 asset text not null,
 duration_seconds integer,
 start_time datetime,
 end_time datetime
);

create table if not exists job(
 job_id integer primary key autoincrement,
 campaign_id integer,
 screen_id integer,
 start_time datetime,
 end_time datetime,
 duration_seconds integer,
 completion_seconds integer,
 last_update datetime
);
