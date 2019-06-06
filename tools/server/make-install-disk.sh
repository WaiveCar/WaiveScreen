#!/bin/bash
#
# NODISK    - Won't do disk things 
# NONET     - Won't try to do internet stuff
# NOMIRROR  - Won't do the mirroring
#
##

die() {
  echo $1
  exit 1
}
if [ -z "$NODISK" ]; then
  [ $# -lt 1 ] && die "You need to pass a disk dev entry to install to such as /dev/sdb"
  disk=$1
  echo "Installing to $disk"
  sudo fdisk -l $disk
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

dir=$HOME/usb
file=$HOME/WaiveScreen-$(date +%Y%m%d%H%M)-$(git describe).iso


# Place the pip stuff there regardless every time.
NONET=1 $DIR/syncer.sh pip || die "Can't sync"
NONET=1 $DIR/syncer.sh force || die "Can't force an update"

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

if [ -z "$NODISK" ]; then
  echo "Writing to $disk"

  if [ -e "$file" ]; then
    dd if=$file | pv -s $size | sudo dd of=$disk bs=2M
  else
    echo "$file does not exist, Bailing!"
  fi
else 
  echo dd if=$file | pv -s $size | sudo dd of=$disk bs=2M
fi

