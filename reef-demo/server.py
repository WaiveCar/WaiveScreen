from flask import Flask, send_from_directory, render_template
import os

app = Flask(__name__)

@app.route('/<path:path>')
def serve(path):
    return render_template(path + '/index.html')

if __name__ == '__main__':
  app.run()
