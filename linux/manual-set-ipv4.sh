#!/bin/bash

sudo mmcli -m 0 -e

sudo mmcli -m 0 \
	--location-enable-gps-raw \
	--location-enable-gps-nmea \
	--location-set-enable-signal

sudo mmcli -m 0 --simple-connect="apn=internet"
wwan=`ip addr show | grep wwp | head -1 | awk -F ':' ' { print $2 } '`

# get ipv6
sudo dhclient $wwan

# Show the config | find ipv4 | drop the LHS | replace the colons with equals | drop the whitespace | put everything on one line
eval `mmcli -b 0 | grep -A 3 IPv4| awk -F '|' ' { print $2 } ' | sed s'/: /=/' | sed -E s'/\s+//' | tr '\n' ';'`

sudo ip addr add $address/$prefix  dev $wwan
sudo ip route add default via $gateway dev $wwan

cat << ENDL | sudo tee /etc/resolv.conf
nameserver 8.8.8.8
nameserver 4.2.2.1
nameserver 2001:4860:4860::8888 
nameserver 2001:4860:4860::8844
ENDL
