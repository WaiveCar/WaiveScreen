#!/bin/bash

. lib.sh

date +%s > /tmp/startup

export DISPLAY=$1
REALPPID=$2

# Force a UUID update if needed
get_uuid 1

# I want to remove anything that I did previously so I can start fresh
rm -fr $DEST/.notion/default-session--* 
/usr/bin/notion &

[ -e $DEST/screen-splash.png ] && display -window root $DEST/screen-splash.png

# Everything above is stuff we can run every time we start X
(( $( pgrep start-x-stuff | wc -l ) > 2 )) && exit -1

_warn $(get_uuid) $MYPHONE $ENV

#
# If the hostname is changed via UUID, then
# this lock will prevent chromium from starting 
# up again and will just present a dialog box.
# 
rm -f $DEST/.config/chromium/Singleton*

sensor_daemon
screen_daemon
screen_display 
disk_monitor

# 
# This nomodem shouldn't be necessary
# but we are putting it in here to not
# cause any problems
#
NOMODEM=1 pycall set_autobright

#
# This delay is rather important because the
# wwan modem loads asynchronously and if we 
# try to do things with it before it's up 
# and running then it will break it and we 
# need to start over.
#
sleep 17

#
# Get online first before anything in the 
# stack spoils our beautiful virgin modem
# (it gets confused very easily apparently)
#
modem_enable
modem_connect

ssh_hole
sms_cleanup

# just a fun hack.
dcall text_loop &

#set_event xstartup $REALPPID
