#!/bin/bash
#
# NODISK    - Won't do disk things 
# NONET     - Won't try to do internet stuff
# MIRROR    - Will (re)do the mirroring
# ONLYDISK  - Only creates a disk
# NOPIP     - Skip over pip download
# NOKBD     - Excludes keyboard override magic
# JUSTDOIT  - Overrides the blocking of only creating release disks
#

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
dir=$HOME/usb
now=$(date +%Y%m%d%H%M)
branch=$(git rev-parse --abbrev-ref HEAD)
version=$(git describe)-$branch
repo=$HOME/installs/
file=$repo/WaiveScreen-$now-$version.iso
backup=/home/chris/backup-test

die() {
  echo $1
  exit 1
}

ddcmd() {
  local size=$(stat -c %s $1)
  echo "sudo dd if=$1 of=$2 bs=1M"
  [[ -z "$NODISK" ]] && echo $now $(udevadm info --name=$2 | grep SERIAL=) $1 >> $repo/log.txt
  exit
}

if [[ -z "$NODISK" ]]; then
  [[ $# -lt 1 ]] && die "You need to pass a disk dev entry to install to such as /dev/sdb"
  disk=$1
  [[ $disk == "release" ]] && disk=/dev/sdb
  [[ -b $disk ]] || die "Woops, $disk isn't a disk"
  [[ $(stat -c %T $disk) -eq 11 ]] && die "Woah, $disk is a PARTITION. I need the whole disk."
  if [[ $# -gt 1 ]]; then
    query=$(udevadm info --name=$disk | grep SERIAL=)
    grep "$query" $repo/log.txt
    exit
  fi

  sudo fdisk -l $disk

  if [[ $1 == "release" ]]; then
    touse=$(ls -tr $repo*release* | tail -1)
    echo "using $touse"
    eval $(ddcmd $touse $disk)
    exit
  fi

  if [[ -n "$ONLYDISK" ]]; then
    eval $(ddcmd $(ls -tr1 $HOME/installs/Wai*| tail -1) $disk) 
    exit
  fi
fi

[[ -z "$JUSTDOIT" && $branch != "release" ]] && die "Nope, not doing it. You need to switch to the release branch or pass JUSTDOIT."

preexist=$(ls $HOME/WaiveScreen-*$version.iso 2> /dev/null)
[[ -n "$preexist" ]] && die "$preexist already exists. Either run with ONLYDISK or remove the iso(s)."
if [[ -z "$NOPIP" ]]; then
  NONET=1 $DIR/syncer.sh pip || die "Can't install the pip requirements, check requirements.txt" 
fi

if [ "$MIRROR" -o ! -e $dir ]; then
  [ -d $usb ] && rm -fr $usb
  mkdir -p $dir
  fai-mirror -v -cDEBIAN $dir
fi

echo "Creating a bootable iso named $file"
if [[ -z "$NOKBD" ]]; then
  # We make a magic file named xorriso which injects
  # our keyboard override
  mkdir -p /tmp/bin
  cat > /tmp/bin/xorriso << ENDL
#!/bin/bash
set -x
for i in \$*; do
  if [[ \$i =~ /tmp/fai ]] && [[ -d \$i ]]; then
    echo "Making keyboard unlock file in \$i"
    touch \$i/voHCPtpJS9izQxt3QtaDAQ_make_keyboard_work
  fi
done
echo /usr/bin/xorriso "\$@"
/usr/bin/xorriso "\$@"
ENDL
  chmod +x /tmp/bin/xorriso

  sudo PATH=/tmp/bin:$PATH fai-cd -m $dir $file
else 
  echo "Skipping keyboard override"
  sudo fai-cd -m $dir $file
fi

if [[ -z "$NODISK" ]]; then
  [[ -e "$file" ]] || die "$file does not exist, Bailing!"
  eval $(ddcmd $file $disk)
else 
  echo $(ddcmd $file $disk)
fi

