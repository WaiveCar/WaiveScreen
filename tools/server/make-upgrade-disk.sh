#!/bin/bash
#
# RESET   - Will remove the previous copy of the code and start afresh
# NODISK  - Won't do disk things 
# NOCLONE - Will skip over cloning
# NOPIP   - Skips over pip install
# LOCAL   - Just use local code
#
##

if [ -z "$NODISK" ]; then
  if [ $# -lt 1 ]; then
    echo "You need to pass a dev entry for it such as /dev/sdb1"
    exit
  fi
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

disk=$1
path=/tmp/upgradedisk
package=/tmp/upgrade.package
mount=/tmp/mount
dest_home=$path/Linux/fai-config/files/home

if [ -n "$RESET" ]; then
  [ -e $path ] && rm -fr $path
fi

[ -d $path ] || mkdir $path

if [ -z "$NOCLONE" ]; then
  if [ -n "$LOCAL" ]; then
    echo "Using local code"
    cp -puvr $DIR/../../* $path
  elif [ -e $path ]; then
    cd $path
    if ! git pull; then
      cd /tmp
      rm -fr $path
      git clone git@github.com:WaiveCar/WaiveScreen.git $path
      cd $path
    fi
    [ -z "$NOPIP" ] && pip3 download -d $dest_home/pip -r $path/ScreenDaemon/requirements.txt
  else
    mkdir $path
    git clone git@github.com:WaiveCar/WaiveScreen.git $path
    mkdir -p $dest_home/pip
    [ -z "$NOPIP"] && pip3 download -d $dest_home/pip -r $path/ScreenDaemon/requirements.txt
    cd $path
  fi

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
  echo "Upgrade package at $package"
fi

if [ -z "$NODISK" ]; then
  if [ ! -e $disk ]; then
    echo "Woops, $disk doesn't exist. Check your spelling."
    exit
  fi

  [ -e $mount ] || mkdir $mount
  sudo umount $mount >& /dev/null 

  if sudo mount $disk $mount; then
    sudo cp -v $package $mount
    sudo umount $mount
    exit
  fi
  echo "Can't mount $disk on $mount - fix this and then rerun with the NOCLONE=1 env variable to skip the cloning"
fi
