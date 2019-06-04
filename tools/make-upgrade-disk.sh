#!/bin/bash
if [ $# -lt 1 ]; then
  echo "You need to pass a dev entry for it such as /dev/sdb1"
  exit
fi

disk=$1
path=/tmp/upgradedisk
package=/tmp/upgrade.package
mount=/tmp/mount

if [ -z "$NOCLONE" ]; then
  [ -e $path ] && rm -fr $path
  mkdir $path
  git clone git@github.com:WaiveCar/WaiveScreen.git $path
  cd $path

  #
  # This is not a mistake, this was tested among xz, compress, bzip2, 
  # and gzip
  #
  # After testing, xz was only a 2% space gain over boring straight .tar
  # Also it was 26 seconds versus < 0.1. Since this is going to be
  # on physical medium we want to minimize time, not space. Even in
  # decompression we are talking 2 sec versus < 0.1. So we'll do
  # generic bland .tar since it's 2 orders of magnitude faster
  #
  tar -cf $package .
  echo "cleaning up"
  rm -fr $path
  echo "Upgrade package at $package"
fi

[ -e $mount ] || mkdir $mount
sudo umount $mount >& /dev/null 

if sudo mount $disk $mount; then
  sudo cp -v $package $mount
  sudo umount $mount
else
  echo "Can't mount $disk on $mount - fix this and then rerun with the NOCLONE=1 env variable to skip the cloning"
fi
