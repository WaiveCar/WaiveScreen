#!/usr/bin/python3

from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import json
import urllib
import lib.lib as lib
import lib.db as db
import lib.arduino as arduino
import logging
import pprint
import traceback
import os
import datetime
import time
import sys
from logging.handlers import RotatingFileHandler
from pdb import set_trace as bp


_reading = False
app = Flask(__name__)
DTFORMAT = '%Y-%m-%d %H:%M:%S.%f'
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

  return success({
    'campaign': campaign,
    'system': db.kv_get()
  })

@app.route('/sow', methods=['GET', 'POST'])
def next_ad(work = False):
  """
  For now we are going to do a stupid pass-through to the remote server
  and then just kinda return stuff. Keeping track of our own things 
  can be considered an optimization or at least a cache here... so those
  rules apply
  """

  # This is likely unnecessary.
  #
  # lib.ping_if_needed()

  # The first thing we get is the last known location.
  sensor = lib.sensor_last()
  payload = {
    'uid': lib.get_uuid(),
    'lat': db.kv_get('Lat'),
    'lng': db.kv_get('Lng')
  }

  db.kv_set('last_sow', int(time.time()))

  try:
    # we probably want a smarter way to do this.
    # probably from https://github.com/python-xlib/python-xlib
    dpms = os.popen('xset q').read().strip()[-2:]
    power = 'awake' if dpms == 'On' else 'sleep'

    if power != 'sleep':
      jobList = request.get_json()

      if type(jobList) is not list:
        jobList = [ jobList ]

      payload['jobs'] = jobList

      for i in range(len(jobList)):
        job = jobList[i]

        sensorList = [dict(x) for x in db.range('sensor', job['start_time'], job['end_time'])]
        job['sensor'] = sensorList

        # start_time and end_time are javascript epochs
        # so they are in millisecond
        job['start_time'] = datetime.datetime.utcfromtimestamp(job['start_time']/1000).strftime(DTFORMAT)
        job['end_time'] = datetime.datetime.utcfromtimestamp(job['end_time']/1000).strftime(DTFORMAT)

    payload['power'] = power
    payload['uid'] = lib.get_uuid()

  except Exception as ex:
    logging.warning("Error in getting ranges: {}".format(ex))
    pass

  data = False
  data_raw = False
  err = ''

  # This is a really retarded job queue system. Essentially we take our payload and always put it
  # in the queue.
  db.insert('queue', {'data': json.dumps(payload)})

  logging.debug(json.dumps(payload))

  try:
    for queuejob in db.all('queue'):
      payload = json.loads(queuejob['data'])
      with lib.post('sow', payload) as response:
        data_raw = response.text

        # we really only care about the last job ... 
        data = json.loads(data_raw)

        # Let's celebrate this is done.
        db.delete('queue', queuejob['id']) 

  except Exception as ex:
    data = False
    err = ex
    if data_raw:
      logging.warning("Unable to parse {}: {}".format(data_raw, ex))

  if data:
    try:
      job_list = []
      if data['res']:
        for job in data['data']:
          if job:
            # Here we cache the assets so the display is using
            # local copies so if all hell breaks lose and it
            # loses the cached copy or whatever, it won't matter.
            job = lib.asset_cache(job)

            #pprint.pprint(job)
            job_list.append(job)
            lib.job_store(job)

        lib.task_ingest(data)

        return success(job_list)
      else:
        return failure(data['data'])

    except Exception as ex:
      logging.warning("parsing issues?! {} {}".format(ex, data_raw))
      return failure({
        'payload': data
      })


  else:
    return failure('Error: {}'.format(err))

if __name__ == '__main__':

  db.kv_set('version', lib.VERSION)
  lib.set_logger('/var/log/screen/screendaemon.log')

  if lib.SANITYCHECK:
    sys.exit(0)

  # db.upgrade()
  db.incr('runcount')
  app.run(port=4096)
