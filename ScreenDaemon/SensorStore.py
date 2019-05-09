#!/usr/bin/python3
import lib.lib as lib
import arduino.lib as arduino
import sys

import dbus
import time
import pprint
from datetime import datetime

bus = dbus.SystemBus()

foundModem = False
modem_ix = 0

def next_iface():
  global modem_ix
  proxy = bus.get_object('org.freedesktop.ModemManager1','/org/freedesktop/ModemManager1/Modem/{}'.format(modem_ix))
  iface = {
    'location': dbus.Interface(proxy, dbus_interface='org.freedesktop.ModemManager1.Modem.Location'),
    'time': dbus.Interface(proxy, dbus_interface='org.freedesktop.ModemManager1.Modem.Time')
  }
  modem_ix += 1 

  return iface

iface = next_iface()

# Try 10 eps to find a modem.
for i in range(0, 10):
  try: 
    iface['location'].GetLocation()

    # if we get here then we know that our modem works
    foundModem = True
    break

  except Exception as inst:
    print(inst)
    iface = next_iface()


arduino.setup()
while True:
  sensor = arduino.arduino_read()

  # Put data in if we have it
  location = {}
  net_time = 0
  system_time = datetime.now().replace(microsecond=0).isoformat()

  if foundModem:
    modem = iface['location'].GetLocation()
    net_time = iface['time'].GetNetworkTime()
  
    try:
      location = {
        'lat': "{:.5f}".format(modem[2]['latitude']),
        'lng': "{:.5f}".format(modem[2]['longitude'])
      }
    except:
      pass

  # We can xref the net_time and system_time for now. Eventually this will
  # probably not be necessary but in the early stages (2019/05/09) this is
  # a sanity check.
  all = {**location, **sensor, 'GPStime': net_time, 'SystemTime': system_time } 
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
  """
