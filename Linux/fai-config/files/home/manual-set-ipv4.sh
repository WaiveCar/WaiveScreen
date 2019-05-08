#!/bin/bash

set -x
export PATH=$PATH:/usr/bin/

mmcli -m 0 -e

mmcli -m 0 \
	--location-enable-gps-raw \
	--location-enable-gps-nmea \
	--location-set-enable-signal

mmcli -m 0 --simple-connect="apn=internet"
wwan=`ip addr show | grep wwp | head -1 | awk -F ':' ' { print $2 } '`

if [ -z "$wwan" ]; then
  echo "Modem Not Found!!"
  exit -1
fi

# get ipv6
dhclient $wwan &

# Show the config | find ipv4 | drop the LHS | replace the colons with equals | drop the whitespace | put everything on one line
eval `mmcli -b 0 | grep -A 3 IPv4| awk -F '|' ' { print $2 } ' | sed s'/: /=/' | sed -E s'/\s+//' | tr '\n' ';'`

ip addr add $address/$prefix  dev $wwan
ip route add default via $gateway dev $wwan

cat << ENDL | tee /etc/resolv.conf
nameserver 8.8.8.8
nameserver 4.2.2.1
nameserver 2001:4860:4860::8888 
nameserver 2001:4860:4860::8844
ENDL

