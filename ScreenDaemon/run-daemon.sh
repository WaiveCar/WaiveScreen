#!/bin/bash
sudo chown root sensor-store.py
sudo chmod +s sensor-store.py
./sensor-store.py&

FLASK_ENV=development ./ScreenDaemon.py
