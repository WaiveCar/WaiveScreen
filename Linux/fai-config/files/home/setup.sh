#!/bin/bash
if [ -e WaiveScreen ]; then
  cd WaiveScreen
  git pull
else  
  git clone git@github.com:WaiveCar/WaiveScreen.git
fi

cd WaiveScreen/ScreenDaemom
pip3 install -r requirements.txt 
ainsl ~demo/.bashrc 'PATH=$PATH:$HOME/.local/bin' 'HOME/.local/bin'
./ScreenDaemon.py &
