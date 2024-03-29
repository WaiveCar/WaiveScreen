#!/usr/bin/env python3
from . import db
import serial
import time
import math
import struct
import binascii
import json
import sys
import os
import atexit
import termios

_arduino = False
_first = False
_sleeping = None
_log = False
# we do this to get an initial value
_changeTime = time.time()
_baseline = False
_baselineList = []

USER = os.environ.get('USER')
if not USER or USER == 'root':
  # This tool probably shouldn't be run as root but we should
  # know who we are talking about if it is
  USER = 'adorno'

# If the voltage drops below this we send it off to sleep
VOLTAGE_SLEEP = float(db.kv_get('voltage_sleep') or 11.5)
VOLTAGE_WAKE = float(db.kv_get('voltage_wake') or 13.5)
DISPLAY = ':0' #os.environ.get('DISPLAY') or ':0'

@atexit.register
def close():
  if _arduino:
    _arduino.close()

def set_log(what):
  global _log
  _log = what

class FakeArduino:
  def __init__(self):
    self.in_waiting  = 0
    self.is_fake = True

  def write(self, payload):
    _log.info("fake writing: {}".format(binascii.b2a_base64(payload)))

  def read(self, payload):
    return None

  def open():
    _log.info("fake open")

  def close():
    _log.info("fake close")

  def reset_input_buffer():
    _log.info("fake reset")


_fake_arduino = FakeArduino()

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
      with open(com_port) as f:
        attrs = termios.tcgetattr(f)
        attrs[2] = attrs[2] & ~termios.HUPCL
        termios.tcsetattr(f, termios.TCSAFLUSH, attrs)

      _arduino = serial.Serial(com_port, 115200, timeout=0.1)
      _arduino.is_fake = False

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
  from .lib import get_brightness_map

  brightness_map = get_brightness_map()

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
    level = min(float(max_bright), level)

  _log.info('[autobright] Setting to {}'.format(level))
  set_backlight(level)

def do_awake():
  global _sleeping, _changeTime, _baseline, _baselineList

  if not db.sess_get('force_sleep'):
    _sleeping = False
    _changeTime = time.time()
    _baseline = False
    _baselineList = []
    db.sess_del('backlight')
    db.sess_set('power', 'awake')
    os.system("/usr/bin/sudo /usr/bin/xset -display {} dpms force on".format(DISPLAY))
    _log.info("Waking up")
    _log.info("Changetime set {}".format(time.time()))
    set_autobright()
    set_fanauto()

def do_sleep():
  global _sleeping, _changeTime, _baseline, _baselineList
  db.sess_set('power', 'sleep')
  
  _sleeping = True
  _changeTime = time.time()
  _baseline = False
  _baselineList = []
  _log.info("Going to sleep")
  _log.info("Changetime set {}".format(time.time()))

  os.system("/usr/bin/sudo /usr/bin/xset -display {} dpms force suspend".format(DISPLAY))
  set_backlight(0)
  db.sess_set('backlight', 0)

  set_fanspeed(0)
  #
  # TODO: This will immediately turn back on thanks to our Quectel modem. See #8 at 
  # https://github.com/WaiveCar/WaiveScreen/issues/8 to follow this - we're going 
  # to not even try it for now since all it will do in practice is drain some power
  # by doing some unnecessary shit and then turn immediately back on.
  #
  # os.system("/usr/bin/sudo /usr/bin/acpitool -s")

def pm_if_needed(avg, last):
  global _changeTime, _baselineList, _baseline

  # Right I know this is crazy but every car seems to require its own special system
  model = db.kv_get('model')

  if model == 'camry':
    if _changeTime and not _baseline:
      delta = time.time() - _changeTime 

      if delta > 0.5 and delta < 5.0:
        if len(_baselineList) == 0:
          _log.info("Baseline time window started")

        _baselineList.append(last)

      elif delta > 5.0:
        _baseline = sum(_baselineList) / len(_baselineList)
        _log.info("Baseline time window finished. Value to compare: {}".format(_baseline))
        _baselineList = []

    if _baseline:
      if (_sleeping == None or _sleeping == False) and avg < _baseline - 0.5:
        _log.info("Sleep threshold met: {} < {} ({})".format(avg, _baseline - 0.5, last))
        do_sleep()

      elif (_sleeping == None or _sleeping == True) and avg > _baseline + 0.95:
        _log.info("Awake threshold met: {} > {} ({})".format(avg, _baseline + 0.95, last))
        do_awake()

  else:
    if (_sleeping == None or _sleeping == False) and avg < VOLTAGE_SLEEP: 
      do_sleep()

    # TODO: replace z_accel wakeup with status from invers. currently going by change in the z accel which will be
    # triggered by either the door closing or the car starting to move.
    if (_sleeping == None or _sleeping == True) and avg > VOLTAGE_WAKE: 
      do_awake()


def clear():
  _arduino = get_arduino(False)
  if _arduino:
    _arduino.reset_input_buffer()


def send_arduino_ping():
  get_arduino().write(b'\x03\x00')

def set_fanspeed(value):
  arduino_queue_add( { 'set': { 'fanspeed': value } } )

def _set_fanspeed(value):
  _arduino = get_arduino()
  if value <= 1: 
    value = round(value * 256)

  fan_speed = int(min(value, 255))

  _arduino.write(b'\x01')
  _arduino.write(struct.pack('!B', fan_speed))

def set_fanauto():
  arduino_queue_add( { 'set': { 'fanspeed': 'auto' } } )

def _set_fanauto():
  _arduino = get_arduino()
  _arduino.write(b'\x01\x01')

def set_backlight(value):
  arduino_queue_add( { 'set': { 'backlight': value } } )

def _set_backlight(value):
  _arduino = get_arduino()
  if value <= 1: 
    value = round(value * 256)

  backlight = int(min(value, 255))

  _arduino.write(b'\x10')
  _arduino.write(struct.pack('!B', backlight))
  dcall('set_brightness', (value / 255.0), 'nopy')

#def send_wakeup_signal():
#  _arduino = get_arduino()
#  _arduino.write(b'\x11\xff')

def arduino_queue_add(cmd):
  try:
    cmd_text = json.dumps(cmd)
  except TypeError:
    _log.error('Unable to add cmd to arduino queue: {}'.format(cmd))
    return False
  return db.insert('arduino_queue', {'text': cmd_text })


def process_arduino_queue():
  q_list = db.all('arduino_queue')
  q_list.reverse()
  processed_ids = []
  no_dup_params = []
  for q_item in q_list:
    processed_ids.append(q_item['id'])
    try:
      q_cmd = json.loads(q_item['text'])
    except:
      _log.error('Arduino Queue: unable to parse entry {}: {}'.format(q_item['id'], q_item['text']))
      continue
    try:
      for k, v in q_cmd.items():
        if k == 'set':
          for param, value in v.items():
            if param in no_dup_params:
              continue
            if param == 'backlight':
              _set_backlight(float(value))
              no_dup_params.append(param)
            elif param == 'fanspeed':
              if value == 'auto':
                _set_fanauto()
              else:
                _set_fanspeed(float(value))
              no_dup_params.append(param)
            else:
              _log.warning('Arduino Queue: unknown parameter "{}" in entry {}: {}'.format(k, q_item['id'], q_item['text']))
        else:
          _log.warning('Arduino Queue: unknown command "{}" in entry {}: {}'.format(k, q_item['id'], q_item['text']))
    except Exception as ex:
      _log.error('Arduino Queue: exception processing entry {}: {} - Ex: {}'.format(q_item['id'], q_item['text'], ex))
  for q_id in processed_ids:
    db.delete('arduino_queue', q_id)


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

_parserMap = {}
def get_packet(arduino):
  from collections import namedtuple
  global _parserMap
  kindMap = [
    'sensor', # 00
    'version' # 01
  ]

  kindNum, length = struct.unpack('<BH', arduino.read(3))
  kind = kindMap[kindNum]

  if kind == 'version':
    return (kind, struct.unpack("<{}s".format(length), arduion.read(length)))

  if kind == 'sensor':
    if 'sensor' not in _parserMap:
      # refer to https://docs.python.org/2/library/struct.html
      FORMAT = (
        ( 'time_ms', 'I' ),
        ( 'current_read', 'H'),
        ( 'voltage', 'H' ),
        ( 'therm_read', 'H'),
        ( 'accel_x', 'H' ),
        ( 'accel_y', 'H' ),
        ( 'accel_z', 'H' ),
        ( 'gyro_x', 'H' ), 
        ( 'gyro_y', 'H' ),
        ( 'gyro_z', 'H' ),
        ( 'fan_speed', 'B' ),
        ( 'backlight_value', 'B' )
      )

      names = ' '.join([x[0] for x in FORMAT])
      format = ">{}".format(''.join([x[1] for x in FORMAT]))
      size = struct.calcsize(format)
      _parserMap['sensor'] = {
        'struct': struct.Struct(format),
        'packet': namedtuple('sensor', names), 
        'size': size
      }

  p = _parserMap[what]

  return (kind, p['packet']._make(p['struct'].unpack(arduino.read(p['size']))))

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
  try:
    sw_version = bytes.decode(_arduino.read(8))
  except:
    # On older firmware versions, we will read the 0xff start of the next frame
    # We catch that and set the version to unknown.
    sw_version = 'unknown'
  received_dict = {
    #'Arduino_time': time_ms,
    'Sw_version': sw_version,
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

def arduino_disconnect():
  global _arduino
  if _arduino:
    _arduino.close()
    _arduino = False

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
