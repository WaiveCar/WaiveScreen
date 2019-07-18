#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. $DIR/const.sh

# this copies over the .sh scripts and infrastructure
sync_scripts() {
  local source=${1:-$DEV/Linux/fai-config/files/home/}

  if [[ -e $source ]]; then
    rsync --exclude=.xinitrc,locals.sh -aqzr $source $DEST
    $SUDO cp $source/.xinitrc $ROOTHOME
    chmod 0600 $DEST/.ssh/KeyBounce $DEST/.ssh/github $DEST/.ssh/dev
  fi
}

_as_user() {
  [[ "$USER" != "$WHO" ]] && su $WHO -c "$*" || eval $*
}

_git() {
  _as_user git $*
}

local_sync() {
  # Since everything is in memory and already loaded
  # we can try to just pull things down
  cd $BASE
  local sha1=${1:-$BRANCH}
  
  # We make sure that local changes (there shouldn't be any)
  # get tossed aside and pull down the new code.
  _git stash
  if _git pull; then
    _git checkout $sha1

    # If there's script updates we try to pull those down
    # as well - we can use our pre-existing sync script
    # to deal with it.
    sync_scripts $BASE/Linux/fai-config/files/home/
    return 0
  fi
  return 1
}

# The success case here is the empty string. Anything
# other than that is failure
code_check() {
  BASEDIR=$1
  LINDIR=$BASEDIR/Linux/fai-config/files/home/

  for i in const.sh baseline.sh lib.sh; do
    . $LINDIR/$i
  done

  for i in start-x-stuff.sh .xinitrc; do
    bash -n $LINDIR/$i
  done

  SANITYCHECK=1 $BASEDIR/ScreenDaemon/SensorDaemon.py
  SANITYCHECK=1 $BASEDIR/ScreenDaemon/ScreenDaemon.py

  [[ $($LINDIR/dcall kv_get sms) = $($BASEDIR/ScreenDaemon/dcall kv_get sms) ]] || echo "The python and bash kv_get don't match"
}
