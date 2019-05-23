#!/usr/bin/python3
import lib.lib as lib
import arduino.lib as arduino
import sys

import time
import pprint
from datetime import datetime

# Reading interval, so a number such as 0.2
# would take a reading every 0.2 seconds
FREQUENCY = 0.5
PERIOD = 10000
START = time.time()
last_reading = False
ix = 0

def is_significant(totest):
  global last_reading, ix

  if not last_reading or ix % PERIOD == 0:
    last_reading = totest
    return True

  """
    'Arduino_time': time_ms,
    'Backlight': backlight_value,
    'Fan': fan_speed,
    'Temp': temp_c,
    'Current': current,
    'Accel_x': accel_x,
    'Accel_y': accel_y,
    'Accel_z': accel_z,
    'Gyro_x': gyro_x,
    'Gyro_y': gyro_y,
    'Gyro_z': gyro_z,
    'Voltage': v_in,
    'Therm_read': therm_read,
    'Therm_resistance': therm_resistance,
    'Pitch': pitch,
    'Roll': roll,
    'Yaw': yaw
    'latitude
  """
  # We only update our baseline if we say something is significant
  # otherwise we could creep along below a threshold without ever
  # triggering this.
  last_reading = 

while True:
  sensor = arduino.arduino_read()

  # Put data in if we have it
  location = lib.get_gps()
  system_time = datetime.now().replace(microsecond=0).isoformat()

  # We can xref the net_time and system_time for now. Eventually this will
  # probably not be necessary but in the early stages (2019/05/09) this is
  # a sanity check.
  all = {**location, **sensor, 'SystemTime': system_time } 

  if is_significant(all):
  pprint.pprint(all)

  # Now you'd think that we just sleep on the frequency, that'd be wrong.
  # Thanks, try again. Instead we need to use the baseline time from start
  # up multiplied by the counter, then subtracted from the time to account
  # for the skew that is introduced from the sensor reads.
  ix += 1
  naptime = (START + ix * FREQUENCY) - time.time()
  if naptime > 0:
    time.sleep(naptime)

