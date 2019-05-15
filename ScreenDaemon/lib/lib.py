#!/usr/bin/python3
from . import db
import configparser
import os
import requests
import json
import dbus
from pprint import pprint

VERSION = os.popen("/usr/bin/git describe").read().strip()
UUID = False
BUS = dbus.SystemBus()

# Eventually we can change this but right now nothing is live
SERVER_URL = 'http://www.waivescreen.com/api/'

# We aren't always calling from something with flask
if 'app' in dir() and app.config['ENV'] == 'development':
  SERVER_URL = 'http://www.waivescreen.com/api/' 

storage_base = '/var/lib/waivescreen/'

"""
  1. grabs data from the board, puts it in database
  2. serves things to screen display, getting it from the database
  3. talks to ad daemon using most recent data from database for lat/lng
"""

modem_iface = False
modem_ix = 0
modem_max = 10
modem_info = {}
def get_modem(try_again=False):
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
    try: 
      proxy = BUS.get_object('org.freedesktop.ModemManager1','/org/freedesktop/ModemManager1/Modem/{}'.format(i))
      modem_iface = {
        'proxy': proxy,
        'device': dbus.Interface(proxy, dbus_interface='org.freedesktop.DBus.Properties'),
        'location': dbus.Interface(proxy, dbus_interface='org.freedesktop.ModemManager1.Modem.Location'),
        'time': dbus.Interface(proxy, dbus_interface='org.freedesktop.ModemManager1.Modem.Time')
      }
      modem_iface['location'].GetLocation()
  
      # if we get here then we know that our modem works
      break
  
    except Exception as exc:
      print(exc)
      pass

  return modem_iface


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
    return {'lat':34.019860, 'lng':-118.468477}

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



def ping():
  payload = {
    'uid': get_uuid(),
    'version': VERSION,
    **get_modem_info
  }

  with requests.post(urlify('ping'), verify=False, json=payload) as response:
    data_raw = response.text
    try:
      data = json.loads(data_raw)
    except:
      data = False
      logging.warn("Unable to parse {}".format(data_raw))

    if data:
      db.kv_set('port', data['port'])

def get_uuid():
  global UUID
  
  if not UUID:
    if not os.path.isfile('/etc/UUID'):
      UUID="NONAME"
    else:
      with open('/etc/UUID') as f:
        UUID = f.read().strip()
       
  return UUID
