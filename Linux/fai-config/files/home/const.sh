#!/bin/bash

export WHO=adorno
export DEST=/home/$WHO
export BASE=$DEST/WaiveScreen

export SERVER=staging.waivescreen.com
export BRANCH=202-raspbian-install
export CACHE=/var/cache/assets
export DB=/var/db/config.db
export DEV=$BASE.sshfs
export DISPLAY=${DISPLAY:-:0}
export ENV=production
export EVREST=20
export EV=/tmp/event
export LOG=/var/log/screen
export PATH=/usr/bin:/usr/sbin:$PATH:$DEST
export ROOTHOME=/root
export VID=/var/capture
export SMSDIR=/var/log/sms 
export NOMODEM=1

[[ $USER != 'root' ]] && SUDO=/usr/bin/sudo

# Local overrides to the above 
[[ -e $DEST/overrides ]] && . $DEST/overrides
