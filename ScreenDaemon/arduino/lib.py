#!/usr/bin/env python3
import serial
import time
import math
import struct
import pandas as pd
import pprint
import sys
import os
import atexit

arduino = False
first_read = False

def get_arduino():
  global arduino
  if not arduino:
    if sys.platform == "linux" or sys.platform == "linux2":
      com_port = '/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0'
      # com_port = '/dev/ttyACM0'
    else:
      com_port = 'COM6'

    arduino = serial.Serial(com_port, 115200, timeout=0.1)
  return arduino

def setup():
  global first_read, arduino
  arduino = get_arduino()
  first_read = arduino_read()
  pprint.pprint(first_read)

@atexit.register
def close():
  if arduino:
    arduino.close()
  
def power_management():
  setup()

  arduino.reset_input_buffer()
  received_dict = arduino_read()
  moving, last_smooth = get_move_status(first_read=first_read, last_read=received_dict,
                                        last_smooth={'x': 0.0, 'y': 0.0, 'z': 0.0})
  voltage = received_dict['Voltage']
  voltage_timeout = 0
  while voltage > 12.5 or moving or voltage_timeout < 150:
    received_dict = arduino_read()
    if received_dict != -1:
      voltage = received_dict['Voltage']
      if voltage < 12.5:
          voltage_timeout += 1
      else:
          voltage_timeout = 0
      moving, last_smooth = get_move_status(first_read=first_read, last_read=received_dict,
                                            last_smooth=last_smooth)
    current = received_dict['Current']
    if voltage < 12.5 and current > 1:
      # low_power_mode will hold and record until voltage goes above 13.5V

      received_dict = low_power_mode(arduino, received_dict['Backlight'])
      # the below line will wake up the dpms if it's a linux machine
      os.system("xset -display :0 dpms force on")


def set_fan_speed(arduino, value):
    fan_speed = value
    if fan_speed > 255:
        fan_speed = 255
    arduino.write(b'\x01{}')
    arduino.write(struct.pack('!B', fan_speed))


def set_fan_auto(arduino):
    arduino.write(b'\x01\x01')


def set_backlight(arduino, value):
    backlight = min(value, 255)
    arduino.write('\x10'.encode())
    arduino.write(struct.pack('!B', backlight))


def send_wakeup_signal(arduino):
    arduino.write(b'\x11\xff')


def arduino_read():
    try:
        arduino.in_waiting
    except 'SerialException':
        print("trying")
        arduino.close()
        arduino.open()
    while arduino.in_waiting < 25:
        pass

    # first byte is the header, must be 0xff
    header = ord(arduino.read())
    while header != 0xff:
        header = ord(arduino.read())
    # next 4 bytes are the time the arduino has been on in milliseconds
    time_ms = (ord(arduino.read())) + (ord(arduino.read()) << 8) + \
              (ord(arduino.read()) << 16) + (ord(arduino.read()) << 24)
    # 2 bytes for the current, thermistor, and voltage readings
    current_read = (ord(arduino.read()) << 8) + (ord(arduino.read()))
    # the two different current sense chips are oppositely directioned and need to be calculated differently
    # luckily, because we're using DC current, the returned value indicates which component is being used.
    if current_read > 511:
        # ACS711EX
        current = 73.3 * current_read / 1023 - 36.7
    else:
        # GY-712-30A
        current = (513.0-current_read) / 1023.0 * 60.0
    voltage_read = (ord(arduino.read()) << 8) + (ord(arduino.read()))

    # v_ref is the 3v3 pin on the nano board, however, practically speaking
    # this pin is generally between 3.5 and 3.7v on the nanos tested. Need to confirm
    # on each brand of the nano and potentially adjust.
    v_ref = 3.65
    r1 = 300000.0
    r2 = 68000.0
    voltage = voltage_read / 1023.0 * v_ref
    v_in = voltage * (r1 / r2 + 1)

    therm_read = (ord(arduino.read()) << 8) + (ord(arduino.read()))
    try:
        therm_resistance = (1023.0 / therm_read - 1) * 100000
    except ZeroDivisionError:
        # if we can't read the temperature, assume it's high for safety
        therm_resistance = 0

    temp_c = therm_resistance / 100000
    try:
        temp_c = math.log(temp_c) / 3950 + (1 / (25 + 273.13))
        temp_c = 1 / temp_c - 273.15

    except ValueError:
        temp_c = 0

    # 2 bytes each for accel x, y, z, and gyro x, y, z.  Note values are signed int so must rectify
    accel_x = (ord(arduino.read()) << 8) + (ord(arduino.read()))
    accel_x = -1 * (0xFFFF - accel_x) if accel_x > 0x8000 else accel_x
    accel_y = (ord(arduino.read()) << 8) + (ord(arduino.read()))
    accel_y = -1 * (0xFFFF - accel_y) if accel_y > 0x8000 else accel_y
    accel_z = (ord(arduino.read()) << 8) + (ord(arduino.read()))
    accel_z = -1 * (0xFFFF - accel_z) if accel_z > 0x8000 else accel_z
    pitch = 180.0 / math.pi * (math.atan(accel_x / math.sqrt((math.pow(accel_y, 2) + math.pow(accel_z, 2)))))
    roll = 180.0 / math.pi * (math.atan(accel_y / math.sqrt((math.pow(accel_x, 2) + math.pow(accel_z, 2)))))
    yaw = 180.0 / math.pi * (math.atan(accel_z / math.sqrt((math.pow(accel_x, 2) + math.pow(accel_y, 2)))))
    gyro_x = (ord(arduino.read()) << 8) + (ord(arduino.read()))
    gyro_x = -1 * (0xFFFF - gyro_x) if gyro_x > 0x8000 else gyro_x
    gyro_y = (ord(arduino.read()) << 8) + (ord(arduino.read()))
    gyro_y = -1 * (0xFFFF - gyro_y) if gyro_y > 0x8000 else gyro_y
    gyro_z = (ord(arduino.read()) << 8) + (ord(arduino.read()))
    gyro_z = -1 * (0xFFFF - gyro_z) if gyro_z > 0x8000 else gyro_z
    fan_speed = ord(arduino.read())
    backlight_value = ord(arduino.read())
    received_dict = {
        'ArduinoTime': time_ms,
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
    }
    return received_dict


def low_power_mode(arduino, backlight_resume_value):
    arduino = arduino
    stored_backlight_value = backlight_resume_value
    set_backlight(arduino, 0)
    send_sleep_signal()

    os.system("xset -display :0 dpms force suspend")

    # This shuts things down.
    os.system("/usr/bin/sudo /usr/bin/acpitool -s")

    i = 0
    received_dict = arduino_read()

    # todo: replace z_accel wakeup with status from invers. currently going by change in the z accel which will be
    # triggered by either the door closing or the car starting to move.
    z_init = received_dict['Accel_z']
    while received_dict['Voltage'] < 13.5 or \
            (received_dict['Voltage'] > 13.5 and -1500 < received_dict['Accel_z'] - z_init < 1500):
        i += 1
        received_dict = arduino_read()
        df.loc[i] = {
            'Time': received_dict['Time'],
            'Current': received_dict['Current'],
            'Voltage': received_dict['Voltage'],
            'Temp': received_dict['Temp'],
            'Fan': received_dict['Fan'],
            'Backlight': received_dict['Backlight']
        }
    set_backlight(arduino, stored_backlight_value)
    now = time.localtime()
    return received_dict


def get_move_status(first_read, last_read, last_smooth):
    alpha = 0.01
    move_threshold = 250
    
    move_magnitude = {'x': math.fabs(last_read['Accel_x'] - first_read['Accel_x']),
                      'y': math.fabs(last_read['Accel_y'] - first_read['Accel_y']),
                      'z': math.fabs(last_read['Accel_z'] - first_read['Accel_z'])}
    smooth_move = {
        'x': min(move_magnitude['x']*alpha + last_smooth['x']*(1-alpha), 600),
        'y': min(move_magnitude['y']*alpha + last_smooth['y']*(1-alpha), 600),
        'z': min(move_magnitude['z']*alpha + last_smooth['z']*(1-alpha), 600)
    }
    if smooth_move['x'] > move_threshold or smooth_move['y'] > move_threshold or smooth_move['z'] > move_threshold:
        moving = True
    else:
        moving = False
    return moving, smooth_move


if __name__ == '__main__':
    setup()


"""
pseudo code for main logic:

go:
    while v_in > 13 && not asleep:
        do the main stuff and record to the dataframe.
    if v_in > 13 && asleep:
        send wakeup signal
        wait for x seconds to make sure wakeup signal goes through
        check to see if it worked (via current check)
            asleep = false
        
    if v_in < 12.5:
        if current < 1.0:
            asleep = true
            
        
"""
