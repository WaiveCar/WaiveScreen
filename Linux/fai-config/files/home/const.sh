#!/bin/bash

export WHO=adorno
export DEST=/home/$WHO
export PATH=/usr/bin:/usr/sbin:$PATH:$DEST
export BASE=$DEST/WaiveScreen
export ROOTHOME=/root
export DEV=$BASE.sshfs
export EV=/tmp/event
export DISPLAY=${DISPLAY:-:0}
export VID=/var/capture
export LOG=/var/log/screen
export DB=/var/db/config.db
export CACHE=/var/cache/assets
export ENV=production
[[ $USER != 'root' ]] && SUDO=/usr/bin/sudo

# Local overrides to the above 
[[ -e $DEST/overrides ]] && . $DEST/overrides
