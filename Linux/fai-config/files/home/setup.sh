#!/bin/bash
if [ -e WaiveScreen ]; then
  cd WaiveScreen
  git pull
else  
  git clone git@github.com:WaiveCar/WaiveScreen.git
fi

