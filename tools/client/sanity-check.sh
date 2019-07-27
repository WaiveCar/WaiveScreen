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
  if ! pgrep -if sensordaemon > /dev/null; then
    _as_user dcall sensor_daemon
  else
    last_read=$(sqlite3 $DB 'select created_at from sensor order by id desc limit 1;')
    db_delta=$(perl -e "use Date::Parse;print time() - str2time('$last_read');")
    # BUGBUG NOTE: If we change the minimum sensor heartbeat to be over 90 seconds
    # this will make the sensor daemon go wacky
    (( $db_delta > 180 )) && _as_user dcall sensor_daemon
  fi
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
