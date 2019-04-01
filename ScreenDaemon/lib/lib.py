#!/usr/bin/python3
from . import db
import configparser
import os

storage_base = '/var/lib/waivescreen/'
"""
  1. grabs data from the board, puts it in database
  2. serves things to screen display, getting it from the database
  3. talks to ad daemon using most recent data from database for lat/lng
"""

def sensor_store(data):
  return db.insert('sensor', data)

def sensor_last(index = False):
  res = db.get('sensor', index)
  # If we don't have a real sensor value then we just use 2102 pico
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

def get_uuid():
  import subprocess
  import json

  # TODO: FIX later
  return "YEZB0qB2Sk6GHGmY08gusQ"
  """
  fp = storage_base + 'config.ini'
  config = configparser.ConfigParser()
  if os.path.exists(fp):
    config.read(fp)
  
  m = subprocess.run(["/bin/ip","-j","-p","addr","show","enp3s0"], stdout=subprocess.PIPE)
  json = json.loads(m.stdout.decode('utf-8'))

  for iface in json:
      if 'address' in iface:
          return iface['address']
  """

