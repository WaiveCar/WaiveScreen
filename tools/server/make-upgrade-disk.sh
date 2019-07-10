#!/bin/bash
#
# NODISK  - Won't do disk things 
# NOCLONE - Will skip over cloning
# NOPIP   - Skips over pip install
# LOCAL   - Just use local code

die() {
  exit $1
  exit
}

[[ -z "$NODISK" ]] && [[ $# -lt 1 ]] && die "You need to pass a dev entry for it such as /dev/sdb1"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

disk=$1
path=/tmp/upgradedisk
package=/tmp/upgrade.package
mount=/tmp/mount
dest_home=$path/Linux/fai-config/files/home

if [[ -z "$NOCLONE" ]]; then
  [[ -d $path ]] && sudo rm -fr $path
  mkdir -p $path

  if [[ -n "$LOCAL" ]]; then
    echo "Using local code"
    cp -puvr $DIR/../../* $path

  else
    git clone git@github.com:WaiveCar/WaiveScreen.git $path
    mkdir -p $dest_home/pip
    [[ -z "$NOPIP" ]] && pip3 download -d $dest_home/pip -r $path/ScreenDaemon/requirements.txt
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

if [[ -z "$NODISK" ]]; then
  [[ -e $disk ]] || die "Woops, $disk doesn't exist. Check your spelling."
  [[ -e $mount ]] || mkdir $mount
  sudo umount $mount >& /dev/null 
  sudo mount $disk $mount || die "Can't mount $disk on $mount - fix this and then rerun with the NOCLONE=1 env variable to skip the cloning"
  sudo cp -v $package $mount
  sudo umount $mount
fi
