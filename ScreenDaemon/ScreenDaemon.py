#!/usr/bin/python3

from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import json
import urllib
import lib.lib as lib
import logging
import pprint
import traceback

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

def url(what):
  return "{}/{}".format('http://ads.waivecar.com/api' if app.config['ENV'] == 'development' else 'https://ad.waivecar.com/api', what)

@app.route('/sow', methods=['GET', 'POST'])
def next_ad(work = False):
  """
  For now we are going to do a stupid pass-through to the remote server
  and then just kinda return stuff. Keeping track of our own things 
  can be considered an optimization or at least a cache here... so those
  rules apply
  """


  # The first thing we get is the last known location.
  sensor = lib.sensor_last()

  payload = {
    'uid': lib.get_uuid(),
    'lat': sensor['lat'],
    'lng': sensor['lng'],
    'jobs': request.get_json()
  }

  data = urllib.parse.urlencode(payload).encode()

  with urllib.request.urlopen(url('sow'), data=data) as response:
    data_raw = response.read().decode('utf-8')

    try:
      data = json.loads(data_raw)
    except:
      data = False
      logging.warn("Unable to parse {}".format(data_raw))

  if data:
    try:
      job_list = []
      if data['res']:
        for job in data['data']:
          job_list.append(job)
          lib.job_store(job)

        return success(job_list)
      else:
        return failure(data['data'])

    except Exception as ex:
      pprint.pprint([ex, traceback.format_exc()])
      return failure({
        'payload': data
      })


  else:
    return failure("Got nothing back from the ad server")
    # now we ask the ad daemon for jobs given our lat/lng

if __name__ == '__main__':
  app.run(port=4096)
