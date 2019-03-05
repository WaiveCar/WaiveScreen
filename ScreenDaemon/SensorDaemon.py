#!/usr/bin/env python3
import dbus
import serial
import time
import math
import struct
import sys
import nanonest02arduinoread as ar

import lib.db as db
import lib.lib as lib

arduino = False
def get_arduino():
    global arduino
    if !arduino:
        if sys.platform == "linux" or sys.platform == "linux2":
            comPort = '/dev/ttyACM0'
        else:
            comPort = 'COM6'

        arduino = serial.Serial(comPort, 9600, timeout=0.1)
    return arduino

# arduino.close()

iface = False
def get_iface(num = False):
    global iface
    if num == False and iface != False:
        return iface

    print("Trying modem {}".format(num))
    proxy = bus.get_object('org.freedesktop.ModemManager1','/org/freedesktop/ModemManager1/Modem/{}'.format(num))
    iface = {
        'location': dbus.Interface(proxy, dbus_interface='org.freedesktop.ModemManager1.Modem.Location'),
        'time': dbus.Interface(proxy, dbus_interface='org.freedesktop.ModemManager1.Modem.Time'),
        'ix': num
    }
    return iface

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

def get_payload():
    arduino = get_arduino()

    # first byte is the header
    header = ord(arduino.read())

    # next 4 byte are the time
    time_ms = (ord(arduino.read())) + (ord(arduino.read())<<8) + (ord(arduino.read())<<16) + (ord(arduino.read())<<24)

    # 2 bytes for current and thermistor readings
    current_read = (ord(arduino.read())<<8) + (ord(arduino.read()))
    current = 73.3*current_read/1023 - 36.7
    therm_read = (ord(arduino.read()) << 8) + (ord(arduino.read()))
    therm_resistance = (1023.0/therm_read - 1) * 100000
    temp_c = therm_resistance/100000
    temp_c = math.log(temp_c)/3950 + (1/(25 + 273.13))
    temp_c = 1/temp_c - 273.15

    # 2 bytes each for accel x, y, z, and gyro x, y, and z
    accel_x = (ord(arduino.read()) << 8) + (ord(arduino.read()))
    accel_x = -1*(0xFFFF - accel_x) if accel_x > 0x8000 else accel_x
    accel_y = (ord(arduino.read()) << 8) + (ord(arduino.read()))
    accel_y = -1*(0xFFFF - accel_y) if accel_y > 0x8000 else accel_y
    accel_z = (ord(arduino.read()) << 8) + (ord(arduino.read()))
    accel_z = -1*(0xFFFF - accel_z) if accel_z > 0x8000 else accel_z
    pitch = 180.0/math.pi * (math.atan(accel_x / math.sqrt((math.pow(accel_y, 2) + math.pow(accel_z, 2)))))
    roll = 180.0/math.pi * (math.atan(accel_y / math.sqrt((math.pow(accel_x, 2) + math.pow(accel_z, 2)))))
    yaw = 180.0/math.pi * (math.atan(accel_z / math.sqrt((math.pow(accel_x, 2) + math.pow(accel_y, 2)))))
    gyro_x = (ord(arduino.read()) << 8) + (ord(arduino.read()))
    gyro_x = -1*(0xFFFF - gyro_x) if gyro_x > 0x8000 else gyro_x
    gyro_y = (ord(arduino.read()) << 8) + (ord(arduino.read()))
    gyro_y = -1*(0xFFFF - gyro_y) if gyro_y > 0x8000 else gyro_y
    gyro_z = (ord(arduino.read()) << 8) + (ord(arduino.read()))
    gyro_z = -1*(0xFFFF - gyro_z) if gyro_z > 0x8000 else gyro_z
    fan_speed = ord(arduino.read())
    backlight_value = ord(arduino.read())

    """
    return {
        'ts': time_ms,
        'backlight': backlight_value,
        'fan': fan_speed,
        'temp': temp_c,
        'current': {
            'raw': current_read,
            'normalized': current
        },
        'accel': {
            'x': accel_x,
            'y': accel_y,
            'z': accel_z
        },
        'gyro': {
            'x': gyro_x,
            'y': gyro_y,
            'z': gyro_z
        },
        'therm': {
            'read': therm_read,
            'resistance': therm_resistance
        },
        'pitch': pitch,
        'roll': roll,
        'yaw': yaw
    }
    """
    return {
        'ts': time_ms,
        'backlight': backlight_value,
        'fan': fan_speed,
        'temp': temp_c,
        'current_raw': current_read,
        'current_normalized': current,
        'accel_x':  accel_x,
        'accel_y': accel_y,
        'accel_z': accel_z
        'gyro_x': gyro_x,
        'gyro_y': gyro_y,
        'gyro_z': gyro_z
        'therm_read': therm_read,
        'therm_resistance': therm_resistance
        'pitch': pitch,
        'roll': roll,
        'yaw': yaw
    }

if __name__ == '__main__':
  start = time.time()
  period = 0.5
  ix = 0

  while True:

    lib.sensor_store({
      "now": time.time(),
      "sensor": get_payload(), 
      "gps": get_gps()
    })

    ix += 1
    tts = (start + period * ix) - time.time()
    if tts > 0:
      time.sleep(tts)


