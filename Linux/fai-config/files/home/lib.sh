#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. $DIR/const.sh

pkill osd_cat

if [ ! -d $EV ]; then 
  mkdir -p $EV 
  chmod 0777 $EV
fi

[[ $ENV = 'development' ]] && export BASE=$DEV
[[ $USER = 'root' ]] && SUDO= || SUDO=/usr/bin/sudo

list() {
  # just show the local fuctions
  declare -F | sed s/'declare -f//g' | sort
}

_onscreen() {
  if [ ! -e /tmp/offset ]; then
    offset=0
  else
    offset=$( cat /tmp/offset )
  fi

  ts=$( printf "%03d" $(( $(date +%s) - $(cat /tmp/startup) )))
  size=14

  #from=$( caller 1 | awk ' { print $2":"$1 } ' )
  echo $1 "$ts" | osd_cat \
      -c $2 \
      -u black \
      -A right \
      -O 1 \
      -o $offset \
      -d $3 \
      -f lucidasanstypewriter-bold-$size &

  echo $1
  offset=$(( (offset + size + 9) % ((size + 9) * 25) ))

  echo $offset > /tmp/offset
  chmod 0666 /tmp/offset
}
_announce() {
  _onscreen "$*" white 20
}
_info() {
  _onscreen "$*" white 10
}
_warn() {
  _onscreen "$*" yellow 40
}
_error() {
  _onscreen "$*" red 90
}

who_am_i() {
  _info $(uuid) $ENV
}

set_event() {
  pid=${2:-$!}
  [ -e $EV/$1 ] || _announce Event:$1
  echo -n $pid > $EV/$1
}

test_arduino() {
  sleep=4
  {
    cd $BASE/ScreenDaemon
    for func in set_fan_speed set_backlight; do
      for lvl in 0 0.5 1; do
        _announce "arduino.$func $lvl"
        ./dcall $func $lvl
        sleep $sleep
      done
    done

    for func in do_sleep do_awake arduino_read; do
      _announce $func
      ./dcall arduino.$func
      sleep $sleep
    done
  }
}

modem_enable() {
  for i in $( seq 1 5 ); do
    $SUDO mmcli -m 0 -e

    if [ ! $? ]; then 
      _warn "Searching for modem"
      sleep 1
      continue
    fi

    # You won't find these options in the manpage, they are from
    # cli/mmcli-modem-location.c in the ModemManager source code
    # over at https://www.freedesktop.org/software/ModemManager/
    $SUDO mmcli -m 0 \
      --location-enable-gps-raw \
      --location-enable-agps \
      --location-enable-gps-nmea \
      --location-set-enable-signal

      #
      # I don't quite know what this option does (but I didn't 
      # study the code). Our Quectel 25A modems seem to not 
      # understand it.
      #
      #--location-enable-gps-unmanaged \

    set_event modem
    break
  done
}

modem_connect() {
  for i in 1 2; do
    $SUDO mmcli -m 0 --simple-connect="apn=internet"
    wwan=`ip addr show | grep wwp | head -1 | awk -F ':' ' { print $2 } '`

    if [ -z "$wwan" ]; then
      _warn  "No modem found. Trying again"
      sleep 4
    else
      break
    fi
  done

  # get ipv6
  $SUDO dhclient $wwan &

  # Show the config | find ipv4 | drop the LHS | replace the colons with equals | drop the whitespace | put everything on one line
  eval `mmcli -b 0 | grep -A 3 IPv4 | awk -F '|' ' { print $2 } ' | sed s'/: /=/' | sed -E s'/\s+//' | tr '\n' ';'`

  $SUDO ip addr add $address/$prefix dev $wwan
  $SUDO ip route add default via $gateway dev $wwan

  cat << ENDL | $SUDO tee /etc/resolv.conf
  nameserver 8.8.8.8
  nameserver 4.2.2.1
  nameserver 2001:4860:4860::8888 
  nameserver 2001:4860:4860::8844
ENDL
  set_event net ''

  sleep 9

  if ping -c 1 -i 0.3 waivescreen.com; then
    _announce "waivescreen.com found" 
  else
    _warn "waivescreen.com unresolvable!"

    while ! mmcli -m 0; do
      _announce "Waiting for modem"
      sleep 9
    done

    hasip=$( ip addr show $wwan | grep inet | wc -l )
    myphone=$( mmcli  -m 0 | grep own | awk ' { print $NF } ' )
    if (( hasip > 0 )); then
      _warn "Data plan issues."
    else
      _warn "No IP assigned."
    fi
    _error "$myphone"
  fi
}

ssh_hole() {
  $SUDO $BASE/ScreenDaemon/dcall emit_startup | /bin/sh
  set_event ssh
}

screen_daemon() {
  down screen_daemon
  # TODO: We need to use some polkit thing so we can
  # access the modem here and not run this as root in the future
  $SUDO FLASK_ENV=$ENV $BASE/ScreenDaemon/ScreenDaemon.py &

  set_event screen_daemon
}

sensor_daemon() {
  down sensor_daemon
  $SUDO $BASE/ScreenDaemon/SensorDaemon.py &
  set_event sensor_daemon
}

git_waivescreen() {
  {
    # Make sure we're online
    wait_for net

    if [ -e $DEST/WaiveScreen ]; then
      cd $DEST/WaiveScreen
      git stash
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
  cat $UUID
}

wait_for() {
  path=${2:-$EV}/$1

  if [ ! -e "$path" ]; then
    until [ -e "$path" ]; do
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
  # Note: this usually runs as normal user
  #
  # echo development > $DEST/.env
  $SUDO dhclient enp3s0 
  [ -e $DEV ] || mkdir $DEV

  if [ -z "$SUDO" ]; then
    _warn "Hey, you can't be root to do sshfs"
  fi

  sshfs -o uid=$(id -u $WHO),gid=$(id -g $WHO) dev:/home/chris/code/WaiveScreen $DEV -C -o allow_root
  export BASE=$DEV
  set_event net ''
}


install() {
  cd $BASE/ScreenDaemon
  $SUDO pip3 install -r requirements.txt 
}

_screen_display_single() {
  export DISPLAY=${DISPLAY:-:0}

  [[ $ENV = 'development' ]] && wait_for net

  if [ ! -e $BASE ]; then
    git_waivescreen
    wait_for $BASE ''
  fi

  local app=$BASE/ScreenDisplay/display.html 
  if [ -e $app ]; then
    chromium --no-first-run --non-secure --default-background-color='#000' --app=file://$app &
    set_event screen_display
  else
    _error "Can't find $app. Exiting"
    exit 
  fi
}

screen_display() {
  {
    while pgrep Xorg; do

      while pgrep chromium; do
        sleep 5
      done

      _screen_display_single
    done
  } > /dev/null &
}

down() {
  cd $EV
  if [ -n "$1" ]; then
    [ -s "$pidfile" ] && $SUDO kill $( cat $pidfile )
    [ -e "$pidfile" ] && $SUDO rm $pidfile
  else
    for pidfile in $( ls ); do
      echo $pidfile
      [ -s "$pidfile" ] && $SUDO kill $( cat $pidfile )
      [ -e "$pidfile" ] && $SUDO rm $pidfile
    done
  fi
}

upgrade() {
  # Since everything is in memory and already loaded
  # we can try to just pull things down
  cd $BASE
  
  # We make sure that local changes (there shouldn't be any)
  # get tossed aside and pull down the new code.
  git stash

  if git pull; then
    # If there's script updates we try to pull those down
    # as well
    rsync --exclude=.xinitrc -aqzr $BASE/Linux/fai-config/files/home/ $DEST
    chmod 0600 $DEST/.ssh/KeyBounce $DEST/.ssh/github $DEST/.ssh/dev

    # Now we take down the browser.
    down screen_display

    # This stuff shouldn't be needed
    # But right now it is.
    $SUDO pkill start-x-stuff
    $SUDO pkill -f ScreenDisplay

    # And the server (which in practice called us from a ping command)
    down screen_daemon
    $SUDO pkill -f ScreenDaemon

    # And lastly the sensor daemon
    down sensor_daemon
    $SUDO pkill -f SensorDaemon

    screen_display 
    sensor_daemon

    # Upgrade the database if necessary
    {
      cd $BASE/ScreenDaemon
      pip3 install -r requirements.txt
      ./dcall upgrade
    }

    screen_daemon
  fi
}

restart_xorg() {
  {
    $SUDO pkill Xorg
    $SUDO xinit
  } &
}

location() {
  $SUDO mmcli -m 0 --location-get
  $SUDO mmcli -m 0 --location-status
}

nop() { 
  true
}
