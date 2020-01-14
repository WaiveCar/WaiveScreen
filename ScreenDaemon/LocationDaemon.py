#!/usr/bin/python3 -u
#
# We use '-u' so stdout/stderr are unbuffered, for logging purposes.
# Despite the name, we are not running as a daemon.  We will rely on systemd to manage the process.

import json
import logging
import math
import sys
import time
from lib.wifi_location import wifi_location, wifi_scan_shutdown, wifi_last_submission
from lib.lib import get_gps, update_gps_xtra_data, get_gpgga_dict, DEBUG, set_logger, system_uptime, get_uuid, post
import lib.db as db

if DEBUG:
  set_logger(sys.stderr)
else:
  set_logger('/var/log/screen/locationdaemon.log')

# location_loop sleep time - applies to GPS polling
SLEEP_TIME = 5

# extra time to wait if we're using the wifi location service
# We don't want to spam MLS and hit their 100,000 daily request limit
if DEBUG:
  MIN_WIFI_INTERVAL = 60
else:
  MIN_WIFI_INTERVAL = 300

class Haversine:
  """
  use the haversine class to calculate the distance between
  two lon/lat coordnate pairs.
  output distance available in kilometers, meters, miles, and feet.
  example usage: Haversine([lon1,lat1],[lon2,lat2]).feet

  Source: https://github.com/nathanrooy/spatial-analysis/blob/master/haversine.py
  """
  def __init__(self,coord1,coord2):
    lon1,lat1=coord1
    lon2,lat2=coord2

    R=6371000                               # radius of Earth in meters
    phi_1=math.radians(lat1)
    phi_2=math.radians(lat2)

    delta_phi=math.radians(lat2-lat1)
    delta_lambda=math.radians(lon2-lon1)

    a=math.sin(delta_phi/2.0)**2+\
       math.cos(phi_1)*math.cos(phi_2)*\
       math.sin(delta_lambda/2.0)**2
    c=2*math.atan2(math.sqrt(a),math.sqrt(1-a))

    self.meters=R*c                         # output distance in meters
    self.km=self.meters/1000.0              # output distance in kilometers
    self.miles=self.meters*0.000621371      # output distance in miles
    self.feet=self.miles*5280               # output distance in feet


def get_location_from_wifi():
  l = wifi_location()
  if float(l.get('accuracy', 100000)) <= 500.0:
    logging.debug('Wifi Location Response: {}'.format(l))
    return l
  else:
    logging.warning('Ignoring wifi_location with accuracy over 500: {}'.format(l))
    return False

def stop_wifi_location_service():
  wifi_scan_shutdown()

def get_location_from_gps():
  l = get_gps(True)
  utc = l.get('Utc')
  age = l.get('age')
  accuracy = l.get('accuracy')
  if utc is None:
    logging.warning('GPS location has no UTC timestamp: {}'.format(l))
    return False
  elif accuracy is None:
    logging.warning('GPS location has no accuracy: {}'.format(l))
    return False
  elif float(accuracy) > 500.0:
    logging.warning('Ignoring GPS location with accuracy over 500: {}'.format(l))
    return False
  elif age > SLEEP_TIME:
    logging.warning('Ignoring get_gps with stale UTC: {}'.format(l))
    return False
  else:
    logging.debug('GPS Location Response: {}'.format(l))
    return l

def sanity_check(location):
  last_location_time = db.kv_get('location_time', use_cache=True)
  if last_location_time is None:
    logging.warning('Last location time not saved in kv db (This should only happen ONCE)')
    return True
  time_diff = time.time() - float(last_location_time)
  if time_diff > 60 * 10:  # More than 10 minutes
    logging.info('Last location older than 10 minutes.')
    return True
  last_lat = db.kv_get('Lat', use_cache=True)
  last_lng = db.kv_get('Lng', use_cache=True)
  if last_lat is None or last_lng is None:
    logging.warning('Last location not in kv db. (This should only happen ONCE)')
    return True
  dist = Haversine([float(last_lng), float(last_lat)], [float(location['Lng']), float(location['Lat'])])
  miles_per_second = dist.miles / time_diff
  logging.debug('Calculated speed: {} miles/second, {} miles/hour'.format(miles_per_second, miles_per_second * (60 * 60)))
  logging.debug('last_lat:{} last_lng:{} lat:{} lng:{} dist.meters:{} dist.miles:{} time_diff:{}'.format(float(last_lat), \
                float(last_lng), float(location['Lat']), float(location['Lng']), dist.meters, dist.miles, time_diff))
  if miles_per_second > 150.0 / (60 * 60):  # Faster than 150 mph
    return False
  else:
    return True

def save_location(location):
  """ Save current location info to the database """
  db.insert( 'location', {
      'lat': location['Lat'],
      'lng': location['Lng'],
      'accuracy': location.get('accuracy', ''),
      'speed': location.get('speed', ''),
      'heading': location.get('heading', ''),
      'source': location_source() })
  if not sanity_check(location):
    logging.warning('New location failed sanity_check: {}'.format(location))
    return False
  logging.debug("Saving location: lat:{} lng:{} accuracy:{} utc:{} source:{}".format(location['Lat'], location['Lng'], location.get('accuracy'), location.get('Utc'), location_source()))
  db.kv_set('Lat', location['Lat'])
  db.kv_set('Lng', location['Lng'])
  db.kv_set('location_time', int(time.time()))
  db.kv_set('location_accuracy', location.get('accuracy', ''))
  db.kv_set('gps_gpgga', json.dumps(get_gpgga_dict(location.get('Nmea', ''))))
  if db.kv_get('send_location') is not None:
    send_location(location)

def location_source(set_it=False):
  if set_it:
    db.kv_set('location_source', set_it)
  else:
    return db.kv_get('location_source')

def send_location(location):
  payload = { 'uid': get_uuid(), 'lat': location['Lat'], 'lng': location['Lng'] }
  post('eagerlocation', payload)


def location_loop():
  """
  We prefer the location from the GPS.  If that fails,
  we try and determine our location based on a Wifi scan.
  """
  failure_count = 0
  logging.info('LocationDaemon.py starting...')
  sys_uptime = system_uptime()
  if sys_uptime < 60:
    #  Allow time for modem, network and gps to become active
    time.sleep(60.0 - sys_uptime)
    update_gps_xtra_data()
  while failure_count < 60:
    location = False
    try:
      location = get_location_from_gps()
      if location:
        if location_source() != 'gps':
          stop_wifi_location_service()
        location_source('gps')
        save_location(location)
      elif time.time() - wifi_last_submission() >= MIN_WIFI_INTERVAL:
        location = get_location_from_wifi()
        if location:
          location_source('wifi')
          save_location(location)
        else:
          failure_count += 1
          location_source('none')
          logging.warning('Unable to determine our location.  GPS and Wifi failed.')
    except Exception as ex:
      failure_count += 1
      logging.error('Error in location_loop: {}'.format(ex))

    time.sleep(SLEEP_TIME)


if __name__ == '__main__':
  location_loop()

