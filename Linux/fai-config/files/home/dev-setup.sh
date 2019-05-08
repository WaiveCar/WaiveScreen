#!/bin/bash
#
# note! runs as normal user
#
sudo /usr/sbin/dhclient enp3s0 
[ -e WaiveScreen.nfs ] || mkdir WaiveScreen.nfs

/usr/bin/sshfs dev:/home/chris/code/WaiveScreen WaiveScreen.nfs -C
