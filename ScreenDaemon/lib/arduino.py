#!/usr/bin/env python3
from . import db
import serial
import time
import math
import struct
import sys
import os
import atexit

_arduino = False
_first = False
_sleeping = None
_log = False

USER = os.environ.get('USER')
if not USER or USER == 'root':
  # This tool probably shouldn't be run as root but we should
  # know who we are talking about if it is
  USER = 'adorno'

# If the voltage drops below this we send it off to sleep
VOLTAGE_SLEEP = db.kv_get('voltage_sleep') or 11.5
VOLTAGE_WAKE = db.kv_get('voltage_wake') or 13.5
DISPLAY = os.environ.get('DISPLAY') or ':0'

@atexit.register
def close():
  if _arduino:
    _arduino.close()

def set_log(what):
  global _log
  _log = what

_arduino_err = 0
def get_arduino(stop_on_failure=True):
  global _arduino, _first, _arduino_err

  if not _arduino:
    direct = '/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0'
    com_port = direct if os.path.exists(direct) else '/dev/ttyACM0'

    if not os.path.exists(com_port):
      err = "Can't find port {}, stopping here.".format(com_port)

      _arduino_err += 1
      if _arduino_err < 5:
        _log.warning(err)

      if stop_on_failure:
        raise Exception(err)
      else:
        return False

    _log.debug("Using {}".format(com_port))

    try:
      _arduino = serial.Serial(com_port, 115200, timeout=0.1)
      _first = arduino_read()

    except Exception as ex:
      err = "Can't open arduino: {}".format(ex)

      # Make sure we don't mis-report this as working
      _arduino = False

      _arduino_err += 1
      if _arduino_err < 5:
        _log.warning(err)

      if stop_on_failure:
        raise Exception(err)
      else:
        return False

  return _arduino

def dcall(*kvarg):
  home = '/home/{}'.format(USER)
  dcall = '{}/dcall'.format(home)
  os.popen('{} {}'.format(dcall,' '.join([str(k) for k in kvarg])))

def set_autobright():
  brightness_map = [
    0.20, 0.08, 0.08, 0.08,  # 4am
    0.10, 0.30, 0.70, 0.90,  # 8am
    1.00, 1.00, 1.00, 1.00,  # 12pm
    1.00, 1.00, 1.00, 1.00,  # 4pm
    1.00, 0.90, 0.80, 0.70,  # 8pm
    0.50, 0.50, 0.40, 0.30,  # midnight
  ]

  level = brightness_map[time.localtime().tm_hour]
  
  #
  # The maximum brightness can be instructed to us
  # on a per-boot-instance basis by a "brightnes" 
  # task command. If we have that then we should
  # observe that value and not auto-bright ourselves
  # past it. (see #38 for discussion about this)
  #
  max_bright = db.sess_get('backlight')
  if max_bright is not None:
    level = min(max_bright, level)

  set_backlight(level)
  dcall('set_brightness', level, 'nopy')

def do_awake():
  global _sleeping
  _sleeping = False
  db.sess_set('power', 'awake')
  os.system("/usr/bin/sudo /usr/bin/xset -display {} dpms force on".format(DISPLAY))
  set_autobright()
  set_fanauto()

def do_sleep():
  global _sleeping
  db.sess_set('power', 'sleep')
  
  _sleeping = True
  _log.info("Going to sleep")
  os.system("/usr/bin/sudo /usr/bin/xset -display {} dpms force suspend".format(DISPLAY))

  set_backlight(0)
  set_fanspeed(0)
  #
  # TODO: This will immediately turn back on thanks to our Quectel modem. See #8 at 
  # https://github.com/WaiveCar/WaiveScreen/issues/8 to follow this - we're going 
  # to not even try it for now since all it will do in practice is drain some power
  # by doing some unnecessary shit and then turn immediately back on.
  #
  # os.system("/usr/bin/sudo /usr/bin/acpitool -s")

def pm_if_needed(avg):
  if (_sleeping == None or _sleeping == False) and avg < VOLTAGE_SLEEP: # and reading['Current'] > 1:
    do_sleep()

  # TODO: replace z_accel wakeup with status from invers. currently going by change in the z accel which will be
  # triggered by either the door closing or the car starting to move.
  if (_sleeping == None or _sleeping == True) and avg > VOLTAGE_WAKE: # or abs(_base - reading['Accel_z']) > 1500):
    do_awake()


def clear():
  _arduino = get_arduino(False)
  if _arduino:
    _arduino.reset_input_buffer()

def set_fanspeed(value):
  _arduino = get_arduino()
  if value <= 1: 
    value = round(value * 256)

  fan_speed = int(min(value, 255))

  _arduino.write(b'\x01')
  _arduino.write(struct.pack('!B', fan_speed))


def set_fanauto():
  _arduino = get_arduino()
  _arduino.write(b'\x01\x01')


def set_backlight(value):
  _arduino = get_arduino()
  if value <= 1: 
    value = round(value * 256)

  backlight = int(min(value, 255))

  _arduino.write(b'\x10')
  _arduino.write(struct.pack('!B', backlight))

  return True

def send_wakeup_signal():
  _arduino = get_arduino()
  _arduino.write(b'\x11\xff')


def test_do(ex, delay=1):
  _log.debug(ex)
  eval(ex)
  if delay:
    time.sleep(delay)

def test(parts='fbs'):
  fnlist = []

  if parts.find('f') != -1:
    fnlist.append('set_fanspeed')

  if parts.find('b') != -1:
    fnlist.append('set_backlight')

  for fn in fnlist:
    for rate in range(0, 20):
      test_do("{}({})".format(fn, float(rate)/20), 0.2)

  if parts.find('s') != -1: 
    set_fanauto()
    _log.debug('do_sleep()')
    do_sleep()
    time.sleep(30)
    _log.debug('do_awake()')
    do_awake()

def arduino_read():
  _arduino = get_arduino(False)

  if not _arduino:
    return {}

  attempts = 0
  try:
    _arduino.in_waiting
    
  except 'SerialException':
    _arduino.close()
    _arduino.open()

  while _arduino.in_waiting < 25:
    # Our period is 100hz so we try to 
    # wait a bit under that.
    sleep = 0.007
    time.sleep(sleep)
    attempts += 1

    # if we didn't hear anything back
    # in some time period, then we just
    # return a fail case 
    if attempts > 3 / sleep:
      _log.warning("Timeout: Could not read from arduino ({})".format(_arduino.in_waiting))
      return {}
    pass

  # First byte is the header, must be 0xff
  header = ord(_arduino.read())
  while header != 0xff:
    header = ord(_arduino.read())

  # Next 4 bytes are the time the _arduino has been on in milliseconds
  time_ms = (ord(_arduino.read())) + (ord(_arduino.read()) << 8) + \
            (ord(_arduino.read()) << 16) + (ord(_arduino.read()) << 24)

  # 2 bytes for the current, thermistor, and voltage readings
  current_read = (ord(_arduino.read()) << 8) + (ord(_arduino.read()))

  # The two different current sense chips are oppositely directioned and need to be calculated differently
  # luckily, because we're using DC current, the returned value indicates which component is being used.
  if current_read > 511:
    # ACS711EX
    current = 73.3 * current_read / 1023 - 36.7
  else:
    # GY-712-30A
    current = (513.0 - current_read) / 1023.0 * 60.0

  voltage_read = (ord(_arduino.read()) << 8) + (ord(_arduino.read()))

  # v_ref is the 3v3 pin on the nano board, however, practically speaking
  # this pin is generally between 3.5 and 3.7v on the nanos tested. Need to confirm
  # on each brand of the nano and potentially adjust.
  v_ref = 3.65
  r1 = 300000.0
  r2 = 68000.0
  voltage = voltage_read / 1023.0 * v_ref
  v_in = voltage * (r1 / r2 + 1)

  therm_read = (ord(_arduino.read()) << 8) + (ord(_arduino.read()))

  try:
    therm_resistance = (1023.0 / therm_read - 1) * 100000

  except ZeroDivisionError:
    # If we can't read the temperature, assume it's high for safety
    therm_resistance = 0

  temp_c = therm_resistance / 100000
  try:
    temp_c = math.log(temp_c) / 3950 + (1 / (25 + 273.13))
    temp_c = 1 / temp_c - 273.15

  except ValueError:
    temp_c = 0

  # 2 bytes each for accel x, y, z, and gyro x, y, z.  Note values are signed int so must rectify
  accel_x = (ord(_arduino.read()) << 8) + (ord(_arduino.read()))
  accel_x = -1 * (0xFFFF - accel_x) if accel_x > 0x8000 else accel_x
  accel_y = (ord(_arduino.read()) << 8) + (ord(_arduino.read()))
  accel_y = -1 * (0xFFFF - accel_y) if accel_y > 0x8000 else accel_y
  accel_z = (ord(_arduino.read()) << 8) + (ord(_arduino.read()))
  accel_z = -1 * (0xFFFF - accel_z) if accel_z > 0x8000 else accel_z
  pitch = 180.0 / math.pi * (math.atan(accel_x / math.sqrt((math.pow(accel_y, 2) + math.pow(accel_z, 2)))))
  roll = 180.0 / math.pi * (math.atan(accel_y / math.sqrt((math.pow(accel_x, 2) + math.pow(accel_z, 2)))))
  yaw = 180.0 / math.pi * (math.atan(accel_z / math.sqrt((math.pow(accel_x, 2) + math.pow(accel_y, 2)))))
  gyro_x = (ord(_arduino.read()) << 8) + (ord(_arduino.read()))
  gyro_x = -1 * (0xFFFF - gyro_x) if gyro_x > 0x8000 else gyro_x
  gyro_y = (ord(_arduino.read()) << 8) + (ord(_arduino.read()))
  gyro_y = -1 * (0xFFFF - gyro_y) if gyro_y > 0x8000 else gyro_y
  gyro_z = (ord(_arduino.read()) << 8) + (ord(_arduino.read()))
  gyro_z = -1 * (0xFFFF - gyro_z) if gyro_z > 0x8000 else gyro_z
  fan_speed = ord(_arduino.read())
  backlight_value = ord(_arduino.read())
  received_dict = {
    #'Arduino_time': time_ms,
    'Light': backlight_value,
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
    'Tread': therm_read,
    'Tres': therm_resistance,
    'Pitch': pitch,
    'Roll': roll,
    'Yaw': yaw
  }
  return received_dict


def get_move_status(last_read, last_smooth):
  global _first

  alpha = 0.01
  move_threshold = 250
  
  move_magnitude = {
    'x': math.fabs(last_read['Accel_x'] - _first['Accel_x']),
    'y': math.fabs(last_read['Accel_y'] - _first['Accel_y']),
    'z': math.fabs(last_read['Accel_z'] - _first['Accel_z'])
  }

  smooth_move = {
    'x': min(move_magnitude['x'] * alpha + last_smooth['x'] * (1 - alpha), 600),
    'y': min(move_magnitude['y'] * alpha + last_smooth['y'] * (1 - alpha), 600),
    'z': min(move_magnitude['z'] * alpha + last_smooth['z'] * (1 - alpha), 600)
  }

  moving = smooth_move['x'] > move_threshold or smooth_move['y'] > move_threshold or smooth_move['z'] > move_threshold

  return moving, smooth_move


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
            
        
# TODO: We need to find out how to mitigate this.
def power_management():
  _arduino = get_arduino()

  _arduino.reset_input_buffer()
  res = arduino_read()
  moving, last_smooth = get_move_status(last_read=res,
                                        last_smooth={'x': 0.0, 'y': 0.0, 'z': 0.0})
  voltage_timeout = 0
  while res['Voltage'] > VOLTAGE_SLEEP or moving or voltage_timeout < 150:
    res = arduino_read()

    if res['Voltage'] < VOLTAGE_SLEEP:
      voltage_timeout += 1
    else:
      voltage_timeout = 0

    moving, last_smooth = get_move_status(last_read=res, last_smooth=last_smooth)

    if res['Voltage'] < VOLTAGE_SLEEP and res['Current'] > 1:
      # low_power_mode will hold and record until voltage goes above VOLTAGE_WAKE

      res = low_power_mode(res['Light'])
      # the below line will wake up the dpms if it's a linux machine
      os.system("xset -display :0 dpms force on")

"""
