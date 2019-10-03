#!/usr/bin/env python3
import logging
from flask import Flask, send_from_directory, render_template
import os
import random

ROOT = os.path.dirname(os.path.realpath(__file__))
app = Flask(__name__)

@app.route('/<path:path>')
def serve(path):
  if os.path.exists("{}/templates/{}/index.html".format(ROOT, path)):
    return render_template(path + '/index.html', rand=random.random())

  elif os.path.exists("{}/{}".format(ROOT, path)):
    return send_from_directory(ROOT, path)

  else:
    logging.warning("Can't find {}/{}".format(ROOT,path))
    return "not found"

if __name__ == '__main__':
  app.run()
