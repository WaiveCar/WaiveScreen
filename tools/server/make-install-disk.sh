#!/bin/bash
#
# NODISK    - Won't do disk things 
# NONET     - Won't try to do internet stuff
# NOMIRROR  - Won't do the mirroring
# ONLYDISK  - Only creates a disk
# NOPIP     - Skip over pip download
#
##

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

dir=$HOME/usb
file=$HOME/WaiveScreen-$(date +%Y%m%d%H%M)-$(git describe).iso
backup=/home/chris/backup-test

die() {
  echo $1
  exit 1
}

ddcmd() {
  size=$(stat -c %s $1)
  echo "sudo dd if=$1 of=$2 bs=1M"
}

if [ -z "$NODISK" ]; then
  [ $# -lt 1 ] && die "You need to pass a disk dev entry to install to such as /dev/sdb"
  disk=$1
  [ -b $disk ] || die "Woops, $disk isn't a disk"
  [ $(stat -c %T $disk) -eq 11 ] && die "Woah, $disk is a PARTITION. I need the whole disk."


  echo "Installing to $disk"
  sudo fdisk -l $disk

  if [ -n "$ONLYDISK" ]; then
    echo $(ddcmd $(ls -tr1 $HOME/Wai*| tail -1) $disk) | /bin/bash
    exit
  fi
fi



# Place the pip stuff there regardless every time.
if [ -z "$NOPIP" ]; then
  NONET=1 $DIR/syncer.sh pip || die "Can't sync"
  NONET=1 $DIR/syncer.sh force || die "Can't force an update"
fi

if [ "$NOMIRROR" ]; then
  echo "Skipping mirroring"
else
  echo "Using $dir - some serious space is probably needed"
  # [ -e $dir ] && rm -rf $dir
  mkdir -p $dir
  fai-mirror -v -cDEBIAN $dir
fi

echo "Creating a bootable iso named $file"
sudo fai-cd -m $dir $file

if [ -z "$NODISK" ]; then

  if [ -e "$file" ]; then
    echo "Writing to $disk"
    eval $(ddcmd $file $disk)
  else
    echo "$file does not exist, Bailing!"
  fi
else 
  echo $(ddcmd $file $disk)
fi

