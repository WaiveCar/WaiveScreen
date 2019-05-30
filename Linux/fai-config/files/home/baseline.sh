#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. $DIR/const.sh

sync_scripts() {
  source=$DEV/Linux/fai-config/files/home/

  if [ ! -e $source ]; then
    echo "Warning: $source doesn't exist."
  else
    rsync --exclude=.xinitrc -aqzr $source $DEST
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

  if [ -z "$SUDO" ]; then
    _warn "Hey, you can't be root to do sshfs"
  fi

  sshfs -o uid=$(id -u $WHO),gid=$(id -g $WHO) dev:/home/chris/code/WaiveScreen $DEV -C -o allow_root
  export BASE=$DEV
  set_event net ''
}
