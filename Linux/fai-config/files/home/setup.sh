#!/bin/bash
git() {
  if [ -e WaiveScreen ]; then
    cd WaiveScreen
    git pull
  else  
    git clone git@github.com:WaiveCar/WaiveScreen.git
    ainsl ~demo/.bashrc 'PATH=$PATH:$HOME/.local/bin' 'HOME/.local/bin'
  fi
}

uuid() {
  UUID=/etc/UUID
  if [ ! -e $UUID ] ; then
    sudo dmidecode -t 4 | grep ID | sed -E s'/ID://;s/\s//g' | sudo tee $UUID
  fi
}

install() {
  cd WaiveScreen/ScreenDaemon
  pip3 install -r requirements.txt 
}

run() {
  cd $HOME/WaiveScreen/ScreenDaemon
  ./ScreenDaemon.py&
}

# git
# install

uuid
run
