#!/usr/bin/python3

from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import json
import urllib
import requests
import lib.lib as lib
import lib.db as db
import logging
import pprint
import traceback
import os
from logging.handlers import RotatingFileHandler


app = Flask(__name__)
CORS(app)

def res(what):
  return jsonify(what)

def success(what):
  return res({ 'res': True, 'data': what })

def failure(what):
  return res({ 'res': False, 'data': what })

def get_location():
  return lib.sensor_last()

@app.route('/default')
def default():
  attempted_ping = False
  campaign = False
  campaign_id = db.kv_get('default')

  # This means we probably haven't successfully pinged yet.
  if not campaign_id:
    lib.ping()
    attempted_ping = True
    campaign_id = db.kv_get('default')

  # Let's make sure we can pull it from the database
  if campaign_id:
    campaign = db.get('campaign', campaign_id)
    if not campaign:
      lib.ping()
      attempted_ping = True
      campaign = db.get('campaign', campaign_id)

  if not attempted_ping:
    lib.ping_if_needed()

  if not campaign:
    # Things aren't working out for us
    return failure("Cannot contact server")

  return success(campaign)

@app.route('/sow', methods=['GET', 'POST'])
def next_ad(work = False):
  """
  For now we are going to do a stupid pass-through to the remote server
  and then just kinda return stuff. Keeping track of our own things 
  can be considered an optimization or at least a cache here... so those
  rules apply
  """

  lib.ping_if_needed()

  # The first thing we get is the last known location.
  sensor = lib.sensor_last()
  payload = {
    'uid': lib.get_uuid(),
    'lat': sensor['lat'],
    'lng': sensor['lng']
  }
  try:
    jobList = request.get_json()
    if type(jobList) is not list:
      jobList = [ jobList ]

    payload['jobs'] = jobList

  except:
    pass

  data = False
  try:
    with requests.post(lib.urlify('sow'), verify=False, json=payload) as response:
      data_raw = response.text
      data = json.loads(data_raw)

  except:
    data = False
    if data_raw:
      logging.warn("Unable to parse {}".format(data_raw))

  if data:
    try:
      job_list = []
      if data['res']:
        for job in data['data']:
          if job:
            # Here we cache the assets
            # so the display is using
            # local copies so if all
            # hell breaks lose and it
            # loses the cached copy or
            # whatever, it won't matter.
            job = lib.asset_cache(job)

            pprint.pprint(job)
            job_list.append(job)
            lib.job_store(job)

        if 'task' in data:
          if data['task'] == 'upgrade':
            lib.ping()

        return success(job_list)
      else:
        return failure(data['data'])

    except Exception as ex:
      pprint.pprint([ex, traceback.format_exc()])
      return failure({
        'payload': data
      })


  else:
    # We just can't contact the server that's fine
    pass

if __name__ == '__main__':

  if os.path.exists('/home/adorno'):
    logpath = '/home/adorno'
  else:
    logpath = os.getenv('HOME')

  if os.getenv('DEBUG'):
    level = logging.DEBUG
  else:
    level = logging.WARN

  logging.basicConfig(filename='/var/log/screen/screendaemon.log', format='%(asctime)-15s %(levelname)s %(message)s', level=level)

  # db.upgrade()
  db.incr('runcount')
  app.run(port=4096)
