#!/usr/bin/python3

from flask import Flask
import lib.db as db
import lib.lib as lib

app = Flask(__name__)

def get_location():
  return lib.sensor_last()

@app.route('/next-ad')
def next_ad():
  return 'Hello, World!'


