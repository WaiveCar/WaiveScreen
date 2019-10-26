#!/usr/bin/python3
import lib.lib as lib
import lib.db as db
import lib.arduino as arduino
import logging
import sys

import csv
import os
import shutil
import time
import pprint
from datetime import datetime

# Reading interval, so a number such as 0.2
# would take a reading every 0.2 seconds
# We sample 6dof data at 25Hz
FREQUENCY = 0.04 if 'FREQUENCY' not in os.environ else os.environ['FREQUENCY']
WINDOW_SIZE = int(12.0 / FREQUENCY)

# If all the sensor deltas reach this percentage
# (multiplied by 100) from the baseline, then we
# call this a "significant event" and store it.
AGGREGATE_THRESHOLD = 10

START = time.time()

# The frequency at which to sample the Power/Temp sensors in seconds
POWERTEMP_FREQ = 2.0
POWERTEMP_PERIOD = POWERTEMP_FREQ / FREQUENCY

# The frequency at which to check for commands to send to the Arduino
CMD_QUEUE_FREQ = 1.0
CMD_QUEUE_PERIOD = CMD_QUEUE_FREQ / FREQUENCY

_autobright_set = False
ix = 0
first = True
avg = 0
_arduinoConnectionDown = False

SIXDOF_FIELDS = ['Time', 'Accel_x', 'Accel_y', 'Accel_z', 'Gyro_x', 'Gyro_y', 'Gyro_z', 'Pitch', 'Roll', 'Yaw']
POWERTEMP_FIELDS = ['Time', 'Voltage', 'Current', 'Temp', 'Fan', 'Light', 'DPMS1', 'DPMS2']
FIELDS_TO_ROUND = {'Time': 2, 'Pitch': 3, 'Roll': 3, 'Yaw': 3, 'Voltage': 2, 'Current': 2, 'Temp': 2}

if lib.DEBUG:
  lib.set_logger(sys.stderr)
else:
  #lib.set_logger(sys.stderr)
  lib.set_logger('{}/sensordaemon.log'.format(lib.LOG))


def open_csv_writer(filename, fieldnames):
  """ Return a csv.DictWriter for the given filename.  If the
  file is empty, we write the header row at the top.  If the file
  already exists, we trim the end of any incomplete writes. """
  csvfile = open(filename, 'a+', buffering=1, newline='')
  shutil.chown(filename, lib.USER, lib.USER)
  file_pos = csvfile.tell()
  if file_pos > 0:
    # We check the end of existing files for incomplete lines or binary junk
    while file_pos > 0 and csvfile.read(1) != '\n':
      file_pos -= 1
      csvfile.seek(file_pos)
    csvfile.truncate(file_pos + 1)
    csvfile.flush()
  writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
  if file_pos == 0:
    writer.writeheader()
  return writer

def round_fields(d):
  for k, v in FIELDS_TO_ROUND.items():
    d[k] = round(d.get(k, 0), v)


run = db.kv_get('runcount')
window = []

# f = open ("/home/adorno/charge-record.txt", "a+")

if lib.SANITYCHECK:
  sys.exit(0)

sixdof_writer = open_csv_writer('{}/sixdof.csv'.format(lib.LOG), SIXDOF_FIELDS)
powertemp_writer = open_csv_writer('{}/powertemp.csv'.format(lib.LOG), POWERTEMP_FIELDS)

while True:
  try:
    sensor = arduino.arduino_read()

    if not sensor:
      raise Exception('arduino_read() returned no data')

    elif _arduinoConnectionDown:
      _arduinoConnectionDown = False
      logging.info('Connection to arduino reestablished')
      arduino.do_awake()


    if first:
      # Tell the arduino that we are live.
      arduino.send_arduino_ping()

      logging.info("Got first arduino read")
      first = False
      db.kv_set('arduino_seen', 1)
      db.kv_set('arduino_version', sensor.get('Sw_version'))

    if not _autobright_set:
      location = lib.get_latlng()
      try:
        if location:
          _autobright_set = True
          arduino.set_autobright()
      except:
        pass

    all = {**sensor, 'run': run, 'Time': time.time()}


    window.append(all.get('Voltage'))
    if len(window) > WINDOW_SIZE * 1.2:
      window = window[-WINDOW_SIZE:]

    try:
      avg = float(sum(window)) / len(window)

    except:
      avg = 0


    # If we need to go into/get out of a low power mode
    # We also need to make sure that we are looking at a nice
    # window of time. Let's not make it the window_size just
    # in case our tidiness algorithm breaks.

    #if sensor and len(window) > WINDOW_SIZE * 0.8 and lib.BRANCH != 'release':
    #  arduino.pm_if_needed(avg, all.get('Voltage'))

    round_fields(all)
    sixdof_writer.writerow(all)
    if ix % POWERTEMP_PERIOD == 0:
      all['DPMS1'], all['DPMS2'] = lib.get_dpms_state()
      powertemp_writer.writerow(all)

    # Check for commands to send to Arduino and process them.
    if ix % CMD_QUEUE_PERIOD == 0:
      arduino.process_arduino_queue()

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

