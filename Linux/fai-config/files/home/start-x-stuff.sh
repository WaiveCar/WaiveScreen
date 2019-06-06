#!/bin/bash

. lib.sh

date +%s > /tmp/startup

export DISPLAY=$1
REALPPID=$2

# I want to remove anything that I did previously so I can start fresh
rm -fr $DEST/.notion/default-session--* 
/usr/bin/notion &

[ -e $DEST/screen-splash.png ] && display -window root $DEST/screen-splash.png

# Everything above is stuff we can run every time we start X
(( $( pgrep start-x-stuff | wc -l ) > 2 )) && exit -1

_info $(get_uuid) $ENV

#
# This delay is rather important because the
# wwan modem loads asynchronously and if we 
# try to do things with it before it's up 
# and running then it will break it and we 
# need to start over.
#
# We could *potentially* show an ad prior
# to this delay but let's put such streamlining
# off to later.
#
disk_monitor
screen_display 

sleep 20

#
# Get online first before anything in the 
# stack spoils our beautiful virgin modem
# (it gets confused very easily apparently)
#
modem_enable
modem_connect

ssh_hole
sensor_daemon
screen_daemon

set_event xstartup $REALPPID
