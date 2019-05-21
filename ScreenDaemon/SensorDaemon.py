#!/usr/bin/python3
import lib.lib as lib
import arduino.lib as arduino
import sys

import time
import pprint
from datetime import datetime

while True:
  sensor = arduino.arduino_read()

  # Put data in if we have it
  location = lib.get_gps()
  system_time = datetime.now().replace(microsecond=0).isoformat()

  # We can xref the net_time and system_time for now. Eventually this will
  # probably not be necessary but in the early stages (2019/05/09) this is
  # a sanity check.
  all = {**location, **sensor,  'SystemTime': system_time } 
  pprint.pprint(all)
  time.sleep(5)

  """
  lat = "{:.5f}".format(location[2]['latitude'])
  lng = "{:.5f}".format(location[2]['longitude'])
  ix += 1

  # Ostensibly, record every second of GPS change or, alternatively
  # once every long duration if nothing seems to change.
  if old_lat != lat or old_lng != lng or ix % 1000 == 0:
      print("{} {} {}".format(int(time.time()), lat, lng))

  old_lat = lat
  old_lng = lng


  start = time.time()
  period = 0.5
  ix = 0

  while True:

    lib.sensor_store({
      "now": time.time(),
      "sensor": arduino.arduino_read(),
      "gps": get_gps()
    })

    ix += 1
    tts = (start + period * ix) - time.time()
    if tts > 0:
      time.sleep(tts)

  """
