#!/bin/bash

export WHO=adorno
export DEST=/home/$WHO
export PATH=/usr/bin:/usr/sbin:$PATH:$DEST
export BASE=$DEST/WaiveScreen
export DEV=$BASE.sshfs
export VID=$DEST/capture
export EV=/tmp/event
export DISPLAY=${DISPLAY:-:0}
#
# Valid values are "production" and "development"
#
# These are used for things like flask so you really
# shouldn't be lazy and shorten them unless you want
# to somehow accomodate for that fact.
#
if [ -e $DEST/.env ]; then
  export ENV=$( cat $DEST/.env )
else
  export ENV=production
fi
