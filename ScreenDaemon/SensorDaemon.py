#!/usr/bin/python3
import lib.lib as lib
import lib.db as db
import lib.arduino as arduino
import logging
import sys

import os
import time
import pprint
from datetime import datetime

# Reading interval, so a number such as 0.2
# would take a reading every 0.2 seconds

FREQUENCY = 0.1 if 'FREQUENCY' not in os.environ else os.environ['FREQUENCY']
WINDOW_SIZE = int(12.0 / FREQUENCY)

# If all the sensor deltas reach this percentage
# (multiplied by 100) from the baseline, then we
# call this a "significant event" and store it.
AGGREGATE_THRESHOLD = 10

# This is the Heartbeat in seconds - we do
# a reading in this frequency (in seconds) to state that
# we're still alive.
HB = 120

PERIOD = HB / FREQUENCY
START = time.time()

last_reading = False
ix = 0
ix_hb = 0
first = True

format = '%(asctime)-15s %(message)s'
level = logging.DEBUG if os.getenv('DEBUG') else logging.INFO
logpath = '/var/log/screen/sensordaemon.log'

try:
  logging.basicConfig(filename=logpath, format=format, level=level)

except:
  os.system('/usr/bin/sudo chmod 0666 {}'.format(logpath))
  logging.basicConfig(filename=logpath, format=format, level=level)

logger = logging.getLogger()
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
    'Temp': 2,
    'Accel_x': 1000,
    'Accel_y': 1000,
    'Accel_z': 1000,
    'Gyro_x': 150, 
    'Gyro_y': 200, 
    'Gyro_z': 150, 
    'Pitch': 3.0,
    'Roll': 3.0,
    'Yaw': 4.5,
    'Voltage': 0.05,
    'Current': 0.05,
    'Lat': 0.01,
    'Lng': 0.01
  }

  ttl = 0
  isFirst = True
  buffer = []
  for k,v in deltaMap.items():
    if k not in last_reading:
      continue

    if k in totest:
      diff = abs(last_reading[k] - totest[k])
      if diff > v:
        if isFirst:
            buffer.append('-----')
            isFirst = False
        ttl += (diff / v) - 1
        buffer.append("{:10} {:3.4f} {:.4f} {:4.4f}->{:4.4f}".format(k, ttl, diff/v, last_reading[k], totest[k]))

  if ttl > AGGREGATE_THRESHOLD:
    logging.info("\n".join(buffer))
    last_reading = totest
    return True


run = db.kv_get('runcount')
window = []
f = open ("/home/adorno/charge-record.txt", "a+")

while True:
  sensor = arduino.arduino_read()
  if first:
    logging.info("Got first arduino read")

  # Put data in if we have it
  location = {} if lib.NOMODEM else lib.get_gps()

  # We can xref the net_time and system_time for now. Eventually this will
  # probably not be necessary but in the early stages (2019/05/09) this is
  # a sanity check.
  all = {**location, **sensor, 'run': run} 

  if first:
    logging.debug("Success, Main Loop")
    first = False

  window.append(all.get('Voltage'))
  if len(window) > WINDOW_SIZE * 1.2:
    window = window[-WINDOW_SIZE:]
  avg = float(sum(window)) / len(window)

  if is_significant(all):
    lib.sensor_store(all)

  ln="{} {} {} {} {} \n".format(time.strftime("%H:%M:%S"), all['Voltage'], all['Current'], avg, db.sess_get('power'))

  f.write(ln)
  if ix % 10 == 0:
    f.flush()

  # If we need to go into/get out of a low power mode
  if sensor:
    arduino.pm_if_needed(avg)

  # Now you'd think that we just sleep on the frequency, that'd be wrong.
  # Thanks, try again. Instead we need to use the baseline time from start
  # up multiplied by the counter, then subtracted from the time to account
  # for the skew that is introduced from the sensor reads.
  ix += 1
  naptime = (START + ix * FREQUENCY) - time.time()
  if naptime > 0:
    time.sleep(naptime)

  arduino.clear()
