#!/bin/bash

export WHO=adorno
export DEST=/home/$WHO
export PATH=/usr/bin:/usr/sbin:$PATH:$DEST
export BASE=$DEST/WaiveScreen
export DEV=$BASE.nfs
export VID=$DEST/capture
export EV=/tmp/event

if [ ! -d $EV ]; then 
  mkdir -p $EV 
  chmod 0777 $EV
fi

[[ $USER = 'root' ]] && SUDO= || SUDO=/usr/bin/sudo

help() {
  # just show the local fuctions
  declare -F | sed s/'declare -f//g' | sort
}

set_event() {
  touch $EV/$1
  echo `date +%R:%S` $1
}

modem_enable() {
  $SUDO mmcli -m 0 -e

  $SUDO mmcli -m 0 \
    --location-enable-gps-raw \
    --location-enable-gps-nmea \
    --location-set-enable-signal
}

modem_connect() {
  $SUDO mmcli -m 0 --simple-connect="apn=internet"
  wwan=`ip addr show | grep wwp | head -1 | awk -F ':' ' { print $2 } '`

  if [ -z "$wwan" ]; then
    echo "Modem Not Found!!"
    exit -1
  fi

  # get ipv6
  $SUDO dhclient $wwan &

  # Show the config | find ipv4 | drop the LHS | replace the colons with equals | drop the whitespace | put everything on one line
  eval `mmcli -b 0 | grep -A 3 IPv4| awk -F '|' ' { print $2 } ' | sed s'/: /=/' | sed -E s'/\s+//' | tr '\n' ';'`

  $SUDO ip addr add $address/$prefix  dev $wwan
  $SUDO ip route add default via $gateway dev $wwan

  cat << ENDL | $SUDO tee /etc/resolv.conf
  nameserver 8.8.8.8
  nameserver 4.2.2.1
  nameserver 2001:4860:4860::8888 
  nameserver 2001:4860:4860::8844
ENDL
  set_event net
}

ssh_hole() {
  $BASE/ScreenDaemon/dcall emit_startup | /bin/sh
}

screen_daemon() {
  FLASK_ENV=development $BASE/ScreenDaemon/ScreenDaemon.py
}

sensor_daemon() {
  $SUDO $BASE/ScreenDaemon/SensorStore.py
}

git_waivescreen() {
  {
    # Make sure we're online
    wait_for $EV/net

    if [ -e $DEST/WaiveScreen ]; then
      cd $DEST/WaiveScreen
      git pull
    else  
      cd $DEST
      git clone git@github.com:WaiveCar/WaiveScreen.git
      ainsl $DEST/.bashrc 'PATH=$PATH:$HOME/.local/bin' 'HOME/.local/bin'
    fi
  } &
}

uuid() {
  UUID=/etc/UUID
  if [ ! -e $UUID ] ; then
    $SUDO dmidecode -t 4 | grep ID | sed -E s'/ID://;s/\s//g' | $SUDO tee $UUID
  fi
}

sync_scripts() {
  rsync --exclude=.xinitrc -aqzr $DEV/Linux/fai-config/files/home/ $DEST
  chmod 0600 $DEST/.ssh/KeyBounce $DEST/.ssh/github $DEST/.ssh/dev
}

wait_for() {
  if [ ! -e "$1" ]; then
    until [ -e "$1" ]; do
      echo `date +%R:%S` WAIT $1
      sleep 0.5
    done
    # Give it a little bit after the file exists to
    # avoid unforseen race conditions
    sleep 0.05
  fi
}

dev_setup() {
  #
  # note! this usually runs as normal user
  #
  $SUDO dhclient enp3s0 
  [ -e $DEV ] || mkdir $DEV

  sshfs dev:/home/chris/code/WaiveScreen $DEV -C -o allow_root
  set_event net
}


install() {
  cd $BASE/ScreenDaemon
  $SUDO pip3 install -r requirements.txt 
}

show_ad() {
  if [ ! -e $BASE ]; then
    git_waivescreen
    wait_for $BASE
  fi

  set_event chromium
  chromium --app=file://$BASE/ScreenDisplay/display.html
}

nop() { 
  true
}
