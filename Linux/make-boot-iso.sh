#!/bin/bash

now=$(date +%Y%m%d%H%M)
dir=${1:-$HOME/usb}
file=${2:-$HOME/WaiveScreen-$now.iso}

if [ "$NOMIRROR" ]; then
  echo "Skipping mirroring"
else
  echo "Using $dir - some serious space is probably needed"
  mkdir -p $dir
  fai-mirror -v -cDEBIAN $dir
fi

echo "Creating a bootable iso named $file"
sudo fai-cd -m $dir $file
echo "dd if=bootable.iso of=/dev/sdXXXX bs=1M"

