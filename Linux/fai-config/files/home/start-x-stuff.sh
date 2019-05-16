#!/bin/bash

. lib.sh

export DISPLAY=$1

notion &

[ -e $DEST/screen-splash.png ] && display -window root $DEST/screen-splash.png

# Everything above is stuff we can run every time we start X
(( $( pgrep start-x-stuff ) > 2 )) && exit -1

# Everything below should be stuff that we only need to run once
loop_ad &

# Get online and open up our ssh hole
modem_enable

# TODO: comment out b4 prod
dev_setup
# TODO: put this in
# modem_connect

ssh_hole
screen_daemon
