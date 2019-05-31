#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOCALS=$DIR/locals.sh

. $DIR/const.sh
. $DIR/baseline.sh
. $LOCALS

pkill osd_cat

if [ ! -d $EV ]; then 
  mkdir -p $EV 
  chmod 0777 $EV
fi

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

  echo $ts $1 | $SUDO tee -a /tmp/messages
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

online_loop() {
  {
    cat > $DEST/online

    ONLINE=0
    while [ 0 ]; do
      if ping -c 1 waivecreen.com; then
        echo 'ONLINE=1' > $DEST/online
      fi
    done
  }&
}

set_event() {
  pid=${2:-$!}
  [ -e $EV/$1 ] || _announce Event:$1
  echo -n $pid > $EV/$1
}

test_arduino() {
  cd $BASE/ScreenDaemon
  ./dcall arduino.test
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

local_set() {
  # First remove it
  sed -i "s/^$1=.*//" $LOCALS

  # Now get rid of excess newlines created
  # by the above process.
  sed -ni '/./p' $LOCALS

  # Then put it back in
  echo $1=$2 >> $LOCALS
  
  # And re-read it
  source $LOCALS
}

ssh_hole() {
  {
    while [ 0 ]; do
      if [ ! "$PORT" ]; then
        local_set PORT "$($SUDO $BASE/ScreenDaemon/dcall get_port)"
      fi
      
      if [ ! "$PORT" ]; then
        _warn "Cannot contact the server for my port"

      elif ps -o pid= -p $( cat $EV/ssh ); then
        # this means we have an ssh open and life is fine
        sleep 10

      else
        ssh -NC -R bounce:$PORT:127.0.0.1:22 bounce &
        set_event ssh
      fi

      sleep 10
    done
  } >> /tmp/ssh_hole.log &

  # The 0 makes sure that the wrapper is killed before
  # the client 
  set_event 0_ssh_wrapper
}

screen_daemon() {
  down screen_daemon
  # TODO: We need to use some polkit thing so we can
  # access the modem here and not run this as root in the future
  FLASK_ENV=$ENV DEBUG=1 $SUDO $BASE/ScreenDaemon/ScreenDaemon.py &

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
      _git stash
      _git pull
    else  
      cd $DEST
      _git clone git@github.com:WaiveCar/WaiveScreen.git
      ainsl $DEST/.bashrc 'PATH=$PATH:$HOME/.local/bin' 'HOME/.local/bin'
    fi
  } &
}

pip_install() {
  pip3 install $DEST/pip/*
}

uuid() {
  UUID=/etc/UUID
  if [ ! -e $UUID ] ; then
    {
      $SUDO dmidecode -t 4 | grep ID | sed -E s'/ID://;s/\s//g' | $SUDO tee $UUID
      hostname=bernays-$(cat $UUID)
      echo $hostname | $SUDO tee /etc/hostname
      $SUDO ainsl /etc/hosts "127.0.0.1 $hostname"
    } > /dev/null
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
    _as_user chromium --no-first-run --non-secure --default-background-color='#000' --app=file://$app &
    set_event screen_display
  else
    _error "Can't find $app. Exiting"
    exit 
  fi
}

screen_display() {
  ix=0
  {
    while pgrep Xorg; do

      while pgrep chromium; do
        (( ix ++ ))
        sleep 10
        # We try to ping the remote here
        # in case our browser broke from
        # a botched upgrade.
        if (( ix % 30 == 0 )); then
          $BASE/ScreenDaemon/dcall lib.ping
        fi
      done

      _screen_display_single
    done
  } >> /tmp/screen_display.log &

  set_event 0_screen_wrapper
}

running() {
  cd $EV
  ls
}

down() {
  cd $EV

  if [ -n "$1" ]; then
    list=$1
  else
    list=$( ls )
  fi

  for pidfile in $list; do
    if [ -e "$pidfile" ]; then
      echo "Trying to kill $pidfile"
      {
        if ps -o pid= -p $( cat $pidfile ); then
          $SUDO kill $( cat $pidfile )
        fi
      } > /dev/null
      $SUDO rm $pidfile
    fi
  done
}

up() {
  $DEST/dcall screen_display 
  $DEST/dcall sensor_daemon
  $DEST/dcall screen_daemon
}

upgrade() {
  # should be run OOB
  #
  # local_sync
  #

  # Now we take down the browser.
  $DEST/dcall down 0_screen_wrapper
  $DEST/dcall down screen_display

  # There's a bug in the infrastructure that required this.
  $SUDO pkill chromium

  # This stuff shouldn't be needed
  # But right now it is.
  $SUDO pkill start-x-stuff

  # And the server (which in practice called us from a ping command)
  $DEST/dcall down screen_daemon

  # And lastly the sensor daemon
  $DEST/dcall down sensor_daemon
  $SUDO pkill ScreenDaemon

  # This permits us to use a potentially new way
  # of starting up the tools
  $DEST/dcall screen_display 
  $DEST/dcall sensor_daemon

  # Upgrade the database if necessary
  {
    cd $BASE/ScreenDaemon
    pip3 install -r requirements.txt
    ./dcall db.upgrade
  }

  $DEST/dcall screen_daemon
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

