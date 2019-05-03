#!/bin/sh

count=`pgrep start-x-stuff | wc -l`
if [ "$count" -gt "2" ]; then
  exit -1
fi

export DISPLAY=$1
/usr/bin/notion &
[ -e ~demo/screen-splash.png ] && /usr/bin/display -window root ~demo/screen-splash.png
while [ 0 ]; do
  /usr/bin/chromium --app=file:///home/demo/WaiveScreen/ScreenDisplay/display.html

  count=`pgrep chromium | wc -l`
  while [ "$count" -ne "0" ]; do
    count=`pgrep chromium | wc -l`
    sleep 5
  done
  count=`pgrep Xorg | wc -l`
  if [ "$count" -eq "0" ]; then
    exit
  fi
done
