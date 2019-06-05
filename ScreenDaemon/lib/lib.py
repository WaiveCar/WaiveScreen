#!/usr/bin/python3
from . import db
import configparser
import os
import requests
import json
import dbus
import time
import logging
import sys
from threading import Lock
from pprint import pprint

# This is needed for the git describe to succeed
MYPATH = os.path.dirname(os.path.realpath(__file__))
os.chdir(MYPATH)
VERSION = os.popen("/usr/bin/git describe").read().strip()

# The unix time of the last commit
VERSIONDATE = os.popen("/usr/bin/git log -1 --format='%at'").read().strip()

UUID = False
BUS = dbus.SystemBus()

_pinglock = Lock()

if os.environ['USER'] == 'root':
  # This tool probably shouldn't be run as root but we should
  # know who we are talking about if it is
  USER = 'adorno'
else:
  USER = os.environ['USER']

NOMODEM = os.environ.get('NOMODEM')
DEBUG = os.environ.get('DEBUG')

if 'SERVER' in os.environ:
  SERVER_URL = os.environ['SERVER']
  logging.info("Using {} as the server as specified in the server shell env variable")
else:
  # Eventually we can change this but right now nothing is live
  SERVER_URL = 'http://waivescreen.com/api'

  # We aren't always calling from something with flask
  if 'app' in dir() and app.config['ENV'] == 'development':
    SERVER_URL = 'http://waivescreen.com/api' 

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
def get_modem(try_again=False):
  if NOMODEM:
    return {}

  global modem_iface, modem_ix
  
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


def dcall(*kvarg):
  home = '/home/{}'.format(USER)
  dcall = '{}/dcall'.format(home)
  os.popen('{} {}'.format(dcall,' '.join([str(k) for k in kvarg])))

def get_gps():
  modem = get_modem()

  if modem:
    try:
      location = modem['location'].GetLocation()

      gps = location.get(2)
      if not gps:
        return { }
      else:
        return {
          'Lat': gps['latitude'],
          'Lng': gps['longitude']
        }
    except Exception as ex:
      logging.warning("Modem issue {}".format(ex)) 

  return {}


def task_ingest(data):
  if 'task' not in data:
    return

  for action, args in data['task']:
    if action == 'upgrade':
      lib.ping()

    elif action == 'screenoff':
      global _reading
      _reading = arduino.do_sleep()

    elif action == 'screenon':
      arduino.do_awake(_reading)

    elif action == 'reboot':
      os.system('/usr/bin/sudo /sbin/reboot')

    elif action == 'brightness':
      val = float(args)
      arduino.set_backlight(val)
      dcall('set_brightness', val, 'nopy')


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

  return modem_info

  
def urlify(what):
  return "{}/{}".format(SERVER_URL, what)

def sensor_store(data):

  precision = {'Temp': 2, 'Current': 2, 'Voltage': 2, 'Tres': 0, 'Pitch': 3, 'Roll': 3, 'Yaw': 3, 'Lat': 4, 'Lng': 4 }
  for k,v in precision.items():
    if k in data:
      data[k] = round(data[k], v)

  toInsert = {
    'raw': json.dumps(data)
  }
  return db.insert('sensor', toInsert)

def sensor_last(index = False):
  res = db.kv_get('sensor', index)
  # If we don't have a real sensor value then we just use 2102 pico in samo
  if not res:
    return {'lat':False, 'lng':False}
    #return {'lat':34.019860, 'lng':-118.468477}

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


def asset_cache(check):
  #
  # Now we have the campaign in the database, yay us I guess
  # On the FAi partition, assuming we have 2, most crap goes
  # into the home directory which can derive from our global
  # USER variable
  #
  path = "/home/{}/assets".format(USER)

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

def ping():
  global _pinglock

  if not _pinglock.acquire(False):
    return True

  payload = {
    'uid': get_uuid(),
    'version': VERSION,
    **get_modem_info()
  }

  try: 
    with requests.post(urlify('ping'), verify=False, json=payload) as response:
      data_raw = response.text
      try:
        data = json.loads(data_raw)
      except:
        data = False
        logging.warning("Unable to parse {}".format(data_raw))

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

        if data['version_date'] <= VERSIONDATE:
          logging.debug("Us: {} {}, server: {} {}".format(VERSION, VERSIONDATE, data['version'], data['version_date']))
        else:
          logging.warning("This is {} but {} is available".format(VERSION, data['version']))
          # This means we can upgrade.
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

            # Now we ask the shell to do the upgrade
            # a bunch of assumptions are being done here.
            os.chdir('/home/{}'.format(USER))
            os.system('./dcall upgrade &')

        task_ingest(data)

    _pinglock.release()

  except Exception as ex:
    _pinglock.release()
    if DEBUG:
      raise ex

    return False


def get_uuid():
  global UUID
  
  if not UUID:
    if not os.path.isfile('/etc/UUID'):
      UUID="NONAME"
    else:
      with open('/etc/UUID') as f:
        UUID = f.read().strip()
       
  return UUID

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

