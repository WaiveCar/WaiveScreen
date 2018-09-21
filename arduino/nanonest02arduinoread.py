
import serial
import time
import math
import struct
import sys

if sys.platform == "linux" or sys.platform == "linux2":
    comPort = '/dev/ttyACM0'
else:
    comPort = 'COM6'

arduino = serial.Serial(comPort, 9600, timeout=0.1)
#sys.exit(0)
time.sleep(3)
arduino.readall()
for _ in range(10):
    arduino.readall()
    time.sleep(1)
    header = ord(arduino.read())
    time_ms = (ord(arduino.read())<<24) + (ord(arduino.read())<<16) + (ord(arduino.read())<<8) + (ord(arduino.read()))
    current_read = (ord(arduino.read())) + (ord(arduino.read())<<8)
    current = 73.3*current_read/1023 - 36.7
    voltage_read = (ord(arduino.read())) + (ord(arduino.read())<<8)
    # v_ref is the 3v3 pin on the nano board, however, practically speaking
    # this pin is generally between 3.5 and 3.7v on the nanos tested. Need to confirm
    # on each brand of the nano and potentially adjust.
    v_ref = 3.5
    r1 = 300000.0
    r2 = 68000.0
    voltage = voltage_read/1023.0 * v_ref
    v_in = voltage * (r1/r2+1)
    therm_read = (ord(arduino.read())) + (ord(arduino.read()) << 8)
    try:
        therm_resistance = (1023.0/therm_read - 1) * 100000
    except(ZeroDivisionError):
        # if we can't read the temperature, assume it's high for safety
        therm_resistance = 0
    temp_c = therm_resistance/100000
    temp_c = math.log(temp_c)/3950 + (1/(25 + 273.13))
    temp_c = 1/temp_c - 273.15
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
    if fan_speed < 255:
        arduino.write('\x01'+struct.pack('B', fan_speed+10))
    backlight_value = ord(arduino.read())
    if backlight_value < 255:
        arduino.write('\x10'+struct.pack('B', backlight_value + 20))
    time.sleep(.5)
    print('Header: {}'.format(header))
    print('current_read: {}'.format(current_read))
    print('Current: {} A'.format(current))
    print('Voltage_read: {}'.format(voltage_read))
    print('Voltage: {} V'.format(voltage))
    print('Vin: {} V'.format(v_in))
    print('Power Draw: {} W'.format(v_in*current))
    print('Thermistor read: {}'.format(therm_read))
    print('Thermistor resistance: {} Ohm'.format(therm_resistance))
    print('Temperature: {} C'.format(temp_c))
    print('Accel X: {}, Y: {}, Z: {}'.format(accel_x, accel_y, accel_z))
    print('Pitch: {} deg, Roll: {} deg, Yaw: {} deg'.format(pitch, roll, yaw))
    print('Gyro X: {}, Y: {}, Z: {}'.format(gyro_x, gyro_y, gyro_z))
    print('Fan Speed: {}'.format(fan_speed))
    print('Backlight_brightness: {}'.format(backlight_value))

arduino.close()
