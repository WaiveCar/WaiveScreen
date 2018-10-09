#!/usr/bin/python3

import dbus
import time
import pprint

bus = dbus.SystemBus()
proxy = bus.get_object('org.freedesktop.ModemManager1','/org/freedesktop/ModemManager1/Modem/1')
iface = {
    'location': dbus.Interface(proxy, dbus_interface='org.freedesktop.ModemManager1.Modem.Location'),
    'time': dbus.Interface(proxy, dbus_interface='org.freedesktop.ModemManager1.Modem.Time')
}

old_lat = False
old_lng = False
ix = 0

while True:
    location = iface['location'].GetLocation()
    pprint.pprint(location) 
    location = iface['time'].GetNetworkTime()
    pprint.pprint(location) 
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
    time.sleep(2)
