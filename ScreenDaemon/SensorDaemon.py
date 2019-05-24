#!/usr/bin/python3
import lib.lib as lib
import arduino.lib as arduino
import sys

import time
import pprint
from datetime import datetime

# Reading interval, so a number such as 0.2
# would take a reading every 0.2 seconds
FREQUENCY = 0.05

# This is the Heartbeat in seconds - we do
# a reading in this frequency (in seconds) to state that
# we're still alive.
HB = 30

PERIOD = HB / FREQUENCY
START = time.time()
last_reading = False
ix = 0
ix_hb = 0

def is_significant(totest):
  global last_reading, ix, ix_hb

  if not last_reading or ix % PERIOD == 0:
    if not last_reading:
      print("First reading")
    else:
      ix_hb += 1
      print("HB {}".format(ix_hb))
    last_reading = totest
    return True

  # We only update our baseline if we say something is significant
  # otherwise we could creep along below a threshold without ever
  # triggering this.
  deltaMap = {
    'Temp': 5,
    'Accel_x': 200,
    'Accel_y': 200,
    'Accel_z': 300,
    'Gyro_x': 30,
    'Gyro_y': 30,
    'Gyro_z': 30,
    'Pitch': 0.8,
    'Roll': 0.8,
    'Yaw': 0.9,
    'Latitude': 0.01,
    'Longitude': 0.01
  }

  ttl = 0
  for k,v in deltaMap.items():
    if k in last_reading:
      diff = abs(last_reading[k] - totest[k])
      if diff > v:
        ttl += (diff / v) - 1
        #print("{:10s}:{:5.2f} reached: {}".format(k,v, diff))

  min = 10
  if ttl > min:
    print("{:10s}:{:5.2f} reached: {}".format('percent', min, ttl))
    last_reading = totest
    return True

  #print("skip")

while True:
  sensor = arduino.arduino_read()

  # Put data in if we have it
  if lib.NOMODEM:
    location = {}
  else:
    location = lib.get_gps()

  system_time = datetime.now().replace(microsecond=0).isoformat()

  # We can xref the net_time and system_time for now. Eventually this will
  # probably not be necessary but in the early stages (2019/05/09) this is
  # a sanity check.
  all = {**location, **sensor, 'SystemTime': system_time } 

  if is_significant(all):
    pass
    #pprint.pprint(all)

  # Now you'd think that we just sleep on the frequency, that'd be wrong.
  # Thanks, try again. Instead we need to use the baseline time from start
  # up multiplied by the counter, then subtracted from the time to account
  # for the skew that is introduced from the sensor reads.
  ix += 1
  naptime = (START + ix * FREQUENCY) - time.time()
  if naptime > 0:
    time.sleep(naptime)

  arduino.arduino.reset_input_buffer()
