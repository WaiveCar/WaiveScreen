#!/bin/bash

. /home/adorno/const.sh
. /home/adorno/baseline.sh

export PATH=$DEST:$PATH

pycall() {
  _as_user $BASE/ScreenDaemon/dcall $*
}

check_ssh_hole() {
  local tomake=$(mktemp -u)

  port=$( pycall db.kv_get port )
  # Next we try to create this remotely using su if we need to.
  echo "ssh -o ConnectTimeout=10 adorno@bounce -p $port touch $tomake" | _as_user /bin/bash

  # If the file exists we are done, let's clean it up
  # otherwise our hole is down and we need to restart 
  if [[ -e $tomake ]]; then 
    rm $tomake
  else 
    dcall down ssh_hole
    _as_user dcall ssh_hole 
  fi
}

check_screen_daemon() {
  curl -s 127.1:4096/default > /dev/null || _as_user dcall screen_daemon
}

check_sensor_daemon() {
  db_delta=$(( $(date +%s) - $(stat -c %Y /var/db/config.db) ))
  [ "$db_delta" -gt 900 ] && _as_user dcall sensor_daemon
}

check_screen_display() {
  if ! pgrep chromium > /dev/null; then
    _as_user dcall screen_display
  else
    # we also have to make sure it hasn't just 
    # straight up crashed. Time is in seconds
    if (( $(date +%s) - $(dcall kv_get last_sow) > 600 )); then
      dcall down screen_display
      pkill chromium
      _as_user dcall screen_display
    fi
  fi
}

check_online() {
  if ! ping -c 1 -i 0.3 waivescreen.com; then
    # we try to do a one-shot reconnection thing
    _as_user dcall modem_connect

    # if things still suck
    if ! ping -c 1 -i 0.3 waivescreen.com; then
      # if we fail to do multiple times
      if (( $(pycall sess_incr ping_fail) > 6 )); then
        /bin/true
        # shrug our shoulders and just try to reboot, I dunno
        # I ran into a reboot loop that I can't find. It's probably
        # best to just not do it.
        # sudo reboot_from_sanity
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
