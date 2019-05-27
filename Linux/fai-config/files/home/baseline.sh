#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. $DIR/const.sh


sync_scripts() {
  rsync --exclude=.xinitrc -aqzr $DEV/Linux/fai-config/files/home/ $DEST
  chmod 0600 $DEST/.ssh/KeyBounce $DEST/.ssh/github $DEST/.ssh/dev
}
