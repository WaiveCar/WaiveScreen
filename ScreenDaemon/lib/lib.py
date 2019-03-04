#!/usr/bin/python3
import db


"""
  1. grabs data from the board, puts it in database
  2. serves things to screen display, getting it from the database
  3. talks to ad daemon using most recent data from database for lat/lng
"""

def sensor_store(data):
  return db.insert('sensor', data)

def sensor_last(index = 0):
  return run('select * from sensor order by id desc limit 1').fetchone()

def job_store(data):
    pass

def job_get(index = 0):
    pass
