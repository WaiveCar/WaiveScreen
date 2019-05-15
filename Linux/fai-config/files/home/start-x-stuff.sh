#!/bin/bash
. lib.sh

unique() {
  count=`pgrep start-x-stuff | wc -l`
  if [ "$count" -gt "2" ]; then
    exit -1
  fi
}

export DISPLAY=$1
/usr/bin/notion &

[ -e $DEST/screen-splash.png ] && /usr/bin/display -window root $DEST/screen-splash.png

#
# Everything above is stuff we can run every time we start X
# Everything below should be stuff that we only need to run once
#
# After this is displaying now we can do blocking things

unique
show_ad &

# TODO: comment out b4 prod
dev_setup

# Get online and open up our ssh hole
modem_enable

# modem_connect
ssh_hole
screen_daemon

wait_for $EV/chromium

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
