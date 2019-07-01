#!/bin/bash
#
# NODISK    - Won't do disk things 
# NONET     - Won't try to do internet stuff
# MIRROR    - Will (re)do the mirroring
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
  local size=$(stat -c %s $1)
  echo "sudo dd if=$1 of=$2 bs=1M"
}

if [[ -z "$NODISK" ]]; then
  [[ $# -lt 1 ]] && die "You need to pass a disk dev entry to install to such as /dev/sdb"
  disk=$1
  [[ -b $disk ]] || die "Woops, $disk isn't a disk"
  [[ $(stat -c %T $disk) -eq 11 ]] && die "Woah, $disk is a PARTITION. I need the whole disk."

  sudo fdisk -l $disk

  if [[ -n "$ONLYDISK" ]]; then
    eval $(ddcmd $(ls -tr1 $HOME/Wai*| tail -1) $disk) 
    exit
  fi
fi

if [[ -z "$NOPIP" ]]; then
  NONET=1 $DIR/syncer.sh pip || die "Can't sync"
  NONET=1 $DIR/syncer.sh force || die "Can't force an update"
fi

if [ "$MIRROR" -o ! -e $dir ]; then
  mkdir -p $dir
  fai-mirror -v -cDEBIAN $dir
fi

echo "Creating a bootable iso named $file"
sudo fai-cd -m $dir $file

if [[ -z "$NODISK" ]]; then
  [[ -e "$file" ]] || die "$file does not exist, Bailing!"
  eval $(ddcmd $file $disk)
else 
  echo $(ddcmd $file $disk)
fi

