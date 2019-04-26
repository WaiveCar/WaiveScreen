#!/bin/bash
if [ -e WaiveScreen ]; then
  cd WaiveScreen
  git pull
else  
  git clone git@github.com:WaiveCar/WaiveScreen.git
  ainsl ~demo/.bashrc 'PATH=$PATH:$HOME/.local/bin' 'HOME/.local/bin'
fi

UUID=/etc/UUID
if [ ! -e $UUID ] ; then
  sudo dmidecode -t 4 | grep ID | sed -E s'/ID://;s/\s//g' | sudo tee $UUID
fi

cd WaiveScreen/ScreenDaemom
pip3 install -r requirements.txt 
#./ScreenDaemon.py &
