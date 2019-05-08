#!/bin/bash
sudo ./sensor-store.py&

FLASK_ENV=development ./ScreenDaemon.py
