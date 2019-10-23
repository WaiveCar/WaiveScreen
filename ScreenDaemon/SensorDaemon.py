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

_autobright_set = False
last_reading = False
ix = 0
ix_hb = 0
first = True
avg = 0
_arduinoConnectionDown = False

if lib.DEBUG:
  lib.set_logger(sys.stderr)
else:
  #lib.set_logger(sys.stderr)
  lib.set_logger('{}/sensordaemon.log'.format(lib.LOG))

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
    logging.debug("\n".join(buffer))
    last_reading = totest
    return True


run = db.kv_get('runcount')
window = []

# f = open ("/home/adorno/charge-record.txt", "a+")

if lib.SANITYCHECK:
  sys.exit(0)

n = 0
while True:
  try:
    sensor = arduino.arduino_read()

    if not sensor:
      raise Exception('arduino_read() returned no data')

    elif _arduinoConnectionDown:
      _arduinoConnectionDown = False
      # We could wake the screen up here, but I'm assuming the pm_if_needed call below will do the right thing
      logging.info('Connection to arduino reestablished')

    n += 1
    if n % 8 == 0:
      logging.info("voltage {:.3f} current {:.3f} avg: {:.3f}".format(sensor['Voltage'], sensor['Current'], avg))

    if first:
      # Tell the arduino that we are live.
      arduino.ping()

      logging.info("Got first arduino read")
      first = False
      db.kv_set('arduino_seen', 1)
      db.kv_set('arduino_version', sensor.get('Sw_version'))

    # Put data in if we have it
    location = lib.get_latlng()

    try:
      if location and not _autobright_set:
        _autobright_set = True
        arduino.set_autobright()

    except:
      pass

    all = {**location, **sensor, 'run': run}


    window.append(all.get('Voltage'))
    if len(window) > WINDOW_SIZE * 1.2:
      window = window[-WINDOW_SIZE:]

    try:
      avg = float(sum(window)) / len(window)

    except:
      avg = 0

    if is_significant(all):
      lib.sensor_store(all)

    # If we need to go into/get out of a low power mode
    # We also need to make sure that we are looking at a nice
    # window of time. Let's not make it the window_size just
    # in case our tidiness algorithm breaks.
    #if sensor and len(window) > WINDOW_SIZE * 0.8 and lib.BRANCH != 'release':
    #  arduino.pm_if_needed(avg, all.get('Voltage'))

    # Now you'd think that we just sleep on the frequency, that'd be wrong.
    # Thanks, try again. Instead we need to use the baseline time from start
    # up multiplied by the counter, then subtracted from the time to account
    # for the skew that is introduced from the sensor reads.
    ix += 1
    naptime = (START + ix * FREQUENCY) - time.time()
    if naptime > 0:
      time.sleep(naptime)

    arduino.clear()

  # We are unable to communicate with the arduino.  We will assume that the screen is on
  # at max brightness and shutdown the screen immediately.
  except Exception as ex:
    if not _arduinoConnectionDown:
      logging.error('Arduino communication down: {}'.format(ex))
      _arduinoConnectionDown = True
      # TODO Add more logic to guess the state of the car before we lost contact.
      arduino_seen = db.kv_get('arduino_seen')
      if arduino_seen is not None:
        logging.info('Arduino disconnected: Putting the screen to sleep')
        try:
          arduino.do_sleep()
        except:
          # The call should turn off the display but fail trying to turn off the backlight.  That's okay.
          pass
      else:
        logging.info('Arduino has never been detected: Leaving the screen on')
      # if _arduino isn't set to false, we won't reconnect
      arduino.arduino_disconnect()
    time.sleep(1)

