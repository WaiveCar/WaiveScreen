#!/usr/bin/python3
import lib.lib as lib
import arduino.lib as arduino
import logging
import sys

import time
import pprint
from datetime import datetime

# Reading interval, so a number such as 0.2
# would take a reading every 0.2 seconds
FREQUENCY = 0.05

# If all the sensor deltas reach this percentage
# (multiplied by 100) from the baseline, then we
# call this a "significant event" and store it.
AGGREGATE_THRESHOLD = 10

# This is the Heartbeat in seconds - we do
# a reading in this frequency (in seconds) to state that
# we're still alive.
HB = 30

PERIOD = HB / FREQUENCY
START = time.time()

last_reading = False
ix = 0
ix_hb = 0
first = True

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger(__name__)
arduino.set_log(logger)

def is_significant(totest):
  global last_reading, ix, ix_hb

  if not last_reading or ix % PERIOD == 0:
    if not last_reading:
      pass
    else:
      ix_hb += 1
      pass
    last_reading = totest
    return True

  # We only update our baseline if we say something is significant
  # otherwise we could creep along below a threshold without ever
  # triggering this.
  deltaMap = {
    'Temp': 5,
    'Accel': [200, 200, 300],
    'Gyro': [30, 30, 30],
    'Pitch': 0.8,
    'Roll': 0.8,
    'Yaw': 0.9,
    'Latitude': 0.01,
    'Longitude': 0.01
  }

  ttl = 0
  for k,v in deltaMap.items():
    if k in last_reading:
      if type(v) is list:
        for i in range(len(v)):
          diff = abs(last_reading[k][i] - totest[k][i])
          if diff > v[i]:
            ttl += (diff / v[i]) - 1

      else:
        diff = abs(last_reading[k] - totest[k])
        if diff > v:
          ttl += (diff / v) - 1

  if ttl > AGGREGATE_THRESHOLD:
    last_reading = totest
    return True


while True:
  sensor = arduino.arduino_read()
  if first:
    logging.info("Got first arduino read")

  # Put data in if we have it
  location = {} if lib.NOMODEM else lib.get_gps()

  # We can xref the net_time and system_time for now. Eventually this will
  # probably not be necessary but in the early stages (2019/05/09) this is
  # a sanity check.
  all = {**location, **sensor} 

  if first:
    logging.info("Success, Main Loop")
    first = False

  if is_significant(all):
    lib.sensor_store(all)

  # If we need to go into/get out of a low power mode
  arduino.pm_if_needed(sensor)

  # Now you'd think that we just sleep on the frequency, that'd be wrong.
  # Thanks, try again. Instead we need to use the baseline time from start
  # up multiplied by the counter, then subtracted from the time to account
  # for the skew that is introduced from the sensor reads.
  ix += 1
  naptime = (START + ix * FREQUENCY) - time.time()
  if naptime > 0:
    time.sleep(naptime)

  arduino.clear()
