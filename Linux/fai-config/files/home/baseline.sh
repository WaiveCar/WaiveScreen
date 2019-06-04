#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. $DIR/const.sh

sync_scripts() {
  source=${1:-$DEV/Linux/fai-config/files/home/}

  if [ ! -e $source ]; then
    echo "Warning: $source doesn't exist."
  else
    rsync --exclude=.xinitrc,locals.sh -aqzr $source $DEST
    chmod 0600 $DEST/.ssh/KeyBounce $DEST/.ssh/github $DEST/.ssh/dev
  fi
}

dev_setup() {
  #
  # Note: this usually runs as normal user
  #
  # echo development > $DEST/.env
  $SUDO dhclient enp3s0 
  [ -e $DEV ] || mkdir $DEV

  _as_user sshfs -o uid=$(id -u $WHO),gid=$(id -g $WHO),nonempty,allow_root dev:/home/chris/code/WaiveScreen $DEV -C 
  export BASE=$DEV
}

_as_user() {
  if [ $USER = 'root' ]; then
    echo "Running as $WHO"
    su $WHO -c "$*"
  else
    echo "Running as me"
    eval $*
  fi
}
_git() {
  _as_user git $*
}

local_sync() {
  # Since everything is in memory and already loaded
  # we can try to just pull things down
  cd $BASE
  
  # We make sure that local changes (there shouldn't be any)
  # get tossed aside and pull down the new code.
  _git stash
  _git pull

  # If there's script updates we try to pull those down
  # as well - we can use our pre-existing sync script
  # to deal with it.
  sync_scripts $BASE/Linux/fai-config/files/home/
}
