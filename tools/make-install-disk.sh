#!/bin/bash
if [ $# -lt 1 ]; then
  echo "You need to pass a disk dev entry to install to such as /dev/sdb"
  exit
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

disk=$1
now=$(date +%Y%m%d%H%M)
current=$(git describe)
dir=$HOME/usb
file=$HOME/WaiveScreen-$now-$current.iso
isopath=/srv/fai/config/files/home/WaiveScreen
{
  cd $isopath
  toiso=$(git describe)
}

echo "Installing to $disk"
sudo fdisk -l $disk

echo "$current: current"
echo "$toiso: $isopath"
if [ "$current" != "$toiso" ]; then
  echo "Out of date ... syncing"
  NONET=1 $DIR/syncer.sh force
else
  echo "Not syncing"
fi

if [ "$NOMIRROR" ]; then
  echo "Skipping mirroring"
else
  echo "Using $dir - some serious space is probably needed"
  [ -e $dir ] && rm -rf $dir
  mkdir -p $dir
  fai-mirror -v -cDEBIAN $dir
fi

echo "Creating a bootable iso named $file"
sudo fai-cd -m $dir $file
size=$(stat -c %s $file)
echo "Writing to $disk"

if [ -e "$file" ]; then
  dd if=$file | pv -s $size | sudo dd of=$disk bs=2M
else
  echo "$file does not exist, Bailing!"
fi

