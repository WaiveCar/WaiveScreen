#!/bin/bash
#
# TODO: All of this in DBUS one day
#

sudo mmcli -m 0 --simple-connect="apn=internet"
wwan=`ip addr show | grep wwp | head -1 | awk -F ':' ' { print $2 } '`

# get ipv6
sudo dhclient $wwan

# Show the config | find ipv4 | drop the LHS | replace the colons with equals | drop the whitespace | put everything on one line
eval `mmcli -b 0 | grep -A 3 IPv4| awk -F '|' ' { print $2 } ' | sed s'/: /=/' | sed -E s'/\s+//' | tr '\n' ';'`

sudo ip addr add $address/$prefix  dev $wwan
sudo ip route add default via $gateway dev $wwan

cat > /etc/resolv.conf << ENDL
nameserver 8.8.8.8
nameserver 4.2.2.1
ENDL
