#!/bin/bash

. /home/adorno/const.sh

export PATH=$DEST:$PATH

pycall() {
  $BASE/ScreenDaemon/dcall $*
}

check_ssh_hole() {
  local tomake=$(mktemp -u)

  [[ $USER = 'root' ]] && cmd="su adorno -c"

  port=$( pycall db.kv_get port )
  # Next we try to create this remotely using su if we need to.
  echo "ssh -o ConnectTimeout=10 adorno@bounce -p $port touch $tomake" | $cmd /bin/bash

  # If the file exists we are done, let's clean it up
  # otherwise our hole is down and we need to restart 
  [[ -e $tomake ]] && rm $tomake || dcall ssh_hole 
}

check_screen_daemon() {
  curl -s 127.1:4096/default > /dev/null || dcall screen_daemon
}

check_sensor_daemon() {
  db_delta=$(( $(date +%s) - $(stat -c %Y /var/db/config.db) ))
  [ "$db_delta" -gt 900 ] && dcall sensor_daemon
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
    dcall modem_connect

    # if things still suck
    if ! ping -c 1 -i 0.3 waivescreen.com; then
      # if we fail to do multiple times
      if (( $(pycall sess_incr ping_fail) > 6 )); then
        # shrug our shoulders and just try to reboot, I dunno
        sudo reboot
      fi
    fi
  else
    pycall sess_set ping_fail,0
    return 0
  fi
  return 1
}

if [[ $(pycall sess_get modem) == 1 ]]; then
  date >> /tmp/sanity-check
  check_online && check_ssh_hole
  pycall lib.ping
  check_screen_daemon
  check_sensor_daemon
  check_screen_display
else
  echo $(date) nomodem >> /tmp/sanity-check
fi
