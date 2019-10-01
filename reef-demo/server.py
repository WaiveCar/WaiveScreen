from flask import Flask, send_from_directory, render_template
import os

app = Flask(__name__, static_folder='./')

@app.route('/')
def serve(route_path=None):
  return render_template('base.html')

if __name__ == '__main__':
  app.run()
