#!/usr/bin/python3
from . import db
import configparser
import os
import requests

# Eventually we can change this but right now nothing is live
server_url = 'http://waivescreen.com/api/'
# We aren't always calling from something with flask
if 'app' in dir():
  server_url = 'http://waivescreen.com/api/' if app.config['ENV'] == 'development' else 'http://waivescreen.com/api/'

storage_base = '/var/lib/waivescreen/'

"""
  1. grabs data from the board, puts it in database
  2. serves things to screen display, getting it from the database
  3. talks to ad daemon using most recent data from database for lat/lng
"""

UUID=False

def sensor_store(data):
  return db.insert('sensor', data)

def sensor_last(index = False):
  res = db.get('sensor', index)
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
  return db.get('job', index)

def ping():
  uid = get_uuid()
  print(uid)

def get_uuid():
  global UUID
  
  if not UUID:
    if not os.path.isfile('/etc/UUID'):
      UUID="NONAME"
    else:
      with open('/etc/UUID') as f:
        UUID = f.read().strip()
       
  return UUID
