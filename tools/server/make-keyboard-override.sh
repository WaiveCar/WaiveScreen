#!/bin/bash

die() {
  echo $1
  exit
}

[[ $# -lt 1 ]] && die "You need to pass a dev entry for it such as /dev/sdb1"

disk=$1
mount=/tmp/mount
magic_override_file=voHCPtpJS9izQxt3QtaDAQ_make_keyboard_work

[[ -e $disk ]] || die "Woops, $disk doesn't exist. Check your spelling."
[[ -e $mount ]] || mkdir $mount
sudo umount $mount >& /dev/null 
sudo mount $disk $mount || die "Can't mount $disk on $mount - fix this and then rerun with the NOCLONE=1 env variable to skip the cloning"
sudo touch $mount/$magic_override_file && echo "Made keyboard override file on $disk"
sudo umount $mount
