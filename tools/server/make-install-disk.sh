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

ddcmd() {
  size=$(stat -c %s $1)
  echo "dd if=$1 | pv -s $size | sudo dd of=$2 bs=2M"
}

if [ -z "$NODISK" ]; then
  [ $# -lt 1 ] && die "You need to pass a disk dev entry to install to such as /dev/sdb"
  disk=$1
  echo "Installing to $disk"
  sudo fdisk -l $disk
  if [ -n "$ONLYDISK" ]; then
    $(ddcmd $(ls -tr1 Wai*| tail -1) $disk)
  fi
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

dir=$HOME/usb
file=$HOME/WaiveScreen-$(date +%Y%m%d%H%M)-$(git describe).iso
backup=/home/chris/backup-test

die() {
  echo $1
  exit
}

# Place the pip stuff there regardless every time.
if [ -z "$NOPIP" ]; then
  NONET=1 $DIR/syncer.sh pip || die "Can't sync"
  NONET=1 $DIR/syncer.sh force || die "Can't force an update"
fi

if [ "$NOMIRROR" ]; then
  echo "Skipping mirroring"
else
  echo "Using $dir - some serious space is probably needed"
  [ -e $dir ] && rm -rf $dir
  mkdir -p $dir
  fai-mirror -v -cDEBIAN $dir
fi

echo "Checking for the most common fai fail case"
for i in aptcache  conf  db  dists  pool; do
  if [ ! -e $dir/$i ]; then
    echo "Nope nope nope. fai-cd will fail without $dir/$i existing"
    if [ -e $backup/$i ]; then
      echo "Trying to be brilliant and copy over a backup - don't ask me, I only work here."
      cp -r $backup/$i $dir
    else
      die "Can't find a backup either. Fuck all this."
    fi
  else 
    echo "Making a new backup of $i for future fai failures!"
    [ -e $backup/$i ] && rm -fr $backup/$i
    cp -r $dir/$i $backup
  fi
done

echo "Creating a bootable iso named $file"
sudo fai-cd -m $dir $file

if [ -z "$NODISK" ]; then

  if [ -e "$file" ]; then
    echo "Writing to $disk"
    $(ddcmd $file $disk)
  else
    echo "$file does not exist, Bailing!"
  fi
else 
  echo $(ddcmd $file $disk)
fi

