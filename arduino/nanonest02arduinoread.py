#!/usr/bin/env python3
import serial
import time
import math
import struct
import pandas as pd
import sys
import os


def main():
    if sys.platform == "linux" or sys.platform == "linux2":
        comPort = '/dev/ttyACM0'
    else:
        comPort = 'COM6'
    arduino = serial.Serial(comPort, 115200, timeout=0.1)
    while(1):
        last_reading = nominal_operation(arduino=arduino)

    arduino.close()


def nominal_operation(arduino):
    arduino = arduino
    df = pd.DataFrame(columns=['Time', 'Accel_x', 'Accel_y', 'Accel_z', 'Gyro_x', 'Gyro_y',
                           'Gyro_z', 'Current', 'Voltage', 'Temp_C', 'FanSpeed', 'Backlight'])
    now = time.localtime()
    log_name = '{}.{:02d}.{:02d}.{:02d}.{:02d}.{:02d}'.format(now.tm_year, now.tm_mon, now.tm_mday,
                                                              now.tm_hour, now.tm_min, now.tm_sec)
    arduino.reset_input_buffer()
    received_dict = arduino_read(arduino)
    voltage = received_dict['Voltage']
    i = 0
    while voltage > 12.5:
        received_dict = arduino_read(arduino)
        if received_dict != -1:
            df.loc[i] = received_dict
            i += 1
            voltage = received_dict['Voltage']
            print(voltage)
    now = time.localtime()
    log_name += '-{}.{:02d}.{:02d}.{:02d}.{:02d}.{:02d}'.format(now.tm_year, now.tm_mon, now.tm_mday,
                                                                now.tm_hour, now.tm_min, now.tm_sec)
    # uncomment the below line to save the log to a folder called logs
    df.to_csv("logs//{}.csv".format(log_name), index=False)

    current = received_dict['Current']
    if voltage < 12.5 and current > 1:
        received_dict = low_power_mode(arduino, received_dict['Backlight'])
        if sys.platform == "linux" or sys.platform == "linux2":
            os.system("xset -display :0 dpmx force on")

    # while current < 1:
    #     received_dict = arduino_read(arduino)
    #     if received_dict != -1:
    #         voltage = received_dict['Voltage']
    #         current = received_dict['Current']
    # #        print(voltage, current)
    return received_dict


def read_until_empty(arduino):
    arduino = arduino
    while arduino.in_waiting > 0:
        received_dict = arduino_read(arduino)
    return 0


def set_fanspeed(arduino, value):
    fan_speed = value
    if fan_speed > 255:
        fan_speed = 255
    arduino.write(b'\x01{}')
    arduino.write(struct.pack('!B', fan_speed))


def set_fan_auto(arduino):
    arduino.write(b'\x01\x01')


def set_backlight(arduino, value):
    backlight = value
    if backlight > 255:
        backlight = 255
    arduino.write('\x10'.encode())
    arduino.write(struct.pack('!B', backlight))


def send_wakeup_signal(arduino):
    arduino.write(b'\x11\xff')


def send_sleep_signal():
    if sys.platform == "linux" or sys.platform == "linux2":
        os.system("xset -display :0 dpmx force suspend")
    else:
        os.system("rundll32.exe powrprof.dll,SetSuspendState sleep")


def arduino_read(arduino):
    arduino = arduino
    try:
        arduino.in_waiting
    except 'SerialException':
        arduino.close()
        arduino.open()
    while arduino.in_waiting < 25:
        pass
    # first byte is the header, must be 0xff
    header = ord(arduino.read())
    while header != 0xff:
        header = ord(arduino.read())
    # next 4 bytes are the time the arduino has been on in milliseconds
    time_ms = (ord(arduino.read())) + (ord(arduino.read()) << 8) + (ord(arduino.read()) << 16) + (ord(arduino.read()) << 24)
    # 2 bytes for the current, thermistor, and voltage readings
    current_read = (ord(arduino.read()) << 8) + (ord(arduino.read()))
    current = 73.3 * current_read / 1023 - 36.7
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
    # print(voltage_read, current_read, therm_read)
    try:
        therm_resistance = (1023.0 / therm_read - 1) * 100000
    except ZeroDivisionError:
        # if we can't read the temperature, assume it's high for safety
        therm_resistance = 0
    temp_c = therm_resistance / 100000
    try:
        temp_c = math.log(temp_c) / 3950 + (1 / (25 + 273.13))
    except ValueError:
        return -1
    temp_c = 1 / temp_c - 273.15
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
    return received_dict


def low_power_mode(arduino, backlight_resume_value):
    arduino = arduino
    stored_backlight_value = backlight_resume_value
    set_backlight(arduino, 0)
    send_sleep_signal()
    now = time.localtime()
    log_name = '{}.{:02d}.{:02d}.{:02d}.{:02d}.{:02d}'.format(now.tm_year, now.tm_mon, now.tm_mday,
                                                              now.tm_hour, now.tm_min, now.tm_sec)
    i = 0
    df = pd.DataFrame(columns=['Time', 'Current', 'Voltage', 'Temp_C', 'FanSpeed', 'Backlight'])
    received_dict = arduino_read(arduino)
    df.loc[i] = {
        'Time': received_dict['Time'],
        'Current': received_dict['Current'],
        'Voltage': received_dict['Voltage'],
        'Temp_C': received_dict['Temp_C'],
        'FanSpeed': received_dict['FanSpeed'],
        'Backlight': received_dict['Backlight']
    }
    while received_dict['Voltage'] < 13.5:
        i += 1
        received_dict = arduino_read(arduino)
        print('Low Power: ', received_dict['Voltage'])
        df.loc[i] = {
            'Time': received_dict['Time'],
            'Current': received_dict['Current'],
            'Voltage': received_dict['Voltage'],
            'Temp_C': received_dict['Temp_C'],
            'FanSpeed': received_dict['FanSpeed'],
            'Backlight': received_dict['Backlight']
        }
    set_backlight(arduino, stored_backlight_value)
    now = time.localtime()
    log_name += '-{}.{:02d}.{:02d}.{:02d}.{:02d}.{:02d}'.format(now.tm_year, now.tm_mon, now.tm_mday,
                                                                now.tm_hour, now.tm_min, now.tm_sec)
    # uncomment the below line to save the log to a folder called logs
    df.to_csv("logs//{}.csv".format(log_name), index=False)
    return received_dict


if __name__ == '__main__':
    main()



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