#!/usr/bin/python3

from flask import Flask, request
import json
import urllib
import lib.lib as lib

app = Flask(__name__)

def sucess(what):
  return { 'res': true, 'data': what }

def get_location():
  return lib.sensor_last()

@app.route('/sow')
def next_ad(work):
  """
  For now we are going to do a stupid pass-through to the remote server
  and then just kinda return stuff. Keeping track of our own things 
  can be considered an optimization or at least a cache here... so those
  rules apply
  """

  # The first thing we get is the last known location.
  sensor = lib.sensor_last()

  payload = {
    'id': lib.get_uuid(),
    'lat': sensor['lat'],
    'lng': sensor['lng'],
    'jobs': request.form
  }

  data = urllib.parse.urlencode(payload).encode()
  req  = urllib.request.Request('http://ads.waivecar.com/sow', data=data) 

  with urllib.request.urlopen(req) as response:
    data_raw = response.read()

    try:
      data = json.load(data_raw)
    except:
      logging.warn("Unable to parse {}".format(data_raw))

  job_list = []
  if data['res']:
    for job in data['jobs']:
      job_list.append(job)
      lib.job_store(job)

  return success(job_list)
  # now we ask the ad daemon for jobs given our lat/lng
