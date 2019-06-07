#!/bin/bash

DEST=/home/adorno/

. $DEST/const.sh
. $DEST/locals.sh

export PATH=$DEST:$PATH

check_ssh_hole() {

  tomake=$(mktemp -u -p)

  [[ $USER = 'root' ]] && cmd="su adorno -c"

  # Next we try to create this remotely using su if we need to.
  echo "ssh -o ConnectTimeout=10 adorno@bounce -p $PORT touch $tomake" | $cmd /bin/bash

  # If the file exists we are done, let's clean it up
  # otherwise our hole is down and we need to restart 
  [ -e $tomake ] && rm $tomake || dcall ssh_hole 
}

check_screen_daemon() {
  if ! curl 127.1:4096/default; then
    dcall screen_daemon
  fi
}

check_sensor_daemon() {
  db_delta=$(( $(date +%s) - $(stat -c %Y /var/db/config.db) ))

  # If nothing has been written in 15 minutes.
  if [ "$db_delta" -gt 900 ]; then
    dcall sensor_daemon
  fi
}

check_ssh_hole
check_screen_daemon
check_sensor_daemon
