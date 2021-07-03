#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MM="mmcli -m 0"
FFMPEG="ffmpeg -loglevel panic -nostats -hide_banner -y -an"

. $DIR/const.sh
. $DIR/baseline.sh

_mkdir() {
  [[ -d $1 ]] && return
  $SUDO mkdir -p $1 
  $SUDO chmod 0777 $1
}

_mkdir $EV

die() {
  [[ "$2" == "info" ]] && _info "$1" || _error "$1"
  exit
}

_sqlite3() {
  sqlite3 -cmd ".timeout $SQLTIMEOUTMS" "$@"
}

show_locks() {
  local base=$( dirname $DB )
  lsof +d $base

  for pid in $(lsof +d $base | grep -v bash | awk ' { print $2 } ' | grep -v PID | sort | uniq); do
    echo
    echo $pid
    echo

    gdb -q /usr/bin/python3 << ENDL
      attach $pid
      py-locals
      py-bt
      bt
      detach
      quit
ENDL
  done
}

kv_get() {
  _sqlite3 $DB "select value from kv where key='$1'"
  [[ $? == 5 ]] && show_locks | grep -Ev "^(\(gdb|Reading symbols|done.)" >> $LOG/messages.log
}

# This _does not_ echo, it only returns whether the flag is set or not
sess_get() {
  local val=$(_sqlite3 $DB "select value from kv where key='$1' and bootcount=$(< /etc/bootcount )")
  # echo $val
  [[ -n "$val" ]] && return 0 || return 1
}

kv_unset() {
  _sqlite3 $DB "delete from kv where key='$1'"
}

kv_set() {
  pycall kv_set $*
}

kv_incr() {
  local curval=$(kv_get $1)
  if [[ -z "$curval" ]]; then 
    _sqlite3 $DB "insert into kv(key, value) values('$1',0)" &
    echo 0
  else
    curval=$(( curval + 1 ))
    _sqlite3 $DB "update kv set value=$curval where key='$1'";
    [[ $? == 5 ]] && show_locks >> $LOG/messages.log
    echo $curval
  fi
}

add_history() {
  local kind=$1
  local value=$2
  local extra=$3
  _sqlite3 $DB "insert into history(kind, value, extra) values('$kind','$value','$extra')" 
}

list() {
  # just show the local fuctions
  if [[ $# -gt 0 ]]; then
    while [[ $# -gt 0 ]]; do
      declare -f $1
      shift
    done
  else
    declare -F | sed s/'declare -f//g' | sort
  fi
}

_bigtext() {
  if [[ "$B64" ]]; then
    middle="base64 -d"
    unset B64
  else
    middle="cat"
  fi
  echo "$*" | $middle | aosd_cat -p 4 -n "DejaVu Sans 72" -R white -f 1500 -u 1200 -o 1500 -d 30 -b 216 -B black &
  echo "$*" | $middle
}

selfie() {
  local now=`date +%Y%m%d%H%M%S`
  local opts=''
  local num=0

  down camera_daemon
  pycall calibrate_cameras
  for i in $( seq 0 2 6 ); do
    $SUDO $FFMPEG -f v4l2 -video_size 1280x720 -i /dev/video$i -vframes 1 $CACHE/$now-$i.jpg 
  done

  # the above code is a built-in delay so that
  # we can *guess* that the asset is on the screen
  # by the time we get here.
  import -window root $CACHE/$now-screen.jpg

  for i in $CACHE/$now-screen.jpg $CACHE/$now-0.jpg $CACHE/$now-2.jpg $CACHE/$now-4.jpg $CACHE/$now-6.jpg; do
    if [[ -e "$i" ]]; then
      opts="$opts -F \"f$num=@$i\""
      (( num ++ ))
    fi
  done

  res=$(eval curl -sX POST $opts "$SERVER/selfie.php?pre=$now")
  [[ -n "$1" ]] && sms $sender "This just happened: $res. More cool stuff coming soon ;-)"
  echo $res
  camera_daemon
}

sms() {
  local phnumber=$1
  shift
  local number=$($SUDO $MM --messaging-create-sms="number=$phnumber,text='$*'" | awk ' { print $NF } ')
}

_mmsimage() {
  local file=$1
  local cmd="convert - -resize 450x -background black -gravity center -extent 450x450"

  dd skip=1 bs=$(( $(grep -abPo '(JFIF.*)' $file | awk -F : ' { print $1 }') - 6 )) if=$file | $cmd $file.jpg

  if [[ -s $file ]]; then
    echo '' | aosd_cat -n "FreeSans 0" -u 4000 -p 7 -d 225 -f 0 -o 0 &
    sleep 0.03
    display -window $(xwininfo -root -tree | grep aosd | head -1 | awk ' { print $1 } ') $file.jpg &
  fi
}

sms_cleanup() {
  [[ -n "$1" ]] && list=$1 || list=$($MM --messaging-list-sms | awk ' { print $1 } ')
  for i in $list; do
    [[ "$i" = "No" ]] && continue
    local num=$( kv_incr sms )

    # Try to make sure we aren't overwriting
    while [[ -e $SMSDIR/$num ]]; do
      num=$( kv_incr sms )
      sleep 0.02
    done

    $MM -s $i > $SMSDIR/$num
    grep -i "class: 1" $SMSDIR/$num > /dev/null && $MM -s $i --create-file-with-data=$SMSDIR/${num}.raw 
    $SUDO $MM --messaging-delete-sms=$i
  done
  pycall sess_set cleanup,1
}

text_loop() {
  _mkdir $SMSDIR
  local foundModem=

  while true; do
    if [[ -z "$foundModem" ]]; then
      if ! sess_get simok; then
        sleep 10
        continue
      fi
      foundModem=1
    fi

    sms=$(pycall lib.next_sms)

    if [[ -n "$sms" ]]; then
      eval $sms

      if [[ "$type" == "recv" ]]; then
        if [[ -n "$message" ]]; then
          sms_cleanup $dbuspath
          local text=$(echo "$message" | base64 -d)
          ws_browser "sms,$text"
          selfie $sender &
          sleep 2
          #local as_text=$(B64=1 _bigtext $message)
        else
          # Wait a while for the image to come in
          sleep 1.5
          local num=$(basename $dbuspath)
          $MM -s $dbuspath --create-file-with-data=$SMSDIR/${num}.raw
          sender=$(strings $SMSDIR/${num}.raw | grep ^+ | cut -c -12 )
          curl -s $(strings $SMSDIR/${num}.raw | grep http) > $SMSDIR/${num}.payload
          ( selfie $sender; sms_cleanup $dbuspath ) &
          _mmsimage $SMSDIR/${num}.payload
          sleep 0.5
        fi
      else
        sms_cleanup $dbuspath 
      fi
    fi
  done
}

_log() {
  echo $(date +"%Y-%m-%d %H:%M:%S") $(< /etc/bootcount) "$*" | $SUDO tee -a $LOG/messages.log
}

_onscreen() {
  [[ -e /tmp/offset ]] && offset=$(< /tmp/offset ) || offset=0

  local size=12

  echo $1 | osd_cat \
    -c $3 -d $4 \
    -u black -A right \
    -O 1 -o $offset \
    -f lucidasanstypewriter-bold-$size &

  _log "[$2]" "$1"
  offset=$(( (offset + size + 9) % ( (size + 9) * 28 ) ))

  echo $offset > /tmp/offset
  chmod 0666 /tmp/offset
}
_info() {
  _onscreen "$*" info white 8
}
_warn() {
  _onscreen "$*" warn yellow 30 
}
_error() {
  _onscreen "$*" error red 80
}

set_wrap() {
  local pid=${2:-$!}
  [[ -e $EV/0_$1 ]] && $SUDO rm $EV/0_$1
  echo -n $pid > $EV/0_$1
}

set_event() {
  local pid=${2:-$!}
  [[ -e $EV/$1 ]] || _info $1
  echo -n $pid | $SUDO tee $EV/$1
}

set_brightness() {
  local level=$1
  local nopy=$2

  if [[ -z "$nopy" ]]; then
    pycall arduino.set_backlight $level
  else
    local shift=$(perl -e "print .5 * $level + .5")
    local revlevel=$(perl -e "print .7 * $level + .3")

    for display in HDMI-1 HDMI-2; do
      DISPLAY=:0 xrandr --output $display --gamma 1:1:$shift --brightness $revlevel
    done
  fi
}

enable_gps() {
  $SUDO $MM -e
  $SUDO $MM \
    --location-set-enable-signal \
    --location-enable-gps-nmea \
    --location-enable-gps-raw \
    --location-enable-3gpp \
    --location-disable-agps
  if [[ $? ]]; then
    pycall db.sess_set modem,1
  fi
}

get_number() {
  # mmcli may not properly be reporting the phone number. T-mobile sends it to
  # us in our first text so we try to work it from there.
  phone=$( pycall lib.update_number_if_needed )
  if [[ -z "$phone" ]]; then
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

    if [[ ! $? ]]; then 
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
    $SUDO $MM --simple-disconnect
    $SUDO $MM --set-allowed-modes='3g|4g' --set-preferred-mode=4g
    $SUDO $MM --simple-connect="apn=internet,ip-type=ipv4v6"
    wwan=`ip addr show | grep ww[pa] | head -1 | awk -F ':' ' { print $2 } '`

    if [[ -z "$wwan" ]]; then
      _warn  "No modem found. Trying again"
      sleep 4
    else
      break
    fi
  done

  # get ipv6
  #$SUDO dhclient $wwan &

  # Show the config | find ipv4 | drop the LHS | replace the colons with equals | drop the whitespace | put everything on one line
  eval `mmcli -b 0 | grep -A 4 IPv4 | awk -F '|' ' { print $2 } ' | sed -E s'/: (.*)/="\1"/' | sed -E "s/^[\' ]+/four_/g" | tr '\n' ';'`
  eval `mmcli -b 0 | grep -A 4 IPv6 | awk -F '|' ' { print $2 } ' | sed -E s'/: (.*)/="\1"/' | sed -E "s/^[\' ]+/six_/g" | tr '\n' ';'`

  $SUDO ip addr flush dev $wwan
  $SUDO ip route flush 0/0
  $SUDO ifconfig $wwan up
  $SUDO ip addr add $four_address/$four_prefix dev $wwan
  $SUDO ip addr add $six_address/$six_prefix dev $wwan
  $SUDO ip route add default via $four_gateway dev $wwan
  $SUDO ip route add default via $six_gateway dev $wwan

  perl -l << EPERL | $SUDO tee /etc/resolv.conf
    @lines = split(/,\s*/, '$four_dns');
    foreach( @lines ) {
      print 'nameserver ', \$_;
    }
    @lines = split(/,\s*/, '$six_dns');
    foreach( @lines ) {
      print 'nameserver ', \$_;
    }
EPERL

  set_event net ''

  sleep 4

  if ping -c 1 -i 0.3 $SERVER; then
    _info "$SERVER found" 
    pycall db.sess_set simok,1 
  else
    _warn "$SERVER unresolvable!"

    # Well let's see if that small stanford project is still resolvable
    if ping -c 1 -i 0.3 yahoo.com; then
      _warn "Server likely down."
    else
      local ix=0
      while ! $MM; do
        (( ++ix < 4 )) && _info "Waiting for modem"
        sleep 9
      done

      hasip=$( ip addr show $wwan | grep inet | wc -l )

      (( hasip > 0 )) && _warn "Data plan/SIM issues." || _warn "No IP assigned."
    fi
  fi
  pycall db.sess_set modem,1 
  get_number
}

## test this later.
network_check() {
  PING="ping -c 1 -i 0.3"
  if $PING $SERVER; then
    echo UP
  elif $PING yahoo.com; then
    echo SERVER_DOWN
  elif $PING 8.8.8.8; then
    echo DNS
  else
    echo DOWN
  fi
}

first_run() {
  if [[ -z $(kv_get first_run) ]]; then
    set -x
    #$SUDO systemctl disable hostapd
    sudo nmcli connection add type wifi ifname wlan0 con-name REEF_CORP ssid REEF_CORP 802-11-wireless-security.key-mgmt WPA-PSK 802-11-wireless-security.psk 'M!am!2021'
    $SUDO systemctl enable location-daemon
    $SUDO apt -y update || die "Can't find network" info
    kv_set first_run,1
  fi
}

pycall() {
  $BASE/ScreenDaemon/dcall $*
}

ssh_hole() {
  local event=ssh_hole

  # I think this is causing problems. Either the event pattern works or it doesn't.
  # (( $(pgrep -cf dcall\ ssh_hole ) > 1 )) && die "ssh_hole already running" info

  ssh-keygen -f "$DEST/.ssh/known_hosts" -R "reflect.screen.waive.com"
  {
    while true; do
      local port=$(kv_get port)
      
      if [[ -z "$port" ]]; then
        # This will cycle on a screen that's not properly
        # installed. That's kinda unnecessary
        # _warn "Cannot contact the server for my port"
        /bin/true

      elif [[ -e $EV/$event ]] && ps -o pid= -p $(< $EV/$event ); then
        # this means we have an ssh open and life is fine
        sleep $EVREST

      else
        ssh -oStrictHostKeyChecking=no -NC -R bounce:$port:127.0.0.1:22 bounce &
        set_event $event
      fi

      sleep $EVREST
    done
  } > /dev/null &

  set_wrap $event
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

camera_daemon() {
  down camera_daemon
  $BASE/ScreenDaemon/CameraDaemon.py &
  set_event camera_daemon
}

# This is used during the installation - don't touch it!
# {
pip_install() {
  pip3 -q install $DEST/pip/*
}

install() {
  cd $BASE/ScreenDaemon
  $SUDO pip3 install -r requirements.txt 
}
# } end of stuff used during the install that you 
# SHOULD NOT REMOVE

get_state() {
  local uuid=$(< /etc/UUID)
  local now=$(date +%Y%m%d%H%m%S)
  local myname=state-$uuid-$now
  local archive=${myname}.tbz
  local path=/tmp/$uuid/$now
  mkdir -p $path

  cp -r $SMSDIR $LOG $path
  cp $DEST/.bash_history /var/log/wtmp /proc/uptime /etc/bootcount /etc/UUID $path
  $SUDO cp /var/log/daemon.log $path
  $SUDO chmod 0666 $path/daemon.log

  _sqlite3 $DB .dump > $path/backup.sql

  get_version > $path/version 

  cd /tmp/
  tar cjf /tmp/$archive $uuid/$now
  curl -sX POST -F "f0=@/tmp/$archive" "$SERVER/api/state" > /dev/null && echo $archive || _log "Could not send"
}

get_uuid() {
  local UUIDfile=/etc/UUID
  if [ -n "$1" -o ! -e $UUIDfile -o $# -gt 1 ]; then
    {
      # The MAC addresses are just SOOO similar we want more variation so let's md5sum
      local uuid_old=$(< $UUIDfile )
      local uuid="unknown"
      for eth_addr_file in /sys/class/net/{enp3s0,eth0}/address; do
        if [[ -f "${eth_addr_file}" ]]; then
          uuid=$(cat "${eth_addr_file}" | md5sum | awk ' { print $1 } ' | xxd -r -p | base64 | sed -E 's/[=\/\+]//g')
          break
        fi
      done

      if [[ "$uuid" != "$uuid_old" ]]; then
        kv_set uuid,$uuid
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

_screen_display_single() {
  export DISPLAY=${DISPLAY:-:0}
  local app=$BASE/ScreenDisplay/display.html 

  [[ -e $app ]] || die "Can't find $app. Exiting"

  _as_user chromium --kiosk \
    --check-for-update-interval=2147483647 \
    --incognito \
    --disable-translate --disable-features=TranslateUI \
    --fast --fast-start \
    --disable-infobars --noerrdialogs \
    --remote-debugging-port=9222 --user-data-dir=remote-profile \
    --no-first-run --non-secure --default-background-color='#000' file://$app &
  set_event screen_display
}

screen_display() {
  local ix=0
  {
    while pgrep Xorg; do
      while pgrep chromium; do
        sleep $EVREST
        [[ -e $EV/0_screen_display ]] || return
        [[ "$(< $EV/0_screen_display )" != "$pid" ]] && return
      done

      _screen_display_single
    done
  } >> /tmp/screen_display.log &
  local pid=$!

  set_wrap screen_display $pid
}

wait_for() {
  path=${2:-$EV}/$1

  if [[ ! -e "$path" ]]; then
    echo $(date +%R:%S) WAIT $1
    until [[ -e "$path" ]]; do
      sleep 0.5
    done

    # Give it a little bit after the file exists to
    # avoid unforseen race conditions
    sleep 0.05
  fi
}

running() {
  cd $EV
  for pidfile in $( ls ); do
    local pid=$(< $pidfile )
    local line="-"
    {
      if [[ -n "$pid" ]]; then 
        line=$(ps -o start=,command= -p $(< $pidfile ))
        [[ -n "$line" ]] && running="UP" || running="??"
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

  local pidfile
  _log down $1
  for pidfile in $1; do
    # kill the wrapper first
    [[ -e "0_$pidfile" ]] && down "0_$pidfile"

    if [[ -e "$pidfile" ]]; then
      local pid=$(< $pidfile )
      printf " X $pidfile ($pid) \n"
      # Anonymous events, like the net need to stay triggered while
      # process dependent ones should go away
      if [[ -n "$pid" ]]; then
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


hotspot() {
  # Only run if we have wifi
  eval $(pycall feature_detect)
  if [[ -z "$wifi" ]]; then
    $SUDO service hostap stop
    return
  fi

  SSID=Waive-$( kv_get number | cut -c 6- )
  DEV_INTERNET=$( ip addr show | grep ww[pa] | head -1 | awk -F ':' ' { print $2 } ' )
  DEV_AP=$( ip addr show | grep wl[pa] | head -1 | awk -F ': ' ' { print $2 } ' )

  IP_START=172.16.10
  IP_END=.1
  IP_AP=$IP_START$IP_END

  MASK_AP=255.255.255.0
  CLASS_AP=24

  cat << endl | $SUDO tee /etc/hostapd/hostapd.conf
logger_syslog=-1
logger_syslog_level=2
interface=$DEV_AP
driver=nl80211
ssid=$SSID
channel=11
hw_mode=g
ieee80211n=1
wmm_enabled=1
ht_capab=[HT40-][SHORT-GI-20][SHORT-GI-40]
country_code=US
eap_server=0
macaddr_acl=0
logger_stdout=-1
ignore_broadcast_ssid=0
endl

  $SUDO sed -i -r 's/(INTERFACESv4=).*/INTERFACESv4="'$DEV_AP'"/' /etc/default/isc-dhcp-server

  cat << endl | $SUDO tee /etc/dhcp/dhcpd.conf
  ddns-update-style none;
  default-lease-time 600;
  subnet ${IP_START}.0 netmask $MASK_AP {
    range ${IP_START}.5 ${IP_START}.30;
    option domain-name-servers 8.8.4.4,1.1.1.1,8.8.8.8,1.0.0.1;
    option routers $IP_AP;
    option broadcast-address ${IP_START}.255;
    default-lease-time 60000;
    max-lease-time 720000;
  }
endl

  $SUDO pkill -f hostapd
  sleep 1
  $SUDO service hostapd restart #/etc/hostapd/hostapd.conf&
  #$SUDO hostapd /etc/hostapd/hostapd.conf&

  $SUDO sysctl net.ipv4.conf.all.forwarding=1

  $SUDO ifconfig $DEV_AP $IP_AP netmask $MASK_AP
  $SUDO ip route add ${IP_START}.0/$CLASS_AP dev $DEV_AP

  $SUDO service isc-dhcp-server stop
  [[ -e /var/run/dhcpd.pid ]] && $SUDO rm /var/run/dhcpd.pid
  sleep 1
  $SUDO service isc-dhcp-server start

  $SUDO iptables -F
  $SUDO iptables --table nat -F
  $SUDO iptables --table mangle -F
  $SUDO iptables -X
  $SUDO iptables -A INPUT -i lo -j ACCEPT

  $SUDO iptables --table nat --append POSTROUTING --out-interface $DEV_INTERNET -j MASQUERADE
  $SUDO iptables --append FORWARD --in-interface $DEV_AP -o $DEV_INTERNET -j ACCEPT 
  $SUDO iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
  $SUDO iptables -A FORWARD -p tcp -m multiport --dports 80,443,110,53 -j ACCEPT 
  $SUDO iptables -A INPUT -m state --state NEW -j ACCEPT
}

_sanityafter() {
  delay=${1:-30}
  ( sleep $delay; $SUDO $BASE/tools/client/sanity-check.sh ) &
}

nosanity() {
  pycall sess_set nosanity
  if pgrep sanity-check.sh; then
    _log "nosanity: killing running sanity-check.sh"
    $SUDO pkill sanity-check.sh
  fi
}

upgrade_scripts() {
  for script in $(pycall upgrades_to_run); do
    cd $BASE
    local upgrade_dir="${BASE}/Linux/upgrade"
    # we do this every time because some upgrades
    # may call for a reboot
    _log "[upgrade-script] $script"

    # #153, well the start of it at least.
    add_history upgrade_script $script
    kv_set last_upgrade,$script

    local res=$($SUDO "${upgrade_dir}/$script" upgradepost)
    # If we survived the script and it didn't reboot
    # then we have the pleasure of storing the output
    # of the script, hopefully without issue.
    # REMOVED: This was running into problems with the script output being un-escaped.
    #sqlite3 $DB "update history set extra='$res' where value='$script' and kind='$upgrade'"
    _log "${script} output: ${res}"
  done
}

_upgrade_pre() {
  local usb_repo="${1}"
  local old_repo="$(readlink -f ${BASE})"
  local old_repo_link="${DEST}/.WaiveScreen.old"
  local new_repo_link="${DEST}/.WaiveScreen.new"
  local date_string="$(date +%Y%m%d%H%M)"

  # Remove old versions if they're there
  if [[ -L "${old_repo_link}" ]]; then
    local old_old_repo="$(readlink -f ${old_repo_link})"
    if [[ -d "${old_old_repo}" ]] && [[ "${old_old_repo}" != "${old_repo}" ]] && [[ "${DEST}" = "$(dirname ${old_old_repo})" ]]; then
      _log "Removing old install directory: ${old_old_repo}"
      $SUDO rm -rf "${old_old_repo}"
    fi
  fi

  ln -sTf "$(basename ${old_repo})" "${old_repo_link}"

  if [[ -z "${usb_repo}" ]]; then
    # Fetch the latest info from github and get the
    # name of the new version of our branch.
    cd "${old_repo}"
    # Files disappear during copy if we don't do this
    git config --add gc.autoDetach false
    git fetch --force --tags origin ${BRANCH}
    git config --unset gc.autoDetach
    local new_repo="${DEST}/.WaiveScreen-${date_string}-$(git describe origin/${BRANCH})"

    # Make a copy of the existing repository
    # and use that for our upgrade.
    cp -av "${old_repo}" "${new_repo}"
  else
    # Get the name of the new version
    cd "${usb_repo}"
    local new_repo="${DEST}/.WaiveScreen-${date_string}-$(git describe)"

    # Move the usb files to the properly named directory
    mv "${usb_repo}" "${new_repo}"
    chmod 0755 "${new_repo}"
  fi

  # Update links
  ln -sTf "$(basename ${new_repo})" "${new_repo_link}"
  ln -sTf "$(basename ${new_repo})" "${BASE}"
}

_upgrade_post() {
  local version=$(get_version)

  $SUDO dpkg --configure -a
  $SUDO apt install -fy
  perlcall install_list | xargs $SUDO apt -y install
  $SUDO apt -y autoremove

  pycall db.upgrade
  add_history upgrade "$version"

  #update_arduino
  upgrade_scripts
  $SUDO systemctl restart location-daemon
  stack_restart 
  _info "Now on $version"
}

ws_browser() {
  curl -sX POST --data "$*" localhost:4096/browser
}

# This is for upgrading over USB
local_disk() {
  local dev=$1
  local mountpoint='/tmp/upgrade'
  local package=$mountpoint/upgrade.package

  _mkdir $mountpoint

  $SUDO umount $mountpoint >& /dev/null

  if $SUDO mount $dev -o uid=$(id -u $WHO),gid=$(id -g $WHO) $mountpoint; then
    if [[ -e $mountpoint/voHCPtpJS9izQxt3QtaDAQ_make_keyboard_work ]]; then
      $SUDO modprobe usbhid hid_apple
      pycall db.sess_set keyboard_allowed,1 
      _info "Keyboards are now enabled"

    elif [[ -e $package && -z "$2" ]]; then
      _sanityafter
      _info "Found upgrade package - installing"
      local usb_temp="$(mktemp -d)"
      tar xf $package -C "${usb_temp}"
      _upgrade_pre "${usb_temp}"
      $SUDO umount -l $mountpoint

      _info "Disk can be removed"

      DEST="${BASE}/Linux/fai-config/files/home" pip_install

      # cleanup the old files
      cd $BASE && git clean -fxd

      _info "Reinstalling base"
      sync_scripts $BASE/Linux/fai-config/files/home/
      # This should call the new _upgrade_post function
      dcall _upgrade_post
    else
      _info "No upgrade found"
      $SUDO umount -l $mountpoint
    fi
  else
    _info "Failed to mount $dev"
  fi
}

upgrade() {
  if [[ -n "$(kv_get driving_upgrade)" ]]; then
    _error "Can NOT upgrade while driving_upgrade is queued."
    return 1
  fi
  _info "Upgrading... Please wait"
  {
    set -x
    _sanityafter
    _upgrade_pre
    if local_sync; then
      # note: git clean only goes deeper, it doesn't do by default the entire repo
      cd $BASE && git clean -fxd
      $SUDO pip3 install -r $BASE/ScreenDaemon/requirements.txt
      # This should call the new _upgrade_post function
      dcall _upgrade_post
    else
      _warn "Failed to upgrade"
    fi
  } |& $SUDO tee -a /var/log/upgrade.log &
}

driving_upgrade() {
  # Wait 2 minutes so there's a good chance the system is stable.
  sleep 120
  local speed_count=0
  local speed=0
  local upgrade_speed="$(kv_get driving_upgrade_speed)"
  upgrade_speed="${upgrade_speed:-95}"
  while sleep 1; do
    speed="$(mmcli -m 0 --location-get | grep GPVTG | cut -d ',' -f 8 | cut -d '.' -f 1)"
    if [[ ${speed} -gt ${upgrade_speed} ]]; then
      ((++speed_count))
      if [[ $speed_count -eq 5 ]]; then
        _log "driving_upgrade: Hit target speed of ${upgrade_speed} km/h. Starting upgrade."
        kv_unset driving_upgrade
        kv_unset driving_upgrade_speed
        upgrade
        break
      fi
    else
      speed_count=0
    fi
  done
}

driving_upgrade_check() {
  if [[ -n "$(kv_get driving_upgrade)" ]]; then
    if [[ "$(get_version)" == "$(kv_get driving_upgrade)" ]]; then
      _log "driving_upgrade_check: starting driving_upgrade"
      driving_upgrade &
    else
      _log "driving_upgrade_check: Upgrade already happened (must have been over USB)."
      kv_unset driving_upgrade
      kv_unset upgrade_speed
    fi
  fi
}

debug() {
  down sensor_daemon
  DEBUG=1 $SUDO $BASE/ScreenDaemon/SensorDaemon.py 
}

make_patch() {
  cp -pu $DEST/* $DEST/.* $BASE/Linux/fai-config/files/home
  cd $BASE
  git diff origin/$BRANCH > /tmp/patch
  [[ -s /tmp/patch ]] && curl -sX POST -F "f0=@/tmp/patch" "$SERVER/patch.php" || echo "No changes"
}

disk_monitor() {
  (( $( pgrep -cf 'dcall disk_monitor' ) < 1 )) || return
  {
    while true; do
      local disk=$(pycall lib.disk_monitor)
      [[ -n "$disk" ]] && local_disk $disk
      sleep 3
    done
  } &
}

_avrdude() {
  $BASE/tools/client/avrdude -C$BASE/tools/client/avrdude.conf \
    -v -patmega328p -carduino -P/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0 -b57600 -D \
    $*
}

update_arduino() {
  local my_arduino_version=$(pycall kv_get arduino_version)
  local new_arduino_version=$(< ${BASE}/tools/client/sensors.ino.version)

  if [[ "${my_arduino_version}" != "${new_arduino_version}" ]]; then
    local sensors_backup=/tmp/sensors_backup.ino.hex
    local final_cmds="pycall sess_del nosanity; sensor_daemon"

    _warn "Updating arduino.  Please do not turn the car off."
    nosanity
    sleep 1
    down sensor_daemon
    sleep 2

    # Backup existing image
    if ! _avrdude -Uflash:r:${sensors_backup}:i ; then
      _error "Unable to backup Arduino image.  Aborting update."
      eval $final_cmds
      return 1
    fi

    # Flash new image
    if ! _avrdude -Uflash:w:$BASE/tools/client/sensors.ino.hex:i ; then
      _error "Unable to flash new Arduino image."
    fi

    # Test new image
    if [[ -z "$(pycall arduino_read)" ]]; then
      _error "New Arduino image FAILED read test.  Rolling back to previous version"
      if ! _avrdude -Uflash:w:${sensors_backup}:i ; then
        _error "Unable to flash previous Arduino image.  We may have borked it.  Call for help."
      fi
    fi
    eval $final_cmds
  fi
}

stack_down() {
  for i in screen_daemon screen_display; do
    $DEST/dcall down $i
  done

  # This stuff shouldn't be needed but right now it is.
  echo chromium start-x-stuff ScreenDaemon | xargs -n 1 $SUDO pkill -f
}

# This permits us to use a potentially new way
# of starting up the tools
stack_up() {
  for i in screen_display screen_daemon disk_monitor; do
    $DEST/dcall $i &
  done
}

stack_restart() {
  stack_down
  sleep 2
  stack_up
}

_raw() {
  eval "$*"
}

acceptance_test() {
  _bigtext 'Loading...⌛'
  set_brightness 1
  if perlcall acceptance_screen; then
    _as_user chromium --app=file:///tmp/acceptance.html
  else
    _warn "Acceptance test failed!"
  fi
}

get_location() {
  $SUDO $MM --location-get
  $SUDO $MM --location-status
}
