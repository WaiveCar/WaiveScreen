#!/bin/bash

dir=${1:-$HOME/usb}
file=${2:-bootable.iso}

if [ "$NOMIRROR" ]; then
  echo "Skipping mirroring"
else
  echo "Using $dir - some serious space is probably needed"
  mkdir -p $dir
  fai-mirror -v -cDEBIAN $dir
fi

sudo fai-cd -m $dir $file
echo "Created a bootable iso named $file"

