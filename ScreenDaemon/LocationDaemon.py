#!/usr/bin/python3 -u
#
# We use '-u' so stdout/stderr are unbuffered, for logging purposes.
# Despite the name, we are not running as a daemon.  We will rely on systemd to manage the process.

import time
import json
import logging
from lib.wifi_location import wifi_location, wifi_scan_shutdown, wifi_last_submission
from lib.lib import get_gps, update_gps_xtra_data, get_gpgga_dict
import lib.db as db

logging.basicConfig(level=logging.DEBUG) #TODO remove this after testing

# location_loop sleep time - applies to GPS polling
SLEEP_TIME = 10
# extra time to wait if we're using the wifi location service
# We don't want to spam MLS and hit their 100,000 daily request limit
MIN_WIFI_INTERVAL = 60 #TODO change back to 600 after testing

def get_location_from_wifi():
  l = wifi_location()
  if float(l.get('accuracy', 100000)) <= 500.0:
    logging.debug('Wifi Location Response: {}'.format(l))
    return l
  else:
    logging.debug('Ignoring wifi_location with accuracy over 500: {}'.format(l))
    return False

def stop_wifi_location_service():
  wifi_scan_shutdown()

def get_location_from_gps():
  l = get_gps(True)
  if float(time.strftime('%H%M%S')) - float(l.get('Utc', 0)) <= SLEEP_TIME:
    logging.debug('GPS Location Response: {}'.format(l))
    return l
  else:
    logging.debug('Ignoring get_gps with stale UTC: {}'.format(l))
    return False

def save_location(location):
  # Save current location info to the database
  logging.info("Saving location: lat:{} lng:{} accuracy:{} utc:{} source:{}".format(location['Lat'], location['Lng'], location.get('accuracy'), location.get('Utc'), location_source()))
  db.kv_set('lat', location['Lat'])
  db.kv_set('lng', location['Lng'])
  db.kv_set('location_accuracy', location.get('accuracy', ''))
  db.kv_set('gps_gpgga', json.dumps(get_gpgga_dict(location.get('Nmea', ''))))

def location_source(set_it=False):
  if set_it:
    db.kv_set('location_source', set_it)
  else:
    return db.kv_get('location_source')

def system_uptime():
  with open('/proc/uptime', 'r') as f:
    return float(f.readline().split(' ')[0])

def location_loop():
  # We prefer the location from the GPS.  If that fails,
  # we try and determine our location based on a Wifi scan.
  failure_count = 0
  logging.info('LocationDaemon.py starting...')
  sys_uptime = system_uptime()
  if sys_uptime < 60:
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

