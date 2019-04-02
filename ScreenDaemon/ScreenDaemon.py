#!/usr/bin/python3

from flask import Flask, request, Response, jsonify
import json
import urllib
import lib.lib as lib
import logging

app = Flask(__name__)

def res(what):
  resp = jsonify(what)
  resp.headers.add('Access-Control-Allow-Origin', '*')
  return resp

def success(what):
  return res({ 'res': True, 'data': what })

def failure(what):
  return res({ 'res': False, 'data': what })

def get_location():
  return lib.sensor_last()

@app.route('/sow')
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
    'jobs': request.form
  }

  data = urllib.parse.urlencode(payload).encode()
  req  = urllib.request.Request('http://ads.waivecar.com/sow', data=data) 

  with urllib.request.urlopen(req) as response:
    data_raw = response.read().decode('utf-8')

    try:
      data = json.loads(data_raw)
    except:
      data = False
      logging.warn("Unable to parse {}".format(data_raw))

  if data:
    job_list = []
    if data['res']:
      for job in data['jobs']:
        job_list.append(job)
        lib.job_store(job)

      return success(job_list)
    else:
      return failure(data['data'])


  else:
    return failure("Got nothing back from the ad server")
    # now we ask the ad daemon for jobs given our lat/lng

if __name__ == '__main__':
  app.run(port=4096)
