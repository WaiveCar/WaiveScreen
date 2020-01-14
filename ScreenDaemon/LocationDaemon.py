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
from lib.lib import get_gps, update_gps_xtra_data, get_gpgga_dict, DEBUG, set_logger, system_uptime, get_uuid, post, save_location, get_location_from_gps, save_location, location_source 
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
      location = get_location_from_gps(SLEEP_TIME)
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

