#!/bin/bash

. lib.sh
date +%s > /tmp/startup

export DISPLAY=$1

# I want to remove anything that I did previously so I can start fresh
rm -r $DEST/.notion/default-session--* $
notion &

[ -e $DEST/screen-splash.png ] && display -window root $DEST/screen-splash.png

# Everything above is stuff we can run every time we start X
(( $( pgrep start-x-stuff | wc -l ) > 2 )) && exit -1

who_am_i

up

# Get online and open up our ssh hole
modem_enable
modem_connect

set_event xstartup $$

wait_for net
  ssh_hole
