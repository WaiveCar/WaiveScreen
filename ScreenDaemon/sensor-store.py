#!/usr/bin/python3
import lib.lib as lib
import arduino.lib as arduino

import dbus
import time
import pprint

bus = dbus.SystemBus()

old_lat = False
old_lng = False

foundModem = False
modem = 0
def next_iface():
  global modem
  print("Trying modem {}".format(modem))
  proxy = bus.get_object('org.freedesktop.ModemManager1','/org/freedesktop/ModemManager1/Modem/{}'.format(modem))
  iface = {
    'location': dbus.Interface(proxy, dbus_interface='org.freedesktop.ModemManager1.Modem.Location'),
    'time': dbus.Interface(proxy, dbus_interface='org.freedesktop.ModemManager1.Modem.Time')
  }
  modem += 1 
  return iface

iface = next_iface()

while not foundModem:
  try: 
    location = iface['location'].GetLocation()
    location = iface['time'].GetNetworkTime()
    foundModem = True

  except Exception as inst:
    print(inst)
    iface = next_iface()


arduion.setup()
while True:
  sensor = arduino.get_sensors()
  location = iface['location'].GetLocation()
  pprint.pprint([sensor, location])
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
