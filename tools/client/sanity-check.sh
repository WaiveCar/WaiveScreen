#!/bin/bash

. /home/adorno/const.sh
. /home/adorno/baseline.sh

export PATH=$DEST:$PATH

doit() {
  _as_user dcall $1
  _as_user dcall add_history restart $1 "$2"
}

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
    doit ssh_hole sanity-check
  fi
}

check_screen_daemon() {
  curl -s 127.1:4096/default > /dev/null || doit screen_daemon sanity-check
}

check_sensor_daemon() {
  if ! pgrep -if sensordaemon > /dev/null; then
    doit sensor_daemon not-running
  else
    if (( $(date +%s) - $(date +%s -r ${LOG}/powertemp.csv) > 120 )); then
      doit sensor_daemon output-check
    fi
  fi
}

check_screen_display() {
  if ! pgrep chromium > /dev/null; then
    _as_user dcall screen_display not-running
  else
    # we also have to make sure it hasn't just 
    # straight up crashed. Time is in seconds
    if (( $(date +%s) - $(dcall kv_get last_sow) > 600 )); then
      dcall down screen_display
      pkill chromium
      doit screen_display database-check
    fi
  fi
}

check_online() {
  host=8.8.8.8
  if ! ping -c 1 -i 0.3 $host; then
    # we try to do a one-shot reconnection thing
    doit modem_connect no-ping

    # if things still suck
    if ! ping -c 1 -i 0.3 $host; then
      # if we fail to do multiple times
      if (( $(pycall sess_incr ping_fail) > 6 )); then
        /bin/true
        # sudo reboot_from_sanity
      fi
    fi
  else
    pycall sess_set ping_fail,0
    return 0
  fi
  return 1
}

if dcall sess_get nosanity; then
  echo $(date) nosanity >> /tmp/sanity-check
elif dcall sess_get modem; then
  date >> /tmp/sanity-check
  check_online && check_ssh_hole
  pycall lib.ping
  pycall lib.update_uptime_log
  check_screen_daemon
  check_sensor_daemon
  check_screen_display
else
  echo $(date) nomodem >> /tmp/sanity-check
fi
