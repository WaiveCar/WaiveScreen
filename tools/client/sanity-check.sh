#!/bin/bash

DEST=/home/adorno/

. $DEST/const.sh
. $DEST/locals.sh

export PATH=$DEST:$PATH

check_ssh_hole() {

  tomake=$(mktemp -u)

  [[ $USER = 'root' ]] && cmd="su adorno -c"

  # Next we try to create this remotely using su if we need to.
  echo "ssh -o ConnectTimeout=10 adorno@bounce -p $PORT touch $tomake" | $cmd /bin/bash

  # If the file exists we are done, let's clean it up
  # otherwise our hole is down and we need to restart 
  if [ -e $tomake ]; then
		echo "SSH Hole Running"
	 	rm $tomake 
	else
		dcall ssh_hole 
	fi
}

check_screen_daemon() {
  if ! curl -s 127.1:4096/default > /dev/null; then
    dcall screen_daemon
	else
		echo "Screen Daemon Running"
	fi
}

check_sensor_daemon() {
  db_delta=$(( $(date +%s) - $(stat -c %Y /var/db/config.db) ))

  # If nothing has been written in 15 minutes.
  if [ "$db_delta" -gt 900 ]; then
    dcall sensor_daemon
	else
		echo "Sensor Daemon Running"
	fi
}

check_screen_display() {
	if ! pgrep chromium > /dev/null; then
		dcall screen_display
	else
		echo "Chromium running"
	fi
}

check_online() {
  if ! ping -c 1 -i 0.3 waivescreen.com; then
    /bin/true
  fi
}

check_ssh_hole
check_screen_daemon
check_sensor_daemon
check_screen_display
