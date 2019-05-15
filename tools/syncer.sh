#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CODE=$DIR/../Linux/fai-config

while [ 0 ]; do
  sudo cp -pru $CODE/* /srv/fai/config
  sudo chown -R root.root /srv/fai/config/scripts
  ssh screen "./dcall sync_scripts"
  date +%X > /tmp/last-sync
  inotifywait -qe close_write,attrib,modify,move,move_self,create,delete,delete_self -r $CODE
done
