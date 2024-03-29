#!/usr/bin/python3
from . import db
import base64
import configparser
import dbus
import glob
import hashlib
import json
import logging
import os
import re
import requests
import subprocess
import sys
import time
import math
from urllib.parse import quote
from threading import Lock
from pprint import pprint
from datetime import datetime, timedelta
from .wifi_location import wifi_location

#
# IMPORTANT. DO NOT LOG ANYTHING HERE BEFORE CALLING
# THE BASICCONFIG. If you do your basicconfig will 
# be ignored and your logs will drift away to mysterious
# netherworlds
#
# This is needed for the git describe to succeed
MYPATH = os.path.dirname(os.path.realpath(__file__))

# We live in ScreenDaemon/lib so we go up 2
ROOT = os.path.dirname(os.path.dirname(MYPATH))

UUID = False

_pinglock = Lock()
#_reading = 0.7

USER = os.environ.get('USER')
if not USER or USER == 'root':
  # This tool probably shouldn't be run as root but we should
  # know who we are talking about if it is
  USER = 'adorno'

SANITYCHECK = os.environ.get('SANITYCHECK')
NOMODEM = os.environ.get('NOMODEM')
CRASH = os.environ.get('CRASH')
DEBUG = os.environ.get('DEBUG')
DISPLAY = os.environ.get('DISPLAY')
BRANCH = os.environ.get('BRANCH')
LOG = os.environ.get('LOG') or '/var/log/screen'
CACHE = os.environ.get('CACHE') or '/var/cache/assets'
SERVER_URL = "http://{}/api".format(os.environ.get('SERVER') or 'waivescreen.com')

GPS_DEVICE_ACCURACY = 5.0 # Assumed, but not verified
GPGGA_FIELD_NAMES = ( 'utc_time', 'latitude', 'ns_indicator',
                      'longitude', 'ew_indicator', 'fix_quality',
                      'satellites_used', 'hdop', 'msl_altitude',
                      'units', 'geoid_separation', 'units',
                      'dgps', 'checksum' )
GPVTG_FIELD_NAMES = ( 'heading_true', 'true', 'heading_magnetic',
                      'magnetic', 'speed_knots', 'knots',
                      'speed_kph', 'kph', 'checksum' )

storage_base = '/var/lib/waivescreen/'

"""
  1. grabs data from the board, puts it in database
  2. serves things to screen display, getting it from the database
  3. talks to ad daemon using most recent data from database for lat/lng
"""

modem_iface = False
modem_ix = 0
modem_max = 4
modem_info = {}
modem_ison = False

_VERSION = False
def get_version():
  global _VERSION
  if not _VERSION:
    _VERSION = dcall("get_version").strip()
  return _VERSION

def get_modem(try_again=False, BUS=False):
  global modem_ison, modem_iface, modem_ix

  if not modem_ison:
    modem_ison = db.sess_get('modem') 

  if NOMODEM or not modem_ison:
    return {}

  if not BUS:
    BUS = dbus.SystemBus()
  
  # If we've found it previously than don't
  # worry looking.
  if modem_iface:
    return modem_iface

  # If we really tried to find it and couldn't
  if modem_ix == modem_max:
    # we have an option to run through things
    # again if someone tries to manually enable
    # the modem.
    if try_again:
      modem_ix = 0

    else:
      return False

  
  # Try modem_max eps to find a modem.
  for i in range(modem_ix, modem_max):
    ix = i % 2
    try: 
      proxy = BUS.get_object('org.freedesktop.ModemManager1','/org/freedesktop/ModemManager1/Modem/{}'.format(ix))
      modem_iface = {
        'proxy': proxy,
        'modem': dbus.Interface(proxy, dbus_interface='org.freedesktop.ModemManager1.Modem'),
        'sms': dbus.Interface(proxy, dbus_interface='org.freedesktop.ModemManager1.Modem.Messaging'),
        'device': dbus.Interface(proxy, dbus_interface='org.freedesktop.DBus.Properties'),
        'location': dbus.Interface(proxy, dbus_interface='org.freedesktop.ModemManager1.Modem.Location'),
        'time': dbus.Interface(proxy, dbus_interface='org.freedesktop.ModemManager1.Modem.Time')
      }
      proxy = BUS.get_object('org.freedesktop.ModemManager1','/org/freedesktop/ModemManager1/SIM/{}'.format(ix))
      modem_iface['sim'] = dbus.Interface(proxy, dbus_interface='org.freedesktop.DBus.Properties')

      modem_iface['modem'].Enable(True)
  
      # if we get here then we know that our modem works
      break
  
    except Exception as exc:
      time.sleep(1)
      modem_iface = False
      print(exc)
      pass

  return modem_iface

_bus = False
_loop = False
def get_message(dbus_path):
  global _bus

  raw_number = db.kv_get('number') or ''
  mynumber = "+{}".format( raw_number.strip('+') )
  proxy = str(dbus_path)
  smsindex = proxy.split('/')[-1]
  smsproxy = _bus.get_object('org.freedesktop.ModemManager1', proxy)
  iface = dbus.Interface(smsproxy, 'org.freedesktop.ModemManager1.Sms')
  ifaceone = dbus.Interface(smsproxy, 'org.freedesktop.DBus.Properties')
  fn = ifaceone.GetAll('org.freedesktop.ModemManager1.Sms')
  message = ''
  number = fn['Number'] 

  # pprint(json.dumps(fn))
  if fn['PduType'] == 2:
    try:
      iface.Send()

    except Exception as ex:
      logging.warning("Sending issue {}".format(ex)) 

    print("type=sent;dbuspath={}".format(proxy))

  else:
    if ';;' in fn['Text'] and fn['Text'].index(';;') == 0:
      # There's a possible boot-loop bug so we use the cleanup
      # trigger to avoid it
      if db.sess_get('cleanup'):
        klass = "cmd"
        res = dcall(fn['Text'][2:])
        modem = get_modem()
        if modem:
          modem['sms'].Create({'number': fn['Number'], 'text': res})

    # Makes sure that we are not reporting our own text
    else:
      klass = 'recv'
      if fn['Number'] == '+18559248355':
        message = fn['Text'].split(' ')[1]
        db.kv_set('number', message)

      else:
        prev_sms_list = db.find('history', {'type': 'sms', 'value': number})
        ident_count = 0
        message = fn['Text']
        if prev_sms_list:
          max_ident = 3
          for prev in prev_sms_list:
            ident_count += prev['extra'] == message

          if ident_count > max_ident:
            logging.warning("Found {} identical messages of '{}' from {}, ignoring.".format(ident_count, message, number))
            klass = 'ignore'


    add_history('sms', number, message)

    print("type={};sender={};message='{}';dbuspath={}".format(klass, number, base64.b64encode(message.encode('utf-8')).decode(), proxy))


def set_logger(logpath):
  from . import arduino

  # From https://stackoverflow.com/questions/1943747/python-logging-before-you-run-logging-basicconfig
  root = logging.getLogger()
  if root.handlers:
    for handler in root.handlers:
      root.removeHandler(handler)

  level = logging.DEBUG if DEBUG else logging.INFO
  format = '%(asctime)s %(levelname)s:%(message)s'

  if logpath == sys.stderr:
    logging.basicConfig(stream=logpath, format=format, level=level)

  else:
    try:
      logging.basicConfig(filename=logpath, format=format, level=level)

    except:
      os.system('/usr/bin/sudo /bin/mkdir -p {}'.format(os.path.dirname(logpath)))
      os.system('/usr/bin/sudo /usr/bin/touch {}'.format(logpath))
      os.system('/usr/bin/sudo chmod 0666 {}'.format(logpath))
      logging.basicConfig(filename=logpath, format=format, level=level)

  logger = logging.getLogger()
  arduino.set_log(logger)

def catchall_signal_handler(*args, **kwargs):
  from gi.repository import GLib
  global _loop
  get_message(args[0])
  GLib.MainLoop.quit(_loop)

def next_sms():
  global _bus, _loop

  from gi.repository import GLib
  import dbus.mainloop.glib
  myloop = dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

  _bus = dbus.SystemBus()
  proxy = _bus.get_object('org.freedesktop.ModemManager1','/org/freedesktop/ModemManager1/Modem/0')
  sms = dbus.Interface(proxy, dbus_interface='org.freedesktop.ModemManager1.Modem.Messaging')
  sms.connect_to_signal('Added', catchall_signal_handler)

  manager_proxy = _bus.get_object('org.freedesktop.ModemManager1','/org/freedesktop/ModemManager1')
  manager_iface = dbus.Interface(manager_proxy, dbus_interface='org.freedesktop.DBus.ObjectManager')
  obj = manager_iface.GetManagedObjects()
  service_dict = list(obj.values())[0]
  sms_list = service_dict.get('org.freedesktop.ModemManager1.Modem.Messaging').get('Messages')
  
  if len(sms_list) > 0:
    get_message(sms_list[-1])
    sys.exit(0)

  _loop = GLib.MainLoop()
  _loop.run()

def dcall(*kvarg, method='popen', what="dcall"):
  home = '/home/{}'.format(USER)
  dcall = '{}/{}'.format(home, what)
  res = ''

  if method == 'subprocess':
    subprocess.call([dcall] + [str(k) for k in kvarg])
  else: 
    with os.popen('{} {}'.format(dcall,' '.join([str(k) for k in kvarg]))) as fh:
      res = fh.read()

  return res


def post(url, payload):
  headers = {
   'User-Agent': get_uuid()
  }
  logging.info("{} {}".format(url, json.dumps(payload)))
  response = requests.post(urlify(url), verify=False, headers=headers, json=payload)
  logging.debug(response.text)
  return response


def update_gps_xtra_data():
  """ Download the GPS's Xtra assistance data and inject it into the gps. """
  modem = get_modem()
  if modem:
    try:
      xtra_servers = modem['device'].Get('org.freedesktop.ModemManager1.Modem.Location', 'AssistanceDataServers')
      for url in xtra_servers:
        r = requests.get(url)
        if r.status_code == 200:
          logging.info('Updating GPS Xtra Data')
          xtra_data = dbus.ByteArray(r.content)
          modem['location'].InjectAssistanceData(xtra_data) #TODO check return value
          return True
    except Exception as ex:
      logging.error('Failed to update GPS Xtra Data: {}'.format(ex))
  return False


def _get_gp_dict(nmea_string, gp_name, field_names):
  """ Parse the NMEA string from the GPS and return a Dict
  of the GP??? keys => values """
  gp_dict = {}
  gp_start = nmea_string.find('${}'.format(gp_name))
  gp_end = nmea_string.find('\r\n', gp_start)
  gp_string = nmea_string[gp_start:gp_end]
  for k, v in enumerate(gp_string.split(',')[1:]):
    gp_dict[field_names[k]] = v
  return gp_dict


def get_gpgga_dict(nmea_string):
  return _get_gp_dict(nmea_string, 'GPGGA', GPGGA_FIELD_NAMES)


def get_gpvtg_dict(nmea_string):
  return _get_gp_dict(nmea_string, 'GPVTG', GPVTG_FIELD_NAMES)


def gps_accuracy(nmea_string):
  gpgga = get_gpgga_dict(nmea_string)
  hdop = gpgga.get('hdop')
  if hdop:
    try:
      return GPS_DEVICE_ACCURACY * float(hdop)
    except:
      return None
  else:
    return None

def utc_secs(utc):
  secs = int(utc[4:6])
  secs += int(utc[2:4]) * 60
  secs += int(utc[0:2]) * 3600
  return secs

def gps_age(gps_secs):
  """ Return the age (in seconds) of the passed UTC timestamp """
  if gps_secs is not None:
    gps_utc_secs = utc_secs(gps_secs)
    my_utc_secs = utc_secs(time.strftime('%H%M%S'))
    # The GPS time is a 24-hour clock. If it's bigger than our local time, we probably just ticked over.
    if my_utc_secs < gps_utc_secs:
      gps_utc_secs -= 86400
    return my_utc_secs - gps_utc_secs
  else:
    return None

def get_gps(all_fields=False):
  modem = get_modem()

  if modem:
    try:
      location = modem['location'].GetLocation()

      gps = location.get(2)
      if not gps:
        return {}
      else:
        nmea_string = location.get(4, '')
        location_dict = {
          'Lat': gps['latitude'],
          'Lng': gps['longitude'],
          'accuracy': gps_accuracy(nmea_string),
          'age': gps_age(gps['utc-time'])
        }
        if all_fields:
          gpvtg = get_gpvtg_dict(nmea_string)
          location_dict.update( {
            'Utc': gps['utc-time'],
            'Nmea': nmea_string,
            '3gpp': location.get(1),
            'speed': gpvtg.get('speed_kph'),
            'heading': gpvtg.get('heading_true')
          } )
        return location_dict
    except Exception as ex:
      logging.warning("Modem issue {}".format(ex)) 

  return {}


def add_history(kind, value, extra = None):
  # This is kind of what we want..
  #if kind not in ['upgrade', 'feature', 'state']:
  #
  opts = { 'kind': kind, 'value': value }
  if extra is not None:
    opts['extra'] = extra

  return db.insert('history', opts)

def task_response(which, payload):
  db.update('command_history', {'ref_id': which}, {'response': payload})

  post('response', {
    'uid': get_uuid(),
    'task_id': which,
    'response': payload
  })

def task_ingest(data):
  #global _reading
  if 'taskList' not in data:
    return

  from . import arduino
  last_task = int(db.kv_get('last_task') or 0)

  for task in data.get('taskList'):
    logging.info("Doing task: {}".format(json.dumps(task)))

    id = task.get('id')

    if id <= last_task:
      continue

    db.kv_set('last_task', id)
    ## TODO: expiry check

    action = task.get('command')
    args = task.get('args')

    db.insert('command_history', {
      'ref_id': id,
      'command': action,
      'args': args
    })

    if action == 'upgrade':
      task_response(id, True)
      dcall("upgrade", method='subprocess')

    if action == 'dcall':
      task_response(id, dcall(args))

    elif action == 'screenoff':
      db.sess_set('force_sleep')
      #_reading = arduino.do_sleep()
      arduino.do_sleep()
      task_response(id, True)

    elif action == 'screenon':
      db.sess_del('force_sleep')
      #arduino.do_awake(_reading or 0.7)
      arduino.do_awake()
      task_response(id, True)

    elif action == 'autobright':
      db.sess_del('backlight')
      arduino.set_autobright()
      task_response(id, True)

    elif action == 'raw':
      task_response(id, os.popen(args).read().strip())

    elif action == 'brightness':
      val = float(args)
      #arduino.set_backlight(val)
      #dcall('set_brightness', val, 'nopy')

      # This becomes a ceiling until either we
      # call this again, call autobright (above)
      # or reboot
      db.sess_set('backlight', val)
      arduino.set_autobright()
      task_response(id, True)

    elif action == 'driving_upgrade':
      # By default driving_upgrade will trigger above 95 km/h unless a different
      # value is passed as an arg
      logging.info('driving_upgrade requested.')
      current_version = dcall('get_version').strip()
      db.kv_set('driving_upgrade', current_version)
      if args.isdigit():
        db.kv_set('driving_upgrade_speed', int(args))
      task_response(id, current_version)

def get_modem_info():
  global modem_info

  if not modem_info:
    modem = get_modem()

    if modem:
      props = modem['device'].GetAll('org.freedesktop.ModemManager1.Modem')
      sim = modem['sim'].GetAll('org.freedesktop.ModemManager1.Sim')

      modem_info = { 
        'imsi': sim.get('Imsi'),
        'icc': sim.get('SimIdentifier'),
        'imei': props.get('EquipmentIdentifier') 
      }
      numberList = props.get('OwnNumbers')

      if numberList:
        modem_info['phone'] = numberList[0]
      else:
        modem_info['phone'] = db.kv_get('number')

  return modem_info

  
def urlify(what):
  return "{}/{}".format(SERVER_URL, what)

def sensor_store(data):
  precision = {'Temp': 2, 'Current': 2, 'Voltage': 2, 'Tres': 0, 'Pitch': 3, 'Roll': 3, 'Yaw': 3, 'Lat': 4, 'Lng': 4 }
  for k,v in precision.items():
    if k in data:
      data[k] = round(data[k], v)

  return db.insert('sensor', data)

def sensor_last(index = False):
  res = db.run("select * from sensor order by id desc limit 1").fetchone()

  if not res:
    return {'Lat':False, 'Lng':False}
    # If we don't have a real sensor value then we just use 2102 pico in samo
    #return {'lat':34.019860, 'lng':-118.468477}

  return dict(res)

def campaign_store(data):
  return db.upsert('campaign', data)

def job_store(data):
  if 'campaign' in data:
    campaign_store(data['campaign'])
    del data['campaign']

  return db.upsert('job', data)

def job_get(index = False):
  return db.kv_get('job', index)

def get_port():
  port = db.kv_get('port')

  if not port:
    ping()
    port = db.kv_get('port')

  if not port:
    return ""

  return port

def update_number_if_needed():
  #if not db.sess_get('simok'):
  #  return None

  info = get_modem_info() or {}

  if 'number' in info:
    del info['number']

  # The first thing we do is clear out our old number.
  # And then to avoid clearing out a correct number but
  # going through this again, we then immediately set
  # our new icc, with an empty number.
  if db.kv_get('phone_icc') != info.get('icc'):
    db.kv_set('number', None) 

  #
  # DO NOT OPTIMIZE. WE DO NOT WANT THE PHONE NUMBER IN
  # THE INFO OBJECT TO BE SET HERE. REALLY, IT SHOULD
  # ABSOLUTELY NOT BE DONE HERE.
  #
  for k in ['imsi','icc','imei']:
    if k in info:
      db.kv_set('phone_{}'.format(k), info.get(k))

  return get_number()

def get_number():
  return re.sub('[^\d]', '', db.kv_get('number') or '')

def image_swapper(match):
  url = match.group(2)
  if url:
    logging.warning("Found image: {}".format(url))
    checksum_name = asset_cache(url, only_filename=True)
    return "{}{}".format(match.group(1), checksum_name)

  return ""

def asset_cache(check, only_filename=False, announce=False):
  import magic

  # Now we have the campaign in the database, yay us I guess
  if type(check) is str:
    check = { 'asset_meta': [{'url': check, 'nocache': True}] }

  path = CACHE
  if not os.path.exists(path):
    os.system('/usr/bin/sudo /bin/mkdir -p {}'.format(path))
    os.system('/usr/bin/sudo /bin/chmod 0777 {}'.format(path))


  res = []

  if 'asset_meta' not in check:
    logging.warning("Woops, couldn't find an asset meta in something I was told to cache")
    return check

  # Moving from asset -> asset_meta (2020-01-02)
  for row in check['asset_meta']:
    # checksum name (#188)
    # This will also truncate things after a ?, such as
    # image.jpg?uniqid=123...

    skipcache = row.get('nocache') # if it doesn't exist, it will default to false
    asset = row['url']
    ext = ''
    parts = re.search('(\.\w+)', asset.split('/')[-1])
    if parts:
      ext = parts.group(1)

    else:
      logging.warning("No extension found for {}".format(asset))

    if skipcache:
      res.append(row)

    else:
      checksum_name = "{}/{}{}".format(path, hashlib.md5(asset.encode('utf-8')).hexdigest(), ext)

      if (not os.path.exists(checksum_name)) or os.path.getsize(checksum_name) == 0:
        if announce:
          dcall("_bigtext", "Getting {}".format(announce))

        r = requests.get(asset, allow_redirects=True)
        logging.debug("Downloaded {} ({}b)".format(asset, len(r.content)))

        # If we are dealing with html we should also cache the assets
        # inside the html file.
        mime = magic.from_buffer(r.content, mime=True)
        if 'html' in mime:
          logging.info("parsing html")
          buf = str.encode(re.sub(r'(src\s*=["\']?)([^"\'>]*)', image_swapper, r.content.decode('utf-8')))

        else:
          buf = r.content

        # 
        # Since we are serving a file:/// then we don't have to worry
        # about putting shit in an accessible path ... we have the
        # whole file system to access.
        #
        open(checksum_name, 'wb').write(bytes(buf))

      else:
        # This is equivalent to a "touch" - used for a cache cleaning 
        # system
        try:
          with open(checksum_name, 'a'):
            os.utime(checksum_name, None)
        except:
          pass

      #
      # As it turns out, the browser thinks a file is text/plain unless
      # the server can give it a content-type or if served locally 
      # there's extension hinting.
      #
      # So what's that mean for us?! If we are looking at text/html
      # and we don't have an extension then we should either serve it
      # ourselves (unlikely) or just tack an extension on to it.
      #
      # But wait, we can't /just move/ the file otherwise our caching
      # system above would eat shit each time. So we exploit the fact
      # that hard drives are big and HTML files are small and we just
      # copy it over, insulting every programmer who used blood sweat
      # and tears to cram say 215 bytes to 211 in a bygone era.
      #
      mime = magic.from_file(checksum_name, mime=True)

      if row.get('duration'):
        duration = row['duration']
      elif 'html' in mime and 'html' not in checksum_name:
        import shutil
        happybrowser = "{}.html".format(checksum_name)
        if not os.path.exists(happybrowser):
          os.symlink(checksum_name, happybrowser)

        checksum_name = happybrowser
        duration = 150
      else:
        duration = 7.5

      if only_filename:
        return checksum_name

      # see #154 - we're restructuring this away from a string and
      # into an object - eventually we have to assume that
      # we're getting an object and then just injecting the mime
      # type on ... but not yet my sweetie.
      res.append({
        'duration': duration,
        'mime': mime,
        'url': checksum_name
      })

  check['asset'] = res
  return check

def campaign_cache(check):
  campaign = db.get('campaign', check['id'])
  if not campaign:
    campaign = db.insert('campaign', data['default'])

def ping_if_needed():
  last_ping = db.kv_get('lastping')
  if not last_ping or int(db.kv_get('runcount')) > int(last_ping):
    ping()

def get_uptime():
  # There's a few ways to do this.
  # We have a /tmp/startup that happens
  # when the machine comes up but we
  # also have an incrementing number in
  # /proc/uptime we can get - that's what
  # I'll do for now ... maybe something else
  # later
  return int(float(open('/proc/uptime').read().split(' ')[0]))
  
def ping():
  global _pinglock

  if not _pinglock.acquire(False):
    return True

  bootcount = int(db.get_bootcount())

  payload = {
    'uid': get_uuid(),
    'uptime': get_uptime(),
    'last_uptime': db.findOne('history', {'kind': 'boot_uptime', 'value': bootcount - 1}, fields='extra, created_at'),
    'bootcount': bootcount,
    'version': get_version(),
    'last_task': db.kv_get('last_task') or 0,
    'last_task_result': db.findOne('command_history', fields='ref_id, response, created_at'),
    'features': feature_detect(),
    'ping_count': db.sess_incr('ping_count'),
    'modem': get_modem_info(),
    'location': get_location(),
  }

  try: 
    with post('ping', payload) as response:
      data_raw = response.text
      try:
        data = json.loads(data_raw)
      except Exception as ex:
        data = False
        logging.warning("Unable to parse {}: {}".format(data_raw, ex))

      if data:
        # we have 
        # * this screen's info in "screen"
        # * the default campaign in "default"
  
        screen = data.get('screen') or {} 
        default = data.get('default') or {}

        for key in ['port','model','project','car','serial']:
          if key in screen:
            db.kv_set(key, screen[key])

        for key in ['bootcount','ping_count']:
          if key in screen:
            server_value = int(screen[key])
            my_value = int(db.kv_get(key) or 0)
            #
            # We want to accommodate for off-by-1 errors ... in fact, we only care if it looks like
            # it's clearly a different value ... this is in the case of a re-install.
            #
            if server_value > (3 + my_value):
              logging.warning("The server thinks my {} is {}, while I think it's {}. I'm using the server's value.".format(key, server_value, my_value))
              db.kv_set(key, server_value)
  
        db.kv_set('default', default.get('id'))
  
        # We run through it every time, should be fine
        default_campaign = asset_cache(default)
        campaign_store(default_campaign)

        db.kv_set('lastping', db.kv_get('runcount')) 

        task_ingest(data)

    _pinglock.release()

  except Exception as ex:
    _pinglock.release()
    logging.exception("ping issue: {}".format(ex)) 

    return False

def feature_detect():
  videoList = glob.glob("/dev/video*")
  hasSim = int(os.popen('mmcli -m 0 --output-keyvalue | grep sim | grep org | wc -l').read().strip())
  layout = dcall('camera_layout', what='perlcall')

  resolution_raw = os.popen("xrandr | grep connected | grep -Po '(\d+(?x))(\d+)'").read().strip()
  parts = [int(x) for x in resolution_raw.split('\n')]

  resolution_list = []
  size_list = []

  for i in range(0, len(parts), 4):
    resolution_list.append(parts[i:i+2])
    size_list.append(parts[i+2:i+4])

  # * btle - todo
  return {
    'modem'   : os.path.exists("/dev/cdc-wdm0") or os.path.exists('/dev/cdc-wdm1'),
    'arduino' : os.path.exists("/dev/ttyACM0"),
    'cameras' : int(len(videoList) / 2),
    'panels' : {
      'count': int(len(parts) / 4),
      'resolutions': resolution_list,
      'size': size_list 
    },
    'layout'  : layout,
    'wifi'    : os.path.exists("/proc/sys/net/ipv4/conf/wlp1s0"),
    'sim'     : hasSim > 0,
    'size'    : int(os.popen('df -m --output=size / | tail -1').read().strip())
  }

def get_uuid():
  global UUID
  
  if not UUID:
    if not os.path.isfile('/etc/UUID'):
      UUID="NONAME"
    else:
      with open('/etc/UUID') as f:
        UUID = f.read().strip()
       
  return UUID

def upgrades_to_run():
  upgrade_glob = "{}/Linux/upgrade/*.script".format(ROOT)
  last_upgrade_script = db.kv_get('last_upgrade', default='').split('/')[-1]
  pos = -1
  upgrade_list = sorted([s.split('/')[-1] for s in glob.glob(upgrade_glob)])

  if len(upgrade_list) == 0:
    logging.warning("Woops, couldn't find anything at {}".format(upgrade_glob))

  else:

    try:
      pos = upgrade_list.index(last_upgrade_script)
      pos += 1
    except Exception as ex:
      pos = 0

    to_run = upgrade_list[pos:]
    print(" ".join(to_run))
  
  
def disk_monitor(): 
  import pyudev
  import shutil

  context = pyudev.Context()
  monitor = pyudev.Monitor.from_netlink(context)

  for action, device in monitor:
    if action == 'add' and device.get('DEVTYPE') == 'partition':
      path = device.get('DEVNAME')
      print(path)
      sys.exit(0)

    elif action == 'bind' and device.get('DEVTYPE') == 'usb_device' and not db.sess_get('keyboard_allowed'): 
      if 'Keyboard' in (str(device.attributes.get('product')) or ''):
        dcall("_info", "Keyboard is disabled")


class Haversine:
  """
  use the haversine class to calculate the distance between
  two lon/lat coordnate pairs.
  output distance available in kilometers, meters, miles, and feet.
  example usage: Haversine([lon1,lat1],[lon2,lat2]).feet

  Source: https://github.com/nathanrooy/spatial-analysis/blob/master/haversine.py
  """
  def __init__(self,coord1,coord2):
    lon1,lat1=coord1
    lon2,lat2=coord2

    R=6371000                               # radius of Earth in meters
    phi_1=math.radians(lat1)
    phi_2=math.radians(lat2)

    delta_phi=math.radians(lat2-lat1)
    delta_lambda=math.radians(lon2-lon1)

    a=math.sin(delta_phi/2.0)**2+\
       math.cos(phi_1)*math.cos(phi_2)*\
       math.sin(delta_lambda/2.0)**2
    c=2*math.atan2(math.sqrt(a),math.sqrt(1-a))

    self.meters=R*c                         # output distance in meters
    self.km=self.meters/1000.0              # output distance in kilometers
    self.miles=self.meters*0.000621371      # output distance in miles
    self.feet=self.miles*5280               # output distance in feet

def get_location():
  try:
    gpgga = json.loads(db.kv_get('gps_gpgga'))
  except:
    gpgga = db.kv_get('gps_gpgga')

  location = {
    'Lat': db.kv_get('Lat'),
    'Lng': db.kv_get('Lng'),
    'accuracy': db.kv_get('location_accuracy'),
    'source': db.kv_get('location_source'),
    'time': db.kv_get('location_time'),
    'gps_gpgga': gpgga
  }
  return location

def save_location_now():
  """ Try and get the latest location from GPS and save it. """
  l = get_location_from_gps()
  if l:
    return save_location(l)
  else:
    return False

def get_latlng():
  lat = db.kv_get('Lat')
  lng = db.kv_get('Lng')
  if lat is None or lng is None:
    return {}
  else:
    return { 'Lat': float(lat), 'Lng': float(lng) }

def get_location_from_gps(exclude_age=5):
  l = get_gps(True)
  logging.debug('GPS Location Response: {}'.format(l))
  utc = l.get('Utc')
  age = l.get('age')
  accuracy = l.get('accuracy')
  if utc is None:
    logging.warning('GPS location has no UTC timestamp.')
    return False
  elif accuracy is None:
    logging.warning('GPS location has no accuracy.')
    return False
  elif float(accuracy) > 500.0:
    logging.warning('Ignoring GPS location with accuracy over 500.')
    return False
  elif age > exclude_age:
    logging.warning('Ignoring get_gps with stale UTC.')
    return False
  else:
    return l

def sanity_check(location):
  last_location_time = db.kv_get('location_time')
  if last_location_time is None:
    logging.warning('Last location time not saved in kv db (This should only happen ONCE)')
    return True
  time_diff = time.time() - float(last_location_time)
  if time_diff > 60 * 10:  # More than 10 minutes
    logging.info('Last location older than 10 minutes.')
    return True
  last_lat = db.kv_get('Lat')
  last_lng = db.kv_get('Lng')
  if last_lat is None or last_lng is None:
    logging.warning('Last location not in kv db. (This should only happen ONCE)')
    return True
  dist = Haversine([float(last_lng), float(last_lat)], [float(location['Lng']), float(location['Lat'])])
  miles_per_second = dist.miles / time_diff
  logging.debug('Calculated speed: {} miles/second, {} miles/hour'.format(miles_per_second, miles_per_second * (60 * 60)))
  logging.debug('last_lat:{} last_lng:{} lat:{} lng:{} dist.meters:{} dist.miles:{} time_diff:{}'.format(float(last_lat), \
                float(last_lng), float(location['Lat']), float(location['Lng']), dist.meters, dist.miles, time_diff))
  if miles_per_second > 150.0 / (60 * 60):  # Faster than 150 mph
    return False
  else:
    return True

def save_location(location):
  """ Save current location info to the database """
  if not sanity_check(location):
    logging.warning('New location failed sanity_check: {}'.format(location))
    return False
  db.insert( 'location', {
      'lat': location['Lat'],
      'lng': location['Lng'],
      'accuracy': location.get('accuracy', ''),
      'speed': location.get('speed', ''),
      'heading': location.get('heading', ''),
      'source': location_source() })
  logging.debug("Saving location: lat:{} lng:{} accuracy:{} utc:{} source:{}".format(location['Lat'], location['Lng'], location.get('accuracy'), location.get('Utc'), location_source()))
  db.kv_set('Lat', location['Lat'])
  db.kv_set('Lng', location['Lng'])
  db.kv_set('location_time', int(time.time()))
  db.kv_set('location_accuracy', location.get('accuracy', ''))
  db.kv_set('gps_gpgga', json.dumps(get_gpgga_dict(location.get('Nmea', ''))))
  if db.kv_get('send_location') is not None:
    send_location(location)
  return True

def location_source(set_it=False):
  if set_it:
    db.kv_set('location_source', set_it)
  else:
    return db.kv_get('location_source')

def send_location(location):
  payload = { 'uid': get_uuid(), 'lat': location['Lat'], 'lng': location['Lng'] }
  post('eagerlocation', payload)

def get_brightness_map():
  # Fallback map if we can't get the lat/long from GPS
  """
  default_brightness_map = [
    0.20, 0.08, 0.08, 0.08,  # 4am
    0.10, 0.30, 0.70, 0.90,  # 8am
    1.00, 1.00, 1.00, 1.00,  # 12pm
    1.00, 1.00, 1.00, 1.00,  # 4pm
    1.00, 0.90, 0.80, 0.70,  # 8pm
    0.50, 0.50, 0.40, 0.30,  # midnight
  ]
  """
  default_brightness_map = [
    0.60, 0.60, 0.60, 0.60,  # 4am
    0.60, 0.60, 0.60, 0.60,  # 8am
    0.60, 0.60, 0.60, 0.60,  # 12pm
    0.60, 0.60, 0.60, 0.60,  # 4pm
    0.60, 0.60, 0.60, 0.60,  # 8pm
    0.60, 0.60, 0.60, 0.60,  # midnight
  ]
  # Get dict of local dawn, sunrise, sunset dusk times in UTC
  suntimes = get_suntimes()
  if suntimes:
    logging.info('[autobright] Using suntimes')
    def hours_diff(t1, t2):
      return round((t1 - t2).seconds / 3600)

    night_brightness = 0.2      # Default nighttime brightness level
    transition_brightness = 0.6 # Default transition brightness level
    day_brightness = 1.0        # Default day brightness level
    dawn_len = hours_diff(suntimes['sunrise'], suntimes['dawn']) + 1
    day_len = hours_diff(suntimes['sunset'], suntimes['sunrise']) - 1
    dusk_len = hours_diff(suntimes['dusk'], suntimes['sunset']) + 1

    bmap = [transition_brightness] * dawn_len + \
           [day_brightness] * day_len + \
           [transition_brightness] * dusk_len
    bmap = bmap + [night_brightness] * (24 - len(bmap))
    # Calculate and rotate the map by dawn hour
    rotate_map_by = suntimes['dawn'].hour
    return bmap[-rotate_map_by:] + bmap[:-rotate_map_by]
  else:
    logging.info('[autobright] Using fallback')
    return default_brightness_map

def get_suntimes():
  # Attempt to get Lat/Long from GPS. On success,
  # return dict of local dawn, sunrise, sunset dusk times in UTC
  location = get_latlng()
  if location:
    db.sess_set('autobright')

    try:
      from astral import Astral
    except ImportError as ex:
      logging.warning("Failed to import astral module: {}".format(ex))
      return {}

    a = Astral()
    suntimes = a.sun_utc(datetime.today(), float(location['Lat']), float(location['Lng']))
    return suntimes
  else:
    return {}

def get_timezone():
  try:
    from timezonefinder import TimezoneFinder
  except ImportError as ex:
    logging.warning("Failed to import timezonefinder module: {}".format(ex))
    return None

  location = get_latlng()
  if location:
    return TimezoneFinder().timezone_at(lat=float(location['Lat']), lng=float(location['Lng']))
  else:
    return None

def modem_usage():
  """ Return the network traffic transfer totals for the modem in bytes """
  bytes_total = 0
  for bytes_path in glob.glob('/sys/class/net/ww[pa]*/statistics/??_bytes'):
    with open(bytes_path, 'r') as bytes_file:
      bytes_total += int(bytes_file.read())
  return bytes_total

def system_uptime():
  with open('/proc/uptime', 'r') as f:
    return float(f.readline().split(' ')[0])

def get_dpms_state(hdmi_port='both'):
  if hdmi_port == 'both':
    return ( get_dpms_state(1), get_dpms_state(2) )
  else:
    try:
      with open('/sys/class/drm/card0/card0-HDMI-A-{}/dpms'.format(hdmi_port), 'r') as f:
        return f.read().strip()
    except:
      return False

def update_modem_usage_log():
  bootcount = db.get_bootcount()
  modem_bytes = modem_usage()

  record = db.findOne('history', {'kind': 'modem_usage', 'value': bootcount})

  if not record:
    db.insert('history', {
      'kind': 'modem_usage',
      'value': bootcount,
      'extra': modem_bytes
    })

  else:
    db.update('history', {'kind': 'modem_usage', 'value': bootcount}, {'extra': modem_bytes})

def update_uptime_log():
  bootcount = db.get_bootcount()
  uptime = system_uptime()

  record = db.findOne('history', {'kind': 'boot_uptime', 'value': bootcount})

  if not record:
    db.insert('history', {
      'created_at': datetime.now() - timedelta(seconds=uptime),
      'kind': 'boot_uptime', 
      'value': bootcount, 
      'extra': uptime
    })

  else:
    db.update('history', {'kind': 'boot_uptime', 'value': bootcount}, {'extra': uptime})

def get_wifi_location():
  return wifi_location()

def calibrate_cameras():
  try:
    from . import camera
    camera.calibrate_cameras()
  except Exception as ex:
    logging.error('Failed to calibrate cameras with error: {}'.format(ex))

