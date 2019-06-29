#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. $DIR/const.sh

# this copies over the .sh scripts and infrastructure
sync_scripts() {
  local source=${1:-$DEV/Linux/fai-config/files/home/}

  if [[ ! -e $source ]]; then
    echo "Warning: $source doesn't exist."
  else
    rsync --exclude=.xinitrc,locals.sh -aqzr $source $DEST
    chmod 0600 $DEST/.ssh/KeyBounce $DEST/.ssh/github $DEST/.ssh/dev
  fi
}

dev_setup() {
  $SUDO pkill dhclient
  oldroute=$(ip route show | grep default | awk ' { print $1" "$2" "$3 }')
  [[ -n "$oldroute" ]] && $SUDO ip route delete $oldroute

  $SUDO dhclient enp3s0 
  [[ -e $DEV ]] || mkdir $DEV

  _as_user sshfs -o uid=$(id -u $WHO),gid=$(id -g $WHO),nonempty,allow_root dev:/home/chris/code/WaiveScreen $DEV -C 
  export BASE=$DEV
}

_as_user() {
  [[ $USER = 'root' ]] && su $WHO -c "$*" || eval $*
}

_git() {
  _as_user git $*
}

local_sync() {
  # Since everything is in memory and already loaded
  # we can try to just pull things down
  cd $BASE
  local sha1=${1:-master}
  
  # We make sure that local changes (there shouldn't be any)
  # get tossed aside and pull down the new code.
  _git stash
  if _git pull; then
    _get checkout $sha1

    # If there's script updates we try to pull those down
    # as well - we can use our pre-existing sync script
    # to deal with it.
    sync_scripts $BASE/Linux/fai-config/files/home/
    return 0
  fi
  return 1
}
