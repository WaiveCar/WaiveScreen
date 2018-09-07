modprobe qmi_wwan

if [ -z "`pgrep ModemManager`" ]; then
  /usr/local/sbin/ModemManager&
fi
qmi-network /dev/cdc-wdm1 start
mmcli -m 0 --simple-connect="apn=internet"
wwan=`ip addr show | grep ww | head -1 | awk -F ':' ' { print $2 } '`


# Show the config | find ipv4 | drop the LHS | replace the colons with equals | drop the whitespace | put everything on one line
eval `mmcli -b 0 | grep -A 3 IPv4| awk -F '|' ' { print $2 } ' | sed s'/: /=/' | sed -E s'/\s+//' | tr '\n' ';'`

sudo ip addr add $address/$prefix  dev $wwan
sudo ip route add default via $gateway dev $wwan

ntpdate -v pool.ntp.org

# get ipv6
dhclient -6 -v $wwan&
cp /root/resolv.conf /etc/resolv.conf
