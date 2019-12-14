#!/usr/bin/env python3
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import time
from multiprocessing import Process, Queue
    
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
qData = Queue()

@app.route('/hi')
def index():
  socketio.emit('ab', [1,23])
  return ""

@socketio.on('connect')
def connect():
  emit("ab", [1,2,3])

@socketio.on('disconnect')
def test_disconnect():
  print('Client disconnected')

@socketio.on('my event')
def test_message(message):
  emit('my response', [1,23])#, [a,b,c])
  #a, b, c = qData.get()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0')

