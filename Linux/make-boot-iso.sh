#!/bin/bash

dir=${1:-$HOME/usb}
file=${2:-bootable.iso}

echo "Using $dir - some serious space is probably needed"
mkdir -p $dir
fai-mirror -v -cDEBIAN $dir
fai-cd -m $dir $file
echo "Created a bootable iso named $file"

