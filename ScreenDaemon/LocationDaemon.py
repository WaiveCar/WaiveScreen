#!/usr/bin/python3 -u
#
# We use '-u' so stdout/stderr are unbuffered, for logging purposes.
# Despite the name, we are not running as a daemon.  We will rely on systemd to manage the process.

import time
import logging
from lib.wifi_location import wifi_location, wifi_scan_shutdown
from lib.lib import get_gps
import lib.db as db

logging.basicConfig(level=logging.DEBUG)

SLEEP_TIME = 10
MAX_WIFI_INTERVAL = 60 #0
_current_location_source = None
_last_wifi_location_request_time = 0.0

def get_location_from_wifi():
  l = wifi_location()
  return l

def stop_wifi_location_service():
  wifi_scan_shutdown()

def get_location_from_gps():
  l = get_gps()
  return l

def save_location(location):
  logging.debug("Saving location: lat:{} lng:{} accuracy:{}".format(location['Lat'], location['Lng'], location.get('accuracy')))
  db.kv_set('lat', location['Lat'])
  db.kv_set('lng', location['Lng'])
  db.kv_set('location_accuracy', location.get('accuracy', ''))
  db.kv_set('location_source', _current_location_source)

def location_loop():
  global _current_location_source, _last_wifi_location_request_time
  while True:
    location = False
    try:
      location = get_location_from_gps()
      if location:
        if _current_location_source == 'wifi':
          stop_wifi_location_service()
        _current_location_source = 'gps'
        save_location(location)
      elif time.time() - _last_wifi_location_request_time >= MAX_WIFI_INTERVAL:
        location = get_location_from_wifi()
        _last_wifi_location_request_time = time.time()
        _current_location_source = 'wifi'
        if location:
          save_location(location)
        else:
          logging.info('Unable to determine our location.  GPS and Wifi failed.')
    except Exception as ex:
      logging.error('Error in main loop: {}'.format(ex))

    time.sleep(SLEEP_TIME)


#if __name__ == '__main__':
#  location_loop()

