#!/usr/bin/python3
from . import db
import configparser
import os
import requests
import json
import dbus
import time
import logging
from pprint import pprint

# This is needed for the git describe to succeed
os.chdir(os.path.dirname(os.path.realpath(__file__)))
VERSION = os.popen("/usr/bin/git describe").read().strip()

UUID = False
BUS = dbus.SystemBus()


if os.environ['USER'] == 'root':
  # This tool probably shouldn't be run as root but we should
  # know who we are talking about if it is
  USER = 'adorno'
else:
  USER = os.environ['USER']

NOMODEM = 'NOMODEM' in os.environ
DEBUG = 'DEBUG' in os.environ

if 'SERVER' in os.environ:
  SERVER_URL = os.environ['SERVER']
  logging.info("Using {} as the server as specified in the server shell env variable")
else:
  # Eventually we can change this but right now nothing is live
  SERVER_URL = 'http://waivescreen.com/api/'

  # We aren't always calling from something with flask
  if 'app' in dir() and app.config['ENV'] == 'development':
    SERVER_URL = 'http://waivescreen.com/api/' 

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


def get_gps():
  modem = get_modem()

  if modem:
    location = modem['location'].GetLocation()
    networktime = modem['time'].GetNetworkTime()
    if '2' not in location:
      return { 'time': networktime }
    else:
      return {
        'Altitude': location[2]['altitude'],
        'Latitude': location[2]['latitude'],
        'Longitude': location[2]['longitude'],
        'GPS_time': location[2]['utc-time'],
        'Time': networktime[0]
      }
  return {}



def get_modem_info():
  global modem_info

  if not modem_info:
    modem = get_modem()

    if modem:
      props = modem['device'].GetAll('org.freedesktop.ModemManager1.Modem')

      modem_info = {
       'phone': props['OwnNumbers'][0],
       'imei': props['EquipmentIdentifier']
      }

  return modem_info

  
def urlify(what):
  return "{}/{}".format(SERVER_URL, what)

def sensor_store(data):
  return db.insert('sensor', data)

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

def emit_startup():
  # Contact the server, get the port if needed
  ping()
  port = db.kv_get('port')
  print("ssh -f -NC -R bounce:{}:127.0.0.1:22 bounce".format(port))


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

def ping():
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
        logging.warn("Unable to parse {}".format(data_raw))
  
      if data:
        # we have 
        #
        #  * this screen's info in "screen"
        #  * the default campaign in "default"
        #  * software version in "version"
        #
        if data['version'] != VERSION:
          # TODO we need to do better than this bullshit
          logging.warn("This is {} but {} is available".format(VERSION, data['version']))
  
        db.kv_set('port', data['screen']['port'])
  
        # set the default campaign
        db.kv_set('default', data['default']['id'])
  
        if not db.get('campaign', data['default']['id']):
          default = asset_cache(data['default'])
          db.insert('campaign', default)
  except Exception as ex:
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
