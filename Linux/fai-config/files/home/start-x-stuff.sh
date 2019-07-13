#!/bin/bash

. lib.sh

date +%s > /tmp/startup

export DISPLAY=$1

# Force a UUID update if needed
get_uuid 1

# I want to remove anything that I did previously so I can start fresh
rm -fr $DEST/.notion/default-session--* 
/usr/bin/notion &

version=$(cd $BASE; git describe | awk -F \- ' { print $2"-"$3 } ')
_warn $(get_uuid) $version 

# If the hostname is changed via UUID, then
# this lock will prevent chromium from starting 
# up again and will just present a dialog box.
rm -f $DEST/.config/chromium/Singleton*

# Honestly I don't care if there's some miraculous DNS spoofing. I can't
# have this fail when I move the host around.
ssh-keygen -f "$DEST/.ssh/known_hosts" -R "reflect.waivescreen.com"

sensor_daemon
screen_daemon
screen_display 
disk_monitor

# 
# This nomodem shouldn't be necessary
# but we are putting it in here to not
# cause any problems
#
NOMODEM=1 pycall arduino.set_autobright

#
# This delay is rather important because the
# wwan modem loads asynchronously and if we 
# try to do things with it before it's up 
# and running then it will break it and we 
# need to start over.
#
sudo service ModemManager start &
sleep 17

# Putting this higher than the modem connect
# is important. Otherwise we won't receive
# our number
text_loop &

#
# Get online first before anything in the 
# stack spoils our beautiful virgin modem
# (it gets confused very easily apparently)
#
modem_connect
hotspot

pycall lib.ping
ssh_hole
sms_cleanup
first_run
upgrade_scripts
