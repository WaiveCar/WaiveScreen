#!/usr/bin/env python3
import serial
import time
import math
import struct
import pandas as pd
import sys

if sys.platform == "linux" or sys.platform == "linux2":
    comPort = '/dev/ttyACM0'
else:
    comPort = 'COM6'

arduino = serial.Serial(comPort, 115200, timeout=0.1)
df = pd.DataFrame(columns=['Time', 'Accel_x', 'Accel_y', 'Accel_z', 'Gyro_x', 'Gyro_y',
                           'Gyro_z', 'Current', 'Voltage', 'Temp_C', 'FanSpeed', 'Backlight'])
now = time.localtime()
log_name = '{}.{}.{}.{}.{}.{}'.format(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min,
                                      now.tm_sec)
#sys.exit(0)
for _ in range(100):
    while arduino.in_waiting < 25:
        pass
    # first byte is the header, must be 0xff
    header = ord(arduino.read())
    while header <> 0xff:
        header = ord(arduino.read())
    # next 4 bytes are the time the arduino has been on in milliseconds
    time_ms = (ord(arduino.read())) + (ord(arduino.read()) << 8) + (ord(arduino.read()) << 16) + (ord(arduino.read()) << 24)
    # 2 bytes for the current, thermistor, and voltage readings
    current_read = (ord(arduino.read())<<8) + (ord(arduino.read()))
    current = 73.3*current_read/1023 - 36.7
    voltage_read = (ord(arduino.read())<<8) + (ord(arduino.read()))
    # v_ref is the 3v3 pin on the nano board, however, practically speaking
    # this pin is generally between 3.5 and 3.7v on the nanos tested. Need to confirm
    # on each brand of the nano and potentially adjust.
    v_ref = 3.6
    r1 = 300000.0
    r2 = 68000.0
    voltage = voltage_read/1023.0 * v_ref
    v_in = voltage * (r1/r2+1)
    arduino.iread_until()
    therm_read = (ord(arduino.read())<<8) + (ord(arduino.read()))
    try:
        therm_resistance = (1023.0/therm_read - 1) * 100000
    except(ZeroDivisionError):
        # if we can't read the temperature, assume it's high for safety
        therm_resistance = 0
    temp_c = therm_resistance/100000
    temp_c = math.log(temp_c)/3950 + (1/(25 + 273.13))
    temp_c = 1/temp_c - 273.15
    # 2 bytes each for accel x, y, z, and gyro x, y, z.  Note values are signed int so must rectify
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
    received_dict = {
        'Time': time_ms,
        'Current': current,
        'Voltage': v_in,
        'Temp_C': temp_c,
        'Accel_x': accel_x,
        'Accel_y': accel_y,
        'Accel_z': accel_z,
        'Gyro_x': gyro_x,
        'Gyro_y': gyro_y,
        'Gyro_z': gyro_z,
        'FanSpeed': fan_speed,
        'Backlight': backlight_value
    }
    df.loc[_] = received_dict
    print received_dict
    # print('Header: {}'.format(header))
    # print('Time stamp: {}ms'.format(time_ms))
    # print('current_read: {}'.format(current_read))
    # print('Current: {} A'.format(current))
    # print('Voltage_read: {}'.format(voltage_read))
    # print('Voltage: {} V'.format(voltage))
    # print('Vin: {} V'.format(v_in))
    # print('Power Draw: {} W'.format(v_in*current))
    # print('Thermistor read: {}'.format(therm_read))
    # print('Thermistor resistance: {} Ohm'.format(therm_resistance))
    # print('Temperature: {} C'.format(temp_c))
    # print('Accel X: {}, Y: {}, Z: {}'.format(accel_x, accel_y, accel_z))
    # print('Pitch: {} deg, Roll: {} deg, Yaw: {} deg'.format(pitch, roll, yaw))
    # print('Gyro X: {}, Y: {}, Z: {}'.format(gyro_x, gyro_y, gyro_z))
    # print('Fan Speed: {}'.format(fan_speed))
    # print('Backlight_brightness: {}'.format(backlight_value))

arduino.close()
now = time.localtime()
log_name += '-{}.{}.{}.{}.{}.{}'.format(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min,
                                       now.tm_sec)
# uncomment the below line to save the log to a folder called log
# df.to_csv("logs\{}.csv".format(log_name), index=False)
