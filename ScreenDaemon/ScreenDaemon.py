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
from pdb import set_trace as bp


_reading = False
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

  # This is likely unnecessary.
  #
  # lib.ping_if_needed()

  # The first thing we get is the last known location.
  sensor = lib.sensor_last()
  payload = {
    'uid': lib.get_uuid(),
    'lat': sensor.get('Lat'),
    'lng': sensor.get('Lng')
  }

  try:
    if db.sess_get('power') != 'sleep':
      jobList = request.get_json()

      if type(jobList) is not list:
        jobList = [ jobList ]

      payload['jobs'] = jobList

      for i in range(len(jobList)):
        job = jobList[i]

        sensorList = [dict(x) for x in db.range('sensor', job['start_time'], job['end_time'])]
        job['sensor'] = sensorList

    payload['power'] = db.sess_get('power')

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
    for job in db.all('queue'):
      payload = json.loads(job['data'])
      with requests.post(lib.urlify('sow'), verify=False, json=payload) as response:
        data_raw = response.text

        # we really only care about the last job ... 
        data = json.loads(data_raw)

        # Let's celebrate this is done.
        db.delete('queue', job['id']) 

  except Exception as ex:
    data = False
    err = ex
    if data_raw:
      logging.warning("Unable to parse {}".format(data_raw))

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
    return failure('Error: {}'.format(ex))

if __name__ == '__main__':

  level = logging.DEBUG if os.getenv('DEBUG') else logging.WARN
  format='%(levelname)s@%(lineno)d:%(message)s'
  logpath='/var/log/screen/screendaemon.log'
  try:
    logging.basicConfig(filename=logpath, format=format, level=level)

  except:
    os.system('/usr/bin/sudo chmod 0666 {}'.format(logpath))
    logging.basicConfig(filename=logpath, format=format, level=level)


  # db.upgrade()
  db.incr('runcount')
  app.run(port=4096)
