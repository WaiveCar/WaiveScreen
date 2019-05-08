#!/bin/bash
/usr/sbin/dhclient enp3s0 
[ -e WaiveScreen.nfs ] || mkdir WaiveScreen.nfs
/usr/bin/sshfs chris@172.16.10.1:/home/chris/code/WaiveScreen WaiveScreen.nfs -C
