#!/bin/sh

export DISPLAY=$1
/usr/bin/notion &
[ -e ~demo/screen-splash.png ] && /usr/bin/display -window root ~demo/screen-splash.png
while [ 0 ]; do
  /usr/bin/chromium --app=file:///home/demo/WaiveScreen/ScreenDisplay/display.html
  sleep 1
done
