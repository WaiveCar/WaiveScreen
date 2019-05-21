#!/usr/bin/env python3
import dbus
import serial
import time
import math
import struct
import sys

import arduino.lib as arduino
import lib.db as db
import lib.lib as lib

def get_gps():
    iface = get_iface()

    try: 
        location = iface['location'].GetLocation()
        networktime = iface['time'].GetNetworkTime()
    except:
        iface = next_iface(iface['ix'] + 1)

    return {
        'altitude': location[2]['altitude']
        'latitude': location[2]['latitude']
        'longitude': location[2]['longitude'],
        'gps_time': location[2]['utc-time'],
        'time': networktime[0]
    }

def set_backlight(value):
    if value < 1: 
        value = round(value * 256)
    return ar.set_backlight( get_arduino(), value )

def set_fan(value):
    arduino = get_arduino()
    if value < 1: 
        value = round(value * 256)

    arduino.write(struct.pack('BB', 1, value))


if __name__ == '__main__':
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


