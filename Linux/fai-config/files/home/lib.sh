#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MM="mmcli -m 0"
SMSDIR=/var/log/sms 
FFMPEG="ffmpeg -loglevel panic -nostats -hide_banner -y -an"

. $DIR/const.sh
. $DIR/baseline.sh

pkill osd_cat

if [ ! -d $EV ]; then 
  mkdir -p $EV 
  chmod 0777 $EV
fi

kv_get() {
  sqlite3 $DB "select value from kv where key='$1'"
}

kv_incr() {
  local curval=$(kv_get $1)
  if [ -z "$curval" ]; then 
    sqlite3 $DB "insert into kv(key, value) values('$1',0)" &
    echo 0
  else
    curval=$(( curval + 1 ))
    sqlite3 $DB "update kv set value=$curval where key='$1'";
    echo $curval
  fi
}

list() {
  # just show the local fuctions
  if [ $# -gt 0 ]; then
    while [ $# -gt 0 ]; do
      declare -f $1
      shift
    done
  else
    declare -F | sed s/'declare -f//g' | sort
  fi
}

_bigtext() {
  if [ "$B64" ]; then
    middle="base64 -d"
    unset B64
  else
    middle="cat"
  fi
  echo "$*" | $middle | aosd_cat -p 4 -n "DejaVu Sans 72" -R white -f 1500 -u 1200 -o 1500 -d 30 -b 216 -B black &
}

selfie() {
  local cache=/var/cache/assets/
  local now=`date +%Y%m%d%H%M%S`
  local opts=''
  local num=0

  for i in $( seq 0 2 6 ); do
    $SUDO $FFMPEG -f v4l2 -video_size 1280x720 -i /dev/video$i -vframes 1 $cache/$now-$i.jpg 
  done

  if [ -n "$1" ]; then
     sms_cleanup &
  fi
  import -window root $cache/$now-screen.jpg

  for i in $cache/$now-screen.jpg $cache/$now-0.jpg $cache/$now-2.jpg $cache/$now-4.jpg $cache/$now-6.jpg; do
    if [ -e "$i" ]; then
      opts="$opts -F \"f$num=@$i\""
      (( num ++ ))
    fi
  done
  res=$(eval curl -sX POST $opts "waivescreen.com/selfie.php?pre=$now")
  if [ -n "$1" ]; then
    sms $sender "This just happened: $res. More cool stuff coming soon ;-)"
  else
    echo $res
  fi
}

sms() {
  local phnumber=$1
  shift
  local number=$($SUDO $MM --messaging-create-sms="number=$phnumber,text='$*'" | awk ' { print $NF } ')
  # $SUDO $MM -s $number --send
}

_mmsimage() {
  local file=$1
  local cmd="convert - -resize 450x -background black -gravity center -extent 450x450"

  dd skip=1 bs=$(( $(grep -abPo '(JFIF.*)' $file | awk -F : ' { print $1 }') - 6 )) if=$file | $cmd $file.jpg

  if [ -s $file ]; then
    echo '' | aosd_cat -n "FreeSans 0" -u 4000 -p 7 -d 225 -f 0 -o 0 &
    sleep 0.03
    display -window $(xwininfo -root -tree | grep aosd | head -1 | awk ' { print $1 } ') $file.jpg &
  fi
}

sms_cleanup() {
  # cleanup
  for i in $($MM --messaging-list-sms | awk ' { print $1 } '); do
    [ "$i" = "No" ] && continue
    local num=$( kv_incr sms )

    # Try to make sure we aren't overwriting
    while [ -e $SMSDIR/$num ]; do
      num=$( kv_incr sms )
      sleep 0.01
    done

    $MM -s $i > $SMSDIR/$num
    $MM -s $i --create-file-with-data=$SMSDIR/${num}.raw >& /dev/null
    $SUDO $MM --messaging-delete-sms=$i
  done
}

t() {
  echo $(date +%s.%N) $*
}

text_loop() {
  [ -d $SMSDIR ] || $SUDO mkdir $SMSDIR
  $SUDO chmod 0777 $SMSDIR

  while [ 0 ]; do
    sms=$(pycall next_sms)

    if [ -n "$sms" ]; then
      eval $sms

      if [ -n "$message" ]; then
        selfie $sender &
        sleep 2
        B64=1 _bigtext $message
      else
        # Wait a while for the image to come in
        sleep 1.5
        local num=$(basename $dbuspath)
        $MM -s $dbuspath --create-file-with-data=$SMSDIR/${num}.raw
        sender=$(strings $SMSDIR/${num}.raw | grep ^+ | cut -c -12 )
        curl -s $(strings $SMSDIR/${num}.raw | grep http) > $SMSDIR/${num}.payload
        selfie $sender &
        _mmsimage $SMSDIR/${num}.payload
        sleep 0.5
      fi
    fi
  done
}

_onscreen() {
  [ -e /tmp/offset ] && offset=$(< /tmp/offset ) || offset=0

  local ts=$( printf "%03d" $(( $(date +%s) - $(< /tmp/startup) )))
  local size=14

  #from=$( caller 1 | awk ' { print $2":"$1 } ' )
  echo $1 "$ts" | osd_cat \
    -c $2 -u black  -A right \
    -O 1 -o $offset \
    -d $3 \
    -f lucidasanstypewriter-bold-$size &

  echo $ts $1 | $SUDO tee -a /tmp/messages
  offset=$(( (offset + size + 9) % ((size + 9) * 28) ))

  echo $offset > /tmp/offset
  chmod 0666 /tmp/offset
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

set_wrap() {
  local pid=${2:-$!}
  [ -e $EV/0_$1 ] && $SUDO rm $EV/0_$1
  echo -n $pid > $EV/0_$1
}

set_event() {
  pid=${2:-$!}
  [ -e $EV/$1 ] || _info Event:$1
  echo -n $pid > $EV/$1
}

set_brightness() {
  local level=$1
  local nopy=$2

  local shift=$(perl -e "print .5 * $level + .5")
  local revlevel=$(perl -e "print .7 * $level + .3")

  [ -z "$nopy" ] && pycall arduino.set_backlight $level

  for display in HDMI-1 HDMI-2; do
    DISPLAY=:0 xrandr --output $display --gamma 1:1:$shift --brightness $revlevel
  done
}

enable_gps() {
  $SUDO $MM \
    --location-set-enable-signal \
    --location-enable-agps \
    --location-enable-gps-nmea \
    --location-enable-gps-raw 
}

capture_all_cameras() {
  # This makes sure that the wiring is good
  {
    for ix in $(seq 0 2 6); do
      $SUDO rm -f "/tmp/video${ix}.mp4";
      $SUDO $FFMPEG -i /dev/video$ix -t 4 /tmp/video${ix}.mp4 &
    done

    sleep 7
  } >& /dev/null 

  echo /tmp/video*mp4 | wc -w
}

get_number() {
  # mmcli may not properly be reporting the phone number. T-mobile sends it to
  # us in our first text so we try to work it from there.
  phone=$( pycall lib.get_number )
  if [ -z "$phone" ]; then
    # mmcli may not properly number the sms messages starting at 0 so we find the earliest
    sms 8559248355 '__echo__'
    # wait for our echo service to set the variable
    sleep 4
    phone=$( kv_get number )
  fi 
  echo $phone
}

#
# --3gpp-scan  -> status state: registered
# --3gpp-register-home then
# try $SUDO $MM --simple-connect="apn=internet"
#
# Then mmcli -b 0 will show up
#
modem_connect() {
  for i in $( seq 1 5 ); do
    $SUDO $MM -e

    if [ ! $? ]; then 
      _warn "Searching for modem"
      sleep 1
      continue
    fi

    # This bizarre magic actually works. We reliably
    # get the GPS lat/lng to finally appear with this 
    # nonsense. Why? I wish I had the time to investigate
    enable_gps
    $SUDO $MM -d
    $SUDO $MM -e
    enable_gps

    break
  done

  for i in $( seq 1 5 ); do
    $SUDO $MM --set-allowed-modes='3g|4g' --set-preferred-mode=4g
    $SUDO $MM --simple-connect="apn=internet,ip-type=ipv4v6"
    wwan=`ip addr show | grep ww[pa] | head -1 | awk -F ':' ' { print $2 } '`

    if [ -z "$wwan" ]; then
      _warn  "No modem found. Trying again"
      sleep 4
    else
      break
    fi
  done

  # get ipv6
  #$SUDO dhclient $wwan &

  # Show the config | find ipv4 | drop the LHS | replace the colons with equals | drop the whitespace | put everything on one line
  eval `mmcli -b 0 | grep -A 4 IPv4 | awk -F '|' ' { print $2 } ' | sed -E s'/: (.*)/="\1"/' | sed -E "s/[\' +]//g" | tr '\n' ';'`

  $SUDO ifconfig $wwan up
  $SUDO ip addr add $address/$prefix dev $wwan
  $SUDO ip route add default via $gateway dev $wwan

  cat << ENDL | sed 's/^\s*//' | $SUDO tee /etc/resolv.conf
$(perl -l << EPERL
  @lines = split(/,\s*/, '$dns');
  foreach( @lines ) {
    print 'nameserver ', \$_;
  }
EPERL
)
  nameserver 2001:4860:4860::8888 
  nameserver 2001:4860:4860::8844
ENDL
  set_event net ''

  sleep 4

  if ping -c 1 -i 0.3 waivescreen.com; then
    _info "waivescreen.com found" 
    pycall db.kv_set number,$(get_number)
  else
    _warn "waivescreen.com unresolvable!"

    ix=0
    while ! $MM; do
      (( ix ++ ))
      if (( ix < 4 )); then
        _info "Waiting for modem"
      fi
      sleep 9
    done

    hasip=$( ip addr show $wwan | grep inet | wc -l )

    if (( hasip > 0 )); then
      _warn "Data plan issues."
    else
      _warn "No IP assigned."
    fi
    _error $(get_number)
  fi
  pycall db.sess_set modem,1 
}

# This tries to see if it can find a wireless network
# to connect to. Generally speaking this is for debugging
# something that is out in the field
try_wireless() {
  down wpa_supplicant
  $SUDO wpa_supplicant -d -Dnl80211,wext -i$DEV -c/etc/wpa_supplicant.conf &
  set_event wpa_supplicant

  down wireless_dhclient
  $SUDO dhclient $DEV &
  set_event wireless_dhclient
}

pycall() {
  $BASE/ScreenDaemon/dcall $*
}

ssh_hole() {
  local rest=20
  local event=ssh_hole

  if (( $(pgrep -cf dcall\ ssh_hole ) > 1 )); then
    echo "Nope, kill the others first"
    exit 0
  fi

  {
    while [ 0 ]; do
      local port=$(kv_get port)
      
      if [ -z "$port" ]; then
        # This will cycle on a screen that's not properly
        # installed. That's kinda unnecessary
        # _warn "Cannot contact the server for my port"
        /bin/true

      elif [ -e $EV/$event ] && ps -o pid= -p $(< $EV/$event ); then
        # this means we have an ssh open and life is fine
        sleep $rest

      else
        ssh -NC -R bounce:$port:127.0.0.1:22 bounce &
        set_event $event
      fi

      sleep $rest
    done
  } > /dev/null &

  set_wrap ssh_hole
}

screen_daemon() {
  down screen_daemon
  FLASK_ENV=$ENV $BASE/ScreenDaemon/ScreenDaemon.py &
  set_event screen_daemon
}

sensor_daemon() {
  down sensor_daemon
  $SUDO $BASE/ScreenDaemon/SensorDaemon.py &
  set_event sensor_daemon
}

# This is used during the installation - don't touch it!
pip_install() {
  pip3 -q install $DEST/pip/*
}

install() {
  cd $BASE/ScreenDaemon
  $SUDO pip3 install -r requirements.txt 
}

get_uuid() {
  local UUIDfile=/etc/UUID
  if [ -n "$1" -o ! -e $UUIDfile -o $# -gt 1 ]; then
    {
      # The MAC addresses are just SOOO similar we want more variation so let's md5sum
      local uuid_old=$(< $UUIDfile )
      uuid=$(cat /sys/class/net/enp3s0/address | md5sum | awk ' { print $1 } ' | xxd -r -p | base64 | sed -E 's/[=\/\+]//g')

      if [ "$uuid" != "$uuid_old" ]; then
        _info "New UUID $uuid_old -> $uuid"
        echo $uuid_old | $SUDO tee -a $UUIDfile.bak
        echo $uuid | $SUDO tee $UUIDfile
        hostname=bernays-$uuid
        echo $hostname | $SUDO tee /etc/hostname
        $SUDO ainsl /etc/hosts "127.0.0.1 $hostname"
      fi
    } > /dev/null
  fi
  cat $UUIDfile
}

wait_for() {
  path=${2:-$EV}/$1

  if [ ! -e "$path" ]; then
    echo `date +%R:%S` WAIT $1
    until [ -e "$path" ]; do
      sleep 0.5
    done

    # Give it a little bit after the file exists to
    # avoid unforseen race conditions
    sleep 0.05
  fi
}

_screen_display_single() {
  export DISPLAY=${DISPLAY:-:0}
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
  local ix=0
  {
    while pgrep Xorg; do
      while pgrep chromium; do
        sleep 10

        # We try to ping the remote here
        # in case our browser broke from
        # a botched upgrade.
        (( ++ix % 30 == 0 )) && pycall lib.ping

        [ -e $EV/0_screen_display ] || return
        [ "$(< $EV/0_screen_display )" != "$pid" ] && return
      done

      _screen_display_single
    done
  } >> /tmp/screen_display.log &
  local pid=$!

  set_wrap screen_display $pid
}

running() {
  cd $EV
  for pidfile in $( ls ); do
    local pid=$(< $pidfile )
    local line="-"
    {
      if [ -n "$pid" ]; then 
        line=$(ps -o start=,command= -p $(< $pidfile ))
        [ -n "$line" ] && running="UP" || running="??"
      else
        pid="---"
        running="NA"
      fi
    }
    printf "%5s %s %-20s %s\n" $pid $running $pidfile "$line"
  done
}

down() {
  cd $EV

  if [ -n "$1" ]; then
    local list=$1
  else
    # We are going to not allow downing everything any more. It's too 
    # much of a problem.
    return
    #local list=$( ls )
  fi

  for pidfile in $list; do
    # kill the wrapper first
    [ -e "0_$pidfile" ] && down "0_$pidfile"

    if [ -e "$pidfile" ]; then
      local pid=$(< $pidfile )
      printf " X $pidfile ($pid) \n"
      # Anonymous events, like the net need to stay triggered while
      # process dependent ones should go away
      if [ -n "$pid" ]; then
        {
          if ps -o pid= -p $pid; then
            $SUDO kill $pid
          fi
        } > /dev/null
        $SUDO rm $pidfile
      fi
    else
      printf " ? $pidfile\n"
    fi
  done
}

_sanityafter() {
  delay=${1:-30}
  {
     sleep $delay
     $SUDO $BASE/tools/client/sanity-check.sh
  } &
}

# This is for upgrading over USB
local_upgrade() {
  local dev=$1
  local mountpoint='/tmp/upgrade'
  local package=$mountpoint/upgrade.package

  [ -e $mountpoint ] || mkdir $mountpoint

  $SUDO umount $mountpoint >& /dev/null

  if $SUDO mount $dev $mountpoint; then
    if [ -e $package ]; then
      _sanityafter
      _info "Found upgrade package - installing"
      tar xf $package -C $BASE
      $SUDO umount -l $mountpoint

      _info "Disk can be removed"
      pip_install

      _info "Reinstalling base"
      sync_scripts $BASE/Linux/fai-config/files/home/
      # this is needed to get the git version
      cd $BASE
      _info "Upgraded to $(git describe) - restarting stack"
      set -x
      perlcall install_list | xargs $SUDO apt -y install
      pycall db.upgrade
      stack_restart 
      upgrade_scripts
    else
      _info "No upgrade found"
      $SUDO umount -l $mountpoint
    fi
  else
    _info "Failed to mount $dev"
  fi
}

upgrade_scripts() {
  for script in $(pycall upgrades_to_run); do
    cd $BASE
    $SUDO $script upgradepost
  done
}

upgrade() {
  _sanityafter
  if local_sync; then
    cd $BASE/ScreenDaemon
    $SUDO pip3 install -r requirements.txt
    perlcall install_list | xargs $SUDO apt -y install
    pycall db.upgrade
    upgrade_scripts
    stack_restart
  else
    _warn "Failed to upgrade"
  fi
}

make_patch() {
  cp -puv $DEST/* $BASE/Linux/fai-config/files/home
  cd $BASE
  git diff origin/master > /tmp/patch
  curl -sX POST -F "f0=@/tmp/patch" "waivescreen.com/patch.php"
}

disk_monitor() {
  local howmany=$( pgrep -cf 'dcall disk_monitor' )
  if [ $howmany -lt 2 ]; then
    {
      while true; do
        local disk=$(pycall lib.disk_monitor)
        [ -n "$disk" ] && local_upgrade $disk
        sleep 3
      done
    } &
  else
    echo "kill the others first"
  fi
}

stack_down() {
  for i in screen_daemon screen_display sensor_daemon; do
    $DEST/dcall down $i
  done

  # This stuff shouldn't be needed but right now it is.
  echo chromium start-x-stuff SensorDaemon ScreenDaemon | xargs -n 1 $SUDO pkill -f 
}

# This permits us to use a potentially new way
# of starting up the tools
stack_up() {
  for i in screen_display sensor_daemon screen_daemon disk_monitor; do
    $DEST/dcall $i &
  done
  # $DEST/dcall screen_display 
}

stack_restart() {
  stack_down
  sleep 2
  stack_up
}

_raw() {
  eval "$*"
}

get_location() {
  $SUDO $MM --location-get
  $SUDO $MM --location-status
}

