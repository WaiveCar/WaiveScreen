#!/bin/bash

DEST=/home/adorno/

. $DEST/const.sh

export PATH=$DEST:$PATH

pycall() {
  $BASE/ScreenDaemon/dcall $*
}

check_ssh_hole() {

  local tomake=$(mktemp -u)

  [[ $USER = 'root' ]] && cmd="su adorno -c"

  # Next we try to create this remotely using su if we need to.
  echo "ssh -o ConnectTimeout=10 adorno@bounce -p $PORT touch $tomake" | $cmd /bin/bash

  # If the file exists we are done, let's clean it up
  # otherwise our hole is down and we need to restart 
  if [ -e $tomake ]; then
     rm $tomake 
  else
    dcall ssh_hole 
  fi
}

check_screen_daemon() {
  if ! curl -s 127.1:4096/default > /dev/null; then
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

check_screen_display() {
  if ! pgrep chromium > /dev/null; then
    dcall screen_display
  else
    # we also have to make sure it hasn't just 
    # straight up crashed. Time is in seconds
    if (( $(date +%s) - $(dcall kv_get last_sow) > 600 )); then
      dcall down screen_display
      pkill chromium
      dcall screen_display
    fi
  fi
}

check_online() {
  if ! ping -c 1 -i 0.3 waivescreen.com; then
    # we try to do a one-shot reconnection thing
    dcall modem_enable

    # if things still suck
    if ! ping -c 1 -i 0.3 waivescreen.com; then
      # if we fail to do multiple times
      if (( $(pycall sess_incr ping-fail) > 1 )); then
        # shrug our shoulders and just try to reboot, I dunno
        sudo reboot
      fi
    fi
  else
    pycall sess_set ping-fail,0
  fi
}

check_ssh_hole
check_screen_daemon
check_sensor_daemon
check_screen_display
check_online
