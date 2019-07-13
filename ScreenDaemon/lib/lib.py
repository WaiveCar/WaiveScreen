#!/usr/bin/python3
from . import db
import configparser
import os
import requests
import re
import json
import dbus
import time
import logging
import sys
import glob
import base64
import subprocess
from threading import Lock
from pprint import pprint

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

os.chdir(MYPATH)
VERSION = os.popen("/usr/bin/git describe").read().strip()

# The unix time of the last commit
VERSIONDATE = os.popen("/usr/bin/git log -1 --format='%at'").read().strip()

UUID = False

_pinglock = Lock()

USER = os.environ.get('USER')
if not USER or USER == 'root':
  # This tool probably shouldn't be run as root but we should
  # know who we are talking about if it is
  USER = 'adorno'

SANITYCHECK = os.environ.get('SANITYCHECK')
NOMODEM = os.environ.get('NOMODEM')
DEBUG = os.environ.get('DEBUG')
SERVER_URL = os.environ.get('SERVER_URL') or 'http://waivescreen.com/api'

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

  # pprint(json.dumps(fn))
  if fn['PduType'] == 2:
    try:
      iface.Send()

    except Exception as ex:
      logging.warning("Sending issue {}".format(ex)) 

    print("type=sent;dbuspath={}".format(proxy))

  else:
    if ';;' in fn['Text'] and fn['Text'].index(';;') == 0:
      klass="cmd"
      res = dcall(fn['Text'][2:])
      modem = get_modem()
      if modem:
        modem['sms'].Create({'number': fn['Number'], 'text': res})

    # Makes sure that we are not reporting our own text
    else:
      klass='recv'
      if fn['Number'] == '+18559248355':
        message = fn['Text'].split(' ')[1]
        db.kv_set('number', message)

      else:
        message = fn['Text']

    print("type={};sender={};message='{}';dbuspath={}".format(klass, fn['Number'], base64.b64encode(message.encode('utf-8')).decode(), proxy))


def catchall_signal_handler(*args, **kwargs):
  from gi.repository import GLib
  global _loop
  get_message(args[0])
  GLib.MainLoop.quit(_loop)

def next_sms():
  global _bus
  global _loop
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

def dcall(*kvarg, method='popen'):
  home = '/home/{}'.format(USER)
  dcall = '{}/dcall'.format(home)
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
  return requests.post(urlify(url), verify=False, headers=headers, json=payload)

def get_gps():
  modem = get_modem()

  if modem:
    try:
      location = modem['location'].GetLocation()

      gps = location.get(2)
      if not gps:
        return {}

      else:
        return {
          'Lat': gps['latitude'],
          'Lng': gps['longitude']
        }
    except Exception as ex:
      logging.warning("Modem issue {}".format(ex)) 

  return {}


def task_response(which, payload):
  post('response', {
    'uid': get_uuid(),
    'task_id': which,
    'response': payload
  })

def task_ingest(data):
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

    if action == 'upgrade':
      dcall("upgrade &")

    if action == 'dcall':
      task_response(id, dcall(args))

    elif action == 'screenoff':
      db.sess_set('force_sleep')
      global _reading
      _reading = arduino.do_sleep()
      task_response(id, True)

    elif action == 'screenon':
      db.sess_del('force_sleep')
      arduino.do_awake(_reading)
      task_response(id, True)

    elif action == 'reboot':
      # we respond before we do it, probably a bad idea
      task_response(id, True)
      os.system('/usr/bin/sudo /sbin/reboot')

    elif action == 'autobright':
      db.sess_del('backlight')
      arduino.set_autobright()
      task_response(id, True)

    elif action == 'raw':
      task_response(id, os.popen(args).read().strip())

    elif action == 'brightness':
      val = float(args)
      arduino.set_backlight(val)
      dcall('set_brightness', val, 'nopy')

      # This becomes a ceiling until either we
      # call this again, call autobright (above)
      # or reboot
      db.sess_set('backlight', val)
      task_response(id, True)


def get_modem_info():
  global modem_info

  if not modem_info:
    modem = get_modem()

    if modem:
      props = modem['device'].GetAll('org.freedesktop.ModemManager1.Modem')

      modem_info = {}

      modem_info = { 'imei': props.get('EquipmentIdentifier') }
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

def get_number():
  return re.sub('[^\d]', '', db.kv_get('number') or '')

def asset_cache(check):
  #
  # Now we have the campaign in the database, yay us I guess
  # On the FAi partition, assuming we have 2, most crap goes
  # into the home directory which can derive from our global
  # USER variable
  #
  path = "/var/cache/assets"
  if not os.path.exists(path):
    os.system('/usr/bin/sudo /bin/mkdir -p {}'.format(path))
    os.system('/usr/bin/sudo /bin/chmod 0777 {}'.format(path))


  res = []
  for asset in check['asset']:
    name = "{}/{}".format(path, asset.split('/')[-1])
    if not os.path.exists(name):
      r = requests.get(asset, allow_redirects=True)
      # 
      # Since we are serving a file:/// then we don't have to worry
      # about putting shit in an accessible path ... we have the
      # whole file system to access.
      #
      open(name, 'wb').write(r.content)

    else:
      # This is equivalent to a "touch" - used for a cache cleaning 
      # system
      try:
        with open(name, 'a'):
          os.utime(name, None)
      except:
        pass

    res.append(name)

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

  payload = {
    'uid': get_uuid(),
    'uptime': get_uptime(),
    'version': VERSION,
    'version_time': VERSIONDATE,
    'last_task': db.kv_get('last_task') or 0,
    'features': feature_detect(),
    'modem': get_modem_info(),
    'gps': get_gps(),
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
        #
        #  * this screen's info in "screen"
        #  * the default campaign in "default"
        #  * software version in "version"
        #
  
        db.kv_set('port', data['screen']['port'])
  
        # set the default campaign
        db.kv_set('default', data['default']['id'])
  
        if not db.get('campaign', data['default']['id']):
          default = asset_cache(data['default'])
          db.insert('campaign', default)

        db.kv_set('lastping', db.kv_get('runcount')) 

        if int(data['version_date']) <= int(VERSIONDATE):
          logging.debug("Us: {} {}, server: {} {}".format(VERSION, VERSIONDATE, data['version'], data['version_date']))
        else:
          logging.warning("This is {} but {} is available".format(VERSION, data['version']))
          # This means we can .
          #
          # We need to make sure that a failed
          # upgrade doesn't send us in some kind
          # of crazy upgrade loop where we constantly
          # try to restart things.
          #
          version = db.kv_get('version_date')
          if version and version >= data['version_date']:
            logging.warning("Not upgrading to {}. We attempted to do it before ({}={})".format(VERSION, version,  data['version_date']))

          else:
            # Regardless of whether we succeed or not
            # we store this latest version as the last
            # version we *attempted* to upgrade to
            # in order to avoid the aforementioned 
            # issue
            db.kv_set('version_date', data['version_date'])
            logging.info("Upgrading from {} to {}. So long.".format(VERSION, data['version']))

            dcall("upgrade &")

        task_ingest(data)

    _pinglock.release()

  except Exception as ex:
    _pinglock.release()
    logging.warning("ping issue {}".format(ex)) 

    return False

def acceptance_test():
  from . import arduino
  arduino.test('fb')
  dcall('_warn', 'phone:{}'.format( db.kv_get('number')), method='subprocess')
  dcall('_warn', 'camera:{}'.format( dcall('capture_all_cameras') ), method='subprocess')

def feature_detect():
  videoList = glob.glob("/dev/video*")
  hasSim = int(os.popen('mmcli -m 0 --output-keyvalue | grep sim | grep org | wc -l').read().strip())

  # * btle - todo
  return {
    'modem'   : os.path.exists("/dev/cdc-wdm0") or os.path.exists('/dev/cdc-wdm1'),
    'arduino' : os.path.exists("/dev/ttyACM0"),
    'cameras' : int(len(videoList) / 2),
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
  last_upgrade_script = db.kv_get('last_upgrade')
  pos = -1
  upgrade_list = sorted(glob.glob(upgrade_glob))

  if len(upgrade_list) == 0:
    logging.warning("Woops, couldn't find anything at {}".format(upgrade_glob))

  else:

    try:
      pos = upgrade_list.index(last_upgrade_script)
    except Exception as ex:
      pos = -1
      
    pos += 1

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
      #dcall('local_upgrade', path, '&')

