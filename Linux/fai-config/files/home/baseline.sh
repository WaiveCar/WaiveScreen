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
