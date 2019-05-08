#!/bin/bash
USER=demo
DEST=/home/demo

count=`pgrep start-x-stuff | wc -l`
if [ "$count" -gt "2" ]; then
  exit -1
fi

ssh_hole() {
  cd $DEST/WaiveScreeen/ScreenDaemon/
  ./dcall emit_startup | sh
  ./run-daemon.sh &
}

get_online() {
  sudo $DEST/manual-set-ipv4.sh
}

dev_setup() {
  $DEST/dev-setup.sh
}

show_ad() {
  /usr/bin/chromium --app=file://$DEST/WaiveScreen/ScreenDisplay/display.html
}

export DISPLAY=$1
/usr/bin/notion &

[ -e ~$USER/screen-splash.png ] && /usr/bin/display -window root ~$USER/screen-splash.png

# After this is displaying now we can do blocking things
show_ad

# Like getting online and opening up our ssh hole
get_online
ssh_hole
$DEST/ping-and-update

# TODO: comment out b4 prod
dev_setup

while [ 0 ]; do

  count=`pgrep chromium | wc -l`
  while [ "$count" -ne "0" ]; do
    count=`pgrep chromium | wc -l`
    sleep 5
  done
  count=`pgrep Xorg | wc -l`
  if [ "$count" -eq "0" ]; then
    exit
  fi

  show_ad
done
