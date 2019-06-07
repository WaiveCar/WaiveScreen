#!/bin/bash

. $HOME/const.sh
. $DEST/locals.sh

check_ssh_hole() {

  tomake=$(mktemp -u -p)

  [[ $USER = 'root' ]] && cmd="su adorno -c"

  # Next we try to create this remotely using su if we need to.
  echo "ssh -o ConnectTimeout=10 adorno@bounce -p $PORT touch $tomake" | $cmd /bin/bash

  # If the file exists we are done, let's clean it up
  # otherwise our hole is down and we need to restart 
  [ -e $tomake ] && rm $tomake || dcall ssh_hole 
}
